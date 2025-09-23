import streamlit as st
from openai import OpenAI
import sqlite3
import os
from datetime import datetime
from typing import List, Dict
from dotenv import load_dotenv
from pydantic import BaseModel
import json

load_dotenv()


class Message(BaseModel):
    role: str
    content: str
    timestamp: datetime


class Character(BaseModel):
    name: str
    description: str
    personality: str
    avatar: str = ""


class DatabaseManager:
    def __init__(self, db_path: str = "data/roleplay.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS characters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT NOT NULL,
                    personality TEXT NOT NULL,
                    avatar TEXT DEFAULT ''
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    character_id INTEGER,
                    messages TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (character_id) REFERENCES characters (id)
                )
            """
            )

            self.populate_default_characters()

    def populate_default_characters(self):
        default_characters = [
            {
                "name": "艾莉娅",
                "description": "一位聪明优雅的精灵法师，拥有千年的智慧",
                "personality": "温和、智慧、神秘，喜欢用诗意的语言交流",
            },
            {
                "name": "雷克斯",
                "description": "勇敢的人类骑士，致力于保护弱者",
                "personality": "正义、勇敢、直率，说话简洁有力",
            },
            {
                "name": "小雪",
                "description": "活泼可爱的狐妖少女，天真烂漫",
                "personality": "天真、活泼、好奇心强，经常使用可爱的语气",
            },
        ]

        with sqlite3.connect(self.db_path) as conn:
            for char in default_characters:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO characters (name, description, personality)
                    VALUES (?, ?, ?)
                """,
                    (char["name"], char["description"], char["personality"]),
                )

    def get_characters(self) -> List[Character]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT name, description, personality, avatar FROM characters"
            )
            return [
                Character(
                    name=row[0], description=row[1], personality=row[2], avatar=row[3]
                )
                for row in cursor.fetchall()
            ]

    def save_conversation(self, character_name: str, messages: List[Dict]):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT id FROM characters WHERE name = ?", (character_name,)
            )
            character_id = cursor.fetchone()[0]

            conn.execute(
                """
                INSERT INTO conversations (character_id, messages)
                VALUES (?, ?)
            """,
                (character_id, json.dumps(messages, ensure_ascii=False)),
            )


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

    def get_character_prompt(self, character: Character) -> str:
        return f"""你现在要扮演{character.name}。

角色描述：{character.description}

性格特点：{character.personality}

请严格按照这个角色的性格和背景来回应，保持角色的一致性。用中文回复，语言风格要符合角色设定。"""

    def generate_response(self, messages: List[Dict], character: Character) -> str:
        try:
            system_prompt = self.get_character_prompt(character)

            formatted_messages = [{"role": "system", "content": system_prompt}]
            formatted_messages.extend(messages)

            response = self.client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL"),
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

            characters = self.db.get_characters()
            character_names = [char.name for char in characters]

            selected_name = st.selectbox(
                "选择一个角色开始对话",
                character_names,
                index=0 if character_names else None,
            )

            if selected_name:
                selected_character = next(
                    char for char in characters if char.name == selected_name
                )

                if st.session_state.selected_character != selected_character:
                    st.session_state.selected_character = selected_character
                    st.session_state.messages = []

                st.markdown("---")
                st.markdown(f"**{selected_character.name}**")
                st.markdown(selected_character.description)
                st.markdown(f"*性格：{selected_character.personality}*")

                if st.button("🗑️ 清空对话", type="secondary"):
                    st.session_state.messages = []
                    st.rerun()

    def render_chat(self):
        if not st.session_state.selected_character:
            st.info("请在左侧选择一个角色开始对话")
            return

        character = st.session_state.selected_character
        st.title(f"💬 与 {character.name} 对话")

        chat_container = st.container()

        with chat_container:
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

        if prompt := st.chat_input("输入你的消息..."):
            st.session_state.messages.append({"role": "user", "content": prompt})

            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner(f"{character.name}正在思考..."):
                    response = self.generate_response(
                        st.session_state.messages, character
                    )
                st.markdown(response)

            st.session_state.messages.append({"role": "assistant", "content": response})

            if len(st.session_state.messages) > 20:
                self.db.save_conversation(character.name, st.session_state.messages)

    def run(self):
        st.set_page_config(
            page_title=os.getenv("APP_TITLE", "AI角色扮演聊天网站"),
            page_icon="🎭",
            layout="wide",
        )

        self.render_sidebar()
        self.render_chat()


if __name__ == "__main__":
    app = AIRolePlayApp()
    app.run()
