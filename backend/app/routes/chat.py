import json
import logging
import traceback
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage

from app.models.chat import ChatRequest
from app.agent.graph import graph

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["chat"])

from pydantic import BaseModel

from app.services.tvo_calculator import calculate_tvo


class OverridePhaseRequest(BaseModel):
    session_id: str
    target_phase: str
    proposal_approved: bool | None = None


class ProductCalcParams(BaseModel):
    product_id: str
    product_name: str
    unit_price: float
    warranty_years: int
    failure_rate: float
    competitor_name: str
    competitor_price: float
    competitor_warranty_years: int
    competitor_failure_rate: float
    # Feature flags for productivity factors
    has_hot_swap: bool = True
    display_nits: int = 1400
    competitor_display_nits: int = 600
    ip_rating: int = 66
    competitor_ip_rating: int = 53
    has_wifi7: bool = True
    competitor_has_wifi7: bool = False


class ConfirmedCalculationRequest(BaseModel):
    session_id: str
    fleet_size: int
    deployment_years: int
    hourly_productivity_value: float = 50.0
    avg_downtime_hours_per_failure: float = 16.0
    annual_repair_cost: float = 450.0
    products: list[ProductCalcParams]


def _serialize_products(products):
    """Serialize a list of GetacProduct objects to dicts."""
    if not products:
        return []
    return [p.model_dump() if hasattr(p, "model_dump") else p for p in products]


def _serialize_tvo_results(tvo_results):
    """Serialize a dict of product_id -> TVOCalculation to dicts."""
    if not tvo_results:
        return {}
    return {k: (v.model_dump() if hasattr(v, "model_dump") else v) for k, v in tvo_results.items()}


@router.post("/chat/override-phase")
async def override_phase(request: OverridePhaseRequest):
    """Override the LangGraph state to force a specific phase without LLM logic."""
    config = {"configurable": {"thread_id": request.session_id}}
    try:
        update_data: dict = {"current_phase": request.target_phase}
        if request.proposal_approved is not None:
            update_data["proposal_approved"] = request.proposal_approved
        graph.update_state(config, update_data)

        state = graph.get_state(config)
        values = state.values if state else {}

        result: dict = {"status": "success", "phase": request.target_phase}
        if values.get("persona"):
            p = values["persona"]
            result["persona"] = p.model_dump() if hasattr(p, "model_dump") else p
        if values.get("selected_products"):
            result["selected_products"] = _serialize_products(values["selected_products"])
        if values.get("tvo_results"):
            result["tvo_results"] = _serialize_tvo_results(values["tvo_results"])
        if values.get("competitive_advantages"):
            result["competitive_advantages"] = values["competitive_advantages"]
        if values.get("competitor_product_names"):
            result["competitor_product_names"] = values["competitor_product_names"]
        result["proposal_approved"] = values.get("proposal_approved", False)

        return result
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/calculate-confirmed")
async def calculate_confirmed(request: ConfirmedCalculationRequest):
    """Run TVO calculation with user-confirmed parameters (bypasses LLM calculation node)."""
    config = {"configurable": {"thread_id": request.session_id}}

    try:
        # Get current state to preserve existing data
        state = graph.get_state(config)
        values = state.values if state else {}

        # Compute TVO for each product with user-supplied params
        tvo_results = {}
        for prod_params in request.products:
            tvo = calculate_tvo(
                getac_unit_price=prod_params.unit_price,
                getac_warranty_years=prod_params.warranty_years,
                getac_failure_rate=prod_params.failure_rate,
                competitor_unit_price=prod_params.competitor_price,
                competitor_warranty_years=prod_params.competitor_warranty_years,
                competitor_failure_rate=prod_params.competitor_failure_rate,
                fleet_size=request.fleet_size,
                deployment_years=request.deployment_years,
                hourly_productivity_value=request.hourly_productivity_value,
                avg_downtime_hours_per_failure=request.avg_downtime_hours_per_failure,
                annual_repair_cost=request.annual_repair_cost,
                getac_has_hot_swap=prod_params.has_hot_swap,
                getac_display_nits=prod_params.display_nits,
                competitor_display_nits=prod_params.competitor_display_nits,
                getac_ip_rating=prod_params.ip_rating,
                competitor_ip_rating=prod_params.competitor_ip_rating,
                getac_has_wifi7=prod_params.has_wifi7,
                competitor_has_wifi7=prod_params.competitor_has_wifi7,
            )
            tvo_results[prod_params.product_id] = tvo

        # Update graph state with TVO results
        update_data = {
            "current_phase": "calculation",
            "tvo_results": tvo_results,
            "fleet_size": request.fleet_size,
            "deployment_years": request.deployment_years,
        }
        graph.update_state(config, update_data)

        return {
            "success": True,
            "phase": "calculation",
            "tvo_results": _serialize_tvo_results(tvo_results),
            "selected_products": _serialize_products(values.get("selected_products")),
        }
    except Exception as e:
        logger.error("Confirmed calculation failed: %s", e, exc_info=True)
        return {"success": False, "error": str(e)}


@router.post("/chat")
async def chat(request: ChatRequest):
    """Non-streaming chat endpoint."""
    config = {"configurable": {"thread_id": request.session_id}}

    current_state = None
    try:
        current_state = graph.get_state(config)
    except Exception:
        pass

    input_data = {"messages": [HumanMessage(content=request.message)]}

    if not current_state or not current_state.values:
        input_data["session_id"] = request.session_id
        input_data["current_phase"] = "intake"
        input_data["proposal_approved"] = False

    result = await graph.ainvoke(input_data, config=config)

    ai_message = result["messages"][-1].content if result["messages"] else ""
    phase = result.get("current_phase", "intake")

    structured_data = {}
    if result.get("persona"):
        structured_data["persona"] = result["persona"].model_dump()
    if result.get("selected_products"):
        structured_data["selected_products"] = _serialize_products(result["selected_products"])
    if result.get("tvo_results"):
        structured_data["tvo_results"] = _serialize_tvo_results(result["tvo_results"])
    if result.get("competitive_advantages"):
        structured_data["competitive_advantages"] = result["competitive_advantages"]
    if result.get("competitor_product_names"):
        structured_data["competitor_product_names"] = result["competitor_product_names"]
    if result.get("pptx_path"):
        structured_data["pptx_path"] = result["pptx_path"]
    structured_data["proposal_approved"] = result.get("proposal_approved", False)

    return {
        "session_id": request.session_id,
        "phase": phase,
        "message": ai_message,
        "structured_data": structured_data,
    }


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Streaming chat endpoint using SSE."""
    config = {"configurable": {"thread_id": request.session_id}}

    current_state = None
    try:
        current_state = graph.get_state(config)
    except Exception:
        pass

    input_data = {"messages": [HumanMessage(content=request.message)]}

    if not current_state or not current_state.values:
        input_data["session_id"] = request.session_id
        input_data["current_phase"] = "intake"
        input_data["proposal_approved"] = False

    phase_node_names = {"intake", "recommendation", "calculation", "review", "generation"}

    def _build_state_update(output: dict) -> dict:
        """Build a state_update payload from node output or graph state values."""
        phase = output.get("current_phase", "intake")
        state_update: dict = {"phase": phase}
        if output.get("persona"):
            p = output["persona"]
            state_update["persona"] = p.model_dump() if hasattr(p, "model_dump") else p
        if output.get("selected_products"):
            state_update["selected_products"] = _serialize_products(output["selected_products"])
        if output.get("tvo_results"):
            state_update["tvo_results"] = _serialize_tvo_results(output["tvo_results"])
        if output.get("competitive_advantages"):
            state_update["competitive_advantages"] = output["competitive_advantages"]
        if output.get("competitor_product_names"):
            state_update["competitor_product_names"] = output["competitor_product_names"]
        if output.get("pptx_path"):
            state_update["pptx_path"] = output["pptx_path"]
        if "proposal_approved" in output:
            state_update["proposal_approved"] = output["proposal_approved"]
        return state_update

    async def event_generator():
        last_emitted_phase = None
        try:
            async for event in graph.astream_events(
                input_data, config=config, version="v2"
            ):
                kind = event["event"]

                if kind == "on_chat_model_stream":
                    tags = event.get("tags", [])
                    if "extraction" in tags:
                        continue
                    chunk = event["data"]["chunk"]
                    if hasattr(chunk, "content") and chunk.content:
                        yield f"data: {json.dumps({'type': 'token', 'content': chunk.content})}\n\n"

                elif kind == "on_chain_end":
                    name = event.get("name", "")
                    if name in phase_node_names or any(name.endswith(f":{n}") or name.endswith(f"_{n}") for n in phase_node_names):
                        output = event["data"].get("output", {})
                        if isinstance(output, dict) and "current_phase" in output:
                            state_update = _build_state_update(output)
                            last_emitted_phase = state_update["phase"]
                            yield f"data: {json.dumps({'type': 'state_update', **state_update})}\n\n"

        except Exception as e:
            logger.error("SSE stream error: %s\n%s", e, traceback.format_exc())
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

        # Always emit final state from checkpointer
        try:
            final_state = graph.get_state(config)
            if final_state and final_state.values:
                vals = final_state.values
                final_phase = vals.get("current_phase", "intake")
                if final_phase != last_emitted_phase:
                    state_update = _build_state_update(vals)
                    yield f"data: {json.dumps({'type': 'state_update', **state_update})}\n\n"
        except Exception as e:
            logger.error("Final state sync error: %s\n%s", e, traceback.format_exc())

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
