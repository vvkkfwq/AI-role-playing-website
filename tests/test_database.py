#!/usr/bin/env python3
"""
Test script for database CRUD operations

This script demonstrates and tests all the database operations:
- Character CRUD operations
- Conversation management
- Message handling
"""

from app.database import DatabaseManager
from app.models import CharacterCreate, CharacterUpdate, VoiceConfig, MessageRole
from pprint import pprint


def test_character_operations(db: DatabaseManager):
    """Test character CRUD operations"""
    print("🧪 Testing Character CRUD Operations")
    print("-" * 40)

    # Test: Get all characters
    print("1. Getting all characters:")
    characters = db.get_all_characters()
    for char in characters:
        print(f"   - {char.name} ({char.id}): {char.title}")

    # Test: Get character by ID
    print("\n2. Getting character by ID (1):")
    char = db.get_character_by_id(1)
    if char:
        print(f"   Found: {char.name} - {char.title}")
        print(f"   Personality: {char.personality}")
        print(f"   Skills: {char.skills}")

    # Test: Get character by name
    print("\n3. Getting character by name ('哈利·波特'):")
    char = db.get_character_by_name("哈利·波特")
    if char:
        print(f"   Found: {char.name} - {char.title}")

    # Test: Create new character
    print("\n4. Creating new character:")
    new_char_data = CharacterCreate(
        name="测试角色",
        title="用于测试的角色",
        avatar_emoji="🧪",
        personality=["友善", "好奇"],
        prompt_template="你是一个测试角色，请友善地回应用户。",
        skills=["测试", "调试"],
        voice_config=VoiceConfig(voice_id="nova", speed=1.2)
    )

    try:
        new_char = db.create_character(new_char_data)
        print(f"   Created: {new_char.name} (ID: {new_char.id})")
    except Exception as e:
        print(f"   Error creating character: {e}")

    # Test: Update character
    print("\n5. Updating character:")
    if new_char:
        update_data = CharacterUpdate(
            title="更新后的测试角色",
            personality=["友善", "好奇", "聪明"]
        )
        updated_char = db.update_character(new_char.id, update_data)
        if updated_char:
            print(f"   Updated: {updated_char.title}")
            print(f"   New personality: {updated_char.personality}")

    # Test: Delete character (cleanup)
    print("\n6. Deleting test character:")
    if new_char:
        deleted = db.delete_character(new_char.id)
        print(f"   Deletion {'successful' if deleted else 'failed'}")

    print()


def test_conversation_operations(db: DatabaseManager):
    """Test conversation and message operations"""
    print("💬 Testing Conversation Operations")
    print("-" * 40)

    # Get a character to work with
    char = db.get_character_by_name("哈利·波特")
    if not char:
        print("No character found for testing")
        return

    print(f"Testing with character: {char.name}")

    # Test: Create conversation
    print("\n1. Creating new conversation:")
    conv_id = db.create_conversation(char.id, "测试对话")
    print(f"   Created conversation ID: {conv_id}")

    # Test: Add messages
    print("\n2. Adding messages to conversation:")
    msg1_id = db.add_message(conv_id, MessageRole.USER.value, "你好，哈利！")
    print(f"   Added user message (ID: {msg1_id})")

    msg2_id = db.add_message(conv_id, MessageRole.ASSISTANT.value, "你好！很高兴见到你。")
    print(f"   Added assistant message (ID: {msg2_id})")

    msg3_id = db.add_message(conv_id, MessageRole.USER.value, "告诉我关于霍格沃茨的事情")
    print(f"   Added user message (ID: {msg3_id})")

    # Test: Get conversation with messages
    print("\n3. Retrieving conversation with messages:")
    conversation = db.get_conversation_by_id(conv_id)
    if conversation:
        print(f"   Conversation: {conversation.title}")
        print(f"   Messages count: {len(conversation.messages)}")
        for i, msg in enumerate(conversation.messages, 1):
            print(f"   Message {i} ({msg.role}): {msg.content[:50]}...")

    # Test: Get conversations by character
    print("\n4. Getting all conversations for character:")
    conversations = db.get_conversations_by_character(char.id)
    print(f"   Found {len(conversations)} conversations:")
    for conv in conversations:
        print(f"   - {conv.title} ({len(conv.messages)} messages)")

    # Cleanup: Delete test conversation
    print("\n5. Cleaning up test conversation:")
    deleted = db.delete_conversation(conv_id)
    print(f"   Deletion {'successful' if deleted else 'failed'}")

    print()


def test_data_integrity(db: DatabaseManager):
    """Test data integrity and edge cases"""
    print("🔍 Testing Data Integrity")
    print("-" * 40)

    # Test: Non-existent character
    print("1. Testing non-existent character:")
    char = db.get_character_by_id(9999)
    print(f"   Result: {char}")

    # Test: Non-existent conversation
    print("\n2. Testing non-existent conversation:")
    conv = db.get_conversation_by_id(9999)
    print(f"   Result: {conv}")

    # Test: Duplicate character name
    print("\n3. Testing duplicate character name:")
    try:
        duplicate_data = CharacterCreate(
            name="哈利·波特",  # This should already exist
            title="重复角色",
            personality=["测试"],
            prompt_template="测试提示"
        )
        duplicate_char = db.create_character(duplicate_data)
        print(f"   Unexpected success: {duplicate_char.name}")
    except Exception as e:
        print(f"   Expected error: {type(e).__name__}")

    print()


def main():
    """Run all database tests"""
    print("🎭 Database CRUD Operations Test")
    print("=" * 50)

    # Initialize database
    db = DatabaseManager()

    try:
        # Run all tests
        test_character_operations(db)
        test_conversation_operations(db)
        test_data_integrity(db)

        print("✅ All tests completed!")

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()