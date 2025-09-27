import sqlite3
import json
import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from contextlib import contextmanager

from app.models import Character, Conversation, Message, CharacterCreate, CharacterUpdate, VoiceConfig


class DatabaseManager:
    """Enhanced database manager with comprehensive CRUD operations"""

    def __init__(self, db_path: str = "data/roleplay.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize database with all required tables"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            # Enable foreign key constraints
            conn.execute("PRAGMA foreign_keys = ON")

            # Create characters table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS characters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    avatar_emoji TEXT DEFAULT '🎭',
                    personality TEXT NOT NULL,  -- JSON array of traits
                    prompt_template TEXT NOT NULL,
                    skills TEXT DEFAULT '[]',  -- JSON array of skills
                    voice_config TEXT DEFAULT '{}',  -- JSON voice configuration
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create conversations table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    character_id INTEGER NOT NULL,
                    title TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (character_id) REFERENCES characters (id) ON DELETE CASCADE
                )
            """)

            # Create messages table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id INTEGER NOT NULL,
                    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT DEFAULT '{}',  -- JSON metadata
                    FOREIGN KEY (conversation_id) REFERENCES conversations (id) ON DELETE CASCADE
                )
            """)

            # Create indexes for better performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_conversations_character_id ON conversations(character_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp)")

            conn.commit()

    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    # Character CRUD Operations
    def create_character(self, character_data: CharacterCreate) -> Character:
        """Create a new character"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO characters (
                    name, title, avatar_emoji, personality, prompt_template,
                    skills, voice_config, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                character_data.name,
                character_data.title,
                character_data.avatar_emoji,
                json.dumps(character_data.personality, ensure_ascii=False),
                character_data.prompt_template,
                json.dumps(character_data.skills, ensure_ascii=False),
                json.dumps(character_data.voice_config.dict() if character_data.voice_config else {}, ensure_ascii=False),
                datetime.now(),
                datetime.now()
            ))

            character_id = cursor.lastrowid
            conn.commit()

            return self.get_character_by_id(character_id)

    def get_character_by_id(self, character_id: int) -> Optional[Character]:
        """Get character by ID"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM characters WHERE id = ?",
                (character_id,)
            )
            row = cursor.fetchone()

            if row:
                return self._row_to_character(row)
            return None

    def get_character_by_name(self, name: str) -> Optional[Character]:
        """Get character by name"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM characters WHERE name = ?",
                (name,)
            )
            row = cursor.fetchone()

            if row:
                return self._row_to_character(row)
            return None

    def get_all_characters(self) -> List[Character]:
        """Get all characters"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM characters ORDER BY created_at DESC"
            )
            rows = cursor.fetchall()

            return [self._row_to_character(row) for row in rows]

    def update_character(self, character_id: int, character_data: CharacterUpdate) -> Optional[Character]:
        """Update an existing character"""
        update_fields = []
        update_values = []

        if character_data.name is not None:
            update_fields.append("name = ?")
            update_values.append(character_data.name)
        if character_data.title is not None:
            update_fields.append("title = ?")
            update_values.append(character_data.title)
        if character_data.avatar_emoji is not None:
            update_fields.append("avatar_emoji = ?")
            update_values.append(character_data.avatar_emoji)
        if character_data.personality is not None:
            update_fields.append("personality = ?")
            update_values.append(json.dumps(character_data.personality, ensure_ascii=False))
        if character_data.prompt_template is not None:
            update_fields.append("prompt_template = ?")
            update_values.append(character_data.prompt_template)
        if character_data.skills is not None:
            update_fields.append("skills = ?")
            update_values.append(json.dumps(character_data.skills, ensure_ascii=False))
        if character_data.voice_config is not None:
            update_fields.append("voice_config = ?")
            update_values.append(json.dumps(character_data.voice_config.dict(), ensure_ascii=False))

        if not update_fields:
            return self.get_character_by_id(character_id)

        update_fields.append("updated_at = ?")
        update_values.append(datetime.now())
        update_values.append(character_id)

        with self.get_connection() as conn:
            conn.execute(
                f"UPDATE characters SET {', '.join(update_fields)} WHERE id = ?",
                update_values
            )
            conn.commit()

            return self.get_character_by_id(character_id)

    def delete_character(self, character_id: int) -> bool:
        """Delete a character and all related conversations"""
        with self.get_connection() as conn:
            cursor = conn.execute("DELETE FROM characters WHERE id = ?", (character_id,))
            conn.commit()
            return cursor.rowcount > 0

    # Conversation CRUD Operations
    def create_conversation(self, character_id: int, title: Optional[str] = None) -> int:
        """Create a new conversation"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO conversations (character_id, title, created_at, updated_at)
                VALUES (?, ?, ?, ?)
            """, (character_id, title, datetime.now(), datetime.now()))

            conversation_id = cursor.lastrowid
            conn.commit()
            return conversation_id

    def get_conversation_by_id(self, conversation_id: int) -> Optional[Conversation]:
        """Get conversation with all messages"""
        with self.get_connection() as conn:
            # Get conversation info
            cursor = conn.execute(
                "SELECT * FROM conversations WHERE id = ?",
                (conversation_id,)
            )
            conv_row = cursor.fetchone()

            if not conv_row:
                return None

            # Get all messages for this conversation
            cursor = conn.execute("""
                SELECT * FROM messages
                WHERE conversation_id = ?
                ORDER BY timestamp ASC
            """, (conversation_id,))
            message_rows = cursor.fetchall()

            messages = [self._row_to_message(row) for row in message_rows]

            return Conversation(
                id=conv_row['id'],
                character_id=conv_row['character_id'],
                title=conv_row['title'],
                created_at=datetime.fromisoformat(conv_row['created_at']),
                updated_at=datetime.fromisoformat(conv_row['updated_at']),
                messages=messages
            )

    def get_conversations_by_character(self, character_id: int) -> List[Conversation]:
        """Get all conversations for a character"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM conversations
                WHERE character_id = ?
                ORDER BY updated_at DESC
            """, (character_id,))
            rows = cursor.fetchall()

            conversations = []
            for row in rows:
                conv = self.get_conversation_by_id(row['id'])
                if conv:
                    conversations.append(conv)

            return conversations

    # Message CRUD Operations
    def add_message(self, conversation_id: int, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> int:
        """Add a message to a conversation"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO messages (conversation_id, role, content, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (
                conversation_id,
                role,
                content,
                datetime.now(),
                json.dumps(metadata or {}, ensure_ascii=False)
            ))

            message_id = cursor.lastrowid

            # Update conversation timestamp
            conn.execute(
                "UPDATE conversations SET updated_at = ? WHERE id = ?",
                (datetime.now(), conversation_id)
            )

            conn.commit()
            return message_id

    def delete_conversation(self, conversation_id: int) -> bool:
        """Delete a conversation and all its messages"""
        with self.get_connection() as conn:
            cursor = conn.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
            conn.commit()
            return cursor.rowcount > 0

    # Helper methods
    def _row_to_character(self, row: sqlite3.Row) -> Character:
        """Convert database row to Character object"""
        voice_config_data = json.loads(row['voice_config']) if row['voice_config'] else {}

        return Character(
            id=row['id'],
            name=row['name'],
            title=row['title'],
            avatar_emoji=row['avatar_emoji'],
            personality=json.loads(row['personality']),
            prompt_template=row['prompt_template'],
            skills=json.loads(row['skills']),
            voice_config=VoiceConfig(**voice_config_data),
            created_at=datetime.fromisoformat(row['created_at']),
            updated_at=datetime.fromisoformat(row['updated_at'])
        )

    def _row_to_message(self, row: sqlite3.Row) -> Message:
        """Convert database row to Message object"""
        return Message(
            id=row['id'],
            conversation_id=row['conversation_id'],
            role=row['role'],
            content=row['content'],
            timestamp=datetime.fromisoformat(row['timestamp']),
            metadata=json.loads(row['metadata']) if row['metadata'] else {}
        )