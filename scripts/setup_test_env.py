#!/usr/bin/env python3
"""
Set up test environment with all necessary dependencies and configurations.
"""

import os
import sys
import subprocess
from pathlib import Path


def install_test_dependencies():
    """Install test dependencies."""
    print("Installing test dependencies...")
    
    test_deps = [
        'pytest>=7.4.0',
        'pytest-asyncio>=0.21.0',
        'pytest-cov>=4.1.0',
        'pytest-mock>=3.12.0',
        'moto[all]>=4.2.0',
        'httpx>=0.25.0',
    ]
    
    for dep in test_deps:
        try:
            result = subprocess.run([sys.executable, '-m', 'pip', 'install', dep], 
                                  check=True, capture_output=True, text=True)
            print(f"✅ Installed {dep}")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {dep}")
            print(f"Error: {e.stderr}")
            sys.exit(1)


def setup_local_services():
    """Set up local services for testing."""
    print("Setting up local services...")
    
    # Create docker-compose override for testing
    docker_compose_test = """
version: '3.8'
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes
    
  localstack:
    image: localstack/localstack:latest
    ports:
      - "4566:4566"
    environment:
      - SERVICES=dynamodb,s3,kinesis,cloudwatch,opensearch
      - DEBUG=1
      - DATA_DIR=/tmp/localstack/data
    volumes:
      - "./tmp/localstack:/tmp/localstack"
      - "/var/run/docker.sock:/var/run/docker.sock"
"""
    
    test_compose_path = Path("docker-compose.test.yml")
    with open(test_compose_path, 'w') as f:
        f.write(docker_compose_test)
    
    print(f"Created {test_compose_path}")
    print("Run 'docker-compose -f docker-compose.test.yml up -d' to start test services")


def create_test_env_file():
    """Create test environment file."""
    test_env_content = """
# Test Environment Configuration
ENVIRONMENT=test
DEBUG=true
LOG_LEVEL=DEBUG

# AWS Configuration (for LocalStack)
AWS_ACCESS_KEY_ID=test-access-key
AWS_SECRET_ACCESS_KEY=test-secret-key
AWS_DEFAULT_REGION=us-east-1
AWS_ENDPOINT_URL=http://localhost:4566

# Service Configuration
REDIS_URL=redis://localhost:6379
DATABASE_URL=sqlite:///:memory:

# External Service Mocks
DATADOG_API_KEY=test-datadog-key
PAGERDUTY_API_KEY=test-pagerduty-key
SLACK_BOT_TOKEN=test-slack-token
OPENAI_API_KEY=test-openai-key

# OpenSearch Configuration
OPENSEARCH_ENDPOINT=http://localhost:9200
OPENSEARCH_USERNAME=test
OPENSEARCH_PASSWORD=test

# Performance Limits
COST_BUDGET_LIMIT=200.0
MAX_CONCURRENT_INCIDENTS=10
AGENT_TIMEOUT_SECONDS=30
"""
    
    env_test_path = Path(".env.test")
    with open(env_test_path, 'w') as f:
        f.write(test_env_content.strip())
    
    print(f"Created {env_test_path}")


def setup_test_directories():
    """Set up test directory structure."""
    test_dirs = [
        "tests/unit",
        "tests/integration", 
        "tests/validation",
        "tests/mocks",
        "tests/fixtures",
        "tmp/localstack",
        "htmlcov"
    ]
    
    for dir_path in test_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")


def main():
    """Main setup function."""
    print("Setting up test environment for Incident Commander...")
    
    # Change to project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    setup_test_directories()
    create_test_env_file()
    setup_local_services()
    install_test_dependencies()
    
    print("\nTest environment setup complete!")
    print("\nNext steps:")
    print("1. Start test services: docker-compose -f docker-compose.test.yml up -d")
    print("2. Run tests: python tests/run_tests.py")
    print("3. Or run specific test types: python tests/run_tests.py unit")


if __name__ == '__main__':
    main()