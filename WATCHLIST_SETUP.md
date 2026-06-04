# Watchlist + change-tracking setup (Supabase)

Run this SQL once in **Supabase → SQL Editor**. It creates the shared-watchlist
tables, the listing/price-history tables the scraper writes to, and the
Row-Level-Security rules so friends can share a watchlist safely.

```sql
-- ── LISTINGS (scraper source of truth for change tracking) ──────────────────
create table if not exists listings (
  id          text primary key,
  title       text,
  title_en    text,
  prefecture  text,
  city        text,
  price_jpy   bigint,
  status      text default 'active',     -- 'active' | 'sold'
  source      text,
  source_url  text,
  image_url   text,
  last_seen   timestamptz default now(),
  updated_at  timestamptz default now()
);

-- ── CHANGE EVENTS (feed the notifications) ──────────────────────────────────
create table if not exists listing_changes (
  id          bigint generated always as identity primary key,
  listing_id  text references listings(id) on delete cascade,
  type        text not null,             -- 'price_drop' | 'price_rise' | 'sold'
  old_price   bigint,
  new_price   bigint,
  created_at  timestamptz default now()
);
create index if not exists idx_changes_listing on listing_changes(listing_id);
create index if not exists idx_changes_date on listing_changes(created_at desc);

-- ── WATCHLISTS (shared with friends) ────────────────────────────────────────
create table if not exists watchlists (
  id         uuid primary key default gen_random_uuid(),
  owner_id   uuid not null references auth.users(id) on delete cascade,
  name       text not null default 'My Watchlist',
  created_at timestamptz default now()
);

create table if not exists watchlist_members (
  watchlist_id uuid references watchlists(id) on delete cascade,
  user_id      uuid references auth.users(id) on delete cascade,
  role         text default 'member',     -- 'owner' | 'member'
  added_at     timestamptz default now(),
  primary key (watchlist_id, user_id)
);

create table if not exists watchlist_items (
  watchlist_id uuid references watchlists(id) on delete cascade,
  listing_id   text not null,
  added_by     uuid references auth.users(id),
  added_at     timestamptz default now(),
  primary key (watchlist_id, listing_id)
);

create table if not exists watchlist_invites (
  id           uuid primary key default gen_random_uuid(),
  watchlist_id uuid references watchlists(id) on delete cascade,
  email        text not null,
  invited_by   uuid references auth.users(id),
  created_at   timestamptz default now()
);

-- per-user "last time notifications were viewed" (for the unread badge)
create table if not exists user_state (
  user_id              uuid primary key references auth.users(id) on delete cascade,
  notifications_seen_at timestamptz default now()
);

-- ── Membership helper (SECURITY DEFINER avoids RLS recursion) ───────────────
create or replace function is_watchlist_member(wl uuid)
returns boolean language sql security definer stable as $$
  select exists (
    select 1 from watchlist_members m
    where m.watchlist_id = wl and m.user_id = auth.uid()
  );
$$;

-- ── Row-Level Security ──────────────────────────────────────────────────────
alter table listings           enable row level security;
alter table listing_changes    enable row level security;
alter table watchlists         enable row level security;
alter table watchlist_members  enable row level security;
alter table watchlist_items    enable row level security;
alter table watchlist_invites  enable row level security;
alter table user_state         enable row level security;

-- Listings + changes are public read (browsing / notifications); only the
-- scraper (service_role) writes them, which bypasses RLS automatically.
create policy "listings public read"  on listings        for select using (true);
create policy "changes public read"   on listing_changes for select using (true);

-- Watchlists: members (or owner) can see; owner manages.
create policy "wl select"  on watchlists for select using (owner_id = auth.uid() or is_watchlist_member(id));
create policy "wl insert"  on watchlists for insert with check (owner_id = auth.uid());
create policy "wl update"  on watchlists for update using (owner_id = auth.uid());
create policy "wl delete"  on watchlists for delete using (owner_id = auth.uid());

-- Members: visible to fellow members; you may add yourself by accepting an
-- invite addressed to your email; owners/you can remove.
create policy "wm select" on watchlist_members for select using (is_watchlist_member(watchlist_id));
create policy "wm join via invite" on watchlist_members for insert with check (
  user_id = auth.uid() and exists (
    select 1 from watchlist_invites i
    where i.watchlist_id = watchlist_members.watchlist_id
      and i.email = (auth.jwt() ->> 'email')
  )
);
create policy "wm owner add" on watchlist_members for insert with check (
  exists (select 1 from watchlists w where w.id = watchlist_id and w.owner_id = auth.uid())
);
create policy "wm delete" on watchlist_members for delete using (
  user_id = auth.uid()
  or exists (select 1 from watchlists w where w.id = watchlist_id and w.owner_id = auth.uid())
);

-- Items: any member can view/add/remove houses.
create policy "wi select" on watchlist_items for select using (is_watchlist_member(watchlist_id));
create policy "wi insert" on watchlist_items for insert with check (is_watchlist_member(watchlist_id));
create policy "wi delete" on watchlist_items for delete using (is_watchlist_member(watchlist_id));

-- Invites: owner creates; the invited person (by email) can see + delete theirs.
create policy "inv select" on watchlist_invites for select using (
  invited_by = auth.uid() or email = (auth.jwt() ->> 'email')
);
create policy "inv insert" on watchlist_invites for insert with check (
  exists (select 1 from watchlists w where w.id = watchlist_id and w.owner_id = auth.uid())
);
create policy "inv delete" on watchlist_invites for delete using (
  email = (auth.jwt() ->> 'email')
  or exists (select 1 from watchlists w where w.id = watchlist_id and w.owner_id = auth.uid())
);

-- user_state: each user manages their own row.
create policy "us all" on user_state for all using (user_id = auth.uid()) with check (user_id = auth.uid());
```

## After running the SQL — give the scraper write access
The scraper records price/sold changes, which needs the **service_role** key
(server-side only — bypasses RLS). Add it as secrets:

- **GitHub** repo → Settings → Secrets → Actions → add:
  - `SUPABASE_URL` = `https://wmevbetyxqhtprdahxqh.supabase.co`
  - `SUPABASE_SERVICE_KEY` = (Supabase → Settings → API → **service_role** secret key)
- **Locally** (for manual runs), set them in your shell before `python run_pipeline.py`:
  ```powershell
  $env:SUPABASE_URL = "https://wmevbetyxqhtprdahxqh.supabase.co"
  $env:SUPABASE_SERVICE_KEY = "eyJ...service_role..."
  ```

> ⚠️ The **service_role** key is secret — never put it in `index.html` or commit it.
> It only lives in GitHub Secrets / your shell env.
