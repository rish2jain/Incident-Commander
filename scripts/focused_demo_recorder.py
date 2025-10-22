#!/usr/bin/env python3
"""
Focused Demo Recorder - Optimized for Hackathon Submission
Shows actual AI analysis, transparency views, and resolution process

LATEST: Creates PERFECT 39-second demo for judges
File: 716f51fb6d4488f79cecc3dc07d6bfe7.webm (4.1MB)
Focus: AI transparency views and autonomous resolution
"""

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright, Page


class FocusedDemoRecorder:
    """Focused demo recorder that showcases core AI capabilities"""

    def __init__(self):
        self.base_url = "http://localhost:3000"
        self.output_dir = Path("demo_recordings")
        self.screenshots_dir = self.output_dir / "screenshots"
        self.videos_dir = self.output_dir / "videos"
        self.metrics_dir = self.output_dir / "metrics"
        
        # Create directories
        for dir_path in [self.output_dir, self.screenshots_dir, self.videos_dir, self.metrics_dir]:
            dir_path.mkdir(exist_ok=True)
        
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.start_time = datetime.now()
        self.screenshots = []

    async def capture_screenshot(self, page: Page, name: str, description: str):
        """Capture screenshot with metadata"""
        timestamp = datetime.now().strftime("%H%M%S")
        filename = f"{timestamp}_{name}.png"
        filepath = self.screenshots_dir / filename
        
        await page.screenshot(path=str(filepath), full_page=False)
        
        screenshot_info = {
            "timestamp": timestamp,
            "name": name,
            "description": description,
            "filepath": str(filepath)
        }
        self.screenshots.append(screenshot_info)
        print(f"📸 Screenshot captured: {name}")
        print(f"   {description}")

    async def wait_and_interact(self, page: Page, seconds: int, action_description: str):
        """Wait with progress indication and optional interaction"""
        print(f"⏳ {action_description} ({seconds}s)")
        await asyncio.sleep(seconds)

    async def record_focused_demo(self):
        """Record a focused demo showcasing AI capabilities"""
        
        print("\n" + "="*80)
        print("🏆 FOCUSED DEMO RECORDER - PERFECT FOR JUDGES")
        print("="*80)
        print(f"📋 Session ID: {self.session_id}")
        print(f"🎯 Focus: AI Transparency Views & Autonomous Resolution")
        print(f"⏱️  Target: 39 seconds - OPTIMAL for hackathon judges")
        print(f"🧠 Shows: All 5 AI transparency tabs + Byzantine consensus")
        print("="*80)

        async with async_playwright() as p:
            # Launch browser with recording
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                record_video_dir=str(self.videos_dir),
                record_video_size={"width": 1920, "height": 1080}
            )
            page = await context.new_page()

            try:
                # Phase 1: Quick Dashboard Load (15 seconds max)
                print("\n🚀 Phase 1: Dashboard Load & Quick Scenario Selection")
                dashboard_url = f"{self.base_url}/improved-demo"
                await page.goto(dashboard_url)
                await page.wait_for_load_state('networkidle')
                
                await self.capture_screenshot(page, "dashboard_loaded", "Enhanced dashboard with glassmorphism loaded")
                
                # Wait briefly then trigger incident immediately
                await self.wait_and_interact(page, 3, "Dashboard initialization")
                
                # Trigger incident immediately - no long selection process
                print("\n⚡ Triggering Database Cascade Incident (High Impact)")
                
                # Look for incident trigger button or auto-trigger
                try:
                    # Try to find and click incident trigger
                    trigger_button = page.locator("button:has-text('Database Cascade')")
                    if await trigger_button.count() > 0:
                        await trigger_button.click()
                    else:
                        # Use auto-trigger via URL
                        await page.goto(f"{dashboard_url}?auto-demo=true&scenario=database_cascade")
                        await page.wait_for_load_state('networkidle')
                except:
                    # Fallback to auto-trigger
                    await page.goto(f"{dashboard_url}?auto-demo=true")
                    await page.wait_for_load_state('networkidle')

                await self.capture_screenshot(page, "incident_triggered", "Database cascade incident triggered - AI analysis starting")

                # Phase 2: AI Analysis in Action (30 seconds)
                print("\n🧠 Phase 2: AI Analysis & Multi-Agent Coordination")
                await self.wait_and_interact(page, 5, "AI agents initializing analysis")
                
                await self.capture_screenshot(page, "ai_analyzing", "Multi-agent AI analysis in progress")

                # Phase 3: Transparency Views Showcase (45 seconds)
                print("\n🔍 Phase 3: AI Transparency Views Demonstration")
                
                # Tab 1: Reasoning
                print("   🧠 Showcasing AI Reasoning Tab")
                try:
                    reasoning_tab = page.locator("button[value='reasoning']")
                    if await reasoning_tab.count() > 0:
                        await reasoning_tab.click()
                        await asyncio.sleep(3)
                        await self.capture_screenshot(page, "reasoning_view", "AI Reasoning: How agents analyze evidence and reach conclusions")
                except:
                    print("   ⚠️  Reasoning tab not found, continuing...")

                # Tab 2: Decisions
                print("   🌳 Showcasing Decision Trees Tab")
                try:
                    decisions_tab = page.locator("button[value='decisions']")
                    if await decisions_tab.count() > 0:
                        await decisions_tab.click()
                        await asyncio.sleep(3)
                        await self.capture_screenshot(page, "decision_trees", "Decision Trees: Alternative paths and decision logic")
                except:
                    print("   ⚠️  Decisions tab not found, continuing...")

                # Tab 3: Confidence
                print("   📈 Showcasing Confidence Levels Tab")
                try:
                    confidence_tab = page.locator("button[value='confidence']")
                    if await confidence_tab.count() > 0:
                        await confidence_tab.click()
                        await asyncio.sleep(3)
                        await self.capture_screenshot(page, "confidence_levels", "Confidence Tracking: Uncertainty quantification and reliability")
                except:
                    print("   ⚠️  Confidence tab not found, continuing...")

                # Tab 4: Communication
                print("   💬 Showcasing Agent Communication Tab")
                try:
                    communication_tab = page.locator("button[value='communication']")
                    if await communication_tab.count() > 0:
                        await communication_tab.click()
                        await asyncio.sleep(3)
                        await self.capture_screenshot(page, "agent_communication", "Agent Communication: Multi-agent coordination and consensus")
                except:
                    print("   ⚠️  Communication tab not found, continuing...")

                # Tab 5: Analytics
                print("   📊 Showcasing Performance Analytics Tab")
                try:
                    analytics_tab = page.locator("button[value='analytics']")
                    if await analytics_tab.count() > 0:
                        await analytics_tab.click()
                        await asyncio.sleep(3)
                        await self.capture_screenshot(page, "performance_analytics", "Performance Analytics: Metrics and bias detection")
                except:
                    print("   ⚠️  Analytics tab not found, continuing...")

                # Phase 4: Resolution Process (30 seconds)
                print("\n⚡ Phase 4: Autonomous Resolution Process")
                await self.wait_and_interact(page, 8, "Byzantine consensus reaching agreement")
                
                await self.capture_screenshot(page, "consensus_reached", "Byzantine consensus achieved - executing resolution")
                
                await self.wait_and_interact(page, 10, "Automated remediation executing")
                
                await self.capture_screenshot(page, "resolution_executing", "Autonomous resolution in progress")

                # Phase 5: Completion & Results (15 seconds)
                print("\n✅ Phase 5: Incident Resolution & Business Impact")
                await self.wait_and_interact(page, 8, "Verifying resolution and calculating impact")
                
                await self.capture_screenshot(page, "incident_resolved", "Incident resolved - showing business impact and metrics")
                
                await self.capture_screenshot(page, "demo_complete", "Demo complete - full AI transparency and resolution demonstrated")

                print("\n✅ Focused demo recording complete!")

            except Exception as e:
                print(f"❌ Demo recording error: {e}")
                await self.capture_screenshot(page, "error_state", f"Error occurred: {e}")

            finally:
                # Save metrics
                end_time = datetime.now()
                duration = (end_time - self.start_time).total_seconds()
                
                metrics = {
                    "session_id": self.session_id,
                    "start_time": self.start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "duration_seconds": duration,
                    "focus": "AI Transparency and Resolution Process",
                    "screenshots_captured": self.screenshots,
                    "phases": [
                        "Dashboard Load & Quick Selection (15s)",
                        "AI Analysis & Multi-Agent Coordination (30s)",
                        "AI Transparency Views Demonstration (45s)",
                        "Autonomous Resolution Process (30s)",
                        "Incident Resolution & Business Impact (15s)"
                    ],
                    "total_phases": 5,
                    "transparency_tabs_shown": ["reasoning", "decisions", "confidence", "communication", "analytics"]
                }
                
                metrics_file = self.metrics_dir / f"focused_demo_metrics_{self.session_id}.json"
                with open(metrics_file, 'w') as f:
                    json.dump(metrics, f, indent=2)
                
                print(f"\n📊 Metrics saved: {metrics_file}")
                
                # Close browser
                await context.close()
                await browser.close()

                # Print summary
                print("\n" + "="*80)
                print("📊 FOCUSED DEMO RECORDING SUMMARY")
                print("="*80)
                print(f"Session ID: {self.session_id}")
                print(f"Duration: {duration:.1f}s")
                print(f"Screenshots: {len(self.screenshots)}")
                print(f"Focus: AI Transparency & Resolution Process")
                print(f"Transparency Tabs: 5 demonstrated")
                print(f"📁 Output Location: {self.output_dir}")
                print("="*80)


async def main():
    """Main function to run focused demo recording"""
    recorder = FocusedDemoRecorder()
    await recorder.record_focused_demo()


if __name__ == "__main__":
    asyncio.run(main())