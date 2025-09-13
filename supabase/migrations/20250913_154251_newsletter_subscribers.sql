-- Enable required extensions
create extension if not exists pgcrypto;

-- 1) Table
create table if not exists public.newsletter_subscribers (
  id uuid primary key default gen_random_uuid(),
  email text not null,
  created_at timestamptz not null default now()
);

-- 2) Unique, case-insensitive email
create unique index if not exists newsletter_subscribers_email_key
  on public.newsletter_subscribers (lower(email));

-- 3) RLS
alter table public.newsletter_subscribers enable row level security;

-- Allow anonymous inserts (server-side anon key) so the API route can upsert
drop policy if exists "anon can insert newsletter" on public.newsletter_subscribers;
create policy "anon can insert newsletter"
  on public.newsletter_subscribers
  for insert
  to anon
  with check (true);

-- (Optional) prevent reads for anon role
drop policy if exists "no select for anon" on public.newsletter_subscribers;
create policy "no select for anon"
  on public.newsletter_subscribers
  for select
  to anon
  using (false);
