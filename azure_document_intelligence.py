"""
Azure AI Document Intelligence Integration

This module provides a service for interacting with the Azure AI Document
Intelligence API. It encapsulates the logic for analyzing documents,
extracting data, and structuring the results.

Key Features:
- Asynchronous client for non-blocking I/O.
- Handles document analysis from file paths and in-memory content.
- Structures the complex API response into a more usable format.
- Includes health checks and validation for robustness.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest, AnalyzeResult
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError

from config import settings

# Standard library imports for file handling
import os

logger = logging.getLogger(__name__)

class AzureDocumentIntelligenceService:
    """
    A service class for interacting with Azure's Document Intelligence API.
    Manages the client lifecycle, document analysis, and result processing.
    """
    
    def __init__(self):
        self.client: Optional[DocumentIntelligenceClient] = None
        self.is_initialized = False
        self._initialization_lock = asyncio.Lock()
    
    async def initialize(self):
        """
        Initializes the Azure Document Intelligence client.
        This method is thread-safe and ensures the client is initialized only once.
        """
        async with self._initialization_lock:
            if self.is_initialized:
                return
            
            try:
                config = settings.get_azure_document_intelligence_config()
                
                if not config['key'] or not config['endpoint']:
                    raise ValueError("Azure Document Intelligence credentials are not configured.")
                
                credential = AzureKeyCredential(config['key'])
                self.client = DocumentIntelligenceClient(endpoint=config['endpoint'], credential=credential)
                
                self.is_initialized = True
                logger.info("Azure Document Intelligence client initialized successfully.")
                
            except Exception as e:
                logger.error(f"Failed to initialize Azure Document Intelligence: {e}")
                raise
    
    async def check_health(self) -> bool:
        """
        Performs a health check on the Azure Document Intelligence service.
        Returns True if the service is responsive, False otherwise.
        """
        if not self.is_initialized:
            return False
        
        try:
            # A simple way to check health is to see if the client is not None.
            # A more robust check might involve a lightweight API call.
            return self.client is not None
        except Exception:
            return False
    
    async def analyze_document_from_file(
        self,
        file_path: str,
        model_id: str = "prebuilt-document"
    ) -> Dict[str, Any]:
        """
        Analyzes a document from a given file path.

        Args:
            file_path: The local path to the document file.
            model_id: The ID of the model to use for analysis.

        Returns:
            A dictionary containing the structured analysis result.
        """
        if not self.is_initialized:
            await self.initialize()
            
        try:
            with open(file_path, "rb") as f:
                document_content = f.read()
            
            return await self.analyze_document_from_content(document_content, model_id)
            
        except FileNotFoundError:
            logger.error(f"File not found at path: {file_path}")
            raise
        except Exception as e:
            logger.error(f"Error analyzing document file {file_path}: {e}")
            raise
    
    async def analyze_document_from_content(
        self,
        document_content: bytes,
        model_id: str = "prebuilt-document"
    ) -> Dict[str, Any]:
        """
        Analyzes a document from its byte content.

        Args:
            document_content: The byte content of the document.
            model_id: The ID of the model to use for analysis.

        Returns:
            A dictionary containing the structured analysis result.
        """
        if not self.is_initialized:
            await self.initialize()
        
        try:
            start_time = datetime.utcnow()
            
            poller = self.client.begin_analyze_document(
                model_id=model_id,
                analyze_request=AnalyzeDocumentRequest(bytes_source=document_content)
            )
            result: AnalyzeResult = poller.result()
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            structured_result = self._structure_analysis_result(result, processing_time)
            
            logger.info(f"Document analysis completed in {processing_time:.2f} seconds.")
            
            return structured_result
            
        except HttpResponseError as e:
            logger.error(f"Azure Document Intelligence API error: {e}")
            raise
        except Exception as e:
            logger.error(f"An unexpected error occurred during document analysis: {e}")
            raise
    
    def _structure_analysis_result(
        self,
        result: AnalyzeResult,
        processing_time: float
    ) -> Dict[str, Any]:
        """
        Transforms the raw Azure API response into a more structured and usable format.

        Args:
            result: The AnalyzeResult object from the Azure SDK.
            processing_time: The time taken for the analysis.

        Returns:
            A structured dictionary of the analysis results.
        """
        
        structured_content = {
            "full_text": result.content,
            "pages": [],
            "tables": [],
            "key_value_pairs": [],
        }

        # Process pages and their content
        if result.pages:
            for page in result.pages:
                structured_content["pages"].append({
                    "page_number": page.page_number,
                    "lines": [line.content for line in page.lines],
                })

        # Process tables
        if result.tables:
            for table in result.tables:
                structured_content["tables"].append({
                    "row_count": table.row_count,
                    "column_count": table.column_count,
                    "cells": [
                        {
                            "content": cell.content,
                            "row_index": cell.row_index,
                            "column_index": cell.column_index,
                        }
                        for cell in table.cells
                    ],
                })

        # Process key-value pairs
        if result.key_value_pairs:
            for kv_pair in result.key_value_pairs:
                structured_content["key_value_pairs"].append({
                    "key": kv_pair.key.content,
                    "value": kv_pair.value.content if kv_pair.value else None,
                    "confidence": kv_pair.confidence,
                })

        return {
            "processing_time_seconds": processing_time,
            "processed_at": datetime.utcnow().isoformat(),
            "model_id": result.model_id,
            "content": structured_content,
        }

# --- Singleton Instance ---
# This ensures that only one instance of the service is used throughout the application.
azure_document_intelligence_service = AzureDocumentIntelligenceService()

