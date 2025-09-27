import re
from typing import Dict, Any, List
from datetime import datetime

from ...core.base import SkillBase
from ...core.models import (
    SkillMetadata, SkillContext, SkillConfig, SkillResult,
    SkillCategory, SkillTrigger, SkillPriority
)


class DeepQuestioningSkill(SkillBase):
    """
    深度提问技能 - 苏格拉底式提问，引导用户深入思考
    """

    @classmethod
    def get_metadata(cls) -> SkillMetadata:
        """获取技能元数据"""
        return SkillMetadata(
            name="deep_questioning",
            display_name="深度提问",
            description="通过苏格拉底式提问方法，引导用户深入思考问题的本质和内在逻辑",
            category=SkillCategory.CONVERSATION,
            triggers=SkillTrigger(
                keywords=["为什么", "如何", "怎么", "原理", "本质", "深入", "思考"],
                patterns=[r".*为什么.*", r".*如何.*", r".*怎么.*", r".*原理.*"],
                intent_types=["deep_conversation", "analysis"],
                emotional_states=["curious", "confused"]
            ),
            priority=SkillPriority.HIGH,
            character_compatibility=["苏格拉底", "阿尔伯特·爱因斯坦"],
            max_execution_time=15.0
        )

    def can_handle(self, context: SkillContext, config: SkillConfig) -> bool:
        """判断是否能处理当前请求"""
        user_input = context.user_input.lower()

        # 检查是否包含疑问词
        question_indicators = ["为什么", "如何", "怎么", "原理", "本质", "深入", "为何", "何以"]
        has_question = any(indicator in user_input for indicator in question_indicators)

        # 检查是否是问号结尾
        ends_with_question = user_input.rstrip().endswith('?') or user_input.rstrip().endswith('？')

        # 检查字符长度，避免处理过短的输入
        is_substantial = len(user_input.strip()) >= 5

        return (has_question or ends_with_question) and is_substantial

    def get_confidence_score(self, context: SkillContext, config: SkillConfig) -> float:
        """计算技能置信度"""
        user_input = context.user_input.lower()
        score = 0.0

        # 基于关键词匹配
        question_words = ["为什么", "如何", "怎么", "原理", "本质", "深入", "为何"]
        matches = sum(1 for word in question_words if word in user_input)
        score += min(matches * 0.2, 0.6)

        # 基于问号
        if user_input.rstrip().endswith(('?', '？')):
            score += 0.3

        # 基于角色匹配
        if context.character and "苏格拉底" in context.character.get("name", ""):
            score += 0.2

        # 基于上下文
        if context.detected_intent == "deep_conversation":
            score += 0.3

        return min(score, 1.0)

    async def execute(self, context: SkillContext, config: SkillConfig) -> SkillResult:
        """执行深度提问技能"""
        user_input = context.user_input
        character_name = context.character.get("name", "") if context.character else ""

        # 分析用户问题的类型
        question_type = self._analyze_question_type(user_input)

        # 根据角色和问题类型生成回应
        if "苏格拉底" in character_name:
            response = self._generate_socratic_response(user_input, question_type, context)
        elif "爱因斯坦" in character_name:
            response = self._generate_einstein_response(user_input, question_type, context)
        else:
            response = self._generate_general_response(user_input, question_type, context)

        # 计算质量指标
        quality_score = self._calculate_quality_score(response, user_input)
        relevance_score = self._calculate_relevance_score(response, user_input, context)

        return SkillResult(
            skill_name=self.metadata.name,
            execution_id="",  # 会被执行器设置
            status="completed",  # 会被基类设置
            generated_content=response,
            confidence_score=self.get_confidence_score(context, config),
            relevance_score=relevance_score,
            quality_score=quality_score,
            result_data={
                "question_type": question_type,
                "character_style": "socratic" if "苏格拉底" in character_name else "general",
                "word_count": len(response)
            }
        )

    def _analyze_question_type(self, user_input: str) -> str:
        """分析问题类型"""
        user_input_lower = user_input.lower()

        if any(word in user_input_lower for word in ["为什么", "为何", "原因", "why"]):
            return "causal"  # 因果关系
        elif any(word in user_input_lower for word in ["如何", "怎么", "方法", "how"]):
            return "procedural"  # 程序性
        elif any(word in user_input_lower for word in ["是什么", "定义", "本质", "what"]):
            return "definitional"  # 定义性
        elif any(word in user_input_lower for word in ["哪个", "which", "选择"]):
            return "comparative"  # 比较性
        else:
            return "exploratory"  # 探索性

    def _generate_socratic_response(self, user_input: str, question_type: str, context: SkillContext) -> str:
        """生成苏格拉底式回应"""
        templates = {
            "causal": [
                "让我们先思考一下，当你问'{question}'时，你是否已经考虑过可能的原因？你认为最重要的因素是什么？",
                "这是一个很好的问题。在寻找答案之前，我想问你：你是否注意到这个现象背后可能存在多个层面的原因？",
                "'{question}' - 这让我想起一个问题：我们是在寻找直接原因，还是在探寻更深层的根本原因？你觉得这两者有什么区别？"
            ],
            "procedural": [
                "你问的是方法，这很好。但让我们先退一步思考：你认为找到正确方法的关键在于什么？",
                "在我回答'{question}'之前，我想了解你的想法：你已经尝试过哪些方法？它们为什么没有成功？",
                "方法很重要，但更重要的是理解为什么这个方法有效。你能想象一下理想的解决方案应该具备什么特征吗？"
            ],
            "definitional": [
                "你寻求定义，这表明你在认真思考。让我反问你：如果你要向一个孩子解释这个概念，你会怎么说？",
                "定义往往比我们想象的更复杂。关于'{question}'，你认为最核心的特征是什么？",
                "有趣的是，我们经常使用一些概念却很少深入思考它们的本质。你觉得理解一个概念的真正含义重要吗？"
            ],
            "comparative": [
                "你在比较选择，这说明你在思考。让我问你：你用来比较的标准是什么？这些标准本身是否合理？",
                "选择往往反映我们的价值观。在做出这个选择时，什么对你来说是最重要的？",
                "有时候最好的答案不是选择其中之一，而是理解为什么我们需要选择。你觉得呢？"
            ],
            "exploratory": [
                "你的问题让我思考。在我们探索答案之前，你能告诉我是什么促使你提出这个问题的吗？",
                "这是一个值得深入探讨的话题。你觉得我们应该从哪个角度开始思考？",
                "问题本身就蕴含着智慧。你认为提出好问题和找到好答案，哪个更重要？"
            ]
        }

        template_list = templates.get(question_type, templates["exploratory"])
        template = template_list[hash(user_input) % len(template_list)]

        return template.format(question=user_input)

    def _generate_einstein_response(self, user_input: str, question_type: str, context: SkillContext) -> str:
        """生成爱因斯坦式回应"""
        templates = {
            "causal": [
                "你知道，'{question}'这个问题让我想起了物理学中的因果关系。在自然界中，每个现象都有其深层的原因。让我们用科学的方法来思考：你觉得这里是否存在一个更根本的原理？",
                "这是个好问题！爱因斯坦曾说'想象力比知识更重要'。在思考这个问题时，我们不妨发挥想象力：如果你能设计一个思想实验来验证这个原因，你会怎么设计？"
            ],
            "procedural": [
                "'{question}' - 这让我想起解决物理问题的方法。我们总是先理解原理，再寻找方法。你认为这里的基本原理是什么？",
                "解决问题就像做科学研究一样，需要假设、实验和验证。对于你的问题，你已经有什么假设了吗？"
            ],
            "definitional": [
                "定义在科学中非常重要。就像我们定义'时间'和'空间'一样，准确的定义是理解的基础。你觉得对于'{question}'，什么是最本质的特征？",
                "你知道吗？有时候重新定义一个概念，就能带来全新的理解。你能尝试用不同的方式来思考这个概念吗？"
            ],
            "comparative": [
                "选择就像物理学中的路径积分，有时候看起来不同的路径其实遵循相同的原理。你觉得这些选择之间有什么共同点吗？",
                "在相对论中，我们学到观察者的角度很重要。从不同的角度看这个选择，你看到了什么？"
            ],
            "exploratory": [
                "好奇心是科学进步的动力！你的问题让我想起了我年轻时的思考。让我们一起用科学的眼光来探索这个问题，你觉得从哪里开始比较好？",
                "伟大的发现往往来自于简单的问题。你的问题虽然简单，但可能蕴含着深刻的道理。我们来一起思考一下..."
            ]
        }

        template_list = templates.get(question_type, templates["exploratory"])
        template = template_list[hash(user_input) % len(template_list)]

        return template.format(question=user_input)

    def _generate_general_response(self, user_input: str, question_type: str, context: SkillContext) -> str:
        """生成通用的深度提问回应"""
        templates = {
            "causal": [
                "你提出了一个很有深度的问题。让我们一起思考：除了显而易见的原因，是否还有其他可能的解释？",
                "这个问题的答案可能不只一个。你觉得我们应该从哪个角度来分析这个原因？"
            ],
            "procedural": [
                "方法确实重要，但理解背后的原理同样重要。你认为什么原理支撑着这个方法？",
                "在寻找方法之前，让我们先确定目标。你希望通过这个方法达到什么样的结果？"
            ],
            "definitional": [
                "定义一个概念往往比我们想象的更有挑战性。你能尝试用自己的话来描述一下吗？",
                "理解一个概念的最好方法是思考它的边界。你觉得什么不属于这个概念？"
            ],
            "comparative": [
                "比较是理解事物的好方法。你用来比较的标准是什么？这些标准合理吗？",
                "有时候最好的选择不是非此即彼，而是找到一个更高层面的解决方案。你觉得呢？"
            ],
            "exploratory": [
                "这是一个值得深入思考的问题。让我们从不同的角度来探索这个话题。",
                "你的问题让我想到了很多可能的方向。我们应该先探索哪一个方面？"
            ]
        }

        template_list = templates.get(question_type, templates["exploratory"])
        template = template_list[hash(user_input) % len(template_list)]

        return template.format(question=user_input)

    def _calculate_quality_score(self, response: str, user_input: str) -> float:
        """计算回应质量得分"""
        score = 0.0

        # 基于长度（适中的长度更好）
        length = len(response)
        if 50 <= length <= 300:
            score += 0.3
        elif 300 < length <= 500:
            score += 0.2

        # 基于是否包含反问
        if '?' in response or '？' in response:
            score += 0.3

        # 基于是否包含思考性词汇
        thinking_words = ["思考", "探索", "理解", "分析", "原理", "本质"]
        thinking_count = sum(1 for word in thinking_words if word in response)
        score += min(thinking_count * 0.1, 0.4)

        return min(score, 1.0)

    def _calculate_relevance_score(self, response: str, user_input: str, context: SkillContext) -> float:
        """计算相关性得分"""
        score = 0.7  # 基础得分

        # 检查是否引用了用户的问题
        if user_input[:20] in response:
            score += 0.2

        # 检查是否与用户的意图相关
        if context.detected_intent == "deep_conversation":
            score += 0.1

        return min(score, 1.0)