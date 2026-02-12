# Supabase Setup Guide

## 🚀 Quick Setup (5 minutes)

### Step 1: Create Supabase Account
1. Go to **https://supabase.com**
2. Click **"Start your project"**  
3. Sign up with **GitHub** (recommended) or email

### Step 2: Create Project
1. Click **"New Project"**
2. Fill in details:
   - **Name**: `leobook-production`
   - **Database Password**: Generate a strong one (save it securely!)
   - **Region**: Choose closest to your users (e.g., **Europe (Frankfurt)** or **US East (N. Virginia)**)
   - **Pricing Plan**: Free
3. Click **"Create new project"**  
4. ⏳ Wait ~2 minutes for project to initialize

### Step 3: Run Database Schema
1. Once project is ready, go to **SQL Editor** (left sidebar)
2. Click **"New Query"**
3. Copy the entire contents of `Scripts/supabase_schema.sql`
4. Paste into the editor
5. Click **"Run"** (or press Ctrl+Enter)
6. ✅ You should see "Success. No rows returned"

### Step 4: Get API Credentials
1. Go to **Project Settings** (gear icon in left sidebar)
2. Click **"API"** in the settings menu
3. Copy these two values:

   **Project URL:**
   ```
   https://xxxxxxxxxxxxx.supabase.co
   ```

   **Anon/Public Key** (starts with `eyJhbGc...`):
   ```
   eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```

4. **ALSO copy the Service Role Key** (you'll need this for data upload):
   ```
   eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```
   ⚠️ **Keep this secret!** Never commit it to GitHub!

---

## 📤 Upload Data to Supabase

### Option 1: Python Script (Recommended)

1. Install dependencies:
   ```bash
   pip install supabase
   ```

2. Run the upload script:
   ```bash
   cd Scripts
   python upload_to_supabase.py
   ```

3. When prompted:
   - Enter your **Project URL**
   - Enter your **SERVICE ROLE Key** (NOT the anon key!)
   - Type `yes` to confirm

4. ⏳ Wait for upload (~30 seconds for 7,434 rows)

### Option 2: CSV Import (Manual)

1. In Supabase Dashboard, go to **Table Editor**
2. Click on `predictions` table
3. Click **"Insert"** → **"Import data from CSV"**
4. Select `Data/Store/predictions.csv`
5. Map columns automatically
6. Click **"Import"**

---

## ✅ Verify Setup

### Check Data was Uploaded
1. Go to **Table Editor** → `predictions`
2. You should see **7,434 rows**
3. Run this query in SQL Editor:
   ```sql
   SELECT COUNT(*) as total_rows FROM predictions;
   ```
   Expected result: `7434`

### Test Upcoming Matches Query
```sql
SELECT * FROM predictions 
WHERE date >= CURRENT_DATE 
  AND date <= CURRENT_DATE + INTERVAL '14 days'
ORDER BY date ASC
LIMIT 10;
```
This should return matches from the next 2 weeks.

---

## 🔐 Provide Credentials to Developer

Once everything is set up, provide these to me:

1. **Project URL**: `https://xxxxxxxxxxxxx.supabase.co`
2. **Anon/Public Key**: `eyJhbGc...` (safe to share, used in Flutter app)

I'll then update the Flutter app configuration files with these credentials.

---

## 📱 What Happens Next

After you provide the credentials, I will:

1. Update `lib/core/config/supabase_config.dart` with your API keys
2. Modify `lib/main.dart` to initialize Supabase on app startup
3. Rewrite `lib/data/repositories/data_repository.dart` to use Supabase
4. Delete `lib/data/database/predictions_database.dart` (no longer needed)
5. Test on web, mobile, and desktop platforms

**Total time**: ~10 minutes

---

## 🎉 Benefits You'll Get

✅ **No more timeout errors** on web  
✅ **40x smaller payloads** (only upcoming matches)  
✅ **Works on all platforms** identically  
✅ **Production-ready backend**  
✅ **Room to scale** (add features later)  

Let's do this! 🚀
