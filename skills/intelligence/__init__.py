"""Intelligence components for skill matching and recommendation"""

from .intent_classifier import IntentClassifier
from .skill_matcher import SkillMatcher
from .recommendation_engine import RecommendationEngine

__all__ = [
    "IntentClassifier",
    "SkillMatcher", 
    "RecommendationEngine"
]