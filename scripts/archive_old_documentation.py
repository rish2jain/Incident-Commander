#!/usr/bin/env python3
"""
Documentation Archive System
Organizes old status reports and summaries to prevent clutter
"""

import os
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

def archive_old_documentation():
    """Archive old documentation files to maintain clean project structure"""
    
    project_root = Path(__file__).parent.parent
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_dir = project_root / "archive" / f"documentation_{timestamp}"
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    # Import canonical file list
    from archive_config import FILES_TO_ARCHIVE
    files_to_archive = FILES_TO_ARCHIVE
    
    archived_files = []
    failed_files = []
    for filename in files_to_archive:
        source_path = project_root / filename
        if source_path.exists():
            dest_path = archive_dir / filename
            try:
                shutil.move(str(source_path), str(dest_path))
                archived_files.append(filename)
                print(f"✅ Archived: {filename}")
            except Exception as e:
                failed_files.append(filename)
                print(f"❌ Failed to archive {filename}: {e}")
                continue
    
    # Create archive index
    archive_index = {
        "archive_session": {
            "timestamp": timestamp,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "files_archived": len(archived_files),
            "reason": "Demo recording preparation and documentation cleanup"
        },
        "archived_files": archived_files,
        "archive_location": str(archive_dir.relative_to(project_root)),
        "notes": [
            "Files archived to maintain clean project structure",
            "Old status reports and update summaries moved to archive",
            "Current documentation remains in project root",
            "Archive preserves complete project history"
        ]
    }
    
    # Save archive index
    with open(archive_dir / "archive_index.json", "w") as f:
        json.dump(archive_index, f, indent=2)
    
    # Create archive README
    archive_readme = f"""# Documentation Archive - {timestamp}

## Archive Summary

- **Date**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- **Files Archived**: {len(archived_files)}
- **Reason**: Demo recording preparation and documentation cleanup

## Archived Files

{chr(10).join(f"- {filename}" for filename in archived_files)}

## Notes

- Files archived to maintain clean project structure
- Old status reports and update summaries moved to archive
- Current documentation remains in project root
- Archive preserves complete project history

## Restoration

To restore any archived file:

```bash
cp archive/documentation_{timestamp}/[filename] ./
```

---

**Archive created during demo recording system preparation**
"""
    
    with open(archive_dir / "README.md", "w") as f:
        f.write(archive_readme)
    
    print(f"\n📁 Archive created: {archive_dir}")
    print(f"📄 Files archived: {len(archived_files)}")
    if failed_files:
        print(f"❌ Files failed: {len(failed_files)} - {', '.join(failed_files)}")
    print(f"📋 Archive index: archive_index.json")
    print(f"📖 Archive README: README.md")
    
    return archive_dir, archived_files

if __name__ == "__main__":
    archive_dir, archived_files = archive_old_documentation()
    print(f"\n✅ Documentation archival complete!")
    print(f"📁 Location: {archive_dir}")
    print(f"📊 Files: {len(archived_files)} archived")