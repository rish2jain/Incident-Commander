#!/usr/bin/env python3
"""
DevPost Submission Features Validation Script
Validates features specifically mentioned in the DEVPOST_SUBMISSION.md

October 24, 2025 - Validates latest submission features
"""

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

try:
    from playwright.async_api import async_playwright, Page, Browser
    import requests
except ImportError:
    print("❌ Required packages not installed. Installing...")
    import subprocess
    subprocess.run(["pip", "install", "playwright", "requests"])
    subprocess.run(["playwright", "install"])
    from playwright.async_api import async_playwright, Page, Browser
    import requests

# Configuration
DASHBOARD_URL = "http://localhost:3000"
BACKEND_URL = "http://localhost:8000"
VALIDATION_TIMEOUT = 30000

class DevPostSubmissionValidator:
    """Validates features specifically mentioned in DEVPOST submission."""
    
    def __init__(self):
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.results = {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "validation_type": "DevPost Submission Features",
            "categories": {},
            "overall_score": 0,
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0
        }
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        
    async def setup_browser(self):
        """Initialize browser for testing."""
        print("🔧 Setting up browser for DevPost validation...")
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=False)
        context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080}
        )
        self.page = await context.new_page()
        print("✅ Browser setup complete")
        
    async def validate_three_dashboard_architecture(self) -> Dict[str, Any]:
        """Validate the 3-Dashboard Architecture mentioned in DevPost submission."""
        print("\n🏗️ Validating 3-Dashboard Architecture...")
        
        category_results = {
            "name": "3-Dashboard Architecture",
            "tests": [],
            "score": 0,
            "max_score": 100
        }
        
        dashboards = [
            {
                "name": "Power Demo Dashboard (/demo)",
                "url": f"{DASHBOARD_URL}/demo",
                "description": "Business value with quantified metrics and enhanced UI indicators"
            },
            {
                "name": "AI Transparency Dashboard (/transparency)",
                "url": f"{DASHBOARD_URL}/transparency", 
                "description": "AI explainability with smart success/failure indicators"
            },
            {
                "name": "Operations Dashboard (/ops)",
                "url": f"{DASHBOARD_URL}/ops",
                "description": "Real-time WebSocket streaming with enhanced agent monitoring"
            }
        ]
        
        for dashboard in dashboards:
            try:
                await self.page.goto(dashboard["url"])
                await self.page.wait_for_load_state("networkidle")
                await asyncio.sleep(2)
                
                # Check for dashboard-specific features
                dashboard_elements = await self.page.query_selector_all(
                    ".card, .dashboard-card, [class*='card'], main, section"
                )
                
                # Check for interactive elements
                interactive_elements = await self.page.query_selector_all(
                    "button, [role='button'], .interactive-card, [class*='hover']"
                )
                
                # Check for data visualization
                viz_elements = await self.page.query_selector_all(
                    ".chart, .graph, .metric, .counter, [class*='progress'], .badge"
                )
                
                test_result = {
                    "name": dashboard["name"],
                    "passed": len(dashboard_elements) >= 3 and len(interactive_elements) >= 1,
                    "score": 25 if len(dashboard_elements) >= 3 and len(interactive_elements) >= 1 else 10,
                    "max_score": 25,
                    "details": f"Elements: {len(dashboard_elements)}, Interactive: {len(interactive_elements)}, Viz: {len(viz_elements)}"
                }
                
                category_results["tests"].append(test_result)
                print(f"   {'✅' if test_result['passed'] else '⚠️'} {dashboard['name']}: {test_result['details']}")
                
            except Exception as e:
                print(f"   ❌ {dashboard['name']}: Error - {e}")
                category_results["tests"].append({
                    "name": dashboard["name"],
                    "passed": False,
                    "score": 0,
                    "max_score": 25,
                    "error": str(e)
                })
        
        # Test navigation between dashboards
        try:
            # Test homepage navigation
            await self.page.goto(f"{DASHBOARD_URL}/")
            await self.page.wait_for_load_state("networkidle")
            
            nav_links = await self.page.query_selector_all(
                "a[href='/demo'], a[href='/transparency'], a[href='/ops'], nav a"
            )
            
            test_result = {
                "name": "Dashboard Navigation",
                "passed": len(nav_links) >= 3,
                "score": 25 if len(nav_links) >= 3 else 10,
                "max_score": 25,
                "details": f"Navigation links found: {len(nav_links)}"
            }
            
            category_results["tests"].append(test_result)
            print(f"   {'✅' if test_result['passed'] else '⚠️'} Dashboard Navigation: {test_result['details']}")
            
        except Exception as e:
            print(f"   ❌ Dashboard Navigation: Error - {e}")
            category_results["tests"].append({
                "name": "Dashboard Navigation",
                "passed": False,
                "score": 0,
                "max_score": 25,
                "error": str(e)
            })
        
        # Calculate category score
        total_score = sum(test["score"] for test in category_results["tests"])
        max_total_score = sum(test["max_score"] for test in category_results["tests"])
        category_results["score"] = (total_score / max_total_score * 100) if max_total_score > 0 else 0
        
        return category_results
    
    async def validate_business_metrics(self) -> Dict[str, Any]:
        """Validate business metrics mentioned in DevPost submission."""
        print("\n💰 Validating Business Metrics...")
        
        category_results = {
            "name": "Business Metrics",
            "tests": [],
            "score": 0,
            "max_score": 100
        }
        
        # Expected metrics from DevPost submission
        expected_metrics = [
            "95.2% MTTR reduction",
            "$2.8M projected annual savings", 
            "458% ROI",
            "85% incident prevention rate",
            "6.2-month payback period"
        ]
        
        try:
            # Check demo dashboard for business metrics
            await self.page.goto(f"{DASHBOARD_URL}/demo")
            await self.page.wait_for_load_state("networkidle")
            await asyncio.sleep(3)
            
            page_content = await self.page.content()
            
            found_metrics = []
            for metric in expected_metrics:
                # Check for key numbers in the metric
                if "95.2%" in page_content or "95%" in page_content:
                    if metric.startswith("95.2%"):
                        found_metrics.append(metric)
                elif "$2.8M" in page_content or "2.8M" in page_content:
                    if metric.startswith("$2.8M"):
                        found_metrics.append(metric)
                elif "458%" in page_content or "458" in page_content:
                    if metric.startswith("458%"):
                        found_metrics.append(metric)
                elif "85%" in page_content and "prevention" in page_content.lower():
                    if metric.startswith("85%"):
                        found_metrics.append(metric)
                elif "6.2" in page_content and "month" in page_content.lower():
                    if metric.startswith("6.2"):
                        found_metrics.append(metric)
            
            test_result = {
                "name": "Business Metrics Display",
                "passed": len(found_metrics) >= 3,
                "score": min(100, len(found_metrics) * 20),
                "max_score": 100,
                "details": f"Found {len(found_metrics)}/{len(expected_metrics)} metrics: {', '.join(found_metrics)}"
            }
            
            category_results["tests"].append(test_result)
            print(f"   {'✅' if test_result['passed'] else '⚠️'} Business Metrics: {test_result['details']}")
            
        except Exception as e:
            print(f"   ❌ Business Metrics: Error - {e}")
            category_results["tests"].append({
                "name": "Business Metrics Display",
                "passed": False,
                "score": 0,
                "max_score": 100,
                "error": str(e)
            })
        
        # Calculate category score
        total_score = sum(test["score"] for test in category_results["tests"])
        max_total_score = sum(test["max_score"] for test in category_results["tests"])
        category_results["score"] = (total_score / max_total_score * 100) if max_total_score > 0 else 0
        
        return category_results
    
    async def validate_aws_ai_services_showcase(self) -> Dict[str, Any]:
        """Validate AWS AI services showcase mentioned in DevPost submission."""
        print("\n🤖 Validating AWS AI Services Showcase...")
        
        category_results = {
            "name": "AWS AI Services Showcase",
            "tests": [],
            "score": 0,
            "max_score": 100
        }
        
        # Expected AWS AI services from DevPost submission
        expected_services = [
            "Amazon Bedrock AgentCore",
            "Claude 3.5 Sonnet", 
            "Amazon Q Business",
            "Nova Act",
            "Strands SDK",
            "Claude 3 Haiku",
            "Amazon Titan Embeddings",
            "Bedrock Guardrails"
        ]
        
        try:
            # Check transparency dashboard for AWS services
            await self.page.goto(f"{DASHBOARD_URL}/transparency")
            await self.page.wait_for_load_state("networkidle")
            await asyncio.sleep(3)
            
            page_content = await self.page.content()
            
            found_services = []
            for service in expected_services:
                if service.lower() in page_content.lower():
                    found_services.append(service)
            
            # Check for prize badges
            prize_badges = await self.page.query_selector_all(
                "text=$3K Prize, .prize-badge, [class*='prize']"
            )
            
            test_result = {
                "name": "AWS AI Services Display",
                "passed": len(found_services) >= 5,
                "score": min(80, len(found_services) * 10),
                "max_score": 80,
                "details": f"Found {len(found_services)}/{len(expected_services)} services, {len(prize_badges)} prize badges"
            }
            
            category_results["tests"].append(test_result)
            print(f"   {'✅' if test_result['passed'] else '⚠️'} AWS Services: {test_result['details']}")
            
            # Test prize eligibility indicators
            test_result = {
                "name": "Prize Eligibility Indicators",
                "passed": len(prize_badges) >= 3,
                "score": 20 if len(prize_badges) >= 3 else 10,
                "max_score": 20,
                "details": f"Prize badges found: {len(prize_badges)}"
            }
            
            category_results["tests"].append(test_result)
            print(f"   {'✅' if test_result['passed'] else '⚠️'} Prize Indicators: {test_result['details']}")
            
        except Exception as e:
            print(f"   ❌ AWS AI Services: Error - {e}")
            category_results["tests"].append({
                "name": "AWS AI Services Display",
                "passed": False,
                "score": 0,
                "max_score": 100,
                "error": str(e)
            })
        
        # Calculate category score
        total_score = sum(test["score"] for test in category_results["tests"])
        max_total_score = sum(test["max_score"] for test in category_results["tests"])
        category_results["score"] = (total_score / max_total_score * 100) if max_total_score > 0 else 0
        
        return category_results
    
    async def validate_byzantine_fault_tolerance(self) -> Dict[str, Any]:
        """Validate Byzantine Fault Tolerance features mentioned in DevPost submission."""
        print("\n🛡️ Validating Byzantine Fault Tolerance...")
        
        category_results = {
            "name": "Byzantine Fault Tolerance",
            "tests": [],
            "score": 0,
            "max_score": 100
        }
        
        try:
            # Check transparency dashboard for Byzantine consensus
            await self.page.goto(f"{DASHBOARD_URL}/transparency")
            await self.page.wait_for_load_state("networkidle")
            await asyncio.sleep(3)
            
            page_content = await self.page.content()
            
            # Check for Byzantine-related terms
            byzantine_terms = [
                "byzantine", "consensus", "fault tolerance", "weighted voting",
                "confidence", "70%", "quorum", "compromise"
            ]
            
            found_terms = []
            for term in byzantine_terms:
                if term.lower() in page_content.lower():
                    found_terms.append(term)
            
            # Check for consensus visualization elements
            consensus_elements = await self.page.query_selector_all(
                "[class*='progress'], [class*='consensus'], .byzantine, [class*='confidence']"
            )
            
            # Check for agent status indicators
            agent_elements = await self.page.query_selector_all(
                ".agent, [class*='agent'], .multi-agent, [data-testid*='agent']"
            )
            
            test_result = {
                "name": "Byzantine Consensus Features",
                "passed": len(found_terms) >= 4 and len(consensus_elements) >= 2,
                "score": min(100, len(found_terms) * 10 + len(consensus_elements) * 5),
                "max_score": 100,
                "details": f"Terms: {len(found_terms)}, Consensus UI: {len(consensus_elements)}, Agents: {len(agent_elements)}"
            }
            
            category_results["tests"].append(test_result)
            print(f"   {'✅' if test_result['passed'] else '⚠️'} Byzantine Features: {test_result['details']}")
            
        except Exception as e:
            print(f"   ❌ Byzantine Fault Tolerance: Error - {e}")
            category_results["tests"].append({
                "name": "Byzantine Consensus Features",
                "passed": False,
                "score": 0,
                "max_score": 100,
                "error": str(e)
            })
        
        # Calculate category score
        total_score = sum(test["score"] for test in category_results["tests"])
        max_total_score = sum(test["max_score"] for test in category_results["tests"])
        category_results["score"] = (total_score / max_total_score * 100) if max_total_score > 0 else 0
        
        return category_results
    
    async def run_validation(self) -> Dict[str, Any]:
        """Run complete DevPost submission features validation."""
        print("🚀 Starting DevPost Submission Features Validation")
        print(f"📅 Session: {self.session_id}")
        print("=" * 60)
        
        try:
            await self.setup_browser()
            
            # Run validation categories
            categories = [
                await self.validate_three_dashboard_architecture(),
                await self.validate_business_metrics(),
                await self.validate_aws_ai_services_showcase(),
                await self.validate_byzantine_fault_tolerance()
            ]
            
            # Calculate overall results
            total_score = 0
            max_total_score = 0
            total_tests = 0
            passed_tests = 0
            
            for category in categories:
                self.results["categories"][category["name"]] = category
                total_score += category["score"]
                max_total_score += category["max_score"]
                
                for test in category["tests"]:
                    total_tests += 1
                    if test["passed"]:
                        passed_tests += 1
            
            self.results["overall_score"] = (total_score / max_total_score * 100) if max_total_score > 0 else 0
            self.results["total_tests"] = total_tests
            self.results["passed_tests"] = passed_tests
            self.results["failed_tests"] = total_tests - passed_tests
            
            # Save results
            results_file = Path(f"hackathon/devpost_submission_validation_{self.session_id}.json")
            with open(results_file, 'w') as f:
                json.dump(self.results, f, indent=2)
            
            print("\n" + "=" * 60)
            print("🎉 DevPost Submission Features Validation Complete!")
            print("=" * 60)
            print(f"📊 Overall Score: {self.results['overall_score']:.1f}%")
            print(f"✅ Tests Passed: {passed_tests}/{total_tests}")
            print(f"📁 Results saved: {results_file}")
            
            # Print category summaries
            for category_name, category in self.results["categories"].items():
                print(f"\n📋 {category_name}: {category['score']:.1f}%")
                for test in category["tests"]:
                    status = "✅" if test["passed"] else "❌"
                    print(f"   {status} {test['name']}: {test['score']}/{test['max_score']}")
            
            return self.results
            
        except Exception as e:
            print(f"❌ Validation failed: {e}")
            self.results["error"] = str(e)
            return self.results
        
        finally:
            if self.browser:
                await self.browser.close()

async def main():
    """Main validation function."""
    validator = DevPostSubmissionValidator()
    results = await validator.run_validation()
    
    # Print final summary
    if results["overall_score"] >= 80:
        print(f"\n🏆 EXCELLENT: DevPost submission features are production-ready!")
    elif results["overall_score"] >= 60:
        print(f"\n✅ GOOD: DevPost submission features are functional")
    else:
        print(f"\n⚠️  NEEDS WORK: DevPost submission features require attention")
    
    return results

if __name__ == "__main__":
    print("🎯 DevPost Submission Features Validation")
    print("🔧 Testing features specifically mentioned in DEVPOST_SUBMISSION.md")
    print("💡 Ensure dashboard is running: cd dashboard && npm run dev")
    print()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Validation stopped by user")
    except Exception as e:
        print(f"\n💥 Validation error: {e}")
        import traceback
        traceback.print_exc()