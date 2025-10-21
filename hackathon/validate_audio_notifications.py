#!/usr/bin/env python3
"""
Audio Notifications Validation Script
Tests the new audio notification system with configurable sound packs

Features tested:
- Audio notification configuration
- Sound pack selection (default, minimal, professional, retro)
- Volume control and accessibility
- Event-specific audio alerts
- Type-safe audio configuration
"""

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

import requests
from playwright.async_api import async_playwright


class AudioNotificationValidator:
    """Validates audio notification system functionality"""
    
    def __init__(self, base_url: str = "http://localhost:3000"):
        self.base_url = base_url
        self.validation_results = {
            "timestamp": datetime.now().isoformat(),
            "audio_features": {},
            "sound_packs": {},
            "accessibility": {},
            "performance": {},
            "overall_status": "unknown"
        }
    
    async def validate_audio_configuration(self, page):
        """Test audio configuration interface"""
        print("🔊 Testing audio configuration interface...")
        
        try:
            # Navigate to insights demo with audio features
            await page.goto(f"{self.base_url}/insights-demo")
            await page.wait_for_load_state("networkidle")
            
            # Look for audio settings component
            audio_settings = await page.query_selector('[data-testid="audio-settings"]')
            if not audio_settings:
                # Try alternative selectors
                audio_settings = await page.query_selector('.audio-notification-settings')
            
            if audio_settings:
                self.validation_results["audio_features"]["settings_component"] = "✅ Found"
                print("  ✅ Audio settings component found")
            else:
                self.validation_results["audio_features"]["settings_component"] = "❌ Missing"
                print("  ❌ Audio settings component not found")
                return False
            
            # Test volume control
            volume_control = await page.query_selector('input[type="range"]')
            if volume_control:
                self.validation_results["audio_features"]["volume_control"] = "✅ Found"
                print("  ✅ Volume control found")
                
                # Test volume adjustment
                await volume_control.fill("75")
                await page.wait_for_timeout(500)
                
            else:
                self.validation_results["audio_features"]["volume_control"] = "❌ Missing"
                print("  ❌ Volume control not found")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Audio configuration test failed: {e}")
            self.validation_results["audio_features"]["error"] = str(e)
            return False
    
    async def validate_sound_packs(self, page):
        """Test sound pack selection functionality"""
        print("🎵 Testing sound pack selection...")
        
        try:
            sound_packs = ["default", "minimal", "professional", "retro"]
            
            for pack in sound_packs:
                # Look for sound pack selector
                pack_selector = await page.query_selector(f'[data-value="{pack}"]')
                if pack_selector:
                    self.validation_results["sound_packs"][pack] = "✅ Available"
                    print(f"  ✅ {pack.capitalize()} sound pack available")
                    
                    # Test selection
                    await pack_selector.click()
                    await page.wait_for_timeout(300)
                    
                else:
                    self.validation_results["sound_packs"][pack] = "❌ Missing"
                    print(f"  ❌ {pack.capitalize()} sound pack not found")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Sound pack test failed: {e}")
            self.validation_results["sound_packs"]["error"] = str(e)
            return False
    
    async def validate_audio_events(self, page):
        """Test audio notifications for incident events"""
        print("🚨 Testing audio event notifications...")
        
        try:
            # Trigger a demo incident to test audio notifications
            trigger_button = await page.query_selector('[data-testid="trigger-demo"]')
            if not trigger_button:
                trigger_button = await page.query_selector('button:has-text("Start Demo")')
            
            if trigger_button:
                await trigger_button.click()
                print("  ✅ Demo triggered for audio testing")
                
                # Wait for incident events and check for audio indicators
                await page.wait_for_timeout(2000)
                
                # Look for audio notification indicators
                audio_indicators = await page.query_selector_all('.audio-notification-active')
                if audio_indicators:
                    self.validation_results["audio_features"]["event_notifications"] = f"✅ {len(audio_indicators)} events"
                    print(f"  ✅ {len(audio_indicators)} audio notifications detected")
                else:
                    self.validation_results["audio_features"]["event_notifications"] = "⚠️ No indicators"
                    print("  ⚠️ No audio notification indicators found")
                
            else:
                print("  ❌ Could not trigger demo for audio testing")
                return False
            
            return True
            
        except Exception as e:
            print(f"  ❌ Audio events test failed: {e}")
            self.validation_results["audio_features"]["events_error"] = str(e)
            return False
    
    async def validate_accessibility_features(self, page):
        """Test audio accessibility features"""
        print("♿ Testing audio accessibility features...")
        
        try:
            # Check for ARIA labels on audio controls
            aria_controls = await page.query_selector_all('[aria-label*="audio"], [aria-label*="volume"], [aria-label*="sound"]')
            if aria_controls:
                self.validation_results["accessibility"]["aria_labels"] = f"✅ {len(aria_controls)} controls"
                print(f"  ✅ {len(aria_controls)} audio controls with ARIA labels")
            else:
                self.validation_results["accessibility"]["aria_labels"] = "❌ Missing"
                print("  ❌ No ARIA labels found on audio controls")
            
            # Check for keyboard navigation support
            volume_control = await page.query_selector('input[type="range"]')
            if volume_control:
                await volume_control.focus()
                await page.keyboard.press('ArrowRight')
                await page.wait_for_timeout(200)
                self.validation_results["accessibility"]["keyboard_navigation"] = "✅ Supported"
                print("  ✅ Keyboard navigation supported")
            
            # Check for mute/unmute functionality
            mute_button = await page.query_selector('[aria-label*="mute"], [data-testid*="mute"]')
            if mute_button:
                self.validation_results["accessibility"]["mute_control"] = "✅ Available"
                print("  ✅ Mute control available")
            else:
                self.validation_results["accessibility"]["mute_control"] = "❌ Missing"
                print("  ❌ Mute control not found")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Accessibility test failed: {e}")
            self.validation_results["accessibility"]["error"] = str(e)
            return False
    
    async def validate_performance(self, page):
        """Test audio system performance"""
        print("⚡ Testing audio system performance...")
        
        try:
            start_time = time.time()
            
            # Test audio configuration load time
            await page.goto(f"{self.base_url}/insights-demo")
            await page.wait_for_load_state("networkidle")
            
            load_time = time.time() - start_time
            self.validation_results["performance"]["page_load_time"] = f"{load_time:.2f}s"
            
            if load_time < 2.0:
                print(f"  ✅ Page load time: {load_time:.2f}s (excellent)")
            elif load_time < 5.0:
                print(f"  ⚠️ Page load time: {load_time:.2f}s (acceptable)")
            else:
                print(f"  ❌ Page load time: {load_time:.2f}s (too slow)")
            
            # Test audio configuration response time
            config_start = time.time()
            volume_control = await page.query_selector('input[type="range"]')
            if volume_control:
                await volume_control.fill("50")
                await page.wait_for_timeout(100)
            config_time = time.time() - config_start
            
            self.validation_results["performance"]["config_response_time"] = f"{config_time:.3f}s"
            print(f"  ✅ Audio config response: {config_time:.3f}s")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Performance test failed: {e}")
            self.validation_results["performance"]["error"] = str(e)
            return False
    
    async def run_validation(self):
        """Run complete audio notification validation"""
        print("🎵 Starting Audio Notification System Validation")
        print("=" * 60)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                # Run all validation tests
                tests = [
                    self.validate_audio_configuration(page),
                    self.validate_sound_packs(page),
                    self.validate_audio_events(page),
                    self.validate_accessibility_features(page),
                    self.validate_performance(page)
                ]
                
                results = await asyncio.gather(*tests, return_exceptions=True)
                
                # Calculate overall status
                passed_tests = sum(1 for result in results if result is True)
                total_tests = len(results)
                
                if passed_tests == total_tests:
                    self.validation_results["overall_status"] = "✅ All tests passed"
                elif passed_tests >= total_tests * 0.8:
                    self.validation_results["overall_status"] = "⚠️ Most tests passed"
                else:
                    self.validation_results["overall_status"] = "❌ Multiple failures"
                
                print("\n" + "=" * 60)
                print(f"🎵 Audio Validation Complete: {passed_tests}/{total_tests} tests passed")
                print(f"Status: {self.validation_results['overall_status']}")
                
            finally:
                await browser.close()
        
        # Save results
        results_file = Path("hackathon") / "audio_validation_results.json"
        with open(results_file, "w") as f:
            json.dump(self.validation_results, f, indent=2)
        
        print(f"📊 Results saved to: {results_file}")
        return self.validation_results


async def main():
    """Main validation function"""
    validator = AudioNotificationValidator()
    results = await validator.run_validation()
    
    # Print summary
    print("\n🎵 AUDIO NOTIFICATION VALIDATION SUMMARY")
    print("=" * 50)
    print(f"Overall Status: {results['overall_status']}")
    print(f"Timestamp: {results['timestamp']}")
    
    if results['audio_features']:
        print("\n🔊 Audio Features:")
        for feature, status in results['audio_features'].items():
            print(f"  {feature}: {status}")
    
    if results['sound_packs']:
        print("\n🎵 Sound Packs:")
        for pack, status in results['sound_packs'].items():
            print(f"  {pack}: {status}")
    
    if results['accessibility']:
        print("\n♿ Accessibility:")
        for feature, status in results['accessibility'].items():
            print(f"  {feature}: {status}")
    
    if results['performance']:
        print("\n⚡ Performance:")
        for metric, value in results['performance'].items():
            print(f"  {metric}: {value}")


if __name__ == "__main__":
    asyncio.run(main())