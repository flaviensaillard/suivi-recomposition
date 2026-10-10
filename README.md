# Équilibre — menus, nutrition et suivi de recomposition

> **État audité le 10 octobre 2026.** Ce dépôt contient deux expériences distinctes : une application Streamlit connectée au foyer et une coque Android à données locales. Voir le [rapport d’audit complet](AUDIT_COMPLET_2026-10-10.md).
>
> **Important : l’exigence produit « APK hors ligne synchronisée » n’est pas satisfaite.** L’APK actuelle fonctionne hors ligne sur un seul appareil, mais n’envoie ni ne reçoit aucune donnée. Les menus de l’APK ne sont pas partagés avec le foyer ni avec Streamlit. Ne pas la présenter comme un client synchronisé.

## Versions et publication

- Dernière release GitHub vérifiée : [`v1.0.12`](https://github.com/flaviensaillard/suivi-recomposition/releases/tag/v1.0.12), publiée le **6 octobre 2026**, `versionCode 13`.
- Cible de développement dans cette branche : **Android 1.0.13 / code 14**. Aucun nouveau binaire n’a été publié.
- Le build Android de cette branche n’a pas pu être compilé dans l’environnement d’audit : SDK Android absent. Le code et les tests locaux sont donc à distinguer d’une APK testée sur appareil.
- GitHub Actions produit un artefact de vérification ; la publication est désactivée par défaut et bloquée tant que la synchronisation hors ligne n’est pas implémentée et validée. Une future release devra aussi disposer des secrets de signature Android.

## Matrice fonctionnelle

| Besoin | Streamlit | APK Android (code actuel) |
|---|---|---|
| Menus familiaux partagés | Planning, recettes et courses passent par le magasin de menus connecté ; un parcours « partage » existe. Les permissions de la base de menus en production n’ont pas été vérifiées pendant cet audit. | Quelques écrans et données locales peuvent être utilisés sur le téléphone, mais il n’existe ni partage familial entre appareils, ni synchronisation avec le magasin Streamlit. |
| Suivis personnels | Connexion Supabase et filtrage par compte dans le code ; le schéma SQL suivi définit des règles RLS par `auth.uid()`. L’état réel des politiques Supabase n’a pas été inspecté. | Une seule zone locale au téléphone, sans authentification ni séparation de membres. |
| Utilisation hors ligne | Le service cloud nécessite un réseau. SQLite est réservé au développement mono-utilisateur explicitement activé ; il ne synchronise rien. | Les actifs HTML/JS et la saisie locale fonctionnent sans réseau. C’est du **stockage hors ligne uniquement**, pas du « offline-first synchronisé ». |
| Persistance | Supabase en mode connecté ; SQLite temporaire pour les tests et le développement local. | `localStorage` du WebView. Pas de file d’envoi, de fusion, de reprise après conflit ou de sauvegarde Android (`allowBackup=false`). |
| Accès aux pages Web | Application Streamlit. | Les URL Streamlit sont ouvertes dans le navigateur système, hors du WebView privilégié. |

Le parcours familial et les suivis privés restent donc à éprouver avec deux comptes de test et sur l’instance réelle avant toute affirmation de confidentialité de bout en bout.

## Architecture vérifiée dans le dépôt

```text
app.py, db.py, menus.py, repas.py, seances.py  → application Python / Streamlit
schema.sql                                      → schéma proposé pour les tables personnelles
app/src/main/                                   → source Android utilisée par build.sh
android/app/src/main/                           → copie Gradle, synchronisée avec la source ci-dessus
app/src/main/assets/www/js/net.js               → transport Supabase désactivé
app/src/main/assets/www/js/store.js             → données du téléphone dans localStorage
data/foods_ciqual.csv                           → extrait Ciqual local (3 339 lignes)
data/demo_menus.json                            → jeu de démonstration, pas la base de production
.github/workflows/apk.yml                       → build CI, release protégée
```

`MainActivity.java` charge les actifs locaux dans un WebView dont les requêtes réseau sont bloquées. Le pont JavaScript natif expose notamment haptique et ouverture de liens HTTPS, mais aucun transport HTTP de synchronisation. `net.js` renvoie explicitement l’état « désactivée ». Le code de l’APK ne constitue donc pas un client de Supabase.

### Limites importantes de la configuration de données

- Le script `schema.sql` suivi ici ne contient pas les colonnes d’objectifs glucides, lipides et calories que l’interface Streamlit demande. L’interface refuse maintenant de confirmer une sauvegarde partielle du profil lorsque le schéma est incompatible. **Aucune migration n’a été exécutée** ; faire vérifier et mettre à niveau le schéma avant de confirmer un profil complet.
- L’accès aux menus peut emprunter la clé publique si aucun compte de partage n’est configuré. Le code source ne suffit pas à établir les droits effectifs : les politiques des tables de menus en production doivent être contrôlées séparément.
- Les liens personnels Streamlit contenant `?cle=…` sont des secrets porteurs d’accès. Éviter de les publier, de les envoyer à des tiers ou de les laisser dans des journaux/captures.
- Le mode SQLite local ne doit pas être exposé sur Internet et n’isole pas plusieurs membres.

## Nutrition : calculs et provenance

- Le fichier `data/foods_ciqual.csv` contient **3 339 codes distincts** : 8 valeurs protéines, 144 glucides, 10 lipides, 3 281 fibres et 120 sels sont absents. Il ne s’agit pas d’une mesure des données familiales en production.
- Le convertisseur `ciqual.py` vise l’édition Ciqual 2025 de l’ANSES, qui annonce 3 484 aliments ; le CSV suivi dans ce dépôt n’a pas été réconcilié avec le classeur officiel pendant cet audit. La version exacte de cet extrait reste à établir.
- Les données sont des valeurs de référence pour 100 g de partie comestible. Des quantités/unités mal renseignées rendent les macros incomplètes ou approximatives. Les conversions estimées doivent rester visibles et ne pas être traitées comme une mesure exacte.
- Les totaux « calories estimées » à partir des macros utilisent une approximation 4/4/9 ; ils peuvent différer de l’énergie Ciqual. Les macros manquantes restent inconnues, pas zéro. Une valeur « 0 » explicitement saisie reste un zéro valide.
- Les objectifs et exemples codés dans `content.py` sont des repères historiques, non des recommandations universelles. Les écrans de comparaison restent neutralisés tant que le profil personnel n’est pas complet. L’exemple de journée restrictive a été retiré de l’écran Nutrition ; les objectifs de l’utilisateur n’ont pas été modifiés.

Sources : [Table Ciqual 2025 — ANSES](https://ciqual.anses.fr/cms/sites/default/files/inline-files/Table%20Ciqual%202025%20doc%20FR_2025_11_19.pdf) · [Notice du jeu de données et licence](https://entrepot.recherche.data.gouv.fr/dataset.xhtml?persistentId=doi%3A10.57745%2FRDMHWY). Toute redistribution doit conserver l’attribution ANSES et la licence applicables.

## Proposition sportive (générique, à adapter)

Le calendrier **lundi renforcement A / jeudi rugby / vendredi renforcement B** est intentionnel et conservé. Proposition prudente, non personnalisée :

- **Lundi — bas du corps et tronc :** squat ou variante, charnière de hanche, mouvement unilatéral, tronc ; choisir des variantes maîtrisées, démarrer avec un volume tolérable et garder quelques répétitions en réserve.
- **Jeudi — rugby :** activité principale à intensité variable ; noter la durée réellement effectuée et le ressenti. Une dépense calorique par formule MET reste une estimation très incertaine et ne doit pas modifier automatiquement l’alimentation.
- **Vendredi — haut du corps :** tirage et poussée, épaules et tronc ; alléger ou reporter selon la récupération après le rugby, et ne pas entraîner une zone douloureuse.
- **Progression :** ne changer qu’un paramètre à la fois après plusieurs séances confortables et correctement consignées. Un RPE, le sommeil ou une performance isolée ne diagnostiquent ni la récupération ni la conservation musculaire. En cas de douleur persistante ou inquiétante, demander un avis professionnel.

Le programme dans le code reste une base générique : matériel, antécédents, niveau, charge réelle et contraintes individuelles ne sont pas validés. Les adaptations proposées doivent rester explicites et confirmées par la personne.

## Tests reproductibles exécutés

Depuis la racine du dépôt :

```bash
node test_mobile.js
.venv/bin/python test_integrite.py
.venv/bin/python test_app.py
.venv/bin/python -m compileall -q .
bash -n build.sh
git diff --check
```

Résultats de cet audit :

- **6/6** tests mobiles ciblés passent (premier lancement vide, conservation des données locales anciennes, macros non préremplies, saisies facultatives, rendus mobiles).
- **12/12** tests d’intégrité Python passent (profils, macros, unités, sessions, douleur et estimation rugby).
- **10/10** pages Streamlit sont rendues sans exception dans le banc `AppTest`, avec SQLite jetable et mode mono-utilisateur de test.
- Compilation syntaxique Python, `bash -n` et `git diff --check` passent ; les arbres `app/src/main` et `android/app/src/main` sont identiques.
- **Compilation APK non vérifiée** : `bash build.sh` s’arrête faute de SDK Android dans cet environnement. Aucun téléphone/émulateur, compte réel, base Supabase ou instance Streamlit de production n’a été testé.

Pour compiler localement, installer un JDK 17 et le SDK Android avec build-tools 34.0.0, puis lancer `bash build.sh`. Sans clé persistante explicitement configurée, le script utilise une clé temporaire aléatoire, supprimée en fin de build ; l’APK ainsi signée n’est pas une release installable par-dessus une version signée avec la clé de production.

## Feuille de route priorisée

1. **P0 — APK synchronisée :** concevoir authentification individuelle, stockage local durable, file d’opérations idempotente, reprise réseau, suppressions/tombstones, conflits, confidentialité au repos, migrations locales, déconnexion, export et stratégie de récupération. Tester avec deux comptes et deux appareils. Tant que ce lot n’est pas validé, garder `APK_SYNC_READY=false` et ne pas publier.
2. **P0 — Confidentialité de production :** vérifier, en lecture seule, les politiques RLS de toutes les tables personnelles et de menus, le parcours `?partage=1`, les comptes de partage et l’isolation Léa/Flavien ; documenter précisément qui peut lire/écrire. Ne pas confondre les commentaires du code avec une mesure en production.
3. **P1 — Schéma et sauvegarde du profil :** réconcilier `schema.sql` avec les champs réellement utilisés par Streamlit, tester la mise à niveau sur une base de test, puis seulement planifier une migration contrôlée. Ce dépôt n’a appliqué aucune migration.
4. **P1 — Données nutritionnelles :** comparer l’extrait de 3 339 lignes au fichier Ciqual officiel 2025, conserver provenance/licence et valeurs « traces » comme inconnues, mesurer la couverture des ingrédients du foyer et faire valider les unités/portions.
5. **P1 — Validation sportive :** vérifier le matériel, les variantes et le volume avec l’utilisateur ; distinguer séances prévues et réalisées, puis n’exploiter que des séries réellement saisies. Faire relire les contenus santé par un professionnel.
6. **P2 — Versionnement et documentation :** harmoniser les numéros de version Streamlit/Android et les URLs configurées ; archiver les rapports précédents comme historiques afin qu’ils ne soient pas confondus avec l’état courant.

## Périmètre de sécurité de cette session

Tests isolés et code source seulement. Pas de lecture/écriture Supabase, pas de changement de permissions, pas de migration, pas d’accès aux secrets de production, pas de déploiement Streamlit, pas de publication GitHub, pas de commit ni push. Le rapport décrit ce qui est vérifié dans ce checkout ; toute propriété de la base ou du service actuellement déployé qui n’a pas été mesurée est indiquée comme non vérifiée.
