#!/usr/bin/env python3
"""
Latest UI Enhancements Validation Script
Validates the newest UI improvements including success/failure indicators

October 24, 2025 - Enhanced Agent Completion Indicators with Smart Success/Failure Visual Feedback
"""

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

try:
    from playwright.async_api import async_playwright, Page, Browser
    import requests
except ImportError:
    print("❌ Required packages not installed. Installing...")
    import subprocess
    subprocess.run(["pip", "install", "playwright", "requests"])
    subprocess.run(["playwright", "install"])
    from playwright.async_api import async_playwright, Page, Browser
    import requests

# Configuration
DASHBOARD_URL = "http://localhost:3000"
BACKEND_URL = "http://localhost:8000"  # Simplified deployment backend
VALIDATION_TIMEOUT = 30000  # 30 seconds

class UIEnhancementValidator:
    """Validates the latest UI enhancements and features."""
    
    def __init__(self):
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.results = {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "validation_type": "Latest UI Enhancements",
            "categories": {},
            "overall_score": 0,
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0
        }
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        
    async def setup_browser(self):
        """Initialize browser for testing."""
        print("🔧 Setting up browser for UI validation...")
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=False)
        context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080}
        )
        self.page = await context.new_page()
        print("✅ Browser setup complete")
        
    async def validate_agent_completion_indicators(self) -> Dict[str, Any]:
        """Validate enhanced agent completion indicators."""
        print("\n🎯 Validating Agent Completion Indicators...")
        
        category_results = {
            "name": "Agent Completion Indicators",
            "tests": [],
            "score": 0,
            "max_score": 100
        }
        
        try:
            # Navigate to transparency dashboard
            await self.page.goto(f"{DASHBOARD_URL}/transparency")
            await self.page.wait_for_load_state("networkidle")
            await asyncio.sleep(3)
            
            # Test 1: Check for AgentCompletionIndicator component
            test_result = await self._test_component_presence(
                "AgentCompletionIndicator component",
                "[data-testid='agent-completion-indicator'], .agent-completion-indicator, h3:has-text('Agent Completions')"
            )
            category_results["tests"].append(test_result)
            
            # Test 2: Check for success/failure indicators
            test_result = await self._test_success_failure_indicators()
            category_results["tests"].append(test_result)
            
            # Test 3: Check for enhanced visual feedback
            test_result = await self._test_enhanced_visual_feedback()
            category_results["tests"].append(test_result)
            
            # Test 4: Check for real-time status updates
            test_result = await self._test_realtime_status_updates()
            category_results["tests"].append(test_result)
            
            # Test 5: Check for professional UI polish
            test_result = await self._test_professional_ui_polish()
            category_results["tests"].append(test_result)
            
        except Exception as e:
            print(f"❌ Error validating agent completion indicators: {e}")
            category_results["tests"].append({
                "name": "Agent Completion Indicators Error",
                "passed": False,
                "score": 0,
                "max_score": 20,
                "error": str(e)
            })
        
        # Calculate category score
        total_score = sum(test["score"] for test in category_results["tests"])
        max_total_score = sum(test["max_score"] for test in category_results["tests"])
        category_results["score"] = (total_score / max_total_score * 100) if max_total_score > 0 else 0
        
        return category_results
    
    async def _test_component_presence(self, test_name: str, selector: str) -> Dict[str, Any]:
        """Test if a component is present on the page."""
        try:
            element = await self.page.query_selector(selector)
            if element and await element.is_visible():
                print(f"   ✅ {test_name}: Found and visible")
                return {
                    "name": test_name,
                    "passed": True,
                    "score": 20,
                    "max_score": 20,
                    "details": "Component found and visible"
                }
            else:
                print(f"   ❌ {test_name}: Not found or not visible")
                return {
                    "name": test_name,
                    "passed": False,
                    "score": 0,
                    "max_score": 20,
                    "details": "Component not found or not visible"
                }
        except Exception as e:
            print(f"   ❌ {test_name}: Error - {e}")
            return {
                "name": test_name,
                "passed": False,
                "score": 0,
                "max_score": 20,
                "error": str(e)
            }
    
    async def _test_success_failure_indicators(self) -> Dict[str, Any]:
        """Test for success/failure indicator functionality."""
        test_name = "Success/Failure Indicators"
        try:
            # Look for success indicators (CheckCircle)
            success_indicators = await self.page.query_selector_all(
                "svg[data-testid='CheckCircle'], .lucide-check-circle, [class*='check-circle']"
            )
            
            # Look for failure indicators (XCircle)
            failure_indicators = await self.page.query_selector_all(
                "svg[data-testid='XCircle'], .lucide-x-circle, [class*='x-circle']"
            )
            
            # Look for colored backgrounds indicating success/failure
            colored_indicators = await self.page.query_selector_all(
                ".bg-green-500, .bg-red-500, [class*='bg-green'], [class*='bg-red']"
            )
            
            total_indicators = len(success_indicators) + len(failure_indicators) + len(colored_indicators)
            
            if total_indicators > 0:
                print(f"   ✅ {test_name}: Found {total_indicators} success/failure indicators")
                return {
                    "name": test_name,
                    "passed": True,
                    "score": 20,
                    "max_score": 20,
                    "details": f"Found {len(success_indicators)} success, {len(failure_indicators)} failure, {len(colored_indicators)} colored indicators"
                }
            else:
                print(f"   ❌ {test_name}: No success/failure indicators found")
                return {
                    "name": test_name,
                    "passed": False,
                    "score": 0,
                    "max_score": 20,
                    "details": "No success/failure indicators found"
                }
                
        except Exception as e:
            print(f"   ❌ {test_name}: Error - {e}")
            return {
                "name": test_name,
                "passed": False,
                "score": 0,
                "max_score": 20,
                "error": str(e)
            }
    
    async def _test_enhanced_visual_feedback(self) -> Dict[str, Any]:
        """Test for enhanced visual feedback elements."""
        test_name = "Enhanced Visual Feedback"
        try:
            # Look for animated elements
            animated_elements = await self.page.query_selector_all(
                "[class*='animate'], [class*='transition'], [class*='motion']"
            )
            
            # Look for hover effects
            hover_elements = await self.page.query_selector_all(
                "[class*='hover:'], .hover\\:shadow, .hover\\:scale"
            )
            
            # Look for gradient backgrounds
            gradient_elements = await self.page.query_selector_all(
                "[class*='gradient'], .bg-gradient-to"
            )
            
            total_feedback_elements = len(animated_elements) + len(hover_elements) + len(gradient_elements)
            
            if total_feedback_elements >= 5:
                print(f"   ✅ {test_name}: Found {total_feedback_elements} visual feedback elements")
                return {
                    "name": test_name,
                    "passed": True,
                    "score": 20,
                    "max_score": 20,
                    "details": f"Found {len(animated_elements)} animated, {len(hover_elements)} hover, {len(gradient_elements)} gradient elements"
                }
            else:
                print(f"   ⚠️  {test_name}: Limited visual feedback elements ({total_feedback_elements})")
                return {
                    "name": test_name,
                    "passed": False,
                    "score": 10,
                    "max_score": 20,
                    "details": f"Found only {total_feedback_elements} visual feedback elements"
                }
                
        except Exception as e:
            print(f"   ❌ {test_name}: Error - {e}")
            return {
                "name": test_name,
                "passed": False,
                "score": 0,
                "max_score": 20,
                "error": str(e)
            }
    
    async def _test_realtime_status_updates(self) -> Dict[str, Any]:
        """Test for real-time status update capabilities."""
        test_name = "Real-Time Status Updates"
        try:
            # Look for elements that suggest real-time updates
            realtime_elements = await self.page.query_selector_all(
                "[class*='pulse'], [class*='animate-pulse'], .animate-spin, [data-testid*='realtime'], [class*='live']"
            )
            
            # Look for timestamp elements
            timestamp_elements = await self.page.query_selector_all(
                "[class*='timestamp'], .time, [data-testid*='time'], time"
            )
            
            # Look for status indicators
            status_elements = await self.page.query_selector_all(
                "[class*='status'], .badge, [data-testid*='status'], [class*='indicator']"
            )
            
            total_realtime_elements = len(realtime_elements) + len(timestamp_elements) + len(status_elements)
            
            if total_realtime_elements >= 3:
                print(f"   ✅ {test_name}: Found {total_realtime_elements} real-time elements")
                return {
                    "name": test_name,
                    "passed": True,
                    "score": 20,
                    "max_score": 20,
                    "details": f"Found {len(realtime_elements)} animated, {len(timestamp_elements)} timestamp, {len(status_elements)} status elements"
                }
            else:
                print(f"   ⚠️  {test_name}: Limited real-time elements ({total_realtime_elements})")
                return {
                    "name": test_name,
                    "passed": False,
                    "score": 10,
                    "max_score": 20,
                    "details": f"Found only {total_realtime_elements} real-time elements"
                }
                
        except Exception as e:
            print(f"   ❌ {test_name}: Error - {e}")
            return {
                "name": test_name,
                "passed": False,
                "score": 0,
                "max_score": 20,
                "error": str(e)
            }
    
    async def _test_professional_ui_polish(self) -> Dict[str, Any]:
        """Test for professional UI polish and consistency."""
        test_name = "Professional UI Polish"
        try:
            # Look for consistent styling elements
            card_elements = await self.page.query_selector_all(
                ".card, [class*='card'], .border, [class*='rounded']"
            )
            
            # Look for typography consistency
            typography_elements = await self.page.query_selector_all(
                "h1, h2, h3, h4, h5, h6, .font-bold, .font-semibold, .text-lg, .text-xl"
            )
            
            # Look for spacing consistency
            spacing_elements = await self.page.query_selector_all(
                "[class*='p-'], [class*='m-'], [class*='gap-'], [class*='space-']"
            )
            
            # Look for color consistency
            color_elements = await self.page.query_selector_all(
                "[class*='text-'], [class*='bg-'], [class*='border-']"
            )
            
            total_polish_elements = len(card_elements) + len(typography_elements) + len(spacing_elements) + len(color_elements)
            
            if total_polish_elements >= 20:
                print(f"   ✅ {test_name}: Found {total_polish_elements} professional UI elements")
                return {
                    "name": test_name,
                    "passed": True,
                    "score": 20,
                    "max_score": 20,
                    "details": f"Found {len(card_elements)} cards, {len(typography_elements)} typography, {len(spacing_elements)} spacing, {len(color_elements)} color elements"
                }
            else:
                print(f"   ⚠️  {test_name}: Limited professional UI elements ({total_polish_elements})")
                return {
                    "name": test_name,
                    "passed": False,
                    "score": 10,
                    "max_score": 20,
                    "details": f"Found only {total_polish_elements} professional UI elements"
                }
                
        except Exception as e:
            print(f"   ❌ {test_name}: Error - {e}")
            return {
                "name": test_name,
                "passed": False,
                "score": 0,
                "max_score": 20,
                "error": str(e)
            }
    
    async def validate_dashboard_consistency(self) -> Dict[str, Any]:
        """Validate consistency across all dashboard views."""
        print("\n🎨 Validating Dashboard Consistency...")
        
        category_results = {
            "name": "Dashboard Consistency",
            "tests": [],
            "score": 0,
            "max_score": 100
        }
        
        dashboards = [
            {"name": "Demo Dashboard", "url": f"{DASHBOARD_URL}/demo"},
            {"name": "Transparency Dashboard", "url": f"{DASHBOARD_URL}/transparency"},
            {"name": "Operations Dashboard", "url": f"{DASHBOARD_URL}/ops"}
        ]
        
        for dashboard in dashboards:
            try:
                await self.page.goto(dashboard["url"])
                await self.page.wait_for_load_state("networkidle")
                await asyncio.sleep(2)
                
                # Test for consistent navigation
                nav_elements = await self.page.query_selector_all("nav, .nav, [role='navigation']")
                
                # Test for consistent styling
                consistent_elements = await self.page.query_selector_all(
                    ".card, .border, [class*='rounded'], [class*='shadow']"
                )
                
                # Test for enhanced indicators
                indicator_elements = await self.page.query_selector_all(
                    ".bg-green-500, .bg-red-500, svg[data-testid='CheckCircle'], svg[data-testid='XCircle']"
                )
                
                test_result = {
                    "name": f"{dashboard['name']} Consistency",
                    "passed": len(nav_elements) > 0 and len(consistent_elements) >= 5,
                    "score": 20 if len(nav_elements) > 0 and len(consistent_elements) >= 5 else 10,
                    "max_score": 20,
                    "details": f"Nav: {len(nav_elements)}, Styled: {len(consistent_elements)}, Indicators: {len(indicator_elements)}"
                }
                
                category_results["tests"].append(test_result)
                print(f"   {'✅' if test_result['passed'] else '⚠️'} {dashboard['name']}: {test_result['details']}")
                
            except Exception as e:
                print(f"   ❌ {dashboard['name']}: Error - {e}")
                category_results["tests"].append({
                    "name": f"{dashboard['name']} Error",
                    "passed": False,
                    "score": 0,
                    "max_score": 20,
                    "error": str(e)
                })
        
        # Calculate category score
        total_score = sum(test["score"] for test in category_results["tests"])
        max_total_score = sum(test["max_score"] for test in category_results["tests"])
        category_results["score"] = (total_score / max_total_score * 100) if max_total_score > 0 else 0
        
        return category_results
    
    async def run_validation(self) -> Dict[str, Any]:
        """Run complete UI enhancement validation."""
        print("🚀 Starting Latest UI Enhancements Validation")
        print(f"📅 Session: {self.session_id}")
        print("=" * 60)
        
        try:
            await self.setup_browser()
            
            # Run validation categories
            categories = [
                await self.validate_agent_completion_indicators(),
                await self.validate_dashboard_consistency()
            ]
            
            # Calculate overall results
            total_score = 0
            max_total_score = 0
            total_tests = 0
            passed_tests = 0
            
            for category in categories:
                self.results["categories"][category["name"]] = category
                total_score += category["score"]
                max_total_score += category["max_score"]
                
                for test in category["tests"]:
                    total_tests += 1
                    if test["passed"]:
                        passed_tests += 1
            
            self.results["overall_score"] = (total_score / max_total_score * 100) if max_total_score > 0 else 0
            self.results["total_tests"] = total_tests
            self.results["passed_tests"] = passed_tests
            self.results["failed_tests"] = total_tests - passed_tests
            
            # Save results
            results_file = Path(f"hackathon/ui_enhancement_validation_{self.session_id}.json")
            with open(results_file, 'w') as f:
                json.dump(self.results, f, indent=2)
            
            print("\n" + "=" * 60)
            print("🎉 UI Enhancement Validation Complete!")
            print("=" * 60)
            print(f"📊 Overall Score: {self.results['overall_score']:.1f}%")
            print(f"✅ Tests Passed: {passed_tests}/{total_tests}")
            print(f"📁 Results saved: {results_file}")
            
            # Print category summaries
            for category_name, category in self.results["categories"].items():
                print(f"\n📋 {category_name}: {category['score']:.1f}%")
                for test in category["tests"]:
                    status = "✅" if test["passed"] else "❌"
                    print(f"   {status} {test['name']}: {test['score']}/{test['max_score']}")
            
            return self.results
            
        except Exception as e:
            print(f"❌ Validation failed: {e}")
            self.results["error"] = str(e)
            return self.results
        
        finally:
            if self.browser:
                await self.browser.close()

async def main():
    """Main validation function."""
    validator = UIEnhancementValidator()
    results = await validator.run_validation()
    
    # Print final summary
    if results["overall_score"] >= 80:
        print(f"\n🏆 EXCELLENT: UI enhancements are production-ready!")
    elif results["overall_score"] >= 60:
        print(f"\n✅ GOOD: UI enhancements are functional with room for improvement")
    else:
        print(f"\n⚠️  NEEDS WORK: UI enhancements require attention")
    
    return results

if __name__ == "__main__":
    print("🎯 Latest UI Enhancements Validation")
    print("🔧 Testing enhanced agent completion indicators and UI polish")
    print("💡 Ensure dashboard is running: cd dashboard && npm run dev")
    print()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Validation stopped by user")
    except Exception as e:
        print(f"\n💥 Validation error: {e}")
        import traceback
        traceback.print_exc()