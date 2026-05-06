import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.core.config import get_settings
from app.database.connection import create_tables
from app.rag.retriever import is_index_loaded
from app.routes.plan import router as plan_router
from app.routes.history import router as history_router

settings = get_settings()


# ─── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # ── Startup ──
    logger.info("JourneyMind API starting up...")
    logger.info(f"Environment: {settings.environment}")

    # Create DB tables if they don't exist
    await create_tables()
    logger.info("Database tables ready")

    # Auto-build FAISS index if not found (HF Spaces has no persistent disk)
    faiss_path = Path(settings.faiss_index_path) / "travel.index"
    if not faiss_path.exists():
        logger.warning("FAISS index not found — building now (this takes ~30s)...")
        try:
            from app.rag.embedder import build_faiss_index
            build_faiss_index()
            logger.success("FAISS index built successfully on startup")
        except Exception as e:
            logger.error(f"Failed to build FAISS index: {e}")
    else:
        logger.success("FAISS index found — loading into memory")

    # Warm up FAISS index into memory
    try:
        faiss_ready = is_index_loaded()
        if faiss_ready:
            logger.success("FAISS index loaded and ready")
        else:
            logger.warning("FAISS index not ready after build attempt")
    except Exception as e:
        logger.warning(f"FAISS index not ready: {e}")

    logger.success("JourneyMind API startup complete")
    yield

    # ── Shutdown ──
    logger.info("JourneyMind API shutting down...")


# ─── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="JourneyMind AI",
    description="Intelligent travel planning powered by CrewAI 4-agent system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# ─── CORS ──────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "https://journeymind-ai.vercel.app",
        "https://venkata1236-journeymind-api.hf.space",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Routers ───────────────────────────────────────────────────────────────────

app.include_router(plan_router)
app.include_router(history_router)


# ─── Health ────────────────────────────────────────────────────────────────────

@app.get("/health", tags=["Health"])
async def health():
    return {
        "status":             "healthy",
        "environment":        settings.environment,
        "faiss_index_loaded": is_index_loaded(),
    }


@app.get("/", tags=["Root"])
async def root():
    return {
        "name":    "JourneyMind AI",
        "version": "1.0.0",
        "docs":    "/docs",
        "health":  "/health",
    }