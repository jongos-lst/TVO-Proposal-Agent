from pydantic import BaseModel


class ProductivityFactor(BaseModel):
    """One productivity sub-factor with full explainability."""
    name: str           # e.g. "Downtime Avoidance", "Battery Continuity"
    description: str    # 1-line explanation for the proposal deck
    formula: str        # Human-readable formula string
    annual_value: float # Dollar value per year
    total_value: float  # Dollar value over deployment period
    applies: bool       # Whether this factor applies (based on product features)
    assumptions: list[str]  # Factor-specific assumptions


class TCOLineItem(BaseModel):
    label: str
    formula: str
    getac_value: float
    competitor_value: float
    difference: float
    notes: str


class TVOCalculation(BaseModel):
    # Input parameters
    fleet_size: int
    deployment_years: int
    hourly_productivity_value: float

    # TCO comparison
    tco_line_items: list[TCOLineItem]
    getac_total_tco: float
    competitor_total_tco: float
    tco_savings: float
    tco_savings_percent: float

    # Productivity
    getac_annual_downtime_hours: float
    competitor_annual_downtime_hours: float
    productivity_savings_annual: float
    productivity_savings_total: float

    # Risk
    getac_expected_failures: float
    competitor_expected_failures: float
    risk_reduction_percent: float

    # ROI & Projections
    roi_payback_months: float = 0.0
    yearly_getac_cumulative: list[float] = []
    yearly_competitor_cumulative: list[float] = []

    # Productivity breakdown
    productivity_breakdown: list[ProductivityFactor] = []

    # Summary
    total_value_advantage: float
    assumptions: list[str]
