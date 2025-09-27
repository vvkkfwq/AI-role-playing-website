from typing import Dict, Any, List
from datetime import datetime

from ...core.base import SkillBase
from ...core.models import (
    SkillMetadata, SkillContext, SkillConfig, SkillResult,
    SkillCategory, SkillTrigger, SkillPriority
)


class AnalysisSkill(SkillBase):
    """
    分析技能 - 对问题进行深入分析和解构
    """

    @classmethod
    def get_metadata(cls) -> SkillMetadata:
        """获取技能元数据"""
        return SkillMetadata(
            name="analysis",
            display_name="深度分析",
            description="对复杂问题进行逻辑分析和多角度解构",
            category=SkillCategory.KNOWLEDGE,
            triggers=SkillTrigger(
                keywords=["分析", "分解", "比较", "评价", "优缺点", "原因", "影响"],
                patterns=[r".*分析.*", r".*比较.*", r".*评价.*"],
                intent_types=["analysis", "comparison", "deep_conversation"]
            ),
            priority=SkillPriority.HIGH,
            character_compatibility=["苏格拉底", "阿尔伯特·爱因斯坦"],
            max_execution_time=15.0
        )

    def can_handle(self, context: SkillContext, config: SkillConfig) -> bool:
        """判断是否能处理当前请求"""
        user_input = context.user_input.lower()

        # 检查分析类关键词
        analysis_keywords = ["分析", "分解", "比较", "评价", "优缺点", "原因", "影响", "区别"]
        has_analysis_request = any(keyword in user_input for keyword in analysis_keywords)

        # 检查复杂问题特征
        is_complex = len(user_input.strip()) > 10 and ("？" in user_input or "?" in user_input)

        return has_analysis_request or (is_complex and context.detected_intent == "analysis")

    def get_confidence_score(self, context: SkillContext, config: SkillConfig) -> float:
        """计算技能置信度"""
        user_input = context.user_input.lower()
        score = 0.0

        # 基于分析关键词
        analysis_words = ["分析", "分解", "比较", "评价", "优缺点", "原因", "影响"]
        matches = sum(1 for word in analysis_words if word in user_input)
        score += min(matches * 0.2, 0.6)

        # 基于问题复杂度
        if len(user_input.strip()) > 20:
            score += 0.2

        # 基于角色匹配
        if context.character:
            character_name = context.character.get("name", "")
            if "苏格拉底" in character_name or "爱因斯坦" in character_name:
                score += 0.3

        # 基于意图匹配
        if context.detected_intent in ["analysis", "comparison"]:
            score += 0.3

        return min(score, 1.0)

    async def execute(self, context: SkillContext, config: SkillConfig) -> SkillResult:
        """执行分析技能"""
        user_input = context.user_input
        character_name = context.character.get("name", "") if context.character else ""

        # 分析问题类型
        analysis_type = self._determine_analysis_type(user_input)

        # 根据角色生成分析
        if "苏格拉底" in character_name:
            analysis = self._generate_socratic_analysis(user_input, analysis_type, context)
        elif "爱因斯坦" in character_name:
            analysis = self._generate_scientific_analysis(user_input, analysis_type, context)
        else:
            analysis = self._generate_general_analysis(user_input, analysis_type, context)

        # 计算质量指标
        quality_score = self._calculate_quality_score(analysis, user_input)
        relevance_score = self._calculate_relevance_score(analysis, user_input, context)

        return SkillResult(
            skill_name=self.metadata.name,
            execution_id="",
            status="completed",
            generated_content=analysis,
            confidence_score=self.get_confidence_score(context, config),
            relevance_score=relevance_score,
            quality_score=quality_score,
            result_data={
                "analysis_type": analysis_type,
                "character_perspective": character_name,
                "structure": "multi_angle",
                "depth_level": "deep"
            }
        )

    def _determine_analysis_type(self, user_input: str) -> str:
        """确定分析类型"""
        user_input_lower = user_input.lower()

        if any(word in user_input_lower for word in ["比较", "对比", "区别", "不同"]):
            return "comparative"
        elif any(word in user_input_lower for word in ["原因", "为什么", "导致", "引起"]):
            return "causal"
        elif any(word in user_input_lower for word in ["影响", "后果", "结果", "效果"]):
            return "impact"
        elif any(word in user_input_lower for word in ["优缺点", "利弊", "好坏", "评价"]):
            return "evaluative"
        elif any(word in user_input_lower for word in ["过程", "步骤", "如何", "方法"]):
            return "procedural"
        else:
            return "general"

    def _generate_socratic_analysis(self, user_input: str, analysis_type: str, context: SkillContext) -> str:
        """生成苏格拉底式分析"""
        intro = "让我们用哲学的方法来分析这个问题。"

        if analysis_type == "comparative":
            analysis = f"""{intro}

当我们比较两个事物时，我们需要问自己几个问题：

🔍 **基础思考**
首先，我们比较的标准是什么？这些标准本身是否合理？我们是否应该质疑这些标准？

📏 **多维视角**
- 从表面现象看，它们有什么不同？
- 从本质属性看，它们的根本区别是什么？
- 从功能作用看，它们服务于什么目的？

💭 **深层反思**
但是，我想问你：为什么我们需要进行这种比较？比较的目的是为了选择，还是为了理解？

也许真正的智慧不在于找到标准答案，而在于理解为什么我们要提出这个问题。你觉得呢？"""

        elif analysis_type == "causal":
            analysis = f"""{intro}

寻找原因是哲学的核心任务之一。让我们一层层剥开现象的外衣：

🌱 **直接原因**
表面上看，什么直接导致了这个现象？但这真的是原因吗，还是只是另一个现象？

🌳 **根本原因**
让我们往更深处挖掘：什么是这个原因背后的原因？是否存在一个更根本的原理？

🔄 **因果链条**
原因和结果的关系真的如我们想象的那样简单吗？是否可能结果也在影响原因？

💡 **哲学思辨**
最重要的是，我们要问：真的存在绝对的原因吗？还是原因只是我们为了理解世界而创造的概念？

这个问题让你想到了什么？"""

        else:
            analysis = f"""{intro}

让我们用苏格拉底式的方法来探索这个问题：

❓ **质疑假设**
首先，我们对这个问题有什么预设？这些预设是否经得起推敲？

🔍 **分解问题**
我们能否将这个复杂的问题分解成几个更简单的部分？

🎯 **寻找本质**
在所有的表面现象背后，什么是最核心、最不变的要素？

🤔 **反思过程**
最重要的是，我们思考这个问题的过程本身告诉了我们什么？

记住，有时候问题比答案更重要。你从这个思考过程中学到了什么？"""

        return analysis

    def _generate_scientific_analysis(self, user_input: str, analysis_type: str, context: SkillContext) -> str:
        """生成科学式分析"""
        intro = "让我们用科学的方法来分析这个问题。"

        if analysis_type == "comparative":
            analysis = f"""{intro}

在科学中，比较是发现规律的重要方法：

🔬 **定量分析**
- 我们能用什么可测量的标准来比较？
- 数据告诉我们什么故事？
- 是否存在我们没有考虑到的变量？

📐 **模型建立**
就像在物理学中，我们可以建立简化的模型来理解复杂现象。这里的关键变量是什么？

⚖️ **相对性原理**
记住，比较总是相对的。从不同的参考系看，结果可能完全不同。

🧪 **实验思维**
如果我们能设计一个实验来验证我们的比较，那会是什么样的？

科学告诉我们，最好的理解来自于精确的观察和严谨的推理。"""

        elif analysis_type == "causal":
            analysis = f"""{intro}

在科学中，因果关系需要严格的验证：

🔗 **因果链条**
- 时间序列：原因必须在结果之前发生
- 相关性：原因和结果之间必须有可观察的联系
- 排除其他：我们能否排除其他可能的解释？

📊 **系统思维**
大多数现象都是多因素相互作用的结果。我们需要考虑：
- 主要因素和次要因素
- 直接影响和间接影响
- 反馈回路和动态平衡

🎯 **可证伪性**
一个好的因果解释必须是可证伪的。我们能设计什么实验来测试这个假设？

想象力比知识更重要，但严谨的逻辑是通向真理的道路。"""

        else:
            analysis = f"""{intro}

让我们用科学方法的步骤来分析：

📝 **观察现象**
首先，我们观察到了什么？哪些是事实，哪些是推测？

💡 **提出假设**
基于观察，我们能提出什么假设来解释这个现象？

🧪 **设计验证**
如果我们的假设是对的，应该能观察到什么结果？

📈 **数据分析**
证据支持还是反对我们的假设？我们需要修正理论吗？

🔄 **迭代改进**
科学是一个不断修正和完善的过程。每个答案都会带来新的问题。

记住，在科学中，"我不知道"是智慧的开始，好奇心是进步的动力。"""

        return analysis

    def _generate_general_analysis(self, user_input: str, analysis_type: str, context: SkillContext) -> str:
        """生成通用分析"""
        intro = "让我来帮你分析这个问题："

        frameworks = {
            "comparative": """
📊 **多角度比较分析**

**相似点分析：**
• 共同特征和基础属性
• 相似的功能或作用
• 面临的共同挑战

**差异点分析：**
• 核心区别和独特特征
• 不同的优势和劣势
• 适用场景的差异

**综合评价：**
• 在不同情况下的适用性
• 选择标准和决策建议
• 未来发展趋势对比

这样的对比有助于我们做出更明智的选择。""",

            "causal": """
🔍 **原因分析框架**

**直接原因：**
• 立即触发因素
• 显而易见的关联
• 短期影响因素

**根本原因：**
• 深层结构性问题
• 长期累积的因素
• 系统性的根源

**影响因素：**
• 内部因素 vs 外部因素
• 可控因素 vs 不可控因素
• 主要因素 vs 次要因素

通过这种层次化分析，我们能更好地理解问题的全貌。""",

            "general": """
🎯 **综合分析框架**

**问题分解：**
• 核心问题识别
• 子问题梳理
• 关键要素提取

**多维度思考：**
• 现状分析：是什么？
• 原因分析：为什么？
• 影响分析：会怎样？
• 对策分析：怎么办？

**综合判断：**
• 权衡各种因素
• 考虑不同视角
• 形成合理结论

这种系统性的分析方法能帮助我们更全面地理解问题。"""
        }

        return intro + frameworks.get(analysis_type, frameworks["general"])

    def _calculate_quality_score(self, analysis: str, user_input: str) -> float:
        """计算分析质量得分"""
        score = 0.0

        # 基于结构化程度
        structure_indicators = ["**", "•", "🔍", "📊", "💡"]
        structure_count = sum(1 for indicator in structure_indicators if indicator in analysis)
        score += min(structure_count * 0.1, 0.3)

        # 基于分析深度
        depth_words = ["原因", "影响", "分析", "思考", "理解", "本质"]
        depth_count = sum(1 for word in depth_words if word in analysis)
        score += min(depth_count * 0.05, 0.3)

        # 基于逻辑性
        logic_indicators = ["首先", "其次", "然后", "因此", "所以", "但是"]
        logic_count = sum(1 for indicator in logic_indicators if indicator in analysis)
        score += min(logic_count * 0.05, 0.2)

        # 基于内容长度
        if len(analysis) > 200:
            score += 0.2

        return min(score, 1.0)

    def _calculate_relevance_score(self, analysis: str, user_input: str, context: SkillContext) -> float:
        """计算相关性得分"""
        score = 0.7  # 基础得分

        # 检查关键词重叠
        user_words = set(user_input.lower().split())
        analysis_words = set(analysis.lower().split())
        overlap = len(user_words.intersection(analysis_words))
        if overlap > 0:
            score += min(overlap * 0.02, 0.2)

        # 检查意图匹配
        if context.detected_intent == "analysis":
            score += 0.1

        return min(score, 1.0)