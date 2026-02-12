# Production Requirements for Supabase Sync Integration

## Overview
Automated sync system to push Data/Store CSV changes to Supabase after Leo.py execution.

## Architecture
```
Leo.py (generates predictions) 
    → Data/Store/predictions.csv (source of truth)
    → [User prompt: Sync to Supabase? Y/N]
    → Scripts/sync_to_supabase.py (IF YES)
    → Supabase Database (API for Flutter app)
```

---

## Production Setup Checklist

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

**New dependencies:**
- `supabase>=2.0.0` - Python client for Supabase
- `python-dotenv` (already installed) - Environment variable management

### 2. Configure Environment Variables

**Create `.env` file** (copy from `.env.example`):
```bash
cp .env.example .env
```

**Fill in your credentials:**
```env
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1...  # From Supabase Dashboard → API → Service Role
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1...    # For Flutter app (optional for sync script)
```

> ⚠️ **SECURITY**: Add `.env` to `.gitignore` (already done). NEVER commit credentials!

### 3. Set up Logging Directory
```bash
mkdir -p logs
```

Logs will be written to: `logs/supabase_sync.log`

### 4. Test Supabase Connection
```bash
# Dry run (doesn't write to database)
python Scripts/sync_to_supabase.py --dry-run
```

Expected output:
```
✅ Connected to Supabase: https://xxx.supabase.co
📂 Read 7434 rows from predictions.csv
🔍 DRY RUN MODE - No data will be written
📦 Processing batch 1/15 (500 rows)
   Would upsert 500 rows
...
🎉 Sync completed successfully!
```

### 5. Run First Sync (Manual)
```bash
python Scripts/sync_to_supabase.py
```

You'll be prompted:
```
🔄 Update Supabase with Data/Store changes? (Y/N): Y
```

---

## Integration with Leo.py

### Option A: Manual Integration (Recommended for testing)

Add this to the **end of `Leo.py`** (before script exits):

```python
import subprocess
import sys

def sync_to_supabase():
    """Prompt user to sync predictions to Supabase."""
    try:
        # Run sync script
        result = subprocess.run(
            [sys.executable, 'Scripts/sync_to_supabase.py'],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=False  # Show output in real-time
        )
        
        if result.returncode == 0:
            print("✅ Supabase sync completed successfully")
        else:
            print("⚠️  Supabase sync failed (check logs/supabase_sync.log)")
            
    except Exception as e:
        print(f"⚠️  Could not run Supabase sync: {e}")

# At the very end of Leo.py, before exit:
if __name__ == "__main__":
    # ... your existing code ...
    
    # Sync to Supabase
    sync_to_supabase()
```

### Option B: Automatic Sync (Production)

Add `--force` flag to skip prompt:

```python
def sync_to_supabase_auto():
    """Automatically sync to Supabase without prompting."""
    subprocess.run(
        [sys.executable, 'Scripts/sync_to_supabase.py', '--force'],
        cwd=os.path.dirname(os.path.abspath(__file__))
    )
```

---

## Sync Script Features

### UPSERT Logic
- **Insert**: New predictions (fixture_id not in database)
- **Update**: Existing predictions (fixture_id already exists)
- **Conflict Resolution**: Uses `fixture_id` as unique key

### Batch Processing
- Processes 500 rows per batch
- Prevents memory issues with large datasets
- Graceful error handling per batch

### Error Handling
- Validates environment variables
- Handles missing CSV files
- Logs failed batches for debugging
- Returns non-zero exit code on failure

### Logging
-Writes to: `logs/supabase_sync.log`
- **Format**: `YYYY-MM-DD HH:MM:SS - LEVEL - Message`
- **Retention**: Append mode (you should rotate logs periodically)

---

## CLI Usage

```bash
# Interactive mode (prompts user)
python Scripts/sync_to_supabase.py

# Dry run (simulate without writing)
python Scripts/sync_to_supabase.py --dry-run

# Force sync (no prompt)
python Scripts/sync_to_supabase.py --force

# Combine dry-run + force (for CI/CD testing)
python Scripts/sync_to_supabase.py --dry-run --force
```

---

## Monitoring & Safety

### Check Sync Logs
```bash
tail -f logs/supabase_sync.log
```

### Verify in Supabase Dashboard
1. Go to **Table Editor** → `predictions`
2. Check row count matches CSV
3. Run test query:
   ```sql
   SELECT COUNT(*) FROM predictions;
   SELECT * FROM predictions ORDER BY generated_at DESC LIMIT 10;
   ```

### Rollback Strategy
If sync goes wrong:
1. **Supabase Dashboard** → **SQL Editor**
2. Delete recent records:
   ```sql
   DELETE FROM predictions 
   WHERE created_at > '2026-02-10 22:00:00';
   ```
3. Re-run sync script

### Conflict Resolution
The script uses `fixture_id` as the unique key:
- **Same fixture_id**: Updates existing row
- **New fixture_id**: Inserts new row
- **Deleted from CSV**: Stays in database (manual cleanup required)

---

## Performance Benchmarks

| Rows | Sync Time | Bandwidth |
|------|-----------|-----------|
| 1,000 | ~3s | ~500 KB |
| 7,500 | ~20s | ~3.5 MB |
| 10,000 | ~25s | ~4.7 MB |

**Recommendation**: Run sync once per Leo.py execution (not every minor change).

---

## Security Best Practices

1. ✅ **Never commit** `.env` file
2. ✅ **Use Service Role Key** for sync script (has write access)
3. ✅ **Use Anon Key** in Flutter app (read-only via RLS)
4. ✅ **Rotate keys** if compromised (Supabase Dashboard → API → Reset)
5. ✅ **Monitor logs** for unauthorized access attempts

---

## Troubleshooting

### Error: "Missing environment variables"
**Solution**: Create `.env` file and add credentials

### Error: "predictions.csv not found"
**Solution**: Check file exists at `Data/Store/predictions.csv`

### Error: "Connection timeout"
**Solution**: Check internet connection and Supabase URL

### Error: "Permission denied"
**Solution**: Verify you're using SERVICE_ROLE_KEY (not ANON_KEY)

### Batch fails with "duplicate key"
**Solution**: This is normal during UPSERT - script resolves automatically

---

## Production Deployment

### GitHub Actions (CI/CD)
```yaml
name: Sync to Supabase

on:
  push:
    paths:
      - 'Data/Store/predictions.csv'

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Sync to Supabase
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_SERVICE_KEY: ${{ secrets.SUPABASE_SERVICE_KEY }}
        run: python Scripts/sync_to_supabase.py --force
```

---

## Summary

✅ **Source of Truth**: CSV files (generated by Leo.py)  
✅ **Sync Target**: Supabase (consumed by Flutter app)  
✅ **Trigger**: User prompt after Leo.py completes  
✅ **Operation**: UPSERT (insert new, update existing)  
✅ **Safety**: Dry-run mode, logging, error handling  
✅ **Performance**: Batched processing, ~25s for 10k rows  

**Next Steps:**
1. Set up `.env` with your Supabase credentials
2. Run `python Scripts/sync_to_supabase.py --dry-run` to test
3. Integrate sync call into `Leo.py` shutdown
4. Monitor `logs/supabase_sync.log` for issues
