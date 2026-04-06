from fastapi import APIRouter
from langchain_core.messages import HumanMessage, AIMessage

from app.models.persona import CustomerPersona
from app.agent.graph import graph

router = APIRouter(prefix="/api", tags=["intake"])


class IntakeRequest(CustomerPersona):
    """Form submission for Phase 01. Extends CustomerPersona with session_id."""
    session_id: str


@router.post("/intake")
async def submit_intake(request: IntakeRequest):
    """Submit structured intake form, skip chat-based collection, advance to Phase 02."""
    config = {"configurable": {"thread_id": request.session_id}}

    persona = CustomerPersona(**request.model_dump(exclude={"session_id"}))
    missing = persona.get_missing_required_fields()
    if missing:
        return {
            "success": False,
            "error": f"Missing required fields: {', '.join(missing)}",
            "missing_fields": missing,
        }

    # Build a summary message so the conversation has context
    summary_parts = []
    if persona.customer_name:
        summary_parts.append(f"Customer: {persona.customer_name}")
    if persona.industry:
        summary_parts.append(f"Industry: {persona.industry}")
    if persona.pain_points:
        summary_parts.append(f"Pain Points: {', '.join(persona.pain_points)}")
    if persona.use_scenarios:
        summary_parts.append(f"Use Scenarios: {', '.join(persona.use_scenarios)}")
    if persona.budget_amount:
        summary_parts.append(f"Budget: ${persona.budget_amount:,.0f}")
    if persona.service_warranty_needs:
        summary_parts.append(f"Warranty Needs: {persona.service_warranty_needs}")
    if persona.current_devices:
        summary_parts.append(f"Current Devices: {', '.join(persona.current_devices)}")
    if persona.fleet_size:
        summary_parts.append(f"Fleet Size: {persona.fleet_size}")
    if persona.deployment_timeline:
        summary_parts.append(f"Deployment Timeline: {persona.deployment_timeline}")

    user_summary = "Customer intake form submitted:\n" + "\n".join(f"- {p}" for p in summary_parts)

    # Initialize graph state with the persona already complete, phase set to recommendation
    input_data = {
        "messages": [
            HumanMessage(content=user_summary),
            AIMessage(content=(
                f"Thank you! I've recorded the customer profile for "
                f"{persona.customer_name or 'your customer'}. "
                f"All required information has been collected. "
                f"Let's move on to product recommendation. "
                f"Which Getac product would you like to recommend for this customer?"
            )),
        ],
        "session_id": request.session_id,
        "current_phase": "recommendation",
        "persona": persona,
        "proposal_approved": False,
    }

    # Use update_state to seed the graph checkpoint directly
    graph.update_state(config, input_data)

    return {
        "success": True,
        "session_id": request.session_id,
        "phase": "recommendation",
        "persona": persona.model_dump(),
    }
