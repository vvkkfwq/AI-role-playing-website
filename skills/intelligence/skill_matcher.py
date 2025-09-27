import logging
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, timedelta

from ..core.base import SkillBase
from ..core.models import SkillContext, SkillConfig, IntentClassification, SkillCategory
from .intent_classifier import IntentClassifier

logger = logging.getLogger(__name__)


class SkillMatcher:
    """
    技能匹配器 - 基于意图识别结果和上下文信息匹配最合适的技能
    """

    def __init__(self, intent_classifier: Optional[IntentClassifier] = None):
        self.intent_classifier = intent_classifier or IntentClassifier()

        # 意图到技能类别的映射
        self.intent_to_category_mapping = {
            # 对话类技能
            "deep_conversation": [SkillCategory.CONVERSATION],
            "storytelling": [SkillCategory.CONVERSATION],
            "scientific_explanation": [SkillCategory.CONVERSATION, SkillCategory.KNOWLEDGE],
            "emotional_support": [SkillCategory.CONVERSATION],
            "humor": [SkillCategory.CONVERSATION, SkillCategory.CREATIVE],

            # 知识类技能
            "fact_lookup": [SkillCategory.KNOWLEDGE],
            "analysis": [SkillCategory.KNOWLEDGE],
            "memory_recall": [SkillCategory.KNOWLEDGE],
            "comparison": [SkillCategory.KNOWLEDGE],

            # 创意类技能
            "creative_writing": [SkillCategory.CREATIVE],
            "brainstorming": [SkillCategory.CREATIVE],
            "roleplay": [SkillCategory.CREATIVE],
            "imagination": [SkillCategory.CREATIVE],

            # 实用类技能
            "translation": [SkillCategory.UTILITY],
            "summarization": [SkillCategory.UTILITY],
            "planning": [SkillCategory.UTILITY],
            "reflection": [SkillCategory.UTILITY]
        }

        # 角色到技能偏好的映射
        self.character_skill_preferences = {
            "哈利·波特": {
                "storytelling": 1.5,
                "roleplay": 1.3,
                "imagination": 1.2,
                "emotional_support": 1.1
            },
            "苏格拉底": {
                "deep_conversation": 1.5,
                "analysis": 1.4,
                "fact_lookup": 1.2,
                "reflection": 1.3
            },
            "阿尔伯特·爱因斯坦": {
                "scientific_explanation": 1.5,
                "imagination": 1.3,
                "analysis": 1.2,
                "creative_writing": 1.1
            }
        }

        # 技能冷却时间跟踪
        self._skill_cooldowns: Dict[str, datetime] = {}

    async def match_skills(
        self,
        context: SkillContext,
        available_skills: List[SkillBase],
        skill_configs: Dict[str, SkillConfig],
        max_skills: int = 3
    ) -> List[Tuple[SkillBase, SkillConfig, float]]:
        """
        匹配最合适的技能

        Args:
            context: 执行上下文
            available_skills: 可用技能列表
            skill_configs: 技能配置字典
            max_skills: 最大技能数量

        Returns:
            List[Tuple[SkillBase, SkillConfig, float]]: 匹配的技能、配置和得分列表
        """
        logger.info(f"开始技能匹配，可用技能数: {len(available_skills)}")

        # 1. 意图识别
        intent_classification = await self.intent_classifier.classify_intent(context)
        context.detected_intent = intent_classification.detected_intent
        context.intent_confidence = intent_classification.confidence

        logger.info(f"检测到意图: {intent_classification.detected_intent} (置信度: {intent_classification.confidence:.2f})")

        # 2. 基于意图筛选技能
        relevant_skills = self._filter_skills_by_intent(
            available_skills,
            intent_classification
        )

        if not relevant_skills:
            logger.warning("没有找到与意图匹配的技能")
            return []

        # 3. 计算技能得分
        skill_scores = []
        for skill in relevant_skills:
            config = skill_configs.get(skill.metadata.name, SkillConfig(skill_name=skill.metadata.name))

            # 检查技能是否能处理当前请求
            if not skill.can_handle(context, config):
                continue

            # 检查冷却时间
            if self._is_skill_in_cooldown(skill.metadata.name, config):
                continue

            # 计算综合得分
            score = await self._calculate_skill_score(
                skill,
                config,
                context,
                intent_classification
            )

            if score > 0:
                skill_scores.append((skill, config, score))

        # 4. 排序并返回top技能
        skill_scores.sort(key=lambda x: x[2], reverse=True)
        selected_skills = skill_scores[:max_skills]

        # 5. 更新冷却时间
        for skill, config, _ in selected_skills:
            self._update_skill_cooldown(skill.metadata.name, config)

        logger.info(f"匹配完成，选中技能: {[s[0].metadata.name for s in selected_skills]}")

        return selected_skills

    def _filter_skills_by_intent(
        self,
        available_skills: List[SkillBase],
        intent_classification: IntentClassification
    ) -> List[SkillBase]:
        """基于意图筛选相关技能"""
        detected_intent = intent_classification.detected_intent

        # 获取意图对应的技能类别
        relevant_categories = self.intent_to_category_mapping.get(detected_intent, [])

        if not relevant_categories:
            # 如果没有明确的类别映射，返回所有技能
            return available_skills

        # 筛选相关类别的技能
        relevant_skills = [
            skill for skill in available_skills
            if skill.metadata.category in relevant_categories
        ]

        # 如果没有找到相关技能，考虑候选意图
        if not relevant_skills and intent_classification.alternative_intents:
            for alt_intent in intent_classification.alternative_intents:
                alt_categories = self.intent_to_category_mapping.get(alt_intent["intent"], [])
                alt_skills = [
                    skill for skill in available_skills
                    if skill.metadata.category in alt_categories
                ]
                relevant_skills.extend(alt_skills)

        return list(set(relevant_skills))  # 去重

    async def _calculate_skill_score(
        self,
        skill: SkillBase,
        config: SkillConfig,
        context: SkillContext,
        intent_classification: IntentClassification
    ) -> float:
        """计算技能综合得分"""
        base_score = 0.0

        # 1. 技能基础置信度得分
        confidence_score = skill.get_confidence_score(context, config)
        base_score += confidence_score * 0.4

        # 2. 意图匹配得分
        intent_score = self._calculate_intent_match_score(
            skill,
            intent_classification
        )
        base_score += intent_score * 0.3

        # 3. 角色偏好得分
        character_score = self._calculate_character_preference_score(
            skill,
            context
        )
        base_score += character_score * 0.2

        # 4. 上下文相关性得分
        context_score = self._calculate_context_relevance_score(
            skill,
            context
        )
        base_score += context_score * 0.1

        # 5. 应用技能权重
        weighted_score = base_score * config.weight

        # 6. 检查阈值
        if weighted_score < config.threshold:
            return 0.0

        return weighted_score

    def _calculate_intent_match_score(
        self,
        skill: SkillBase,
        intent_classification: IntentClassification
    ) -> float:
        """计算意图匹配得分"""
        skill_category = skill.metadata.category
        detected_intent = intent_classification.detected_intent

        # 直接匹配
        relevant_categories = self.intent_to_category_mapping.get(detected_intent, [])
        if skill_category in relevant_categories:
            return intent_classification.confidence

        # 候选意图匹配
        for alt_intent in intent_classification.alternative_intents:
            alt_categories = self.intent_to_category_mapping.get(alt_intent["intent"], [])
            if skill_category in alt_categories:
                return alt_intent["confidence"] * 0.7

        return 0.0

    def _calculate_character_preference_score(
        self,
        skill: SkillBase,
        context: SkillContext
    ) -> float:
        """计算角色偏好得分"""
        if not context.character:
            return 0.5  # 默认得分

        character_name = context.character.get("name", "")
        if not character_name:
            return 0.5

        # 检查角色是否在技能的兼容列表中
        if skill.metadata.character_compatibility:
            if character_name not in skill.metadata.character_compatibility:
                return 0.1  # 不兼容的角色得分很低

        # 获取角色对技能的偏好
        character_preferences = self.character_skill_preferences.get(character_name, {})

        # 基于技能名称的偏好
        skill_preference = character_preferences.get(skill.metadata.name, 1.0)

        # 基于意图的偏好
        if context.detected_intent:
            intent_preference = character_preferences.get(context.detected_intent, 1.0)
            return min(skill_preference * intent_preference, 2.0) / 2.0

        return min(skill_preference, 2.0) / 2.0

    def _calculate_context_relevance_score(
        self,
        skill: SkillBase,
        context: SkillContext
    ) -> float:
        """计算上下文相关性得分"""
        score = 0.5  # 基础得分

        # 基于对话历史长度
        conversation_length = len(context.conversation_history)
        if conversation_length > 10:
            # 长对话中，偏好回忆和反思类技能
            if "memory" in skill.metadata.name.lower() or "reflection" in skill.metadata.name.lower():
                score += 0.2

        # 基于情感状态
        emotional_state = context.emotional_state
        if emotional_state:
            if emotional_state in ["sad", "anxious"] and "emotional_support" in skill.metadata.name.lower():
                score += 0.3
            elif emotional_state == "curious" and skill.metadata.category == SkillCategory.KNOWLEDGE:
                score += 0.2

        # 基于技能使用历史
        skill_history = context.skill_history
        if skill_history:
            recent_skills = [s["skill_name"] for s in skill_history[-5:]]
            # 避免重复使用相同技能
            if skill.metadata.name in recent_skills:
                score -= 0.2

        return max(0.0, min(1.0, score))

    def _is_skill_in_cooldown(self, skill_name: str, config: SkillConfig) -> bool:
        """检查技能是否在冷却期"""
        if config.cooldown_seconds <= 0:
            return False

        last_used = self._skill_cooldowns.get(skill_name)
        if not last_used:
            return False

        time_since_last_use = (datetime.now() - last_used).total_seconds()
        return time_since_last_use < config.cooldown_seconds

    def _update_skill_cooldown(self, skill_name: str, config: SkillConfig):
        """更新技能冷却时间"""
        if config.cooldown_seconds > 0:
            self._skill_cooldowns[skill_name] = datetime.now()

    def get_skill_suggestions(
        self,
        user_input: str,
        available_skills: List[SkillBase],
        character_name: Optional[str] = None,
        max_suggestions: int = 5
    ) -> List[Dict[str, Any]]:
        """
        获取技能建议（不执行技能，只提供建议）

        Args:
            user_input: 用户输入
            available_skills: 可用技能列表
            character_name: 角色名称
            max_suggestions: 最大建议数量

        Returns:
            List[Dict[str, Any]]: 技能建议列表
        """
        suggestions = []

        # 创建临时上下文
        temp_context = SkillContext(
            user_input=user_input,
            character={"name": character_name} if character_name else None,
            request_id="suggestion_request"
        )

        for skill in available_skills:
            if skill.can_handle(temp_context, SkillConfig(skill_name=skill.metadata.name)):
                confidence = skill.get_confidence_score(
                    temp_context,
                    SkillConfig(skill_name=skill.metadata.name)
                )

                # 应用角色偏好
                if character_name:
                    character_preferences = self.character_skill_preferences.get(character_name, {})
                    preference_boost = character_preferences.get(skill.metadata.name, 1.0)
                    confidence *= preference_boost

                suggestions.append({
                    "skill_name": skill.metadata.name,
                    "display_name": skill.metadata.display_name,
                    "description": skill.metadata.description,
                    "category": skill.metadata.category.value,
                    "confidence": min(confidence, 1.0),
                    "reasoning": self._generate_suggestion_reasoning(skill, temp_context)
                })

        # 按置信度排序
        suggestions.sort(key=lambda x: x["confidence"], reverse=True)
        return suggestions[:max_suggestions]

    def _generate_suggestion_reasoning(self, skill: SkillBase, context: SkillContext) -> str:
        """生成技能建议的推理说明"""
        category_descriptions = {
            SkillCategory.CONVERSATION: "适合深度对话和交流",
            SkillCategory.KNOWLEDGE: "适合知识查询和分析",
            SkillCategory.CREATIVE: "适合创意和想象力发挥",
            SkillCategory.UTILITY: "适合实用功能和工具"
        }

        category_desc = category_descriptions.get(skill.metadata.category, "通用技能")
        return f"{skill.metadata.description}，{category_desc}"

    def update_character_preferences(
        self,
        character_name: str,
        skill_preferences: Dict[str, float]
    ):
        """更新角色技能偏好"""
        if character_name not in self.character_skill_preferences:
            self.character_skill_preferences[character_name] = {}

        self.character_skill_preferences[character_name].update(skill_preferences)
        logger.info(f"更新角色 {character_name} 的技能偏好")

    def get_matching_statistics(self) -> Dict[str, Any]:
        """获取匹配统计信息"""
        return {
            "intent_mappings": len(self.intent_to_category_mapping),
            "character_preferences": len(self.character_skill_preferences),
            "active_cooldowns": len(self._skill_cooldowns),
            "supported_categories": len(SkillCategory)
        }