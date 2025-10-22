#!/usr/bin/env python3
"""
Infrastructure Update Validation Script
Validates the LocalStack configuration changes and overall infrastructure health.
"""

import os
import sys
import json
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

# Timeout constant for subprocess calls
SUBPROCESS_TIMEOUT = 30

class InfrastructureValidator:
    """Validates infrastructure configuration and deployment readiness."""
    
    def __init__(self):
        self.results = {
            "docker_compose": {"status": "pending", "details": []},
            "localstack_config": {"status": "pending", "details": []},
            "cdk_infrastructure": {"status": "pending", "details": []},
            "environment_config": {"status": "pending", "details": []},
            "monitoring_setup": {"status": "pending", "details": []},
            "security_validation": {"status": "pending", "details": []},
            "deployment_readiness": {"status": "pending", "details": []}
        }
    
    def validate_docker_compose(self) -> bool:
        """Validate Docker Compose configuration."""
        print("🐳 Validating Docker Compose configuration...")
        
        try:
            # Check docker-compose.yml syntax
            try:
                result = subprocess.run(
                    ["docker-compose", "config"],
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=SUBPROCESS_TIMEOUT
                )
            except subprocess.TimeoutExpired:
                print(f"❌ Docker Compose config check timed out after {SUBPROCESS_TIMEOUT}s")
                return False
            
            self.results["docker_compose"]["details"].append("✅ Docker Compose syntax valid")
            
            # Validate LocalStack configuration changes
            with open("docker-compose.yml", "r") as f:
                content = f.read()
                
            # Check for updated LocalStack paths
            if "/var/lib/localstack/data" in content:
                self.results["docker_compose"]["details"].append("✅ LocalStack DATA_DIR updated to /var/lib/localstack/data")
            else:
                self.results["docker_compose"]["details"].append("❌ LocalStack DATA_DIR not properly configured")
                return False
                
            if "TMPDIR=/var/lib/localstack/tmp" in content:
                self.results["docker_compose"]["details"].append("✅ LocalStack TMPDIR configured")
            else:
                self.results["docker_compose"]["details"].append("❌ LocalStack TMPDIR not configured")
                return False
                
            # Check volume mapping
            if "localstack_data:/var/lib/localstack" in content:
                self.results["docker_compose"]["details"].append("✅ LocalStack volume mapping updated")
            else:
                self.results["docker_compose"]["details"].append("❌ LocalStack volume mapping incorrect")
                return False
            
            # Validate service health checks
            services_with_health_checks = ["localstack", "redis", "postgres", "prometheus", "grafana"]
            for service in services_with_health_checks:
                if f"{service}:" in content and "healthcheck:" in content:
                    self.results["docker_compose"]["details"].append(f"✅ {service} health check configured")
                else:
                    self.results["docker_compose"]["details"].append(f"⚠️ {service} health check missing")
            
            self.results["docker_compose"]["status"] = "passed"
            return True
            
        except subprocess.CalledProcessError as e:
            self.results["docker_compose"]["details"].append(f"❌ Docker Compose validation failed: {e}")
            self.results["docker_compose"]["status"] = "failed"
            return False
    
    def validate_localstack_config(self) -> bool:
        """Validate LocalStack configuration compatibility."""
        print("🏗️ Validating LocalStack configuration...")
        
        try:
            # Check required services
            required_services = [
                "dynamodb", "s3", "kinesis", "lambda", 
                "ecs", "bedrock", "secretsmanager", "iam", "sts"
            ]
            
            with open("docker-compose.yml", "r") as f:
                content = f.read()
            
            for service in required_services:
                if service in content:
                    self.results["localstack_config"]["details"].append(f"✅ {service} service enabled")
                else:
                    self.results["localstack_config"]["details"].append(f"❌ {service} service missing")
                    return False
            
            # Check persistence configuration
            if "PERSISTENCE=1" in content:
                self.results["localstack_config"]["details"].append("✅ LocalStack persistence enabled")
            else:
                self.results["localstack_config"]["details"].append("❌ LocalStack persistence not enabled")
                return False
            
            # Check Lambda executor
            if "LAMBDA_EXECUTOR=docker-reuse" in content:
                self.results["localstack_config"]["details"].append("✅ Lambda executor configured for performance")
            else:
                self.results["localstack_config"]["details"].append("⚠️ Lambda executor not optimized")
            
            self.results["localstack_config"]["status"] = "passed"
            return True
            
        except Exception as e:
            self.results["localstack_config"]["details"].append(f"❌ LocalStack validation failed: {e}")
            self.results["localstack_config"]["status"] = "failed"
            return False
    
    def validate_cdk_infrastructure(self) -> bool:
        """Validate CDK infrastructure configuration."""
        print("☁️ Validating CDK infrastructure...")
        
        try:
            # Check CDK synthesis
            try:
                result = subprocess.run(
                    ["cdk", "synth", "--all"],
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=SUBPROCESS_TIMEOUT
                )
            except subprocess.TimeoutExpired:
                print(f"❌ CDK synthesis timed out after {SUBPROCESS_TIMEOUT}s")
                return False
            
            self.results["cdk_infrastructure"]["details"].append("✅ CDK synthesis successful")
            
            # Check for expected stacks (check for full names as they appear in output)
            expected_stacks = [
                "IncidentCommanderCore-development",
                "IncidentCommanderNetworking-development", 
                "IncidentCommanderSecurity-development",
                "IncidentCommanderStorage-development",
                "IncidentCommanderBedrock-development",
                "IncidentCommanderCompute-development",
                "IncidentCommanderMonitoring-development"
            ]
            
            # Check both stdout and stderr since CDK outputs to both
            output_text = result.stdout + result.stderr
            
            for stack in expected_stacks:
                if stack in output_text:
                    self.results["cdk_infrastructure"]["details"].append(f"✅ {stack} stack defined")
                else:
                    self.results["cdk_infrastructure"]["details"].append(f"❌ {stack} stack missing")
                    return False
            
            # Check CDK diff (should show new resources for fresh deployment)
            try:
                diff_result = subprocess.run(
                    ["cdk", "diff"],
                    capture_output=True,
                    timeout=SUBPROCESS_TIMEOUT,
                    text=True
                )
            except subprocess.TimeoutExpired:
                print(f"❌ CDK diff timed out after {SUBPROCESS_TIMEOUT}s")
                return False
            
            if "Number of stacks with differences:" in diff_result.stdout:
                self.results["cdk_infrastructure"]["details"].append("✅ CDK diff shows infrastructure changes ready")
            else:
                self.results["cdk_infrastructure"]["details"].append("ℹ️ No CDK differences detected")
            
            self.results["cdk_infrastructure"]["status"] = "passed"
            return True
            
        except subprocess.CalledProcessError as e:
            self.results["cdk_infrastructure"]["details"].append(f"❌ CDK validation failed: {e}")
            self.results["cdk_infrastructure"]["status"] = "failed"
            return False
    
    def validate_environment_config(self) -> bool:
        """Validate environment configuration."""
        print("⚙️ Validating environment configuration...")
        
        try:
            # Check .env.example exists and is properly configured
            if not Path(".env.example").exists():
                self.results["environment_config"]["details"].append("❌ .env.example file missing")
                return False
            
            with open(".env.example", "r") as f:
                env_content = f.read()
            
            # Check for required environment variables
            required_vars = [
                "AWS_REGION", "AWS_ENDPOINT_URL", "BEDROCK_PRIMARY_MODEL",
                "DYNAMODB_TABLE_PREFIX", "REDIS_HOST", "API_BASE_URL"
            ]
            
            for var in required_vars:
                if f"{var}=" in env_content:
                    self.results["environment_config"]["details"].append(f"✅ {var} configured")
                else:
                    self.results["environment_config"]["details"].append(f"❌ {var} missing")
                    return False
            
            # Check LocalStack configuration
            if "AWS_ENDPOINT_URL=http://localhost:4566" in env_content:
                self.results["environment_config"]["details"].append("✅ LocalStack endpoint configured")
            else:
                self.results["environment_config"]["details"].append("❌ LocalStack endpoint not configured")
                return False
            
            # Check config.py compatibility
            if Path("src/utils/config.py").exists():
                self.results["environment_config"]["details"].append("✅ Configuration management module exists")
            else:
                self.results["environment_config"]["details"].append("❌ Configuration management module missing")
                return False
            
            self.results["environment_config"]["status"] = "passed"
            return True
            
        except Exception as e:
            self.results["environment_config"]["details"].append(f"❌ Environment validation failed: {e}")
            self.results["environment_config"]["status"] = "failed"
            return False
    
    def validate_monitoring_setup(self) -> bool:
        """Validate monitoring and observability setup."""
        print("📊 Validating monitoring setup...")
        
        try:
            # Check Prometheus configuration
            if Path("monitoring/prometheus.yml").exists():
                self.results["monitoring_setup"]["details"].append("✅ Prometheus configuration exists")
                
                with open("monitoring/prometheus.yml", "r") as f:
                    prom_config = f.read()
                
                if "incident-commander-api" in prom_config:
                    self.results["monitoring_setup"]["details"].append("✅ Incident Commander API monitoring configured")
                else:
                    self.results["monitoring_setup"]["details"].append("⚠️ API monitoring not configured")
            else:
                self.results["monitoring_setup"]["details"].append("❌ Prometheus configuration missing")
                return False
            
            # Check Grafana directories
            grafana_dirs = ["monitoring/grafana/dashboards", "monitoring/grafana/datasources"]
            for dir_path in grafana_dirs:
                if Path(dir_path).exists():
                    self.results["monitoring_setup"]["details"].append(f"✅ {dir_path} exists")
                else:
                    self.results["monitoring_setup"]["details"].append(f"❌ {dir_path} missing")
                    return False
            
            # Check for monitoring stack in docker-compose
            with open("docker-compose.yml", "r") as f:
                compose_content = f.read()
            
            monitoring_services = ["prometheus", "grafana"]
            for service in monitoring_services:
                if f"{service}:" in compose_content:
                    self.results["monitoring_setup"]["details"].append(f"✅ {service} service configured")
                else:
                    self.results["monitoring_setup"]["details"].append(f"❌ {service} service missing")
                    return False
            
            self.results["monitoring_setup"]["status"] = "passed"
            return True
            
        except Exception as e:
            self.results["monitoring_setup"]["details"].append(f"❌ Monitoring validation failed: {e}")
            self.results["monitoring_setup"]["status"] = "failed"
            return False
    
    def validate_security_configuration(self) -> bool:
        """Validate security configuration."""
        print("🔒 Validating security configuration...")
        
        try:
            # Check .gitignore for sensitive files
            if Path(".gitignore").exists():
                with open(".gitignore", "r") as f:
                    gitignore_content = f.read()
                
                sensitive_patterns = [".env", "*.key", "*.pem", "__pycache__"]
                for pattern in sensitive_patterns:
                    if pattern in gitignore_content:
                        self.results["security_validation"]["details"].append(f"✅ {pattern} ignored in git")
                    else:
                        self.results["security_validation"]["details"].append(f"⚠️ {pattern} not in .gitignore")
            
            # Check for hardcoded credentials in environment files
            with open(".env.example", "r") as f:
                env_content = f.read()
            
            # Should have test credentials only
            if "AWS_ACCESS_KEY_ID=test" in env_content and "AWS_SECRET_ACCESS_KEY=test" in env_content:
                self.results["security_validation"]["details"].append("✅ Only test credentials in .env.example")
            else:
                self.results["security_validation"]["details"].append("❌ Invalid credentials configuration")
                return False
            
            # Check for production security configurations
            security_vars = ["JWT_SECRET_KEY", "ENCRYPTION_KEY", "CORS_ORIGINS"]
            for var in security_vars:
                if f"{var}=" in env_content:
                    self.results["security_validation"]["details"].append(f"✅ {var} template configured")
                else:
                    self.results["security_validation"]["details"].append(f"❌ {var} template missing")
                    return False
            
            self.results["security_validation"]["status"] = "passed"
            return True
            
        except Exception as e:
            self.results["security_validation"]["details"].append(f"❌ Security validation failed: {e}")
            self.results["security_validation"]["status"] = "failed"
            return False
    
    def validate_deployment_readiness(self) -> bool:
        """Validate overall deployment readiness."""
        print("🚀 Validating deployment readiness...")
        
        try:
            # Check required files exist
            required_files = [
                "requirements.txt", "pyproject.toml", "cdk.json",
                "docker-compose.yml", ".env.example"
            ]
            
            for file_path in required_files:
                if Path(file_path).exists():
                    self.results["deployment_readiness"]["details"].append(f"✅ {file_path} exists")
                else:
                    self.results["deployment_readiness"]["details"].append(f"❌ {file_path} missing")
                    return False
            
            # Check infrastructure directory
            if Path("infrastructure").exists() and Path("infrastructure/app.py").exists():
                self.results["deployment_readiness"]["details"].append("✅ Infrastructure code ready")
            else:
                self.results["deployment_readiness"]["details"].append("❌ Infrastructure code missing")
                return False
            
            # Check source code structure
            if Path("src").exists() and Path("src/main.py").exists():
                self.results["deployment_readiness"]["details"].append("✅ Source code structure ready")
            else:
                self.results["deployment_readiness"]["details"].append("❌ Source code structure incomplete")
                return False
            
            # Check agent implementations
            if Path("agents").exists():
                agent_dirs = ["detection", "diagnosis", "prediction", "resolution", "communication"]
                for agent_dir in agent_dirs:
                    if Path(f"agents/{agent_dir}").exists():
                        self.results["deployment_readiness"]["details"].append(f"✅ {agent_dir} agent ready")
                    else:
                        self.results["deployment_readiness"]["details"].append(f"❌ {agent_dir} agent missing")
                        return False
            
            self.results["deployment_readiness"]["status"] = "passed"
            return True
            
        except Exception as e:
            self.results["deployment_readiness"]["details"].append(f"❌ Deployment readiness failed: {e}")
            self.results["deployment_readiness"]["status"] = "failed"
            return False
    
    def run_validation(self) -> Dict[str, Any]:
        """Run complete infrastructure validation."""
        print("🔍 Starting Infrastructure Validation...")
        print("=" * 60)
        
        validations = [
            ("Docker Compose", self.validate_docker_compose),
            ("LocalStack Config", self.validate_localstack_config),
            ("CDK Infrastructure", self.validate_cdk_infrastructure),
            ("Environment Config", self.validate_environment_config),
            ("Monitoring Setup", self.validate_monitoring_setup),
            ("Security Config", self.validate_security_configuration),
            ("Deployment Readiness", self.validate_deployment_readiness)
        ]
        
        all_passed = True
        
        for name, validation_func in validations:
            try:
                result = validation_func()
                if not result:
                    all_passed = False
                print()
            except Exception as e:
                print(f"❌ {name} validation failed with exception: {e}")
                all_passed = False
                print()
        
        # Generate summary
        self.generate_summary(all_passed)
        
        return {
            "overall_status": "passed" if all_passed else "failed",
            "results": self.results,
            "timestamp": time.time()
        }
    
    def generate_summary(self, all_passed: bool):
        """Generate validation summary."""
        print("=" * 60)
        print("📋 INFRASTRUCTURE VALIDATION SUMMARY")
        print("=" * 60)
        
        for category, result in self.results.items():
            status_icon = "✅" if result["status"] == "passed" else "❌" if result["status"] == "failed" else "⏳"
            print(f"{status_icon} {category.replace('_', ' ').title()}: {result['status'].upper()}")
            
            for detail in result["details"]:
                print(f"   {detail}")
            print()
        
        if all_passed:
            print("🎉 ALL VALIDATIONS PASSED!")
            print("✅ Infrastructure is ready for deployment")
            print("✅ LocalStack configuration updated successfully")
            print("✅ CDK infrastructure validated")
            print("✅ Security configurations verified")
            print("✅ Monitoring stack ready")
        else:
            print("⚠️ SOME VALIDATIONS FAILED!")
            print("❌ Please address the issues above before deployment")
        
        print("=" * 60)

def main():
    """Main validation function."""
    validator = InfrastructureValidator()
    results = validator.run_validation()
    
    # Save results to file
    with open("infrastructure_validation_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    # Exit with appropriate code
    sys.exit(0 if results["overall_status"] == "passed" else 1)

if __name__ == "__main__":
    main()