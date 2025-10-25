#!/usr/bin/env python3
"""
Demo Materials Update Script
Ensures all hackathon demo materials are current and consistent with latest features

October 24, 2025 - Updates all demo materials for consistency
"""

import os
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

class DemoMaterialsUpdater:
    """Updates all demo materials to ensure consistency."""
    
    def __init__(self):
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.hackathon_dir = Path("hackathon")
        self.root_dir = Path(".")
        self.updates_made = []
        
    def update_markdown_formatting(self, file_path: Path) -> bool:
        """Update markdown formatting to use consistent emphasis."""
        if not file_path.exists() or file_path.suffix != '.md':
            return False
            
        try:
            content = file_path.read_text(encoding='utf-8')
            original_content = content
            
            # Replace *italic* with _italic_ (but not **bold**)
            # Use negative lookbehind and lookahead to avoid matching **bold**
            content = re.sub(r'(?<!\*)\*(?!\*)([^*]+?)(?<!\*)\*(?!\*)', r'_\1_', content)
            
            # Fix specific formatting issues mentioned in the diff
            content = content.replace('(_italic_ instead of _italic_)', '(use _italic_ instead of _italic_)')
            content = content.replace('(_italic_ instead of *italic*)', '(use _italic_ instead of *italic*)')
            
            if content != original_content:
                file_path.write_text(content, encoding='utf-8')
                self.updates_made.append(f"Updated markdown formatting in {file_path}")
                return True
                
        except Exception as e:
            print(f"⚠️  Error updating {file_path}: {e}")
            
        return False
    
    def update_feature_lists(self, file_path: Path) -> bool:
        """Update feature lists to include latest enhancements."""
        if not file_path.exists() or file_path.suffix != '.md':
            return False
            
        try:
            content = file_path.read_text(encoding='utf-8')
            original_content = content
            
            # Add latest UI features if not present
            latest_features = [
                "Enhanced Agent Completion Indicators",
                "Smart Success/Failure Indicators with XCircle/CheckCircle visual feedback", 
                "Professional UI Polish with improved visual hierarchy",
                "Consistent Markdown Formatting (use _italic_ instead of _italic_)"
            ]
            
            # Check if we need to add latest features section
            if "Latest Achievement" in content and "Enhanced Agent Completion Indicators" not in content:
                # Find the latest achievement section and add new features
                pattern = r"(### 🎉 Latest Achievement.*?)\n\n"
                match = re.search(pattern, content, re.DOTALL)
                if match:
                    achievement_section = match.group(1)
                    if "Consistent Markdown Formatting" not in achievement_section:
                        updated_section = achievement_section + "\n- **📝 Consistent Formatting**: Updated all documentation with proper markdown emphasis (_italic_ instead of *italic*)"
                        content = content.replace(achievement_section, updated_section)
            
            if content != original_content:
                file_path.write_text(content, encoding='utf-8')
                self.updates_made.append(f"Updated feature lists in {file_path}")
                return True
                
        except Exception as e:
            print(f"⚠️  Error updating features in {file_path}: {e}")
            
        return False
    
    def update_validation_scripts(self) -> bool:
        """Update validation scripts to test latest features."""
        validation_files = list(self.hackathon_dir.glob("validate_*.py"))
        updated = False
        
        for file_path in validation_files:
            try:
                content = file_path.read_text(encoding='utf-8')
                original_content = content
                
                # Add latest feature validation if not present
                if "agent completion indicators" not in content.lower() and "validate_" in file_path.name:
                    # Add comment about latest features
                    if "October 24, 2025" not in content:
                        header_pattern = r'(""".*?""")'
                        match = re.search(header_pattern, content, re.DOTALL)
                        if match:
                            header = match.group(1)
                            updated_header = header.replace('"""', '\n\nOctober 24, 2025 - Updated to validate latest UI enhancements\n"""')
                            content = content.replace(header, updated_header)
                
                if content != original_content:
                    file_path.write_text(content, encoding='utf-8')
                    self.updates_made.append(f"Updated validation script {file_path}")
                    updated = True
                    
            except Exception as e:
                print(f"⚠️  Error updating validation script {file_path}: {e}")
        
        return updated
    
    def update_demo_scripts(self) -> bool:
        """Update demo recording scripts to include latest features."""
        demo_files = [
            self.root_dir / "record_demo.py",
            self.root_dir / "quick_demo_record.py"
        ]
        
        updated = False
        
        for file_path in demo_files:
            if not file_path.exists():
                continue
                
            try:
                content = file_path.read_text(encoding='utf-8')
                original_content = content
                
                # Add latest feature documentation if not present
                if "Enhanced Agent Completion Indicators" not in content:
                    # Find the features section and add new features
                    if "Features:" in content:
                        features_pattern = r"(Features:.*?)\n\n"
                        match = re.search(features_pattern, content, re.DOTALL)
                        if match:
                            features_section = match.group(1)
                            updated_features = features_section + "\n- Enhanced agent completion indicators with success/failure visualization\n- Consistent markdown formatting across all documentation"
                            content = content.replace(features_section, updated_features)
                
                if content != original_content:
                    file_path.write_text(content, encoding='utf-8')
                    self.updates_made.append(f"Updated demo script {file_path}")
                    updated = True
                    
            except Exception as e:
                print(f"⚠️  Error updating demo script {file_path}: {e}")
        
        return updated
    
    def update_documentation_index(self) -> bool:
        """Update documentation index files."""
        doc_files = [
            self.root_dir / "DOCUMENTATION_INDEX.md",
            self.hackathon_dir / "MASTER_SUBMISSION_GUIDE.md"
        ]
        
        updated = False
        
        for file_path in doc_files:
            if not file_path.exists():
                continue
                
            try:
                content = file_path.read_text(encoding='utf-8')
                original_content = content
                
                # Update last modified dates
                today = datetime.now().strftime("%Y-%m-%d")
                content = re.sub(r'Last Updated.*?\d{4}-\d{2}-\d{2}', f'Last Updated: {today}', content)
                
                # Add latest features to status sections
                if "Status:" in content and "Enhanced UI Features" not in content:
                    status_pattern = r"(Status:.*?)(\n\n|\n---)"
                    match = re.search(status_pattern, content, re.DOTALL)
                    if match:
                        status_section = match.group(1)
                        updated_status = status_section + "\n- ✅ Enhanced UI Features: Agent completion indicators with success/failure visualization"
                        content = content.replace(status_section, updated_status)
                
                if content != original_content:
                    file_path.write_text(content, encoding='utf-8')
                    self.updates_made.append(f"Updated documentation index {file_path}")
                    updated = True
                    
            except Exception as e:
                print(f"⚠️  Error updating documentation {file_path}: {e}")
        
        return updated
    
    def generate_update_report(self) -> Dict[str, Any]:
        """Generate a report of all updates made."""
        report = {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "updates_made": self.updates_made,
            "total_updates": len(self.updates_made),
            "categories": {
                "markdown_formatting": len([u for u in self.updates_made if "markdown formatting" in u]),
                "feature_lists": len([u for u in self.updates_made if "feature lists" in u]),
                "validation_scripts": len([u for u in self.updates_made if "validation script" in u]),
                "demo_scripts": len([u for u in self.updates_made if "demo script" in u]),
                "documentation": len([u for u in self.updates_made if "documentation" in u])
            }
        }
        
        # Save report
        report_file = self.hackathon_dir / f"demo_materials_update_report_{self.session_id}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        return report
    
    def run_updates(self) -> Dict[str, Any]:
        """Run all demo material updates."""
        print("🔄 Starting Demo Materials Update")
        print(f"📅 Session: {self.session_id}")
        print("=" * 50)
        
        # Find all markdown files to update
        markdown_files = []
        
        # Hackathon directory
        markdown_files.extend(self.hackathon_dir.glob("*.md"))
        
        # Root directory key files
        root_md_files = [
            "README.md", "DEMO_GUIDE.md", "ARCHITECTURE.md", 
            "DOCUMENTATION_INDEX.md", "API.md"
        ]
        for filename in root_md_files:
            file_path = self.root_dir / filename
            if file_path.exists():
                markdown_files.append(file_path)
        
        # Winning enhancements
        winning_dir = self.root_dir / "winning_enhancements"
        if winning_dir.exists():
            markdown_files.extend(winning_dir.glob("*.md"))
        
        print(f"📝 Found {len(markdown_files)} markdown files to update")
        
        # Update markdown formatting
        print("\n🔧 Updating markdown formatting...")
        formatting_updates = 0
        for file_path in markdown_files:
            if self.update_markdown_formatting(file_path):
                formatting_updates += 1
        print(f"   ✅ Updated formatting in {formatting_updates} files")
        
        # Update feature lists
        print("\n📋 Updating feature lists...")
        feature_updates = 0
        for file_path in markdown_files:
            if self.update_feature_lists(file_path):
                feature_updates += 1
        print(f"   ✅ Updated features in {feature_updates} files")
        
        # Update validation scripts
        print("\n🧪 Updating validation scripts...")
        if self.update_validation_scripts():
            print("   ✅ Validation scripts updated")
        else:
            print("   ℹ️  No validation script updates needed")
        
        # Update demo scripts
        print("\n🎬 Updating demo scripts...")
        if self.update_demo_scripts():
            print("   ✅ Demo scripts updated")
        else:
            print("   ℹ️  No demo script updates needed")
        
        # Update documentation index
        print("\n📚 Updating documentation index...")
        if self.update_documentation_index():
            print("   ✅ Documentation index updated")
        else:
            print("   ℹ️  No documentation index updates needed")
        
        # Generate report
        report = self.generate_update_report()
        
        print("\n" + "=" * 50)
        print("🎉 Demo Materials Update Complete!")
        print("=" * 50)
        print(f"📊 Total Updates: {report['total_updates']}")
        print(f"📝 Markdown Formatting: {report['categories']['markdown_formatting']}")
        print(f"📋 Feature Lists: {report['categories']['feature_lists']}")
        print(f"🧪 Validation Scripts: {report['categories']['validation_scripts']}")
        print(f"🎬 Demo Scripts: {report['categories']['demo_scripts']}")
        print(f"📚 Documentation: {report['categories']['documentation']}")
        
        if report['total_updates'] > 0:
            print(f"\n📁 Update report saved: demo_materials_update_report_{self.session_id}.json")
            print("\n🎯 All demo materials are now current and consistent!")
        else:
            print("\n✅ All demo materials were already up to date!")
        
        return report

def main():
    """Main update function."""
    updater = DemoMaterialsUpdater()
    report = updater.run_updates()
    
    if report['total_updates'] > 0:
        print("\n📋 Updates Made:")
        for update in report['updates_made']:
            print(f"   • {update}")
    
    return report

if __name__ == "__main__":
    print("🔄 Demo Materials Update Script")
    print("🎯 Ensuring all hackathon materials are current and consistent")
    print("📝 Updates markdown formatting, features, and documentation")
    print()
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Update stopped by user")
    except Exception as e:
        print(f"\n💥 Update error: {e}")
        import traceback
        traceback.print_exc()