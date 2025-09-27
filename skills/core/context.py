from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

from .models import SkillContext


class ContextManager:
    """上下文管理器 - 管理技能执行的上下文信息"""

    def __init__(self):
        self._global_context: Dict[str, Any] = {}
        self._session_contexts: Dict[str, Dict[str, Any]] = {}
        self._conversation_contexts: Dict[int, Dict[str, Any]] = {}

    def create_skill_context(
        self,
        user_input: str,
        character_id: Optional[int] = None,
        conversation_id: Optional[int] = None,
        message_id: Optional[int] = None,
        character_info: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        session_id: Optional[str] = None
    ) -> SkillContext:
        """
        创建技能执行上下文

        Args:
            user_input: 用户输入
            character_id: 角色ID
            conversation_id: 会话ID
            message_id: 消息ID
            character_info: 角色信息
            conversation_history: 对话历史
            session_id: 会话ID

        Returns:
            SkillContext: 技能执行上下文
        """
        request_id = str(uuid.uuid4())

        # 获取会话上下文数据
        session_data = {}
        if session_id:
            session_data = self._session_contexts.get(session_id, {})

        # 获取对话上下文数据
        conversation_context_data = {}
        if conversation_id:
            conversation_context_data = self._conversation_contexts.get(conversation_id, {})

        # 合并上下文数据
        context_data = {
            **self._global_context,
            **conversation_context_data,
            **session_data
        }

        return SkillContext(
            conversation_id=conversation_id,
            message_id=message_id,
            user_input=user_input,
            character=character_info,
            character_id=character_id,
            conversation_history=conversation_history or [],
            skill_history=self._get_skill_history(conversation_id),
            context_data=context_data,
            session_data=session_data,
            execution_timestamp=datetime.now(),
            request_id=request_id
        )

    def update_global_context(self, key: str, value: Any):
        """更新全局上下文"""
        self._global_context[key] = value

    def update_session_context(self, session_id: str, key: str, value: Any):
        """更新会话上下文"""
        if session_id not in self._session_contexts:
            self._session_contexts[session_id] = {}
        self._session_contexts[session_id][key] = value

    def update_conversation_context(self, conversation_id: int, key: str, value: Any):
        """更新对话上下文"""
        if conversation_id not in self._conversation_contexts:
            self._conversation_contexts[conversation_id] = {}
        self._conversation_contexts[conversation_id][key] = value

    def get_global_context(self) -> Dict[str, Any]:
        """获取全局上下文"""
        return self._global_context.copy()

    def get_session_context(self, session_id: str) -> Dict[str, Any]:
        """获取会话上下文"""
        return self._session_contexts.get(session_id, {}).copy()

    def get_conversation_context(self, conversation_id: int) -> Dict[str, Any]:
        """获取对话上下文"""
        return self._conversation_contexts.get(conversation_id, {}).copy()

    def clear_session_context(self, session_id: str):
        """清空会话上下文"""
        if session_id in self._session_contexts:
            del self._session_contexts[session_id]

    def clear_conversation_context(self, conversation_id: int):
        """清空对话上下文"""
        if conversation_id in self._conversation_contexts:
            del self._conversation_contexts[conversation_id]

    def _get_skill_history(self, conversation_id: Optional[int]) -> List[Dict[str, Any]]:
        """获取技能使用历史"""
        if not conversation_id:
            return []

        # 这里应该从数据库或缓存中获取技能使用历史
        # 暂时返回空列表，后续集成数据库时实现
        return []

    def cleanup_old_contexts(self, max_age_hours: int = 24):
        """清理过期的上下文数据"""
        # 实现上下文清理逻辑
        # 可以基于时间戳清理长时间未使用的会话和对话上下文
        pass