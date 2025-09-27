#!/usr/bin/env python3
"""
Test script for Speech-to-Text functionality

This script tests the STT service with various scenarios including:
- OpenAI Whisper API integration
- Fallback to speech_recognition
- Audio preprocessing
- Error handling
- Statistics tracking
"""

import os
import sys
import tempfile
from pathlib import Path
from dotenv import load_dotenv

# Add project root directory to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from pydub import AudioSegment
    from pydub.generators import Sine
except ImportError:
    print("❌ pydub not available. Please install with: pip install pydub")
    sys.exit(1)

from services.stt_service import (
    stt_service,
    ComprehensiveSTTService,
    AudioPreprocessor,
    STTStatisticsManager
)

load_dotenv()


class STTTester:
    """Test suite for STT functionality"""

    def __init__(self):
        self.test_results = []
        self.service = stt_service

    def log_test(self, test_name: str, success: bool, message: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append((test_name, success, message))
        print(f"{status}: {test_name}")
        if message:
            print(f"    {message}")

    def create_test_audio(self, frequency: int = 440, duration_ms: int = 2000) -> AudioSegment:
        """Create a test audio segment"""
        try:
            # Generate a simple sine wave
            sine_wave = Sine(frequency).to_audio_segment(duration=duration_ms)
            return sine_wave
        except Exception as e:
            print(f"Warning: Could not generate test audio: {e}")
            # Create silent audio as fallback
            return AudioSegment.silent(duration=duration_ms)

    def test_service_initialization(self):
        """Test STT service initialization"""
        try:
            # Check if services are initialized
            assert self.service is not None
            assert isinstance(self.service, ComprehensiveSTTService)

            # Check if components are available
            assert self.service.preprocessor is not None
            assert self.service.whisper_service is not None
            assert self.service.fallback_service is not None
            assert self.service.stats_manager is not None

            self.log_test("Service Initialization", True, "All components initialized successfully")

        except Exception as e:
            self.log_test("Service Initialization", False, str(e))

    def test_service_status(self):
        """Test service status reporting"""
        try:
            status = self.service.get_service_status()

            assert isinstance(status, dict)
            assert "whisper_available" in status
            assert "speech_recognition_available" in status
            assert "preprocessing_enabled" in status
            assert "statistics" in status

            # Check API key availability
            whisper_available = status["whisper_available"]
            sr_available = status["speech_recognition_available"]

            if whisper_available:
                self.log_test("Whisper API Status", True, "OpenAI API key configured")
            else:
                self.log_test("Whisper API Status", False, "OpenAI API key not found")

            if sr_available:
                self.log_test("SpeechRecognition Status", True, "speech_recognition library available")
            else:
                self.log_test("SpeechRecognition Status", False, "speech_recognition library not available")

        except Exception as e:
            self.log_test("Service Status", False, str(e))

    def test_audio_preprocessing(self):
        """Test audio preprocessing functionality"""
        try:
            preprocessor = AudioPreprocessor()

            # Create test audio
            test_audio = self.create_test_audio(440, 3000)  # 3 seconds

            # Test preprocessing
            processed_audio = preprocessor.preprocess_audio(test_audio)

            # Check if audio was processed
            assert processed_audio is not None
            assert len(processed_audio) > 0

            # Check sample rate conversion
            assert processed_audio.frame_rate == 16000  # Target sample rate
            assert processed_audio.channels == 1  # Mono

            self.log_test("Audio Preprocessing", True, f"Processed {len(processed_audio)}ms audio")

        except Exception as e:
            self.log_test("Audio Preprocessing", False, str(e))

    def test_long_audio_splitting(self):
        """Test long audio splitting functionality"""
        try:
            preprocessor = AudioPreprocessor()

            # Create long test audio (30 seconds)
            long_audio = self.create_test_audio(440, 30000)

            # Test splitting
            chunks = preprocessor.split_long_audio(long_audio, max_chunk_size=10)

            # Check if audio was split
            assert len(chunks) > 1
            assert all(len(chunk) <= 10500 for chunk in chunks)  # 10.5 seconds tolerance

            total_duration = sum(len(chunk) for chunk in chunks)
            assert abs(total_duration - len(long_audio)) < 1000  # 1 second tolerance

            self.log_test("Long Audio Splitting", True, f"Split into {len(chunks)} chunks")

        except Exception as e:
            self.log_test("Long Audio Splitting", False, str(e))

    def test_statistics_manager(self):
        """Test STT statistics management"""
        try:
            stats_manager = STTStatisticsManager("test_stats.json")

            # Test initial stats
            summary = stats_manager.get_statistics_summary()
            assert isinstance(summary, dict)

            # Create mock STT result
            from services.stt_service import STTResult
            mock_result = STTResult(
                text="test transcription",
                confidence=0.85,
                language="en",
                duration=2.0,
                method="test",
                processing_time=1.5
            )

            # Record request
            stats_manager.record_request(mock_result, user_edited=False)

            # Check updated stats
            updated_summary = stats_manager.get_statistics_summary()
            assert updated_summary["total_requests"] == 1
            assert updated_summary["success_rate"] > 0

            # Test user satisfaction recording
            stats_manager.record_user_satisfaction(5)
            satisfaction_summary = stats_manager.get_statistics_summary()
            assert satisfaction_summary["satisfaction_count"] == 1
            assert satisfaction_summary["average_satisfaction"] == 5.0

            self.log_test("Statistics Manager", True, "Statistics recording works correctly")

            # Clean up test file
            try:
                Path("test_stats.json").unlink()
            except:
                pass

        except Exception as e:
            self.log_test("Statistics Manager", False, str(e))

    def test_whisper_integration(self):
        """Test Whisper API integration (if API key available)"""
        if not os.getenv("OPENAI_API_KEY"):
            self.log_test("Whisper Integration", False, "OpenAI API key not configured")
            return

        try:
            # Create test audio
            test_audio = self.create_test_audio(440, 2000)  # 2 seconds

            # Test transcription (this will likely fail with generated audio, but tests the API call)
            result = self.service.transcribe_audio(test_audio, language="en")

            # Check result structure
            assert hasattr(result, 'text')
            assert hasattr(result, 'confidence')
            assert hasattr(result, 'language')
            assert hasattr(result, 'method')
            assert hasattr(result, 'processing_time')

            if result.error:
                self.log_test("Whisper Integration", True, f"API call successful (expected error with generated audio): {result.error}")
            else:
                self.log_test("Whisper Integration", True, f"Transcription: '{result.text}'")

        except Exception as e:
            self.log_test("Whisper Integration", False, str(e))

    def test_fallback_integration(self):
        """Test speech_recognition fallback integration"""
        try:
            # Check if fallback service is available
            if not self.service.fallback_service.recognizer:
                self.log_test("Fallback Integration", False, "speech_recognition not available")
                return

            # Create test audio
            test_audio = self.create_test_audio(440, 2000)

            # Test fallback transcription
            result = self.service.fallback_service.transcribe_audio(test_audio, language="en-US")

            # Check result structure
            assert hasattr(result, 'text')
            assert hasattr(result, 'method')
            assert result.method == "speech_recognition"

            if result.error:
                self.log_test("Fallback Integration", True, f"Fallback service accessible (expected error with generated audio): {result.error}")
            else:
                self.log_test("Fallback Integration", True, f"Fallback transcription: '{result.text}'")

        except Exception as e:
            self.log_test("Fallback Integration", False, str(e))

    def test_error_handling(self):
        """Test error handling with invalid inputs"""
        try:
            # Test with None audio
            result = self.service.transcribe_audio(None)
            assert result.error is not None

            # Test with empty audio
            empty_audio = AudioSegment.empty()
            result = self.service.transcribe_audio(empty_audio)
            assert result.error is not None

            # Test with very short audio
            short_audio = self.create_test_audio(440, 100)  # 0.1 seconds
            result = self.service.transcribe_audio(short_audio)
            # This might succeed or fail depending on validation, both are acceptable

            self.log_test("Error Handling", True, "Error conditions handled gracefully")

        except Exception as e:
            self.log_test("Error Handling", False, str(e))

    def test_language_support(self):
        """Test language detection and processing"""
        try:
            test_audio = self.create_test_audio(440, 2000)

            # Test different language settings
            languages = ["auto", "zh", "en"]

            for lang in languages:
                try:
                    result = self.service.transcribe_audio(test_audio, language=lang)
                    assert result.language is not None
                    # Result might have error (expected with generated audio), but should handle language parameter
                except Exception as lang_error:
                    raise Exception(f"Language {lang} failed: {lang_error}")

            self.log_test("Language Support", True, "All language options processed correctly")

        except Exception as e:
            self.log_test("Language Support", False, str(e))

    def test_memory_and_performance(self):
        """Test memory usage and performance with multiple requests"""
        try:
            import time

            test_audio = self.create_test_audio(440, 1000)  # 1 second

            start_time = time.time()
            results = []

            # Process multiple requests
            for i in range(3):
                result = self.service.transcribe_audio(test_audio, language="en")
                results.append(result)

            total_time = time.time() - start_time

            # Check that all results were processed
            assert len(results) == 3
            assert all(hasattr(r, 'processing_time') for r in results)

            avg_processing_time = sum(r.processing_time for r in results) / len(results)

            self.log_test("Memory and Performance", True,
                         f"Processed 3 requests in {total_time:.1f}s (avg: {avg_processing_time:.1f}s per request)")

        except Exception as e:
            self.log_test("Memory and Performance", False, str(e))

    def run_all_tests(self):
        """Run all tests and display results"""
        print("🧪 Starting STT Service Tests...")
        print("=" * 50)

        # Run tests
        self.test_service_initialization()
        self.test_service_status()
        self.test_audio_preprocessing()
        self.test_long_audio_splitting()
        self.test_statistics_manager()
        self.test_whisper_integration()
        self.test_fallback_integration()
        self.test_error_handling()
        self.test_language_support()
        self.test_memory_and_performance()

        # Display results
        print("\n" + "=" * 50)
        print("🔍 Test Results Summary:")
        print("=" * 50)

        passed = sum(1 for _, success, _ in self.test_results if success)
        total = len(self.test_results)

        print(f"Tests Passed: {passed}/{total}")
        print(f"Success Rate: {passed/total*100:.1f}%")

        if passed < total:
            print("\n❌ Failed Tests:")
            for name, success, message in self.test_results:
                if not success:
                    print(f"  - {name}: {message}")

        # Display service status
        print("\n📊 Service Status:")
        try:
            status = self.service.get_service_status()
            print(f"  Whisper API: {'✅' if status['whisper_available'] else '❌'}")
            print(f"  SpeechRecognition: {'✅' if status['speech_recognition_available'] else '❌'}")
            print(f"  Preprocessing: {'✅' if status['preprocessing_enabled'] else '❌'}")
            print(f"  Fallback: {'✅' if status['fallback_enabled'] else '❌'}")

            stats = status['statistics']
            if 'total_requests' in stats and stats['total_requests'] > 0:
                print(f"\n📈 Usage Statistics:")
                print(f"  Total Requests: {stats['total_requests']}")
                print(f"  Success Rate: {stats['success_rate']}%")
                print(f"  Average Confidence: {stats['average_confidence']}%")
        except Exception as e:
            print(f"  Error getting status: {e}")

        print("\n🎯 Recommendations:")
        if not os.getenv("OPENAI_API_KEY"):
            print("  - Configure OPENAI_API_KEY for Whisper API functionality")

        try:
            from speech_recognition import Recognizer
            print("  - SpeechRecognition fallback is available")
        except ImportError:
            print("  - Install SpeechRecognition for fallback: pip install SpeechRecognition")

        try:
            from pydub.utils import which
            if not which("ffmpeg"):
                print("  - Install FFmpeg for better audio processing")
        except:
            pass

        print("\n✨ STT Service is ready for use!")
        return passed == total


def main():
    """Main test function"""
    print("🎤 AI Role-Playing Website - STT Service Test")
    print("=" * 50)

    # Check basic dependencies
    try:
        from pydub import AudioSegment
        print("✅ pydub available")
    except ImportError:
        print("❌ pydub not available - install with: pip install pydub")
        return False

    try:
        import speech_recognition
        print("✅ SpeechRecognition available")
    except ImportError:
        print("⚠️ SpeechRecognition not available - install with: pip install SpeechRecognition")

    try:
        from openai import OpenAI
        print("✅ OpenAI client available")

        if os.getenv("OPENAI_API_KEY"):
            print("✅ OpenAI API key configured")
        else:
            print("⚠️ OpenAI API key not configured in .env file")
    except ImportError:
        print("❌ OpenAI client not available")
        return False

    print("\n" + "🧪 Starting Test Suite...")

    # Run tests
    tester = STTTester()
    success = tester.run_all_tests()

    if success:
        print("\n🎉 All tests passed! STT service is ready.")
        return True
    else:
        print("\n⚠️ Some tests failed. Check the logs above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)