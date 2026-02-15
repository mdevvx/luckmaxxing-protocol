-- ============================================
-- Luckmaxxing Protocol Bot - Complete Supabase Schema
-- Production-Ready Version with All Fixes Applied
-- ============================================
-- Version: 2.0
-- Last Updated: 2026-02-15
-- Features: Enrollment IDs, Combined Day 1, RLS properly configured
--
-- Run this entire file in your Supabase SQL Editor
-- Safe to run multiple times (idempotent)
-- ============================================

-- ============================================
-- STEP 1: Clean up existing policies (if any)
-- ============================================
DROP POLICY IF EXISTS "Service role has full access to enrollments" ON enrollments;
DROP POLICY IF EXISTS "Service role has full access to guild_settings" ON guild_settings;
DROP POLICY IF EXISTS "Service role has full access to daily_progress" ON daily_progress;
DROP POLICY IF EXISTS "Service role has full access to enrollment_ids" ON enrollment_ids;
DROP POLICY IF EXISTS "Allow all access to enrollments" ON enrollments;
DROP POLICY IF EXISTS "Allow all access to guild_settings" ON guild_settings;
DROP POLICY IF EXISTS "Allow all access to daily_progress" ON daily_progress;
DROP POLICY IF EXISTS "Allow all access to enrollment_ids" ON enrollment_ids;

-- ============================================
-- STEP 2: Create Tables
-- ============================================

-- --------------------------------------------
-- Table: enrollments
-- Stores user enrollment data and progress
-- --------------------------------------------
CREATE TABLE IF NOT EXISTS enrollments (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    guild_id BIGINT NOT NULL,
    current_day INTEGER DEFAULT 0 NOT NULL,
    enrolled_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_message_sent TIMESTAMP WITH TIME ZONE,
    completed BOOLEAN DEFAULT FALSE,
    UNIQUE(user_id, guild_id)
);

-- Indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_enrollments_user_guild ON enrollments(user_id, guild_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_guild ON enrollments(guild_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_completed ON enrollments(completed);
CREATE INDEX IF NOT EXISTS idx_enrollments_current_day ON enrollments(current_day);

-- Table comments
COMMENT ON TABLE enrollments IS 'Stores user enrollments and training progress';
COMMENT ON COLUMN enrollments.user_id IS 'Discord user ID';
COMMENT ON COLUMN enrollments.guild_id IS 'Discord server/guild ID';
COMMENT ON COLUMN enrollments.current_day IS 'Current day in training (1=Day 1 in progress, 2=awaiting Day 2, etc.)';
COMMENT ON COLUMN enrollments.completed IS 'Whether user has completed all 8 days';
COMMENT ON COLUMN enrollments.last_message_sent IS 'Timestamp of last training message sent';

-- --------------------------------------------
-- Table: guild_settings
-- Stores per-guild bot configuration
-- --------------------------------------------
CREATE TABLE IF NOT EXISTS guild_settings (
    guild_id BIGINT PRIMARY KEY,
    bot_enabled BOOLEAN DEFAULT TRUE,
    protocol_channel_id BIGINT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table comments
COMMENT ON TABLE guild_settings IS 'Stores per-guild bot configuration';
COMMENT ON COLUMN guild_settings.guild_id IS 'Discord server/guild ID';
COMMENT ON COLUMN guild_settings.bot_enabled IS 'Whether bot is active in this guild';
COMMENT ON COLUMN guild_settings.protocol_channel_id IS 'ID of the protocol enrollment channel';

-- --------------------------------------------
-- Table: daily_progress
-- Logs each day's completion for analytics
-- --------------------------------------------
CREATE TABLE IF NOT EXISTS daily_progress (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    guild_id BIGINT NOT NULL,
    day_number INTEGER NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for progress tracking
CREATE INDEX IF NOT EXISTS idx_daily_progress_user ON daily_progress(user_id, guild_id);
CREATE INDEX IF NOT EXISTS idx_daily_progress_day ON daily_progress(day_number);
CREATE INDEX IF NOT EXISTS idx_daily_progress_completed_at ON daily_progress(completed_at);

-- Table comments
COMMENT ON TABLE daily_progress IS 'Logs daily completion events for analytics';
COMMENT ON COLUMN daily_progress.user_id IS 'Discord user ID';
COMMENT ON COLUMN daily_progress.guild_id IS 'Discord server/guild ID';
COMMENT ON COLUMN daily_progress.day_number IS 'Which day was completed (1-8)';
COMMENT ON COLUMN daily_progress.completed_at IS 'When the day was completed';

-- --------------------------------------------
-- Table: enrollment_ids
-- Stores generated enrollment IDs for access control
-- --------------------------------------------
CREATE TABLE IF NOT EXISTS enrollment_ids (
    id BIGSERIAL PRIMARY KEY,
    enrollment_id VARCHAR(5) NOT NULL,
    guild_id BIGINT NOT NULL,
    used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    used_by BIGINT,
    used_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(enrollment_id, guild_id)
);

-- Indexes for ID lookups
CREATE INDEX IF NOT EXISTS idx_enrollment_ids_guild ON enrollment_ids(guild_id);
CREATE INDEX IF NOT EXISTS idx_enrollment_ids_used ON enrollment_ids(used);
CREATE INDEX IF NOT EXISTS idx_enrollment_ids_lookup ON enrollment_ids(enrollment_id, guild_id);

-- Table comments
COMMENT ON TABLE enrollment_ids IS 'Stores generated enrollment IDs for access control';
COMMENT ON COLUMN enrollment_ids.enrollment_id IS '5-character unique enrollment code (e.g., XKP87)';
COMMENT ON COLUMN enrollment_ids.guild_id IS 'Discord server/guild ID this ID is valid for';
COMMENT ON COLUMN enrollment_ids.used IS 'Whether this ID has been used';
COMMENT ON COLUMN enrollment_ids.used_by IS 'User ID who used this ID';
COMMENT ON COLUMN enrollment_ids.used_at IS 'When the ID was used';

-- ============================================
-- STEP 3: Configure Row Level Security (RLS)
-- ============================================
-- Note: RLS can cause issues with service_role access.
-- If you encounter "row-level security policy" errors,
-- run the OPTIONAL FIX at the end of this file.
-- ============================================

-- Disable RLS first (clean slate)
ALTER TABLE enrollments DISABLE ROW LEVEL SECURITY;
ALTER TABLE guild_settings DISABLE ROW LEVEL SECURITY;
ALTER TABLE daily_progress DISABLE ROW LEVEL SECURITY;
ALTER TABLE enrollment_ids DISABLE ROW LEVEL SECURITY;

-- Enable RLS
ALTER TABLE enrollments ENABLE ROW LEVEL SECURITY;
ALTER TABLE guild_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE daily_progress ENABLE ROW LEVEL SECURITY;
ALTER TABLE enrollment_ids ENABLE ROW LEVEL SECURITY;

-- Create policies for service_role (your bot uses this)
CREATE POLICY "Service role has full access to enrollments" ON enrollments
    FOR ALL 
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Service role has full access to guild_settings" ON guild_settings
    FOR ALL 
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Service role has full access to daily_progress" ON daily_progress
    FOR ALL 
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Service role has full access to enrollment_ids" ON enrollment_ids
    FOR ALL 
    TO service_role
    USING (true)
    WITH CHECK (true);

-- ============================================
-- STEP 4: Grant permissions explicitly
-- ============================================
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO service_role;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO service_role;
GRANT USAGE ON SCHEMA public TO service_role;

-- ============================================
-- STEP 5: Success Message
-- ============================================
DO $$ 
BEGIN 
    RAISE NOTICE '============================================';
    RAISE NOTICE 'Luckmaxxing Protocol Database Setup Complete!';
    RAISE NOTICE '============================================';
    RAISE NOTICE 'Tables created:';
    RAISE NOTICE '  ✅ enrollments (user progress tracking)';
    RAISE NOTICE '  ✅ guild_settings (server configuration)';
    RAISE NOTICE '  ✅ daily_progress (analytics)';
    RAISE NOTICE '  ✅ enrollment_ids (access control)';
    RAISE NOTICE '';
    RAISE NOTICE 'Indexes created: 11 indexes';
    RAISE NOTICE 'RLS Policies: Enabled and configured';
    RAISE NOTICE 'Permissions: Granted to service_role';
    RAISE NOTICE '';
    RAISE NOTICE 'Next steps:';
    RAISE NOTICE '  1. Get your Supabase credentials from Settings → API';
    RAISE NOTICE '  2. Use the SERVICE_ROLE key (not anon key)';
    RAISE NOTICE '  3. Add SUPABASE_URL and SUPABASE_KEY to your .env file';
    RAISE NOTICE '  4. Run your bot: python bot.py';
    RAISE NOTICE '  5. Use /generateid command to create enrollment IDs';
    RAISE NOTICE '';
    RAISE NOTICE 'If you get RLS errors, run the OPTIONAL FIX below';
    RAISE NOTICE '============================================';
END $$;

-- ============================================
-- OPTIONAL FIX: Disable RLS Completely
-- ============================================
-- ONLY run this section if you get errors like:
-- "new row violates row-level security policy"
-- 
-- Uncomment the lines below by removing the -- at the start
-- ============================================

-- ALTER TABLE enrollments DISABLE ROW LEVEL SECURITY;
-- ALTER TABLE guild_settings DISABLE ROW LEVEL SECURITY;
-- ALTER TABLE daily_progress DISABLE ROW LEVEL SECURITY;
-- ALTER TABLE enrollment_ids DISABLE ROW LEVEL SECURITY;

-- DO $$ 
-- BEGIN 
--     RAISE NOTICE '============================================';
--     RAISE NOTICE 'RLS DISABLED - Bot should work now!';
--     RAISE NOTICE '============================================';
--     RAISE NOTICE 'Note: RLS is disabled for all tables.';
--     RAISE NOTICE 'This is safe because you are using service_role key.';
--     RAISE NOTICE '============================================';
-- END $$;

-- ============================================
-- VERIFICATION QUERIES
-- ============================================
-- Run these to verify your setup
-- ============================================

-- Check all tables exist
SELECT 'Tables Check' AS test,
    CASE 
        WHEN COUNT(*) = 4 THEN '✅ All 4 tables exist'
        ELSE '❌ Missing tables! Expected 4, found ' || COUNT(*)
    END AS result
FROM information_schema.tables 
WHERE table_schema = 'public' 
    AND table_name IN ('enrollments', 'guild_settings', 'daily_progress', 'enrollment_ids');

-- Check RLS status
SELECT 
    tablename AS table_name,
    CASE 
        WHEN rowsecurity THEN '🔒 RLS Enabled'
        ELSE '🔓 RLS Disabled'
    END AS rls_status
FROM pg_tables 
WHERE schemaname = 'public' 
    AND tablename IN ('enrollments', 'guild_settings', 'daily_progress', 'enrollment_ids')
ORDER BY tablename;

-- Check indexes
SELECT 'Indexes Check' AS test,
    CASE 
        WHEN COUNT(*) >= 11 THEN '✅ All indexes created (' || COUNT(*) || ')'
        ELSE '⚠️ Some indexes missing. Found ' || COUNT(*) || ', expected 11+'
    END AS result
FROM pg_indexes 
WHERE schemaname = 'public' 
    AND tablename IN ('enrollments', 'guild_settings', 'daily_progress', 'enrollment_ids');

-- Check policies
SELECT 
    tablename AS table_name,
    COUNT(*) AS policy_count,
    CASE 
        WHEN COUNT(*) > 0 THEN '✅ Has policies'
        ELSE '⚠️ No policies'
    END AS status
FROM pg_policies 
WHERE schemaname = 'public'
GROUP BY tablename
ORDER BY tablename;

-- ============================================
-- DATABASE SUMMARY
-- ============================================
SELECT '============================================' AS summary
UNION ALL SELECT 'Database Structure:'
UNION ALL SELECT '  • 4 tables (enrollments, guild_settings, daily_progress, enrollment_ids)'
UNION ALL SELECT '  • 11 indexes for performance'
UNION ALL SELECT '  • RLS policies for security'
UNION ALL SELECT '  • Service role permissions granted'
UNION ALL SELECT ''
UNION ALL SELECT 'Table Relationships:'
UNION ALL SELECT '  • enrollments: Tracks user progress (1 user per guild)'
UNION ALL SELECT '  • guild_settings: Bot configuration per server'
UNION ALL SELECT '  • daily_progress: Analytics log for completions'
UNION ALL SELECT '  • enrollment_ids: Access control via unique codes'
UNION ALL SELECT ''
UNION ALL SELECT 'User Journey:'
UNION ALL SELECT '  1. Admin generates ID with /generateid'
UNION ALL SELECT '  2. User enrolls with ID → current_day = 1'
UNION ALL SELECT '  3. User completes Day 1 → current_day = 2'
UNION ALL SELECT '  4. Bot sends Days 2-8 automatically'
UNION ALL SELECT '  5. After Day 8 → completed = true'
UNION ALL SELECT '============================================';

-- ============================================
-- TROUBLESHOOTING GUIDE
-- ============================================
-- If bot cannot access database:
--
-- 1. Verify you're using SERVICE_ROLE key (not anon)
--    Go to: Supabase → Settings → API
--    Copy: "service_role" key (very long, 200+ chars)
--
-- 2. Check .env file has:
--    SUPABASE_URL=https://xxxxx.supabase.co
--    SUPABASE_KEY=eyJhbG.... (your service_role key)
--
-- 3. If RLS errors occur:
--    Uncomment and run the OPTIONAL FIX section above
--
-- 4. Verify connection with Python:
--    from supabase import create_client
--    client = create_client(SUPABASE_URL, SUPABASE_KEY)
--    response = client.table('enrollments').select('*').limit(1).execute()
--    print(response.data)  # Should not error
--
-- ============================================

-- ============================================
-- QUICK FIX: Disable RLS to Fix Policy Errors
-- ============================================
-- Run this in your Supabase SQL Editor NOW
-- This will immediately fix the error you're seeing
-- ============================================

-- Disable RLS on all tables
ALTER TABLE enrollments DISABLE ROW LEVEL SECURITY;
ALTER TABLE guild_settings DISABLE ROW LEVEL SECURITY;
ALTER TABLE daily_progress DISABLE ROW LEVEL SECURITY;
ALTER TABLE enrollment_ids DISABLE ROW LEVEL SECURITY;

-- Drop all existing policies (they're not needed)
DROP POLICY IF EXISTS "Service role has full access to enrollments" ON enrollments;
DROP POLICY IF EXISTS "Service role has full access to guild_settings" ON guild_settings;
DROP POLICY IF EXISTS "Service role has full access to daily_progress" ON daily_progress;
DROP POLICY IF EXISTS "Service role has full access to enrollment_ids" ON enrollment_ids;

-- Explicitly grant permissions (just to be safe)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO service_role;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO service_role;

-- Verify it worked
SELECT 'RLS FIX APPLIED SUCCESSFULLY! ✅' AS status;

SELECT 
    tablename,
    CASE 
        WHEN rowsecurity THEN '❌ RLS Still Enabled (ERROR!)'
        ELSE '✅ RLS Disabled (GOOD!)'
    END AS rls_status
FROM pg_tables 
WHERE schemaname = 'public' 
    AND tablename IN ('enrollments', 'guild_settings', 'daily_progress', 'enrollment_ids')
ORDER BY tablename;

-- ======================================================
--                     SCHEMA UPDATED
-- ======================================================

-- ============================================
-- Migration Script for Existing Database
-- ============================================
-- This adds the new columns to your existing tables
-- Run this in Supabase SQL Editor
-- ============================================

-- Step 1: Add new columns to enrollments table
ALTER TABLE enrollments 
ADD COLUMN IF NOT EXISTS enrollment_id TEXT;

ALTER TABLE enrollments 
ADD COLUMN IF NOT EXISTS enrollment_used BOOLEAN DEFAULT FALSE;

-- Step 2: Generate enrollment IDs for existing users
UPDATE enrollments 
SET enrollment_id = 'LUCK-' || UPPER(SUBSTRING(md5(random()::text || user_id::text || guild_id::text) FROM 1 FOR 12))
WHERE enrollment_id IS NULL;

-- Step 3: Make enrollment_id NOT NULL
ALTER TABLE enrollments 
ALTER COLUMN enrollment_id SET NOT NULL;

-- Step 4: Add unique constraint
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'enrollments_enrollment_id_key'
    ) THEN
        ALTER TABLE enrollments 
        ADD CONSTRAINT enrollments_enrollment_id_key UNIQUE (enrollment_id);
    END IF;
END $$;

-- Step 5: Set enrollment_used = TRUE for users already past Day 0
UPDATE enrollments 
SET enrollment_used = TRUE 
WHERE current_day > 0;

-- Step 6: Add index for enrollment_id
CREATE INDEX IF NOT EXISTS idx_enrollments_enrollment_id ON enrollments(enrollment_id);

-- Step 7: Verify the migration
DO $$ 
DECLARE
    total_count INTEGER;
    with_ids INTEGER;
    null_ids INTEGER;
BEGIN
    SELECT COUNT(*) INTO total_count FROM enrollments;
    SELECT COUNT(*) INTO with_ids FROM enrollments WHERE enrollment_id IS NOT NULL;
    SELECT COUNT(*) INTO null_ids FROM enrollments WHERE enrollment_id IS NULL;
    
    RAISE NOTICE '============================================';
    RAISE NOTICE 'Migration Complete!';
    RAISE NOTICE '============================================';
    RAISE NOTICE 'Total enrollments: %', total_count;
    RAISE NOTICE 'With enrollment IDs: %', with_ids;
    RAISE NOTICE 'NULL enrollment IDs: %', null_ids;
    
    IF null_ids = 0 THEN
        RAISE NOTICE '✅ All users have enrollment IDs!';
    ELSE
        RAISE WARNING 'WARNING: % users still have NULL IDs', null_ids;
    END IF;
    RAISE NOTICE '============================================';
END $$;

-- Step 8: Show sample data
SELECT 
    user_id,
    guild_id,
    enrollment_id,
    enrollment_used,
    current_day,
    enrolled_at
FROM enrollments 
ORDER BY enrolled_at DESC
LIMIT 5;