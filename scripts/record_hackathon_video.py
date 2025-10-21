#!/usr/bin/env python3
"""
Hackathon Video Recording Script
Creates a professional 3-minute demo video showcasing AI transparency features

Features:
- HD video recording (1920x1080)
- Professional narration timing
- Key feature highlights
- Judge-friendly presentation
- Competitive differentiation focus
"""

import asyncio
from playwright.async_api import async_playwright
from pathlib import Path
from datetime import datetime
import json

async def record_hackathon_video():
    """Record comprehensive hackathon submission video"""
    
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path("hackathon_video")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    video_metrics = {
        "session_id": session_id,
        "start_time": datetime.now().isoformat(),
        "video_type": "Hackathon Submission",
        "target_duration": "3 minutes",
        "key_messages": [],
        "features_demonstrated": [],
        "competitive_advantages": [],
        "screenshots": []
    }
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            record_video_dir=str(output_dir),
            record_video_size={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        
        try:
            print("🎬 HACKATHON VIDEO RECORDING - AI TRANSPARENCY DEMO")
            print("=" * 70)
            print("🎯 Target: 3-minute professional demo for judges")
            print("🏆 Focus: Revolutionary AI transparency and explainability")
            print("=" * 70)
            
            # PHASE 1: Opening Hook (0:00-0:20)
            print("\n🎭 PHASE 1: Opening Hook (0:00-0:20)")
            print("💬 Narration: 'Every minute of downtime costs enterprises $5,600...'")
            
            await page.goto("http://localhost:3000/insights-demo")
            await page.wait_for_load_state('networkidle')
            
            # Capture opening shot
            await page.screenshot(path=str(output_dir / "01_opening_hook.png"))
            video_metrics["screenshots"].append("01_opening_hook.png")
            video_metrics["key_messages"].append("Problem statement: High cost of downtime")
            
            await asyncio.sleep(5)  # Pause for narration
            
            # PHASE 2: Solution Introduction (0:20-0:50)
            print("\n🧠 PHASE 2: Solution Introduction (0:20-0:50)")
            print("💬 Narration: 'Meet the world's first AI transparency system...'")
            
            # Highlight the revolutionary dashboard
            await page.screenshot(path=str(output_dir / "02_solution_intro.png"))
            video_metrics["screenshots"].append("02_solution_intro.png")
            video_metrics["key_messages"].append("Revolutionary AI transparency system")
            video_metrics["competitive_advantages"].append("Industry-first comprehensive AI explainability")
            
            # Show the tabbed interface
            tabs = await page.query_selector_all('[role="tab"]')
            print(f"   📊 Showcasing {len(tabs)} transparency categories")
            video_metrics["features_demonstrated"].append(f"Tabbed interface with {len(tabs)} insight categories")
            
            await asyncio.sleep(8)  # Pause for solution explanation
            
            # PHASE 3: Live Demo Trigger (0:50-1:10)
            print("\n🚨 PHASE 3: Live Demo Trigger (0:50-1:10)")
            print("💬 Narration: 'Watch AI transparency in action...'")
            
            # Trigger the enhanced demo
            trigger_btn = await page.query_selector('button:has-text("Trigger Enhanced Demo")')
            if trigger_btn:
                await trigger_btn.click()
                print("   ✅ Enhanced AI transparency demo triggered")
                video_metrics["features_demonstrated"].append("Interactive demo triggering")
                
                await page.screenshot(path=str(output_dir / "03_demo_triggered.png"))
                video_metrics["screenshots"].append("03_demo_triggered.png")
                video_metrics["key_messages"].append("Live AI transparency demonstration")
            
            await asyncio.sleep(5)  # Wait for demo to start
            
            # PHASE 4: Agent Reasoning Showcase (1:10-1:40)
            print("\n🧠 PHASE 4: Agent Reasoning Showcase (1:10-1:40)")
            print("💬 Narration: 'See exactly how AI agents think through problems...'")
            
            # Wait for reasoning to appear
            await asyncio.sleep(8)
            
            # Capture agent reasoning
            reasoning_elements = await page.query_selector_all('[class*="border-slate-600"]')
            if len(reasoning_elements) > 0:
                print(f"   🔍 Captured {len(reasoning_elements)} agent reasoning steps")
                video_metrics["features_demonstrated"].append("Step-by-step agent reasoning visualization")
                video_metrics["competitive_advantages"].append("Transparent AI decision-making process")
            
            await page.screenshot(path=str(output_dir / "04_agent_reasoning.png"))
            video_metrics["screenshots"].append("04_agent_reasoning.png")
            video_metrics["key_messages"].append("Transparent agent reasoning process")
            
            await asyncio.sleep(10)  # Show reasoning development
            
            # PHASE 5: Decision Tree Exploration (1:40-2:00)
            print("\n🌳 PHASE 5: Decision Tree Exploration (1:40-2:00)")
            print("💬 Narration: 'Explore AI choices and alternatives interactively...'")
            
            # Switch to decision tree tab
            decisions_tab = await page.query_selector('[value="decisions"]')
            if decisions_tab:
                await decisions_tab.click()
                await asyncio.sleep(3)
                
                print("   🌳 Interactive decision tree displayed")
                video_metrics["features_demonstrated"].append("Interactive decision tree visualization")
                video_metrics["competitive_advantages"].append("Counterfactual analysis and alternative exploration")
                
                await page.screenshot(path=str(output_dir / "05_decision_tree.png"))
                video_metrics["screenshots"].append("05_decision_tree.png")
                video_metrics["key_messages"].append("Interactive decision tree exploration")
            
            await asyncio.sleep(8)  # Explore decision tree
            
            # PHASE 6: Confidence & Communication (2:00-2:30)
            print("\n📈 PHASE 6: Confidence & Communication (2:00-2:30)")
            print("💬 Narration: 'Monitor AI certainty and inter-agent discussions...'")
            
            # Switch to confidence tab
            confidence_tab = await page.query_selector('[value="confidence"]')
            if confidence_tab:
                await confidence_tab.click()
                await asyncio.sleep(3)
                
                print("   📊 Real-time confidence tracking displayed")
                video_metrics["features_demonstrated"].append("Real-time confidence calibration")
                
                await page.screenshot(path=str(output_dir / "06_confidence_tracking.png"))
                video_metrics["screenshots"].append("06_confidence_tracking.png")
            
            await asyncio.sleep(5)
            
            # Switch to communication tab
            comm_tab = await page.query_selector('[value="communication"]')
            if comm_tab:
                await comm_tab.click()
                await asyncio.sleep(3)
                
                print("   💬 Inter-agent communication matrix shown")
                video_metrics["features_demonstrated"].append("Inter-agent communication transparency")
                video_metrics["competitive_advantages"].append("Byzantine consensus visualization")
                
                await page.screenshot(path=str(output_dir / "07_communication_matrix.png"))
                video_metrics["screenshots"].append("07_communication_matrix.png")
            
            await asyncio.sleep(7)
            
            # PHASE 7: Analytics & Bias Detection (2:30-2:50)
            print("\n📊 PHASE 7: Analytics & Bias Detection (2:30-2:50)")
            print("💬 Narration: 'Systematic bias detection and performance analytics...'")
            
            # Switch to analytics tab
            analytics_tab = await page.query_selector('[value="analytics"]')
            if analytics_tab:
                await analytics_tab.click()
                await asyncio.sleep(3)
                
                print("   🎯 Bias detection and analytics displayed")
                video_metrics["features_demonstrated"].append("AI bias detection and monitoring")
                video_metrics["competitive_advantages"].append("Regulatory compliance and fairness metrics")
                
                await page.screenshot(path=str(output_dir / "08_analytics_bias.png"))
                video_metrics["screenshots"].append("08_analytics_bias.png")
                video_metrics["key_messages"].append("Systematic bias detection and compliance")
            
            await asyncio.sleep(8)
            
            # PHASE 8: Closing Impact (2:50-3:00)
            print("\n🏆 PHASE 8: Closing Impact (2:50-3:00)")
            print("💬 Narration: 'The future of trustworthy AI in critical systems...'")
            
            # Return to reasoning tab for final shot
            reasoning_tab = await page.query_selector('[value="reasoning"]')
            if reasoning_tab:
                await reasoning_tab.click()
                await asyncio.sleep(2)
            
            # Final comprehensive screenshot
            await page.screenshot(path=str(output_dir / "09_closing_impact.png"))
            video_metrics["screenshots"].append("09_closing_impact.png")
            video_metrics["key_messages"].append("Future of trustworthy AI")
            video_metrics["competitive_advantages"].append("Sets global standard for responsible AI")
            
            await asyncio.sleep(5)  # Final pause
            
            print("\n✅ Video recording phases completed!")
            
        except Exception as e:
            print(f"❌ Error during video recording: {e}")
            video_metrics["error"] = str(e)
            await page.screenshot(path=str(output_dir / "error_state.png"))
        
        finally:
            video_metrics["end_time"] = datetime.now().isoformat()
            duration = (datetime.fromisoformat(video_metrics["end_time"]) - 
                       datetime.fromisoformat(video_metrics["start_time"])).total_seconds()
            video_metrics["actual_duration"] = duration
            
            await context.close()
            await browser.close()
    
    # Save video metrics
    with open(output_dir / "video_metrics.json", "w") as f:
        json.dump(video_metrics, f, indent=2)
    
    # Print comprehensive summary
    print("\n" + "=" * 70)
    print("🎬 HACKATHON VIDEO RECORDING COMPLETE")
    print("=" * 70)
    
    print(f"🎥 Session ID: {video_metrics['session_id']}")
    print(f"⏱️ Actual Duration: {video_metrics['actual_duration']:.1f} seconds")
    print(f"🎯 Target Duration: {video_metrics['target_duration']}")
    
    print(f"\n🎭 Key Messages Delivered ({len(video_metrics['key_messages'])}):")
    for i, message in enumerate(video_metrics['key_messages'], 1):
        print(f"   {i:2d}. {message}")
    
    print(f"\n✨ Features Demonstrated ({len(video_metrics['features_demonstrated'])}):")
    for i, feature in enumerate(video_metrics['features_demonstrated'], 1):
        print(f"   {i:2d}. {feature}")
    
    print(f"\n🏆 Competitive Advantages ({len(video_metrics['competitive_advantages'])}):")
    for i, advantage in enumerate(video_metrics['competitive_advantages'], 1):
        print(f"   {i:2d}. {advantage}")
    
    print(f"\n📸 Screenshots Captured ({len(video_metrics['screenshots'])}):")
    for screenshot in video_metrics['screenshots']:
        print(f"   • {screenshot}")
    
    print(f"\n📁 Output Directory: {output_dir}")
    print("🎥 Video: Automatically saved by Playwright")
    
    # Evaluate video quality
    required_elements = [
        "agent reasoning", "decision tree", "confidence", "communication", "bias detection"
    ]
    
    demonstrated_features_lower = [f.lower() for f in video_metrics['features_demonstrated']]
    elements_found = sum(1 for req in required_elements 
                        if any(req in demo for demo in demonstrated_features_lower))
    
    if elements_found >= 4:
        print("\n🏆 EXCELLENT HACKATHON VIDEO RECORDED!")
        print("✅ Revolutionary AI transparency comprehensively demonstrated")
        print("✅ All key competitive advantages showcased")
        print("✅ Professional quality with HD recording")
        print("✅ Judge-friendly presentation and timing")
        print("✅ World-class AI interpretability highlighted")
        print("✅ Ready for hackathon submission!")
    else:
        print(f"\n⚠️ Some key elements may need attention ({elements_found}/5)")
    
    print(f"\n🎉 Hackathon video recording complete!")
    print(f"🌟 Your revolutionary AI transparency system is ready to impress judges!")
    
    return elements_found >= 4

if __name__ == "__main__":
    success = asyncio.run(record_hackathon_video())
    exit(0 if success else 1)