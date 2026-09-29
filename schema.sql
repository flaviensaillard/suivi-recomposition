-- =============================================================================
--  SUIVI RECOMPOSITION — SCRIPT SQL COMPLET
--  Projet Supabase : gestion-menus
--
--  COMMENT FAIRE :
--   1. Supabase → menu de gauche → « SQL Editor »
--   2. Bouton « New query »
--   3. Tu copies TOUT ce fichier (Ctrl+A puis Ctrl+C) et tu le colles dans la zone
--   4. Tu cliques sur le bouton « Run » (ou Ctrl + Entrée)
--   5. Tu dois voir, tout en bas, un tableau de 8 lignes → c'est bon ✅
--
--  CE QUE FAIT CE SCRIPT :
--   • il crée les 8 tables de ton suivi, toutes préfixées « sr_ »
--   • il active la sécurité (RLS) : toi seul peux lire tes données
--   • il ne touche PAS à tes tables existantes (recipes, menu, planned_meals…)
--   • il ne supprime AUCUNE donnée
--   • tu peux le relancer autant de fois que tu veux : il ne fait rien la 2e fois
-- =============================================================================


-- -----------------------------------------------------------------------------
--  0. AU CAS OÙ : renomme des tables d'une toute première version (sans préfixe)
--     Si elles n'existent pas, cette partie ne fait rien du tout.
-- -----------------------------------------------------------------------------
do $$
declare
  paires text[][] := array[
    ['profiles',        'sr_profiles'],
    ['daily_logs',      'sr_daily_logs'],
    ['measurements',    'sr_measurements'],
    ['workouts',        'sr_workouts'],
    ['workout_sets',    'sr_workout_sets'],
    ['protein_entries', 'sr_protein_entries'],
    ['shopping_state',  'sr_shopping_state']
  ];
  i int;
begin
  for i in 1 .. array_length(paires, 1) loop
    if exists (select 1 from information_schema.tables
               where table_schema = 'public' and table_name = paires[i][1])
       and not exists (select 1 from information_schema.tables
                       where table_schema = 'public' and table_name = paires[i][2])
    then
      execute format('alter table public.%I rename to %I', paires[i][1], paires[i][2]);
      raise notice 'Table renommee : % -> %', paires[i][1], paires[i][2];
    end if;
  end loop;
end $$;


-- -----------------------------------------------------------------------------
--  1. PROFIL — tes constantes et tes objectifs
-- -----------------------------------------------------------------------------
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


-- -----------------------------------------------------------------------------
--  2. JOURNAL QUOTIDIEN — pesée du matin + habitudes
-- -----------------------------------------------------------------------------
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
  activity     text,
  energy       smallint,
  notes        text,
  created_at   timestamptz default now(),
  unique (user_id, log_date)
);


-- -----------------------------------------------------------------------------
--  3. MENSURATIONS — une fois par semaine (lundi matin)
-- -----------------------------------------------------------------------------
create table if not exists sr_measurements (
  id         bigint generated always as identity primary key,
  user_id    uuid not null references auth.users(id) on delete cascade,
  meas_date  date not null,
  waist_cm   numeric(4,1),
  hips_cm    numeric(4,1),
  chest_cm   numeric(4,1),
  arm_cm     numeric(4,1),
  thigh_cm   numeric(4,1),
  neck_cm    numeric(4,1),
  photos     boolean default false,
  notes      text,
  unique (user_id, meas_date)
);


-- -----------------------------------------------------------------------------
--  4. SÉANCES — une ligne par séance (A ou B)
-- -----------------------------------------------------------------------------
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


-- -----------------------------------------------------------------------------
--  5. SÉRIES — une ligne par exercice et par série
-- -----------------------------------------------------------------------------
create table if not exists sr_workout_sets (
  id          bigint generated always as identity primary key,
  user_id     uuid not null references auth.users(id) on delete cascade,
  set_date    date not null,
  session     text not null check (session in ('A','B')),
  exercise    text not null,
  set_no      smallint not null,
  reps        smallint,
  load_kg     numeric(5,1),
  variant     text,
  rpe         smallint,
  unique (user_id, set_date, session, exercise, set_no)
);


-- -----------------------------------------------------------------------------
--  6. PROTÉINES — le compteur du jour, aliment par aliment
-- -----------------------------------------------------------------------------
create table if not exists sr_protein_entries (
  id         bigint generated always as identity primary key,
  user_id    uuid not null references auth.users(id) on delete cascade,
  entry_date date not null,
  item       text not null,
  protein_g  integer not null,
  qty        numeric(4,1) default 1,
  created_at timestamptz default now()
);


-- -----------------------------------------------------------------------------
--  7. COURSES — les cases à cocher de la liste hebdomadaire
-- -----------------------------------------------------------------------------
create table if not exists sr_shopping_state (
  id        bigint generated always as identity primary key,
  user_id   uuid not null references auth.users(id) on delete cascade,
  item_key  text not null,
  week_of   date not null,
  checked   boolean default false,
  unique (user_id, item_key, week_of)
);


-- -----------------------------------------------------------------------------
--  8. PASSERELLE — la correspondance avec ton application de menus
-- -----------------------------------------------------------------------------
create table if not exists sr_integration_map (
  user_id    uuid primary key references auth.users(id) on delete cascade,
  mapping    jsonb not null default '{}'::jsonb,
  updated_at timestamptz default now()
);


-- =============================================================================
--  9. SÉCURITÉ (RLS) — toi seul peux lire et écrire tes lignes
-- =============================================================================
alter table sr_profiles         enable row level security;
alter table sr_daily_logs       enable row level security;
alter table sr_measurements     enable row level security;
alter table sr_workouts         enable row level security;
alter table sr_workout_sets     enable row level security;
alter table sr_protein_entries  enable row level security;
alter table sr_shopping_state   enable row level security;
alter table sr_integration_map  enable row level security;

do $$
declare t text;
begin
  foreach t in array array['sr_profiles','sr_daily_logs','sr_measurements','sr_workouts',
                           'sr_workout_sets','sr_protein_entries','sr_shopping_state',
                           'sr_integration_map']
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


-- =============================================================================
-- 10. ACCÉLÉRATEURS (index) — pour que l'application reste rapide
-- =============================================================================
create index if not exists idx_sr_daily_user_date on sr_daily_logs (user_id, log_date desc);
create index if not exists idx_sr_meas_user_date  on sr_measurements (user_id, meas_date desc);
create index if not exists idx_sr_sets_user_date  on sr_workout_sets (user_id, set_date desc);
create index if not exists idx_sr_prot_user_date  on sr_protein_entries (user_id, entry_date desc);


-- =============================================================================
-- 11. VÉRIFICATION — rien à faire, c'est automatique
--     TU DOIS VOIR 8 LIGNES S'AFFICHER EN BAS DE L'ÉCRAN ✅
-- =============================================================================
select
  t.tablename                                        as "Table créée",
  (select count(*) from information_schema.columns c
    where c.table_schema = 'public' and c.table_name = t.tablename) as "Colonnes",
  t.rowsecurity                                      as "Sécurité active"
from pg_tables t
where t.schemaname = 'public' and t.tablename like 'sr_%'
order by t.tablename;
