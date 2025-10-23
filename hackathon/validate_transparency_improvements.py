#!/usr/bin/env python3
"""
Transparency Improvements Validation Script

Validates that the latest transparency improvements are properly implemented:
- Mock data labeling in PowerDashboard
- Honest data presentation
- Clear sourcing methodology
- Judge trust maintenance features
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

try:
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
    import requests
except ImportError:
    print("❌ Required packages not installed.")
    print("   To install, run:")
    print("   pip install playwright requests")
    print("   playwright install")
    proceed = input("Install now? (yes/no): ").strip().lower()
    if proceed in ('yes', 'y'):
        import subprocess
        try:
            subprocess.run(["pip", "install", "playwright", "requests"], check=True)
            subprocess.run(["playwright", "install"], check=True)
            from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
            import requests
        except subprocess.CalledProcessError as e:
            print(f"❌ Installation failed: {e}")
            print("   Please install manually using the commands above.")
            sys.exit(1)
    else:
        print("Installation declined. Exiting.")
        sys.exit(1)

# Configuration
DASHBOARD_URL = "http://localhost:3000"
VALIDATION_CONFIG = {
    "timeout": 10000,
    "screenshot_dir": Path("validation_screenshots"),
    "report_file": "transparency_validation_report.json"
}

class TransparencyValidator:
    """Validates transparency improvements in the demo system."""
    
    def __init__(self):
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.validation_results = []
        self.screenshot_count = 0
        
        # Create output directory
        VALIDATION_CONFIG["screenshot_dir"].mkdir(exist_ok=True)
        
        print(f"🔍 Transparency Improvements Validator - Session: {self.session_id}")
        print("=" * 70)
    
    async def validate_mock_labeling(self, page):
        """Validate that mock data is properly labeled."""
        print("🏷️  Validating mock data labeling...")
        
        try:
            # Navigate to PowerDashboard
            await page.goto(f"{DASHBOARD_URL}/demo")
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(3)
            
            # Check for mock labels in live metrics
            mock_labels = [
                "Incidents Resolved Today (mock)",
                "Average Resolution (mock)", 
                "Zero-Touch Streak: 47 (mock)",
                "Multi-Agent Status (Mock)"
            ]
            
            found_labels = []
            missing_labels = []
            
            for label in mock_labels:
                try:
                    element = await page.wait_for_selector(f"text={label}", timeout=5000)
                    if element:
                        found_labels.append(label)
                        print(f"   ✅ Found mock label: {label}")
                    else:
                        missing_labels.append(label)
                        print(f"   ❌ Missing mock label: {label}")
                except PlaywrightTimeoutError:
                    missing_labels.append(label)
                    print(f"   ❌ Missing mock label: {label}")
            
            # Take screenshot
            screenshot_path = VALIDATION_CONFIG["screenshot_dir"] / f"mock_labeling_{self.session_id}.png"
            await page.screenshot(path=str(screenshot_path), full_page=True)
            self.screenshot_count += 1
            
            result = {
                "test": "mock_data_labeling",
                "status": "PASS" if len(missing_labels) == 0 else "FAIL",
                "found_labels": found_labels,
                "missing_labels": missing_labels,
                "screenshot": str(screenshot_path),
                "timestamp": datetime.now().isoformat()
            }
            
            self.validation_results.append(result)
            
            if missing_labels:
                print(f"   ❌ Mock labeling validation FAILED - {len(missing_labels)} labels missing")
                return False
            else:
                print(f"   ✅ Mock labeling validation PASSED - All {len(found_labels)} labels found")
                return True
                
        except Exception as e:
            print(f"   ❌ Mock labeling validation ERROR: {e}")
            result = {
                "test": "mock_data_labeling",
                "status": "ERROR",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            self.validation_results.append(result)
            return False
    
    async def validate_transparency_messaging(self, page):
        """Validate transparency messaging throughout the interface."""
        print("💬 Validating transparency messaging...")
        
        try:
            # Check for transparency-related text
            transparency_indicators = [
                "mock",
                "demo data",
                "projected",
                "benchmark",
                "simulation"
            ]
            
            page_content = await page.content()
            found_indicators = []
            
            for indicator in transparency_indicators:
                if indicator.lower() in page_content.lower():
                    found_indicators.append(indicator)
                    print(f"   ✅ Found transparency indicator: {indicator}")
            
            # Take screenshot
            screenshot_path = VALIDATION_CONFIG["screenshot_dir"] / f"transparency_messaging_{self.session_id}.png"
            await page.screenshot(path=str(screenshot_path), full_page=True)
            self.screenshot_count += 1
            
            result = {
                "test": "transparency_messaging",
                "status": "PASS" if len(found_indicators) > 0 else "FAIL",
                "found_indicators": found_indicators,
                "total_indicators": len(transparency_indicators),
                "screenshot": str(screenshot_path),
                "timestamp": datetime.now().isoformat()
            }
            
            self.validation_results.append(result)
            
            if len(found_indicators) > 0:
                print(f"   ✅ Transparency messaging validation PASSED - {len(found_indicators)} indicators found")
                return True
            else:
                print(f"   ❌ Transparency messaging validation FAILED - No transparency indicators found")
                return False
                
        except Exception as e:
            print(f"   ❌ Transparency messaging validation ERROR: {e}")
            result = {
                "test": "transparency_messaging",
                "status": "ERROR",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            self.validation_results.append(result)
            return False
    
    async def validate_honest_presentation(self, page):
        """Validate honest data presentation practices."""
        print("🎯 Validating honest presentation practices...")
        
        try:
            # Navigate to different dashboard sections
            sections = [
                {"url": "/demo", "name": "PowerDashboard"},
                {"url": "/transparency", "name": "Transparency"},
                {"url": "/ops", "name": "Operations"}
            ]
            
            honest_presentation_score = 0
            total_sections = len(sections)
            
            for section in sections:
                try:
                    await page.goto(f"{DASHBOARD_URL}{section['url']}")
                    await page.wait_for_load_state("networkidle")
                    await asyncio.sleep(2)
                    
                    # Check for honest presentation indicators
                    page_content = await page.content()
                    honest_indicators = [
                        "mock", "demo", "projected", "benchmark", 
                        "simulation", "example", "sample"
                    ]
                    
                    section_indicators = []
                    for indicator in honest_indicators:
                        if indicator.lower() in page_content.lower():
                            section_indicators.append(indicator)
                    
                    if len(section_indicators) > 0:
                        honest_presentation_score += 1
                        print(f"   ✅ {section['name']}: {len(section_indicators)} honest indicators found")
                    else:
                        print(f"   ⚠️  {section['name']}: No honest indicators found")
                    
                except Exception as e:
                    print(f"   ❌ {section['name']}: Error checking section - {e}")
            
            # Take final screenshot
            screenshot_path = VALIDATION_CONFIG["screenshot_dir"] / f"honest_presentation_{self.session_id}.png"
            await page.screenshot(path=str(screenshot_path), full_page=True)
            self.screenshot_count += 1
            
            result = {
                "test": "honest_presentation",
                "status": "PASS" if honest_presentation_score >= total_sections * 0.5 else "FAIL",
                "sections_with_indicators": honest_presentation_score,
                "total_sections": total_sections,
                "percentage": (honest_presentation_score / total_sections) * 100,
                "screenshot": str(screenshot_path),
                "timestamp": datetime.now().isoformat()
            }
            
            self.validation_results.append(result)
            
            if honest_presentation_score >= total_sections * 0.5:
                print(f"   ✅ Honest presentation validation PASSED - {honest_presentation_score}/{total_sections} sections")
                return True
            else:
                print(f"   ❌ Honest presentation validation FAILED - {honest_presentation_score}/{total_sections} sections")
                return False
                
        except Exception as e:
            print(f"   ❌ Honest presentation validation ERROR: {e}")
            result = {
                "test": "honest_presentation",
                "status": "ERROR",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            self.validation_results.append(result)
            return False
    
    async def validate_judge_trust_features(self, page):
        """Validate features designed to maintain judge trust."""
        print("🤝 Validating judge trust features...")
        
        try:
            # Navigate to main demo page
            await page.goto(f"{DASHBOARD_URL}/demo")
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(3)
            
            # Check for trust-building elements
            trust_elements = [
                {"selector": "text=mock", "description": "Mock data labeling"},
                {"selector": "text=demo", "description": "Demo data identification"},
                {"selector": "text=projected", "description": "Projected values identification"},
                {"selector": "text=benchmark", "description": "Benchmark sourcing"}
            ]
            
            found_elements = []
            missing_elements = []
            
            for element in trust_elements:
                try:
                    found = await page.query_selector(element["selector"])
                    if found:
                        found_elements.append(element["description"])
                        print(f"   ✅ Found trust element: {element['description']}")
                    else:
                        missing_elements.append(element["description"])
                        print(f"   ⚠️  Missing trust element: {element['description']}")
                except PlaywrightTimeoutError:
                    missing_elements.append(element["description"])
                    print(f"   ⚠️  Missing trust element: {element['description']}")
            
            # Take screenshot
            screenshot_path = VALIDATION_CONFIG["screenshot_dir"] / f"judge_trust_{self.session_id}.png"
            await page.screenshot(path=str(screenshot_path), full_page=True)
            self.screenshot_count += 1
            
            trust_score = len(found_elements) / len(trust_elements) * 100
            
            result = {
                "test": "judge_trust_features",
                "status": "PASS" if trust_score >= 50 else "FAIL",
                "found_elements": found_elements,
                "missing_elements": missing_elements,
                "trust_score": trust_score,
                "screenshot": str(screenshot_path),
                "timestamp": datetime.now().isoformat()
            }
            
            self.validation_results.append(result)
            
            if trust_score >= 50:
                print(f"   ✅ Judge trust validation PASSED - {trust_score:.1f}% trust elements found")
                return True
            else:
                print(f"   ❌ Judge trust validation FAILED - {trust_score:.1f}% trust elements found")
                return False
                
        except Exception as e:
            print(f"   ❌ Judge trust validation ERROR: {e}")
            result = {
                "test": "judge_trust_features",
                "status": "ERROR",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            self.validation_results.append(result)
            return False
    
    async def run_validation(self):
        """Run complete transparency validation suite."""
        print("🚀 Starting transparency improvements validation...")
        
        # Check dashboard availability
        try:
            response = requests.get(DASHBOARD_URL, timeout=10)
            if response.status_code != 200:
                print(f"❌ Dashboard not accessible at {DASHBOARD_URL}")
                return False
        except Exception as e:
            print(f"❌ Dashboard connection failed: {e}")
            print("   Please start the dashboard: cd dashboard && npm run dev")
            return False
        
        print("✅ Dashboard is accessible")
        
        # Run validation tests
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=False)
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080}
            )
            page = await context.new_page()
            
            try:
                validation_tests = [
                    self.validate_mock_labeling,
                    self.validate_transparency_messaging,
                    self.validate_honest_presentation,
                    self.validate_judge_trust_features
                ]
                
                passed_tests = 0
                total_tests = len(validation_tests)
                
                for test in validation_tests:
                    try:
                        result = await test(page)
                        if result:
                            passed_tests += 1
                    except Exception as e:
                        print(f"   ❌ Test failed with exception: {e}")
                
                # Generate final report
                await self.generate_report(passed_tests, total_tests)
                
                return passed_tests == total_tests
                
            finally:
                await context.close()
                await browser.close()
    
    async def generate_report(self, passed_tests: int, total_tests: int):
        """Generate comprehensive validation report."""
        print("\n" + "=" * 70)
        print("📋 TRANSPARENCY VALIDATION REPORT")
        print("=" * 70)
        
        success_rate = (passed_tests / total_tests) * 100
        
        report = {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "validation_summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": total_tests - passed_tests,
                "success_rate": success_rate,
                "status": "PASS" if passed_tests == total_tests else "PARTIAL" if passed_tests > 0 else "FAIL"
            },
            "test_results": self.validation_results,
            "screenshots_captured": self.screenshot_count,
            "recommendations": self.generate_recommendations()
        }
        
        # Save report
        report_path = Path(VALIDATION_CONFIG["report_file"])
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📊 Tests Passed: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        print(f"📸 Screenshots: {self.screenshot_count} captured")
        print(f"📁 Report saved: {report_path}")
        
        if passed_tests == total_tests:
            print("🎉 ALL TRANSPARENCY VALIDATIONS PASSED!")
            print("   ✅ Mock data properly labeled")
            print("   ✅ Transparency messaging present")
            print("   ✅ Honest presentation practices implemented")
            print("   ✅ Judge trust features operational")
        else:
            print(f"⚠️  {total_tests - passed_tests} validation(s) failed")
            print("   Review individual test results for details")
        
        return report
    
    def generate_recommendations(self) -> List[str]:
        """Generate recommendations based on validation results."""
        recommendations = []
        
        for result in self.validation_results:
            if result["status"] == "FAIL":
                if result["test"] == "mock_data_labeling":
                    recommendations.append("Add '(mock)' labels to all demo metrics in PowerDashboard")
                elif result["test"] == "transparency_messaging":
                    recommendations.append("Include more transparency indicators throughout the interface")
                elif result["test"] == "honest_presentation":
                    recommendations.append("Add honest data sourcing information to all dashboard sections")
                elif result["test"] == "judge_trust_features":
                    recommendations.append("Implement additional trust-building elements for judge evaluation")
        
        if not recommendations:
            recommendations.append("All transparency features are properly implemented")
        
        return recommendations

async def main():
    """Main validation function."""
    print("🔍 Transparency Improvements Validation")
    print("🎯 Validating latest transparency enhancements")
    print("=" * 70)
    
    validator = TransparencyValidator()
    
    try:
        success = await validator.run_validation()
        
        if success:
            print("\n🎉 VALIDATION COMPLETE - ALL TESTS PASSED")
            print("   System ready for hackathon submission with transparency improvements")
            sys.exit(0)
        else:
            print("\n⚠️  VALIDATION INCOMPLETE - SOME TESTS FAILED")
            print("   Review validation report for details")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())