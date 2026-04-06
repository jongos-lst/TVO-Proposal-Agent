"""Tests for chart generation functions."""

import os
from io import BytesIO

import pytest

from app.models.tvo import TVOCalculation, TCOLineItem, ProductivityFactor
from app.services.chart_generator import (
    generate_tco_comparison_chart,
    generate_total_tco_chart,
    generate_savings_breakdown_chart,
    generate_productivity_chart,
    generate_roi_timeline_chart,
    generate_cost_waterfall_chart,
    generate_risk_gauge_chart,
    generate_all_charts,
)


@pytest.fixture
def sample_tvo():
    """Build a minimal TVOCalculation with realistic data."""
    return TVOCalculation(
        fleet_size=150,
        deployment_years=5,
        hourly_productivity_value=65.0,
        tco_line_items=[
            TCOLineItem(label="Hardware Acquisition", formula="unit_price x 150",
                        getac_value=494850, competitor_value=329850, difference=-165000,
                        notes="One-time purchase cost"),
            TCOLineItem(label="Extended Warranty", formula="extra_years x $250/unit/year x 150",
                        getac_value=75000, competitor_value=150000, difference=75000,
                        notes="Warranty gap"),
            TCOLineItem(label="Repair & Replacement", formula="failure_rate x 150 x $520 x 5yr",
                        getac_value=7800, competitor_value=46800, difference=39000,
                        notes="Failure-driven repairs"),
            TCOLineItem(label="Productivity Loss", formula="failures x 18h x $65/h x 5yr",
                        getac_value=17550, competitor_value=105300, difference=87750,
                        notes="Downtime cost"),
        ],
        getac_total_tco=595200,
        competitor_total_tco=631950,
        tco_savings=36750,
        tco_savings_percent=5.8,
        getac_annual_downtime_hours=54.0,
        competitor_annual_downtime_hours=324.0,
        productivity_savings_annual=17550,
        productivity_savings_total=87750,
        getac_expected_failures=15.0,
        competitor_expected_failures=90.0,
        risk_reduction_percent=83.3,
        roi_payback_months=49.1,
        yearly_getac_cumulative=[514920.0, 534990.0, 555060.0, 575130.0, 595200.0],
        yearly_competitor_cumulative=[390270.0, 450690.0, 511110.0, 571530.0, 631950.0],
        productivity_breakdown=[
            ProductivityFactor(
                name="Downtime Avoidance",
                description="Fewer failures = fewer hours lost",
                formula="failure_diff x 18h x $65/h x 5yr",
                annual_value=17550, total_value=87750,
                applies=True,
                assumptions=["16h avg downtime per failure"],
            ),
            ProductivityFactor(
                name="Battery Continuity",
                description="Hot-swap eliminates shutdown for charging",
                formula="150 x 15min x $1.08/min x 250d x 5yr",
                annual_value=60937.5, total_value=304687.5,
                applies=True,
                assumptions=["15 min saved per battery swap per day"],
            ),
            ProductivityFactor(
                name="Display Readability",
                description="1400-nit sunlight-readable display",
                formula="150 x 60% x 20min x $1.08/min x 250d x 5yr",
                annual_value=48750, total_value=243750,
                applies=True,
                assumptions=["60% outdoor workers, 20 min/day lost"],
            ),
        ],
        total_value_advantage=36750,
        assumptions=["Extended warranty at $250/unit/year", "Repair cost $520/incident"],
    )


def _assert_valid_png(buf: BytesIO):
    """Assert the buffer contains a non-empty PNG."""
    assert isinstance(buf, BytesIO)
    assert buf.getbuffer().nbytes > 0
    buf.seek(0)
    assert buf.read(4) == b"\x89PNG"


class TestExistingCharts:
    def test_tco_comparison_returns_png(self, sample_tvo):
        buf = generate_tco_comparison_chart(sample_tvo)
        _assert_valid_png(buf)

    def test_total_tco_returns_png(self, sample_tvo):
        buf = generate_total_tco_chart(sample_tvo)
        _assert_valid_png(buf)

    def test_savings_breakdown_returns_png(self, sample_tvo):
        buf = generate_savings_breakdown_chart(sample_tvo)
        _assert_valid_png(buf)

    def test_productivity_returns_png(self, sample_tvo):
        buf = generate_productivity_chart(sample_tvo)
        _assert_valid_png(buf)


class TestNewCharts:
    def test_roi_timeline_returns_png(self, sample_tvo):
        buf = generate_roi_timeline_chart(sample_tvo)
        _assert_valid_png(buf)

    def test_cost_waterfall_returns_png(self, sample_tvo):
        buf = generate_cost_waterfall_chart(sample_tvo)
        _assert_valid_png(buf)

    def test_risk_gauge_returns_png(self, sample_tvo):
        buf = generate_risk_gauge_chart(sample_tvo)
        _assert_valid_png(buf)


class TestEdgeCases:
    def test_roi_no_crossover(self, sample_tvo):
        """Getac always more expensive (no crossover)."""
        tvo = sample_tvo.model_copy(update={
            "roi_payback_months": 60.0,  # = deployment_years * 12
            "yearly_getac_cumulative": [600000, 700000, 800000, 900000, 1000000],
            "yearly_competitor_cumulative": [300000, 400000, 500000, 600000, 700000],
        })
        buf = generate_roi_timeline_chart(tvo)
        _assert_valid_png(buf)

    def test_roi_immediate_payback(self, sample_tvo):
        """Getac cheaper from day 1."""
        tvo = sample_tvo.model_copy(update={
            "roi_payback_months": 0.0,
            "yearly_getac_cumulative": [200000, 220000, 240000, 260000, 280000],
            "yearly_competitor_cumulative": [300000, 400000, 500000, 600000, 700000],
        })
        buf = generate_roi_timeline_chart(tvo)
        _assert_valid_png(buf)

    def test_risk_gauge_zero_failures(self, sample_tvo):
        """Zero competitor failures edge case."""
        tvo = sample_tvo.model_copy(update={
            "risk_reduction_percent": 0.0,
            "getac_expected_failures": 0.0,
            "competitor_expected_failures": 0.0,
        })
        buf = generate_risk_gauge_chart(tvo)
        _assert_valid_png(buf)

    def test_risk_gauge_100_percent(self, sample_tvo):
        """Maximum risk reduction."""
        tvo = sample_tvo.model_copy(update={
            "risk_reduction_percent": 100.0,
            "getac_expected_failures": 0.0,
            "competitor_expected_failures": 90.0,
        })
        buf = generate_risk_gauge_chart(tvo)
        _assert_valid_png(buf)

    def test_savings_breakdown_no_savings(self, sample_tvo):
        """No positive savings items."""
        tvo = sample_tvo.model_copy(update={
            "tco_line_items": [
                TCOLineItem(label="Hardware", formula="", getac_value=500000,
                            competitor_value=300000, difference=-200000, notes=""),
            ],
            "productivity_savings_total": 0,
        })
        buf = generate_savings_breakdown_chart(tvo)
        assert isinstance(buf, BytesIO)  # may be empty, should not crash

    def test_waterfall_single_year(self, sample_tvo):
        """Single-year deployment."""
        tvo = sample_tvo.model_copy(update={
            "deployment_years": 1,
            "yearly_getac_cumulative": [520000.0],
            "yearly_competitor_cumulative": [390000.0],
        })
        buf = generate_cost_waterfall_chart(tvo)
        _assert_valid_png(buf)


class TestGenerateAll:
    def test_generates_7_chart_files(self, sample_tvo, tmp_path):
        charts = generate_all_charts(sample_tvo, str(tmp_path))
        assert len(charts) == 7
        expected_names = {
            "tco_comparison", "total_tco", "savings_breakdown", "productivity",
            "roi_timeline", "cost_waterfall", "risk_gauge",
        }
        assert set(charts.keys()) == expected_names
        for path in charts.values():
            assert os.path.exists(path)
            assert os.path.getsize(path) > 0
