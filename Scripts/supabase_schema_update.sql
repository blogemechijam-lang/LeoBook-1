-- Supabase Schema Update: Add 'status' Column to schedules Table
-- Run this in Supabase SQL Editor (Dashboard -> SQL Editor -> New Query)
-- Author: LeoBook Team
-- Date: 2026-02-12

-- ============================================================================
-- SCHEDULES TABLE: Add 'status' column
-- ============================================================================

-- Add status column (if not exists)
ALTER TABLE schedules 
ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'scheduled';

-- Create index for faster status filtering
CREATE INDEX IF NOT EXISTS idx_schedules_status ON schedules(status);

-- Populate status from match_status (if data already exists)
UPDATE schedules
SET status = CASE 
    WHEN match_status = 'finished' THEN 'finished'
    WHEN match_status = 'postponed' THEN 'postponed'
    WHEN match_status = 'canceled' OR match_status = 'cancelled' THEN 'canceled'
    ELSE 'scheduled'
END
WHERE status IS NULL OR status = 'scheduled';

-- ============================================================================
-- VERIFY CHANGES
-- ============================================================================

-- Check column exists
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'schedules' AND column_name = 'status';

-- Check status distribution
SELECT status, COUNT(*) as count
FROM schedules
GROUP BY status
ORDER BY count DESC;

-- Sample data check
SELECT fixture_id, date, home_team, away_team, match_status, status
FROM schedules
LIMIT 20;

-- ============================================================================
-- NOTES
-- ============================================================================
-- This script is idempotent - safe to run multiple times
-- The 'status' column will be used by the Flutter app for quick filtering:
--   - 'scheduled': Future matches
--   - 'finished': Past matches with results
--   - 'postponed': Delayed matches
--   - 'canceled': Cancelled matches
--   - Live matches are determined dynamically by app logic
