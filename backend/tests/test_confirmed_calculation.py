"""Tests for the confirmed calculation endpoint and competitors endpoint."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.product_catalog import load_catalog


@pytest.fixture(scope="module", autouse=True)
def _load_catalog():
    """Ensure product catalog is loaded before tests."""
    load_catalog()


@pytest.fixture
def client():
    return TestClient(app)


class TestCompetitorsEndpoint:
    def test_list_competitors(self, client):
        response = client.get("/api/competitors")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        # Check structure
        comp = data[0]
        assert "name" in comp
        assert "base_price" in comp
        assert "annual_failure_rate" in comp
        assert "warranty_standard" in comp


class TestConfirmedCalculation:
    def test_calculate_with_single_product(self, client):
        # First initialize a session via intake
        session_id = "test-confirm-001"
        intake_response = client.post("/api/intake", json={
            "session_id": session_id,
            "pain_points": ["device failures"],
            "use_scenarios": ["field service"],
            "budget_amount": 500000,
            "service_warranty_needs": "3-year",
            "current_devices": ["Dell Latitude"],
        })
        assert intake_response.status_code == 200

        # Now run confirmed calculation
        response = client.post("/api/calculate-confirmed", json={
            "session_id": session_id,
            "fleet_size": 100,
            "deployment_years": 5,
            "products": [{
                "product_id": "b360",
                "product_name": "Getac B360",
                "unit_price": 3299.0,
                "warranty_years": 3,
                "failure_rate": 0.02,
                "competitor_name": "Dell Latitude 5430",
                "competitor_price": 2199.0,
                "competitor_warranty_years": 1,
                "competitor_failure_rate": 0.12,
            }],
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["phase"] == "calculation"
        assert "b360" in data["tvo_results"]

        tvo = data["tvo_results"]["b360"]
        assert tvo["fleet_size"] == 100
        assert tvo["deployment_years"] == 5
        assert tvo["tco_savings"] > 0

    def test_calculate_with_custom_fleet_size(self, client):
        session_id = "test-confirm-002"
        client.post("/api/intake", json={
            "session_id": session_id,
            "pain_points": ["failures"],
            "use_scenarios": ["warehouse"],
            "budget_amount": 300000,
            "service_warranty_needs": "5-year",
            "current_devices": ["iPad"],
        })

        response = client.post("/api/calculate-confirmed", json={
            "session_id": session_id,
            "fleet_size": 200,
            "deployment_years": 3,
            "products": [{
                "product_id": "f110",
                "product_name": "Getac F110",
                "unit_price": 2499.0,
                "warranty_years": 3,
                "failure_rate": 0.03,
                "competitor_name": "Samsung Galaxy Tab",
                "competitor_price": 1200.0,
                "competitor_warranty_years": 1,
                "competitor_failure_rate": 0.15,
            }],
        })
        data = response.json()
        assert data["success"] is True
        tvo = data["tvo_results"]["f110"]
        assert tvo["fleet_size"] == 200
        assert tvo["deployment_years"] == 3

    def test_calculate_with_multiple_products(self, client):
        session_id = "test-confirm-003"
        client.post("/api/intake", json={
            "session_id": session_id,
            "pain_points": ["multiple issues"],
            "use_scenarios": ["field + office"],
            "budget_amount": 1000000,
            "service_warranty_needs": "5-year",
            "current_devices": ["Dell Latitude", "iPad"],
        })

        response = client.post("/api/calculate-confirmed", json={
            "session_id": session_id,
            "fleet_size": 150,
            "deployment_years": 5,
            "products": [
                {
                    "product_id": "b360",
                    "product_name": "Getac B360",
                    "unit_price": 3299.0,
                    "warranty_years": 3,
                    "failure_rate": 0.02,
                    "competitor_name": "Dell Latitude",
                    "competitor_price": 2199.0,
                    "competitor_warranty_years": 1,
                    "competitor_failure_rate": 0.12,
                },
                {
                    "product_id": "f110",
                    "product_name": "Getac F110",
                    "unit_price": 2499.0,
                    "warranty_years": 3,
                    "failure_rate": 0.03,
                    "competitor_name": "iPad Pro",
                    "competitor_price": 1200.0,
                    "competitor_warranty_years": 1,
                    "competitor_failure_rate": 0.15,
                },
            ],
        })
        data = response.json()
        assert data["success"] is True
        assert "b360" in data["tvo_results"]
        assert "f110" in data["tvo_results"]

    def test_calculate_with_all_params(self, client):
        """Verify all TVO calculator parameters are passed through."""
        session_id = "test-confirm-005"
        client.post("/api/intake", json={
            "session_id": session_id,
            "pain_points": ["failures"],
            "use_scenarios": ["outdoor"],
            "budget_amount": 500000,
            "service_warranty_needs": "5-year",
            "current_devices": ["Dell"],
        })

        response = client.post("/api/calculate-confirmed", json={
            "session_id": session_id,
            "fleet_size": 100,
            "deployment_years": 5,
            "hourly_productivity_value": 75.0,
            "avg_downtime_hours_per_failure": 20.0,
            "annual_repair_cost": 600.0,
            "products": [{
                "product_id": "b360",
                "product_name": "Getac B360",
                "unit_price": 3299.0,
                "warranty_years": 3,
                "failure_rate": 0.02,
                "competitor_name": "Dell Latitude 5430",
                "competitor_price": 2199.0,
                "competitor_warranty_years": 1,
                "competitor_failure_rate": 0.12,
                "has_hot_swap": True,
                "display_nits": 1400,
                "competitor_display_nits": 300,
                "ip_rating": 66,
                "competitor_ip_rating": 53,
                "has_wifi7": True,
                "competitor_has_wifi7": False,
            }],
        })
        data = response.json()
        assert data["success"] is True
        tvo = data["tvo_results"]["b360"]
        assert tvo["hourly_productivity_value"] == 75.0
        # All 5 productivity factors should apply
        breakdown = tvo.get("productivity_breakdown", [])
        applicable = [f for f in breakdown if f["applies"]]
        assert len(applicable) == 5

    def test_calculate_with_disabled_features(self, client):
        """Verify feature flags disable productivity factors."""
        session_id = "test-confirm-006"
        client.post("/api/intake", json={
            "session_id": session_id,
            "pain_points": ["test"],
            "use_scenarios": ["test"],
            "budget_amount": 100000,
            "service_warranty_needs": "basic",
            "current_devices": ["test"],
        })

        response = client.post("/api/calculate-confirmed", json={
            "session_id": session_id,
            "fleet_size": 100,
            "deployment_years": 5,
            "products": [{
                "product_id": "b360",
                "product_name": "Getac B360",
                "unit_price": 3299.0,
                "warranty_years": 3,
                "failure_rate": 0.02,
                "competitor_name": "Dell Latitude",
                "competitor_price": 2199.0,
                "competitor_warranty_years": 1,
                "competitor_failure_rate": 0.12,
                "has_hot_swap": False,
                "display_nits": 600,
                "competitor_display_nits": 600,
                "ip_rating": 53,
                "competitor_ip_rating": 53,
                "has_wifi7": False,
                "competitor_has_wifi7": False,
            }],
        })
        data = response.json()
        assert data["success"] is True
        tvo = data["tvo_results"]["b360"]
        breakdown = tvo.get("productivity_breakdown", [])
        # Only downtime avoidance should apply (failure rates differ)
        applicable = [f for f in breakdown if f["applies"]]
        assert len(applicable) == 1
        assert applicable[0]["name"] == "Downtime Avoidance"

    def test_calculate_empty_products(self, client):
        session_id = "test-confirm-004"
        client.post("/api/intake", json={
            "session_id": session_id,
            "pain_points": ["test"],
            "use_scenarios": ["test"],
            "budget_amount": 100000,
            "service_warranty_needs": "basic",
            "current_devices": ["test"],
        })

        response = client.post("/api/calculate-confirmed", json={
            "session_id": session_id,
            "fleet_size": 100,
            "deployment_years": 5,
            "products": [],
        })
        data = response.json()
        assert data["success"] is True
        assert data["tvo_results"] == {}
