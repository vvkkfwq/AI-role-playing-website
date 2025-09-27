# 语音转文字(STT)集成指南

## 📋 文档信息

- **文档版本**: v2.0
- **适用系统**: AI角色扮演聊天网站
- **更新日期**: 2025-09-27
- **文档类型**: STT集成和配置指南

> **相关文档**:
> - [AI智能技能系统开发指南](skill_system_update_v2.0.md)
> - [数据库设计文档](DATABASE_README.md)
> - [文字转语音集成指南](TTS_INTEGRATION_GUIDE.md)

---

## 功能概述

本系统集成了完整的语音转文字功能，支持与AI角色扮演聊天的无缝整合。主要特性包括：

### 🎤 核心功能
- **OpenAI Whisper API集成**: 高精度语音识别，支持多语言
- **智能音频预处理**: 降噪、标准化、格式转换
- **分段处理**: 自动处理长音频文件
- **实时进度反馈**: 用户可见的处理状态
- **用户编辑界面**: 允许修正识别结果
- **备用服务**: speech_recognition库作为fallback

### 📊 统计与反馈
- **准确率统计**: 实时跟踪识别成功率
- **用户反馈机制**: 5星评分系统
- **性能监控**: 处理时间和置信度跟踪
- **错误分析**: 常见错误类型统计

## 技术架构

> **相关参考**: STT服务与[AI智能技能系统](skill_system_update_v2.0.md)和[数据库系统](DATABASE_README.md)紧密集成

### 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      STT 服务架构                            │
├─────────────────────────────────────────────────────────────┤
│                   用户界面层 (UI Layer)                       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐  │
│  │ Audio Recorder  │  │  STT Controls   │  │ Result Editor│  │
│  │ - 录音控制        │  │ - 语言选择       │  │ - 文本编辑    │  │
│  │ - 状态显示        │  │ - 服务切换       │  │ - 置信度显示  │  │
│  │ - 质量检测        │  │ - 统计查看       │  │ - 用户反馈    │  │
│  └─────────────────┘  └─────────────────┘  └──────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                    服务协调层 (Service Layer)                 │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │            ComprehensiveSTTService                      │  │
│  │  - 统一STT接口           - 智能服务路由                   │  │
│  │  - 错误处理和重试         - 性能监控                     │  │
│  │  - 质量评估              - 用户反馈收集                   │  │
│  └─────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                    处理层 (Processing Layer)                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐  │
│  │ AudioPreprocessor│  │WhisperSTTService│  │SpeechRecognition│
│  │ - 格式标准化      │  │ - OpenAI API    │  │ - Google API  │  │
│  │ - 降噪优化        │  │ - 置信度计算     │  │ - 备用服务    │  │
│  │ - 分段处理        │  │ - 多语言识别     │  │ - 离线支持    │  │
│  └─────────────────┘  └─────────────────┘  └──────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                    数据层 (Data Layer)                       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐  │
│  │STTStatisticsManager│ │   数据库存储     │  │   缓存系统    │  │
│  │ - 准确率统计      │  │ - 结果存储       │  │ - 临时文件    │  │
│  │ - 性能跟踪        │  │ - 历史记录       │  │ - 音频缓存    │  │
│  │ - 用户反馈        │  │ - 元数据管理     │  │ - 结果缓存    │  │
│  └─────────────────┘  └─────────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 主要组件

1. **ComprehensiveSTTService**: 主服务类
   - 统一的STT接口和服务协调
   - 智能路由到不同识别服务
   - 错误处理和重试机制
   - 同步/异步双模式支持

2. **WhisperSTTService**: OpenAI Whisper集成
   - API调用和响应解析
   - 置信度计算和质量评估
   - 多语言自动检测
   - 分段音频处理支持

3. **AudioPreprocessor**: 音频预处理器
   - 格式标准化 (16kHz mono WAV)
   - 降噪和音质增强
   - 长音频智能分段处理
   - 音频质量验证

4. **SpeechRecognitionFallback**: 备用识别服务
   - Google Web Speech API集成
   - 网络故障时的降级服务
   - 基础语音识别功能
   - 离线识别选项

5. **STTStatisticsManager**: 统计管理器
   - 准确率和性能跟踪
   - 用户满意度收集
   - 数据持久化存储
   - 实时质量监控

## 使用流程

### 基本语音识别流程

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  用户录音    │───▶│  音频验证    │───▶│  音频预处理  │───▶│ Whisper API │
│  Audio      │    │  Validation │    │ Preprocessing│    │  Processing │
│  Recording  │    │             │    │             │    │             │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                          │                                      │
                          ▼                                      ▼
                   ┌─────────────┐                        ┌─────────────┐
                   │   错误处理   │                        │  结果展示    │
                   │ Error       │                        │ Result      │
                   │ Handling    │                        │ Display     │
                   └─────────────┘                        └─────────────┘
                                                                 │
                                                                 ▼
    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
    │  备用服务    │◀───│   服务降级   │    │  用户编辑    │───▶│  消息发送    │
    │ Fallback    │    │ Service     │    │ User Edit   │    │ Message     │
    │ Service     │    │ Fallback    │    │             │    │ Send        │
    └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

**详细流程说明:**

1. **录音阶段**: 用户点击录音按钮，系统开始音频捕获
2. **验证阶段**: 检查音频时长、文件大小和格式有效性
3. **预处理阶段**: 音频格式标准化、降噪、音量归一化
4. **识别阶段**: 调用Whisper API进行语音识别
5. **降级机制**: API失败时自动切换到backup服务
6. **结果处理**: 显示识别文本和置信度，提供编辑功能
7. **用户确认**: 用户可编辑文本或重新识别
8. **消息发送**: 将最终文本作为用户消息发送

### 用户交互流程
1. **录音**: 点击录制按钮开始录音
2. **预览**: 显示音频时长和播放控件
3. **选择处理方式**:
   - 🔤 转文字: 进入编辑模式
   - 📤 发送语音: 直接发送(可选STT)
4. **编辑模式** (如果选择转文字):
   - 显示识别结果和置信度
   - 提供文本编辑区域
   - 操作选项: 发送消息/重新识别/仅发语音/取消
   - 用户反馈: 满意度评分

## API配置

### 环境变量设置
```bash
# OpenAI API配置
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-3.5-turbo

# STT服务配置 (可选)
STT_LANGUAGE=auto  # auto, zh, en
STT_PREPROCESSING=true
STT_FALLBACK_ENABLED=true
```

### 支持的语言
- `auto`: 自动检测 (推荐)
- `zh`: 中文识别
- `en`: 英语识别

## 性能优化

### 音频预处理优化
- **采样率**: 16kHz (Whisper最佳)
- **声道**: 单声道
- **格式**: WAV PCM 16-bit
- **降噪**: 高通/低通滤波器
- **标准化**: 音量归一化

### 分段处理策略
- **短音频** (≤30秒): 直接处理
- **长音频** (>30秒): 自动分段
- **分段算法**: 基于静音检测
- **最大段长**: 25秒 (Whisper API限制)

### 错误处理机制
1. **输入验证**: 音频时长、文件大小检查
2. **API重试**: 网络错误自动重试
3. **服务降级**: Whisper失败自动切换到备用服务
4. **用户提示**: 友好的错误消息显示

## 集成说明

### 在聊天流程中的集成

#### 基础STT集成

```python
# 启用STT的音频消息处理
def process_user_message_with_stt(audio_segment, character):
    # 1. 执行语音识别
    stt_result = stt_service.transcribe_audio(
        audio_segment,
        language=st.session_state.stt_language,
        prompt=f"角色对话: {character.name}",
        use_fallback_on_error=True
    )

    # 2. 处理识别结果
    if stt_result.text and not stt_result.error:
        content = stt_result.text
        # 记录成功统计
        stt_service.stats_manager.record_request(stt_result, user_edited=False)
    else:
        content = "[音频消息]"
        # 记录失败统计
        if stt_result.error:
            st.warning(f"语音识别失败: {stt_result.error}")

    # 3. 保存消息和完整元数据
    message_data = {
        "role": "user",
        "content": content,
        "metadata": {
            "audio": {
                "stt_result": {
                    "text": stt_result.text,
                    "confidence": stt_result.confidence,
                    "language": stt_result.language,
                    "method": stt_result.method,
                    "processing_time": stt_result.processing_time,
                    "error": stt_result.error
                },
                "file_path": audio_metadata.get("file_path"),
                "duration": audio_metadata.get("duration"),
                "quality": "processed"
            },
            "source": "voice_input",
            "timestamp": datetime.now().isoformat()
        }
    }

    # 4. 发送给AI并显示回复
    generate_ai_response(message_data, character)

    return stt_result
```

#### 高级集成 - 与技能系统协作

```python
# STT与AI技能系统集成
async def process_stt_with_skills(audio_segment, character, conversation_id):
    # 1. STT处理
    stt_result = stt_service.transcribe_audio(audio_segment)

    if not stt_result.text:
        return None

    # 2. 创建技能执行上下文
    from skills.core.models import SkillContext
    skill_context = SkillContext(
        user_input=stt_result.text,
        character=character.__dict__,
        conversation_id=conversation_id,
        detected_intent=None,  # 将由技能系统分析
        emotional_state=None,  # 将由技能系统分析
        request_id=f"stt_{int(time.time())}"
    )

    # 3. 执行技能处理
    from skills.core.manager import skill_manager
    skill_results = await skill_manager.process_user_input(
        user_input=stt_result.text,
        character_id=character.id,
        conversation_id=conversation_id,
        character_info=character.__dict__
    )

    # 4. 整合STT和技能结果
    enhanced_metadata = {
        "audio": {
            "stt_result": stt_result.__dict__,
            "file_path": "...",
            "duration": "..."
        },
        "skills_executed": [
            {
                "skill_name": result.skill_name,
                "confidence_score": result.confidence_score,
                "quality_score": result.quality_score,
                "execution_time": result.execution_time,
                "generated_content": result.generated_content
            }
            for result in skill_results
        ],
        "enhanced_by_skills": len(skill_results) > 0
    }

    return {
        "stt_result": stt_result,
        "skill_results": skill_results,
        "metadata": enhanced_metadata
    }
```

### 数据库集成

STT结果存储在消息的metadata字段中：

```json
{
  "role": "user",
  "content": "你好，哈利波特",
  "metadata": {
    "audio": {
      "file_path": "/path/to/audio.wav",
      "duration": 2.5,
      "stt_result": {
        "text": "你好，哈利波特",
        "confidence": 0.92,
        "language": "zh",
        "method": "whisper",
        "processing_time": 1.8,
        "user_edited": false
      }
    }
  }
}
```

## 用户界面特性

### 侧边栏设置
- **启用开关**: 语音识别功能开关
- **语言选择**: 识别语言偏好
- **统计信息**: 使用情况和准确率显示

### 聊天界面集成
- **识别状态显示**: 实时处理进度
- **结果展示**: 置信度和方法指示器
- **编辑界面**: 内嵌的文本编辑功能
- **反馈收集**: 用户满意度评分

### 历史记录增强
- **STT元数据显示**: 识别方法和准确率
- **音频回放**: 保留原始音频播放功能
- **内容对比**: 原音频vs识别文本

## 性能指标

### 基准测试结果 (test_stt.py)
- **Whisper API准确率**: >90% (真实语音)
- **平均处理时间**: 1.5秒 (2秒音频)
- **文件支持**: 最大25MB
- **语言支持**: 99种语言自动检测

### 资源使用
- **内存占用**: ~50MB (服务组件)
- **存储**: 音频文件24小时自动清理
- **网络**: 仅API调用时使用

## 故障排除

### 常见问题

1. **麦克风无法访问**
   - 检查浏览器权限设置
   - 确保使用HTTPS连接
   - 重新加载页面

2. **识别准确率低**
   - 检查音频质量和环境噪音
   - 尝试不同的语言设置
   - 使用较短的录音片段

3. **API调用失败**
   - 验证OpenAI API key配置
   - 检查网络连接
   - 查看API配额限制

4. **处理时间过长**
   - 减少音频时长
   - 检查音频文件大小
   - 网络状况影响

### 日志和调试

```python
# 启用调试模式
import logging
logging.basicConfig(level=logging.DEBUG)

# 检查服务状态
status = stt_service.get_service_status()
print(status)

# 查看统计信息
stats = stt_service.stats_manager.get_statistics_summary()
print(stats)
```

## 扩展和定制

### 添加新的STT服务
```python
class CustomSTTService:
    def transcribe_audio(self, audio_segment, language="auto"):
        # 实现自定义识别逻辑
        return STTResult(...)

# 集成到主服务
stt_service.custom_service = CustomSTTService()
```

### 自定义预处理
```python
class CustomPreprocessor(AudioPreprocessor):
    def preprocess_audio(self, audio_segment):
        # 添加自定义预处理步骤
        processed = super().preprocess_audio(audio_segment)
        # 进一步处理...
        return processed
```

### 个性化提示优化
```python
def get_character_prompt(character):
    return f"""
    角色: {character.name} ({character.title})
    性格: {', '.join(character.personality)}
    场景: 日常对话交流
    请识别用户的语音输入，考虑角色扮演的上下文。
    """
```

## 更新日志

### v1.0.0 (2024)
- ✅ 基础STT功能集成
- ✅ OpenAI Whisper API支持
- ✅ 音频预处理和优化
- ✅ 用户编辑界面
- ✅ 统计和反馈机制
- ✅ 备用服务集成
- ✅ 错误处理和恢复
- ✅ 长音频分段处理
- ✅ 多语言支持
- ✅ 性能监控和优化

## 技术支持

### 依赖管理
确保以下依赖已安装：
```bash
pip install streamlit>=1.29.0
pip install openai>=1.3.0
pip install pydub>=0.25.1
pip install SpeechRecognition>=3.10.0
pip install streamlit-audiorecorder>=0.0.5
```

### 系统要求
- Python 3.8+
- FFmpeg (音频处理)
- HTTPS环境 (生产环境麦克风访问)
- OpenAI API账户和密钥

### 测试验证
```bash
# 运行完整测试套件
python test_stt.py

# 检查依赖
python -c "from stt_service import stt_service; print(stt_service.get_service_status())"
```

## 结论

语音转文字功能为AI角色扮演聊天系统提供了更自然的交互方式，通过先进的语音识别技术和智能的用户界面设计，用户可以享受流畅的语音对话体验。系统具备完整的错误处理、性能监控和用户反馈机制，确保服务的可靠性和持续改进。