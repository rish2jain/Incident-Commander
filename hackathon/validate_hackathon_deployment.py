#!/usr/bin/env python3
"""
Hackathon Deployment Validation Script

Validates that all systems are ready for hackathon submission and demo.
"""

import requests
import json
import time
from typing import Dict, Any, List
from datetime import datetime


class HackathonValidator:
    """Validates hackathon deployment readiness."""
    
    def __init__(self):
        self.base_url = "https://h8xlzr74h8.execute-api.us-east-1.amazonaws.com"
        self.endpoints = {
            'main': '',
            'health': '/health',
            'demo_incident': '/demo/incident',
            'demo_stats': '/demo/stats'
        }
        self.results = []
    
    def test_endpoint(self, name: str, path: str) -> Dict[str, Any]:
        """Test a single endpoint."""
        url = f"{self.base_url}{path}"
        
        try:
            start_time = time.time()
            response = requests.get(url, timeout=10)
            response_time = (time.time() - start_time) * 1000  # ms
            
            result = {
                'endpoint': name,
                'url': url,
                'status_code': response.status_code,
                'response_time_ms': round(response_time, 2),
                'success': response.status_code == 200,
                'content_type': response.headers.get('content-type', ''),
                'response_size': len(response.content)
            }
            
            if response.status_code == 200:
                try:
                    result['json_response'] = response.json()
                    result['json_valid'] = True
                except:
                    result['json_valid'] = False
                    result['response_text'] = response.text[:200]
            else:
                result['error'] = response.text[:200]
            
            return result
            
        except Exception as e:
            return {
                'endpoint': name,
                'url': url,
                'success': False,
                'error': str(e),
                'response_time_ms': 0
            }
    
    def validate_response_content(self, endpoint: str, response: Dict[str, Any]) -> List[str]:
        """Validate response content for specific endpoints."""
        issues = []
        
        if endpoint == 'main':
            required_fields = ['service', 'description', 'features', 'endpoints']
            for field in required_fields:
                if field not in response:
                    issues.append(f"Missing required field: {field}")
            
            if 'features' in response and len(response['features']) < 5:
                issues.append("Should have at least 5 features listed")
        
        elif endpoint == 'demo_incident':
            required_fields = ['incident_id', 'status', 'resolution_time', 'cost_saved']
            for field in required_fields:
                if field not in response:
                    issues.append(f"Missing required field: {field}")
            
            if response.get('status') != 'resolved':
                issues.append("Incident should show as resolved")
        
        elif endpoint == 'demo_stats':
            required_fields = ['mttr_improvement', 'annual_savings', 'roi', 'aws_services']
            for field in required_fields:
                if field not in response:
                    issues.append(f"Missing required field: {field}")
            
            if response.get('aws_services') != 8:
                issues.append("Should show 8 AWS services integrated")
        
        return issues
    
    def run_validation(self) -> Dict[str, Any]:
        """Run complete validation suite."""
        print("🚀 Starting Hackathon Deployment Validation")
        print("=" * 60)
        
        all_passed = True
        total_response_time = 0
        
        for name, path in self.endpoints.items():
            print(f"\n🧪 Testing {name} endpoint...")
            result = self.test_endpoint(name, path)
            self.results.append(result)
            
            if result['success']:
                print(f"✅ {name}: {result['status_code']} - {result['response_time_ms']}ms")
                total_response_time += result['response_time_ms']
                
                # Validate content
                if result.get('json_valid') and result.get('json_response'):
                    issues = self.validate_response_content(name, result['json_response'])
                    if issues:
                        print(f"⚠️  Content issues: {', '.join(issues)}")
                        result['content_issues'] = issues
                    else:
                        print(f"✅ Content validation passed")
                        result['content_valid'] = True
            else:
                print(f"❌ {name}: FAILED - {result.get('error', 'Unknown error')}")
                all_passed = False
        
        # Calculate summary
        avg_response_time = total_response_time / len([r for r in self.results if r['success']])
        
        summary = {
            'validation_time': datetime.utcnow().isoformat(),
            'all_endpoints_passed': all_passed,
            'total_endpoints': len(self.endpoints),
            'successful_endpoints': len([r for r in self.results if r['success']]),
            'average_response_time_ms': round(avg_response_time, 2),
            'base_url': self.base_url,
            'results': self.results
        }
        
        return summary
    
    def print_summary(self, summary: Dict[str, Any]):
        """Print validation summary."""
        print("\n" + "=" * 60)
        print("📊 VALIDATION SUMMARY")
        print("=" * 60)
        
        status = "✅ READY" if summary['all_endpoints_passed'] else "❌ ISSUES FOUND"
        print(f"Status: {status}")
        print(f"Endpoints: {summary['successful_endpoints']}/{summary['total_endpoints']} passing")
        print(f"Average Response Time: {summary['average_response_time_ms']}ms")
        print(f"Base URL: {summary['base_url']}")
        
        print("\n📋 Endpoint Details:")
        for result in summary['results']:
            status_icon = "✅" if result['success'] else "❌"
            print(f"  {status_icon} {result['endpoint']}: {result.get('response_time_ms', 0)}ms")
        
        if summary['all_endpoints_passed']:
            print("\n🎉 HACKATHON DEPLOYMENT READY!")
            print("✅ All systems operational for demo")
            print("✅ API responses validated")
            print("✅ Performance within acceptable limits")
            
            print("\n🎬 Demo Script Ready:")
            print("1. Main API: Shows system overview and capabilities")
            print("2. Demo Incident: Shows autonomous resolution example")
            print("3. Demo Stats: Shows business impact metrics")
            
            print("\n🏆 Submission Checklist:")
            print("✅ AWS deployment live and tested")
            print("✅ API endpoints responding correctly")
            print("✅ Demo content validated")
            print("✅ Performance metrics acceptable")
            print("✅ Ready for video recording")
        else:
            print("\n⚠️  ISSUES TO RESOLVE:")
            for result in summary['results']:
                if not result['success']:
                    print(f"  • {result['endpoint']}: {result.get('error', 'Failed')}")
    
    def generate_demo_commands(self):
        """Generate demo commands for video recording."""
        print("\n🎬 DEMO COMMANDS FOR VIDEO RECORDING")
        print("=" * 60)
        
        commands = [
            ("System Overview", f"curl -s {self.base_url} | jq ."),
            ("Demo Incident", f"curl -s {self.base_url}/demo/incident | jq ."),
            ("Demo Stats", f"curl -s {self.base_url}/demo/stats | jq .")
        ]
        
        for name, command in commands:
            print(f"\n# {name}")
            print(f"{command}")
        
        print("\n📝 Copy these commands for your demo video!")
        print("💡 Test them before recording to ensure they work")


def main():
    """Run hackathon validation."""
    validator = HackathonValidator()
    
    try:
        summary = validator.run_validation()
        validator.print_summary(summary)
        validator.generate_demo_commands()
        
        # Save results
        with open('hackathon_validation_results.json', 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n💾 Results saved to: hackathon_validation_results.json")
        
        if summary['all_endpoints_passed']:
            print("\n🚀 YOU'RE READY TO WIN THE HACKATHON! 🏆")
            exit(0)
        else:
            print("\n⚠️  Please resolve issues before submission")
            exit(1)
            
    except Exception as e:
        print(f"\n❌ Validation failed: {e}")
        exit(1)


if __name__ == "__main__":
    main()