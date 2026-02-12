-- LeoBook Predictions Database Schema for Supabase
-- Run this in Supabase SQL Editor after creating your project

-- Create predictions table
CREATE TABLE IF NOT EXISTS predictions (
  id BIGSERIAL PRIMARY KEY,
  fixture_id TEXT NOT NULL UNIQUE,
  date DATE NOT NULL,
  match_time TEXT,
  region_league TEXT,
  home_team TEXT NOT NULL,
  away_team TEXT NOT NULL,
  home_team_id TEXT,
  away_team_id TEXT,
  prediction TEXT,
  confidence TEXT,
  reason TEXT,
  xg_home NUMERIC,
  xg_away NUMERIC,
  btts TEXT,
  over_2_5 TEXT,
  best_score TEXT,
  top_scores TEXT,
  home_form_n INTEGER,
  away_form_n INTEGER,
  home_tags TEXT,
  away_tags TEXT,
  h2h_tags TEXT,
  standings_tags TEXT,
  h2h_count INTEGER,
  form_count INTEGER,
  actual_score TEXT,
  outcome_correct BOOLEAN,
  generated_at TIMESTAMP,
  status TEXT,
  match_link TEXT,
  odds TEXT,
  market_reliability_score TEXT,
  home_crest_url TEXT,
  away_crest_url TEXT,
  is_recommended BOOLEAN,
  recommendation_score NUMERIC,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Create performance indexes
CREATE INDEX IF NOT EXISTS idx_predictions_date ON predictions(date);
CREATE INDEX IF NOT EXISTS idx_predictions_fixture_id ON predictions(fixture_id);
CREATE INDEX IF NOT EXISTS idx_predictions_league ON predictions(region_league);
CREATE INDEX IF NOT EXISTS idx_predictions_date_status ON predictions(date, status);

-- Enable Row Level Security (RLS)
ALTER TABLE predictions ENABLE ROW LEVEL SECURITY;

-- Idempotent Policy Creation for Predictions
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'predictions' AND policyname = 'Public read access'
    ) THEN
        CREATE POLICY "Public read access" ON predictions FOR SELECT USING (true);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'predictions' AND policyname = 'Service role write access'
    ) THEN
        CREATE POLICY "Service role write access" ON predictions FOR ALL USING (auth.role() = 'service_role');
    END IF;
END
$$;

-- Create schedules table
CREATE TABLE IF NOT EXISTS schedules (
  id BIGSERIAL PRIMARY KEY,
  fixture_id TEXT NOT NULL UNIQUE,
  date DATE,
  match_time TEXT,
  region_league TEXT,
  home_team TEXT,
  away_team TEXT,
  home_team_id TEXT,
  away_team_id TEXT,
  home_score TEXT,
  away_score TEXT,
  match_status TEXT,
  match_link TEXT,
  rl_id TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Create standings table
CREATE TABLE IF NOT EXISTS standings (
  id BIGSERIAL PRIMARY KEY,
  standings_key TEXT NOT NULL UNIQUE,
  region_league TEXT,
  position INTEGER,
  team_name TEXT,
  team_id TEXT,
  played INTEGER,
  wins INTEGER,
  draws INTEGER,
  losses INTEGER,
  goals_for INTEGER,
  goals_against INTEGER,
  goal_difference INTEGER,
  points INTEGER,
  last_updated TIMESTAMP,
  url TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Create teams table
CREATE TABLE IF NOT EXISTS teams (
  id BIGSERIAL PRIMARY KEY,
  team_id TEXT NOT NULL UNIQUE,
  team_name TEXT,
  rl_ids TEXT,
  team_crest TEXT,
  team_url TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Create region_leagues table
CREATE TABLE IF NOT EXISTS region_leagues (
  id BIGSERIAL PRIMARY KEY,
  rl_id TEXT NOT NULL UNIQUE,
  region TEXT,
  region_flag TEXT,
  league TEXT,
  league_crest TEXT,
  league_url TEXT,
  date_updated TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Enable RLS for new tables
ALTER TABLE schedules ENABLE ROW LEVEL SECURITY;
ALTER TABLE standings ENABLE ROW LEVEL SECURITY;
ALTER TABLE teams ENABLE ROW LEVEL SECURITY;
ALTER TABLE region_leagues ENABLE ROW LEVEL SECURITY;

-- Idempotent Policy Creation for New Tables
DO $$
BEGIN
    -- Schedules Policies
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'schedules' AND policyname = 'Public read schedules') THEN
        CREATE POLICY "Public read schedules" ON schedules FOR SELECT USING (true);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'schedules' AND policyname = 'Service write schedules') THEN
        CREATE POLICY "Service write schedules" ON schedules FOR ALL USING (auth.role() = 'service_role');
    END IF;

    -- Standings Policies
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'standings' AND policyname = 'Public read standings') THEN
        CREATE POLICY "Public read standings" ON standings FOR SELECT USING (true);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'standings' AND policyname = 'Service write standings') THEN
        CREATE POLICY "Service write standings" ON standings FOR ALL USING (auth.role() = 'service_role');
    END IF;

    -- Teams Policies
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'teams' AND policyname = 'Public read teams') THEN
        CREATE POLICY "Public read teams" ON teams FOR SELECT USING (true);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'teams' AND policyname = 'Service write teams') THEN
        CREATE POLICY "Service write teams" ON teams FOR ALL USING (auth.role() = 'service_role');
    END IF;

    -- Region Leagues Policies
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'region_leagues' AND policyname = 'Public read region_leagues') THEN
        CREATE POLICY "Public read region_leagues" ON region_leagues FOR SELECT USING (true);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'region_leagues' AND policyname = 'Service write region_leagues') THEN
        CREATE POLICY "Service write region_leagues" ON region_leagues FOR ALL USING (auth.role() = 'service_role');
    END IF;
END
$$;

-- Add columns if they don't exist (for existing tables patch)
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
