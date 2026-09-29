# 🚀 METTRE L'APPLICATION EN LIGNE SUR STREAMLIT

**6 étapes · 15 minutes · 2 choses à télécharger seulement** (le dossier de l'appli, et rien d'autre).

> ### 💡 La bonne nouvelle
> Avec Streamlit, **tu ne télécharges jamais l'application sur ton téléphone**.
> L'application vit sur Internet, à une adresse web. Ton téléphone l'ouvre comme un site.
> Quand je modifie quelque chose : tu remplaces le fichier sur GitHub, et **l'application se
> met à jour toute seule** — pas de nouveau téléchargement. 👍

---

## 🗺️ Vue d'ensemble

| Étape | Où | Ce que tu fais | Durée |
|---|---|---|---|
| **0** | Supabase | 2 petites préparations (tables du suivi + ton compte) | 3 min |
| **1** | GitHub | Tu mets les fichiers dans un nouveau dépôt | 5 min |
| **2** | Streamlit | Tu déploies : l'appli devient un site web | 3 min |
| **3** | Streamlit | Tu colles tes 2 clés Supabase | 2 min |
| **4** | Ton navigateur | Tu te connectes et tu vérifies | 2 min |
| **5** | — | Comment on fera les mises à jour | — |

---

## ÉTAPE 0 — Deux préparations dans Supabase (3 min)

### 0.1 Créer les 8 tables du suivi

1. Va sur **supabase.com** → ton projet **`gestion-menus`**
2. Menu de gauche → **SQL Editor** (`>_`)
3. Bouton **New query**
4. Ouvre le fichier **`schema.sql`** (il est dans le dossier de l'application) → **Ctrl+A**, **Ctrl+C**
5. Colle dans Supabase → **Run**
6. Tu dois voir **un tableau avec 8 lignes** → c'est bon ✅

> Ces tables sont toutes préfixées `sr_` : **elles ne touchent à aucune de tes tables**
> (`ingredients`, `recipes`, `planned_meals`…). Tu peux relancer ce script sans risque.

### 0.2 Créer ton compte de connexion

L'application te demandera un email et un mot de passe au démarrage (pour que **tes données de
suivi restent privées** : ta femme aura le sien).

1. Supabase → menu de gauche → **Authentication**
2. Onglet **Users** → bouton **Add user** → **Create new user**
3. Remplis :
   - **Email** : ton email
   - **Password** : un mot de passe de ton choix (8 caractères minimum)
   - ✅ **Coche « Auto Confirm User »**
4. **Create user**

> ⚠️ **Ne touche PAS** au réglage global « Confirm email » du projet : il sert à ton
> application de menus. La case « Auto Confirm User » suffit.

📝 **Note quelque part** l'email et le mot de passe : c'est avec ça que tu te connecteras.

---

## ÉTAPE 1 — GitHub : les fichiers (5 min)

### 1.1 Télécharger le dossier

Télécharge **`pour-github.zip`** (le fichier que je te donne), puis :

1. Clic droit dessus → **Extraire tout…** → **Extraire**
2. Tu obtiens un dossier **`pour-github`** avec 14 fichiers dedans (dont un sous-dossier `data`)

### 1.2 Créer un nouveau dépôt

> On crée un **nouveau** dépôt : **ton application de menus actuelle reste intacte et
> fonctionne comme avant.** On ne touche pas à `gestion-menus`.

1. Va sur **github.com** → connecte-toi
2. En haut à droite, le **+** → **New repository**
3. Remplis :
   - **Repository name** : `suivi-recomposition`
   - **Description** (facultatif) : `Suivi recomposition + menus`
   - Choisis **Public**
   - ⚠️ **Ne coche rien d'autre** (pas de README, pas de .gitignore)
4. **Create repository**

### 1.3 Envoyer les fichiers

1. Sur la page qui s'affiche, clique sur le lien bleu **« uploading an existing file »**
2. **Ouvre ton dossier `pour-github`**, fais **Ctrl+A** (tout sélectionner)
3. **Glisse-dépose** tout dans la zone grise de GitHub
4. Attends que la liste des fichiers apparaisse (14 fichiers)
5. En bas, dans « Commit changes », clique sur le bouton vert **Commit changes**

✅ **Vérifie** : ta page doit lister `app.py`, `menus.py`, `repas.py`, `editeurs.py`, `data`…

> ❌ Si tu vois « Yowza, that's a big file » : c'est que tu as envoyé le `.zip`.
> C'est un piège classique — GitHub ne sait pas ouvrir un zip. Envoie **les fichiers extraits**.

### 1.4 (facultatif) Le petit réglage de couleur

Si tu veux les couleurs que tu as vues dans l'aperçu :

1. Sur ton dépôt → **Add file** → **Create new file**
2. Dans le nom du fichier, tape exactement : **`.streamlit/config.toml`**
   *(le `/` crée le dossier automatiquement)*
3. Colle ceci :
```
[theme]
base = "light"
primaryColor = "#0d9488"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f4f7fa"
textColor = "#1c2530"

[browser]
gatherUsageStats = false

[client]
toolbarMode = "minimal"
```
4. **Commit changes**

---

## ÉTAPE 2 — Streamlit : le déploiement (3 min)

1. Va sur **share.streamlit.io**
2. Connecte-toi **avec GitHub** (bouton « Continue with GitHub »)
3. Clique **Create app** (en haut à droite) puis choisis **Deploy a public app from GitHub**
4. Remplis les 3 champs :
   - **Repository** : `flaviensaillard/suivi-recomposition`
   - **Branch** : `main`
   - **Main file path** : `app.py`
5. Clique **Advanced settings…** :
   - **Python version** : `3.12` (ou 3.11 si 3.12 n'est pas proposé)
   - **Secrets** : laisse vide pour l'instant (on le fait à l'étape 3)
6. Clique **Deploy**

⏳ Il installe les composants : compte **2 à 4 minutes**. Tu vois défiler des lignes — c'est normal.

**Ton application est en ligne !** 🎉 Tu as maintenant une adresse du genre
`https://suivi-recomposition.streamlit.app`

> À ce stade, elle s'ouvre en **mode local** (données de démonstration). C'est déjà utilisable
> pour cliquer partout. L'étape 3 la branche sur ta vraie base.

---

## ÉTAPE 3 — Brancher tes vraies données (2 min)

### 3.1 Récupérer tes 2 clés

1. Supabase → ton projet `gestion-menus`
2. **Deux chemins possibles** :
   - Le bouton vert **« Connect »** en haut à droite → onglet **App Frameworks**
   - ou : roue dentée **⚙ Settings** (en bas du menu de gauche) → **API Keys**
3. Copie :
   - la **Project URL** → ressemble à `https://abcdefgh.supabase.co`
   - la clé **publishable** → `sb_publishable_…`
     *(ou, si tu ne la trouves pas : onglet **Legacy API keys** → la clé **anon** `eyJhbGci…`)*

> ⛔ **N'utilise jamais** la clé `sb_secret_…` ou `service_role` : elle donne tous les droits.
> L'application la refusera de toute façon et te le dira.

### 3.2 Les coller dans Streamlit

1. Sur **share.streamlit.io** → clique sur ton application → menu **⋮** (trois points) → **Settings**
2. Onglet **Secrets**
3. Colle **exactement** ceci, en remplaçant les deux parties entre guillemets :

```toml
[supabase]
url = "https://abcdefgh.supabase.co"
anon_key = "sb_publishable_xxxxxxxxxxxx"
```

4. **Save**
5. L'application redémarre toute seule (30 secondes)

---

## ÉTAPE 4 — Vérifier (2 min)

1. Ouvre ton adresse `https://….streamlit.app`
2. **Connecte-toi** avec l'email et le mot de passe de l'étape 0.2
3. Vérifie dans l'ordre :

- [ ] **🍽️ Repas & menus** : mes recettes apparaissent, avec kcal et protéines
- [ ] **📅 Planifier** : ma semaine est là
- [ ] **🥕 Mes ingrédients** : ma liste d'ingrédients
- [ ] **🛒 Courses** : la liste par rayon, avec les bons arrondis
- [ ] **📄 Fiche PDF** : le bouton génère bien ma fiche
- [ ] **💪 Séance / ⚖️ Pesée** : je peux saisir (ce sont les tables `sr_`)

### ⚠️ Avant de juger la liste de courses

Si tu n'as pas encore lancé ces 2 scripts, fais-les maintenant (10 s chacun, sans risque) :

| Fichier | Ce qu'il apporte |
|---|---|
| `2d_noms_lisibles.sql` | Des noms courts : « Pâtes » au lieu de « Pâtes sèches, standard, crues » |
| `2e_poids_pieces.sql` | Efface les « poids à la pièce » fantômes (conserves, sauces) |

---

## ÉTAPE 5 — Et ensuite ? Les mises à jour

C'est là que Streamlit est génial :

| Quand je te donne une correction | Ce que tu fais |
|---|---|
| 1 fichier modifié (ex. `menus.py`) | GitHub → ton dépôt → clic sur le fichier → 🗑️ **Supprimer** → puis **Add file → Upload files** → glisser le nouveau → **Commit** |
| Plusieurs fichiers | GitHub → **Add file → Upload files** → glisser les fichiers (ils remplacent ceux du même nom) → **Commit** |

**En 30 secondes, ton application en ligne est à jour — rien à réinstaller, rien à
retélécharger.** C'est aussi ce qui se passera quand on touchera à l'APK : l'APK n'affiche
qu'une fenêtre vers ce site, donc il n'a besoin d'être installé **qu'une seule fois**.

---

## 🆘 Si quelque chose ne va pas

| Message | Solution |
|---|---|
| **« ModuleNotFoundError: No module named 'menus' »** | Un fichier manque sur GitHub. Vérifie que `menus.py`, `repas.py`, `editeurs.py`, `pdf_menus.py` sont bien dans le dépôt (à la racine, pas dans un sous-dossier) |
| **« url doit ressembler à https://xxxxx.supabase.co »** | Tu as collé l'adresse du tableau de bord. Reprends la **Project URL** dans Connect ou Settings → API Keys |
| **« Invalid API key »** | Tu as pris la clé secrète. Prends celle qui commence par `sb_publishable_` ou `eyJ` |
| **La page de connexion refuse** | Le compte n'existe pas ou n'est pas confirmé. Refais l'étape 0.2 **avec la case « Auto Confirm User » cochée** |
| **« relation sr_profiles does not exist »** | Le script `schema.sql` n'a pas été lancé. Refais l'étape 0.1 |
| **L'appli affiche le bandeau « Mode aperçu »** | Les clés ne sont pas encore enregistrées (étape 3), ou l'appli n'a pas redémarré : Settings → Secrets → **Save** puis **Reboot app** |
| **Le déploiement échoue avec « Error installing requirements »** | Settings → **Reboot app**. Si ça persiste, dis-le moi : je te donne un `requirements.txt` plus souple |

**Dans tous les cas** : copie-colle moi le message exact (ou une capture d'écran) — et regarde
les **logs** : sur share.streamlit.io, en bas à droite de l'appli, il y a **« Manage app » →
Logs**, qui dit toujours ce qui ne va pas.

---

## 📋 Récapitulatif — la liste à cocher

- [ ] **0.1** `schema.sql` lancé dans Supabase → tableau de 8 lignes
- [ ] **0.2** Compte créé (Authentication → Users → Add user + Auto Confirm)
- [ ] **1.1** `pour-github.zip` téléchargé **et extrait**
- [ ] **1.2** Dépôt GitHub `suivi-recomposition` créé (public)
- [ ] **1.3** Les **14 fichiers** envoyés sur GitHub
- [ ] **2** Application déployée sur share.streamlit.io (`app.py`, Python 3.12)
- [ ] **3** Secrets collés (Project URL + clé publishable) → Save
- [ ] **4** Connexion et vérification des pages
- [ ] **en option** `2d_noms_lisibles.sql` et `2e_poids_pieces.sql` lancés
