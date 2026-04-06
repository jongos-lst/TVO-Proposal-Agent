"""Tests for TVO calculator, focusing on the 5-factor productivity breakdown."""

import pytest

from app.services.tvo_calculator import calculate_tvo
from app.models.tvo import ProductivityFactor


# Shared base params for brevity
BASE = dict(
    getac_unit_price=3299,
    getac_warranty_years=3,
    getac_failure_rate=0.02,
    competitor_unit_price=2199,
    competitor_warranty_years=1,
    competitor_failure_rate=0.12,
    fleet_size=100,
    deployment_years=5,
)


class TestProductivityBreakdown:
    def test_all_five_factors_present(self):
        """With all features enabled, 5 factors should be in breakdown."""
        tvo = calculate_tvo(**BASE)
        assert len(tvo.productivity_breakdown) == 5
        names = {f.name for f in tvo.productivity_breakdown}
        assert names == {
            "Downtime Avoidance",
            "Battery Continuity",
            "Display Readability",
            "Environmental Resilience",
            "Connectivity Advantage",
        }

    def test_all_factors_apply_with_defaults(self):
        """Default params enable all 5 factors (Getac has hot-swap, 1400 nit, IP66, Wi-Fi 7)."""
        tvo = calculate_tvo(**BASE)
        applicable = [f for f in tvo.productivity_breakdown if f.applies]
        assert len(applicable) == 5

    def test_productivity_total_equals_factor_sum(self):
        """Aggregate productivity_savings_total must equal sum of applicable factor totals."""
        tvo = calculate_tvo(**BASE)
        factor_sum = sum(f.total_value for f in tvo.productivity_breakdown if f.applies)
        assert abs(tvo.productivity_savings_total - factor_sum) < 0.01

    def test_no_hot_swap_disables_battery_factor(self):
        tvo = calculate_tvo(**BASE, getac_has_hot_swap=False)
        battery = next(f for f in tvo.productivity_breakdown if "Battery" in f.name)
        assert not battery.applies
        assert battery.total_value == 0

    def test_equal_display_disables_readability_factor(self):
        tvo = calculate_tvo(**BASE, getac_display_nits=600, competitor_display_nits=600)
        display = next(f for f in tvo.productivity_breakdown if "Display" in f.name)
        assert not display.applies
        assert display.total_value == 0

    def test_equal_ip_disables_resilience_factor(self):
        tvo = calculate_tvo(**BASE, getac_ip_rating=53, competitor_ip_rating=53)
        resilience = next(f for f in tvo.productivity_breakdown if "Resilience" in f.name)
        assert not resilience.applies
        assert resilience.total_value == 0

    def test_both_wifi7_disables_connectivity_factor(self):
        tvo = calculate_tvo(**BASE, getac_has_wifi7=True, competitor_has_wifi7=True)
        conn = next(f for f in tvo.productivity_breakdown if "Connectivity" in f.name)
        assert not conn.applies
        assert conn.total_value == 0

    def test_equal_failure_rate_disables_downtime_factor(self):
        tvo = calculate_tvo(**{**BASE, "getac_failure_rate": 0.05, "competitor_failure_rate": 0.05})
        downtime = next(f for f in tvo.productivity_breakdown if "Downtime" in f.name)
        assert not downtime.applies
        assert downtime.total_value == 0

    def test_all_factors_disabled(self):
        """When product has no advantages, all factors should be disabled."""
        tvo = calculate_tvo(
            **{**BASE, "getac_failure_rate": 0.12},
            getac_has_hot_swap=False,
            getac_display_nits=600,
            competitor_display_nits=600,
            getac_ip_rating=53,
            competitor_ip_rating=53,
            getac_has_wifi7=False,
            competitor_has_wifi7=False,
        )
        applicable = [f for f in tvo.productivity_breakdown if f.applies]
        assert len(applicable) == 0
        assert tvo.productivity_savings_total == 0

    def test_fleet_size_scales_linearly(self):
        """Doubling fleet size should roughly double productivity savings."""
        tvo_100 = calculate_tvo(**{**BASE, "fleet_size": 100})
        tvo_200 = calculate_tvo(**{**BASE, "fleet_size": 200})
        ratio = tvo_200.productivity_savings_total / tvo_100.productivity_savings_total
        assert 1.95 < ratio < 2.05

    def test_deployment_years_scales(self):
        """Doubling deployment years should roughly double total productivity savings."""
        tvo_3 = calculate_tvo(**{**BASE, "deployment_years": 3})
        tvo_6 = calculate_tvo(**{**BASE, "deployment_years": 6})
        ratio = tvo_6.productivity_savings_total / tvo_3.productivity_savings_total
        assert 1.95 < ratio < 2.05

    def test_each_factor_has_formula_and_assumptions(self):
        """Every factor must have a non-empty formula and at least one assumption."""
        tvo = calculate_tvo(**BASE)
        for factor in tvo.productivity_breakdown:
            assert factor.formula, f"{factor.name} missing formula"
            assert len(factor.assumptions) >= 1, f"{factor.name} missing assumptions"
            assert factor.description, f"{factor.name} missing description"

    def test_backward_compatible_defaults(self):
        """Calling with only original params should work (all new params have defaults)."""
        tvo = calculate_tvo(
            getac_unit_price=3299, getac_warranty_years=3, getac_failure_rate=0.02,
            competitor_unit_price=2199, competitor_warranty_years=1, competitor_failure_rate=0.12,
            fleet_size=100, deployment_years=5,
        )
        assert tvo.productivity_savings_total > 0
        assert len(tvo.productivity_breakdown) == 5


class TestTCOIntegrity:
    """Verify the overall TCO calculation still works correctly with the new model."""

    def test_tco_savings_positive_for_typical_case(self):
        tvo = calculate_tvo(**BASE)
        assert tvo.tco_savings > 0
        assert tvo.tco_savings_percent > 0

    def test_line_items_include_productivity(self):
        tvo = calculate_tvo(**BASE)
        labels = [item.label for item in tvo.tco_line_items]
        assert "Productivity & Operational Efficiency" in labels

    def test_yearly_cumulative_increases(self):
        tvo = calculate_tvo(**BASE)
        for i in range(1, len(tvo.yearly_getac_cumulative)):
            assert tvo.yearly_getac_cumulative[i] >= tvo.yearly_getac_cumulative[i - 1]
        for i in range(1, len(tvo.yearly_competitor_cumulative)):
            assert tvo.yearly_competitor_cumulative[i] >= tvo.yearly_competitor_cumulative[i - 1]

    def test_roi_payback_within_deployment(self):
        tvo = calculate_tvo(**BASE)
        assert 0 <= tvo.roi_payback_months <= BASE["deployment_years"] * 12

    def test_assumptions_list_populated(self):
        tvo = calculate_tvo(**BASE)
        assert len(tvo.assumptions) >= 5  # warranty, repair, plus factor assumptions
