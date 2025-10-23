#!/usr/bin/env python3
"""
Hackathon 2025 Branding Validation Script

Validates that the PowerDashboard and related components display
the correct hackathon year (2025) and branding elements.
"""

import json
import time
from datetime import datetime
from pathlib import Path
import subprocess
import sys

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
except ImportError:
    print("Installing selenium...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "selenium"])
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

def validate_hackathon_2025_branding():
    """Validate Hackathon 2025 branding elements"""
    
    print("🏆 Validating Hackathon 2025 Branding...")
    
    # Setup Chrome driver
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # Navigate to PowerDashboard
        print("🌐 Loading PowerDashboard at http://localhost:3000/demo...")
        driver.get("http://localhost:3000/demo")
        time.sleep(3)
        
        validation_results = {
            "timestamp": datetime.now().isoformat(),
            "test_type": "Hackathon 2025 Branding Validation",
            "url": "http://localhost:3000/demo",
            "branding_elements": {},
            "overall_score": 0
        }
        
        # Test 1: Hackathon 2025 Footer Text
        print("📋 Testing Hackathon 2025 Footer Text...")
        try:
            hackathon_2025 = driver.find_element(By.XPATH, "//*[contains(text(), 'AWS Hackathon 2025')]")
            transparent_autonomous = driver.find_element(By.XPATH, "//*[contains(text(), 'World\\'s First Transparent Autonomous')]")
            incident_commander = driver.find_element(By.XPATH, "//*[contains(text(), 'Incident Commander')]")
            
            validation_results["branding_elements"]["hackathon_footer"] = {
                "status": "PASS",
                "elements_found": ["hackathon_2025", "transparent_autonomous", "incident_commander"],
                "details": "Footer displays correct Hackathon 2025 branding"
            }
            print("  ✅ Hackathon 2025 footer text validated")
        except Exception as e:
            validation_results["branding_elements"]["hackathon_footer"] = {
                "status": "FAIL",
                "error": str(e)
            }
            print(f"  ❌ Hackathon 2025 footer text failed: {e}")
        
        # Test 2: AWS AI Services Integration Text
        print("📋 Testing AWS AI Services Integration Text...")
        try:
            aws_bedrock = driver.find_element(By.XPATH, "//*[contains(text(), 'AWS Bedrock')]")
            claude_sonnet = driver.find_element(By.XPATH, "//*[contains(text(), 'Claude 3.5 Sonnet')]")
            byzantine_consensus = driver.find_element(By.XPATH, "//*[contains(text(), 'Byzantine Consensus')]")
            rag_memory = driver.find_element(By.XPATH, "//*[contains(text(), 'RAG Memory')]")
            eight_services = driver.find_element(By.XPATH, "//*[contains(text(), '8/8 AWS AI Services')]")
            
            validation_results["branding_elements"]["aws_services"] = {
                "status": "PASS",
                "elements_found": ["aws_bedrock", "claude_sonnet", "byzantine_consensus", "rag_memory", "eight_services"],
                "details": "Footer displays complete AWS AI services integration"
            }
            print("  ✅ AWS AI services integration text validated")
        except Exception as e:
            validation_results["branding_elements"]["aws_services"] = {
                "status": "FAIL",
                "error": str(e)
            }
            print(f"  ❌ AWS AI services integration text failed: {e}")
        
        # Test 3: PowerDashboard Title and Branding
        print("📋 Testing PowerDashboard Title and Branding...")
        try:
            power_dashboard_title = driver.find_element(By.XPATH, "//*[contains(text(), 'PowerDashboard - Interactive Demo')]")
            multi_agent_subtitle = driver.find_element(By.XPATH, "//*[contains(text(), 'Complete Multi-Agent Incident Response System')]")
            
            validation_results["branding_elements"]["dashboard_branding"] = {
                "status": "PASS",
                "elements_found": ["power_dashboard_title", "multi_agent_subtitle"],
                "details": "PowerDashboard displays correct title and subtitle branding"
            }
            print("  ✅ PowerDashboard title and branding validated")
        except Exception as e:
            validation_results["branding_elements"]["dashboard_branding"] = {
                "status": "FAIL",
                "error": str(e)
            }
            print(f"  ❌ PowerDashboard title and branding failed: {e}")
        
        # Test 4: Interactive Features Branding
        print("📋 Testing Interactive Features Branding...")
        try:
            live_demo_title = driver.find_element(By.XPATH, "//*[contains(text(), 'Live Incident Demo')]")
            restart_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Restart Demo')]")
            replay_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Replay Animation')]")
            
            validation_results["branding_elements"]["interactive_features"] = {
                "status": "PASS",
                "elements_found": ["live_demo_title", "restart_button", "replay_button"],
                "details": "Interactive features display correct branding and functionality"
            }
            print("  ✅ Interactive features branding validated")
        except Exception as e:
            validation_results["branding_elements"]["interactive_features"] = {
                "status": "FAIL",
                "error": str(e)
            }
            print(f"  ❌ Interactive features branding failed: {e}")
        
        # Calculate overall score
        total_tests = len(validation_results["branding_elements"])
        passed_tests = sum(1 for test in validation_results["branding_elements"].values() 
                          if test.get("status") == "PASS")
        
        overall_score = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        validation_results["overall_score"] = round(overall_score, 1)
        validation_results["test_summary"] = {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": total_tests - passed_tests
        }
        
        print(f"\n📊 Hackathon 2025 Branding Validation Summary:")
        print(f"  Total Tests: {total_tests}")
        print(f"  Passed: {passed_tests}")
        print(f"  Failed: {total_tests - passed_tests}")
        print(f"  Overall Score: {overall_score}%")
        
        if overall_score >= 90:
            print("🏆 STATUS: EXCELLENT - All Hackathon 2025 branding elements validated")
        elif overall_score >= 75:
            print("✅ STATUS: GOOD - Hackathon 2025 branding ready for submission")
        else:
            print("⚠️  STATUS: NEEDS WORK - Some branding elements need attention")
        
        # Save results
        results_file = Path("hackathon/hackathon_2025_branding_validation.json")
        with open(results_file, 'w') as f:
            json.dump(validation_results, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: {results_file}")
        
        return overall_score >= 75
        
    except Exception as e:
        print(f"❌ Critical error during validation: {e}")
        return False
    finally:
        driver.quit()

if __name__ == "__main__":
    success = validate_hackathon_2025_branding()
    sys.exit(0 if success else 1)