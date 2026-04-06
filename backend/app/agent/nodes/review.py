import json
import logging
from langchain_core.messages import SystemMessage, AIMessage
from app.agent.state import AgentState
from app.agent.prompts import REVIEW_SYSTEM_PROMPT
from app.services.llm import get_llm

logger = logging.getLogger(__name__)


APPROVAL_CHECK_PROMPT = """Classify the sales rep's latest message into exactly one of these categories:

"approved" — The rep explicitly approved the proposal. Examples: "approve", "looks good", "yes generate it", "go ahead", "let's generate the deck", "approved", "ship it", "looks correct"
"changes" — The rep wants to modify something. Examples: "change fleet size to 200", "switch to the F110", "update the budget", "can we adjust..."
"reviewing" — The rep is asking questions, reviewing, or hasn't decided. Examples: "tell me more about...", "what if we...", "can you explain...", "hmm"

Return ONLY: {{"status": "approved"}} or {{"status": "changes"}} or {{"status": "reviewing"}}
No other text."""


async def review_node(state: AgentState) -> dict:
    """Phase 04: Proposal review with human-in-the-loop (multi-product)."""
    llm = get_llm()
    persona = state.get("persona")
    selected_products = state.get("selected_products") or []
    tvo_results = state.get("tvo_results") or {}
    competitor_names = state.get("competitor_product_names") or {}
    advantages_map = state.get("competitive_advantages") or {}
    messages = state["messages"]
    approved = state.get("proposal_approved", False)

    # Check if user approved in their latest message
    if len(messages) > 1 and not approved:
        try:
            extraction_llm = get_llm(streaming=False, temperature=0).with_config(tags=["extraction"])
            check_messages = list(messages[-3:]) + [SystemMessage(content=APPROVAL_CHECK_PROMPT)]
            result = await extraction_llm.ainvoke(check_messages)
            content = result.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            parsed = json.loads(content.strip())
            if parsed.get("status") == "approved":
                approved = True
        except (json.JSONDecodeError, IndexError):
            pass
        except Exception as e:
            logger.warning("Approval extraction LLM failed: %s", e)
            last_msg = str(messages[-1].content).lower()
            approval_keywords = ["approve", "approved", "looks good", "go ahead", "generate", "ship it", "let's go"]
            if any(kw in last_msg for kw in approval_keywords):
                approved = True

    # Build proposal summary for all products
    sections = []
    if persona:
        persona_data = persona.model_dump()
        persona_lines = []
        for k, v in persona_data.items():
            if v is not None and v != []:
                label = k.replace("_", " ").title()
                persona_lines.append(f"  {label}: {v}")
        sections.append("CUSTOMER PROFILE:\n" + "\n".join(persona_lines))

    for product in selected_products:
        sections.append(
            f"RECOMMENDED PRODUCT: {product.name}\n"
            f"  Category: {product.category}\n"
            f"  Price: ${product.base_price:,.0f}\n"
            f"  Warranty: {product.warranty_standard}\n"
            f"  Rugged Rating: {product.rugged_rating}"
        )

        tvo = tvo_results.get(product.id)
        if tvo:
            sections.append(
                f"TVO/TCO FOR {product.name}:\n"
                f"  vs. {competitor_names.get(product.id, 'Competitor')}\n"
                f"  Total Getac TCO: ${tvo.getac_total_tco:,.0f}\n"
                f"  Total Competitor TCO: ${tvo.competitor_total_tco:,.0f}\n"
                f"  Total Savings: ${tvo.tco_savings:,.0f} ({tvo.tco_savings_percent:.1f}%)\n"
                f"  Productivity Savings: ${tvo.productivity_savings_total:,.0f}\n"
                f"  Risk Reduction: {tvo.risk_reduction_percent:.1f}%"
            )

        prod_advantages = advantages_map.get(product.id, [])
        if prod_advantages:
            sections.append(
                f"COMPETITIVE ADVANTAGES ({product.name}):\n" +
                "\n".join(f"  - {a}" for a in prod_advantages)
            )

    # Combined savings summary
    total_savings = sum(t.tco_savings for t in tvo_results.values())
    if total_savings > 0:
        sections.append(
            f"COMBINED SAVINGS ACROSS ALL {len(selected_products)} PRODUCT(S):\n"
            f"  Total Combined Savings: ${total_savings:,.0f}"
        )

    proposal_summary = "\n\n".join(sections)

    deployment_years = state.get("deployment_years", 5)
    system = REVIEW_SYSTEM_PROMPT.format(
        proposal_summary=proposal_summary,
        deployment_years=deployment_years,
        product_count=len(selected_products),
    )
    recent_messages = list(messages)[-6:]
    try:
        response = await llm.ainvoke([SystemMessage(content=system)] + recent_messages)
    except Exception as e:
        logger.error("Review LLM call failed: %s", e, exc_info=True)
        response = AIMessage(content=(
            "I encountered a temporary error connecting to the AI service. "
            "Your proposal data is safe. Please try again — say **'approve'** to generate the deck, "
            "or ask me to modify any section."
        ))

    # Generate value proposition if approving
    value_prop = state.get("value_proposition")
    if approved and not value_prop:
        try:
            vp_llm = get_llm(streaming=False).with_config(tags=["extraction"])
            vp_result = await vp_llm.ainvoke([
                SystemMessage(content=(
                    "Write a 2-3 sentence compelling value proposition for this TVO proposal "
                    f"covering {len(selected_products)} product(s). "
                    "Focus on the combined savings and benefits. Be specific with numbers.\n\n"
                    f"{proposal_summary}"
                ))
            ])
            value_prop = vp_result.content
        except Exception as e:
            logger.warning("Value proposition generation failed: %s", e)
            if tvo_results:
                customer_name = persona.customer_name if persona else "the customer"
                value_prop = (
                    f"By switching to Getac's recommended solution of {len(selected_products)} product(s), "
                    f"{customer_name} can save a combined ${total_savings:,.0f} over {deployment_years} years "
                    f"while significantly reducing device failures and downtime."
                )
            else:
                value_prop = "Getac rugged devices deliver lower total cost of ownership through reduced failures, longer device lifecycles, and superior field productivity."

    new_phase = "review"

    return {
        "messages": [response],
        "proposal_approved": approved,
        "value_proposition": value_prop,
        "current_phase": new_phase,
    }
