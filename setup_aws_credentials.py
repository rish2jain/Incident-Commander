#!/usr/bin/env python3
"""
AWS Credentials Setup Helper for Incident Commander Hackathon
"""

import os
import platform
import subprocess
import sys


def check_aws_cli():
    """Check if AWS CLI is installed."""
    try:
        result = subprocess.run(['aws', '--version'], capture_output=True, text=True)
        print(f"✅ AWS CLI installed: {result.stdout.strip()}")
        return True
    except FileNotFoundError:
        print("❌ AWS CLI not found. Please install it first.")
        return False


def check_aws_credentials():
    """Check if AWS credentials are configured."""
    try:
        result = subprocess.run(['aws', 'sts', 'get-caller-identity'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ AWS credentials are configured")
            print(f"Account: {result.stdout}")
            return True
        else:
            print("❌ AWS credentials not configured or invalid")
            print(f"Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error checking AWS credentials: {e}")
        return False


def setup_credentials():
    """Guide user through AWS credentials setup."""
    print("\n🔧 AWS Credentials Setup")
    print("=" * 50)
    
    print("\nYou need AWS credentials to deploy the Incident Commander.")
    print("You can get these from your AWS Console:")
    print("1. Go to AWS Console > IAM > Users")
    print("2. Create a new user or select existing user")
    print("3. Go to Security Credentials tab")
    print("4. Create Access Key")
    
    print("\nRunning 'aws configure' to set up credentials...")
    print("You'll need to provide:")
    print("- AWS Access Key ID")
    print("- AWS Secret Access Key") 
    print("- Default region (recommend: us-east-1)")
    print("- Default output format (recommend: json)")
    
    try:
        subprocess.run(['aws', 'configure'], check=True)
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to configure AWS credentials")
        return False
    except KeyboardInterrupt:
        print("\n❌ Setup cancelled by user")
        return False


def check_bedrock_access():
    """Check if Bedrock is available in the region."""
    try:
        result = subprocess.run([
            'aws', 'bedrock', 'list-foundation-models', 
            '--region', 'us-east-1'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Bedrock access confirmed in us-east-1")
            return True
        else:
            print("⚠️  Bedrock access issue:")
            print(f"Error: {result.stderr}")
            print("\nYou may need to:")
            print("1. Request access to Bedrock models in AWS Console")
            print("2. Ensure you're using us-east-1 region")
            return False
    except Exception as e:
        print(f"⚠️  Could not check Bedrock access: {e}")
        return False


def main():
    """Main setup function."""
    print("🚀 Incident Commander - AWS Setup")
    print("=" * 50)
    
    # Check AWS CLI
    if not check_aws_cli():
        print("\nPlease install AWS CLI first:")
        system = platform.system().lower()
        if system == "darwin":
            print("brew install awscli")
        elif system == "linux":
            print("# For Ubuntu/Debian:")
            print("sudo apt-get update && sudo apt-get install awscli")
            print("# For RHEL/CentOS/Fedora:")
            print("sudo yum install awscli  # or sudo dnf install awscli")
        elif system == "windows":
            print("# Using Chocolatey:")
            print("choco install awscli")
            print("# Using winget:")
            print("winget install Amazon.AWSCLI")
        else:
            print("Visit: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html")
        sys.exit(1)
    
    # Check credentials
    if not check_aws_credentials():
        print("\n🔧 Setting up AWS credentials...")
        if not setup_credentials():
            sys.exit(1)
        
        # Verify after setup
        if not check_aws_credentials():
            print("❌ Credentials setup failed")
            sys.exit(1)
    
    # Check Bedrock access
    check_bedrock_access()
    
    print("\n✅ AWS setup complete!")
    print("\nNext steps:")
    print("1. Run: cdk bootstrap")
    print("2. Run: cdk deploy --all")
    print("3. Test deployment with: curl <api-gateway-url>/health")


if __name__ == "__main__":
    main()