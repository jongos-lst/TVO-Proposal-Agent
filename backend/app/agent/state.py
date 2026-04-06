from typing import Annotated, Optional, Literal
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

from app.models.persona import CustomerPersona
from app.models.product import GetacProduct
from app.models.tvo import TVOCalculation


class AgentState(TypedDict):
    """Central state flowing through the LangGraph workflow."""
    # Conversation
    messages: Annotated[list[BaseMessage], add_messages]
    session_id: str
    current_phase: Literal[
        "intake", "recommendation", "calculation", "review", "generation", "complete"
    ]

    # Phase 01 — Customer Persona
    persona: Optional[CustomerPersona]

    # Phase 02 — Product Recommendation (multi-product)
    selected_products: Optional[list[GetacProduct]]
    competitor_product_names: Optional[dict[str, str]]        # product_id -> competitor name
    competitive_advantages: Optional[dict[str, list[str]]]    # product_id -> advantages

    # Phase 03 — TVO Calculation (multi-product)
    tvo_results: Optional[dict[str, TVOCalculation]]          # product_id -> TVO result
    fleet_size: Optional[int]
    deployment_years: Optional[int]

    # Phase 04 — Review
    proposal_approved: bool
    value_proposition: Optional[str]

    # Phase 05 — Generation
    pptx_path: Optional[str]
