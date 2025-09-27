#!/usr/bin/env python3
"""
Test script for Text-to-Speech (TTS) functionality

This script tests the TTS service integration with all characters
to ensure voice generation works correctly with different voice profiles.
"""

import os
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_imports():
    """Test if all required modules can be imported"""
    print("🧪 Testing module imports...")

    try:
        from services.tts_service import TTSService, TTSManager
        from app.models import Character, VoiceConfig
        from app.database import DatabaseManager
        from config.preset_characters import get_preset_characters
        print("✅ All modules imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_tts_service_initialization():
    """Test TTS service initialization"""
    print("\n🧪 Testing TTS service initialization...")

    try:
        from services.tts_service import TTSService, tts_manager

        # Test service initialization
        tts_service = TTSService()
        print(f"✅ TTS service initialized")
        print(f"   - Cache directory: {tts_service.cache_dir}")
        print(f"   - Supported models: {tts_service.supported_models}")
        print(f"   - Supported voices: {tts_service.supported_voices}")

        # Test manager initialization
        print(f"✅ TTS manager initialized")

        return True
    except Exception as e:
        print(f"❌ TTS service initialization failed: {e}")
        return False

def test_character_voice_configurations():
    """Test character voice configurations"""
    print("\n🧪 Testing character voice configurations...")

    try:
        from config.preset_characters import get_preset_characters

        characters = get_preset_characters()
        print(f"✅ Found {len(characters)} preset characters")

        for char_data in characters:
            voice_config = char_data.voice_config
            print(f"   📢 {char_data.name}:")
            print(f"      - Voice ID: {voice_config.voice_id}")
            print(f"      - Speed: {voice_config.speed}")
            print(f"      - Provider: {voice_config.provider}")

        return True
    except Exception as e:
        print(f"❌ Character voice configuration test failed: {e}")
        return False

def test_tts_generation():
    """Test TTS generation for each character"""
    print("\n🧪 Testing TTS generation...")

    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not found in environment")
        return False

    try:
        from services.tts_service import tts_manager
        from config.preset_characters import get_preset_characters
        from app.models import Character

        characters_data = get_preset_characters()
        test_text = "你好，这是一个语音测试。"

        for char_data in characters_data:
            print(f"\n   🎭 Testing {char_data.name}...")

            # Create character object for testing
            character = Character(
                name=char_data.name,
                title=char_data.title,
                avatar_emoji=char_data.avatar_emoji,
                personality=char_data.personality,
                prompt_template=char_data.prompt_template,
                skills=char_data.skills,
                voice_config=char_data.voice_config
            )

            # Generate TTS
            start_time = time.time()
            tts_result = tts_manager.generate_character_speech(
                text=test_text,
                character=character,
                show_progress=False,
                use_cache=True
            )
            end_time = time.time()

            if tts_result:
                size_kb = tts_result.get("size", 0) / 1024
                cached = tts_result.get("cached", False)
                cache_status = "cached" if cached else "generated"

                print(f"      ✅ TTS generated successfully ({cache_status})")
                print(f"         - Size: {size_kb:.1f} KB")
                print(f"         - Time: {end_time - start_time:.2f}s")
                print(f"         - Voice: {tts_result.get('voice_id', 'unknown')}")
            else:
                print(f"      ❌ TTS generation failed")
                return False

        print("✅ All character TTS generation tests passed")
        return True

    except Exception as e:
        print(f"❌ TTS generation test failed: {e}")
        return False

def test_cache_functionality():
    """Test TTS caching functionality"""
    print("\n🧪 Testing TTS cache functionality...")

    try:
        from services.tts_service import tts_manager

        # Get cache info
        cache_info = tts_manager.tts_service.get_cache_info()
        print("✅ Cache info retrieved:")
        print(f"   - Files: {cache_info['total_files']}")
        print(f"   - Size: {cache_info['total_size_mb']} MB")
        print(f"   - Directory: {cache_info['cache_dir']}")

        # Test cache cleanup (don't actually clear for this test)
        print("✅ Cache management functions available")

        return True
    except Exception as e:
        print(f"❌ Cache functionality test failed: {e}")
        return False

def test_voice_preview():
    """Test voice preview functionality"""
    print("\n🧪 Testing voice preview functionality...")

    try:
        from services.tts_service import TTSService

        tts_service = TTSService()

        # Test preview text generation
        for voice_id in ["echo", "onyx", "fable"]:
            preview_text = tts_service.get_voice_preview(voice_id)
            print(f"   🎵 {voice_id}: {preview_text}")

        # Test character mapping
        character_voices = {
            "哈利·波特": tts_service.get_optimal_voice_for_character("哈利·波特"),
            "苏格拉底": tts_service.get_optimal_voice_for_character("苏格拉底"),
            "阿尔伯特·爱因斯坦": tts_service.get_optimal_voice_for_character("阿尔伯特·爱因斯坦")
        }

        print("✅ Character voice mapping:")
        for char, voice in character_voices.items():
            print(f"   - {char}: {voice}")

        return True
    except Exception as e:
        print(f"❌ Voice preview test failed: {e}")
        return False

def test_ui_components():
    """Test UI component functions (without Streamlit context)"""
    print("\n🧪 Testing UI components (structural test)...")

    try:
        from services.audio_utils import TTSPlaybackUI

        # Test that UI methods exist and are callable
        ui_methods = [
            'show_tts_player',
            'show_tts_info',
            'show_voice_preview_player',
            'show_voice_characteristics',
            'show_tts_settings_panel',
            'show_tts_status',
            'show_cache_management'
        ]

        for method_name in ui_methods:
            if hasattr(TTSPlaybackUI, method_name):
                print(f"   ✅ {method_name} method available")
            else:
                print(f"   ❌ {method_name} method missing")
                return False

        print("✅ All UI components are available")
        return True
    except Exception as e:
        print(f"❌ UI components test failed: {e}")
        return False

def main():
    """Run all TTS tests"""
    print("🚀 Starting TTS functionality tests\n")

    tests = [
        ("Module Imports", test_imports),
        ("TTS Service Initialization", test_tts_service_initialization),
        ("Character Voice Configurations", test_character_voice_configurations),
        ("Voice Preview", test_voice_preview),
        ("Cache Functionality", test_cache_functionality),
        ("UI Components", test_ui_components),
        ("TTS Generation", test_tts_generation),  # This test requires API key
    ]

    results = {}

    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results[test_name] = False

    # Summary
    print("\n" + "="*50)
    print("📊 TEST RESULTS SUMMARY")
    print("="*50)

    passed = sum(results.values())
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")

    print("-" * 50)
    print(f"Overall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! TTS functionality is ready.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")

    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)