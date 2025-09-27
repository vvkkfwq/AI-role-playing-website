# AI 角色扮演聊天网站

基于 Streamlit 和 OpenAI 构建的网页版 AI 角色扮演聊天应用，采用 Pydantic 数据模型和 SQLite 数据库，支持语音输入和语音合成功能。

## ✨ 功能特色

- 🎭 **多角色扮演**: 预设 3 个经典角色（哈利·波特、苏格拉底、爱因斯坦）
- 💬 **实时对话**: 流畅的聊天界面，支持角色头像和个性化回复
- 🎤 **语音输入**: 支持录音输入，自动转换为文本（Speech-to-Text）
- 🔊 **语音合成**: 角色专属语音回复，支持多种声音选择（Text-to-Speech）
- 📚 **对话历史**: 完整的对话记录和管理功能，包含音频元数据
- 🔧 **数据模型**: 基于 Pydantic 的完整数据验证和类型注解
- 🗄️ **数据库管理**: SQLite 数据库，支持完整的 CRUD 操作
- 🎨 **个性化**: 每个角色都有独特的性格特征、技能和语音配置
- 🚀 **智能缓存**: TTS 音频缓存和自动清理机制

## 🏗️ 项目结构

```
AI-role-playing-website/
├── app/                   # 应用核心模块
│   ├── main.py           # Streamlit 主应用
│   ├── models.py         # Pydantic 数据模型
│   ├── database.py       # 数据库管理和 CRUD 操作
│   └── __init__.py
├── services/             # 服务层模块
│   ├── audio_utils.py    # 音频处理工具和 UI 组件
│   ├── stt_service.py    # 语音转文本服务（OpenAI Whisper）
│   ├── tts_service.py    # 文本转语音服务（OpenAI TTS）
│   └── __init__.py
├── config/               # 配置模块
│   ├── preset_characters.py  # 预设角色数据
│   └── __init__.py
├── scripts/              # 脚本工具
│   ├── run.py           # 应用启动脚本
│   ├── init_database.py # 数据库初始化脚本
│   └── __init__.py
├── tests/                # 测试模块
│   ├── test_database.py # 数据库测试
│   ├── test_audio.py    # 音频功能测试
│   ├── test_stt.py      # STT 服务测试
│   ├── test_tts.py      # TTS 服务测试
│   └── __init__.py
├── docs/                 # 技术文档
│   ├── DATABASE_README.md     # 数据库设计文档
│   ├── STT_INTEGRATION_GUIDE.md  # STT 集成指南
│   └── TTS_INTEGRATION_GUIDE.md  # TTS 集成指南
├── data/                 # 数据存储
│   └── roleplay.db      # SQLite 数据库文件
├── audio_temp/           # 临时音频文件
├── tts_cache/            # TTS 音频缓存
├── run.py                # 根级启动脚本
├── requirements.txt      # Python 依赖
├── .env.example         # 环境变量模板
├── CLAUDE.md            # Claude Code 项目指南
└── README.md            # 项目说明
```

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd AI-role-playing-website

# 安装依赖（包含音频处理支持）
pip install -r requirements.txt

# 安装音频处理系统依赖
# macOS:
brew install ffmpeg

# Ubuntu/Debian:
sudo apt update && sudo apt install ffmpeg

# Windows:
# 下载 ffmpeg 并添加到 PATH 环境变量
```

### 2. 配置环境变量

创建 `.env` 文件：

```bash
cp .env.example .env
```

编辑 `.env` 文件，添加必要配置：

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-3.5-turbo
APP_TITLE=AI角色扮演聊天网站
```

### 3. 初始化数据库

```bash
# 简单启动（自动初始化）
python run.py

# 或手动初始化数据库
python scripts/init_database.py --reset --sample-data
```

### 4. 运行应用

```bash
# 使用启动脚本（推荐，包含依赖检查）
python run.py

# 或直接运行 Streamlit
streamlit run app/main.py
```

## 🎭 角色介绍

### 哈利·波特 ⚡

- **描述**: 勇敢的霍格沃茨学生
- **性格**: 勇敢无畏、忠诚友善、正义感强
- **技能**: 防御黑魔法、魁地奇飞行、守护神咒语
- **语音**: 年轻男性声音，英式口音

### 苏格拉底 🏛️

- **描述**: 智慧的古希腊哲学家
- **性格**: 睿智深刻、善于提问、追求真理
- **技能**: 哲学思辨、逻辑推理、苏格拉底方法
- **语音**: 成熟男性声音，深沉稳重

### 阿尔伯特·爱因斯坦 🧠

- **描述**: 好奇的理论物理学家
- **性格**: 极度好奇、想象力丰富、深度思考
- **技能**: 理论物理、数学建模、思想实验
- **语音**: 智慧男性声音，德式口音

## 📊 数据库模型

### 核心表结构

- **characters**: 角色信息（姓名、描述、性格、技能、语音配置等）
- **conversations**: 对话记录（角色关联、标题、时间戳）
- **messages**: 消息内容（用户/助手消息、内容、音频元数据）

### 音频数据集成

- **音频元数据**: 存储在消息的 `metadata` JSON 字段中
- **语音配置**: 角色的 `voice_config` 字段定义 TTS 设置
- **文件关联**: 临时音频文件和缓存文件的路径映射

详细的数据库设计请参考 [docs/DATABASE_README.md](docs/DATABASE_README.md)

## 🛠️ 开发和测试

### 运行测试

```bash
# 测试数据库 CRUD 操作
python tests/test_database.py

# 测试完整音频功能
python tests/test_audio.py

# 测试语音转文本服务
python tests/test_stt.py

# 测试文本转语音服务
python tests/test_tts.py

# 测试角色数据创建
python -c "from config.preset_characters import get_preset_characters; print(get_preset_characters())"

# 检查音频依赖
python -c "from services.audio_utils import AudioUI; AudioUI.show_dependencies_warning()"
```

### 重置数据库

```bash
# 完全重置并创建示例数据
python scripts/init_database.py --reset --sample-data

# 或使用启动脚本
python run.py --reset --sample-data
```

## 📝 使用说明

### 基础功能

1. **选择角色**: 在左侧边栏选择想要对话的角色
2. **文本对话**: 在聊天框中输入消息开始与角色互动
3. **查看信息**: 左侧显示角色的详细信息（性格、技能、语音配置等）
4. **保存对话**: 点击"保存对话"按钮保存当前会话
5. **查看历史**: 切换到"对话历史"标签查看过往对话
6. **管理对话**: 可以加载历史对话继续聊天或删除不需要的对话

### 语音功能

7. **录音输入**: 点击录音按钮进行语音输入，自动转换为文字
8. **语音回复**: 角色回复时自动生成语音，点击播放按钮收听
9. **语音设置**: 可在设置中调整音频质量和语音选项
10. **缓存管理**: 系统自动管理音频缓存，优化性能

### 浏览器要求

- **HTTPS**: 生产环境需要 HTTPS 才能使用麦克风功能
- **权限**: 首次使用需要授权麦克风访问权限
- **兼容性**: 支持 Chrome、Firefox、Safari、Edge 等主流浏览器

## 🔧 配置选项

### OpenAI API 配置

#### 聊天模型

- `gpt-3.5-turbo` (默认，快速响应)
- `gpt-4` (更高质量，需要相应 API 权限)
- `gpt-4-turbo` (平衡性能和质量)

#### 语音服务

- **STT 模型**: `whisper-1` (OpenAI Whisper API)
- **TTS 模型**: `tts-1` 或 `tts-1-hd` (高质量语音合成)
- **支持语音**: alloy, echo, fable, onyx, nova, shimmer

### 数据库配置

默认使用 SQLite，数据库文件位于 `data/roleplay.db`

可以通过修改 `DatabaseManager` 初始化参数更改数据库路径：

```python
db = DatabaseManager("custom/path/database.db")
```

### 音频配置

#### 录音设置

- **最大时长**: 5 分钟
- **最大文件大小**: 5 MB
- **音频格式**: WAV (16-bit PCM)

#### TTS 设置

- **缓存目录**: `tts_cache/`
- **临时文件**: `audio_temp/`
- **自动清理**: 24 小时后删除临时文件

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- [Streamlit](https://streamlit.io/) - 优秀的 Web 应用框架
- [OpenAI](https://openai.com/) - 强大的 AI 语言模型和语音服务
- [Pydantic](https://pydantic-docs.helpmanual.io/) - 数据验证和序列化
- [pydub](https://github.com/jiaaro/pydub) - 音频处理库
- [streamlit-audiorecorder](https://github.com/Joooohan/streamlit-audiorecorder) - 录音组件
- [SpeechRecognition](https://github.com/Uberi/speech_recognition) - 语音识别备用库

## 📞 支持

如果您遇到问题或有建议，请：

1. 查看技术文档：
   - [docs/DATABASE_README.md](docs/DATABASE_README.md) - 数据库相关问题
   - [docs/STT_INTEGRATION_GUIDE.md](docs/STT_INTEGRATION_GUIDE.md) - 语音转文本集成
   - [docs/TTS_INTEGRATION_GUIDE.md](docs/TTS_INTEGRATION_GUIDE.md) - 文本转语音集成
2. 检查环境配置：
   - `.env` 文件配置是否正确
   - OpenAI API Key 有效且有足够额度
   - ffmpeg 是否正确安装
3. 运行测试验证功能：
   - `python tests/test_database.py` - 验证数据库功能
   - `python tests/test_audio.py` - 验证音频功能
   - `python tests/test_stt.py` - 验证 STT 服务
   - `python tests/test_tts.py` - 验证 TTS 服务

---

**Enjoy chatting with AI characters! 🎭✨**
