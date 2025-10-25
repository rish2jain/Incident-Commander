#!/usr/bin/env python3
"""
Deployment Validation Script for Incident Commander

Quick validation script to verify deployment status and system health.
This script performs essential checks without full integration testing.

Usage:
    python validate_deployment.py --environment production
    python validate_deployment.py --environment staging --quick
"""

import os
import sys
import json
import boto3
import argparse
import requests
from typing import Dict, List, Any
from datetime import datetime
from botocore.exceptions import ClientError


class DeploymentValidator:
    """Quick deployment validation for Incident Commander."""
    
    def __init__(self, environment: str = "production", region: str = "us-east-1"):
        self.environment = environment
        self.region = region
        
        # Initialize AWS clients
        self.session = boto3.Session(region_name=region)
        self.dynamodb = self.session.client('dynamodb')
        self.events = self.session.client('events')
        self.bedrock = self.session.client('bedrock')
        self.apigateway = self.session.client('apigatewayv2')
        self.cloudwatch = self.session.client('cloudwatch')
        
        self.validation_results = {
            'environment': environment,
            'region': region,
            'timestamp': datetime.utcnow().isoformat(),
            'checks': {},
            'overall_status': 'UNKNOWN'
        }
    
    def check_dynamodb_tables(self) -> bool:
        """Validate DynamoDB tables exist and are active."""
        print("🗄️  Checking DynamoDB tables...")
        
        expected_tables = [
            f'incident-commander-incident-events-{self.environment}',
            f'incident-commander-agent-state-{self.environment}',
            f'incident-commander-consensus-decisions-{self.environment}'
        ]
        
        active_tables = []
        missing_tables = []
        
        for table_name in expected_tables:
            try:
                response = self.dynamodb.describe_table(TableName=table_name)
                status = response['Table']['TableStatus']
                
                if status == 'ACTIVE':
                    active_tables.append(table_name)
                    print(f"  ✅ {table_name}: {status}")
                else:
                    print(f"  ⚠️  {table_name}: {status}")
                    
            except ClientError as e:
                if e.response['Error']['Code'] == 'ResourceNotFoundException':
                    missing_tables.append(table_name)
                    print(f"  ❌ {table_name}: NOT FOUND")
                else:
                    print(f"  ❌ {table_name}: ERROR - {e}")
        
        success = len(active_tables) == len(expected_tables)
        
        self.validation_results['checks']['dynamodb'] = {
            'status': 'PASS' if success else 'FAIL',
            'active_tables': len(active_tables),
            'expected_tables': len(expected_tables),
            'missing_tables': missing_tables
        }
        
        return success
    
    def check_eventbridge_setup(self) -> bool:
        """Validate EventBridge configuration."""
        print("📡 Checking EventBridge setup...")
        
        bus_name = f"incident-commander-{self.environment}"
        
        try:
            # Check event bus
            self.events.describe_event_bus(Name=bus_name)
            print(f"  ✅ Event bus '{bus_name}' exists")
            
            # Check rules
            rules_response = self.events.list_rules(EventBusName=bus_name)
            rule_count = len(rules_response['Rules'])
            
            print(f"  ✅ Found {rule_count} EventBridge rules")
            
            success = rule_count > 0
            
            self.validation_results['checks']['eventbridge'] = {
                'status': 'PASS' if success else 'FAIL',
                'bus_exists': True,
                'rule_count': rule_count
            }
            
            return success
            
        except ClientError as e:
            print(f"  ❌ EventBridge check failed: {e}")
            
            self.validation_results['checks']['eventbridge'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            
            return False
    
    def check_bedrock_access(self) -> bool:
        """Validate Bedrock model access."""
        print("🧠 Checking Bedrock access...")
        
        try:
            # Check model access
            models_response = self.bedrock.list_foundation_models()
            available_models = [model['modelId'] for model in models_response['modelSummaries']]
            
            required_models = [
                'anthropic.claude-3-5-sonnet-20241022-v2:0',
                'anthropic.claude-3-haiku-20240307-v1:0',
                'amazon.titan-embed-text-v1'
            ]
            
            accessible_models = [model for model in required_models if model in available_models]
            
            print(f"  ✅ {len(accessible_models)}/{len(required_models)} required models accessible")
            
            success = len(accessible_models) == len(required_models)
            
            self.validation_results['checks']['bedrock'] = {
                'status': 'PASS' if success else 'FAIL',
                'accessible_models': len(accessible_models),
                'required_models': len(required_models),
                'missing_models': [m for m in required_models if m not in available_models]
            }
            
            return success
            
        except ClientError as e:
            print(f"  ❌ Bedrock access check failed: {e}")
            
            self.validation_results['checks']['bedrock'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            
            return False
    
    def check_api_gateway(self) -> bool:
        """Validate API Gateway deployment."""
        print("🌐 Checking API Gateway...")
        
        api_name = f"incident-commander-api-{self.environment}"
        
        try:
            # List APIs
            apis_response = self.apigateway.get_apis()
            apis = apis_response.get('Items', [])
            
            # Find our API
            target_api = None
            for api in apis:
                if api['Name'] == api_name:
                    target_api = api
                    break
            
            if target_api:
                api_endpoint = target_api.get('ApiEndpoint', '')
                print(f"  ✅ API Gateway found: {api_endpoint}")
                
                # Test health endpoint if available
                if api_endpoint:
                    try:
                        health_url = f"{api_endpoint}/health"
                        response = requests.get(health_url, timeout=5)
                        
                        if response.status_code == 200:
                            print(f"  ✅ Health endpoint responding: {response.status_code}")
                        else:
                            print(f"  ⚠️  Health endpoint status: {response.status_code}")
                            
                    except requests.RequestException as e:
                        print(f"  ⚠️  Health endpoint not accessible: {e}")
                
                self.validation_results['checks']['api_gateway'] = {
                    'status': 'PASS',
                    'endpoint': api_endpoint,
                    'api_id': target_api['ApiId']
                }
                
                return True
            else:
                print(f"  ❌ API Gateway '{api_name}' not found")
                
                self.validation_results['checks']['api_gateway'] = {
                    'status': 'FAIL',
                    'error': f"API {api_name} not found"
                }
                
                return False
                
        except ClientError as e:
            print(f"  ❌ API Gateway check failed: {e}")
            
            self.validation_results['checks']['api_gateway'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            
            return False
    
    def check_cloudwatch_monitoring(self) -> bool:
        """Validate CloudWatch monitoring setup."""
        print("📊 Checking CloudWatch monitoring...")
        
        dashboard_name = f"IncidentCommander-Executive-{self.environment}"
        
        try:
            # Check dashboard
            self.cloudwatch.get_dashboard(DashboardName=dashboard_name)
            print(f"  ✅ Dashboard '{dashboard_name}' exists")
            
            # Check alarms
            alarms_response = self.cloudwatch.describe_alarms(
                AlarmNamePrefix=f"IncidentCommander-"
            )
            alarm_count = len(alarms_response['MetricAlarms'])
            
            print(f"  ✅ Found {alarm_count} CloudWatch alarms")
            
            success = alarm_count > 0
            
            self.validation_results['checks']['cloudwatch'] = {
                'status': 'PASS' if success else 'FAIL',
                'dashboard_exists': True,
                'alarm_count': alarm_count
            }
            
            return success
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFound':
                print(f"  ❌ Dashboard '{dashboard_name}' not found")
            else:
                print(f"  ❌ CloudWatch check failed: {e}")
            
            self.validation_results['checks']['cloudwatch'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            
            return False
    
    def check_iam_permissions(self) -> bool:
        """Validate IAM roles and permissions."""
        print("🔐 Checking IAM permissions...")
        
        try:
            # Get current identity
            sts = self.session.client('sts')
            identity = sts.get_caller_identity()
            
            print(f"  ✅ Current identity: {identity['Arn']}")
            
            # Basic permission check - try to list DynamoDB tables
            tables = self.dynamodb.list_tables()
            print(f"  ✅ DynamoDB access confirmed ({len(tables['TableNames'])} tables visible)")
            
            self.validation_results['checks']['iam'] = {
                'status': 'PASS',
                'identity': identity['Arn'],
                'account': identity['Account']
            }
            
            return True
            
        except ClientError as e:
            print(f"  ❌ IAM permission check failed: {e}")
            
            self.validation_results['checks']['iam'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            
            return False
    
    def validate_deployment(self, quick: bool = False) -> Dict[str, Any]:
        """Run all validation checks."""
        print(f"🔍 Validating deployment for environment: {self.environment}")
        print(f"   Region: {self.region}")
        print(f"   Quick mode: {quick}")
        print("")
        
        # Define validation checks
        checks = [
            ("IAM Permissions", self.check_iam_permissions),
            ("DynamoDB Tables", self.check_dynamodb_tables),
            ("EventBridge Setup", self.check_eventbridge_setup),
            ("Bedrock Access", self.check_bedrock_access),
        ]
        
        # Add additional checks for full validation
        if not quick:
            checks.extend([
                ("API Gateway", self.check_api_gateway),
                ("CloudWatch Monitoring", self.check_cloudwatch_monitoring),
            ])
        
        # Run checks
        passed_checks = 0
        total_checks = len(checks)
        
        for check_name, check_func in checks:
            try:
                if check_func():
                    passed_checks += 1
            except Exception as e:
                print(f"  ❌ {check_name} failed with exception: {e}")
                self.validation_results['checks'][check_name.lower().replace(' ', '_')] = {
                    'status': 'FAIL',
                    'error': str(e)
                }
        
        # Calculate overall status
        success_rate = (passed_checks / total_checks) * 100
        
        if success_rate == 100:
            overall_status = 'PASS'
            status_emoji = '🎉'
            status_message = 'All validation checks passed!'
        elif success_rate >= 80:
            overall_status = 'PARTIAL'
            status_emoji = '⚠️'
            status_message = 'Most validation checks passed with some issues'
        else:
            overall_status = 'FAIL'
            status_emoji = '❌'
            status_message = 'Multiple validation checks failed'
        
        self.validation_results['overall_status'] = overall_status
        self.validation_results['success_rate'] = success_rate
        self.validation_results['passed_checks'] = passed_checks
        self.validation_results['total_checks'] = total_checks
        
        # Print summary
        print(f"\n{'='*60}")
        print(f"DEPLOYMENT VALIDATION RESULTS")
        print(f"{'='*60}")
        print(f"Environment: {self.environment}")
        print(f"Region: {self.region}")
        print(f"Checks Passed: {passed_checks}/{total_checks} ({success_rate:.1f}%)")
        print(f"Overall Status: {overall_status}")
        print(f"\n{status_emoji} {status_message}")
        
        # Show failed checks
        failed_checks = [
            name for name, result in self.validation_results['checks'].items()
            if result.get('status') == 'FAIL'
        ]
        
        if failed_checks:
            print(f"\n❌ Failed Checks:")
            for check in failed_checks:
                error = self.validation_results['checks'][check].get('error', 'Unknown error')
                print(f"  - {check.replace('_', ' ').title()}: {error}")
        
        # Save results
        results_file = f'validation-results-{self.environment}.json'
        with open(results_file, 'w') as f:
            json.dump(self.validation_results, f, indent=2)
        
        print(f"\n📄 Validation results saved to: {results_file}")
        
        return self.validation_results


def main():
    """Main validation entry point."""
    parser = argparse.ArgumentParser(description='Validate Incident Commander deployment')
    parser.add_argument('--environment', '-e', default='production',
                       choices=['development', 'staging', 'production'],
                       help='Environment to validate')
    parser.add_argument('--region', '-r', default='us-east-1',
                       help='AWS region')
    parser.add_argument('--quick', '-q', action='store_true',
                       help='Run quick validation (essential checks only)')
    
    args = parser.parse_args()
    
    # Initialize validator
    validator = DeploymentValidator(args.environment, args.region)
    
    # Run validation
    results = validator.validate_deployment(args.quick)
    
    # Exit with appropriate code
    if results['overall_status'] == 'PASS':
        sys.exit(0)
    elif results['overall_status'] == 'PARTIAL':
        sys.exit(1)
    else:
        sys.exit(2)


if __name__ == '__main__':
    main()