# 💪 Suivi Recomposition — application de suivi

> 🚀 **Tu débutes ? Ne lis pas ce fichier tout de suite : ouvre `GUIDE_DEMARRAGE.md`.**
> Il t'emmène pas à pas de zéro jusqu'à l'application installée sur ton téléphone.

Application mobile de suivi pour la perte de gras sans perte de muscle.
Stack : **Streamlit** (interface) + **Supabase** (base de données cloud, gratuite) + **GitHub** (code et hébergement).

Elle remplace le fichier Excel : pesée du matin, séances de 30 minutes, compteur de protéines,
mensurations, liste de courses. Les données sont synchronisées entre le PC et le téléphone.

---

## 1. Ce que fait l'application

| Page | Contenu |
|---|---|
| 🏠 **Tableau de bord** | Poids moyen 7 jours, tour de taille, masse grasse, protéines moyennes, séances de la semaine, progression vers 77 kg, **alertes automatiques du coach** |
| ⚖️ **Pesée & tendance** | Saisie du matin (poids, % gras balance, pas, sommeil, énergie), graphique poids + moyenne 7 jours |
| 💪 **Séance 30 min** | Séance A (lundi) / B (vendredi) en supersets, **chrono de repos**, saisie des séries, rappel de la dernière performance, détection « monte d'un niveau », suivi des tractions |
| 🍽️ **Cuisine & menus** | Passerelle avec ton application de menus : repas prévus détectés automatiquement, protéines calculées, un appui pour les compter. Détail : `JUMELAGE.md` |
| 🥗 **Protéines** | Objectif 140 g, ajout en un appui selon ce que tu viens de manger, moyenne 7/30 jours, historique |
| 📏 **Mensurations** | Tour de taille au nombril (la vraie mesure), calcul du % de gras par la formule Marine en plus de la balance |
| 🛒 **Courses** | Liste hebdomadaire cochable, par rayon, avec prix indicatifs et total |
| ⚙️ **Réglages** | Profil, objectifs, export CSV de toutes les données |

**Autonomie** : sans Supabase configuré, l'application fonctionne en **mode local** (fichier SQLite).
Elle est utilisable immédiatement, hors ligne, sans compte. Supabase sert à synchroniser PC ↔ mobile.

---

## 2. Démarrage local (5 minutes)

```bash
cd app
python -m venv .venv
source .venv/bin/activate        # Windows : .venv\Scripts\activate
pip install -r requirements.txt

python seed_demo.py              # optionnel : 6 semaines de données de démonstration
streamlit run app.py
```

L'application s'ouvre sur `http://localhost:8501`.

Pour repartir de zéro : supprime `data/suivi.db` (les données de démo disparaissent avec).

---

## 3. Mise en ligne (pour l'utiliser sur ton téléphone)

### Étape 1 — Base de données Supabase (gratuit)

1. Crée un compte sur [supabase.com](https://supabase.com) → **New project** (choisis une région européenne, ex. Paris).
   *Le plan gratuit limite à **2 projets actifs par organisation**. Si tu as déjà 2 projets :
   crée une **nouvelle organisation** (2 projets gratuits de plus), mets un projet inutilisé **en pause**
   (un projet en pause ne compte pas), ou **réutilise un projet existant** — le schéma est intégralement
   préfixé **`sr_`**, donc aucune collision possible. Procédure détaillée pour un projet déjà utilisé :
   voir **`SUPABASE_GESTION-MENUS.md`** à la racine du dépôt.*
2. Dans **SQL Editor → New query**, colle l'intégralité de `schema.sql` puis **Run**.
   Tu dois voir un tableau de **8 lignes** s'afficher : 8 tables `sr_*` avec la sécurité **RLS** active
   (chaque ligne n'est lisible que par son propriétaire). Le script est réexécutable sans risque.
3. **Authentication → Users → Add user** : crée ton compte (email + mot de passe). C'est avec ça que tu te connecteras.
4. **Authentication → Providers → Email** : décoche « Confirm email » si tu veux éviter l'email de validation.
5. **Project Settings → API** : note `Project URL` et la clé `anon public`.

### Étape 2 — GitHub

```bash
cd app
git init
git add .
git commit -m "Suivi recomposition : application Streamlit + Supabase"
git branch -M main
git remote add origin git@github.com:<ton-compte>/suivi-recomposition.git
git push -u origin main
```

> Le `.gitignore` empêche déjà l'envoi de `secrets.toml` et de `data/`. **Ne committe jamais ta clé.**
> Si tu veux que le dépôt reste privé : GitHub → Settings → General → Change visibility → Private.

### Étape 3 — Streamlit Community Cloud (gratuit)

1. [share.streamlit.io](https://share.streamlit.io) → **Create app** → choisis ton dépôt GitHub.
2. **Main file path** : `app.py` (ou `app/app.py` si tu as poussé le dossier entier).
3. **Advanced settings → Secrets** : colle ce bloc avec tes vraies valeurs :

```toml
[supabase]
url = "https://xxxxxxxxxxxxx.supabase.co"
anon_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

4. **Deploy**. Tu obtiens une URL du type `https://suivi-recomposition.streamlit.app`.

### Étape 4 — Sur ton mobile

Ouvre l'URL dans Chrome (Android) ou Safari (iPhone) → menu → **Ajouter à l'écran d'accueil**.
L'application se lance alors en plein écran, comme une application native. Connecte-toi une fois :
la session est conservée.

---

## 4. Structure du projet

```
app/
├── app.py                       # interface Streamlit (7 pages)
├── db.py                        # couche de données : Supabase OU SQLite local
├── content.py                   # programme 30 min, liste de courses, presets protéines, calculs
├── integration.py               # passerelle avec l'application de menus (détection des colonnes)
├── schema.sql                   # schéma Supabase + politiques RLS (à coller dans le SQL Editor)
├── seed_demo.py                 # jeu de données de démonstration
├── requirements.txt
├── .streamlit/
│   ├── config.toml              # thème, port, options serveur
│   └── secrets.toml.example     # modèle de configuration Supabase (+ section [apps] facultative)
└── data/suivi.db                # base locale (mode hors ligne, non committée)
```

## 5. Utiliser Supabase depuis Python (hors de l'app)

La clé `anon` est faite pour être exposée côté client : la sécurité repose sur les **politiques RLS**,
qui n'autorisent l'accès qu'aux lignes dont `user_id = auth.uid()`. Depuis l'app Streamlit, l'utilisateur
s'authentifie par email/mot de passe, et toutes les requêtes portent son jeton.
En aucun cas il ne faut utiliser la clé `service_role` dans ce projet : elle contourne la RLS.

## 6. Notes

- Streamlit Community Cloud met l'application en veille après quelques jours sans visite : le premier
  chargement peut prendre 20 à 30 secondes. C'est normal et gratuit.
- Sauvegarde : page **Réglages → Export** (ZIP de CSV). À faire une fois par mois.
- Pour faire évoluer le programme (exercices, variantes, liste de courses) : tout est dans `content.py`,
  aucune autre modification n'est nécessaire.
