# 🎯 Il te reste 4 étapes — la feuille de route

**Tu as fait l'étape 1 (la commande SQL) : c'était la plus technique. Bravo.** ✅

Il reste 4 étapes, dans cet ordre. Compte **20 minutes** au total.
Coche au fur et à mesure. Ne saute pas d'étape : chacune prépare la suivante.

---

## ☐ ÉTAPE 2 — Créer ton compte de connexion · 1 min

**Où :** Supabase → **Authentication** → onglet **Users**

**Deux cas :**

- **Tu as déjà un utilisateur** (celui qui te sert pour `gestion-menus`) et tu veux l'utiliser
  → ✅ **rien à faire**, passe à l'étape 3.
- **Tu veux un compte dédié** au suivi (recommandé si ton appli de menus est utilisée en famille)
  → clique **Add user** → **Create new user** → ton email + un mot de passe →
  **coche « Auto Confirm User »** → **Create user**. Note ce mot de passe.

> ⛔ **Ne touche pas** au réglage « Confirm email » dans *Authentication → Sign In / Providers* :
> il est **global au projet** et ton application `gestion-menus` en dépend. C'est pour ça qu'on
> utilise « Auto Confirm User » à la place.

---

## ☐ ÉTAPE 3 — Récupérer tes 2 clés · 2 min

**Le chemin le plus rapide :** en haut de la page de ton projet, clique le bouton vert **Connect**
→ onglet **App Frameworks**. Tu y trouves :

- `SUPABASE_URL` → `https://xxxxxxxx.supabase.co` ← **la Project URL**
- `SUPABASE_KEY` → `sb_publishable_...` ou `eyJ...` ← **la clé**

**Si tu ne vois pas ce bouton :** ⚙ *Project Settings* (en bas du menu de gauche) → **API Keys**
→ **« Project URL »** est tout en haut de la page.

**Si tu ne trouves toujours pas :** regarde la barre d'adresse de ton navigateur :

```
https://supabase.com/dashboard/project/abcdefghijklm
                                          └──────┬──────┘
Ta Project URL = https://abcdefghijklm.supabase.co
```

📋 **Copie ces deux valeurs dans un coin** (Bloc-notes, note du téléphone) : tu en as besoin à
l'étape 4, puis à l'étape 6 pour ton autre application.

> ⚠️ Prends la clé **`sb_publishable_...`** ou l'ancienne **`anon` (`eyJ...`)**.
> **Jamais** celle qui commence par `sb_secret_` ni `service_role`.

---

## ☐ ÉTAPE 4 — Mettre l'application en ligne · 8 min

### 4a. GitHub (3 min)

1. github.com → **+** (en haut à droite) → **New repository**
2. Nom : `suivi-recomposition` · **Public** (le plus simple) · ne coche **rien** d'autre
3. **Create repository**
4. Sur la page suivante, clique le lien **uploading an existing file**
5. **Décompresse `suivi-recomposition-github.zip`** sur ton ordinateur
6. Sélectionne **tout ce qu'il y a DANS le dossier décompressé** (fichiers *et* dossiers :
   `app.py`, `db.py`, `integration.py`, `requirements.txt`, `schema.sql`, `android`…) et
   **glisse-les** dans la zone « Drag files here… »
   ⚠️ Glisse le **contenu**, pas le dossier lui-même
7. En bas → bouton vert **Commit changes**

### 4b. Streamlit (5 min)

1. share.streamlit.io → **Create app** → *Deploy a public app from GitHub*
2. **Repository** : `ton-pseudo/suivi-recomposition` · **Branch** : `main` ·
   **Main file path** : `app.py`
3. **Advanced settings…** → zone **Secrets** → colle exactement ceci avec tes valeurs de l'étape 3 :

```toml
[supabase]
url = "https://xxxxxxxx.supabase.co"
anon_key = "sb_publishable_xxxxxxxxxxxx"

[apps]
menus_url = "https://gestion-menus.streamlit.app"
```

4. **Deploy** · attends 1 à 3 minutes · ton adresse s'affiche :
   `https://suivi-recomposition.streamlit.app`
5. Connecte-toi dans l'application avec ton compte de l'étape 2

> 🔎 **VÉRIFICATION OBLIGATOIRE — ne saute pas ça.**
> Dans la **barre latérale** de l'application, tu dois lire :
> **« Stockage actuel : Supabase (synchronisé) »**
>
> Si tu lis **« Local (SQLite) »** : les Secrets sont mal saisis.
> → share.streamlit.io → ton appli → **⋮ → Settings → Secrets**, corrige, **Save**, **Reboot**.
>
> ⚠️ **Ne saisis aucune donnée avant que ce soit corrigé** : en mode local, elles seraient perdues.

---

## ☐ ÉTAPE 5 — Le test qui prouve que tout marche · 2 min

1. **⚖️ Pesée** → saisis ton poids du matin → **Enregistrer**
2. **🥗 Protéines** → ajoute 2 aliments (les boutons « 3 œufs durs », « Shaker whey »…)
3. **🍽️ Cuisine & menus** → vérifie que tes repas de la semaine remontent de `planned_meals`
4. Retourne dans **Supabase → Table Editor** → ouvre **`sr_daily_logs`**

👉 **Ta pesée doit apparaître dans la table.** C'est la preuve que ton application écrit bien
dans ta base. Et jette un œil à `recipes` : **tes données sont toujours là.**

---

## ☐ ÉTAPE 6 — Ton application sur le téléphone · 5 min

1. **Ouvre cette conversation sur ton téléphone** et télécharge **`SuiviRecomposition-1.1.apk`**
2. Appuie dessus → **Paramètres** dans le message de sécurité → **Autoriser depuis cette source**
3. **Installer** → si Play Protect râle : **Plus de détails** → **Installer quand même**
4. Ouvre l'appli **« Mes apps »** → renseigne **les deux adresses** :
   - **Suivi** : `https://suivi-recomposition.streamlit.app`
   - **Menus** : l'adresse de ton `gestion-menus`
5. **Enregistrer et ouvrir** → teste le bouton **⇄** en haut à droite

> ✅ Elle est signée avec la même clé que la version 1.0 : **installe-la par-dessus sans
> désinstaller**.

---

## 📊 Récapitulatif

| # | Étape | État |
|---|---|---|
| 1 | Commande SQL dans Supabase | ✅ **fait** |
| 2 | Compte de connexion | ☐ 1 min |
| 3 | Les 2 clés | ☐ 2 min |
| 4 | GitHub + Streamlit | ☐ 8 min |
| 5 | Test de bout en bout | ☐ 2 min |
| 6 | APK sur le téléphone | ☐ 5 min |

---

## 🆘 En cas de pépin

**Règle n°1 : copie-moi le message d'erreur exact** (ou une capture d'écran). Je débloque ça en
une réponse. Les cas les plus fréquents :

| Message | Cause | Solution |
|---|---|---|
| « Error running app » sur Streamlit | Secrets mal formatés | Vérifie `[supabase]` seul sur sa ligne, guillemets compris |
| « Invalid login credentials » | Utilisateur non créé ou non confirmé | Authentication → Users → **⋯** → **Confirm email** |
| L'appli affiche « Local (SQLite) » | Secrets non lus | **⋮ → Settings → Secrets** → Save → **Reboot** |
| « Impossible de charger l'application » sur l'APK | Adresse erronée, ou appli en veille | Réessayer, puis vérifier l'adresse avec **⚙** |
| L'appli refuse de démarrer avec un message rouge | Mauvaise clé (secrète, ou mot de passe) | C'est la protection que j'ai ajoutée : reprends la clé `sb_publishable_...` |

---

## 💪 Et pendant que tu fais tout ça

Ton plan de coaching ne change pas d'un iota :

- **Samedi** → courses avec la liste (35-45 € pour ta part, 1 seule sortie)
- **Dimanche** → 45 min de batch cooking (lentilles, pois chiches, 15 œufs durs, poulet portionné)
- **Lundi 20 h 15** → **Séance A, 30 minutes**, chrono de repos lancé
- **Vendredi** → **Séance B**
- Et chaque matin : la pesée, à jeun, avant de boire.

Objectif 31 décembre : **77 kg, −4 cm de tour de taille, et la même force.**
On y va. 💪
