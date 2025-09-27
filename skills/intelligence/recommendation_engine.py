import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter

from ..core.base import SkillBase
from ..core.models import SkillContext, SkillConfig, SkillResult, SkillCategory

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """
    技能推荐引擎 - 基于用户行为、技能性能和上下文提供智能推荐
    """

    def __init__(self):
        # 用户使用模式跟踪
        self.user_skill_usage: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.skill_performance_history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.context_skill_associations: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))

        # 推荐策略权重
        self.recommendation_weights = {
            "usage_frequency": 0.25,    # 使用频率
            "performance_score": 0.30,  # 性能得分
            "context_relevance": 0.25,  # 上下文相关性
            "novelty_factor": 0.20      # 新颖性因子
        }

        # 时间衰减因子
        self.time_decay_factor = 0.95  # 每天衰减5%

    def record_skill_usage(
        self,
        user_id: str,
        skill_name: str,
        context: SkillContext,
        result: SkillResult
    ):
        """
        记录技能使用情况

        Args:
            user_id: 用户ID
            skill_name: 技能名称
            context: 使用上下文
            result: 执行结果
        """
        usage_record = {
            "skill_name": skill_name,
            "timestamp": datetime.now(),
            "context_type": self._extract_context_type(context),
            "intent": context.detected_intent,
            "character_id": context.character_id,
            "success": result.status.value == "completed",
            "execution_time": result.execution_time,
            "quality_score": result.quality_score,
            "relevance_score": result.relevance_score,
            "user_satisfaction": self._estimate_user_satisfaction(result)
        }

        self.user_skill_usage[user_id].append(usage_record)

        # 更新上下文关联
        context_key = self._generate_context_key(context)
        self.context_skill_associations[context_key][skill_name] += 1

        # 记录性能历史
        self.skill_performance_history[skill_name].append({
            "timestamp": datetime.now(),
            "execution_time": result.execution_time,
            "quality_score": result.quality_score,
            "relevance_score": result.relevance_score,
            "success": result.status.value == "completed"
        })

        logger.debug(f"记录技能使用: {skill_name} for user {user_id}")

    def get_skill_recommendations(
        self,
        user_id: str,
        context: SkillContext,
        available_skills: List[SkillBase],
        max_recommendations: int = 5
    ) -> List[Dict[str, Any]]:
        """
        获取技能推荐

        Args:
            user_id: 用户ID
            context: 当前上下文
            available_skills: 可用技能列表
            max_recommendations: 最大推荐数量

        Returns:
            List[Dict[str, Any]]: 推荐技能列表
        """
        recommendations = []

        for skill in available_skills:
            # 计算推荐得分
            score = self._calculate_recommendation_score(
                user_id,
                skill,
                context
            )

            if score > 0:
                recommendation = {
                    "skill_name": skill.metadata.name,
                    "display_name": skill.metadata.display_name,
                    "description": skill.metadata.description,
                    "category": skill.metadata.category.value,
                    "recommendation_score": score,
                    "reasoning": self._generate_recommendation_reasoning(
                        user_id, skill, context, score
                    ),
                    "predicted_performance": self._predict_skill_performance(skill.metadata.name),
                    "usage_stats": self._get_skill_usage_stats(user_id, skill.metadata.name)
                }
                recommendations.append(recommendation)

        # 按推荐得分排序
        recommendations.sort(key=lambda x: x["recommendation_score"], reverse=True)

        # 应用多样性过滤
        diverse_recommendations = self._apply_diversity_filter(
            recommendations,
            max_recommendations
        )

        logger.info(f"生成 {len(diverse_recommendations)} 个技能推荐")
        return diverse_recommendations

    def _calculate_recommendation_score(
        self,
        user_id: str,
        skill: SkillBase,
        context: SkillContext
    ) -> float:
        """计算技能推荐得分"""
        skill_name = skill.metadata.name

        # 1. 使用频率得分
        usage_score = self._calculate_usage_frequency_score(user_id, skill_name)

        # 2. 性能得分
        performance_score = self._calculate_performance_score(skill_name)

        # 3. 上下文相关性得分
        context_score = self._calculate_context_relevance_score(skill_name, context)

        # 4. 新颖性得分
        novelty_score = self._calculate_novelty_score(user_id, skill_name)

        # 加权综合得分
        total_score = (
            usage_score * self.recommendation_weights["usage_frequency"] +
            performance_score * self.recommendation_weights["performance_score"] +
            context_score * self.recommendation_weights["context_relevance"] +
            novelty_score * self.recommendation_weights["novelty_factor"]
        )

        return min(total_score, 1.0)

    def _calculate_usage_frequency_score(self, user_id: str, skill_name: str) -> float:
        """计算使用频率得分"""
        usage_history = self.user_skill_usage.get(user_id, [])
        if not usage_history:
            return 0.3  # 新用户默认得分

        # 统计技能使用次数，应用时间衰减
        skill_uses = [
            record for record in usage_history
            if record["skill_name"] == skill_name
        ]

        if not skill_uses:
            return 0.2  # 未使用过的技能

        # 计算加权使用频率
        now = datetime.now()
        weighted_usage = 0.0
        total_weight = 0.0

        for use_record in skill_uses:
            days_ago = (now - use_record["timestamp"]).days
            weight = self.time_decay_factor ** days_ago
            weighted_usage += weight
            total_weight += weight

        # 归一化
        if total_weight > 0:
            normalized_usage = weighted_usage / len(usage_history)
            return min(normalized_usage * 2, 1.0)

        return 0.2

    def _calculate_performance_score(self, skill_name: str) -> float:
        """计算技能性能得分"""
        performance_history = self.skill_performance_history.get(skill_name, [])
        if not performance_history:
            return 0.5  # 默认得分

        # 计算最近性能指标
        recent_performances = performance_history[-10:]  # 最近10次
        if not recent_performances:
            return 0.5

        # 计算平均性能指标
        avg_quality = sum(p["quality_score"] for p in recent_performances) / len(recent_performances)
        avg_relevance = sum(p["relevance_score"] for p in recent_performances) / len(recent_performances)
        success_rate = sum(1 for p in recent_performances if p["success"]) / len(recent_performances)

        # 综合性能得分
        performance_score = (avg_quality * 0.4 + avg_relevance * 0.4 + success_rate * 0.2)
        return performance_score

    def _calculate_context_relevance_score(self, skill_name: str, context: SkillContext) -> float:
        """计算上下文相关性得分"""
        context_key = self._generate_context_key(context)
        skill_associations = self.context_skill_associations.get(context_key, {})

        if not skill_associations:
            return 0.4  # 新上下文默认得分

        total_uses = sum(skill_associations.values())
        skill_uses = skill_associations.get(skill_name, 0)

        if total_uses == 0:
            return 0.4

        # 计算在此上下文中的使用比例
        relevance_score = skill_uses / total_uses
        return min(relevance_score * 2, 1.0)

    def _calculate_novelty_score(self, user_id: str, skill_name: str) -> float:
        """计算新颖性得分"""
        usage_history = self.user_skill_usage.get(user_id, [])
        if not usage_history:
            return 1.0  # 新用户，所有技能都是新的

        # 检查最近使用情况
        recent_usage = usage_history[-10:]  # 最近10次使用
        recent_skill_names = [record["skill_name"] for record in recent_usage]

        # 计算技能在最近使用中的频率
        skill_frequency = recent_skill_names.count(skill_name)

        # 新颖性得分与最近使用频率成反比
        if skill_frequency == 0:
            return 1.0  # 完全新颖
        elif skill_frequency <= 2:
            return 0.7  # 较新颖
        elif skill_frequency <= 5:
            return 0.4  # 一般
        else:
            return 0.1  # 不新颖

    def _extract_context_type(self, context: SkillContext) -> str:
        """提取上下文类型"""
        factors = []

        # 基于意图
        if context.detected_intent:
            factors.append(f"intent:{context.detected_intent}")

        # 基于情感状态
        if context.emotional_state:
            factors.append(f"emotion:{context.emotional_state}")

        # 基于对话长度
        conversation_length = len(context.conversation_history)
        if conversation_length <= 2:
            factors.append("conversation:short")
        elif conversation_length <= 10:
            factors.append("conversation:medium")
        else:
            factors.append("conversation:long")

        return "|".join(factors) if factors else "general"

    def _generate_context_key(self, context: SkillContext) -> str:
        """生成上下文键"""
        return self._extract_context_type(context)

    def _estimate_user_satisfaction(self, result: SkillResult) -> float:
        """估算用户满意度"""
        # 基于结果质量估算满意度
        if result.status.value == "completed":
            satisfaction = (result.quality_score * 0.5 +
                          result.relevance_score * 0.3 +
                          result.confidence_score * 0.2)
        else:
            satisfaction = 0.2  # 失败执行的满意度很低

        return min(satisfaction, 1.0)

    def _predict_skill_performance(self, skill_name: str) -> Dict[str, float]:
        """预测技能性能"""
        performance_history = self.skill_performance_history.get(skill_name, [])
        if not performance_history:
            return {
                "predicted_quality": 0.5,
                "predicted_relevance": 0.5,
                "predicted_execution_time": 10.0,
                "predicted_success_rate": 0.8
            }

        recent_performances = performance_history[-20:]  # 最近20次

        return {
            "predicted_quality": sum(p["quality_score"] for p in recent_performances) / len(recent_performances),
            "predicted_relevance": sum(p["relevance_score"] for p in recent_performances) / len(recent_performances),
            "predicted_execution_time": sum(p["execution_time"] for p in recent_performances) / len(recent_performances),
            "predicted_success_rate": sum(1 for p in recent_performances if p["success"]) / len(recent_performances)
        }

    def _get_skill_usage_stats(self, user_id: str, skill_name: str) -> Dict[str, Any]:
        """获取技能使用统计"""
        usage_history = self.user_skill_usage.get(user_id, [])
        skill_uses = [
            record for record in usage_history
            if record["skill_name"] == skill_name
        ]

        if not skill_uses:
            return {
                "total_uses": 0,
                "recent_uses": 0,
                "last_used": None,
                "average_satisfaction": 0.0
            }

        # 最近7天的使用
        week_ago = datetime.now() - timedelta(days=7)
        recent_uses = [
            use for use in skill_uses
            if use["timestamp"] > week_ago
        ]

        return {
            "total_uses": len(skill_uses),
            "recent_uses": len(recent_uses),
            "last_used": max(use["timestamp"] for use in skill_uses),
            "average_satisfaction": sum(use["user_satisfaction"] for use in skill_uses) / len(skill_uses)
        }

    def _apply_diversity_filter(
        self,
        recommendations: List[Dict[str, Any]],
        max_recommendations: int
    ) -> List[Dict[str, Any]]:
        """应用多样性过滤，确保推荐的技能类别多样化"""
        if len(recommendations) <= max_recommendations:
            return recommendations

        # 按类别分组
        category_groups = defaultdict(list)
        for rec in recommendations:
            category_groups[rec["category"]].append(rec)

        # 从每个类别中选择最佳技能
        diverse_recommendations = []
        categories = list(category_groups.keys())
        category_index = 0

        while len(diverse_recommendations) < max_recommendations and any(category_groups.values()):
            current_category = categories[category_index % len(categories)]

            if category_groups[current_category]:
                # 从当前类别中选择得分最高的技能
                best_in_category = category_groups[current_category].pop(0)
                diverse_recommendations.append(best_in_category)

            category_index += 1

        return diverse_recommendations

    def _generate_recommendation_reasoning(
        self,
        user_id: str,
        skill: SkillBase,
        context: SkillContext,
        score: float
    ) -> str:
        """生成推荐理由"""
        reasons = []

        # 基于使用频率
        usage_score = self._calculate_usage_frequency_score(user_id, skill.metadata.name)
        if usage_score > 0.7:
            reasons.append("您经常使用此类技能")
        elif usage_score < 0.3:
            reasons.append("尝试新技能")

        # 基于性能
        performance_score = self._calculate_performance_score(skill.metadata.name)
        if performance_score > 0.8:
            reasons.append("该技能表现优异")

        # 基于上下文
        context_score = self._calculate_context_relevance_score(skill.metadata.name, context)
        if context_score > 0.6:
            reasons.append("适合当前对话情境")

        # 基于意图
        if context.detected_intent:
            intent_descriptions = {
                "deep_conversation": "适合深度交流",
                "storytelling": "适合故事分享",
                "scientific_explanation": "适合科学探讨",
                "creative_writing": "适合创意表达"
            }
            if context.detected_intent in intent_descriptions:
                reasons.append(intent_descriptions[context.detected_intent])

        if not reasons:
            reasons.append("推荐尝试")

        return "，".join(reasons)

    def get_user_skill_insights(self, user_id: str) -> Dict[str, Any]:
        """获取用户技能使用洞察"""
        usage_history = self.user_skill_usage.get(user_id, [])
        if not usage_history:
            return {"message": "暂无使用数据"}

        # 统计最常用技能
        skill_usage_count = Counter(record["skill_name"] for record in usage_history)
        most_used_skills = skill_usage_count.most_common(5)

        # 统计最喜欢的类别
        category_usage = Counter(record.get("context_type", "general") for record in usage_history)
        favorite_categories = category_usage.most_common(3)

        # 计算平均满意度
        avg_satisfaction = sum(record["user_satisfaction"] for record in usage_history) / len(usage_history)

        # 使用趋势
        recent_week = datetime.now() - timedelta(days=7)
        recent_usage = [record for record in usage_history if record["timestamp"] > recent_week]

        return {
            "total_skill_uses": len(usage_history),
            "most_used_skills": most_used_skills,
            "favorite_categories": favorite_categories,
            "average_satisfaction": avg_satisfaction,
            "recent_activity": len(recent_usage),
            "skill_diversity": len(set(record["skill_name"] for record in usage_history))
        }

    def update_recommendation_weights(self, new_weights: Dict[str, float]):
        """更新推荐策略权重"""
        total_weight = sum(new_weights.values())
        if abs(total_weight - 1.0) > 0.01:
            logger.warning(f"推荐权重总和不为1.0: {total_weight}")

        self.recommendation_weights.update(new_weights)
        logger.info("推荐权重已更新")

    def clear_old_data(self, days_to_keep: int = 30):
        """清理旧数据"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)

        # 清理用户使用数据
        for user_id in self.user_skill_usage:
            self.user_skill_usage[user_id] = [
                record for record in self.user_skill_usage[user_id]
                if record["timestamp"] > cutoff_date
            ]

        # 清理性能历史数据
        for skill_name in self.skill_performance_history:
            self.skill_performance_history[skill_name] = [
                record for record in self.skill_performance_history[skill_name]
                if record["timestamp"] > cutoff_date
            ]

        logger.info(f"清理了 {days_to_keep} 天前的数据")