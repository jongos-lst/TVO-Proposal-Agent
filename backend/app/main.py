from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.services.product_catalog import load_catalog
from app.routes import chat, intake, products, export, scraper, charts


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    load_catalog()
    yield
    # Shutdown (nothing to clean up)


app = FastAPI(
    title="TVO Proposal Agent",
    description="AI-driven Total Value of Ownership proposal engine for Getac",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(chat.router)
app.include_router(intake.router)
app.include_router(products.router)
app.include_router(export.router)
app.include_router(scraper.router)
app.include_router(charts.router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "llm_provider": settings.llm_provider}
