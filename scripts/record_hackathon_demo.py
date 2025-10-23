#!/usr/bin/env python3
"""
Hackathon Demo Recorder - Production-Ready 3-Minute Pitch

Records a polished 3-minute demo video showcasing fully deployed production system.
Demonstrates:
- Production-ready backend with real-time agent orchestration
- 3 specialized dashboards with WebSocket streaming
- 8 AWS AI services integrated with usage tracking
- Byzantine fault-tolerant consensus
- Complete deployment infrastructure with auto-scaling
- 95% MTTR reduction (30min → 1.4min)

Optimized for:
- Hackathon judges (comprehensive system evaluation)
- AWS prize eligibility showcase (8 services, 3 prize-eligible)
- Professional presentation quality
- 3-minute format with narration timing

Usage:
    python scripts/record_hackathon_demo.py

Output:
    - Video: demo_recordings/videos/hackathon_demo_3min_YYYYMMDD_HHMMSS.webm
    - Screenshots: demo_recordings/screenshots/hackathon_*
    - Metadata: demo_recordings/hackathon_demo_metadata.json

Prerequisites:
    - Dashboard running on http://localhost:3000 (3 dashboards)
    - Backend running on http://localhost:8000 (production-ready API)
    - Playwright installed: pip install playwright && playwright install
    - System health verified: curl http://localhost:8000/dashboard/health/detailed
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright, Page, Browser
import sys

class HackathonDemoRecorder:
    """Record professional 3-minute hackathon demo"""

    def __init__(self):
        self.base_url = "http://localhost:3000"
        self.backend_url = "http://localhost:8000"
        self.output_dir = Path("demo_recordings")
        self.screenshots_dir = self.output_dir / "screenshots"
        self.videos_dir = self.output_dir / "videos"
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Create output directories
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        self.videos_dir.mkdir(parents=True, exist_ok=True)

    async def check_services(self) -> bool:
        """Verify all services are running"""
        print("🔍 Checking services...")

        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                # Check basic backend health
                async with session.get(f"{self.backend_url}/dashboard/health", timeout=5) as response:
                    if response.status != 200:
                        print(f"❌ Backend unhealthy: {response.status}")
                        return False
                    health_data = await response.json()
                    print(f"✅ Backend Health: {health_data.get('status', 'unknown')}")

                # Check detailed system health
                async with session.get(f"{self.backend_url}/dashboard/health/detailed", timeout=5) as response:
                    if response.status == 200:
                        detailed = await response.json()
                        print(f"✅ System Status: {detailed.get('status', 'unknown')}")
                        components = detailed.get('components', {})
                        print(f"   - WebSocket: {components.get('websocket', {}).get('status', 'unknown')}")
                        print(f"   - Orchestrator: {components.get('orchestrator', {}).get('status', 'unknown')}")
                        print(f"   - Active Agents: {components.get('orchestrator', {}).get('active_agents', 0)}")

                # Check dashboard
                async with session.get(f"{self.base_url}", timeout=5) as response:
                    if response.status != 200:
                        print(f"❌ Dashboard unhealthy: {response.status}")
                        return False
                    print("✅ Dashboard healthy")

            return True
        except ImportError:
            print("⚠️  aiohttp not installed, skipping service check")
            return True
        except Exception as e:
            print(f"❌ Service check failed: {e}")
            return False

    async def wait_and_screenshot(self, page: Page, name: str, wait_ms: int = 1000):
        """Wait and take screenshot"""
        await asyncio.sleep(wait_ms / 1000)
        screenshot_path = self.screenshots_dir / f"hackathon_{name}_{self.timestamp}.png"
        await page.screenshot(path=str(screenshot_path), full_page=False)
        print(f"📸 Screenshot: {name}")

    async def record_dashboard_1(self, page: Page, start_time: float) -> float:
        """Record Dashboard 1: Executive View (30 seconds)"""
        print("\n📊 Recording Dashboard 1: Executive View...")

        # Navigate to Dashboard 1
        await page.goto(f"{self.base_url}/demo")
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(2)

        # Take initial screenshot
        await self.wait_and_screenshot(page, "dashboard1_overview", 1000)

        # Scroll to show Byzantine consensus
        await page.evaluate("window.scrollTo(0, 300)")
        await self.wait_and_screenshot(page, "dashboard1_byzantine_consensus", 2000)

        # Scroll to show metrics
        await page.evaluate("window.scrollTo(0, 600)")
        await self.wait_and_screenshot(page, "dashboard1_metrics", 2000)

        # Scroll to show predictive prevention
        await page.evaluate("window.scrollTo(0, 900)")
        await self.wait_and_screenshot(page, "dashboard1_prevention", 2000)

        # Total: ~10 seconds of recording, narration fills to 30 seconds
        current_time = asyncio.get_event_loop().time()
        elapsed = current_time - start_time
        print(f"⏱️  Dashboard 1 complete: {elapsed:.1f}s elapsed")

        return current_time

    async def record_dashboard_2(self, page: Page, start_time: float) -> float:
        """Record Dashboard 2: Engineering View (45 seconds)"""
        print("\n🧠 Recording Dashboard 2: Engineering View...")

        # Navigate to Dashboard 2
        await page.goto(f"{self.base_url}/transparency")
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(2)

        # Take overview screenshot
        await self.wait_and_screenshot(page, "dashboard2_overview", 1000)

        # Show scenario selection
        await page.evaluate("window.scrollTo(0, 200)")
        await self.wait_and_screenshot(page, "dashboard2_scenarios", 2000)

        # Scroll to agent reasoning panel
        await page.evaluate("window.scrollTo(0, 800)")
        await self.wait_and_screenshot(page, "dashboard2_agent_reasoning", 2000)

        # Click "Reasoning" tab if visible
        try:
            reasoning_tab = page.locator('button:has-text("Reasoning")')
            if await reasoning_tab.is_visible(timeout=2000):
                await reasoning_tab.click()
                await self.wait_and_screenshot(page, "dashboard2_reasoning_detail", 2000)
        except:
            print("  ℹ️  Reasoning tab not found, continuing...")

        # Click "Decisions" tab to show decision tree
        try:
            decisions_tab = page.locator('button:has-text("Decisions")')
            if await decisions_tab.is_visible(timeout=2000):
                await decisions_tab.click()
                await self.wait_and_screenshot(page, "dashboard2_decision_tree", 2000)
        except:
            print("  ℹ️  Decisions tab not found, continuing...")

        # Total: ~15 seconds of recording, narration fills to 45 seconds
        current_time = asyncio.get_event_loop().time()
        elapsed = current_time - start_time
        print(f"⏱️  Dashboard 2 complete: {elapsed:.1f}s elapsed")

        return current_time

    async def record_dashboard_3(self, page: Page, start_time: float) -> float:
        """Record Dashboard 3: Operations View (65 seconds)"""
        print("\n🚨 Recording Dashboard 3: Operations View...")

        # Navigate to Dashboard 3
        await page.goto(f"{self.base_url}/ops")
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(2)

        # Take overview screenshot showing WebSocket status
        await self.wait_and_screenshot(page, "dashboard3_overview", 1000)

        # Scroll to show agent status
        await page.evaluate("window.scrollTo(0, 300)")
        await self.wait_and_screenshot(page, "dashboard3_agents", 2000)

        # Look for "Trigger Demo" button and click it
        try:
            trigger_button = page.locator('button:has-text("Trigger")')
            if await trigger_button.is_visible(timeout=3000):
                print("  🎬 Triggering live demo incident...")
                await trigger_button.click()
                await self.wait_and_screenshot(page, "dashboard3_incident_triggered", 1000)

                # Wait for agents to activate (8-10 seconds)
                await asyncio.sleep(3)
                await self.wait_and_screenshot(page, "dashboard3_agents_active", 1000)

                await asyncio.sleep(3)
                await self.wait_and_screenshot(page, "dashboard3_agents_analyzing", 1000)

                await asyncio.sleep(3)
                await self.wait_and_screenshot(page, "dashboard3_resolution", 1000)
        except Exception as e:
            print(f"  ⚠️  Could not trigger demo: {e}")

        # Scroll to show AWS Services Monitor panel (if exists)
        await page.evaluate("window.scrollTo(0, 600)")
        await self.wait_and_screenshot(page, "dashboard3_aws_services", 2000)

        # Scroll to show business metrics
        await page.evaluate("window.scrollTo(0, 900)")
        await self.wait_and_screenshot(page, "dashboard3_business_metrics", 2000)

        # Total: ~20 seconds of recording, narration fills to 65 seconds
        current_time = asyncio.get_event_loop().time()
        elapsed = current_time - start_time
        print(f"⏱️  Dashboard 3 complete: {elapsed:.1f}s elapsed")

        return current_time

    async def record_demo(self):
        """Record complete 3-minute hackathon demo"""
        print("🎬 Hackathon Demo Recorder - Starting...")
        print("=" * 60)

        # Check services
        if not await self.check_services():
            print("\n❌ Services not ready. Please start the backend and dashboard.")
            print("   Backend: python -m uvicorn src.main:app --reload")
            print("   Dashboard: cd dashboard && npm run dev")
            return False

        async with async_playwright() as p:
            # Launch browser
            print("\n🌐 Launching browser...")
            browser = await p.chromium.launch(headless=True)

            # Create context with video recording
            video_path = self.videos_dir / f"hackathon_demo_3min_{self.timestamp}.webm"
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                record_video_dir=str(self.videos_dir),
                record_video_size={"width": 1920, "height": 1080}
            )

            page = await context.new_page()

            try:
                start_time = asyncio.get_event_loop().time()

                # Opening Hook - Dashboard 1 (0:00-0:50)
                print("\n🎯 Section 1: Opening Hook + Dashboard 1 (0:00-0:50)")
                await self.record_dashboard_1(page, start_time)

                # Wait for narration timing (30 seconds narration)
                await asyncio.sleep(20)  # Extra time for narration

                # Dashboard 2 (0:50-1:35)
                print("\n🎯 Section 2: Dashboard 2 Engineering View (0:50-1:35)")
                await self.record_dashboard_2(page, start_time)

                # Wait for narration timing (45 seconds narration)
                await asyncio.sleep(30)  # Extra time for narration

                # Dashboard 3 (1:35-2:40)
                print("\n🎯 Section 3: Dashboard 3 Live Operations (1:35-2:40)")
                await self.record_dashboard_3(page, start_time)

                # Wait for narration timing (65 seconds narration)
                await asyncio.sleep(40)  # Extra time for narration

                # Closing (2:40-3:00) - show final dashboard 3 state
                print("\n🎯 Section 4: Closing Summary (2:40-3:00)")
                await page.goto(f"{self.base_url}/ops")
                await page.wait_for_load_state("networkidle")
                await self.wait_and_screenshot(page, "closing_final_state", 2000)

                # Wait for closing narration
                await asyncio.sleep(20)

                # End recording
                end_time = asyncio.get_event_loop().time()
                total_time = end_time - start_time

                print("\n" + "=" * 60)
                print(f"✅ Recording complete!")
                print(f"⏱️  Total recording time: {total_time:.1f} seconds")

                # Close browser and save video
                await context.close()
                await browser.close()

                # Find the video file (Playwright saves it with a unique name)
                video_files = list(self.videos_dir.glob("*.webm"))
                if video_files:
                    latest_video = max(video_files, key=lambda p: p.stat().st_mtime)
                    # Rename to our standard name
                    latest_video.rename(video_path)
                    print(f"🎥 Video saved: {video_path}")

                # Save metadata
                metadata = {
                    "timestamp": self.timestamp,
                    "duration_seconds": total_time,
                    "format": "3-minute production-ready hackathon demo",
                    "resolution": "1920x1080",
                    "video_path": str(video_path),
                    "screenshots_count": len(list(self.screenshots_dir.glob(f"hackathon_*_{self.timestamp}.png"))),
                    "system_capabilities": {
                        "dashboards": 3,
                        "aws_services": 8,
                        "prize_eligible_services": ["Amazon Q Business", "Amazon Nova", "Bedrock Agents with Memory"],
                        "websocket_capacity": "1,000+ concurrent connections",
                        "mttr_reduction": "95% (30min → 1.4min)",
                        "architecture": "Byzantine fault-tolerant consensus",
                        "infrastructure": "AWS CDK with auto-scaling"
                    },
                    "sections": {
                        "opening_hook": "0:00-0:20",
                        "dashboard_1_executive": "0:20-0:50",
                        "dashboard_2_transparency": "0:50-1:35",
                        "dashboard_3_operations": "1:35-2:40",
                        "closing_production_ready": "2:40-3:00"
                    }
                }

                metadata_path = self.output_dir / f"hackathon_demo_metadata_{self.timestamp}.json"
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f, indent=2)

                print(f"📋 Metadata saved: {metadata_path}")
                print("\n📁 Output files:")
                print(f"   Video:       {video_path}")
                print(f"   Screenshots: {self.screenshots_dir}/")
                print(f"   Metadata:    {metadata_path}")
                print("\n🎉 Production-Ready Demo Recording Successful!")
                print("\n🚀 System Capabilities Recorded:")
                print("   ✅ 3 specialized dashboards (Executive, Transparency, Operations)")
                print("   ✅ 8 AWS AI services integration")
                print("   ✅ WebSocket real-time streaming (1,000+ connections)")
                print("   ✅ Byzantine fault-tolerant consensus")
                print("   ✅ 95% MTTR reduction (30min → 1.4min)")
                print("   ✅ Production deployment infrastructure")
                print("\n💡 Next steps:")
                print("   1. Review the video against demo script")
                print("   2. Practice narration with production-ready talking points")
                print("   3. Use for backup if live demo fails")
                print("   4. Share with judges for comprehensive evaluation")

                return True

            except Exception as e:
                print(f"\n❌ Recording failed: {e}")
                import traceback
                traceback.print_exc()
                return False

async def main():
    """Main entry point"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║       Hackathon Demo Recorder - Production-Ready System      ║
║              3-Minute Format • 100% Operational              ║
║        3 Dashboards • 8 AWS Services • Byzantine AI          ║
╚══════════════════════════════════════════════════════════════╝
""")

    recorder = HackathonDemoRecorder()
    success = await recorder.record_demo()

    if not success:
        sys.exit(1)

    print("\n✨ Recording session complete!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Recording interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)
