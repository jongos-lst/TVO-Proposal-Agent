import logging
import os
import uuid
from datetime import datetime
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from app.agent.state import AgentState
from app.agent.prompts import GENERATION_SYSTEM_PROMPT
from app.models.proposal import Proposal
from app.services.llm import get_llm
from app.services.pptx_generator import generate_proposal_pptx

logger = logging.getLogger(__name__)


async def generation_node(state: AgentState) -> dict:
    """Phase 05: Generate PowerPoint proposal deck (multi-product)."""
    messages = state["messages"]

    selected_products = state.get("selected_products") or []
    tvo_results = state.get("tvo_results") or {}
    persona = state.get("persona")
    value_proposition = state.get("value_proposition")

    # Generate value proposition if missing (bypassed when frontend overrides to generation)
    if not value_proposition and selected_products:
        try:
            vp_llm = get_llm(streaming=False).with_config(tags=["extraction"])
            # Build a summary for the LLM
            sections = []
            if persona:
                sections.append(f"Customer: {persona.customer_name or 'N/A'}, Industry: {persona.industry or 'N/A'}")
            for p in selected_products:
                tvo = tvo_results.get(p.id)
                if tvo:
                    sections.append(
                        f"{p.name}: TCO Savings ${tvo.tco_savings:,.0f} ({tvo.tco_savings_percent:.1f}%), "
                        f"Productivity Savings ${tvo.productivity_savings_total:,.0f}, "
                        f"Risk Reduction {tvo.risk_reduction_percent:.1f}%"
                    )
            summary = "\n".join(sections)
            vp_result = await vp_llm.ainvoke([
                SystemMessage(content=(
                    "Write a 2-3 sentence compelling value proposition for this TVO proposal "
                    f"covering {len(selected_products)} product(s). "
                    "Focus on the combined savings and benefits. Be specific with numbers.\n\n"
                    f"{summary}"
                ))
            ])
            value_proposition = vp_result.content
        except Exception as e:
            logger.warning("Value proposition generation in generation node failed: %s", e)
            total_savings = sum(t.tco_savings for t in tvo_results.values())
            deployment_years = state.get("deployment_years", 5)
            customer_name = persona.customer_name if persona else "the customer"
            if tvo_results:
                value_proposition = (
                    f"By switching to Getac's recommended solution of {len(selected_products)} product(s), "
                    f"{customer_name} can save a combined ${total_savings:,.0f} over {deployment_years} years "
                    f"while significantly reducing device failures and downtime."
                )
            else:
                value_proposition = (
                    "Getac rugged devices deliver lower total cost of ownership through "
                    "reduced failures, longer device lifecycles, and superior field productivity."
                )

    # Build the Proposal object from state
    proposal = Proposal(
        id=state.get("session_id", str(uuid.uuid4())),
        persona=persona,
        selected_products=selected_products,
        competitor_product_names=state.get("competitor_product_names") or {},
        competitive_advantages=state.get("competitive_advantages") or {},
        tvo_calculations=tvo_results,
        value_proposition=value_proposition,
        status="approved",
    )

    # Generate the PowerPoint file with timestamp
    output_dir = os.path.join(os.path.dirname(__file__), "..", "..", "output")
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    customer_slug = ""
    if proposal.persona and proposal.persona.customer_name:
        customer_slug = proposal.persona.customer_name.replace(" ", "_")[:30] + "_"
    pptx_path = os.path.join(output_dir, f"TVO_Proposal_{customer_slug}{timestamp}.pptx")

    try:
        pptx_buffer = generate_proposal_pptx(proposal)
        with open(pptx_path, "wb") as f:
            f.write(pptx_buffer.read())
    except Exception as e:
        logger.error("PPTX generation failed: %s", e, exc_info=True)
        return {
            "messages": [AIMessage(content=(
                f"**Error generating the PowerPoint deck:** {e}\n\n"
                "Please try again — you can say 'generate deck' to retry."
            ))],
            "current_phase": "review",
            "proposal_approved": True,
        }

    product_count = len(proposal.selected_products)

    # Generate the response message
    try:
        llm = get_llm()
        last_user = [m for m in messages if isinstance(m, HumanMessage)][-1:]
        system_prompt = GENERATION_SYSTEM_PROMPT.format(product_count=product_count)
        response = await llm.ainvoke([SystemMessage(content=system_prompt)] + last_user)
        if not response.content or not response.content.strip():
            raise ValueError("Empty LLM response")
    except Exception as e:
        logger.warning("Generation LLM response failed (deck still generated): %s", e)
        product_names = ", ".join(p.name for p in proposal.selected_products)
        response = AIMessage(content=(
            f"Your TVO proposal deck has been generated with **{product_count} product(s)** "
            f"({product_names}) and is ready for download!\n\n"
            "**The deck includes:**\n"
            "1. Cover slide with customer details\n"
            "2. Customer situation & challenges\n"
            f"3. Recommended solution slides ({product_count} products)\n"
            f"4. TVO/TCO comparison slides ({product_count} analyses)\n"
            "5. Savings breakdown & productivity impact\n"
            "6. Competitive differentiation\n"
            "7. Conclusion & next steps\n\n"
            "Click the **Download PowerPoint** button to get your deck. "
            "You can customize it further before presenting to the customer."
        ))

    return {
        "messages": [response],
        "pptx_path": pptx_path,
        "current_phase": "complete",
        "proposal_approved": True,
        "value_proposition": value_proposition,
    }
