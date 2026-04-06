import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from app.agent.graph import graph

router = APIRouter(prefix="/api", tags=["export"])


@router.get("/proposals/{session_id}/export/pptx")
async def export_pptx(session_id: str):
    """Download the generated PowerPoint proposal."""
    config = {"configurable": {"thread_id": session_id}}

    try:
        state = graph.get_state(config)
        pptx_path = state.values.get("pptx_path")
    except Exception:
        pptx_path = None

    if not pptx_path or not os.path.exists(pptx_path):
        raise HTTPException(status_code=404, detail="PowerPoint not yet generated")

    return FileResponse(
        pptx_path,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        filename=f"TVO_Proposal_{session_id[:8]}.pptx",
    )
