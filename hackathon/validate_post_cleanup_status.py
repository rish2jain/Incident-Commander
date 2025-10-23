#!/usr/bin/env python3
"""
Post-Cleanup System Validation
Validates system status after October 2025 repository cleanup
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

def validate_archive_structure():
    """Validate archive cleanup structure"""
    print("🔍 Validating Archive Structure...")
    
    archive_path = Path("archive/october_2025_cleanup")
    if not archive_path.exists():
        print("❌ Archive cleanup directory not found")
        return False
    
    readme_path = archive_path / "README.md"
    if not readme_path.exists():
        print("❌ Archive README.md not found")
        return False
    
    print("✅ Archive structure validated")
    return True

def validate_demo_assets():
    """Validate demo recording assets"""
    print("🔍 Validating Demo Assets...")
    
    demo_path = Path("demo_recordings")
    if not demo_path.exists():
        print("❌ Demo recordings directory not found")
        return False
    
    # Check for latest recordings
    videos_path = demo_path / "videos"
    expected_videos = [
        "0282d14bf09ba025c01c06fa9d1b6ef5.webm",  # Enhanced Demo V2
        "hackathon_demo_3min_20251022_175521.webm"  # Hackathon Demo
    ]
    
    missing_videos = []
    for video in expected_videos:
        if not (videos_path / video).exists():
            missing_videos.append(video)
    
    if missing_videos:
        print(f"⚠️  Missing videos: {missing_videos}")
    else:
        print("✅ Demo videos validated")
    
    # Check screenshots
    screenshots_path = demo_path / "screenshots"
    if screenshots_path.exists():
        screenshot_count = len(list(screenshots_path.glob("*.png")))
        print(f"✅ Screenshots available: {screenshot_count}")
    
    return len(missing_videos) == 0

def validate_hackathon_docs():
    """Validate hackathon documentation is current"""
    print("🔍 Validating Hackathon Documentation...")
    
    hackathon_path = Path("hackathon")
    key_docs = [
        "README.md",
        "MASTER_SUBMISSION_GUIDE.md",
        "CURRENT_SYSTEM_STATUS_OCTOBER_22.md"
    ]
    
    missing_docs = []
    for doc in key_docs:
        doc_path = hackathon_path / doc
        if not doc_path.exists():
            missing_docs.append(doc)
        else:
            # Check if updated recently (within last day)
            stat = doc_path.stat()
            age_hours = (datetime.now().timestamp() - stat.st_mtime) / 3600
            if age_hours > 24:
                print(f"⚠️  {doc} may need updating (last modified {age_hours:.1f} hours ago)")
    
    if missing_docs:
        print(f"❌ Missing documentation: {missing_docs}")
        return False
    
    print("✅ Hackathon documentation validated")
    return True

def validate_live_endpoints():
    """Validate live AWS endpoints are documented"""
    print("🔍 Validating Live Endpoint Documentation...")
    
    # Check if endpoint is documented in hackathon files
    hackathon_readme = Path("hackathon/README.md")
    if hackathon_readme.exists():
        content = hackathon_readme.read_text()
        if "h8xlzr74h8.execute-api.us-east-1.amazonaws.com" in content:
            print("✅ Live AWS endpoint documented")
            return True
    
    print("⚠️  Live AWS endpoint may not be properly documented")
    return False

def validate_dashboard_structure():
    """Validate dashboard structure is current"""
    print("🔍 Validating Dashboard Structure...")
    
    dashboard_path = Path("dashboard")
    if not dashboard_path.exists():
        print("❌ Dashboard directory not found")
        return False
    
    # Check for key dashboard files
    key_files = [
        "package.json",
        "next.config.js",
        "app/page.tsx"
    ]
    
    missing_files = []
    for file in key_files:
        if not (dashboard_path / file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing dashboard files: {missing_files}")
        return False
    
    print("✅ Dashboard structure validated")
    return True

def generate_validation_report():
    """Generate comprehensive validation report"""
    print("\n" + "="*60)
    print("🏆 POST-CLEANUP SYSTEM VALIDATION REPORT")
    print("="*60)
    
    validations = [
        ("Archive Structure", validate_archive_structure),
        ("Demo Assets", validate_demo_assets),
        ("Hackathon Documentation", validate_hackathon_docs),
        ("Live Endpoints", validate_live_endpoints),
        ("Dashboard Structure", validate_dashboard_structure)
    ]
    
    results = {}
    total_score = 0
    
    for name, validator in validations:
        print(f"\n📋 {name}")
        print("-" * 40)
        result = validator()
        results[name] = result
        if result:
            total_score += 1
    
    # Calculate overall score
    overall_score = (total_score / len(validations)) * 100
    
    print("\n" + "="*60)
    print("📊 VALIDATION SUMMARY")
    print("="*60)
    
    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name:<25} {status}")
    
    print(f"\n🎯 Overall Score: {overall_score:.1f}% ({total_score}/{len(validations)})")
    
    if overall_score >= 80:
        print("🏆 STATUS: READY FOR HACKATHON SUBMISSION")
    elif overall_score >= 60:
        print("⚠️  STATUS: MINOR ISSUES - REVIEW RECOMMENDED")
    else:
        print("❌ STATUS: MAJOR ISSUES - FIXES REQUIRED")
    
    # Save results
    report = {
        "timestamp": datetime.now().isoformat(),
        "validation_results": results,
        "overall_score": overall_score,
        "total_validations": len(validations),
        "passed_validations": total_score,
        "status": "READY" if overall_score >= 80 else "NEEDS_REVIEW"
    }
    
    report_path = Path("hackathon/post_cleanup_validation_results.json")
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: {report_path}")
    
    return overall_score >= 80

if __name__ == "__main__":
    success = generate_validation_report()
    sys.exit(0 if success else 1)