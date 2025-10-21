#!/usr/bin/env python3
"""
Static AWS Deployment Script for AI Insights Dashboard
Deploys to S3 + CloudFront for global access by hackathon judges

Features:
- One-command deployment
- Custom domain support
- Global CDN distribution
- HTTPS by default
- Cost-effective (~$1-5/month)
"""

import boto3
import json
import os
import time
from pathlib import Path
import subprocess
import hashlib

class StaticAWSDeployer:
    def __init__(self):
        self.s3_client = boto3.client('s3')
        self.cloudfront_client = boto3.client('cloudfront')
        self.route53_client = boto3.client('route53')
        
        # Configuration
        self.bucket_name = f"ai-insights-dashboard-{self.generate_unique_suffix()}"
        self.distribution_id = None
        self.domain_name = None
        
    def generate_unique_suffix(self):
        """Generate unique suffix for bucket name"""
        import uuid
        return str(uuid.uuid4())[:8]
    
    def build_dashboard(self):
        """Build the Next.js dashboard for production"""
        print("🏗️ Building AI Insights Dashboard for production...")
        
        dashboard_dir = Path("dashboard")
        if not dashboard_dir.exists():
            raise Exception("Dashboard directory not found. Run from project root.")
        
        # Build Next.js app
        try:
            subprocess.run(["npm", "run", "build"], cwd=dashboard_dir, check=True)
            print("   ✅ Next.js build completed")
            
            # Export static files
            subprocess.run(["npm", "run", "export"], cwd=dashboard_dir, check=True)
            print("   ✅ Static export completed")
            
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Build failed: {e}")
            raise
    
    def create_s3_bucket(self):
        """Create S3 bucket for static hosting"""
        print(f"📦 Creating S3 bucket: {self.bucket_name}")
        
        try:
            # Create bucket
            self.s3_client.create_bucket(Bucket=self.bucket_name)
            print(f"   ✅ Bucket created: {self.bucket_name}")
            
            # Configure for static website hosting
            website_config = {
                'IndexDocument': {'Suffix': 'index.html'},
                'ErrorDocument': {'Key': 'error.html'}
            }
            
            self.s3_client.put_bucket_website(
                Bucket=self.bucket_name,
                WebsiteConfiguration=website_config
            )
            print("   ✅ Static website hosting configured")
            
            # Set bucket policy for public read
            bucket_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": "PublicReadGetObject",
                        "Effect": "Allow",
                        "Principal": "*",
                        "Action": "s3:GetObject",
                        "Resource": f"arn:aws:s3:::{self.bucket_name}/*"
                    }
                ]
            }
            
            self.s3_client.put_bucket_policy(
                Bucket=self.bucket_name,
                Policy=json.dumps(bucket_policy)
            )
            print("   ✅ Public read access configured")
            
        except Exception as e:
            print(f"   ❌ S3 setup failed: {e}")
            raise
    
    def upload_files(self):
        """Upload built files to S3"""
        print("📤 Uploading dashboard files to S3...")
        
        out_dir = Path("dashboard/out")
        if not out_dir.exists():
            raise Exception("Build output not found. Run build first.")
        
        uploaded_count = 0
        
        for file_path in out_dir.rglob("*"):
            if file_path.is_file():
                # Calculate S3 key (relative path)
                s3_key = str(file_path.relative_to(out_dir))
                
                # Determine content type
                content_type = self.get_content_type(file_path.suffix)
                
                # Upload file
                try:
                    self.s3_client.upload_file(
                        str(file_path),
                        self.bucket_name,
                        s3_key,
                        ExtraArgs={'ContentType': content_type}
                    )
                    uploaded_count += 1
                    
                except Exception as e:
                    print(f"   ⚠️ Failed to upload {s3_key}: {e}")
        
        print(f"   ✅ Uploaded {uploaded_count} files")
    
    def get_content_type(self, extension):
        """Get appropriate content type for file extension"""
        content_types = {
            '.html': 'text/html',
            '.css': 'text/css',
            '.js': 'application/javascript',
            '.json': 'application/json',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.svg': 'image/svg+xml',
            '.ico': 'image/x-icon',
            '.woff': 'font/woff',
            '.woff2': 'font/woff2',
            '.ttf': 'font/ttf',
            '.eot': 'application/vnd.ms-fontobject'
        }
        return content_types.get(extension.lower(), 'binary/octet-stream')
    
    def create_cloudfront_distribution(self):
        """Create CloudFront distribution for global CDN"""
        print("🌐 Creating CloudFront distribution...")
        
        distribution_config = {
            'CallerReference': f"ai-insights-{int(time.time())}",
            'Comment': 'AI Insights Dashboard - Hackathon Demo',
            'DefaultCacheBehavior': {
                'TargetOriginId': 'S3Origin',
                'ViewerProtocolPolicy': 'redirect-to-https',
                'TrustedSigners': {
                    'Enabled': False,
                    'Quantity': 0
                },
                'ForwardedValues': {
                    'QueryString': False,
                    'Cookies': {'Forward': 'none'}
                },
                'MinTTL': 0,
                'DefaultTTL': 86400,
                'MaxTTL': 31536000
            },
            'Origins': {
                'Quantity': 1,
                'Items': [
                    {
                        'Id': 'S3Origin',
                        'DomainName': f"{self.bucket_name}.s3-website-us-east-1.amazonaws.com",
                        'CustomOriginConfig': {
                            'HTTPPort': 80,
                            'HTTPSPort': 443,
                            'OriginProtocolPolicy': 'http-only'
                        }
                    }
                ]
            },
            'Enabled': True,
            'DefaultRootObject': 'insights-demo.html',
            'PriceClass': 'PriceClass_100'  # Use only US, Canada, Europe
        }
        
        try:
            response = self.cloudfront_client.create_distribution(
                DistributionConfig=distribution_config
            )
            
            self.distribution_id = response['Distribution']['Id']
            self.domain_name = response['Distribution']['DomainName']
            
            print(f"   ✅ CloudFront distribution created")
            print(f"   📍 Distribution ID: {self.distribution_id}")
            print(f"   🌐 Domain: {self.domain_name}")
            
        except Exception as e:
            print(f"   ❌ CloudFront creation failed: {e}")
            raise
    
    def wait_for_deployment(self, max_wait_seconds=900):  # 15 minutes
        """Wait for CloudFront deployment to complete"""
        print("⏳ Waiting for CloudFront deployment (this may take 10-15 minutes)...")
        
        start_time = time.time()
        
        while True:
            elapsed = time.time() - start_time
            
            if elapsed > max_wait_seconds:
                print(f"   ❌ Deployment timeout after {max_wait_seconds} seconds")
                print("   💡 Deployment may still be in progress. Check AWS Console.")
                raise TimeoutError(f"CloudFront deployment timeout after {max_wait_seconds} seconds")
            
            try:
                response = self.cloudfront_client.get_distribution(
                    Id=self.distribution_id
                )
                
                status = response['Distribution']['Status']
                
                if status == 'Deployed':
                    elapsed_final = int(time.time() - start_time)
                    print(f"   ✅ Deployment completed in {elapsed_final} seconds")
                    break
                else:
                    print(f"   ⏳ Status: {status} (waiting... {int(elapsed)}s elapsed)")
                    time.sleep(30)
                    
            except Exception as e:
                print(f"   ⚠️ Error checking status: {e}")
                time.sleep(30)
    
    def create_demo_data(self):
        """Create demo data file for static deployment"""
        print("📊 Creating demo data for static deployment...")
        
        demo_data = {
            "incidents": [
                {
                    "id": "demo-001",
                    "type": "database_cascade",
                    "severity": "critical",
                    "timestamp": "2025-10-20T16:00:00Z",
                    "status": "resolved",
                    "mttr_seconds": 87,
                    "cost_saved": 103313,
                    "agents_involved": ["detection", "diagnosis", "prediction", "resolution", "communication"]
                }
            ],
            "agent_reasoning": [
                {
                    "agent": "Detection",
                    "step": "Analyzing symptoms",
                    "evidence": [
                        "Connection pool: 500/500 (100% utilization)",
                        "Error rate: 47% (baseline: 0.1%)",
                        "Response time: 8.5s (baseline: 120ms)"
                    ],
                    "confidence": 0.89,
                    "timestamp": "2025-10-20T16:00:05Z"
                },
                {
                    "agent": "Diagnosis", 
                    "step": "Identifying root cause",
                    "evidence": [
                        "Query analytics_daily_rollup running 47s",
                        "12 queries blocked in queue",
                        "Historical pattern: 94% match to slow query cascade"
                    ],
                    "confidence": 0.94,
                    "timestamp": "2025-10-20T16:00:15Z"
                }
            ],
            "decision_tree": {
                "root": "Database Performance Issue",
                "chosen_path": ["Query Duration > 30s", "Pool utilization > 90%"],
                "confidence": 0.96
            },
            "performance_metrics": {
                "accuracy": 0.96,
                "calibration": 0.94,
                "bias_score": 0.12,
                "learning_gain": 0.03
            }
        }
        
        # Save demo data
        demo_file = Path("dashboard/out/demo-data.json")
        with open(demo_file, 'w') as f:
            json.dump(demo_data, f, indent=2)
        
        print("   ✅ Demo data created")
    
    def deploy(self):
        """Execute complete deployment"""
        print("🚀 DEPLOYING AI INSIGHTS DASHBOARD TO AWS")
        print("=" * 60)
        
        try:
            # Step 1: Build dashboard
            self.build_dashboard()
            
            # Step 2: Create demo data
            self.create_demo_data()
            
            # Step 3: Create S3 bucket
            self.create_s3_bucket()
            
            # Step 4: Upload files
            self.upload_files()
            
            # Step 5: Create CloudFront distribution
            self.create_cloudfront_distribution()
            
            # Step 6: Wait for deployment
            self.wait_for_deployment()
            
            # Success!
            self.print_success_info()
            
        except Exception as e:
            print(f"\n❌ Deployment failed: {e}")
            self.cleanup_on_failure()
            raise
    
    def print_success_info(self):
        """Print deployment success information"""
        print("\n" + "=" * 60)
        print("🎉 DEPLOYMENT SUCCESSFUL!")
        print("=" * 60)
        
        print(f"\n🌐 Your AI Insights Dashboard is now live:")
        print(f"   URL: https://{self.domain_name}")
        print(f"   Direct link: https://{self.domain_name}/insights-demo")
        
        print(f"\n📊 Deployment Details:")
        print(f"   S3 Bucket: {self.bucket_name}")
        print(f"   CloudFront ID: {self.distribution_id}")
        print(f"   Region: us-east-1")
        
        print(f"\n💰 Estimated Monthly Cost: $1-5")
        print(f"   S3 Storage: ~$0.50")
        print(f"   CloudFront: ~$1-4 (depending on traffic)")
        
        print(f"\n🎯 For Hackathon Judges:")
        print(f"   Share this URL: https://{self.domain_name}")
        print(f"   Demo loads automatically")
        print(f"   Works on all devices")
        print(f"   Global CDN for fast loading")
        
        print(f"\n🔧 Management:")
        print(f"   Update: Re-run this script")
        print(f"   Delete: python scripts/cleanup_aws_deployment.py")
        
        print(f"\n✅ Ready for hackathon submission!")
    
    def cleanup_on_failure(self):
        """Clean up resources if deployment fails"""
        print("\n🧹 Cleaning up failed deployment...")
        
        try:
            if hasattr(self, 'bucket_name'):
                # Delete S3 bucket contents
                objects = self.s3_client.list_objects_v2(Bucket=self.bucket_name)
                if 'Contents' in objects:
                    delete_keys = [{'Key': obj['Key']} for obj in objects['Contents']]
                    self.s3_client.delete_objects(
                        Bucket=self.bucket_name,
                        Delete={'Objects': delete_keys}
                    )
                
                # Delete bucket
                self.s3_client.delete_bucket(Bucket=self.bucket_name)
                print("   ✅ S3 bucket cleaned up")
                
        except Exception as e:
            print(f"   ⚠️ Cleanup warning: {e}")

def main():
    """Main deployment function"""
    
    # Check AWS credentials
    try:
        boto3.client('sts').get_caller_identity()
        print("✅ AWS credentials found")
    except Exception as e:
        print("❌ AWS credentials not configured")
        print("   Run: aws configure")
        print("   Or set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY")
        return
    
    # Deploy
    deployer = StaticAWSDeployer()
    deployer.deploy()

if __name__ == "__main__":
    main()