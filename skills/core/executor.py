import asyncio
import time
import uuid
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from .base import SkillBase
from .models import SkillContext, SkillConfig, SkillResult, SkillExecution, SkillExecutionStatus

logger = logging.getLogger(__name__)


class AsyncSkillExecutor:
    """异步技能执行器 - 负责管理和执行技能"""

    def __init__(self, max_concurrent_executions: int = 10):
        """
        初始化异步技能执行器

        Args:
            max_concurrent_executions: 最大并发执行数
        """
        self.max_concurrent_executions = max_concurrent_executions
        self._active_executions: Dict[str, SkillExecution] = {}
        self._execution_semaphore = asyncio.Semaphore(max_concurrent_executions)
        self._thread_executor = ThreadPoolExecutor(max_workers=max_concurrent_executions)

    async def execute_skill(
        self,
        skill: SkillBase,
        context: SkillContext,
        config: SkillConfig
    ) -> SkillResult:
        """
        执行单个技能

        Args:
            skill: 技能实例
            context: 执行上下文
            config: 技能配置

        Returns:
            SkillResult: 执行结果
        """
        execution_id = str(uuid.uuid4())
        execution = SkillExecution(
            id=execution_id,
            skill_name=skill.metadata.name,
            character_id=context.character_id,
            conversation_id=context.conversation_id,
            message_id=context.message_id,
            status=SkillExecutionStatus.PENDING,
            started_at=datetime.now()
        )

        try:
            # 记录执行开始
            self._active_executions[execution_id] = execution
            execution.status = SkillExecutionStatus.RUNNING
            execution.progress = 0.1

            logger.info(f"开始执行技能: {skill.metadata.name} (ID: {execution_id})")

            # 使用信号量控制并发
            async with self._execution_semaphore:
                # 检查技能是否能处理当前请求
                if not skill.can_handle(context, config):
                    raise ValueError(f"技能 '{skill.metadata.name}' 无法处理当前请求")

                execution.progress = 0.3

                # 执行前钩子
                await skill.on_before_execute(context, config)
                execution.progress = 0.4

                # 执行技能
                result = await skill.execute_with_monitoring(context, config)
                execution.progress = 0.9

                # 执行后钩子
                await skill.on_after_execute(context, config, result)
                execution.progress = 1.0

                # 更新执行记录
                execution.status = SkillExecutionStatus.COMPLETED
                execution.completed_at = datetime.now()
                execution.execution_time = (execution.completed_at - execution.started_at).total_seconds()
                execution.result = result

                logger.info(f"技能执行完成: {skill.metadata.name} (耗时: {execution.execution_time:.2f}秒)")

                return result

        except asyncio.TimeoutError:
            execution.status = SkillExecutionStatus.TIMEOUT
            execution.completed_at = datetime.now()
            execution.execution_time = (execution.completed_at - execution.started_at).total_seconds()

            error_result = SkillResult(
                skill_name=skill.metadata.name,
                execution_id=execution_id,
                status=SkillExecutionStatus.TIMEOUT,
                error_message="技能执行超时",
                error_code="TIMEOUT",
                execution_time=execution.execution_time
            )
            execution.result = error_result

            logger.warning(f"技能执行超时: {skill.metadata.name}")
            return error_result

        except Exception as e:
            execution.status = SkillExecutionStatus.FAILED
            execution.completed_at = datetime.now()
            execution.execution_time = (execution.completed_at - execution.started_at).total_seconds()

            error_result = SkillResult(
                skill_name=skill.metadata.name,
                execution_id=execution_id,
                status=SkillExecutionStatus.FAILED,
                error_message=str(e),
                error_code="EXECUTION_ERROR",
                execution_time=execution.execution_time
            )
            execution.result = error_result

            # 调用错误处理钩子
            try:
                await skill.on_error(context, config, e)
            except Exception as hook_error:
                logger.error(f"技能错误处理钩子执行失败: {hook_error}")

            logger.error(f"技能执行失败: {skill.metadata.name} - {e}")
            return error_result

        finally:
            # 清理执行记录
            if execution_id in self._active_executions:
                del self._active_executions[execution_id]

    async def execute_skills_parallel(
        self,
        skill_configs: List[Tuple[SkillBase, SkillContext, SkillConfig]]
    ) -> List[SkillResult]:
        """
        并行执行多个技能

        Args:
            skill_configs: 技能配置列表，每个元素为(技能实例, 上下文, 配置)

        Returns:
            List[SkillResult]: 执行结果列表
        """
        if not skill_configs:
            return []

        logger.info(f"开始并行执行 {len(skill_configs)} 个技能")

        # 创建协程任务
        tasks = []
        for skill, context, config in skill_configs:
            task = asyncio.create_task(
                self.execute_skill(skill, context, config),
                name=f"skill_{skill.metadata.name}"
            )
            tasks.append(task)

        # 等待所有任务完成
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理异常结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                skill_name = skill_configs[i][0].metadata.name
                error_result = SkillResult(
                    skill_name=skill_name,
                    execution_id=str(uuid.uuid4()),
                    status=SkillExecutionStatus.FAILED,
                    error_message=str(result),
                    error_code="PARALLEL_EXECUTION_ERROR"
                )
                processed_results.append(error_result)
                logger.error(f"并行执行技能失败: {skill_name} - {result}")
            else:
                processed_results.append(result)

        logger.info(f"并行执行完成，成功: {sum(1 for r in processed_results if r.status == SkillExecutionStatus.COMPLETED)} 个")

        return processed_results

    async def execute_skills_sequential(
        self,
        skill_configs: List[Tuple[SkillBase, SkillContext, SkillConfig]],
        stop_on_error: bool = False
    ) -> List[SkillResult]:
        """
        顺序执行多个技能

        Args:
            skill_configs: 技能配置列表
            stop_on_error: 是否在遇到错误时停止执行

        Returns:
            List[SkillResult]: 执行结果列表
        """
        results = []

        for skill, context, config in skill_configs:
            try:
                result = await self.execute_skill(skill, context, config)
                results.append(result)

                # 如果设置了遇到错误停止，且当前执行失败，则停止后续执行
                if stop_on_error and result.status in [SkillExecutionStatus.FAILED, SkillExecutionStatus.TIMEOUT]:
                    logger.warning(f"技能执行失败，停止后续执行: {skill.metadata.name}")
                    break

            except Exception as e:
                error_result = SkillResult(
                    skill_name=skill.metadata.name,
                    execution_id=str(uuid.uuid4()),
                    status=SkillExecutionStatus.FAILED,
                    error_message=str(e),
                    error_code="SEQUENTIAL_EXECUTION_ERROR"
                )
                results.append(error_result)

                if stop_on_error:
                    logger.warning(f"技能执行异常，停止后续执行: {skill.metadata.name} - {e}")
                    break

        return results

    async def execute_skills_with_strategy(
        self,
        skill_configs: List[Tuple[SkillBase, SkillContext, SkillConfig]],
        strategy: str = "parallel"
    ) -> List[SkillResult]:
        """
        使用指定策略执行技能

        Args:
            skill_configs: 技能配置列表
            strategy: 执行策略 ("parallel", "sequential", "adaptive")

        Returns:
            List[SkillResult]: 执行结果列表
        """
        if strategy == "parallel":
            return await self.execute_skills_parallel(skill_configs)
        elif strategy == "sequential":
            return await self.execute_skills_sequential(skill_configs)
        elif strategy == "adaptive":
            return await self._execute_skills_adaptive(skill_configs)
        else:
            raise ValueError(f"不支持的执行策略: {strategy}")

    async def _execute_skills_adaptive(
        self,
        skill_configs: List[Tuple[SkillBase, SkillContext, SkillConfig]]
    ) -> List[SkillResult]:
        """
        自适应执行策略 - 根据技能特性和系统负载选择最优执行方式

        Args:
            skill_configs: 技能配置列表

        Returns:
            List[SkillResult]: 执行结果列表
        """
        if not skill_configs:
            return []

        # 分析技能特性
        parallel_skills = []
        sequential_skills = []

        for skill, context, config in skill_configs:
            # 根据技能元数据决定执行方式
            if (skill.metadata.concurrent_limit > 1 and
                skill.metadata.max_execution_time <= 10.0):
                parallel_skills.append((skill, context, config))
            else:
                sequential_skills.append((skill, context, config))

        results = []

        # 先并行执行快速技能
        if parallel_skills:
            parallel_results = await self.execute_skills_parallel(parallel_skills)
            results.extend(parallel_results)

        # 再顺序执行需要串行的技能
        if sequential_skills:
            sequential_results = await self.execute_skills_sequential(sequential_skills)
            results.extend(sequential_results)

        return results

    def get_active_executions(self) -> Dict[str, SkillExecution]:
        """获取当前活跃的执行任务"""
        return self._active_executions.copy()

    def get_execution_statistics(self) -> Dict[str, Any]:
        """获取执行统计信息"""
        active_count = len(self._active_executions)
        return {
            "active_executions": active_count,
            "max_concurrent": self.max_concurrent_executions,
            "available_slots": self.max_concurrent_executions - active_count,
            "semaphore_value": self._execution_semaphore._value
        }

    async def cancel_execution(self, execution_id: str) -> bool:
        """
        取消指定的执行任务

        Args:
            execution_id: 执行ID

        Returns:
            bool: 是否成功取消
        """
        if execution_id not in self._active_executions:
            return False

        execution = self._active_executions[execution_id]
        execution.status = SkillExecutionStatus.CANCELLED
        execution.completed_at = datetime.now()
        execution.execution_time = (execution.completed_at - execution.started_at).total_seconds()

        # 从活跃执行列表中移除
        del self._active_executions[execution_id]

        logger.info(f"取消技能执行: {execution.skill_name} (ID: {execution_id})")
        return True

    async def shutdown(self):
        """关闭执行器，清理资源"""
        # 等待所有活跃任务完成
        if self._active_executions:
            logger.info(f"等待 {len(self._active_executions)} 个活跃任务完成...")
            # 这里可以添加等待逻辑或强制取消逻辑

        # 关闭线程池
        self._thread_executor.shutdown(wait=True)
        logger.info("技能执行器已关闭")