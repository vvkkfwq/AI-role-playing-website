from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum


class SkillCategory(str, Enum):
    """技能分类枚举"""
    CONVERSATION = "conversation"  # 对话技能
    KNOWLEDGE = "knowledge"       # 知识技能
    CREATIVE = "creative"         # 创意技能
    UTILITY = "utility"          # 实用技能


class SkillTrigger(BaseModel):
    """技能触发条件"""
    keywords: List[str] = Field(default_factory=list, description="触发关键词")
    patterns: List[str] = Field(default_factory=list, description="触发模式(正则表达式)")
    intent_types: List[str] = Field(default_factory=list, description="意图类型")
    emotional_states: List[str] = Field(default_factory=list, description="情绪状态")
    context_requirements: Dict[str, Any] = Field(default_factory=dict, description="上下文要求")


class SkillPriority(str, Enum):
    """技能优先级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SkillExecutionStatus(str, Enum):
    """技能执行状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class SkillMetadata(BaseModel):
    """技能元数据"""
    name: str = Field(..., min_length=1, max_length=100, description="技能名称")
    display_name: str = Field(..., min_length=1, max_length=100, description="显示名称")
    description: str = Field(..., min_length=1, max_length=500, description="技能描述")
    category: SkillCategory = Field(..., description="技能分类")
    version: str = Field(default="1.0.0", description="技能版本")
    author: str = Field(default="System", description="作者")

    # 技能能力配置
    triggers: SkillTrigger = Field(default_factory=SkillTrigger, description="触发条件")
    priority: SkillPriority = Field(default=SkillPriority.MEDIUM, description="默认优先级")
    character_compatibility: List[str] = Field(default_factory=list, description="兼容的角色名称")
    dependencies: List[str] = Field(default_factory=list, description="依赖的其他技能")

    # 性能配置
    max_execution_time: float = Field(default=30.0, ge=0.1, le=300.0, description="最大执行时间(秒)")
    concurrent_limit: int = Field(default=1, ge=1, le=10, description="并发执行限制")
    cache_results: bool = Field(default=True, description="是否缓存结果")

    # 元信息
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    enabled: bool = Field(default=True, description="是否启用")


class SkillConfig(BaseModel):
    """角色特定的技能配置"""
    skill_name: str = Field(..., description="技能名称")
    character_id: Optional[int] = Field(None, description="角色ID")
    character_name: Optional[str] = Field(None, description="角色名称")

    # 个性化参数
    parameters: Dict[str, Any] = Field(default_factory=dict, description="技能参数")
    weight: float = Field(default=1.0, ge=0.0, le=10.0, description="技能权重")
    threshold: float = Field(default=0.5, ge=0.0, le=1.0, description="触发阈值")
    priority: SkillPriority = Field(default=SkillPriority.MEDIUM, description="优先级")

    # 个性化设置
    personalization: Dict[str, Any] = Field(default_factory=dict, description="个性化设置")
    response_style: Dict[str, Any] = Field(default_factory=dict, description="响应风格")

    # 状态控制
    enabled: bool = Field(default=True, description="是否启用")
    max_uses_per_conversation: Optional[int] = Field(None, ge=1, description="每次对话最大使用次数")
    cooldown_seconds: float = Field(default=0.0, ge=0.0, description="冷却时间(秒)")


class SkillContext(BaseModel):
    """技能执行上下文"""
    # 会话信息
    conversation_id: Optional[int] = Field(None, description="会话ID")
    message_id: Optional[int] = Field(None, description="消息ID")
    user_input: str = Field(..., description="用户输入")

    # 角色信息
    character: Optional[Dict[str, Any]] = Field(None, description="当前角色信息")
    character_id: Optional[int] = Field(None, description="角色ID")

    # 历史信息
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list, description="对话历史")
    skill_history: List[Dict[str, Any]] = Field(default_factory=list, description="技能使用历史")

    # 上下文数据
    context_data: Dict[str, Any] = Field(default_factory=dict, description="上下文数据")
    session_data: Dict[str, Any] = Field(default_factory=dict, description="会话数据")

    # 执行环境
    execution_timestamp: datetime = Field(default_factory=datetime.now)
    request_id: str = Field(..., description="请求ID")

    # 意图识别结果
    detected_intent: Optional[str] = Field(None, description="检测到的意图")
    intent_confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="意图置信度")

    # 情感分析
    emotional_state: Optional[str] = Field(None, description="情绪状态")
    sentiment_score: float = Field(default=0.0, ge=-1.0, le=1.0, description="情感得分")


class SkillResult(BaseModel):
    """技能执行结果"""
    skill_name: str = Field(..., description="技能名称")
    execution_id: str = Field(..., description="执行ID")
    status: SkillExecutionStatus = Field(..., description="执行状态")

    # 结果数据
    result_data: Dict[str, Any] = Field(default_factory=dict, description="结果数据")
    generated_content: Optional[str] = Field(None, description="生成的内容")
    structured_output: Optional[Dict[str, Any]] = Field(None, description="结构化输出")

    # 性能指标
    execution_time: float = Field(default=0.0, ge=0.0, description="执行时间(秒)")
    memory_usage: Optional[float] = Field(None, ge=0.0, description="内存使用(MB)")
    api_calls: int = Field(default=0, ge=0, description="API调用次数")

    # 质量评估
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0, description="置信度")
    relevance_score: float = Field(default=0.0, ge=0.0, le=1.0, description="相关性得分")
    quality_score: float = Field(default=0.0, ge=0.0, le=1.0, description="质量得分")

    # 错误信息
    error_message: Optional[str] = Field(None, description="错误信息")
    error_code: Optional[str] = Field(None, description="错误代码")
    warnings: List[str] = Field(default_factory=list, description="警告信息")

    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict, description="执行元数据")
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = Field(None, description="完成时间")


class SkillExecution(BaseModel):
    """技能执行记录"""
    id: Optional[str] = Field(None, description="执行ID")
    skill_name: str = Field(..., description="技能名称")
    character_id: Optional[int] = Field(None, description="角色ID")
    conversation_id: Optional[int] = Field(None, description="会话ID")
    message_id: Optional[int] = Field(None, description="消息ID")

    # 执行状态
    status: SkillExecutionStatus = Field(..., description="执行状态")
    progress: float = Field(default=0.0, ge=0.0, le=1.0, description="执行进度")

    # 时间信息
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    execution_time: Optional[float] = Field(None, ge=0.0, description="执行时间(秒)")

    # 执行结果
    result: Optional[SkillResult] = Field(None, description="执行结果")

    # 性能数据
    performance_metrics: Dict[str, Any] = Field(default_factory=dict, description="性能指标")

    class Config:
        from_attributes = True


class IntentClassification(BaseModel):
    """意图识别结果"""
    input_text: str = Field(..., description="输入文本")
    detected_intent: str = Field(..., description="检测到的意图")
    confidence: float = Field(..., ge=0.0, le=1.0, description="置信度")

    # 候选意图
    alternative_intents: List[Dict[str, float]] = Field(default_factory=list, description="候选意图及其置信度")

    # 提取的实体
    entities: Dict[str, Any] = Field(default_factory=dict, description="提取的实体")

    # 推荐技能
    recommended_skills: List[Dict[str, Any]] = Field(default_factory=list, description="推荐的技能")

    # 上下文信息
    context_factors: Dict[str, Any] = Field(default_factory=dict, description="影响因素")

    # 元数据
    processing_time: float = Field(default=0.0, ge=0.0, description="处理时间(秒)")
    model_version: str = Field(default="1.0.0", description="模型版本")
    created_at: datetime = Field(default_factory=datetime.now)


class PerformanceMetrics(BaseModel):
    """性能指标"""
    skill_name: str = Field(..., description="技能名称")
    character_id: Optional[int] = Field(None, description="角色ID")

    # 执行统计
    total_executions: int = Field(default=0, ge=0, description="总执行次数")
    successful_executions: int = Field(default=0, ge=0, description="成功执行次数")
    failed_executions: int = Field(default=0, ge=0, description="失败执行次数")

    # 性能指标
    average_execution_time: float = Field(default=0.0, ge=0.0, description="平均执行时间(秒)")
    min_execution_time: float = Field(default=0.0, ge=0.0, description="最小执行时间(秒)")
    max_execution_time: float = Field(default=0.0, ge=0.0, description="最大执行时间(秒)")

    # 质量指标
    average_confidence_score: float = Field(default=0.0, ge=0.0, le=1.0, description="平均置信度")
    average_relevance_score: float = Field(default=0.0, ge=0.0, le=1.0, description="平均相关性")
    average_quality_score: float = Field(default=0.0, ge=0.0, le=1.0, description="平均质量")

    # 用户反馈
    user_satisfaction_score: float = Field(default=0.0, ge=0.0, le=5.0, description="用户满意度(1-5)")
    positive_feedback_count: int = Field(default=0, ge=0, description="正面反馈数")
    negative_feedback_count: int = Field(default=0, ge=0, description="负面反馈数")

    # 使用统计
    daily_usage_count: Dict[str, int] = Field(default_factory=dict, description="每日使用统计")
    peak_usage_time: Optional[str] = Field(None, description="使用高峰时间")

    # 时间信息
    last_updated: datetime = Field(default_factory=datetime.now)
    measurement_period_start: datetime = Field(default_factory=datetime.now)
    measurement_period_end: datetime = Field(default_factory=datetime.now)

    class Config:
        from_attributes = True