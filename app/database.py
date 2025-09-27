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

            # Create skill executions table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS skill_executions (
                    id TEXT PRIMARY KEY,  -- UUID
                    skill_name TEXT NOT NULL,
                    character_id INTEGER,
                    conversation_id INTEGER,
                    message_id INTEGER,
                    status TEXT NOT NULL CHECK (status IN ('pending', 'running', 'completed', 'failed', 'timeout', 'cancelled')),
                    progress REAL DEFAULT 0.0,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    execution_time REAL,
                    result_data TEXT DEFAULT '{}',  -- JSON result data
                    performance_metrics TEXT DEFAULT '{}',  -- JSON performance metrics
                    error_message TEXT,
                    error_code TEXT,
                    FOREIGN KEY (character_id) REFERENCES characters (id) ON DELETE SET NULL,
                    FOREIGN KEY (conversation_id) REFERENCES conversations (id) ON DELETE CASCADE,
                    FOREIGN KEY (message_id) REFERENCES messages (id) ON DELETE CASCADE
                )
            """)

            # Create character skill configs table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS character_skill_configs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    character_id INTEGER NOT NULL,
                    skill_name TEXT NOT NULL,
                    parameters TEXT DEFAULT '{}',  -- JSON parameters
                    weight REAL DEFAULT 1.0,
                    threshold REAL DEFAULT 0.5,
                    priority TEXT DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'critical')),
                    personalization TEXT DEFAULT '{}',  -- JSON personalization settings
                    response_style TEXT DEFAULT '{}',  -- JSON response style
                    enabled BOOLEAN DEFAULT 1,
                    max_uses_per_conversation INTEGER,
                    cooldown_seconds REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (character_id) REFERENCES characters (id) ON DELETE CASCADE,
                    UNIQUE(character_id, skill_name)
                )
            """)

            # Create skill performance metrics table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS skill_performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    skill_name TEXT NOT NULL,
                    character_id INTEGER,
                    total_executions INTEGER DEFAULT 0,
                    successful_executions INTEGER DEFAULT 0,
                    failed_executions INTEGER DEFAULT 0,
                    average_execution_time REAL DEFAULT 0.0,
                    min_execution_time REAL DEFAULT 0.0,
                    max_execution_time REAL DEFAULT 0.0,
                    average_confidence_score REAL DEFAULT 0.0,
                    average_relevance_score REAL DEFAULT 0.0,
                    average_quality_score REAL DEFAULT 0.0,
                    user_satisfaction_score REAL DEFAULT 0.0,
                    positive_feedback_count INTEGER DEFAULT 0,
                    negative_feedback_count INTEGER DEFAULT 0,
                    daily_usage_count TEXT DEFAULT '{}',  -- JSON daily usage stats
                    peak_usage_time TEXT,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    measurement_period_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    measurement_period_end TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (character_id) REFERENCES characters (id) ON DELETE CASCADE,
                    UNIQUE(skill_name, character_id)
                )
            """)

            # Create indexes for better performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_conversations_character_id ON conversations(character_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp)")

            # Skill-related indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_skill_executions_skill_name ON skill_executions(skill_name)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_skill_executions_character_id ON skill_executions(character_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_skill_executions_conversation_id ON skill_executions(conversation_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_skill_executions_started_at ON skill_executions(started_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_character_skill_configs_character_id ON character_skill_configs(character_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_skill_performance_metrics_skill_name ON skill_performance_metrics(skill_name)")

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

    # Skill Execution CRUD Operations
    def create_skill_execution(self, execution_data: Dict[str, Any]) -> str:
        """Create a new skill execution record"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO skill_executions (
                    id, skill_name, character_id, conversation_id, message_id,
                    status, progress, started_at, result_data, performance_metrics
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                execution_data.get('id'),
                execution_data.get('skill_name'),
                execution_data.get('character_id'),
                execution_data.get('conversation_id'),
                execution_data.get('message_id'),
                execution_data.get('status', 'pending'),
                execution_data.get('progress', 0.0),
                execution_data.get('started_at', datetime.now()),
                json.dumps(execution_data.get('result_data', {}), ensure_ascii=False),
                json.dumps(execution_data.get('performance_metrics', {}), ensure_ascii=False)
            ))

            conn.commit()
            return execution_data.get('id')

    def update_skill_execution(self, execution_id: str, update_data: Dict[str, Any]) -> bool:
        """Update skill execution record"""
        with self.get_connection() as conn:
            update_fields = []
            update_values = []

            for field in ['status', 'progress', 'completed_at', 'execution_time', 'result_data',
                         'performance_metrics', 'error_message', 'error_code']:
                if field in update_data:
                    update_fields.append(f"{field} = ?")
                    if field in ['result_data', 'performance_metrics']:
                        update_values.append(json.dumps(update_data[field], ensure_ascii=False))
                    else:
                        update_values.append(update_data[field])

            if not update_fields:
                return False

            update_values.append(execution_id)
            query = f"UPDATE skill_executions SET {', '.join(update_fields)} WHERE id = ?"

            cursor = conn.execute(query, update_values)
            conn.commit()
            return cursor.rowcount > 0

    def get_skill_execution(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get skill execution by ID"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM skill_executions WHERE id = ?",
                (execution_id,)
            )
            row = cursor.fetchone()

            if row:
                return self._row_to_skill_execution(row)
            return None

    def get_skill_executions_by_conversation(self, conversation_id: int) -> List[Dict[str, Any]]:
        """Get all skill executions for a conversation"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM skill_executions
                WHERE conversation_id = ?
                ORDER BY started_at DESC
            """, (conversation_id,))
            rows = cursor.fetchall()

            return [self._row_to_skill_execution(row) for row in rows]

    def get_skill_executions_by_character(self, character_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        """Get skill executions for a character"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM skill_executions
                WHERE character_id = ?
                ORDER BY started_at DESC
                LIMIT ?
            """, (character_id, limit))
            rows = cursor.fetchall()

            return [self._row_to_skill_execution(row) for row in rows]

    # Character Skill Config CRUD Operations
    def create_character_skill_config(self, config_data: Dict[str, Any]) -> int:
        """Create character skill configuration"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT OR REPLACE INTO character_skill_configs (
                    character_id, skill_name, parameters, weight, threshold, priority,
                    personalization, response_style, enabled, max_uses_per_conversation,
                    cooldown_seconds, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                config_data.get('character_id'),
                config_data.get('skill_name'),
                json.dumps(config_data.get('parameters', {}), ensure_ascii=False),
                config_data.get('weight', 1.0),
                config_data.get('threshold', 0.5),
                config_data.get('priority', 'medium'),
                json.dumps(config_data.get('personalization', {}), ensure_ascii=False),
                json.dumps(config_data.get('response_style', {}), ensure_ascii=False),
                config_data.get('enabled', True),
                config_data.get('max_uses_per_conversation'),
                config_data.get('cooldown_seconds', 0.0),
                datetime.now(),
                datetime.now()
            ))

            config_id = cursor.lastrowid
            conn.commit()
            return config_id

    def get_character_skill_configs(self, character_id: int) -> List[Dict[str, Any]]:
        """Get all skill configurations for a character"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM character_skill_configs
                WHERE character_id = ?
                ORDER BY skill_name
            """, (character_id,))
            rows = cursor.fetchall()

            return [self._row_to_skill_config(row) for row in rows]

    def get_character_skill_config(self, character_id: int, skill_name: str) -> Optional[Dict[str, Any]]:
        """Get specific skill configuration for a character"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM character_skill_configs
                WHERE character_id = ? AND skill_name = ?
            """, (character_id, skill_name))
            row = cursor.fetchone()

            if row:
                return self._row_to_skill_config(row)
            return None

    def update_character_skill_config(self, character_id: int, skill_name: str, update_data: Dict[str, Any]) -> bool:
        """Update character skill configuration"""
        with self.get_connection() as conn:
            update_fields = []
            update_values = []

            for field in ['parameters', 'weight', 'threshold', 'priority', 'personalization',
                         'response_style', 'enabled', 'max_uses_per_conversation', 'cooldown_seconds']:
                if field in update_data:
                    update_fields.append(f"{field} = ?")
                    if field in ['parameters', 'personalization', 'response_style']:
                        update_values.append(json.dumps(update_data[field], ensure_ascii=False))
                    else:
                        update_values.append(update_data[field])

            if not update_fields:
                return False

            update_fields.append("updated_at = ?")
            update_values.extend([datetime.now(), character_id, skill_name])

            query = f"UPDATE character_skill_configs SET {', '.join(update_fields)} WHERE character_id = ? AND skill_name = ?"

            cursor = conn.execute(query, update_values)
            conn.commit()
            return cursor.rowcount > 0

    # Skill Performance Metrics CRUD Operations
    def create_or_update_skill_metrics(self, metrics_data: Dict[str, Any]) -> int:
        """Create or update skill performance metrics"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT OR REPLACE INTO skill_performance_metrics (
                    skill_name, character_id, total_executions, successful_executions,
                    failed_executions, average_execution_time, min_execution_time,
                    max_execution_time, average_confidence_score, average_relevance_score,
                    average_quality_score, user_satisfaction_score, positive_feedback_count,
                    negative_feedback_count, daily_usage_count, peak_usage_time,
                    last_updated, measurement_period_start, measurement_period_end
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metrics_data.get('skill_name'),
                metrics_data.get('character_id'),
                metrics_data.get('total_executions', 0),
                metrics_data.get('successful_executions', 0),
                metrics_data.get('failed_executions', 0),
                metrics_data.get('average_execution_time', 0.0),
                metrics_data.get('min_execution_time', 0.0),
                metrics_data.get('max_execution_time', 0.0),
                metrics_data.get('average_confidence_score', 0.0),
                metrics_data.get('average_relevance_score', 0.0),
                metrics_data.get('average_quality_score', 0.0),
                metrics_data.get('user_satisfaction_score', 0.0),
                metrics_data.get('positive_feedback_count', 0),
                metrics_data.get('negative_feedback_count', 0),
                json.dumps(metrics_data.get('daily_usage_count', {}), ensure_ascii=False),
                metrics_data.get('peak_usage_time'),
                datetime.now(),
                metrics_data.get('measurement_period_start', datetime.now()),
                metrics_data.get('measurement_period_end', datetime.now())
            ))

            metrics_id = cursor.lastrowid
            conn.commit()
            return metrics_id

    def get_skill_metrics(self, skill_name: str, character_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Get skill performance metrics"""
        with self.get_connection() as conn:
            if character_id:
                cursor = conn.execute("""
                    SELECT * FROM skill_performance_metrics
                    WHERE skill_name = ? AND character_id = ?
                """, (skill_name, character_id))
            else:
                cursor = conn.execute("""
                    SELECT * FROM skill_performance_metrics
                    WHERE skill_name = ? AND character_id IS NULL
                """, (skill_name,))

            row = cursor.fetchone()
            if row:
                return self._row_to_skill_metrics(row)
            return None

    def get_all_skill_metrics(self, character_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get all skill performance metrics"""
        with self.get_connection() as conn:
            if character_id:
                cursor = conn.execute("""
                    SELECT * FROM skill_performance_metrics
                    WHERE character_id = ?
                    ORDER BY skill_name
                """, (character_id,))
            else:
                cursor = conn.execute("""
                    SELECT * FROM skill_performance_metrics
                    ORDER BY skill_name
                """)

            rows = cursor.fetchall()
            return [self._row_to_skill_metrics(row) for row in rows]

    # Helper methods for skill data conversion
    def _row_to_skill_execution(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Convert database row to skill execution dict"""
        return {
            'id': row['id'],
            'skill_name': row['skill_name'],
            'character_id': row['character_id'],
            'conversation_id': row['conversation_id'],
            'message_id': row['message_id'],
            'status': row['status'],
            'progress': row['progress'],
            'started_at': datetime.fromisoformat(row['started_at']) if row['started_at'] else None,
            'completed_at': datetime.fromisoformat(row['completed_at']) if row['completed_at'] else None,
            'execution_time': row['execution_time'],
            'result_data': json.loads(row['result_data']) if row['result_data'] else {},
            'performance_metrics': json.loads(row['performance_metrics']) if row['performance_metrics'] else {},
            'error_message': row['error_message'],
            'error_code': row['error_code']
        }

    def _row_to_skill_config(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Convert database row to skill config dict"""
        return {
            'id': row['id'],
            'character_id': row['character_id'],
            'skill_name': row['skill_name'],
            'parameters': json.loads(row['parameters']) if row['parameters'] else {},
            'weight': row['weight'],
            'threshold': row['threshold'],
            'priority': row['priority'],
            'personalization': json.loads(row['personalization']) if row['personalization'] else {},
            'response_style': json.loads(row['response_style']) if row['response_style'] else {},
            'enabled': bool(row['enabled']),
            'max_uses_per_conversation': row['max_uses_per_conversation'],
            'cooldown_seconds': row['cooldown_seconds'],
            'created_at': datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            'updated_at': datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
        }

    def _row_to_skill_metrics(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Convert database row to skill metrics dict"""
        return {
            'id': row['id'],
            'skill_name': row['skill_name'],
            'character_id': row['character_id'],
            'total_executions': row['total_executions'],
            'successful_executions': row['successful_executions'],
            'failed_executions': row['failed_executions'],
            'average_execution_time': row['average_execution_time'],
            'min_execution_time': row['min_execution_time'],
            'max_execution_time': row['max_execution_time'],
            'average_confidence_score': row['average_confidence_score'],
            'average_relevance_score': row['average_relevance_score'],
            'average_quality_score': row['average_quality_score'],
            'user_satisfaction_score': row['user_satisfaction_score'],
            'positive_feedback_count': row['positive_feedback_count'],
            'negative_feedback_count': row['negative_feedback_count'],
            'daily_usage_count': json.loads(row['daily_usage_count']) if row['daily_usage_count'] else {},
            'peak_usage_time': row['peak_usage_time'],
            'last_updated': datetime.fromisoformat(row['last_updated']) if row['last_updated'] else None,
            'measurement_period_start': datetime.fromisoformat(row['measurement_period_start']) if row['measurement_period_start'] else None,
            'measurement_period_end': datetime.fromisoformat(row['measurement_period_end']) if row['measurement_period_end'] else None
        }