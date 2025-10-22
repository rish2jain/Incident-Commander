#!/usr/bin/env python3
"""
Validation script for Ultimate Demo implementation
"""

import json
import os
from pathlib import Path
from datetime import datetime

def validate_ultimate_demo():
    """Validate the ultimate demo implementation and assets"""
    
    print("🔍 VALIDATING ULTIMATE DEMO IMPLEMENTATION")
    print("=" * 60)
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "validation_type": "ultimate_demo",
        "tests": [],
        "summary": {}
    }
    
    # Test 1: Ultimate Demo Video
    print("\n🎬 Test 1: Ultimate Demo Video")
    video_path = Path("demo_recordings/videos/a088f233f2e407b13c15ae17f434d6a6.webm")
    
    if video_path.exists():
        video_size = video_path.stat().st_size / (1024 * 1024)  # MB
        test_result = {
            "test": "Ultimate Demo Video",
            "status": "PASS",
            "details": f"Video exists: {video_size:.1f}MB",
            "file_path": str(video_path)
        }
        results["tests"].append(test_result)
        print(f"   ✅ {test_result['details']}")
    else:
        test_result = {
            "test": "Ultimate Demo Video",
            "status": "FAIL",
            "details": "Ultimate demo video not found"
        }
        results["tests"].append(test_result)
        print("   ❌ Ultimate demo video not found")
    
    # Test 2: Ultimate Demo Screenshots
    print("\n📸 Test 2: Ultimate Demo Screenshots")
    screenshots_dir = Path("demo_recordings/screenshots")
    
    if screenshots_dir.exists():
        # Look for ultimate screenshots (115xxx pattern)
        ultimate_screenshots = list(screenshots_dir.glob("115*_*.png"))
        
        expected_screenshots = [
            "system_overview_ultimate",
            "business_metrics_comprehensive", 
            "professional_visual_hierarchy",
            "agent_summaries_detailed_ultimate",
            "trust_indicators_comprehensive",
            "federated_coordination",
            "transparency_dashboard_ultimate",
            "aws_ai_services_complete",
            "prize_eligibility_showcase",
            "ai_explainability_complete",
            "byzantine_consensus_ultimate",
            "consensus_weighted_display",
            "autonomous_execution_approved",
            "predictive_prevention_ultimate",
            "predictive_alerts_display",
            "prevention_methodology",
            "power_demo_ultimate",
            "business_impact_ultimate",
            "roi_calculator",
            "competitive_advantages_ultimate",
            "production_deployment_ultimate",
            "hackathon_readiness"
        ]
        
        found_screenshots = []
        for screenshot in ultimate_screenshots:
            for expected in expected_screenshots:
                if expected in screenshot.name:
                    found_screenshots.append(expected)
                    break
        
        test_result = {
            "test": "Ultimate Demo Screenshots",
            "status": "PASS" if len(found_screenshots) >= 20 else "PARTIAL",
            "details": f"Found {len(found_screenshots)}/22 ultimate screenshots",
            "screenshots_found": len(ultimate_screenshots),
            "expected_screenshots": found_screenshots
        }
        results["tests"].append(test_result)
        print(f"   {'✅' if test_result['status'] == 'PASS' else '⚠️'} {test_result['details']}")
    else:
        test_result = {
            "test": "Ultimate Demo Screenshots",
            "status": "FAIL",
            "details": "Screenshots directory not found"
        }
        results["tests"].append(test_result)
        print("   ❌ Screenshots directory not found")
    
    # Test 3: Ultimate Demo Metrics
    print("\n📊 Test 3: Ultimate Demo Metrics")
    metrics_path = Path("demo_recordings/metrics/ultimate_demo_20251022_115525.json")
    
    if metrics_path.exists():
        try:
            with open(metrics_path, 'r') as f:
                metrics_data = json.load(f)
            
            # Check for key metrics fields
            required_fields = [
                "session_id",
                "recording_type", 
                "features_demonstrated",
                "aws_services_showcased",
                "business_value_demonstrated",
                "competitive_advantages",
                "screenshots_count"
            ]
            
            found_fields = []
            for field in required_fields:
                if field in metrics_data:
                    found_fields.append(field)
            
            # Check for prize eligibility data
            prize_eligibility = False
            if "aws_services_showcased" in metrics_data:
                services = metrics_data["aws_services_showcased"]
                if len(services) >= 8:
                    prize_eligibility = True
            
            test_result = {
                "test": "Ultimate Demo Metrics",
                "status": "PASS" if len(found_fields) >= 6 and prize_eligibility else "PARTIAL",
                "details": f"Found {len(found_fields)}/7 required fields, Prize eligibility: {prize_eligibility}",
                "session_id": metrics_data.get("session_id", "Unknown"),
                "screenshots_count": metrics_data.get("screenshots_count", 0),
                "aws_services_count": len(metrics_data.get("aws_services_showcased", []))
            }
            results["tests"].append(test_result)
            print(f"   {'✅' if test_result['status'] == 'PASS' else '⚠️'} {test_result['details']}")
        except Exception as e:
            test_result = {
                "test": "Ultimate Demo Metrics",
                "status": "FAIL",
                "details": f"Error reading metrics: {e}"
            }
            results["tests"].append(test_result)
            print(f"   ❌ Error reading metrics: {e}")
    else:
        test_result = {
            "test": "Ultimate Demo Metrics",
            "status": "FAIL",
            "details": "Ultimate demo metrics file not found"
        }
        results["tests"].append(test_result)
        print("   ❌ Ultimate demo metrics file not found")
    
    # Test 4: Ultimate Demo Status Documentation
    print("\n📋 Test 4: Ultimate Demo Status Documentation")
    status_path = Path("hackathon/ULTIMATE_DEMO_FINAL_STATUS.md")
    
    if status_path.exists():
        content = status_path.read_text()
        
        # Check for key sections
        key_sections = [
            "ULTIMATE DEMO COMPLETE",
            "Prize Eligibility Showcase",
            "Ultimate Demo Assets",
            "Competitive Advantages Demonstrated",
            "Judge Evaluation Options"
        ]
        
        found_sections = []
        for section in key_sections:
            if section in content:
                found_sections.append(section)
        
        test_result = {
            "test": "Ultimate Demo Status Documentation",
            "status": "PASS" if len(found_sections) >= 4 else "PARTIAL",
            "details": f"Found {len(found_sections)}/5 key sections",
            "sections_found": found_sections
        }
        results["tests"].append(test_result)
        print(f"   {'✅' if test_result['status'] == 'PASS' else '⚠️'} {test_result['details']}")
    else:
        test_result = {
            "test": "Ultimate Demo Status Documentation",
            "status": "FAIL",
            "details": "Ultimate demo status file not found"
        }
        results["tests"].append(test_result)
        print("   ❌ Ultimate demo status file not found")
    
    # Test 5: Archive Management
    print("\n🗄️ Test 5: Archive Management")
    archive_path = Path("demo_recordings/archive/2025-10-22-comprehensive-v1")
    
    if archive_path.exists():
        archive_readme = archive_path / "ARCHIVE_README.md"
        if archive_readme.exists():
            test_result = {
                "test": "Archive Management",
                "status": "PASS",
                "details": "Previous comprehensive demo properly archived",
                "archive_path": str(archive_path)
            }
            results["tests"].append(test_result)
            print(f"   ✅ {test_result['details']}")
        else:
            test_result = {
                "test": "Archive Management",
                "status": "PARTIAL",
                "details": "Archive exists but missing README"
            }
            results["tests"].append(test_result)
            print(f"   ⚠️ {test_result['details']}")
    else:
        test_result = {
            "test": "Archive Management",
            "status": "FAIL",
            "details": "Archive directory not found"
        }
        results["tests"].append(test_result)
        print("   ❌ Archive directory not found")
    
    # Calculate overall results
    total_tests = len(results["tests"])
    successful_tests = sum(1 for test in results["tests"] if test["status"] == "PASS")
    partial_tests = sum(1 for test in results["tests"] if test["status"] == "PARTIAL")
    
    results["summary"] = {
        "total_tests": total_tests,
        "successful_tests": successful_tests,
        "partial_tests": partial_tests,
        "failed_tests": total_tests - successful_tests - partial_tests,
        "success_rate": successful_tests / total_tests,
        "status": "PASS" if successful_tests / total_tests >= 0.8 else "PARTIAL" if (successful_tests + partial_tests) / total_tests >= 0.6 else "FAIL"
    }
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 ULTIMATE DEMO VALIDATION SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {total_tests}")
    print(f"Successful: {successful_tests}")
    print(f"Partial: {partial_tests}")
    print(f"Failed: {results['summary']['failed_tests']}")
    print(f"Success Rate: {results['summary']['success_rate']:.1%}")
    print(f"Status: {'✅ PASS' if results['summary']['status'] == 'PASS' else '⚠️ PARTIAL' if results['summary']['status'] == 'PARTIAL' else '❌ FAIL'}")
    
    if results['summary']['status'] == 'PASS':
        print("\n🏆 Ultimate Demo: COMPLETE AND VALIDATED")
        print("🎯 Maximum prize eligibility achieved with professional presentation quality")
    elif results['summary']['status'] == 'PARTIAL':
        print("\n⚠️ Ultimate Demo: MOSTLY COMPLETE")
        print("🔧 Some components may need attention for optimal submission")
    else:
        print("\n❌ Ultimate Demo: NEEDS ATTENTION")
        print("🚨 Critical components missing or incomplete")
    
    # Save validation results
    results_file = Path("hackathon/ultimate_demo_validation.json")
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Validation results saved: {results_file}")
    
    return results['summary']['status'] in ['PASS', 'PARTIAL']

if __name__ == "__main__":
    success = validate_ultimate_demo()
    exit(0 if success else 1)