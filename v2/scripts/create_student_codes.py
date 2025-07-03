#!/usr/bin/env python3
"""
Script to create student user codes from CSV file
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from utils.database import connect_mongodb, create_user, generate_unique_code
from datetime import datetime
import argparse

def create_student_codes(csv_file, output_file=None):
    """Create student codes from CSV file"""
    print(f"Processing student data from: {csv_file}")
    
    # Connect to database
    try:
        db = connect_mongodb()
        print("✅ Connected to MongoDB")
    except Exception as e:
        print(f"❌ Error connecting to database: {str(e)}")
        return False
    
    # Read CSV file
    try:
        df = pd.read_csv(csv_file)
        print(f"📊 Loaded {len(df)} rows from CSV")
    except Exception as e:
        print(f"❌ Error reading CSV file: {str(e)}")
        return False
    
    # Validate CSV columns
    required_columns = ['name', 'email']  # Adjust as needed
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        print(f"❌ Missing required columns: {missing_columns}")
        print(f"Available columns: {list(df.columns)}")
        return False
    
    # Check if 'code' column already exists
    has_existing_codes = 'code' in df.columns
    if has_existing_codes:
        print("📝 Found existing 'code' column in CSV")
    
    created_codes = []
    failed_codes = []
    skipped_codes = []
    
    # Process each student
    for index, row in df.iterrows():
        try:
            student_name = str(row['name']).strip()
            student_email = str(row['email']).strip()
            
            # Skip if existing code and it's not empty
            if has_existing_codes and pd.notna(row['code']) and str(row['code']).strip():
                existing_code = str(row['code']).strip()
                skipped_codes.append({
                    'name': student_name,
                    'email': student_email,
                    'code': existing_code
                })
                print(f"⏭️  Skipped {student_name} - already has code: {existing_code}")
                continue
            
            # Generate unique code
            code = generate_unique_code()
            
            # Create user in database (no initial consent for students)
            if create_user(code, data_use_consent=None):
                # Add code to dataframe
                df.at[index, 'code'] = code
                
                created_codes.append({
                    'name': student_name,
                    'email': student_email,
                    'code': code
                })
                print(f"✅ Created code for {student_name}: {code}")
            else:
                failed_codes.append({
                    'name': student_name,
                    'email': student_email,
                    'error': 'Database creation failed'
                })
                print(f"❌ Failed to create user for {student_name}")
                
        except Exception as e:
            failed_codes.append({
                'name': str(row.get('name', 'Unknown')),
                'email': str(row.get('email', 'Unknown')),
                'error': str(e)
            })
            print(f"❌ Error processing row {index}: {str(e)}")
    
    # Save updated CSV
    try:
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"students_with_codes_{timestamp}.csv"
        
        df.to_csv(output_file, index=False)
        print(f"💾 Updated CSV saved to: {output_file}")
        
    except Exception as e:
        print(f"❌ Error saving CSV: {str(e)}")
    
    # Generate summary report
    generate_summary_report(created_codes, failed_codes, skipped_codes)
    
    return len(created_codes) > 0

def generate_summary_report(created_codes, failed_codes, skipped_codes):
    """Generate a summary report"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    print("\n" + "="*60)
    print("SUMMARY REPORT")
    print("="*60)
    print(f"Successfully created: {len(created_codes)} codes")
    print(f"Skipped (existing): {len(skipped_codes)} codes")
    print(f"Failed: {len(failed_codes)} codes")
    
    # Save detailed report
    report_filename = f"student_codes_report_{timestamp}.txt"
    
    try:
        with open(report_filename, 'w') as f:
            f.write(f"Student Codes Report\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n")
            f.write("="*60 + "\n\n")
            
            # Summary
            f.write("SUMMARY:\n")
            f.write(f"Created: {len(created_codes)}\n")
            f.write(f"Skipped: {len(skipped_codes)}\n")
            f.write(f"Failed: {len(failed_codes)}\n\n")
            
            # Created codes
            if created_codes:
                f.write("CREATED CODES:\n")
                f.write("-" * 30 + "\n")
                for item in created_codes:
                    f.write(f"Name: {item['name']}\n")
                    f.write(f"Email: {item['email']}\n")
                    f.write(f"Code: {item['code']}\n")
                    f.write("-" * 30 + "\n")
                f.write("\n")
            
            # Skipped codes
            if skipped_codes:
                f.write("SKIPPED (EXISTING CODES):\n")
                f.write("-" * 30 + "\n")
                for item in skipped_codes:
                    f.write(f"Name: {item['name']}\n")
                    f.write(f"Email: {item['email']}\n")
                    f.write(f"Existing Code: {item['code']}\n")
                    f.write("-" * 30 + "\n")
                f.write("\n")
            
            # Failed codes
            if failed_codes:
                f.write("FAILED:\n")
                f.write("-" * 30 + "\n")
                for item in failed_codes:
                    f.write(f"Name: {item['name']}\n")
                    f.write(f"Email: {item['email']}\n")
                    f.write(f"Error: {item['error']}\n")
                    f.write("-" * 30 + "\n")
        
        print(f"\n📊 Detailed report saved to: {report_filename}")
        
    except Exception as e:
        print(f"❌ Error saving report: {str(e)}")

def create_sample_csv():
    """Create a sample CSV file for testing"""
    sample_data = {
        'name': [
            'John Doe',
            'Jane Smith',
            'Mike Johnson',
            'Sarah Wilson',
            'Tom Brown'
        ],
        'email': [
            'john.doe@university.edu',
            'jane.smith@university.edu',
            'mike.johnson@university.edu',
            'sarah.wilson@university.edu',
            'tom.brown@university.edu'
        ]
    }
    
    df = pd.DataFrame(sample_data)
    filename = "sample_students.csv"
    df.to_csv(filename, index=False)
    
    print(f"📝 Sample CSV created: {filename}")
    print("Columns:", list(df.columns))
    print(f"Rows: {len(df)}")

def main():
    parser = argparse.ArgumentParser(description="Create student user codes from CSV file")
    parser.add_argument(
        "csv_file", 
        nargs='?',
        help="Path to CSV file with student data"
    )
    parser.add_argument(
        "--output", 
        help="Output CSV file path (default: auto-generated)"
    )
    parser.add_argument(
        "--sample", 
        action="store_true", 
        help="Create a sample CSV file for testing"
    )
    
    args = parser.parse_args()
    
    if args.sample:
        create_sample_csv()
        return
    
    if not args.csv_file:
        print("❌ Error: CSV file path is required")
        print("Usage: python create_student_codes.py <csv_file>")
        print("Or: python create_student_codes.py --sample")
        return
    
    if not os.path.exists(args.csv_file):
        print(f"❌ Error: File not found: {args.csv_file}")
        return
    
    create_student_codes(args.csv_file, args.output)

if __name__ == "__main__":
    main()