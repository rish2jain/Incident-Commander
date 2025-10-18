"""
Detection Agent Lambda Function for Incident Commander
"""

import json
import os
import uuid
from datetime import datetime
from decimal import Decimal
import boto3
import sys

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
try:
    from src.utils.dynamodb_helpers import prepare_item_for_dynamodb
except ImportError:
    # Fallback if utils not available
    def prepare_item_for_dynamodb(item):
        return item


def handler(event, context):
    """Lambda handler for incident detection and triggering."""
    
    try:
        # Parse the request body
        if 'body' in event:
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        else:
            body = event
        
        # Create incident
        incident = create_incident(body)
        
        # Store in DynamoDB (if available)
        try:
            store_incident(incident)
        except Exception as e:
            print(f"Warning: Could not store incident in DynamoDB: {e}")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'incident_id': incident['incident_id'],
                'status': 'created',
                'message': 'Incident detection initiated',
                'incident': incident
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': str(e),
                'message': 'Failed to process incident'
            })
        }


def create_incident(body):
    """Create an incident from the request body."""
    
    incident_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat()
    
    incident = {
        'incident_id': incident_id,
        'timestamp': timestamp,
        'incident_type': body.get('incident_type', 'unknown'),
        'severity': body.get('severity', 'medium'),
        'description': body.get('description', 'No description provided'),
        'source': body.get('source', 'api'),
        'status': 'detected',
        'agent_actions': [
            {
                'agent': 'detection',
                'action': 'incident_created',
                'timestamp': timestamp,
                'confidence': 0.9
            }
        ]
    }
    
    return incident


def store_incident(incident):
    """Store incident in DynamoDB."""
    
    dynamodb_table = os.getenv('DYNAMODB_TABLE')
    if not dynamodb_table:
        raise Exception("DYNAMODB_TABLE environment variable not set")
    
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(dynamodb_table)
    
    # Convert floats to Decimal for DynamoDB compatibility
    prepared_incident = prepare_item_for_dynamodb(incident)
    
    # Store the incident
    table.put_item(Item=prepared_incident)
    
    print(f"Stored incident {incident['incident_id']} in DynamoDB")