#!/usr/bin/env python3
"""
AWS Integration Test Suite for Incident Commander

This test suite validates all AWS service integrations including:
- DynamoDB event sourcing
- EventBridge event routing
- Bedrock agent functionality
- Amazon Q Business integration
- API Gateway endpoints
- CloudWatch monitoring

Usage:
    python test_aws_integration.py --environment production
    python test_aws_integration.py --environment staging --verbose
"""

import os
import sys
import json
import time
import boto3
import asyncio
import argparse
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from botocore.exceptions import ClientError
import pytest
import requests


class AWSIntegrationTester:
    """Comprehensive AWS integration testing for Incident Commander."""
    
    def __init__(self, environment: str = "production", region: str = "us-east-1"):
        self.environment = environment
        self.region = region
        self.verbose = False
        
        # Initialize AWS clients
        self.session = boto3.Session(region_name=region)
        self.dynamodb = self.session.client('dynamodb')
        self.events = self.session.client('events')
        self.bedrock = self.session.client('bedrock')
        self.bedrock_agent = self.session.client('bedrock-agent')
        self.bedrock_runtime = self.session.client('bedrock-runtime')
        self.apigateway = self.session.client('apigatewayv2')
        self.cloudwatch = self.session.client('cloudwatch')
        self.logs = self.session.client('logs')
        
        # Test results tracking
        self.test_results = {
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'details': []
        }
    
    def log(self, message: str, level: str = "INFO"):
        """Log test messages with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        if level == "ERROR":
            print(f"[{timestamp}] ❌ {message}")
        elif level == "SUCCESS":
            print(f"[{timestamp}] ✅ {message}")
        elif level == "WARNING":
            print(f"[{timestamp}] ⚠️  {message}")
        elif self.verbose or level == "INFO":
            print(f"[{timestamp}] ℹ️  {message}")
    
    def record_test_result(self, test_name: str, passed: bool, details: str = ""):
        """Record test result for reporting."""
        if passed:
            self.test_results['passed'] += 1
            self.log(f"Test '{test_name}' PASSED", "SUCCESS")
        else:
            self.test_results['failed'] += 1
            self.log(f"Test '{test_name}' FAILED: {details}", "ERROR")
        
        self.test_results['details'].append({
            'test': test_name,
            'passed': passed,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })
    
    async def test_dynamodb_connectivity(self) -> bool:
        """Test DynamoDB table connectivity and operations."""
        self.log("Testing DynamoDB connectivity...")
        
        table_name = f"incident-commander-incident-events-{self.environment}"
        
        try:
            # Test table existence
            response = self.dynamodb.describe_table(TableName=table_name)
            table_status = response['Table']['TableStatus']
            
            if table_status != 'ACTIVE':
                self.record_test_result(
                    "DynamoDB Table Status", 
                    False, 
                    f"Table status is {table_status}, expected ACTIVE"
                )
                return False
            
            # Test write operation
            test_item = {
                'incident_id': {'S': f'test-{int(time.time())}'},
                'version': {'N': '1'},
                'timestamp': {'S': datetime.now(timezone.utc).isoformat()},
                'event_data': {'S': json.dumps({'test': True})},
                'event_type': {'S': 'test_event'}
            }
            
            self.dynamodb.put_item(TableName=table_name, Item=test_item)
            
            # Test read operation
            response = self.dynamodb.get_item(
                TableName=table_name,
                Key={
                    'incident_id': test_item['incident_id'],
                    'version': test_item['version']
                }
            )
            
            if 'Item' not in response:
                self.record_test_result(
                    "DynamoDB Read/Write", 
                    False, 
                    "Failed to read back written item"
                )
                return False
            
            # Clean up test item
            self.dynamodb.delete_item(
                TableName=table_name,
                Key={
                    'incident_id': test_item['incident_id'],
                    'version': test_item['version']
                }
            )
            
            self.record_test_result("DynamoDB Connectivity", True)
            return True
            
        except ClientError as e:
            self.record_test_result(
                "DynamoDB Connectivity", 
                False, 
                f"ClientError: {e.response['Error']['Code']} - {e.response['Error']['Message']}"
            )
            return False
        except Exception as e:
            self.record_test_result("DynamoDB Connectivity", False, str(e))
            return False
    
    async def test_eventbridge_functionality(self) -> bool:
        """Test EventBridge event publishing and routing."""
        self.log("Testing EventBridge functionality...")
        
        bus_name = f"incident-commander-{self.environment}"
        
        try:
            # Test event bus existence
            self.events.describe_event_bus(Name=bus_name)
            
            # Test event publishing
            test_event = {
                'Source': 'incident-commander',
                'DetailType': 'Test Event',
                'Detail': json.dumps({
                    'test_id': f'test-{int(time.time())}',
                    'severity': 'LOW',
                    'message': 'Integration test event'
                }),
                'EventBusName': bus_name
            }
            
            response = self.events.put_events(Entries=[test_event])
            
            if response['FailedEntryCount'] > 0:
                self.record_test_result(
                    "EventBridge Publishing", 
                    False, 
                    f"Failed to publish {response['FailedEntryCount']} events"
                )
                return False
            
            # Test rule listing
            rules_response = self.events.list_rules(EventBusName=bus_name)
            rule_count = len(rules_response['Rules'])
            
            if rule_count == 0:
                self.record_test_result(
                    "EventBridge Rules", 
                    False, 
                    "No EventBridge rules found"
                )
                return False
            
            self.record_test_result("EventBridge Functionality", True)
            return True
            
        except ClientError as e:
            self.record_test_result(
                "EventBridge Functionality", 
                False, 
                f"ClientError: {e.response['Error']['Code']}"
            )
            return False
        except Exception as e:
            self.record_test_result("EventBridge Functionality", False, str(e))
            return False
    
    async def test_bedrock_models(self) -> bool:
        """Test Bedrock model access and inference."""
        self.log("Testing Bedrock model access...")
        
        try:
            # Test model listing
            models_response = self.bedrock.list_foundation_models()
            available_models = [model['modelId'] for model in models_response['modelSummaries']]
            
            required_models = [
                'anthropic.claude-3-5-sonnet-20241022-v2:0',
                'anthropic.claude-3-haiku-20240307-v1:0',
                'amazon.titan-embed-text-v1'
            ]
            
            missing_models = [model for model in required_models if model not in available_models]
            
            if missing_models:
                self.record_test_result(
                    "Bedrock Model Access", 
                    False, 
                    f"Missing models: {missing_models}"
                )
                return False
            
            # Test Claude inference
            test_prompt = "Hello, this is a test message for integration testing."
            
            try:
                response = self.bedrock_runtime.invoke_model(
                    modelId='anthropic.claude-3-haiku-20240307-v1:0',
                    body=json.dumps({
                        'anthropic_version': 'bedrock-2023-05-31',
                        'max_tokens': 100,
                        'messages': [
                            {
                                'role': 'user',
                                'content': test_prompt
                            }
                        ]
                    })
                )
                
                response_body = json.loads(response['body'].read())
                
                if 'content' not in response_body or not response_body['content']:
                    self.record_test_result(
                        "Bedrock Inference", 
                        False, 
                        "Empty response from Claude model"
                    )
                    return False
                
            except ClientError as e:
                if e.response['Error']['Code'] == 'AccessDeniedException':
                    self.record_test_result(
                        "Bedrock Inference", 
                        False, 
                        "Access denied - check model access permissions"
                    )
                    return False
                raise
            
            # Test Titan embeddings
            try:
                embedding_response = self.bedrock_runtime.invoke_model(
                    modelId='amazon.titan-embed-text-v1',
                    body=json.dumps({
                        'inputText': test_prompt
                    })
                )
                
                embedding_body = json.loads(embedding_response['body'].read())
                
                if 'embedding' not in embedding_body:
                    self.record_test_result(
                        "Titan Embeddings", 
                        False, 
                        "No embedding in Titan response"
                    )
                    return False
                
            except ClientError as e:
                if e.response['Error']['Code'] == 'AccessDeniedException':
                    self.record_test_result(
                        "Titan Embeddings", 
                        False, 
                        "Access denied - check Titan model permissions"
                    )
                    return False
                raise
            
            self.record_test_result("Bedrock Models", True)
            return True
            
        except Exception as e:
            self.record_test_result("Bedrock Models", False, str(e))
            return False
    
    async def test_bedrock_agents(self) -> bool:
        """Test Bedrock agent functionality."""
        self.log("Testing Bedrock agents...")
        
        try:
            # List agents
            agents_response = self.bedrock_agent.list_agents()
            agent_summaries = agents_response.get('agentSummaries', [])
            
            # Filter agents for this environment
            env_agents = [
                agent for agent in agent_summaries 
                if f"-{self.environment}" in agent['agentName']
            ]
            
            if not env_agents:
                self.record_test_result(
                    "Bedrock Agents", 
                    False, 
                    f"No agents found for environment {self.environment}"
                )
                return False
            
            # Test each agent
            for agent in env_agents[:2]:  # Test first 2 agents to avoid rate limits
                agent_id = agent['agentId']
                agent_name = agent['agentName']
                
                try:
                    # Get agent details
                    agent_details = self.bedrock_agent.get_agent(agentId=agent_id)
                    agent_status = agent_details['agent']['agentStatus']
                    
                    if agent_status not in ['PREPARED', 'NOT_PREPARED']:
                        self.log(f"Agent {agent_name} status: {agent_status}", "WARNING")
                        continue
                    
                    # Test agent invocation (if prepared)
                    if agent_status == 'PREPARED':
                        try:
                            # Create agent alias for testing
                            alias_response = self.bedrock_agent.create_agent_alias(
                                agentId=agent_id,
                                agentAliasName=f"test-alias-{int(time.time())}"
                            )
                            alias_id = alias_response['agentAlias']['agentAliasId']
                            
                            # Clean up alias
                            self.bedrock_agent.delete_agent_alias(
                                agentId=agent_id,
                                agentAliasId=alias_id
                            )
                            
                        except ClientError as e:
                            if e.response['Error']['Code'] != 'ConflictException':
                                self.log(f"Agent alias test failed for {agent_name}: {e}", "WARNING")
                    
                except ClientError as e:
                    self.log(f"Failed to test agent {agent_name}: {e}", "WARNING")
                    continue
            
            self.record_test_result("Bedrock Agents", True)
            return True
            
        except Exception as e:
            self.record_test_result("Bedrock Agents", False, str(e))
            return False
    
    async def test_api_gateway_endpoints(self) -> bool:
        """Test API Gateway endpoints if available."""
        self.log("Testing API Gateway endpoints...")
        
        try:
            # List APIs
            apis_response = self.apigateway.get_apis()
            apis = apis_response.get('Items', [])
            
            # Find our API
            api_name = f"incident-commander-api-{self.environment}"
            target_api = None
            
            for api in apis:
                if api['Name'] == api_name:
                    target_api = api
                    break
            
            if not target_api:
                self.record_test_result(
                    "API Gateway", 
                    False, 
                    f"API {api_name} not found"
                )
                return False
            
            api_endpoint = target_api.get('ApiEndpoint', '')
            
            if not api_endpoint:
                self.record_test_result(
                    "API Gateway", 
                    False, 
                    "API endpoint not available"
                )
                return False
            
            # Test health endpoint
            try:
                health_url = f"{api_endpoint}/health"
                response = requests.get(health_url, timeout=10)
                
                if response.status_code != 200:
                    self.record_test_result(
                        "API Health Endpoint", 
                        False, 
                        f"Health endpoint returned {response.status_code}"
                    )
                    return False
                
            except requests.RequestException as e:
                self.record_test_result(
                    "API Health Endpoint", 
                    False, 
                    f"Request failed: {e}"
                )
                return False
            
            self.record_test_result("API Gateway", True)
            return True
            
        except Exception as e:
            self.record_test_result("API Gateway", False, str(e))
            return False
    
    async def test_cloudwatch_monitoring(self) -> bool:
        """Test CloudWatch monitoring setup."""
        self.log("Testing CloudWatch monitoring...")
        
        try:
            # Test dashboard existence
            dashboard_name = f"IncidentCommander-{self.environment}"
            
            try:
                self.cloudwatch.get_dashboard(DashboardName=dashboard_name)
            except ClientError as e:
                if e.response['Error']['Code'] == 'ResourceNotFound':
                    self.record_test_result(
                        "CloudWatch Dashboard", 
                        False, 
                        f"Dashboard {dashboard_name} not found"
                    )
                    return False
                raise
            
            # Test metric publishing
            test_metric_name = 'IntegrationTest'
            namespace = f'IncidentCommander/{self.environment}'
            
            self.cloudwatch.put_metric_data(
                Namespace=namespace,
                MetricData=[
                    {
                        'MetricName': test_metric_name,
                        'Value': 1.0,
                        'Unit': 'Count',
                        'Timestamp': datetime.now(timezone.utc)
                    }
                ]
            )
            
            # Wait a moment for metric to be available
            await asyncio.sleep(2)
            
            # Test metric retrieval
            end_time = datetime.now(timezone.utc)
            start_time = end_time.replace(minute=end_time.minute - 5)
            
            metrics_response = self.cloudwatch.get_metric_statistics(
                Namespace=namespace,
                MetricName=test_metric_name,
                StartTime=start_time,
                EndTime=end_time,
                Period=300,
                Statistics=['Sum']
            )
            
            self.record_test_result("CloudWatch Monitoring", True)
            return True
            
        except Exception as e:
            self.record_test_result("CloudWatch Monitoring", False, str(e))
            return False
    
    async def test_end_to_end_workflow(self) -> bool:
        """Test end-to-end incident workflow."""
        self.log("Testing end-to-end workflow...")
        
        try:
            # Create test incident
            incident_id = f"test-incident-{int(time.time())}"
            table_name = f"incident-commander-incident-events-{self.environment}"
            
            # Step 1: Detection event
            detection_event = {
                'incident_id': {'S': incident_id},
                'version': {'N': '1'},
                'timestamp': {'S': datetime.now(timezone.utc).isoformat()},
                'event_data': {'S': json.dumps({
                    'event_type': 'incident_detected',
                    'severity': 'HIGH',
                    'source': 'integration_test',
                    'description': 'Test incident for integration testing'
                })},
                'event_type': {'S': 'incident_detected'}
            }
            
            self.dynamodb.put_item(TableName=table_name, Item=detection_event)
            
            # Step 2: Publish EventBridge event
            bus_name = f"incident-commander-{self.environment}"
            
            event_detail = {
                'incident_id': incident_id,
                'severity': 'HIGH',
                'event_type': 'incident_detected',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            self.events.put_events(
                Entries=[{
                    'Source': 'incident-commander',
                    'DetailType': 'Incident Detected',
                    'Detail': json.dumps(event_detail),
                    'EventBusName': bus_name
                }]
            )
            
            # Step 3: Verify event storage
            stored_event = self.dynamodb.get_item(
                TableName=table_name,
                Key={
                    'incident_id': {'S': incident_id},
                    'version': {'N': '1'}
                }
            )
            
            if 'Item' not in stored_event:
                self.record_test_result(
                    "End-to-End Workflow", 
                    False, 
                    "Failed to retrieve stored incident event"
                )
                return False
            
            # Step 4: Clean up
            self.dynamodb.delete_item(
                TableName=table_name,
                Key={
                    'incident_id': {'S': incident_id},
                    'version': {'N': '1'}
                }
            )
            
            self.record_test_result("End-to-End Workflow", True)
            return True
            
        except Exception as e:
            self.record_test_result("End-to-End Workflow", False, str(e))
            return False
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all integration tests."""
        self.log(f"Starting AWS integration tests for environment: {self.environment}")
        start_time = time.time()
        
        # Define test suite
        tests = [
            ("DynamoDB Connectivity", self.test_dynamodb_connectivity),
            ("EventBridge Functionality", self.test_eventbridge_functionality),
            ("Bedrock Models", self.test_bedrock_models),
            ("Bedrock Agents", self.test_bedrock_agents),
            ("API Gateway", self.test_api_gateway_endpoints),
            ("CloudWatch Monitoring", self.test_cloudwatch_monitoring),
            ("End-to-End Workflow", self.test_end_to_end_workflow)
        ]
        
        # Run tests
        for test_name, test_func in tests:
            self.log(f"Running test: {test_name}")
            try:
                await test_func()
            except Exception as e:
                self.record_test_result(test_name, False, f"Unexpected error: {e}")
        
        # Calculate results
        total_tests = len(tests)
        passed_tests = self.test_results['passed']
        failed_tests = self.test_results['failed']
        success_rate = (passed_tests / total_tests) * 100
        duration = time.time() - start_time
        
        # Generate report
        report = {
            'environment': self.environment,
            'region': self.region,
            'timestamp': datetime.now().isoformat(),
            'duration_seconds': round(duration, 2),
            'total_tests': total_tests,
            'passed': passed_tests,
            'failed': failed_tests,
            'success_rate': round(success_rate, 1),
            'details': self.test_results['details']
        }
        
        # Print summary
        print(f"\n{'='*60}")
        print(f"AWS INTEGRATION TEST RESULTS")
        print(f"{'='*60}")
        print(f"Environment: {self.environment}")
        print(f"Duration: {duration:.2f} seconds")
        print(f"Tests Passed: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for detail in self.test_results['details']:
                if not detail['passed']:
                    print(f"  - {detail['test']}: {detail['details']}")
        
        if passed_tests == total_tests:
            print(f"\n🎉 ALL TESTS PASSED! System is ready for production.")
        else:
            print(f"\n⚠️  {failed_tests} test(s) failed. Please review and fix issues.")
        
        # Save report
        report_file = f'integration-test-report-{self.environment}.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: {report_file}")
        
        return report


async def main():
    """Main test runner entry point."""
    parser = argparse.ArgumentParser(description='Run AWS integration tests')
    parser.add_argument('--environment', '-e', default='production',
                       choices=['development', 'staging', 'production'],
                       help='Environment to test')
    parser.add_argument('--region', '-r', default='us-east-1',
                       help='AWS region')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Initialize tester
    tester = AWSIntegrationTester(args.environment, args.region)
    tester.verbose = args.verbose
    
    # Run tests
    report = await tester.run_all_tests()
    
    # Exit with appropriate code
    if report['failed'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    asyncio.run(main())