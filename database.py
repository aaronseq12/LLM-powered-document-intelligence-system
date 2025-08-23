"""
SQLAlchemy 2.0+ async database system for LLM Document Intelligence System.
Handles database connections, models, and session management.
"""

import logging
from datetime import datetime
from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Float, Boolean,
    JSON, ForeignKey, Index, UniqueConstraint
)
from sqlalchemy.ext.asyncio import (
    AsyncSession, async_sessionmaker, create_async_engine,
    AsyncEngine
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, selectinload
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import uuid

from config import settings

logger = logging.getLogger(__name__)

# Base class for all models
Base = declarative_base()

# Database engine with connection pooling
engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.is_development,
    **settings.get_database_config()
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


class TimestampMixin:
    """Mixin for adding created_at and updated_at timestamps."""
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class User(Base, TimestampMixin):
    """User model for authentication and authorization."""
    
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    
    # Relationships
    documents = relationship("Document", back_populates="user", lazy="selectin")
    processing_jobs = relationship("ProcessingJob", back_populates="user", lazy="selectin")
    
    # Indexes
    __table_args__ = (
        Index("idx_user_username", "username"),
        Index("idx_user_email", "email"),
        Index("idx_user_active", "is_active"),
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"


class Document(Base, TimestampMixin):
    """Document model for storing document metadata and processing results."""
    
    __tablename__ = "documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_hash = Column(String(64), nullable=False, index=True)
    
    # Document metadata
    language = Column(String(10), default="en")
    page_count = Column(Integer)
    
    # Processing information
    processing_status = Column(String(20), default="pending", index=True)
    extraction_type = Column(String(20), nullable=False)
    confidence_threshold = Column(Float, default=0.8)
    
    # Results
    extracted_data = Column(JSON)
    confidence_score = Column(Float)
    processing_time_seconds = Column(Float)
    error_message = Column(Text)
    
    # Foreign keys
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="documents")
    processing_jobs = relationship("ProcessingJob", back_populates="document", lazy="selectin")
    extractions = relationship("DataExtraction", back_populates="document", lazy="selectin")
    
    # Indexes
    __table_args__ = (
        Index("idx_document_user_id", "user_id"),
        Index("idx_document_status", "processing_status"),
        Index("idx_document_hash", "file_hash"),
        Index("idx_document_created", "created_at"),
        UniqueConstraint("file_hash", "user_id", name="uq_document_hash_user"),
    )
    
    def __repr__(self):
        return f"<Document(id={self.id}, filename='{self.filename}', status='{self.processing_status}')>"


class ProcessingJob(Base, TimestampMixin):
    """Processing job model for tracking document processing tasks."""
    
    __tablename__ = "processing_jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_type = Column(String(50), nullable=False)  # 'document_analysis', 'llm_enhancement'
    status = Column(String(20), default="queued", index=True)  # queued, processing, completed, failed
    progress_percentage = Column(Integer, default=0)
    
    # Job parameters
    parameters = Column(JSON)
    
    # Results
    result = Column(JSON)
    error_message = Column(Text)
    
    # Timing
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    processing_time_seconds = Column(Float)
    
    # Foreign keys
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="processing_jobs")
    document = relationship("Document", back_populates="processing_jobs")
    
    # Indexes
    __table_args__ = (
        Index("idx_processing_job_user_id", "user_id"),
        Index("idx_processing_job_document_id", "document_id"),
        Index("idx_processing_job_status", "status"),
        Index("idx_processing_job_type", "job_type"),
        Index("idx_processing_job_created", "created_at"),
    )
    
    def __repr__(self):
        return f"<ProcessingJob(id={self.id}, type='{self.job_type}', status='{self.status}')>"


class DataExtraction(Base, TimestampMixin):
    """Data extraction model for storing specific extracted data items."""
    
    __tablename__ = "data_extractions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Extraction metadata
    extraction_type = Column(String(50), nullable=False)  # 'text', 'table', 'form', 'key_value'
    field_name = Column(String(255))
    field_type = Column(String(50))
    
    # Extracted content
    extracted_text = Column(Text)
    extracted_value = Column(Text)
    structured_data = Column(JSON)
    
    # Quality metrics
    confidence_score = Column(Float)
    bounding_box = Column(JSON)  # Coordinates on the page
    page_number = Column(Integer)
    
    # Azure Document Intelligence specific
    azure_field_id = Column(String(255))
    azure_confidence = Column(Float)
    
    # LLM enhancement
    llm_enhanced = Column(Boolean, default=False)
    llm_confidence = Column(Float)
    llm_reasoning = Column(Text)
    
    # Foreign keys
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    
    # Relationships
    document = relationship("Document", back_populates="extractions")
    
    # Indexes
    __table_args__ = (
        Index("idx_data_extraction_document_id", "document_id"),
        Index("idx_data_extraction_type", "extraction_type"),
        Index("idx_data_extraction_field_name", "field_name"),
        Index("idx_data_extraction_confidence", "confidence_score"),
        Index("idx_data_extraction_page", "page_number"),
    )
    
    def __repr__(self):
        return f"<DataExtraction(id={self.id}, type='{self.extraction_type}', field='{self.field_name}')>"


class ProcessingMetrics(Base, TimestampMixin):
    """Processing metrics model for performance monitoring."""
    
    __tablename__ = "processing_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Metric information
    metric_name = Column(String(100), nullable=False, index=True)
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String(20))
    
    # Context
    document_type = Column(String(50))
    processing_stage = Column(String(50))
    model_version = Column(String(50))
    
    # Metadata
    metadata = Column(JSON)
    
    # Foreign keys
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Indexes
    __table_args__ = (
        Index("idx_metrics_name", "metric_name"),
        Index("idx_metrics_document_id", "document_id"),
        Index("idx_metrics_user_id", "user_id"),
        Index("idx_metrics_created", "created_at"),
        Index("idx_metrics_name_created", "metric_name", "created_at"),
    )
    
    def __repr__(self):
        return f"<ProcessingMetrics(metric='{self.metric_name}', value={self.metric_value})>"


class AuditLog(Base, TimestampMixin):
    """Audit log model for tracking system events."""
    
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Event information
    event_type = Column(String(50), nullable=False, index=True)
    event_description = Column(Text, nullable=False)
    
    # Context
    resource_type = Column(String(50))  # 'document', 'user', 'processing_job'
    resource_id = Column(String(255), index=True)
    
    # User context
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    user_ip = Column(String(45))
    user_agent = Column(Text)
    
    # Additional data
    metadata = Column(JSON)
    
    # Indexes
    __table_args__ = (
        Index("idx_audit_event_type", "event_type"),
        Index("idx_audit_resource", "resource_type", "resource_id"),
        Index("idx_audit_user_id", "user_id"),
        Index("idx_audit_created", "created_at"),
    )
    
    def __repr__(self):
        return f"<AuditLog(event='{self.event_type}', resource='{self.resource_type}')>"


# Database session dependency
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()


async def create_tables():
    """Create all database tables."""
    try:
        async with engine.begin() as conn:
            logger.info("Creating database tables...")
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise


async def drop_tables():
    """Drop all database tables."""
    try:
        async with engine.begin() as conn:
            logger.info("Dropping database tables...")
            await conn.run_sync(Base.metadata.drop_all)
            logger.info("Database tables dropped successfully")
    except Exception as e:
        logger.error(f"Error dropping database tables: {e}")
        raise


async def check_database_connection() -> bool:
    """Check if database connection is working."""
    try:
        async with engine.begin() as conn:
            await conn.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False


async def get_database_stats():
    """Get database statistics."""
    try:
        async with AsyncSessionLocal() as session:
            # Get table row counts
            stats = {}
            
            for table_name, model in [
                ("users", User),
                ("documents", Document),
                ("processing_jobs", ProcessingJob),
                ("data_extractions", DataExtraction),
                ("processing_metrics", ProcessingMetrics),
                ("audit_logs", AuditLog),
            ]:
                result = await session.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = result.scalar()
                stats[table_name] = count
            
            return stats
            
    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
        return {}


# Repository classes for data access
class BaseRepository:
    """Base repository class with common database operations."""
    
    def __init__(self, session: AsyncSession, model_class):
        self.session = session
        self.model_class = model_class
    
    async def get_by_id(self, id: uuid.UUID):
        """Get record by ID."""
        return await self.session.get(self.model_class, id)
    
    async def create(self, **kwargs):
        """Create new record."""
        instance = self.model_class(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        return instance
    
    async def update(self, id: uuid.UUID, **kwargs):
        """Update record by ID."""
        instance = await self.get_by_id(id)
        if instance:
            for key, value in kwargs.items():
                setattr(instance, key, value)
            await self.session.flush()
        return instance
    
    async def delete(self, id: uuid.UUID):
        """Delete record by ID."""
        instance = await self.get_by_id(id)
        if instance:
            await self.session.delete(instance)
            await self.session.flush()
        return instance


class DocumentRepository(BaseRepository):
    """Repository for document operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, Document)
    
    async def get_by_user_id(self, user_id: uuid.UUID, limit: int = 50, offset: int = 0):
        """Get documents by user ID with pagination."""
        from sqlalchemy import select
        
        query = (
            select(Document)
            .where(Document.user_id == user_id)
            .order_by(Document.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_by_hash(self, file_hash: str, user_id: uuid.UUID):
        """Get document by file hash and user ID."""
        from sqlalchemy import select
        
        query = select(Document).where(
            Document.file_hash == file_hash,
            Document.user_id == user_id
        )
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()


class UserRepository(BaseRepository):
    """Repository for user operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, User)
    
    async def get_by_username(self, username: str):
        """Get user by username."""
        from sqlalchemy import select
        
        query = select(User).where(User.username == username)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str):
        """Get user by email."""
        from sqlalchemy import select
        
        query = select(User).where(User.email == email)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()