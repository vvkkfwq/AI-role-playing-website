#!/usr/bin/env python3
"""
Audio processing utilities for AI Role-Playing Chat Application

This module provides audio processing functionality including:
- Audio file management and storage
- Audio format validation and conversion
- File cleanup and size management
- Audio quality checks
"""

import os
import time
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from datetime import datetime

try:
    from pydub import AudioSegment
    from pydub.utils import which
except ImportError:
    AudioSegment = None

import streamlit as st


class AudioManager:
    """Manager for audio file operations and storage"""

    def __init__(self, storage_dir: str = "audio_temp"):
        """Initialize AudioManager with storage directory"""
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)

        # Audio settings
        self.max_duration_seconds = 300  # 5 minutes
        self.max_file_size_mb = 5  # 5 MB
        self.supported_formats = ["wav", "mp3", "ogg", "m4a"]

        # Check if required tools are available
        self._check_dependencies()

    def _check_dependencies(self) -> Dict[str, bool]:
        """Check if required audio processing tools are available"""
        deps = {
            "pydub": AudioSegment is not None,
            "ffmpeg": which("ffmpeg") is not None,
        }
        return deps

    def validate_audio(self, audio_segment: "AudioSegment") -> Tuple[bool, str]:
        """
        Validate audio segment for duration and quality

        Args:
            audio_segment: pydub AudioSegment object

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not audio_segment:
            return False, "音频为空"

        # Check duration
        duration_seconds = len(audio_segment) / 1000.0
        if duration_seconds > self.max_duration_seconds:
            return False, f"录音时长超过限制({self.max_duration_seconds}秒)"

        if duration_seconds < 0.5:
            return False, "录音时长太短(至少0.5秒)"

        # Check file size (estimate)
        estimated_size = len(audio_segment.raw_data)
        if estimated_size > self.max_file_size_mb * 1024 * 1024:
            return False, f"音频文件过大(超过{self.max_file_size_mb}MB)"

        return True, ""

    def save_audio(
        self,
        audio_segment: "AudioSegment",
        conversation_id: Optional[int] = None,
        message_id: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Save audio segment to storage directory

        Args:
            audio_segment: pydub AudioSegment object
            conversation_id: Optional conversation ID
            message_id: Optional message ID

        Returns:
            Dictionary with audio metadata or None if failed
        """
        if not audio_segment:
            return None

        # Validate audio
        is_valid, error_msg = self.validate_audio(audio_segment)
        if not is_valid:
            st.error(f"音频验证失败: {error_msg}")
            return None

        # Generate filename
        timestamp = int(time.time())
        filename = f"audio_{conversation_id or 'temp'}_{message_id or timestamp}.wav"
        file_path = self.storage_dir / filename

        try:
            # Export audio as WAV format
            audio_segment.export(
                str(file_path),
                format="wav",
                parameters=["-acodec", "pcm_s16le"],  # Standard WAV format
            )

            # Get audio metadata
            duration = len(audio_segment) / 1000.0
            file_size = file_path.stat().st_size

            metadata = {
                "file_path": str(file_path),
                "filename": filename,
                "duration": round(duration, 2),
                "format": "wav",
                "size": file_size,
                "sample_rate": audio_segment.frame_rate,
                "channels": audio_segment.channels,
                "created_at": datetime.now().isoformat(),
            }

            return metadata

        except Exception as e:
            st.error(f"保存音频文件失败: {str(e)}")
            return None

    def load_audio(self, file_path: str) -> Optional["AudioSegment"]:
        """
        Load audio file as AudioSegment

        Args:
            file_path: Path to audio file

        Returns:
            AudioSegment object or None if failed
        """
        if not os.path.exists(file_path):
            return None

        try:
            return AudioSegment.from_wav(file_path)
        except Exception as e:
            st.error(f"加载音频文件失败: {str(e)}")
            return None

    def cleanup_old_files(self, max_age_hours: int = 24):
        """
        Remove audio files older than specified hours

        Args:
            max_age_hours: Maximum age in hours before deletion
        """
        cutoff_time = time.time() - (max_age_hours * 3600)

        for file_path in self.storage_dir.glob("*.wav"):
            if file_path.stat().st_mtime < cutoff_time:
                try:
                    file_path.unlink()
                except OSError:
                    pass  # Ignore errors during cleanup

    def get_storage_info(self) -> Dict[str, Any]:
        """
        Get information about audio storage

        Returns:
            Dictionary with storage statistics
        """
        files = list(self.storage_dir.glob("*.wav"))
        total_size = sum(f.stat().st_size for f in files)

        return {
            "total_files": len(files),
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "storage_dir": str(self.storage_dir),
            "max_duration": self.max_duration_seconds,
            "max_file_size_mb": self.max_file_size_mb,
        }

    def format_duration(self, seconds: float) -> str:
        """
        Format duration in seconds to human readable format

        Args:
            seconds: Duration in seconds

        Returns:
            Formatted duration string
        """
        if seconds < 60:
            return f"{seconds:.1f}秒"
        else:
            minutes = int(seconds // 60)
            remaining_seconds = seconds % 60
            return f"{minutes}分{remaining_seconds:.1f}秒"


class AudioUI:
    """UI components for audio recording and playback"""

    @staticmethod
    def show_recording_status(is_recording: bool, duration: float = 0):
        """Display recording status indicator"""
        if is_recording:
            st.markdown(
                f"""
                <div style="color: red; font-weight: bold;">
                    🔴 录制中... {duration:.1f}秒
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown("🎤 点击开始录制")

    @staticmethod
    def show_audio_info(metadata: Dict[str, Any]):
        """Display audio file information"""
        if not metadata:
            return

        duration_str = AudioManager().format_duration(metadata.get("duration", 0))
        size_mb = metadata.get("size", 0) / (1024 * 1024)

        st.markdown(
            f"""
        **音频信息:**
        - 时长: {duration_str}
        - 大小: {size_mb:.2f} MB
        - 格式: {metadata.get('format', '未知').upper()}
        - 采样率: {metadata.get('sample_rate', '未知')} Hz
        """
        )

    @staticmethod
    def show_error_message(error_type: str, details: str = ""):
        """Display user-friendly error messages"""
        error_messages = {
            "no_microphone": "❌ 未检测到麦克风设备",
            "permission_denied": "❌ 麦克风权限被拒绝，请在浏览器设置中允许麦克风访问",
            "https_required": "❌ 录音功能需要HTTPS连接，请使用https://访问",
            "browser_not_supported": "❌ 您的浏览器不支持录音功能",
            "file_too_large": "❌ 录音文件过大",
            "recording_failed": "❌ 录音失败",
            "playback_failed": "❌ 播放失败",
        }

        message = error_messages.get(error_type, f"❌ 未知错误: {error_type}")
        if details:
            message += f"\n详细信息: {details}"

        st.error(message)

    @staticmethod
    def show_dependencies_warning():
        """Show warning if audio dependencies are missing"""
        audio_manager = AudioManager()
        deps = audio_manager._check_dependencies()

        missing_deps = [name for name, available in deps.items() if not available]

        if missing_deps:
            st.warning(
                f"""
            ⚠️ 音频功能需要以下依赖项:
            {', '.join(missing_deps)}

            请安装: pip install {' '.join(missing_deps)}
            """
            )
            return False

        return True


# Singleton instance for global use
audio_manager = AudioManager()
