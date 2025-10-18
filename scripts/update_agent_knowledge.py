#!/usr/bin/env python3
"""
Enhanced script to update agent learning data after RAG memory system changes.
Implements comprehensive knowledge base refresh with validation and compliance checks.
"""

import asyncio
import sys
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.models.incident import Incident, IncidentSeverity, IncidentStatus, BusinessImpact, ServiceTier, IncidentMetadata
    from src.services.rag_memory import ScalableRAGMemory, get_rag_memory, IncidentPattern
    from src.services.aws import AWSServiceFactory, get_aws_service_factory
    from src.utils.logging import get_logger
    from src.utils.constants import LEARNING_CONFIG, SECURITY_CONFIG
    from src.utils.exceptions import ResourceLimitError
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("This script requires the incident commander project structure.")
    print("Please run from the project root directory.")
    sys.exit(1)

logger = get_logger(__name__)


class KnowledgeUpdateValidator:
    """Validates knowledge updates for data quality and compliance."""
    
    def __init__(self):
        self.pii_patterns = [
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
            r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',  # IP Address
            r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b'  # Credit Card
        ]
    
    def validate_incident_data(self, incident: Incident) -> Dict[str, Any]:
        """Validate incident data format and completeness."""
        validation_result = {
            "is_valid": True,
            "completeness_score": 0.0,
            "quality_issues": [],
            "pii_detected": False,
            "integrity_verified": False
        }
        
        # Check required fields
        required_fields = ["id", "title", "description", "severity", "business_impact"]
        missing_fields = []
        
        for field in required_fields:
            if not hasattr(incident, field) or getattr(incident, field) is None:
                missing_fields.append(field)
        
        if missing_fields:
            validation_result["quality_issues"].append(f"Missing required fields: {missing_fields}")
            validation_result["is_valid"] = False
        
        # Calculate completeness score
        total_fields = 10  # Total expected fields
        present_fields = total_fields - len(missing_fields)
        validation_result["completeness_score"] = present_fields / total_fields
        
        # Check for PII in description and title
        text_content = f"{incident.title} {incident.description}"
        for pattern in self.pii_patterns:
            import re
            if re.search(pattern, text_content):
                validation_result["pii_detected"] = True
                validation_result["quality_issues"].append("PII detected in incident content")
                break
        
        # Verify data integrity
        if incident.checksum:
            validation_result["integrity_verified"] = incident.verify_integrity()
            if not validation_result["integrity_verified"]:
                validation_result["quality_issues"].append("Data integrity check failed")
                validation_result["is_valid"] = False
        
        return validation_result


def create_sample_incidents() -> List[Incident]:
    """Create multiple sample incidents for comprehensive testing."""
    incidents = []
    
    # High severity API Gateway incident
    business_impact_1 = BusinessImpact(
        service_tier=ServiceTier.TIER_1,
        affected_users=5000,
        revenue_impact_per_minute=500.0,
        sla_breach_risk=0.8,
        reputation_impact=0.6
    )
    
    metadata_1 = IncidentMetadata(
        source_system="datadog",
        alert_ids=["alert-123", "alert-456"],
        tags={"service": "api-gateway", "environment": "production"},
        correlation_id="corr-789"
    )
    
    incident_1 = Incident(
        title="API Gateway High Latency",
        description="API Gateway experiencing high latency (>2s) affecting user authentication",
        severity=IncidentSeverity.HIGH,
        status=IncidentStatus.RESOLVED,
        business_impact=business_impact_1,
        metadata=metadata_1,
        detected_at=datetime.utcnow() - timedelta(minutes=45),
        started_at=datetime.utcnow() - timedelta(minutes=40),
        resolved_at=datetime.utcnow() - timedelta(minutes=5)
    )
    incident_1.update_checksum()
    incidents.append(incident_1)
    
    # Critical database incident
    business_impact_2 = BusinessImpact(
        service_tier=ServiceTier.TIER_1,
        affected_users=15000,
        revenue_impact_per_minute=2000.0,
        sla_breach_risk=0.95,
        reputation_impact=0.9
    )
    
    metadata_2 = IncidentMetadata(
        source_system="cloudwatch",
        alert_ids=["alert-db-001", "alert-db-002"],
        tags={"service": "database", "environment": "production", "cluster": "primary"},
        correlation_id="corr-db-456"
    )
    
    incident_2 = Incident(
        title="Database Connection Pool Exhaustion",
        description="Primary database cluster experiencing connection pool exhaustion, causing application timeouts",
        severity=IncidentSeverity.CRITICAL,
        status=IncidentStatus.RESOLVED,
        business_impact=business_impact_2,
        metadata=metadata_2,
        detected_at=datetime.utcnow() - timedelta(hours=2),
        started_at=datetime.utcnow() - timedelta(hours=2, minutes=5),
        resolved_at=datetime.utcnow() - timedelta(minutes=15)
    )
    incident_2.update_checksum()
    incidents.append(incident_2)
    
    # Medium severity memory leak incident
    business_impact_3 = BusinessImpact(
        service_tier=ServiceTier.TIER_2,
        affected_users=1000,
        revenue_impact_per_minute=100.0,
        sla_breach_risk=0.4,
        reputation_impact=0.2
    )
    
    metadata_3 = IncidentMetadata(
        source_system="prometheus",
        alert_ids=["alert-mem-001"],
        tags={"service": "worker-service", "environment": "production"},
        correlation_id="corr-mem-123"
    )
    
    incident_3 = Incident(
        title="Worker Service Memory Leak",
        description="Background worker service showing gradual memory increase over 6 hours",
        severity=IncidentSeverity.MEDIUM,
        status=IncidentStatus.RESOLVED,
        business_impact=business_impact_3,
        metadata=metadata_3,
        detected_at=datetime.utcnow() - timedelta(hours=6),
        started_at=datetime.utcnow() - timedelta(hours=6, minutes=10),
        resolved_at=datetime.utcnow() - timedelta(minutes=30)
    )
    incident_3.update_checksum()
    incidents.append(incident_3)
    
    return incidents


def create_resolution_actions_for_incident(incident: Incident) -> List[str]:
    """Create resolution actions based on incident characteristics."""
    actions = []
    
    # Actions based on service type
    service = incident.metadata.tags.get("service", "unknown")
    
    if "api-gateway" in service:
        actions.extend([
            "scale_api_gateway_instances",
            "increase_connection_pool_size",
            "enable_request_throttling",
            "restart_unhealthy_instances"
        ])
    elif "database" in service:
        actions.extend([
            "increase_connection_pool_size",
            "restart_database_connections",
            "scale_read_replicas",
            "optimize_slow_queries"
        ])
    elif "worker" in service:
        actions.extend([
            "restart_worker_processes",
            "increase_memory_limits",
            "scale_worker_instances",
            "clear_memory_leaks"
        ])
    
    # Actions based on severity
    if incident.severity == IncidentSeverity.CRITICAL:
        actions.extend([
            "activate_disaster_recovery",
            "notify_executive_team",
            "enable_maintenance_mode"
        ])
    elif incident.severity == IncidentSeverity.HIGH:
        actions.extend([
            "scale_infrastructure",
            "notify_on_call_team"
        ])
    
    return actions


async def update_vector_embeddings(rag_memory: ScalableRAGMemory, incidents: List[Incident]) -> Dict[str, Any]:
    """Update vector embeddings in the RAG memory system."""
    update_stats = {
        "total_incidents": len(incidents),
        "successful_updates": 0,
        "failed_updates": 0,
        "embedding_errors": [],
        "processing_time_ms": 0
    }
    
    start_time = datetime.utcnow()
    
    for incident in incidents:
        try:
            # Create resolution actions for this incident
            resolution_actions = create_resolution_actions_for_incident(incident)
            
            # Store incident pattern in RAG memory
            pattern_id = await rag_memory.store_incident_pattern(
                incident=incident,
                resolution_actions=resolution_actions,
                success_rate=0.95  # Assume high success rate for resolved incidents
            )
            
            logger.info(f"Stored pattern {pattern_id} for incident {incident.id}")
            update_stats["successful_updates"] += 1
            
        except Exception as e:
            logger.error(f"Failed to update embeddings for incident {incident.id}: {e}")
            update_stats["failed_updates"] += 1
            update_stats["embedding_errors"].append(str(e))
    
    end_time = datetime.utcnow()
    update_stats["processing_time_ms"] = int((end_time - start_time).total_seconds() * 1000)
    
    return update_stats


async def validate_rag_retrieval_accuracy(rag_memory: ScalableRAGMemory, test_incidents: List[Incident]) -> Dict[str, Any]:
    """Test RAG retrieval accuracy with known incidents."""
    accuracy_stats = {
        "total_tests": len(test_incidents),
        "accurate_retrievals": 0,
        "average_similarity": 0.0,
        "retrieval_errors": []
    }
    
    total_similarity = 0.0
    
    for incident in test_incidents:
        try:
            # Find similar patterns
            similar_patterns = await rag_memory.find_similar_patterns(
                incident=incident,
                limit=3,
                min_similarity=0.5
            )
            
            if similar_patterns:
                # Check if we found relevant patterns
                best_similarity = similar_patterns[0].similarity_score
                total_similarity += best_similarity
                
                # Consider accurate if similarity > 0.7
                if best_similarity > 0.7:
                    accuracy_stats["accurate_retrievals"] += 1
                
                logger.info(f"Found {len(similar_patterns)} similar patterns for {incident.id}, best similarity: {best_similarity:.3f}")
            else:
                logger.warning(f"No similar patterns found for incident {incident.id}")
                
        except Exception as e:
            logger.error(f"Retrieval test failed for incident {incident.id}: {e}")
            accuracy_stats["retrieval_errors"].append(str(e))
    
    if accuracy_stats["total_tests"] > 0:
        accuracy_stats["average_similarity"] = total_similarity / accuracy_stats["total_tests"]
    
    return accuracy_stats


async def check_data_quality_and_anomalies(incidents: List[Incident]) -> Dict[str, Any]:
    """Check for data quality issues and anomalies."""
    validator = KnowledgeUpdateValidator()
    quality_report = {
        "total_incidents": len(incidents),
        "valid_incidents": 0,
        "quality_issues": [],
        "pii_violations": 0,
        "integrity_failures": 0,
        "average_completeness": 0.0
    }
    
    total_completeness = 0.0
    
    for incident in incidents:
        validation_result = validator.validate_incident_data(incident)
        
        if validation_result["is_valid"]:
            quality_report["valid_incidents"] += 1
        
        if validation_result["pii_detected"]:
            quality_report["pii_violations"] += 1
        
        if not validation_result["integrity_verified"]:
            quality_report["integrity_failures"] += 1
        
        total_completeness += validation_result["completeness_score"]
        quality_report["quality_issues"].extend(validation_result["quality_issues"])
    
    if len(incidents) > 0:
        quality_report["average_completeness"] = total_completeness / len(incidents)
    
    return quality_report


async def generate_learning_effectiveness_report(rag_memory: ScalableRAGMemory) -> Dict[str, Any]:
    """Generate comprehensive learning effectiveness report."""
    try:
        # Get pattern statistics
        pattern_stats = await rag_memory.get_pattern_statistics()
        
        # Calculate learning metrics
        total_patterns = pattern_stats.get("total_patterns", 0)
        avg_success_rate = pattern_stats.get("average_success_rate", 0.0)
        avg_confidence = pattern_stats.get("average_confidence", 0.0)
        
        # Determine learning effectiveness
        effectiveness_score = 0.0
        if total_patterns > 0:
            effectiveness_score = (avg_success_rate * 0.4 + avg_confidence * 0.3 + min(total_patterns / 1000, 1.0) * 0.3)
        
        report = {
            "total_patterns_learned": total_patterns,
            "average_success_rate": avg_success_rate,
            "average_confidence": avg_confidence,
            "effectiveness_score": effectiveness_score,
            "learning_status": "excellent" if effectiveness_score > 0.8 else "good" if effectiveness_score > 0.6 else "needs_improvement",
            "pattern_distribution": pattern_stats.get("incident_type_distribution", []),
            "cache_efficiency": {
                "embedding_cache_size": pattern_stats.get("cache_stats", {}).get("embedding_cache_size", 0),
                "pattern_cache_size": pattern_stats.get("cache_stats", {}).get("pattern_cache_size", 0)
            }
        }
        
        return report
        
    except Exception as e:
        logger.error(f"Failed to generate learning effectiveness report: {e}")
        return {"error": str(e)}


async def main():
    """Enhanced main function for comprehensive knowledge base refresh."""
    
    print("🚀 Starting Enhanced Agent Knowledge Base Refresh")
    print("=" * 60)
    
    try:
        # Initialize services
        print("🔧 Initializing services...")
        service_factory = get_aws_service_factory()
        rag_memory = await get_rag_memory(service_factory)
        
        # Step 1: Create and validate incident data
        print("\n📊 Step 1: Creating and validating incident data...")
        incidents = create_sample_incidents()
        print(f"✅ Created {len(incidents)} sample incidents")
        
        for i, incident in enumerate(incidents, 1):
            print(f"   {i}. {incident.title} ({incident.severity})")
            print(f"      Duration: {incident.calculate_duration_minutes():.1f} min, Cost: ${incident.calculate_total_cost():.2f}")
        
        # Step 2: Validate data quality and check for issues
        print("\n🔍 Step 2: Checking data quality and anomalies...")
        quality_report = await check_data_quality_and_anomalies(incidents)
        
        print(f"   - Valid incidents: {quality_report['valid_incidents']}/{quality_report['total_incidents']}")
        print(f"   - Average completeness: {quality_report['average_completeness']:.1%}")
        print(f"   - PII violations: {quality_report['pii_violations']}")
        print(f"   - Integrity failures: {quality_report['integrity_failures']}")
        
        if quality_report['quality_issues']:
            print("   ⚠️  Quality issues detected:")
            for issue in quality_report['quality_issues'][:5]:  # Show first 5
                print(f"      - {issue}")
        
        # Step 3: Update vector embeddings
        print("\n🧠 Step 3: Updating vector embeddings in RAG memory...")
        embedding_stats = await update_vector_embeddings(rag_memory, incidents)
        
        print(f"   - Successful updates: {embedding_stats['successful_updates']}")
        print(f"   - Failed updates: {embedding_stats['failed_updates']}")
        print(f"   - Processing time: {embedding_stats['processing_time_ms']}ms")
        
        if embedding_stats['embedding_errors']:
            print("   ⚠️  Embedding errors:")
            for error in embedding_stats['embedding_errors'][:3]:
                print(f"      - {error}")
        
        # Step 4: Test RAG retrieval accuracy
        print("\n🔎 Step 4: Validating RAG retrieval accuracy...")
        accuracy_stats = await validate_rag_retrieval_accuracy(rag_memory, incidents)
        
        accuracy_rate = accuracy_stats['accurate_retrievals'] / max(accuracy_stats['total_tests'], 1)
        print(f"   - Retrieval accuracy: {accuracy_rate:.1%}")
        print(f"   - Average similarity: {accuracy_stats['average_similarity']:.3f}")
        print(f"   - Tests completed: {accuracy_stats['total_tests']}")
        
        if accuracy_stats['retrieval_errors']:
            print("   ⚠️  Retrieval errors:")
            for error in accuracy_stats['retrieval_errors'][:3]:
                print(f"      - {error}")
        
        # Step 5: Generate learning effectiveness report
        print("\n📈 Step 5: Generating learning effectiveness report...")
        learning_report = await generate_learning_effectiveness_report(rag_memory)
        
        if "error" not in learning_report:
            print(f"   - Total patterns learned: {learning_report['total_patterns_learned']}")
            print(f"   - Average success rate: {learning_report['average_success_rate']:.1%}")
            print(f"   - Average confidence: {learning_report['average_confidence']:.1%}")
            print(f"   - Effectiveness score: {learning_report['effectiveness_score']:.3f}")
            print(f"   - Learning status: {learning_report['learning_status']}")
            
            # Show pattern distribution
            if learning_report['pattern_distribution']:
                print("   - Top incident patterns:")
                for pattern in learning_report['pattern_distribution'][:3]:
                    print(f"      • {pattern.get('key', 'unknown')}: {pattern.get('doc_count', 0)} incidents")
        else:
            print(f"   ⚠️  Error generating report: {learning_report['error']}")
        
        # Step 6: Get comprehensive RAG memory statistics
        print("\n📊 Step 6: RAG Memory System Statistics...")
        try:
            pattern_stats = await rag_memory.get_pattern_statistics()
            
            if pattern_stats:
                print(f"   - Total patterns: {pattern_stats.get('total_patterns', 0)}")
                print(f"   - Index size: {pattern_stats.get('index_size_bytes', 0) / 1024 / 1024:.1f} MB")
                print(f"   - Cache efficiency:")
                cache_stats = pattern_stats.get('cache_stats', {})
                print(f"     • Embedding cache: {cache_stats.get('embedding_cache_size', 0)} entries")
                print(f"     • Pattern cache: {cache_stats.get('pattern_cache_size', 0)} entries")
            else:
                print("   ⚠️  No statistics available")
                
        except Exception as e:
            print(f"   ⚠️  Error getting statistics: {e}")
        
        # Step 7: Test similarity search with cross-validation
        print("\n🔍 Step 7: Testing similarity search indexes...")
        search_test_results = []
        
        for incident in incidents[:2]:  # Test with first 2 incidents
            try:
                similar_patterns = await rag_memory.find_similar_patterns(
                    incident=incident,
                    limit=3,
                    min_similarity=0.5
                )
                
                search_test_results.append({
                    "incident_id": incident.id,
                    "patterns_found": len(similar_patterns),
                    "best_similarity": similar_patterns[0].similarity_score if similar_patterns else 0.0
                })
                
            except Exception as e:
                logger.error(f"Search test failed for {incident.id}: {e}")
        
        if search_test_results:
            avg_patterns = sum(r["patterns_found"] for r in search_test_results) / len(search_test_results)
            avg_similarity = sum(r["best_similarity"] for r in search_test_results) / len(search_test_results)
            
            print(f"   - Average patterns found: {avg_patterns:.1f}")
            print(f"   - Average best similarity: {avg_similarity:.3f}")
            print(f"   - Search index status: {'✅ Healthy' if avg_similarity > 0.6 else '⚠️ Needs attention'}")
        
        # Step 8: Compliance and privacy validation
        print("\n🔒 Step 8: Privacy and compliance validation...")
        
        compliance_score = 1.0
        compliance_issues = []
        
        # Check PII redaction
        if quality_report['pii_violations'] > 0:
            compliance_score -= 0.3
            compliance_issues.append(f"{quality_report['pii_violations']} PII violations detected")
        
        # Check data integrity
        if quality_report['integrity_failures'] > 0:
            compliance_score -= 0.2
            compliance_issues.append(f"{quality_report['integrity_failures']} integrity failures")
        
        # Check data retention compliance
        if SECURITY_CONFIG["audit_log_retention_days"] < 2555:  # 7 years required
            compliance_score -= 0.1
            compliance_issues.append("Audit log retention below compliance requirement")
        
        compliance_score = max(0.0, compliance_score)
        
        print(f"   - Compliance score: {compliance_score:.1%}")
        print(f"   - PII redaction: {'✅ Compliant' if quality_report['pii_violations'] == 0 else '❌ Violations detected'}")
        print(f"   - Data integrity: {'✅ Verified' if quality_report['integrity_failures'] == 0 else '❌ Failures detected'}")
        
        if compliance_issues:
            print("   ⚠️  Compliance issues:")
            for issue in compliance_issues:
                print(f"      - {issue}")
        
        # Final summary
        print("\n" + "=" * 60)
        print("📋 KNOWLEDGE BASE REFRESH SUMMARY")
        print("=" * 60)
        
        overall_success = (
            embedding_stats['successful_updates'] > 0 and
            accuracy_rate > 0.6 and
            compliance_score > 0.7
        )
        
        print(f"Overall Status: {'✅ SUCCESS' if overall_success else '❌ NEEDS ATTENTION'}")
        print(f"Incidents Processed: {len(incidents)}")
        print(f"Embeddings Updated: {embedding_stats['successful_updates']}")
        print(f"Retrieval Accuracy: {accuracy_rate:.1%}")
        print(f"Compliance Score: {compliance_score:.1%}")
        print(f"Data Quality: {quality_report['average_completeness']:.1%}")
        
        if overall_success:
            print("\n🎉 Knowledge base refresh completed successfully!")
            print("   All systems are ready for enhanced incident response.")
        else:
            print("\n⚠️  Knowledge base refresh completed with issues.")
            print("   Review the errors above and re-run after fixes.")
        
        return 0 if overall_success else 1
        
    except Exception as e:
        print(f"\n❌ Critical error during knowledge base refresh: {e}")
        logger.error(f"Knowledge base refresh failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)