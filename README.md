# Getac TVO Proposal Agent

**AI-driven Total Value of Ownership proposal engine for Getac rugged devices**

Python 3.11 | FastAPI | LangGraph | React 19 | TypeScript | Tailwind CSS | ChromaDB | Docker

---

## Overview

The TVO Proposal Agent is an AI-powered sales engineering tool that guides Getac sales representatives through a structured 5-phase workflow to generate data-backed TVO (Total Value of Ownership) proposals. In minutes, a sales rep can go from customer intake to a downloadable PowerPoint deck with quantified cost savings, productivity gains, and risk reduction metrics.

Unlike a generic chatbot, the agent maintains phase-aware state, enforces completeness checks, integrates competitive intelligence via RAG, and produces explainable financial calculations that sales reps can confidently present to enterprise customers.

### Key Features

- **5-Phase Guided Workflow** -- Intake, Recommendation, Calculation, Review, Export with explicit phase gating
- **Multi-Product Support** -- Recommend and compare multiple Getac products in a single proposal
- **Explainable TVO/TCO Calculations** -- Pure-math engine with transparent formulas and assumptions
- **RAG-Powered Competitive Intelligence** -- ChromaDB vector search over product specs and competitor data
- **7 Professional Charts** -- matplotlib-generated visualizations (TCO comparison, ROI timeline, risk gauge, etc.)
- **Automated PowerPoint Generation** -- 6-slide branded deck with python-pptx
- **Real-Time Streaming** -- SSE (Server-Sent Events) for live AI responses
- **Switchable LLM Providers** -- OpenRouter (GPT-4o), OpenAI, or local Ollama
- **Docker Compose Deployment** -- Single command to start the full stack
- **Editable Calculation Parameters** -- Side-by-side Getac vs. competitor parameter editing before calculation

---

## Demo Flow

```
Phase 01          Phase 02              Phase 03           Phase 04        Phase 05
Customer    -->   Product          -->  TVO/TCO       -->  Proposal   -->  PowerPoint
Intake            Recommendation        Calculation        Review          Export

[Form +           [Product cards +      [Cost tables +     [Full summary   [Download
 AI chat]          competitor match]     7 charts]          + approve]       .pptx]
```

The agent collects customer context (pain points, use scenarios, budget, warranty needs, current devices), recommends Getac products with competitive advantages, calculates quantified value metrics, presents a reviewable summary, and generates a downloadable PowerPoint deck.

---

## Architecture

```
                          +-------------------+
                          |    React Frontend  |
                          |   (Vite + Tailwind)|
                          |    localhost:5173  |
                          +--------+----------+
                                   | SSE + REST
                                   v
                          +--------+----------+
                          |   FastAPI Backend   |
                          |    localhost:8000   |
                          +--------+----------+
                                   |
              +--------------------+--------------------+
              |                    |                    |
     +--------v---------+  +-------v---------+  +-------v--------+
     |  LangGraph       |  |  TVO Calculator |  |  ChromaDB      |
     |  StateGraph      |  |  (pure math)    |  |  (RAG vectors) |
     |  5 phase nodes   |  |  no LLM needed  |  |  product specs |
     +------------------+  +-----------------+  +----------------+
              |
     +--------v--------+
     |  LLM Provider    |
     |  OpenRouter /    |
     |  OpenAI / Ollama |
     +------------------+
```

### LangGraph Workflow

The backend is built around a **LangGraph StateGraph** with 5 nodes connected by conditional edges. Each node corresponds to one phase. State flows through the graph as an `AgentState` TypedDict:

```
intake --> recommendation --> calculation --> review --> generation --> END
  |            |                  |              |
  +-- loop if  +-- loop if no    +-- loop if    +-- loop if not
     incomplete    product          no TVO         approved
```

**Phase gating is explicit** -- phases only advance when the user clicks "Continue to [next phase]", not via chat keywords. The backend always returns to the current phase; the frontend controls forward navigation based on per-phase prerequisites:

| Phase | Prerequisite to Continue |
|---|---|
| Intake | All required persona fields collected |
| Recommendation | At least one product selected |
| Calculation | TVO results computed |
| Review | Proposal explicitly approved |

### AgentState

```python
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    session_id: str
    current_phase: Literal["intake", "recommendation", "calculation", "review", "generation", "complete"]

    # Phase 01 -- Customer Persona
    persona: Optional[CustomerPersona]

    # Phase 02 -- Product Recommendation (multi-product)
    selected_products: Optional[list[GetacProduct]]
    competitor_product_names: Optional[dict[str, str]]
    competitive_advantages: Optional[dict[str, list[str]]]

    # Phase 03 -- TVO Calculation (multi-product)
    tvo_results: Optional[dict[str, TVOCalculation]]
    fleet_size: Optional[int]
    deployment_years: Optional[int]

    # Phase 04 -- Review
    proposal_approved: bool
    value_proposition: Optional[str]

    # Phase 05 -- Generation
    pptx_path: Optional[str]
```

State is persisted in-memory via LangGraph's `MemorySaver` checkpointer, keyed by `session_id`.

---

## Technology Choices

| Technology | Role | Why This Choice |
|---|---|---|
| **Python 3.11 + FastAPI** | Backend API | Async-native, excellent for SSE streaming, strong type hints with Pydantic |
| **LangGraph / LangChain** | Agent orchestration | Purpose-built for multi-step agent workflows with state management and conditional routing |
| **React 19 + TypeScript** | Frontend | Component-based UI, strong typing, large ecosystem. Vite for fast dev builds |
| **Tailwind CSS 4** | Styling | Utility-first approach enables rapid UI iteration without CSS files |
| **ChromaDB** | Vector database | Embedded (no server needed), persistent storage, integrates natively with LangChain |
| **SSE (Server-Sent Events)** | Streaming | Simpler than WebSocket for unidirectional streaming; sufficient for LLM token-by-token output |
| **matplotlib** | Chart generation | Server-side rendering to PNG; no client-side charting library needed |
| **python-pptx** | PowerPoint generation | Direct .pptx creation with full control over slides, layouts, and branding |
| **Sentence Transformers** | Embeddings | Local `all-MiniLM-L6-v2` model -- no API calls needed for embeddings |
| **Docker Compose** | Deployment | Single-command full-stack startup; appropriate for demo/interview context |

### LLM Provider Strategy

The LLM is **switchable via a single environment variable** (`LLM_PROVIDER`):

| Provider | Model | Use Case |
|---|---|---|
| `openrouter` | GPT-4o via OpenRouter | Recommended for demo (best quality) |
| `openai` | GPT-4o direct | Alternative if you have an OpenAI key |
| `ollama` | Any local model | Offline development, no API costs |

---

## Quick Start

### Option A: Docker Compose (Recommended)

```bash
# 1. Clone the repo
git clone <repo-url>
cd TVO-Proposal-Agent

# 2. Configure environment
cp .env.example .env
# Edit .env -- set LLM_PROVIDER and API key

# 3. Start the full stack
docker compose up --build

# 4. Ingest knowledge base (first time only)
docker compose run --rm ingest

# 5. Open the app
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/api/health
```

### Option B: Local Development

```bash
# 1. Backend setup
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Frontend setup
cd ../frontend
npm install

# 3. Configure environment
cd ..
cp .env.example .env
# Edit .env -- set LLM_PROVIDER and API key

# 4. Ingest knowledge base (first time only)
cd backend
source venv/bin/activate
python -m scripts.ingest_knowledge

# 5. Start backend (terminal 1)
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000

# 6. Start frontend (terminal 2)
cd frontend
npm run dev

# 7. Open the app
# http://localhost:5173
```

### Makefile Shortcuts

```bash
make install        # Install all dependencies (backend + frontend)
make ingest         # Ingest knowledge base into ChromaDB
make dev            # Start both backend and frontend
make test           # Run backend tests

# Docker
make docker-up      # docker compose up --build
make docker-down    # docker compose down
make docker-ingest  # docker compose run --rm ingest
make docker-logs    # docker compose logs -f
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `ollama` | LLM backend: `ollama`, `openrouter`, or `openai` |
| `OPENROUTER_API_KEY` | -- | API key for OpenRouter |
| `OPENROUTER_MODEL` | `openai/gpt-4o` | Model to use via OpenRouter |
| `OPENAI_API_KEY` | -- | API key for OpenAI direct |
| `OPENAI_MODEL` | `gpt-4o` | Model to use via OpenAI |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL (use `http://host.docker.internal:11434` for Docker) |
| `OLLAMA_MODEL` | `minimax-m2.7:cloud` | Local model name |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Sentence transformer model for embeddings |
| `BACKEND_PORT` | `8000` | FastAPI server port |
| `FRONTEND_URL` | `http://localhost:5173` | CORS allowed origin |

---

## Project Structure

```
TVO-Proposal-Agent/
|-- backend/
|   |-- app/
|   |   |-- agent/
|   |   |   |-- graph.py            # LangGraph StateGraph definition
|   |   |   |-- state.py            # AgentState TypedDict
|   |   |   |-- prompts.py          # All system prompts by phase
|   |   |   |-- nodes/
|   |   |       |-- intake.py       # Phase 01: Customer persona collection
|   |   |       |-- recommendation.py  # Phase 02: Product matching
|   |   |       |-- calculation.py  # Phase 03: TVO/TCO computation
|   |   |       |-- review.py       # Phase 04: Proposal review
|   |   |       |-- generation.py   # Phase 05: PowerPoint generation
|   |   |-- models/
|   |   |   |-- persona.py          # CustomerPersona Pydantic model
|   |   |   |-- product.py          # GetacProduct model
|   |   |   |-- tvo.py              # TVOCalculation model
|   |   |   |-- chat.py             # Chat request/response models
|   |   |   |-- proposal.py         # Proposal summary model
|   |   |-- routes/
|   |   |   |-- chat.py             # SSE streaming + chat endpoints
|   |   |   |-- charts.py           # On-demand chart PNG generation
|   |   |   |-- export.py           # PowerPoint download
|   |   |   |-- intake.py           # Structured intake submission
|   |   |   |-- products.py         # Product catalog + competitors
|   |   |   |-- scraper.py          # Competitor data refresh
|   |   |-- services/
|   |   |   |-- llm.py              # LLM provider factory
|   |   |   |-- tvo_calculator.py   # Pure-math TVO/TCO engine
|   |   |   |-- chart_generator.py  # 7 matplotlib chart types
|   |   |   |-- pptx_generator.py   # PowerPoint deck builder
|   |   |   |-- rag.py              # ChromaDB ingestion + retrieval
|   |   |   |-- product_catalog.py  # Product data loader
|   |   |   |-- competitor_scraper.py  # Web scraper for competitor pages
|   |   |-- data/
|   |   |   |-- products.json       # 5 Getac products with specs/pricing
|   |   |   |-- competitors.json    # 4 competitor products
|   |   |   |-- knowledge/          # Markdown files for RAG ingestion
|   |   |-- config.py               # Pydantic Settings (env vars)
|   |   |-- main.py                 # FastAPI app entry point
|   |-- scripts/
|   |   |-- ingest_knowledge.py     # ChromaDB ingestion script
|   |   |-- scrape_products.py      # Competitor page scraper
|   |-- tests/
|   |   |-- test_tvo_calculator.py  # 40+ TVO calculation tests
|   |   |-- test_chart_generator.py # 14 chart rendering tests
|   |   |-- test_pptx_generator.py  # PowerPoint generation tests
|   |   |-- test_confirmed_calculation.py
|   |   |-- test_rag_integration.py
|   |-- Dockerfile
|   |-- requirements.txt
|-- frontend/
|   |-- src/
|   |   |-- hooks/useChat.ts        # Core SSE streaming + state hook
|   |   |-- api/client.ts           # API client + SSE parser
|   |   |-- types/index.ts          # TypeScript interfaces
|   |   |-- config/PhaseConfig.ts   # Phase metadata (labels, icons, chips)
|   |   |-- components/
|   |   |   |-- wizard/WizardContainer.tsx   # Main 2-column layout + phase routing
|   |   |   |-- chat/ChatContainer.tsx       # Chat message panel
|   |   |   |-- chat/InputBar.tsx            # Message input + quick chips
|   |   |   |-- chat/MessageBubble.tsx       # Individual message rendering
|   |   |   |-- layout/PhaseIndicator.tsx    # 5-step progress stepper
|   |   |   |-- phases/IntakeForm.tsx        # Structured intake form
|   |   |   |-- phases/IntakeSummary.tsx     # Persona summary card
|   |   |   |-- phases/ProductCard.tsx       # Product recommendation card
|   |   |   |-- phases/ConfirmationPanel.tsx # Editable calculation params
|   |   |   |-- phases/TVOTable.tsx          # Cost breakdown table
|   |   |   |-- phases/TVOCharts.tsx         # 7-chart visualization grid
|   |   |   |-- phases/ReviewPanel.tsx       # Proposal review summary
|   |   |   |-- phases/ExportButton.tsx      # PowerPoint download button
|   |   |   |-- shared/RichMarkdown.tsx      # Markdown renderer
|   |   |-- App.tsx
|   |   |-- main.tsx
|   |-- Dockerfile
|   |-- nginx.conf
|   |-- package.json
|-- docker-compose.yml
|-- Makefile
|-- .env.example
|-- CLAUDE.md
```

---

## Agent Workflow Design

### Phase 01: Customer Intake

The agent collects a structured customer persona through natural conversation. Required fields:

1. **Pain Points** -- Problems with current devices (failures, downtime, screen readability)
2. **Use Scenarios** -- Deployment context (field service, warehouse, patrol vehicle)
3. **Budget** -- Per-unit or total fleet budget
4. **Service & Warranty Needs** -- Required SLA level
5. **Current Devices** -- What the customer currently uses

The intake node extracts structured data from free-form conversation using an LLM with a JSON schema. A **completeness check** detects missing fields and the agent proactively asks follow-up questions. The phase only advances when all 5 required fields are populated.

An optional **structured form** (IntakeForm) lets the rep enter fields directly, bypassing conversation if preferred.

### Phase 02: Product Recommendation

Given the persona, the agent:
1. Matches customer needs to the Getac product catalog
2. Queries ChromaDB for competitive intelligence via RAG
3. Identifies the closest competitor and retrieves differentiation points
4. If no competitor match is found, notifies the user before defaulting to a generic competitor

The sales rep confirms which product(s) to proceed with. **Multiple products** can be selected for different deployment scenarios (e.g., laptops for office + tablets for field).

### Phase 03: TVO Calculation

Before calculation, a **Confirmation Panel** presents all parameters side-by-side (Getac vs. Competitor) for review and editing:

- Unit price, warranty, failure rate
- Display brightness, IP rating
- Hot-swap battery, Wi-Fi 7 capability
- Fleet size, deployment years, productivity value

The TVO calculator is a **pure-math engine** (no LLM involvement in the numbers). It computes:

- **TCO Comparison** -- Hardware + warranty + repair + downtime costs over deployment period
- **Productivity Savings** -- 5 quantified factors (Hot-Swap Battery, Display Readability, Rugged Reliability, Connectivity Advantage, Weather Sealing)
- **Risk Reduction** -- Expected failure count comparison
- **ROI Timeline** -- Break-even month calculation

Results are visualized in **7 charts** (TCO comparison bar chart, total TCO, savings donut, ROI timeline, cumulative cost waterfall, risk gauge, productivity breakdown) generated server-side with matplotlib.

### Phase 04: Proposal Review

The agent compiles all collected data into a structured summary:
- Customer persona
- Recommended products with pricing
- TVO/TCO calculation results
- Competitive advantages
- Suggested value proposition

The sales rep can modify any field or approve the proposal. **Human-in-the-loop**: the workflow only proceeds to generation after explicit approval.

### Phase 05: PowerPoint Export

On approval, the system generates a **6-slide PowerPoint deck** using python-pptx:

1. Cover page (customer name, date, Getac branding)
2. Customer situation and pain points
3. Getac solution introduction
4. TVO/TCO comparison table with charts
5. Competitive differentiation analysis
6. Conclusion and recommended next steps

The deck is available for immediate download.

---

## Prompt Design

Each phase has a dedicated system prompt in `backend/app/agent/prompts.py`. Prompts follow these design principles:

### Dynamic Context Injection

Prompts are not static. Each prompt template receives runtime variables:

```python
# Example: Intake prompt receives current field status
INTAKE_SYSTEM_PROMPT = """...
CURRENTLY COLLECTED:
{collected_fields}

STILL MISSING:
{missing_fields}
..."""
```

This lets the LLM know exactly what information has been gathered and what gaps remain, enabling targeted follow-up questions.

### Phase-Specific Behavior

| Phase | Prompt Strategy |
|---|---|
| Intake | Conversational peer-to-peer tone. Ask 1-2 fields per turn. Show industry knowledge. |
| Recommendation | Present product matches with specs. Reference competitive advantages from RAG. |
| Calculation | Explain numbers transparently. Every metric has a visible formula and assumptions list. |
| Review | Summarize all data. Highlight key selling points. Ask for explicit approval. |
| Generation | Minimal prompt -- triggers PPTX generation pipeline. |

### Conversation Guidelines

- The agent speaks to Getac sales reps as a peer (solutions architect tone), not to end customers
- Responses are concise (3-5 sentences per turn)
- The agent probes deeper on high-impact fields (pain points and use scenarios) before less critical ones
- Industry-specific knowledge is demonstrated when the rep mentions a vertical

---

## Data Integration Architecture

### Product Catalog

- **Source**: `backend/app/data/products.json` (5 Getac products) and `competitors.json` (4 competitors)
- **Loading**: Loaded at startup via `product_catalog.py`
- **Content**: Full specs including pricing, warranty, failure rates, rugged ratings, key features

### RAG Pipeline (Competitive Intelligence)

```
Markdown files (knowledge/)
        |
        v
  Text Splitter (RecursiveCharacterTextSplitter)
        |
        v
  Embeddings (all-MiniLM-L6-v2, local)
        |
        v
  ChromaDB (persistent, ./chroma_data)
        |
        v
  Similarity Search (k=5 relevant chunks)
        |
        v
  LLM Context (competitive advantages, product specs)
```

**Knowledge sources** (13 documents):
- 5 Getac product spec sheets (B360, F110, K120, V120, X600)
- 4 hand-written competitor profiles (Dell, HP, Panasonic, Samsung)
- 4 scraped competitor product pages (Dell Latitude 5430/7330 Rugged, Panasonic Toughbook 33/40)

The scraper (`competitor_scraper.py`) can refresh competitor data from live web pages using DuckDuckGo search and BeautifulSoup.

### ChromaDB

- **Embedding model**: `all-MiniLM-L6-v2` (runs locally, no API needed)
- **Persistence**: SQLite-backed at `backend/chroma_data/`
- **Ingestion**: Run once via `python -m scripts.ingest_knowledge` (or `make ingest`)
- **Retrieval**: Integrated into recommendation and review phases

---

## TVO Calculation Engine

The calculator (`backend/app/services/tvo_calculator.py`) is a **pure-function engine** with no LLM dependency. This is a deliberate design choice: financial calculations must be deterministic, auditable, and explainable.

### TCO Components

| Cost Category | Getac Calculation | Competitor Calculation |
|---|---|---|
| Hardware | `unit_price * fleet_size` | `competitor_price * fleet_size` |
| Extended Warranty | `warranty_cost * years_beyond_standard` | Same formula, different rates |
| Repair & Replacement | `failure_rate * fleet_size * years * repair_cost` | Higher failure rate |
| Downtime Cost | `failures * downtime_hours * hourly_value` | More failures = more downtime |
| Productivity Loss | 5 factor calculation (see below) | Baseline comparison |

### 5 Productivity Factors

Each factor is independently calculated with transparent assumptions:

1. **Hot-Swap Battery** -- Time saved from battery swaps vs. AC charging (if applicable)
2. **Display Readability** -- Reduced rework from outdoor screen visibility (nits comparison)
3. **Rugged Reliability** -- Fewer disruptions from device failures (failure rate delta)
4. **Connectivity Advantage** -- Time saved from Wi-Fi 7 vs. older standards (if applicable)
5. **Weather Sealing** -- Reduced weather-related incidents (IP rating comparison)

### Explainability

Every calculation produces:
- `tco_line_items` -- Per-category cost breakdown with formula strings
- `assumptions` -- List of all assumptions used
- `productivity_breakdown` -- Per-factor details with `applies` flag and `formula` string

This lets the sales rep explain every number to the customer.

---

## API Reference

All routes are prefixed with `/api`.

### Chat & Workflow

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/chat/stream` | SSE streaming chat -- main interaction endpoint |
| `POST` | `/api/chat` | Non-streaming chat (returns full response) |
| `POST` | `/api/chat/override-phase` | Force transition to a specific phase |
| `POST` | `/api/calculate-confirmed` | Run TVO calculation with confirmed parameters |

### Products & Data

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/products` | List all Getac products |
| `GET` | `/api/products/{id}` | Get single product details |
| `GET` | `/api/competitors` | List all competitor products |

### Charts

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/charts/{session_id}/{product_id}/{chart_name}` | Generate and return chart PNG |

Available chart names: `tco_comparison`, `total_tco`, `savings_breakdown`, `productivity`, `roi_timeline`, `cost_waterfall`, `risk_gauge`

### Export

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/proposals/{session_id}/export/pptx` | Download generated PowerPoint deck |

### Intake & Scraper

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/intake` | Submit structured intake form data |
| `POST` | `/api/scraper/refresh` | Re-scrape competitor product pages |
| `GET` | `/api/scraper/status` | Check scraper status |
| `GET` | `/api/catalog/summary` | Product catalog summary |

### Health

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/health` | Health check (returns LLM provider info) |

---

## Frontend Components

The frontend is a **wizard-style SPA** with a 2-column layout:

- **Left panel**: Phase-specific structured data (forms, product cards, TVO tables, charts)
- **Right panel**: AI agent analysis and conversation
- **Bottom bar**: Chat input with quick-action chips + phase navigation buttons

### Key Components

| Component | Purpose |
|---|---|
| `WizardContainer` | Main layout orchestrator. Routes phase-specific panels, manages navigation |
| `PhaseIndicator` | 5-step progress stepper in the sidebar |
| `IntakeForm` | Structured form for customer persona fields |
| `ProductCard` | Product recommendation card with specs and competitive advantages |
| `ConfirmationPanel` | Full-screen parameter editor (Getac vs. Competitor side-by-side) |
| `TVOTable` | Cost breakdown table with bar visualizations |
| `TVOCharts` | 7-chart visualization grid (full-width + 3-column layouts) |
| `ReviewPanel` | Proposal summary for review and approval |
| `ExportButton` | PowerPoint download with loading state |
| `RichMarkdown` | Markdown renderer for AI responses (supports GFM tables, code blocks) |

---

## Testing

### Running Tests

```bash
# All backend tests
cd backend && source venv/bin/activate && python -m pytest tests/ -v

# Specific test files
python -m pytest tests/test_tvo_calculator.py -v    # TVO math (40+ tests)
python -m pytest tests/test_chart_generator.py -v   # Chart rendering (14 tests)
python -m pytest tests/test_pptx_generator.py -v    # PowerPoint generation
python -m pytest tests/test_rag_integration.py -v   # RAG pipeline

# TypeScript check
cd frontend && npx tsc --noEmit
```

### Test Coverage

| Test File | Tests | Coverage Area |
|---|---|---|
| `test_tvo_calculator.py` | 40+ | TCO line items, productivity factors, edge cases, cumulative costs, ROI payback |
| `test_chart_generator.py` | 14 | All 7 chart types + edge cases (zero values, single year, no savings) |
| `test_pptx_generator.py` | 5+ | Slide generation, content verification |
| `test_confirmed_calculation.py` | 5+ | End-to-end calculation with confirmed parameters |
| `test_rag_integration.py` | 10+ | Knowledge ingestion, retrieval, competitor matching |

**Total: 76 tests**

---

## Docker

### Services

| Service | Image | Port | Purpose |
|---|---|---|---|
| `backend` | Python 3.11-slim | 8000 | FastAPI + LangGraph + matplotlib |
| `frontend` | nginx:alpine | 3000 | Static React build + API reverse proxy |
| `ingest` | (same as backend) | -- | One-shot ChromaDB knowledge ingestion |

### Volumes

| Volume | Purpose |
|---|---|
| `chroma_data` | ChromaDB vector database persistence |
| `backend_output` | Generated PowerPoint files |

### Commands

```bash
# Start everything
docker compose up --build

# Ingest knowledge base (first time)
docker compose run --rm ingest

# View logs
docker compose logs -f backend

# Stop
docker compose down

# Stop and remove volumes (full reset)
docker compose down -v
```

### Docker Notes

- The `ingest` service uses `profiles: ["init"]` -- it only runs when explicitly invoked, not on `docker compose up`
- For Ollama users, set `OLLAMA_BASE_URL=http://host.docker.internal:11434` in `.env` to reach the host machine's Ollama
- The first backend start may be slow as `sentence-transformers` downloads the embedding model (~90MB)
- nginx is configured with `proxy_buffering off` for SSE streaming support

---

## License

This project was built as a Stage 2 interview challenge for Getac's Advanced Technology Division.
