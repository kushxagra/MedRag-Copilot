import logging

from fastapi import FastAPI

from app.core.config import settings
from app.core.logging import configure_logging

configure_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.app_name, version="0.1.0")


@app.on_event("startup")
def on_startup() -> None:
    logger.info("MedRAG Copilot starting up")


@app.get("/health")
def health_check():
    logger.info("Health check called")
    return {"status": "ok"}
