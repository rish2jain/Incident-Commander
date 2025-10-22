#!/usr/bin/env python3
"""
Quick test script to check autoscrolling behavior
Takes screenshots at key moments to verify timeline scrolling
"""

import asyncio
import pytest
from playwright.async_api import async_playwright
from pathlib import Path
import time

@pytest.mark.asyncio
async def test_autoscroll():
    """Test the autoscrolling behavior with screenshots"""
    
    output_dir = Path("demo_recordings/autoscroll_test")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        
        try:
            # Navigate to dashboard
            await page.goto("http://localhost:3000/agent_actions_dashboard.html")
            await page.wait_for_load_state('networkidle')
            
            # Take initial screenshot
            await page.screenshot(path=str(output_dir / "01_initial.png"))
            print("📸 Initial state captured")
            
            # Trigger incident manually
            await page.click('button:has-text("Trigger Database Cascade Incident")')
            await asyncio.sleep(2)
            
            # Take screenshot after trigger
            await page.screenshot(path=str(output_dir / "02_after_trigger.png"))
            print("📸 After trigger captured")
            
            # Wait for some timeline events
            await asyncio.sleep(10)
            await page.screenshot(path=str(output_dir / "03_timeline_events.png"))
            print("📸 Timeline events captured")
            
            # Check if timeline is scrolled to top (newest events visible)
            timeline_container = await page.query_selector('.timeline-section')
            if timeline_container:
                scroll_top = await timeline_container.evaluate('el => el.scrollTop')
                print(f"📊 Timeline scroll position: {scroll_top}px")
                
                # Check if newest events are visible
                newest_event = await page.query_selector('#timeline-feed .timeline-event:last-child')
                if newest_event:
                    is_visible = await newest_event.is_visible()
                    print(f"📊 Newest event visible: {is_visible}")
            
            # Wait for more events
            await asyncio.sleep(15)
            await page.screenshot(path=str(output_dir / "04_more_events.png"))
            print("📸 More events captured")
            
            # Check scroll position again - re-query to avoid stale reference
            timeline_container = await page.query_selector('.timeline-section')
            if timeline_container:
                scroll_top = await timeline_container.evaluate('el => el.scrollTop')
                print(f"📊 Timeline scroll position after more events: {scroll_top}px")
            
            # Test manual scrolling
            await page.evaluate('''
                const container = document.querySelector('.timeline-section');
                if (container) {
                    container.scrollTop = container.scrollHeight / 2;
                }
            ''')
            await asyncio.sleep(2)
            await page.screenshot(path=str(output_dir / "05_manual_scroll.png"))
            print("📸 After manual scroll captured")
            
            # Wait for new event to see if it auto-scrolls back
            await asyncio.sleep(10)
            await page.screenshot(path=str(output_dir / "06_after_manual_scroll.png"))
            print("📸 After manual scroll + new events captured")
            
            # Final scroll position check - re-query to avoid stale reference
            timeline_container = await page.query_selector('.timeline-section')
            if timeline_container:
                scroll_top = await timeline_container.evaluate('el => el.scrollTop')
                print(f"📊 Final timeline scroll position: {scroll_top}px")
        
        finally:
            await browser.close()
        
        print(f"\n✅ Autoscroll test complete!")
        print(f"📁 Screenshots saved to: {output_dir}")
        print(f"\n📋 Analysis:")
        print(f"   - Check if timeline stays at top (scrollTop ≈ 0) for newest events")
        print(f"   - Verify newest events are always visible")
        print(f"   - Confirm manual scrolling pauses auto-scroll")

if __name__ == "__main__":
    asyncio.run(test_autoscroll())