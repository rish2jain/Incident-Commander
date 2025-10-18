"""
Vector store service for RAG memory and similarity search.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from uuid import uuid4

import numpy as np
from pydantic import BaseModel

from src.models.incident import Incident
from src.models.agent import AgentRecommendation
from src.utils.config import config
from src.utils.logging import get_logger

logger = get_logger(__name__)


class VectorDocument(BaseModel):
    """Document stored in vector database."""
    
    id: str = str(uuid4())
    content: str
    metadata: Dict[str, Any] = {}
    embedding: Optional[List[float]] = None
    
    # Document classification
    document_type: str  # incident, pattern, resolution, knowledge
    source: str
    
    # Timestamps
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()
    last_accessed: Optional[datetime] = None
    
    # Usage statistics
    access_count: int = 0
    relevance_score: float = 0.0
    
    def update_access(self) -> None:
        """Update access statistics."""
        self.last_accessed = datetime.utcnow()
        self.access_count += 1


class SimilarityResult(BaseModel):
    """Result from similarity search."""
    
    document: VectorDocument
    similarity_score: float
    rank: int
    
    # Search context
    query_embedding: List[float]
    search_timestamp: datetime = datetime.utcnow()
    
    def is_relevant(self, threshold: float = 0.7) -> bool:
        """Check if result meets relevance threshold."""
        return self.similarity_score >= threshold


class VectorStoreService:
    """Service for managing vector embeddings and similarity search."""
    
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        self.documents: Dict[str, VectorDocument] = {}
        self.embeddings_cache: Dict[str, List[float]] = {}
        
        # Configuration
        self.embedding_dimension = 1536  # Bedrock Titan embedding size
        self.similarity_threshold = 0.7
        self.max_results = 10
        self.cache_ttl_hours = 24
    
    async def add_incident_document(self, incident: Incident, 
                                  recommendations: List[AgentRecommendation]) -> str:
        """Add incident as a searchable document."""
        
        try:
            # Create document content
            content = self._create_incident_content(incident, recommendations)
            
            # Generate metadata
            metadata = {
                "incident_id": incident.id,
                "severity": incident.severity,
                "status": incident.status,
                "service_tier": incident.business_impact.service_tier,
                "cost_impact": incident.calculate_total_cost(),
                "duration_minutes": incident.calculate_duration_minutes(),
                "agent_count": len(recommendations),
                "source_system": incident.metadata.source_system,
                "tags": incident.metadata.tags
            }
            
            # Create document
            document = VectorDocument(
                content=content,
                metadata=metadata,
                document_type="incident",
                source="incident_resolution"
            )
            
            # Generate embedding
            embedding = await self._generate_embedding(content)
            document.embedding = embedding
            
            # Store document
            self.documents[document.id] = document
            
            self.logger.info(f"Added incident document: {incident.id}")
            return document.id
            
        except Exception as e:
            self.logger.error(f"Error adding incident document: {e}")
            raise
    
    def _create_incident_content(self, incident: Incident, 
                               recommendations: List[AgentRecommendation]) -> str:
        """Create searchable content from incident and recommendations."""
        
        # Build comprehensive content for embedding
        content_parts = [
            f"Incident: {incident.title}",
            f"Description: {incident.description}",
            f"Severity: {incident.severity}",
            f"Service Tier: {incident.business_impact.service_tier}",
            f"Source System: {incident.metadata.source_system}"
        ]
        
        # Add tags
        if incident.metadata.tags:
            tags_str = ", ".join([f"{k}:{v}" for k, v in incident.metadata.tags.items()])
            content_parts.append(f"Tags: {tags_str}")
        
        # Add recommendations
        for rec in recommendations:
            content_parts.extend([
                f"Agent {rec.agent_name} recommended: {rec.description}",
                f"Confidence: {rec.confidence:.2f}",
                f"Reasoning: {rec.reasoning}"
            ])
            
            # Add evidence
            for evidence in rec.evidence:
                if isinstance(evidence.get("data"), dict):
                    evidence_text = json.dumps(evidence["data"])[:200]  # Truncate
                    content_parts.append(f"Evidence from {evidence.get('source', 'unknown')}: {evidence_text}")
        
        return " | ".join(content_parts)
    
    async def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding vector for text using Bedrock Titan."""
        
        # Check cache first
        cache_key = hash(text)
        if str(cache_key) in self.embeddings_cache:
            return self.embeddings_cache[str(cache_key)]
        
        try:
            # In production, this would call Bedrock Titan Embeddings
            # For now, simulate with random vector (normalized)
            embedding = np.random.normal(0, 1, self.embedding_dimension).tolist()
            
            # Normalize vector
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = (np.array(embedding) / norm).tolist()
            
            # Cache result
            self.embeddings_cache[str(cache_key)] = embedding
            
            return embedding
            
        except Exception as e:
            self.logger.error(f"Error generating embedding: {e}")
            # Return zero vector as fallback
            return [0.0] * self.embedding_dimension
    
    async def search_similar_incidents(self, query_incident: Incident, 
                                     max_results: Optional[int] = None) -> List[SimilarityResult]:
        """Search for incidents similar to the query incident."""
        
        try:
            # Generate query content and embedding
            query_content = self._create_query_content(query_incident)
            query_embedding = await self._generate_embedding(query_content)
            
            # Search through stored documents
            results = []
            for doc_id, document in self.documents.items():
                if document.document_type != "incident" or not document.embedding:
                    continue
                
                # Skip same incident
                if document.metadata.get("incident_id") == query_incident.id:
                    continue
                
                # Calculate similarity
                similarity = self._calculate_cosine_similarity(query_embedding, document.embedding)
                
                if similarity >= self.similarity_threshold:
                    result = SimilarityResult(
                        document=document,
                        similarity_score=similarity,
                        rank=0,  # Will be set after sorting
                        query_embedding=query_embedding
                    )
                    results.append(result)
            
            # Sort by similarity score
            results.sort(key=lambda x: x.similarity_score, reverse=True)
            
            # Set ranks and limit results
            max_results = max_results or self.max_results
            for i, result in enumerate(results[:max_results]):
                result.rank = i + 1
                result.document.update_access()  # Update access statistics
            
            self.logger.info(f"Found {len(results)} similar incidents for {query_incident.id}")
            return results[:max_results]
            
        except Exception as e:
            self.logger.error(f"Error searching similar incidents: {e}")
            return []
    
    def _create_query_content(self, incident: Incident) -> str:
        """Create query content from incident for similarity search."""
        
        content_parts = [
            incident.title,
            incident.description,
            incident.severity,
            incident.business_impact.service_tier,
            incident.metadata.source_system
        ]
        
        # Add tags
        if incident.metadata.tags:
            content_parts.extend(incident.metadata.tags.values())
        
        return " ".join(content_parts)
    
    def _calculate_cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        
        try:
            # Convert to numpy arrays
            a = np.array(vec1)
            b = np.array(vec2)
            
            # Calculate cosine similarity
            dot_product = np.dot(a, b)
            norm_a = np.linalg.norm(a)
            norm_b = np.linalg.norm(b)
            
            if norm_a == 0 or norm_b == 0:
                return 0.0
            
            similarity = dot_product / (norm_a * norm_b)
            return float(similarity)
            
        except Exception as e:
            self.logger.error(f"Error calculating similarity: {e}")
            return 0.0
    
    async def add_knowledge_pattern(self, pattern_name: str, pattern_data: Dict[str, Any]) -> str:
        """Add a knowledge pattern to the vector store."""
        
        try:
            # Create content from pattern data
            content = self._create_pattern_content(pattern_name, pattern_data)
            
            # Create document
            document = VectorDocument(
                content=content,
                metadata=pattern_data,
                document_type="pattern",
                source="pattern_discovery"
            )
            
            # Generate embedding
            embedding = await self._generate_embedding(content)
            document.embedding = embedding
            
            # Store document
            self.documents[document.id] = document
            
            self.logger.info(f"Added knowledge pattern: {pattern_name}")
            return document.id
            
        except Exception as e:
            self.logger.error(f"Error adding knowledge pattern: {e}")
            raise
    
    def _create_pattern_content(self, pattern_name: str, pattern_data: Dict[str, Any]) -> str:
        """Create searchable content from pattern data."""
        
        content_parts = [f"Pattern: {pattern_name}"]
        
        # Add pattern characteristics
        for key, value in pattern_data.items():
            if isinstance(value, (str, int, float)):
                content_parts.append(f"{key}: {value}")
            elif isinstance(value, list):
                content_parts.append(f"{key}: {', '.join(map(str, value))}")
            elif isinstance(value, dict):
                content_parts.append(f"{key}: {json.dumps(value)[:100]}")
        
        return " | ".join(content_parts)
    
    async def search_patterns(self, query: str, pattern_type: Optional[str] = None) -> List[SimilarityResult]:
        """Search for knowledge patterns matching the query."""
        
        try:
            # Generate query embedding
            query_embedding = await self._generate_embedding(query)
            
            # Search through pattern documents
            results = []
            for doc_id, document in self.documents.items():
                if document.document_type != "pattern" or not document.embedding:
                    continue
                
                # Filter by pattern type if specified
                if pattern_type and document.metadata.get("pattern_type") != pattern_type:
                    continue
                
                # Calculate similarity
                similarity = self._calculate_cosine_similarity(query_embedding, document.embedding)
                
                if similarity >= self.similarity_threshold:
                    result = SimilarityResult(
                        document=document,
                        similarity_score=similarity,
                        rank=0,
                        query_embedding=query_embedding
                    )
                    results.append(result)
            
            # Sort and rank results
            results.sort(key=lambda x: x.similarity_score, reverse=True)
            for i, result in enumerate(results[:self.max_results]):
                result.rank = i + 1
                result.document.update_access()
            
            return results[:self.max_results]
            
        except Exception as e:
            self.logger.error(f"Error searching patterns: {e}")
            return []
    
    async def update_document_relevance(self, document_id: str, relevance_score: float) -> None:
        """Update document relevance based on user feedback."""
        
        if document_id in self.documents:
            self.documents[document_id].relevance_score = relevance_score
            self.documents[document_id].updated_at = datetime.utcnow()
            
            self.logger.debug(f"Updated relevance for document {document_id}: {relevance_score}")
    
    async def get_vector_store_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store."""
        
        total_docs = len(self.documents)
        doc_types = {}
        total_accesses = 0
        avg_relevance = 0.0
        
        for document in self.documents.values():
            # Count by type
            doc_types[document.document_type] = doc_types.get(document.document_type, 0) + 1
            
            # Sum statistics
            total_accesses += document.access_count
            avg_relevance += document.relevance_score
        
        if total_docs > 0:
            avg_relevance /= total_docs
        
        return {
            "total_documents": total_docs,
            "document_types": doc_types,
            "total_accesses": total_accesses,
            "average_relevance": avg_relevance,
            "cache_size": len(self.embeddings_cache),
            "embedding_dimension": self.embedding_dimension,
            "similarity_threshold": self.similarity_threshold
        }
    
    async def cleanup_old_embeddings(self, max_age_hours: int = 24) -> None:
        """Clean up old cached embeddings."""
        
        # In production, this would check timestamp-based cache expiry
        # For now, just limit cache size
        if len(self.embeddings_cache) > 1000:
            # Remove oldest half of cache entries
            keys_to_remove = list(self.embeddings_cache.keys())[:500]
            for key in keys_to_remove:
                del self.embeddings_cache[key]
            
            self.logger.info(f"Cleaned up {len(keys_to_remove)} cached embeddings")


# Global vector store service instance
vector_store = VectorStoreService()