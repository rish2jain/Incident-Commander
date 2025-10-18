"""
Hardened Diagnosis Agent with bounds checking and defensive programming.
"""

import asyncio
import json
import re
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass

from src.interfaces.agent import DiagnosisAgent
from src.models.incident import Incident
from src.models.agent import AgentRecommendation, ActionType, RiskLevel, Evidence, AgentMessage
from src.utils.constants import RESOURCE_LIMITS, PERFORMANCE_TARGETS
from src.utils.logging import get_logger
from src.utils.exceptions import ResourceLimitError, AgentTimeoutError


logger = get_logger("diagnosis_agent")


@dataclass
class LogAnalysisResult:
    """Result of log analysis."""
    source: str
    patterns_found: List[str]
    error_count: int
    warning_count: int
    anomalies: List[Dict[str, Any]]
    confidence: float
    analysis_duration_ms: int


@dataclass
class CorrelationResult:
    """Result of correlation analysis."""
    correlation_id: str
    related_events: List[Dict[str, Any]]
    correlation_strength: float
    root_cause_candidates: List[str]
    evidence_chain: List[str]


class HardenedDiagnosisAgent(DiagnosisAgent):
    """
    Hardened diagnosis agent with circular reference detection and bounds checking.
    """
    
    def __init__(self, name: str = "hardened_diagnosis"):
        """Initialize hardened diagnosis agent."""
        super().__init__(name)
        
        # Defensive programming limits
        self.max_log_size = RESOURCE_LIMITS["log_analysis_limit"]  # 100MB
        self.max_correlation_depth = RESOURCE_LIMITS["correlation_depth"]  # 5 levels
        self.processing_timeout = PERFORMANCE_TARGETS["diagnosis"]["max"]  # 180s
        
        # Circular reference detection
        self.analysis_stack: Set[str] = set()
        self.correlation_graph: Dict[str, Set[str]] = defaultdict(set)
        
        # Analysis cache with TTL
        self.analysis_cache: Dict[str, Tuple[Any, datetime]] = {}
        self.cache_ttl = timedelta(minutes=15)
        
        # Pattern recognition
        self.error_patterns = {
            "connection_timeout": r"connection.*timeout|timeout.*connection",
            "memory_error": r"out of memory|memory.*exhausted|oom",
            "database_error": r"database.*error|sql.*error|connection.*refused",
            "authentication_error": r"auth.*failed|unauthorized|forbidden",
            "rate_limit": r"rate.*limit|too many requests|throttled",
            "service_unavailable": r"service.*unavailable|503|502|504"
        }
        
        # Anomaly detection thresholds
        self.anomaly_thresholds = {
            "error_rate_spike": 0.1,  # 10% error rate
            "response_time_spike": 2.0,  # 2x normal response time
            "volume_spike": 3.0  # 3x normal volume
        }
    
    async def process_incident(self, incident: Incident) -> List[AgentRecommendation]:
        """
        Process incident and return diagnosis recommendations.
        
        Args:
            incident: Incident to diagnose
            
        Returns:
            List of diagnosis recommendations
        """
        start_time = time.time()
        
        try:
            self.increment_processing_count()
            
            # Prevent circular analysis
            if incident.id in self.analysis_stack:
                logger.warning(f"Circular reference detected for incident {incident.id}")
                return []
            
            self.analysis_stack.add(incident.id)
            
            try:
                # Perform root cause analysis
                root_cause_analysis = await self.trace_root_cause(incident)
                
                # Generate recommendations based on analysis
                recommendations = await self._generate_diagnosis_recommendations(
                    incident, root_cause_analysis
                )
                
                # Check processing time
                processing_time = time.time() - start_time
                if processing_time > self.processing_timeout:
                    logger.warning(f"Diagnosis processing exceeded timeout: {processing_time}s")
                
                return recommendations
                
            finally:
                self.analysis_stack.discard(incident.id)
            
        except Exception as e:
            self.increment_error_count()
            logger.error(f"Diagnosis agent processing failed: {e}")
            raise
    
    async def analyze_logs(self, log_sources: List[str], 
                          time_range: tuple) -> Dict[str, Any]:
        """
        Analyze logs with size bounds and defensive parsing.
        
        Args:
            log_sources: List of log sources to analyze
            time_range: (start_time, end_time) tuple
            
        Returns:
            Analysis results
        """
        start_time = time.time()
        analysis_results = {}
        
        try:
            for source in log_sources[:10]:  # Limit to 10 sources max
                # Check cache first
                cache_key = f"{source}_{time_range[0]}_{time_range[1]}"
                cached_result = self._get_cached_analysis(cache_key)
                if cached_result:
                    analysis_results[source] = cached_result
                    continue
                
                # Analyze log source with bounds checking
                try:
                    result = await self._analyze_single_log_source(source, time_range)
                    analysis_results[source] = result
                    
                    # Cache result
                    self._cache_analysis(cache_key, result)
                    
                except Exception as e:
                    logger.warning(f"Failed to analyze log source {source}: {e}")
                    analysis_results[source] = LogAnalysisResult(
                        source=source,
                        patterns_found=[],
                        error_count=0,
                        warning_count=0,
                        anomalies=[],
                        confidence=0.0,
                        analysis_duration_ms=0
                    )
                
                # Check timeout
                if time.time() - start_time > self.processing_timeout:
                    logger.warning("Log analysis timeout, returning partial results")
                    break
            
            return {
                "analysis_results": analysis_results,
                "total_sources_analyzed": len(analysis_results),
                "analysis_duration_ms": int((time.time() - start_time) * 1000)
            }
            
        except Exception as e:
            logger.error(f"Log analysis failed: {e}")
            raise
    
    async def _analyze_single_log_source(self, source: str, 
                                       time_range: tuple) -> LogAnalysisResult:
        """Analyze a single log source with defensive programming."""
        analysis_start = time.time()
        
        try:
            # Simulate log retrieval with size checking
            log_data = await self._retrieve_log_data(source, time_range)
            
            if len(log_data) > self.max_log_size:
                logger.warning(f"Log source {source} exceeds size limit, sampling")
                log_data = self._sample_log_data(log_data)
            
            # Parse logs defensively
            parsed_logs = self._parse_logs_safely(log_data)
            
            # Pattern matching
            patterns_found = []
            error_count = 0
            warning_count = 0
            
            for log_entry in parsed_logs:
                # Count errors and warnings
                if log_entry.get("level", "").lower() in ["error", "err"]:
                    error_count += 1
                elif log_entry.get("level", "").lower() in ["warning", "warn"]:
                    warning_count += 1
                
                # Pattern matching
                message = log_entry.get("message", "").lower()
                for pattern_name, pattern in self.error_patterns.items():
                    if re.search(pattern, message, re.IGNORECASE):
                        patterns_found.append(pattern_name)
            
            # Anomaly detection
            anomalies = self._detect_anomalies(parsed_logs)
            
            # Calculate confidence based on findings
            confidence = self._calculate_analysis_confidence(
                patterns_found, error_count, warning_count, anomalies
            )
            
            analysis_duration = int((time.time() - analysis_start) * 1000)
            
            return LogAnalysisResult(
                source=source,
                patterns_found=list(set(patterns_found)),  # Remove duplicates
                error_count=error_count,
                warning_count=warning_count,
                anomalies=anomalies,
                confidence=confidence,
                analysis_duration_ms=analysis_duration
            )
            
        except Exception as e:
            logger.error(f"Single log source analysis failed for {source}: {e}")
            raise
    
    async def _retrieve_log_data(self, source: str, time_range: tuple) -> str:
        """Simulate log data retrieval."""
        # In real implementation, this would connect to log aggregation service
        # For now, return simulated log data
        start_time, end_time = time_range
        
        # Simulate different log patterns based on source
        if "error" in source.lower():
            return """
2024-01-01T12:00:00Z ERROR Database connection timeout after 30s
2024-01-01T12:01:00Z ERROR Failed to authenticate user: invalid credentials
2024-01-01T12:02:00Z WARN High memory usage detected: 85%
2024-01-01T12:03:00Z ERROR Service unavailable: upstream service not responding
"""
        else:
            return """
2024-01-01T12:00:00Z INFO Request processed successfully
2024-01-01T12:01:00Z INFO User authenticated
2024-01-01T12:02:00Z WARN Response time above threshold: 2.5s
2024-01-01T12:03:00Z INFO Cache miss, fetching from database
"""
    
    def _sample_log_data(self, log_data: str) -> str:
        """Sample log data when it exceeds size limits."""
        lines = log_data.split('\n')
        
        if len(lines) <= 1000:
            return log_data
        
        # Take first 300, middle 400, and last 300 lines
        sampled_lines = (
            lines[:300] + 
            lines[len(lines)//2 - 200:len(lines)//2 + 200] + 
            lines[-300:]
        )
        
        return '\n'.join(sampled_lines)
    
    def _parse_logs_safely(self, log_data: str) -> List[Dict[str, Any]]:
        """Parse logs with defensive error handling."""
        parsed_logs = []
        
        for line_num, line in enumerate(log_data.split('\n')):
            if not line.strip():
                continue
            
            try:
                # Try to parse as JSON first
                if line.strip().startswith('{'):
                    log_entry = json.loads(line)
                else:
                    # Parse structured log format
                    log_entry = self._parse_structured_log_line(line)
                
                # Validate parsed entry
                if isinstance(log_entry, dict):
                    parsed_logs.append(log_entry)
                
            except Exception as e:
                # Create basic entry for unparseable lines
                parsed_logs.append({
                    "line_number": line_num,
                    "raw_message": line[:500],  # Limit length
                    "level": "unknown",
                    "timestamp": datetime.utcnow().isoformat(),
                    "parse_error": str(e)[:100]
                })
            
            # Limit total parsed logs
            if len(parsed_logs) >= 10000:
                logger.warning("Reached maximum parsed log limit")
                break
        
        return parsed_logs
    
    def _parse_structured_log_line(self, line: str) -> Dict[str, Any]:
        """Parse structured log line (timestamp level message format)."""
        # Simple regex for common log format
        pattern = r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z?)\s+(\w+)\s+(.*)'
        match = re.match(pattern, line)
        
        if match:
            timestamp, level, message = match.groups()
            return {
                "timestamp": timestamp,
                "level": level,
                "message": message
            }
        else:
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "level": "unknown",
                "message": line
            }
    
    def _detect_anomalies(self, parsed_logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect anomalies in parsed logs."""
        anomalies = []
        
        # Count errors by time window
        error_counts = defaultdict(int)
        total_counts = defaultdict(int)
        
        for log_entry in parsed_logs:
            timestamp = log_entry.get("timestamp", "")
            level = log_entry.get("level", "").lower()
            
            # Extract hour for windowing
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                hour_key = dt.strftime("%Y-%m-%d %H:00")
                
                total_counts[hour_key] += 1
                if level in ["error", "err"]:
                    error_counts[hour_key] += 1
                    
            except Exception:
                continue
        
        # Detect error rate spikes
        for hour_key in total_counts:
            if total_counts[hour_key] > 0:
                error_rate = error_counts[hour_key] / total_counts[hour_key]
                if error_rate > self.anomaly_thresholds["error_rate_spike"]:
                    anomalies.append({
                        "type": "error_rate_spike",
                        "time_window": hour_key,
                        "error_rate": error_rate,
                        "threshold": self.anomaly_thresholds["error_rate_spike"],
                        "severity": "high" if error_rate > 0.2 else "medium"
                    })
        
        return anomalies
    
    def _calculate_analysis_confidence(self, patterns_found: List[str], 
                                     error_count: int, warning_count: int,
                                     anomalies: List[Dict[str, Any]]) -> float:
        """Calculate confidence score for analysis results."""
        confidence = 0.5  # Base confidence
        
        # Increase confidence based on findings
        if patterns_found:
            confidence += 0.2 * min(len(patterns_found) / 3, 1.0)
        
        if error_count > 0:
            confidence += 0.1 * min(error_count / 10, 1.0)
        
        if anomalies:
            confidence += 0.2 * min(len(anomalies) / 2, 1.0)
        
        return min(1.0, confidence)
    
    async def trace_root_cause(self, incident: Incident) -> Dict[str, Any]:
        """
        Trace root cause with depth limiting and circular reference detection.
        
        Args:
            incident: Incident to analyze
            
        Returns:
            Root cause analysis results
        """
        try:
            # Analyze logs around incident time
            incident_time = incident.detected_at
            time_range = (
                incident_time - timedelta(minutes=30),
                incident_time + timedelta(minutes=10)
            )
            
            # Get relevant log sources based on incident metadata
            log_sources = self._identify_relevant_log_sources(incident)
            
            # Perform log analysis
            log_analysis = await self.analyze_logs(log_sources, time_range)
            
            # Search for similar historical patterns using RAG memory
            historical_patterns = await self._search_historical_patterns(incident)
            
            # Perform correlation analysis with depth limiting
            correlation_analysis = await self._perform_correlation_analysis(
                incident, log_analysis, depth=0
            )
            
            # Generate root cause hypothesis with historical context
            root_cause_hypothesis = self._generate_root_cause_hypothesis(
                incident, log_analysis, correlation_analysis, historical_patterns
            )
            
            return {
                "incident_id": incident.id,
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "log_analysis": log_analysis,
                "correlation_analysis": correlation_analysis,
                "historical_patterns": historical_patterns,
                "root_cause_hypothesis": root_cause_hypothesis,
                "confidence": self._calculate_overall_confidence(
                    log_analysis, correlation_analysis, historical_patterns
                )
            }
            
        except Exception as e:
            logger.error(f"Root cause analysis failed: {e}")
            raise
    
    def _identify_relevant_log_sources(self, incident: Incident) -> List[str]:
        """Identify relevant log sources based on incident characteristics."""
        log_sources = ["application", "system"]  # Default sources
        
        # Add sources based on incident metadata
        if incident.metadata.source_system:
            log_sources.append(incident.metadata.source_system)
        
        # Add sources based on tags
        for tag_key, tag_value in incident.metadata.tags.items():
            if tag_key in ["service", "component", "system"]:
                log_sources.append(tag_value)
        
        # Add sources based on business impact
        if incident.business_impact.service_tier.value == "tier_1":
            log_sources.extend(["api_gateway", "load_balancer", "database"])
        
        return list(set(log_sources))  # Remove duplicates
    
    async def _perform_correlation_analysis(self, incident: Incident, 
                                          log_analysis: Dict[str, Any],
                                          depth: int = 0) -> CorrelationResult:
        """Perform correlation analysis with depth limiting."""
        if depth >= self.max_correlation_depth:
            logger.warning(f"Reached maximum correlation depth: {depth}")
            return CorrelationResult(
                correlation_id=f"depth_limited_{incident.id}",
                related_events=[],
                correlation_strength=0.0,
                root_cause_candidates=[],
                evidence_chain=[]
            )
        
        correlation_id = f"corr_{incident.id}_{depth}"
        
        # Prevent circular correlation
        if correlation_id in self.analysis_stack:
            logger.warning(f"Circular correlation detected: {correlation_id}")
            return CorrelationResult(
                correlation_id=correlation_id,
                related_events=[],
                correlation_strength=0.0,
                root_cause_candidates=[],
                evidence_chain=["circular_reference_detected"]
            )
        
        self.analysis_stack.add(correlation_id)
        
        try:
            # Find related events based on patterns
            related_events = []
            root_cause_candidates = []
            evidence_chain = []
            
            # Analyze patterns from log analysis
            for source, analysis_result in log_analysis.get("analysis_results", {}).items():
                if hasattr(analysis_result, 'patterns_found'):
                    for pattern in analysis_result.patterns_found:
                        related_events.append({
                            "source": source,
                            "pattern": pattern,
                            "confidence": analysis_result.confidence
                        })
                        
                        # Generate root cause candidates
                        if pattern in ["database_error", "connection_timeout"]:
                            root_cause_candidates.append("database_connectivity_issue")
                            evidence_chain.append(f"Pattern '{pattern}' found in {source}")
                        elif pattern in ["memory_error", "service_unavailable"]:
                            root_cause_candidates.append("resource_exhaustion")
                            evidence_chain.append(f"Resource issue pattern '{pattern}' in {source}")
            
            # Calculate correlation strength
            correlation_strength = min(1.0, len(related_events) / 5.0)
            
            return CorrelationResult(
                correlation_id=correlation_id,
                related_events=related_events,
                correlation_strength=correlation_strength,
                root_cause_candidates=list(set(root_cause_candidates)),
                evidence_chain=evidence_chain
            )
            
        finally:
            self.analysis_stack.discard(correlation_id)
    
    async def _search_historical_patterns(self, incident: Incident) -> Dict[str, Any]:
        """Search for similar historical patterns using RAG memory."""
        try:
            from src.services.rag_memory import get_rag_memory
            from src.services.aws import AWSServiceFactory
            
            # Get RAG memory instance
            service_factory = AWSServiceFactory()
            rag_memory = await get_rag_memory(service_factory)
            
            # Search for similar patterns
            similar_patterns = await rag_memory.find_similar_patterns(
                incident,
                limit=5,
                min_similarity=0.7
            )
            
            # Extract relevant information
            pattern_insights = []
            for result in similar_patterns:
                pattern_insights.append({
                    "incident_id": result.incident_id,
                    "similarity_score": result.similarity_score,
                    "incident_type": result.pattern.incident_type,
                    "root_causes": result.pattern.root_causes,
                    "resolution_actions": result.pattern.resolution_actions,
                    "success_rate": result.pattern.success_rate,
                    "usage_count": result.pattern.usage_count
                })
            
            return {
                "similar_patterns_found": len(pattern_insights),
                "patterns": pattern_insights,
                "search_confidence": min(1.0, len(pattern_insights) / 3.0),  # Higher confidence with more patterns
                "historical_context_available": len(pattern_insights) > 0
            }
            
        except Exception as e:
            logger.warning(f"Failed to search historical patterns: {e}")
            return {
                "similar_patterns_found": 0,
                "patterns": [],
                "search_confidence": 0.0,
                "historical_context_available": False,
                "error": str(e)
            }
    
    def _generate_root_cause_hypothesis(self, incident: Incident,
                                      log_analysis: Dict[str, Any],
                                      correlation_analysis: CorrelationResult,
                                      historical_patterns: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate root cause hypothesis based on analysis and historical patterns."""
        hypothesis = {
            "primary_cause": "unknown",
            "contributing_factors": [],
            "confidence": 0.0,
            "evidence": [],
            "recommended_actions": [],
            "historical_validation": False
        }
        
        # Analyze root cause candidates from correlation
        correlation_confidence = 0.0
        if correlation_analysis.root_cause_candidates:
            # Use most common candidate as primary cause
            candidate_counts = defaultdict(int)
            for candidate in correlation_analysis.root_cause_candidates:
                candidate_counts[candidate] += 1
            
            primary_cause = max(candidate_counts.items(), key=lambda x: x[1])
            hypothesis["primary_cause"] = primary_cause[0]
            correlation_confidence = min(1.0, primary_cause[1] / 3.0)
            
            # Add evidence from correlation analysis
            hypothesis["evidence"] = correlation_analysis.evidence_chain
        
        # Enhance with historical patterns if available
        historical_confidence = 0.0
        if historical_patterns and historical_patterns.get("historical_context_available"):
            # Look for patterns that match our hypothesis
            matching_patterns = []
            for pattern in historical_patterns.get("patterns", []):
                # Check if historical root causes match our hypothesis
                if hypothesis["primary_cause"] in pattern.get("root_causes", []):
                    matching_patterns.append(pattern)
            
            if matching_patterns:
                hypothesis["historical_validation"] = True
                historical_confidence = historical_patterns.get("search_confidence", 0.0)
                
                # Use historical resolution actions
                historical_actions = set()
                for pattern in matching_patterns:
                    historical_actions.update(pattern.get("resolution_actions", []))
                
                hypothesis["recommended_actions"] = list(historical_actions)
                
                # Add historical evidence
                hypothesis["evidence"].extend([
                    f"Historical pattern match: {len(matching_patterns)} similar incidents",
                    f"Average success rate: {sum(p.get('success_rate', 0) for p in matching_patterns) / len(matching_patterns):.2f}"
                ])
                
                # Update primary cause if historical data suggests different cause
                historical_causes = []
                for pattern in matching_patterns:
                    historical_causes.extend(pattern.get("root_causes", []))
                
                if historical_causes:
                    most_common_historical = max(set(historical_causes), key=historical_causes.count)
                    if most_common_historical != hypothesis["primary_cause"]:
                        hypothesis["contributing_factors"].append(hypothesis["primary_cause"])
                        hypothesis["primary_cause"] = most_common_historical
        
        # Fallback actions if no historical data
        if not hypothesis["recommended_actions"]:
            if hypothesis["primary_cause"] == "database_connectivity_issue":
                hypothesis["recommended_actions"] = [
                    "check_database_connections",
                    "verify_network_connectivity", 
                    "review_connection_pool_settings"
                ]
            elif hypothesis["primary_cause"] == "resource_exhaustion":
                hypothesis["recommended_actions"] = [
                    "scale_up_resources",
                    "check_memory_usage",
                    "review_resource_limits"
                ]
            else:
                hypothesis["recommended_actions"] = [
                    "investigate_logs",
                    "check_system_health",
                    "escalate_to_expert"
                ]
        
        # Calculate combined confidence
        if historical_confidence > 0:
            # Weight historical patterns more heavily if available
            hypothesis["confidence"] = (correlation_confidence * 0.4) + (historical_confidence * 0.6)
        else:
            hypothesis["confidence"] = correlation_confidence
        
        return hypothesis
    
    def _calculate_overall_confidence(self, log_analysis: Dict[str, Any],
                                    correlation_analysis: CorrelationResult,
                                    historical_patterns: Dict[str, Any] = None) -> float:
        """Calculate overall confidence in the diagnosis."""
        confidences = []
        
        # Add log analysis confidences
        for source, analysis_result in log_analysis.get("analysis_results", {}).items():
            if hasattr(analysis_result, 'confidence'):
                confidences.append(analysis_result.confidence)
        
        # Add correlation confidence
        confidences.append(correlation_analysis.correlation_strength)
        
        # Add historical pattern confidence if available
        if historical_patterns and historical_patterns.get("historical_context_available"):
            historical_confidence = historical_patterns.get("search_confidence", 0.0)
            # Weight historical patterns more heavily
            confidences.append(historical_confidence * 1.5)
        
        if not confidences:
            return 0.0
        
        # Return weighted average, capped at 1.0
        return min(1.0, sum(confidences) / len(confidences))
    
    async def _generate_diagnosis_recommendations(self, incident: Incident,
                                                root_cause_analysis: Dict[str, Any]) -> List[AgentRecommendation]:
        """Generate diagnosis recommendations based on analysis."""
        recommendations = []
        
        hypothesis = root_cause_analysis.get("root_cause_hypothesis", {})
        primary_cause = hypothesis.get("primary_cause", "unknown")
        confidence = hypothesis.get("confidence", 0.0)
        
        if primary_cause != "unknown" and confidence > 0.3:
            # Create recommendation based on root cause
            recommendation = AgentRecommendation(
                agent_name=self.agent_type,
                incident_id=incident.id,
                action_type=ActionType.ESCALATE_INCIDENT,
                action_id=f"diagnosis_{primary_cause}",
                confidence=confidence,
                risk_level=RiskLevel.MEDIUM,
                estimated_impact="Provides root cause analysis for targeted resolution",
                reasoning=f"Diagnosed root cause as {primary_cause} with {confidence:.2f} confidence",
                urgency=0.6
            )
            
            # Add evidence from analysis
            for evidence_item in hypothesis.get("evidence", []):
                recommendation.add_evidence(
                    source="log_analysis",
                    data={"evidence": evidence_item, "primary_cause": primary_cause},
                    confidence=confidence,
                    description=f"Evidence supporting {primary_cause} diagnosis"
                )
            
            recommendations.append(recommendation)
        
        return recommendations
    
    def _get_cached_analysis(self, cache_key: str) -> Optional[LogAnalysisResult]:
        """Get cached analysis result if still valid."""
        if cache_key in self.analysis_cache:
            result, timestamp = self.analysis_cache[cache_key]
            if datetime.utcnow() - timestamp < self.cache_ttl:
                return result
            else:
                del self.analysis_cache[cache_key]
        return None
    
    def _cache_analysis(self, cache_key: str, result: LogAnalysisResult) -> None:
        """Cache analysis result with timestamp."""
        self.analysis_cache[cache_key] = (result, datetime.utcnow())
        
        # Clean old cache entries
        if len(self.analysis_cache) > 100:
            oldest_key = min(self.analysis_cache.keys(), 
                           key=lambda k: self.analysis_cache[k][1])
            del self.analysis_cache[oldest_key]
    
    async def handle_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Handle message from another agent."""
        try:
            logger.info(f"Diagnosis agent received message: {message.message_type}")
            
            if message.message_type == "health_check":
                return AgentMessage(
                    sender_agent=self.agent_type,
                    recipient_agent=message.sender_agent,
                    message_type="health_response",
                    payload={
                        "status": "healthy",
                        "processing_count": self.processing_count,
                        "cache_size": len(self.analysis_cache),
                        "analysis_stack_size": len(self.analysis_stack)
                    },
                    correlation_id=message.correlation_id
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to handle message: {e}")
            return None
    
    async def health_check(self) -> bool:
        """Perform health check for diagnosis agent."""
        try:
            # Check analysis stack for potential deadlocks
            if len(self.analysis_stack) > 10:
                logger.warning("Analysis stack size is high, potential deadlock")
                self.is_healthy = False
                return False
            
            # Check cache size
            if len(self.analysis_cache) > 1000:
                logger.warning("Analysis cache is too large")
                # Clean cache
                self.analysis_cache.clear()
            
            # Check error rate
            if self.error_count > 20:
                self.is_healthy = False
                return False
            
            self.update_heartbeat()
            self.is_healthy = True
            return True
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            self.is_healthy = False
            return False