#!/usr/bin/env python3
"""
Script to fix duplicate conversation and prompt IDs
This script will:
1. Find and fix duplicate conversation IDs
2. Find and fix duplicate prompt IDs  
3. Set up proper counters for future ID generation
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from utils.database import get_database
from datetime import datetime

def fix_conversation_ids():
    """Fix duplicate conversation IDs by renumbering them"""
    print("🔧 Fixing conversation IDs...")
    
    db = get_database()
    conversations_collection = db.conversations
    counters_collection = db.counters
    
    # Get all conversations sorted by creation time
    conversations = list(conversations_collection.find().sort("created_at", 1))
    
    if not conversations:
        print("No conversations found.")
        return
    
    print(f"Found {len(conversations)} conversations to process...")
    
    # Track used IDs to detect duplicates
    used_ids = set()
    duplicate_count = 0
    renumbered_count = 0
    
    for i, conv in enumerate(conversations):
        current_id = conv.get("conversation_id")
        new_id = f"C{i+1:03d}"
        
        if current_id in used_ids:
            print(f"  Found duplicate ID: {current_id}")
            duplicate_count += 1
            
            # Update the conversation with new ID
            result = conversations_collection.update_one(
                {"_id": conv["_id"]},
                {"$set": {"conversation_id": new_id}}
            )
            
            if result.modified_count > 0:
                print(f"    Renumbered to: {new_id}")
                renumbered_count += 1
            else:
                print(f"    Failed to renumber!")
        else:
            used_ids.add(current_id)
            
            # If the ID is not sequential, update it
            if current_id != new_id:
                print(f"  Fixing non-sequential ID: {current_id} -> {new_id}")
                result = conversations_collection.update_one(
                    {"_id": conv["_id"]},
                    {"$set": {"conversation_id": new_id}}
                )
                if result.modified_count > 0:
                    renumbered_count += 1
    
    # Set up the counter for future conversation IDs
    counters_collection.update_one(
        {"_id": "conversation_id"},
        {"$set": {"sequence": len(conversations)}},
        upsert=True
    )
    
    print(f"✅ Conversation ID fix complete:")
    print(f"   - Found {duplicate_count} duplicate IDs")
    print(f"   - Renumbered {renumbered_count} conversations")
    print(f"   - Set counter to {len(conversations)}")

def fix_prompt_ids():
    """Fix duplicate prompt IDs by renumbering them per user"""
    print("\n🔧 Fixing prompt IDs...")
    
    db = get_database()
    prompts_collection = db.prompts
    counters_collection = db.counters
    
    # Get all prompts sorted by user and creation time
    prompts = list(prompts_collection.find().sort([("user_code", 1), ("created_at", 1)]))
    
    if not prompts:
        print("No prompts found.")
        return
    
    print(f"Found {len(prompts)} prompts to process...")
    
    # Group prompts by user
    user_prompts = {}
    for prompt in prompts:
        user_code = prompt.get("user_code")
        if user_code not in user_prompts:
            user_prompts[user_code] = []
        user_prompts[user_code].append(prompt)
    
    duplicate_count = 0
    renumbered_count = 0
    
    for user_code, user_prompt_list in user_prompts.items():
        print(f"  Processing user: {user_code} ({len(user_prompt_list)} prompts)")
        
        # Track used IDs for this user
        used_ids = set()
        
        for i, prompt in enumerate(user_prompt_list):
            current_id = prompt.get("prompt_id")
            new_id = f"P{i+1:03d}"
            
            if current_id in used_ids:
                print(f"    Found duplicate ID: {current_id}")
                duplicate_count += 1
                
                # Update the prompt with new ID
                result = prompts_collection.update_one(
                    {"_id": prompt["_id"]},
                    {"$set": {"prompt_id": new_id}}
                )
                
                if result.modified_count > 0:
                    print(f"      Renumbered to: {new_id}")
                    renumbered_count += 1
                else:
                    print(f"      Failed to renumber!")
            else:
                used_ids.add(current_id)
                
                # If the ID is not sequential, update it
                if current_id != new_id:
                    print(f"    Fixing non-sequential ID: {current_id} -> {new_id}")
                    result = prompts_collection.update_one(
                        {"_id": prompt["_id"]},
                        {"$set": {"prompt_id": new_id}}
                    )
                    if result.modified_count > 0:
                        renumbered_count += 1
        
        # Set up the counter for this user's future prompt IDs
        counters_collection.update_one(
            {"_id": f"prompt_id_{user_code}"},
            {"$set": {"sequence": len(user_prompt_list)}},
            upsert=True
        )
    
    print(f"✅ Prompt ID fix complete:")
    print(f"   - Found {duplicate_count} duplicate IDs")
    print(f"   - Renumbered {renumbered_count} prompts")
    print(f"   - Set counters for {len(user_prompts)} users")

def verify_fixes():
    """Verify that all IDs are now unique"""
    print("\n🔍 Verifying fixes...")
    
    db = get_database()
    conversations_collection = db.conversations
    prompts_collection = db.prompts
    
    # Check conversation IDs
    conversation_ids = [conv["conversation_id"] for conv in conversations_collection.find()]
    unique_conversation_ids = set(conversation_ids)
    
    if len(conversation_ids) == len(unique_conversation_ids):
        print("✅ All conversation IDs are unique")
    else:
        print(f"❌ Found {len(conversation_ids) - len(unique_conversation_ids)} duplicate conversation IDs")
    
    # Check prompt IDs per user
    all_prompts = list(prompts_collection.find())
    user_prompts = {}
    for prompt in all_prompts:
        user_code = prompt.get("user_code")
        if user_code not in user_prompts:
            user_prompts[user_code] = []
        user_prompts[user_code].append(prompt["prompt_id"])
    
    all_unique = True
    for user_code, prompt_ids in user_prompts.items():
        unique_prompt_ids = set(prompt_ids)
        if len(prompt_ids) != len(unique_prompt_ids):
            print(f"❌ User {user_code} has {len(prompt_ids) - len(unique_prompt_ids)} duplicate prompt IDs")
            all_unique = False
    
    if all_unique:
        print("✅ All prompt IDs are unique per user")

def main():
    """Main function to run the ID fix"""
    print("🚀 Starting ID fix process...")
    print(f"Timestamp: {datetime.now()}")
    print("=" * 50)
    
    try:
        # Fix conversation IDs
        fix_conversation_ids()
        
        # Fix prompt IDs
        fix_prompt_ids()
        
        # Verify fixes
        verify_fixes()
        
        print("\n" + "=" * 50)
        print("✅ ID fix process completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during ID fix process: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
