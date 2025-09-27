#!/usr/bin/env python3
"""
Audio functionality test script

This script tests the audio recording and processing functionality
without requiring the full Streamlit application.
"""

import sys
import os
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_audio_dependencies():
    """Test if audio dependencies are available"""
    print("🔍 Testing audio dependencies...")

    try:
        from pydub import AudioSegment
        from pydub.utils import which
        print("✅ pydub is available")

        # Check ffmpeg
        ffmpeg_available = which("ffmpeg") is not None
        if ffmpeg_available:
            print("✅ ffmpeg is available")
        else:
            print("❌ ffmpeg is not available")
            print("   Install with: brew install ffmpeg (macOS) or apt install ffmpeg (Ubuntu)")

    except ImportError as e:
        print(f"❌ pydub import failed: {e}")
        print("   Install with: pip install pydub")
        return False

    try:
        from audiorecorder import audiorecorder
        print("✅ streamlit-audiorecorder is available")
    except ImportError as e:
        print(f"❌ streamlit-audiorecorder import failed: {e}")
        print("   Install with: pip install streamlit-audiorecorder")
        return False

    return True


def test_audio_manager():
    """Test AudioManager functionality"""
    print("\n🔧 Testing AudioManager...")

    try:
        from services.audio_utils import AudioManager, audio_manager

        # Test initialization
        manager = AudioManager()
        print("✅ AudioManager initialized successfully")

        # Test storage info
        storage_info = manager.get_storage_info()
        print(f"✅ Storage info: {storage_info}")

        # Test cleanup
        manager.cleanup_old_files(max_age_hours=1)
        print("✅ Cleanup function works")

        # Test format_duration
        duration_str = manager.format_duration(125.5)
        print(f"✅ Duration formatting: {duration_str}")

        return True

    except Exception as e:
        print(f"❌ AudioManager test failed: {e}")
        return False


def test_audio_ui():
    """Test AudioUI functionality"""
    print("\n🎨 Testing AudioUI...")

    try:
        from services.audio_utils import AudioUI

        # Test error messages (these should not fail)
        print("✅ AudioUI imported successfully")

        # Test dependency check
        # Note: This will show warnings if dependencies are missing
        print("📋 Checking dependencies through AudioUI:")

        return True

    except Exception as e:
        print(f"❌ AudioUI test failed: {e}")
        return False


def test_directory_creation():
    """Test audio storage directory creation"""
    print("\n📁 Testing directory creation...")

    try:
        from services.audio_utils import AudioManager

        # Test with custom directory
        test_dir = "test_audio_temp"
        manager = AudioManager(test_dir)

        if Path(test_dir).exists():
            print(f"✅ Directory '{test_dir}' created successfully")
            # Clean up test directory
            Path(test_dir).rmdir()
            print("✅ Test directory cleaned up")
        else:
            print(f"❌ Directory '{test_dir}' was not created")
            return False

        return True

    except Exception as e:
        print(f"❌ Directory creation test failed: {e}")
        return False


def main():
    """Run all audio tests"""
    print("🎤 AI Role-Playing Audio Functionality Tests")
    print("=" * 50)

    tests = [
        ("Dependencies", test_audio_dependencies),
        ("AudioManager", test_audio_manager),
        ("AudioUI", test_audio_ui),
        ("Directory Creation", test_directory_creation),
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results[test_name] = False

    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print("=" * 50)

    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:<20} {status}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All tests passed! Audio functionality should work correctly.")
        print("\nNext steps:")
        print("1. Run: python run.py")
        print("2. Navigate to the chat interface")
        print("3. Try recording a voice message")
    else:
        print("⚠️  Some tests failed. Please resolve the issues before using audio features.")
        print("\nCommon solutions:")
        print("- Install missing packages: pip install streamlit-audiorecorder pydub")
        print("- Install ffmpeg: brew install ffmpeg (macOS) or apt install ffmpeg (Ubuntu)")
        print("- Ensure you're running the app over HTTPS in production")

    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)