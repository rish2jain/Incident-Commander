"""
Dashboard Stack for Incident Commander - CloudFront with S3 Origin
Bypasses S3 public access restrictions using Origin Access Control (OAC)
"""

from aws_cdk import (
    Stack,
    RemovalPolicy,
    Duration,
    aws_s3 as s3,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_s3_deployment as s3_deploy,
    aws_kms as kms,
    aws_iam as iam,
    CfnOutput
)
from constructs import Construct


class IncidentCommanderDashboardStack(Stack):
    """Dashboard infrastructure stack with CloudFront CDN."""

    def __init__(self, scope: Construct, construct_id: str,
                 environment_name: str, env_config: dict,
                 kms_key: kms.Key = None, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create S3 bucket for dashboard static files
        # Note: Block all public access - CloudFront will access via OAC
        self.dashboard_bucket = s3.Bucket(
            self, "DashboardBucket",
            bucket_name=f"incident-commander-dashboard-{environment_name}",
            encryption=s3.BucketEncryption.S3_MANAGED,  # Use S3-managed for CloudFront compatibility
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,  # Blocks public access
            versioned=True,
            removal_policy=RemovalPolicy.DESTROY if environment_name != "production" else RemovalPolicy.RETAIN,
            auto_delete_objects=True if environment_name != "production" else False,
        )

        # Create CloudFront Origin Access Control (OAC)
        # This is the modern replacement for OAI and works with account-level public access blocks
        cfn_origin_access_control = cloudfront.CfnOriginAccessControl(
            self, "DashboardOAC",
            origin_access_control_config=cloudfront.CfnOriginAccessControl.OriginAccessControlConfigProperty(
                name=f"incident-commander-dashboard-oac-{environment_name}",
                origin_access_control_origin_type="s3",
                signing_behavior="always",
                signing_protocol="sigv4",
                description="Origin Access Control for Incident Commander Dashboard"
            )
        )

        # Create CloudFront distribution with custom cache policy
        cache_policy = cloudfront.CachePolicy(
            self, "DashboardCachePolicy",
            cache_policy_name=f"IncidentCommanderDashboard-{environment_name}",
            comment="Cache policy for Incident Commander dashboard",
            default_ttl=Duration.hours(24),
            min_ttl=Duration.minutes(1),
            max_ttl=Duration.days(365),
            cookie_behavior=cloudfront.CacheCookieBehavior.none(),
            header_behavior=cloudfront.CacheHeaderBehavior.none(),
            query_string_behavior=cloudfront.CacheQueryStringBehavior.none(),
            enable_accept_encoding_gzip=True,
            enable_accept_encoding_brotli=True,
        )

        # Create CloudFront distribution
        self.distribution = cloudfront.Distribution(
            self, "DashboardDistribution",
            comment=f"Incident Commander Dashboard - {environment_name}",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3Origin(self.dashboard_bucket),
                cache_policy=cache_policy,
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                allowed_methods=cloudfront.AllowedMethods.ALLOW_GET_HEAD_OPTIONS,
                compress=True,
            ),
            default_root_object="index.html",
            error_responses=[
                cloudfront.ErrorResponse(
                    http_status=403,
                    response_http_status=200,
                    response_page_path="/index.html",
                    ttl=Duration.minutes(5)
                ),
                cloudfront.ErrorResponse(
                    http_status=404,
                    response_http_status=200,
                    response_page_path="/index.html",
                    ttl=Duration.minutes(5)
                )
            ],
            price_class=cloudfront.PriceClass.PRICE_CLASS_100,  # Use only North America and Europe
            enabled=True,
        )

        # Get the CloudFront distribution's L1 construct to modify OAC
        cfn_distribution = self.distribution.node.default_child

        # Update the S3 origin to use OAC instead of OAI
        cfn_distribution.add_property_override(
            "DistributionConfig.Origins.0.OriginAccessControlId",
            cfn_origin_access_control.attr_id
        )

        # Remove the OAI that CDK automatically adds
        cfn_distribution.add_property_override(
            "DistributionConfig.Origins.0.S3OriginConfig.OriginAccessIdentity",
            ""
        )

        # Grant CloudFront OAC read access to the S3 bucket
        self.dashboard_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                actions=["s3:GetObject"],
                resources=[f"{self.dashboard_bucket.bucket_arn}/*"],
                principals=[iam.ServicePrincipal("cloudfront.amazonaws.com")],
                conditions={
                    "StringEquals": {
                        "AWS:SourceArn": f"arn:aws:cloudfront::{self.account}:distribution/{self.distribution.distribution_id}"
                    }
                }
            )
        )

        # Output the CloudFront distribution URL
        CfnOutput(
            self, "DashboardURL",
            value=f"https://{self.distribution.distribution_domain_name}",
            description="CloudFront URL for Incident Commander Dashboard",
            export_name=f"IncidentCommanderDashboardURL-{environment_name}"
        )

        CfnOutput(
            self, "DashboardBucketName",
            value=self.dashboard_bucket.bucket_name,
            description="S3 bucket name for dashboard files",
            export_name=f"IncidentCommanderDashboardBucket-{environment_name}"
        )

        CfnOutput(
            self, "DistributionId",
            value=self.distribution.distribution_id,
            description="CloudFront distribution ID",
            export_name=f"IncidentCommanderDistributionId-{environment_name}"
        )
