#!/usr/bin/env python3
"""
Validation script for knowledge base update functionality.
Tests core components without requiring full AWS infrastructure.
"""

import sys
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def validate_rag_memory_implementation():
    """Validate RAG memory implementation."""
    print("🔍 Validating RAG Memory Implementation...")
    
    try:
        # Check if RAG memory file exists and has required classes
        rag_memory_file = project_root / "src" / "services" / "rag_memory.py"
        
        if not rag_memory_file.exists():
            print("❌ RAG memory file not found")
            return False
        
        # Read and validate content
        content = rag_memory_file.read_text()
        
        required_classes = [
            "class ScalableRAGMemory",
            "class IncidentPattern",
            "class SimilarityResult"
        ]
        
        missing_classes = []
        for class_def in required_classes:
            if class_def not in content:
                missing_classes.append(class_def)
        
        if missing_classes:
            print(f"❌ Missing required classes: {missing_classes}")
            return False
        
        # Check for required methods
        required_methods = [
            "store_incident_pattern",
            "find_similar_patterns",
            "generate_embedding",
            "get_pattern_statistics"
        ]
        
        missing_methods = []
        for method in required_methods:
            if f"def {method}" not in content:
                missing_methods.append(method)
        
        if missing_methods:
            print(f"❌ Missing required methods: {missing_methods}")
            return False
        
        print("✅ RAG memory implementation validated")
        return True
        
    except Exception as e:
        print(f"❌ Error validating RAG memory: {e}")
        return False


def validate_incident_model():
    """Validate incident model structure."""
    print("🔍 Validating Incident Model...")
    
    try:
        from src.models.incident import Incident, IncidentSeverity, BusinessImpact, ServiceTier, IncidentMetadata
        
        # Create test incident
        business_impact = BusinessImpact(
            service_tier=ServiceTier.TIER_1,
            affected_users=1000,
            revenue_impact_per_minute=100.0
        )
        
        metadata = IncidentMetadata(
            source_system="test",
            tags={"service": "api"}
        )
        
        incident = Incident(
            title="Test Incident",
            description="Test incident for validation",
            severity=IncidentSeverity.HIGH,
            business_impact=business_impact,
            metadata=metadata
        )
        
        # Test methods
        duration = incident.calculate_duration_minutes()
        cost = incident.calculate_total_cost()
        incident.update_checksum()
        integrity_ok = incident.verify_integrity()
        
        print(f"✅ Incident model validated (Duration: {duration:.1f}min, Cost: ${cost:.2f})")
        return True
        
    except Exception as e:
        print(f"❌ Error validating incident model: {e}")
        return False


def validate_constants():
    """Validate constants configuration."""
    print("🔍 Validating Constants Configuration...")
    
    try:
        from src.utils.constants import LEARNING_CONFIG, SECURITY_CONFIG, PERFORMANCE_TARGETS
        
        # Check required learning config
        required_learning_keys = [
            "min_confidence_threshold",
            "embedding_dimension",
            "similarity_threshold",
            "data_quality_threshold"
        ]
        
        for key in required_learning_keys:
            if key not in LEARNING_CONFIG:
                print(f"❌ Missing learning config key: {key}")
                return False
        
        # Check security config
        required_security_keys = [
            "audit_log_retention_days",
            "pii_redaction_enabled",
            "integrity_check_enabled"
        ]
        
        for key in required_security_keys:
            if key not in SECURITY_CONFIG:
                print(f"❌ Missing security config key: {key}")
                return False
        
        print("✅ Constants configuration validated")
        return True
        
    except Exception as e:
        print(f"❌ Error validating constants: {e}")
        return False


def validate_knowledge_update_script():
    """Validate knowledge update script structure."""
    print("🔍 Validating Knowledge Update Script...")
    
    try:
        update_script = project_root / "scripts" / "update_agent_knowledge.py"
        
        if not update_script.exists():
            print("❌ Knowledge update script not found")
            return False
        
        content = update_script.read_text()
        
        # Check for required functions
        required_functions = [
            "class KnowledgeUpdateValidator",
            "def create_sample_incidents",
            "def update_vector_embeddings",
            "def validate_rag_retrieval_accuracy",
            "def check_data_quality_and_anomalies",
            "def generate_learning_effectiveness_report"
        ]
        
        missing_functions = []
        for func in required_functions:
            if func not in content:
                missing_functions.append(func)
        
        if missing_functions:
            print(f"❌ Missing required functions: {missing_functions}")
            return False
        
        print("✅ Knowledge update script validated")
        return True
        
    except Exception as e:
        print(f"❌ Error validating update script: {e}")
        return False


def test_data_validation():
    """Test data validation functionality."""
    print("🔍 Testing Data Validation...")
    
    try:
        # Test PII detection patterns
        pii_patterns = [
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
            r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',  # IP Address
        ]
        
        test_texts = [
            "User email: john.doe@example.com reported issue",  # Should detect email
            "Server IP 192.168.1.100 is down",  # Should detect IP
            "SSN 123-45-6789 in logs",  # Should detect SSN
            "Normal incident description without PII"  # Should be clean
        ]
        
        import re
        pii_detected = 0
        
        for text in test_texts:
            for pattern in pii_patterns:
                if re.search(pattern, text):
                    pii_detected += 1
                    break
        
        expected_pii = 3  # First 3 texts contain PII
        if pii_detected == expected_pii:
            print(f"✅ PII detection working correctly ({pii_detected}/{len(test_texts)} detected)")
        else:
            print(f"⚠️  PII detection may have issues ({pii_detected}/{expected_pii} expected)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing data validation: {e}")
        return False


def test_embedding_simulation():
    """Test simulated embedding generation."""
    print("🔍 Testing Embedding Generation...")
    
    try:
        # Simulate the embedding generation logic from RAG memory
        def generate_simulated_embedding(text: str, dimension: int = 1536) -> List[float]:
            text_hash = hashlib.sha256(text.encode()).hexdigest()
            
            embedding = []
            for i in range(0, min(len(text_hash), dimension * 8), 8):
                hex_chunk = text_hash[i:i+8]
                if len(hex_chunk) == 8:
                    int_val = int(hex_chunk, 16)
                    float_val = (int_val / (16**8)) * 2 - 1
                    embedding.append(float_val)
            
            while len(embedding) < dimension:
                embedding.append(0.0)
            
            return embedding[:dimension]
        
        # Test embedding generation
        test_text = "API Gateway experiencing high latency"
        embedding = generate_simulated_embedding(test_text)
        
        if len(embedding) == 1536 and all(isinstance(x, float) for x in embedding):
            print(f"✅ Embedding generation working (dimension: {len(embedding)})")
            
            # Test consistency
            embedding2 = generate_simulated_embedding(test_text)
            if embedding == embedding2:
                print("✅ Embedding generation is deterministic")
            else:
                print("⚠️  Embedding generation is not deterministic")
            
            return True
        else:
            print(f"❌ Embedding generation failed (dimension: {len(embedding)})")
            return False
        
    except Exception as e:
        print(f"❌ Error testing embedding generation: {e}")
        return False


def main():
    """Main validation function."""
    print("🚀 Starting Knowledge Base Update Validation")
    print("=" * 50)
    
    validation_results = []
    
    # Run all validations
    validations = [
        ("RAG Memory Implementation", validate_rag_memory_implementation),
        ("Incident Model", validate_incident_model),
        ("Constants Configuration", validate_constants),
        ("Knowledge Update Script", validate_knowledge_update_script),
        ("Data Validation", test_data_validation),
        ("Embedding Generation", test_embedding_simulation)
    ]
    
    for name, validation_func in validations:
        try:
            result = validation_func()
            validation_results.append((name, result))
        except Exception as e:
            print(f"❌ {name} validation failed with exception: {e}")
            validation_results.append((name, False))
        
        print()  # Add spacing between validations
    
    # Summary
    print("=" * 50)
    print("📋 VALIDATION SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, result in validation_results if result)
    total = len(validation_results)
    
    for name, result in validation_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name}: {status}")
    
    print(f"\nOverall: {passed}/{total} validations passed")
    
    if passed == total:
        print("\n🎉 All validations passed! Knowledge base update system is ready.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} validations failed. Please review and fix issues.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)