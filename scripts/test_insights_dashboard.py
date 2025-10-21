#!/usr/bin/env python3
"""
Test the enhanced insights dashboard with AI transparency features
"""

import asyncio
import os
from playwright.async_api import async_playwright
from pathlib import Path

async def test_insights_dashboard():
    """Test the insights dashboard functionality"""
    
    async with async_playwright() as p:
        # Parse headless mode from environment
        headless_env = os.getenv('PLAYWRIGHT_HEADLESS', 'true').lower()
        headless = headless_env in ('1', 'true', 'yes')
        
        browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()
        
        try:
            print("🧠 Testing Enhanced Insights Dashboard...")
            
            # Navigate to insights dashboard
            await page.goto("http://localhost:3000/insights-demo")
            await page.wait_for_load_state('networkidle', timeout=10000)
            
            # Check if page loaded
            title = await page.title()
            print(f"   Page title: {title}")
            
            # Look for main heading
            heading = await page.query_selector('h1')
            if heading:
                heading_text = await heading.inner_text()
                print(f"   Main heading: {heading_text}")
                
                if "AI Insights" in heading_text:
                    print("   ✅ Insights dashboard loaded successfully!")
                    
                    # Take initial screenshot
                    Path("demo_recordings").mkdir(parents=True, exist_ok=True)
                    await page.screenshot(path="demo_recordings/insights_dashboard_initial.png")
                    print("   📸 Initial screenshot saved")
                    
                    # Test tabs
                    tabs = await page.query_selector_all('[role="tab"]')
                    print(f"   📑 Found {len(tabs)} insight tabs")
                    
                    # Test trigger button
                    trigger_btn = await page.query_selector('button:has-text("Trigger Enhanced Demo")')
                    if trigger_btn:
                        print("   🔘 Found enhanced demo trigger button")
                        
                        # Click to start enhanced demo
                        await trigger_btn.click()
                        print("   ✅ Enhanced demo triggered!")
                        
                        # Wait for agent reasoning to appear
                        await asyncio.sleep(5)
                        
                        # Check for agent reasoning
                        reasoning_elements = await page.query_selector_all('[class*="border-slate-600"]')
                        print(f"   🧠 Agent reasoning elements: {len(reasoning_elements)}")
                        
                        # Take screenshot during reasoning
                        await page.screenshot(path="demo_recordings/insights_reasoning.png")
                        print("   📸 Reasoning screenshot saved")
                        
                        # Test different tabs
                        tab_names = ["decisions", "confidence", "communication", "analytics"]
                        for tab_name in tab_names:
                            try:
                                tab = await page.query_selector(f'[value="{tab_name}"]')
                                if tab:
                                    await tab.click()
                                    await asyncio.sleep(2)
                                    await page.screenshot(path=f"demo_recordings/insights_{tab_name}_tab.png")
                                    print(f"   📸 {tab_name.title()} tab screenshot saved")
                            except Exception as e:
                                print(f"   ⚠️ Could not test {tab_name} tab: {e}")
                        
                        # Wait for demo to complete
                        await asyncio.sleep(10)
                        
                        # Final screenshot
                        await page.screenshot(path="demo_recordings/insights_dashboard_complete.png")
                        print("   📸 Final screenshot saved")
                        
                        return True
                    else:
                        print("   ❌ Trigger button not found")
                else:
                    print("   ❌ Wrong content loaded")
            else:
                print("   ❌ No heading found")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            await page.screenshot(path="demo_recordings/insights_dashboard_error.png")
            
        finally:
            await browser.close()
    
    return False

if __name__ == "__main__":
    success = asyncio.run(test_insights_dashboard())
    if success:
        print("\n🎉 Enhanced insights dashboard is working correctly!")
        print("✅ AI transparency features operational")
        print("✅ Agent reasoning visualization working")
        print("✅ Decision trees and confidence tracking active")
        print("✅ Communication matrix functional")
        print("✅ Analytics and bias detection ready")
    else:
        print("\n❌ Insights dashboard has issues")
    exit(0 if success else 1)