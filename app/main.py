import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.ask import router as ask_router
from app.core.config import settings
from app.core.logging import configure_logging

configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("MedRAG Copilot starting up")
    yield
    logger.info("MedRAG Copilot shutting down")


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
app.include_router(ask_router)
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/health")
def health_check():
    logger.info("Health check called")
    return {"status": "ok"}


@app.get("/")
def serve_frontend():
    return FileResponse("app/static/index.html")
