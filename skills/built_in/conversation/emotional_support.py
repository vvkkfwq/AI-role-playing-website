from typing import Dict, Any, List
from datetime import datetime

from ...core.base import SkillBase
from ...core.models import (
    SkillMetadata, SkillContext, SkillConfig, SkillResult,
    SkillCategory, SkillTrigger, SkillPriority
)


class EmotionalSupportSkill(SkillBase):
    """
    情感支持技能 - 提供共情和情感支持
    """

    @classmethod
    def get_metadata(cls) -> SkillMetadata:
        """获取技能元数据"""
        return SkillMetadata(
            name="emotional_support",
            display_name="情感支持",
            description="提供情感支持和共情，帮助用户处理负面情绪",
            category=SkillCategory.CONVERSATION,
            triggers=SkillTrigger(
                keywords=["难过", "伤心", "沮丧", "焦虑", "担心", "害怕", "孤独"],
                patterns=[r".*难过.*", r".*担心.*", r".*焦虑.*"],
                emotional_states=["sad", "anxious", "angry", "confused"]
            ),
            priority=SkillPriority.HIGH,
            character_compatibility=["哈利·波特", "苏格拉底"],
            max_execution_time=10.0
        )

    def can_handle(self, context: SkillContext, config: SkillConfig) -> bool:
        """判断是否能处理当前请求"""
        user_input = context.user_input.lower()

        # 检查情感关键词
        emotional_keywords = ["难过", "伤心", "沮丧", "焦虑", "担心", "害怕", "孤独", "失落"]
        has_emotional_content = any(keyword in user_input for keyword in emotional_keywords)

        # 检查情感状态
        is_negative_emotion = context.emotional_state in ["sad", "anxious", "angry", "confused"]

        return has_emotional_content or is_negative_emotion

    def get_confidence_score(self, context: SkillContext, config: SkillConfig) -> float:
        """计算技能置信度"""
        user_input = context.user_input.lower()
        score = 0.0

        # 基于情感关键词
        emotional_words = ["难过", "伤心", "沮丧", "焦虑", "担心", "害怕", "孤独"]
        matches = sum(1 for word in emotional_words if word in user_input)
        score += min(matches * 0.2, 0.6)

        # 基于情感状态
        if context.emotional_state in ["sad", "anxious", "angry"]:
            score += 0.4

        # 基于角色匹配
        if context.character and "哈利" in context.character.get("name", ""):
            score += 0.2

        return min(score, 1.0)

    async def execute(self, context: SkillContext, config: SkillConfig) -> SkillResult:
        """执行情感支持技能"""
        user_input = context.user_input
        character_name = context.character.get("name", "") if context.character else ""

        # 识别情感类型
        emotion_type = self._identify_emotion_type(user_input, context)

        # 生成支持性回应
        if "哈利" in character_name:
            response = self._generate_harry_support(emotion_type, context)
        elif "苏格拉底" in character_name:
            response = self._generate_socrates_support(emotion_type, context)
        else:
            response = self._generate_general_support(emotion_type, context)

        # 计算质量指标
        quality_score = self._calculate_quality_score(response, user_input)
        relevance_score = self._calculate_relevance_score(response, user_input, context)

        return SkillResult(
            skill_name=self.metadata.name,
            execution_id="",
            status="completed",
            generated_content=response,
            confidence_score=self.get_confidence_score(context, config),
            relevance_score=relevance_score,
            quality_score=quality_score,
            result_data={
                "emotion_type": emotion_type,
                "support_style": character_name or "general",
                "empathy_level": "high"
            }
        )

    def _identify_emotion_type(self, user_input: str, context: SkillContext) -> str:
        """识别情感类型"""
        user_input_lower = user_input.lower()

        if any(word in user_input_lower for word in ["难过", "伤心", "沮丧", "失落"]):
            return "sadness"
        elif any(word in user_input_lower for word in ["焦虑", "担心", "害怕", "紧张"]):
            return "anxiety"
        elif any(word in user_input_lower for word in ["生气", "愤怒", "恼火"]):
            return "anger"
        elif any(word in user_input_lower for word in ["孤独", "寂寞", "没人理解"]):
            return "loneliness"
        elif any(word in user_input_lower for word in ["困惑", "迷茫", "不知道"]):
            return "confusion"
        else:
            return context.emotional_state or "general"

    def _generate_harry_support(self, emotion_type: str, context: SkillContext) -> str:
        """生成哈利波特风格的情感支持"""
        responses = {
            "sadness": "我理解你现在的感受。我也曾经感到非常难过，特别是当我失去重要的人的时候。但我学到了一件事——虽然悲伤是真实的，但它不会永远持续下去。就像邓布利多说过的，'黑暗过后总会有光明'。你并不孤单，总有人关心着你。",

            "anxiety": "我知道担心的感觉，特别是面对未知的时候。每次面对伏地魔之前，我都会感到恐惧和焦虑。但我发现，和朋友分享这些感受会让我感觉好很多。你也可以试着和信任的人聊聊，有时候说出来就已经减轻了一半的负担。",

            "loneliness": "我从小就感到孤独，在德思礼家的时候，我总觉得没有人真正理解我。但后来我发现，真正的连接不在于身边有多少人，而在于有几个真正关心你的人。即使现在，我也想让你知道，你的感受是重要的，你并不孤单。",

            "confusion": "生活有时候确实很困惑，就像走在迷雾中一样。我记得有很多次我不知道该做什么决定，感觉一切都没有意义。但每次当我停下来思考，听听内心的声音，答案往往就会出现。给自己一些时间，答案会来的。"
        }

        return responses.get(emotion_type, "我能感受到你现在的感受。记住，即使在最黑暗的时候，也总有希望的光芒。你比你想象的更强大，而且你不是一个人在战斗。")

    def _generate_socrates_support(self, emotion_type: str, context: SkillContext) -> str:
        """生成苏格拉底风格的情感支持"""
        responses = {
            "sadness": "你感到悲伤，这表明你内心深处有所牵挂，有所珍视。让我问你：如果一个人从不感到悲伤，这意味着什么？也许悲伤正是我们人性的体现，是我们能够爱的证明。虽然痛苦，但它也提醒我们什么是真正重要的。",

            "anxiety": "焦虑常常来自于对未来的担忧。但让我们思考一下：我们能控制的是什么？是过去已经发生的事，还是尚未到来的未来？还是此时此刻的我们自己？也许真正的平静来自于专注于我们能够掌控的东西。",

            "confusion": "困惑是智慧的开始，我的朋友。当我们不再困惑时，可能就停止了思考。你的困惑说明你在认真对待生活，在寻找真正的答案。这难道不是值得赞赏的吗？让我们一起探索这个困惑，也许其中隐藏着重要的真理。"
        }

        return responses.get(emotion_type, "情感是人类最真实的体验。你愿意和我一起探讨这种感受吗？有时候，理解我们的情感比消除它们更重要。")

    def _generate_general_support(self, emotion_type: str, context: SkillContext) -> str:
        """生成通用的情感支持"""
        responses = {
            "sadness": "我能理解你现在的感受。悲伤是人类情感的一部分，它提醒我们什么对我们来说是重要的。虽然现在很痛苦，但请记住，这种感受会过去的。你并不孤单，总有人愿意倾听和支持你。",

            "anxiety": "焦虑让人很不舒服，我理解。但请记住，大多数我们担心的事情都不会发生。试着专注于现在这一刻，深深呼吸，告诉自己你能够处理遇到的挑战。",

            "loneliness": "孤独是一种很深的感受，让人觉得与世界失去了连接。但请记住，即使在最孤独的时刻，也有人关心着你。有时候，主动向别人伸出手，也会帮助我们重新建立连接。"
        }

        return responses.get(emotion_type, "我听到了你的感受，这些感受都是真实和重要的。记住，寻求帮助是勇敢的表现，不是软弱。")

    def _calculate_quality_score(self, response: str, user_input: str) -> float:
        """计算回应质量得分"""
        score = 0.0

        # 基于共情词汇
        empathy_words = ["理解", "感受", "知道", "明白"]
        empathy_count = sum(1 for word in empathy_words if word in response)
        score += min(empathy_count * 0.15, 0.4)

        # 基于支持性语言
        support_words = ["不孤单", "关心", "支持", "帮助", "陪伴"]
        support_count = sum(1 for word in support_words if word in response)
        score += min(support_count * 0.1, 0.3)

        # 基于积极性
        positive_words = ["希望", "光明", "强大", "可以", "能够"]
        positive_count = sum(1 for word in positive_words if word in response)
        score += min(positive_count * 0.1, 0.3)

        return min(score, 1.0)

    def _calculate_relevance_score(self, response: str, user_input: str, context: SkillContext) -> float:
        """计算相关性得分"""
        score = 0.8  # 情感支持通常都比较相关

        # 检查是否回应了具体的情感
        user_emotions = ["难过", "担心", "焦虑", "害怕", "孤独"]
        mentioned_emotions = [emotion for emotion in user_emotions if emotion in user_input.lower()]

        if mentioned_emotions:
            for emotion in mentioned_emotions:
                if emotion in response:
                    score += 0.1

        return min(score, 1.0)