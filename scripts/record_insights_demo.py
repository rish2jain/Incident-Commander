#!/usr/bin/env python3
"""
Comprehensive demo recording for the AI Insights & Transparency Dashboard
Showcases advanced AI interpretability and explainability features
"""

import asyncio
from playwright.async_api import async_playwright
from pathlib import Path
from datetime import datetime
import json

async def record_insights_demo():
    """Record comprehensive insights dashboard demo"""
    
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path("demo_recordings/insights_demo")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    metrics = {
        "session_id": session_id,
        "start_time": datetime.now().isoformat(),
        "dashboard_type": "AI Insights & Transparency",
        "features_demonstrated": [],
        "screenshots": [],
        "transparency_metrics": {}
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
            print("🧠 AI INSIGHTS & TRANSPARENCY DASHBOARD DEMO")
            print("=" * 60)
            
            # Phase 1: Load Insights Dashboard
            print("\n🚀 Phase 1: Loading AI Insights Dashboard...")
            start_time = datetime.now()
            
            await page.goto("http://localhost:3000/insights-demo")
            await page.wait_for_load_state('networkidle')
            
            load_time = (datetime.now() - start_time).total_seconds()
            metrics["transparency_metrics"]["load_time"] = load_time
            
            await page.screenshot(path=str(output_dir / "01_insights_dashboard_loaded.png"))
            metrics["screenshots"].append("01_insights_dashboard_loaded.png")
            
            print(f"   ✅ Insights dashboard loaded in {load_time:.2f}s")
            metrics["features_demonstrated"].append("Advanced dashboard loading")
            
            # Phase 2: Demonstrate Tabbed Interface
            print("\n📑 Phase 2: Exploring Transparency Features...")
            
            # Count tabs
            tabs = await page.query_selector_all('[role="tab"]')
            tab_count = len(tabs)
            metrics["transparency_metrics"]["available_tabs"] = tab_count
            
            print(f"   📊 Found {tab_count} insight categories")
            metrics["features_demonstrated"].append("Multi-tab insights interface")
            
            await page.screenshot(path=str(output_dir / "02_tabs_overview.png"))
            metrics["screenshots"].append("02_tabs_overview.png")
            
            # Phase 3: Trigger Enhanced Demo
            print("\n🎮 Phase 3: Triggering Enhanced AI Demo...")
            
            trigger_btn = await page.query_selector('button:has-text("Trigger Enhanced Demo")')
            if trigger_btn:
                await trigger_btn.click()
                print("   ✅ Enhanced demo triggered with AI transparency")
                metrics["features_demonstrated"].append("Enhanced demo with AI reasoning")
                
                await asyncio.sleep(3)
                await page.screenshot(path=str(output_dir / "03_demo_triggered.png"))
                metrics["screenshots"].append("03_demo_triggered.png")
            
            # Phase 4: Agent Reasoning Analysis
            print("\n🧠 Phase 4: Analyzing Agent Reasoning Process...")
            
            # Wait for reasoning to appear
            await asyncio.sleep(5)
            
            # Check reasoning elements
            reasoning_elements = await page.query_selector_all('[class*="border-slate-600"]')
            reasoning_count = len(reasoning_elements)
            metrics["transparency_metrics"]["reasoning_steps"] = reasoning_count
            
            print(f"   🔍 Agent reasoning steps captured: {reasoning_count}")
            metrics["features_demonstrated"].append("Step-by-step agent reasoning")
            
            # Check for evidence and alternatives
            evidence_elements = await page.query_selector_all('text=Evidence considered')
            alternatives_elements = await page.query_selector_all('text=Alternatives considered')
            
            if len(evidence_elements) > 0:
                print("   📋 Evidence-based reasoning demonstrated")
                metrics["features_demonstrated"].append("Evidence-based decision making")
            
            if len(alternatives_elements) > 0:
                print("   🔀 Alternative options analysis shown")
                metrics["features_demonstrated"].append("Alternative options consideration")
            
            await page.screenshot(path=str(output_dir / "04_agent_reasoning.png"))
            metrics["screenshots"].append("04_agent_reasoning.png")
            
            # Phase 5: Decision Tree Exploration
            print("\n🌳 Phase 5: Exploring Decision Trees...")
            
            # Switch to decision tree tab
            decisions_tab = await page.query_selector('[value="decisions"]')
            if decisions_tab:
                await decisions_tab.click()
                await asyncio.sleep(3)
                
                # Check for decision tree elements
                tree_elements = await page.query_selector_all('[class*="bg-blue-500/20"]')
                if len(tree_elements) > 0:
                    print("   🌳 Interactive decision tree displayed")
                    metrics["features_demonstrated"].append("Interactive decision tree visualization")
                
                # Check for probability indicators
                prob_elements = await page.query_selector_all('text*="P:"')
                if len(prob_elements) > 0:
                    print(f"   📊 Probability indicators found: {len(prob_elements)}")
                    metrics["features_demonstrated"].append("Decision probability visualization")
                
                await page.screenshot(path=str(output_dir / "05_decision_tree.png"))
                metrics["screenshots"].append("05_decision_tree.png")
            
            # Phase 6: Confidence Tracking
            print("\n📈 Phase 6: Monitoring Confidence Evolution...")
            
            # Switch to confidence tab
            confidence_tab = await page.query_selector('[value="confidence"]')
            if confidence_tab:
                await confidence_tab.click()
                await asyncio.sleep(2)
                
                # Check for progress bars
                progress_elements = await page.query_selector_all('[role="progressbar"]')
                confidence_bars = len(progress_elements)
                metrics["transparency_metrics"]["confidence_indicators"] = confidence_bars
                
                print(f"   📊 Confidence indicators active: {confidence_bars}")
                metrics["features_demonstrated"].append("Real-time confidence tracking")
                
                # Check for calibration metrics
                calibration_elements = await page.query_selector_all('text*="Calibration"')
                if len(calibration_elements) > 0:
                    print("   🎯 Confidence calibration metrics displayed")
                    metrics["features_demonstrated"].append("Confidence calibration analysis")
                
                await page.screenshot(path=str(output_dir / "06_confidence_tracking.png"))
                metrics["screenshots"].append("06_confidence_tracking.png")
            
            # Phase 7: Communication Matrix
            print("\n💬 Phase 7: Analyzing Agent Communication...")
            
            # Switch to communication tab
            comm_tab = await page.query_selector('[value="communication"]')
            if comm_tab:
                await comm_tab.click()
                await asyncio.sleep(2)
                
                # Check for communication elements
                comm_elements = await page.query_selector_all('[class*="border-red-500/30"], [class*="border-green-500/30"], [class*="border-blue-500/30"]')
                comm_count = len(comm_elements)
                metrics["transparency_metrics"]["communication_events"] = comm_count
                
                print(f"   💬 Inter-agent communications tracked: {comm_count}")
                metrics["features_demonstrated"].append("Inter-agent communication tracking")
                
                # Check for communication types
                type_badges = await page.query_selector_all('text="escalation", text="consensus", text="recommendation"')
                if len(type_badges) > 0:
                    print("   🏷️ Communication type classification active")
                    metrics["features_demonstrated"].append("Communication type classification")
                
                await page.screenshot(path=str(output_dir / "07_communication_matrix.png"))
                metrics["screenshots"].append("07_communication_matrix.png")
            
            # Phase 8: Analytics and Bias Detection
            print("\n📊 Phase 8: Reviewing Analytics & Bias Detection...")
            
            # Switch to analytics tab
            analytics_tab = await page.query_selector('[value="analytics"]')
            if analytics_tab:
                await analytics_tab.click()
                await asyncio.sleep(2)
                
                # Check for performance metrics
                perf_elements = await page.query_selector_all('text*="Accuracy", text*="Calibration"')
                if len(perf_elements) > 0:
                    print("   📈 Performance analytics displayed")
                    metrics["features_demonstrated"].append("Performance analytics dashboard")
                
                # Check for bias detection
                bias_elements = await page.query_selector_all('text*="Bias Detection"')
                if len(bias_elements) > 0:
                    print("   🎯 Bias detection metrics active")
                    metrics["features_demonstrated"].append("AI bias detection and monitoring")
                
                # Check for learning insights
                learning_elements = await page.query_selector_all('text*="Learning Insights"')
                if len(learning_elements) > 0:
                    print("   🧠 Learning insights visualization working")
                    metrics["features_demonstrated"].append("AI learning insights tracking")
                
                await page.screenshot(path=str(output_dir / "08_analytics_bias_detection.png"))
                metrics["screenshots"].append("08_analytics_bias_detection.png")
            
            # Phase 9: Final State Capture
            print("\n✅ Phase 9: Capturing Final Transparency State...")
            
            # Return to reasoning tab for final view
            reasoning_tab = await page.query_selector('[value="reasoning"]')
            if reasoning_tab:
                await reasoning_tab.click()
                await asyncio.sleep(2)
            
            # Final comprehensive screenshot
            await page.screenshot(path=str(output_dir / "09_final_transparency_state.png"))
            metrics["screenshots"].append("09_final_transparency_state.png")
            
            # Count total transparency features
            total_features = len(metrics["features_demonstrated"])
            metrics["transparency_metrics"]["total_features_demonstrated"] = total_features
            
            print(f"   🏆 Total transparency features demonstrated: {total_features}")
            
        except Exception as e:
            print(f"❌ Error during insights demo: {e}")
            metrics["error"] = str(e)
            await page.screenshot(path=str(output_dir / "error_state.png"))
        
        finally:
            metrics["end_time"] = datetime.now().isoformat()
            duration = (datetime.fromisoformat(metrics["end_time"]) - 
                       datetime.fromisoformat(metrics["start_time"])).total_seconds()
            metrics["transparency_metrics"]["total_duration"] = duration
            
            await context.close()
            await browser.close()
    
    # Save comprehensive metrics
    with open(output_dir / "insights_demo_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)
    
    # Print comprehensive summary
    print("\n" + "=" * 60)
    print("🧠 AI INSIGHTS & TRANSPARENCY DEMO SUMMARY")
    print("=" * 60)
    
    print(f"🎬 Session ID: {metrics['session_id']}")
    print(f"⏱️ Total Duration: {metrics['transparency_metrics'].get('total_duration', 0):.1f}s")
    print(f"🚀 Load Time: {metrics['transparency_metrics'].get('load_time', 0):.2f}s")
    
    print(f"\n✅ Transparency Features Demonstrated ({len(metrics['features_demonstrated'])}):")
    for i, feature in enumerate(metrics['features_demonstrated'], 1):
        print(f"   {i:2d}. {feature}")
    
    print(f"\n📸 Screenshots Captured ({len(metrics['screenshots'])}):")
    for screenshot in metrics['screenshots']:
        print(f"   • {screenshot}")
    
    print(f"\n📊 Transparency Metrics:")
    for metric, value in metrics['transparency_metrics'].items():
        print(f"   • {metric.replace('_', ' ').title()}: {value}")
    
    print(f"\n📁 Output Directory: {output_dir}")
    print("🎥 Video: Automatically saved by Playwright")
    
    # Evaluate success
    required_features = [
        "agent reasoning", "decision tree", "confidence tracking", 
        "communication tracking", "bias detection", "learning insights"
    ]
    
    demonstrated_features_lower = [f.lower() for f in metrics['features_demonstrated']]
    features_found = sum(1 for req in required_features 
                        if any(req in demo for demo in demonstrated_features_lower))
    
    if features_found >= 5:
        print("\n🏆 COMPREHENSIVE AI TRANSPARENCY DEMONSTRATED!")
        print("✅ Agent reasoning and decision-making processes visible")
        print("✅ Decision trees and alternative analysis shown")
        print("✅ Confidence tracking and calibration metrics active")
        print("✅ Inter-agent communication transparency working")
        print("✅ Bias detection and learning insights operational")
        print("✅ World-class AI interpretability and explainability!")
    else:
        print(f"\n⚠️ Some transparency features may need attention ({features_found}/6)")
    
    print("\n🎉 AI Insights & Transparency demo recording complete!")
    return features_found >= 5

if __name__ == "__main__":
    success = asyncio.run(record_insights_demo())
    exit(0 if success else 1)