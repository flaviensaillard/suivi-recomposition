# 🚀 Guide de A à Z — de zéro à l'application sur ton téléphone

**Temps total : environ 30 minutes.** Aucune ligne de code à taper, aucune installation sur ton PC.
Tout se fait dans le navigateur, avec des copier-coller.

À la fin, tu auras :
- une application en ligne (ton suivi accessible depuis n'importe quel appareil) ;
- **une vraie icône sur ton téléphone** qui ouvre l'application en plein écran (fichier `SuiviRecomposition-1.0.apk`) ;
- tes données stockées dans Supabase, donc conservées même quand l'application se met en veille.

## Résumé ultra-court (si tu es pressé)

| # | Où | Ce que tu fais | Durée |
|---|---|---|---|
| 1 | Supabase | Créer **ou réutiliser** un projet, coller `schema.sql`, créer ton utilisateur, copier 2 clés | 10 min |
| 2 | GitHub | Créer un dépôt, glisser-déposer les fichiers du ZIP | 5 min |
| 3 | Streamlit | Déployer, coller les 2 clés dans « Secrets », obtenir l'adresse | 5 min |
| 4 | Téléphone | Installer l'APK, coller l'adresse dans l'application | 5 min |

> ⚠️ **L'ordre compte.** Fais Supabase **avant** Streamlit : sans les clés Supabase, l'application
> fonctionnerait en mode local et tes données seraient effacées à chaque mise en veille.

> 📂 **Ton cas particulier :** tu réutilises ton projet Supabase **`gestion-menus`** (tu as déjà
> 2 projets et tu ne veux pas payer). Dans ce cas, **remplace l'Étape 1 ci-dessous par le document
> dédié `SUPABASE_GESTION-MENUS.md`** — il fait la même chose, mais adapté à ta base existante
> (vérification de collision, test de bout en bout, procédure d'annulation). Les étapes 2, 3 et 4
> restent identiques.

---

# 📦 Avant de commencer : 2 fichiers à récupérer

Depuis cette conversation, télécharge :

1. **`SuiviRecomposition-1.0.apk`** → l'application pour ton téléphone (45 Ko).
2. **`suivi-recomposition-github.zip`** → le paquet à envoyer sur GitHub (contient l'application,
   le guide, et le projet Android).

📱 **Astuce :** ouvre cette conversation sur ton téléphone et télécharge l'APK directement dessus —
tu éviteras de le transférer depuis l'ordinateur.

---

# ÉTAPE 1 — Supabase (la base de données) · 10 min

### 1.1 Créer le projet

> ## 🟠 Tu as déjà 2 projets Supabase et tu ne veux pas payer ?
>
> Le plan gratuit autorise **2 projets actifs par organisation** — c'est une limite du compte,
> pas du projet. Tu as trois solutions, **toutes gratuites** :
>
> **✅ Option A — Créer une nouvelle organisation (recommandée, 2 minutes)**
> Sur le tableau de bord Supabase, clique sur le **nom de ton organisation** en haut à gauche →
> **New organization** → donne-lui un nom (ex. `Perso`) → choisis le plan **Free** → Create.
> Tu repars avec **2 nouveaux projets gratuits**, totalement séparés de tes autres projets.
> C'est la solution officielle, documentée par Supabase (« You can create another Free Plan
> organization »). Reviens ensuite au point 1 ci-dessous : tu créeras ton projet dans cette
> nouvelle organisation.
>
> **✅ Option B — Mettre en pause un projet dont tu ne te sers plus**
> Un projet **en pause ne compte plus** dans la limite des 2. Va dans ce projet →
> **Project Settings** → **General** → **Pause project** (tu pourras le réactiver plus tard,
> tes données sont conservées). Tu peux alors créer ton 3ᵉ projet gratuitement.
>
> **✅ Option C — Réutiliser un de tes projets existants, sans rien créer**
> 👉 **C'est ton cas** : tu utilises le projet **`gestion-menus`**.
> **Suis le document dédié `SUPABASE_GESTION-MENUS.md`** (6 minutes, 7 étapes détaillées,
> avec un test de bout en bout pour vérifier que tes deux applications cohabitent sans se mélanger).
>
> En résumé : aucune collision (nos 7 tables sont préfixées **`sr_`**, tes 8 tables n'y touchent pas),
> tu réutilises tes clés existantes, et tu ne modifies **pas** le réglage « Confirm email »
> puisque ton gestionnaire de menus en dépend.
>
> **Dans tous les cas :** la base ne pèse que quelques mégaoctets, très loin des 500 Mo offerts.

1. Va sur **supabase.com** → **Sign in** (connecte-toi).
2. Clique **New project**.
3. Remplis :
   - **Name** : `suivi-recomposition`
   - **Database Password** : clique sur **Generate a password**, puis **copie-le quelque part**
     (tu n'en auras probablement jamais besoin, mais ne le perds pas).
   - **Region** : `Europe (Paris)` ou `Europe (Frankfurt)` — le plus proche de chez toi.
   - **Plan** : **Free**.
4. Clique **Create new project** et attends 1 à 2 minutes (il affiche « Setting up project... »).

### 1.2 Créer les tables

5. Dans le menu de gauche, clique **SQL Editor** (icône `>_`).
6. Clique **New query**.
7. **Copie tout le contenu du fichier `schema.sql`** (il est dans le ZIP, dossier racine) et colle-le
   dans la zone de texte.
8. Clique le bouton **Run** (en haut à droite, ou `Ctrl+Entrée`).
9. Tu dois voir apparaître en bas : **« Success. No rows returned »**. ✅ C'est bon.

> Ce script crée 7 tables et active la sécurité « RLS » : seule ta connexion pourra lire tes données.

### 1.3 Créer ton compte de connexion

10. Menu de gauche → **Authentication** → onglet **Sign In / Providers** (ou **Providers**).
11. Dans la liste, clique **Email**.
12. **Désactive** l'option **Confirm email** (le bouton doit être gris). Enregistre si un bouton
    **Save** apparaît.
    *Pourquoi ? Sinon Supabase t'envoie un email de confirmation et tu ne pourras pas te connecter
    tant que tu ne l'as pas validé.*
13. Menu de gauche → **Authentication** → onglet **Users**.
14. Clique **Add user** → **Create new user**.
15. Renseigne :
    - **Email** : ton adresse email
    - **Password** : un mot de passe (note-le ! c'est celui que tu utiliseras dans l'application)
    - Si une case **Auto Confirm User** est proposée : **coche-la**.
16. Clique **Create user**.

### 1.4 Récupérer tes 2 clés

17. Clique sur la **roue dentée** (⚙ **Project Settings**) en bas du menu de gauche.
18. Clique **API** (ou **API Keys** selon la version).
19. Copie et garde de côté **deux valeurs** :
    - **Project URL** → ressemble à `https://abcdefgh.supabase.co`
    - **anon public** (parfois appelée **publishable key**) → longue chaîne commençant par `eyJ...`

> La clé « anon » est faite pour être utilisée dans une application : elle ne donne accès qu'à
> *tes* lignes, grâce à la sécurité RLS activée à l'étape 1.2. N'utilise jamais la clé
> « service_role » : elle, elle donnerait accès à tout.

✅ **Supabase est prêt.** Garde la fenêtre ouverte, tu vas copier ces 2 valeurs à l'étape 3.

---

# ÉTAPE 2 — GitHub (héberger le code) · 5 min

1. Va sur **github.com** → connecte-toi.
2. Clique le **+** en haut à droite → **New repository**.
3. Remplis :
   - **Repository name** : `suivi-recomposition`
   - **Description** (facultatif) : `Application de suivi — recomposition corporelle`
   - **Public** (le plus simple : l'application Streamlit se déploiera sans autorisation spéciale).
     Tu peux aussi choisir **Private**, Streamlit te demandera alors d'autoriser l'accès.
   - Ne coche **rien** d'autre (pas de README, pas de .gitignore).
4. Clique **Create repository**.
5. Sur la page qui s'affiche, clique le lien bleu **uploading an existing file**
   (au milieu de la page : *« …or upload an existing file »*).
6. **Décompresse le ZIP `suivi-recomposition-github.zip` sur ton ordinateur.**
7. **Sélectionne tout ce qu'il y a DANS le dossier décompressé** (fichiers **et** dossiers :
   `app.py`, `db.py`, `content.py`, `requirements.txt`, `schema.sql`, le dossier `android`, etc.)
   et **glisse-les** dans la grande zone de la page GitHub qui dit
   *« Drag files here to add them to your repository »*.
   ⚠️ Glisse le **contenu** du dossier, pas le dossier lui-même — pour que `app.py` se retrouve
   directement à la racine du dépôt.
8. Attends que tous les fichiers apparaissent dans la liste (quelques secondes).
9. En bas, clique le bouton vert **Commit changes**.

✅ Vérification : sur la page du dépôt, tu dois voir `app.py` tout en haut de la liste des fichiers.
Si tu vois un dossier `suivi-recomposition` contenant `app.py`, pas de panique : note simplement
que le chemin à saisir à l'étape 3 sera `suivi-recomposition/app.py`.

> Les dossiers qui commencent par un point (`.streamlit`, `.github`) peuvent ne pas s'afficher dans
> le Finder macOS (touche `Cmd + Maj + .` pour les voir) ni être sélectionnables d'un coup.
> **Ce n'est pas grave** : `.streamlit` ne sert qu'à la couleur de l'interface, et `.github`
> seulement au bonus de la fin de ce guide. L'application fonctionne sans eux.

---

# ÉTAPE 3 — Streamlit (mettre l'application en ligne) · 5 min

1. Va sur **share.streamlit.io** → **Continue with GitHub** (autorise l'accès si demandé).
2. Clique **Create app** (ou **New app**).
3. Choisis **Deploy a public app from GitHub**.
4. Remplis les 3 champs :
   - **Repository** : `ton-pseudo/suivi-recomposition`
   - **Branch** : `main`
   - **Main file path** : `app.py`
     *(ou `suivi-recomposition/app.py` si tes fichiers sont dans un sous-dossier — voir étape 2)*
5. Clique **Advanced settings...** et, dans la zone **Secrets**, colle exactement ceci
   en remplaçant par tes 2 valeurs de l'étape 1.4 :

```toml
[supabase]
url = "https://abcdefgh.supabase.co"
anon_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

> Respecte bien les guillemets, les espaces autour du `=` et les majuscules.
> **Ne mets pas** `[supabase]` sur la même ligne que `url`.

6. Clique **Deploy** et patiente 1 à 3 minutes (tu vois les logs défiler : `Installing dependencies`,
   puis `You can now view your Streamlit app`).
7. Ton application s'ouvre, avec une adresse de la forme :
   **`https://suivi-recomposition.streamlit.app`**
   *(tu peux la personnaliser : menu **⋮** en haut à droite de l'app → **Settings** → **App URL**)*

8. **Connecte-toi** dans l'application avec l'email et le mot de passe créés à l'étape 1.3.

### ✅ Vérification indispensable

Dans la **barre latérale** de l'application, tu dois lire :

> **Stockage actuel : Supabase (synchronisé)**

Si tu lis **« Local (SQLite) »**, alors les Secrets ne sont pas lus → retourne dans
**⋮ → Settings → Secrets** (ou `share.streamlit.io` → ton app → **⋮ → Settings → Secrets**),
corrige le contenu, et clique **Save** puis **Reboot** l'application.
**Ne saisis aucune donnée avant que ce soit corrigé**, sinon elles seront perdues à la mise en veille.

📱 **À ce stade, ton application fonctionne déjà** : tu peux l'ouvrir depuis ton téléphone dans
le navigateur. L'étape suivante te donne juste une vraie icône et le plein écran.

---

# ÉTAPE 4 — Installer l'APK sur ton téléphone · 5 min

> ℹ️ **Ce qu'est cet APK :** une application Android native qui affiche ton suivi en plein écran
> et mémorise son adresse. C'est la façon la plus propre d'avoir « ton application » sur ton
> téléphone sans passer par le Play Store. Elle a besoin d'internet (tes données sont dans le cloud).

### 4.1 Transférer le fichier

Le plus simple : **ouvre cette conversation sur ton téléphone** et télécharge
`SuiviRecomposition-1.0.apk` (il arrive dans ton dossier **Téléchargements**).

Autres options si tu préfères depuis l'ordinateur : envoie-toi le fichier par email (à toi-même),
via Google Drive, ou par WhatsApp (« Message à moi-même »).

### 4.2 Autoriser l'installation

1. Ouvre l'application **Fichiers** (ou **Mes fichiers** / **Téléchargements**) sur ton téléphone.
2. Appuie sur `SuiviRecomposition-1.0.apk`.
3. Android affiche un message du type *« Pour votre sécurité, votre téléphone n'est pas autorisé
   à installer d'applications inconnues provenant de cette source »*.
4. Appuie sur **Paramètres** (dans ce message) puis active **Autoriser à partir de cette source**
   (coche l'autorisation pour **Chrome** ou **Fichiers**, selon ce qui installe).
   *Sur certains téléphones le chemin est : Paramètres → Applications → Accès spéciaux →
   Installer des applications inconnues.*
5. Reviens en arrière, appuie de nouveau sur le fichier → **Installer**.
6. Si **Google Play Protect** affiche *« Application non vérifiée »* ou *« Bloquer l'installation ? »* :
   appuie sur **Plus de détails** → **Installer quand même**.
   Normal : cette application n'est pas publiée sur le Play Store, personne ne l'a « vérifiée »
   à part toi. C'est **ton** application, installée par toi.

### 4.3 Premier lancement

1. Ouvre l'application **Suivi** (icône bleu-vert avec un haltère) depuis ton écran d'accueil.
2. Elle affiche un écran de configuration : colle l'adresse obtenue à l'étape 3
   (`https://....streamlit.app`).
3. Appuie sur **Ouvrir mon application**.
4. L'application se charge. Connecte-toi avec ton email/mot de passe Supabase.

**Les boutons de l'application :**
- **⟳** (en haut à droite) : recharger la page.
- **⚙** : modifier l'adresse, vider le cache, ouvrir dans le navigateur.
- **Bouton retour du téléphone** : revient dans l'application au lieu de la fermer.

---

# ÉTAPE 5 — Les 6 vérifications finales

| # | À vérifier | Où |
|---|---|---|
| 1 | Le tableau de bord s'affiche avec les graphiques | page 🏠 |
| 2 | La barre latérale indique **Supabase (synchronisé)** | barre latérale |
| 3 | Tu arrives à te connecter avec ton email/mot de passe Supabase | écran de connexion |
| 4 | Tu saisis une pesée, tu recharges (bouton ⟳) : la donnée est toujours là | page ⚖️ |
| 5 | Tu ajoutes 3 protéines, le total se met à jour | page 🥗 |
| 6 | Ferme complètement l'application et rouvre-la : elle s'ouvre directement sur ton suivi | icône du téléphone |

Si les 6 sont validées : **tout est en place.** 🎉

---

# 🆘 Dépannage

### « Error running app » sur Streamlit au déploiement
- Le plus souvent : erreur dans les **Secrets**. Vérifie qu'ils sont exactement de la forme :
  ```
  [supabase]
  url = "https://..."
  anon_key = "eyJ..."
  ```
  (guillemets compris, `[supabase]` seul sur sa ligne, aucun espace avant `[`).
- Sinon : clique **Manage app** en bas à droite → onglet **Logs** → lis la dernière ligne rouge
  et envoie-la-moi.

### L'application affiche « Local (SQLite) » alors que j'ai tout saisi
- Les Secrets n'ont pas été enregistrés ou l'appli n'a pas redémarré.
  Va sur **share.streamlit.io** → clique ton application → **⋮** → **Settings** → **Secrets**,
  vérifie le contenu, **Save**, puis **Reboot**.

### « You have reached the maximum number of free projects »
- Voir l'encadré orange de l'**étape 1** : crée une nouvelle organisation (option A), mets un projet
  inutilisé en pause (option B), ou réutilise un projet existant avec les tables `sr_` (option C).

### « Invalid login credentials » à la connexion
- L'utilisateur n'existe pas, ou le mot de passe est différent.
  Retourne dans Supabase → **Authentication → Users** → vérifie l'email, ou clique **Reset password**.
- Si ton utilisateur n'est pas marqué comme confirmé : **Authentication → Users** → menu **⋯** de la
  ligne → **Confirm email**.

### Le premier chargement est très long (20-30 s) ou l'appli est « réveillée »
- Normal et gratuit : Streamlit met l'application en veille après quelques jours sans visite.
  Tape sur **⟳** dans la barre du haut, ça repart. Tes données ne sont pas concernées (elles sont
  dans Supabase).
- Astuce : ouvre l'application une fois par jour, le réveil se fait en arrière-plan.

### L'APK affiche « Impossible de charger l'application »
1. Vérifie ta connexion internet.
2. Appuie sur **Réessayer** (parfois l'appli était en veille).
3. Vérifie l'adresse avec **⚙** → *Modifier l'adresse*. Elle doit être exactement celle affichée
   par Streamlit (avec `https://` et sans `/` à la fin).

### Android refuse d'installer l'APK
- Autorise l'installation depuis la source (voir 4.2 étape 4).
- Si le message parle d'un **conflit de signature** : tu as déjà une version installée avec une autre
  clé → désinstalle l'ancienne application puis réinstalle.
- **Android 6 ou antérieur** : l'application nécessite Android 7 minimum.

### J'ai saisi des données puis tout a disparu
- Tu étais en mode local (SQLite) dans une application hébergée : le disque de Streamlit est
  temporaire. Configure Supabase (étape 1) + Secrets (étape 3) et reboot.

---

# 🎁 Bonus — reconstruire l'APK toi-même (facultatif)

Si tu veux modifier l'application (son nom, son icône, l'adresse par défaut), **tu n'as rien à
installer sur ton PC** : GitHub peut compiler l'APK à ta place.

1. Va sur la page de ton dépôt GitHub → onglet **Actions**.
2. À gauche, clique **Build APK** → bouton **Run workflow** → **Run workflow**.
3. Attends 2 à 4 minutes, recharge la page : un nouvel élément apparaît sous le nom du workflow.
4. Clique dessus → en bas, section **Artifacts** → télécharge **SuiviRecomposition-apk** (un `.zip`).
5. Décompresse-le : tu obtiens `app-debug.apk`, à installer comme à l'étape 4.

⚠️ Cet APK est signé avec une clé différente : **désinstalle l'application déjà installée** avant
d'installer celle-ci.

---

# 🔑 À conserver précieusement

| Fichier / valeur | Où | Pourquoi |
|---|---|---|
| `SuiviRecomposition-1.0.apk` | ton téléphone + une copie sur ton PC | réinstallation rapide |
| `android/keystore/suivi-release.jks` (mot de passe `suivi2026`) | hors du dépôt GitHub | **clé de signature** : indispensable pour publier une mise à jour de l'APK par-dessus l'ancienne |
| Email + mot de passe de l'application | Supabase → Authentication → Users | connexion à l'appli |
| `Project URL` + `anon key` | Supabase → Project Settings → API | déploiement / redéploiement |

**Et un réflexe :** page **⚙ Réglages** de l'application → bouton
**Télécharger un ZIP de sauvegarde (CSV)**, une fois par mois. Tes données t'appartiennent.

---

# 🧭 Et maintenant ?

Ton plan de coaching complet reste dans **`plan_coaching_recomposition.html`** (nutrition, séances
de 30 minutes, suivi, ajustements). L'application ne fait « que » le suivi — c'est le plan qui décide.

**Premiers gestes dans l'application, cette semaine :**
1. **⚙ Réglages** → renseigne ton poids de départ (85 kg) et ton objectif (77 kg).
2. **📏 Mensurations** → prends tes mesures de départ (tour de taille au nombril, cou, etc.)
   et note ton nombre de tractions.
3. **⚖️ Pesée** chaque matin, à jeun.
4. **💪 Séance** lundi et vendredi, chrono lancé.
5. **🥗 Protéines** à chaque repas, en un appui.

Bonne route. 💪
