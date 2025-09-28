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


class TTSPlaybackUI:
    """UI components for TTS audio playback controls"""

    @staticmethod
    def show_tts_player(audio_metadata: Dict[str, Any], key_suffix: str = ""):
        """
        Display TTS audio player with controls

        Args:
            audio_metadata: Audio metadata from TTS service
            key_suffix: Unique suffix for Streamlit widget keys
        """
        if not audio_metadata:
            return

        # Create columns for player layout
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            # Audio file display
            file_path = audio_metadata.get("file_path")
            if file_path and os.path.exists(file_path):
                st.audio(file_path, format="audio/mp3")
            elif audio_metadata.get("content"):
                # Display audio from content bytes
                st.audio(audio_metadata["content"], format="audio/mp3")
            else:
                st.warning("音频文件不可用")

        with col2:
            # Audio info
            TTSPlaybackUI.show_tts_info(audio_metadata)

        with col3:
            # Control buttons
            if st.button("🔊 重播", key=f"replay_tts_{key_suffix}"):
                st.rerun()

            # Auto-generated indicator
            if audio_metadata.get("auto_generated"):
                st.markdown("🤖 **自动生成**")
                st.caption("已自动生成语音文件")

            if audio_metadata.get("cached"):
                cache_status = "💾 已缓存"
                if audio_metadata.get("cache_hit"):
                    cache_status += " (命中)"
            else:
                cache_status = "🆕 新生成"

            st.caption(cache_status)

    @staticmethod
    def show_tts_info(audio_metadata: Dict[str, Any]):
        """Display TTS audio information"""
        if not audio_metadata:
            return

        size_kb = audio_metadata.get("size", 0) / 1024
        voice_id = audio_metadata.get("voice_id", "未知")
        model = audio_metadata.get("model", "未知")
        speed = audio_metadata.get("speed", 1.0)

        st.markdown(
            f"""
            <div style="font-size: 0.8em; color: #666;">
            🎵 <strong>语音信息</strong><br/>
            声音: {voice_id}<br/>
            模型: {model}<br/>
            语速: {speed}x<br/>
            大小: {size_kb:.1f} KB
            </div>
            """,
            unsafe_allow_html=True
        )

    @staticmethod
    def show_voice_preview_player(character_name: str, voice_id: str, preview_audio: Dict[str, Any]):
        """Display voice preview player for character selection"""
        st.markdown(f"**{character_name}** ({voice_id})")

        if preview_audio:
            # Show audio player
            file_path = preview_audio.get("file_path")
            if file_path and os.path.exists(file_path):
                st.audio(file_path, format="audio/mp3")
            elif preview_audio.get("content"):
                st.audio(preview_audio["content"], format="audio/mp3")

            # Show voice characteristics
            TTSPlaybackUI.show_voice_characteristics(voice_id)
        else:
            st.warning("预览音频生成失败")

    @staticmethod
    def show_voice_characteristics(voice_id: str):
        """Display voice characteristics description"""
        characteristics = {
            "echo": "🎭 年轻活力的男性声音，适合哈利波特",
            "onyx": "🏛️ 深沉成熟的男性声音，适合苏格拉底",
            "fable": "🧠 温和友善的声音，适合爱因斯坦",
            "alloy": "⚖️ 平衡自然的中性声音",
            "nova": "✨ 充满活力的女性声音",
            "shimmer": "🌟 温柔甜美的女性声音"
        }

        desc = characteristics.get(voice_id, "🎵 标准语音")
        st.caption(desc)

    @staticmethod
    def show_tts_settings_panel():
        """Display TTS settings configuration panel"""
        st.subheader("🎙️ 语音设置")

        with st.expander("高级语音选项", expanded=False):
            col1, col2 = st.columns(2)

            with col1:
                model = st.selectbox(
                    "TTS模型",
                    options=["tts-1-hd", "tts-1"],
                    help="tts-1-hd: 高质量但较慢, tts-1: 快速但质量一般"
                )

                format_option = st.selectbox(
                    "音频格式",
                    options=["mp3", "opus", "aac", "flac"],
                    help="mp3: 通用格式, opus: 高压缩, aac: 高质量, flac: 无损"
                )

            with col2:
                use_cache = st.checkbox(
                    "启用缓存",
                    value=True,
                    help="缓存生成的音频以提高性能"
                )

                auto_play = st.checkbox(
                    "自动生成语音",
                    value=False,
                    help="AI回复后自动生成语音文件"
                )

        return {
            "model": model,
            "format": format_option,
            "use_cache": use_cache,
            "auto_play": auto_play
        }

    @staticmethod
    def show_tts_status(is_generating: bool, message: str = ""):
        """Display TTS generation status"""
        if is_generating:
            st.markdown(
                f"""
                <div style="color: #ff6b35; font-weight: bold; padding: 10px;
                           background-color: #fff3e0; border-radius: 5px; margin: 10px 0;">
                    🎙️ 正在生成语音... {message}
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            # Clear status
            st.empty()

    @staticmethod
    def show_cache_management():
        """Display cache management interface with collapsible layout"""
        try:
            from services.tts_service import tts_manager
            cache_info = tts_manager.tts_service.get_cache_info()

            # Calculate summary info for expander title
            total_files = cache_info["total_files"]
            max_size = cache_info["max_cache_size_mb"]
            usage_pct = (cache_info["total_size_mb"] / max_size * 100) if max_size > 0 else 0

            # Create expander with summary in title
            with st.expander(f"💾 缓存管理 ({total_files} 文件, {usage_pct:.1f}%)", expanded=False):
                # Detailed metrics
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("缓存文件数", total_files)

                with col2:
                    st.metric("缓存大小", f"{cache_info['total_size_mb']} MB")

                with col3:
                    st.metric("使用率", f"{usage_pct:.1f}%")

                st.caption(f"📁 缓存目录: {cache_info['cache_dir']}")
                st.caption(f"⏱️ 缓存期限: {cache_info['cache_duration_days']} 天")

                st.markdown("---")

                # Management buttons with better layout
                col1, col2 = st.columns(2)

                with col1:
                    if st.button("🧹 清理过期文件", use_container_width=True):
                        tts_manager.tts_service._cleanup_cache()
                        st.success("✅ 已清理过期文件")
                        st.rerun()

                with col2:
                    # Clear cache with confirmation
                    if "confirm_clear_cache" not in st.session_state:
                        st.session_state.confirm_clear_cache = False

                    if not st.session_state.confirm_clear_cache:
                        if st.button("🗑️ 清空缓存", use_container_width=True):
                            st.session_state.confirm_clear_cache = True
                            st.rerun()
                    else:
                        st.warning("⚠️ 确定要清空所有缓存文件吗？")
                        col_confirm, col_cancel = st.columns(2)

                        with col_confirm:
                            if st.button("✅ 确认", type="primary", use_container_width=True):
                                cleared = tts_manager.tts_service.clear_cache()
                                st.success(f"✅ 已清空 {cleared} 个缓存文件")
                                st.session_state.confirm_clear_cache = False
                                st.rerun()

                        with col_cancel:
                            if st.button("❌ 取消", use_container_width=True):
                                st.session_state.confirm_clear_cache = False
                                st.rerun()

        except ImportError:
            with st.expander("💾 缓存管理 (服务未初始化)", expanded=False):
                st.error("❌ TTS服务未正确初始化")
                st.info("💡 请检查OpenAI API密钥配置")
        except Exception as e:
            with st.expander("💾 缓存管理 (加载失败)", expanded=False):
                st.error(f"❌ 加载缓存信息失败: {str(e)}")
                st.info("💡 请检查TTS服务配置")


# Singleton instance for global use
audio_manager = AudioManager()
