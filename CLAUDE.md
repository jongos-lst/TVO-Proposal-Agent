# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TVO (Total Value of Ownership) Proposal Agent for Getac. An AI-driven system that helps sales/SA teams generate TVO proposals for enterprise customers. The agent guides users through 5 structured phases — from customer intake to automated PowerPoint deck generation.

This is a **Stage 2 interview challenge** for Getac's Advanced Technology Division. The deliverable includes a GitHub repo, README, and a 15–20 minute live demo showing the full end-to-end flow.

## Tech Stack

- **Backend**: Python 3.11 + FastAPI + LangGraph/LangChain
- **Frontend**: React + TypeScript + Vite + Tailwind CSS
- **LLM**: Switchable via `LLM_PROVIDER` env var — `openrouter` (GPT-4o), `openai`, or `ollama` (local)
- **Vector DB**: ChromaDB (embedded) for RAG competitive intelligence
- **File Generation**: python-pptx for PowerPoint output
- **Streaming**: SSE (Server-Sent Events)

## Development Commands

```bash
# Install dependencies
cd backend && python3.11 -m venv venv && source venv/bin/activate && pip install -r requirements.txt
cd frontend && npm install

# Ingest knowledge base into ChromaDB (run once)
cd backend && source venv/bin/activate && python -m scripts.ingest_knowledge

# Start backend (from backend/)
source venv/bin/activate && uvicorn app.main:app --reload --port 8000

# Start frontend (from frontend/)
npm run dev

# Run tests
cd backend && source venv/bin/activate && python -m pytest tests/ -v

# TypeScript check
cd frontend && npx tsc --noEmit
```

## Architecture

### Backend (`backend/app/`)

**LangGraph StateGraph** with 5 nodes connected by conditional edges enforcing phase gating:
```
intake → recommendation → calculation → review → generation → END
  ↻ loop if incomplete   ↻ loop if no product    ↻ loop if not approved
```

- `agent/graph.py` — Central LangGraph workflow definition (entry point for all agent logic)
- `agent/state.py` — `AgentState` TypedDict flowing between all phases
- `agent/nodes/` — One file per phase: `intake.py`, `recommendation.py`, `calculation.py`, `review.py`, `generation.py`
- `agent/prompts.py` — All system prompts organized by phase
- `services/llm.py` — LLM provider factory (Ollama/OpenRouter/OpenAI via single env var)
- `services/tvo_calculator.py` — Pure-function TVO/TCO math, no LLM dependency, fully explainable
- `services/pptx_generator.py` — 6-slide PowerPoint generation with Getac branding
- `services/rag.py` — ChromaDB ingestion and retrieval
- `services/product_catalog.py` — Loads `data/products.json` at startup
- `routes/chat.py` — `POST /api/chat/stream` (SSE) and `POST /api/chat` endpoints
- `routes/export.py` — `GET /api/proposals/{id}/export/pptx` for PowerPoint download
- `data/products.json` — 4 Getac products with specs/pricing
- `data/competitors.json` — 4 competitor products
- `data/knowledge/*.md` — Markdown files ingested into ChromaDB for RAG

State management: In-memory via LangGraph `MemorySaver` checkpointer.

### Frontend (`frontend/src/`)

- `hooks/useChat.ts` — Core hook managing messages, SSE streaming, and proposal state
- `api/client.ts` — SSE stream parser + REST helpers
- `components/chat/` — `ChatContainer`, `MessageBubble`, `InputBar`
- `components/layout/PhaseIndicator.tsx` — 5-step progress stepper
- `components/phases/` — `IntakeSummary`, `ProductCard`, `TVOTable`, `ExportButton`
- `App.tsx` — Main layout: sidebar (phases + data) + chat panel

### Key Design Decisions

- **TVO calculator is pure math** — no LLM computes the numbers; the LLM presents/explains them
- **SSE over WebSocket** — simpler, sufficient for unidirectional streaming
- **Each node sets `current_phase`** — a single router function dispatches to the next node
- **Vite proxies `/api` to backend** — no CORS issues in development
