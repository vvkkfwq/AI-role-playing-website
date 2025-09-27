# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an AI role-playing chat website built with Streamlit and OpenAI, featuring a comprehensive Pydantic data model system, SQLite database, and advanced audio capabilities including Speech-to-Text (STT) and Text-to-Speech (TTS). The application allows users to interact with preset AI characters through both text and voice interfaces.

## Architecture

### Core Components

#### Application Layer
- **app/main.py**: Main Streamlit application with `AIRolePlayApp` class handling UI, chat logic, and audio integration
- **app/models.py**: Pydantic data models defining `Character`, `Message`, `Conversation`, `VoiceConfig`, and supporting types
- **app/database.py**: `DatabaseManager` class providing comprehensive CRUD operations for SQLite
- **run.py**: Root-level startup script (entry point)

#### Configuration Layer
- **config/preset_characters.py**: Predefined character data with personality traits, skills, voice configurations, and prompt templates

#### Services Layer
- **services/audio_utils.py**: Core audio management utilities, UI components, and playback functionality
- **services/stt_service.py**: Speech-to-Text service using OpenAI Whisper API with preprocessing and fallback support
- **services/tts_service.py**: Text-to-Speech service using OpenAI TTS API with caching and character-specific voices

#### Skills System
- **skills/core/**: Core framework for AI skills with models, registry, manager, and executor
- **skills/built_in/**: Built-in skills including conversation and knowledge skills
- **skills/intelligence/**: Intelligence modules for intent classification, skill matching, and recommendations
- **skills/monitoring/**: Performance monitoring and analytics for skill execution

#### Scripts and Testing
- **scripts/run.py**: Startup script with dependency checking and database initialization
- **scripts/init_database.py**: Database initialization and sample data setup
- **tests/**: Comprehensive test modules including audio functionality testing

#### Documentation
- **docs/**: Technical documentation including database, STT, and TTS integration guides

### Data Layer Architecture

The application uses a three-layer data architecture:

1. **Characters**: Store character profiles with personality, skills, and voice configurations
2. **Conversations**: Link characters to chat sessions with metadata
3. **Messages**: Store individual chat messages with roles (user/assistant) and timestamps

### Key Design Patterns

- **Pydantic Models**: All data structures use Pydantic for validation and type safety
- **Service-Oriented Architecture**: Modular services for audio processing, STT, and TTS functionality
- **Database Abstraction**: `DatabaseManager` provides high-level CRUD operations with audio metadata support
- **Session Management**: Streamlit session state manages current character, conversation context, and audio settings
- **Template-based Prompts**: Characters use structured prompt templates for consistent AI behavior
- **Audio Pipeline**: Integrated recording → STT → processing → TTS → playback workflow
- **Caching Strategy**: Intelligent caching for TTS audio files and processing optimization
- **Skills Framework**: Modular AI skills system with dynamic matching, execution, and monitoring
- **Intent Recognition**: AI-powered intent classification and context-aware skill recommendations
- **Emotional Intelligence**: Automatic emotion detection and character-specific emotional support

## Development Commands

### Setup and Installation

```bash
# Install dependencies (including audio support)
pip install -r requirements.txt

# Install system dependencies for audio processing
# macOS:
brew install ffmpeg

# Ubuntu/Debian:
sudo apt update && sudo apt install ffmpeg

# Setup environment
cp .env.example .env
# Edit .env with your OPENAI_API_KEY
```

### Running the Application

```bash
# Recommended: Use startup script (checks deps, initializes DB)
python run.py

# Or run directly
streamlit run app/main.py
```

### Database Management

```bash
# Initialize database with preset characters
python scripts/init_database.py --reset --sample-data

# Test database operations
python tests/test_database.py

# Reset database via startup script
python run.py --reset --sample-data
```

### Audio Feature Testing

```bash
# Test complete audio functionality
python tests/test_audio.py

# Test Speech-to-Text service
python tests/test_stt.py

# Test Text-to-Speech service
python tests/test_tts.py

# Check audio dependencies
python -c "from services.audio_utils import AudioUI; AudioUI.show_dependencies_warning()"
```

### Development Workflow

```bash
# Check requirements and environment
python run.py --init

# Test character creation
python -c "from config.preset_characters import get_preset_characters; print(get_preset_characters())"

# Test all functionality including audio
python tests/test_audio.py

# Test skills system
python -c "from skills.core.registry import SkillRegistry; print(SkillRegistry.list_skills())"

# Test emotional support skill
python -c "from skills.built_in.conversation.emotional_support import EmotionalSupportSkill; print(EmotionalSupportSkill.get_metadata())"
```

## Key Configuration

### Environment Variables (.env)

- `OPENAI_API_KEY`: Required for AI responses
- `OPENAI_MODEL`: Model to use (default: gpt-3.5-turbo)
- `DATABASE_PATH`: SQLite database location (default: data/roleplay.db)

### Database Schema

- **characters**: Character profiles with JSON fields for personality/skills
- **conversations**: Chat sessions linked to characters
- **messages**: Individual chat messages with role and timestamp

### Character System

Characters are defined with:

- `prompt_template`: Core AI personality prompt
- `personality`: List of character traits
- `skills`: List of character abilities
- `voice_config`: Voice synthesis settings (VoiceConfig model)

## Important Notes

### Database Initialization

The database auto-initializes on first run. Use `--reset` flag carefully as it destroys existing data.

### Message Flow

#### Text Messages
1. User input → Streamlit UI
2. Intent classification and emotional analysis
3. Skills matching and recommendation
4. Format messages with character's system prompt and skills
5. Send to OpenAI API with skill context
6. Skills execution and quality assessment
7. Store conversation in database with skills metadata
8. Generate TTS audio (if enabled)
9. Display response with audio controls

#### Voice Messages
1. Audio recording → streamlit-audiorecorder
2. Audio preprocessing → pydub optimization
3. Speech-to-Text → OpenAI Whisper API
4. Text processing → same as text message flow with skills
5. Response generation with audio output

### Character Prompt Structure

Character prompts follow a template pattern combining personality traits, skills, and behavioral instructions to create consistent AI responses.

## Audio Processing Features

### Audio Services Architecture

#### Core Components
- **streamlit-audiorecorder**: Primary recording component for voice input
- **services/audio_utils.py**: Comprehensive audio management with UI components and playback controls
- **services/stt_service.py**: OpenAI Whisper-based Speech-to-Text with preprocessing and fallback
- **services/tts_service.py**: OpenAI TTS API integration with character-specific voice synthesis

#### Storage Strategy
- **audio_temp/**: Temporary recording files with automatic 24-hour cleanup
- **tts_cache/**: Cached TTS audio files for performance optimization
- **data/**: Database storage for audio metadata and message associations

### Complete Audio Processing Pipeline

#### Speech-to-Text Flow
1. **Recording**: User clicks record → streamlit-audiorecorder captures audio
2. **Preprocessing**: AudioSegment optimization (normalization, noise reduction, format conversion)
3. **STT Processing**: OpenAI Whisper API transcription with language detection
4. **Fallback**: speech_recognition library backup for API failures
5. **Validation**: Confidence scoring and accuracy feedback

#### Text-to-Speech Flow
1. **Voice Selection**: Character-specific voice configuration (alloy, echo, fable, onyx, nova, shimmer)
2. **Audio Generation**: OpenAI TTS API synthesis with quality optimization
3. **Caching**: Intelligent file caching based on content hash for performance
4. **Playback**: Integrated audio controls in chat interface
5. **Cleanup**: Automatic cache management and old file removal

### Audio Configuration

#### Recording Settings
- **Max Duration**: 5 minutes per recording
- **Max File Size**: 5 MB
- **Format**: WAV (16-bit PCM, 44.1kHz sampling rate)
- **Quality**: Optimized for speech recognition accuracy

#### TTS Settings
- **Voices**: Character-specific voice mapping (6 OpenAI voices available)
- **Quality**: High-definition audio output
- **Speed**: Configurable speech rate (0.25x to 4.0x)
- **Caching**: Content-based hash caching for repeated phrases

#### System Requirements
- **Browser**: Chrome, Firefox, Safari, Edge support
- **HTTPS**: Required for microphone access in production
- **Dependencies**: ffmpeg, pydub, streamlit-audiorecorder

### Audio Error Handling & Recovery

#### STT Error Management
- **API Failures**: Automatic fallback to speech_recognition library
- **Audio Quality**: Preprocessing to improve recognition accuracy
- **Language Detection**: Automatic language identification for multilingual support
- **Retry Logic**: Progressive retry with exponential backoff

#### TTS Error Management
- **API Rate Limiting**: Request queuing and throttling
- **Cache Corruption**: Automatic cache validation and rebuilding
- **File System**: Graceful handling of storage errors

#### User Experience
- **Microphone Permissions**: Clear user guidance and fallback options
- **Browser Compatibility**: Feature detection and graceful degradation
- **Network Issues**: Offline capability messaging and retry options

### Storage Architecture

```
├── audio_temp/                    # Temporary recording files
│   ├── audio_conv123_msg456_*.wav # Conversation-specific recordings
│   └── temp_audio_*.wav          # General temporary files
├── tts_cache/                    # TTS output cache
│   ├── character_voice_hash.mp3  # Cached character responses
│   └── cleanup_log.json         # Cache management metadata
└── data/                        # Database and persistent storage
    └── roleplay.db              # SQLite with audio metadata
```

### Integration Notes

- **Message Metadata**: Audio information stored in `Message.metadata` JSON field
- **Character Voices**: Voice configurations defined in `VoiceConfig` Pydantic model
- **Session State**: Audio settings persist across conversation sessions
- **Performance**: Async processing prevents UI blocking during audio operations
- **Testing**: Comprehensive test coverage including edge cases and error scenarios

## AI Skills System Architecture

### Core Framework

#### Skills Registry (`skills/core/registry.py`)
- **Centralized Registration**: All skills are registered in a central registry
- **Dynamic Discovery**: Automatic skill discovery and loading
- **Metadata Management**: Comprehensive skill metadata tracking
- **Dependency Resolution**: Handles skill dependencies and compatibility

#### Skills Manager (`skills/core/manager.py`)
- **Execution Orchestration**: Coordinates skill execution workflows
- **Context Management**: Manages skill execution contexts and data flow
- **Performance Monitoring**: Tracks execution metrics and quality scores
- **Error Handling**: Robust error handling and fallback strategies

#### Skills Executor (`skills/core/executor.py`)
- **Async Execution**: Non-blocking skill execution
- **Timeout Management**: Prevents long-running skills from blocking
- **Resource Control**: Manages concurrent execution limits
- **Result Processing**: Handles skill results and quality assessment

### Built-in Skills

#### Emotional Support (`skills/built_in/conversation/emotional_support.py`)
- **Emotion Detection**: Identifies emotional states from user input
- **Character-Specific Responses**: Tailored emotional support based on character
- **Quality Assessment**: Evaluates empathy and support effectiveness
- **Confidence Scoring**: Provides confidence levels for emotional support

#### Deep Questioning (`skills/built_in/conversation/deep_questioning.py`)
- **Socratic Method**: Implements philosophical questioning techniques
- **Thought Provocation**: Encourages deeper reflection and analysis
- **Context Awareness**: Builds on previous conversation context

#### Storytelling (`skills/built_in/conversation/storytelling.py`)
- **Creative Narratives**: Generates personalized stories
- **Character Integration**: Stories incorporate character traits and style
- **Interactive Elements**: Supports user participation in story development

### Intelligence Modules

#### Intent Classification (`skills/intelligence/intent_classifier.py`)
- **Natural Language Understanding**: Analyzes user intent from text
- **Context Integration**: Considers conversation history and character context
- **Confidence Scoring**: Provides reliability metrics for classifications
- **Multi-Intent Support**: Handles complex inputs with multiple intents

#### Skill Matcher (`skills/intelligence/skill_matcher.py`)
- **Dynamic Matching**: Real-time skill selection based on context
- **Confidence Ranking**: Orders skills by relevance and confidence
- **Character Compatibility**: Considers character-skill compatibility
- **Context Weighting**: Adjusts matching based on conversation context

#### Recommendation Engine (`skills/intelligence/recommendation_engine.py`)
- **Proactive Suggestions**: Recommends skills before explicit requests
- **Learning Adaptation**: Improves recommendations based on user interactions
- **Context Sensitivity**: Considers current conversation flow and mood
- **Performance Optimization**: Balances relevance with execution efficiency

### Skills Data Models

#### Core Models (`skills/core/models.py`)
- **SkillMetadata**: Complete skill definition and configuration
- **SkillContext**: Execution context with conversation and character data
- **SkillResult**: Execution results with performance metrics
- **SkillExecution**: Execution tracking and monitoring data
- **PerformanceMetrics**: Comprehensive performance analytics

### Skills Execution Flow

```
1. User Input Reception
   ↓
2. Intent Classification & Emotional Analysis
   ↓
3. Skills Discovery & Matching
   ↓
4. Confidence Scoring & Ranking
   ↓
5. Context Preparation
   ↓
6. Skills Execution (Async)
   ↓
7. Result Processing & Quality Assessment
   ↓
8. Response Integration
   ↓
9. Performance Metrics Recording
```

### Performance Monitoring

#### Execution Metrics
- **Response Time**: Skill execution duration tracking
- **Success Rate**: Success/failure ratio monitoring
- **Quality Scores**: Response quality assessment
- **User Satisfaction**: Feedback-based satisfaction tracking

#### Optimization Features
- **Caching**: Results caching for repeated scenarios
- **Load Balancing**: Distributes skill execution load
- **Fallback Strategies**: Handles skill failures gracefully
- **Continuous Learning**: Improves performance based on usage patterns
