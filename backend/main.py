import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.core.config import settings
from backend.app.core.database import init_db
from backend.app.api.endpoints import auth, meetings, transcript, mom, export, search
from backend.app.websockets.meeting_socket import ws_manager
from backend.app.services.dataset_eval import dataset_evaluator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('mom_backend')

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing MoM Generator Database & Models...")
    await init_db()
    yield
    logger.info("MoM Generator Application Shutdown.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Automated Minutes of Meeting (MoM) Generator with task-specific NLP/ML pipeline and live transcription.",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(search.router, prefix=settings.API_V1_STR)
app.include_router(meetings.router, prefix=settings.API_V1_STR)
app.include_router(transcript.router, prefix=settings.API_V1_STR)
app.include_router(mom.router, prefix=settings.API_V1_STR)
app.include_router(export.router, prefix=settings.API_V1_STR)

@app.get(f"{settings.API_V1_STR}/benchmark")
async def get_system_benchmark():
    """Returns NLP/ASR benchmark metrics across AMI, ICSI+AIMU, MeetingBank, QMSum, and Custom MoM Dataset"""
    return dataset_evaluator.get_benchmark_scores()

@app.get(f"{settings.API_V1_STR}/health")
async def health_check():
    return {"status": "healthy", "service": settings.PROJECT_NAME, "version": settings.VERSION}

# WebSocket Endpoint for Live Meetings
@app.websocket("/ws/meetings/{meeting_id}")
async def websocket_meeting_endpoint(websocket: WebSocket, meeting_id: int):
    await ws_manager.connect(meeting_id, websocket)
    try:
        while True:
            # Handle binary audio or json control message
            message = await websocket.receive()
            if "bytes" in message and message["bytes"]:
                await ws_manager.handle_audio_stream_or_message(meeting_id, message["bytes"], user_id=1)
            elif "text" in message and message["text"]:
                await ws_manager.handle_audio_stream_or_message(meeting_id, message["text"], user_id=1)
    except WebSocketDisconnect:
        ws_manager.disconnect(meeting_id, websocket)
    except Exception as e:
        logger.error(f"WebSocket error in meeting {meeting_id}: {e}")
        ws_manager.disconnect(meeting_id, websocket)

# Mount frontend build if available
frontend_dist = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
