#!/usr/bin/env python3
"""
AWS Integration Status Validation Script

Validates that all documentation accurately reflects the current AWS AI service integration status:
- 2/8 services production-ready (Bedrock AgentCore + Claude 3.5 Sonnet)
- 6/8 services planned for Q4 2025
- No misleading claims about complete integration
- Honest implementation roadmap
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Any
from datetime import datetime


class AWSIntegrationValidator:
    """Validates AWS integration status across all documentation"""
    
    def __init__(self):
        self.validation_results = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "PENDING",
            "files_checked": 0,
            "issues_found": 0,
            "validations": []
        }
        
        # Expected status for each service
        self.expected_status = {
            "Amazon Bedrock AgentCore": "PRODUCTION",
            "Claude 3.5 Sonnet": "PRODUCTION", 
            "Claude 3 Haiku": "PLANNED",
            "Amazon Titan Embeddings": "PLANNED",
            "Amazon Q Business": "PLANNED",
            "Nova Act": "PLANNED",
            "Strands SDK": "PLANNED",
            "Bedrock Guardrails": "PLANNED"
        }
        
        # Files to check
        self.files_to_check = [
            "hackathon/README.md",
            "hackathon/HACKATHON_ARCHITECTURE.md",
            "hackathon/MASTER_SUBMISSION_GUIDE.md",
            "hackathon/COMPREHENSIVE_JUDGE_GUIDE.md",
            "DEMO_GUIDE.md",
            "README.md"
        ]
        
        # Patterns that indicate misleading claims
        self.misleading_patterns = [
            r"8/8 services.*(?:active|operational|integrated|complete)",
            r"complete AWS AI.*integration",
            r"all 8.*services.*working",
            r"✅.*8/8",
            r"fully integrated.*8 services"
        ]
        
        # Patterns that indicate honest status
        self.honest_patterns = [
            r"2/8.*production",
            r"6/8.*planned",
            r"partial.*integration",
            r"Q4 2025.*roadmap"
        ]

    def validate_file(self, file_path: Path) -> Dict[str, Any]:
        """Validate a single file for honest AWS integration status"""
        
        if not file_path.exists():
            return {
                "file": str(file_path),
                "status": "SKIPPED",
                "reason": "File not found",
                "issues": [],
                "honest_indicators": []
            }
        
        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception as e:
            return {
                "file": str(file_path),
                "status": "ERROR",
                "reason": f"Failed to read file: {e}",
                "issues": [],
                "honest_indicators": []
            }
        
        issues = []
        honest_indicators = []
        
        # Check for misleading patterns
        for pattern in self.misleading_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                issues.append({
                    "type": "MISLEADING_CLAIM",
                    "line": line_num,
                    "text": match.group(),
                    "pattern": pattern
                })
        
        # Check for honest indicators
        for pattern in self.honest_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                honest_indicators.append({
                    "type": "HONEST_STATUS",
                    "line": line_num,
                    "text": match.group(),
                    "pattern": pattern
                })
        
        # Check for service-specific status
        service_status = {}
        for service, expected in self.expected_status.items():
            # Look for service mentions with status indicators
            service_pattern = rf"{re.escape(service)}.*?(?:✅|🎯|PRODUCTION|PLANNED|ACTIVE)"
            matches = re.finditer(service_pattern, content, re.IGNORECASE | re.DOTALL)
            
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                text = match.group()
                
                if expected == "PRODUCTION":
                    if "✅" in text or "PRODUCTION" in text.upper():
                        service_status[service] = "CORRECT"
                    else:
                        issues.append({
                            "type": "INCORRECT_SERVICE_STATUS",
                            "service": service,
                            "line": line_num,
                            "expected": "PRODUCTION",
                            "found": text
                        })
                else:  # PLANNED
                    if "🎯" in text or "PLANNED" in text.upper():
                        service_status[service] = "CORRECT"
                    elif "✅" in text or "PRODUCTION" in text.upper():
                        issues.append({
                            "type": "INCORRECT_SERVICE_STATUS", 
                            "service": service,
                            "line": line_num,
                            "expected": "PLANNED",
                            "found": text
                        })
        
        status = "PASS" if len(issues) == 0 else "FAIL"
        
        return {
            "file": str(file_path),
            "status": status,
            "issues_count": len(issues),
            "honest_indicators_count": len(honest_indicators),
            "issues": issues,
            "honest_indicators": honest_indicators,
            "service_status": service_status
        }

    def run_validation(self) -> Dict[str, Any]:
        """Run validation across all files"""
        
        print("🔍 Validating AWS Integration Status Documentation...")
        print("=" * 60)
        
        for file_path_str in self.files_to_check:
            file_path = Path(file_path_str)
            print(f"\n📄 Checking {file_path}...")
            
            result = self.validate_file(file_path)
            self.validation_results["validations"].append(result)
            self.validation_results["files_checked"] += 1
            
            if result["status"] == "PASS":
                print(f"   ✅ PASS - {result['honest_indicators_count']} honest indicators found")
            elif result["status"] == "FAIL":
                print(f"   ❌ FAIL - {result['issues_count']} issues found")
                self.validation_results["issues_found"] += result["issues_count"]
                
                # Show first few issues
                for issue in result["issues"][:3]:
                    if issue["type"] == "MISLEADING_CLAIM":
                        print(f"      • Line {issue['line']}: Misleading claim - '{issue['text'][:50]}...'")
                    elif issue["type"] == "INCORRECT_SERVICE_STATUS":
                        print(f"      • Line {issue['line']}: {issue['service']} should be {issue['expected']}")
                
                if len(result["issues"]) > 3:
                    print(f"      • ... and {len(result['issues']) - 3} more issues")
            else:
                print(f"   ⚠️  {result['status']} - {result.get('reason', 'Unknown')}")
        
        # Overall assessment
        if self.validation_results["issues_found"] == 0:
            self.validation_results["overall_status"] = "PASS"
            print(f"\n🎉 VALIDATION PASSED")
            print(f"   All {self.validation_results['files_checked']} files have honest AWS integration status")
        else:
            self.validation_results["overall_status"] = "FAIL"
            print(f"\n❌ VALIDATION FAILED")
            print(f"   Found {self.validation_results['issues_found']} issues across {self.validation_results['files_checked']} files")
        
        return self.validation_results

    def generate_report(self) -> None:
        """Generate detailed validation report"""
        
        report_file = Path("aws_integration_validation_report.json")
        
        with open(report_file, 'w') as f:
            json.dump(self.validation_results, f, indent=2)
        
        print(f"\n📊 Detailed report saved to: {report_file}")
        
        # Generate summary
        summary_file = Path("aws_integration_validation_summary.md")
        
        with open(summary_file, 'w') as f:
            f.write("# AWS Integration Status Validation Summary\n\n")
            f.write(f"**Validation Date**: {self.validation_results['timestamp']}\n")
            f.write(f"**Overall Status**: {self.validation_results['overall_status']}\n")
            f.write(f"**Files Checked**: {self.validation_results['files_checked']}\n")
            f.write(f"**Issues Found**: {self.validation_results['issues_found']}\n\n")
            
            f.write("## Expected AWS Service Status\n\n")
            f.write("**✅ Production-Ready (2/8)**:\n")
            f.write("- Amazon Bedrock AgentCore\n")
            f.write("- Claude 3.5 Sonnet\n\n")
            
            f.write("**🎯 Planned for Q4 2025 (6/8)**:\n")
            f.write("- Claude 3 Haiku\n")
            f.write("- Amazon Titan Embeddings\n")
            f.write("- Amazon Q Business\n")
            f.write("- Nova Act\n")
            f.write("- Strands SDK\n")
            f.write("- Bedrock Guardrails\n\n")
            
            if self.validation_results["issues_found"] > 0:
                f.write("## Issues Found\n\n")
                for validation in self.validation_results["validations"]:
                    if validation["status"] == "FAIL":
                        f.write(f"### {validation['file']}\n\n")
                        for issue in validation["issues"]:
                            f.write(f"- **Line {issue.get('line', 'N/A')}**: {issue['type']} - {issue.get('text', issue.get('service', 'Unknown'))}\n")
                        f.write("\n")
            
            f.write("## Recommendations\n\n")
            if self.validation_results["overall_status"] == "PASS":
                f.write("✅ All documentation accurately reflects current AWS integration status.\n")
            else:
                f.write("❌ Update documentation to reflect honest implementation status:\n")
                f.write("- Replace claims of '8/8 services' with '2/8 production-ready, 6/8 planned'\n")
                f.write("- Use 🎯 PLANNED status for services not yet implemented\n")
                f.write("- Include Q4 2025 timeline for planned services\n")
                f.write("- Maintain transparency about current capabilities\n")
        
        print(f"📋 Summary report saved to: {summary_file}")


def main():
    """Main validation function"""
    
    validator = AWSIntegrationValidator()
    results = validator.run_validation()
    validator.generate_report()
    
    # Exit with appropriate code
    if results["overall_status"] == "PASS":
        print("\n✅ AWS Integration Status Validation: PASSED")
        return 0
    else:
        print("\n❌ AWS Integration Status Validation: FAILED")
        return 1


if __name__ == "__main__":
    exit(main())