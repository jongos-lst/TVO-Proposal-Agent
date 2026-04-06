from pydantic import BaseModel
from typing import Optional


class CustomerPersona(BaseModel):
    customer_name: Optional[str] = None
    industry: Optional[str] = None
    pain_points: Optional[list[str]] = None
    use_scenarios: Optional[list[str]] = None
    budget_amount: Optional[float] = None
    service_warranty_needs: Optional[str] = None
    current_devices: Optional[list[str]] = None
    fleet_size: Optional[int] = None
    deployment_timeline: Optional[str] = None

    def get_missing_required_fields(self) -> list[str]:
        """Return list of required fields that are still empty."""
        required = {
            "pain_points": self.pain_points,
            "use_scenarios": self.use_scenarios,
            "budget_amount": self.budget_amount,
            "service_warranty_needs": self.service_warranty_needs,
            "current_devices": self.current_devices,
        }
        return [field for field, value in required.items() if not value]

    def is_complete(self) -> bool:
        return len(self.get_missing_required_fields()) == 0
