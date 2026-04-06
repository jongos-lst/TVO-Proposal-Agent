from app.models.tvo import TVOCalculation, TCOLineItem, ProductivityFactor


def calculate_tvo(
    getac_unit_price: float,
    getac_warranty_years: int,
    getac_failure_rate: float,
    competitor_unit_price: float,
    competitor_warranty_years: int,
    competitor_failure_rate: float,
    fleet_size: int,
    deployment_years: int,
    hourly_productivity_value: float = 50.0,
    avg_downtime_hours_per_failure: float = 16.0,
    annual_repair_cost: float = 450.0,
    # Product feature flags for productivity factors
    getac_has_hot_swap: bool = True,
    getac_display_nits: int = 1400,
    competitor_display_nits: int = 600,
    getac_ip_rating: int = 66,
    competitor_ip_rating: int = 53,
    getac_has_wifi7: bool = True,
    competitor_has_wifi7: bool = False,
) -> TVOCalculation:
    """Pure-function TVO/TCO calculation. No LLM dependency. Fully explainable."""

    line_items: list[TCOLineItem] = []
    assumptions: list[str] = []

    # --- 1. Hardware Acquisition Cost ---
    getac_hw = getac_unit_price * fleet_size
    comp_hw = competitor_unit_price * fleet_size
    line_items.append(TCOLineItem(
        label="Hardware Acquisition",
        formula=f"unit_price x {fleet_size} devices",
        getac_value=getac_hw,
        competitor_value=comp_hw,
        difference=comp_hw - getac_hw,
        notes="One-time purchase cost for the entire fleet",
    ))

    # --- 2. Extended Warranty Cost ---
    # Getac includes bumper-to-bumper; competitor may need extended warranty purchase
    extra_warranty_years = max(0, deployment_years - competitor_warranty_years)
    warranty_cost_per_unit_per_year = 250.0
    getac_warranty_cost = 0.0  # included in bumper-to-bumper for standard term
    getac_extra = max(0, deployment_years - getac_warranty_years)
    if getac_extra > 0:
        getac_warranty_cost = getac_extra * warranty_cost_per_unit_per_year * fleet_size

    comp_warranty_cost = extra_warranty_years * warranty_cost_per_unit_per_year * fleet_size
    line_items.append(TCOLineItem(
        label="Extended Warranty",
        formula=f"extra_years x ${warranty_cost_per_unit_per_year}/unit/year x {fleet_size} devices",
        getac_value=getac_warranty_cost,
        competitor_value=comp_warranty_cost,
        difference=comp_warranty_cost - getac_warranty_cost,
        notes=f"Getac includes {getac_warranty_years}-year bumper-to-bumper; competitor has {competitor_warranty_years}-year base",
    ))
    assumptions.append(f"Extended warranty cost estimated at ${warranty_cost_per_unit_per_year}/unit/year")

    # --- 3. Repair & Replacement Costs ---
    getac_failures_annual = getac_failure_rate * fleet_size
    comp_failures_annual = competitor_failure_rate * fleet_size
    getac_repair_total = getac_failures_annual * annual_repair_cost * deployment_years
    comp_repair_total = comp_failures_annual * annual_repair_cost * deployment_years
    line_items.append(TCOLineItem(
        label="Repair & Replacement",
        formula=f"failure_rate x {fleet_size} x ${annual_repair_cost}/repair x {deployment_years} years",
        getac_value=getac_repair_total,
        competitor_value=comp_repair_total,
        difference=comp_repair_total - getac_repair_total,
        notes=f"Getac failure rate: {getac_failure_rate*100:.1f}%, Competitor: {competitor_failure_rate*100:.1f}%",
    ))
    assumptions.append(f"Average repair/replacement cost: ${annual_repair_cost} per incident")

    # --- 4. Productivity & Operational Efficiency (5-factor model) ---
    working_days_per_year = 250
    hourly_rate = hourly_productivity_value
    productivity_factors = _calculate_productivity_factors(
        fleet_size=fleet_size,
        deployment_years=deployment_years,
        hourly_rate=hourly_rate,
        working_days_per_year=working_days_per_year,
        getac_failures_annual=getac_failures_annual,
        comp_failures_annual=comp_failures_annual,
        avg_downtime_hours_per_failure=avg_downtime_hours_per_failure,
        annual_repair_cost=annual_repair_cost,
        getac_has_hot_swap=getac_has_hot_swap,
        getac_display_nits=getac_display_nits,
        competitor_display_nits=competitor_display_nits,
        getac_ip_rating=getac_ip_rating,
        competitor_ip_rating=competitor_ip_rating,
        getac_has_wifi7=getac_has_wifi7,
        competitor_has_wifi7=competitor_has_wifi7,
    )

    # Aggregate productivity values
    productivity_savings_annual = sum(
        f.annual_value for f in productivity_factors if f.applies
    )
    productivity_savings_total = sum(
        f.total_value for f in productivity_factors if f.applies
    )

    # Downtime numbers (from factor 1) for backward compat fields
    getac_downtime_annual = getac_failures_annual * avg_downtime_hours_per_failure
    comp_downtime_annual = comp_failures_annual * avg_downtime_hours_per_failure

    # TCO line item uses aggregate of all factors
    getac_downtime_cost = getac_downtime_annual * hourly_rate * deployment_years
    comp_productivity_cost = getac_downtime_cost + productivity_savings_total
    line_items.append(TCOLineItem(
        label="Productivity & Operational Efficiency",
        formula=f"Sum of {sum(1 for f in productivity_factors if f.applies)} productivity factors over {deployment_years} years",
        getac_value=getac_downtime_cost,
        competitor_value=getac_downtime_cost + productivity_savings_total,
        difference=productivity_savings_total,
        notes=f"Includes: {', '.join(f.name for f in productivity_factors if f.applies)}",
    ))

    # Add per-factor assumptions
    for factor in productivity_factors:
        if factor.applies:
            for a in factor.assumptions:
                assumptions.append(a)
    assumptions.append(f"Worker productivity value: ${hourly_rate}/hour")
    assumptions.append(f"Working days per year: {working_days_per_year}")

    # --- Totals ---
    getac_tco = getac_hw + getac_warranty_cost + getac_repair_total + getac_downtime_cost
    comp_tco = comp_hw + comp_warranty_cost + comp_repair_total + comp_productivity_cost
    tco_savings = comp_tco - getac_tco
    tco_savings_pct = (tco_savings / comp_tco * 100) if comp_tco > 0 else 0

    # Risk
    getac_failures_total = getac_failures_annual * deployment_years
    comp_failures_total = comp_failures_annual * deployment_years
    risk_reduction = ((comp_failures_total - getac_failures_total) / comp_failures_total * 100) if comp_failures_total > 0 else 0

    assumptions.append(f"Deployment period: {deployment_years} years")
    assumptions.append(f"Fleet size: {fleet_size} devices")

    # --- Year-by-year cumulative costs ---
    getac_annual_recurring = (
        (getac_warranty_cost / deployment_years if deployment_years > 0 else 0)
        + getac_failures_annual * annual_repair_cost
        + getac_downtime_annual * hourly_rate
    )
    comp_annual_recurring = (
        (comp_warranty_cost / deployment_years if deployment_years > 0 else 0)
        + comp_failures_annual * annual_repair_cost
        + comp_downtime_annual * hourly_rate
        + (productivity_savings_annual - (comp_downtime_annual - getac_downtime_annual) * hourly_rate)
    )

    yearly_getac = []
    yearly_comp = []
    for yr in range(1, deployment_years + 1):
        yearly_getac.append(round(getac_hw + getac_annual_recurring * yr, 2))
        yearly_comp.append(round(comp_hw + comp_annual_recurring * yr, 2))

    # --- ROI payback: month when Getac cumulative <= Competitor cumulative ---
    roi_months = float(deployment_years * 12)  # default: no payback within period
    if getac_hw <= comp_hw:
        roi_months = 0.0  # Getac cheaper upfront
    else:
        monthly_savings = (comp_annual_recurring - getac_annual_recurring) / 12
        if monthly_savings > 0:
            price_gap = getac_hw - comp_hw
            roi_months = min(price_gap / monthly_savings, deployment_years * 12)
        # else: competitor recurring costs lower — no payback

    return TVOCalculation(
        fleet_size=fleet_size,
        deployment_years=deployment_years,
        hourly_productivity_value=hourly_productivity_value,
        tco_line_items=line_items,
        getac_total_tco=round(getac_tco, 2),
        competitor_total_tco=round(comp_tco, 2),
        tco_savings=round(tco_savings, 2),
        tco_savings_percent=round(tco_savings_pct, 1),
        getac_annual_downtime_hours=round(getac_downtime_annual, 1),
        competitor_annual_downtime_hours=round(comp_downtime_annual, 1),
        productivity_savings_annual=round(productivity_savings_annual, 2),
        productivity_savings_total=round(productivity_savings_total, 2),
        getac_expected_failures=round(getac_failures_total, 1),
        competitor_expected_failures=round(comp_failures_total, 1),
        risk_reduction_percent=round(risk_reduction, 1),
        roi_payback_months=round(roi_months, 1),
        yearly_getac_cumulative=yearly_getac,
        yearly_competitor_cumulative=yearly_comp,
        productivity_breakdown=productivity_factors,
        total_value_advantage=round(tco_savings, 2),
        assumptions=assumptions,
    )


def _calculate_productivity_factors(
    *,
    fleet_size: int,
    deployment_years: int,
    hourly_rate: float,
    working_days_per_year: int,
    getac_failures_annual: float,
    comp_failures_annual: float,
    avg_downtime_hours_per_failure: float,
    annual_repair_cost: float,
    getac_has_hot_swap: bool,
    getac_display_nits: int,
    competitor_display_nits: int,
    getac_ip_rating: int,
    competitor_ip_rating: int,
    getac_has_wifi7: bool,
    competitor_has_wifi7: bool,
) -> list[ProductivityFactor]:
    """Compute 5 productivity factors with full explainability."""
    factors: list[ProductivityFactor] = []
    minute_rate = hourly_rate / 60

    # ── Factor 1: Downtime Avoidance ──
    # Fewer failures = fewer hours of worker idle time
    failure_diff = comp_failures_annual - getac_failures_annual
    downtime_annual = failure_diff * avg_downtime_hours_per_failure * hourly_rate
    downtime_total = downtime_annual * deployment_years
    factors.append(ProductivityFactor(
        name="Downtime Avoidance",
        description="Lower failure rate means fewer hours of worker idle time waiting for device repair or replacement",
        formula=(
            f"({comp_failures_annual:.1f} - {getac_failures_annual:.1f}) failures/yr "
            f"x {avg_downtime_hours_per_failure}h x ${hourly_rate}/h x {deployment_years}yr"
        ),
        annual_value=round(max(downtime_annual, 0), 2),
        total_value=round(max(downtime_total, 0), 2),
        applies=failure_diff > 0,
        assumptions=[
            f"Average downtime per device failure: {avg_downtime_hours_per_failure} hours",
            f"Includes logistics, repair/replacement, data restoration, and re-deployment",
        ],
    ))

    # ── Factor 2: Battery Continuity ──
    # Hot-swappable batteries eliminate shutdown-for-charging downtime
    battery_swap_minutes_saved = 15.0  # minutes saved per device per day
    battery_annual = fleet_size * (battery_swap_minutes_saved * minute_rate) * working_days_per_year
    battery_total = battery_annual * deployment_years
    battery_applies = getac_has_hot_swap
    factors.append(ProductivityFactor(
        name="Battery Continuity",
        description="Hot-swappable batteries eliminate shutdown for charging — workers never pause for power",
        formula=(
            f"{fleet_size} devices x {battery_swap_minutes_saved} min/day "
            f"x ${minute_rate:.2f}/min x {working_days_per_year} days x {deployment_years}yr"
        ),
        annual_value=round(battery_annual if battery_applies else 0, 2),
        total_value=round(battery_total if battery_applies else 0, 2),
        applies=battery_applies,
        assumptions=[
            f"Hot-swap saves {battery_swap_minutes_saved} min per device per day vs shutdown-to-charge",
            f"{working_days_per_year} working days per year",
        ],
    ))

    # ── Factor 3: Display Readability ��─
    # Sunlight-readable display reduces time spent repositioning or shading screen
    outdoor_worker_pct = 0.4  # 40% of fleet deployed primarily outdoors
    time_lost_minutes = 8.0   # minutes per day lost to poor screen visibility
    nit_advantage = getac_display_nits > competitor_display_nits
    display_applies = nit_advantage and getac_display_nits >= 1000
    display_annual = (
        fleet_size * outdoor_worker_pct * (time_lost_minutes * minute_rate) * working_days_per_year
    )
    display_total = display_annual * deployment_years
    factors.append(ProductivityFactor(
        name="Display Readability",
        description=(
            f"Sunlight-readable {getac_display_nits}-nit display reduces time lost "
            f"to screen glare vs {competitor_display_nits}-nit competitor"
        ),
        formula=(
            f"{fleet_size} devices x {outdoor_worker_pct:.0%} outdoor "
            f"x {time_lost_minutes} min/day x ${minute_rate:.2f}/min "
            f"x {working_days_per_year} days x {deployment_years}yr"
        ),
        annual_value=round(display_annual if display_applies else 0, 2),
        total_value=round(display_total if display_applies else 0, 2),
        applies=display_applies,
        assumptions=[
            f"{outdoor_worker_pct:.0%} of fleet deployed in outdoor/high-glare environments",
            f"Workers lose ~{time_lost_minutes} min/day to shading, squinting, or relocating with low-brightness screens",
            f"Getac: {getac_display_nits} nits vs Competitor: {competitor_display_nits} nits",
        ],
    ))

    # ── Factor 4: Environmental Resilience ──
    # Higher IP rating = fewer environment-caused incidents beyond standard failure rate
    ip_advantage = getac_ip_rating > competitor_ip_rating
    env_incident_rate_reduction = 0.03  # 3% of fleet avoids environmental damage per year
    cost_per_env_incident = annual_repair_cost + (avg_downtime_hours_per_failure * hourly_rate)
    resilience_annual = fleet_size * env_incident_rate_reduction * cost_per_env_incident
    resilience_total = resilience_annual * deployment_years
    factors.append(ProductivityFactor(
        name="Environmental Resilience",
        description=(
            f"IP{getac_ip_rating} protection prevents water/dust damage incidents "
            f"that IP{competitor_ip_rating}-rated devices would suffer"
        ),
        formula=(
            f"{fleet_size} devices x {env_incident_rate_reduction:.0%} incident reduction "
            f"x ${cost_per_env_incident:,.0f}/incident x {deployment_years}yr"
        ),
        annual_value=round(resilience_annual if ip_advantage else 0, 2),
        total_value=round(resilience_total if ip_advantage else 0, 2),
        applies=ip_advantage,
        assumptions=[
            f"IP{getac_ip_rating} vs IP{competitor_ip_rating}: ~{env_incident_rate_reduction:.0%} fewer environment-caused failures per year",
            f"Each environmental incident costs ${cost_per_env_incident:,.0f} (repair + downtime)",
        ],
    ))

    # ── Factor 5: Connectivity Advantage ──
    # Wi-Fi 7 + dedicated GPS = faster sync, fewer drops
    connectivity_minutes_saved = 3.0  # minutes per device per day
    connectivity_applies = getac_has_wifi7 and not competitor_has_wifi7
    connectivity_annual = fleet_size * (connectivity_minutes_saved * minute_rate) * working_days_per_year
    connectivity_total = connectivity_annual * deployment_years
    factors.append(ProductivityFactor(
        name="Connectivity Advantage",
        description="Wi-Fi 7 and dedicated GPS provide faster data sync and fewer connection drops",
        formula=(
            f"{fleet_size} devices x {connectivity_minutes_saved} min/day "
            f"x ${minute_rate:.2f}/min x {working_days_per_year} days x {deployment_years}yr"
        ),
        annual_value=round(connectivity_annual if connectivity_applies else 0, 2),
        total_value=round(connectivity_total if connectivity_applies else 0, 2),
        applies=connectivity_applies,
        assumptions=[
            f"Wi-Fi 7 saves ~{connectivity_minutes_saved} min/day per device vs Wi-Fi 6 (faster uploads, fewer retries)",
            "Dedicated GPS module enables optimized field routing",
        ],
    ))

    return factors
