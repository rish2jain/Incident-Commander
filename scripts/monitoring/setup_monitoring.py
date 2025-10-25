#!/usr/bin/env python3
"""
Monitoring and Logging Setup for Incident Commander

This script configures comprehensive monitoring including:
- CloudWatch dashboards and alarms
- Log groups and retention policies
- Custom metrics and KPIs
- Performance monitoring
- Security monitoring
- Business impact tracking

Usage:
    python setup_monitoring.py --environment production
    python setup_monitoring.py --environment staging --enable-detailed-monitoring
"""

import os
import sys
import json
import boto3
import argparse
from typing import Dict, List, Any
from datetime import datetime, timedelta
from botocore.exceptions import ClientError


class MonitoringSetup:
    """Comprehensive monitoring setup for Incident Commander."""
    
    def __init__(self, environment: str = "production", region: str = "us-east-1"):
        self.environment = environment
        self.region = region
        
        # Initialize AWS clients
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        self.logs = boto3.client('logs', region_name=region)
        self.sns = boto3.client('sns', region_name=region)
        self.lambda_client = boto3.client('lambda', region_name=region)
        
        # Monitoring configuration
        self.namespace = f"IncidentCommander/{environment}"
        self.log_retention_days = 90 if environment == "production" else 30
        
    def create_log_groups(self) -> Dict[str, str]:
        """Create CloudWatch log groups for all components."""
        print("📝 Creating CloudWatch log groups...")
        
        log_groups = {
            'api-gateway': f'/aws/apigateway/incident-commander-{self.environment}',
            'detection-agent': f'/aws/lambda/incident-commander-detection-{self.environment}',
            'diagnosis-agent': f'/aws/lambda/incident-commander-diagnosis-{self.environment}',
            'prediction-agent': f'/aws/lambda/incident-commander-prediction-{self.environment}',
            'resolution-agent': f'/aws/lambda/incident-commander-resolution-{self.environment}',
            'communication-agent': f'/aws/lambda/incident-commander-communication-{self.environment}',
            'orchestrator': f'/incident-commander/{self.environment}/orchestrator',
            'consensus-engine': f'/incident-commander/{self.environment}/consensus',
            'business-impact': f'/incident-commander/{self.environment}/business-impact',
            'security-audit': f'/incident-commander/{self.environment}/security',
            'performance': f'/incident-commander/{self.environment}/performance'
        }
        
        created_groups = {}
        
        for group_name, log_group_name in log_groups.items():
            try:
                # Check if log group exists
                self.logs.describe_log_groups(logGroupNamePrefix=log_group_name)
                print(f"  ✅ Log group {log_group_name} already exists")
                created_groups[group_name] = log_group_name
                continue
                
            except ClientError as e:
                if e.response['Error']['Code'] != 'ResourceNotFoundException':
                    raise
            
            try:
                # Create log group
                self.logs.create_log_group(
                    logGroupName=log_group_name,
                    tags={
                        'Project': 'IncidentCommander',
                        'Environment': self.environment,
                        'Component': group_name
                    }
                )
                
                # Set retention policy
                self.logs.put_retention_policy(
                    logGroupName=log_group_name,
                    retentionInDays=self.log_retention_days
                )
                
                print(f"  ✅ Created log group {log_group_name}")
                created_groups[group_name] = log_group_name
                
            except ClientError as e:
                print(f"  ❌ Failed to create log group {log_group_name}: {e}")
        
        return created_groups
    
    def create_custom_metrics(self) -> List[str]:
        """Create custom CloudWatch metrics for business KPIs."""
        print("📊 Setting up custom metrics...")
        
        metrics = [
            # Incident Response Metrics
            'IncidentDetectionTime',
            'IncidentDiagnosisTime', 
            'IncidentResolutionTime',
            'MeanTimeToResolution',
            'IncidentCount',
            'IncidentSeverityDistribution',
            
            # Agent Performance Metrics
            'AgentResponseTime',
            'AgentAccuracy',
            'ConsensusTime',
            'ConflictResolutionTime',
            'AgentAvailability',
            
            # Business Impact Metrics
            'CostSavings',
            'PreventedIncidents',
            'BusinessImpactScore',
            'CustomerImpactMinutes',
            'RevenueProtected',
            
            # System Health Metrics
            'SystemAvailability',
            'APILatency',
            'DatabasePerformance',
            'ErrorRate',
            'ThroughputRPS'
        ]
        
        # Publish initial metric values to establish metrics
        for metric_name in metrics:
            try:
                self.cloudwatch.put_metric_data(
                    Namespace=self.namespace,
                    MetricData=[
                        {
                            'MetricName': metric_name,
                            'Value': 0.0,
                            'Unit': 'Count',
                            'Timestamp': datetime.utcnow()
                        }
                    ]
                )
            except ClientError as e:
                print(f"  ❌ Failed to create metric {metric_name}: {e}")
        
        print(f"  ✅ Created {len(metrics)} custom metrics")
        return metrics
    
    def create_dashboards(self) -> Dict[str, str]:
        """Create comprehensive CloudWatch dashboards."""
        print("📈 Creating CloudWatch dashboards...")
        
        dashboards = {
            'executive': self._create_executive_dashboard(),
            'operational': self._create_operational_dashboard(),
            'technical': self._create_technical_dashboard(),
            'security': self._create_security_dashboard()
        }
        
        created_dashboards = {}
        
        for dashboard_type, dashboard_config in dashboards.items():
            dashboard_name = f"IncidentCommander-{dashboard_type.title()}-{self.environment}"
            
            try:
                self.cloudwatch.put_dashboard(
                    DashboardName=dashboard_name,
                    DashboardBody=json.dumps(dashboard_config)
                )
                
                dashboard_url = (
                    f"https://{self.region}.console.aws.amazon.com/cloudwatch/home"
                    f"?region={self.region}#dashboards:name={dashboard_name}"
                )
                
                print(f"  ✅ Created {dashboard_type} dashboard: {dashboard_name}")
                created_dashboards[dashboard_type] = dashboard_url
                
            except ClientError as e:
                print(f"  ❌ Failed to create {dashboard_type} dashboard: {e}")
        
        return created_dashboards
    
    def _create_executive_dashboard(self) -> Dict[str, Any]:
        """Create executive-level dashboard with business metrics."""
        return {
            "widgets": [
                {
                    "type": "metric",
                    "x": 0, "y": 0, "width": 12, "height": 6,
                    "properties": {
                        "metrics": [
                            [self.namespace, "MeanTimeToResolution"],
                            [self.namespace, "IncidentCount"],
                            [self.namespace, "PreventedIncidents"]
                        ],
                        "period": 3600,
                        "stat": "Average",
                        "region": self.region,
                        "title": "Incident Response Performance",
                        "yAxis": {"left": {"min": 0}}
                    }
                },
                {
                    "type": "metric",
                    "x": 12, "y": 0, "width": 12, "height": 6,
                    "properties": {
                        "metrics": [
                            [self.namespace, "CostSavings"],
                            [self.namespace, "RevenueProtected"],
                            [self.namespace, "BusinessImpactScore"]
                        ],
                        "period": 3600,
                        "stat": "Sum",
                        "region": self.region,
                        "title": "Business Impact & ROI",
                        "yAxis": {"left": {"min": 0}}
                    }
                },
                {
                    "type": "number",
                    "x": 0, "y": 6, "width": 6, "height": 3,
                    "properties": {
                        "metrics": [
                            [self.namespace, "SystemAvailability"]
                        ],
                        "period": 300,
                        "stat": "Average",
                        "region": self.region,
                        "title": "System Availability (%)"
                    }
                },
                {
                    "type": "number",
                    "x": 6, "y": 6, "width": 6, "height": 3,
                    "properties": {
                        "metrics": [
                            [self.namespace, "AgentAccuracy"]
                        ],
                        "period": 300,
                        "stat": "Average",
                        "region": self.region,
                        "title": "Agent Accuracy (%)"
                    }
                }
            ]
        }
    
    def _create_operational_dashboard(self) -> Dict[str, Any]:
        """Create operational dashboard for SRE teams."""
        return {
            "widgets": [
                {
                    "type": "metric",
                    "x": 0, "y": 0, "width": 8, "height": 6,
                    "properties": {
                        "metrics": [
                            [self.namespace, "IncidentDetectionTime"],
                            [self.namespace, "IncidentDiagnosisTime"],
                            [self.namespace, "IncidentResolutionTime"]
                        ],
                        "period": 300,
                        "stat": "Average",
                        "region": self.region,
                        "title": "Agent Response Times (seconds)"
                    }
                },
                {
                    "type": "metric",
                    "x": 8, "y": 0, "width": 8, "height": 6,
                    "properties": {
                        "metrics": [
                            ["AWS/Lambda", "Duration", "FunctionName", f"incident-commander-detection-{self.environment}"],
                            ["AWS/Lambda", "Duration", "FunctionName", f"incident-commander-diagnosis-{self.environment}"],
                            ["AWS/Lambda", "Duration", "FunctionName", f"incident-commander-resolution-{self.environment}"]
                        ],
                        "period": 300,
                        "stat": "Average",
                        "region": self.region,
                        "title": "Lambda Function Duration"
                    }
                },
                {
                    "type": "metric",
                    "x": 16, "y": 0, "width": 8, "height": 6,
                    "properties": {
                        "metrics": [
                            ["AWS/DynamoDB", "ConsumedReadCapacityUnits", "TableName", f"incident-commander-incident-events-{self.environment}"],
                            ["AWS/DynamoDB", "ConsumedWriteCapacityUnits", "TableName", f"incident-commander-incident-events-{self.environment}"]
                        ],
                        "period": 300,
                        "stat": "Sum",
                        "region": self.region,
                        "title": "DynamoDB Capacity Usage"
                    }
                }
            ]
        }
    
    def _create_technical_dashboard(self) -> Dict[str, Any]:
        """Create technical dashboard for developers."""
        return {
            "widgets": [
                {
                    "type": "log",
                    "x": 0, "y": 0, "width": 24, "height": 6,
                    "properties": {
                        "query": f"SOURCE '/incident-commander/{self.environment}/orchestrator'\n| fields @timestamp, @message\n| filter @message like /ERROR/\n| sort @timestamp desc\n| limit 100",
                        "region": self.region,
                        "title": "Recent Errors",
                        "view": "table"
                    }
                },
                {
                    "type": "metric",
                    "x": 0, "y": 6, "width": 12, "height": 6,
                    "properties": {
                        "metrics": [
                            [self.namespace, "ConsensusTime"],
                            [self.namespace, "ConflictResolutionTime"]
                        ],
                        "period": 300,
                        "stat": "Average",
                        "region": self.region,
                        "title": "Consensus Engine Performance"
                    }
                },
                {
                    "type": "metric",
                    "x": 12, "y": 6, "width": 12, "height": 6,
                    "properties": {
                        "metrics": [
                            [self.namespace, "APILatency"],
                            [self.namespace, "ErrorRate"],
                            [self.namespace, "ThroughputRPS"]
                        ],
                        "period": 300,
                        "stat": "Average",
                        "region": self.region,
                        "title": "API Performance Metrics"
                    }
                }
            ]
        }
    
    def _create_security_dashboard(self) -> Dict[str, Any]:
        """Create security monitoring dashboard."""
        return {
            "widgets": [
                {
                    "type": "log",
                    "x": 0, "y": 0, "width": 24, "height": 6,
                    "properties": {
                        "query": f"SOURCE '/incident-commander/{self.environment}/security'\n| fields @timestamp, event_type, agent_id, details\n| filter event_type = \"security_violation\"\n| sort @timestamp desc\n| limit 50",
                        "region": self.region,
                        "title": "Security Violations",
                        "view": "table"
                    }
                },
                {
                    "type": "log",
                    "x": 0, "y": 6, "width": 12, "height": 6,
                    "properties": {
                        "query": f"SOURCE '/incident-commander/{self.environment}/security'\n| fields @timestamp, agent_id\n| filter @message like /authentication_failed/\n| stats count() by agent_id\n| sort count desc",
                        "region": self.region,
                        "title": "Failed Authentication by Agent",
                        "view": "table"
                    }
                },
                {
                    "type": "log",
                    "x": 12, "y": 6, "width": 12, "height": 6,
                    "properties": {
                        "query": f"SOURCE '/incident-commander/{self.environment}/security'\n| fields @timestamp, @message\n| filter @message like /privilege_escalation/\n| sort @timestamp desc\n| limit 20",
                        "region": self.region,
                        "title": "Privilege Escalation Attempts",
                        "view": "table"
                    }
                }
            ]
        }
    
    def create_alarms(self) -> Dict[str, str]:
        """Create CloudWatch alarms for critical metrics."""
        print("🚨 Creating CloudWatch alarms...")
        
        alarms = {
            'high-mttr': {
                'AlarmName': f'IncidentCommander-HighMTTR-{self.environment}',
                'AlarmDescription': 'Mean Time To Resolution is too high',
                'MetricName': 'MeanTimeToResolution',
                'Threshold': 300.0,  # 5 minutes
                'ComparisonOperator': 'GreaterThanThreshold',
                'EvaluationPeriods': 2,
                'Period': 300,
                'Statistic': 'Average'
            },
            'low-availability': {
                'AlarmName': f'IncidentCommander-LowAvailability-{self.environment}',
                'AlarmDescription': 'System availability is below threshold',
                'MetricName': 'SystemAvailability',
                'Threshold': 99.0,  # 99%
                'ComparisonOperator': 'LessThanThreshold',
                'EvaluationPeriods': 1,
                'Period': 300,
                'Statistic': 'Average'
            },
            'high-error-rate': {
                'AlarmName': f'IncidentCommander-HighErrorRate-{self.environment}',
                'AlarmDescription': 'Error rate is too high',
                'MetricName': 'ErrorRate',
                'Threshold': 5.0,  # 5%
                'ComparisonOperator': 'GreaterThanThreshold',
                'EvaluationPeriods': 2,
                'Period': 300,
                'Statistic': 'Average'
            },
            'agent-consensus-failure': {
                'AlarmName': f'IncidentCommander-ConsensusFailure-{self.environment}',
                'AlarmDescription': 'Agent consensus is taking too long',
                'MetricName': 'ConsensusTime',
                'Threshold': 60.0,  # 1 minute
                'ComparisonOperator': 'GreaterThanThreshold',
                'EvaluationPeriods': 1,
                'Period': 300,
                'Statistic': 'Average'
            }
        }
        
        created_alarms = {}
        
        for alarm_key, alarm_config in alarms.items():
            try:
                self.cloudwatch.put_metric_alarm(
                    AlarmName=alarm_config['AlarmName'],
                    AlarmDescription=alarm_config['AlarmDescription'],
                    MetricName=alarm_config['MetricName'],
                    Namespace=self.namespace,
                    Statistic=alarm_config['Statistic'],
                    Period=alarm_config['Period'],
                    EvaluationPeriods=alarm_config['EvaluationPeriods'],
                    Threshold=alarm_config['Threshold'],
                    ComparisonOperator=alarm_config['ComparisonOperator'],
                    TreatMissingData='notBreaching',
                    Tags=[
                        {'Key': 'Project', 'Value': 'IncidentCommander'},
                        {'Key': 'Environment', 'Value': self.environment}
                    ]
                )
                
                print(f"  ✅ Created alarm: {alarm_config['AlarmName']}")
                created_alarms[alarm_key] = alarm_config['AlarmName']
                
            except ClientError as e:
                print(f"  ❌ Failed to create alarm {alarm_config['AlarmName']}: {e}")
        
        return created_alarms
    
    def setup_log_insights_queries(self) -> Dict[str, str]:
        """Create saved CloudWatch Logs Insights queries."""
        print("🔍 Setting up Log Insights queries...")
        
        queries = {
            'incident-timeline': {
                'name': f'IncidentCommander-IncidentTimeline-{self.environment}',
                'query': '''
                fields @timestamp, incident_id, event_type, agent_id, @message
                | filter incident_id like /incident-/
                | sort @timestamp asc
                | limit 1000
                '''
            },
            'agent-performance': {
                'name': f'IncidentCommander-AgentPerformance-{self.environment}',
                'query': '''
                fields @timestamp, agent_id, duration, confidence_score
                | filter @message like /agent_execution_complete/
                | stats avg(duration), avg(confidence_score) by agent_id
                | sort avg(duration) desc
                '''
            },
            'consensus-analysis': {
                'name': f'IncidentCommander-ConsensusAnalysis-{self.environment}',
                'query': '''
                fields @timestamp, consensus_decision, agent_votes, final_confidence
                | filter @message like /consensus_reached/
                | stats count() by consensus_decision
                | sort count desc
                '''
            },
            'error-analysis': {
                'name': f'IncidentCommander-ErrorAnalysis-{self.environment}',
                'query': '''
                fields @timestamp, @message, error_type, stack_trace
                | filter @level = "ERROR"
                | stats count() by error_type
                | sort count desc
                '''
            }
        }
        
        # Note: CloudWatch Logs Insights doesn't have an API to save queries
        # These would need to be created manually in the console
        print("  ⚠️  Log Insights queries need to be created manually in the console:")
        
        for query_key, query_config in queries.items():
            print(f"    - {query_config['name']}")
            print(f"      Query: {query_config['query'].strip()}")
        
        return {k: v['name'] for k, v in queries.items()}
    
    def setup_monitoring(self, enable_detailed: bool = False) -> Dict[str, Any]:
        """Set up complete monitoring infrastructure."""
        print(f"🔧 Setting up monitoring for environment: {self.environment}")
        
        results = {
            'environment': self.environment,
            'region': self.region,
            'timestamp': datetime.utcnow().isoformat(),
            'detailed_monitoring': enable_detailed
        }
        
        try:
            # Create log groups
            results['log_groups'] = self.create_log_groups()
            
            # Create custom metrics
            results['custom_metrics'] = self.create_custom_metrics()
            
            # Create dashboards
            results['dashboards'] = self.create_dashboards()
            
            # Create alarms
            results['alarms'] = self.create_alarms()
            
            # Setup log insights queries
            results['log_insights_queries'] = self.setup_log_insights_queries()
            
            print(f"\n🎉 Monitoring setup completed successfully!")
            print(f"   Log groups: {len(results['log_groups'])}")
            print(f"   Custom metrics: {len(results['custom_metrics'])}")
            print(f"   Dashboards: {len(results['dashboards'])}")
            print(f"   Alarms: {len(results['alarms'])}")
            
            # Save configuration
            config_file = f'monitoring-config-{self.environment}.json'
            with open(config_file, 'w') as f:
                json.dump(results, f, indent=2)
            
            print(f"   Configuration saved to: {config_file}")
            
            return results
            
        except Exception as e:
            print(f"\n❌ Monitoring setup failed: {e}")
            raise


def main():
    """Main monitoring setup entry point."""
    parser = argparse.ArgumentParser(description='Setup monitoring for Incident Commander')
    parser.add_argument('--environment', '-e', default='production',
                       choices=['development', 'staging', 'production'],
                       help='Environment to setup monitoring for')
    parser.add_argument('--region', '-r', default='us-east-1',
                       help='AWS region')
    parser.add_argument('--enable-detailed-monitoring', action='store_true',
                       help='Enable detailed monitoring with higher resolution')
    
    args = parser.parse_args()
    
    # Initialize monitoring setup
    monitor = MonitoringSetup(args.environment, args.region)
    
    # Setup monitoring
    results = monitor.setup_monitoring(args.enable_detailed_monitoring)
    
    print(f"\n📋 Next Steps:")
    print("1. Review created dashboards in CloudWatch console")
    print("2. Configure SNS topics for alarm notifications")
    print("3. Set up Log Insights queries manually")
    print("4. Test alarm thresholds with sample data")
    print("5. Configure external monitoring integrations (Datadog, etc.)")


if __name__ == '__main__':
    main()