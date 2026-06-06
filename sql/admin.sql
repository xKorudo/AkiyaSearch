-- Admin moderation + user reports for Akiya Search.
-- Run once in the Supabase SQL editor. Then seed yourself as admin (bottom).

-- 1) ADMINS ------------------------------------------------------------------
create table if not exists admins (
  user_id  uuid primary key references auth.users(id) on delete cascade,
  added_at timestamptz default now()
);
alter table admins enable row level security;  -- only reached via is_admin()

create or replace function is_admin()
returns boolean
language sql security definer stable
set search_path = public
as $$
  select exists (select 1 from admins where user_id = auth.uid());
$$;
grant execute on function is_admin() to anon, authenticated;

-- 2) REPORTS (anyone may file; only admins read/update) -----------------------
create table if not exists reports (
  id          bigint generated always as identity primary key,
  listing_id  text not null,
  category    text not null check (category in ('sold','duplicate','broken_link','wrong_data','other')),
  note        text,
  status      text not null default 'open' check (status in ('open','resolved','dismissed')),
  reporter    uuid,
  created_at  timestamptz default now()
);
alter table reports enable row level security;
grant insert on reports to anon, authenticated;
grant select, update on reports to authenticated;

drop policy if exists "reports insert anyone" on reports;
create policy "reports insert anyone" on reports
  for insert to anon, authenticated with check (true);

drop policy if exists "reports admin read" on reports;
create policy "reports admin read" on reports
  for select to authenticated using (is_admin());

drop policy if exists "reports admin update" on reports;
create policy "reports admin update" on reports
  for update to authenticated using (is_admin()) with check (is_admin());

-- 3) LISTING OVERRIDES (moderation: hide / patch fields) ----------------------
-- Applied client-side over the scraped listings, so they survive every re-scrape.
create table if not exists listing_overrides (
  listing_id text primary key,
  hidden     boolean not null default false,
  patch      jsonb   not null default '{}'::jsonb,  -- e.g. {"price_jpy":0,"title_en":"…","sold":true}
  updated_by uuid,
  updated_at timestamptz default now()
);
alter table listing_overrides enable row level security;
grant select on listing_overrides to anon, authenticated;
grant insert, update, delete on listing_overrides to authenticated;

drop policy if exists "overrides read all" on listing_overrides;
create policy "overrides read all" on listing_overrides
  for select using (true);

drop policy if exists "overrides admin write" on listing_overrides;
create policy "overrides admin write" on listing_overrides
  for all to authenticated using (is_admin()) with check (is_admin());

-- 4) SEED YOURSELF AS ADMIN --------------------------------------------------
-- After signing in once, find your user id under Authentication → Users
-- (or run: select auth.uid();  while logged into the app), then:
--   insert into admins (user_id) values ('YOUR-USER-UUID');
