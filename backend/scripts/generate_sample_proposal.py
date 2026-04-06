#!/usr/bin/env python3
"""
Standalone pipeline: generate a complete TVO Proposal PowerPoint with sample data.

Usage:
    cd backend
    source venv/bin/activate
    python -m scripts.generate_sample_proposal

Output: backend/output/TVO_Proposal_Sample.pptx
"""

import os
import sys

# Add backend to path so app imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.persona import CustomerPersona
from app.models.product import GetacProduct
from app.models.tvo import TVOCalculation
from app.models.proposal import Proposal
from app.services.tvo_calculator import calculate_tvo
from app.services.pptx_generator import generate_proposal_pptx


def build_sample_proposal() -> Proposal:
    """Build a realistic sample proposal for demo purposes."""

    # Phase 1: Customer persona
    persona = CustomerPersona(
        customer_name="Pacific Northwest Utilities Corp",
        industry="Utilities & Energy",
        pain_points=[
            "Field tablets fail frequently in rain/cold conditions",
            "Consumer laptops averaging 15% annual failure rate",
            "16+ hours downtime per device failure costs productivity",
            "No hot-swap battery — crews lose time returning to depot",
            "Warranty gaps lead to $450+ unplanned repair costs",
        ],
        use_scenarios=[
            "Substation inspection and maintenance logging",
            "Real-time GIS mapping in remote terrain",
            "Work order management in extreme weather",
            "Crew dispatch and safety compliance tracking",
        ],
        budget_amount=650000.0,
        service_warranty_needs="5-year bumper-to-bumper with next-day replacement",
        current_devices=["Dell Latitude 5430 Rugged", "Aging Panasonic CF-33"],
        fleet_size=150,
        deployment_timeline="Q3 2026 rollout",
    )

    # Phase 2: Product recommendation
    product = GetacProduct(
        id="b360",
        name="Getac B360",
        category="Fully Rugged Laptop",
        base_price=3299.00,
        display_size="13.3 inch FHD",
        processor="Intel Core i7-1265U (12th Gen)",
        ram_options=["8GB", "16GB", "32GB", "64GB"],
        storage_options=["256GB SSD", "512GB SSD", "1TB SSD", "2TB SSD"],
        rugged_rating="MIL-STD-810H, IP66",
        operating_temp="-29°C to 63°C",
        battery_life="Up to 12.5 hours (dual hot-swappable batteries)",
        warranty_standard="3-year bumper-to-bumper",
        warranty_options=["5-year bumper-to-bumper", "Accidental damage coverage", "Next-day replacement"],
        key_features=[
            "Hot-swappable dual batteries for zero-downtime",
            "Sunlight-readable 1400 nit display",
            "LTE/5G connectivity options",
            "Built-in barcode reader option",
            "Thunderbolt 4 docking support",
            "Windows Hello facial recognition",
        ],
        target_industries=["Field Service", "Utilities", "Oil & Gas", "Manufacturing", "Public Safety"],
        annual_failure_rate=0.02,
    )

    competitive_advantages = [
        "2% failure rate vs 12% for Dell Latitude 5430 in field conditions — 83% fewer failures",
        "IP66 fully sealed — operates in heavy rain, dust, and extreme temps",
        "Hot-swappable dual batteries eliminate depot trips for charging",
        "1400 nit sunlight-readable display vs 1000 nit competitor screens",
        "3-year bumper-to-bumper warranty included (vs limited hardware-only)",
        "MIL-STD-810H certified for 6-foot drops onto concrete",
        "Thunderbolt 4 docking for seamless office/field transitions",
        "Lower 5-year TCO despite higher initial unit price",
    ]

    # Phase 3: TVO calculation
    # Dell 5430 Rugged has 3-year limited (not bumper-to-bumper) and 8% failure rate.
    # With 150 units over 5 years, higher failures + downtime + warranty gaps erode savings.
    tvo = calculate_tvo(
        getac_unit_price=3299.00,
        getac_warranty_years=3,
        getac_failure_rate=0.02,
        competitor_unit_price=2199.00,
        competitor_warranty_years=1,       # Dell limited warranty effectively 1yr for accidental
        competitor_failure_rate=0.12,      # Semi-rugged in harsh field conditions
        fleet_size=150,
        deployment_years=5,
        hourly_productivity_value=65.0,    # Utility worker productivity value
        avg_downtime_hours_per_failure=18.0,
        annual_repair_cost=520.0,
    )

    # Phase 4: Value proposition
    value_proposition = (
        "By deploying the Getac B360 across your 150-unit fleet, Pacific Northwest Utilities Corp "
        "will reduce total cost of ownership by over $600K across 5 years — driven by 75% fewer "
        "device failures, eliminated downtime from hot-swappable batteries, and comprehensive "
        "bumper-to-bumper warranty coverage. The rugged IP66 design ensures reliable operation "
        "in the harsh Pacific Northwest conditions your crews face daily, while the 1400-nit "
        "sunlight-readable display and LTE/5G connectivity keep teams productive in the field."
    )

    return Proposal(
        id="sample-pnw-utilities-2026",
        status="approved",
        persona=persona,
        selected_products=[product],
        competitor_product_names={product.id: "Dell Latitude 5430 Rugged"},
        competitive_advantages={product.id: competitive_advantages},
        tvo_calculations={product.id: tvo},
        value_proposition=value_proposition,
    )


def main():
    print("=" * 60)
    print("  TVO Proposal Agent — PowerPoint Generation Pipeline")
    print("=" * 60)

    # Build sample proposal
    print("\n[1/4] Building sample proposal data...")
    proposal = build_sample_proposal()
    print(f"  Customer : {proposal.persona.customer_name}")
    print(f"  Industry : {proposal.persona.industry}")
    print(f"  Products : {', '.join(p.name for p in proposal.selected_products)}")
    print(f"  Fleet    : {proposal.persona.fleet_size} units")
    print(f"  Competitors: {', '.join(proposal.competitor_product_names.values())}")

    # Show TVO summary (first product)
    first_product = proposal.selected_products[0]
    tvo = proposal.tvo_calculations[first_product.id]
    print("\n[2/4] TVO Calculation Results:")
    print(f"  Getac Total TCO      : ${tvo.getac_total_tco:>12,.2f}")
    print(f"  Competitor Total TCO : ${tvo.competitor_total_tco:>12,.2f}")
    print(f"  TCO Savings          : ${tvo.tco_savings:>12,.2f} ({tvo.tco_savings_percent:.1f}%)")
    print(f"  Productivity Savings : ${tvo.productivity_savings_total:>12,.2f}")
    print(f"  Risk Reduction       : {tvo.risk_reduction_percent:.1f}%")

    print("\n  TCO Line Items:")
    for item in tvo.tco_line_items:
        print(f"    {item.label:<28} Getac: ${item.getac_value:>10,.0f}  |  Competitor: ${item.competitor_value:>10,.0f}  |  Δ ${item.difference:>10,.0f}")

    # Generate charts + PPTX
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output")
    os.makedirs(output_dir, exist_ok=True)

    print(f"\n[3/4] Generating charts to {output_dir}/charts/ ...")
    pptx_buffer = generate_proposal_pptx(proposal, output_dir=os.path.join(output_dir, "charts"))

    pptx_path = os.path.join(output_dir, "TVO_Proposal_Sample.pptx")
    with open(pptx_path, "wb") as f:
        f.write(pptx_buffer.read())

    print(f"\n[4/4] PowerPoint saved!")
    print(f"  📄 {pptx_path}")
    file_size = os.path.getsize(pptx_path) / 1024
    print(f"  Size: {file_size:.1f} KB")

    # List generated charts
    charts_dir = os.path.join(output_dir, "charts")
    if os.path.isdir(charts_dir):
        chart_files = [f for f in os.listdir(charts_dir) if f.endswith(".png")]
        print(f"\n  Charts generated ({len(chart_files)}):")
        for cf in sorted(chart_files):
            size = os.path.getsize(os.path.join(charts_dir, cf)) / 1024
            print(f"    📊 {cf} ({size:.0f} KB)")

    print("\n" + "=" * 60)
    print("  10-slide deck (Getac corporate theme):")
    print("    1.  Title / Cover")
    print("    2.  Executive Summary (KPIs + Value Proposition)")
    print("    3.  Customer Situation & Challenges")
    print("    4.  Recommended Solution (Getac B360)")
    print("    5.  TCO Analysis (data table + chart)")
    print("    6.  ROI & Savings Analysis")
    print("    7.  Risk & Reliability")
    print("    8.  Competitive Differentiation")
    print("    9.  Conclusion & Next Steps")
    print("   10.  Thank You")
    print("=" * 60)
    print("\nDone! Open the .pptx file to review.\n")


if __name__ == "__main__":
    main()
