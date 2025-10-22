#!/usr/bin/env python3
"""
Validate Latest Demo Sync - October 21, 2025
Ensures all hackathon demo files reference the latest recording session
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Tuple


class LatestDemoSyncValidator:
    """Validates that all demo files reference the latest recording session"""
    
    def __init__(self):
        self.latest_session = "20251022_093751"
        self.latest_video = "dc34a876ad0dda52ecffcaeb3faf502e.webm"
        self.latest_duration = "132.4"
        self.latest_screenshots = 20
        self.validation_results = []
        
    def validate_file_references(self, file_path: str, content: str) -> List[str]:
        """Validate that a file references the latest demo session"""
        issues = []
        
        # Check for outdated session references
        outdated_sessions = [
            "20251022_004834",  # Previous session
            "20251021_235144",  # Earlier session
            "20251021_222000",  # Earlier session
            "20251021_164724",  # Earlier session
        ]
        
        for session in outdated_sessions:
            if session in content and "ARCHIVED" not in content and "Previous Demo" not in content:
                issues.append(f"References outdated session {session} without proper archival marking")
        
        # Check for outdated video references
        outdated_videos = [
            "4d76376f8249437e5a422f3900f09892.webm",  # Previous video
            "00b6a99e232bc15389fff08c63a89189.webm",  # Earlier video
            "61f6efd11e2551303ffff60940c897f7.webm",  # Earlier video
        ]
        
        for video in outdated_videos:
            if video in content and "ARCHIVED" not in content:
                issues.append(f"References outdated video {video} without ARCHIVED note")
        
        # Check for outdated duration references
        if "150.6" in content and "132.4" not in content:
            issues.append("References outdated duration 150.6s without latest 132.4s")
        if "154.2" in content and "132.4" not in content:
            issues.append("References outdated duration 154.2s without latest 132.4s")
        if "155.8" in content and "132.4" not in content:
            issues.append("References outdated duration 155.8s without latest 132.4s")
        
        # Check for outdated screenshot count
        if "19 comprehensive" in content and "20 comprehensive" not in content:
            issues.append("References outdated screenshot count (19) without latest (20)")
        if "23 comprehensive" in content and "20 comprehensive" not in content:
            issues.append("References outdated screenshot count (23) without latest (20)")
        
        return issues
    
    def validate_demo_files(self) -> Dict[str, List[str]]:
        """Validate all demo-related files"""
        files_to_check = [
            "hackathon/README.md",
            "hackathon/MASTER_SUBMISSION_GUIDE.md",
            "hackathon/LATEST_DEMO_RECORDING_SUMMARY.md",
            "hackathon/docs/PHASE4_DEMO_SCRIPT.md",
            "hackathon/docs/HACKATHON_INDEX.md",
            "scripts/comprehensive_demo_recorder.py"
        ]
        
        results = {}
        
        for file_path in files_to_check:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                issues = self.validate_file_references(file_path, content)
                if issues:
                    results[file_path] = issues
                else:
                    results[file_path] = ["✅ All references up to date"]
            else:
                results[file_path] = ["❌ File not found"]
        
        return results
    
    def check_latest_demo_assets(self) -> Dict[str, str]:
        """Check if latest demo assets exist"""
        assets = {}
        
        # Check video file
        video_path = f"demo_recordings/videos/{self.latest_video}"
        assets["Latest Video"] = "✅ Found" if os.path.exists(video_path) else "❌ Missing"
        
        # Check screenshots directory
        screenshots_dir = Path("demo_recordings/screenshots")
        if screenshots_dir.exists():
            screenshot_files = list(screenshots_dir.glob("093*.png"))
            assets["Latest Screenshots"] = f"✅ Found {len(screenshot_files)} files" if screenshot_files else "❌ No 093xxx series found"
        else:
            assets["Latest Screenshots"] = "❌ Screenshots directory missing"
        
        # Check metrics file
        metrics_path = f"demo_recordings/metrics/enhanced_demo_v2_metrics_{self.latest_session}.json"
        assets["Latest Metrics"] = "✅ Found" if os.path.exists(metrics_path) else "❌ Missing"
        
        return assets
    
    def generate_validation_report(self) -> Dict:
        """Generate comprehensive validation report"""
        file_results = self.validate_demo_files()
        asset_results = self.check_latest_demo_assets()
        
        # Count issues
        total_files = len(file_results)
        files_with_issues = len([f for f, issues in file_results.items() if not any("✅" in issue for issue in issues)])
        
        report = {
            "validation_timestamp": "2025-10-21T23:52:00Z",
            "latest_session_id": self.latest_session,
            "latest_video_file": self.latest_video,
            "latest_duration_seconds": self.latest_duration,
            "latest_screenshot_count": self.latest_screenshots,
            "file_validation": {
                "total_files_checked": total_files,
                "files_with_issues": files_with_issues,
                "files_up_to_date": total_files - files_with_issues,
                "details": file_results
            },
            "asset_validation": asset_results,
            "overall_status": "✅ SYNC COMPLETE" if files_with_issues == 0 else f"⚠️ {files_with_issues} files need updates",
            "recommendations": self.generate_recommendations(file_results, asset_results)
        }
        
        return report
    
    def generate_recommendations(self, file_results: Dict, asset_results: Dict) -> List[str]:
        """Generate recommendations based on validation results"""
        recommendations = []
        
        # File update recommendations
        for file_path, issues in file_results.items():
            if not any("✅" in issue for issue in issues):
                recommendations.append(f"Update {file_path} to reference latest session {self.latest_session}")
        
        # Asset recommendations
        for asset, status in asset_results.items():
            if "❌" in status:
                recommendations.append(f"Ensure {asset} is available for judges")
        
        if not recommendations:
            recommendations.append("All demo files are synchronized with latest recording")
        
        return recommendations


def main():
    """Main validation function"""
    print("🔍 LATEST DEMO SYNC VALIDATION")
    print("=" * 50)
    
    validator = LatestDemoSyncValidator()
    report = validator.generate_validation_report()
    
    # Print summary
    print(f"📋 Session: {report['latest_session_id']}")
    print(f"🎥 Video: {report['latest_video_file']}")
    print(f"⏱️ Duration: {report['latest_duration_seconds']}s")
    print(f"📸 Screenshots: {report['latest_screenshot_count']}")
    print(f"📊 Status: {report['overall_status']}")
    print()
    
    # Print file validation results
    print("📁 FILE VALIDATION RESULTS:")
    for file_path, issues in report['file_validation']['details'].items():
        print(f"  {file_path}:")
        for issue in issues:
            print(f"    {issue}")
    print()
    
    # Print asset validation results
    print("📦 ASSET VALIDATION RESULTS:")
    for asset, status in report['asset_validation'].items():
        print(f"  {asset}: {status}")
    print()
    
    # Print recommendations
    if report['recommendations']:
        print("💡 RECOMMENDATIONS:")
        for rec in report['recommendations']:
            print(f"  • {rec}")
    
    # Save report
    report_path = "hackathon/latest_demo_sync_validation.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Full report saved to: {report_path}")
    
    # Return success/failure
    return report['file_validation']['files_with_issues'] == 0


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)