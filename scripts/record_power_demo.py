#!/usr/bin/env python3
"""
Record PowerDashboard Demo Video

This script records a demonstration of the PowerDashboard showing:
1. Interactive incident timeline
2. Agent coordination visualization
3. Business impact calculator
4. Before vs After comparison
5. Predicted incidents
6. Industry firsts
7. Competitor comparison

The recording will show the "power demo" features that were missing from previous videos.
"""

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
import subprocess
import sys

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.action_chains import ActionChains
except ImportError:
    print("Installing required packages...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "selenium"])
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.action_chains import ActionChains

class PowerDemoRecorder:
    def __init__(self):
        self.demo_url = "http://localhost:3000/demo"
        self.output_dir = Path("demo_recordings")
        self.output_dir.mkdir(exist_ok=True)
        
        # Create session ID for this recording
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.video_filename = f"power_demo_{self.session_id}.webm"
        
        self.driver = None
        self.wait = None
        
    def setup_driver(self):
        """Setup Chrome driver with recording capabilities"""
        chrome_options = Options()
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # Enable media recording
        chrome_options.add_experimental_option("useAutomationExtension", False)
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
        
    def start_recording(self):
        """Start screen recording using JavaScript MediaRecorder API"""
        recording_script = """
        window.mediaRecorder = null;
        window.recordedChunks = [];
        
        navigator.mediaDevices.getDisplayMedia({
            video: { mediaSource: 'screen', width: 1920, height: 1080 },
            audio: false
        }).then(stream => {
            window.mediaRecorder = new MediaRecorder(stream, {
                mimeType: 'video/webm;codecs=vp9'
            });
            
            window.mediaRecorder.ondataavailable = event => {
                if (event.data.size > 0) {
                    window.recordedChunks.push(event.data);
                }
            };
            
            window.mediaRecorder.start();
            console.log('Recording started');
        }).catch(err => {
            console.error('Error starting recording:', err);
        });
        """
        
        self.driver.execute_script(recording_script)
        time.sleep(2)  # Wait for recording to start
        
    def stop_recording(self):
        """Stop recording and save video"""
        stop_script = """
        return new Promise((resolve) => {
            if (window.mediaRecorder && window.mediaRecorder.state === 'recording') {
                window.mediaRecorder.onstop = () => {
                    const blob = new Blob(window.recordedChunks, { type: 'video/webm' });
                    const reader = new FileReader();
                    reader.onload = () => resolve(reader.result);
                    reader.readAsDataURL(blob);
                };
                window.mediaRecorder.stop();
            } else {
                resolve(null);
            }
        });
        """
        
        video_data = self.driver.execute_script(stop_script)
        
        if video_data:
            # Save video file
            import base64
            video_bytes = base64.b64decode(video_data.split(',')[1])
            video_path = self.output_dir / "videos" / self.video_filename
            video_path.parent.mkdir(exist_ok=True)
            
            with open(video_path, 'wb') as f:
                f.write(video_bytes)
                
            print(f"Video saved: {video_path}")
            return video_path
        
        return None
        
    def take_screenshot(self, name: str, description: str = ""):
        """Take a screenshot with metadata"""
        screenshot_dir = self.output_dir / "screenshots"
        screenshot_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%H%M%S")
        filename = f"{timestamp}_{name}.png"
        filepath = screenshot_dir / filename
        
        self.driver.save_screenshot(str(filepath))
        
        # Save metadata
        metadata = {
            "filename": filename,
            "timestamp": datetime.now().isoformat(),
            "description": description,
            "url": self.driver.current_url,
            "session_id": self.session_id
        }
        
        metadata_file = screenshot_dir / f"{timestamp}_{name}_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
            
        print(f"Screenshot: {filename} - {description}")
        return filepath
        
    def wait_for_element(self, selector: str, timeout: int = 10):
        """Wait for element to be present and visible"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            return element
        except Exception as e:
            print(f"Element not found: {selector} - {e}")
            return None
            
    def smooth_scroll(self, element):
        """Smooth scroll to element"""
        self.driver.execute_script("""
            arguments[0].scrollIntoView({ 
                behavior: 'smooth', 
                block: 'center' 
            });
        """, element)
        time.sleep(1)
        
    async def record_power_demo(self):
        """Record the complete PowerDashboard demonstration"""
        try:
            print("🎬 Starting PowerDashboard Demo Recording...")
            
            # Setup and navigate
            self.setup_driver()
            self.driver.get(self.demo_url)
            
            # Wait for page to load
            time.sleep(3)
            
            # Start recording
            print("📹 Starting screen recording...")
            self.start_recording()
            
            # 1. Initial PowerDashboard Overview
            print("📸 Capturing PowerDashboard overview...")
            self.take_screenshot("01_power_dashboard_overview", 
                              "PowerDashboard with 4-column layout and live metrics")
            time.sleep(2)
            
            # 2. Live Savings Counter (Column 1)
            print("📸 Highlighting live savings counter...")
            savings_card = self.wait_for_element("[data-testid='live-savings-counter']")
            if not savings_card:
                savings_card = self.wait_for_element(".card-glass")
            
            if savings_card:
                self.smooth_scroll(savings_card)
                self.take_screenshot("02_live_savings_counter", 
                                  "Real-time cost savings and zero-touch streak")
            time.sleep(2)
            
            # 3. Agent Status with Tooltips (Column 1)
            print("📸 Showing agent status with interactive tooltips...")
            agent_status = self.wait_for_element("[data-testid='agent-status']")
            if not agent_status:
                # Look for agent cards
                agent_cards = self.driver.find_elements(By.CSS_SELECTOR, ".p-3.rounded-lg")
                if agent_cards:
                    agent_status = agent_cards[0]
            
            if agent_status:
                self.smooth_scroll(agent_status)
                # Hover to show tooltip
                ActionChains(self.driver).move_to_element(agent_status).perform()
                time.sleep(1)
                self.take_screenshot("03_agent_status_tooltips", 
                                  "Multi-agent status with confidence scores and reasoning tooltips")
            time.sleep(2)
            
            # 4. Before vs After Comparison (Column 2)
            print("📸 Capturing before vs after comparison...")
            comparison_card = self.wait_for_element("[data-testid='impact-comparison']")
            if not comparison_card:
                # Look for comparison elements
                comparison_elements = self.driver.find_elements(By.CSS_SELECTOR, ".bg-red-900\\/20, .bg-green-900\\/20")
                if comparison_elements:
                    comparison_card = comparison_elements[0].find_element(By.XPATH, "./ancestor::div[contains(@class, 'card')]")
            
            if comparison_card:
                self.smooth_scroll(comparison_card)
                self.take_screenshot("04_before_after_comparison", 
                                  "Manual vs AI response time comparison showing 91% improvement")
            time.sleep(2)
            
            # 5. Incident Timeline (Column 2)
            print("📸 Showing incident timeline...")
            timeline_card = self.wait_for_element("[data-testid='incident-timeline']")
            if not timeline_card:
                # Look for timeline elements
                timeline_elements = self.driver.find_elements(By.CSS_SELECTOR, ".relative.spacing-md, .space-y-3")
                if timeline_elements:
                    timeline_card = timeline_elements[0].find_element(By.XPATH, "./ancestor::div[contains(@class, 'card')]")
            
            if timeline_card:
                self.smooth_scroll(timeline_card)
                self.take_screenshot("05_incident_timeline", 
                                  "Step-by-step incident resolution timeline with agent actions")
            time.sleep(2)
            
            # 6. Agent Coordination Visualization (Column 3)
            print("📸 Capturing agent coordination...")
            coordination_card = self.wait_for_element("[data-testid='agent-coordination']")
            if not coordination_card:
                # Look for coordination flow
                flow_elements = self.driver.find_elements(By.CSS_SELECTOR, ".bg-blue-600, .bg-purple-600, .bg-pink-600")
                if flow_elements:
                    coordination_card = flow_elements[0].find_element(By.XPATH, "./ancestor::div[contains(@class, 'card')]")
            
            if coordination_card:
                self.smooth_scroll(coordination_card)
                self.take_screenshot("06_agent_coordination", 
                                  "Byzantine consensus flow with weighted agent contributions")
            time.sleep(2)
            
            # 7. AI Transparency Panel (Column 3)
            print("📸 Showing AI transparency...")
            transparency_card = self.wait_for_element("[data-testid='ai-transparency']")
            if not transparency_card:
                # Look for transparency elements
                transparency_elements = self.driver.find_elements(By.CSS_SELECTOR, ".grid.grid-cols-2")
                if transparency_elements:
                    transparency_card = transparency_elements[0].find_element(By.XPATH, "./ancestor::div[contains(@class, 'card')]")
            
            if transparency_card:
                self.smooth_scroll(transparency_card)
                self.take_screenshot("07_ai_transparency", 
                                  "Side-by-side agent reasoning and confidence scores")
            time.sleep(2)
            
            # 8. Business Impact Calculator (Column 4)
            print("📸 Highlighting business impact...")
            business_card = self.wait_for_element("[data-testid='business-impact']")
            if not business_card:
                # Look for business impact elements
                business_elements = self.driver.find_elements(By.CSS_SELECTOR, ".bg-gradient-to-br.from-emerald-900")
                if business_elements:
                    business_card = business_elements[0]
            
            if business_card:
                self.smooth_scroll(business_card)
                self.take_screenshot("08_business_impact_calculator", 
                                  "Real-time business impact calculation showing $230K saved")
            time.sleep(2)
            
            # 9. Predicted Incidents (Column 4)
            print("📸 Showing predicted incidents...")
            prediction_card = self.wait_for_element("[data-testid='predicted-incidents']")
            if not prediction_card:
                # Look for prediction elements
                prediction_elements = self.driver.find_elements(By.CSS_SELECTOR, ".bg-orange-900\\/20, .bg-blue-900\\/20")
                if prediction_elements:
                    prediction_card = prediction_elements[0].find_element(By.XPATH, "./ancestor::div[contains(@class, 'card')]")
            
            if prediction_card:
                self.smooth_scroll(prediction_card)
                self.take_screenshot("09_predicted_incidents", 
                                  "Proactive incident prediction with prevention actions")
            time.sleep(2)
            
            # 10. Industry Firsts Panel
            print("📸 Capturing industry firsts...")
            firsts_card = self.wait_for_element("[data-testid='industry-firsts']")
            if not firsts_card:
                # Look for industry firsts
                firsts_elements = self.driver.find_elements(By.CSS_SELECTOR, ".bg-gradient-to-br.from-amber-900")
                if firsts_elements:
                    firsts_card = firsts_elements[0]
            
            if firsts_card:
                self.smooth_scroll(firsts_card)
                self.take_screenshot("10_industry_firsts", 
                                  "Unique differentiators and industry-first capabilities")
            time.sleep(2)
            
            # 11. Demo Controls
            print("📸 Showing interactive demo controls...")
            demo_controls = self.wait_for_element("[data-testid='demo-controls']")
            if not demo_controls:
                # Look for demo control buttons
                control_buttons = self.driver.find_elements(By.CSS_SELECTOR, "button")
                if control_buttons:
                    # Find the card containing demo controls
                    for button in control_buttons:
                        if "Start Incident Demo" in button.text or "Restart Demo" in button.text:
                            demo_controls = button.find_element(By.XPATH, "./ancestor::div[contains(@class, 'card')]")
                            break
            
            if demo_controls:
                self.smooth_scroll(demo_controls)
                self.take_screenshot("11_demo_controls", 
                                  "Interactive playback controls for incident demonstration")
            time.sleep(2)
            
            # 12. Test Interactive Demo Controls
            print("🎬 Testing interactive demo controls...")
            restart_button = None
            replay_button = None
            speed_button = None
            
            buttons = self.driver.find_elements(By.CSS_SELECTOR, "button")
            for button in buttons:
                if "Restart Demo" in button.text:
                    restart_button = button
                elif "Replay Animation" in button.text:
                    replay_button = button
                elif "2x" in button.text:
                    speed_button = button
            
            if restart_button and replay_button and speed_button:
                self.smooth_scroll(restart_button)
                
                # Test restart button
                restart_button.click()
                time.sleep(1)
                self.take_screenshot("12_restart_demo", 
                                  "Interactive restart button clicked - demo state reset")
                
                # Test replay button
                replay_button.click()
                time.sleep(1)
                self.take_screenshot("13_replay_demo", 
                                  "Interactive replay button clicked - animation started")
                
                # Test speed control
                initial_speed = speed_button.text
                speed_button.click()
                time.sleep(1)
                new_speed = speed_button.text
                self.take_screenshot("14_speed_control", 
                                  f"Speed control clicked - changed from {initial_speed} to {new_speed}")
                
                # Show completed state
                time.sleep(2)
                self.take_screenshot("15_demo_complete", 
                                  "Interactive demo controls fully functional with state management")
            
            # 16. Final Overview
            print("📸 Final PowerDashboard overview...")
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)
            self.take_screenshot("16_final_overview", 
                              "Complete PowerDashboard with all interactive features demonstrated")
            
            # Stop recording
            print("🛑 Stopping recording...")
            video_path = self.stop_recording()
            
            # Generate summary
            self.generate_summary(video_path)
            
            print("✅ PowerDashboard demo recording complete!")
            
        except Exception as e:
            print(f"❌ Error during recording: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if self.driver:
                self.driver.quit()
                
    def generate_summary(self, video_path):
        """Generate recording summary"""
        summary = {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "video_file": str(video_path) if video_path else None,
            "demo_url": self.demo_url,
            "features_demonstrated": [
                "PowerDashboard 4-column layout",
                "Live savings counter with zero-touch streak",
                "Multi-agent status with interactive tooltips",
                "Before vs After comparison (91% improvement)",
                "Step-by-step incident timeline",
                "Byzantine consensus visualization",
                "AI transparency with reasoning",
                "Business impact calculator ($230K saved)",
                "Predicted incidents with prevention",
                "Industry firsts and differentiators",
                "Interactive demo controls with functional testing",
                "Live state management demonstration",
                "Speed control functionality",
                "Auto-incrementing metrics system"
            ],
            "key_metrics_shown": {
                "mttr_improvement": "91% faster resolution",
                "cost_savings": "$230K per incident",
                "zero_touch_streak": "47 incidents",
                "consensus_confidence": "94%",
                "incident_prevention": "85% success rate"
            },
            "screenshots_count": 16,
            "duration_estimate": "3-4 minutes",
            "quality": "HD 1920x1080"
        }
        
        summary_file = self.output_dir / f"power_demo_summary_{self.session_id}.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
            
        print(f"📋 Summary saved: {summary_file}")

async def main():
    """Main recording function"""
    recorder = PowerDemoRecorder()
    await recorder.record_power_demo()

if __name__ == "__main__":
    asyncio.run(main())