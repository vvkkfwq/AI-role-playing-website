#!/usr/bin/env python3
"""
Speech-to-Text Service for AI Role-Playing Chat Application

This module provides comprehensive STT functionality including:
- OpenAI Whisper API integration
- Audio preprocessing and optimization
- Multi-language support (Chinese and English focus)
- Accuracy statistics and user feedback
- Fallback with speech_recognition library
- Real-time progress feedback
"""

import os
import io
import time
import tempfile
from typing import Optional, Dict, Any, Tuple, List
from pathlib import Path
import json
from datetime import datetime
from dataclasses import dataclass, asdict

try:
    from pydub import AudioSegment
    from pydub.effects import normalize, low_pass_filter, high_pass_filter
    from pydub.silence import split_on_silence
except ImportError:
    AudioSegment = None

try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False

import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


@dataclass
class STTResult:
    """Result of speech-to-text operation"""
    text: str
    confidence: float
    language: str
    duration: float
    method: str  # 'whisper' or 'speech_recognition'
    processing_time: float
    segments: Optional[List[Dict]] = None
    error: Optional[str] = None


@dataclass
class STTStats:
    """Statistics for STT accuracy and user feedback"""
    total_requests: int = 0
    successful_requests: int = 0
    average_confidence: float = 0.0
    user_corrections: int = 0
    user_satisfaction_ratings: List[int] = None
    common_errors: Dict[str, int] = None

    def __post_init__(self):
        if self.user_satisfaction_ratings is None:
            self.user_satisfaction_ratings = []
        if self.common_errors is None:
            self.common_errors = {}


class AudioPreprocessor:
    """Audio preprocessing utilities for better STT accuracy"""

    def __init__(self):
        self.target_sample_rate = 16000  # Whisper's preferred sample rate
        self.target_channels = 1  # Mono audio
        self.min_silence_len = 300  # ms
        self.silence_thresh = -40  # dB

    def preprocess_audio(self, audio_segment: AudioSegment) -> AudioSegment:
        """
        Preprocess audio for optimal STT results

        Args:
            audio_segment: Input audio segment

        Returns:
            Preprocessed audio segment
        """
        try:
            # Convert to mono
            if audio_segment.channels > 1:
                audio_segment = audio_segment.set_channels(1)

            # Set target sample rate
            if audio_segment.frame_rate != self.target_sample_rate:
                audio_segment = audio_segment.set_frame_rate(self.target_sample_rate)

            # Normalize audio levels
            audio_segment = normalize(audio_segment)

            # Apply noise reduction filters
            # High-pass filter to remove low-frequency noise
            audio_segment = high_pass_filter(audio_segment, cutoff=80)

            # Low-pass filter to remove high-frequency noise
            audio_segment = low_pass_filter(audio_segment, cutoff=8000)

            return audio_segment

        except Exception as e:
            st.warning(f"Audio preprocessing warning: {str(e)}")
            return audio_segment

    def split_long_audio(self, audio_segment: AudioSegment, max_chunk_size: int = 25) -> List[AudioSegment]:
        """
        Split long audio into smaller chunks for better processing

        Args:
            audio_segment: Input audio segment
            max_chunk_size: Maximum chunk size in seconds

        Returns:
            List of audio chunks
        """
        duration_seconds = len(audio_segment) / 1000.0

        if duration_seconds <= max_chunk_size:
            return [audio_segment]

        try:
            # Try to split on silence first
            chunks = split_on_silence(
                audio_segment,
                min_silence_len=self.min_silence_len,
                silence_thresh=self.silence_thresh,
                keep_silence=200  # Keep some silence for context
            )

            # If chunks are still too long, split by time
            final_chunks = []
            for chunk in chunks:
                if len(chunk) / 1000.0 > max_chunk_size:
                    # Split by time
                    chunk_duration_ms = max_chunk_size * 1000
                    for i in range(0, len(chunk), chunk_duration_ms):
                        final_chunks.append(chunk[i:i + chunk_duration_ms])
                else:
                    final_chunks.append(chunk)

            return final_chunks if final_chunks else [audio_segment]

        except Exception:
            # Fallback: split by time only
            chunk_duration_ms = max_chunk_size * 1000
            chunks = []
            for i in range(0, len(audio_segment), chunk_duration_ms):
                chunks.append(audio_segment[i:i + chunk_duration_ms])
            return chunks


class WhisperSTTService:
    """OpenAI Whisper API service for speech-to-text"""

    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "whisper-1"
        self.supported_languages = ["zh", "en", "auto"]
        self.max_file_size = 25 * 1024 * 1024  # 25MB limit for Whisper API

    async def transcribe_audio(
        self,
        audio_segment: AudioSegment,
        language: str = "auto",
        prompt: Optional[str] = None
    ) -> STTResult:
        """
        Transcribe audio using OpenAI Whisper API

        Args:
            audio_segment: Audio to transcribe
            language: Language code ('zh', 'en', 'auto')
            prompt: Optional context prompt for better accuracy

        Returns:
            STTResult object with transcription results
        """
        start_time = time.time()

        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                audio_segment.export(temp_file.name, format="wav")
                temp_file_path = temp_file.name

            # Check file size
            file_size = os.path.getsize(temp_file_path)
            if file_size > self.max_file_size:
                os.unlink(temp_file_path)
                return STTResult(
                    text="", confidence=0.0, language=language,
                    duration=len(audio_segment) / 1000.0, method="whisper",
                    processing_time=time.time() - start_time,
                    error="音频文件过大，请分段录制"
                )

            # Prepare API request parameters
            api_params = {
                "model": self.model,
                "response_format": "verbose_json"
            }

            if language != "auto":
                api_params["language"] = language

            if prompt:
                api_params["prompt"] = prompt

            # Make API request
            with open(temp_file_path, "rb") as audio_file:
                response = self.client.audio.transcriptions.create(
                    file=audio_file,
                    **api_params
                )

            # Clean up temporary file
            os.unlink(temp_file_path)

            # Parse response
            text = response.text.strip()
            detected_language = getattr(response, 'language', language)
            segments = getattr(response, 'segments', [])

            # Calculate average confidence from segments
            confidence = 0.0
            if segments:
                confidences = [seg.get('avg_logprob', 0) for seg in segments if 'avg_logprob' in seg]
                if confidences:
                    # Convert log probability to confidence (0-1)
                    confidence = min(1.0, max(0.0, (sum(confidences) / len(confidences) + 1) / 2))
            else:
                confidence = 0.8  # Default confidence when segments not available

            processing_time = time.time() - start_time

            return STTResult(
                text=text,
                confidence=confidence,
                language=detected_language,
                duration=len(audio_segment) / 1000.0,
                method="whisper",
                processing_time=processing_time,
                segments=segments
            )

        except Exception as e:
            # Clean up temporary file if it exists
            try:
                os.unlink(temp_file_path)
            except:
                pass

            return STTResult(
                text="", confidence=0.0, language=language,
                duration=len(audio_segment) / 1000.0, method="whisper",
                processing_time=time.time() - start_time,
                error=f"Whisper API错误: {str(e)}"
            )


class SpeechRecognitionFallback:
    """Fallback STT service using speech_recognition library"""

    def __init__(self):
        if SPEECH_RECOGNITION_AVAILABLE:
            self.recognizer = sr.Recognizer()
        else:
            self.recognizer = None

    def transcribe_audio(
        self,
        audio_segment: AudioSegment,
        language: str = "zh-CN"
    ) -> STTResult:
        """
        Transcribe audio using speech_recognition library

        Args:
            audio_segment: Audio to transcribe
            language: Language code for Google Web Speech API

        Returns:
            STTResult object with transcription results
        """
        if not self.recognizer:
            return STTResult(
                text="", confidence=0.0, language=language,
                duration=len(audio_segment) / 1000.0, method="speech_recognition",
                processing_time=0.0,
                error="speech_recognition库不可用"
            )

        start_time = time.time()

        try:
            # Convert AudioSegment to audio data
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                audio_segment.export(temp_file.name, format="wav")
                temp_file_path = temp_file.name

            # Load audio file
            with sr.AudioFile(temp_file_path) as source:
                audio_data = self.recognizer.record(source)

            # Clean up temporary file
            os.unlink(temp_file_path)

            # Recognize speech
            text = self.recognizer.recognize_google(audio_data, language=language)

            processing_time = time.time() - start_time

            return STTResult(
                text=text,
                confidence=0.7,  # speech_recognition doesn't provide confidence scores
                language=language,
                duration=len(audio_segment) / 1000.0,
                method="speech_recognition",
                processing_time=processing_time
            )

        except sr.UnknownValueError:
            return STTResult(
                text="", confidence=0.0, language=language,
                duration=len(audio_segment) / 1000.0, method="speech_recognition",
                processing_time=time.time() - start_time,
                error="无法识别音频内容"
            )
        except sr.RequestError as e:
            return STTResult(
                text="", confidence=0.0, language=language,
                duration=len(audio_segment) / 1000.0, method="speech_recognition",
                processing_time=time.time() - start_time,
                error=f"语音识别服务错误: {str(e)}"
            )
        except Exception as e:
            # Clean up temporary file if it exists
            try:
                os.unlink(temp_file_path)
            except:
                pass

            return STTResult(
                text="", confidence=0.0, language=language,
                duration=len(audio_segment) / 1000.0, method="speech_recognition",
                processing_time=time.time() - start_time,
                error=f"识别错误: {str(e)}"
            )


class STTStatisticsManager:
    """Manager for STT accuracy statistics and user feedback"""

    def __init__(self, stats_file: str = "data/stt_stats.json"):
        self.stats_file = Path(stats_file)
        self.stats_file.parent.mkdir(exist_ok=True)
        self.stats = self.load_stats()

    def load_stats(self) -> STTStats:
        """Load statistics from file"""
        if self.stats_file.exists():
            try:
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return STTStats(**data)
            except Exception:
                pass
        return STTStats()

    def save_stats(self):
        """Save statistics to file"""
        try:
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(self.stats), f, ensure_ascii=False, indent=2)
        except Exception as e:
            st.warning(f"保存统计数据失败: {str(e)}")

    def record_request(self, result: STTResult, user_edited: bool = False):
        """Record an STT request result"""
        self.stats.total_requests += 1

        if result.text and not result.error:
            self.stats.successful_requests += 1

            # Update average confidence
            old_avg = self.stats.average_confidence
            total_successful = self.stats.successful_requests
            self.stats.average_confidence = (old_avg * (total_successful - 1) + result.confidence) / total_successful

        if user_edited:
            self.stats.user_corrections += 1

        if result.error:
            error_key = result.error[:50]  # Truncate error message
            self.stats.common_errors[error_key] = self.stats.common_errors.get(error_key, 0) + 1

        self.save_stats()

    def record_user_satisfaction(self, rating: int):
        """Record user satisfaction rating (1-5 stars)"""
        if 1 <= rating <= 5:
            self.stats.user_satisfaction_ratings.append(rating)
            self.save_stats()

    def get_statistics_summary(self) -> Dict[str, Any]:
        """Get summary of STT statistics"""
        total = self.stats.total_requests
        if total == 0:
            return {"message": "暂无统计数据"}

        success_rate = (self.stats.successful_requests / total) * 100
        correction_rate = (self.stats.user_corrections / total) * 100 if total > 0 else 0

        avg_satisfaction = 0.0
        if self.stats.user_satisfaction_ratings:
            avg_satisfaction = sum(self.stats.user_satisfaction_ratings) / len(self.stats.user_satisfaction_ratings)

        return {
            "total_requests": total,
            "success_rate": round(success_rate, 1),
            "average_confidence": round(self.stats.average_confidence * 100, 1),
            "correction_rate": round(correction_rate, 1),
            "average_satisfaction": round(avg_satisfaction, 1),
            "satisfaction_count": len(self.stats.user_satisfaction_ratings),
            "common_errors": dict(list(self.stats.common_errors.items())[:5])  # Top 5 errors
        }


class ComprehensiveSTTService:
    """Main STT service combining all components"""

    def __init__(self):
        self.preprocessor = AudioPreprocessor()
        self.whisper_service = WhisperSTTService()
        self.fallback_service = SpeechRecognitionFallback()
        self.stats_manager = STTStatisticsManager()

        # Settings
        self.use_preprocessing = True
        self.use_fallback = True
        self.preferred_language = "auto"  # auto, zh, en

    def transcribe_audio(
        self,
        audio_segment: AudioSegment,
        language: str = None,
        use_fallback_on_error: bool = True,
        prompt: Optional[str] = None
    ) -> STTResult:
        """
        Main transcription method with preprocessing and fallback

        Args:
            audio_segment: Audio to transcribe
            language: Target language (overrides default)
            use_fallback_on_error: Whether to use fallback on Whisper errors
            prompt: Context prompt for better accuracy

        Returns:
            STTResult object
        """
        if not audio_segment:
            return STTResult(
                text="", confidence=0.0, language=language or "auto",
                duration=0.0, method="none", processing_time=0.0,
                error="音频为空"
            )

        target_language = language or self.preferred_language

        # Preprocess audio if enabled
        if self.use_preprocessing:
            try:
                audio_segment = self.preprocessor.preprocess_audio(audio_segment)
            except Exception as e:
                st.warning(f"音频预处理失败: {str(e)}")

        # Try Whisper API first
        try:
            # For async call, we need to handle it properly in Streamlit
            import asyncio

            # Check if there's a running event loop
            try:
                loop = asyncio.get_running_loop()
                # If there's a running loop, we can't use asyncio.run()
                # For Streamlit, we'll make it synchronous
                result = self._transcribe_whisper_sync(audio_segment, target_language, prompt)
            except RuntimeError:
                # No running loop, can use asyncio.run()
                result = asyncio.run(
                    self.whisper_service.transcribe_audio(audio_segment, target_language, prompt)
                )

            if result.text or not (use_fallback_on_error and self.use_fallback):
                self.stats_manager.record_request(result)
                return result

        except Exception as e:
            st.warning(f"Whisper API调用失败: {str(e)}")

        # Fallback to speech_recognition if Whisper fails
        if use_fallback_on_error and self.use_fallback:
            st.info("正在使用备用语音识别服务...")

            # Convert language code for speech_recognition
            sr_language = "zh-CN" if target_language in ["zh", "auto"] else "en-US"

            result = self.fallback_service.transcribe_audio(audio_segment, sr_language)
            self.stats_manager.record_request(result)
            return result

        # Return error if both services fail
        return STTResult(
            text="", confidence=0.0, language=target_language,
            duration=len(audio_segment) / 1000.0, method="failed",
            processing_time=0.0, error="所有语音识别服务都不可用"
        )

    def _transcribe_whisper_sync(
        self,
        audio_segment: AudioSegment,
        language: str,
        prompt: Optional[str]
    ) -> STTResult:
        """Synchronous version of Whisper transcription for Streamlit compatibility"""
        start_time = time.time()

        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                audio_segment.export(temp_file.name, format="wav")
                temp_file_path = temp_file.name

            # Check file size
            file_size = os.path.getsize(temp_file_path)
            if file_size > self.whisper_service.max_file_size:
                os.unlink(temp_file_path)
                return STTResult(
                    text="", confidence=0.0, language=language,
                    duration=len(audio_segment) / 1000.0, method="whisper",
                    processing_time=time.time() - start_time,
                    error="音频文件过大，请分段录制"
                )

            # Prepare API request parameters
            api_params = {
                "model": self.whisper_service.model,
                "response_format": "verbose_json"
            }

            if language != "auto":
                api_params["language"] = language

            if prompt:
                api_params["prompt"] = prompt

            # Make API request
            with open(temp_file_path, "rb") as audio_file:
                response = self.whisper_service.client.audio.transcriptions.create(
                    file=audio_file,
                    **api_params
                )

            # Clean up temporary file
            os.unlink(temp_file_path)

            # Parse response
            text = response.text.strip()
            detected_language = getattr(response, 'language', language)
            segments = getattr(response, 'segments', [])

            # Calculate average confidence from segments
            confidence = 0.0
            if segments:
                confidences = [seg.get('avg_logprob', 0) for seg in segments if 'avg_logprob' in seg]
                if confidences:
                    # Convert log probability to confidence (0-1)
                    confidence = min(1.0, max(0.0, (sum(confidences) / len(confidences) + 1) / 2))
            else:
                confidence = 0.8  # Default confidence when segments not available

            processing_time = time.time() - start_time

            return STTResult(
                text=text,
                confidence=confidence,
                language=detected_language,
                duration=len(audio_segment) / 1000.0,
                method="whisper",
                processing_time=processing_time,
                segments=segments
            )

        except Exception as e:
            # Clean up temporary file if it exists
            try:
                os.unlink(temp_file_path)
            except:
                pass

            return STTResult(
                text="", confidence=0.0, language=language,
                duration=len(audio_segment) / 1000.0, method="whisper",
                processing_time=time.time() - start_time,
                error=f"Whisper API错误: {str(e)}"
            )

    def process_long_audio(
        self,
        audio_segment: AudioSegment,
        language: str = None,
        prompt: Optional[str] = None
    ) -> STTResult:
        """
        Process long audio by splitting into chunks

        Args:
            audio_segment: Long audio to transcribe
            language: Target language
            prompt: Context prompt

        Returns:
            Combined STTResult
        """
        # Split audio into chunks
        chunks = self.preprocessor.split_long_audio(audio_segment)

        if len(chunks) == 1:
            return self.transcribe_audio(chunks[0], language, prompt=prompt)

        # Process each chunk
        results = []
        total_confidence = 0.0
        total_processing_time = 0.0
        combined_text = ""
        errors = []

        progress_bar = st.progress(0)
        status_text = st.empty()

        for i, chunk in enumerate(chunks):
            status_text.text(f"正在处理音频片段 {i+1}/{len(chunks)}...")
            progress_bar.progress((i + 1) / len(chunks))

            result = self.transcribe_audio(chunk, language, prompt=prompt)
            results.append(result)

            if result.text:
                combined_text += result.text + " "
                total_confidence += result.confidence

            total_processing_time += result.processing_time

            if result.error:
                errors.append(f"片段{i+1}: {result.error}")

        progress_bar.empty()
        status_text.empty()

        # Calculate combined results
        successful_chunks = [r for r in results if r.text]
        avg_confidence = total_confidence / len(successful_chunks) if successful_chunks else 0.0

        combined_error = "; ".join(errors) if errors else None

        return STTResult(
            text=combined_text.strip(),
            confidence=avg_confidence,
            language=results[0].language if results else (language or "auto"),
            duration=len(audio_segment) / 1000.0,
            method="whisper_chunked",
            processing_time=total_processing_time,
            segments=[],
            error=combined_error
        )

    def get_service_status(self) -> Dict[str, Any]:
        """Get status of all STT services"""
        return {
            "whisper_available": bool(os.getenv("OPENAI_API_KEY")),
            "speech_recognition_available": SPEECH_RECOGNITION_AVAILABLE,
            "preprocessing_enabled": self.use_preprocessing,
            "fallback_enabled": self.use_fallback,
            "preferred_language": self.preferred_language,
            "statistics": self.stats_manager.get_statistics_summary()
        }


# Singleton instance for global use
stt_service = ComprehensiveSTTService()