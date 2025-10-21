#!/usr/bin/env python3
"""
Test the React dashboard to see if it's working properly
"""

import asyncio
from playwright.async_api import async_playwright
from pathlib import Path

async def test_react_dashboard():
    """Test if the React dashboard is working"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()
        
        try:
            print("🧪 Testing React Dashboard...")
            
            # Test simple demo page
            print("📱 Testing simple demo page...")
            await page.goto("http://localhost:3000/simple-demo")
            await page.wait_for_load_state('networkidle', timeout=10000)
            
            # Check if page loaded successfully
            title = await page.title()
            print(f"   Page title: {title}")
            
            # Look for the main heading
            heading = await page.query_selector('h1')
            if heading:
                heading_text = await heading.inner_text()
                print(f"   Main heading: {heading_text}")
                
                if "Autonomous Incident Commander" in heading_text:
                    print("   ✅ React dashboard loaded successfully!")
                    
                    # Take screenshot
                    await page.screenshot(path="demo_recordings/react_dashboard_test.png")
                    print("   📸 Screenshot saved")
                    
                    # Test the trigger button
                    trigger_btn = await page.query_selector('button')
                    if trigger_btn:
                        btn_text = await trigger_btn.inner_text()
                        print(f"   Button found: {btn_text}")
                        
                        # Click the button to test functionality
                        await trigger_btn.click()
                        await asyncio.sleep(3)
                        
                        # Check if events appeared
                        events = await page.query_selector_all('[class*="border-l-4"]')
                        print(f"   Events generated: {len(events)}")
                        
                        if len(events) > 0:
                            print("   ✅ Demo functionality working!")
                        else:
                            print("   ⚠️ No events generated")
                    
                    return True
                else:
                    print("   ❌ Wrong content loaded")
            else:
                print("   ❌ No heading found")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            
            # Take error screenshot
            await page.screenshot(path="demo_recordings/react_dashboard_error.png")
            
        finally:
            await browser.close()
    
    return False

if __name__ == "__main__":
    success = asyncio.run(test_react_dashboard())
    if success:
        print("\n🎉 React dashboard is working correctly!")
    else:
        print("\n❌ React dashboard has issues")
    exit(0 if success else 1)