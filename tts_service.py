#!/usr/bin/env python3
"""
Text-to-Speech (TTS) service for AI Role-Playing Chat Application

This module provides TTS functionality using OpenAI's Text-to-Speech API with:
- Character-specific voice configurations
- Audio quality optimization
- Caching mechanism for performance
- Async audio generation
- Retry logic for reliability
"""

import os
import time
import asyncio
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any, Union
from datetime import datetime, timedelta

import streamlit as st
from openai import OpenAI
from pydub import AudioSegment

from models import VoiceConfig, Character
from audio_utils import AudioManager


class TTSService:
    """Text-to-Speech service using OpenAI API"""

    def __init__(self, cache_dir: str = "tts_cache"):
        """Initialize TTS service with caching"""
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.client = OpenAI(api_key=api_key)
        else:
            self.client = None

        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.audio_manager = AudioManager()

        # TTS settings
        self.supported_models = ["tts-1", "tts-1-hd"]
        self.supported_voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
        self.supported_formats = ["mp3", "opus", "aac", "flac"]

        # Cache settings
        self.cache_duration_days = 7
        self.max_cache_size_mb = 100

    def _generate_cache_key(self, text: str, voice_config: VoiceConfig, model: str) -> str:
        """Generate unique cache key for text and voice settings"""
        content = f"{text}_{voice_config.voice_id}_{voice_config.speed}_{model}"
        return hashlib.md5(content.encode()).hexdigest()

    def _get_cache_path(self, cache_key: str, format: str = "mp3") -> Path:
        """Get cache file path for given key"""
        return self.cache_dir / f"{cache_key}.{format}"

    def _is_cache_valid(self, cache_path: Path) -> bool:
        """Check if cache file is still valid"""
        if not cache_path.exists():
            return False

        # Check if file is within cache duration
        file_time = datetime.fromtimestamp(cache_path.stat().st_mtime)
        expiry_time = datetime.now() - timedelta(days=self.cache_duration_days)

        return file_time > expiry_time

    def _cleanup_cache(self):
        """Remove old cache files and manage cache size"""
        cache_files = list(self.cache_dir.glob("*.mp3"))

        # Remove expired files
        current_time = datetime.now()
        expiry_time = current_time - timedelta(days=self.cache_duration_days)

        for file_path in cache_files:
            file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
            if file_time < expiry_time:
                try:
                    file_path.unlink()
                except OSError:
                    pass

        # Check cache size and remove oldest files if needed
        remaining_files = list(self.cache_dir.glob("*.mp3"))
        total_size = sum(f.stat().st_size for f in remaining_files)
        max_size_bytes = self.max_cache_size_mb * 1024 * 1024

        if total_size > max_size_bytes:
            # Sort by modification time (oldest first)
            remaining_files.sort(key=lambda f: f.stat().st_mtime)

            for file_path in remaining_files:
                try:
                    file_path.unlink()
                    total_size -= file_path.stat().st_size
                    if total_size <= max_size_bytes * 0.8:  # Keep 80% of max size
                        break
                except OSError:
                    pass

    def generate_speech(
        self,
        text: str,
        voice_config: VoiceConfig,
        model: str = "tts-1-hd",
        format: str = "mp3",
        use_cache: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Generate speech from text using OpenAI TTS API

        Args:
            text: Text to convert to speech
            voice_config: Voice configuration
            model: TTS model to use ("tts-1" or "tts-1-hd")
            format: Audio format ("mp3", "opus", "aac", "flac")
            use_cache: Whether to use caching

        Returns:
            Dictionary with audio metadata or None if failed
        """
        if not text.strip():
            return None

        # Check if API client is available
        if not self.client:
            if 'st' in globals():
                st.error("OpenAI API密钥未设置，无法生成语音")
            return None

        # Validate inputs
        if model not in self.supported_models:
            model = "tts-1-hd"

        if voice_config.voice_id not in self.supported_voices:
            if 'st' in globals():
                st.warning(f"不支持的声音ID: {voice_config.voice_id}，使用默认声音")
            voice_config.voice_id = "alloy"

        # Check cache first
        cache_key = self._generate_cache_key(text, voice_config, model)
        cache_path = self._get_cache_path(cache_key, format)

        if use_cache and self._is_cache_valid(cache_path):
            return self._load_cached_audio(cache_path, text)

        try:
            # Generate speech using OpenAI API
            response = self.client.audio.speech.create(
                model=model,
                voice=voice_config.voice_id,
                input=text,
                response_format=format,
                speed=max(0.25, min(4.0, voice_config.speed))  # Clamp speed to valid range
            )

            # Save to cache
            if use_cache:
                with open(cache_path, "wb") as f:
                    f.write(response.content)

            # Create metadata
            metadata = {
                "file_path": str(cache_path) if use_cache else None,
                "content": response.content if not use_cache else None,
                "text": text,
                "voice_id": voice_config.voice_id,
                "model": model,
                "format": format,
                "speed": voice_config.speed,
                "size": len(response.content),
                "created_at": datetime.now().isoformat(),
                "cached": use_cache
            }

            return metadata

        except Exception as e:
            st.error(f"TTS生成失败: {str(e)}")
            return None

    def _load_cached_audio(self, cache_path: Path, text: str) -> Dict[str, Any]:
        """Load audio from cache and return metadata"""
        try:
            file_size = cache_path.stat().st_size

            metadata = {
                "file_path": str(cache_path),
                "content": None,
                "text": text,
                "format": cache_path.suffix[1:],  # Remove the dot
                "size": file_size,
                "cached": True,
                "cache_hit": True,
                "created_at": datetime.fromtimestamp(cache_path.stat().st_mtime).isoformat()
            }

            return metadata

        except Exception as e:
            st.error(f"加载缓存音频失败: {str(e)}")
            return None

    async def generate_speech_async(
        self,
        text: str,
        voice_config: VoiceConfig,
        model: str = "tts-1-hd",
        format: str = "mp3",
        use_cache: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Async version of generate_speech"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.generate_speech,
            text, voice_config, model, format, use_cache
        )

    def generate_speech_with_retry(
        self,
        text: str,
        voice_config: VoiceConfig,
        model: str = "tts-1-hd",
        format: str = "mp3",
        max_retries: int = 3,
        use_cache: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Generate speech with retry logic"""
        for attempt in range(max_retries):
            try:
                result = self.generate_speech(text, voice_config, model, format, use_cache)
                if result:
                    return result
            except Exception as e:
                if attempt == max_retries - 1:
                    st.error(f"TTS生成失败，重试{max_retries}次后放弃: {str(e)}")
                    return None
                else:
                    st.warning(f"TTS生成失败，正在重试 ({attempt + 1}/{max_retries})")
                    time.sleep(1)  # Wait before retry

        return None

    def get_voice_preview(self, voice_id: str) -> str:
        """Get a preview text for voice demonstration"""
        previews = {
            "alloy": "你好，我是Alloy，一个平衡自然的声音。",
            "echo": "你好，我是Echo，一个年轻活力的男性声音。",
            "fable": "你好，我是Fable，一个温和友善的声音。",
            "onyx": "你好，我是Onyx，一个深沉成熟的男性声音。",
            "nova": "你好，我是Nova，一个充满活力的女性声音。",
            "shimmer": "你好，我是Shimmer，一个温柔甜美的女性声音。"
        }
        return previews.get(voice_id, "你好，这是语音预览。")

    def get_optimal_voice_for_character(self, character_name: str) -> str:
        """Get optimal voice ID for character based on their traits"""
        voice_mapping = {
            "哈利·波特": "echo",      # 年轻活力的男性声音
            "苏格拉底": "onyx",       # 深沉成熟的男性声音
            "阿尔伯特·爱因斯坦": "fable"  # 温和友善的学者声音
        }
        return voice_mapping.get(character_name, "alloy")

    def get_cache_info(self) -> Dict[str, Any]:
        """Get cache statistics"""
        cache_files = list(self.cache_dir.glob("*.mp3"))
        total_size = sum(f.stat().st_size for f in cache_files)

        return {
            "total_files": len(cache_files),
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "cache_dir": str(self.cache_dir),
            "max_cache_size_mb": self.max_cache_size_mb,
            "cache_duration_days": self.cache_duration_days
        }

    def clear_cache(self):
        """Clear all cached audio files"""
        cache_files = list(self.cache_dir.glob("*.mp3"))
        cleared_count = 0

        for file_path in cache_files:
            try:
                file_path.unlink()
                cleared_count += 1
            except OSError:
                pass

        return cleared_count


class TTSManager:
    """High-level TTS manager for character-based speech generation"""

    def __init__(self):
        """Initialize TTS manager"""
        self.tts_service = TTSService()
        self.progress_container = None

    def generate_character_speech(
        self,
        text: str,
        character: Character,
        show_progress: bool = True,
        use_cache: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Generate speech for a specific character

        Args:
            text: Text to convert to speech
            character: Character object with voice configuration
            show_progress: Whether to show progress indicator
            use_cache: Whether to use caching

        Returns:
            Dictionary with audio metadata or None if failed
        """
        if show_progress:
            self.progress_container = st.empty()
            with self.progress_container:
                st.info("🎙️ 正在生成语音...")

        try:
            # Use character's voice config or get optimal voice
            voice_config = character.voice_config
            if not voice_config or voice_config.provider != "openai":
                # Create optimal voice config for character
                optimal_voice = self.tts_service.get_optimal_voice_for_character(character.name)
                voice_config = VoiceConfig(
                    provider="openai",
                    voice_id=optimal_voice,
                    speed=1.0,
                    volume=0.9
                )

            # Generate speech
            result = self.tts_service.generate_speech_with_retry(
                text=text,
                voice_config=voice_config,
                model="tts-1-hd",
                format="mp3",
                use_cache=use_cache
            )

            if show_progress and self.progress_container:
                if result:
                    cache_status = "（从缓存加载）" if result.get("cache_hit") else "（新生成）"
                    self.progress_container.success(f"✅ 语音生成完成 {cache_status}")
                else:
                    self.progress_container.error("❌ 语音生成失败")

            return result

        except Exception as e:
            if show_progress and self.progress_container:
                self.progress_container.error(f"❌ 语音生成错误: {str(e)}")
            return None

    def get_character_voice_preview(self, character: Character) -> Optional[Dict[str, Any]]:
        """Generate a voice preview for character"""
        preview_text = f"你好，我是{character.name}。{character.title}。"
        return self.generate_character_speech(
            text=preview_text,
            character=character,
            show_progress=False,
            use_cache=True
        )


# Singleton instance for global use
tts_manager = TTSManager()