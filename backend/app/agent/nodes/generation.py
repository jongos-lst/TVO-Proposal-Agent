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

    # Build the Proposal object from state
    proposal = Proposal(
        id=state.get("session_id", str(uuid.uuid4())),
        persona=state.get("persona"),
        selected_products=state.get("selected_products") or [],
        competitor_product_names=state.get("competitor_product_names") or {},
        competitive_advantages=state.get("competitive_advantages") or {},
        tvo_calculations=state.get("tvo_results") or {},
        value_proposition=state.get("value_proposition"),
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
    }
