#!/usr/bin/env python3
"""
Comprehensive Test Suite for Hackathon Readiness

Runs all validation tests to ensure the Incident Commander is ready for demo.
"""

import asyncio
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Any, List


class ComprehensiveTestRunner:
    """Runs all tests to validate hackathon readiness."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.test_results: Dict[str, Any] = {}
        
    def run_foundation_tests(self) -> bool:
        """Run foundation test suite."""
        print("🧪 Running Foundation Tests...")
        
        try:
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                "tests/test_foundation.py", 
                "-v", "--tb=short"
            ], capture_output=True, text=True, timeout=120)
            
            success = result.returncode == 0
            
            if success:
                print("✅ Foundation tests passed")
            else:
                print("❌ Foundation tests failed")
                print(f"Error: {result.stderr}")
            
            self.test_results['foundation_tests'] = {
                'success': success,
                'output': result.stdout,
                'error': result.stderr
            }
            
            return success
            
        except subprocess.TimeoutExpired:
            print("❌ Foundation tests timed out")
            return False
        except Exception as e:
            print(f"❌ Foundation tests error: {e}")
            return False
    
    def run_setup_verification(self) -> bool:
        """Run setup verification script."""
        print("🔧 Running Setup Verification...")
        
        try:
            result = subprocess.run([
                sys.executable, "scripts/verify_setup.py"
            ], capture_output=True, text=True, timeout=60)
            
            success = result.returncode == 0
            
            if success:
                print("✅ Setup verification passed")
            else:
                print("❌ Setup verification failed")
                print(f"Error: {result.stderr}")
            
            self.test_results['setup_verification'] = {
                'success': success,
                'output': result.stdout,
                'error': result.stderr
            }
            
            return success
            
        except Exception as e:
            print(f"❌ Setup verification error: {e}")
            return False
    
    async def run_websocket_validation(self) -> bool:
        """Run WebSocket integration validation."""
        print("🔌 Running WebSocket Validation...")
        
        try:
            # Import and run WebSocket validator
            from validate_websocket import WebSocketValidator
            
            validator = WebSocketValidator()
            success = await validator.run_validation()
            
            self.test_results['websocket_validation'] = {
                'success': success,
                'details': 'WebSocket integration validated'
            }
            
            return success
            
        except Exception as e:
            print(f"❌ WebSocket validation error: {e}")
            self.test_results['websocket_validation'] = {
                'success': False,
                'error': str(e)
            }
            return False
    
    async def run_performance_validation(self) -> bool:
        """Run performance validation."""
        print("⚡ Running Performance Validation...")
        
        try:
            # Import and run performance validator
            from validate_demo_performance import DemoPerformanceValidator
            
            validator = DemoPerformanceValidator()
            results = await validator.run_performance_validation()
            
            success = results['all_targets_met']
            
            self.test_results['performance_validation'] = {
                'success': success,
                'results': results['summary']
            }
            
            return success
            
        except Exception as e:
            print(f"❌ Performance validation error: {e}")
            self.test_results['performance_validation'] = {
                'success': False,
                'error': str(e)
            }
            return False
    
    def run_security_hardening(self) -> bool:
        """Run security hardening."""
        print("🔒 Running Security Hardening...")
        
        try:
            result = subprocess.run([
                sys.executable, "harden_security.py"
            ], capture_output=True, text=True, timeout=60)
            
            success = result.returncode == 0
            
            if success:
                print("✅ Security hardening completed")
            else:
                print("❌ Security hardening failed")
                print(f"Error: {result.stderr}")
            
            self.test_results['security_hardening'] = {
                'success': success,
                'output': result.stdout,
                'error': result.stderr
            }
            
            return success
            
        except Exception as e:
            print(f"❌ Security hardening error: {e}")
            return False
    
    def check_file_integrity(self) -> bool:
        """Check that all required files exist."""
        print("📁 Checking File Integrity...")
        
        required_files = [
            "src/main.py",
            "src/services/websocket_manager.py",
            "src/services/realtime_integration.py",
            "dashboard/enhanced_live_dashboard.html",
            "dashboard/live_dashboard.html",
            "validate_websocket.py",
            "validate_demo_performance.py",
            "harden_security.py",
            "start_demo.py",
            "WEBSOCKET_INTEGRATION.md",
            "DEPLOYMENT_CHECKLIST.md"
        ]
        
        missing_files = []
        
        for file_path in required_files:
            if not (self.project_root / file_path).exists():
                missing_files.append(file_path)
        
        if missing_files:
            print("❌ Missing required files:")
            for file_path in missing_files:
                print(f"   - {file_path}")
            
            self.test_results['file_integrity'] = {
                'success': False,
                'missing_files': missing_files
            }
            return False
        else:
            print("✅ All required files present")
            self.test_results['file_integrity'] = {
                'success': True,
                'files_checked': len(required_files)
            }
            return True
    
    def validate_configuration(self) -> bool:
        """Validate configuration files."""
        print("⚙️  Validating Configuration...")
        
        try:
            # Check .env.example exists
            env_example = self.project_root / ".env.example"
            if not env_example.exists():
                print("❌ .env.example not found")
                return False
            
            # Check production template exists
            env_prod_template = self.project_root / ".env.production.template"
            if not env_prod_template.exists():
                print("❌ .env.production.template not found")
                return False
            
            # Validate basic configuration structure
            try:
                from src.utils.config import config
                config.validate_required_config()
                print("✅ Configuration validation passed")
                
                self.test_results['configuration'] = {
                    'success': True,
                    'details': 'Configuration files validated'
                }
                return True
                
            except Exception as e:
                print(f"❌ Configuration validation failed: {e}")
                self.test_results['configuration'] = {
                    'success': False,
                    'error': str(e)
                }
                return False
                
        except Exception as e:
            print(f"❌ Configuration check error: {e}")
            return False
    
    async def run_comprehensive_tests(self) -> Dict[str, Any]:
        """Run all comprehensive tests."""
        print("🚀 Starting Comprehensive Test Suite")
        print("=" * 60)
        
        test_functions = [
            ("File Integrity", self.check_file_integrity),
            ("Configuration", self.validate_configuration),
            ("Foundation Tests", self.run_foundation_tests),
            ("Setup Verification", self.run_setup_verification),
            ("WebSocket Validation", self.run_websocket_validation),
            ("Performance Validation", self.run_performance_validation),
            ("Security Hardening", self.run_security_hardening)
        ]
        
        passed_tests = 0
        total_tests = len(test_functions)
        
        for test_name, test_func in test_functions:
            print(f"\n📋 {test_name}")
            print("-" * 40)
            
            try:
                if asyncio.iscoroutinefunction(test_func):
                    success = await test_func()
                else:
                    success = test_func()
                
                if success:
                    passed_tests += 1
                    print(f"✅ {test_name}: PASSED")
                else:
                    print(f"❌ {test_name}: FAILED")
                    
            except Exception as e:
                print(f"❌ {test_name}: ERROR - {e}")
                self.test_results[test_name.lower().replace(' ', '_')] = {
                    'success': False,
                    'error': str(e)
                }
        
        # Generate final report
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE TEST RESULTS")
        print("=" * 60)
        
        success_rate = (passed_tests / total_tests) * 100
        
        print(f"Tests Passed: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        
        if passed_tests == total_tests:
            print("🎉 ALL TESTS PASSED - HACKATHON READY!")
            print("✅ System is fully validated and ready for demo")
            status = "READY"
        elif passed_tests >= total_tests * 0.8:  # 80% pass rate
            print("⚠️  MOSTLY READY - Minor issues detected")
            print("🔧 Address remaining issues for optimal demo experience")
            status = "MOSTLY_READY"
        else:
            print("❌ NOT READY - Critical issues detected")
            print("🛠️  Resolve issues before hackathon demo")
            status = "NOT_READY"
        
        # Detailed results
        print("\n📋 Detailed Results:")
        for test_name, result in self.test_results.items():
            status_icon = "✅" if result['success'] else "❌"
            print(f"  {status_icon} {test_name.replace('_', ' ').title()}")
        
        return {
            'status': status,
            'passed_tests': passed_tests,
            'total_tests': total_tests,
            'success_rate': success_rate,
            'detailed_results': self.test_results,
            'ready_for_hackathon': passed_tests == total_tests
        }


async def main():
    """Run comprehensive test suite."""
    runner = ComprehensiveTestRunner()
    
    try:
        results = await runner.run_comprehensive_tests()
        
        if results['ready_for_hackathon']:
            print("\n🚀 HACKATHON READY!")
            sys.exit(0)
        elif results['status'] == 'MOSTLY_READY':
            print("\n⚠️  MOSTLY READY - Review issues")
            sys.exit(1)
        else:
            print("\n❌ NOT READY - Fix critical issues")
            sys.exit(2)
            
    except KeyboardInterrupt:
        print("\n⏹️  Test suite cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())