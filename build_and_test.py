#!/usr/bin/env python3
"""
Build and test script for Incident Commander.
Validates core functionality and runs essential tests.
"""

import os
import sys
import subprocess
import asyncio
from pathlib import Path

def run_command(cmd: str, description: str) -> bool:
    """Run a command and return success status."""
    print(f"\n🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"Exit code: {e.returncode}")
        if e.stdout:
            print(f"STDOUT:\n{e.stdout}")
        if e.stderr:
            print(f"STDERR:\n{e.stderr}")
        return False

def setup_test_environment():
    """Set up test environment variables."""
    os.environ.setdefault('AWS_ACCESS_KEY_ID', 'test-access-key')
    os.environ.setdefault('AWS_SECRET_ACCESS_KEY', 'test-secret-key')
    os.environ.setdefault('AWS_DEFAULT_REGION', 'us-east-1')
    os.environ.setdefault('AWS_REGION', 'us-east-1')
    os.environ.setdefault('ENVIRONMENT', 'test')
    os.environ.setdefault('DEBUG', 'true')
    os.environ.setdefault('REDIS_URL', 'redis://localhost:6379')
    os.environ.setdefault('AWS_ENDPOINT_URL', 'http://localhost:4566')

def main():
    """Main build and test routine."""
    print("🚀 Incident Commander - Build and Test")
    print("=" * 50)
    
    # Setup test environment
    setup_test_environment()
    
    # Check if virtual environment is activated
    if not os.environ.get('VIRTUAL_ENV'):
        print("⚠️  Warning: Virtual environment not detected")
        print("   Please run: source .venv/bin/activate")
    
    success_count = 0
    total_tests = 0
    
    # Test 1: Import core modules
    total_tests += 1
    if run_command(
        "python -c 'from src.main import app; print(\"FastAPI app imported successfully\")'",
        "Testing core module imports"
    ):
        success_count += 1
    
    # Test 2: Run foundation tests
    total_tests += 1
    if run_command(
        "python -m pytest tests/test_foundation.py -v --tb=short",
        "Running foundation tests"
    ):
        success_count += 1
    
    # Test 3: Run core unit tests
    total_tests += 1
    if run_command(
        "python -m pytest tests/unit/test_constants.py tests/unit/test_core.py -v --tb=short",
        "Running core unit tests"
    ):
        success_count += 1
    
    # Test 4: Test AWS service factory
    total_tests += 1
    if run_command(
        "python -c 'from src.services.aws import get_aws_service_factory; print(\"AWS service factory created successfully\")'",
        "Testing AWS service factory"
    ):
        success_count += 1
    
    # Test 5: Test agent imports
    total_tests += 1
    if run_command(
        "python -c 'from agents.detection.agent import DetectionAgent; from agents.diagnosis.agent import DiagnosisAgent; print(\"Agent imports successful\")'",
        "Testing agent imports"
    ):
        success_count += 1
    
    # Test 6: Validate configuration
    total_tests += 1
    if run_command(
        "python -c 'from src.utils.config import config; print(f\"Configuration loaded: {config.environment}\")'",
        "Testing configuration loading"
    ):
        success_count += 1
    
    # Summary
    print("\n" + "=" * 50)
    print(f"📊 Build and Test Summary")
    print(f"✅ Passed: {success_count}/{total_tests}")
    print(f"❌ Failed: {total_tests - success_count}/{total_tests}")
    
    if success_count == total_tests:
        print("\n🎉 All core tests passed! The system is ready for development.")
        return 0
    else:
        print(f"\n⚠️  {total_tests - success_count} test(s) failed. Please review the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())