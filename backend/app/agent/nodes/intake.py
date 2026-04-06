import json
from langchain_core.messages import SystemMessage, AIMessage
from app.agent.state import AgentState
from app.agent.prompts import INTAKE_SYSTEM_PROMPT
from app.models.persona import CustomerPersona
from app.services.llm import get_llm


EXTRACTION_PROMPT = """You are a data extraction assistant. Analyze the full conversation and extract every piece of customer information mentioned so far.

Return a JSON object. Use null for any field NOT explicitly mentioned or clearly implied. Do not guess or infer values that weren't stated.

Fields:
- customer_name: string or null (company or organization name)
- industry: string or null (e.g., "Utilities", "Public Safety", "Oil & Gas", "Manufacturing", "Healthcare", "Transportation")
- pain_points: list of strings or null (problems with current devices — e.g., "devices break in rain", "screen unreadable in sunlight", "high repair costs", "frequent downtime")
- use_scenarios: list of strings or null (where/how devices are used — e.g., "outdoor field inspections", "patrol vehicles", "warehouse inventory", "construction sites")
- budget_amount: number or null (numeric total budget in USD, e.g., 500000, 200000)
- service_warranty_needs: string or null (e.g., "bumper-to-bumper", "3-year minimum", "next-day replacement", "accidental damage coverage")
- current_devices: list of strings or null (device names — e.g., ["Dell Latitude 5430", "iPad Pro"], not generic terms like "laptops")
- fleet_size: number or null (integer number of devices needed)
- deployment_timeline: string or null (e.g., "Q3 2026", "within 6 months", "immediate")

Return ONLY valid JSON. No markdown, no explanation."""


async def intake_node(state: AgentState) -> dict:
    """Phase 01: Collect customer persona through conversation."""
    llm = get_llm()
    persona = state.get("persona") or CustomerPersona()

    # Extract persona fields from conversation
    messages = state["messages"]
    if len(messages) > 1:  # Skip extraction on first message
        extraction_llm = get_llm(streaming=False)
        extraction_messages = list(messages) + [
            SystemMessage(content=EXTRACTION_PROMPT)
        ]
        extraction_result = await extraction_llm.ainvoke(extraction_messages)
        try:
            content = extraction_result.content
            # Try to parse JSON from the response
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            extracted = json.loads(content.strip())
            # Merge extracted fields into persona (only non-null values)
            for field, value in extracted.items():
                if value is not None and hasattr(persona, field):
                    setattr(persona, field, value)
        except (json.JSONDecodeError, IndexError):
            pass  # If extraction fails, continue with what we have

    # Build the conversational response
    missing = persona.get_missing_required_fields()
    collected = {
        k: v for k, v in persona.model_dump().items()
        if v is not None and v != []
    }

    field_labels = {
        "pain_points": "Pain Points",
        "use_scenarios": "Use Scenarios",
        "budget_amount": "Budget",
        "service_warranty_needs": "Service & Warranty Needs",
        "current_devices": "Current Devices",
    }

    if collected:
        collected_str = "\n".join(
            f"  {k.replace('_', ' ').title()}: {v}" for k, v in collected.items()
        )
    else:
        collected_str = "None yet"
    missing_str = ", ".join(field_labels.get(f, f) for f in missing) if missing else "All required fields collected!"

    system = INTAKE_SYSTEM_PROMPT.format(
        collected_fields=collected_str,
        missing_fields=missing_str,
    )

    response = await llm.ainvoke([SystemMessage(content=system)] + list(messages))

    # Determine next phase
    new_phase = "intake" if missing else "recommendation"

    return {
        "messages": [response],
        "persona": persona,
        "current_phase": new_phase,
    }
