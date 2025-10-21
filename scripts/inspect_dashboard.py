#!/usr/bin/env python3
"""
Simple script to inspect the dashboard and find available buttons
"""

import asyncio
from playwright.async_api import async_playwright

async def inspect_dashboard():
    async with async_playwright() as p:
        browser = None
        try:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            print("🔗 Navigating to dashboard...")
            try:
                await page.goto("http://localhost:3000", timeout=10000)
                await page.wait_for_load_state("networkidle", timeout=5000)
            except Exception as e:
                print(f"❌ Navigation failed: {e}")
                return
            
            # Wait for page to load
            await page.wait_for_timeout(3000)
            
            # Perform all inspection logic while browser is open
            print("\n📋 Page title:", await page.title())
            
            # Find all buttons
            buttons = await page.query_selector_all("button")
            print(f"\n🔘 Found {len(buttons)} buttons:")
            
            for i, button in enumerate(buttons):
                text = await button.inner_text()
                if text.strip():
                    print(f"  {i+1}. '{text.strip()}'")
            
            # Find all text containing "Database" or "Cascade"
            print("\n🔍 Text containing 'Database' or 'Cascade':")
            database_elements = await page.query_selector_all("text=Database")
            cascade_elements = await page.query_selector_all("text=Cascade")
            
            for elem in database_elements + cascade_elements:
                text = await elem.inner_text()
                print(f"  - '{text}'")
            
            # Take a screenshot
            await page.screenshot(path="scripts/dashboard_inspection.png")
            print("\n📸 Screenshot saved: scripts/dashboard_inspection.png")
            
        except Exception as e:
            print(f"❌ Browser setup failed: {e}")
            return
        finally:
            if browser:
                await browser.close()

if __name__ == "__main__":
    asyncio.run(inspect_dashboard())