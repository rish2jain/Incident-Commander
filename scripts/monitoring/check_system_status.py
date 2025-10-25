#!/usr/bin/env python3
"""
System Status Check for Incident Commander

Quick health check script for monitoring system status.
Can be run periodically or integrated with monitoring systems.

Usage:
    python check_system_status.py --environment production
    python check_system_status.py --environment production --json
"""

import os
import sys
import json
import boto3
import argparse
import requests
from typing import Dict, Any
from datetime import datetime, timedelta
from botocore.exceptions import ClientError


class SystemStatusChecker:
    """Quick system status checker for Incident Commander."""
    
    def __init__(self, environment: str = "production", region: str = "us-east-1"):
        self.environment = environment
        self.region = region
        
        # Initialize AWS clients
        self.session = boto3.Session(region_name=region)
        self.dynamodb = self.session.client('dynamodb')
        self.cloudwatch = self.session.client('cloudwatch')
        self.apigateway = self.session.client('apigatewayv2')
        
        self.status = {
            'timestamp': datetime.utcnow().isoformat(),
            'environment': environment,
            'region': region,
            'overall_status': 'UNKNOWN',
            'components': {}
        }
    
    def check_dynamodb_health(self) -> Dict[str, Any]:
        """Check DynamoDB table health and performance."""
        try:
            table_name = f"incident-commander-incident-events-{self.environment}"
            
            # Check table status
            response = self.dynamodb.describe_table(TableName=table_name)
            table_status = response['Table']['TableStatus']
            
            # Get basic metrics
            item_count = response['Table'].get('ItemCount', 0)
            table_size = response['Table'].get('TableSizeBytes', 0)
            
            return {
                'status': 'HEALTHY' if table_status == 'ACTIVE' else 'UNHEALTHY',
                'table_status': table_status,
                'item_count': item_count,
                'size_bytes': table_size,
                'last_updated': response['Table'].get('TableCreationDateTime', '').isoformat() if response['Table'].get('TableCreationDateTime') else None
            }
            
        except ClientError as e:
            return {
                'status': 'ERROR',
                'error': str(e)
            }
    
    def check_api_health(self) -> Dict[str, Any]:
        """Check API Gateway health."""
        try:
            # Find API
            apis_response = self.apigateway.get_apis()
            api_name = f"incident-commander-api-{self.environment}"
            
            target_api = None
            for api in apis_response.get('Items', []):
                if api['Name'] == api_name:
                    target_api = api
                    break
            
            if not target_api:
                return {
                    'status': 'NOT_FOUND',
                    'error': f'API {api_name} not found'
                }
            
            api_endpoint = target_api.get('ApiEndpoint', '')
            
            # Test health endpoint
            if api_endpoint:
                try:
                    health_url = f"{api_endpoint}/health"
                    response = requests.get(health_url, timeout=5)
                    
                    return {
                        'status': 'HEALTHY' if response.status_code == 200 else 'UNHEALTHY',
                        'endpoint': api_endpoint,
                        'response_code': response.status_code,
                        'response_time_ms': int(response.elapsed.total_seconds() * 1000)
                    }
                    
                except requests.RequestException as e:
                    return {
                        'status': 'UNREACHABLE',
                        'endpoint': api_endpoint,
                        'error': str(e)
                    }
            else:
                return {
                    'status': 'NO_ENDPOINT',
                    'api_id': target_api['ApiId']
                }
                
        except ClientError as e:
            return {
                'status': 'ERROR',
                'error': str(e)
            }
    
    def check_cloudwatch_metrics(self) -> Dict[str, Any]:
        """Check recent CloudWatch metrics."""
        try:
            namespace = f"IncidentCommander/{self.environment}"
            
            # Get recent metrics (last 5 minutes)
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(minutes=5)
            
            metrics_to_check = [
                'SystemAvailability',
                'ErrorRate',
                'APILatency'
            ]
            
            metric_values = {}
            
            for metric_name in metrics_to_check:
                try:
                    response = self.cloudwatch.get_metric_statistics(
                        Namespace=namespace,
                        MetricName=metric_name,
                        StartTime=start_time,
                        EndTime=end_time,
                        Period=300,
                        Statistics=['Average']
                    )
                    
                    datapoints = response.get('Datapoints', [])
                    if datapoints:
                        latest_value = max(datapoints, key=lambda x: x['Timestamp'])['Average']
                        metric_values[metric_name] = latest_value
                    else:
                        metric_values[metric_name] = None
                        
                except ClientError:
                    metric_values[metric_name] = None
            
            # Determine health based on metrics
            status = 'HEALTHY'
            
            if metric_values.get('SystemAvailability') is not None:
                if metric_values['SystemAvailability'] < 99.0:
                    status = 'DEGRADED'
            
            if metric_values.get('ErrorRate') is not None:
                if metric_values['ErrorRate'] > 5.0:
                    status = 'UNHEALTHY'
            
            return {
                'status': status,
                'metrics': metric_values,
                'period_minutes': 5
            }
            
        except ClientError as e:
            return {
                'status': 'ERROR',
                'error': str(e)
            }
    
    def check_alarms(self) -> Dict[str, Any]:
        """Check CloudWatch alarm status."""
        try:
            # Get alarms for this environment
            response = self.cloudwatch.describe_alarms(
                AlarmNamePrefix=f"IncidentCommander-",
                StateValue='ALARM'
            )
            
            active_alarms = response.get('MetricAlarms', [])
            
            # Filter for this environment
            env_alarms = [
                alarm for alarm in active_alarms
                if f"-{self.environment}" in alarm['AlarmName']
            ]
            
            return {
                'status': 'HEALTHY' if len(env_alarms) == 0 else 'ALARMING',
                'active_alarms': len(env_alarms),
                'alarm_names': [alarm['AlarmName'] for alarm in env_alarms]
            }
            
        except ClientError as e:
            return {
                'status': 'ERROR',
                'error': str(e)
            }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        
        # Check all components
        self.status['components']['dynamodb'] = self.check_dynamodb_health()
        self.status['components']['api_gateway'] = self.check_api_health()
        self.status['components']['metrics'] = self.check_cloudwatch_metrics()
        self.status['components']['alarms'] = self.check_alarms()
        
        # Determine overall status
        component_statuses = [
            comp.get('status', 'UNKNOWN') 
            for comp in self.status['components'].values()
        ]
        
        if all(status == 'HEALTHY' for status in component_statuses):
            overall_status = 'HEALTHY'
        elif any(status in ['ERROR', 'UNHEALTHY'] for status in component_statuses):
            overall_status = 'UNHEALTHY'
        elif any(status in ['DEGRADED', 'ALARMING'] for status in component_statuses):
            overall_status = 'DEGRADED'
        else:
            overall_status = 'UNKNOWN'
        
        self.status['overall_status'] = overall_status
        
        return self.status
    
    def print_status_report(self, status: Dict[str, Any]):
        """Print human-readable status report."""
        
        # Status emoji mapping
        status_emojis = {
            'HEALTHY': '🟢',
            'DEGRADED': '🟡',
            'UNHEALTHY': '🔴',
            'ERROR': '❌',
            'UNKNOWN': '⚪',
            'NOT_FOUND': '❓',
            'UNREACHABLE': '🔌',
            'ALARMING': '🚨'
        }
        
        overall_emoji = status_emojis.get(status['overall_status'], '⚪')
        
        print(f"\n{overall_emoji} INCIDENT COMMANDER SYSTEM STATUS")
        print(f"{'='*50}")
        print(f"Environment: {status['environment']}")
        print(f"Region: {status['region']}")
        print(f"Timestamp: {status['timestamp']}")
        print(f"Overall Status: {status['overall_status']}")
        print()
        
        # Component details
        for component, details in status['components'].items():
            comp_emoji = status_emojis.get(details.get('status', 'UNKNOWN'), '⚪')
            comp_status = details.get('status', 'UNKNOWN')
            
            print(f"{comp_emoji} {component.upper().replace('_', ' ')}: {comp_status}")
            
            # Component-specific details
            if component == 'dynamodb':
                if 'item_count' in details:
                    print(f"   Items: {details['item_count']:,}")
                if 'size_bytes' in details:
                    size_mb = details['size_bytes'] / (1024 * 1024)
                    print(f"   Size: {size_mb:.1f} MB")
            
            elif component == 'api_gateway':
                if 'endpoint' in details:
                    print(f"   Endpoint: {details['endpoint']}")
                if 'response_time_ms' in details:
                    print(f"   Response Time: {details['response_time_ms']}ms")
            
            elif component == 'metrics':
                if 'metrics' in details:
                    for metric, value in details['metrics'].items():
                        if value is not None:
                            if metric == 'SystemAvailability':
                                print(f"   {metric}: {value:.2f}%")
                            elif metric == 'ErrorRate':
                                print(f"   {metric}: {value:.2f}%")
                            elif metric == 'APILatency':
                                print(f"   {metric}: {value:.1f}ms")
            
            elif component == 'alarms':
                if 'active_alarms' in details:
                    print(f"   Active Alarms: {details['active_alarms']}")
                    if details.get('alarm_names'):
                        for alarm in details['alarm_names']:
                            print(f"     - {alarm}")
            
            # Show errors
            if 'error' in details:
                print(f"   Error: {details['error']}")
            
            print()
        
        # Summary
        if status['overall_status'] == 'HEALTHY':
            print("✅ System is operating normally")
        elif status['overall_status'] == 'DEGRADED':
            print("⚠️  System is experiencing minor issues")
        elif status['overall_status'] == 'UNHEALTHY':
            print("🚨 System requires immediate attention")
        else:
            print("❓ System status could not be determined")


def main():
    """Main status check entry point."""
    parser = argparse.ArgumentParser(description='Check Incident Commander system status')
    parser.add_argument('--environment', '-e', default='production',
                       choices=['development', 'staging', 'production'],
                       help='Environment to check')
    parser.add_argument('--region', '-r', default='us-east-1',
                       help='AWS region')
    parser.add_argument('--json', action='store_true',
                       help='Output results in JSON format')
    
    args = parser.parse_args()
    
    # Initialize status checker
    checker = SystemStatusChecker(args.environment, args.region)
    
    # Get system status
    status = checker.get_system_status()
    
    # Output results
    if args.json:
        print(json.dumps(status, indent=2))
    else:
        checker.print_status_report(status)
    
    # Exit with appropriate code
    if status['overall_status'] == 'HEALTHY':
        sys.exit(0)
    elif status['overall_status'] == 'DEGRADED':
        sys.exit(1)
    else:
        sys.exit(2)


if __name__ == '__main__':
    main()