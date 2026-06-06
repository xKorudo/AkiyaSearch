-- Listing view counter for the "🔥 HOT" feature.
-- Run this once in the Supabase SQL editor.

create table if not exists listing_views (
  listing_id text primary key,
  views      bigint not null default 0,
  updated_at timestamptz not null default now()
);

alter table listing_views enable row level security;

-- Anyone (incl. anonymous visitors) may read view counts.
drop policy if exists "listing_views readable" on listing_views;
create policy "listing_views readable" on listing_views
  for select using (true);

-- Increments happen ONLY through this function (security definer), so visitors
-- can add +1 but cannot set arbitrary counts. No direct insert/update policy.
create or replace function bump_listing_view(lid text)
returns void
language sql
security definer
set search_path = public
as $$
  insert into listing_views (listing_id, views, updated_at)
  values (lid, 1, now())
  on conflict (listing_id)
  do update set views = listing_views.views + 1, updated_at = now();
$$;

grant execute on function bump_listing_view(text) to anon, authenticated;
