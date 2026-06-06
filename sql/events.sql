-- Anonymous, cookieless analytics events for Akiya Search.
-- Requires sql/admin.sql first (uses is_admin()). Run once in Supabase.

create table if not exists events (
  id         bigint generated always as identity primary key,
  session_id text,           -- random per-tab id (sessionStorage), NOT personal
  name       text not null,   -- 'page_view','listing_open','source_click','report_open','fav_add','search'
  page       text,            -- 'landing','search','map','discover','listing'
  ref        text,            -- referrer host (page_view only)
  meta       jsonb,           -- extra context (listing_id, prefecture, query…)
  created_at timestamptz not null default now()
);
create index if not exists events_created_idx on events (created_at desc);
create index if not exists events_session_idx on events (session_id);

alter table events enable row level security;
grant insert on events to anon, authenticated;
grant select on events to authenticated;

drop policy if exists "events insert anyone" on events;
create policy "events insert anyone" on events
  for insert to anon, authenticated with check (true);

drop policy if exists "events admin read" on events;
create policy "events admin read" on events
  for select to authenticated using (is_admin());
