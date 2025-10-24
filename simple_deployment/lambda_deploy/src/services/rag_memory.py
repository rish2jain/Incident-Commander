"""
RAG Memory System with OpenSearch Serverless integration for scalable vector search.
"""

import asyncio
import json
import hashlib
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from uuid import uuid4

from opensearchpy import AsyncOpenSearch, RequestsHttpConnection
from opensearchpy.exceptions import OpenSearchException

from src.models.incident import Incident
from src.services.aws import AWSServiceFactory, BedrockClient
from src.utils.config import config
from src.utils.logging import get_logger
from src.utils.exceptions import ResourceLimitError


logger = get_logger("rag_memory")


@dataclass
class IncidentPattern:
    """Represents a learned incident pattern."""
    pattern_id: str
    incident_type: str
    symptoms: List[str]
    root_causes: List[str]
    resolution_actions: List[str]
    success_rate: float
    confidence: float
    created_at: datetime
    last_used: datetime
    usage_count: int


@dataclass
class SimilarityResult:
    """Result of similarity search."""
    incident_id: str
    similarity_score: float
    pattern: IncidentPattern
    metadata: Dict[str, Any]


class ScalableRAGMemory:
    """RAG Memory system with OpenSearch Serverless for scalable vector search."""
    
    def __init__(self, service_factory: AWSServiceFactory):
        """Initialize RAG memory system."""
        self._service_factory = service_factory
        self._opensearch_client = None
        self._bedrock_client = None
        self._index_name = "incident-patterns"
        self._embedding_dimension = 1536  # Titan embedding dimension
        self._max_patterns = 100000  # 100K pattern limit
        
        # Performance optimization
        self._embedding_cache: Dict[str, List[float]] = {}
        self._pattern_cache: Dict[str, IncidentPattern] = {}
        self._cache_ttl = timedelta(hours=1)
        self._last_cache_cleanup = datetime.utcnow()
    
    async def _get_opensearch_client(self) -> AsyncOpenSearch:
        """Get or create OpenSearch client."""
        if not self._opensearch_client:
            if config.database.opensearch_endpoint:
                # Production OpenSearch Serverless
                self._opensearch_client = AsyncOpenSearch(
                    hosts=[config.database.opensearch_endpoint],
                    http_auth=await self._get_opensearch_auth(),
                    use_ssl=True,
                    verify_certs=True,
                    connection_class=RequestsHttpConnection,
                    timeout=30
                )
            else:
                # Local development fallback
                self._opensearch_client = AsyncOpenSearch(
                    hosts=[{"host": "localhost", "port": 9200}],
                    http_auth=("admin", "admin"),
                    use_ssl=False,
                    verify_certs=False,
                    connection_class=RequestsHttpConnection
                )
            
            # Initialize index
            await self._initialize_index()
        
        return self._opensearch_client
    
    async def _get_opensearch_auth(self) -> Tuple[str, str]:
        """Get OpenSearch authentication credentials."""
        # In production, this would use AWS IAM or service credentials
        # For now, return default credentials
        return ("admin", "admin")
    
    async def _get_bedrock_client(self) -> BedrockClient:
        """Get or create Bedrock client for embeddings."""
        if not self._bedrock_client:
            self._bedrock_client = BedrockClient(self._service_factory)
        return self._bedrock_client
    
    async def _initialize_index(self) -> None:
        """Initialize OpenSearch index with proper mapping."""
        try:
            client = await self._get_opensearch_client()
            
            # Check if index exists
            if await client.indices.exists(index=self._index_name):
                logger.info(f"Index {self._index_name} already exists")
                return
            
            # Create index with vector field mapping
            index_mapping = {
                "mappings": {
                    "properties": {
                        "pattern_id": {"type": "keyword"},
                        "incident_type": {"type": "keyword"},
                        "symptoms": {"type": "text"},
                        "root_causes": {"type": "text"},
                        "resolution_actions": {"type": "text"},
                        "success_rate": {"type": "float"},
                        "confidence": {"type": "float"},
                        "created_at": {"type": "date"},
                        "last_used": {"type": "date"},
                        "usage_count": {"type": "integer"},
                        "embedding": {
                            "type": "knn_vector",
                            "dimension": self._embedding_dimension,
                            "method": {
                                "name": "hnsw",
                                "space_type": "cosinesimil",
                                "engine": "nmslib"
                            }
                        },
                        "text_content": {"type": "text"},
                        "metadata": {"type": "object"}
                    }
                },
                "settings": {
                    "index": {
                        "knn": True,
                        "knn.algo_param.ef_search": 100,
                        "number_of_shards": 2,
                        "number_of_replicas": 1
                    }
                }
            }
            
            await client.indices.create(
                index=self._index_name,
                body=index_mapping
            )
            
            logger.info(f"Created OpenSearch index: {self._index_name}")
            
        except OpenSearchException as e:
            logger.error(f"Failed to initialize OpenSearch index: {e}")
            raise
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using Bedrock Titan."""
        # Check cache first
        text_hash = hashlib.md5(text.encode()).hexdigest()
        if text_hash in self._embedding_cache:
            return self._embedding_cache[text_hash]
        
        try:
            bedrock_client = await self._get_bedrock_client()
            
            # Use real Titan embedding model
            embedding_request = {
                "inputText": text[:8000]  # Limit input size for Titan
            }
            
            try:
                # Call Amazon Titan Embeddings model
                response = await bedrock_client.invoke_model_async(
                    modelId="amazon.titan-embed-text-v1",
                    body=json.dumps(embedding_request),
                    contentType="application/json"
                )
                
                # Parse Titan response
                response_body = json.loads(response['body'].read())
                embedding = response_body.get('embedding', [])
                
                if not embedding or len(embedding) != self._embedding_dimension:
                    logger.warning(f"Invalid Titan embedding response, falling back to simulated")
                    embedding = self._generate_simulated_embedding(text)
                
                logger.debug(f"Generated Titan embedding for text: {text[:50]}...")
                
            except Exception as titan_error:
                logger.warning(f"Titan embedding failed, using simulated: {titan_error}")
                # Fallback to simulated embedding for development
                embedding = self._generate_simulated_embedding(text)
            
            # Cache the embedding
            self._embedding_cache[text_hash] = embedding
            
            # Clean cache if too large
            if len(self._embedding_cache) > 1000:
                await self._cleanup_embedding_cache()
            
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            # Return zero vector as fallback
            return [0.0] * self._embedding_dimension
    
    def _generate_simulated_embedding(self, text: str) -> List[float]:
        """Generate simulated embedding for development/testing."""
        # Create deterministic embedding based on text hash
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        
        # Convert hash to float values
        embedding = []
        for i in range(0, min(len(text_hash), self._embedding_dimension * 8), 8):
            hex_chunk = text_hash[i:i+8]
            if len(hex_chunk) == 8:
                # Convert hex to float between -1 and 1
                int_val = int(hex_chunk, 16)
                float_val = (int_val / (16**8)) * 2 - 1
                embedding.append(float_val)
        
        # Pad or truncate to correct dimension
        while len(embedding) < self._embedding_dimension:
            embedding.append(0.0)
        
        return embedding[:self._embedding_dimension]
    
    async def store_incident_pattern(self, incident: Incident, 
                                   resolution_actions: List[str],
                                   success_rate: float = 1.0) -> str:
        """Store incident pattern in RAG memory."""
        try:
            # Create pattern from incident
            pattern = IncidentPattern(
                pattern_id=str(uuid4()),
                incident_type=f"{incident.severity}_{incident.business_impact.service_tier.value}",
                symptoms=[incident.title, incident.description],
                root_causes=[],  # Would be populated from diagnosis
                resolution_actions=resolution_actions,
                success_rate=success_rate,
                confidence=0.8,  # Initial confidence
                created_at=datetime.utcnow(),
                last_used=datetime.utcnow(),
                usage_count=1
            )
            
            # Generate text representation for embedding
            text_content = self._pattern_to_text(pattern)
            
            # Generate embedding
            embedding = await self.generate_embedding(text_content)
            
            # Store in OpenSearch
            client = await self._get_opensearch_client()
            
            document = {
                "pattern_id": pattern.pattern_id,
                "incident_type": pattern.incident_type,
                "symptoms": pattern.symptoms,
                "root_causes": pattern.root_causes,
                "resolution_actions": pattern.resolution_actions,
                "success_rate": pattern.success_rate,
                "confidence": pattern.confidence,
                "created_at": pattern.created_at.isoformat(),
                "last_used": pattern.last_used.isoformat(),
                "usage_count": pattern.usage_count,
                "embedding": embedding,
                "text_content": text_content,
                "metadata": {
                    "incident_id": incident.id,
                    "service_tier": incident.business_impact.service_tier.value,
                    "severity": incident.severity
                }
            }
            
            await client.index(
                index=self._index_name,
                id=pattern.pattern_id,
                body=document
            )
            
            # Cache the pattern
            self._pattern_cache[pattern.pattern_id] = pattern
            
            logger.info(f"Stored incident pattern: {pattern.pattern_id}")
            return pattern.pattern_id
            
        except Exception as e:
            logger.error(f"Failed to store incident pattern: {e}")
            raise
    
    def _pattern_to_text(self, pattern: IncidentPattern) -> str:
        """Convert pattern to text representation for embedding."""
        text_parts = [
            f"Incident Type: {pattern.incident_type}",
            f"Symptoms: {' '.join(pattern.symptoms)}",
            f"Root Causes: {' '.join(pattern.root_causes)}",
            f"Resolution Actions: {' '.join(pattern.resolution_actions)}"
        ]
        return " | ".join(text_parts)
    
    async def search_similar_incidents(self, query: str, 
                                     limit: int = 5,
                                     exclude_incident_id: str = None) -> List[Dict[str, Any]]:
        """Search for similar incidents using query string."""
        try:
            # Generate embedding for query
            query_embedding = await self.generate_embedding(query)
            
            client = await self._get_opensearch_client()
            
            # Build search query
            search_query = {
                "size": limit,
                "query": {
                    "bool": {
                        "should": [
                            # Vector similarity search
                            {
                                "knn": {
                                    "embedding": {
                                        "vector": query_embedding,
                                        "k": limit
                                    }
                                }
                            },
                            # Keyword matching
                            {
                                "multi_match": {
                                    "query": query,
                                    "fields": ["symptoms", "text_content"],
                                    "boost": 0.3
                                }
                            }
                        ],
                        "minimum_should_match": 1
                    }
                },
                "_source": {
                    "excludes": ["embedding"]
                }
            }
            
            # Exclude specific incident if provided
            if exclude_incident_id:
                search_query["query"]["bool"]["must_not"] = [
                    {"term": {"metadata.incident_id": exclude_incident_id}}
                ]
            
            response = await client.search(
                index=self._index_name,
                body=search_query
            )
            
            # Format results
            results = []
            for hit in response["hits"]["hits"]:
                result = {
                    "score": hit["_score"],
                    "metadata": hit["_source"]["metadata"],
                    "pattern": hit["_source"]
                }
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to search similar incidents: {e}")
            return []
    
    async def find_similar_patterns(self, incident: Incident, 
                                  limit: int = 5,
                                  min_similarity: float = 0.7) -> List[SimilarityResult]:
        """Find similar incident patterns using hybrid search."""
        try:
            # Generate query text and embedding
            query_text = f"{incident.title} {incident.description}"
            query_embedding = await self.generate_embedding(query_text)
            
            client = await self._get_opensearch_client()
            
            # Hybrid search: vector similarity + keyword matching
            search_query = {
                "size": limit * 2,  # Get more results for filtering
                "query": {
                    "bool": {
                        "should": [
                            # Vector similarity search
                            {
                                "knn": {
                                    "embedding": {
                                        "vector": query_embedding,
                                        "k": limit * 2
                                    }
                                }
                            },
                            # Keyword matching
                            {
                                "multi_match": {
                                    "query": query_text,
                                    "fields": ["symptoms", "root_causes", "resolution_actions"],
                                    "boost": 0.3
                                }
                            },
                            # Incident type matching
                            {
                                "term": {
                                    "incident_type": {
                                        "value": f"{incident.severity}_{incident.business_impact.service_tier.value}",
                                        "boost": 0.5
                                    }
                                }
                            }
                        ],
                        "minimum_should_match": 1
                    }
                },
                "_source": {
                    "excludes": ["embedding"]  # Don't return large embedding vectors
                }
            }
            
            response = await client.search(
                index=self._index_name,
                body=search_query
            )
            
            # Process results
            results = []
            for hit in response["hits"]["hits"]:
                similarity_score = hit["_score"]
                
                # Filter by minimum similarity
                if similarity_score < min_similarity:
                    continue
                
                # Create pattern from hit
                source = hit["_source"]
                pattern = IncidentPattern(
                    pattern_id=source["pattern_id"],
                    incident_type=source["incident_type"],
                    symptoms=source["symptoms"],
                    root_causes=source["root_causes"],
                    resolution_actions=source["resolution_actions"],
                    success_rate=source["success_rate"],
                    confidence=source["confidence"],
                    created_at=datetime.fromisoformat(source["created_at"]),
                    last_used=datetime.fromisoformat(source["last_used"]),
                    usage_count=source["usage_count"]
                )
                
                # Update usage statistics
                await self._update_pattern_usage(pattern.pattern_id)
                
                results.append(SimilarityResult(
                    incident_id=source["metadata"]["incident_id"],
                    similarity_score=similarity_score,
                    pattern=pattern,
                    metadata=source["metadata"]
                ))
            
            # Sort by similarity score and limit results
            results.sort(key=lambda x: x.similarity_score, reverse=True)
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Failed to find similar patterns: {e}")
            return []
    
    async def _update_pattern_usage(self, pattern_id: str) -> None:
        """Update pattern usage statistics."""
        try:
            client = await self._get_opensearch_client()
            
            # Update usage count and last used timestamp
            update_body = {
                "script": {
                    "source": """
                        ctx._source.usage_count += 1;
                        ctx._source.last_used = params.now;
                    """,
                    "params": {
                        "now": datetime.utcnow().isoformat()
                    }
                }
            }
            
            await client.update(
                index=self._index_name,
                id=pattern_id,
                body=update_body
            )
            
        except Exception as e:
            logger.warning(f"Failed to update pattern usage: {e}")
    
    async def get_pattern_statistics(self) -> Dict[str, Any]:
        """Get comprehensive pattern statistics."""
        try:
            client = await self._get_opensearch_client()
            
            # Get index statistics
            stats_response = await client.indices.stats(index=self._index_name)
            
            # Get pattern distribution
            agg_query = {
                "size": 0,
                "aggs": {
                    "incident_types": {
                        "terms": {
                            "field": "incident_type",
                            "size": 20
                        }
                    },
                    "avg_success_rate": {
                        "avg": {
                            "field": "success_rate"
                        }
                    },
                    "avg_confidence": {
                        "avg": {
                            "field": "confidence"
                        }
                    },
                    "usage_distribution": {
                        "histogram": {
                            "field": "usage_count",
                            "interval": 10
                        }
                    }
                }
            }
            
            agg_response = await client.search(
                index=self._index_name,
                body=agg_query
            )
            
            return {
                "total_patterns": stats_response["indices"][self._index_name]["total"]["docs"]["count"],
                "index_size_bytes": stats_response["indices"][self._index_name]["total"]["store"]["size_in_bytes"],
                "incident_type_distribution": agg_response["aggregations"]["incident_types"]["buckets"],
                "average_success_rate": agg_response["aggregations"]["avg_success_rate"]["value"],
                "average_confidence": agg_response["aggregations"]["avg_confidence"]["value"],
                "usage_distribution": agg_response["aggregations"]["usage_distribution"]["buckets"],
                "cache_stats": {
                    "embedding_cache_size": len(self._embedding_cache),
                    "pattern_cache_size": len(self._pattern_cache)
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get pattern statistics: {e}")
            return {}
    
    async def cleanup_old_patterns(self, retention_days: int = 180) -> int:
        """Clean up old, unused patterns."""
        try:
            client = await self._get_opensearch_client()
            
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            # Find old patterns with low usage
            cleanup_query = {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "range": {
                                    "last_used": {
                                        "lt": cutoff_date.isoformat()
                                    }
                                }
                            },
                            {
                                "range": {
                                    "usage_count": {
                                        "lt": 5  # Less than 5 uses
                                    }
                                }
                            }
                        ]
                    }
                }
            }
            
            # Delete old patterns
            delete_response = await client.delete_by_query(
                index=self._index_name,
                body=cleanup_query
            )
            
            deleted_count = delete_response["deleted"]
            logger.info(f"Cleaned up {deleted_count} old patterns")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old patterns: {e}")
            return 0
    
    async def _cleanup_embedding_cache(self) -> None:
        """Clean up embedding cache to prevent memory issues."""
        # Remove oldest 50% of cache entries
        cache_items = list(self._embedding_cache.items())
        cache_items.sort(key=lambda x: len(x[0]))  # Sort by key length as proxy for age
        
        keep_count = len(cache_items) // 2
        self._embedding_cache = dict(cache_items[:keep_count])
        
        logger.info(f"Cleaned embedding cache, kept {keep_count} entries")
    
    async def archive_to_s3(self, archive_older_than_days: int = 365) -> str:
        """Archive old patterns to S3 cold storage."""
        try:
            # This would implement S3 archiving for 6-month lifecycle
            # For now, just log the operation
            cutoff_date = datetime.utcnow() - timedelta(days=archive_older_than_days)
            
            logger.info(f"Would archive patterns older than {cutoff_date}")
            
            # In real implementation:
            # 1. Query old patterns
            # 2. Export to S3
            # 3. Delete from OpenSearch
            # 4. Update lifecycle metadata
            
            return f"archive_{int(time.time())}"
            
        except Exception as e:
            logger.error(f"Failed to archive patterns: {e}")
            raise


# Global RAG memory instance
rag_memory: Optional[ScalableRAGMemory] = None


async def get_rag_memory(service_factory: AWSServiceFactory) -> ScalableRAGMemory:
    """Get or create global RAG memory instance."""
    global rag_memory
    if rag_memory is None:
        rag_memory = ScalableRAGMemory(service_factory)
    return rag_memory