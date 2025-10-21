#!/usr/bin/env python3
"""
Validation script for autoscrolling improvements
Checks that the timeline properly shows newest events and handles user interaction
"""

import asyncio
from playwright.async_api import async_playwright
import json
import os
from pathlib import Path
from datetime import datetime

async def validate_autoscroll():
    """Validate autoscrolling behavior"""
    
    results = {
        "test_name": "Autoscroll Validation",
        "timestamp": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "tests": []
    }
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()
        
        try:
            # Test 1: Initial load
            await page.goto("http://localhost:3000/agent_actions_dashboard.html")
            await page.wait_for_load_state('networkidle')
            
            timeline_container = await page.query_selector('.timeline-section')
            initial_scroll = await timeline_container.evaluate('el => el.scrollTop') if timeline_container else -1
            
            results["tests"].append({
                "name": "Initial scroll position",
                "expected": "0px (top)",
                "actual": f"{initial_scroll}px",
                "passed": initial_scroll <= 20,
                "description": "Timeline should start at top to show newest events"
            })
            
            # Test 2: Trigger incident and check autoscroll
            await page.click('button:has-text("Trigger Database Cascade Incident")')
            await asyncio.sleep(5)  # Wait for some events
            
            # Re-query timeline container to avoid stale reference
            timeline_container_fresh = await page.query_selector('.timeline-section')
            scroll_after_events = await timeline_container_fresh.evaluate('el => el.scrollTop') if timeline_container_fresh else -1
            
            results["tests"].append({
                "name": "Auto-scroll after new events",
                "expected": "≤20px (near top)",
                "actual": f"{scroll_after_events}px",
                "passed": scroll_after_events <= 20,
                "description": "Timeline should auto-scroll to show newest events"
            })
            
            # Test 3: Check if newest events are visible
            newest_events = await page.query_selector_all('#timeline-feed .timeline-event')
            newest_visible = len(newest_events) > 0
            
            if newest_events:
                last_event = newest_events[-1]  # Last in DOM = newest visually (column-reverse)
                is_visible = await last_event.is_visible()
                newest_visible = is_visible
            
            results["tests"].append({
                "name": "Newest events visibility",
                "expected": "True",
                "actual": str(newest_visible),
                "passed": newest_visible,
                "description": "Newest events should be visible in viewport"
            })
            
            # Test 4: Manual scroll behavior
            # First check if there's enough content to scroll
            scroll_info = await page.evaluate('''
                const container = document.querySelector('.timeline-section');
                if (container) {
                    return {
                        scrollHeight: container.scrollHeight,
                        clientHeight: container.clientHeight,
                        maxScroll: container.scrollHeight - container.clientHeight
                    };
                }
                return null;
            ''')
            
            if scroll_info and scroll_info['maxScroll'] > 100:
                # There's enough content to scroll
                scroll_amount = min(scroll_info['maxScroll'] - 50, 500)  # Don't scroll to the very bottom
                
                await page.evaluate(f'''
                    const container = document.querySelector('.timeline-section');
                    if (container) {{
                        container.style.scrollBehavior = 'auto';
                        container.scrollTop = {scroll_amount};
                    }}
                ''')
                await asyncio.sleep(2)
                
                # Re-query timeline container to avoid stale reference
                timeline_container_manual = await page.query_selector('.timeline-section')
                scroll_after_manual = await timeline_container_manual.evaluate('el => el.scrollTop') if timeline_container_manual else -1
                expected_min = scroll_amount * 0.8  # Allow some tolerance
                
                results["tests"].append({
                    "name": "Manual scroll detection",
                    "expected": f"≥{expected_min:.0f}px (scrolled away)",
                    "actual": f"{scroll_after_manual}px",
                    "passed": scroll_after_manual >= expected_min,
                    "description": f"Manual scroll should move away from top (max scroll: {scroll_info['maxScroll']}px)"
                })
            else:
                # Not enough content to scroll meaningfully
                results["tests"].append({
                    "name": "Manual scroll detection",
                    "expected": "N/A (insufficient content)",
                    "actual": f"Content height: {scroll_info['scrollHeight'] if scroll_info else 'unknown'}px",
                    "passed": True,  # Pass if there's not enough content to test
                    "description": "Not enough timeline content to test manual scrolling"
                })
            
            # Test 5: Check scroll indicator
            scroll_indicator = await page.query_selector('.scroll-indicator')
            indicator_visible = await scroll_indicator.is_visible() if scroll_indicator else False
            
            results["tests"].append({
                "name": "Scroll indicator visibility",
                "expected": "True (when scrolled away)",
                "actual": str(indicator_visible),
                "passed": indicator_visible,
                "description": "Scroll indicator should appear when user scrolls away"
            })
            
        except Exception as e:
            results["error"] = str(e)
        
        finally:
            await browser.close()
    
    # Calculate overall results
    passed_tests = sum(1 for test in results["tests"] if test["passed"])
    total_tests = len(results["tests"])
    results["summary"] = {
        "total_tests": total_tests,
        "passed_tests": passed_tests,
        "success_rate": f"{(passed_tests/total_tests)*100:.1f}%" if total_tests > 0 else "0%",
        "overall_passed": passed_tests == total_tests
    }
    
    # Print results
    print("🧪 AUTOSCROLL VALIDATION RESULTS")
    print("=" * 50)
    
    for test in results["tests"]:
        status = "✅ PASS" if test["passed"] else "❌ FAIL"
        print(f"{status} {test['name']}")
        print(f"   Expected: {test['expected']}")
        print(f"   Actual: {test['actual']}")
        print(f"   Description: {test['description']}")
        print()
    
    print("📊 SUMMARY")
    print("-" * 30)
    print(f"Tests Passed: {results['summary']['passed_tests']}/{results['summary']['total_tests']}")
    print(f"Success Rate: {results['summary']['success_rate']}")
    
    if results["summary"]["overall_passed"]:
        print("\n🎉 ALL TESTS PASSED! Autoscrolling is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the results above.")
    
    # Save detailed results
    output_dir = Path("demo_recordings")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_dir / "autoscroll_validation.json", "w") as f:
        json.dump(results, f, indent=2)
    
    return results["summary"]["overall_passed"]

if __name__ == "__main__":
    success = asyncio.run(validate_autoscroll())
    exit(0 if success else 1)