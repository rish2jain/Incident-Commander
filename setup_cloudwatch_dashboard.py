#!/usr/bin/env python3
"""
CloudWatch Dashboard Setup for Incident Commander Hackathon
Creates comprehensive monitoring dashboards with widgets
"""

import boto3
import json
import os
import sys


def create_incident_commander_dashboard():
    """Create a comprehensive CloudWatch dashboard for Incident Commander."""
    
    cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')
    
    # Get model ID from environment or use default
    MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-5-sonnet-20241022-v2:0")
    
    # Dashboard configuration
    dashboard_body = {
        "widgets": [
            {
                "type": "metric",
                "x": 0,
                "y": 0,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["AWS/Lambda", "Duration", "FunctionName", "incident-commander-detection-agent-hackathon"],
                        [".", "Invocations", ".", "."],
                        [".", "Errors", ".", "."],
                        [".", "Throttles", ".", "."]
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": "us-east-1",
                    "title": "Detection Agent Lambda Metrics",
                    "period": 300,
                    "stat": "Average"
                }
            },
            {
                "type": "metric",
                "x": 12,
                "y": 0,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["AWS/Lambda", "Duration", "FunctionName", "incident-commander-health-hackathon"],
                        [".", "Invocations", ".", "."],
                        [".", "Errors", ".", "."]
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": "us-east-1",
                    "title": "Health Check Lambda Metrics",
                    "period": 300,
                    "stat": "Average"
                }
            },
            {
                "type": "metric",
                "x": 0,
                "y": 6,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["AWS/ApiGateway", "Count", "ApiName", "incident-commander-hackathon"],
                        [".", "Latency", ".", "."],
                        [".", "4XXError", ".", "."],
                        [".", "5XXError", ".", "."]
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": "us-east-1",
                    "title": "API Gateway Metrics",
                    "period": 300,
                    "stat": "Sum"
                }
            },
            {
                "type": "metric",
                "x": 12,
                "y": 6,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["AWS/ECS", "CPUUtilization", "ServiceName", "incident-commander-service", "ClusterName", "incident-commander-hackathon"],
                        [".", "MemoryUtilization", ".", ".", ".", "."]
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": "us-east-1",
                    "title": "ECS Service Metrics",
                    "period": 300,
                    "stat": "Average"
                }
            },
            {
                "type": "log",
                "x": 0,
                "y": 12,
                "width": 24,
                "height": 6,
                "properties": {
                    "query": "SOURCE '/aws/lambda/incident-commander-detection-agent-hackathon'\n| fields @timestamp, @message\n| filter @message like /incident/\n| sort @timestamp desc\n| limit 20",
                    "region": "us-east-1",
                    "title": "Recent Incident Logs",
                    "view": "table"
                }
            },
            {
                "type": "metric",
                "x": 0,
                "y": 18,
                "width": 8,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["AWS/DynamoDB", "ConsumedReadCapacityUnits", "TableName", "incident-commander-events-hackathon"],
                        [".", "ConsumedWriteCapacityUnits", ".", "."]
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": "us-east-1",
                    "title": "DynamoDB Capacity",
                    "period": 300,
                    "stat": "Sum"
                }
            },
            {
                "type": "metric",
                "x": 8,
                "y": 18,
                "width": 8,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["AWS/S3", "BucketSizeBytes", "BucketName", "incident-commander-artifacts-hackathon", "StorageType", "StandardStorage"],
                        [".", "NumberOfObjects", ".", ".", ".", "AllStorageTypes"]
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": "us-east-1",
                    "title": "S3 Storage Metrics",
                    "period": 86400,
                    "stat": "Average"
                }
            },
            {
                "type": "metric",
                "x": 16,
                "y": 18,
                "width": 8,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["AWS/Bedrock", "Invocations", "ModelId", MODEL_ID],
                        [".", "InputTokens", ".", "."],
                        [".", "OutputTokens", ".", "."]
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": "us-east-1",
                    "title": "Bedrock Model Usage",
                    "period": 300,
                    "stat": "Sum"
                }
            }
        ]
    }
    
    try:
        response = cloudwatch.put_dashboard(
            DashboardName='IncidentCommanderHackathon',
            DashboardBody=json.dumps(dashboard_body)
        )
        
        print("✅ CloudWatch Dashboard created successfully!")
        print(f"Dashboard URL: https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=IncidentCommanderHackathon")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create dashboard: {e}")
        return False


def create_custom_metrics():
    """Create custom metrics for incident tracking."""
    
    cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')
    
    try:
        # Put sample custom metrics
        cloudwatch.put_metric_data(
            Namespace='IncidentCommander/Hackathon',
            MetricData=[
                {
                    'MetricName': 'IncidentsDetected',
                    'Value': 0,
                    'Unit': 'Count',
                    'Dimensions': [
                        {
                            'Name': 'Environment',
                            'Value': 'hackathon'
                        }
                    ]
                },
                {
                    'MetricName': 'IncidentsResolved',
                    'Value': 0,
                    'Unit': 'Count',
                    'Dimensions': [
                        {
                            'Name': 'Environment',
                            'Value': 'hackathon'
                        }
                    ]
                },
                {
                    'MetricName': 'MeanTimeToResolution',
                    'Value': 0,
                    'Unit': 'Seconds',
                    'Dimensions': [
                        {
                            'Name': 'Environment',
                            'Value': 'hackathon'
                        }
                    ]
                }
            ]
        )
        
        print("✅ Custom metrics initialized!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create custom metrics: {e}")
        return False


def create_alarms():
    """Create CloudWatch alarms for monitoring."""
    
    cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')
    
    alarms = [
        {
            'AlarmName': 'IncidentCommander-HighErrorRate',
            'ComparisonOperator': 'GreaterThanThreshold',
            'EvaluationPeriods': 2,
            'MetricName': 'Errors',
            'Namespace': 'AWS/Lambda',
            'Period': 300,
            'Statistic': 'Sum',
            'Threshold': 5.0,
            'ActionsEnabled': True,
            'AlarmDescription': 'High error rate in Incident Commander Lambda functions',
            'Dimensions': [
                {
                    'Name': 'FunctionName',
                    'Value': 'incident-commander-detection-agent-hackathon'
                }
            ],
            'Unit': 'Count'
        },
        {
            'AlarmName': 'IncidentCommander-HighLatency',
            'ComparisonOperator': 'GreaterThanThreshold',
            'EvaluationPeriods': 2,
            'MetricName': 'Duration',
            'Namespace': 'AWS/Lambda',
            'Period': 300,
            'Statistic': 'Average',
            'Threshold': 30000.0,  # 30 seconds
            'ActionsEnabled': True,
            'AlarmDescription': 'High latency in Incident Commander Lambda functions',
            'Dimensions': [
                {
                    'Name': 'FunctionName',
                    'Value': 'incident-commander-detection-agent-hackathon'
                }
            ],
            'Unit': 'Milliseconds'
        }
    ]
    
    try:
        for alarm in alarms:
            cloudwatch.put_metric_alarm(**alarm)
            print(f"✅ Created alarm: {alarm['AlarmName']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to create alarms: {e}")
        return False


def main():
    """Main setup function."""
    print("🚀 Setting up CloudWatch Dashboard for Incident Commander")
    print("=" * 60)
    
    # Create dashboard
    print("\n📊 Creating CloudWatch Dashboard...")
    if create_incident_commander_dashboard():
        print("Dashboard created with comprehensive monitoring widgets")
    
    # Create custom metrics
    print("\n📈 Initializing Custom Metrics...")
    if create_custom_metrics():
        print("Custom metrics for incident tracking initialized")
    
    # Create alarms
    print("\n🚨 Setting up CloudWatch Alarms...")
    if create_alarms():
        print("Monitoring alarms configured")
    
    print("\n✅ CloudWatch setup complete!")
    print("\nAccess your dashboard at:")
    print("https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=IncidentCommanderHackathon")
    
    print("\n📋 Dashboard includes:")
    print("- Lambda function metrics (duration, invocations, errors)")
    print("- API Gateway performance metrics")
    print("- ECS service resource utilization")
    print("- DynamoDB capacity metrics")
    print("- S3 storage metrics")
    print("- Bedrock model usage")
    print("- Recent incident logs")
    print("- Custom incident tracking metrics")


if __name__ == "__main__":
    main()