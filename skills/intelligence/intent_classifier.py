import re
import logging
from typing import Dict, List, Set, Tuple, Optional
from datetime import datetime

from ..core.models import SkillContext, IntentClassification

logger = logging.getLogger(__name__)


class IntentClassifier:
    """
    意图识别器 - 基于规则和模式识别用户意图
    """

    def __init__(self):
        # 意图定义和关键词映射
        self.intent_patterns = {
            # 对话相关意图
            "deep_conversation": {
                "keywords": ["为什么", "如何", "怎么", "原理", "深入", "详细", "解释", "分析"],
                "patterns": [r".*为什么.*", r".*如何.*", r".*怎么.*", r".*原理.*"],
                "category": "conversation",
                "weight": 1.0
            },
            "storytelling": {
                "keywords": ["故事", "经历", "冒险", "传说", "情节", "讲述", "分享"],
                "patterns": [r".*讲.*故事.*", r".*分享.*经历.*", r".*冒险.*"],
                "category": "conversation",
                "weight": 1.0
            },
            "scientific_explanation": {
                "keywords": ["科学", "物理", "相对论", "实验", "理论", "公式", "原理"],
                "patterns": [r".*科学.*", r".*物理.*", r".*理论.*", r".*实验.*"],
                "category": "conversation",
                "weight": 1.0
            },
            "emotional_support": {
                "keywords": ["难过", "开心", "困惑", "迷茫", "担心", "焦虑", "帮助"],
                "patterns": [r".*难过.*", r".*担心.*", r".*困惑.*", r".*帮助.*"],
                "category": "conversation",
                "weight": 0.9
            },
            "humor": {
                "keywords": ["笑话", "有趣", "幽默", "好玩", "搞笑", "开心"],
                "patterns": [r".*笑话.*", r".*有趣.*", r".*幽默.*"],
                "category": "conversation",
                "weight": 0.8
            },

            # 知识相关意图
            "fact_lookup": {
                "keywords": ["什么是", "定义", "介绍", "资料", "信息", "查找"],
                "patterns": [r".*什么是.*", r".*定义.*", r".*介绍.*"],
                "category": "knowledge",
                "weight": 1.0
            },
            "analysis": {
                "keywords": ["分析", "比较", "对比", "评价", "判断", "区别"],
                "patterns": [r".*分析.*", r".*比较.*", r".*对比.*"],
                "category": "knowledge",
                "weight": 1.0
            },
            "memory_recall": {
                "keywords": ["记得", "之前", "以前", "刚才", "上次", "历史"],
                "patterns": [r".*记得.*", r".*之前.*", r".*以前.*"],
                "category": "knowledge",
                "weight": 0.9
            },
            "comparison": {
                "keywords": ["比如", "像", "类似", "好比", "如同", "相当于"],
                "patterns": [r".*比如.*", r".*像.*", r".*类似.*"],
                "category": "knowledge",
                "weight": 0.8
            },

            # 创意相关意图
            "creative_writing": {
                "keywords": ["写", "创作", "诗", "文章", "小说", "剧本"],
                "patterns": [r".*写.*", r".*创作.*", r".*诗.*"],
                "category": "creative",
                "weight": 1.0
            },
            "brainstorming": {
                "keywords": ["想法", "创意", "点子", "思路", "灵感", "建议"],
                "patterns": [r".*想法.*", r".*创意.*", r".*建议.*"],
                "category": "creative",
                "weight": 1.0
            },
            "roleplay": {
                "keywords": ["扮演", "角色", "情景", "模拟", "假设"],
                "patterns": [r".*扮演.*", r".*角色.*", r".*假设.*"],
                "category": "creative",
                "weight": 0.9
            },
            "imagination": {
                "keywords": ["想象", "如果", "假如", "可能", "也许"],
                "patterns": [r".*想象.*", r".*如果.*", r".*假如.*"],
                "category": "creative",
                "weight": 0.8
            },

            # 实用相关意图
            "translation": {
                "keywords": ["翻译", "英文", "中文", "语言", "转换"],
                "patterns": [r".*翻译.*", r".*英文.*", r".*中文.*"],
                "category": "utility",
                "weight": 1.0
            },
            "summarization": {
                "keywords": ["总结", "概括", "归纳", "要点", "摘要"],
                "patterns": [r".*总结.*", r".*概括.*", r".*归纳.*"],
                "category": "utility",
                "weight": 1.0
            },
            "planning": {
                "keywords": ["计划", "安排", "规划", "步骤", "流程"],
                "patterns": [r".*计划.*", r".*安排.*", r".*规划.*"],
                "category": "utility",
                "weight": 0.9
            },
            "reflection": {
                "keywords": ["反思", "回顾", "总结", "经验", "教训"],
                "patterns": [r".*反思.*", r".*回顾.*", r".*经验.*"],
                "category": "utility",
                "weight": 0.8
            }
        }

        # 情感状态关键词
        self.emotion_keywords = {
            "happy": ["开心", "高兴", "快乐", "愉快", "兴奋"],
            "sad": ["难过", "伤心", "沮丧", "失落", "悲伤"],
            "angry": ["生气", "愤怒", "恼火", "气愤", "不满"],
            "confused": ["困惑", "迷茫", "不懂", "疑惑", "不明白"],
            "anxious": ["担心", "焦虑", "紧张", "不安", "忧虑"],
            "curious": ["好奇", "想知道", "感兴趣", "想了解"]
        }

        # 实体提取模式
        self.entity_patterns = {
            "person": r"([A-Za-z\u4e00-\u9fff]+(?:·[A-Za-z\u4e00-\u9fff]+)*)",
            "number": r"(\d+(?:\.\d+)?)",
            "time": r"(今天|明天|昨天|现在|以前|之前|刚才|上次)",
            "location": r"(在.*?[地方|地点|地区|城市|国家])"
        }

    async def classify_intent(self, context: SkillContext) -> IntentClassification:
        """
        识别用户输入的意图

        Args:
            context: 技能执行上下文

        Returns:
            IntentClassification: 意图识别结果
        """
        user_input = context.user_input.lower()
        start_time = datetime.now()

        # 1. 基于关键词和模式的意图识别
        intent_scores = self._calculate_intent_scores(user_input)

        # 2. 考虑上下文因素
        context_adjusted_scores = self._adjust_scores_by_context(intent_scores, context)

        # 3. 选择最佳意图
        if context_adjusted_scores:
            best_intent = max(context_adjusted_scores.items(), key=lambda x: x[1])
            detected_intent = best_intent[0]
            confidence = best_intent[1]
        else:
            detected_intent = "general_conversation"
            confidence = 0.5

        # 4. 生成候选意图列表
        alternative_intents = [
            {"intent": intent, "confidence": score}
            for intent, score in sorted(context_adjusted_scores.items(), key=lambda x: x[1], reverse=True)[:3]
            if intent != detected_intent
        ]

        # 5. 提取实体
        entities = self._extract_entities(context.user_input)

        # 6. 识别情感状态
        emotional_state = self._detect_emotion(user_input)

        # 7. 计算处理时间
        processing_time = (datetime.now() - start_time).total_seconds()

        return IntentClassification(
            input_text=context.user_input,
            detected_intent=detected_intent,
            confidence=confidence,
            alternative_intents=alternative_intents,
            entities=entities,
            context_factors={
                "character_id": context.character_id,
                "conversation_length": len(context.conversation_history),
                "emotional_state": emotional_state,
                "has_history": len(context.conversation_history) > 0
            },
            processing_time=processing_time,
            model_version="1.0.0"
        )

    def _calculate_intent_scores(self, user_input: str) -> Dict[str, float]:
        """计算各个意图的得分"""
        intent_scores = {}

        for intent_name, intent_config in self.intent_patterns.items():
            score = 0.0

            # 关键词匹配
            keyword_matches = sum(
                1 for keyword in intent_config["keywords"]
                if keyword in user_input
            )
            if keyword_matches > 0:
                score += (keyword_matches / len(intent_config["keywords"])) * 0.7

            # 模式匹配
            pattern_matches = sum(
                1 for pattern in intent_config["patterns"]
                if re.search(pattern, user_input)
            )
            if pattern_matches > 0:
                score += (pattern_matches / len(intent_config["patterns"])) * 0.3

            # 应用权重
            score *= intent_config["weight"]

            if score > 0:
                intent_scores[intent_name] = score

        return intent_scores

    def _adjust_scores_by_context(
        self,
        intent_scores: Dict[str, float],
        context: SkillContext
    ) -> Dict[str, float]:
        """根据上下文调整意图得分"""
        adjusted_scores = intent_scores.copy()

        # 基于角色特征调整
        if context.character:
            character_name = context.character.get("name", "")

            # 哈利波特 - 提升故事讲述和冒险相关意图
            if "哈利" in character_name:
                if "storytelling" in adjusted_scores:
                    adjusted_scores["storytelling"] *= 1.3
                if "roleplay" in adjusted_scores:
                    adjusted_scores["roleplay"] *= 1.2

            # 苏格拉底 - 提升深度对话和分析相关意图
            elif "苏格拉底" in character_name:
                if "deep_conversation" in adjusted_scores:
                    adjusted_scores["deep_conversation"] *= 1.5
                if "analysis" in adjusted_scores:
                    adjusted_scores["analysis"] *= 1.3

            # 爱因斯坦 - 提升科学解释和想象相关意图
            elif "爱因斯坦" in character_name:
                if "scientific_explanation" in adjusted_scores:
                    adjusted_scores["scientific_explanation"] *= 1.5
                if "imagination" in adjusted_scores:
                    adjusted_scores["imagination"] *= 1.2

        # 基于对话历史调整
        conversation_length = len(context.conversation_history)
        if conversation_length > 5:
            # 长对话中提升回忆和反思意图
            if "memory_recall" in adjusted_scores:
                adjusted_scores["memory_recall"] *= 1.2
            if "reflection" in adjusted_scores:
                adjusted_scores["reflection"] *= 1.1

        # 基于技能使用历史调整
        skill_history = context.skill_history
        if skill_history:
            recent_skills = [skill["skill_name"] for skill in skill_history[-3:]]
            # 避免重复使用相同类型的技能
            for intent in adjusted_scores:
                intent_category = self.intent_patterns.get(intent, {}).get("category", "")
                similar_recent_usage = sum(
                    1 for skill in recent_skills
                    if intent_category in skill.lower()
                )
                if similar_recent_usage > 1:
                    adjusted_scores[intent] *= 0.8

        return adjusted_scores

    def _extract_entities(self, user_input: str) -> Dict[str, Any]:
        """提取用户输入中的实体"""
        entities = {}

        for entity_type, pattern in self.entity_patterns.items():
            matches = re.findall(pattern, user_input)
            if matches:
                entities[entity_type] = matches

        return entities

    def _detect_emotion(self, user_input: str) -> Optional[str]:
        """检测情感状态"""
        emotion_scores = {}

        for emotion, keywords in self.emotion_keywords.items():
            score = sum(1 for keyword in keywords if keyword in user_input)
            if score > 0:
                emotion_scores[emotion] = score

        if emotion_scores:
            return max(emotion_scores.items(), key=lambda x: x[1])[0]

        return None

    def add_custom_intent(
        self,
        intent_name: str,
        keywords: List[str],
        patterns: List[str],
        category: str = "custom",
        weight: float = 1.0
    ):
        """添加自定义意图"""
        self.intent_patterns[intent_name] = {
            "keywords": keywords,
            "patterns": patterns,
            "category": category,
            "weight": weight
        }
        logger.info(f"添加自定义意图: {intent_name}")

    def update_intent_weights(self, intent_weights: Dict[str, float]):
        """更新意图权重"""
        for intent_name, weight in intent_weights.items():
            if intent_name in self.intent_patterns:
                self.intent_patterns[intent_name]["weight"] = weight

    def get_supported_intents(self) -> List[str]:
        """获取支持的意图列表"""
        return list(self.intent_patterns.keys())

    def get_intent_statistics(self) -> Dict[str, Any]:
        """获取意图统计信息"""
        categories = {}
        for intent_name, config in self.intent_patterns.items():
            category = config["category"]
            if category not in categories:
                categories[category] = []
            categories[category].append(intent_name)

        return {
            "total_intents": len(self.intent_patterns),
            "categories": categories,
            "category_counts": {cat: len(intents) for cat, intents in categories.items()}
        }