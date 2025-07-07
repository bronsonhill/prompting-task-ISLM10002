#!/usr/bin/env python3
"""
Script to create test user codes for development
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database import connect_mongodb, create_user, generate_unique_code
from datetime import datetime
import argparse

def create_test_codes(num_codes=1):
    """Create test user codes"""
    print(f"Creating {num_codes} test user codes...")
    
    # Connect to database
    try:
        db = connect_mongodb()
        print("✅ Connected to MongoDB")
    except Exception as e:
        print(f"❌ Error connecting to database: {str(e)}")
        return False
    
    created_codes = []
    failed_codes = []
    
    for i in range(num_codes):
        try:
            # Generate unique code
            code = generate_unique_code()
            
            # Create user with consent set to True for test users
            if create_user(code, data_use_consent=True):
                created_codes.append(code)
                print(f"✅ Created test user: {code}")
            else:
                failed_codes.append(code)
                print(f"❌ Failed to create user: {code}")
                
        except Exception as e:
            print(f"❌ Error creating user {i+1}: {str(e)}")
            failed_codes.append(f"ERROR_{i+1}")
    
    # Summary
    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)
    print(f"Successfully created: {len(created_codes)} codes")
    print(f"Failed: {len(failed_codes)} codes")
    
    if created_codes:
        print("\n📝 CREATED TEST CODES:")
        for code in created_codes:
            print(f"  {code}")
    
    if failed_codes:
        print("\n❌ FAILED CODES:")
        for code in failed_codes:
            print(f"  {code}")
    
    # Save to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"test_codes_{timestamp}.txt"
    
    try:
        with open(filename, 'w') as f:
            f.write(f"Test Codes Generated: {datetime.now().isoformat()}\n")
            f.write(f"Total Created: {len(created_codes)}\n")
            f.write("="*50 + "\n")
            f.write("CODES:\n")
            for code in created_codes:
                f.write(f"{code}\n")
        
        print(f"\n💾 Codes saved to: {filename}")
        
    except Exception as e:
        print(f"❌ Error saving codes to file: {str(e)}")
    
    return len(created_codes) > 0

def main():
    parser = argparse.ArgumentParser(description="Create test user codes for development")
    parser.add_argument(
        "--count", 
        type=int, 
        default=1, 
        help="Number of test codes to create (default: 1)"
    )
    parser.add_argument(
        "--list", 
        action="store_true", 
        help="List existing test users"
    )
    
    args = parser.parse_args()
    
    if args.list:
        list_test_users()
    else:
        create_test_codes(args.count)

def list_test_users():
    """List existing test users"""
    try:
        db = connect_mongodb()
        if not db:
            print("❌ Error: Could not connect to database")
            return
            
        users_collection = db.users
        users = list(users_collection.find({}).sort("created_at", -1))
        
        print(f"📊 Total users in database: {len(users)}")
        print("="*50)
        
        for user in users:
            consent_status = "✅" if user.get('data_use_consent') else "❌" if user.get('data_use_consent') is False else "❓"
            print(f"Code: {user['code']} | Consent: {consent_status} | Created: {user['created_at'].strftime('%Y-%m-%d %H:%M')}")
            
    except Exception as e:
        print(f"❌ Error listing users: {str(e)}")

if __name__ == "__main__":
    main()