"""
AI Role-Playing Skill System

A comprehensive skill management system for AI characters featuring:
- Intelligent skill discovery and registration
- Context-aware skill matching and execution
- Performance monitoring and optimization
- Extensible SDK for custom skill development
"""

from .core.manager import SkillManager
from .core.base import SkillBase, SkillResult
from .core.models import SkillMetadata, SkillConfig, SkillContext
from .core.registry import SkillRegistry

__version__ = "1.0.0"
__all__ = [
    "SkillManager",
    "SkillBase",
    "SkillResult",
    "SkillMetadata",
    "SkillConfig",
    "SkillContext",
    "SkillRegistry"
]