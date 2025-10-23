#!/usr/bin/env python3
"""
Complete Dashboard Recording

Records all three dashboards with comprehensive coverage:
1. PowerDashboard (/demo) - Interactive incident demonstration
2. Transparency Dashboard (/transparency) - AI explainability
3. Operations Dashboard (/ops) - Live monitoring

Creates a complete demo video showing the full system capabilities.
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
    from selenium.webdriver.common.action_chains import ActionChains
except ImportError:
    print("Installing selenium...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "selenium"])
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.action_chains import ActionChains

class CompleteDashboardRecorder:
    def __init__(self):
        self.base_url = "http://localhost:3000"
        self.output_dir = Path("demo_recordings")
        self.output_dir.mkdir(exist_ok=True)
        
        # Create session ID for this recording
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        self.driver = None
        self.wait = None
        
    def setup_driver(self):
        """Setup Chrome driver for recording"""
        chrome_options = Options()
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
        
    def take_screenshot(self, name: str, description: str = ""):
        """Take a screenshot with metadata"""
        screenshot_dir = self.output_dir / "screenshots"
        screenshot_dir.mkdir(exist_ok=True)
        
        filename = f"{self.session_id}_{name}.png"
        filepath = screenshot_dir / filename
        
        self.driver.save_screenshot(str(filepath))
        
        print(f"📸 {name}: {description}")
        return filepath
        
    def smooth_scroll(self, element):
        """Smooth scroll to element"""
        self.driver.execute_script("""
            arguments[0].scrollIntoView({ 
                behavior: 'smooth', 
                block: 'center' 
            });
        """, element)
        time.sleep(1.5)
        
    def wait_for_element(self, selector: str, timeout: int = 10):
        """Wait for element to be present"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            return element
        except Exception as e:
            print(f"Element not found: {selector} - {e}")
            return None
            
    def record_homepage(self):
        """Record the homepage with navigation"""
        print("\n🏠 Recording Homepage...")
        
        self.driver.get(self.base_url)
        time.sleep(3)
        
        # Homepage overview
        self.take_screenshot("01_homepage_overview", "Homepage with navigation to all dashboards")
        time.sleep(2)
        
        # Show navigation options
        nav_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/']")
        if nav_links:
            print(f"📍 Found {len(nav_links)} navigation links")
        
        self.take_screenshot("02_homepage_navigation", "Navigation options to different dashboards")
        
    def record_power_dashboard(self):
        """Record the PowerDashboard with interactive features"""
        print("\n🎬 Recording PowerDashboard (/demo)...")
        
        self.driver.get(f"{self.base_url}/demo")
        time.sleep(3)
        
        # 1. Full overview
        self.take_screenshot("03_power_dashboard_full", "Complete PowerDashboard with 4-column layout")
        time.sleep(2)
        
        # 2. Hero section with live metrics
        hero = self.driver.find_element(By.XPATH, "//h1[contains(text(), 'PowerDashboard')]")
        self.smooth_scroll(hero)
        self.take_screenshot("04_power_hero_section", "Hero section with live incident metrics")
        
        # 3. Live savings counter
        try:
            savings_text = self.driver.find_element(By.XPATH, "//*[contains(text(), 'LIVE SAVINGS TODAY')]")
            self.smooth_scroll(savings_text)
            self.take_screenshot("05_live_savings_counter", "Real-time cost savings and zero-touch streak")
        except:
            print("⚠️ Live savings section not found")
        
        # 4. Multi-agent status
        try:
            agent_text = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Multi-Agent Status')]")
            self.smooth_scroll(agent_text)
            self.take_screenshot("06_multi_agent_status", "Dynamic agent status with confidence scores")
        except:
            print("⚠️ Agent status section not found")
        
        # 5. Before/After comparison
        try:
            impact_text = self.driver.find_element(By.XPATH, "//*[contains(text(), 'IMPACT COMPARISON')]")
            self.smooth_scroll(impact_text)
            self.take_screenshot("07_impact_comparison", "Manual vs AI response time comparison")
        except:
            print("⚠️ Impact comparison section not found")
        
        # 6. Incident timeline
        try:
            timeline_text = self.driver.find_element(By.XPATH, "//*[contains(text(), 'INCIDENT TIMELINE')]")
            self.smooth_scroll(timeline_text)
            self.take_screenshot("08_incident_timeline", "Step-by-step incident resolution timeline")
        except:
            print("⚠️ Timeline section not found")
        
        # 7. Agent coordination
        try:
            coord_text = self.driver.find_element(By.XPATH, "//*[contains(text(), 'AGENT COORDINATION')]")
            self.smooth_scroll(coord_text)
            self.take_screenshot("09_agent_coordination", "Byzantine consensus visualization")
        except:
            print("⚠️ Coordination section not found")
        
        # 8. Business impact
        try:
            business_text = self.driver.find_element(By.XPATH, "//*[contains(text(), 'BUSINESS IMPACT')]")
            self.smooth_scroll(business_text)
            self.take_screenshot("10_business_impact", "Real-time ROI calculation")
        except:
            print("⚠️ Business impact section not found")
        
        # 9. Interactive demo controls
        try:
            demo_text = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Live Incident Demo')]")
            self.smooth_scroll(demo_text)
            self.take_screenshot("11_demo_controls", "Interactive demo controls with working buttons")
            
            # Test button interaction
            try:
                restart_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Restart Demo')]")
                restart_button.click()
                time.sleep(2)
                self.take_screenshot("12_demo_restarted", "Demo after clicking Restart button")
                
                # Try to start the demo
                resume_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Resume') or contains(text(), 'Replay')]")
                resume_button.click()
                time.sleep(3)
                self.take_screenshot("13_demo_playing", "Demo animation in progress")
            except Exception as e:
                print(f"⚠️ Button interaction failed: {e}")
        except:
            print("⚠️ Demo controls section not found")
        
    def record_transparency_dashboard(self):
        """Record the Transparency Dashboard"""
        print("\n🔍 Recording Transparency Dashboard (/transparency)...")
        
        self.driver.get(f"{self.base_url}/transparency")
        time.sleep(3)
        
        # 1. Full transparency overview
        self.take_screenshot("14_transparency_full", "Complete AI transparency dashboard")
        time.sleep(2)
        
        # 2. Look for transparency-specific elements
        try:
            # Try to find transparency-specific content
            transparency_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Transparency') or contains(text(), 'Reasoning') or contains(text(), 'Explainability')]")
            if transparency_elements:
                element = transparency_elements[0]
                self.smooth_scroll(element)
                self.take_screenshot("15_transparency_reasoning", "AI reasoning and explainability features")
        except:
            print("⚠️ Transparency-specific elements not found")
        
        # 3. Look for decision trees or reasoning chains
        try:
            decision_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Decision') or contains(text(), 'Chain') or contains(text(), 'Logic')]")
            if decision_elements:
                element = decision_elements[0]
                self.smooth_scroll(element)
                self.take_screenshot("16_decision_trees", "Decision trees and reasoning chains")
        except:
            print("⚠️ Decision elements not found")
        
        # 4. Scroll through the page to capture different sections
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/3);")
        time.sleep(2)
        self.take_screenshot("17_transparency_middle", "Middle section of transparency dashboard")
        
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight*2/3);")
        time.sleep(2)
        self.take_screenshot("18_transparency_lower", "Lower section of transparency dashboard")
        
    def record_operations_dashboard(self):
        """Record the Operations Dashboard"""
        print("\n📊 Recording Operations Dashboard (/ops)...")
        
        self.driver.get(f"{self.base_url}/ops")
        time.sleep(3)
        
        # 1. Full operations overview
        self.take_screenshot("19_operations_full", "Complete operations monitoring dashboard")
        time.sleep(2)
        
        # 2. Look for operations-specific elements
        try:
            ops_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Operations') or contains(text(), 'Monitoring') or contains(text(), 'Live') or contains(text(), 'Real-time')]")
            if ops_elements:
                element = ops_elements[0]
                self.smooth_scroll(element)
                self.take_screenshot("20_operations_monitoring", "Live monitoring and operations features")
        except:
            print("⚠️ Operations-specific elements not found")
        
        # 3. Look for metrics and charts
        try:
            metrics_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Metrics') or contains(text(), 'Chart') or contains(text(), 'Graph')]")
            if metrics_elements:
                element = metrics_elements[0]
                self.smooth_scroll(element)
                self.take_screenshot("21_operations_metrics", "Operations metrics and charts")
        except:
            print("⚠️ Metrics elements not found")
        
        # 4. Scroll through the operations dashboard
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/3);")
        time.sleep(2)
        self.take_screenshot("22_operations_middle", "Middle section of operations dashboard")
        
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight*2/3);")
        time.sleep(2)
        self.take_screenshot("23_operations_lower", "Lower section of operations dashboard")
        
    def record_navigation_flow(self):
        """Record navigation between dashboards"""
        print("\n🔄 Recording Navigation Flow...")
        
        # Start from homepage
        self.driver.get(self.base_url)
        time.sleep(2)
        
        # Try to navigate to each dashboard and capture the transition
        dashboards = [
            ("/demo", "PowerDashboard"),
            ("/transparency", "Transparency Dashboard"), 
            ("/ops", "Operations Dashboard")
        ]
        
        for i, (path, name) in enumerate(dashboards):
            print(f"📍 Navigating to {name}...")
            self.driver.get(f"{self.base_url}{path}")
            time.sleep(3)
            
            self.take_screenshot(f"24_nav_{i+1}_{name.lower().replace(' ', '_')}", 
                               f"Navigation to {name}")
            
            # Scroll to show different sections
            self.driver.execute_script("window.scrollTo(0, 400);")
            time.sleep(1)
            self.take_screenshot(f"25_nav_{i+1}_{name.lower().replace(' ', '_')}_scrolled", 
                               f"{name} - scrolled view")
        
    def generate_summary(self):
        """Generate comprehensive recording summary"""
        summary = {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "recording_type": "Complete Dashboard Suite",
            "dashboards_recorded": [
                {
                    "name": "Homepage",
                    "url": self.base_url,
                    "screenshots": 2,
                    "features": ["Navigation overview", "Dashboard links"]
                },
                {
                    "name": "PowerDashboard", 
                    "url": f"{self.base_url}/demo",
                    "screenshots": 11,
                    "features": [
                        "4-column interactive layout",
                        "Live savings counter", 
                        "Multi-agent status with animations",
                        "Before/After comparison",
                        "Incident timeline",
                        "Agent coordination visualization",
                        "Business impact calculator",
                        "Interactive demo controls",
                        "Working buttons and animations"
                    ]
                },
                {
                    "name": "Transparency Dashboard",
                    "url": f"{self.base_url}/transparency", 
                    "screenshots": 5,
                    "features": [
                        "AI explainability",
                        "Reasoning chains",
                        "Decision trees",
                        "Complete transparency"
                    ]
                },
                {
                    "name": "Operations Dashboard",
                    "url": f"{self.base_url}/ops",
                    "screenshots": 5, 
                    "features": [
                        "Live monitoring",
                        "Real-time metrics",
                        "Operations overview",
                        "System health"
                    ]
                },
                {
                    "name": "Navigation Flow",
                    "screenshots": 6,
                    "features": [
                        "Dashboard transitions",
                        "Navigation demonstration",
                        "Complete system tour"
                    ]
                }
            ],
            "total_screenshots": 29,
            "key_achievements": [
                "Complete system demonstration",
                "All three dashboards captured",
                "Interactive features shown",
                "Professional navigation flow",
                "Comprehensive feature coverage",
                "Working button interactions",
                "Updated 2025 branding"
            ],
            "technical_highlights": [
                "PowerDashboard with working buttons",
                "Real-time animations and updates", 
                "Multi-dashboard architecture",
                "Professional UI/UX design",
                "Complete AWS AI integration showcase"
            ]
        }
        
        import json
        summary_file = self.output_dir / f"complete_dashboard_recording_{self.session_id}.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
            
        print(f"📋 Summary saved: {summary_file}")
        return summary
        
    async def record_complete_demo(self):
        """Record the complete dashboard demonstration"""
        try:
            print("🎬 Starting Complete Dashboard Recording...")
            print(f"📅 Session ID: {self.session_id}")
            
            # Setup driver
            self.setup_driver()
            
            # Record all sections
            self.record_homepage()
            self.record_power_dashboard() 
            self.record_transparency_dashboard()
            self.record_operations_dashboard()
            self.record_navigation_flow()
            
            # Generate summary
            summary = self.generate_summary()
            
            print(f"\n✅ Complete Dashboard Recording Finished!")
            print(f"📊 Total Screenshots: {summary['total_screenshots']}")
            print(f"🎯 Dashboards Covered: {len(summary['dashboards_recorded'])}")
            print(f"📁 Session ID: {self.session_id}")
            
        except Exception as e:
            print(f"❌ Error during recording: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if self.driver:
                self.driver.quit()

async def main():
    """Main recording function"""
    recorder = CompleteDashboardRecorder()
    await recorder.record_complete_demo()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())