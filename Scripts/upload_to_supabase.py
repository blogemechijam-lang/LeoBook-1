import csv
import os
from datetime import datetime

# This script will upload predictions.csv to Supabase
# You'll need to install: pip install supabase

def upload_predictions_to_supabase(supabase_url: str, service_role_key: str):
    """
    Upload predictions from CSV to Supabase database.
    
    Args:
        supabase_url: Your Supabase project URL (e.g., https://xxx.supabase.co)
        service_role_key: Your SERVICE ROLE key (NOT the anon key!)
    """
    from supabase import create_client
    
    print("🚀 Starting Supabase upload...")
    print(f"📍 Project URL: {supabase_url}")
    
    # Initialize Supabase client
    supabase = create_client(supabase_url, service_role_key)
    
    # Read CSV file
    csv_path = os.path.join(os.path.dirname(__file__), '..', 'Data', 'Store', 'predictions.csv')
    
    if not os.path.exists(csv_path):
        print(f"❌ Error: predictions.csv not found at {csv_path}")
        return
    
    print(f"📂 Reading CSV from: {csv_path}")
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        batch = []
        total_uploaded = 0
        batch_size = 500  # Upload in smaller batches for reliability
        
        for row in reader:
            # Convert string booleans
            if 'outcome_correct' in row:
                if row['outcome_correct'].lower() == 'true':
                    row['outcome_correct'] = True
                elif row['outcome_correct'].lower() == 'false':
                    row['outcome_correct'] = False
                else:
                    row['outcome_correct'] = None
            
            # Convert empty strings to None
            for key, value in row.items():
                if value == '' or value == 'N/A':
                    row[key] = None
            
            batch.append(row)
            
            # Upload when batch is full
            if len(batch) >= batch_size:
                try:
                    supabase.table('predictions').insert(batch).execute()
                    total_uploaded += len(batch)
                    print(f"✅ Uploaded {total_uploaded} rows...")
                    batch = []
                except Exception as e:
                    print(f"❌ Error uploading batch: {e}")
                    print(f"   First row in failed batch: {batch[0] if batch else 'N/A'}")
                    return
        
        # Upload remaining rows
        if batch:
            try:
                supabase.table('predictions').insert(batch).execute()
                total_uploaded += len(batch)
                print(f"✅ Uploaded final batch. Total: {total_uploaded} rows")
            except Exception as e:
                print(f"❌ Error uploading final batch: {e}")
                return
    
    print(f"\n🎉 Upload complete! {total_uploaded} predictions uploaded to Supabase")
    print("\n📊 Next steps:")
    print("1. Verify data in Supabase Dashboard → Table Editor → predictions")
    print("2. Check that indexes were created")
    print("3. Test a query: SELECT * FROM predictions WHERE date >= CURRENT_DATE LIMIT 10")


if __name__ == "__main__":
    print("=" * 60)
    print("  SUPABASE PREDICTIONS UPLOADER")
    print("=" * 60)
    print()
    
    # TODO: Replace these with your actual credentials
    SUPABASE_URL = input("Enter your Supabase Project URL: ").strip()
    SERVICE_ROLE_KEY = input("Enter your SERVICE ROLE Key (NOT anon key): ").strip()
    
    if not SUPABASE_URL or not SERVICE_ROLE_KEY:
        print("❌ Error: Both URL and Service Role Key are required")
        exit(1)
    
    # Confirm before uploading
    print(f"\n⚠️  About to upload predictions.csv to: {SUPABASE_URL}")
    confirm = input("Continue? (yes/no): ").strip().lower()
    
    if confirm == 'yes':
        upload_predictions_to_supabase(SUPABASE_URL, SERVICE_ROLE_KEY)
    else:
        print("❌ Upload cancelled")
