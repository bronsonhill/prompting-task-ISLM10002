#!/usr/bin/env python3
"""
Script to generate student user codes and export to CSV
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from utils.database import connect_mongodb, create_user, generate_unique_code
from datetime import datetime
import argparse

def generate_student_codes(num_codes, output_file=None):
    """Generate specified number of student codes"""
    print(f"Generating {num_codes} student codes...")
    
    # Connect to database
    try:
        db = connect_mongodb()
        print("✅ Connected to MongoDB")
    except Exception as e:
        print(f"❌ Error connecting to database: {str(e)}")
        return False
    
    created_codes = []
    failed_codes = []
    
    # Generate codes
    for i in range(num_codes):
        try:
            # Generate unique code
            code = generate_unique_code()
            
            # Create user in database (no initial consent for students)
            if create_user(code, data_use_consent=None):
                created_codes.append({
                    'code': code
                })
                print(f"✅ Generated code {i+1}/{num_codes}: {code}")
            else:
                failed_codes.append({
                    'code': code,
                    'error': 'Database creation failed'
                })
                print(f"❌ Failed to create user for code: {code}")
                
        except Exception as e:
            failed_codes.append({
                'code': 'Unknown',
                'error': str(e)
            })
            print(f"❌ Error generating code {i+1}: {str(e)}")
    
    # Create DataFrame with single column
    if created_codes:
        df = pd.DataFrame(created_codes)
        
        # Save to CSV
        try:
            if not output_file:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f"student_codes_{timestamp}.csv"
            
            df.to_csv(output_file, index=False)
            print(f"💾 Codes saved to: {output_file}")
            
        except Exception as e:
            print(f"❌ Error saving CSV: {str(e)}")
    
    # Generate summary report
    generate_summary_report(created_codes, failed_codes)
    
    return len(created_codes) > 0

def generate_summary_report(created_codes, failed_codes):
    """Generate a summary report"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    print("\n" + "="*60)
    print("SUMMARY REPORT")
    print("="*60)
    print(f"Successfully created: {len(created_codes)} codes")
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
            f.write(f"Failed: {len(failed_codes)}\n\n")
            
            # Created codes
            if created_codes:
                f.write("CREATED CODES:\n")
                f.write("-" * 30 + "\n")
                for item in created_codes:
                    f.write(f"Code: {item['code']}\n")
                    f.write("-" * 30 + "\n")
                f.write("\n")
            
            # Failed codes
            if failed_codes:
                f.write("FAILED:\n")
                f.write("-" * 30 + "\n")
                for item in failed_codes:
                    f.write(f"Code: {item['code']}\n")
                    f.write(f"Error: {item['error']}\n")
                    f.write("-" * 30 + "\n")
        
        print(f"\n📊 Detailed report saved to: {report_filename}")
        
    except Exception as e:
        print(f"❌ Error saving report: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description="Generate student user codes and export to CSV")
    parser.add_argument(
        "num_codes", 
        type=int,
        help="Number of codes to generate"
    )
    parser.add_argument(
        "--output", 
        help="Output CSV file path (default: auto-generated)"
    )
    
    args = parser.parse_args()
    
    if args.num_codes <= 0:
        print("❌ Error: Number of codes must be positive")
        return
    
    generate_student_codes(args.num_codes, args.output)

if __name__ == "__main__":
    main()