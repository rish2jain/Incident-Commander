#!/usr/bin/env python3
"""
Test Demo Route

Simple script to check what's actually being rendered at http://localhost:3000/demo
"""

import time
import sys
from pathlib import Path

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
except ImportError:
    print("Installing selenium...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "selenium"])
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

def test_demo_route():
    """Test what's actually being rendered at the demo route"""
    
    # Setup Chrome driver
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in background
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        print("🌐 Navigating to http://localhost:3000/demo...")
        driver.get("http://localhost:3000/demo")
        
        # Wait for page to load
        time.sleep(3)
        
        # Get page title
        title = driver.title
        print(f"📄 Page Title: {title}")
        
        # Check for PowerDashboard indicators
        print("\n🔍 Looking for PowerDashboard indicators...")
        
        # Look for PowerDashboard specific elements
        power_indicators = [
            "Live Incident Demo",
            "LIVE SAVINGS TODAY", 
            "Multi-Agent Status",
            "INCIDENT TIMELINE",
            "AGENT COORDINATION",
            "BUSINESS IMPACT",
            "PREDICTED INCIDENTS",
            "INDUSTRY FIRSTS",
            "Start Incident Demo",
            "Restart Demo"
        ]
        
        found_indicators = []
        for indicator in power_indicators:
            try:
                element = driver.find_element(By.XPATH, f"//*[contains(text(), '{indicator}')]")
                if element:
                    found_indicators.append(indicator)
                    print(f"  ✅ Found: {indicator}")
            except:
                print(f"  ❌ Missing: {indicator}")
        
        # Check for ExecutiveDashboard indicators
        print("\n🔍 Looking for ExecutiveDashboard indicators...")
        
        exec_indicators = [
            "SwarmAI",
            "AI-Powered Incident Response",
            "Mean Time to Resolution",
            "Cost Savings (Per Incident)",
            "Incidents Prevented",
            "System Accuracy",
            "Byzantine Consensus Network",
            "Ready to Transform Your Incident Response?"
        ]
        
        found_exec = []
        for indicator in exec_indicators:
            try:
                element = driver.find_element(By.XPATH, f"//*[contains(text(), '{indicator}')]")
                if element:
                    found_exec.append(indicator)
                    print(f"  ✅ Found: {indicator}")
            except:
                print(f"  ❌ Missing: {indicator}")
        
        # Get page source snippet
        page_source = driver.page_source
        print(f"\n📝 Page source length: {len(page_source)} characters")
        
        # Look for specific component indicators in source
        if "PowerDashboard" in page_source:
            print("  ✅ PowerDashboard found in source")
        else:
            print("  ❌ PowerDashboard NOT found in source")
            
        if "ExecutiveDashboard" in page_source:
            print("  ✅ ExecutiveDashboard found in source")
        else:
            print("  ❌ ExecutiveDashboard NOT found in source")
        
        # Check main content structure
        print("\n🏗️ Page Structure Analysis:")
        
        # Look for main containers
        containers = driver.find_elements(By.CSS_SELECTOR, ".min-h-screen")
        print(f"  Main containers found: {len(containers)}")
        
        # Look for card elements
        cards = driver.find_elements(By.CSS_SELECTOR, "[class*='card'], .card")
        print(f"  Card elements found: {len(cards)}")
        
        # Look for grid layouts
        grids = driver.find_elements(By.CSS_SELECTOR, "[class*='grid']")
        print(f"  Grid layouts found: {len(grids)}")
        
        # Check for 4-column layout (PowerDashboard specific)
        four_col_grids = driver.find_elements(By.CSS_SELECTOR, ".grid-cols-4")
        print(f"  4-column grids found: {len(four_col_grids)} (PowerDashboard indicator)")
        
        # Summary
        print(f"\n📊 Summary:")
        print(f"  PowerDashboard indicators found: {len(found_indicators)}/10")
        print(f"  ExecutiveDashboard indicators found: {len(found_exec)}/8")
        
        if len(found_indicators) > len(found_exec):
            print("  🎯 Likely showing: PowerDashboard")
        elif len(found_exec) > len(found_indicators):
            print("  🎯 Likely showing: ExecutiveDashboard")
        else:
            print("  🤔 Unclear which dashboard is showing")
            
        # Take a screenshot for verification
        screenshot_path = Path("demo_recordings/screenshots/route_test_verification.png")
        screenshot_path.parent.mkdir(exist_ok=True)
        driver.save_screenshot(str(screenshot_path))
        print(f"  📸 Screenshot saved: {screenshot_path}")
        
    except Exception as e:
        print(f"❌ Error testing demo route: {e}")
        import traceback
        traceback.print_exc()
    finally:
        driver.quit()

if __name__ == "__main__":
    test_demo_route()