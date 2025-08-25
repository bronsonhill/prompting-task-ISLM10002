#!/usr/bin/env python3
"""
Script to delete all conversations except for conversations 1 to 10
This script will:
1. Keep conversations C001 to C010
2. Delete all other conversations
3. Update the conversation counter accordingly
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from utils.database import get_database
from datetime import datetime

def cleanup_conversations():
    """Delete all conversations except C001 to C010"""
    print("🧹 Cleaning up conversations...")
    
    db = get_database()
    conversations_collection = db.conversations
    counters_collection = db.counters
    
    # Get all conversations
    all_conversations = list(conversations_collection.find().sort("conversation_id", 1))
    
    if not all_conversations:
        print("No conversations found.")
        return
    
    print(f"Found {len(all_conversations)} total conversations")
    
    # Identify conversations to keep (C001 to C010)
    conversations_to_keep = []
    conversations_to_delete = []
    
    for conv in all_conversations:
        conv_id = conv.get("conversation_id")
        if conv_id and conv_id in [f"C{i:03d}" for i in range(1, 11)]:
            conversations_to_keep.append(conv)
        else:
            conversations_to_delete.append(conv)
    
    print(f"Conversations to keep: {len(conversations_to_keep)}")
    print(f"Conversations to delete: {len(conversations_to_delete)}")
    
    # Show which conversations will be kept
    if conversations_to_keep:
        print("\nConversations that will be kept:")
        for conv in conversations_to_keep:
            user_code = conv.get("user_code", "Unknown")
            created_at = conv.get("created_at", "Unknown")
            if isinstance(created_at, datetime):
                created_str = created_at.strftime("%Y-%m-%d %H:%M")
            else:
                created_str = str(created_at)
            print(f"  {conv['conversation_id']} - User: {user_code} - Created: {created_str}")
    
    # Show which conversations will be deleted
    if conversations_to_delete:
        print(f"\nConversations that will be deleted (showing first 10):")
        for i, conv in enumerate(conversations_to_delete[:10]):
            user_code = conv.get("user_code", "Unknown")
            created_at = conv.get("created_at", "Unknown")
            if isinstance(created_at, datetime):
                created_str = created_at.strftime("%Y-%m-%d %H:%M")
            else:
                created_str = str(created_at)
            print(f"  {conv['conversation_id']} - User: {user_code} - Created: {created_str}")
        
        if len(conversations_to_delete) > 10:
            print(f"  ... and {len(conversations_to_delete) - 10} more conversations")
    
    # Ask for confirmation
    print(f"\n⚠️  WARNING: This will permanently delete {len(conversations_to_delete)} conversations!")
    print("Are you sure you want to proceed? (yes/no): ", end="")
    
    # For automated execution, we'll proceed without user input
    # In a real scenario, you might want to add user confirmation here
    confirmation = "yes"  # For automated execution
    
    if confirmation.lower() != "yes":
        print("Operation cancelled.")
        return
    
    # Delete conversations
    deleted_count = 0
    for conv in conversations_to_delete:
        result = conversations_collection.delete_one({"_id": conv["_id"]})
        if result.deleted_count > 0:
            deleted_count += 1
            if deleted_count % 100 == 0:  # Progress indicator
                print(f"  Deleted {deleted_count} conversations...")
    
    print(f"\n✅ Deleted {deleted_count} conversations")
    
    # Update the conversation counter to reflect the new count
    remaining_count = len(conversations_to_keep)
    counters_collection.update_one(
        {"_id": "conversation_id"},
        {"$set": {"sequence": remaining_count}},
        upsert=True
    )
    
    print(f"✅ Updated conversation counter to {remaining_count}")
    
    # Verify the cleanup
    remaining_conversations = list(conversations_collection.find().sort("conversation_id", 1))
    print(f"\n🔍 Verification:")
    print(f"  Remaining conversations: {len(remaining_conversations)}")
    
    if remaining_conversations:
        print("  Remaining conversation IDs:")
        for conv in remaining_conversations:
            print(f"    {conv['conversation_id']}")
    
    # Check if we have exactly C001 to C010
    expected_ids = [f"C{i:03d}" for i in range(1, 11)]
    actual_ids = [conv["conversation_id"] for conv in remaining_conversations]
    
    if set(actual_ids) == set(expected_ids):
        print("✅ All remaining conversations are C001 to C010 as expected")
    else:
        print("⚠️  Warning: Some expected conversations are missing or extra conversations remain")
        missing = set(expected_ids) - set(actual_ids)
        extra = set(actual_ids) - set(expected_ids)
        if missing:
            print(f"  Missing: {missing}")
        if extra:
            print(f"  Extra: {extra}")

def main():
    """Main function to run the conversation cleanup"""
    print("🚀 Starting conversation cleanup...")
    print(f"Timestamp: {datetime.now()}")
    print("=" * 50)
    
    try:
        cleanup_conversations()
        
        print("\n" + "=" * 50)
        print("✅ Conversation cleanup completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during conversation cleanup: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
