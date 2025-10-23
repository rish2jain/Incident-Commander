#!/usr/bin/env python3
"""
Validation script for latest dashboard improvements
Tests the ExecutiveDashboard.tsx formatting and code quality enhancements
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

def validate_executive_dashboard_improvements():
    """Validate the latest ExecutiveDashboard.tsx improvements"""
    
    results = {
        "validation_type": "latest_dashboard_improvements",
        "timestamp": datetime.now().isoformat(),
        "checks": [],
        "summary": {}
    }
    
    dashboard_path = Path("dashboard/src/components/ExecutiveDashboard.tsx")
    
    # Check 1: File exists and is readable
    check_1 = {
        "name": "ExecutiveDashboard File Accessibility",
        "status": "success" if dashboard_path.exists() else "error",
        "details": f"File exists at {dashboard_path}" if dashboard_path.exists() else "File not found"
    }
    results["checks"].append(check_1)
    
    if dashboard_path.exists():
        try:
            content = dashboard_path.read_text()
            
            # Check 2: Code formatting improvements
            formatting_indicators = [
                "className={",  # Proper className formatting
                "? \"",         # Ternary operator formatting
                "\" :",         # Ternary operator spacing
                "} {",          # JSX expression spacing
                ">{\" \"}",     # String spacing in JSX
            ]
            
            formatting_score = sum(1 for indicator in formatting_indicators if indicator in content)
            check_2 = {
                "name": "Code Formatting Quality",
                "status": "success" if formatting_score >= 3 else "warning",
                "details": f"Found {formatting_score}/5 formatting improvements",
                "score": formatting_score / 5 * 100
            }
            results["checks"].append(check_2)
            
            # Check 3: Professional text improvements
            professional_text_indicators = [
                "Ready to Transform Your Incident Response?",
                "Deploy in 30 minutes with AWS CDK",
                "Full production readiness",
                "View Technical Details",
                "See Live Demo"
            ]
            
            text_score = sum(1 for text in professional_text_indicators if text in content)
            check_3 = {
                "name": "Professional Text Content",
                "status": "success" if text_score >= 4 else "warning",
                "details": f"Found {text_score}/5 professional text elements",
                "score": text_score / 5 * 100
            }
            results["checks"].append(check_3)
            
            # Check 4: Component structure integrity
            component_indicators = [
                "export function ExecutiveDashboard",
                "AnimatedCounter",
                "MetricCard",
                "ROIHighlight",
                "SystemStatus"
            ]
            
            component_score = sum(1 for component in component_indicators if component in content)
            check_4 = {
                "name": "Component Structure Integrity",
                "status": "success" if component_score >= 4 else "error",
                "details": f"Found {component_score}/5 key components",
                "score": component_score / 5 * 100
            }
            results["checks"].append(check_4)
            
            # Check 5: Business metrics integration
            metrics_indicators = [
                "MTTR Reduction",
                "91.8%",
                "$229K",
                "per major incident",
                "Return on Investment"
            ]
            
            metrics_score = sum(1 for metric in metrics_indicators if metric in content)
            check_5 = {
                "name": "Business Metrics Integration",
                "status": "success" if metrics_score >= 4 else "warning",
                "details": f"Found {metrics_score}/5 business metrics",
                "score": metrics_score / 5 * 100
            }
            results["checks"].append(check_5)
            
            # Check 6: Interactive features
            interactive_indicators = [
                "motion.div",
                "whileHover",
                "AnimatePresence",
                "transition",
                "onClick"
            ]
            
            interactive_score = sum(1 for feature in interactive_indicators if feature in content)
            check_6 = {
                "name": "Interactive Features",
                "status": "success" if interactive_score >= 3 else "warning",
                "details": f"Found {interactive_score}/5 interactive features",
                "score": interactive_score / 5 * 100
            }
            results["checks"].append(check_6)
            
        except Exception as e:
            error_check = {
                "name": "File Reading Error",
                "status": "error",
                "details": f"Error reading file: {str(e)}"
            }
            results["checks"].append(error_check)
    
    # Calculate overall summary
    successful_checks = len([c for c in results["checks"] if c["status"] == "success"])
    warning_checks = len([c for c in results["checks"] if c["status"] == "warning"])
    error_checks = len([c for c in results["checks"] if c["status"] == "error"])
    total_checks = len(results["checks"])
    
    # Calculate average score from checks that have scores
    scored_checks = [c for c in results["checks"] if "score" in c]
    average_score = sum(c["score"] for c in scored_checks) / len(scored_checks) if scored_checks else 0
    
    results["summary"] = {
        "total_checks": total_checks,
        "successful": successful_checks,
        "warnings": warning_checks,
        "errors": error_checks,
        "success_rate": (successful_checks / total_checks * 100) if total_checks > 0 else 0,
        "average_score": round(average_score, 1),
        "overall_status": "excellent" if average_score >= 80 else "good" if average_score >= 60 else "needs_improvement"
    }
    
    return results

def main():
    """Main validation function"""
    print("🔍 Validating Latest Dashboard Improvements...")
    print("=" * 60)
    
    # Run validation
    results = validate_executive_dashboard_improvements()
    
    # Display results
    print(f"\n📊 Validation Results:")
    print(f"Timestamp: {results['timestamp']}")
    print(f"Total Checks: {results['summary']['total_checks']}")
    print(f"Success Rate: {results['summary']['success_rate']:.1f}%")
    print(f"Average Score: {results['summary']['average_score']:.1f}%")
    print(f"Overall Status: {results['summary']['overall_status'].upper()}")
    
    print(f"\n📋 Detailed Results:")
    for i, check in enumerate(results["checks"], 1):
        status_icon = "✅" if check["status"] == "success" else "⚠️" if check["status"] == "warning" else "❌"
        score_text = f" ({check['score']:.1f}%)" if "score" in check else ""
        print(f"{i}. {status_icon} {check['name']}{score_text}")
        print(f"   {check['details']}")
    
    # Save results
    output_file = f"hackathon/latest_dashboard_improvements_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: {output_file}")
    
    # Return appropriate exit code
    if results["summary"]["errors"] > 0:
        print("\n❌ Validation completed with errors")
        return 1
    elif results["summary"]["warnings"] > 0:
        print("\n⚠️ Validation completed with warnings")
        return 0
    else:
        print("\n✅ Validation completed successfully")
        return 0

if __name__ == "__main__":
    sys.exit(main())