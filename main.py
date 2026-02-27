import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database import engine as db_engine, Base
from backend.routers.fraud_router import router as fraud_router
from backend.routers.internal_router import router as internal_router
from backend.routers.analytics import router as analytics_router
from backend.ml.risk_engine import FraudEngine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=db_engine)

    fraud_engine = FraudEngine()
    try:
        fraud_engine.load()
        logger.info("FraudEngine loaded successfully.")
        logger.info("FraudEngine + Composite Intelligence Layer Version 1.0 Loaded")
    except RuntimeError as exc:
        logger.error("FraudEngine failed to load: %s", exc)

    app.state.fraud_engine = fraud_engine
    yield


app = FastAPI(
    title="PM-JAY Fraud Intelligence API",
    description="Hybrid rule + Isolation Forest fraud detection for Ayushman Bharat claims",
    version="3.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5500",
        "http://localhost",
        "http://127.0.0.1"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(fraud_router, prefix="/api/v1", tags=["Fraud Intelligence"])
app.include_router(internal_router, prefix="/api/v1", tags=["Internal / Benchmarking"])
app.include_router(analytics_router, prefix="/api/v1", tags=["Analytics"])

