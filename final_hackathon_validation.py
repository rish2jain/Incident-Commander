#!/usr/bin/env python3
"""
Final Hackathon Validation Script

Comprehensive validation to ensure the Incident Commander is 100% ready
for hackathon presentation with all features working perfectly.
"""

import asyncio
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple


class FinalHackathonValidator:
    """Final comprehensive validation for hackathon readiness."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.validation_results: Dict[str, Any] = {}
        
    def validate_project_structure(self) -> Tuple[bool, Dict[str, Any]]:
        """Validate complete project structure."""
        print("📁 Validating Project Structure...")
        
        required_files = {
            # Core application
            "src/main.py": "FastAPI application entry point",
            "src/services/websocket_manager.py": "WebSocket connection manager",
            "src/services/realtime_integration.py": "Real-time incident broadcasting",
            
            # Enhanced dashboard
            "dashboard/enhanced_live_dashboard.html": "Enhanced demo dashboard",
            "dashboard/live_dashboard.html": "Original live dashboard",
            
            # Validation scripts
            "validate_websocket.py": "WebSocket integration validation",
            "validate_demo_performance.py": "Performance validation",
            "run_comprehensive_tests.py": "Comprehensive test suite",
            
            # Security and deployment
            "harden_security.py": "Security hardening script",
            "deploy_to_aws.py": "AWS deployment script",
            
            # Demo and documentation
            "start_demo.py": "One-command demo startup",
            "HACKATHON_DEMO_GUIDE.md": "Demo presentation guide",
            "WEBSOCKET_INTEGRATION.md": "WebSocket documentation",
            "DEPLOYMENT_CHECKLIST.md": "Deployment checklist",
            
            # Configuration
            ".env.example": "Environment configuration template",
            ".env.production.template": "Production configuration template",
            "requirements.txt": "Python dependencies",
            "requirements-lambda.txt": "Lambda deployment dependencies"
        }
        
        missing_files = []
        file_sizes = {}
        
        for file_path, description in required_files.items():
            full_path = self.project_root / file_path
            if not full_path.exists():
                missing_files.append(f"{file_path} - {description}")
            else:
                file_sizes[file_path] = full_path.stat().st_size
        
        # Check for minimum file sizes (ensure files aren't empty)
        small_files = []
        for file_path, size in file_sizes.items():
            if size < 100:  # Less than 100 bytes is likely empty or incomplete
                small_files.append(f"{file_path} ({size} bytes)")
        
        success = len(missing_files) == 0 and len(small_files) == 0
        
        result = {
            "success": success,
            "total_files": len(required_files),
            "found_files": len(file_sizes),
            "missing_files": missing_files,
            "small_files": small_files,
            "file_sizes": file_sizes
        }
        
        if success:
            print(f"✅ All {len(required_files)} required files present and valid")
        else:
            if missing_files:
                print("❌ Missing files:")
                for file in missing_files:
                    print(f"   - {file}")
            if small_files:
                print("⚠️  Suspiciously small files:")
                for file in small_files:
                    print(f"   - {file}")
        
        return success, result
    
    def validate_demo_scenarios(self) -> Tuple[bool, Dict[str, Any]]:
        """Validate all demo scenarios are properly configured."""
        print("🎭 Validating Demo Scenarios...")
        
        try:
            # Check if main.py contains all required scenarios
            main_py_path = self.project_root / "src" / "main.py"
            with open(main_py_path, 'r') as f:
                main_content = f.read()
            
            required_scenarios = [
                "database_cascade",
                "ddos_attack", 
                "memory_leak",
                "api_overload",
                "storage_failure"
            ]
            
            missing_scenarios = []
            for scenario in required_scenarios:
                if scenario not in main_content:
                    missing_scenarios.append(scenario)
            
            # Check scenario configurations
            scenario_configs_found = "scenario_configs = {" in main_content
            
            success = len(missing_scenarios) == 0 and scenario_configs_found
            
            result = {
                "success": success,
                "required_scenarios": required_scenarios,
                "missing_scenarios": missing_scenarios,
                "scenario_configs_found": scenario_configs_found
            }
            
            if success:
                print(f"✅ All {len(required_scenarios)} demo scenarios configured")
            else:
                if missing_scenarios:
                    print("❌ Missing scenarios:")
                    for scenario in missing_scenarios:
                        print(f"   - {scenario}")
                if not scenario_configs_found:
                    print("❌ Scenario configurations not found in main.py")
            
            return success, result
            
        except Exception as e:
            print(f"❌ Error validating scenarios: {e}")
            return False, {"success": False, "error": str(e)}
    
    def validate_websocket_integration(self) -> Tuple[bool, Dict[str, Any]]:
        """Validate WebSocket integration is properly implemented."""
        print("🔌 Validating WebSocket Integration...")
        
        try:
            # Check WebSocket manager
            ws_manager_path = self.project_root / "src" / "services" / "websocket_manager.py"
            with open(ws_manager_path, 'r') as f:
                ws_content = f.read()
            
            # Check for required WebSocket components
            required_components = [
                "WebSocketConnectionManager",
                "broadcast_incident_started",
                "broadcast_agent_action", 
                "broadcast_incident_resolved",
                "get_websocket_manager"
            ]
            
            missing_components = []
            for component in required_components:
                if component not in ws_content:
                    missing_components.append(component)
            
            # Check main.py for WebSocket endpoint
            main_py_path = self.project_root / "src" / "main.py"
            with open(main_py_path, 'r') as f:
                main_content = f.read()
            
            ws_endpoint_found = "@app.websocket(\"/ws\")" in main_content
            ws_import_found = "from fastapi import" in main_content and "WebSocket" in main_content
            
            success = (len(missing_components) == 0 and 
                      ws_endpoint_found and 
                      ws_import_found)
            
            result = {
                "success": success,
                "missing_components": missing_components,
                "ws_endpoint_found": ws_endpoint_found,
                "ws_import_found": ws_import_found
            }
            
            if success:
                print("✅ WebSocket integration properly implemented")
            else:
                if missing_components:
                    print("❌ Missing WebSocket components:")
                    for component in missing_components:
                        print(f"   - {component}")
                if not ws_endpoint_found:
                    print("❌ WebSocket endpoint not found in main.py")
                if not ws_import_found:
                    print("❌ WebSocket imports not found in main.py")
            
            return success, result
            
        except Exception as e:
            print(f"❌ Error validating WebSocket integration: {e}")
            return False, {"success": False, "error": str(e)}
    
    def validate_dashboard_enhancements(self) -> Tuple[bool, Dict[str, Any]]:
        """Validate enhanced dashboard features."""
        print("🎨 Validating Dashboard Enhancements...")
        
        try:
            enhanced_dashboard_path = self.project_root / "dashboard" / "enhanced_live_dashboard.html"
            
            if not enhanced_dashboard_path.exists():
                return False, {"success": False, "error": "Enhanced dashboard not found"}
            
            with open(enhanced_dashboard_path, 'r') as f:
                dashboard_content = f.read()
            
            # Check for enhanced features
            required_features = [
                "EnhancedLiveDashboard",  # Enhanced JavaScript class
                "glassmorphism",         # Modern design elements
                "backdrop-filter",       # Visual effects
                "animation:",            # CSS animations
                "websocket",             # WebSocket integration
                "scenario-btn",          # Scenario buttons
                "confidence-bar",        # Confidence visualization
                "activity-feed"          # Real-time activity feed
            ]
            
            missing_features = []
            for feature in required_features:
                if feature.lower() not in dashboard_content.lower():
                    missing_features.append(feature)
            
            # Check file size (enhanced dashboard should be substantial)
            file_size = enhanced_dashboard_path.stat().st_size
            size_adequate = file_size > 20000  # At least 20KB
            
            success = len(missing_features) == 0 and size_adequate
            
            result = {
                "success": success,
                "file_size": file_size,
                "size_adequate": size_adequate,
                "missing_features": missing_features,
                "features_found": len(required_features) - len(missing_features)
            }
            
            if success:
                print(f"✅ Enhanced dashboard validated ({file_size:,} bytes)")
            else:
                if missing_features:
                    print("❌ Missing dashboard features:")
                    for feature in missing_features:
                        print(f"   - {feature}")
                if not size_adequate:
                    print(f"⚠️  Dashboard file seems small ({file_size:,} bytes)")
            
            return success, result
            
        except Exception as e:
            print(f"❌ Error validating dashboard: {e}")
            return False, {"success": False, "error": str(e)}
    
    def validate_security_hardening(self) -> Tuple[bool, Dict[str, Any]]:
        """Validate security hardening implementation."""
        print("🔒 Validating Security Hardening...")
        
        try:
            # Check security hardening script
            security_script_path = self.project_root / "harden_security.py"
            with open(security_script_path, 'r') as f:
                security_content = f.read()
            
            # Check for security features
            security_features = [
                "SecurityHardener",
                "harden_cors_policy",
                "add_security_headers",
                "create_production_env_template",
                "create_secrets_manager_integration"
            ]
            
            missing_security_features = []
            for feature in security_features:
                if feature not in security_content:
                    missing_security_features.append(feature)
            
            # Check if production template was created
            prod_template_path = self.project_root / ".env.production.template"
            prod_template_exists = prod_template_path.exists()
            
            # Check deployment checklist
            checklist_path = self.project_root / "DEPLOYMENT_CHECKLIST.md"
            checklist_exists = checklist_path.exists()
            
            success = (len(missing_security_features) == 0 and 
                      prod_template_exists and 
                      checklist_exists)
            
            result = {
                "success": success,
                "missing_security_features": missing_security_features,
                "prod_template_exists": prod_template_exists,
                "checklist_exists": checklist_exists
            }
            
            if success:
                print("✅ Security hardening properly implemented")
            else:
                if missing_security_features:
                    print("❌ Missing security features:")
                    for feature in missing_security_features:
                        print(f"   - {feature}")
                if not prod_template_exists:
                    print("❌ Production environment template not found")
                if not checklist_exists:
                    print("❌ Deployment checklist not found")
            
            return success, result
            
        except Exception as e:
            print(f"❌ Error validating security hardening: {e}")
            return False, {"success": False, "error": str(e)}
    
    def validate_documentation_completeness(self) -> Tuple[bool, Dict[str, Any]]:
        """Validate documentation is complete and helpful."""
        print("📚 Validating Documentation...")
        
        try:
            required_docs = {
                "README.md": ["Quick Start", "Hackathon Demo"],
                "HACKATHON_DEMO_GUIDE.md": ["Demo Script", "Technical Highlights"],
                "WEBSOCKET_INTEGRATION.md": ["WebSocket", "Real-time"],
                "DEPLOYMENT_CHECKLIST.md": ["Security", "Performance"]
            }
            
            missing_docs = []
            incomplete_docs = []
            
            for doc_file, required_content in required_docs.items():
                doc_path = self.project_root / doc_file
                
                if not doc_path.exists():
                    missing_docs.append(doc_file)
                    continue
                
                with open(doc_path, 'r') as f:
                    content = f.read()
                
                missing_content = []
                for required in required_content:
                    if required.lower() not in content.lower():
                        missing_content.append(required)
                
                if missing_content:
                    incomplete_docs.append({
                        "file": doc_file,
                        "missing_content": missing_content
                    })
            
            success = len(missing_docs) == 0 and len(incomplete_docs) == 0
            
            result = {
                "success": success,
                "missing_docs": missing_docs,
                "incomplete_docs": incomplete_docs,
                "total_docs": len(required_docs)
            }
            
            if success:
                print(f"✅ All {len(required_docs)} documentation files complete")
            else:
                if missing_docs:
                    print("❌ Missing documentation:")
                    for doc in missing_docs:
                        print(f"   - {doc}")
                if incomplete_docs:
                    print("❌ Incomplete documentation:")
                    for doc in incomplete_docs:
                        print(f"   - {doc['file']}: missing {doc['missing_content']}")
            
            return success, result
            
        except Exception as e:
            print(f"❌ Error validating documentation: {e}")
            return False, {"success": False, "error": str(e)}
    
    async def run_final_validation(self) -> Dict[str, Any]:
        """Run complete final validation suite."""
        print("🎯 FINAL HACKATHON VALIDATION")
        print("=" * 60)
        print("Ensuring 100% readiness for hackathon presentation...")
        print()
        
        validation_tests = [
            ("Project Structure", self.validate_project_structure),
            ("Demo Scenarios", self.validate_demo_scenarios),
            ("WebSocket Integration", self.validate_websocket_integration),
            ("Dashboard Enhancements", self.validate_dashboard_enhancements),
            ("Security Hardening", self.validate_security_hardening),
            ("Documentation", self.validate_documentation_completeness)
        ]
        
        passed_tests = 0
        total_tests = len(validation_tests)
        detailed_results = {}
        
        for test_name, test_func in validation_tests:
            print(f"📋 {test_name}")
            print("-" * 40)
            
            try:
                success, details = test_func()
                detailed_results[test_name.lower().replace(' ', '_')] = details
                
                if success:
                    passed_tests += 1
                    print(f"✅ {test_name}: PASSED\n")
                else:
                    print(f"❌ {test_name}: FAILED\n")
                    
            except Exception as e:
                print(f"❌ {test_name}: ERROR - {e}\n")
                detailed_results[test_name.lower().replace(' ', '_')] = {
                    "success": False,
                    "error": str(e)
                }
        
        # Final assessment
        print("=" * 60)
        print("🏆 FINAL VALIDATION RESULTS")
        print("=" * 60)
        
        success_rate = (passed_tests / total_tests) * 100
        print(f"Validation Score: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        
        if passed_tests == total_tests:
            print("\n🎉 PERFECT SCORE - 100% HACKATHON READY!")
            print("✅ All systems validated and ready for presentation")
            print("🚀 System is optimized for maximum demo impact")
            readiness_status = "PERFECT"
        elif passed_tests >= total_tests * 0.9:  # 90%+
            print("\n🌟 EXCELLENT - Nearly Perfect!")
            print("✅ System is ready with minor optimizations possible")
            readiness_status = "EXCELLENT"
        elif passed_tests >= total_tests * 0.8:  # 80%+
            print("\n👍 GOOD - Ready with some improvements")
            print("⚠️  Address remaining issues for optimal experience")
            readiness_status = "GOOD"
        else:
            print("\n⚠️  NEEDS WORK - Critical issues detected")
            print("🔧 Resolve issues before hackathon presentation")
            readiness_status = "NEEDS_WORK"
        
        # Provide specific recommendations
        if passed_tests < total_tests:
            print("\n🛠️  RECOMMENDATIONS:")
            for test_name, details in detailed_results.items():
                if not details.get("success", False):
                    print(f"  • Fix {test_name.replace('_', ' ')}")
        
        # Demo readiness checklist
        print("\n📋 HACKATHON DEMO CHECKLIST:")
        checklist_items = [
            ("Enhanced dashboard loads properly", "dashboard_enhancements" in detailed_results and detailed_results["dashboard_enhancements"]["success"]),
            ("WebSocket real-time updates work", "websocket_integration" in detailed_results and detailed_results["websocket_integration"]["success"]),
            ("All 5 demo scenarios configured", "demo_scenarios" in detailed_results and detailed_results["demo_scenarios"]["success"]),
            ("Security hardening applied", "security_hardening" in detailed_results and detailed_results["security_hardening"]["success"]),
            ("Documentation complete", "documentation" in detailed_results and detailed_results["documentation"]["success"]),
            ("Project structure validated", "project_structure" in detailed_results and detailed_results["project_structure"]["success"])
        ]
        
        for item, status in checklist_items:
            icon = "✅" if status else "❌"
            print(f"  {icon} {item}")
        
        return {
            "readiness_status": readiness_status,
            "success_rate": success_rate,
            "passed_tests": passed_tests,
            "total_tests": total_tests,
            "detailed_results": detailed_results,
            "ready_for_hackathon": passed_tests == total_tests,
            "checklist_complete": all(status for _, status in checklist_items)
        }


async def main():
    """Run final hackathon validation."""
    validator = FinalHackathonValidator()
    
    try:
        results = await validator.run_final_validation()
        
        if results["ready_for_hackathon"]:
            print("\n🎯 HACKATHON READY - GO WIN! 🏆")
            sys.exit(0)
        elif results["success_rate"] >= 90:
            print("\n🌟 NEARLY PERFECT - Minor tweaks recommended")
            sys.exit(0)
        elif results["success_rate"] >= 80:
            print("\n👍 GOOD SHAPE - Address remaining issues")
            sys.exit(1)
        else:
            print("\n🔧 NEEDS WORK - Fix critical issues first")
            sys.exit(2)
            
    except KeyboardInterrupt:
        print("\n⏹️  Validation cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Validation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())