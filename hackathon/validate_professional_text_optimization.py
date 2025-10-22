#!/usr/bin/env python3
"""
Validation script for Professional Text Optimization update
"""

import json
import os
from pathlib import Path
from datetime import datetime

def validate_professional_text_optimization():
    """Validate the professional text optimization implementation"""
    
    print("🔍 VALIDATING PROFESSIONAL TEXT OPTIMIZATION")
    print("=" * 60)
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "validation_type": "professional_text_optimization",
        "tests": [],
        "summary": {}
    }
    
    # Test 1: Dashboard Component Text Updates
    print("\n📝 Test 1: Dashboard Component Text Updates")
    dashboard_path = Path("dashboard/src/components/ImprovedOperationsDashboard.tsx")
    
    if dashboard_path.exists():
        content = dashboard_path.read_text()
        
        # Check for professional text optimization features
        professional_features = [
            "89% agent consensus achieved",
            "driving 95% faster resolution",
            "$2.8M cost savings",
            "99.97% uptime",
            "42 min → 6 min",
            "85.7% faster",
            "$5.6M → $275K",
            "95.1% savings",
            "Anomaly correlation across 143 telemetry signals",
            "Query plan regression isolated",
            "lock-wait accumulation detected",
            "Canary rollback validated",
            "Stakeholder updates synchronized"
        ]
        
        found_features = []
        for feature in professional_features:
            if feature in content:
                found_features.append(feature)
        
        test_result = {
            "test": "Dashboard Text Updates",
            "status": "PASS" if len(found_features) >= 10 else "PARTIAL",
            "details": f"Found {len(found_features)}/13 professional text features",
            "features_found": found_features
        }
        results["tests"].append(test_result)
        print(f"   ✅ {test_result['details']}")
    else:
        test_result = {
            "test": "Dashboard Text Updates", 
            "status": "FAIL",
            "details": "Dashboard component not found"
        }
        results["tests"].append(test_result)
        print("   ❌ Dashboard component not found")
    
    # Test 2: New Demo Recording Validation
    print("\n🎬 Test 2: New Demo Recording Validation")
    demo_recordings_path = Path("demo_recordings")
    
    if demo_recordings_path.exists():
        # Check for latest recording session
        videos_path = demo_recordings_path / "videos"
        screenshots_path = demo_recordings_path / "screenshots"
        metrics_path = demo_recordings_path / "metrics"
        
        latest_video = None
        latest_screenshots = []
        latest_metrics = None
        
        # Find latest video file
        if videos_path.exists():
            video_files = list(videos_path.glob("*.webm"))
            if video_files:
                latest_video = max(video_files, key=lambda x: x.stat().st_mtime)
        
        # Find latest screenshots
        if screenshots_path.exists():
            screenshot_files = list(screenshots_path.glob("*.png"))
            # Filter for recent screenshots (last 24 hours)
            recent_screenshots = [f for f in screenshot_files 
                                if (datetime.now().timestamp() - f.stat().st_mtime) < 86400]
            latest_screenshots = recent_screenshots
        
        # Find latest metrics
        if metrics_path.exists():
            metrics_files = list(metrics_path.glob("*20251022*.json"))
            if metrics_files:
                latest_metrics = max(metrics_files, key=lambda x: x.stat().st_mtime)
        
        recording_status = "COMPLETE" if (latest_video and len(latest_screenshots) >= 5 and latest_metrics) else "PARTIAL"
        
        test_result = {
            "test": "New Demo Recording",
            "status": recording_status,
            "details": f"Video: {'✅' if latest_video else '❌'}, Screenshots: {len(latest_screenshots)}, Metrics: {'✅' if latest_metrics else '❌'}",
            "latest_video": str(latest_video) if latest_video else None,
            "screenshot_count": len(latest_screenshots),
            "latest_metrics": str(latest_metrics) if latest_metrics else None
        }
        results["tests"].append(test_result)
        print(f"   {'✅' if recording_status == 'COMPLETE' else '⚠️'} {test_result['details']}")
    else:
        test_result = {
            "test": "New Demo Recording",
            "status": "FAIL", 
            "details": "Demo recordings directory not found"
        }
        results["tests"].append(test_result)
        print("   ❌ Demo recordings directory not found")
    
    # Test 2: Demo Recording Assets
    print("\n🎬 Test 2: Demo Recording Assets")
    demo_dir = Path("../demo_recordings")
    
    screenshots_dir = demo_dir / "screenshots"
    videos_dir = demo_dir / "videos"
    metrics_dir = demo_dir / "metrics"
    
    screenshot_count = len(list(screenshots_dir.glob("*.png"))) if screenshots_dir.exists() else 0
    video_count = len(list(videos_dir.glob("*.webm"))) if videos_dir.exists() else 0
    metrics_count = len(list(metrics_dir.glob("*20251022*.json"))) if metrics_dir.exists() else 0
    
    print(f"  📸 Screenshots: {screenshot_count}")
    print(f"  🎬 Videos: {video_count}")
    print(f"  📊 Metrics: {metrics_count}")
    
    recording_success = screenshot_count >= 8 and video_count >= 1 and metrics_count >= 1
    print(f"  {'✅' if recording_success else '❌'} Recording Assets: {'Complete' if recording_success else 'Incomplete'}")
    
    results["tests"].append({
        "name": "Demo Recording Assets",
        "screenshots": screenshot_count,
        "videos": video_count,
        "metrics": metrics_count,
        "success": recording_success
    })
    
    # Calculate overall results
    total_tests = len(results["tests"])
    successful_tests = sum(1 for test in results["tests"] if test.get("success", test.get("success_rate", 0) > 0.8))
    
    results["summary"] = {
        "total_tests": total_tests,
        "successful_tests": successful_tests,
        "success_rate": successful_tests / total_tests,
        "status": "PASS" if successful_tests / total_tests >= 0.8 else "FAIL"
    }
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 VALIDATION SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {total_tests}")
    print(f"Successful: {successful_tests}")
    print(f"Success Rate: {results['summary']['success_rate']:.1%}")
    print(f"Status: {'✅ PASS' if results['summary']['status'] == 'PASS' else '❌ FAIL'}")
    
    if results['summary']['status'] == 'PASS':
        print("\n🎉 Professional Text Optimization: COMPLETE AND VALIDATED")
        print("🏆 System ready for hackathon submission with enhanced presentation quality")
    else:
        print("\n⚠️  Some components need attention before submission")
    
    return results['summary']['status'] == 'PASS'

if __name__ == "__main__":
    success = validate_professional_text_optimization()
    exit(0 if success else 1)