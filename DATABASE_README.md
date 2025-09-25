# AI角色扮演网站 - 数据库设计文档

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
class Message(BaseModel):
    id: Optional[int]                   # 消息ID
    conversation_id: int                # 关联对话ID
    role: MessageRole                   # 消息角色 (user/assistant/system)
    content: str                        # 消息内容
    timestamp: datetime                 # 时间戳
    metadata: Optional[Dict[str, Any]]  # 元数据
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
    metadata TEXT DEFAULT '{}',         -- JSON object
    FOREIGN KEY (conversation_id) REFERENCES conversations (id) ON DELETE CASCADE
);
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
    metadata={"source": "web"}
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

## 数据库文件位置

默认数据库位置：`data/roleplay.db`

可以通过环境变量或初始化参数自定义路径：
```python
db = DatabaseManager("custom/path/database.db")
```