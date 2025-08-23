"""
LangChain + Azure OpenAI integration for LLM Document Intelligence System.
Provides intelligent document processing, enhancement, and analysis.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

from langchain.llms import AzureOpenAI
from langchain.chat_models import AzureChatOpenAI
from langchain.schema import BaseMessage, HumanMessage, SystemMessage
from langchain.prompts import PromptTemplate, ChatPromptTemplate
from langchain.chains import LLMChain, SequentialChain
from langchain.memory import ConversationBufferMemory
from langchain.callbacks.base import BaseCallbackHandler
from langchain.schema.output_parser import StrOutputParser
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor

from config import settings

logger = logging.getLogger(__name__)


class LLMCallbackHandler(BaseCallbackHandler):
    """Custom callback handler for LLM operations monitoring."""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.total_tokens = 0
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.errors = []
    
    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs) -> None:
        self.start_time = datetime.utcnow()
        logger.debug(f"LLM started with {len(prompts)} prompts")
    
    def on_llm_end(self, response, **kwargs) -> None:
        self.end_time = datetime.utcnow()
        if hasattr(response, 'llm_output') and response.llm_output:
            token_usage = response.llm_output.get('token_usage', {})
            self.total_tokens = token_usage.get('total_tokens', 0)
            self.prompt_tokens = token_usage.get('prompt_tokens', 0)
            self.completion_tokens = token_usage.get('completion_tokens', 0)
        
        duration = (self.end_time - self.start_time).total_seconds()
        logger.debug(f"LLM completed in {duration:.2f}s, tokens: {self.total_tokens}")
    
    def on_llm_error(self, error: Union[Exception, KeyboardInterrupt], **kwargs) -> None:
        self.end_time = datetime.utcnow()
        self.errors.append(str(error))
        logger.error(f"LLM error: {error}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get metrics from this callback."""
        duration = 0
        if self.start_time and self.end_time:
            duration = (self.end_time - self.start_time).total_seconds()
        
        return {
            'duration_seconds': duration,
            'total_tokens': self.total_tokens,
            'prompt_tokens': self.prompt_tokens,
            'completion_tokens': self.completion_tokens,
            'errors': self.errors,
            'success': len(self.errors) == 0
        }


class LLMService:
    """Service for LLM-powered document intelligence operations."""
    
    def __init__(self):
        self.llm: Optional[AzureChatOpenAI] = None
        self.embeddings: Optional[OpenAIEmbeddings] = None
        self.text_splitter: Optional[RecursiveCharacterTextSplitter] = None
        self.initialized = False
        self._lock = asyncio.Lock()
    
    async def initialize(self):
        """Initialize LLM service with Azure OpenAI."""
        async with self._lock:
            if self.initialized:
                return
            
            try:
                # Initialize Azure OpenAI Chat model
                azure_config = settings.get_azure_openai_config()
                
                self.llm = AzureChatOpenAI(
                    openai_api_version=azure_config['api_version'],
                    azure_deployment=azure_config['deployment_name'],
                    azure_endpoint=azure_config['api_base'],
                    openai_api_key=azure_config['api_key'],
                    temperature=azure_config['temperature'],
                    max_tokens=azure_config['max_tokens'],
                    request_timeout=60,
                    max_retries=3
                )
                
                # Initialize embeddings for RAG
                self.embeddings = OpenAIEmbeddings(
                    openai_api_key=azure_config['api_key'],
                    openai_api_base=azure_config['api_base'],
                    openai_api_version=azure_config['api_version'],
                    deployment="text-embedding-ada-002",
                    chunk_size=1000
                )
                
                # Initialize text splitter
                self.text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=1000,
                    chunk_overlap=200,
                    length_function=len,
                    separators=["\n\n", "\n", " ", ""]
                )
                
                self.initialized = True
                logger.info("LLM service initialized successfully")
                
            except Exception as e:
                logger.error(f"Failed to initialize LLM service: {e}")
                raise
    
    async def health_check(self) -> bool:
        """Check LLM service health."""
        if not self.initialized:
            return False
        
        try:
            test_message = [HumanMessage(content="Hello, this is a health check.")]
            response = await self.llm.agenerate([test_message])
            return bool(response)
        except Exception:
            return False
    
    async def enhance_extraction(
        self,
        azure_result: Dict[str, Any],
        extraction_type: str = "hybrid",
        confidence_threshold: float = 0.8,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Enhance Azure Document Intelligence results with LLM processing."""
        callback = LLMCallbackHandler()
        
        try:
            # Prepare the prompt based on extraction type
            if extraction_type == "structured":
                enhanced_result = await self._enhance_structured_data(
                    azure_result, confidence_threshold, callback
                )
            elif extraction_type == "unstructured":
                enhanced_result = await self._enhance_unstructured_data(
                    azure_result, confidence_threshold, callback
                )
            else:  # hybrid
                enhanced_result = await self._enhance_hybrid_data(
                    azure_result, confidence_threshold, callback
                )
            
            # Add context if provided
            if context:
                enhanced_result = await self._add_contextual_analysis(
                    enhanced_result, context, callback
                )
            
            # Calculate overall confidence
            overall_confidence = self._calculate_confidence(enhanced_result, azure_result)
            
            return {
                'data': enhanced_result,
                'confidence': overall_confidence,
                'metrics': callback.get_metrics(),
                'enhancement_type': extraction_type,
                'processed_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error enhancing extraction: {e}")
            return {
                'data': azure_result,
                'confidence': 0.5,
                'metrics': callback.get_metrics(),
                'enhancement_type': extraction_type,
                'error': str(e),
                'processed_at': datetime.utcnow().isoformat()
            }
    
    async def _enhance_structured_data(
        self,
        azure_result: Dict[str, Any],
        confidence_threshold: float,
        callback: LLMCallbackHandler
    ) -> Dict[str, Any]:
        """Enhance structured data extraction (forms, tables)."""
        
        prompt_template = """
        You are an expert document analyst specializing in structured data extraction.
        
        I have extracted data from a document using Azure Document Intelligence:
        {azure_data}
        
        Please analyze and enhance this structured data by:
        1. Validating field values and identifying potential errors
        2. Standardizing formats (dates, numbers, addresses)
        3. Filling missing values where logically possible
        4. Identifying relationships between fields
        5. Extracting additional insights from the structure
        
        Minimum confidence threshold: {confidence_threshold}
        
        Return your analysis as a JSON object with:
        - "validated_fields": corrected/validated field values
        - "standardized_data": data in standard formats
        - "inferred_fields": new fields inferred from existing data
        - "data_quality": assessment of data quality
        - "confidence_scores": confidence score for each field
        - "recommendations": suggestions for data improvement
        
        JSON Response:
        """
        
        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["azure_data", "confidence_threshold"]
        )
        
        chain = LLMChain(llm=self.llm, prompt=prompt, callbacks=[callback])
        
        result = await chain.arun(
            azure_data=json.dumps(azure_result, indent=2),
            confidence_threshold=confidence_threshold
        )
        
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            logger.warning("Failed to parse LLM response as JSON, returning raw text")
            return {"enhanced_text": result, "raw_azure_data": azure_result}
    
    async def _enhance_unstructured_data(
        self,
        azure_result: Dict[str, Any],
        confidence_threshold: float,
        callback: LLMCallbackHandler
    ) -> Dict[str, Any]:
        """Enhance unstructured data extraction (documents, reports)."""
        
        prompt_template = """
        You are an expert document analyst specializing in unstructured text analysis.
        
        I have extracted text from a document using Azure Document Intelligence:
        {azure_data}
        
        Please analyze and enhance this unstructured data by:
        1. Extracting key entities (people, places, organizations, dates, amounts)
        2. Identifying main topics and themes
        3. Summarizing key insights and findings
        4. Detecting sentiment and tone
        5. Extracting actionable items or recommendations
        6. Identifying document type and purpose
        
        Minimum confidence threshold: {confidence_threshold}
        
        Return your analysis as a JSON object with:
        - "entities": extracted named entities with types and confidence
        - "topics": main topics and themes identified
        - "summary": concise summary of the document
        - "sentiment": overall sentiment analysis
        - "key_insights": important findings or insights
        - "action_items": actionable items if any
        - "document_type": inferred document type
        - "confidence_scores": confidence scores for each analysis
        
        JSON Response:
        """
        
        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["azure_data", "confidence_threshold"]
        )
        
        chain = LLMChain(llm=self.llm, prompt=prompt, callbacks=[callback])
        
        result = await chain.arun(
            azure_data=json.dumps(azure_result, indent=2),
            confidence_threshold=confidence_threshold
        )
        
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            logger.warning("Failed to parse LLM response as JSON, returning raw text")
            return {"enhanced_text": result, "raw_azure_data": azure_result}
    
    async def _enhance_hybrid_data(
        self,
        azure_result: Dict[str, Any],
        confidence_threshold: float,
        callback: LLMCallbackHandler
    ) -> Dict[str, Any]:
        """Enhance hybrid data extraction (combination of structured and unstructured)."""
        
        prompt_template = """
        You are an expert document analyst specializing in comprehensive document analysis.
        
        I have extracted data from a document using Azure Document Intelligence:
        {azure_data}
        
        Please perform a comprehensive analysis by:
        1. Processing both structured elements (forms, tables) and unstructured text
        2. Cross-referencing structured and unstructured data for validation
        3. Extracting entities, relationships, and patterns
        4. Identifying discrepancies between different data sources
        5. Providing a unified view of the document content
        6. Generating insights that span both structured and unstructured elements
        
        Minimum confidence threshold: {confidence_threshold}
        
        Return your analysis as a JSON object with:
        - "structured_analysis": analysis of structured elements
        - "unstructured_analysis": analysis of text content
        - "cross_references": relationships between structured and unstructured data
        - "unified_entities": comprehensive entity extraction
        - "document_insights": high-level insights about the document
        - "data_consistency": assessment of data consistency
        - "confidence_scores": confidence scores for different analyses
        - "recommendations": recommendations for data quality improvement
        
        JSON Response:
        """
        
        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["azure_data", "confidence_threshold"]
        )
        
        chain = LLMChain(llm=self.llm, prompt=prompt, callbacks=[callback])
        
        result = await chain.arun(
            azure_data=json.dumps(azure_result, indent=2),
            confidence_threshold=confidence_threshold
        )
        
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            logger.warning("Failed to parse LLM response as JSON, returning raw text")
            return {"enhanced_text": result, "raw_azure_data": azure_result}
    
    async def _add_contextual_analysis(
        self,
        enhanced_result: Dict[str, Any],
        context: str,
        callback: LLMCallbackHandler
    ) -> Dict[str, Any]:
        """Add contextual analysis based on provided context."""
        
        prompt_template = """
        You are analyzing a document with the following context:
        Context: {context}
        
        Current analysis results:
        {enhanced_result}
        
        Please enhance the analysis by considering the provided context:
        1. How does the context change the interpretation of the data?
        2. What additional insights can be derived with this context?
        3. Are there context-specific validations that should be applied?
        4. What context-relevant recommendations can be made?
        
        Return an enhanced analysis as a JSON object that includes:
        - "contextual_insights": insights derived from the context
        - "context_validation": validation results considering context
        - "enhanced_recommendations": context-aware recommendations
        - "relevance_score": how relevant the document is to the context
        - "original_analysis": the original analysis results
        
        JSON Response:
        """
        
        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "enhanced_result"]
        )
        
        chain = LLMChain(llm=self.llm, prompt=prompt, callbacks=[callback])
        
        result = await chain.arun(
            context=context,
            enhanced_result=json.dumps(enhanced_result, indent=2)
        )
        
        try:
            contextual_analysis = json.loads(result)
            # Merge contextual analysis with original results
            enhanced_result['contextual_analysis'] = contextual_analysis
            return enhanced_result
        except json.JSONDecodeError:
            logger.warning("Failed to parse contextual analysis, returning original")
            enhanced_result['contextual_analysis_text'] = result
            return enhanced_result
    
    def _calculate_confidence(
        self,
        enhanced_result: Dict[str, Any],
        azure_result: Dict[str, Any]
    ) -> float:
        """Calculate overall confidence score for the enhancement."""
        
        # Start with Azure confidence if available
        azure_confidence = azure_result.get('confidence', 0.5)
        
        # Extract confidence scores from enhanced result
        confidence_scores = []
        
        def extract_confidence_recursive(data, path=""):
            if isinstance(data, dict):
                for key, value in data.items():
                    if 'confidence' in key.lower() and isinstance(value, (int, float)):
                        confidence_scores.append(value)
                    elif isinstance(value, (dict, list)):
                        extract_confidence_recursive(value, f"{path}.{key}")
            elif isinstance(data, list):
                for i, item in enumerate(data):
                    if isinstance(item, (dict, list)):
                        extract_confidence_recursive(item, f"{path}[{i}]")
        
        extract_confidence_recursive(enhanced_result)
        
        if confidence_scores:
            llm_confidence = sum(confidence_scores) / len(confidence_scores)
            # Weighted average: 60% Azure, 40% LLM
            overall_confidence = (azure_confidence * 0.6) + (llm_confidence * 0.4)
        else:
            # If no LLM confidence scores found, slightly boost Azure confidence
            overall_confidence = min(azure_confidence * 1.1, 1.0)
        
        return round(overall_confidence, 3)
    
    async def summarize_document(
        self,
        document_content: str,
        max_length: int = 500,
        summary_type: str = "extractive"
    ) -> Dict[str, Any]:
        """Generate document summary."""
        callback = LLMCallbackHandler()
        
        try:
            if summary_type == "abstractive":
                prompt_template = """
                Please create a concise, abstractive summary of the following document content.
                The summary should be approximately {max_length} words and capture the key points,
                main arguments, and important details in your own words.
                
                Document Content:
                {content}
                
                Summary:
                """
            else:  # extractive
                prompt_template = """
                Please create an extractive summary of the following document content.
                Extract the most important sentences and phrases that capture the key information.
                The summary should be approximately {max_length} words.
                
                Document Content:
                {content}
                
                Key Points Summary:
                """
            
            prompt = PromptTemplate(
                template=prompt_template,
                input_variables=["content", "max_length"]
            )
            
            # Split content if too long
            if len(document_content) > 4000:
                chunks = self.text_splitter.split_text(document_content)
                summaries = []
                
                for chunk in chunks[:5]:  # Limit to 5 chunks to avoid token limits
                    chain = LLMChain(llm=self.llm, prompt=prompt, callbacks=[callback])
                    chunk_summary = await chain.arun(
                        content=chunk,
                        max_length=max_length // len(chunks[:5])
                    )
                    summaries.append(chunk_summary)
                
                # Combine chunk summaries
                combined_summary = "\n".join(summaries)
                if len(combined_summary) > max_length * 2:
                    # Summarize the summaries
                    final_chain = LLMChain(llm=self.llm, prompt=prompt, callbacks=[callback])
                    final_summary = await final_chain.arun(
                        content=combined_summary,
                        max_length=max_length
                    )
                else:
                    final_summary = combined_summary
            else:
                chain = LLMChain(llm=self.llm, prompt=prompt, callbacks=[callback])
                final_summary = await chain.arun(
                    content=document_content,
                    max_length=max_length
                )
            
            return {
                'summary': final_summary,
                'summary_type': summary_type,
                'original_length': len(document_content),
                'summary_length': len(final_summary),
                'compression_ratio': len(final_summary) / len(document_content),
                'metrics': callback.get_metrics(),
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return {
                'summary': document_content[:max_length] + "..." if len(document_content) > max_length else document_content,
                'summary_type': 'truncated',
                'error': str(e),
                'metrics': callback.get_metrics(),
                'generated_at': datetime.utcnow().isoformat()
            }
    
    async def extract_insights(
        self,
        document_data: Dict[str, Any],
        insight_types: List[str] = None
    ) -> Dict[str, Any]:
        """Extract specific insights from document data."""
        if insight_types is None:
            insight_types = ['trends', 'anomalies', 'recommendations', 'risks']
        
        callback = LLMCallbackHandler()
        
        try:
            prompt_template = """
            You are a business analyst extracting insights from document data.
            
            Document Data:
            {document_data}
            
            Please analyze this data and provide insights for the following categories:
            {insight_types}
            
            For each category, provide:
            1. Key findings
            2. Supporting evidence from the data
            3. Confidence level (0-1)
            4. Potential implications
            
            Return your analysis as a JSON object with each insight type as a key.
            
            JSON Response:
            """
            
            prompt = PromptTemplate(
                template=prompt_template,
                input_variables=["document_data", "insight_types"]
            )
            
            chain = LLMChain(llm=self.llm, prompt=prompt, callbacks=[callback])
            
            result = await chain.arun(
                document_data=json.dumps(document_data, indent=2),
                insight_types=", ".join(insight_types)
            )
            
            try:
                insights = json.loads(result)
            except json.JSONDecodeError:
                insights = {"raw_insights": result}
            
            return {
                'insights': insights,
                'insight_types': insight_types,
                'metrics': callback.get_metrics(),
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error extracting insights: {e}")
            return {
                'insights': {},
                'insight_types': insight_types,
                'error': str(e),
                'metrics': callback.get_metrics(),
                'generated_at': datetime.utcnow().isoformat()
            }
    
    async def classify_document(
        self,
        document_content: str,
        possible_categories: List[str] = None
    ) -> Dict[str, Any]:
        """Classify document type and category."""
        if possible_categories is None:
            possible_categories = [
                'invoice', 'contract', 'report', 'form', 'letter', 
                'resume', 'financial_statement', 'legal_document', 'other'
            ]
        
        callback = LLMCallbackHandler()
        
        try:
            prompt_template = """
            You are a document classification expert. Analyze the following document content
            and classify it into the most appropriate category.
            
            Document Content:
            {content}
            
            Possible Categories:
            {categories}
            
            Please provide:
            1. Primary category (most likely classification)
            2. Secondary category (if applicable)
            3. Confidence score (0-1) for primary classification
            4. Key features that support this classification
            5. Document structure analysis
            
            Return your analysis as a JSON object with:
            - "primary_category": main classification
            - "secondary_category": alternative classification
            - "confidence": confidence score
            - "features": supporting features
            - "structure": document structure analysis
            
            JSON Response:
            """
            
            prompt = PromptTemplate(
                template=prompt_template,
                input_variables=["content", "categories"]
            )
            
            chain = LLMChain(llm=self.llm, prompt=prompt, callbacks=[callback])
            
            result = await chain.arun(
                content=document_content[:2000],  # Limit content length
                categories=", ".join(possible_categories)
            )
            
            try:
                classification = json.loads(result)
            except json.JSONDecodeError:
                classification = {"raw_classification": result}
            
            return {
                'classification': classification,
                'possible_categories': possible_categories,
                'metrics': callback.get_metrics(),
                'classified_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error classifying document: {e}")
            return {
                'classification': {"primary_category": "unknown", "confidence": 0.0},
                'possible_categories': possible_categories,
                'error': str(e),
                'metrics': callback.get_metrics(),
                'classified_at': datetime.utcnow().isoformat()
            }