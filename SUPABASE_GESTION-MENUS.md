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
| `recurring_items` | `sr_integration_map` ← la passerelle vers tes menus |

**Aucun nom en commun.** Nos tables sont toutes préfixées `sr_` (« suivi recomposition »).
Deux mondes séparés dans la même base : ton gestionnaire de menus continue de fonctionner
exactement comme avant.

---

## Étape 1 — La commande SQL, en une seule fois (1 minute)

**C'est la seule chose technique à faire. Tu copies, tu colles, tu cliques Run. Rien à comprendre.**

1. Ouvre ton projet **`gestion-menus`** sur supabase.com.
2. Menu de gauche → **SQL Editor** (l'icône `>_`).
3. Clique **New query**.
4. Ouvre le fichier **`schema.sql`**, fais **Ctrl+A** (tout sélectionner) puis **Ctrl+C** (copier).
   *Sur Mac : Cmd+A puis Cmd+C.*
5. Dans Supabase, clique dans la grande zone de texte et fais **Ctrl+V** (coller).
6. Clique le bouton **Run** (en haut à droite — ou **Ctrl + Entrée**).

### ✅ Ce que tu dois voir en bas de l'écran

Un tableau de **8 lignes** qui s'affiche :

```
    Table créée     | Colonnes | Sécurité active
--------------------+----------+-----------------
 sr_daily_logs      |       13 | t
 sr_integration_map |        3 | t
 sr_measurements    |       11 | t
 sr_profiles        |        9 | t
 sr_protein_entries |        7 | t
 sr_shopping_state  |        5 | t
 sr_workout_sets    |       10 | t
 sr_workouts        |        7 | t
(8 rows)
```

**8 lignes = c'est réussi ✅**

Les mentions `NOTICE` et les lignes en vert `CREATE TABLE` que tu vois au-dessus sont **normales** :
ce sont simplement les messages de progression.

### 🛡️ Ce que cette commande ne fait pas

- Elle **ne touche pas** à tes tables `recipes`, `menu`, `planned_meals`, `ingredients`, etc.
- Elle **ne supprime aucune donnée**.
- Tu peux la **relancer autant de fois que tu veux** : la deuxième fois, elle ne crée rien de plus
  (c'est vérifié, et ça n'affichera toujours que 8 lignes).

### 🔁 Tu avais déjà lancé une ancienne version de ce script ?

**Aucun problème, et rien de spécial à faire.** La commande est prévue pour ça :
- si une ancienne table existe sans le préfixe `sr_`, elle est **renommée** automatiquement
  (tes données de pesée sont conservées) ;
- si les bonnes tables existent déjà, elle ne fait rien dessus.

Dans tous les cas : **relance simplement la même commande** et vérifie que tu obtiens bien 8 lignes.

### 🆘 Si tu vois un message rouge (« ERROR »)

Ne touche à rien. Copie-moi le texte du message et je te corrige ça en une réponse.

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

## Étape 4 — Récupérer tes 2 clés (4 chemins possibles)

⚠️ **C'est ici que beaucoup se perdent : Supabase a renommé cette page plusieurs fois.**
Les tutoriels disent « Settings → API », aujourd'hui elle s'appelle « Settings → **API Keys** ».
Si tu ne la trouves pas, utilise le **chemin 3** : il fonctionne toujours.

**🥇 Chemin 1 — le bouton « Connect » (le plus rapide, 10 secondes)**

1. En haut de la page de ton projet, à droite du nom du projet, clique le bouton vert **Connect**.
2. Choisis l'onglet **App Frameworks**.
3. Tu vois deux lignes, chacune avec une icône « copier » à droite :
   - `SUPABASE_URL` → `https://xxxxxxxx.supabase.co` ← c'est ta **Project URL**
   - `SUPABASE_KEY` → `sb_publishable_...` ou `eyJ...` ← c'est ta clé

**🥈 Chemin 2 — Settings → API Keys**

1. Barre latérale **gauche**, tout en bas : clique la **roue dentée ⚙** (« Project Settings »).
2. Dans le sous-menu qui apparaît à gauche, clique **API Keys**.
   *(Ne cherche pas « API » : le libellé a changé.)*
3. **Tout en haut de cette page : « Project URL »** avec une icône pour la copier.
   C'est la valeur qui ressemble à `https://xxxxxxxx.supabase.co`.
4. Juste en dessous se trouvent les clés. **Deux formats possibles selon l'âge du projet :**
   - **nouveau** : `Publishable key` → commence par `sb_publishable_`
   - **ancien** : onglet ou section **Legacy API keys** → clé `anon` / `public` → commence par `eyJ`
   - ✅ **Les deux fonctionnent avec notre application.** Prends celle des deux que tu trouves.
   - ⛔ **Jamais** la clé `secret` (`sb_secret_...`) ni `service_role` : elle donne accès à tout.

**🥉 Chemin 3 — La barre d'adresse de ton navigateur (infaillible, aucun menu à trouver)**

1. Regarde l'adresse de la page Supabase où tu te trouves. Elle ressemble à :
   `https://supabase.com/dashboard/project/abcdefghijklm`
2. La partie après `/project/` — ici `abcdefghijklm` — est ta **référence de projet**.
3. Ta **Project URL** est cette référence encadrée ainsi :
   → `https://abcdefghijklm.supabase.co`
   *(Uniquement des `https://` + référence + `.supabase.co`, et jamais de `/` à la fin.)*

**🎁 Chemin 4 — Tu l'as déjà sous la main !**

L'application **`gestion-menus`** utilise déjà ces deux valeurs. Retrouve-les :
- si elle est sur Streamlit Cloud → *share.streamlit.io* → ton appli → **⋮ → Settings → Secrets** ;
- sinon, dans son code : le fichier `.streamlit/secrets.toml`, ou un fichier `.env` / `supabase_client.py`.
Tu y verras `url = "https://....supabase.co"` et la clé. **Réutilise exactement les mêmes.**

> ℹ️ **Pourquoi c'est sans danger de partager ces deux valeurs ?** La **Project URL** est publique
> (elle voyage à chaque visite, c'est juste une adresse). La clé **publishable** / **anon** ne donne
> accès **qu'à ce que les règles de sécurité RLS autorisent** — c'est-à-dire uniquement tes propres
> lignes, grâce au script `schema.sql`. C'est pour cette raison qu'il faut copier celle-là et
> **jamais** la clé `secret` / `service_role`.

> 🛡️ **Bonne nouvelle :** l'application **vérifie automatiquement** ces deux valeurs au démarrage.
> Si tu te trompes (adresse du tableau de bord collée par erreur, clé secrète, mot de passe de la
> base…), elle **refuse de démarrer et t'explique précisément quoi corriger**, plutôt que d'écrire
> des données au mauvais endroit.

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
