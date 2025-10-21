#!/usr/bin/env python3
"""
Cleanup script to remove redundant dashboards and focus on AI Insights Dashboard
Keeps only the most innovative and differentiating dashboard for hackathon submission
"""

import os
import shutil
from pathlib import Path

def cleanup_dashboards():
    """Remove redundant dashboards and focus on AI Insights"""
    
    print("🧹 DASHBOARD CLEANUP - FOCUSING ON AI INSIGHTS")
    print("=" * 60)
    
    # Files to remove (redundant dashboards)
    files_to_remove = [
        "dashboard/app/simple-demo/page.tsx",  # React dashboard
        "dashboard/standalone.html",  # Standalone
    ]
    
    # Scripts to remove (redundant)
    scripts_to_remove = [
        "scripts/test_react_dashboard.py",
        "scripts/final_react_demo.py", 
        "scripts/test_autoscroll.py",
        "scripts/validate_autoscroll.py",
    ]
    
    removed_count = 0
    
    print("\n📁 Removing redundant dashboard files...")
    for file_path in files_to_remove:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"   ✅ Removed: {file_path}")
                removed_count += 1
            except Exception as e:
                print(f"   ⚠️ Could not remove {file_path}: {e}")
        else:
            print(f"   ℹ️ Not found: {file_path}")
    
    print("\n🔧 Removing redundant test scripts...")
    for script_path in scripts_to_remove:
        if os.path.exists(script_path):
            try:
                os.remove(script_path)
                print(f"   ✅ Removed: {script_path}")
                removed_count += 1
            except Exception as e:
                print(f"   ⚠️ Could not remove {script_path}: {e}")
        else:
            print(f"   ℹ️ Not found: {script_path}")
    
    print(f"\n📊 Cleanup Summary:")
    print(f"   Files removed: {removed_count}")
    print(f"   Remaining dashboard: AI Insights Dashboard")
    print(f"   Focus: Revolutionary AI transparency and explainability")
    
    print(f"\n✅ CLEANUP COMPLETE!")
    print(f"🎯 Now focused on single, powerful AI Insights Dashboard")
    print(f"🏆 Maximum impact for hackathon judges")
    
    return removed_count

def update_demo_recorder():
    """Update demo recorder to default to insights dashboard"""
    
    recorder_path = "scripts/automated_demo_recorder.py"
    
    if os.path.exists(recorder_path):
        print(f"\n🔧 Updating demo recorder default...")
        
        # Read current content
        with open(recorder_path, 'r') as f:
            content = f.read()
        
        # Update default dashboard type
        updated_content = content.replace(
            'dashboard_type = os.getenv("DASHBOARD_TYPE", "insights")',
            'dashboard_type = os.getenv("DASHBOARD_TYPE", "insights")  # Focused on AI transparency'
        )
        
        # Write updated content
        with open(recorder_path, 'w') as f:
            f.write(updated_content)
        
        print(f"   ✅ Demo recorder now defaults to AI Insights Dashboard")
    
def create_focused_readme():
    """Create a focused README for the streamlined setup"""
    
    readme_content = """# 🧠 AI Insights Dashboard - Focused Setup

## 🎯 Single Dashboard Focus

This setup is streamlined to showcase the **AI Insights & Transparency Dashboard** - the most innovative and differentiating feature for the hackathon.

## 🚀 Quick Start

### Start Services
```bash
# Terminal 1: Dashboard server
cd dashboard && npm run dev

# Terminal 2: Backend API  
python start_simple.py
```

### Record Demo
```bash
# AI Insights Dashboard (default)
python scripts/automated_demo_recorder.py

# Comprehensive insights demo
python scripts/record_insights_demo.py

# Test insights functionality
python scripts/test_insights_dashboard.py
```

### Demo URL
- **AI Insights Dashboard**: http://localhost:3000/insights-demo
- **Auto-demo**: http://localhost:3000/insights-demo?auto-demo=true

## 🏆 Why This Focus?

- **Revolutionary**: Industry-first AI transparency in incident response
- **Differentiating**: Unique explainable AI capabilities
- **Judge Appeal**: Educational and impressive demonstration
- **Competitive Advantage**: Sets new standard for responsible AI

## ✨ Key Features

- 🧠 Agent reasoning visualization
- 🌳 Interactive decision trees  
- 📈 Real-time confidence tracking
- 💬 Inter-agent communication matrix
- 📊 Bias detection and analytics

**Result**: Maximum impact with focused, world-class AI transparency! 🌟
"""
    
    with open("FOCUSED_SETUP.md", "w") as f:
        f.write(readme_content)
    
    print(f"   ✅ Created FOCUSED_SETUP.md guide")

if __name__ == "__main__":
    removed = cleanup_dashboards()
    update_demo_recorder()
    create_focused_readme()
    
    print(f"\n🎉 STREAMLINED FOR SUCCESS!")
    print(f"📈 Single powerful dashboard > Multiple mediocre ones")
    print(f"🏆 Ready for hackathon victory with AI transparency focus!")