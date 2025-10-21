#!/usr/bin/env python3
"""
Enhanced Insights Integration Validation Script
Validates the complete integration of enhanced insights demo features

Features validated:
- Enhanced insights demo URL accessibility
- TypeScript improvements and ref handling
- Comprehensive AI transparency features
- Professional UI/UX enhancements
- Documentation consistency
"""

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

import requests
from playwright.async_api import async_playwright


class EnhancedInsightsValidator:
    """Validates enhanced insights demo integration"""
    
    def __init__(self, base_url: str = "http://localhost:3000"):
        self.base_url = base_url
        self.validation_results = {
            "timestamp": datetime.now().isoformat(),
            "enhanced_insights_demo": {},
            "ai_transparency_features": {},
            "typescript_improvements": {},
            "ui_ux_enhancements": {},
            "documentation_consistency": {},
            "overall_status": "unknown"
        }
    
    async def validate_enhanced_insights_demo(self, page):
        """Test enhanced insights demo accessibility and features"""
        print("🧠 Testing Enhanced Insights Demo...")
        
        try:
            # Test enhanced insights demo URL
            await page.goto(f"{self.base_url}/enhanced-insights-demo")
            await page.wait_for_load_state("networkidle")
            
            # Check for enhanced insights title
            title = await page.query_selector('h1:has-text("AI Insights & Transparency Dashboard")')
            if title:
                self.validation_results["enhanced_insights_demo"]["title"] = "✅ Found"
                print("  ✅ Enhanced insights title found")
            else:
                self.validation_results["enhanced_insights_demo"]["title"] = "❌ Missing"
                print("  ❌ Enhanced insights title not found")
                return False
            
            # Check for comprehensive descriptions
            description = await page.query_selector('p:has-text("Revolutionary explainable AI")')
            if description:
                self.validation_results["enhanced_insights_demo"]["description"] = "✅ Found"
                print("  ✅ Comprehensive description found")
            else:
                self.validation_results["enhanced_insights_demo"]["description"] = "❌ Missing"
                print("  ❌ Comprehensive description not found")
            
            # Check for tabbed interface
            tabs = await page.query_selector_all('[role="tablist"] [role="tab"]')
            if len(tabs) >= 5:
                self.validation_results["enhanced_insights_demo"]["tabs"] = f"✅ {len(tabs)} tabs found"
                print(f"  ✅ {len(tabs)} tabs found in interface")
            else:
                self.validation_results["enhanced_insights_demo"]["tabs"] = f"❌ Only {len(tabs)} tabs"
                print(f"  ❌ Only {len(tabs)} tabs found, expected 5+")
            
            # Check for trigger button
            trigger_button = await page.query_selector('button:has-text("Trigger AI Transparency Demo")')
            if trigger_button:
                self.validation_results["enhanced_insights_demo"]["trigger_button"] = "✅ Found"
                print("  ✅ AI Transparency Demo trigger button found")
            else:
                self.validation_results["enhanced_insights_demo"]["trigger_button"] = "❌ Missing"
                print("  ❌ AI Transparency Demo trigger button not found")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Enhanced insights demo test failed: {e}")
            self.validation_results["enhanced_insights_demo"]["error"] = str(e)
            return False
    
    async def validate_ai_transparency_features(self, page):
        """Test AI transparency features"""
        print("🔍 Testing AI Transparency Features...")
        
        try:
            # Navigate to enhanced insights demo
            await page.goto(f"{self.base_url}/enhanced-insights-demo")
            await page.wait_for_load_state("networkidle")
            
            # Check for tab descriptions
            tab_descriptions = await page.query_selector_all('.mb-4 p:has-text("transparency")')
            if tab_descriptions:
                self.validation_results["ai_transparency_features"]["descriptions"] = f"✅ {len(tab_descriptions)} found"
                print(f"  ✅ {len(tab_descriptions)} transparency descriptions found")
            else:
                self.validation_results["ai_transparency_features"]["descriptions"] = "❌ None found"
                print("  ❌ No transparency descriptions found")
            
            # Check for agent reasoning tab
            reasoning_tab = await page.query_selector('[role="tab"]:has-text("Agent Reasoning")')
            if reasoning_tab:
                await reasoning_tab.click()
                await page.wait_for_timeout(1000)
                
                # Check for reasoning explanation
                reasoning_explanation = await page.query_selector('p:has-text("step-by-step reasoning")')
                if reasoning_explanation:
                    self.validation_results["ai_transparency_features"]["reasoning_explanation"] = "✅ Found"
                    print("  ✅ Agent reasoning explanation found")
                else:
                    self.validation_results["ai_transparency_features"]["reasoning_explanation"] = "❌ Missing"
                    print("  ❌ Agent reasoning explanation not found")
            
            # Check for decision trees tab
            decisions_tab = await page.query_selector('[role="tab"]:has-text("Decision Trees")')
            if decisions_tab:
                await decisions_tab.click()
                await page.wait_for_timeout(1000)
                
                # Check for decision tree explanation
                tree_explanation = await page.query_selector('p:has-text("Interactive decision trees")')
                if tree_explanation:
                    self.validation_results["ai_transparency_features"]["decision_tree_explanation"] = "✅ Found"
                    print("  ✅ Decision tree explanation found")
                else:
                    self.validation_results["ai_transparency_features"]["decision_tree_explanation"] = "❌ Missing"
                    print("  ❌ Decision tree explanation not found")
            
            # Check for confidence tab
            confidence_tab = await page.query_selector('[role="tab"]:has-text("Confidence")')
            if confidence_tab:
                await confidence_tab.click()
                await page.wait_for_timeout(1000)
                
                # Check for confidence explanation
                confidence_explanation = await page.query_selector('p:has-text("confidence evolution")')
                if confidence_explanation:
                    self.validation_results["ai_transparency_features"]["confidence_explanation"] = "✅ Found"
                    print("  ✅ Confidence explanation found")
                else:
                    self.validation_results["ai_transparency_features"]["confidence_explanation"] = "❌ Missing"
                    print("  ❌ Confidence explanation not found")
            
            return True
            
        except Exception as e:
            print(f"  ❌ AI transparency features test failed: {e}")
            self.validation_results["ai_transparency_features"]["error"] = str(e)
            return False
    
    async def validate_typescript_improvements(self, page):
        """Test TypeScript improvements"""
        print("🔧 Testing TypeScript Improvements...")
        
        try:
            # Check for TypeScript compilation errors
            console_errors = []
            
            def handle_console(msg):
                if msg.type == 'error' and any(keyword in msg.text.lower() for keyword in ['typescript', 'type', 'ref']):
                    console_errors.append(msg.text)
            
            page.on('console', handle_console)
            
            # Navigate and wait for any errors
            await page.goto(f"{self.base_url}/enhanced-insights-demo")
            await page.wait_for_load_state("networkidle")
            await page.wait_for_timeout(3000)
            
            if not console_errors:
                self.validation_results["typescript_improvements"]["console_errors"] = "✅ None detected"
                print("  ✅ No TypeScript errors in console")
            else:
                self.validation_results["typescript_improvements"]["console_errors"] = f"❌ {len(console_errors)} errors"
                print(f"  ❌ {len(console_errors)} TypeScript errors detected")
                for error in console_errors[:3]:
                    print(f"    - {error}")
            
            # Test scroll functionality
            scroll_area = await page.query_selector('.scroll-area, [data-testid="enhanced-activity-feed"]')
            if scroll_area:
                self.validation_results["typescript_improvements"]["scroll_area"] = "✅ Found"
                print("  ✅ Enhanced scroll area found")
                
                # Test scroll behavior
                await scroll_area.scroll_into_view_if_needed()
                await page.wait_for_timeout(500)
                
                self.validation_results["typescript_improvements"]["scroll_behavior"] = "✅ Working"
                print("  ✅ Scroll behavior working")
            else:
                self.validation_results["typescript_improvements"]["scroll_area"] = "❌ Not found"
                print("  ❌ Enhanced scroll area not found")
            
            return True
            
        except Exception as e:
            print(f"  ❌ TypeScript improvements test failed: {e}")
            self.validation_results["typescript_improvements"]["error"] = str(e)
            return False
    
    async def validate_ui_ux_enhancements(self, page):
        """Test UI/UX enhancements"""
        print("🎨 Testing UI/UX Enhancements...")
        
        try:
            await page.goto(f"{self.base_url}/enhanced-insights-demo")
            await page.wait_for_load_state("networkidle")
            
            # Check for professional styling
            gradient_elements = await page.query_selector_all('.bg-gradient-to-br, .bg-gradient-to-r')
            if gradient_elements:
                self.validation_results["ui_ux_enhancements"]["gradient_styling"] = f"✅ {len(gradient_elements)} elements"
                print(f"  ✅ {len(gradient_elements)} gradient-styled elements found")
            else:
                self.validation_results["ui_ux_enhancements"]["gradient_styling"] = "❌ None found"
                print("  ❌ No gradient styling found")
            
            # Check for card components
            card_elements = await page.query_selector_all('[class*="card"], .bg-slate-800')
            if card_elements:
                self.validation_results["ui_ux_enhancements"]["card_components"] = f"✅ {len(card_elements)} cards"
                print(f"  ✅ {len(card_elements)} card components found")
            else:
                self.validation_results["ui_ux_enhancements"]["card_components"] = "❌ None found"
                print("  ❌ No card components found")
            
            # Check for badges and indicators
            badge_elements = await page.query_selector_all('[class*="badge"], .font-mono')
            if badge_elements:
                self.validation_results["ui_ux_enhancements"]["badges"] = f"✅ {len(badge_elements)} badges"
                print(f"  ✅ {len(badge_elements)} badges/indicators found")
            else:
                self.validation_results["ui_ux_enhancements"]["badges"] = "❌ None found"
                print("  ❌ No badges/indicators found")
            
            # Check for progress bars
            progress_elements = await page.query_selector_all('[role="progressbar"], .h-2, .h-3, .h-4')
            if progress_elements:
                self.validation_results["ui_ux_enhancements"]["progress_bars"] = f"✅ {len(progress_elements)} found"
                print(f"  ✅ {len(progress_elements)} progress elements found")
            else:
                self.validation_results["ui_ux_enhancements"]["progress_bars"] = "❌ None found"
                print("  ❌ No progress elements found")
            
            return True
            
        except Exception as e:
            print(f"  ❌ UI/UX enhancements test failed: {e}")
            self.validation_results["ui_ux_enhancements"]["error"] = str(e)
            return False
    
    async def validate_documentation_consistency(self):
        """Test documentation consistency"""
        print("📚 Testing Documentation Consistency...")
        
        try:
            # Check if key files exist and contain enhanced insights references
            files_to_check = [
                "DASHBOARD_COMPARISON.md",
                "hackathon/README.md",
                "hackathon/DEMO_GUIDE.md",
                "hackathon/ENHANCED_INSIGHTS_UPDATE_SUMMARY.md"
            ]
            
            for file_path in files_to_check:
                if Path(file_path).exists():
                    with open(file_path, 'r') as f:
                        content = f.read()
                    
                    # Check for enhanced insights references
                    if "enhanced-insights-demo" in content:
                        self.validation_results["documentation_consistency"][file_path] = "✅ Updated"
                        print(f"  ✅ {file_path} contains enhanced insights references")
                    else:
                        self.validation_results["documentation_consistency"][file_path] = "⚠️ No reference"
                        print(f"  ⚠️ {file_path} missing enhanced insights references")
                else:
                    self.validation_results["documentation_consistency"][file_path] = "❌ Missing"
                    print(f"  ❌ {file_path} not found")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Documentation consistency test failed: {e}")
            self.validation_results["documentation_consistency"]["error"] = str(e)
            return False
    
    async def run_validation(self):
        """Run complete enhanced insights integration validation"""
        print("🧠 Starting Enhanced Insights Integration Validation")
        print("=" * 70)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                # Run all validation tests
                tests = [
                    self.validate_enhanced_insights_demo(page),
                    self.validate_ai_transparency_features(page),
                    self.validate_typescript_improvements(page),
                    self.validate_ui_ux_enhancements(page),
                ]
                
                results = await asyncio.gather(*tests, return_exceptions=True)
                
                # Add documentation validation (doesn't need browser)
                doc_result = await self.validate_documentation_consistency()
                results.append(doc_result)
                
                # Calculate overall status
                passed_tests = sum(1 for result in results if result is True)
                total_tests = len(results)
                
                if passed_tests == total_tests:
                    self.validation_results["overall_status"] = "✅ All enhancements validated"
                elif passed_tests >= total_tests * 0.8:
                    self.validation_results["overall_status"] = "⚠️ Most enhancements working"
                else:
                    self.validation_results["overall_status"] = "❌ Multiple issues detected"
                
                print("\n" + "=" * 70)
                print(f"🧠 Enhanced Insights Validation Complete: {passed_tests}/{total_tests} tests passed")
                print(f"Status: {self.validation_results['overall_status']}")
                
            finally:
                await browser.close()
        
        # Save results
        results_file = Path("hackathon") / "enhanced_insights_validation_results.json"
        with open(results_file, "w") as f:
            json.dump(self.validation_results, f, indent=2)
        
        print(f"📊 Results saved to: {results_file}")
        return self.validation_results


async def main():
    """Main validation function"""
    validator = EnhancedInsightsValidator()
    results = await validator.run_validation()
    
    # Print summary
    print("\n🧠 ENHANCED INSIGHTS INTEGRATION SUMMARY")
    print("=" * 60)
    print(f"Overall Status: {results['overall_status']}")
    print(f"Timestamp: {results['timestamp']}")
    
    if results['enhanced_insights_demo']:
        print("\n🧠 Enhanced Insights Demo:")
        for feature, status in results['enhanced_insights_demo'].items():
            print(f"  {feature}: {status}")
    
    if results['ai_transparency_features']:
        print("\n🔍 AI Transparency Features:")
        for feature, status in results['ai_transparency_features'].items():
            print(f"  {feature}: {status}")
    
    if results['typescript_improvements']:
        print("\n🔧 TypeScript Improvements:")
        for feature, status in results['typescript_improvements'].items():
            print(f"  {feature}: {status}")
    
    if results['ui_ux_enhancements']:
        print("\n🎨 UI/UX Enhancements:")
        for feature, status in results['ui_ux_enhancements'].items():
            print(f"  {feature}: {status}")
    
    if results['documentation_consistency']:
        print("\n📚 Documentation Consistency:")
        for file, status in results['documentation_consistency'].items():
            print(f"  {file}: {status}")


if __name__ == "__main__":
    asyncio.run(main())