"""
Azure AI Document Intelligence integration for LLM Document Intelligence System.
Provides advanced OCR, form recognition, and document analysis capabilities.
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

import aiohttp
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import (
    AnalyzeDocumentRequest, AnalyzeResult, Document, DocumentTable,
    DocumentKeyValuePair, DocumentField, BoundingRegion
)
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError, ServiceRequestError

from config import settings

logger = logging.getLogger(__name__)


class AzureDocumentIntelligence:
    """Service for Azure AI Document Intelligence operations."""
    
    def __init__(self):
        self.client: Optional[DocumentIntelligenceClient] = None
        self.initialized = False
        self._lock = asyncio.Lock()
        self.supported_file_types = [
            '.pdf', '.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.heif'
        ]
        self.max_file_size = 50 * 1024 * 1024  # 50MB
    
    async def initialize(self):
        """Initialize Azure Document Intelligence client."""
        async with self._lock:
            if self.initialized:
                return
            
            try:
                config = settings.get_azure_document_intelligence_config()
                
                if not config['key'] or not config['endpoint']:
                    raise ValueError("Azure Document Intelligence credentials not configured")
                
                credential = AzureKeyCredential(config['key'])
                
                self.client = DocumentIntelligenceClient(
                    endpoint=config['endpoint'],
                    credential=credential,
                    api_version=config['api_version']
                )
                
                self.initialized = True
                logger.info("Azure Document Intelligence client initialized successfully")
                
            except Exception as e:
                logger.error(f"Failed to initialize Azure Document Intelligence: {e}")
                raise
    
    async def health_check(self) -> bool:
        """Check Azure Document Intelligence service health."""
        if not self.initialized:
            return False
        
        try:
            # Test with a simple operation
            # In a real implementation, you might want to test with a small document
            return self.client is not None
        except Exception:
            return False
    
    def _validate_file(self, file_path: str) -> Dict[str, Any]:
        """Validate file for processing."""
        if not os.path.exists(file_path):
            return {
                'valid': False,
                'error': f'File not found: {file_path}'
            }
        
        file_size = os.path.getsize(file_path)
        if file_size > self.max_file_size:
            return {
                'valid': False,
                'error': f'File too large: {file_size} bytes (max: {self.max_file_size})'
            }
        
        file_extension = os.path.splitext(file_path)[1].lower()
        if file_extension not in self.supported_file_types:
            return {
                'valid': False,
                'error': f'Unsupported file type: {file_extension}'
            }
        
        return {
            'valid': True,
            'file_size': file_size,
            'file_type': file_extension
        }
    
    async def analyze_document_file(
        self,
        file_path: str,
        extraction_type: str = "prebuilt-document",
        language: str = "en",
        features: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Analyze document from file path."""
        if not self.initialized:
            await self.initialize()
        
        # Validate file
        validation = self._validate_file(file_path)
        if not validation['valid']:
            raise ValueError(validation['error'])
        
        try:
            with open(file_path, 'rb') as file:
                file_content = file.read()
            
            return await self.analyze_document_content(
                file_content,
                extraction_type=extraction_type,
                language=language,
                features=features
            )
            
        except Exception as e:
            logger.error(f"Error analyzing document file {file_path}: {e}")
            raise
    
    async def analyze_document_content(
        self,
        file_content: bytes,
        extraction_type: str = "prebuilt-document",
        language: str = "en",
        features: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Analyze document from file content bytes."""
        if not self.initialized:
            await self.initialize()
        
        try:
            start_time = datetime.utcnow()
            
            # Prepare analyze request
            analyze_request = AnalyzeDocumentRequest(bytes_source=file_content)
            
            # Map extraction type to model ID
            model_id = self._get_model_id(extraction_type)
            
            # Set features if provided
            analysis_features = features or self._get_default_features(extraction_type)
            
            logger.info(f"Starting document analysis with model: {model_id}")
            
            # Start the analysis operation
            poller = self.client.begin_analyze_document(
                model_id=model_id,
                analyze_request=analyze_request,
                locale=language,
                features=analysis_features
            )
            
            # Wait for completion
            result: AnalyzeResult = poller.result()
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Process and structure the results
            structured_result = self._structure_analysis_result(
                result, extraction_type, processing_time
            )
            
            logger.info(f"Document analysis completed in {processing_time:.2f}s")
            
            return structured_result
            
        except HttpResponseError as e:
            logger.error(f"Azure Document Intelligence HTTP error: {e}")
            raise
        except ServiceRequestError as e:
            logger.error(f"Azure Document Intelligence service error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in document analysis: {e}")
            raise
    
    async def analyze_document(
        self,
        document_id: str,
        extraction_type: str = "prebuilt-document",
        language: str = "en",
        features: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Analyze document by document ID (assumes document is stored)."""
        # This would typically retrieve the document from storage
        # For now, we'll return a placeholder structure
        logger.warning(f"Document ID analysis not implemented for: {document_id}")
        
        return {
            'document_id': document_id,
            'status': 'pending',
            'extraction_type': extraction_type,
            'language': language,
            'features': features or [],
            'message': 'Document ID analysis not yet implemented'
        }
    
    def _get_model_id(self, extraction_type: str) -> str:
        """Map extraction type to Azure model ID."""
        model_mapping = {
            'structured': 'prebuilt-document',
            'unstructured': 'prebuilt-read',
            'hybrid': 'prebuilt-document',
            'layout': 'prebuilt-layout',
            'general_document': 'prebuilt-document',
            'invoice': 'prebuilt-invoice',
            'receipt': 'prebuilt-receipt',
            'business_card': 'prebuilt-businessCard',
            'identity_document': 'prebuilt-idDocument',
            'tax_document': 'prebuilt-tax.us.w2',
            'contract': 'prebuilt-contract'
        }
        
        return model_mapping.get(extraction_type, 'prebuilt-document')
    
    def _get_default_features(self, extraction_type: str) -> List[str]:
        """Get default analysis features for extraction type."""
        if extraction_type in ['structured', 'hybrid']:
            return ['keyValuePairs', 'tables', 'styles', 'languages']
        elif extraction_type == 'unstructured':
            return ['styles', 'languages']
        elif extraction_type == 'layout':
            return ['styles', 'languages', 'tables']
        else:
            return ['keyValuePairs', 'tables', 'styles', 'languages']
    
    def _structure_analysis_result(
        self,
        result: AnalyzeResult,
        extraction_type: str,
        processing_time: float
    ) -> Dict[str, Any]:
        """Structure the Azure analysis result into a standardized format."""
        
        structured_result = {
            'extraction_type': extraction_type,
            'processing_time_seconds': processing_time,
            'processed_at': datetime.utcnow().isoformat(),
            'confidence_score': self._calculate_overall_confidence(result),
            'content': {},
            'metadata': {
                'model_id': result.model_id,
                'api_version': getattr(result, 'api_version', 'unknown'),
                'page_count': len(result.pages) if result.pages else 0
            }
        }
        
        # Extract content based on what's available
        if result.content:
            structured_result['content']['full_text'] = result.content
        
        # Process pages
        if result.pages:
            structured_result['content']['pages'] = []
            for page_idx, page in enumerate(result.pages):
                page_content = {
                    'page_number': page_idx + 1,
                    'width': page.width,
                    'height': page.height,
                    'unit': page.unit,
                    'angle': page.angle,
                    'lines': [],
                    'words': [],
                    'spans': []
                }
                
                # Extract lines
                if page.lines:
                    for line in page.lines:
                        line_data = {
                            'content': line.content,
                            'bounding_box': self._extract_bounding_box(line.polygon) if line.polygon else None,
                            'spans': [{'offset': span.offset, 'length': span.length} for span in line.spans] if line.spans else []
                        }
                        page_content['lines'].append(line_data)
                
                # Extract words
                if page.words:
                    for word in page.words:
                        word_data = {
                            'content': word.content,
                            'confidence': word.confidence,
                            'bounding_box': self._extract_bounding_box(word.polygon) if word.polygon else None,
                            'span': {'offset': word.span.offset, 'length': word.span.length} if word.span else None
                        }
                        page_content['words'].append(word_data)
                
                structured_result['content']['pages'].append(page_content)
        
        # Process tables
        if result.tables:
            structured_result['content']['tables'] = []
            for table_idx, table in enumerate(result.tables):
                table_data = {
                    'table_number': table_idx + 1,
                    'row_count': table.row_count,
                    'column_count': table.column_count,
                    'confidence': getattr(table, 'confidence', None),
                    'bounding_regions': self._extract_bounding_regions(table.bounding_regions) if table.bounding_regions else [],
                    'cells': []
                }
                
                if table.cells:
                    for cell in table.cells:
                        cell_data = {
                            'content': cell.content,
                            'row_index': cell.row_index,
                            'column_index': cell.column_index,
                            'row_span': cell.row_span,
                            'column_span': cell.column_span,
                            'confidence': getattr(cell, 'confidence', None),
                            'kind': cell.kind,
                            'bounding_regions': self._extract_bounding_regions(cell.bounding_regions) if cell.bounding_regions else []
                        }
                        table_data['cells'].append(cell_data)
                
                structured_result['content']['tables'].append(table_data)
        
        # Process key-value pairs
        if result.key_value_pairs:
            structured_result['content']['key_value_pairs'] = []
            for kv_pair in result.key_value_pairs:
                kv_data = {
                    'key': {
                        'content': kv_pair.key.content if kv_pair.key else None,
                        'confidence': getattr(kv_pair.key, 'confidence', None) if kv_pair.key else None,
                        'bounding_regions': self._extract_bounding_regions(kv_pair.key.bounding_regions) if kv_pair.key and kv_pair.key.bounding_regions else []
                    },
                    'value': {
                        'content': kv_pair.value.content if kv_pair.value else None,
                        'confidence': getattr(kv_pair.value, 'confidence', None) if kv_pair.value else None,
                        'bounding_regions': self._extract_bounding_regions(kv_pair.value.bounding_regions) if kv_pair.value and kv_pair.value.bounding_regions else []
                    },
                    'confidence': kv_pair.confidence
                }
                structured_result['content']['key_value_pairs'].append(kv_data)
        
        # Process documents (for prebuilt models)
        if result.documents:
            structured_result['content']['documents'] = []
            for doc in result.documents:
                doc_data = {
                    'doc_type': doc.doc_type,
                    'confidence': doc.confidence,
                    'bounding_regions': self._extract_bounding_regions(doc.bounding_regions) if doc.bounding_regions else [],
                    'fields': {}
                }
                
                if doc.fields:
                    for field_name, field_value in doc.fields.items():
                        doc_data['fields'][field_name] = self._extract_document_field(field_value)
                
                structured_result['content']['documents'].append(doc_data)
        
        # Process languages
        if result.languages:
            structured_result['content']['languages'] = []
            for lang in result.languages:
                lang_data = {
                    'locale': lang.locale,
                    'confidence': lang.confidence,
                    'spans': [{'offset': span.offset, 'length': span.length} for span in lang.spans] if lang.spans else []
                }
                structured_result['content']['languages'].append(lang_data)
        
        # Process styles
        if result.styles:
            structured_result['content']['styles'] = []
            for style in result.styles:
                style_data = {
                    'is_handwritten': style.is_handwritten,
                    'confidence': style.confidence,
                    'spans': [{'offset': span.offset, 'length': span.length} for span in style.spans] if style.spans else []
                }
                structured_result['content']['styles'].append(style_data)
        
        return structured_result
    
    def _extract_bounding_box(self, polygon) -> Optional[Dict[str, float]]:
        """Extract bounding box from polygon."""
        if not polygon:
            return None
        
        try:
            # Convert polygon to bounding box (top-left, bottom-right)
            x_coords = [point.x for point in polygon]
            y_coords = [point.y for point in polygon]
            
            return {
                'x': min(x_coords),
                'y': min(y_coords),
                'width': max(x_coords) - min(x_coords),
                'height': max(y_coords) - min(y_coords)
            }
        except Exception:
            return None
    
    def _extract_bounding_regions(self, bounding_regions) -> List[Dict[str, Any]]:
        """Extract bounding regions information."""
        if not bounding_regions:
            return []
        
        regions = []
        for region in bounding_regions:
            region_data = {
                'page_number': region.page_number,
                'bounding_box': self._extract_bounding_box(region.polygon) if region.polygon else None
            }
            regions.append(region_data)
        
        return regions
    
    def _extract_document_field(self, field) -> Dict[str, Any]:
        """Extract document field information."""
        if not field:
            return {}
        
        field_data = {
            'type': field.type,
            'confidence': field.confidence,
            'content': field.content,
            'bounding_regions': self._extract_bounding_regions(field.bounding_regions) if field.bounding_regions else []
        }
        
        # Handle different field types
        if hasattr(field, 'value') and field.value is not None:
            if field.type == 'array':
                field_data['value'] = [self._extract_document_field(item) for item in field.value]
            elif field.type == 'object':
                field_data['value'] = {k: self._extract_document_field(v) for k, v in field.value.items()}
            else:
                field_data['value'] = field.value
        
        return field_data
    
    def _calculate_overall_confidence(self, result: AnalyzeResult) -> float:
        """Calculate overall confidence score from analysis result."""
        confidence_scores = []
        
        # Collect confidence scores from various elements
        if result.pages:
            for page in result.pages:
                if page.words:
                    confidence_scores.extend([word.confidence for word in page.words if word.confidence is not None])
        
        if result.tables:
            for table in result.tables:
                if hasattr(table, 'confidence') and table.confidence is not None:
                    confidence_scores.append(table.confidence)
                if table.cells:
                    confidence_scores.extend([cell.confidence for cell in table.cells if hasattr(cell, 'confidence') and cell.confidence is not None])
        
        if result.key_value_pairs:
            confidence_scores.extend([kv.confidence for kv in result.key_value_pairs if kv.confidence is not None])
        
        if result.documents:
            confidence_scores.extend([doc.confidence for doc in result.documents if doc.confidence is not None])
        
        # Calculate average confidence
        if confidence_scores:
            return round(sum(confidence_scores) / len(confidence_scores), 3)
        else:
            return 0.5  # Default confidence when no scores available
    
    async def get_supported_models(self) -> List[Dict[str, Any]]:
        """Get list of supported prebuilt models."""
        if not self.initialized:
            await self.initialize()
        
        try:
            # Get list of available models
            models = self.client.get_models()
            
            supported_models = []
            for model in models:
                model_info = {
                    'model_id': model.model_id,
                    'description': getattr(model, 'description', ''),
                    'created_date_time': getattr(model, 'created_date_time', None),
                    'api_version': getattr(model, 'api_version', None),
                    'tags': getattr(model, 'tags', {})
                }
                supported_models.append(model_info)
            
            return supported_models
            
        except Exception as e:
            logger.error(f"Error getting supported models: {e}")
            return []
    
    async def get_operation_status(self, operation_id: str) -> Dict[str, Any]:
        """Get status of a document analysis operation."""
        if not self.initialized:
            await self.initialize()
        
        try:
            # This would typically check the status of a long-running operation
            # Implementation depends on the specific Azure SDK methods available
            logger.warning(f"Operation status check not implemented for: {operation_id}")
            return {
                'operation_id': operation_id,
                'status': 'unknown',
                'message': 'Operation status check not implemented'
            }
            
        except Exception as e:
            logger.error(f"Error getting operation status: {e}")
            return {
                'operation_id': operation_id,
                'status': 'error',
                'error': str(e)
            }
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics for the service."""
        # This would typically return usage metrics
        return {
            'initialized': self.initialized,
            'supported_file_types': self.supported_file_types,
            'max_file_size_mb': self.max_file_size // (1024 * 1024),
            'api_version': settings.AZURE_DOCUMENT_INTELLIGENCE_API_VERSION
        }