-- Run this script in Supabase SQL Editor to patch existing tables safely

-- Idempotent Policy Creation (Avoids 'policy already exists' errors)
DO $$
BEGIN
    -- Predictions
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'predictions' AND policyname = 'Public read access') THEN
        CREATE POLICY "Public read access" ON predictions FOR SELECT USING (true);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'predictions' AND policyname = 'Service role write access') THEN
        CREATE POLICY "Service role write access" ON predictions FOR ALL USING (auth.role() = 'service_role');
    END IF;

    -- Schedules
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'schedules' AND policyname = 'Public read schedules') THEN
        CREATE POLICY "Public read schedules" ON schedules FOR SELECT USING (true);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'schedules' AND policyname = 'Service write schedules') THEN
        CREATE POLICY "Service write schedules" ON schedules FOR ALL USING (auth.role() = 'service_role');
    END IF;

    -- Standings
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'standings' AND policyname = 'Public read standings') THEN
        CREATE POLICY "Public read standings" ON standings FOR SELECT USING (true);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'standings' AND policyname = 'Service write standings') THEN
        CREATE POLICY "Service write standings" ON standings FOR ALL USING (auth.role() = 'service_role');
    END IF;

    -- Teams
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'teams' AND policyname = 'Public read teams') THEN
        CREATE POLICY "Public read teams" ON teams FOR SELECT USING (true);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'teams' AND policyname = 'Service write teams') THEN
        CREATE POLICY "Service write teams" ON teams FOR ALL USING (auth.role() = 'service_role');
    END IF;

    -- Region Leagues
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'region_leagues' AND policyname = 'Public read region_leagues') THEN
        CREATE POLICY "Public read region_leagues" ON region_leagues FOR SELECT USING (true);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'region_leagues' AND policyname = 'Service write region_leagues') THEN
        CREATE POLICY "Service write region_leagues" ON region_leagues FOR ALL USING (auth.role() = 'service_role');
    END IF;
END
$$;

-- Add columns if they don't exist (Patch Columns)
DO $$
BEGIN
    -- Predictions Table Updates
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'predictions' AND column_name = 'is_recommended') THEN
        ALTER TABLE predictions ADD COLUMN is_recommended BOOLEAN;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'predictions' AND column_name = 'recommendation_score') THEN
        ALTER TABLE predictions ADD COLUMN recommendation_score NUMERIC;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'predictions' AND column_name = 'odds') THEN
        ALTER TABLE predictions ADD COLUMN odds TEXT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'predictions' AND column_name = 'market_reliability_score') THEN
        ALTER TABLE predictions ADD COLUMN market_reliability_score TEXT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'predictions' AND column_name = 'home_crest_url') THEN
        ALTER TABLE predictions ADD COLUMN home_crest_url TEXT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'predictions' AND column_name = 'away_crest_url') THEN
        ALTER TABLE predictions ADD COLUMN away_crest_url TEXT;
    END IF;

    -- Schedules Table Updates
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'schedules' AND column_name = 'rl_id') THEN
        ALTER TABLE schedules ADD COLUMN rl_id TEXT;
    END IF;
END $$;
