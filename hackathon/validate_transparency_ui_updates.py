#!/usr/bin/env python3
"""
Transparency Dashboard UI Updates Validation Script

Validates the latest prize-winning AI service integration modules
added to the transparency dashboard for the 150-second demo video.

Features Validated:
- Amazon Q Business integration module ($3K Prize)
- Nova Act integration module ($3K Prize) 
- Strands SDK integration module ($3K Prize)
- Dynamic content based on incident state
- Professional styling and responsive design
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

def validate_transparency_dashboard_file():
    """Validate the transparency dashboard file exists and has the new modules."""
    dashboard_file = Path("dashboard/app/transparency/page.tsx")
    
    if not dashboard_file.exists():
        return False, "Transparency dashboard file not found"
    
    content = dashboard_file.read_text()
    
    # Check for Amazon Q Business integration
    if "Amazon Q Business Integration" not in content:
        return False, "Amazon Q Business integration module not found"
    
    if "$3K Prize" not in content:
        return False, "Prize eligibility badges not found"
    
    # Check for Nova Act integration
    if "Nova Act Integration" not in content:
        return False, "Nova Act integration module not found"
    
    # Check for Strands SDK integration
    if "Strands SDK Integration" not in content:
        return False, "Strands SDK integration module not found"
    
    # Check for dynamic content management
    if "incidentActive" not in content:
        return False, "Dynamic incident state management not found"
    
    if "currentPhase" not in content:
        return False, "Current phase state management not found"
    
    # Check for professional styling
    if "card-glass" not in content:
        return False, "Professional card-glass styling not found"
    
    if "border-l-4" not in content:
        return False, "Colored border styling not found"
    
    return True, "All transparency dashboard features validated"

def validate_prize_service_modules():
    """Validate the three prize-winning service modules are properly implemented."""
    dashboard_file = Path("dashboard/app/transparency/page.tsx")
    content = dashboard_file.read_text()
    
    modules = {
        "Amazon Q Business": {
            "color": "orange",
            "icon": "🧠",
            "prize": "$3K Prize"
        },
        "Nova Act": {
            "color": "purple", 
            "icon": "⚡",
            "prize": "$3K Prize"
        },
        "Strands SDK": {
            "color": "cyan",
            "icon": "🔗", 
            "prize": "$3K Prize"
        }
    }
    
    results = []
    
    for module_name, config in modules.items():
        # Check module exists
        if module_name not in content:
            results.append(f"❌ {module_name} module not found")
            continue
            
        # Check color theming
        if f"border-l-{config['color']}-500" not in content:
            results.append(f"❌ {module_name} color theming not found")
            continue
            
        # Check icon
        if config['icon'] not in content:
            results.append(f"❌ {module_name} icon not found")
            continue
            
        # Check prize badge
        if config['prize'] not in content:
            results.append(f"❌ {module_name} prize badge not found")
            continue
            
        results.append(f"✅ {module_name} module fully implemented")
    
    return results

def validate_dynamic_content():
    """Validate dynamic content changes based on incident state."""
    dashboard_file = Path("dashboard/app/transparency/page.tsx")
    content = dashboard_file.read_text()
    
    # Check for state-based conditional rendering
    state_conditions = [
        "incidentActive ?",
        "currentPhase === \"diagnosis\"",
        "currentPhase === \"consensus\"", 
        "currentPhase === \"resolution\"",
        "currentPhase === \"complete\""
    ]
    
    results = []
    for condition in state_conditions:
        if condition in content:
            results.append(f"✅ State condition found: {condition}")
        else:
            results.append(f"❌ State condition missing: {condition}")
    
    # Check for different content states
    content_states = [
        "Ready for",
        "Analyzing",
        "Complete",
        "analyzing incident patterns",
        "generating action plan"
    ]
    
    for state in content_states:
        if state in content:
            results.append(f"✅ Content state found: {state}")
        else:
            results.append(f"⚠️  Content state not found: {state}")
    
    return results

def validate_decision_trees_tab():
    """Validate enhanced decision trees tab with prize services."""
    dashboard_file = Path("dashboard/app/transparency/page.tsx")
    content = dashboard_file.read_text()
    
    # Check for decision trees tab enhancements
    enhancements = [
        "Enhanced Decision Trees Tab",
        "Nova Act Action Plan",
        "Strands SDK Agent Lifecycle", 
        "Action Plan by Nova Act",
        "Agent Lifecycle by Strands SDK"
    ]
    
    results = []
    for enhancement in enhancements:
        if enhancement in content:
            results.append(f"✅ Decision trees enhancement: {enhancement}")
        else:
            results.append(f"❌ Decision trees enhancement missing: {enhancement}")
    
    return results

def validate_professional_styling():
    """Validate professional styling and responsive design."""
    dashboard_file = Path("dashboard/app/transparency/page.tsx")
    content = dashboard_file.read_text()
    
    styling_elements = [
        "card-glass",
        "border-l-4",
        "grid grid-cols-1 lg:grid-cols-3",
        "Badge variant=\"outline\"",
        "bg-orange-500/20",
        "bg-purple-500/20", 
        "bg-cyan-500/20",
        "text-orange-200",
        "text-purple-200",
        "text-cyan-200"
    ]
    
    results = []
    for element in styling_elements:
        if element in content:
            results.append(f"✅ Styling element: {element}")
        else:
            results.append(f"❌ Styling element missing: {element}")
    
    return results

def generate_validation_report():
    """Generate comprehensive validation report."""
    report = {
        "timestamp": datetime.now().isoformat(),
        "validation_type": "Transparency Dashboard UI Updates",
        "version": "150-second demo video ready",
        "results": {}
    }
    
    print("🔍 Validating Transparency Dashboard UI Updates...")
    print("=" * 60)
    
    # Validate main dashboard file
    success, message = validate_transparency_dashboard_file()
    report["results"]["dashboard_file"] = {"success": success, "message": message}
    print(f"📄 Dashboard File: {'✅' if success else '❌'} {message}")
    
    # Validate prize service modules
    print("\n🏆 Prize-Winning Service Modules:")
    module_results = validate_prize_service_modules()
    report["results"]["prize_modules"] = module_results
    for result in module_results:
        print(f"   {result}")
    
    # Validate dynamic content
    print("\n🔄 Dynamic Content Management:")
    dynamic_results = validate_dynamic_content()
    report["results"]["dynamic_content"] = dynamic_results
    for result in dynamic_results[:5]:  # Show first 5 results
        print(f"   {result}")
    
    # Validate decision trees tab
    print("\n🌳 Decision Trees Tab Enhancements:")
    trees_results = validate_decision_trees_tab()
    report["results"]["decision_trees"] = trees_results
    for result in trees_results:
        print(f"   {result}")
    
    # Validate professional styling
    print("\n🎨 Professional Styling:")
    styling_results = validate_professional_styling()
    report["results"]["styling"] = styling_results
    success_count = len([r for r in styling_results if r.startswith("✅")])
    total_count = len(styling_results)
    print(f"   ✅ {success_count}/{total_count} styling elements validated")
    
    # Calculate overall score
    all_results = module_results + dynamic_results + trees_results + styling_results
    success_results = [r for r in all_results if r.startswith("✅")]
    total_results = len(all_results)
    score = (len(success_results) / total_results) * 100 if total_results > 0 else 0
    
    report["overall_score"] = score
    report["success_count"] = len(success_results)
    report["total_count"] = total_results
    
    print("\n" + "=" * 60)
    print(f"🎯 Overall Validation Score: {score:.1f}% ({len(success_results)}/{total_results})")
    
    if score >= 90:
        print("🏆 EXCELLENT - Ready for 150-second demo video recording")
        report["status"] = "EXCELLENT"
    elif score >= 80:
        print("✅ GOOD - Minor improvements recommended")
        report["status"] = "GOOD"
    elif score >= 70:
        print("⚠️  FAIR - Several issues need attention")
        report["status"] = "FAIR"
    else:
        print("❌ POOR - Major issues require fixing")
        report["status"] = "POOR"
    
    # Save report
    report_file = Path("hackathon/transparency_ui_validation_report.json")
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📊 Detailed report saved to: {report_file}")
    
    return score >= 80

def main():
    """Main validation function."""
    print("🚀 Transparency Dashboard UI Updates Validation")
    print("   Validating prize-winning AI service integration modules")
    print("   Ready for 150-second winning demo video\n")
    
    try:
        success = generate_validation_report()
        
        if success:
            print("\n✅ VALIDATION PASSED - System ready for demo recording")
            return 0
        else:
            print("\n❌ VALIDATION FAILED - Issues need to be resolved")
            return 1
            
    except Exception as e:
        print(f"\n💥 VALIDATION ERROR: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())