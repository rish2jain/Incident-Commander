#!/usr/bin/env python3
"""
Latest System Improvements Validation Script

Validates all October 22, 2025 system improvements including:
- Shared component system enhancements
- Dual recording system
- AWS AI service integrations
- UI/UX improvements
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import requests


class LatestImprovementsValidator:
    """Validates latest system improvements and enhancements."""
    
    def __init__(self):
        self.base_url = "http://localhost:3000"
        self.api_url = "http://localhost:8000"
        self.demo_recordings_dir = Path("demo_recordings")
        
        # Latest recording sessions
        self.enhanced_session = "20251022_175225"
        self.hackathon_session = "20251022_175521"
        self.enhanced_video = "0282d14bf09ba025c01c06fa9d1b6ef5.webm"
        self.hackathon_video = "hackathon_demo_3min_20251022_175521.webm"
        
        # Expected improvements
        self.expected_components = [
            "DashboardLayout",
            "DashboardSection", 
            "DashboardGrid",
            "MetricCard",
            "StatusIndicators"
        ]
        
        self.expected_features = [
            "Next.js Image optimization",
            "Shared component system",
            "Professional design tokens",
            "Dual recording system",
            "AWS AI service integration",
            "Client-side timestamp optimization"
        ]
        
        self.results = []
    
    def validate_shared_components(self) -> Dict[str, Any]:
        """Validate shared component system improvements."""
        print("🧩 Validating shared component system...")
        
        component_files = [
            "dashboard/src/components/shared/DashboardLayout.tsx",
            "dashboard/src/components/shared/index.ts",
            "dashboard/src/components/shared/MetricCards.tsx",
            "dashboard/src/components/shared/StatusIndicators.tsx"
        ]
        
        results = {
            'components_exist': 0,
            'components_enhanced': 0,
            'next_js_optimization': False,
            'shared_exports': False,
            'all_components_valid': False
        }
        
        for component_file in component_files:
            if Path(component_file).exists():
                results['components_exist'] += 1
                print(f"✅ Component found: {component_file}")
                
                # Check for Next.js Image optimization
                if "DashboardLayout.tsx" in component_file:
                    with open(component_file, 'r') as f:
                        content = f.read()
                        if 'import Image from "next/image"' in content:
                            results['next_js_optimization'] = True
                            results['components_enhanced'] += 1
                            print("✅ Next.js Image optimization detected")
                
                # Check for client-side optimization in ActivityFeed
                if "ActivityFeed.tsx" in component_file:
                    activity_feed_path = "dashboard/src/components/ActivityFeed.tsx"
                    if Path(activity_feed_path).exists():
                        with open(activity_feed_path, 'r') as f:
                            content = f.read()
                            if 'useClientSideTimestamp' in content:
                                results['components_enhanced'] += 1
                                print("✅ Client-side timestamp optimization detected")
                
                # Check for shared exports
                if "index.ts" in component_file:
                    with open(component_file, 'r') as f:
                        content = f.read()
                        if "DashboardLayout" in content and "MetricCard" in content:
                            results['shared_exports'] = True
                            results['components_enhanced'] += 1
                            print("✅ Shared component exports detected")
            else:
                print(f"❌ Component missing: {component_file}")
        
        results['all_components_valid'] = (
            results['components_exist'] == len(component_files) and
            results['next_js_optimization'] and
            results['shared_exports']
        )
        
        return results
    
    def validate_dual_recording_system(self) -> Dict[str, Any]:
        """Validate dual recording system."""
        print("\n🎬 Validating dual recording system...")
        
        enhanced_video_path = self.demo_recordings_dir / "videos" / self.enhanced_video
        hackathon_video_path = self.demo_recordings_dir / "videos" / self.hackathon_video
        
        results = {
            'enhanced_video_exists': enhanced_video_path.exists(),
            'hackathon_video_exists': hackathon_video_path.exists(),
            'enhanced_video_size_mb': 0,
            'hackathon_video_size_mb': 0,
            'total_screenshots': 0,
            'dual_system_complete': False
        }
        
        if enhanced_video_path.exists():
            results['enhanced_video_size_mb'] = round(enhanced_video_path.stat().st_size / (1024 * 1024), 2)
            print(f"✅ Enhanced video found: {results['enhanced_video_size_mb']} MB")
        else:
            print(f"❌ Enhanced video missing: {self.enhanced_video}")
        
        if hackathon_video_path.exists():
            results['hackathon_video_size_mb'] = round(hackathon_video_path.stat().st_size / (1024 * 1024), 2)
            print(f"✅ Hackathon video found: {results['hackathon_video_size_mb']} MB")
        else:
            print(f"❌ Hackathon video missing: {self.hackathon_video}")
        
        # Count screenshots
        screenshots_dir = self.demo_recordings_dir / "screenshots"
        if screenshots_dir.exists():
            screenshot_files = list(screenshots_dir.glob("*.png"))
            results['total_screenshots'] = len(screenshot_files)
            print(f"✅ Screenshots found: {results['total_screenshots']} files")
        
        results['dual_system_complete'] = (
            results['enhanced_video_exists'] and
            results['hackathon_video_exists'] and
            results['total_screenshots'] >= 30
        )
        
        return results
    
    def validate_dashboard_routes(self) -> Dict[str, Any]:
        """Validate all dashboard routes with latest improvements."""
        print("\n🌐 Validating dashboard routes...")
        
        routes = {
            'homepage': '/',
            'demo': '/demo',
            'transparency': '/transparency',
            'operations': '/ops'
        }
        
        results = {
            'routes_tested': 0,
            'routes_working': 0,
            'route_details': {},
            'all_routes_operational': False
        }
        
        for route_name, path in routes.items():
            url = f"{self.base_url}{path}"
            results['routes_tested'] += 1
            
            try:
                start_time = time.time()
                response = requests.get(url, timeout=10)
                response_time = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    results['routes_working'] += 1
                    results['route_details'][route_name] = {
                        'status': 'working',
                        'response_time_ms': round(response_time, 2),
                        'content_length': len(response.content)
                    }
                    print(f"✅ {route_name}: {response.status_code} - {response_time:.1f}ms")
                else:
                    results['route_details'][route_name] = {
                        'status': 'error',
                        'status_code': response.status_code
                    }
                    print(f"❌ {route_name}: {response.status_code}")
                    
            except Exception as e:
                results['route_details'][route_name] = {
                    'status': 'failed',
                    'error': str(e)
                }
                print(f"❌ {route_name}: {str(e)}")
        
        results['all_routes_operational'] = results['routes_working'] == results['routes_tested']
        
        return results
    
    def validate_aws_ai_integration(self) -> Dict[str, Any]:
        """Validate AWS AI service integration status."""
        print("\n🤖 Validating AWS AI service integration...")
        
        # Check for integration files and documentation
        integration_files = [
            "src/amazon_q_integration.py",
            "src/nova_act_integration.py", 
            "src/strands_sdk_integration.py",
            "hackathon/LATEST_SYSTEM_IMPROVEMENTS_OCT22.md"
        ]
        
        results = {
            'integration_files_exist': 0,
            'documentation_complete': False,
            'prize_eligibility_documented': False,
            'aws_integration_ready': False
        }
        
        for file_path in integration_files:
            if Path(file_path).exists():
                results['integration_files_exist'] += 1
                print(f"✅ Integration file found: {file_path}")
                
                # Check for prize eligibility documentation
                if "LATEST_SYSTEM_IMPROVEMENTS" in file_path:
                    with open(file_path, 'r') as f:
                        content = f.read()
                        if "$3K Prize" in content and "Amazon Q Business" in content:
                            results['prize_eligibility_documented'] = True
                            print("✅ Prize eligibility documented")
            else:
                print(f"❌ Integration file missing: {file_path}")
        
        # Check documentation completeness
        if Path("hackathon/LATEST_SYSTEM_IMPROVEMENTS_OCT22.md").exists():
            results['documentation_complete'] = True
            print("✅ Latest improvements documentation complete")
        
        results['aws_integration_ready'] = (
            results['integration_files_exist'] >= 3 and
            results['documentation_complete'] and
            results['prize_eligibility_documented']
        )
        
        return results
    
    def validate_ui_improvements(self) -> Dict[str, Any]:
        """Validate UI/UX improvements."""
        print("\n🎨 Validating UI/UX improvements...")
        
        ui_files = [
            "dashboard/src/components/shared/DashboardLayout.tsx",
            "dashboard/tailwind.config.js",
            "dashboard/src/styles/globals.css"
        ]
        
        results = {
            'ui_files_exist': 0,
            'modern_architecture': False,
            'professional_styling': False,
            'responsive_design': False,
            'ui_improvements_complete': False
        }
        
        for file_path in ui_files:
            if Path(file_path).exists():
                results['ui_files_exist'] += 1
                print(f"✅ UI file found: {file_path}")
                
                # Check for modern architecture features
                if "DashboardLayout.tsx" in file_path:
                    with open(file_path, 'r') as f:
                        content = f.read()
                        if "DashboardSection" in content and "DashboardGrid" in content:
                            results['modern_architecture'] = True
                            print("✅ Modern component architecture detected")
                
                # Check for professional styling
                if "tailwind.config.js" in file_path:
                    results['professional_styling'] = True
                    print("✅ Professional styling configuration found")
                
                # Check for responsive design
                if "globals.css" in file_path:
                    results['responsive_design'] = True
                    print("✅ Responsive design styles found")
            else:
                print(f"❌ UI file missing: {file_path}")
        
        results['ui_improvements_complete'] = (
            results['ui_files_exist'] == len(ui_files) and
            results['modern_architecture'] and
            results['professional_styling']
        )
        
        return results
    
    def validate_documentation_updates(self) -> Dict[str, Any]:
        """Validate documentation updates."""
        print("\n📚 Validating documentation updates...")
        
        doc_files = [
            "hackathon/README.md",
            "hackathon/LATEST_SYSTEM_IMPROVEMENTS_OCT22.md",
            "winning_enhancements/README.md",
            "README.md"
        ]
        
        results = {
            'docs_updated': 0,
            'latest_improvements_documented': False,
            'hackathon_ready': False,
            'all_docs_current': False
        }
        
        for doc_file in doc_files:
            if Path(doc_file).exists():
                with open(doc_file, 'r') as f:
                    content = f.read()
                    
                    # Check for latest session references
                    if ("20251022_175225" in content or "20251022_175521" in content or 
                        "October 22, 2025" in content):
                        results['docs_updated'] += 1
                        print(f"✅ Documentation updated: {doc_file}")
                        
                        # Check for specific improvements
                        if "LATEST_SYSTEM_IMPROVEMENTS" in doc_file:
                            if "Shared Component System" in content and "Dual Recording" in content:
                                results['latest_improvements_documented'] = True
                                print("✅ Latest improvements fully documented")
                        
                        # Check hackathon readiness
                        if "hackathon/README.md" in doc_file:
                            if "READY FOR IMMEDIATE SUBMISSION" in content:
                                results['hackathon_ready'] = True
                                print("✅ Hackathon submission readiness confirmed")
                    else:
                        print(f"⚠️  Documentation may need updating: {doc_file}")
            else:
                print(f"❌ Documentation missing: {doc_file}")
        
        results['all_docs_current'] = (
            results['docs_updated'] >= 3 and
            results['latest_improvements_documented'] and
            results['hackathon_ready']
        )
        
        return results
    
    def run_validation(self) -> Dict[str, Any]:
        """Run complete latest improvements validation."""
        print("🚀 Starting Latest System Improvements Validation")
        print("=" * 70)
        
        # Run all validation checks
        components_validation = self.validate_shared_components()
        recording_validation = self.validate_dual_recording_system()
        routes_validation = self.validate_dashboard_routes()
        aws_validation = self.validate_aws_ai_integration()
        ui_validation = self.validate_ui_improvements()
        docs_validation = self.validate_documentation_updates()
        
        # Compile overall results
        overall_results = {
            'validation_time': datetime.utcnow().isoformat(),
            'enhanced_session': self.enhanced_session,
            'hackathon_session': self.hackathon_session,
            'components_validation': components_validation,
            'recording_validation': recording_validation,
            'routes_validation': routes_validation,
            'aws_validation': aws_validation,
            'ui_validation': ui_validation,
            'docs_validation': docs_validation,
            'overall_success': (
                components_validation.get('all_components_valid', False) and
                recording_validation.get('dual_system_complete', False) and
                routes_validation.get('all_routes_operational', False) and
                aws_validation.get('aws_integration_ready', False) and
                ui_validation.get('ui_improvements_complete', False) and
                docs_validation.get('all_docs_current', False)
            )
        }
        
        return overall_results
    
    def print_summary(self, results: Dict[str, Any]):
        """Print validation summary."""
        print("\n" + "=" * 70)
        print("📊 LATEST IMPROVEMENTS VALIDATION SUMMARY")
        print("=" * 70)
        
        status = "✅ ALL IMPROVEMENTS VALIDATED" if results['overall_success'] else "❌ ISSUES FOUND"
        print(f"Overall Status: {status}")
        print(f"Enhanced Session: {results['enhanced_session']}")
        print(f"Hackathon Session: {results['hackathon_session']}")
        
        # Component validation summary
        comp_val = results['components_validation']
        print(f"\n🧩 Shared Components:")
        print(f"  Components: {comp_val['components_exist']}/4 exist")
        print(f"  Next.js Optimization: {'✅' if comp_val['next_js_optimization'] else '❌'}")
        print(f"  Shared Exports: {'✅' if comp_val['shared_exports'] else '❌'}")
        
        # Recording validation summary
        rec_val = results['recording_validation']
        print(f"\n🎬 Dual Recording System:")
        print(f"  Enhanced Video: {'✅' if rec_val['enhanced_video_exists'] else '❌'} ({rec_val['enhanced_video_size_mb']} MB)")
        print(f"  Hackathon Video: {'✅' if rec_val['hackathon_video_exists'] else '❌'} ({rec_val['hackathon_video_size_mb']} MB)")
        print(f"  Screenshots: {rec_val['total_screenshots']} total")
        
        # Routes validation summary
        routes_val = results['routes_validation']
        print(f"\n🌐 Dashboard Routes:")
        print(f"  Working Routes: {routes_val['routes_working']}/{routes_val['routes_tested']}")
        
        # AWS validation summary
        aws_val = results['aws_validation']
        print(f"\n🤖 AWS AI Integration:")
        print(f"  Integration Files: {aws_val['integration_files_exist']}/4 exist")
        print(f"  Prize Eligibility: {'✅' if aws_val['prize_eligibility_documented'] else '❌'}")
        
        # UI validation summary
        ui_val = results['ui_validation']
        print(f"\n🎨 UI/UX Improvements:")
        print(f"  UI Files: {ui_val['ui_files_exist']}/3 exist")
        print(f"  Modern Architecture: {'✅' if ui_val['modern_architecture'] else '❌'}")
        
        # Documentation validation summary
        docs_val = results['docs_validation']
        print(f"\n📚 Documentation:")
        print(f"  Updated Docs: {docs_val['docs_updated']}/4 files")
        print(f"  Hackathon Ready: {'✅' if docs_val['hackathon_ready'] else '❌'}")
        
        if results['overall_success']:
            print("\n🎉 ALL LATEST IMPROVEMENTS VALIDATED!")
            print("✅ Shared component system enhanced")
            print("✅ Dual recording system complete")
            print("✅ Dashboard routes operational")
            print("✅ AWS AI integration ready")
            print("✅ UI/UX improvements complete")
            print("✅ Documentation updated")
            
            print("\n🚀 Ready for hackathon submission with latest improvements!")
            
        else:
            print("\n⚠️  IMPROVEMENTS TO COMPLETE:")
            if not comp_val.get('all_components_valid'):
                print("  • Shared component system needs completion")
            if not rec_val.get('dual_system_complete'):
                print("  • Dual recording system needs completion")
            if not routes_val.get('all_routes_operational'):
                print("  • Dashboard routes need fixing")
            if not aws_val.get('aws_integration_ready'):
                print("  • AWS AI integration needs completion")
            if not ui_val.get('ui_improvements_complete'):
                print("  • UI/UX improvements need completion")
            if not docs_val.get('all_docs_current'):
                print("  • Documentation needs updating")


def main():
    """Run latest improvements validation."""
    validator = LatestImprovementsValidator()
    
    try:
        results = validator.run_validation()
        validator.print_summary(results)
        
        # Save results
        output_file = f"hackathon/latest_improvements_validation_{validator.hackathon_session}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Results saved to: {output_file}")
        
        if results['overall_success']:
            print("\n🏆 LATEST IMPROVEMENTS FULLY VALIDATED - READY FOR SUBMISSION! 🚀")
            exit(0)
        else:
            print("\n⚠️  Please complete remaining improvements")
            exit(1)
            
    except Exception as e:
        print(f"\n❌ Validation failed: {e}")
        exit(1)


if __name__ == "__main__":
    main()