"""
Main FastAPI Application for the LLM Document Intelligence System

This file defines the core FastAPI application, including its routes, middleware,
and lifecycle events. It serves as the main entry point for the backend API.
"""

import logging
from contextlib import asynccontextmanager
from typing import Dict
from datetime import datetime
import json
import os
import uuid

from fastapi import (
    FastAPI, File, Form, HTTPException, Depends, WebSocket,
    WebSocketDisconnect, UploadFile, BackgroundTasks
)
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db_session, init_db
from app.llm_service import llm_service
from app.azure_document_intelligence import azure_document_intelligence_service
from app.redis_client import redis_client
from app.auth import create_access_token, get_current_user
from app.websocket_manager import ConnectionManager
from app.schemas import HealthResponse, Token

# --- Logging Configuration ---
logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

# --- WebSocket Connection Manager ---
connection_manager = ConnectionManager()


# --- Application Lifecycle Events ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles application startup and shutdown events."""
    logger.info("Initializing LLM Document Intelligence System...")
    await init_db()
    await redis_client.connect()
    await llm_service.initialize()
    await azure_document_intelligence_service.initialize()
    logger.info("System startup complete.")
    yield
    logger.info("Shutting down...")
    await redis_client.disconnect()
    logger.info("System shutdown complete.")


# --- FastAPI App Initialization ---
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
    description="An enterprise-grade platform for intelligent document processing.",
)

# --- Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.ALLOWED_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- API Endpoints ---

@app.get("/health", response_model=HealthResponse, tags=["Monitoring"])
async def health_check():
    """Provides a health check endpoint for monitoring."""
    return HealthResponse(
        status="ok",
        version=settings.VERSION,
        timestamp=datetime.utcnow()
    )


@app.post("/auth/token", response_model=Token, tags=["Authentication"])
async def login_for_access_token(username: str = Form(...), password: str = Form(...)):
    """Authenticates a user and returns a JWT access token."""
    # In a real application, you would verify the username and password against the database.
    if not password: # Simplified for this example
        raise HTTPException(status_code=400, detail="Password is required")
    access_token = create_access_token(data={"sub": username})
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/api/documents", tags=["Documents"])
async def upload_document_for_processing(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Uploads a document and queues it for asynchronous processing."""
    try:
        document_id = str(uuid.uuid4())
        file_extension = os.path.splitext(file.filename)[1]
        file_path = os.path.join(settings.UPLOAD_DIRECTORY, f"{document_id}{file_extension}")

        os.makedirs(settings.UPLOAD_DIRECTORY, exist_ok=True)

        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())

        background_tasks.add_task(
            process_document_in_background,
            document_id,
            file_path,
            current_user
        )

        return {"document_id": document_id, "status": "queued", "filename": file.filename}

    except Exception as e:
        logger.error(f"Error uploading document: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to upload document.")


@app.get("/api/documents/{document_id}/status", tags=["Documents"])
async def get_document_processing_status(document_id: str):
    """Retrieves the processing status of a document."""
    status = await redis_client.get(f"doc_status:{document_id}")
    if not status:
        raise HTTPException(status_code=404, detail="Document not found or processing not started.")
    return status


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """Provides a WebSocket endpoint for real-time updates."""
    await connection_manager.connect(websocket)
    try:
        while True:
            # Keep the connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
        logger.info(f"WebSocket client {client_id} disconnected.")


# --- Background Processing Task ---
async def process_document_in_background(document_id: str, file_path: str, user: str):
    """
    The background task that processes the uploaded document.
    It updates the status in Redis and broadcasts updates via WebSockets.
    """
    status_key = f"doc_status:{document_id}"

    async def update_status(status: str, progress: int, data: dict = None):
        status_payload = {"status": status, "progress": progress, "document_id": document_id, "data": data}
        await redis_client.set(status_key, status_payload)
        await connection_manager.broadcast(json.dumps(status_payload))

    try:
        await update_status("processing", 10)

        azure_result = await azure_document_intelligence_service.analyze_document_from_file(file_path)
        await update_status("analyzing", 50)

        llm_result = await llm_service.enhance_extracted_data(azure_result)
        await update_status("enhancing", 90)

        final_result = {
            "data": llm_result.get("data"),
            "processed_at": datetime.utcnow().isoformat(),
            "metrics": llm_result.get("metrics")
        }
        await redis_client.set(f"doc_result:{document_id}", final_result)
        await update_status("completed", 100, final_result)
        logger.info(f"Document {document_id} processed successfully for user {user}.")

    except Exception as e:
        logger.error(f"Error processing document {document_id}: {e}", exc_info=True)
        error_payload = {"status": "failed", "error": str(e), "document_id": document_id}
        await redis_client.set(status_key, error_payload)
        await connection_manager.broadcast(json.dumps(error_payload))

    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Cleaned up temporary file: {file_path}")
