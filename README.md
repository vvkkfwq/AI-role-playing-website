# AI 角色扮演聊天网站

基于 Streamlit 和 OpenAI 构建的网页版 AI 角色扮演聊天应用，采用 Pydantic 数据模型和 SQLite 数据库。

## ✨ 功能特色

- 🎭 **多角色扮演**: 预设 3 个经典角色（哈利·波特、苏格拉底、爱因斯坦）
- 💬 **实时对话**: 流畅的聊天界面，支持角色头像和个性化回复
- 📚 **对话历史**: 完整的对话记录和管理功能
- 🔧 **数据模型**: 基于 Pydantic 的完整数据验证和类型注解
- 🗄️ **数据库管理**: SQLite 数据库，支持完整的 CRUD 操作
- 🎨 **个性化**: 每个角色都有独特的性格特征、技能和语音配置

## 🏗️ 项目结构

```
AI-role-playing-website/
├── app.py                 # Streamlit 主应用
├── models.py              # Pydantic 数据模型
├── database.py            # 数据库管理和 CRUD 操作
├── preset_characters.py   # 预设角色数据
├── init_database.py       # 数据库初始化脚本
├── test_database.py       # 数据库测试脚本
├── run.py                 # 应用启动脚本
├── requirements.txt       # Python 依赖
├── .env.example          # 环境变量模板
├── README.md             # 项目说明
├── DATABASE_README.md    # 数据库设计文档
└── data/
    └── roleplay.db       # SQLite 数据库文件
```

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd AI-role-playing-website

# 安装依赖
pip install -r requirements.txt
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
python init_database.py --reset --sample-data
```

### 4. 运行应用

```bash
# 使用启动脚本（推荐）
python run.py

# 或直接运行 Streamlit
streamlit run app.py
```

## 🎭 角色介绍

### 哈利·波特 ⚡

- **描述**: 勇敢的霍格沃茨学生
- **性格**: 勇敢无畏、忠诚友善、正义感强
- **技能**: 防御黑魔法、魁地奇飞行、守护神咒语

### 苏格拉底 🏛️

- **描述**: 智慧的古希腊哲学家
- **性格**: 睿智深刻、善于提问、追求真理
- **技能**: 哲学思辨、逻辑推理、苏格拉底方法

### 阿尔伯特·爱因斯坦 🧠

- **描述**: 好奇的理论物理学家
- **性格**: 极度好奇、想象力丰富、深度思考
- **技能**: 理论物理、数学建模、思想实验

## 📊 数据库模型

### 核心表结构

- **characters**: 角色信息（姓名、描述、性格、技能等）
- **conversations**: 对话记录（角色关联、标题、时间戳）
- **messages**: 消息内容（用户/助手消息、内容、元数据）

详细的数据库设计请参考 [DATABASE_README.md](DATABASE_README.md)

## 🛠️ 开发和测试

### 运行测试

```bash
# 测试数据库 CRUD 操作
python test_database.py

# 测试角色数据创建
python preset_characters.py
```

### 重置数据库

```bash
# 完全重置并创建示例数据
python init_database.py --reset --sample-data

# 或使用启动脚本
python run.py --reset --sample-data
```

## 📝 使用说明

1. **选择角色**: 在左侧边栏选择想要对话的角色
2. **开始对话**: 在聊天框中输入消息开始与角色互动
3. **查看信息**: 左侧显示角色的详细信息（性格、技能等）
4. **保存对话**: 点击"保存对话"按钮保存当前会话
5. **查看历史**: 切换到"对话历史"标签查看过往对话
6. **管理对话**: 可以加载历史对话继续聊天或删除不需要的对话

## 🔧 配置选项

### OpenAI 模型配置

支持的模型：

- `gpt-3.5-turbo` (默认，快速响应)
- `gpt-4` (更高质量，需要相应 API 权限)
- `gpt-4-turbo` (平衡性能和质量)

### 数据库配置

默认使用 SQLite，数据库文件位于 `data/roleplay.db`

可以通过修改 `DatabaseManager` 初始化参数更改数据库路径：

```python
db = DatabaseManager("custom/path/database.db")
```

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
- [OpenAI](https://openai.com/) - 强大的 AI 语言模型
- [Pydantic](https://pydantic-docs.helpmanual.io/) - 数据验证和序列化

## 📞 支持

如果您遇到问题或有建议，请：

1. 查看 [DATABASE_README.md](DATABASE_README.md) 了解数据库相关问题
2. 检查 `.env` 文件配置是否正确
3. 确保 OpenAI API Key 有效且有足够额度
4. 运行 `python test_database.py` 验证数据库功能

---

**Enjoy chatting with AI characters! 🎭✨**
