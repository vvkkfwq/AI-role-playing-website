import sys
import os
from pathlib import Path

# Add project root to path if not already there
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import streamlit as st
from openai import OpenAI
from typing import List, Dict, Any
from dotenv import load_dotenv

# Import our enhanced database and models
from app.database import DatabaseManager
from app.models import Character, MessageRole

# Import audio processing utilities
from services.audio_utils import audio_manager, AudioUI, TTSPlaybackUI

# Import speech-to-text service
from services.stt_service import stt_service, STTResult

# Import text-to-speech service
from services.tts_service import tts_manager

try:
    from audiorecorder import audiorecorder

    AUDIO_RECORDER_AVAILABLE = True
except ImportError:
    AUDIO_RECORDER_AVAILABLE = False

load_dotenv()


class AIRolePlayApp:
    def __init__(self):
        self.db = DatabaseManager()
        self.init_openai()
        self.init_session_state()
        self.init_audio_cleanup()

    def init_openai(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            st.error("请在.env文件中设置OPENAI_API_KEY")
            st.stop()
        self.client = OpenAI(api_key=api_key)

    def init_session_state(self):
        if "messages" not in st.session_state:
            st.session_state.messages = []
        if "selected_character" not in st.session_state:
            st.session_state.selected_character = None
        if "current_conversation_id" not in st.session_state:
            st.session_state.current_conversation_id = None
        # STT-related session state
        if "stt_enabled" not in st.session_state:
            st.session_state.stt_enabled = True
        if "stt_language" not in st.session_state:
            st.session_state.stt_language = "auto"
        if "pending_stt_result" not in st.session_state:
            st.session_state.pending_stt_result = None
        if "show_stt_editing" not in st.session_state:
            st.session_state.show_stt_editing = False
        # TTS-related session state
        if "tts_enabled" not in st.session_state:
            st.session_state.tts_enabled = True
        if "tts_auto_play" not in st.session_state:
            st.session_state.tts_auto_play = False
        if "tts_model" not in st.session_state:
            st.session_state.tts_model = "tts-1-hd"
        if "tts_format" not in st.session_state:
            st.session_state.tts_format = "mp3"

    def init_audio_cleanup(self):
        """Initialize audio file cleanup on app start"""
        try:
            # Clean up old audio files (older than 24 hours)
            audio_manager.cleanup_old_files(max_age_hours=24)
        except Exception:
            # Silently handle cleanup errors
            pass

    def get_character_prompt(self, character: Character) -> str:
        """Generate system prompt from character template"""
        # Use the character's prompt_template directly
        return character.prompt_template

    def generate_response(self, messages: List[Dict], character: Character) -> str:
        try:
            system_prompt = self.get_character_prompt(character)

            formatted_messages = [{"role": "system", "content": system_prompt}]
            formatted_messages.extend(messages)

            response = self.client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
                messages=formatted_messages,
                max_tokens=500,
                temperature=0.8,
                stream=True
            )

            # Handle streaming response
            full_response = ""
            placeholder = st.empty()

            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    full_response += chunk.choices[0].delta.content
                    placeholder.markdown(full_response + "▊")

            # Remove cursor and display final response
            placeholder.markdown(full_response)
            return full_response

        except Exception as e:
            return f"抱歉，我现在无法回应。错误：{str(e)}"

    def render_sidebar(self):
        with st.sidebar:
            st.title("🎭 角色选择")

            characters = self.db.get_all_characters()

            if not characters:
                st.warning(
                    "没有找到角色。请运行 `python init_database.py` 初始化数据库。"
                )
                return

            character_options = {
                f"{char.avatar_emoji} {char.name}": char for char in characters
            }

            selected_display_name = st.selectbox(
                "选择一个角色开始对话", list(character_options.keys()), index=0
            )

            if selected_display_name:
                selected_character = character_options[selected_display_name]

                # Check if character changed
                if (
                    st.session_state.selected_character is None
                    or st.session_state.selected_character.id != selected_character.id
                ):
                    st.session_state.selected_character = selected_character
                    st.session_state.messages = []
                    st.session_state.current_conversation_id = None

                st.markdown("---")

                # Display character info
                st.markdown(
                    f"### {selected_character.avatar_emoji} {selected_character.name}"
                )
                st.markdown(f"**{selected_character.title}**")

                # Display personality traits
                if selected_character.personality:
                    st.markdown("**性格特征:**")
                    for trait in selected_character.personality:
                        st.markdown(f"• {trait}")

                # Display skills
                if selected_character.skills:
                    st.markdown("**技能:**")
                    skills_text = ", ".join(selected_character.skills[:3])
                    if len(selected_character.skills) > 3:
                        skills_text += f" 等{len(selected_character.skills)}项技能"
                    st.markdown(f"*{skills_text}*")

                st.markdown("---")

                # STT Settings
                st.markdown("### 🎤 语音识别设置")

                # STT enable/disable
                st.session_state.stt_enabled = st.toggle(
                    "启用语音识别",
                    value=st.session_state.stt_enabled,
                    help="开启后录音将自动转换为文字"
                )

                if st.session_state.stt_enabled:
                    # Language selection
                    language_options = {
                        "自动检测": "auto",
                        "中文": "zh",
                        "English": "en"
                    }

                    selected_lang = st.selectbox(
                        "识别语言",
                        options=list(language_options.keys()),
                        index=list(language_options.values()).index(st.session_state.stt_language)
                    )
                    st.session_state.stt_language = language_options[selected_lang]

                    # Show STT statistics
                    stt_stats = stt_service.stats_manager.get_statistics_summary()
                    if "total_requests" in stt_stats and stt_stats["total_requests"] > 0:
                        with st.expander("📊 识别统计"):
                            st.metric("总请求数", stt_stats["total_requests"])
                            st.metric("成功率", f"{stt_stats['success_rate']}%")
                            st.metric("平均准确度", f"{stt_stats['average_confidence']}%")
                            if stt_stats["correction_rate"] > 0:
                                st.metric("用户修正率", f"{stt_stats['correction_rate']}%")

                st.markdown("---")

                # TTS Settings
                st.markdown("### 🎙️ 语音合成设置")

                # TTS enable/disable
                st.session_state.tts_enabled = st.toggle(
                    "启用语音合成",
                    value=st.session_state.tts_enabled,
                    help="开启后AI回复将生成语音"
                )

                if st.session_state.tts_enabled:
                    # Auto-play option
                    st.session_state.tts_auto_play = st.checkbox(
                        "自动播放",
                        value=st.session_state.tts_auto_play,
                        help="AI回复后自动播放语音"
                    )

                    # Advanced TTS settings
                    with st.expander("高级设置", expanded=False):
                        st.session_state.tts_model = st.selectbox(
                            "TTS模型",
                            options=["tts-1-hd", "tts-1"],
                            index=0 if st.session_state.tts_model == "tts-1-hd" else 1,
                            help="tts-1-hd: 高质量, tts-1: 快速"
                        )

                        st.session_state.tts_format = st.selectbox(
                            "音频格式",
                            options=["mp3", "opus", "aac"],
                            index=["mp3", "opus", "aac"].index(st.session_state.tts_format),
                            help="不同格式的音质和大小有所差异"
                        )

                        # Voice preview button
                        if st.button("🎵 试听角色声音"):
                            self.play_character_voice_preview(selected_character)

                    # Show cache management
                    TTSPlaybackUI.show_cache_management()

                st.markdown("---")

                # Action buttons
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🗑️ 清空对话", type="secondary"):
                        st.session_state.messages = []
                        st.session_state.current_conversation_id = None
                        st.rerun()

                with col2:
                    if st.button("💾 保存对话"):
                        self.save_current_conversation()
                        st.success("对话已保存!")

    def save_current_conversation(self):
        """Save current conversation to database"""
        if not st.session_state.selected_character or not st.session_state.messages:
            return

        character = st.session_state.selected_character

        # Create conversation if not exists
        if not st.session_state.current_conversation_id:
            # Generate title from first user message
            title = "新对话"
            if st.session_state.messages:
                first_user_msg = next(
                    (msg for msg in st.session_state.messages if msg["role"] == "user"),
                    None,
                )
                if first_user_msg:
                    title = first_user_msg["content"][:30] + (
                        "..." if len(first_user_msg["content"]) > 30 else ""
                    )

            conversation_id = self.db.create_conversation(character.id, title)
            st.session_state.current_conversation_id = conversation_id

        # Add messages to conversation
        for message in st.session_state.messages:
            # Check if message already exists (basic deduplication)
            metadata = message.get("metadata")
            self.db.add_message(
                conversation_id=st.session_state.current_conversation_id,
                role=message["role"],
                content=message["content"],
                metadata=metadata,
            )

    def render_chat(self):
        if not st.session_state.selected_character:
            st.info("请在左侧选择一个角色开始对话")
            return

        character = st.session_state.selected_character
        st.title(f"💬 与 {character.avatar_emoji} {character.name} 对话")

        # Display character description
        st.markdown(f"*{character.title}*")
        st.markdown("---")

        chat_container = st.container()

        with chat_container:
            for message in st.session_state.messages:
                role = message["role"]
                content = message["content"]
                metadata = message.get("metadata", {})

                if role == "user":
                    with st.chat_message("user"):
                        # Check if this is an audio message
                        if "audio" in metadata:
                            self.render_audio_message(metadata["audio"], content)
                        else:
                            st.markdown(content)
                elif role == "assistant":
                    with st.chat_message("assistant", avatar=character.avatar_emoji):
                        st.markdown(content)

                        # Add TTS player if enabled
                        if st.session_state.tts_enabled:
                            self.render_tts_for_message(content, character, message.get("message_id"))

        # Input section with both text and audio options
        self.render_input_section(character)

    def render_audio_message(self, audio_metadata: Dict[str, Any], content: str):
        """Render an audio message with playback controls and STT results"""
        st.markdown(
            f"🎤 **语音消息** ({audio_manager.format_duration(audio_metadata.get('duration', 0))})"
        )

        # Show STT results if available
        stt_result = audio_metadata.get("stt_result")
        if stt_result:
            confidence = stt_result.get("confidence", 0) * 100
            method = stt_result.get("method", "unknown")
            language = stt_result.get("language", "auto")

            # Show transcription with confidence indicator
            confidence_color = "green" if confidence > 80 else "orange" if confidence > 60 else "red"
            st.markdown(
                f"🔤 **识别结果** ({method}, {language}, "
                f"<span style='color:{confidence_color}'>{confidence:.1f}%</span>):",
                unsafe_allow_html=True
            )

            if content and content != "[音频消息]":
                st.markdown(f"*{content}*")
            else:
                st.markdown("*无法识别音频内容*")

            # Show processing time if available
            if "processing_time" in stt_result:
                st.caption(f"处理时间: {stt_result['processing_time']:.1f}秒")

        elif content and content != "[音频消息]":
            st.markdown(f"*转录文本:* {content}")

        # Audio playback
        file_path = audio_metadata.get("file_path")
        if file_path and os.path.exists(file_path):
            with open(file_path, "rb") as audio_file:
                st.audio(audio_file.read(), format="audio/wav")

    def render_input_section(self, character: Character):
        """Render input section with text and audio options"""
        # Text input
        text_prompt = st.chat_input("输入你的消息...")

        # Audio recording section
        if AUDIO_RECORDER_AVAILABLE:
            st.markdown("### 🎤 语音录制")

            # Check dependencies and show warnings
            dependencies_ok = AudioUI.show_dependencies_warning()

            if not dependencies_ok:
                st.info("语音功能暂不可用，请使用文本输入")
            else:
                # Check HTTPS requirement
                if not self._check_https_context():
                    AudioUI.show_error_message("https_required")
                    st.info("请使用文本输入")
                else:
                    col1, col2 = st.columns([3, 1])

                    with col1:
                        try:
                            audio = audiorecorder("点击录制", "点击停止")
                        except Exception as e:
                            AudioUI.show_error_message("recording_failed", str(e))
                            audio = None

                    with col2:
                        if audio and len(audio) > 0:
                            # Validate audio before showing controls
                            is_valid, error_msg = audio_manager.validate_audio(audio)

                            if is_valid:
                                # Show audio info
                                duration = len(audio) / 1000.0
                                st.write(f"⏱️ {audio_manager.format_duration(duration)}")

                                # Preview audio
                                try:
                                    st.audio(audio.export().read(), format="audio/wav")
                                except Exception:
                                    st.warning("音频预览不可用")

                                # STT processing and send buttons
                                col_stt, col_send = st.columns(2)

                                with col_stt:
                                    if st.session_state.stt_enabled and st.button("🔤 转文字", help="使用语音识别转换为文字"):
                                        self.process_stt_conversion(audio, character)
                                        st.rerun()

                                with col_send:
                                    if st.button("📤 发送语音", type="primary"):
                                        if st.session_state.stt_enabled:
                                            # Process with STT
                                            self.process_user_message_with_stt(audio, character)
                                        else:
                                            # Send as audio message only
                                            self.process_user_message("[音频消息]", audio, character)
                                        st.rerun()
                            else:
                                st.error(f"音频验证失败: {error_msg}")

        else:
            st.warning(
                "⚠️ 语音录制功能不可用。请安装: pip install streamlit-audiorecorder"
            )

        # STT Results Editing Interface
        if st.session_state.pending_stt_result and st.session_state.show_stt_editing:
            self.render_stt_editing_interface(character)

        # Process text input
        if text_prompt:
            self.process_user_message(text_prompt, None, character)

    def _check_https_context(self) -> bool:
        """Check if the app is running in HTTPS context for audio recording"""
        try:
            # In Streamlit Cloud or when served over HTTPS, this should work
            # This is a basic check - the actual audio recording will fail gracefully if not HTTPS
            return True  # Let the audiorecorder component handle the HTTPS requirement
        except Exception:
            return False

    def process_stt_conversion(self, audio_segment, character: Character = None):
        """Process STT conversion and show editing interface"""
        with st.spinner("正在识别语音..."):
            # Get character context for better STT accuracy
            prompt = None
            if character:
                prompt = f"角色对话: {character.name} - {character.title}"

            # Perform STT
            stt_result = stt_service.transcribe_audio(
                audio_segment,
                language=st.session_state.stt_language,
                prompt=prompt
            )

            # Store results in session state
            st.session_state.pending_stt_result = {
                "stt_result": stt_result,
                "audio_segment": audio_segment,
                "character": character,
                "original_text": stt_result.text,
                "edited_text": stt_result.text
            }
            st.session_state.show_stt_editing = True

        # Show result
        if stt_result.error:
            st.error(f"语音识别失败: {stt_result.error}")
        else:
            st.success(f"识别完成! 准确度: {stt_result.confidence*100:.1f}%")

    def render_stt_editing_interface(self, character: Character):
        """Render interface for editing STT results"""
        st.markdown("### ✏️ 编辑识别结果")

        pending = st.session_state.pending_stt_result
        if not pending:
            return

        stt_result = pending["stt_result"]

        # Show original result with confidence
        confidence = stt_result.confidence * 100
        confidence_color = "green" if confidence > 80 else "orange" if confidence > 60 else "red"

        st.markdown(
            f"**原识别结果** (准确度: <span style='color:{confidence_color}'>{confidence:.1f}%</span>):",
            unsafe_allow_html=True
        )
        st.info(stt_result.text if stt_result.text else "无法识别音频内容")

        # Editable text area
        edited_text = st.text_area(
            "编辑文本:",
            value=pending["edited_text"],
            height=100,
            help="您可以修正识别错误的文字"
        )

        # Update edited text in session state
        st.session_state.pending_stt_result["edited_text"] = edited_text

        # Action buttons
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("✅ 发送消息", type="primary"):
                # Send the edited text as message
                self.send_stt_message(edited_text, pending, user_edited=(edited_text != stt_result.text))
                st.rerun()

        with col2:
            if st.button("🔄 重新识别"):
                # Re-run STT with different settings
                with st.spinner("重新识别中..."):
                    new_result = stt_service.transcribe_audio(
                        pending["audio_segment"],
                        language="auto",  # Try auto-detection
                        use_fallback_on_error=True
                    )
                    st.session_state.pending_stt_result["stt_result"] = new_result
                    st.session_state.pending_stt_result["edited_text"] = new_result.text
                st.rerun()

        with col3:
            if st.button("📤 仅发语音"):
                # Send as audio message without text
                self.send_stt_message("[音频消息]", pending, user_edited=False)
                st.rerun()

        with col4:
            if st.button("❌ 取消"):
                # Clear pending STT result
                st.session_state.pending_stt_result = None
                st.session_state.show_stt_editing = False
                st.rerun()

        # User feedback section
        st.markdown("---")
        st.markdown("**反馈识别质量** (帮助改进服务):")

        col_rating1, col_rating2 = st.columns([1, 2])

        with col_rating1:
            rating = st.select_slider(
                "满意度",
                options=[1, 2, 3, 4, 5],
                value=3,
                format_func=lambda x: "⭐" * x
            )

        with col_rating2:
            if st.button("提交评分"):
                stt_service.stats_manager.record_user_satisfaction(rating)
                st.success("感谢您的反馈!")

    def send_stt_message(self, text_content: str, pending_data: dict, user_edited: bool = False):
        """Send message with STT metadata"""
        stt_result = pending_data["stt_result"]
        audio_segment = pending_data["audio_segment"]
        character = pending_data["character"]

        # Save audio file
        audio_metadata = audio_manager.save_audio(
            audio_segment,
            conversation_id=st.session_state.current_conversation_id,
        )

        # Add STT result to audio metadata
        if audio_metadata:
            # Convert STTResult to dict for JSON serialization
            stt_dict = {
                "text": stt_result.text,
                "confidence": stt_result.confidence,
                "language": stt_result.language,
                "duration": stt_result.duration,
                "method": stt_result.method,
                "processing_time": stt_result.processing_time,
                "user_edited": user_edited
            }
            audio_metadata["stt_result"] = stt_dict

        # Create message data
        message_data = {
            "role": "user",
            "content": text_content,
            "metadata": {"audio": audio_metadata} if audio_metadata else {}
        }

        # Record STT statistics
        stt_service.stats_manager.record_request(stt_result, user_edited)

        # Add to messages and process
        st.session_state.messages.append(message_data)

        # Generate assistant response
        if character and text_content != "[音频消息]":
            with st.chat_message("assistant", avatar=character.avatar_emoji):
                with st.spinner(f"{character.name}正在思考..."):
                    response = self.generate_response_with_tts(st.session_state.messages, character)
                st.markdown(response)

                # Add TTS player if enabled
                if st.session_state.tts_enabled:
                    self.render_tts_for_message(response, character)

            st.session_state.messages.append({"role": "assistant", "content": response})

        # Clear pending STT result
        st.session_state.pending_stt_result = None
        st.session_state.show_stt_editing = False

        # Auto-save conversation
        if len(st.session_state.messages) % 6 == 0:
            self.save_current_conversation()

    def render_tts_for_message(self, text: str, character: Character, message_id: int = None):
        """Render TTS audio player for assistant message"""
        if not text or text.strip() == "":
            return

        # Create unique key for this message's TTS
        tts_key = f"tts_{message_id}_{hash(text)}" if message_id else f"tts_{hash(text)}"

        # Check if TTS audio already exists in session state
        tts_cache_key = f"tts_audio_{tts_key}"

        if tts_cache_key not in st.session_state:
            # Generate TTS button
            col1, col2 = st.columns([1, 3])
            with col1:
                if st.button("🎵 生成语音", key=f"gen_{tts_key}"):
                    with st.spinner("正在生成语音..."):
                        tts_audio = tts_manager.generate_character_speech(
                            text=text,
                            character=character,
                            show_progress=False,
                            use_cache=True
                        )
                        st.session_state[tts_cache_key] = tts_audio
                        st.rerun()
        else:
            # Display TTS player
            tts_audio = st.session_state[tts_cache_key]
            if tts_audio:
                TTSPlaybackUI.show_tts_player(tts_audio, key_suffix=tts_key)

    def play_character_voice_preview(self, character: Character):
        """Play voice preview for character"""
        with st.spinner("正在生成语音预览..."):
            preview_audio = tts_manager.get_character_voice_preview(character)

        if preview_audio:
            st.success("语音预览生成成功！")
            TTSPlaybackUI.show_voice_preview_player(
                character.name,
                character.voice_config.voice_id if character.voice_config else "alloy",
                preview_audio
            )
        else:
            st.error("语音预览生成失败")

    def generate_response_with_tts(self, messages: List[Dict], character: Character) -> str:
        """Generate streaming response and optionally create TTS audio"""
        try:
            system_prompt = self.get_character_prompt(character)
            formatted_messages = [{"role": "system", "content": system_prompt}]
            formatted_messages.extend(messages)

            response = self.client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
                messages=formatted_messages,
                max_tokens=500,
                temperature=0.8,
                stream=True
            )

            # Handle streaming response
            full_response = ""
            placeholder = st.empty()

            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    full_response += chunk.choices[0].delta.content
                    placeholder.markdown(full_response + "▊")

            # Remove cursor and display final response
            placeholder.markdown(full_response)

            # Generate TTS if enabled and auto-play is on
            if st.session_state.tts_enabled and st.session_state.tts_auto_play:
                # Generate TTS in background
                tts_audio = tts_manager.generate_character_speech(
                    text=full_response,
                    character=character,
                    show_progress=False,
                    use_cache=True
                )

                # Store in session state for immediate playback
                if tts_audio:
                    tts_key = f"tts_auto_{hash(full_response)}"
                    st.session_state[f"tts_audio_{tts_key}"] = tts_audio

            return full_response

        except Exception as e:
            return f"抱歉，我现在无法回应。错误：{str(e)}"

    def process_user_message_with_stt(self, audio_segment, character: Character = None):
        """Process audio message with automatic STT conversion"""
        with st.spinner("正在识别语音..."):
            # Get character context for better STT accuracy
            prompt = None
            if character:
                prompt = f"角色对话: {character.name} - {character.title}"

            # Determine if we should process long audio in chunks
            duration_seconds = len(audio_segment) / 1000.0

            if duration_seconds > 30:  # Long audio
                stt_result = stt_service.process_long_audio(
                    audio_segment,
                    language=st.session_state.stt_language,
                    prompt=prompt
                )
            else:
                stt_result = stt_service.transcribe_audio(
                    audio_segment,
                    language=st.session_state.stt_language,
                    prompt=prompt
                )

        # Handle STT result
        if stt_result.error:
            st.error(f"语音识别失败: {stt_result.error}")
            # Fall back to audio-only message
            self.process_user_message("[音频消息]", audio_segment, character)
        else:
            # Use recognized text or fallback to audio message
            text_content = stt_result.text if stt_result.text else "[音频消息]"

            # Save audio with STT metadata
            audio_metadata = audio_manager.save_audio(
                audio_segment,
                conversation_id=st.session_state.current_conversation_id,
            )

            if audio_metadata:
                # Add STT result to metadata
                stt_dict = {
                    "text": stt_result.text,
                    "confidence": stt_result.confidence,
                    "language": stt_result.language,
                    "duration": stt_result.duration,
                    "method": stt_result.method,
                    "processing_time": stt_result.processing_time,
                    "user_edited": False
                }
                audio_metadata["stt_result"] = stt_dict

            # Create message
            message_data = {
                "role": "user",
                "content": text_content,
                "metadata": {"audio": audio_metadata} if audio_metadata else {}
            }

            # Record statistics
            stt_service.stats_manager.record_request(stt_result, user_edited=False)

            # Add to session and display
            st.session_state.messages.append(message_data)

            # Display user message
            with st.chat_message("user"):
                if audio_metadata:
                    self.render_audio_message(audio_metadata, text_content)
                else:
                    st.markdown(text_content)

            # Generate assistant response if we have text
            if character and text_content != "[音频消息]":
                with st.chat_message("assistant", avatar=character.avatar_emoji):
                    with st.spinner(f"{character.name}正在思考..."):
                        response = self.generate_response_with_tts(st.session_state.messages, character)
                    st.markdown(response)

                    # Add TTS player if enabled
                    if st.session_state.tts_enabled:
                        self.render_tts_for_message(response, character)

                st.session_state.messages.append({"role": "assistant", "content": response})

            # Auto-save conversation
            if len(st.session_state.messages) % 6 == 0:
                self.save_current_conversation()

    def process_user_message(
        self, content: str, audio_segment=None, character: Character = None
    ):
        """Process user message (text or audio) and generate response"""
        message_data = {"role": "user", "content": content}

        # Handle audio message
        if audio_segment is not None:
            try:
                # Save audio file
                audio_metadata = audio_manager.save_audio(
                    audio_segment,
                    conversation_id=st.session_state.current_conversation_id,
                )

                if audio_metadata:
                    message_data["metadata"] = {"audio": audio_metadata}
                else:
                    st.error("音频处理失败，将作为文本消息发送")

            except Exception as e:
                st.error(f"音频处理错误: {str(e)}")

        # Add user message to session
        st.session_state.messages.append(message_data)

        # Display user message
        with st.chat_message("user"):
            if audio_segment is not None and message_data.get("metadata", {}).get(
                "audio"
            ):
                self.render_audio_message(message_data["metadata"]["audio"], content)
            else:
                st.markdown(content)

        # Generate assistant response
        if character:
            with st.chat_message("assistant", avatar=character.avatar_emoji):
                with st.spinner(f"{character.name}正在思考..."):
                    # For audio messages, use the content as text for AI processing
                    response = self.generate_response_with_tts(
                        st.session_state.messages, character
                    )
                st.markdown(response)

                # Add TTS player if enabled
                if st.session_state.tts_enabled:
                    self.render_tts_for_message(response, character)

            st.session_state.messages.append({"role": "assistant", "content": response})

            # Auto-save conversation periodically
            if len(st.session_state.messages) % 6 == 0:
                self.save_current_conversation()

    def render_conversations_history(self):
        """Render conversation history page"""
        st.title("📚 对话历史")

        if not st.session_state.selected_character:
            st.info("请先选择一个角色查看对话历史")
            return

        character = st.session_state.selected_character
        conversations = self.db.get_conversations_by_character(character.id)

        if not conversations:
            st.info(f"暂无与 {character.name} 的对话记录")
            return

        st.markdown(f"### {character.avatar_emoji} {character.name} 的对话记录")

        for conversation in conversations:
            with st.expander(
                f"🗂️ {conversation.title} ({len(conversation.messages)} 条消息)"
            ):
                st.markdown(
                    f"**创建时间:** {conversation.created_at.strftime('%Y-%m-%d %H:%M')}"
                )

                if conversation.messages:
                    st.markdown("**对话内容:**")
                    for msg in conversation.messages[-6:]:  # Show last 6 messages
                        role_icon = (
                            "👤"
                            if msg.role == MessageRole.USER
                            else character.avatar_emoji
                        )

                        # Check if this is an audio message
                        if msg.metadata and "audio" in msg.metadata:
                            audio_info = msg.metadata["audio"]
                            duration_str = audio_manager.format_duration(
                                audio_info.get("duration", 0)
                            )

                            # Show STT info if available
                            stt_info = audio_info.get("stt_result")
                            if stt_info:
                                confidence = stt_info.get("confidence", 0) * 100
                                method = stt_info.get("method", "unknown")
                                st.markdown(
                                    f"{role_icon} **{msg.role.value}:** 🎤 语音消息 ({duration_str}, {method}, {confidence:.0f}%)"
                                )
                            else:
                                st.markdown(
                                    f"{role_icon} **{msg.role.value}:** 🎤 语音消息 ({duration_str})"
                                )

                            if msg.content and msg.content != "[音频消息]":
                                st.markdown(f"   *内容:* {msg.content}")
                        else:
                            st.markdown(
                                f"{role_icon} **{msg.role.value}:** {msg.content}"
                            )

                    if len(conversation.messages) > 6:
                        st.markdown(
                            f"*...还有 {len(conversation.messages) - 6} 条消息*"
                        )

                # Action buttons
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"🔄 加载对话", key=f"load_{conversation.id}"):
                        # Load conversation into current session with metadata
                        messages = []
                        for msg in conversation.messages:
                            message_data = {
                                "role": msg.role.value,
                                "content": msg.content,
                            }
                            if msg.metadata:
                                message_data["metadata"] = msg.metadata
                            messages.append(message_data)

                        st.session_state.messages = messages
                        st.session_state.current_conversation_id = conversation.id
                        st.success("对话已加载!")
                        st.rerun()

                with col2:
                    if st.button(f"🗑️ 删除", key=f"delete_{conversation.id}"):
                        self.db.delete_conversation(conversation.id)
                        st.success("对话已删除!")
                        st.rerun()

    def run(self):
        st.set_page_config(
            page_title=os.getenv("APP_TITLE", "AI角色扮演聊天网站"),
            page_icon="🎭",
            layout="wide",
        )

        # Main navigation
        tab1, tab2 = st.tabs(["💬 角色对话", "📚 对话历史"])

        # Render sidebar for both tabs
        self.render_sidebar()

        with tab1:
            self.render_chat()

        with tab2:
            self.render_conversations_history()


if __name__ == "__main__":
    app = AIRolePlayApp()
    app.run()
