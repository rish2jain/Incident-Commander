#!/usr/bin/env python3
"""
Quick Demo Recording Script for Judges
Simplified version for immediate hackathon evaluation.
"""

import asyncio
import sys
from record_demo import EnhancedDemoRecorder

async def quick_record():
    """Quick recording for judge evaluation."""
    print("🎬 Quick Demo Recording for Hackathon Judges")
    print("⚡ Optimized for immediate evaluation")
    print("=" * 50)
    
    recorder = EnhancedDemoRecorder()
    
    try:
        await recorder.setup_browser()
        results = await recorder.record_complete_demo()
        summary = await recorder.generate_comprehensive_summary()
        
        print("\n🎉 Quick Recording Complete!")
        print(f"📁 Check: {recorder.output_dir}")
        print("🏆 Ready for hackathon submission!")
        
        return True
        
    except Exception as e:
        print(f"❌ Quick recording failed: {e}")
        return False
    finally:
        await recorder.cleanup()

if __name__ == "__main__":
    try:
        success = asyncio.run(quick_record())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n👋 Quick recording stopped")
        sys.exit(0)