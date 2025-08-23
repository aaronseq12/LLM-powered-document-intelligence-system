"""
FastAPI application for LLM-powered document intelligence system.
Advanced FastAPI app with WebSocket support, authentication, and document processing.
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import Dict, List, Optional

import uvicorn
from fastapi import (
    FastAPI, File, Form, HTTPException, Depends, status, WebSocket,
    WebSocketDisconnect, UploadFile, BackgroundTasks
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
import jwt
from datetime import datetime, timedelta
import json

from config import settings
from database import get_db, create_tables, engine
from llm_service import LLMService
from azure_document_intelligence import AzureDocumentIntelligence
from redis_client import redis_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting message: {e}")

manager = ConnectionManager()

# Pydantic models
class DocumentProcessRequest(BaseModel):
    document_id: str
    extraction_type: str = Field(..., description="Type of extraction: 'structured', 'unstructured', or 'hybrid'")
    language: Optional[str] = Field(default="en", description="Document language code")
    confidence_threshold: Optional[float] = Field(default=0.8, description="Minimum confidence score")

class DocumentProcessResponse(BaseModel):
    document_id: str
    status: str
    extracted_data: Dict
    confidence_score: float
    processing_time: float
    metadata: Dict

class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: datetime
    dependencies: Dict[str, str]

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

# Initialize services
llm_service = LLMService()
azure_doc_intelligence = AzureDocumentIntelligence()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting up LLM Document Intelligence System")
    await create_tables()
    await redis_client.connect()
    await llm_service.initialize()
    await azure_doc_intelligence.initialize()
    
    yield
    
    # Shutdown
    logger.info("Shutting down LLM Document Intelligence System")
    await redis_client.disconnect()
    await engine.dispose()

# FastAPI app initialization
app = FastAPI(
    title="LLM-Powered Document Intelligence System",
    description="Enterprise-grade document processing with AI-powered extraction",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/api/redoc" if settings.ENVIRONMENT != "production" else None,
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS,
)

# Authentication functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(credentials.credentials, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    
    return username

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for monitoring"""
    dependencies = {
        "database": "healthy",
        "redis": "healthy" if await redis_client.ping() else "unhealthy",
        "llm_service": "healthy" if await llm_service.health_check() else "unhealthy",
        "azure_doc_intelligence": "healthy" if await azure_doc_intelligence.health_check() else "unhealthy"
    }
    
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.utcnow(),
        dependencies=dependencies
    )

# Authentication endpoints
@app.post("/auth/register", response_model=Token)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user"""
    # Implementation would include user creation in database
    # This is a simplified version
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/auth/login", response_model=Token)
async def login(username: str = Form(...), password: str = Form(...)):
    """Login user and return access token"""
    # Implementation would include user authentication
    # This is a simplified version
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Document processing endpoints
@app.post("/api/documents/upload", response_model=Dict[str, str])
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    extraction_type: str = Form(default="hybrid"),
    language: str = Form(default="en"),
    confidence_threshold: float = Form(default=0.8),
    current_user: str = Depends(get_current_user)
):
    """Upload and queue document for processing"""
    try:
        # Generate unique document ID
        document_id = f"doc_{datetime.utcnow().timestamp()}"
        
        # Save file temporarily
        file_path = f"/tmp/{document_id}_{file.filename}"
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Queue processing task
        background_tasks.add_task(
            process_document_async,
            document_id,
            file_path,
            extraction_type,
            language,
            confidence_threshold,
            current_user
        )
        
        return {
            "document_id": document_id,
            "status": "queued",
            "message": "Document uploaded successfully and queued for processing"
        }
        
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload document")

@app.post("/api/documents/process", response_model=DocumentProcessResponse)
async def process_document(
    request: DocumentProcessRequest,
    current_user: str = Depends(get_current_user)
):
    """Process document with specified parameters"""
    try:
        start_time = datetime.utcnow()
        
        # Check if result is cached
        cache_key = f"doc_result:{request.document_id}"
        cached_result = await redis_client.get(cache_key)
        
        if cached_result:
            logger.info(f"Returning cached result for document {request.document_id}")
            return json.loads(cached_result)
        
        # Process document with Azure Document Intelligence
        azure_result = await azure_doc_intelligence.analyze_document(
            document_id=request.document_id,
            extraction_type=request.extraction_type,
            language=request.language
        )
        
        # Enhance with LLM processing
        llm_result = await llm_service.enhance_extraction(
            azure_result,
            extraction_type=request.extraction_type,
            confidence_threshold=request.confidence_threshold
        )
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        response = DocumentProcessResponse(
            document_id=request.document_id,
            status="completed",
            extracted_data=llm_result["data"],
            confidence_score=llm_result["confidence"],
            processing_time=processing_time,
            metadata={
                "extraction_type": request.extraction_type,
                "language": request.language,
                "processed_by": current_user,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        # Cache result for 1 hour
        await redis_client.set(cache_key, response.json(), ex=3600)
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing document {request.document_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to process document")

@app.get("/api/documents/{document_id}/status")
async def get_document_status(
    document_id: str,
    current_user: str = Depends(get_current_user)
):
    """Get processing status of a document"""
    try:
        status_key = f"doc_status:{document_id}"
        status = await redis_client.get(status_key)
        
        if not status:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return json.loads(status)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get document status")

# WebSocket endpoint for real-time updates
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(f"Message: {data}", websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Background task for document processing
async def process_document_async(
    document_id: str,
    file_path: str,
    extraction_type: str,
    language: str,
    confidence_threshold: float,
    user: str
):
    """Background task for processing documents"""
    try:
        # Update status to processing
        status_key = f"doc_status:{document_id}"
        await redis_client.set(status_key, json.dumps({
            "status": "processing",
            "progress": 0,
            "message": "Starting document analysis"
        }))
        
        # Notify via WebSocket
        await manager.broadcast(json.dumps({
            "document_id": document_id,
            "status": "processing",
            "user": user
        }))
        
        # Process with Azure Document Intelligence
        await redis_client.set(status_key, json.dumps({
            "status": "processing",
            "progress": 25,
            "message": "Analyzing document structure"
        }))
        
        azure_result = await azure_doc_intelligence.analyze_document_file(
            file_path,
            extraction_type=extraction_type,
            language=language
        )
        
        # Enhance with LLM
        await redis_client.set(status_key, json.dumps({
            "status": "processing",
            "progress": 75,
            "message": "Enhancing with AI"
        }))
        
        llm_result = await llm_service.enhance_extraction(
            azure_result,
            extraction_type=extraction_type,
            confidence_threshold=confidence_threshold
        )
        
        # Complete processing
        final_result = {
            "status": "completed",
            "progress": 100,
            "extracted_data": llm_result["data"],
            "confidence_score": llm_result["confidence"],
            "processed_at": datetime.utcnow().isoformat()
        }
        
        await redis_client.set(status_key, json.dumps(final_result))
        
        # Notify completion
        await manager.broadcast(json.dumps({
            "document_id": document_id,
            "status": "completed",
            "user": user
        }))
        
        # Clean up temporary file
        if os.path.exists(file_path):
            os.remove(file_path)
            
    except Exception as e:
        logger.error(f"Error in background processing: {e}")
        await redis_client.set(status_key, json.dumps({
            "status": "failed",
            "error": str(e),
            "failed_at": datetime.utcnow().isoformat()
        }))

# Metrics endpoint for monitoring
@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint"""
    # Implementation would return Prometheus-formatted metrics
    return {"metrics": "# Prometheus metrics would be here"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.ENVIRONMENT == "development",
        workers=settings.WORKERS if settings.ENVIRONMENT == "production" else 1
    )