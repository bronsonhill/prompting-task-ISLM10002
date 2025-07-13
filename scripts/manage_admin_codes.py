#!/usr/bin/env python3
"""
Admin Code Management Script

This script allows you to manage admin codes in the database.
It can be used to add, remove, and list admin codes.

Usage:
    python manage_admin_codes.py --add CODE --level admin
    python manage_admin_codes.py --remove CODE
    python manage_admin_codes.py --list
    python manage_admin_codes.py --init
"""

import argparse
import sys
import os

# Add the parent directory to the path so we can import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database import (
    add_admin_code, remove_admin_code, get_admin_codes, 
    is_admin_code, get_admin_level, create_initial_admin_code
)

def add_admin_code_script(code: str, level: str, added_by: str = "script"):
    """Add an admin code via script"""
    if not code or len(code) != 5 or not code.isalnum():
        print(f"❌ Error: Invalid code format. Code must be 5 alphanumeric characters.")
        return False
    
    if level not in ["admin", "super_admin"]:
        print(f"❌ Error: Invalid level. Must be 'admin' or 'super_admin'.")
        return False
    
    if is_admin_code(code):
        print(f"❌ Error: Code '{code}' is already an admin code.")
        return False
    
    if add_admin_code(code.upper(), level, added_by):
        print(f"✅ Successfully added admin code '{code.upper()}' with level '{level}'")
        return True
    else:
        print(f"❌ Error: Failed to add admin code '{code}'")
        return False

def remove_admin_code_script(code: str, removed_by: str = "script"):
    """Remove an admin code via script"""
    if not is_admin_code(code):
        print(f"❌ Error: Code '{code}' is not an admin code.")
        return False
    
    admin_level = get_admin_level(code)
    if admin_level == "super_admin":
        print(f"❌ Error: Cannot remove super admin code '{code}' via script.")
        print("   Use the admin interface or database directly for super admin removal.")
        return False
    
    if remove_admin_code(code.upper(), removed_by):
        print(f"✅ Successfully removed admin code '{code.upper()}'")
        return True
    else:
        print(f"❌ Error: Failed to remove admin code '{code}'")
        return False

def list_admin_codes_script():
    """List all admin codes"""
    admin_codes = get_admin_codes(include_inactive=True)
    
    if not admin_codes:
        print("📋 No admin codes found in database.")
        return
    
    print("📋 Admin Codes in Database:")
    print("-" * 60)
    print(f"{'Code':<10} {'Level':<15} {'Status':<10} {'Added By':<15} {'Created'}")
    print("-" * 60)
    
    for code_data in admin_codes:
        code = code_data.get("code", "")
        level = code_data.get("level", "")
        is_active = "Active" if code_data.get("is_active", True) else "Inactive"
        added_by = code_data.get("added_by", "")
        created_at = code_data.get("created_at", "")
        
        if created_at:
            created_str = created_at.strftime("%Y-%m-%d %H:%M")
        else:
            created_str = "Unknown"
        
        print(f"{code:<10} {level:<15} {is_active:<10} {added_by:<15} {created_str}")
    
    print("-" * 60)
    
    # Summary
    active_codes = [c for c in admin_codes if c.get("is_active", True)]
    super_admins = [c for c in active_codes if c.get("level") == "super_admin"]
    regular_admins = [c for c in active_codes if c.get("level") == "admin"]
    
    print(f"\n📊 Summary:")
    print(f"   Total admin codes: {len(admin_codes)}")
    print(f"   Active codes: {len(active_codes)}")
    print(f"   Super admins: {len(super_admins)}")
    print(f"   Regular admins: {len(regular_admins)}")

def initialize_admin_codes_script():
    """Initialize secure admin codes"""
    print("🚀 Creating secure initial admin code...")
    
    admin_code = create_initial_admin_code()
    if admin_code:
        print("✅ Secure admin code created successfully!")
        print(f"\n🔐 ADMIN CODE: {admin_code}")
        print("⚠️  IMPORTANT: Save this code securely! It cannot be recovered.")
        print("   Use this code to log in as a super administrator.")
        print("   You can then create additional admin codes through the web interface.")
    else:
        print("ℹ️  Admin codes already exist in database.")
        print("   Use --list to see current admin codes.")
        print("   Use --add to create additional admin codes.")

def main():
    parser = argparse.ArgumentParser(
        description="Manage admin codes in the chat application database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python manage_admin_codes.py --init-secure
  python manage_admin_codes.py --list
  python manage_admin_codes.py --add ABC12 --level admin
  python manage_admin_codes.py --add XYZ99 --level super_admin
  python manage_admin_codes.py --remove TEST1
        """
    )
    
    parser.add_argument(
        "--add", 
        metavar="CODE",
        help="Add a new admin code (5 alphanumeric characters)"
    )
    
    parser.add_argument(
        "--level",
        choices=["admin", "super_admin"],
        default="admin",
        help="Admin level for new code (default: admin)"
    )
    
    parser.add_argument(
        "--remove", 
        metavar="CODE",
        help="Remove an admin code (cannot remove super admins)"
    )
    
    parser.add_argument(
        "--list", 
        action="store_true",
        help="List all admin codes in database"
    )
    
    parser.add_argument(
        "--init", 
        action="store_true",
        help="Initialize secure admin code (DEPRECATED - use --init-secure)"
    )
    
    parser.add_argument(
        "--init-secure", 
        action="store_true",
        help="Create secure initial admin code (recommended for first-time setup)"
    )
    
    args = parser.parse_args()
    
    # Check if at least one action is specified
    if not any([args.add, args.remove, args.list, args.init, args.init_secure]):
        parser.print_help()
        return
    
    try:
        if args.init_secure:
            initialize_admin_codes_script()
        elif args.init:
            print("⚠️  --init is deprecated. Use --init-secure instead.")
            initialize_admin_codes_script()
        elif args.list:
            list_admin_codes_script()
        elif args.add:
            add_admin_code_script(args.add, args.level)
        elif args.remove:
            remove_admin_code_script(args.remove)
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("Make sure your MongoDB connection is configured in .streamlit/secrets.toml")
        sys.exit(1)

if __name__ == "__main__":
    main() 