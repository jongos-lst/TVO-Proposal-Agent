from typing import Optional
from pydantic import BaseModel


class GetacProduct(BaseModel):
    id: str
    name: str
    category: str
    base_price: float
    display_size: str
    display_brightness: Optional[str] = None
    processor: str
    ram_options: list[str]
    storage_options: list[str]
    rugged_rating: str
    operating_temp: str
    battery_life: str
    weight: Optional[str] = None
    warranty_standard: str
    warranty_options: list[str]
    key_features: list[str]
    connectivity: Optional[list[str]] = None
    ports: Optional[list[str]] = None
    target_industries: list[str]
    annual_failure_rate: float  # for TVO calculation
    product_url: Optional[str] = None


class CompetitorProduct(BaseModel):
    name: str
    category: str
    base_price: float
    warranty_standard: str
    annual_failure_rate: float
    weaknesses: list[str]
    display_size: Optional[str] = None
    rugged_rating: Optional[str] = None
    weight: Optional[str] = None
    processor: Optional[str] = None
    product_url: Optional[str] = None
