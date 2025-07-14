#!/usr/bin/env python3
"""
Script to update existing prompts with new token count fields
"""
import sys
import os

# Add the parent directory to the path so we can import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from utils.database import update_prompt_token_counts, get_database

def main():
    """Update all existing prompts with new token count fields"""
    print("🔄 Updating prompt token counts...")
    
    try:
        # Initialize database connection
        try:
            db = get_database()
        except Exception as e:
            print(f"❌ Failed to connect to database: {str(e)}")
            return
        
        # Update token counts
        updated_count = update_prompt_token_counts()
        
        if updated_count > 0:
            print(f"✅ Successfully updated {updated_count} prompts with new token count fields")
        else:
            print("ℹ️  No prompts needed updating (all prompts already have the new fields)")
            
        # Show some statistics
        prompts_collection = db.prompts
        total_prompts = prompts_collection.count_documents({})
        prompts_with_new_fields = prompts_collection.count_documents({
            "prompt_token_count": {"$exists": True},
            "document_token_count": {"$exists": True},
            "total_token_count": {"$exists": True}
        })
        
        print(f"\n📊 Statistics:")
        print(f"   Total prompts: {total_prompts}")
        print(f"   Prompts with new fields: {prompts_with_new_fields}")
        print(f"   Prompts needing update: {total_prompts - prompts_with_new_fields}")
        
    except Exception as e:
        print(f"❌ Error updating token counts: {str(e)}")

if __name__ == "__main__":
    main() 