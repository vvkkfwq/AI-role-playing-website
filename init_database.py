#!/usr/bin/env python3
"""
Database initialization script for AI Role-Playing Website

This script initializes the SQLite database with:
1. All required tables (characters, conversations, messages)
2. Preset characters (Harry Potter, Socrates, Einstein)
3. Sample conversations (optional)

Usage:
    python init_database.py [--reset] [--sample-data]

Options:
    --reset: Delete existing database and start fresh
    --sample-data: Create sample conversations for demonstration
"""

import argparse
import os
import sys
from pathlib import Path

# Add current directory to path to import local modules
sys.path.insert(0, str(Path(__file__).parent))

from database import DatabaseManager
from preset_characters import populate_preset_characters
from models import MessageRole


def reset_database(db_path: str):
    """Remove existing database file"""
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Removed existing database: {db_path}")

    # Also remove the data directory if empty
    data_dir = os.path.dirname(db_path)
    if os.path.exists(data_dir) and not os.listdir(data_dir):
        os.rmdir(data_dir)
        print(f"Removed empty directory: {data_dir}")


def create_sample_conversations(db: DatabaseManager):
    """Create sample conversations for demonstration"""
    characters = db.get_all_characters()

    if not characters:
        print("No characters found, skipping sample conversations")
        return

    sample_conversations = [
        {
            "character_name": "哈利·波特",
            "title": "关于勇气的讨论",
            "messages": [
                {"role": MessageRole.USER, "content": "哈利，你觉得什么是真正的勇气？"},
                {"role": MessageRole.ASSISTANT, "content": "我觉得真正的勇气不是没有恐惧，而是即使害怕也要做正确的事情。就像我面对伏地魔时，说不害怕是假的，但保护朋友和霍格沃茨的信念让我能够坚持下去。有时候，为了保护你爱的人，你必须勇敢地站出来。"},
                {"role": MessageRole.USER, "content": "那你有什么建议给那些想要变得更勇敢的人吗？"},
                {"role": MessageRole.ASSISTANT, "content": "我想说，勇气是可以培养的。从小事开始，比如为朋友挺身而出，或者承认自己的错误。记住，你并不孤单——就像我有赫敏和罗恩一样，真正的朋友会在你需要勇气的时候支持你。还有，相信自己内心的正义感，它会指引你做正确的事。"}
            ]
        },
        {
            "character_name": "苏格拉底",
            "title": "什么是智慧？",
            "messages": [
                {"role": MessageRole.USER, "content": "苏格拉底，请告诉我什么是智慧？"},
                {"role": MessageRole.ASSISTANT, "content": "我的朋友，这是一个绝妙的问题！但让我反问你：你认为什么是智慧呢？我常说'我知道我什么都不知道'，因为真正的智慧或许就是认识到自己的无知。那些自以为什么都知道的人，反而可能离智慧最远。"},
                {"role": MessageRole.USER, "content": "所以智慧就是承认自己的无知吗？"},
                {"role": MessageRole.ASSISTANT, "content": "这是一个很好的开始，但让我们继续思考：如果智慧仅仅是承认无知，那么一个什么都不知道但承认这一点的人，是否就比有学问的人更有智慧呢？或许智慧包含了持续的探索、质疑和学习的态度？你觉得一个智慧的人应该具备什么样的品质呢？"}
            ]
        },
        {
            "character_name": "阿尔伯特·爱因斯坦",
            "title": "想象力与科学",
            "messages": [
                {"role": MessageRole.USER, "content": "爱因斯坦教授，您认为想象力在科学中有多重要？"},
                {"role": MessageRole.ASSISTANT, "content": "啊，这个问题触及了我最珍视的东西！我常说'想象力比知识更重要'，因为知识是有限的，而想象力拥抱整个世界。当我想象自己骑在光束上旅行时，相对论的概念就开始在我脑中形成。科学不仅仅是公式和实验，更是对未知世界的好奇和想象。"},
                {"role": MessageRole.USER, "content": "那么普通人如何培养这种科学想象力呢？"},
                {"role": MessageRole.ASSISTANT, "content": "很简单！保持一颗童心，对一切都感到好奇。问问自己：为什么天空是蓝色的？时间真的是均匀流逝的吗？如果我缩小到原子大小，世界会是什么样？不要害怕提出'愚蠢'的问题，往往最简单的问题会引导你发现最深刻的真理。记住，宇宙最不可理解的就是它是可以理解的！"}
            ]
        }
    ]

    created_conversations = 0

    for conv_data in sample_conversations:
        # Find character by name
        character = db.get_character_by_name(conv_data["character_name"])
        if not character:
            print(f"Character '{conv_data['character_name']}' not found, skipping conversation")
            continue

        # Create conversation
        conversation_id = db.create_conversation(character.id, conv_data["title"])

        # Add messages
        for msg_data in conv_data["messages"]:
            db.add_message(
                conversation_id=conversation_id,
                role=msg_data["role"].value,
                content=msg_data["content"]
            )

        created_conversations += 1
        print(f"Created sample conversation: '{conv_data['title']}' for {character.name}")

    print(f"\nCreated {created_conversations} sample conversations")


def main():
    parser = argparse.ArgumentParser(description="Initialize AI Role-Playing Website database")
    parser.add_argument("--reset", action="store_true", help="Reset database (delete existing)")
    parser.add_argument("--sample-data", action="store_true", help="Create sample conversations")
    parser.add_argument("--db-path", default="data/roleplay.db", help="Database path")

    args = parser.parse_args()

    print("🎭 AI Role-Playing Website Database Initialization")
    print("=" * 50)

    # Reset database if requested
    if args.reset:
        print("\n🗑️  Resetting database...")
        reset_database(args.db_path)

    # Initialize database
    print("\n🔧 Initializing database...")
    db = DatabaseManager(args.db_path)
    print(f"Database initialized at: {args.db_path}")

    # Populate with preset characters
    print("\n👥 Creating preset characters...")
    characters = populate_preset_characters(db)

    # Create sample conversations if requested
    if args.sample_data:
        print("\n💬 Creating sample conversations...")
        create_sample_conversations(db)

    # Summary
    print("\n✅ Database initialization complete!")
    print(f"📊 Total characters: {len(characters)}")

    if characters:
        print("\n🎯 Available characters:")
        for char in characters:
            print(f"   {char.avatar_emoji} {char.name} - {char.title}")
            print(f"      Skills: {', '.join(char.skills[:3])}{'...' if len(char.skills) > 3 else ''}")

    print(f"\n📁 Database location: {os.path.abspath(args.db_path)}")
    print("\n🚀 You can now run 'streamlit run app.py' to start the application!")


if __name__ == "__main__":
    main()