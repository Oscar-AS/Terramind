-- Mémoire du bot Telegram (engine/app/memoire.py). À coller une fois dans Supabase : SQL Editor → Run.
-- Une ligne par conversation. `cle` = empreinte SHA-256 du numéro de conversation (jamais le numéro lui-même).
-- `etat` : langue, position du champ arrondie à ~1 km, culture, date de plantation, 3 derniers échanges.

create table if not exists public.memoire_bot (
  cle  text primary key,
  etat jsonb not null default '{}'::jsonb,
  maj  timestamptz not null default now()
);

-- Personne ne lit ni n'écrit avec la clé publique (anon) : aucune règle n'est créée.
-- Le moteur utilise la clé « service_role » (variable SUPABASE_KEY sur Render), qui passe outre.
alter table public.memoire_bot enable row level security;
