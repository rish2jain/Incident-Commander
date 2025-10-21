#!/usr/bin/env python3
"""
Demo Recording System Validation
Ensures all components are ready for professional recording
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Tuple

def check_dependency(command: str, install_hint: str = "") -> Tuple[bool, str]:
    """Check if a system dependency is available"""
    try:
        # Special handling for screencapture (macOS built-in)
        if command == "screencapture":
            result = subprocess.run(["which", command], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return True, f"✅ {command} available (macOS built-in)"
            else:
                return False, f"❌ {command} not found. {install_hint}"
        else:
            # Try different version flags
            version_flags = ["--version", "-version", "-V"]
            for flag in version_flags:
                try:
                    result = subprocess.run([command, flag], 
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        return True, f"✅ {command} available"
                except (FileNotFoundError, subprocess.TimeoutExpired, subprocess.SubprocessError):
                    continue
            return False, f"❌ {command} not found. {install_hint}"
    except FileNotFoundError:
        return False, f"❌ {command} not found. {install_hint}"
    except subprocess.TimeoutExpired:
        return False, f"❌ {command} timed out. {install_hint}"
    except subprocess.SubprocessError as e:
        return False, f"❌ {command} error: {e}. {install_hint}"

def check_file_exists(file_path: Path, description: str) -> Tuple[bool, str]:
    """Check if a required file exists"""
    if file_path.exists():
        return True, f"✅ {description} exists"
    else:
        return False, f"❌ {description} missing: {file_path}"

def validate_recording_system() -> Dict[str, List[Tuple[bool, str]]]:
    """Validate all components of the recording system"""
    
    project_root = Path(__file__).parent.parent
    results = {
        "dependencies": [],
        "scripts": [],
        "directories": [],
        "documentation": []
    }
    
    # Check system dependencies
    dependencies = [
        ("ffmpeg", "Install with: brew install ffmpeg"),
        ("screencapture", "macOS built-in (requires macOS)"),
        ("python3", "Install Python 3.11+"),
        ("npm", "Install Node.js and npm")
    ]
    
    for dep, hint in dependencies:
        success, message = check_dependency(dep, hint)
        results["dependencies"].append((success, message))
    
    # Check recording scripts
    scripts = [
        (project_root / "scripts" / "create_demo_recording.py", "Demo recording script"),
        (project_root / "scripts" / "run_demo_recording.sh", "Recording shell script"),
        (project_root / "scripts" / "archive_old_documentation.py", "Archive script"),
        (project_root / "scripts" / "validate_recording_system.py", "Validation script")
    ]
    
    for script_path, description in scripts:
        success, message = check_file_exists(script_path, description)
        results["scripts"].append((success, message))
    
    # Check required directories
    directories = [
        (project_root / "scripts", "Scripts directory"),
        (project_root / "src", "Source code directory"),
        (project_root / "dashboard", "Dashboard directory"),
        (project_root / "archive", "Archive directory")
    ]
    
    for dir_path, description in directories:
        success, message = check_file_exists(dir_path, description)
        results["directories"].append((success, message))
    
    # Check documentation
    documentation = [
        (project_root / "DEMO_RECORDING_SYSTEM_READY.md", "Recording system documentation"),
        (project_root / "HACKATHON_DEMO_RECORDING_READY.md", "Hackathon recording guide"),
        (project_root / "DEMO_RECORDING_COMPLETE.md", "Recording completion status"),
        (project_root / "hackathon" / "README.md", "Hackathon README")
    ]
    
    for doc_path, description in documentation:
        success, message = check_file_exists(doc_path, description)
        results["documentation"].append((success, message))
    
    return results

def print_validation_results(results: Dict[str, List[Tuple[bool, str]]]) -> bool:
    """Print validation results and return overall success"""
    
    print("🎬 DEMO RECORDING SYSTEM VALIDATION")
    print("=" * 50)
    
    overall_success = True
    
    for category, checks in results.items():
        print(f"\n📋 {category.upper()}:")
        category_success = True
        
        for success, message in checks:
            print(f"   {message}")
            if not success:
                category_success = False
                overall_success = False
        
        if category_success:
            print(f"   ✅ All {category} validated")
        else:
            print(f"   ❌ Some {category} issues found")
    
    print("\n" + "=" * 50)
    
    if overall_success:
        print("✅ RECORDING SYSTEM READY FOR PRODUCTION")
        print("🎬 Execute: cd scripts && ./run_demo_recording.sh")
        print("📦 Professional HD demo package will be generated")
        print("🏆 Ready for immediate hackathon submission")
    else:
        print("❌ RECORDING SYSTEM NEEDS ATTENTION")
        print("🔧 Please resolve the issues above before recording")
        print("📋 Run validation again after fixes")
    
    return overall_success

def main():
    """Main validation execution"""
    try:
        print("🔍 Validating demo recording system...")
        results = validate_recording_system()
        success = print_validation_results(results)
        
        if success:
            print("\n🚀 NEXT STEPS:")
            print("1. Execute: cd scripts && ./run_demo_recording.sh")
            print("2. Position browser windows when prompted")
            print("3. Professional HD recording will be generated")
            print("4. Complete package ready for DevPost submission")
            return 0
        else:
            print("\n🔧 REQUIRED ACTIONS:")
            print("1. Install missing dependencies")
            print("2. Ensure all scripts are executable")
            print("3. Run validation again")
            print("4. Execute recording when all checks pass")
            return 1
            
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())