"""对话类技能模块"""

from .deep_questioning import DeepQuestioningSkill
from .storytelling import StorytellingSkill
from .emotional_support import EmotionalSupportSkill

__all__ = [
    "DeepQuestioningSkill",
    "StorytellingSkill",
    "EmotionalSupportSkill"
]