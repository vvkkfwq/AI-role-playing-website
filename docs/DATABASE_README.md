# AI角色扮演网站 - 数据库设计文档

## 📋 文档信息

- **文档版本**: v2.0
- **适用系统**: AI角色扮演聊天网站
- **更新日期**: 2025-09-27
- **文档类型**: 数据库设计和开发指南

> **相关文档**:
> - [AI智能技能系统开发指南](skill_system_update_v2.0.md)
> - [语音转文字集成指南](STT_INTEGRATION_GUIDE.md)
> - [文字转语音集成指南](TTS_INTEGRATION_GUIDE.md)

---

## 概述

基于Pydantic和SQLite的角色扮演系统，包含完整的数据模型和CRUD操作。

## 文件结构

```
├── models.py              # Pydantic数据模型定义
├── database.py            # 数据库管理器和CRUD操作
├── preset_characters.py   # 预设角色数据
├── init_database.py       # 数据库初始化脚本
├── test_database.py       # 数据库测试脚本
└── data/
    └── roleplay.db        # SQLite数据库文件
```

## 数据模型

### 1. Character（角色模型）

```python
class Character(BaseModel):
    id: Optional[int]                    # 唯一标识符
    name: str                           # 角色名称
    title: str                          # 角色描述
    avatar_emoji: str                   # 角色表情符号
    personality: List[str]              # 性格特征列表
    prompt_template: str                # 角色扮演提示词
    skills: List[str]                   # 角色技能列表
    voice_config: VoiceConfig           # 语音配置
    created_at: Optional[datetime]      # 创建时间
    updated_at: Optional[datetime]      # 更新时间

class CharacterCreate(BaseModel):
    name: str                           # 角色名称
    title: str                          # 角色描述
    avatar_emoji: str = "🎭"           # 角色表情符号
    personality: List[str]              # 性格特征列表
    prompt_template: str                # 角色扮演提示词
    skills: List[str] = []              # 角色技能列表
    voice_config: VoiceConfig           # 语音配置

class CharacterUpdate(BaseModel):
    name: Optional[str] = None          # 可选更新字段
    title: Optional[str] = None
    avatar_emoji: Optional[str] = None
    personality: Optional[List[str]] = None
    prompt_template: Optional[str] = None
    skills: Optional[List[str]] = None
    voice_config: Optional[VoiceConfig] = None
```

### 2. VoiceConfig（语音配置）

```python
class VoiceConfig(BaseModel):
    provider: str = "openai"            # 语音提供商
    voice_id: str = "alloy"            # 语音ID
    speed: float = 1.0                 # 语速 (0.25-4.0)
    pitch: float = 1.0                 # 音调 (0.5-2.0)
    volume: float = 1.0                # 音量 (0.0-1.0)
```

### 3. Conversation（对话模型）

```python
class Conversation(BaseModel):
    id: Optional[int]                   # 对话ID
    character_id: int                   # 关联角色ID
    title: Optional[str]                # 对话标题
    created_at: datetime                # 创建时间
    updated_at: datetime                # 更新时间
    messages: List[Message]             # 消息列表
```

### 4. Message（消息模型）

```python
class MessageRole(str, Enum):
    USER = "user"                       # 用户消息
    ASSISTANT = "assistant"             # AI助手消息
    SYSTEM = "system"                   # 系统消息

class Message(BaseModel):
    id: Optional[int]                   # 消息ID
    conversation_id: int                # 关联对话ID
    role: MessageRole                   # 消息角色 (user/assistant/system)
    content: str                        # 消息内容
    timestamp: datetime                 # 时间戳
    metadata: Optional[Dict[str, Any]]  # 元数据（音频信息、技能执行等）

class MessageCreate(BaseModel):
    conversation_id: int                # 关联对话ID
    role: MessageRole                   # 消息角色
    content: str                        # 消息内容
    metadata: Optional[Dict[str, Any]] = None  # 可选元数据
```

### 5. AI技能系统模型

> **参考**: 更多技能系统细节请参见 [AI智能技能系统开发指南](skill_system_update_v2.0.md)

#### 5.1 SkillMetadata（技能元数据）

```python
class SkillCategory(str, Enum):
    CONVERSATION = "conversation"       # 对话技能
    KNOWLEDGE = "knowledge"            # 知识技能
    CREATIVE = "creative"              # 创意技能
    UTILITY = "utility"                # 实用技能

class SkillPriority(str, Enum):
    LOW = "low"                        # 低优先级
    MEDIUM = "medium"                  # 中优先级
    HIGH = "high"                      # 高优先级
    CRITICAL = "critical"              # 关键优先级

class SkillTrigger(BaseModel):
    keywords: List[str] = []           # 触发关键词
    patterns: List[str] = []           # 触发模式(正则表达式)
    intent_types: List[str] = []       # 意图类型
    emotional_states: List[str] = []   # 情绪状态
    context_requirements: Dict[str, Any] = {}  # 上下文要求

class SkillMetadata(BaseModel):
    name: str                          # 技能名称
    display_name: str                  # 显示名称
    description: str                   # 技能描述
    category: SkillCategory            # 技能分类
    version: str = "1.0.0"            # 技能版本
    author: str = "System"            # 作者
    triggers: SkillTrigger             # 触发条件
    priority: SkillPriority = SkillPriority.MEDIUM  # 默认优先级
    character_compatibility: List[str] = []  # 兼容的角色名称
    dependencies: List[str] = []       # 依赖的其他技能
    max_execution_time: float = 30.0  # 最大执行时间(秒)
    concurrent_limit: int = 1          # 并发执行限制
    cache_results: bool = True         # 是否缓存结果
    enabled: bool = True               # 是否启用
    created_at: datetime               # 创建时间
    updated_at: datetime               # 更新时间
```

#### 5.2 SkillConfig（技能配置）

```python
class SkillConfig(BaseModel):
    skill_name: str                    # 技能名称
    character_id: Optional[int] = None # 角色ID
    character_name: Optional[str] = None  # 角色名称
    parameters: Dict[str, Any] = {}    # 技能参数
    weight: float = 1.0               # 技能权重(0.0-10.0)
    threshold: float = 0.5            # 触发阈值(0.0-1.0)
    priority: SkillPriority = SkillPriority.MEDIUM  # 优先级
    personalization: Dict[str, Any] = {}  # 个性化设置
    response_style: Dict[str, Any] = {}   # 响应风格
    enabled: bool = True              # 是否启用
    max_uses_per_conversation: Optional[int] = None  # 每次对话最大使用次数
    cooldown_seconds: float = 0.0     # 冷却时间(秒)
```

#### 5.3 SkillResult（技能执行结果）

```python
class SkillExecutionStatus(str, Enum):
    PENDING = "pending"                # 等待执行
    RUNNING = "running"                # 正在执行
    COMPLETED = "completed"            # 执行完成
    FAILED = "failed"                  # 执行失败
    TIMEOUT = "timeout"                # 执行超时
    CANCELLED = "cancelled"            # 执行取消

class SkillResult(BaseModel):
    skill_name: str                    # 技能名称
    execution_id: str                  # 执行ID
    status: SkillExecutionStatus       # 执行状态
    result_data: Dict[str, Any] = {}   # 结果数据
    generated_content: Optional[str] = None  # 生成的内容
    structured_output: Optional[Dict[str, Any]] = None  # 结构化输出
    execution_time: float = 0.0        # 执行时间(秒)
    memory_usage: Optional[float] = None  # 内存使用(MB)
    api_calls: int = 0                # API调用次数
    confidence_score: float = 0.0      # 置信度(0-1)
    relevance_score: float = 0.0       # 相关性得分(0-1)
    quality_score: float = 0.0         # 质量得分(0-1)
    error_message: Optional[str] = None  # 错误信息
    error_code: Optional[str] = None   # 错误代码
    warnings: List[str] = []           # 警告信息
    metadata: Dict[str, Any] = {}      # 执行元数据
    created_at: datetime               # 创建时间
    completed_at: Optional[datetime] = None  # 完成时间
```

## 数据库表结构

### characters（角色表）
```sql
CREATE TABLE characters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    avatar_emoji TEXT DEFAULT '🎭',
    personality TEXT NOT NULL,          -- JSON array
    prompt_template TEXT NOT NULL,
    skills TEXT DEFAULT '[]',           -- JSON array
    voice_config TEXT DEFAULT '{}',     -- JSON object
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### conversations（对话表）
```sql
CREATE TABLE conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id INTEGER NOT NULL,
    title TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (character_id) REFERENCES characters (id) ON DELETE CASCADE
);
```

### messages（消息表）
```sql
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT DEFAULT '{}',         -- JSON object (音频信息、技能执行结果等)
    FOREIGN KEY (conversation_id) REFERENCES conversations (id) ON DELETE CASCADE
);

-- 消息索引优化
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_messages_timestamp ON messages(timestamp);
CREATE INDEX idx_messages_role ON messages(role);
```

### skill_executions（技能执行记录表）
```sql
CREATE TABLE skill_executions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    skill_name TEXT NOT NULL,
    character_id INTEGER,
    conversation_id INTEGER,
    message_id INTEGER,
    execution_id TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('pending', 'running', 'completed', 'failed', 'timeout', 'cancelled')),
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    execution_time REAL,
    confidence_score REAL CHECK (confidence_score >= 0 AND confidence_score <= 1),
    relevance_score REAL CHECK (relevance_score >= 0 AND relevance_score <= 1),
    quality_score REAL CHECK (quality_score >= 0 AND quality_score <= 1),
    result_data TEXT DEFAULT '{}',      -- JSON object
    error_message TEXT,
    metadata TEXT DEFAULT '{}',         -- JSON object
    FOREIGN KEY (character_id) REFERENCES characters (id) ON DELETE SET NULL,
    FOREIGN KEY (conversation_id) REFERENCES conversations (id) ON DELETE CASCADE,
    FOREIGN KEY (message_id) REFERENCES messages (id) ON DELETE CASCADE
);

-- 技能执行索引
CREATE INDEX idx_skill_executions_skill_name ON skill_executions(skill_name);
CREATE INDEX idx_skill_executions_character_id ON skill_executions(character_id);
CREATE INDEX idx_skill_executions_status ON skill_executions(status);
CREATE INDEX idx_skill_executions_started_at ON skill_executions(started_at);
```

### character_skill_configs（角色技能配置表）
```sql
CREATE TABLE character_skill_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id INTEGER NOT NULL,
    skill_name TEXT NOT NULL,
    weight REAL DEFAULT 1.0 CHECK (weight >= 0 AND weight <= 10),
    threshold REAL DEFAULT 0.5 CHECK (threshold >= 0 AND threshold <= 1),
    priority TEXT DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'critical')),
    parameters TEXT DEFAULT '{}',       -- JSON object
    personalization TEXT DEFAULT '{}', -- JSON object
    response_style TEXT DEFAULT '{}',   -- JSON object
    enabled BOOLEAN DEFAULT 1,
    max_uses_per_conversation INTEGER,
    cooldown_seconds REAL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (character_id) REFERENCES characters (id) ON DELETE CASCADE,
    UNIQUE(character_id, skill_name)
);

-- 角色技能配置索引
CREATE INDEX idx_character_skill_configs_character_id ON character_skill_configs(character_id);
CREATE INDEX idx_character_skill_configs_skill_name ON character_skill_configs(skill_name);
CREATE INDEX idx_character_skill_configs_enabled ON character_skill_configs(enabled);
```

### skill_performance_metrics（技能性能指标表）
```sql
CREATE TABLE skill_performance_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    skill_name TEXT NOT NULL,
    character_id INTEGER,
    total_executions INTEGER DEFAULT 0,
    successful_executions INTEGER DEFAULT 0,
    failed_executions INTEGER DEFAULT 0,
    average_execution_time REAL DEFAULT 0,
    min_execution_time REAL DEFAULT 0,
    max_execution_time REAL DEFAULT 0,
    average_confidence_score REAL DEFAULT 0,
    average_relevance_score REAL DEFAULT 0,
    average_quality_score REAL DEFAULT 0,
    user_satisfaction_score REAL DEFAULT 0,
    positive_feedback_count INTEGER DEFAULT 0,
    negative_feedback_count INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    measurement_period_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    measurement_period_end TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (character_id) REFERENCES characters (id) ON DELETE SET NULL,
    UNIQUE(skill_name, character_id)
);

-- 性能指标索引
CREATE INDEX idx_skill_performance_metrics_skill_name ON skill_performance_metrics(skill_name);
CREATE INDEX idx_skill_performance_metrics_character_id ON skill_performance_metrics(character_id);
CREATE INDEX idx_skill_performance_metrics_last_updated ON skill_performance_metrics(last_updated);
```

## 预设角色

系统包含3个预设角色：

### 1. 哈利·波特 ⚡
- **角色描述**: 勇敢的霍格沃茨学生
- **性格特征**: 勇敢无畏、忠诚友善、正义感强、有时冲动、保护弱者、谦逊朴实
- **技能**: 防御黑魔法、魁地奇飞行、守护神咒语、魔法决斗、领导能力、英勇精神

### 2. 苏格拉底 🏛️
- **角色描述**: 智慧的古希腊哲学家
- **性格特征**: 睿智深刻、善于提问、追求真理、谦逊好学、理性思辨、启发他人
- **技能**: 哲学思辨、逻辑推理、道德教育、苏格拉底方法、智慧启发、真理探索

### 3. 阿尔伯特·爱因斯坦 🧠
- **角色描述**: 好奇的理论物理学家
- **性格特征**: 极度好奇、想象力丰富、深度思考、幽默风趣、独立思考、热爱和平
- **技能**: 理论物理、数学建模、思想实验、科学创新、逻辑分析、直觉洞察

## CRUD操作

### 角色操作
```python
# 创建角色
character = db.create_character(CharacterCreate(...))

# 获取角色
character = db.get_character_by_id(1)
character = db.get_character_by_name("哈利·波特")
characters = db.get_all_characters()

# 更新角色
updated_character = db.update_character(1, CharacterUpdate(...))

# 删除角色
success = db.delete_character(1)
```

### 对话操作
```python
# 创建对话
conversation_id = db.create_conversation(character_id, title="对话标题")

# 获取对话
conversation = db.get_conversation_by_id(conversation_id)
conversations = db.get_conversations_by_character(character_id)

# 删除对话
success = db.delete_conversation(conversation_id)
```

### 消息操作
```python
# 添加消息
message_id = db.add_message(
    conversation_id=1,
    role="user",
    content="你好！",
    metadata={
        "source": "web",
        "audio": {
            "file_path": "/path/to/audio.wav",
            "duration": 2.5,
            "stt_result": {
                "confidence": 0.92,
                "method": "whisper"
            }
        }
    }
)

# 添加带技能执行结果的消息
message_id = db.add_message(
    conversation_id=1,
    role="assistant",
    content="我理解你的感受...",
    metadata={
        "skills_executed": [
            {
                "skill_name": "emotional_support",
                "confidence_score": 0.85,
                "quality_score": 0.9,
                "execution_time": 1.2
            }
        ],
        "tts": {
            "voice_id": "echo",
            "cached": True,
            "file_path": "/path/to/tts.mp3"
        }
    }
)
```

### 技能系统操作

#### 技能执行记录
```python
# 记录技能执行
execution_id = db.create_skill_execution(
    skill_name="emotional_support",
    character_id=1,
    conversation_id=1,
    message_id=1,
    execution_id="exec_123",
    status="completed",
    execution_time=1.5,
    confidence_score=0.85,
    result_data={"emotion_type": "sadness", "support_style": "harry"}
)

# 查询技能执行历史
executions = db.get_skill_executions_by_character(character_id=1)
recent_executions = db.get_recent_skill_executions(limit=10)
```

#### 角色技能配置
```python
# 设置角色技能配置
config_id = db.set_character_skill_config(
    character_id=1,
    skill_name="emotional_support",
    weight=1.5,
    threshold=0.4,
    priority="high",
    parameters={"style": "brave_encouragement"},
    personalization={"use_personal_experience": True}
)

# 获取角色技能配置
configs = db.get_character_skill_configs(character_id=1)
config = db.get_character_skill_config(character_id=1, skill_name="emotional_support")
```

#### 性能指标
```python
# 更新技能性能指标
db.update_skill_performance_metrics(
    skill_name="emotional_support",
    character_id=1,
    execution_result={
        "execution_time": 1.2,
        "confidence_score": 0.85,
        "quality_score": 0.9,
        "success": True
    }
)

# 获取性能统计
metrics = db.get_skill_performance_metrics(
    skill_name="emotional_support",
    character_id=1
)
```

## 使用方法

### 1. 初始化数据库
```bash
# 初始化新数据库
python init_database.py

# 重置数据库并创建示例数据
python init_database.py --reset --sample-data
```

### 2. 运行测试
```bash
# 测试所有CRUD操作
python test_database.py
```

### 3. 在代码中使用
```python
from database import DatabaseManager
from models import CharacterCreate, VoiceConfig

# 初始化数据库管理器
db = DatabaseManager()

# 创建新角色
new_character = CharacterCreate(
    name="新角色",
    title="角色描述",
    personality=["友善", "智慧"],
    prompt_template="你是一个友善的角色...",
    skills=["技能1", "技能2"],
    voice_config=VoiceConfig(voice_id="nova")
)

character = db.create_character(new_character)
```

## 特性

### 核心功能
- ✅ 完整的Pydantic数据验证
- ✅ 类型注解和IDE支持
- ✅ 外键约束和数据完整性
- ✅ JSON字段支持复杂数据结构
- ✅ 自动时间戳管理
- ✅ 级联删除操作
- ✅ 上下文管理器确保连接安全
- ✅ 完整的CRUD操作
- ✅ 错误处理和验证
- ✅ 预设角色和示例数据

### AI技能系统支持
- ✅ 技能执行记录追踪
- ✅ 角色专属技能配置
- ✅ 性能指标统计分析
- ✅ 多维度质量评估
- ✅ 技能使用历史查询
- ✅ 实时状态监控
- ✅ 配置热更新支持
- ✅ 分级错误处理

### 音频功能集成
- ✅ STT结果元数据存储
- ✅ TTS生成信息记录
- ✅ 音频文件路径管理
- ✅ 语音质量统计
- ✅ 缓存状态跟踪

### 性能优化
- ✅ 数据库索引优化
- ✅ 查询性能调优
- ✅ 事务完整性保证
- ✅ 连接池管理
- ✅ 批量操作支持

## 数据库文件位置

默认数据库位置：`data/roleplay.db`

可以通过环境变量或初始化参数自定义路径：
```python
db = DatabaseManager("custom/path/database.db")
```