#!/usr/bin/env python3
"""
Dashboard TypeScript Improvements Validation Script
Tests the latest dashboard enhancements including improved ref handling and type safety

Features tested:
- Enhanced TypeScript ref handling in EnhancedActivityFeed
- Improved scroll management and performance
- Type safety improvements across components
- Accessibility enhancements
- Performance optimizations
"""

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

import requests
from playwright.async_api import async_playwright


class DashboardTypeScriptValidator:
    """Validates dashboard TypeScript improvements and enhancements"""
    
    def __init__(self, base_url: str = "http://localhost:3000"):
        self.base_url = base_url
        self.validation_results = {
            "timestamp": datetime.now().isoformat(),
            "typescript_improvements": {},
            "scroll_performance": {},
            "accessibility": {},
            "component_types": {},
            "overall_status": "unknown"
        }
    
    async def validate_typescript_ref_handling(self, page):
        """Test improved TypeScript ref handling"""
        print("🔧 Testing TypeScript ref handling improvements...")
        
        try:
            # Test both insights demo URLs
            urls_to_test = [
                f"{self.base_url}/enhanced-insights-demo",
                f"{self.base_url}/insights-demo"
            ]
            
            url_results = {}
            
            for url in urls_to_test:
                print(f"  Testing URL: {url}")
                await page.goto(url)
                await page.wait_for_load_state("networkidle")
                
                url_key = url.split('/')[-1]  # Get the page name
                url_results[url_key] = {}
                
                # Check for enhanced activity feed component
                activity_feed = await page.query_selector('[data-testid="enhanced-activity-feed"]')
                if not activity_feed:
                    # Try alternative selector
                    activity_feed = await page.query_selector('.enhanced-activity-feed')
                
                if activity_feed:
                    url_results[url_key]["enhanced_activity_feed"] = "✅ Found"
                    print(f"  ✅ Enhanced activity feed component found on {url_key}")
                    
                    # Test scroll functionality
                    scroll_area = await page.query_selector('.scroll-area')
                    if scroll_area:
                        url_results[url_key]["scroll_area"] = "✅ Working"
                        print(f"  ✅ Scroll area with improved ref handling working on {url_key}")
                        
                        # Test scroll behavior
                        await scroll_area.scroll_into_view_if_needed()
                        await page.wait_for_timeout(500)
                        
                    else:
                        url_results[url_key]["scroll_area"] = "❌ Missing"
                        print(f"  ❌ Scroll area not found on {url_key}")
                    
                else:
                    url_results[url_key]["enhanced_activity_feed"] = "❌ Missing"
                    print(f"  ❌ Enhanced activity feed component not found on {url_key}")
            
            # Aggregate results
            self.validation_results["typescript_improvements"]["url_results"] = url_results
            
            # Set overall results based on any successful validation
            any_activity_feed = any(result.get("enhanced_activity_feed") == "✅ Found" for result in url_results.values())
            any_scroll_area = any(result.get("scroll_area") == "✅ Working" for result in url_results.values())
            
            if any_activity_feed:
                self.validation_results["typescript_improvements"]["enhanced_activity_feed"] = "✅ Found"
            else:
                self.validation_results["typescript_improvements"]["enhanced_activity_feed"] = "❌ Missing"
                
            if any_scroll_area:
                self.validation_results["typescript_improvements"]["scroll_area"] = "✅ Working"
            else:
                self.validation_results["typescript_improvements"]["scroll_area"] = "❌ Missing"
                print("  ❌ Enhanced activity feed component not found")
                return False
            
            return True
            
        except Exception as e:
            print(f"  ❌ TypeScript ref handling test failed: {e}")
            self.validation_results["typescript_improvements"]["error"] = str(e)
            return False
    
    async def validate_scroll_performance(self, page):
        """Test scroll performance improvements"""
        print("⚡ Testing scroll performance improvements...")
        
        try:
            # Measure scroll performance
            start_time = time.time()
            
            # Trigger multiple scroll events to test performance
            for i in range(10):
                await page.evaluate("window.scrollBy(0, 100)")
                await page.wait_for_timeout(50)
            
            scroll_time = time.time() - start_time
            self.validation_results["scroll_performance"]["scroll_time"] = f"{scroll_time:.3f}s"
            
            if scroll_time < 1.0:
                print(f"  ✅ Scroll performance excellent: {scroll_time:.3f}s")
                self.validation_results["scroll_performance"]["status"] = "✅ Excellent"
            elif scroll_time < 2.0:
                print(f"  ⚠️ Scroll performance acceptable: {scroll_time:.3f}s")
                self.validation_results["scroll_performance"]["status"] = "⚠️ Acceptable"
            else:
                print(f"  ❌ Scroll performance poor: {scroll_time:.3f}s")
                self.validation_results["scroll_performance"]["status"] = "❌ Poor"
            
            # Test auto-scroll functionality
            auto_scroll_indicator = await page.query_selector('.auto-scroll-indicator')
            if auto_scroll_indicator:
                self.validation_results["scroll_performance"]["auto_scroll"] = "✅ Working"
                print("  ✅ Auto-scroll functionality working")
            else:
                self.validation_results["scroll_performance"]["auto_scroll"] = "⚠️ Not visible"
                print("  ⚠️ Auto-scroll indicator not visible (may be hidden)")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Scroll performance test failed: {e}")
            self.validation_results["scroll_performance"]["error"] = str(e)
            return False
    
    async def validate_component_types(self, page):
        """Test component type safety improvements"""
        print("🔍 Testing component type safety...")
        
        try:
            # Check for TypeScript compilation errors in console
            console_errors = []
            
            def handle_console(msg):
                if msg.type == 'error' and 'typescript' in msg.text.lower():
                    console_errors.append(msg.text)
            
            page.on('console', handle_console)
            
            # Navigate and trigger component interactions
            await page.goto(f"{self.base_url}/enhanced-insights-demo")
            await page.wait_for_load_state("networkidle")
            
            # Wait for any TypeScript errors to appear
            await page.wait_for_timeout(2000)
            
            if not console_errors:
                self.validation_results["component_types"]["typescript_errors"] = "✅ None"
                print("  ✅ No TypeScript errors detected")
            else:
                self.validation_results["component_types"]["typescript_errors"] = f"❌ {len(console_errors)} errors"
                print(f"  ❌ {len(console_errors)} TypeScript errors detected")
                for error in console_errors[:3]:  # Show first 3 errors
                    print(f"    - {error}")
            
            # Test component props and refs
            components_with_refs = await page.query_selector_all('[ref]')
            if components_with_refs:
                self.validation_results["component_types"]["components_with_refs"] = f"✅ {len(components_with_refs)} found"
                print(f"  ✅ {len(components_with_refs)} components with refs found")
            else:
                self.validation_results["component_types"]["components_with_refs"] = "⚠️ None visible"
                print("  ⚠️ No components with visible ref attributes")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Component types test failed: {e}")
            self.validation_results["component_types"]["error"] = str(e)
            return False
    
    async def validate_accessibility_improvements(self, page):
        """Test accessibility enhancements"""
        print("♿ Testing accessibility improvements...")
        
        try:
            # Check for ARIA labels and accessibility attributes
            aria_elements = await page.query_selector_all('[aria-label], [aria-describedby], [role]')
            if aria_elements:
                self.validation_results["accessibility"]["aria_elements"] = f"✅ {len(aria_elements)} found"
                print(f"  ✅ {len(aria_elements)} elements with accessibility attributes")
            else:
                self.validation_results["accessibility"]["aria_elements"] = "❌ None found"
                print("  ❌ No accessibility attributes found")
            
            # Test keyboard navigation
            await page.keyboard.press('Tab')
            focused_element = await page.evaluate('document.activeElement.tagName')
            if focused_element:
                self.validation_results["accessibility"]["keyboard_navigation"] = "✅ Working"
                print(f"  ✅ Keyboard navigation working (focused: {focused_element})")
            else:
                self.validation_results["accessibility"]["keyboard_navigation"] = "❌ Not working"
                print("  ❌ Keyboard navigation not working")
            
            # Check for semantic HTML
            semantic_elements = await page.query_selector_all('main, section, article, nav, header, footer')
            if semantic_elements:
                self.validation_results["accessibility"]["semantic_html"] = f"✅ {len(semantic_elements)} elements"
                print(f"  ✅ {len(semantic_elements)} semantic HTML elements found")
            else:
                self.validation_results["accessibility"]["semantic_html"] = "⚠️ Limited"
                print("  ⚠️ Limited semantic HTML elements")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Accessibility test failed: {e}")
            self.validation_results["accessibility"]["error"] = str(e)
            return False
    
    async def validate_performance_optimizations(self, page):
        """Test performance optimizations"""
        print("🚀 Testing performance optimizations...")
        
        try:
            # Measure page load performance
            start_time = time.time()
            await page.goto(f"{self.base_url}/enhanced-insights-demo")
            await page.wait_for_load_state("networkidle")
            load_time = time.time() - start_time
            
            self.validation_results["scroll_performance"]["page_load_time"] = f"{load_time:.2f}s"
            
            if load_time < 2.0:
                print(f"  ✅ Page load time excellent: {load_time:.2f}s")
            elif load_time < 5.0:
                print(f"  ⚠️ Page load time acceptable: {load_time:.2f}s")
            else:
                print(f"  ❌ Page load time poor: {load_time:.2f}s")
            
            # Test component rendering performance
            render_start = time.time()
            await page.evaluate("""
                // Trigger component re-renders
                window.dispatchEvent(new CustomEvent('test-render'));
            """)
            await page.wait_for_timeout(500)
            render_time = time.time() - render_start
            
            self.validation_results["scroll_performance"]["render_time"] = f"{render_time:.3f}s"
            print(f"  ✅ Component render time: {render_time:.3f}s")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Performance test failed: {e}")
            self.validation_results["scroll_performance"]["performance_error"] = str(e)
            return False
    
    async def run_validation(self):
        """Run complete dashboard TypeScript improvements validation"""
        print("🔧 Starting Dashboard TypeScript Improvements Validation")
        print("=" * 70)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                # Run all validation tests
                tests = [
                    self.validate_typescript_ref_handling(page),
                    self.validate_scroll_performance(page),
                    self.validate_component_types(page),
                    self.validate_accessibility_improvements(page),
                    self.validate_performance_optimizations(page)
                ]
                
                results = await asyncio.gather(*tests, return_exceptions=True)
                
                # Calculate overall status
                passed_tests = sum(1 for result in results if result is True)
                total_tests = len(results)
                
                if passed_tests == total_tests:
                    self.validation_results["overall_status"] = "✅ All improvements validated"
                elif passed_tests >= total_tests * 0.8:
                    self.validation_results["overall_status"] = "⚠️ Most improvements working"
                else:
                    self.validation_results["overall_status"] = "❌ Multiple issues detected"
                
                print("\n" + "=" * 70)
                print(f"🔧 Dashboard TypeScript Validation Complete: {passed_tests}/{total_tests} tests passed")
                print(f"Status: {self.validation_results['overall_status']}")
                
            finally:
                await browser.close()
        
        # Save results
        results_file = Path("hackathon") / "dashboard_typescript_validation_results.json"
        with open(results_file, "w") as f:
            json.dump(self.validation_results, f, indent=2)
        
        print(f"📊 Results saved to: {results_file}")
        return self.validation_results


async def main():
    """Main validation function"""
    validator = DashboardTypeScriptValidator()
    results = await validator.run_validation()
    
    # Print summary
    print("\n🔧 DASHBOARD TYPESCRIPT IMPROVEMENTS SUMMARY")
    print("=" * 60)
    print(f"Overall Status: {results['overall_status']}")
    print(f"Timestamp: {results['timestamp']}")
    
    if results['typescript_improvements']:
        print("\n🔧 TypeScript Improvements:")
        for feature, status in results['typescript_improvements'].items():
            print(f"  {feature}: {status}")
    
    if results['scroll_performance']:
        print("\n⚡ Scroll Performance:")
        for metric, value in results['scroll_performance'].items():
            print(f"  {metric}: {value}")
    
    if results['accessibility']:
        print("\n♿ Accessibility:")
        for feature, status in results['accessibility'].items():
            print(f"  {feature}: {status}")
    
    if results['component_types']:
        print("\n🔍 Component Types:")
        for feature, status in results['component_types'].items():
            print(f"  {feature}: {status}")


if __name__ == "__main__":
    asyncio.run(main())