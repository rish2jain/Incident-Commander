#!/usr/bin/env python3
"""
Dashboard Layout System Validation - October 22, 2025
Validates the shared dashboard layout components and design system
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Tuple


class DashboardLayoutValidator:
    """Validates the shared dashboard layout system and design tokens"""
    
    def __init__(self):
        self.dashboard_dir = Path("dashboard")
        self.validation_results = []
        
    def validate_shared_components(self) -> Dict[str, str]:
        """Validate shared dashboard components exist and are properly structured"""
        results = {}
        
        # Check DashboardLayout component
        layout_path = self.dashboard_dir / "src/components/shared/DashboardLayout.tsx"
        if layout_path.exists():
            with open(layout_path, 'r') as f:
                content = f.read()
                
            # Check for required components
            required_components = [
                "DashboardLayout",
                "DashboardSection", 
                "DashboardGrid"
            ]
            
            missing_components = []
            for component in required_components:
                if f"export function {component}" not in content:
                    missing_components.append(component)
            
            if not missing_components:
                results["Shared Components"] = "✅ All 3 components (DashboardLayout, DashboardSection, DashboardGrid) found"
            else:
                results["Shared Components"] = f"❌ Missing components: {', '.join(missing_components)}"
                
            # Check for TypeScript interfaces
            if "interface DashboardLayoutProps" in content and "interface DashboardSectionProps" in content:
                results["TypeScript Interfaces"] = "✅ Proper TypeScript interfaces defined"
            else:
                results["TypeScript Interfaces"] = "❌ Missing TypeScript interfaces"
                
        else:
            results["Shared Components"] = "❌ DashboardLayout.tsx not found"
            results["TypeScript Interfaces"] = "❌ Cannot validate - file missing"
        
        return results
    
    def validate_design_tokens(self) -> Dict[str, str]:
        """Validate centralized design tokens system"""
        results = {}
        
        # Check design tokens file
        tokens_path = self.dashboard_dir / "src/styles/design-tokens.css"
        if tokens_path.exists():
            with open(tokens_path, 'r') as f:
                content = f.read()
            
            # Check for required token categories
            required_tokens = [
                "--space-", "--text-", "--radius-", "--shadow-",
                "--brand-primary", "--brand-secondary", "--brand-accent",
                "--agent-detection", "--agent-diagnosis", "--agent-prediction",
                "--severity-critical", "--severity-high", "--severity-medium",
                "--glass-bg", "--glass-border"
            ]
            
            missing_tokens = []
            for token in required_tokens:
                if token not in content:
                    missing_tokens.append(token)
            
            if not missing_tokens:
                results["Design Tokens"] = "✅ All required design tokens found"
            else:
                results["Design Tokens"] = f"⚠️ Missing tokens: {', '.join(missing_tokens[:3])}..."
            
            # Check for component utilities
            if ".card-glass" in content and ".dashboard-container" in content:
                results["Component Utilities"] = "✅ Component utility classes defined"
            else:
                results["Component Utilities"] = "❌ Missing component utility classes"
                
        else:
            results["Design Tokens"] = "❌ design-tokens.css not found"
            results["Component Utilities"] = "❌ Cannot validate - file missing"
        
        return results
    
    def validate_dashboard_views(self) -> Dict[str, str]:
        """Validate the three specialized dashboard views"""
        results = {}
        
        app_dir = self.dashboard_dir / "app"
        required_views = ["demo", "transparency", "ops"]
        
        for view in required_views:
            view_path = app_dir / view
            if view_path.exists() and view_path.is_dir():
                results[f"/{view} View"] = "✅ Directory exists"
            else:
                results[f"/{view} View"] = "❌ Directory missing"
        
        # Check main page navigation
        page_path = app_dir / "page.tsx"
        if page_path.exists():
            with open(page_path, 'r') as f:
                content = f.read()
            
            # Check for navigation links to all views
            if all(f'href="/{view}"' in content for view in required_views):
                results["Navigation Links"] = "✅ All 3 dashboard views linked from homepage"
            else:
                results["Navigation Links"] = "⚠️ Some navigation links missing"
        else:
            results["Navigation Links"] = "❌ Main page.tsx not found"
        
        return results
    
    def validate_consistency(self) -> Dict[str, str]:
        """Validate consistency across dashboard implementation"""
        results = {}
        
        # Check if shared components are being imported
        src_dir = self.dashboard_dir / "src/components"
        if src_dir.exists():
            tsx_files = list(src_dir.glob("**/*.tsx"))
            
            shared_imports = 0
            for file_path in tsx_files:
                if file_path.name != "DashboardLayout.tsx":  # Skip the definition file
                    with open(file_path, 'r') as f:
                        content = f.read()
                    if "from.*shared.*DashboardLayout" in content or "DashboardLayout" in content:
                        shared_imports += 1
            
            if shared_imports > 0:
                results["Component Usage"] = f"✅ Shared components used in {shared_imports} files"
            else:
                results["Component Usage"] = "⚠️ Shared components not yet widely adopted"
        else:
            results["Component Usage"] = "❌ Components directory not found"
        
        # Check for consistent styling approach
        if (self.dashboard_dir / "tailwind.config.js").exists():
            results["Styling System"] = "✅ Tailwind CSS configured"
        else:
            results["Styling System"] = "❌ Tailwind config missing"
        
        return results
    
    def generate_validation_report(self) -> Dict:
        """Generate comprehensive validation report"""
        shared_results = self.validate_shared_components()
        tokens_results = self.validate_design_tokens()
        views_results = self.validate_dashboard_views()
        consistency_results = self.validate_consistency()
        
        all_results = {
            **shared_results,
            **tokens_results, 
            **views_results,
            **consistency_results
        }
        
        # Count success/warning/error status
        success_count = len([r for r in all_results.values() if r.startswith("✅")])
        warning_count = len([r for r in all_results.values() if r.startswith("⚠️")])
        error_count = len([r for r in all_results.values() if r.startswith("❌")])
        total_checks = len(all_results)
        
        # Calculate score
        score = (success_count * 100 + warning_count * 50) / (total_checks * 100) * 100
        
        report = {
            "validation_timestamp": "2025-10-22T12:00:00Z",
            "dashboard_layout_system": {
                "total_checks": total_checks,
                "successful": success_count,
                "warnings": warning_count,
                "errors": error_count,
                "score_percentage": round(score, 1),
                "details": all_results
            },
            "overall_status": self.get_overall_status(score),
            "recommendations": self.generate_recommendations(all_results)
        }
        
        return report
    
    def get_overall_status(self, score: float) -> str:
        """Get overall status based on score"""
        if score >= 90:
            return "✅ EXCELLENT - Dashboard layout system fully implemented"
        elif score >= 75:
            return "✅ GOOD - Dashboard layout system mostly complete"
        elif score >= 60:
            return "⚠️ FAIR - Dashboard layout system partially implemented"
        else:
            return "❌ NEEDS WORK - Dashboard layout system requires attention"
    
    def generate_recommendations(self, results: Dict[str, str]) -> List[str]:
        """Generate recommendations based on validation results"""
        recommendations = []
        
        for check, result in results.items():
            if result.startswith("❌"):
                if "Shared Components" in check:
                    recommendations.append("Implement missing shared dashboard components")
                elif "Design Tokens" in check:
                    recommendations.append("Complete design tokens system implementation")
                elif "View" in check:
                    recommendations.append(f"Create missing dashboard view: {check}")
                elif "Navigation" in check:
                    recommendations.append("Add navigation links to all dashboard views")
            elif result.startswith("⚠️"):
                if "Component Usage" in check:
                    recommendations.append("Increase adoption of shared components across dashboard")
                elif "Navigation" in check:
                    recommendations.append("Complete navigation links implementation")
        
        if not recommendations:
            recommendations.append("Dashboard layout system is well implemented - consider performance optimization")
        
        return recommendations


def main():
    """Main validation function"""
    print("🎨 DASHBOARD LAYOUT SYSTEM VALIDATION")
    print("=" * 50)
    
    validator = DashboardLayoutValidator()
    report = validator.generate_validation_report()
    
    # Print summary
    print(f"📊 Total Checks: {report['dashboard_layout_system']['total_checks']}")
    print(f"✅ Successful: {report['dashboard_layout_system']['successful']}")
    print(f"⚠️ Warnings: {report['dashboard_layout_system']['warnings']}")
    print(f"❌ Errors: {report['dashboard_layout_system']['errors']}")
    print(f"📈 Score: {report['dashboard_layout_system']['score_percentage']}%")
    print(f"🎯 Status: {report['overall_status']}")
    print()
    
    # Print detailed results
    print("📋 DETAILED VALIDATION RESULTS:")
    for check, result in report['dashboard_layout_system']['details'].items():
        print(f"  {check}: {result}")
    print()
    
    # Print recommendations
    if report['recommendations']:
        print("💡 RECOMMENDATIONS:")
        for rec in report['recommendations']:
            print(f"  • {rec}")
    
    # Save report
    report_path = "hackathon/dashboard_layout_validation.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Full report saved to: {report_path}")
    
    # Return success/failure
    return report['dashboard_layout_system']['score_percentage'] >= 75


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)