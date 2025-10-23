#!/usr/bin/env python3
"""
Simple PowerDashboard Recording

Takes screenshots of the PowerDashboard sections for demo purposes.
"""

import time
import sys
from pathlib import Path
from datetime import datetime

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

def record_power_dashboard():
    """Record PowerDashboard screenshots"""
    
    # Setup Chrome driver
    chrome_options = Options()
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        print("🎬 Recording PowerDashboard Demo...")
        
        # Navigate to PowerDashboard
        driver.get("http://localhost:3000/demo")
        time.sleep(3)
        
        # Create output directory
        output_dir = Path("demo_recordings/screenshots")
        output_dir.mkdir(exist_ok=True)
        
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 1. Full page overview
        print("📸 Full PowerDashboard overview...")
        driver.save_screenshot(str(output_dir / f"{session_id}_01_power_dashboard_full.png"))
        time.sleep(1)
        
        # 2. Scroll to show different sections
        print("📸 Hero section...")
        hero = driver.find_element(By.XPATH, "//h1[contains(text(), 'PowerDashboard')]")
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", hero)
        time.sleep(2)
        driver.save_screenshot(str(output_dir / f"{session_id}_02_hero_section.png"))
        
        # 3. 4-column layout
        print("📸 4-column layout...")
        grid = driver.find_element(By.CSS_SELECTOR, ".grid-cols-4")
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", grid)
        time.sleep(2)
        driver.save_screenshot(str(output_dir / f"{session_id}_03_four_column_layout.png"))
        
        # 4. Live savings section
        print("📸 Live savings section...")
        savings_text = driver.find_element(By.XPATH, "//*[contains(text(), 'LIVE SAVINGS TODAY')]")
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", savings_text)
        time.sleep(2)
        driver.save_screenshot(str(output_dir / f"{session_id}_04_live_savings.png"))
        
        # 5. Multi-agent status
        print("📸 Multi-agent status...")
        agent_text = driver.find_element(By.XPATH, "//*[contains(text(), 'Multi-Agent Status')]")
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", agent_text)
        time.sleep(2)
        driver.save_screenshot(str(output_dir / f"{session_id}_05_agent_status.png"))
        
        # 6. Industry firsts
        print("📸 Industry firsts...")
        industry_text = driver.find_element(By.XPATH, "//*[contains(text(), 'INDUSTRY FIRSTS')]")
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", industry_text)
        time.sleep(2)
        driver.save_screenshot(str(output_dir / f"{session_id}_06_industry_firsts.png"))
        
        # 7. Impact comparison
        print("📸 Impact comparison...")
        impact_text = driver.find_element(By.XPATH, "//*[contains(text(), 'IMPACT COMPARISON')]")
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", impact_text)
        time.sleep(2)
        driver.save_screenshot(str(output_dir / f"{session_id}_07_impact_comparison.png"))
        
        # 8. Incident timeline
        print("📸 Incident timeline...")
        timeline_text = driver.find_element(By.XPATH, "//*[contains(text(), 'INCIDENT TIMELINE')]")
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", timeline_text)
        time.sleep(2)
        driver.save_screenshot(str(output_dir / f"{session_id}_08_incident_timeline.png"))
        
        # 9. Agent coordination
        print("📸 Agent coordination...")
        coord_text = driver.find_element(By.XPATH, "//*[contains(text(), 'AGENT COORDINATION')]")
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", coord_text)
        time.sleep(2)
        driver.save_screenshot(str(output_dir / f"{session_id}_09_agent_coordination.png"))
        
        # 10. AI transparency
        print("📸 AI transparency...")
        ai_text = driver.find_element(By.XPATH, "//*[contains(text(), 'AI TRANSPARENCY')]")
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", ai_text)
        time.sleep(2)
        driver.save_screenshot(str(output_dir / f"{session_id}_10_ai_transparency.png"))
        
        # 11. Business impact
        print("📸 Business impact...")
        business_text = driver.find_element(By.XPATH, "//*[contains(text(), 'BUSINESS IMPACT')]")
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", business_text)
        time.sleep(2)
        driver.save_screenshot(str(output_dir / f"{session_id}_11_business_impact.png"))
        
        # 12. Predicted incidents
        print("📸 Predicted incidents...")
        pred_text = driver.find_element(By.XPATH, "//*[contains(text(), 'PREDICTED INCIDENTS')]")
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", pred_text)
        time.sleep(2)
        driver.save_screenshot(str(output_dir / f"{session_id}_12_predicted_incidents.png"))
        
        # 13. Competitor comparison
        print("📸 Competitor comparison...")
        comp_text = driver.find_element(By.XPATH, "//*[contains(text(), 'VS. COMPETITORS')]")
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", comp_text)
        time.sleep(2)
        driver.save_screenshot(str(output_dir / f"{session_id}_13_competitor_comparison.png"))
        
        # 14. Demo controls
        print("📸 Demo controls...")
        demo_text = driver.find_element(By.XPATH, "//*[contains(text(), 'Live Incident Demo')]")
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", demo_text)
        time.sleep(2)
        driver.save_screenshot(str(output_dir / f"{session_id}_14_demo_controls.png"))
        
        # 15. Final overview
        print("📸 Final overview...")
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(2)
        driver.save_screenshot(str(output_dir / f"{session_id}_15_final_overview.png"))
        
        print(f"✅ PowerDashboard recording complete! Screenshots saved with session ID: {session_id}")
        
        # Generate summary
        summary = {
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "demo_url": "http://localhost:3000/demo",
            "hackathon_year": "2025",
            "screenshots_captured": 15,
            "features_demonstrated": [
                "PowerDashboard 4-column layout",
                "Live savings counter with zero-touch streak",
                "Multi-agent status with confidence scores",
                "Industry firsts and differentiators",
                "Before vs After comparison (91.8% improvement)",
                "Step-by-step incident timeline",
                "Agent coordination with consensus",
                "AI transparency with reasoning",
                "Business impact calculator ($277K saved)",
                "Predicted incidents with prevention",
                "Competitor comparison",
                "Interactive demo controls with React state management",
                "Hackathon 2025 branding and footer"
            ],
            "key_metrics_shown": {
                "incidents_resolved": 47,
                "time_saved": "18h 23m",
                "cost_avoided": "$156K",
                "zero_touch_streak": 47,
                "mttr_improvement": "91.8% faster",
                "consensus_confidence": "94%",
                "business_savings": "$277K per incident"
            }
        }
        
        import json
        summary_file = Path("demo_recordings") / f"power_dashboard_summary_{session_id}.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
            
        print(f"📋 Summary saved: {summary_file}")
        
    except Exception as e:
        print(f"❌ Error during recording: {e}")
        import traceback
        traceback.print_exc()
    finally:
        driver.quit()

if __name__ == "__main__":
    record_power_dashboard()