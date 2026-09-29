-- ============================================================================
--  SCHÉMA SUPABASE — Suivi recomposition corporelle
--  À coller dans Supabase → SQL Editor → New query → Run
--
--  ⚠️ IMPORTANT : toutes les tables sont préfixées « sr_ » (suivi recomposition).
--  Cela permet d'exécuter ce script dans un projet Supabase DÉJÀ UTILISÉ pour
--  autre chose, sans aucun risque de collision avec tes tables existantes.
--
--  Single-user app : chaque ligne appartient à auth.uid(), protégé par RLS
--  (Row Level Security) : un utilisateur ne peut lire que ses propres lignes.
-- ============================================================================

-- 1. PROFIL (une seule ligne par utilisateur : tes constantes et tes objectifs)
create table if not exists sr_profiles (
  user_id          uuid primary key references auth.users(id) on delete cascade,
  display_name     text,
  height_cm        numeric default 185,
  start_weight_kg  numeric default 85,
  target_weight_kg numeric default 77,
  target_protein_g integer default 140,
  tdee_kcal        integer default 2670,
  phase            text default 'Bloc 0 — remise à niveau',
  created_at       timestamptz default now()
);

-- 2. JOURNAL QUOTIDIEN (pesée du matin + habitudes)
create table if not exists sr_daily_logs (
  id           bigint generated always as identity primary key,
  user_id      uuid not null references auth.users(id) on delete cascade,
  log_date     date not null,
  weight_kg    numeric(5,2),
  body_fat_pct numeric(4,1),
  steps        integer,
  sleep_h      numeric(3,1),
  protein_g    integer,
  kcal         integer,
  activity     text,          -- Repos / Séance A / Séance B / Rugby / Marche / Musique / Autre
  energy       smallint,      -- 1 à 10
  notes        text,
  created_at   timestamptz default now(),
  unique (user_id, log_date)
);

-- 3. MENSURATIONS HEBDOMADAIRES (lundi matin)
create table if not exists sr_measurements (
  id         bigint generated always as identity primary key,
  user_id    uuid not null references auth.users(id) on delete cascade,
  meas_date  date not null,
  waist_cm   numeric(4,1),   -- tour de taille au nombril
  hips_cm    numeric(4,1),
  chest_cm   numeric(4,1),
  arm_cm     numeric(4,1),
  thigh_cm   numeric(4,1),
  neck_cm    numeric(4,1),   -- sert au calcul Marine (US Navy)
  photos     boolean default false,
  notes      text,
  unique (user_id, meas_date)
);

-- 4. SÉANCES (une ligne par séance)
create table if not exists sr_workouts (
  id           bigint generated always as identity primary key,
  user_id      uuid not null references auth.users(id) on delete cascade,
  session_date date not null,
  session      text not null check (session in ('A','B')),
  duration_min integer,
  rpe          smallint,
  notes        text,
  unique (user_id, session_date, session)
);

-- 5. SÉRIES (une ligne par exercice × série)
create table if not exists sr_workout_sets (
  id          bigint generated always as identity primary key,
  user_id     uuid not null references auth.users(id) on delete cascade,
  set_date    date not null,
  session     text not null check (session in ('A','B')),
  exercise    text not null,
  set_no      smallint not null,
  reps        smallint,
  load_kg     numeric(5,1),
  variant     text,          -- niveau N1..N5 utilisé
  rpe         smallint,
  unique (user_id, set_date, session, exercise, set_no)
);

-- 6. PROTÉINES DU JOUR (compteur rapide par aliment)
create table if not exists sr_protein_entries (
  id         bigint generated always as identity primary key,
  user_id    uuid not null references auth.users(id) on delete cascade,
  entry_date date not null,
  item       text not null,
  protein_g  integer not null,
  qty        numeric(4,1) default 1,
  created_at timestamptz default now()
);

-- 7. COURSES (cases à cocher de la liste hebdo)
create table if not exists sr_shopping_state (
  id        bigint generated always as identity primary key,
  user_id   uuid not null references auth.users(id) on delete cascade,
  item_key  text not null,
  week_of   date not null,
  checked   boolean default false,
  unique (user_id, item_key, week_of)
);

-- ============================================================================
--  ROW LEVEL SECURITY : chacun ne voit que ses propres données
-- ============================================================================
alter table sr_profiles         enable row level security;
alter table sr_daily_logs       enable row level security;
alter table sr_measurements     enable row level security;
alter table sr_workouts         enable row level security;
alter table sr_workout_sets     enable row level security;
alter table sr_protein_entries  enable row level security;
alter table sr_shopping_state   enable row level security;

do $$
declare t text;
begin
  foreach t in array array['sr_profiles','sr_daily_logs','sr_measurements','sr_workouts',
                            'sr_workout_sets','sr_protein_entries','sr_shopping_state']
  loop
    execute format('drop policy if exists "own_select" on %I;', t);
    execute format('drop policy if exists "own_insert" on %I;', t);
    execute format('drop policy if exists "own_update" on %I;', t);
    execute format('drop policy if exists "own_delete" on %I;', t);
    execute format('create policy "own_select" on %I for select using (auth.uid() = user_id);', t);
    execute format('create policy "own_insert" on %I for insert with check (auth.uid() = user_id);', t);
    execute format('create policy "own_update" on %I for update using (auth.uid() = user_id) with check (auth.uid() = user_id);', t);
    execute format('create policy "own_delete" on %I for delete using (auth.uid() = user_id);', t);
  end loop;
end $$;

-- ============================================================================
--  INDEX (rapidité des lectures par date)
-- ============================================================================
create index if not exists idx_sr_daily_user_date on sr_daily_logs (user_id, log_date desc);
create index if not exists idx_sr_meas_user_date  on sr_measurements (user_id, meas_date desc);
create index if not exists idx_sr_sets_user_date  on sr_workout_sets (user_id, set_date desc);
create index if not exists idx_sr_prot_user_date  on sr_protein_entries (user_id, entry_date desc);

-- ============================================================================
--  VÉRIFICATION (facultatif) : liste les tables créées
-- ============================================================================
-- select table_name from information_schema.tables
--  where table_schema = 'public' and table_name like 'sr_%' order by table_name;
