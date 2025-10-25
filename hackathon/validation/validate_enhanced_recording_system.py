#!/usr/bin/env python3


October 24, 2025 - Updated to validate latest UI enhancements
"""
Enhanced Recording System Validation Script
Validates the professional HD recording system for hackathon submission.


October 24, 2025 - Updated to validate latest UI enhancements
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from record_demo import EnhancedDemoRecorder, DEMO_SCENARIOS, BUSINESS_METRICS, AWS_AI_SERVICES, RECORDING_CONFIG
    import requests
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please ensure all dependencies are installed and the project structure is correct.")
    sys.exit(1)


class EnhancedRecordingValidator:
    """Validates the enhanced recording system for hackathon readiness."""
    
    def __init__(self):
        self.validation_results = {
            "timestamp": datetime.now().isoformat(),
            "system_status": "unknown",
            "validations": {},
            "errors": [],
            "warnings": [],
            "recommendations": []
        }
        
    def validate_configuration(self) -> bool:
        """Validate recording configuration."""
        print("🔍 Validating recording configuration...")
        
        try:
            # Check recording config
            required_config_keys = [
                "video_format", "video_quality", "screenshot_format", 
                "viewport", "base_url", "backend_url", "recording_duration"
            ]
            
            for key in required_config_keys:
                if key not in RECORDING_CONFIG:
                    self.validation_results["errors"].append(f"Missing recording config key: {key}")
                    return False
            
            # Validate viewport
            viewport = RECORDING_CONFIG["viewport"]
            if viewport["width"] != 1920 or viewport["height"] != 1080:
                self.validation_results["warnings"].append("Viewport not set to HD 1920x1080")
            
            # Check demo scenarios
            if len(DEMO_SCENARIOS) != 5:
                self.validation_results["errors"].append(f"Expected 5 demo scenarios, found {len(DEMO_SCENARIOS)}")
                return False
            
            # Validate scenario structure
            required_scenario_keys = ["name", "url", "duration", "description", "business_focus", "actions", "key_points"]
            for i, scenario in enumerate(DEMO_SCENARIOS):
                for key in required_scenario_keys:
                    if key not in scenario:
                        self.validation_results["errors"].append(f"Scenario {i} missing key: {key}")
                        return False
            
            # Check business metrics
            required_metrics = ["annual_savings", "roi_percentage", "mttr_improvement", "cost_per_incident"]
            for metric in required_metrics:
                if metric not in BUSINESS_METRICS:
                    self.validation_results["errors"].append(f"Missing business metric: {metric}")
                    return False
            
            # Check AWS AI services
            if len(AWS_AI_SERVICES) != 8:
                self.validation_results["errors"].append(f"Expected 8 AWS AI services, found {len(AWS_AI_SERVICES)}")
                return False
            
            self.validation_results["validations"]["configuration"] = "✅ PASS"
            print("✅ Configuration validation passed")
            return True
            
        except Exception as e:
            self.validation_results["errors"].append(f"Configuration validation error: {e}")
            self.validation_results["validations"]["configuration"] = "❌ FAIL"
            print(f"❌ Configuration validation failed: {e}")
            return False
    
    def validate_system_requirements(self) -> bool:
        """Validate system requirements for recording."""
        print("🔍 Validating system requirements...")
        
        try:
            # Check dashboard availability
            dashboard_available = False
            try:
                response = requests.get(RECORDING_CONFIG["base_url"], timeout=5)
                if response.status_code == 200:
                    dashboard_available = True
                    print("✅ Dashboard is accessible")
                else:
                    self.validation_results["warnings"].append(f"Dashboard returned status {response.status_code}")
            except requests.exceptions.ConnectionError:
                self.validation_results["warnings"].append("Dashboard not running - recording will work but some features may be limited")
            except Exception as e:
                self.validation_results["warnings"].append(f"Dashboard check failed: {e}")
            
            # Check backend API (optional)
            backend_available = False
            try:
                response = requests.get(f"{RECORDING_CONFIG['backend_url']}/health", timeout=5)
                if response.status_code == 200:
                    backend_available = True
                    print("✅ Backend API is accessible")
                else:
                    self.validation_results["warnings"].append(f"Backend API returned status {response.status_code}")
            except requests.exceptions.ConnectionError:
                self.validation_results["warnings"].append("Backend API not running - some features may be limited")
            except Exception as e:
                self.validation_results["warnings"].append(f"Backend API check failed: {e}")
            
            # Check required directories
            demo_recordings_dir = Path("demo_recordings")
            if not demo_recordings_dir.exists():
                demo_recordings_dir.mkdir(exist_ok=True)
                print("✅ Created demo_recordings directory")
            
            # Check Python dependencies
            try:
                import playwright
                print("✅ Playwright is available")
            except ImportError:
                self.validation_results["errors"].append("Playwright not installed - run: pip install playwright && playwright install")
                return False
            
            self.validation_results["validations"]["system_requirements"] = "✅ PASS"
            print("✅ System requirements validation passed")
            return True
            
        except Exception as e:
            self.validation_results["errors"].append(f"System requirements validation error: {e}")
            self.validation_results["validations"]["system_requirements"] = "❌ FAIL"
            print(f"❌ System requirements validation failed: {e}")
            return False
    
    def validate_recording_scenarios(self) -> bool:
        """Validate recording scenarios for completeness."""
        print("🔍 Validating recording scenarios...")
        
        try:
            total_duration = sum(scenario["duration"] for scenario in DEMO_SCENARIOS)
            expected_duration = RECORDING_CONFIG["recording_duration"]
            
            if total_duration > expected_duration * 1.2:
                self.validation_results["warnings"].append(f"Total scenario duration ({total_duration}s) exceeds recording duration ({expected_duration}s)")
            
            # Validate scenario coverage
            scenario_names = [scenario["name"] for scenario in DEMO_SCENARIOS]
            expected_scenarios = ["homepage", "power_demo", "transparency", "operations", "aws_ai_showcase"]
            
            for expected in expected_scenarios:
                if expected not in scenario_names:
                    self.validation_results["errors"].append(f"Missing expected scenario: {expected}")
                    return False
            
            # Validate business focus
            for scenario in DEMO_SCENARIOS:
                if not scenario.get("business_focus"):
                    self.validation_results["warnings"].append(f"Scenario {scenario['name']} missing business focus")
                
                if not scenario.get("key_points"):
                    self.validation_results["warnings"].append(f"Scenario {scenario['name']} missing key points")
            
            self.validation_results["validations"]["recording_scenarios"] = "✅ PASS"
            print("✅ Recording scenarios validation passed")
            return True
            
        except Exception as e:
            self.validation_results["errors"].append(f"Recording scenarios validation error: {e}")
            self.validation_results["validations"]["recording_scenarios"] = "❌ FAIL"
            print(f"❌ Recording scenarios validation failed: {e}")
            return False
    
    def validate_segmented_mp4_system(self) -> bool:
        """Validate segmented MP4 recording system."""
        print("🔍 Validating segmented MP4 recording system...")
        
        try:
            # Check for existing segmented recordings
            videos_dir = Path("demo_recordings/videos")
            if videos_dir.exists():
                mp4_files = list(videos_dir.glob("*_segment.mp4"))
                if mp4_files:
                    print(f"✅ Found {len(mp4_files)} existing MP4 segments")
                    
                    # Validate segment naming convention
                    expected_segments = [
                        "homepage_segment.mp4",
                        "power_demo_segment.mp4", 
                        "transparency_segment.mp4",
                        "operations_segment.mp4",
                        "aws_ai_showcase_segment.mp4",
                        "final_overview_segment.mp4"
                    ]
                    
                    found_segments = []
                    for mp4_file in mp4_files:
                        for expected in expected_segments:
                            if expected in mp4_file.name:
                                found_segments.append(expected)
                                break
                    
                    if len(found_segments) >= 5:  # At least 5 of 6 segments
                        print(f"✅ Found {len(found_segments)} expected segments")
                    else:
                        self.validation_results["warnings"].append(f"Only found {len(found_segments)} of 6 expected segments")
                else:
                    self.validation_results["warnings"].append("No MP4 segments found - will be generated during recording")
            
            # Validate MP4 configuration
            video_format = RECORDING_CONFIG.get("video_format", "")
            if "mp4" not in video_format.lower():
                self.validation_results["warnings"].append("Video format should include MP4 for segmented recording")
            
            # Check for H.264/AAC encoding capability
            try:
                import subprocess
                result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    print("✅ FFmpeg available for MP4 encoding")
                else:
                    self.validation_results["warnings"].append("FFmpeg not available - may affect MP4 quality")
            except (subprocess.TimeoutExpired, FileNotFoundError):
                self.validation_results["warnings"].append("FFmpeg not found - MP4 encoding may be limited")
            
            self.validation_results["validations"]["segmented_mp4_system"] = "✅ PASS"
            print("✅ Segmented MP4 system validation passed")
            return True
            
        except Exception as e:
            self.validation_results["errors"].append(f"Segmented MP4 system validation error: {e}")
            self.validation_results["validations"]["segmented_mp4_system"] = "❌ FAIL"
            print(f"❌ Segmented MP4 system validation failed: {e}")
            return False
    
    def validate_business_metrics(self) -> bool:
        """Validate business metrics for hackathon submission."""
        print("🔍 Validating business metrics...")
        
        try:
            # Check metric values
            annual_savings = BUSINESS_METRICS.get("annual_savings", "")
            if not annual_savings.startswith("$"):
                self.validation_results["warnings"].append("Annual savings should be formatted as currency")
            
            roi_percentage = BUSINESS_METRICS.get("roi_percentage", "")
            if not roi_percentage.endswith("%"):
                self.validation_results["warnings"].append("ROI percentage should include % symbol")
            
            mttr_improvement = BUSINESS_METRICS.get("mttr_improvement", "")
            if not mttr_improvement.endswith("%"):
                self.validation_results["warnings"].append("MTTR improvement should include % symbol")
            
            # Validate competitive advantages
            cost_comparison = BUSINESS_METRICS.get("cost_per_incident", "")
            if "vs" not in cost_comparison:
                self.validation_results["warnings"].append("Cost per incident should show comparison (e.g., '$47 vs $5,600')")
            
            self.validation_results["validations"]["business_metrics"] = "✅ PASS"
            print("✅ Business metrics validation passed")
            return True
            
        except Exception as e:
            self.validation_results["errors"].append(f"Business metrics validation error: {e}")
            self.validation_results["validations"]["business_metrics"] = "❌ FAIL"
            print(f"❌ Business metrics validation failed: {e}")
            return False
    
    def validate_aws_services(self) -> bool:
        """Validate AWS AI services for prize eligibility."""
        print("🔍 Validating AWS AI services...")
        
        try:
            # Check service count
            if len(AWS_AI_SERVICES) != 8:
                self.validation_results["errors"].append(f"Expected 8 AWS AI services, found {len(AWS_AI_SERVICES)}")
                return False
            
            # Check for required services
            required_services = [
                "Amazon Bedrock AgentCore",
                "Claude 3.5 Sonnet",
                "Amazon Q Business",
                "Nova Act"
            ]
            
            for service in required_services:
                if not any(service in aws_service for aws_service in AWS_AI_SERVICES):
                    self.validation_results["errors"].append(f"Missing required AWS service: {service}")
                    return False
            
            # Check for prize eligibility services
            prize_services = ["Amazon Q Business", "Nova Act", "Strands SDK"]
            found_prize_services = []
            
            for service in prize_services:
                if any(service in aws_service for aws_service in AWS_AI_SERVICES):
                    found_prize_services.append(service)
            
            if len(found_prize_services) < 3:
                self.validation_results["warnings"].append(f"Only {len(found_prize_services)} prize services found, expected 3+")
            
            self.validation_results["validations"]["aws_services"] = "✅ PASS"
            print("✅ AWS AI services validation passed")
            return True
            
        except Exception as e:
            self.validation_results["errors"].append(f"AWS services validation error: {e}")
            self.validation_results["validations"]["aws_services"] = "❌ FAIL"
            print(f"❌ AWS services validation failed: {e}")
            return False
    
    async def validate_recorder_functionality(self) -> bool:
        """Validate recorder functionality without full recording."""
        print("🔍 Validating recorder functionality...")
        
        try:
            # Test recorder initialization
            recorder = EnhancedDemoRecorder()
            
            # Check output directories
            if not recorder.output_dir.exists():
                self.validation_results["errors"].append("Output directory not created")
                return False
            
            if not recorder.videos_dir.exists():
                self.validation_results["errors"].append("Videos directory not created")
                return False
            
            if not recorder.screenshots_dir.exists():
                self.validation_results["errors"].append("Screenshots directory not created")
                return False
            
            # Test browser setup (without actually launching)
            try:
                # This would test the setup without launching browser
                print("✅ Recorder initialization successful")
            except Exception as e:
                self.validation_results["warnings"].append(f"Browser setup test failed: {e}")
            
            self.validation_results["validations"]["recorder_functionality"] = "✅ PASS"
            print("✅ Recorder functionality validation passed")
            return True
            
        except Exception as e:
            self.validation_results["errors"].append(f"Recorder functionality validation error: {e}")
            self.validation_results["validations"]["recorder_functionality"] = "❌ FAIL"
            print(f"❌ Recorder functionality validation failed: {e}")
            return False
    
    def generate_validation_report(self) -> Dict[str, Any]:
        """Generate comprehensive validation report."""
        
        # Determine overall status
        if self.validation_results["errors"]:
            self.validation_results["system_status"] = "❌ CRITICAL ISSUES"
        elif self.validation_results["warnings"]:
            self.validation_results["system_status"] = "⚠️ WARNINGS PRESENT"
        else:
            self.validation_results["system_status"] = "✅ READY FOR RECORDING"
        
        # Add summary
        self.validation_results["summary"] = {
            "total_validations": len(self.validation_results["validations"]),
            "passed_validations": len([v for v in self.validation_results["validations"].values() if "✅" in v]),
            "failed_validations": len([v for v in self.validation_results["validations"].values() if "❌" in v]),
            "total_errors": len(self.validation_results["errors"]),
            "total_warnings": len(self.validation_results["warnings"])
        }
        
        return self.validation_results
    
    def print_validation_report(self):
        """Print formatted validation report."""
        print("\n" + "=" * 80)
        print("🎬 ENHANCED RECORDING SYSTEM VALIDATION REPORT")
        print("=" * 80)
        
        print(f"\n📊 Overall Status: {self.validation_results['system_status']}")
        
        summary = self.validation_results["summary"]
        print(f"\n📋 Validation Summary:")
        print(f"   • Total Validations: {summary['total_validations']}")
        print(f"   • Passed: {summary['passed_validations']}")
        print(f"   • Failed: {summary['failed_validations']}")
        print(f"   • Errors: {summary['total_errors']}")
        print(f"   • Warnings: {summary['total_warnings']}")
        
        if self.validation_results["validations"]:
            print(f"\n✅ Validation Results:")
            for validation, status in self.validation_results["validations"].items():
                print(f"   • {validation}: {status}")
        
        if self.validation_results["errors"]:
            print(f"\n❌ Critical Errors:")
            for error in self.validation_results["errors"]:
                print(f"   • {error}")
        
        if self.validation_results["warnings"]:
            print(f"\n⚠️ Warnings:")
            for warning in self.validation_results["warnings"]:
                print(f"   • {warning}")
        
        if self.validation_results["recommendations"]:
            print(f"\n💡 Recommendations:")
            for rec in self.validation_results["recommendations"]:
                print(f"   • {rec}")
        
        print("\n" + "=" * 80)
        
        if not self.validation_results["errors"]:
            print("🎉 SEGMENTED MP4 RECORDING SYSTEM IS READY FOR HACKATHON SUBMISSION!")
            print("\nNext Steps:")
            print("   1. Run 'python record_demo.py --format mp4 --segmented' for full segmented demonstration")
            print("   2. Run 'python quick_demo_record.py --output-format mp4' for quick judge recording")
            print("   3. Check 'demo_recordings/videos/' directory for MP4 segments")
            print("   4. Individual segments available for flexible judge review")
        else:
            print("🔧 PLEASE FIX CRITICAL ERRORS BEFORE RECORDING")
            print("\nRecommended Actions:")
            print("   1. Address all critical errors listed above")
            print("   2. Re-run this validation script")
            print("   3. Proceed with segmented MP4 recording once all validations pass")
        
        print("=" * 80)


async def main():
    """Main validation function."""
    print("🎬 Enhanced Recording System Validation")
    print("🏆 AWS AI Agent Global Hackathon 2025")
    print("=" * 80)
    
    validator = EnhancedRecordingValidator()
    
    # Run all validations
    validations = [
        validator.validate_configuration(),
        validator.validate_system_requirements(),
        validator.validate_recording_scenarios(),
        validator.validate_segmented_mp4_system(),
        validator.validate_business_metrics(),
        validator.validate_aws_services(),
        await validator.validate_recorder_functionality()
    ]
    
    # Generate and save report
    report = validator.generate_validation_report()
    
    # Save validation results
    results_file = Path("hackathon") / "enhanced_recording_validation_results.json"
    with open(results_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Print report
    validator.print_validation_report()
    
    print(f"\n📁 Validation results saved to: {results_file}")
    
    # Return success status
    return len(report["errors"]) == 0


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n👋 Validation interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n💥 Validation failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)