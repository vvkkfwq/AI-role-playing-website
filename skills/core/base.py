from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, AsyncIterator
import asyncio
import time
import uuid
from datetime import datetime

from .models import (
    SkillMetadata, SkillConfig, SkillContext, SkillResult,
    SkillExecutionStatus, SkillPriority
)


class SkillBase(ABC):
    """技能基类 - 所有技能必须继承此类"""

    def __init__(self, metadata: SkillMetadata):
        """
        初始化技能基类

        Args:
            metadata: 技能元数据
        """
        self.metadata = metadata
        self._execution_cache: Dict[str, SkillResult] = {}
        self._stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "total_execution_time": 0.0
        }

    @abstractmethod
    async def execute(self, context: SkillContext, config: SkillConfig) -> SkillResult:
        """
        执行技能的核心方法 - 必须被子类实现

        Args:
            context: 技能执行上下文
            config: 技能配置

        Returns:
            SkillResult: 执行结果
        """
        pass

    @abstractmethod
    def can_handle(self, context: SkillContext, config: SkillConfig) -> bool:
        """
        判断技能是否能处理当前请求

        Args:
            context: 技能执行上下文
            config: 技能配置

        Returns:
            bool: 是否能处理
        """
        pass

    @abstractmethod
    def get_confidence_score(self, context: SkillContext, config: SkillConfig) -> float:
        """
        计算技能对当前请求的信心得分

        Args:
            context: 技能执行上下文
            config: 技能配置

        Returns:
            float: 信心得分 (0.0-1.0)
        """
        pass

    async def execute_with_monitoring(
        self,
        context: SkillContext,
        config: SkillConfig
    ) -> SkillResult:
        """
        带监控的技能执行方法

        Args:
            context: 技能执行上下文
            config: 技能配置

        Returns:
            SkillResult: 执行结果
        """
        execution_id = str(uuid.uuid4())
        start_time = time.time()

        # 检查缓存
        if self.metadata.cache_results:
            cache_key = self._generate_cache_key(context, config)
            cached_result = self._execution_cache.get(cache_key)
            if cached_result:
                cached_result.execution_time = 0.0  # 缓存命中
                return cached_result

        try:
            # 更新统计
            self._stats["total_executions"] += 1

            # 执行超时控制
            result = await asyncio.wait_for(
                self.execute(context, config),
                timeout=self.metadata.max_execution_time
            )

            # 设置执行信息
            execution_time = time.time() - start_time
            result.execution_id = execution_id
            result.execution_time = execution_time
            result.status = SkillExecutionStatus.COMPLETED
            result.completed_at = datetime.now()

            # 更新统计
            self._stats["successful_executions"] += 1
            self._stats["total_execution_time"] += execution_time

            # 缓存结果
            if self.metadata.cache_results:
                cache_key = self._generate_cache_key(context, config)
                self._execution_cache[cache_key] = result

            return result

        except asyncio.TimeoutError:
            execution_time = time.time() - start_time
            self._stats["failed_executions"] += 1

            return SkillResult(
                skill_name=self.metadata.name,
                execution_id=execution_id,
                status=SkillExecutionStatus.TIMEOUT,
                execution_time=execution_time,
                error_message=f"技能执行超时 ({self.metadata.max_execution_time}秒)",
                error_code="TIMEOUT",
                confidence_score=0.0,
                relevance_score=0.0,
                quality_score=0.0,
                completed_at=datetime.now()
            )

        except Exception as e:
            execution_time = time.time() - start_time
            self._stats["failed_executions"] += 1

            return SkillResult(
                skill_name=self.metadata.name,
                execution_id=execution_id,
                status=SkillExecutionStatus.FAILED,
                execution_time=execution_time,
                error_message=str(e),
                error_code="EXECUTION_ERROR",
                confidence_score=0.0,
                relevance_score=0.0,
                quality_score=0.0,
                completed_at=datetime.now()
            )

    def _generate_cache_key(self, context: SkillContext, config: SkillConfig) -> str:
        """生成缓存键"""
        key_components = [
            self.metadata.name,
            context.user_input,
            str(context.character_id),
            str(hash(frozenset(config.parameters.items()) if config.parameters else frozenset()))
        ]
        return "|".join(key_components)

    def get_statistics(self) -> Dict[str, Any]:
        """获取技能统计信息"""
        stats = self._stats.copy()
        if stats["total_executions"] > 0:
            stats["average_execution_time"] = stats["total_execution_time"] / stats["total_executions"]
            stats["success_rate"] = stats["successful_executions"] / stats["total_executions"]
        else:
            stats["average_execution_time"] = 0.0
            stats["success_rate"] = 0.0
        return stats

    def clear_cache(self):
        """清空执行缓存"""
        self._execution_cache.clear()

    def reset_statistics(self):
        """重置统计信息"""
        self._stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "total_execution_time": 0.0
        }

    # 可选的生命周期钩子方法
    async def on_before_execute(self, context: SkillContext, config: SkillConfig):
        """执行前钩子 - 子类可以重写"""
        pass

    async def on_after_execute(self, context: SkillContext, config: SkillConfig, result: SkillResult):
        """执行后钩子 - 子类可以重写"""
        pass

    async def on_error(self, context: SkillContext, config: SkillConfig, error: Exception):
        """错误处理钩子 - 子类可以重写"""
        pass

    def validate_config(self, config: SkillConfig) -> List[str]:
        """
        验证技能配置 - 子类可以重写

        Args:
            config: 技能配置

        Returns:
            List[str]: 验证错误信息列表，空列表表示验证通过
        """
        errors = []

        # 基本验证
        if config.weight < 0 or config.weight > 10:
            errors.append("技能权重必须在0-10之间")

        if config.threshold < 0 or config.threshold > 1:
            errors.append("触发阈值必须在0-1之间")

        return errors

    def __str__(self) -> str:
        return f"Skill({self.metadata.name}, {self.metadata.category})"

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.metadata.name}>"


class StreamingSkillBase(SkillBase):
    """支持流式输出的技能基类"""

    @abstractmethod
    async def execute_stream(
        self,
        context: SkillContext,
        config: SkillConfig
    ) -> AsyncIterator[SkillResult]:
        """
        流式执行技能 - 返回异步迭代器

        Args:
            context: 技能执行上下文
            config: 技能配置

        Yields:
            SkillResult: 部分执行结果
        """
        pass

    async def execute(self, context: SkillContext, config: SkillConfig) -> SkillResult:
        """
        标准执行方法 - 收集所有流式结果
        """
        results = []
        async for partial_result in self.execute_stream(context, config):
            results.append(partial_result)

        # 合并所有部分结果
        if results:
            final_result = results[-1]
            # 合并内容
            all_content = "".join(
                result.generated_content or ""
                for result in results
                if result.generated_content
            )
            final_result.generated_content = all_content
            return final_result
        else:
            return SkillResult(
                skill_name=self.metadata.name,
                execution_id=str(uuid.uuid4()),
                status=SkillExecutionStatus.FAILED,
                error_message="流式执行未返回任何结果",
                error_code="NO_RESULTS"
            )


class CompositeSkillBase(SkillBase):
    """组合技能基类 - 可以包含多个子技能"""

    def __init__(self, metadata: SkillMetadata, sub_skills: List[SkillBase]):
        super().__init__(metadata)
        self.sub_skills = sub_skills

    @abstractmethod
    async def compose_results(
        self,
        context: SkillContext,
        config: SkillConfig,
        sub_results: List[SkillResult]
    ) -> SkillResult:
        """
        组合子技能结果

        Args:
            context: 技能执行上下文
            config: 技能配置
            sub_results: 子技能执行结果列表

        Returns:
            SkillResult: 组合后的结果
        """
        pass

    async def execute(self, context: SkillContext, config: SkillConfig) -> SkillResult:
        """执行组合技能"""
        sub_results = []

        for sub_skill in self.sub_skills:
            if sub_skill.can_handle(context, config):
                try:
                    result = await sub_skill.execute_with_monitoring(context, config)
                    sub_results.append(result)
                except Exception as e:
                    # 记录子技能执行错误，但继续执行其他子技能
                    error_result = SkillResult(
                        skill_name=sub_skill.metadata.name,
                        execution_id=str(uuid.uuid4()),
                        status=SkillExecutionStatus.FAILED,
                        error_message=str(e),
                        error_code="SUB_SKILL_ERROR"
                    )
                    sub_results.append(error_result)

        # 组合结果
        return await self.compose_results(context, config, sub_results)

    def can_handle(self, context: SkillContext, config: SkillConfig) -> bool:
        """至少有一个子技能能处理请求"""
        return any(
            sub_skill.can_handle(context, config)
            for sub_skill in self.sub_skills
        )

    def get_confidence_score(self, context: SkillContext, config: SkillConfig) -> float:
        """取子技能信心得分的最大值"""
        scores = [
            sub_skill.get_confidence_score(context, config)
            for sub_skill in self.sub_skills
            if sub_skill.can_handle(context, config)
        ]
        return max(scores) if scores else 0.0