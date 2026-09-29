# 🗂️ Installer le suivi dans ta base existante `gestion-menus`

**Durée : 6 minutes.** Aucun paiement, aucun projet supplémentaire, **aucune de tes tables n'est
touchée**. Ce document remplace l'« Étape 1 » du guide général.

---

## ✅ Vérification faite : aucune collision

| Tes 8 tables existantes | Nos 7 tables à créer |
|---|---|
| `ingredients` | `sr_profiles` |
| `menu_ingredients` | `sr_daily_logs` |
| `menu_recipe` | `sr_measurements` |
| `menu` | `sr_workouts` |
| `planned_meals` | `sr_workout_sets` |
| `recipe_ingredient` | `sr_protein_entries` |
| `recipes` | `sr_shopping_state` |
| `recurring_items` | |

**Aucun nom en commun.** Nos tables sont toutes préfixées `sr_` (« suivi recomposition »).
Deux mondes séparés dans la même base : ton gestionnaire de menus continue de fonctionner
exactement comme avant.

---

## Étape 1 — Contrôle avant travaux (30 secondes)

Dans ton projet `gestion-menus` : **SQL Editor** → **New query** → colle ceci → **Run** :

```sql
select table_name
from information_schema.tables
where table_schema = 'public' and table_name like 'sr_%';
```

**Résultat attendu : aucune ligne** (« Success. No rows returned »).
Si des lignes apparaissent, c'est que le schéma a déjà été installé — tu peux sauter l'étape 2.

---

## Étape 2 — Créer nos 7 tables (1 minute)

1. **SQL Editor** → **New query**.
2. Ouvre le fichier **`schema.sql`** (dans le dossier décompressé du ZIP), **copie tout**,
   **colle** dans la zone de texte.
3. **Run**.

**Résultat attendu : « Success. No rows returned »** ✅

> Ce script crée 7 tables préfixées `sr_`, leurs index (eux aussi en `sr_`), et active la sécurité
> **RLS** sur ces 7 tables uniquement, avec 4 politiques par table. Tes 8 tables existantes ne sont
> ni lues, ni modifiées, ni verrouillées.

### Contrôle immédiat (facultatif mais rassurant)

```sql
select tablename, rowsecurity
from pg_tables
where schemaname = 'public' and tablename like 'sr_%'
order by tablename;
```

**Résultat attendu : 7 lignes, avec `rowsecurity = true` partout.**
*(`rowsecurity = true` = la sécurité est bien active : personne d'autre que toi ne peut lire tes données.)*

---

## Étape 3 — Ton compte de connexion (1 minute)

Menu de gauche → **Authentication** → **Users**.

**Deux cas :**

- **Tu as déjà un utilisateur pour `gestion-menus` qui te convient** → **réutilise-le tel quel**.
  C'est même pratique : un seul identifiant pour tes deux applications.
  Passe directement à l'étape 4.
- **Tu veux un compte dédié au suivi** → **Add user** → **Create new user** → renseigne ton email
  et un mot de passe, et **coche « Auto Confirm User »**. Clique **Create user**.

> ⚠️ **Ne modifie pas le réglage « Confirm email »** dans *Authentication → Sign In / Providers →
> Email* : ce réglage est **global au projet** et sert aussi à ton application `gestion-menus`.
> Si ton gestionnaire de menus fonctionne aujourd'hui, laisse-le exactement comme il est.
> C'est pour ça qu'on utilise « Auto Confirm User » à la création de l'utilisateur : ça contourne
> proprement le problème, uniquement pour ton compte.

---

## Étape 4 — Récupérer les 2 clés (30 secondes)

**Project Settings** (la roue dentée ⚙ en bas du menu de gauche) → **API** :

- **Project URL** → `https://xxxxx.supabase.co`
- **anon public** (ou *publishable key*) → la longue chaîne `eyJ...`

> ℹ️ **Ce sont exactement les mêmes clés que celles utilisées par `gestion-menus`. C'est normal et
> sans danger.** La clé « anon » identifie le projet, pas l'application. La séparation entre tes deux
> applications se fait à deux niveaux : **par table** (`sr_*` vs `*`) et **par ligne**
> (`user_id = auth.uid()` grâce aux politiques RLS). Une application ne peut donc pas voir les
> données de l'autre.

---

## Étape 5 — Streamlit (identique au guide général)

Suis l'**Étape 3 du guide** (`GUIDE_DEMARRAGE.md`) : créer le dépôt GitHub, déployer sur
share.streamlit.io, coller les deux valeurs dans **Advanced settings → Secrets** :

```toml
[supabase]
url = "https://xxxxx.supabase.co"
anon_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

---

## Étape 6 — Le test de bout en bout (2 minutes) 🔬

C'est **la** vérification qui prouve que tout fonctionne. Fais-la avant d'installer l'APK.

1. Dans l'application, **barre latérale** : tu dois lire **« Supabase (synchronisé) »**.
   *(Si tu lis « Local (SQLite) », les Secrets sont mal saisis → Settings → Secrets → Save → Reboot.)*
2. Page **⚖️ Pesée** → saisis ton poids du jour → **Enregistrer**.
3. Retourne dans **Supabase → Table Editor** → ouvre la table **`sr_daily_logs`**.
4. **Ta pesée doit apparaître dans la liste.** ✅
5. Vérifie au passage que tes tables `recipes`, `planned_meals`, etc. ont toujours leurs données.

Puis le test inverse : dans Supabase → **Table Editor** → `sr_daily_logs` → supprime une ligne →
recharge l'application (bouton ⟳) → la donnée a disparu. **Tes deux applications sont bien branchées
sur la même base, sans se mélanger.**

---

## Étape 7 — L'APK (identique au guide général)

Suis l'**Étape 4 du guide** : installer `SuiviRecomposition-1.0.apk` sur ton téléphone et coller
l'adresse `.streamlit.app` au premier lancement.

---

## 🎁 Trois avantages que tu ne soupçonnais peut-être pas

1. **Ton projet ne se mettra jamais en pause.** Le plan gratuit met en veille les projets après
   7 jours *sans aucun appel API*. Comme `gestion-menus` tourne régulièrement, ton suivi reste
   toujours réveillé : ton application s'ouvrira instantanément, sans les 30 secondes de « wake up ».
2. **Un seul point de sauvegarde.** Toutes tes données (menus *et* suivi) sont dans le même projet :
   une seule sauvegarde à faire, un seul endroit à consulter.
3. **Zéro coût.** Tes 7 tables pèsent moins d'1 Mo sur les 500 Mo offerts. Tu es à environ
   0,2 % du quota.

---

## 🧯 En cas de besoin : tout annuler proprement

Si un jour tu veux retirer complètement le suivi de ce projet, une seule requête suffit
(elle ne touche rien d'autre) :

```sql
drop table if exists
  sr_shopping_state, sr_protein_entries, sr_workout_sets, sr_workouts,
  sr_measurements, sr_daily_logs, sr_profiles;
```

⚠️ Cela supprime **tes données de suivi** (poids, séances, mensurations). Pense à faire d'abord
**⚙ Réglages → Télécharger un ZIP de sauvegarde (CSV)** dans l'application.
Tes tables `recipes`, `menu`, `planned_meals`, etc. ne sont pas concernées.

---

## Récapitulatif

| # | Où | Action | Durée |
|---|---|---|---|
| 0 | — | ✅ Vérification de collision : **faite, aucune** | — |
| 1 | Supabase → SQL Editor | Contrôle : aucune table `sr_*` n'existe | 30 s |
| 2 | Supabase → SQL Editor | Coller `schema.sql` → **Run** | 1 min |
| 3 | Supabase → Authentication → Users | Réutiliser ton compte **ou** en créer un (Auto Confirm) | 1 min |
| 4 | Supabase → Settings → API | Copier **Project URL** + **anon key** | 30 s |
| 5 | Streamlit | Créer l'app + coller les Secrets | 5 min |
| 6 | App + Supabase | 🔬 Test de bout en bout (pesée visible dans `sr_daily_logs`) | 2 min |
| 7 | Téléphone | Installer l'APK + coller l'adresse | 5 min |
