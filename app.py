import streamlit as st
from openai import OpenAI
import os
from typing import List, Dict
from dotenv import load_dotenv

# Import our enhanced database and models
from database import DatabaseManager
from models import Character, MessageRole

load_dotenv()


class AIRolePlayApp:
    def __init__(self):
        self.db = DatabaseManager()
        self.init_openai()
        self.init_session_state()

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
                st.warning("没有找到角色。请运行 `python init_database.py` 初始化数据库。")
                return

            character_options = {f"{char.avatar_emoji} {char.name}": char for char in characters}

            selected_display_name = st.selectbox(
                "选择一个角色开始对话",
                list(character_options.keys()),
                index=0
            )

            if selected_display_name:
                selected_character = character_options[selected_display_name]

                # Check if character changed
                if (st.session_state.selected_character is None or
                    st.session_state.selected_character.id != selected_character.id):
                    st.session_state.selected_character = selected_character
                    st.session_state.messages = []
                    st.session_state.current_conversation_id = None

                st.markdown("---")

                # Display character info
                st.markdown(f"### {selected_character.avatar_emoji} {selected_character.name}")
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
                first_user_msg = next((msg for msg in st.session_state.messages if msg["role"] == "user"), None)
                if first_user_msg:
                    title = first_user_msg["content"][:30] + ("..." if len(first_user_msg["content"]) > 30 else "")

            conversation_id = self.db.create_conversation(character.id, title)
            st.session_state.current_conversation_id = conversation_id

        # Add messages to conversation
        for message in st.session_state.messages:
            # Check if message already exists (basic deduplication)
            self.db.add_message(
                conversation_id=st.session_state.current_conversation_id,
                role=message["role"],
                content=message["content"]
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

                if role == "user":
                    with st.chat_message("user"):
                        st.markdown(content)
                elif role == "assistant":
                    with st.chat_message("assistant", avatar=character.avatar_emoji):
                        st.markdown(content)

        # Chat input
        if prompt := st.chat_input("输入你的消息..."):
            # Add user message
            st.session_state.messages.append({"role": "user", "content": prompt})

            with st.chat_message("user"):
                st.markdown(prompt)

            # Generate and add assistant response
            with st.chat_message("assistant", avatar=character.avatar_emoji):
                with st.spinner(f"{character.name}正在思考..."):
                    response = self.generate_response(
                        st.session_state.messages, character
                    )
                st.markdown(response)

            st.session_state.messages.append({"role": "assistant", "content": response})

            # Auto-save conversation periodically
            if len(st.session_state.messages) % 6 == 0:  # Save every 3 exchanges
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
            with st.expander(f"🗂️ {conversation.title} ({len(conversation.messages)} 条消息)"):
                st.markdown(f"**创建时间:** {conversation.created_at.strftime('%Y-%m-%d %H:%M')}")

                if conversation.messages:
                    st.markdown("**对话内容:**")
                    for msg in conversation.messages[-6:]:  # Show last 6 messages
                        role_icon = "👤" if msg.role == MessageRole.USER else character.avatar_emoji
                        st.markdown(f"{role_icon} **{msg.role.value}:** {msg.content}")

                    if len(conversation.messages) > 6:
                        st.markdown(f"*...还有 {len(conversation.messages) - 6} 条消息*")

                # Action buttons
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"🔄 加载对话", key=f"load_{conversation.id}"):
                        # Load conversation into current session
                        st.session_state.messages = [
                            {"role": msg.role.value, "content": msg.content}
                            for msg in conversation.messages
                        ]
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