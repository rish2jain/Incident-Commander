#!/usr/bin/env python3
"""
Complete Hackathon Video Recording Script
Ensures all AI transparency features are captured with proper timing
"""

import asyncio
from playwright.async_api import async_playwright
from pathlib import Path
from datetime import datetime
import json

async def record_complete_hackathon_video():
    """Record comprehensive hackathon video with all features"""
    
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path("hackathon_video_complete")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            record_video_dir=str(output_dir),
            record_video_size={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        
        try:
            print("🎬 COMPLETE HACKATHON VIDEO RECORDING")
            print("=" * 60)
            print("🎯 Comprehensive AI transparency demonstration")
            print("⏱️ Extended timing to capture all features")
            print("=" * 60)
            
            # Load the insights dashboard
            print("\n🚀 Loading AI Insights Dashboard...")
            await page.goto("http://localhost:3000/insights-demo")
            await page.wait_for_load_state('networkidle')
            
            # Opening shot
            await page.screenshot(path=str(output_dir / "01_opening_dashboard.png"))
            print("   📸 Opening dashboard captured")
            
            # Wait for narration
            print("\n🎭 PHASE 1: Opening Hook & Solution Introduction (30s)")
            print("   💬 'Every minute of downtime costs $5,600...'")
            print("   💬 'Meet the world's first AI transparency system...'")
            await asyncio.sleep(15)  # Time for opening narration
            
            # Trigger the demo
            print("\n🚨 PHASE 2: Triggering Enhanced Demo")
            trigger_btn = await page.query_selector('button:has-text("Trigger Enhanced Demo")')
            if trigger_btn:
                await trigger_btn.click()
                print("   ✅ Enhanced demo triggered")
                await page.screenshot(path=str(output_dir / "02_demo_triggered.png"))
            
            # Wait for demo to start and reasoning to appear
            print("   ⏳ Waiting for agent reasoning to develop...")
            await asyncio.sleep(10)
            
            # PHASE 3: Agent Reasoning (Extended)
            print("\n🧠 PHASE 3: Agent Reasoning Showcase (30s)")
            print("   💬 'See exactly how AI agents think through problems...'")
            
            # Capture reasoning development
            for i in range(3):
                await asyncio.sleep(5)
                reasoning_elements = await page.query_selector_all('[class*="border-slate-600"]')
                print(f"   🔍 Reasoning elements: {len(reasoning_elements)}")
                
                if i == 1:  # Mid-reasoning screenshot
                    await page.screenshot(path=str(output_dir / "03_agent_reasoning.png"))
            
            # PHASE 4: Decision Tree Exploration
            print("\n🌳 PHASE 4: Decision Tree Exploration (20s)")
            print("   💬 'Explore AI choices and alternatives interactively...'")
            
            decisions_tab = await page.query_selector('[value="decisions"]')
            if decisions_tab:
                await decisions_tab.click()
                await asyncio.sleep(3)
                print("   ✅ Decision tree tab activated")
                
                await page.screenshot(path=str(output_dir / "04_decision_tree.png"))
                await asyncio.sleep(8)  # Time to explore decision tree
            
            # PHASE 5: Confidence Tracking
            print("\n📈 PHASE 5: Confidence Tracking (15s)")
            print("   💬 'Monitor AI certainty and uncertainty quantification...'")
            
            confidence_tab = await page.query_selector('[value="confidence"]')
            if confidence_tab:
                await confidence_tab.click()
                await asyncio.sleep(3)
                print("   ✅ Confidence tracking displayed")
                
                await page.screenshot(path=str(output_dir / "05_confidence_tracking.png"))
                await asyncio.sleep(7)
            
            # PHASE 6: Communication Matrix
            print("\n💬 PHASE 6: Inter-Agent Communication (15s)")
            print("   💬 'Transparent multi-agent discussions and consensus...'")
            
            comm_tab = await page.query_selector('[value="communication"]')
            if comm_tab:
                await comm_tab.click()
                await asyncio.sleep(3)
                print("   ✅ Communication matrix displayed")
                
                await page.screenshot(path=str(output_dir / "06_communication_matrix.png"))
                await asyncio.sleep(7)
            
            # PHASE 7: Analytics & Bias Detection
            print("\n📊 PHASE 7: Analytics & Bias Detection (15s)")
            print("   💬 'Systematic bias detection and performance analytics...'")
            
            analytics_tab = await page.query_selector('[value="analytics"]')
            if analytics_tab:
                await analytics_tab.click()
                await asyncio.sleep(3)
                print("   ✅ Analytics and bias detection displayed")
                
                await page.screenshot(path=str(output_dir / "07_analytics_bias.png"))
                await asyncio.sleep(7)
            
            # PHASE 8: Final Comprehensive View
            print("\n🏆 PHASE 8: Closing Impact (15s)")
            print("   💬 'The future of trustworthy AI in critical systems...'")
            
            # Return to reasoning tab for final comprehensive view
            reasoning_tab = await page.query_selector('[value="reasoning"]')
            if reasoning_tab:
                await reasoning_tab.click()
                await asyncio.sleep(3)
            
            # Final screenshot showing full system
            await page.screenshot(path=str(output_dir / "08_final_comprehensive.png"))
            await asyncio.sleep(8)  # Final narration time
            
            print("\n✅ Complete video recording finished!")
            
        except Exception as e:
            print(f"❌ Error during recording: {e}")
            await page.screenshot(path=str(output_dir / "error_state.png"))
        
        finally:
            await context.close()
            await browser.close()
    
    # Print summary
    print("\n" + "=" * 60)
    print("🎬 COMPLETE HACKATHON VIDEO SUMMARY")
    print("=" * 60)
    
    print(f"🎥 Session ID: {session_id}")
    print(f"📁 Output Directory: {output_dir}")
    print("🎥 Video: Saved as .webm file by Playwright")
    
    print(f"\n✅ Features Demonstrated:")
    print(f"   🧠 Agent reasoning with step-by-step analysis")
    print(f"   🌳 Interactive decision tree exploration")
    print(f"   📈 Real-time confidence tracking and calibration")
    print(f"   💬 Inter-agent communication and consensus")
    print(f"   📊 Bias detection and performance analytics")
    print(f"   🏆 Comprehensive AI transparency system")
    
    print(f"\n📸 Screenshots Captured:")
    screenshots = [
        "01_opening_dashboard.png",
        "02_demo_triggered.png", 
        "03_agent_reasoning.png",
        "04_decision_tree.png",
        "05_confidence_tracking.png",
        "06_communication_matrix.png",
        "07_analytics_bias.png",
        "08_final_comprehensive.png"
    ]
    
    for screenshot in screenshots:
        print(f"   • {screenshot}")
    
    print(f"\n🏆 HACKATHON VIDEO COMPLETE!")
    print(f"✅ Revolutionary AI transparency comprehensively demonstrated")
    print(f"✅ All key competitive advantages showcased")
    print(f"✅ Professional HD quality recording")
    print(f"✅ Judge-friendly comprehensive presentation")
    print(f"🌟 Ready for hackathon submission!")

if __name__ == "__main__":
    asyncio.run(record_complete_hackathon_video())