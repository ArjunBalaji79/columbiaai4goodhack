"""
CrisisCore FastAPI Application
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from config import get_settings
from api.routes import router
from api.copilot import router as copilot_router
from api.resources import router as resources_router
from api.voice import router as voice_router
from api.websocket import websocket_endpoint
from orchestrator.coordinator import Coordinator

settings = get_settings()

# Global coordinator instance
_coordinator: Coordinator = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _coordinator
    _coordinator = Coordinator()
    await _coordinator.initialize()
    yield
    await _coordinator.shutdown()


app = FastAPI(
    title="CrisisCore API",
    description="Multimodal disaster response coordination system",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")
app.include_router(copilot_router, prefix="/api")
app.include_router(resources_router, prefix="/api")
app.include_router(voice_router, prefix="/api")
app.add_api_websocket_route("/ws", websocket_endpoint)

# Serve demo assets (images, audio) as static files
assets_dir = os.path.join(os.path.dirname(__file__), "demo_data", "assets")
if os.path.isdir(assets_dir):
    app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")


def get_coordinator() -> Coordinator:
    return _coordinator
