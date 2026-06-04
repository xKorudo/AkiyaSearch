# Login + Favorites setup (Supabase)

Favorites already work **locally** (stored in your browser) with no setup.
To enable **accounts + cross-device sync**, do this once:

## 1. Create a Supabase project
1. Go to https://supabase.com → sign up → **New project** (free tier is fine).
2. Wait for it to provision (~2 min).

## 2. Get your keys
Project dashboard → **Project Settings → API**. Copy:
- **Project URL** (e.g. `https://abcd1234.supabase.co`)
- **anon public** key (a long `eyJ...` string — safe to put in frontend)

## 3. Paste them into the site
Open `index.html`, near the top find:
```js
const SUPABASE_URL = "";
const SUPABASE_ANON_KEY = "";
```
Fill both in, e.g.:
```js
const SUPABASE_URL = "https://abcd1234.supabase.co";
const SUPABASE_ANON_KEY = "eyJhbGciOi...";
```

## 4. Create the favorites table
Supabase dashboard → **SQL Editor** → New query → paste & run:

```sql
create table if not exists favorites (
  user_id    uuid references auth.users(id) on delete cascade,
  listing_id text not null,
  created_at timestamptz default now(),
  primary key (user_id, listing_id)
);

-- Row Level Security: each user can only see/edit their own favorites
alter table favorites enable row level security;

create policy "own favorites - select" on favorites
  for select using (auth.uid() = user_id);
create policy "own favorites - insert" on favorites
  for insert with check (auth.uid() = user_id);
create policy "own favorites - delete" on favorites
  for delete using (auth.uid() = user_id);
```

## 5. (Optional) Email confirmation
By default Supabase emails a confirmation link on sign-up. To skip it while testing:
**Authentication → Providers → Email → turn off "Confirm email"**.

## Done
Reload the site:
- **Sign in** button (top right) → create an account / log in.
- Click the **♡** on any listing to save it; **♥ count** in the header shows your saved list.
- Click the header **♡ count** button to view only your favorites.
- Favorites made while logged out (localStorage) are merged into your account on sign-in.

> Note: this is a static site, so the listing data itself is public. Login here
> powers per-user features (favorites now; subscriptions later). True paywalling
> of data would need a Cloudflare Pages Function added at that point.
