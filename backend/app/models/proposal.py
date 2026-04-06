from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
import uuid

from .persona import CustomerPersona
from .product import GetacProduct
from .tvo import TVOCalculation


class Proposal(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.now)
    status: Literal["draft", "approved", "exported"] = "draft"

    # Phase 01
    persona: Optional[CustomerPersona] = None

    # Phase 02 (multi-product)
    selected_products: list[GetacProduct] = []
    competitor_product_names: dict[str, str] = {}          # product_id -> competitor name
    competitive_advantages: dict[str, list[str]] = {}      # product_id -> advantages

    # Phase 03 (multi-product)
    tvo_calculations: dict[str, TVOCalculation] = {}       # product_id -> TVO result

    # Phase 04
    value_proposition: Optional[str] = None
    approved_at: Optional[datetime] = None

    # Phase 05
    pptx_generated: bool = False
