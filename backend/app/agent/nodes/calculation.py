import json
import re
from langchain_core.messages import SystemMessage
from app.agent.state import AgentState
from app.agent.prompts import CALCULATION_SYSTEM_PROMPT
from app.services.llm import get_llm
from app.services.tvo_calculator import calculate_tvo
from app.services.product_catalog import get_competitor, get_all_competitors


async def calculation_node(state: AgentState) -> dict:
    """Phase 03: TVO/TCO value calculation for all selected products."""
    llm = get_llm()
    persona = state.get("persona")
    selected_products = state.get("selected_products") or []
    messages = state["messages"]

    fleet_size = state.get("fleet_size") or (persona.fleet_size if persona else None) or 100
    deployment_years = state.get("deployment_years") or 5

    competitor_names = state.get("competitor_product_names") or {}
    all_competitors = get_all_competitors()

    # Calculate TVO for each selected product
    tvo_results: dict[str, object] = {}
    product_summaries = []
    competitor_summaries = []

    for product in selected_products:
        # Find competitor for this product
        comp_name = competitor_names.get(product.id, "")
        competitor = None
        for c in all_competitors:
            if any(part.lower() in comp_name.lower() for part in c.name.lower().split()):
                competitor = c
                break
        if not competitor and all_competitors:
            competitor = all_competitors[0]

        # Extract feature flags for productivity factors
        features = getattr(product, "key_features", None) or []
        has_hot_swap = any("hot-swap" in f.lower() for f in features)
        display_brightness = getattr(product, "display_brightness", "") or ""
        nits_match = re.search(r"(\d+)\s*nit", display_brightness, re.I)
        getac_nits = int(nits_match.group(1)) if nits_match else 600
        has_wifi7 = any("wi-fi 7" in f.lower() or "802.11be" in f.lower() for f in features)
        rugged = getattr(product, "rugged_rating", "") or ""
        ip_match = re.search(r"IP(\d{2})", rugged)
        getac_ip = int(ip_match.group(1)) if ip_match else 53

        comp_brightness = getattr(competitor, "display_brightness", "") or "" if competitor else ""
        comp_nits_m = re.search(r"(\d+)\s*nit", comp_brightness, re.I)
        comp_nits = int(comp_nits_m.group(1)) if comp_nits_m else 600
        comp_rugged = getattr(competitor, "rugged_rating", "") or "" if competitor else ""
        comp_ip_m = re.search(r"IP(\d{2})", comp_rugged)
        comp_ip = int(comp_ip_m.group(1)) if comp_ip_m else 53

        # Run TVO calculation
        if product and competitor:
            tvo_result = calculate_tvo(
                getac_unit_price=product.base_price,
                getac_warranty_years=int(product.warranty_standard[0]),
                getac_failure_rate=product.annual_failure_rate,
                competitor_unit_price=competitor.base_price,
                competitor_warranty_years=int(competitor.warranty_standard[0]),
                competitor_failure_rate=competitor.annual_failure_rate,
                fleet_size=fleet_size,
                deployment_years=deployment_years,
                getac_has_hot_swap=has_hot_swap,
                getac_display_nits=getac_nits,
                competitor_display_nits=comp_nits,
                getac_ip_rating=getac_ip,
                competitor_ip_rating=comp_ip,
                getac_has_wifi7=has_wifi7,
                competitor_has_wifi7=False,
            )
            tvo_results[product.id] = tvo_result

            product_summaries.append(
                f"**{product.name}** (id: {product.id}) — ${product.base_price:,.0f}, {product.category}, "
                f"Failure rate: {product.annual_failure_rate*100:.1f}%"
            )
            competitor_summaries.append(
                f"vs. **{competitor.name}** — ${competitor.base_price:,.0f}, {competitor.category}, "
                f"Failure rate: {competitor.annual_failure_rate*100:.1f}%"
            )

    # Build prompt context
    if persona:
        pd = persona.model_dump()
        persona_summary = "\n".join(
            f"  {k.replace('_', ' ').title()}: {v}" for k, v in pd.items() if v is not None and v != []
        )
    else:
        persona_summary = "N/A"

    # Build TVO display for all products
    tvo_sections = []
    for product in selected_products:
        tvo = tvo_results.get(product.id)
        if not tvo:
            continue
        lines = [f"\n━━━ {product.name} ━━━"]
        lines.append(f"Fleet Size: {tvo.fleet_size} | Deployment: {tvo.deployment_years} years\n")
        lines.append("TCO BREAKDOWN:")
        for item in tvo.tco_line_items:
            lines.append(f"  {item.label}:")
            lines.append(f"    Formula: {item.formula}")
            lines.append(f"    Getac: ${item.getac_value:,.0f} | Competitor: ${item.competitor_value:,.0f} | Savings: ${item.difference:,.0f}")
            lines.append(f"    Note: {item.notes}")
        lines.append(f"\nTOTAL TCO — Getac: ${tvo.getac_total_tco:,.0f} | Competitor: ${tvo.competitor_total_tco:,.0f}")
        lines.append(f"TOTAL SAVINGS: ${tvo.tco_savings:,.0f} ({tvo.tco_savings_percent:.1f}%)")
        lines.append(f"\nPRODUCTIVITY & OPERATIONAL EFFICIENCY: ${tvo.productivity_savings_total:,.0f} over {tvo.deployment_years} years")
        if tvo.productivity_breakdown:
            for factor in tvo.productivity_breakdown:
                if factor.applies:
                    lines.append(f"  {factor.name}: ${factor.total_value:,.0f}")
                    lines.append(f"    Formula: {factor.formula}")
                    lines.append(f"    {factor.description}")
        lines.append(f"\nRisk Reduction: {tvo.risk_reduction_percent:.1f}% fewer expected failures")
        lines.append(f"\nAssumptions: {'; '.join(tvo.assumptions)}")
        tvo_sections.append("\n".join(lines))

    tvo_display = "\n\n".join(tvo_sections) if tvo_sections else "Calculation pending..."

    system = CALCULATION_SYSTEM_PROMPT.format(
        persona_summary=persona_summary,
        products_summary="\n".join(f"  {i+1}. {s}" for i, s in enumerate(product_summaries)) or "N/A",
        competitors_summary="\n".join(f"  {i+1}. {s}" for i, s in enumerate(competitor_summaries)) or "N/A",
        tvo_results=tvo_display,
        deployment_years=deployment_years,
        product_count=len(selected_products),
    )

    recent_messages = list(messages)[-6:]
    response = await llm.ainvoke([SystemMessage(content=system)] + recent_messages)

    return {
        "messages": [response],
        "tvo_results": tvo_results,
        "fleet_size": fleet_size,
        "deployment_years": deployment_years,
        "current_phase": "calculation",
    }
