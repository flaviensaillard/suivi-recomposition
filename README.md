# Équilibre · Suivi de Recomposition Corporelle & Menus

Application mobile Android native et interface de suivi de recomposition corporelle (perte de masse grasse, maintien du muscle, apport protéique optimal) et de gestion des repas & courses du foyer.

Cette nouvelle version apporte une refonte ergonomique et visuelle complète inspirée du design system moderne et fluide de **MonPortefeuille2** : cartes posées, tuiles interactives cliquables, typographie contrastée, graphiques vectoriels SVG, animations fluides et retour haptique.

---

## 📥 Téléchargement direct de l'APK Android

L'APK Android est construite, signée et publiée directement via GitHub Actions :

- **Lien direct (Dernière version)** : [Equilibre.apk](https://github.com/flaviensaillard/suivi-recomposition/releases/latest/download/Equilibre.apk)
- **Lien direct v1.2.0** : [Equilibre-1.2.0.apk](https://github.com/flaviensaillard/suivi-recomposition/releases/download/v1.2.0/Equilibre-1.2.0.apk)
- **Lien direct alternatif** : [suivi-recomposition.apk](https://github.com/flaviensaillard/suivi-recomposition/releases/latest/download/suivi-recomposition.apk)
- **Releases GitHub** : [Toutes les versions publiées](https://github.com/flaviensaillard/suivi-recomposition/releases)

### Installation sur votre smartphone Android
1. Téléchargez le fichier `Equilibre.apk` via l'un des liens directs ci-dessus.
2. Touchez le fichier dans votre panneau de notifications ou dans votre gestionnaire de fichiers.
3. Si Android vous demande d'autoriser l'installation d'applications inconnues pour votre navigateur ou explorateur, appuyez sur **Autoriser cette source**.
4. Validez l'installation et profitez d'une expérience fluide et instantanée !

---

## ✨ Nouveautés ergonomiques & Fonctionnalités

### 1. 📊 Tableau de bord & Tuiles cliquables
- **Carte Hero** : Poids actuel, cible (77 kg), delta total et moyenne mobile 7 jours.
- **Tuiles métriques interactives** :
  - *Déficit calorique* : Calories du jour vs objectif (1 700 kcal).
  - *Protéines* : Jauge temps réel par rapport à l'objectif de 130 g/jour.
  - *Séance du jour* : Type de séance recommandée (A ou B) avec accès direct.
  - *Repas & Courses* : Aperçu du déjeuner et nombre d'articles restants à acheter.
- **Boutons 1-clic repas types** : Ajout instantané de votre gamelle déjeuner (58 g prot), goûter (7 g prot) ou thé menthe sans formulaire superflu.

### 2. ⚖️ Pesée & Tendance
- **Graphique vectoriel interactif SVG** : Visualisation de l'évolution du poids réel (points tactiles) et de la courbe de tendance (moyenne mobile 7 jours).
- **Graphique d'apport protéique** : Histogramme hebdomadaire avec ligne repère à 130 g.
- **Feuille modale de pesée** : Saisie tactile ultra-rapide (poids, calories, protéines, commentaires).
- **Suivi des mensurations** : Historique et saisie du tour de taille (ombilic), hanches, poitrine, cuisses et bras.

### 3. ⏱️ Séances d'entraînement (30 minutes)
- **Programme optimisé** : Séances A (Dos, Pectoraux, Cuisses) et B (Épaules, Ischios, Bras, Gainage) spécialement conçues pour un créneau court de 30 minutes.
- **Supersets & Notes de progression** : Alternance d'exercices pour maximiser l'intensité et le temps de repos sans perte de temps.
- **Minuteur de repos intégré** : Choix rapide 60s, 90s ou 120s avec compte à rebours, alertes sonores de fin de repos et vibration haptique.
- **Validation en 1 clic** : Sauvegarde dans l'historique d'entraînement.

### 4. 🛒 Menus du foyer & Liste de courses interactive
- **Planning de la semaine** : Répartition midi et soir pour 2 personnes.
- **Fiches recettes détaillées** : Ingrédients, temps de préparation, étapes de cuisson et apports nutritionnels.
- **Liste de courses interactive** : Articles classés par rayon (Frais, Épicerie, Primeur), cases à cocher tactiles avec mémorisation instantanée.

### 5. 🌐 Coque d'applications Web Streamlit
- Bascule instantanée entre **Suivi Recomposition** (`suivi-recomposition-corporelle.streamlit.app`) et **Menus du Foyer** (`menus-foyer.streamlit.app`).
- Bouton d'actualisation rapide et ouverture externe dans le navigateur si nécessaire.

---

## 🛠️ Architecture technique

L'application repose sur une double architecture hybride hautement performante :

```
suivi-recomposition/
├── app/
│   └── src/main/
│       ├── AndroidManifest.xml          # Déclaration permissions, icône et orientation
│       ├── java/fr/recomposition/suivi/
│       │   ├── MainActivity.java        # WebView matérielle, accélération GPU, pont JS
│       │   └── NativeBridge.java        # Pont natif (vibration haptique, toast, HTTP async)
│       ├── res/                         # Icônes mipmap adaptatives, styles et thèmes sombres
│       └── assets/www/                  # Application mobile autonome hors-ligne
│           ├── index.html               # Structure HTML5 épurée
│           ├── css/app.css              # Design system sombre moderne (cibles >= 44px)
│           └── js/
│               ├── util.js              # Formatage dates, nombres, sanitisation HTML
│               ├── models.js            # Données statiques, séances A/B, recettes, repas types
│               ├── store.js             # Moteur de persistance local (LocalStorage / Cache)
│               ├── net.js               # Synchronisation REST avec Supabase
│               ├── ui.js                # Feuilles modales, toasts, haptique, SVG
│               ├── views.js             # Rendu modulaire des 5 écrans
│               └── app.js               # Contrôleur principal et routage
├── android/                             # Arborescence projet Gradle alternative
├── .github/workflows/apk.yml            # Pipeline CI/CD GitHub Actions de compilation & release
├── build.sh                             # Script de compilation autonome ultra-rapide (aapt2/d8)
└── apercu.html                          # Page de présentation avec simulateur mobile interactif
```

---

## 🔨 Compilation locale de l'APK (sans Gradle)

Le script `build.sh` compile l'application en quelques secondes avec les outils standard du SDK Android (`aapt2`, `javac`, `d8`, `zipalign`, `apksigner`) :

```bash
# Vérifier la présence du SDK Android et de Java 17
export ANDROID_SDK_ROOT="/path/to/android-sdk"
export JAVA_HOME="/path/to/jdk-17"

# Lancer la compilation et signature
bash build.sh

# L'APK signée est disponible dans :
# dist/Equilibre.apk
```

---

## 🚀 Pipeline GitHub Actions

À chaque push ou déclenchement manuel via l'onglet **Actions** de GitHub (`workflow_dispatch`), le workflow `.github/workflows/apk.yml` :
1. Configure l'environnement Java 17 et les `build-tools 34.0.0`.
2. Exécute `bash build.sh`.
3. Crée automatiquement la release GitHub `v1.2.0`.
4. Attache `Equilibre.apk` et `Equilibre-1.2.0.apk`.
5. Fournit les liens de téléchargement direct prêts à l'emploi.
