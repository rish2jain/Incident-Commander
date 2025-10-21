#!/usr/bin/env python3
"""
AWS Deployment Cleanup Script
Removes all AWS resources created for the dashboard deployment
"""

import boto3
import json
import time
from pathlib import Path

class AWSCleanup:
    def __init__(self):
        self.s3_client = boto3.client('s3')
        self.cloudfront_client = boto3.client('cloudfront')
        
    def find_resources(self):
        """Find all resources created by the deployment"""
        print("🔍 Finding deployed resources...")
        
        resources = {
            'buckets': [],
            'distributions': []
        }
        
        # Find S3 buckets
        try:
            buckets = self.s3_client.list_buckets()
            for bucket in buckets['Buckets']:
                if 'ai-insights-dashboard' in bucket['Name']:
                    resources['buckets'].append(bucket['Name'])
                    print(f"   📦 Found S3 bucket: {bucket['Name']}")
        except Exception as e:
            print(f"   ⚠️ Error finding S3 buckets: {e}")
        
        # Find CloudFront distributions
        try:
            distributions = self.cloudfront_client.list_distributions()
            if 'DistributionList' in distributions and 'Items' in distributions['DistributionList']:
                for dist in distributions['DistributionList']['Items']:
                    if 'AI Insights Dashboard' in dist.get('Comment', ''):
                        resources['distributions'].append({
                            'id': dist['Id'],
                            'domain': dist['DomainName'],
                            'status': dist['Status']
                        })
                        print(f"   🌐 Found CloudFront distribution: {dist['Id']}")
        except Exception as e:
            print(f"   ⚠️ Error finding CloudFront distributions: {e}")
        
        return resources
    
    def delete_s3_bucket(self, bucket_name):
        """Delete S3 bucket and all contents"""
        print(f"🗑️ Deleting S3 bucket: {bucket_name}")
        
        try:
            # Delete all objects in bucket
            objects = self.s3_client.list_objects_v2(Bucket=bucket_name)
            
            if 'Contents' in objects:
                delete_keys = [{'Key': obj['Key']} for obj in objects['Contents']]
                
                # Delete objects in batches
                for i in range(0, len(delete_keys), 1000):
                    batch = delete_keys[i:i+1000]
                    self.s3_client.delete_objects(
                        Bucket=bucket_name,
                        Delete={'Objects': batch}
                    )
                
                print(f"   ✅ Deleted {len(delete_keys)} objects")
            
            # Delete bucket
            self.s3_client.delete_bucket(Bucket=bucket_name)
            print(f"   ✅ Bucket deleted: {bucket_name}")
            
        except Exception as e:
            print(f"   ❌ Failed to delete bucket {bucket_name}: {e}")
    
    def delete_cloudfront_distribution(self, distribution):
        """Delete CloudFront distribution"""
        dist_id = distribution['id']
        print(f"🌐 Deleting CloudFront distribution: {dist_id}")
        
        try:
            # Get current distribution config
            response = self.cloudfront_client.get_distribution_config(Id=dist_id)
            config = response['DistributionConfig']
            etag = response['ETag']
            
            # Disable distribution first
            if config['Enabled']:
                print(f"   ⏳ Disabling distribution...")
                config['Enabled'] = False
                
                self.cloudfront_client.update_distribution(
                    Id=dist_id,
                    DistributionConfig=config,
                    IfMatch=etag
                )
                
                # Wait for distribution to be disabled
                self.wait_for_distribution_status(dist_id, 'Deployed')
                print(f"   ✅ Distribution disabled")
            
            # Get updated ETag
            response = self.cloudfront_client.get_distribution_config(Id=dist_id)
            etag = response['ETag']
            
            # Delete distribution
            self.cloudfront_client.delete_distribution(Id=dist_id, IfMatch=etag)
            print(f"   ✅ Distribution deletion initiated: {dist_id}")
            
        except Exception as e:
            print(f"   ❌ Failed to delete distribution {dist_id}: {e}")
    
    def wait_for_distribution_status(self, dist_id, target_status):
        """Wait for CloudFront distribution to reach target status"""
        max_wait = 900  # 15 minutes
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            try:
                response = self.cloudfront_client.get_distribution(Id=dist_id)
                status = response['Distribution']['Status']
                
                if status == target_status:
                    return True
                
                print(f"   ⏳ Status: {status} (waiting for {target_status})")
                time.sleep(30)
                
            except Exception as e:
                print(f"   ⚠️ Error checking status: {e}")
                time.sleep(30)
        
        print(f"   ⚠️ Timeout waiting for {target_status}")
        return False
    
    def cleanup_local_files(self):
        """Clean up local deployment files"""
        print("🧹 Cleaning up local files...")
        
        files_to_remove = [
            "aws-deployment-config.json",
            "JUDGE_INSTRUCTIONS.md",
            "dashboard/out",
            "dashboard/next.config.js"
        ]
        
        removed_count = 0
        
        for file_path in files_to_remove:
            path = Path(file_path)
            try:
                if path.is_file():
                    path.unlink()
                    print(f"   ✅ Removed file: {file_path}")
                    removed_count += 1
                elif path.is_dir():
                    import shutil
                    shutil.rmtree(path)
                    print(f"   ✅ Removed directory: {file_path}")
                    removed_count += 1
            except Exception as e:
                print(f"   ⚠️ Could not remove {file_path}: {e}")
        
        print(f"   📊 Removed {removed_count} local files")
    
    def cleanup_all(self):
        """Execute complete cleanup"""
        print("🧹 AWS DEPLOYMENT CLEANUP")
        print("=" * 50)
        
        # Find resources
        resources = self.find_resources()
        
        if not resources['buckets'] and not resources['distributions']:
            print("\n✅ No AWS resources found to clean up")
            self.cleanup_local_files()
            return
        
        # Confirm cleanup
        print(f"\n⚠️ This will delete:")
        for bucket in resources['buckets']:
            print(f"   📦 S3 bucket: {bucket}")
        for dist in resources['distributions']:
            print(f"   🌐 CloudFront distribution: {dist['id']}")
        
        confirm = input(f"\nContinue with cleanup? (yes/no): ").lower().strip()
        if confirm != 'yes':
            print("❌ Cleanup cancelled")
            return
        
        # Delete CloudFront distributions
        for distribution in resources['distributions']:
            self.delete_cloudfront_distribution(distribution)
        
        # Delete S3 buckets
        for bucket in resources['buckets']:
            self.delete_s3_bucket(bucket)
        
        # Clean up local files
        self.cleanup_local_files()
        
        print(f"\n" + "=" * 50)
        print(f"✅ CLEANUP COMPLETE!")
        print(f"=" * 50)
        print(f"\n💰 AWS resources deleted - no more charges")
        print(f"🧹 Local files cleaned up")
        print(f"✅ Ready for fresh deployment if needed")

def main():
    """Main cleanup function"""
    
    # Check AWS credentials
    try:
        boto3.client('sts').get_caller_identity()
        print("✅ AWS credentials found")
    except Exception as e:
        print("❌ AWS credentials not configured")
        print("   Run: aws configure")
        return
    
    # Execute cleanup
    cleanup = AWSCleanup()
    cleanup.cleanup_all()

if __name__ == "__main__":
    main()