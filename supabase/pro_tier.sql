-- Pro subscription tier for Akiya Search
-- Run this in the Supabase SQL editor (supabase.com → SQL Editor)

CREATE TABLE IF NOT EXISTS public.user_profiles (
  user_id    UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  tier       TEXT NOT NULL DEFAULT 'free' CHECK (tier IN ('free', 'pro')),
  created_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;

-- Users can read their own profile (needed for the tier check in listing.html)
CREATE POLICY "users_read_own_profile" ON public.user_profiles
  FOR SELECT USING (auth.uid() = user_id);

-- Service role can manage all profiles (for admin upgrades)
CREATE POLICY "service_manage_profiles" ON public.user_profiles
  FOR ALL TO service_role USING (true) WITH CHECK (true);

GRANT SELECT ON public.user_profiles TO anon, authenticated;
GRANT ALL   ON public.user_profiles TO service_role;


-- ── How to upgrade a user to Pro ─────────────────────────────────────────────
-- Find the user's UUID in Supabase → Authentication → Users
-- Then run:
--
--   INSERT INTO public.user_profiles (user_id, tier)
--   VALUES ('<paste-uuid-here>', 'pro')
--   ON CONFLICT (user_id) DO UPDATE SET tier = 'pro';
--
-- To downgrade back to free:
--
--   UPDATE public.user_profiles SET tier = 'free' WHERE user_id = '<uuid>';
