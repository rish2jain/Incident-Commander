"""
Storage Stack for Incident Commander
"""

from aws_cdk import (
    Stack,
    aws_dynamodb as dynamodb,
    aws_s3 as s3,
    aws_kms as kms,
    aws_ec2 as ec2,
    RemovalPolicy
)
from constructs import Construct


class IncidentCommanderStorageStack(Stack):
    """Storage infrastructure stack."""

    def __init__(self, scope: Construct, construct_id: str, 
                 environment_name: str, env_config: dict, 
                 vpc: ec2.Vpc, kms_key: kms.Key, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create DynamoDB tables
        self.dynamodb_tables = {}
        
        self.dynamodb_tables['events'] = dynamodb.Table(
            self, "IncidentEvents",
            table_name=f"incident-commander-events-{environment_name}",
            partition_key=dynamodb.Attribute(
                name="incident_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=kms_key,
            removal_policy=RemovalPolicy.RETAIN if environment_name == "production" else RemovalPolicy.DESTROY
        )

        # Create S3 buckets
        self.s3_buckets = {}
        
        self.s3_buckets['artifacts'] = s3.Bucket(
            self, "IncidentArtifacts",
            bucket_name=f"incident-commander-artifacts-{environment_name}",
            encryption=s3.BucketEncryption.KMS,
            encryption_key=kms_key,
            removal_policy=RemovalPolicy.RETAIN if environment_name == "production" else RemovalPolicy.DESTROY
        )