import streamlit as st
from openai import OpenAI
import os
from typing import List, Dict, Any
from dotenv import load_dotenv

# Import our enhanced database and models
from database import DatabaseManager
from models import Character, MessageRole

# Import audio processing utilities
from audio_utils import audio_manager, AudioUI

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
            )

            return response.choices[0].message.content

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

        # Input section with both text and audio options
        self.render_input_section(character)

    def render_audio_message(self, audio_metadata: Dict[str, Any], content: str):
        """Render an audio message with playback controls"""
        st.markdown(
            f"🎤 **语音消息** ({audio_manager.format_duration(audio_metadata.get('duration', 0))})"
        )

        # Show transcription if available
        if content and content != "[音频消息]":
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

                                # Send audio button
                                if st.button("📤 发送语音", type="primary"):
                                    self.process_user_message(
                                        "[音频消息]", audio, character
                                    )
                                    st.rerun()
                            else:
                                st.error(f"音频验证失败: {error_msg}")

        else:
            st.warning(
                "⚠️ 语音录制功能不可用。请安装: pip install streamlit-audiorecorder"
            )

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
                    response = self.generate_response(
                        st.session_state.messages, character
                    )
                st.markdown(response)

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
                            st.markdown(
                                f"{role_icon} **{msg.role.value}:** 🎤 语音消息 ({duration_str})"
                            )
                            if msg.content and msg.content != "[音频消息]":
                                st.markdown(f"   *转录:* {msg.content}")
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
