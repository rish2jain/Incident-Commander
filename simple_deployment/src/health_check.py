"""
Health Check Lambda Function for Incident Commander
"""

import json
import os
from datetime import datetime, timezone


def handler(event, context):
    """Lambda handler for health checks and demo endpoints."""
    
    # Get the HTTP method and path
    http_method = event.get('httpMethod', 'GET')
    path = event.get('path', '/health')
    
    if path == '/health':
        return health_check()
    elif path == '/demo/status':
        return demo_status()
    elif path == '/demo/scenarios':
        return demo_scenarios()
    else:
        return {
            'statusCode': 404,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'Not found'})
        }


def health_check():
    """Return health status."""
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'status': 'healthy',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'environment': os.getenv('ENVIRONMENT', 'development'),
            'service': 'incident-commander',
            'version': '1.0.0'
        })
    }


def demo_status():
    """Return demo system status."""
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'demo_mode': True,
            'status': 'ready',
            'agents': {
                'detection': 'active',
                'diagnosis': 'active',
                'prediction': 'active',
                'resolution': 'active',
                'communication': 'active'
            },
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
    }


def demo_scenarios():
    """Return available demo scenarios."""
    scenarios = [
        {
            'id': 'high_cpu_usage',
            'name': 'High CPU Usage',
            'description': 'CPU usage above 80% for 5 minutes',
            'severity': 'medium',
            'estimated_duration': '2-3 minutes'
        },
        {
            'id': 'database_connection_failure',
            'name': 'Database Connection Failure',
            'description': 'Database connection pool exhausted',
            'severity': 'high',
            'estimated_duration': '1-2 minutes'
        },
        {
            'id': 'memory_leak_detection',
            'name': 'Memory Leak Detection',
            'description': 'Memory usage increasing over time',
            'severity': 'medium',
            'estimated_duration': '3-4 minutes'
        },
        {
            'id': 'network_latency_spike',
            'name': 'Network Latency Spike',
            'description': 'Network latency above 500ms',
            'severity': 'low',
            'estimated_duration': '1-2 minutes'
        },
        {
            'id': 'disk_space_critical',
            'name': 'Disk Space Critical',
            'description': 'Disk usage above 95%',
            'severity': 'high',
            'estimated_duration': '2-3 minutes'
        }
    ]
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'scenarios': scenarios,
            'total_count': len(scenarios),
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
    }