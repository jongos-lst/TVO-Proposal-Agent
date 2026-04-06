from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from app.agent.graph import graph
from app.services.chart_generator import (
    generate_tco_comparison_chart,
    generate_total_tco_chart,
    generate_savings_breakdown_chart,
    generate_productivity_chart,
    generate_roi_timeline_chart,
    generate_cost_waterfall_chart,
    generate_risk_gauge_chart,
)

router = APIRouter(prefix="/api", tags=["charts"])

CHART_FUNCS = {
    "tco_comparison": generate_tco_comparison_chart,
    "total_tco": generate_total_tco_chart,
    "savings_breakdown": generate_savings_breakdown_chart,
    "productivity": generate_productivity_chart,
    "roi_timeline": generate_roi_timeline_chart,
    "cost_waterfall": generate_cost_waterfall_chart,
    "risk_gauge": generate_risk_gauge_chart,
}


@router.get("/charts/{session_id}/{product_id}/{chart_name}")
async def get_chart(session_id: str, product_id: str, chart_name: str):
    """Generate and return a TVO chart as PNG image."""
    if chart_name not in CHART_FUNCS:
        raise HTTPException(status_code=404, detail=f"Unknown chart: {chart_name}")

    config = {"configurable": {"thread_id": session_id}}
    try:
        state = graph.get_state(config)
    except Exception:
        raise HTTPException(status_code=404, detail="Session not found")

    if not state or not state.values:
        raise HTTPException(status_code=404, detail="Session not found")

    tvo_results = state.values.get("tvo_results") or {}
    tvo = tvo_results.get(product_id)
    if not tvo:
        raise HTTPException(status_code=404, detail=f"No TVO data for product {product_id}")

    buf = CHART_FUNCS[chart_name](tvo)
    return Response(content=buf.read(), media_type="image/png")
