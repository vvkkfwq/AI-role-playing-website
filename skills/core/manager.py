import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from .base import SkillBase
from .registry import SkillRegistry, skill_registry
from .executor import AsyncSkillExecutor
from .context import ContextManager
from .models import (
    SkillContext, SkillConfig, SkillResult, SkillMetadata,
    SkillCategory, SkillPriority, IntentClassification
)

logger = logging.getLogger(__name__)


class SkillManager:
    """
    技能管理器 - 技能系统的核心编排器

    负责技能的发现、选择、执行和结果处理
    """

    def __init__(
        self,
        registry: Optional[SkillRegistry] = None,
        max_concurrent_executions: int = 10
    ):
        """
        初始化技能管理器

        Args:
            registry: 技能注册中心，如果为None则使用全局注册中心
            max_concurrent_executions: 最大并发执行数
        """
        self.registry = registry or skill_registry
        self.executor = AsyncSkillExecutor(max_concurrent_executions)
        self.context_manager = ContextManager()

        # 技能配置缓存
        self._character_skill_configs: Dict[int, Dict[str, SkillConfig]] = {}

        # 性能统计
        self._execution_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0.0
        }

    async def initialize(self, skill_dirs: Optional[List[str]] = None):
        """
        初始化技能管理器

        Args:
            skill_dirs: 技能目录列表，用于自动发现技能
        """
        logger.info("初始化技能管理器...")

        # 自动发现和注册技能
        if skill_dirs:
            self.registry.auto_discover_skills(skill_dirs)

        # 验证技能依赖关系
        dependency_errors = self.registry.validate_skill_dependencies()
        if dependency_errors:
            logger.warning(f"发现技能依赖问题: {dependency_errors}")

        # 记录注册统计
        stats = self.registry.get_registry_stats()
        logger.info(f"技能管理器初始化完成: {stats}")

    async def process_user_input(
        self,
        user_input: str,
        character_id: Optional[int] = None,
        conversation_id: Optional[int] = None,
        message_id: Optional[int] = None,
        character_info: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        session_id: Optional[str] = None,
        execution_strategy: str = "adaptive"
    ) -> List[SkillResult]:
        """
        处理用户输入，执行相关技能

        Args:
            user_input: 用户输入
            character_id: 角色ID
            conversation_id: 会话ID
            message_id: 消息ID
            character_info: 角色信息
            conversation_history: 对话历史
            session_id: 会话ID
            execution_strategy: 执行策略

        Returns:
            List[SkillResult]: 技能执行结果列表
        """
        start_time = asyncio.get_event_loop().time()
        self._execution_stats["total_requests"] += 1

        try:
            logger.info(f"处理用户输入: {user_input[:50]}{'...' if len(user_input) > 50 else ''}")

            # 1. 创建执行上下文
            context = self.context_manager.create_skill_context(
                user_input=user_input,
                character_id=character_id,
                conversation_id=conversation_id,
                message_id=message_id,
                character_info=character_info,
                conversation_history=conversation_history,
                session_id=session_id
            )

            # 2. 意图识别和技能选择
            selected_skills = await self._select_skills(context, character_info)

            if not selected_skills:
                logger.warning("没有找到适合的技能来处理用户输入")
                return []

            logger.info(f"选中 {len(selected_skills)} 个技能: {[s[0].metadata.name for s in selected_skills]}")

            # 3. 执行技能
            results = await self.executor.execute_skills_with_strategy(
                selected_skills,
                strategy=execution_strategy
            )

            # 4. 后处理
            processed_results = await self._post_process_results(context, results)

            # 5. 更新统计
            execution_time = asyncio.get_event_loop().time() - start_time
            self._update_execution_stats(processed_results, execution_time)

            logger.info(f"用户输入处理完成，耗时: {execution_time:.2f}秒")
            return processed_results

        except Exception as e:
            self._execution_stats["failed_requests"] += 1
            logger.error(f"处理用户输入失败: {e}")
            return []

    async def _select_skills(
        self,
        context: SkillContext,
        character_info: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[SkillBase, SkillContext, SkillConfig]]:
        """
        选择适合的技能

        Args:
            context: 执行上下文
            character_info: 角色信息

        Returns:
            List[Tuple[SkillBase, SkillContext, SkillConfig]]: 选中的技能配置列表
        """
        character_name = None
        if character_info:
            character_name = character_info.get("name")

        # 获取可用技能
        available_skills = self.registry.get_available_skills(character_name)

        if not available_skills:
            logger.warning("没有可用的技能")
            return []

        # 评估每个技能的适合度
        skill_scores = []
        for skill in available_skills:
            # 获取技能配置
            config = self._get_skill_config(skill.metadata.name, context.character_id)

            # 检查技能是否能处理当前请求
            if not skill.can_handle(context, config):
                continue

            # 计算信心得分
            confidence_score = skill.get_confidence_score(context, config)

            # 计算综合得分（结合权重和阈值）
            combined_score = confidence_score * config.weight

            # 检查是否达到触发阈值
            if combined_score >= config.threshold:
                skill_scores.append((skill, context, config, combined_score))

        # 按得分排序
        skill_scores.sort(key=lambda x: x[3], reverse=True)

        # 选择top技能（可以根据策略调整选择数量）
        max_skills = 3  # 最多选择3个技能
        selected = skill_scores[:max_skills]

        return [(skill, context, config) for skill, context, config, _ in selected]

    def _get_skill_config(self, skill_name: str, character_id: Optional[int]) -> SkillConfig:
        """
        获取技能配置

        Args:
            skill_name: 技能名称
            character_id: 角色ID

        Returns:
            SkillConfig: 技能配置
        """
        # 尝试从缓存获取角色特定配置
        if character_id and character_id in self._character_skill_configs:
            character_configs = self._character_skill_configs[character_id]
            if skill_name in character_configs:
                return character_configs[skill_name]

        # 返回默认配置
        return SkillConfig(
            skill_name=skill_name,
            character_id=character_id
        )

    async def _post_process_results(
        self,
        context: SkillContext,
        results: List[SkillResult]
    ) -> List[SkillResult]:
        """
        后处理技能执行结果

        Args:
            context: 执行上下文
            results: 原始结果列表

        Returns:
            List[SkillResult]: 处理后的结果列表
        """
        processed_results = []

        for result in results:
            try:
                # 质量评估
                result = await self._assess_result_quality(context, result)

                # 内容优化
                result = await self._optimize_result_content(context, result)

                processed_results.append(result)

            except Exception as e:
                logger.error(f"后处理技能结果失败 {result.skill_name}: {e}")
                # 保留原始结果
                processed_results.append(result)

        return processed_results

    async def _assess_result_quality(
        self,
        context: SkillContext,
        result: SkillResult
    ) -> SkillResult:
        """
        评估结果质量

        Args:
            context: 执行上下文
            result: 技能结果

        Returns:
            SkillResult: 更新质量分数的结果
        """
        # 这里可以实现复杂的质量评估逻辑
        # 暂时使用简单的启发式方法

        if result.generated_content:
            content_length = len(result.generated_content)

            # 基于内容长度的质量评估
            if content_length > 100:
                result.quality_score = min(0.9, result.quality_score + 0.2)
            elif content_length > 50:
                result.quality_score = min(0.8, result.quality_score + 0.1)

            # 基于相关性的评估
            # 可以使用NLP技术评估生成内容与用户输入的相关性
            # 这里暂时使用简单逻辑
            user_input_lower = context.user_input.lower()
            content_lower = result.generated_content.lower()

            # 检查关键词重叠
            user_words = set(user_input_lower.split())
            content_words = set(content_lower.split())
            overlap = len(user_words.intersection(content_words))

            if overlap > 0:
                relevance_boost = min(0.3, overlap * 0.1)
                result.relevance_score = min(1.0, result.relevance_score + relevance_boost)

        return result

    async def _optimize_result_content(
        self,
        context: SkillContext,
        result: SkillResult
    ) -> SkillResult:
        """
        优化结果内容

        Args:
            context: 执行上下文
            result: 技能结果

        Returns:
            SkillResult: 优化后的结果
        """
        # 这里可以实现内容优化逻辑
        # 例如：格式化、去重、合并等

        if result.generated_content:
            # 简单的内容清理
            content = result.generated_content.strip()

            # 移除多余的空行
            content = "\n".join(line for line in content.split("\n") if line.strip())

            result.generated_content = content

        return result

    def _update_execution_stats(self, results: List[SkillResult], execution_time: float):
        """更新执行统计"""
        successful_results = sum(1 for r in results if r.status.value == "completed")

        if successful_results > 0:
            self._execution_stats["successful_requests"] += 1
        else:
            self._execution_stats["failed_requests"] += 1

        # 更新平均响应时间
        total_requests = self._execution_stats["total_requests"]
        current_avg = self._execution_stats["average_response_time"]
        self._execution_stats["average_response_time"] = (
            (current_avg * (total_requests - 1) + execution_time) / total_requests
        )

    def load_character_skill_configs(
        self,
        character_id: int,
        skill_configs: Dict[str, SkillConfig]
    ):
        """
        加载角色的技能配置

        Args:
            character_id: 角色ID
            skill_configs: 技能配置字典
        """
        self._character_skill_configs[character_id] = skill_configs
        logger.info(f"加载角色 {character_id} 的 {len(skill_configs)} 个技能配置")

    def get_skill_suggestions(
        self,
        user_input: str,
        character_id: Optional[int] = None,
        max_suggestions: int = 5
    ) -> List[Dict[str, Any]]:
        """
        获取技能建议

        Args:
            user_input: 用户输入
            character_id: 角色ID
            max_suggestions: 最大建议数量

        Returns:
            List[Dict[str, Any]]: 技能建议列表
        """
        suggestions = []

        # 创建临时上下文
        context = SkillContext(
            user_input=user_input,
            character_id=character_id,
            request_id="suggestion_request"
        )

        # 获取可用技能
        available_skills = self.registry.get_available_skills()

        for skill in available_skills:
            config = self._get_skill_config(skill.metadata.name, character_id)

            if skill.can_handle(context, config):
                confidence = skill.get_confidence_score(context, config)

                suggestions.append({
                    "skill_name": skill.metadata.name,
                    "display_name": skill.metadata.display_name,
                    "description": skill.metadata.description,
                    "category": skill.metadata.category.value,
                    "confidence": confidence,
                    "weight": config.weight
                })

        # 按信心得分排序
        suggestions.sort(key=lambda x: x["confidence"], reverse=True)

        return suggestions[:max_suggestions]

    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        registry_stats = self.registry.get_registry_stats()
        executor_stats = self.executor.get_execution_statistics()

        return {
            "registry": registry_stats,
            "executor": executor_stats,
            "execution_stats": self._execution_stats,
            "character_configs_loaded": len(self._character_skill_configs)
        }

    async def shutdown(self):
        """关闭技能管理器"""
        logger.info("关闭技能管理器...")
        await self.executor.shutdown()
        logger.info("技能管理器已关闭")