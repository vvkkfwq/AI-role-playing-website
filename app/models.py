from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class VoiceConfig(BaseModel):
    """Voice configuration for character"""
    provider: str = "openai"  # openai, azure, etc.
    voice_id: str = "alloy"  # voice identifier
    speed: float = Field(default=1.0, ge=0.25, le=4.0)  # speech speed
    pitch: float = Field(default=1.0, ge=0.5, le=2.0)  # voice pitch
    volume: float = Field(default=1.0, ge=0.0, le=1.0)  # volume level


class Character(BaseModel):
    """Enhanced Character data model with comprehensive attributes"""
    id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=100)
    title: str = Field(..., min_length=1, max_length=200)  # character description/title
    avatar_emoji: str = Field(default="🎭", max_length=10)
    personality: List[str] = Field(default_factory=list, min_items=1)  # personality traits
    prompt_template: str = Field(..., min_length=10)  # role-playing prompt template
    skills: List[str] = Field(default_factory=list)  # character skills/abilities
    voice_config: VoiceConfig = Field(default_factory=VoiceConfig)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MessageRole(str, Enum):
    """Enumeration for message roles"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(BaseModel):
    """Message model for conversations"""
    id: Optional[int] = None
    conversation_id: int
    role: MessageRole
    content: str = Field(..., min_length=1)
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Optional[Dict[str, Any]] = None  # additional message metadata

    class Config:
        from_attributes = True


class Conversation(BaseModel):
    """Conversation model linking characters and messages"""
    id: Optional[int] = None
    character_id: int
    title: Optional[str] = None  # conversation title/summary
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    messages: List[Message] = Field(default_factory=list)

    class Config:
        from_attributes = True


class CharacterCreate(BaseModel):
    """Model for creating new characters"""
    name: str = Field(..., min_length=1, max_length=100)
    title: str = Field(..., min_length=1, max_length=200)
    avatar_emoji: str = Field(default="🎭", max_length=10)
    personality: List[str] = Field(..., min_items=1)
    prompt_template: str = Field(..., min_length=10)
    skills: List[str] = Field(default_factory=list)
    voice_config: Optional[VoiceConfig] = None


class CharacterUpdate(BaseModel):
    """Model for updating existing characters"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    avatar_emoji: Optional[str] = Field(None, max_length=10)
    personality: Optional[List[str]] = None
    prompt_template: Optional[str] = Field(None, min_length=10)
    skills: Optional[List[str]] = None
    voice_config: Optional[VoiceConfig] = None