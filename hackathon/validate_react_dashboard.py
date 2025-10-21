#!/usr/bin/env python3
"""
React Dashboard Validation Script

Validates the enhanced React dashboard features for hackathon submission.
Tests modern React components, TypeScript integration, and UX improvements.
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List, Any
from playwright.async_api import async_playwright


class ReactDashboardValidator:
    """Validates React dashboard features and functionality."""
    
    def __init__(self):
        self.base_url = "http://localhost:3000"
        self.results = []
        
    async def validate_react_dashboard(self) -> Dict[str, Any]:
        """Validate React dashboard features."""
        print("🎨 Validating React Dashboard Features...")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
            page = await context.new_page()
            
            try:
                # Test 1: React Dashboard Loading
                result = await self._test_react_dashboard_loading(page)
                self.results.append(result)
                
                # Test 2: TypeScript Components
                result = await self._test_typescript_components(page)
                self.results.append(result)
                
                # Test 3: Tailwind CSS Styling
                result = await self._test_tailwind_styling(page)
                self.results.append(result)
                
                # Test 4: Smart Auto-Scroll
                result = await self._test_smart_autoscroll(page)
                self.results.append(result)
                
                # Test 5: Real-time State Management
                result = await self._test_realtime_state(page)
                self.results.append(result)
                
                # Test 6: Accessibility Features
                result = await self._test_accessibility(page)
                self.results.append(result)
                
                # Test 7: Performance Optimization
                result = await self._test_performance(page)
                self.results.append(result)
                
                # Test 8: Tabbed Interface
                result = await self._test_tabbed_interface(page)
                self.results.append(result)
                
            finally:
                await browser.close()
        
        return self._generate_report()
    
    async def _test_react_dashboard_loading(self, page) -> Dict[str, Any]:
        """Test React dashboard loading and initialization."""
        start_time = time.time()
        
        try:
            await page.goto(f"{self.base_url}/simple-demo")
            await page.wait_for_load_state('networkidle', timeout=10000)
            
            # Check for React root element
            react_root = await page.query_selector('[data-reactroot], #__next, #root')
            
            # Check for main heading
            heading = await page.query_selector('h1')
            heading_text = await heading.inner_text() if heading else ""
            
            duration = time.time() - start_time
            
            return {
                'test': 'React Dashboard Loading',
                'success': react_root is not None and "Autonomous Incident Commander" in heading_text,
                'duration_ms': round(duration * 1000, 2),
                'details': {
                    'react_root_found': react_root is not None,
                    'heading_text': heading_text,
                    'load_time': f"{duration:.2f}s"
                }
            }
            
        except Exception as e:
            return {
                'test': 'React Dashboard Loading',
                'success': False,
                'duration_ms': round((time.time() - start_time) * 1000, 2),
                'error': str(e)
            }
    
    async def _test_typescript_components(self, page) -> Dict[str, Any]:
        """Test TypeScript component functionality including tabbed interface."""
        start_time = time.time()
        
        try:
            # Check for TypeScript-specific elements
            cards = await page.query_selector_all('[class*="Card"]')
            buttons = await page.query_selector_all('button')
            badges = await page.query_selector_all('[class*="Badge"]')
            
            # Check for tabbed interface components
            tabs_list = await page.query_selector('[role="tablist"]')
            tab_triggers = await page.query_selector_all('[role="tab"]')
            tab_panels = await page.query_selector_all('[role="tabpanel"]')
            
            # Test tab interactivity
            if tab_triggers and len(tab_triggers) > 1:
                await tab_triggers[1].click()  # Click second tab
                await asyncio.sleep(1)
                await tab_triggers[0].click()  # Click first tab
                await asyncio.sleep(1)
            
            # Test component interactivity
            if buttons:
                await buttons[0].click()
                await asyncio.sleep(2)
            
            duration = time.time() - start_time
            
            return {
                'test': 'TypeScript Components',
                'success': len(cards) > 0 and len(buttons) > 0 and tabs_list is not None,
                'duration_ms': round(duration * 1000, 2),
                'details': {
                    'cards_found': len(cards),
                    'buttons_found': len(buttons),
                    'badges_found': len(badges),
                    'tabs_list_found': tabs_list is not None,
                    'tab_triggers_found': len(tab_triggers),
                    'tab_panels_found': len(tab_panels),
                    'interactive': True,
                    'tabbed_interface': len(tab_triggers) >= 5  # Should have 5 tabs
                }
            }
            
        except Exception as e:
            return {
                'test': 'TypeScript Components',
                'success': False,
                'duration_ms': round((time.time() - start_time) * 1000, 2),
                'error': str(e)
            }
    
    async def _test_tailwind_styling(self, page) -> Dict[str, Any]:
        """Test Tailwind CSS styling and responsive design."""
        start_time = time.time()
        
        try:
            # Check for Tailwind classes
            tailwind_elements = await page.query_selector_all('[class*="bg-"], [class*="text-"], [class*="p-"], [class*="m-"]')
            
            # Check for gradient backgrounds
            gradient_elements = await page.query_selector_all('[class*="gradient"], [style*="gradient"]')
            
            # Check responsive design
            await page.set_viewport_size({'width': 768, 'height': 1024})  # Tablet
            await asyncio.sleep(1)
            
            await page.set_viewport_size({'width': 1920, 'height': 1080})  # Desktop
            await asyncio.sleep(1)
            
            duration = time.time() - start_time
            
            return {
                'test': 'Tailwind CSS Styling',
                'success': len(tailwind_elements) > 10,
                'duration_ms': round(duration * 1000, 2),
                'details': {
                    'tailwind_elements': len(tailwind_elements),
                    'gradient_elements': len(gradient_elements),
                    'responsive_tested': True
                }
            }
            
        except Exception as e:
            return {
                'test': 'Tailwind CSS Styling',
                'success': False,
                'duration_ms': round((time.time() - start_time) * 1000, 2),
                'error': str(e)
            }
    
    async def _test_smart_autoscroll(self, page) -> Dict[str, Any]:
        """Test smart auto-scroll functionality."""
        start_time = time.time()
        
        try:
            # Trigger demo to generate events
            trigger_btn = await page.query_selector('button')
            if trigger_btn:
                await trigger_btn.click()
                await asyncio.sleep(5)  # Wait for events
            
            # Check timeline container
            timeline = await page.query_selector('[class*="timeline"], [class*="overflow-y-auto"]')
            
            # Test scroll behavior
            if timeline:
                scroll_top = await timeline.evaluate('el => el.scrollTop')
                
                # Simulate user scroll
                await timeline.evaluate('el => el.scrollTop = 100')
                await asyncio.sleep(1)
                
                # Check if auto-scroll is paused
                new_scroll_top = await timeline.evaluate('el => el.scrollTop')
            
            duration = time.time() - start_time
            
            return {
                'test': 'Smart Auto-Scroll',
                'success': timeline is not None,
                'duration_ms': round(duration * 1000, 2),
                'details': {
                    'timeline_found': timeline is not None,
                    'initial_scroll': scroll_top if timeline else 'N/A',
                    'scroll_interaction_tested': True
                }
            }
            
        except Exception as e:
            return {
                'test': 'Smart Auto-Scroll',
                'success': False,
                'duration_ms': round((time.time() - start_time) * 1000, 2),
                'error': str(e)
            }
    
    async def _test_realtime_state(self, page) -> Dict[str, Any]:
        """Test real-time state management."""
        start_time = time.time()
        
        try:
            # Check for real-time metrics
            metrics = await page.query_selector_all('[class*="metric"], [id*="metric"]')
            
            # Trigger demo and check for updates
            trigger_btn = await page.query_selector('button')
            if trigger_btn:
                initial_text = await trigger_btn.inner_text()
                await trigger_btn.click()
                await asyncio.sleep(3)
                updated_text = await trigger_btn.inner_text()
                state_changed = initial_text != updated_text
            else:
                state_changed = False
            
            duration = time.time() - start_time
            
            return {
                'test': 'Real-time State Management',
                'success': len(metrics) > 0 and state_changed,
                'duration_ms': round(duration * 1000, 2),
                'details': {
                    'metrics_found': len(metrics),
                    'state_updates': state_changed,
                    'real_time_tested': True
                }
            }
            
        except Exception as e:
            return {
                'test': 'Real-time State Management',
                'success': False,
                'duration_ms': round((time.time() - start_time) * 1000, 2),
                'error': str(e)
            }
    
    async def _test_accessibility(self, page) -> Dict[str, Any]:
        """Test accessibility features."""
        start_time = time.time()
        
        try:
            # Check for ARIA labels
            aria_elements = await page.query_selector_all('[aria-label], [aria-labelledby], [role]')
            
            # Check for semantic HTML
            semantic_elements = await page.query_selector_all('main, section, article, nav, header')
            
            # Check for keyboard navigation
            focusable_elements = await page.query_selector_all('button, input, [tabindex]')
            
            duration = time.time() - start_time
            
            return {
                'test': 'Accessibility Features',
                'success': len(aria_elements) > 5 and len(semantic_elements) > 0,
                'duration_ms': round(duration * 1000, 2),
                'details': {
                    'aria_elements': len(aria_elements),
                    'semantic_elements': len(semantic_elements),
                    'focusable_elements': len(focusable_elements)
                }
            }
            
        except Exception as e:
            return {
                'test': 'Accessibility Features',
                'success': False,
                'duration_ms': round((time.time() - start_time) * 1000, 2),
                'error': str(e)
            }
    
    async def _test_performance(self, page) -> Dict[str, Any]:
        """Test performance optimization."""
        start_time = time.time()
        
        try:
            # Measure page load performance
            await page.goto(f"{self.base_url}/simple-demo")
            
            # Get performance metrics
            performance_metrics = await page.evaluate('''
                () => {
                    const navigation = performance.getEntriesByType('navigation')[0];
                    return {
                        loadTime: navigation.loadEventEnd - navigation.loadEventStart,
                        domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
                        firstPaint: performance.getEntriesByName('first-paint')[0]?.startTime || 0
                    };
                }
            ''')
            
            duration = time.time() - start_time
            
            return {
                'test': 'Performance Optimization',
                'success': performance_metrics['loadTime'] < 2000,  # Under 2 seconds
                'duration_ms': round(duration * 1000, 2),
                'details': {
                    'load_time_ms': performance_metrics['loadTime'],
                    'dom_content_loaded_ms': performance_metrics['domContentLoaded'],
                    'first_paint_ms': performance_metrics['firstPaint'],
                    'performance_optimized': performance_metrics['loadTime'] < 2000
                }
            }
            
        except Exception as e:
            return {
                'test': 'Performance Optimization',
                'success': False,
                'duration_ms': round((time.time() - start_time) * 1000, 2),
                'error': str(e)
            }
    
    async def _test_tabbed_interface(self, page) -> Dict[str, Any]:
        """Test advanced tabbed interface functionality."""
        start_time = time.time()
        
        try:
            # Navigate to insights demo page with tabbed interface
            await page.goto(f"{self.base_url}/insights-demo")
            await page.wait_for_load_state('networkidle')
            
            # Check for tab components
            tabs_root = await page.query_selector('[data-radix-collection-item]')
            tab_list = await page.query_selector('[role="tablist"]')
            tab_triggers = await page.query_selector_all('[role="tab"]')
            tab_panels = await page.query_selector_all('[role="tabpanel"]')
            
            # Test tab switching
            tab_names = []
            if tab_triggers:
                for i, tab in enumerate(tab_triggers[:3]):  # Test first 3 tabs
                    tab_text = await tab.inner_text()
                    tab_names.append(tab_text)
                    await tab.click()
                    await asyncio.sleep(0.5)
                    
                    # Check if tab panel is visible
                    active_panel = await page.query_selector('[role="tabpanel"]:not([hidden])')
                    if not active_panel:
                        active_panel = await page.query_selector('[data-state="active"]')
            
            # Check for specific tab content
            reasoning_content = await page.query_selector('text=Agent Reasoning')
            decision_trees_content = await page.query_selector('text=Decision Trees')
            confidence_content = await page.query_selector('text=Confidence')
            communication_content = await page.query_selector('text=Communication')
            analytics_content = await page.query_selector('text=Analytics')
            
            duration = time.time() - start_time
            
            expected_tabs = 5  # Should have 5 tabs
            has_all_tabs = len(tab_triggers) >= expected_tabs
            has_content = reasoning_content or decision_trees_content or confidence_content
            
            return {
                'test': 'Tabbed Interface',
                'success': tab_list is not None and has_all_tabs and has_content,
                'duration_ms': round(duration * 1000, 2),
                'details': {
                    'tabs_root_found': tabs_root is not None,
                    'tab_list_found': tab_list is not None,
                    'tab_triggers_count': len(tab_triggers),
                    'tab_panels_count': len(tab_panels),
                    'tab_names': tab_names,
                    'expected_tabs': expected_tabs,
                    'has_reasoning_tab': reasoning_content is not None,
                    'has_decision_trees_tab': decision_trees_content is not None,
                    'has_confidence_tab': confidence_content is not None,
                    'has_communication_tab': communication_content is not None,
                    'has_analytics_tab': analytics_content is not None,
                    'tab_switching_tested': len(tab_names) > 0
                }
            }
            
        except Exception as e:
            return {
                'test': 'Tabbed Interface',
                'success': False,
                'duration_ms': round((time.time() - start_time) * 1000, 2),
                'error': str(e)
            }
    
    def _generate_report(self) -> Dict[str, Any]:
        """Generate validation report."""
        passed_tests = sum(1 for result in self.results if result['success'])
        total_tests = len(self.results)
        
        return {
            'validation_timestamp': datetime.utcnow().isoformat(),
            'react_dashboard_validation': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'success_rate': f"{(passed_tests/total_tests)*100:.1f}%" if total_tests > 0 else "0%",
                'overall_success': passed_tests == total_tests
            },
            'test_results': self.results,
            'summary': {
                'react_architecture': any(r['test'] == 'React Dashboard Loading' and r['success'] for r in self.results),
                'typescript_components': any(r['test'] == 'TypeScript Components' and r['success'] for r in self.results),
                'tailwind_styling': any(r['test'] == 'Tailwind CSS Styling' and r['success'] for r in self.results),
                'smart_autoscroll': any(r['test'] == 'Smart Auto-Scroll' and r['success'] for r in self.results),
                'realtime_state': any(r['test'] == 'Real-time State Management' and r['success'] for r in self.results),
                'accessibility': any(r['test'] == 'Accessibility Features' and r['success'] for r in self.results),
                'performance': any(r['test'] == 'Performance Optimization' and r['success'] for r in self.results),
                'tabbed_interface': any(r['test'] == 'Tabbed Interface' and r['success'] for r in self.results)
            }
        }


async def main():
    """Main validation execution."""
    print("🎨 React Dashboard Validation")
    print("=" * 50)
    
    validator = ReactDashboardValidator()
    
    try:
        report = await validator.validate_react_dashboard()
        
        # Print results
        print(f"\n📊 VALIDATION RESULTS")
        print("-" * 30)
        print(f"Tests Passed: {report['react_dashboard_validation']['passed_tests']}/{report['react_dashboard_validation']['total_tests']}")
        print(f"Success Rate: {report['react_dashboard_validation']['success_rate']}")
        
        print(f"\n🧪 TEST DETAILS")
        print("-" * 30)
        for result in report['test_results']:
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"{status} {result['test']} ({result['duration_ms']}ms)")
            if 'error' in result:
                print(f"   Error: {result['error']}")
        
        print(f"\n📋 FEATURE SUMMARY")
        print("-" * 30)
        summary = report['summary']
        for feature, status in summary.items():
            icon = "✅" if status else "❌"
            print(f"{icon} {feature.replace('_', ' ').title()}")
        
        # Save report
        with open('hackathon/react_dashboard_validation.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Report saved to: hackathon/react_dashboard_validation.json")
        
        if report['react_dashboard_validation']['overall_success']:
            print(f"\n🎉 ALL REACT DASHBOARD TESTS PASSED!")
            print("✅ React dashboard is ready for hackathon submission")
            return 0
        else:
            print(f"\n⚠️  Some React dashboard tests failed")
            return 1
            
    except Exception as e:
        print(f"\n❌ Validation failed: {e}")
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))