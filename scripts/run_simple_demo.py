#!/usr/bin/env python3
"""
Simple demo runner for the comprehensive demo dashboard
Works with the standalone HTML file served via HTTP server
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the scripts directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from automated_demo_recorder import DemoRecorder


async def run_simple_demo():
    """Run demo with the comprehensive dashboard"""
    
    print("\n" + "="*80)
    print("🎬 INCIDENT COMMANDER - SIMPLE DEMO RECORDER")
    print("="*80)
    
    # Configuration for agent actions dashboard
    config = {
        "base_url": "http://localhost:3000/agent_actions_dashboard.html",
        "output_dir": "demo_recordings",
        "video_width": 1920,
        "video_height": 1080,
    }
    
    print(f"\n📋 Configuration:")
    print(f"   Dashboard URL: {config['base_url']}")
    print(f"   Output Directory: {config['output_dir']}")
    print(f"   Video Resolution: {config['video_width']}x{config['video_height']}")
    print("\n" + "="*80)

    # Create recorder
    recorder = DemoRecorder(**config)
    
    # Override the run_3min_demo method to work with our HTML file
    async def simple_demo_execution():
        """Simplified demo execution for standalone HTML"""
        browser, context, page = await recorder.setup_browser()
        
        try:
            recorder.metrics["start_time"] = recorder.session_id
            
            print("\n🌐 Loading comprehensive demo dashboard...")
            await page.goto(config["base_url"])
            await page.wait_for_load_state('networkidle')
            
            # Initial screenshot
            await recorder.capture_screenshot(
                page,
                "dashboard_initial",
                "Comprehensive demo dashboard loaded"
            )
            
            print("\n🎬 Starting demo sequence...")
            
            # Look for demo trigger buttons and click them
            try:
                # Try to find and click incident trigger buttons
                buttons = await page.query_selector_all('button')
                print(f"Found {len(buttons)} buttons on the page")
                
                for i, button in enumerate(buttons[:5]):  # Check first 5 buttons
                    try:
                        text = await button.inner_text()
                        if any(keyword in text.lower() for keyword in ['trigger', 'start', 'demo', 'incident']):
                            print(f"Clicking button: {text}")
                            await button.click()
                            await recorder.capture_screenshot(
                                page,
                                f"button_clicked_{i}",
                                f"Clicked button: {text}"
                            )
                            await asyncio.sleep(2)
                    except Exception as e:
                        print(f"Error with button {i}: {e}")
                        
            except Exception as e:
                print(f"Error finding buttons: {e}")
            
            # Capture screenshots at intervals
            for i in range(6):  # 6 screenshots over 30 seconds
                await asyncio.sleep(5)
                await recorder.capture_screenshot(
                    page,
                    f"demo_progress_{i*5}s",
                    f"Demo progress at {i*5} seconds"
                )
            
            # Final screenshot
            await recorder.capture_screenshot(
                page,
                "demo_complete",
                "Demo sequence complete"
            )
            
            print("\n✅ Demo execution complete!")
            
        except Exception as e:
            print(f"\n❌ Demo execution error: {e}")
            await recorder.capture_screenshot(
                page,
                "error_state",
                f"Error occurred: {str(e)}"
            )
        
        finally:
            # Close browser (saves video)
            await context.close()
            await browser.close()
            
        return recorder.metrics

    # Run the simplified demo
    metrics = await simple_demo_execution()
    
    # Print summary
    print("\n" + "="*80)
    print("📊 DEMO RECORDING SUMMARY")
    print("="*80)
    print(f"Session ID: {metrics['session_id']}")
    print(f"Screenshots: {len(metrics['screenshots_captured'])}")
    print(f"\n📁 Output Location: {recorder.output_dir}")
    print("="*80)
    
    return metrics


if __name__ == "__main__":
    asyncio.run(run_simple_demo())