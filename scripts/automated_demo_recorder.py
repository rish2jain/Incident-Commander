#!/usr/bin/env python3
"""
Automated Demo Recorder for Incident Commander
Uses Playwright to automate demo execution with video recording and screenshots

Features:
- Full video recording of demo
- Screenshots at key decision points
- Automated metric collection
- 3-minute demo execution
- Judge-ready output
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from playwright.async_api import async_playwright, Page, Browser, BrowserContext


class DemoRecorder:
    """Automated demo recorder with video and screenshot capture"""

    def __init__(
        self,
        base_url: str = "http://localhost:3000",
        output_dir: str = "demo_recordings",
        video_width: int = 1920,
        video_height: int = 1080,
        dashboard_type: str = "enhanced",  # "enhanced" or "standalone"
    ):
        self.base_url = base_url
        self.dashboard_type = dashboard_type
        self.output_dir = Path(output_dir)
        self.video_width = video_width
        self.video_height = video_height
        self.screenshots_dir = self.output_dir / "screenshots"
        self.videos_dir = self.output_dir / "videos"
        self.metrics_dir = self.output_dir / "metrics"

        # Create output directories
        for directory in [self.screenshots_dir, self.videos_dir, self.metrics_dir]:
            directory.mkdir(parents=True, exist_ok=True)

        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.metrics: Dict = {
            "session_id": self.session_id,
            "start_time": None,
            "end_time": None,
            "duration_seconds": 0,
            "screenshots_captured": [],
            "incidents_triggered": [],
            "agent_activities": [],
            "business_metrics": {},
            "audio_notifications": [],
            "sound_pack_tested": None,
        }

    async def setup_browser(self) -> tuple[Browser, BrowserContext, Page]:
        """Initialize browser with video recording configuration"""
        self.playwright = await async_playwright().start()

        # Launch browser with optimal settings
        browser = await self.playwright.chromium.launch(
            headless=False,  # Show browser for demo visibility
            args=[
                '--start-maximized',
                '--disable-blink-features=AutomationControlled',
            ]
        )

        # Create context with video recording
        context = await browser.new_context(
            viewport={'width': self.video_width, 'height': self.video_height},
            record_video_dir=str(self.videos_dir),
            record_video_size={'width': self.video_width, 'height': self.video_height},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        )

        # Create page
        page = await context.new_page()

        return browser, context, page

    async def cleanup(self):
        """Clean up Playwright resources"""
        if hasattr(self, 'playwright') and self.playwright:
            await self.playwright.stop()

    async def capture_screenshot(
        self,
        page: Page,
        name: str,
        description: str = "",
    ) -> str:
        """Capture screenshot at key moment"""
        timestamp = datetime.now().strftime("%H%M%S")
        filename = f"{timestamp}_{name}.png"
        filepath = self.screenshots_dir / filename

        await page.screenshot(
            path=str(filepath),
            full_page=False,  # Capture viewport only
            type='png',
        )

        # Extract current metrics from page for better descriptions
        try:
            mttr = await page.query_selector('[data-test="mttr-value"]')
            mttr_value = await mttr.inner_text() if mttr else "unknown"
            
            cost_saved = await page.query_selector('[data-test="cost-saved"]')
            cost_value = await cost_saved.inner_text() if cost_saved else "unknown"
            
            incidents = await page.query_selector('[data-test="incidents-resolved"]')
            incidents_value = await incidents.inner_text() if incidents else "unknown"
            
            # Enhance description with actual values
            enhanced_description = f"{description} | MTTR: {mttr_value} | Cost: {cost_value} | Incidents: {incidents_value}"
        except Exception:
            enhanced_description = description

        self.metrics["screenshots_captured"].append({
            "timestamp": timestamp,
            "name": name,
            "description": enhanced_description,
            "filepath": str(filepath),
        })

        print(f"📸 Screenshot captured: {name}")
        print(f"   Metrics: {enhanced_description}")
        return str(filepath)

    async def wait_for_agent_activity(
        self,
        page: Page,
        timeout: int = 30000,
    ) -> bool:
        """Wait for agent activity to appear on dashboard"""
        try:
            # Wait for agent communication panel to show activity
            await page.wait_for_selector(
                '[data-test="agent-activity"]',
                timeout=timeout,
            )
            return True
        except Exception as e:
            print(f"⚠️ Agent activity timeout: {e}")
            return False

    async def trigger_incident(
        self,
        page: Page,
        incident_type: str = "database_cascade",
    ) -> Dict:
        """Trigger incident via dashboard button"""
        print(f"\n🚨 Triggering {incident_type} incident...")

        # Map incident types to button text
        incident_text_map = {
            "database_cascade": "Trigger Database Cascade Incident",
            "database": "Trigger Database Cascade Incident",
            "ddos_attack": "DDoS Attack", 
            "ddos": "DDoS Attack",
            "memory_leak": "Memory Leak",
            "memory": "Memory Leak",
            "api_overload": "API Overload",
            "api": "API Overload",
            "storage_failure": "Storage Failure",
            "storage": "Storage Failure"
        }
        
        button_text = incident_text_map.get(incident_type, "Database Cascade")
        
        # Click trigger button by text content
        try:
            await page.click(f'button:has-text("{button_text}")', timeout=10000)
        except Exception as e:
            print(f"⚠️ Could not find button with text '{button_text}', trying alternative selectors...")
            # Fallback: try clicking any button containing the text
            await page.click(f'text="{button_text}"', timeout=10000)

        # Capture incident trigger moment
        await self.capture_screenshot(
            page,
            f"incident_triggered_{incident_type}",
            f"Incident {incident_type} triggered",
        )

        incident_data = {
            "type": incident_type,
            "triggered_at": datetime.now().isoformat(),
        }

        self.metrics["incidents_triggered"].append(incident_data)
        return incident_data

    async def monitor_agent_consensus(
        self,
        page: Page,
        duration: int = 60,
    ) -> List[Dict]:
        """Monitor agent consensus process"""
        print(f"\n🤖 Monitoring agent consensus for {duration}s...")

        activities = []
        start_time = asyncio.get_event_loop().time()
        screenshot_interval = 15  # Screenshot every 15 seconds
        last_screenshot = 0

        while (asyncio.get_event_loop().time() - start_time) < duration:
            elapsed = asyncio.get_event_loop().time() - start_time

            # Capture periodic screenshots
            if elapsed - last_screenshot >= screenshot_interval:
                await self.capture_screenshot(
                    page,
                    f"consensus_progress_{int(elapsed)}s",
                    f"Byzantine consensus at {int(elapsed)}s",
                )
                last_screenshot = elapsed

            # Check for agent messages
            try:
                agent_messages = await page.query_selector_all('[data-test="agent-message"]')
                if agent_messages:
                    for msg in agent_messages[-3:]:  # Last 3 messages
                        text = await msg.inner_text()
                        activities.append({
                            "timestamp": datetime.now().isoformat(),
                            "message": text,
                        })
            except Exception as e:
                print(f"⚠️ Error reading messages: {e}")

            await asyncio.sleep(1)

        self.metrics["agent_activities"].extend(activities)
        return activities

    async def capture_resolution_metrics(
        self,
        page: Page,
    ) -> Dict:
        """Capture final resolution metrics"""
        print("\n📊 Capturing resolution metrics...")

        metrics = {}

        try:
            # MTTR metric
            mttr_element = await page.query_selector('[data-test="mttr-value"]')
            if mttr_element:
                metrics["mttr"] = await mttr_element.inner_text()

            # Cost savings
            cost_element = await page.query_selector('[data-test="cost-saved"]')
            if cost_element:
                metrics["cost_saved"] = await cost_element.inner_text()

            # Affected users
            users_element = await page.query_selector('[data-test="affected-users"]')
            if users_element:
                metrics["affected_users"] = await users_element.inner_text()

            # Capture final state
            await self.capture_screenshot(
                page,
                "final_resolution",
                "Incident resolved - final metrics",
            )

        except Exception as e:
            print(f"⚠️ Error capturing metrics: {e}")

        self.metrics["business_metrics"] = metrics
        return metrics

    async def run_3min_demo(self) -> Dict:
        """Execute complete 3-minute demo"""
        print("\n" + "="*80)
        print("🎬 Starting Automated Demo Recording")
        print(f"📁 Output directory: {self.output_dir}")
        print("="*80)

        self.metrics["start_time"] = datetime.now().isoformat()

        browser = None
        context = None

        try:
            # Setup browser
            print("\n🌐 Launching browser...")
            browser, context, page = await self.setup_browser()

            # Navigate to dashboard
            print(f"\n🔗 Navigating to {self.base_url}...")
            await page.goto(self.base_url)
            await page.wait_for_load_state('networkidle')

            # Capture initial dashboard
            await self.capture_screenshot(
                page,
                "dashboard_initial",
                "Dashboard loaded - ready state",
            )

            # Wait for dashboard to be ready and auto-demo to trigger
            print("\n⏳ Waiting for dashboard initialization and auto-demo trigger...")
            await asyncio.sleep(5)  # Extra time for auto-demo to start

            # PHASE 1: Auto-triggered incident (0:00-0:10)
            # Note: Incident should auto-trigger with auto-demo=true parameter
            # Capture the auto-triggered incident
            await self.capture_screenshot(
                page,
                "auto_incident_triggered",
                "Auto-demo incident triggered via URL parameter",
            )
            await asyncio.sleep(2)

            # PHASE 2: Agent discovery and analysis (0:10-0:40)
            print("\n🔍 Phase 2: Agent Discovery & Analysis (30s)")
            await self.monitor_agent_consensus(page, duration=30)

            # Capture mid-demo state
            await self.capture_screenshot(
                page,
                "agents_analyzing",
                "Agents performing Byzantine consensus",
            )

            # PHASE 3: Consensus and decision (0:40-1:20)
            print("\n🤝 Phase 3: Byzantine Consensus (40s)")
            await self.monitor_agent_consensus(page, duration=40)

            # Capture consensus reached
            await self.capture_screenshot(
                page,
                "consensus_reached",
                "Consensus reached - executing remediation",
            )

            # PHASE 4: Remediation execution (1:20-2:20)
            print("\n⚡ Phase 4: Remediation Execution (60s)")
            await asyncio.sleep(60)

            await self.capture_screenshot(
                page,
                "remediation_executing",
                "Automated remediation in progress",
            )

            # PHASE 5: Verification and metrics (2:20-3:00)
            print("\n✅ Phase 5: Verification & Metrics (40s)")
            await asyncio.sleep(30)

            # Capture final metrics
            metrics = await self.capture_resolution_metrics(page)

            # Final screenshot
            await self.capture_screenshot(
                page,
                "demo_complete",
                "Demo complete - all metrics captured",
            )

            print("\n✅ Demo execution complete!")

        except Exception as e:
            print(f"\n❌ Demo execution error: {e}")
            self.metrics["error"] = str(e)

            # Capture error state
            if 'page' in locals():
                await self.capture_screenshot(
                    page,
                    "error_state",
                    f"Error occurred: {str(e)}",
                )

        finally:
            # Record end time
            self.metrics["end_time"] = datetime.now().isoformat()

            if self.metrics["start_time"] and self.metrics["end_time"]:
                start = datetime.fromisoformat(self.metrics["start_time"])
                end = datetime.fromisoformat(self.metrics["end_time"])
                self.metrics["duration_seconds"] = (end - start).total_seconds()

            # Save metrics
            metrics_file = self.metrics_dir / f"demo_metrics_{self.session_id}.json"
            with open(metrics_file, 'w') as f:
                json.dump(self.metrics, f, indent=2)

            print(f"\n📊 Metrics saved: {metrics_file}")

            # Close browser (video auto-saved)
            if context:
                await context.close()
                print(f"\n🎥 Video saved to: {self.videos_dir}")

            if browser:
                await browser.close()

        return self.metrics

    async def run_custom_demo(
        self,
        scenario: str,
        duration: int = 180,
    ) -> Dict:
        """Run custom demo with specified scenario and duration"""
        print(f"\n🎯 Running custom demo: {scenario} ({duration}s)")
        # Implementation for custom scenarios
        return await self.run_3min_demo()


async def main():
    """Main demo recorder entry point"""
    # Configuration
    dashboard_type = os.getenv("DASHBOARD_TYPE", "insights")  # "insights", "react", "enhanced", or "standalone"
    
    if dashboard_type == "standalone":
        default_url = "http://localhost:3000/standalone.html"
    elif dashboard_type == "react":
        default_url = "http://localhost:3000/simple-demo?auto-demo=true"
    elif dashboard_type == "insights":
        default_url = "http://localhost:3000/enhanced-insights-demo?auto-demo=true"
    else:
        default_url = "http://localhost:3000/agent_actions_dashboard.html?auto-demo=true"
    
    config = {
        "base_url": os.getenv("DEMO_URL", default_url),
        "output_dir": "demo_recordings",
        "video_width": 1920,
        "video_height": 1080,
        "dashboard_type": dashboard_type,
    }

    print("\n" + "="*80)
    print("🎬 INCIDENT COMMANDER - AUTOMATED DEMO RECORDER")
    print("="*80)
    print(f"\n📋 Configuration:")
    print(f"   Dashboard URL: {config['base_url']}")
    print(f"   Output Directory: {config['output_dir']}")
    print(f"   Video Resolution: {config['video_width']}x{config['video_height']}")
    print("\n" + "="*80)

    # Create recorder
    recorder = DemoRecorder(**config)

    # Run demo
    metrics = await recorder.run_3min_demo()

    # Print summary
    print("\n" + "="*80)
    print("📊 DEMO RECORDING SUMMARY")
    print("="*80)
    print(f"Session ID: {metrics['session_id']}")
    print(f"Duration: {metrics['duration_seconds']:.1f}s")
    print(f"Screenshots: {len(metrics['screenshots_captured'])}")
    print(f"Incidents: {len(metrics['incidents_triggered'])}")
    print(f"Agent Activities: {len(metrics['agent_activities'])}")
    print(f"\n📁 Output Location: {recorder.output_dir}")
    print("="*80)

    return metrics


if __name__ == "__main__":
    asyncio.run(main())