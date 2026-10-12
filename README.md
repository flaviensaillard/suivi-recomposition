# Équilibre — suivi de recomposition, menus et Coach IA

Version **1.4** (Android `versionCode 25`). Streamlit aligné sur la même version.

## 1.4 — Supabase fait autorité

La 1.3.10 était « local-first » : `store.js` écrivait toujours dans `localStorage` et ne poussait
vers Supabase que si une session existait. Sans compte, l'application restait indéfiniment un
carnet local. **Ce n'est plus le cas.**

| | 1.3.10 | 1.4 |
|---|---|---|
| Source de vérité | `localStorage` | **Supabase** |
| Sans compte Supabase | l'app fonctionne en local | **l'app ne s'ouvre pas** : l'écran de connexion s'affiche |
| Hors ligne | fonctionnement normal, local | les saisies vont dans un **tampon local** |
| Retour du réseau | rien, sauf si une nouvelle saisie déclenche la synchro | **le tampon se déverse automatiquement** dans Supabase |

Trois mécanismes portent ce changement :

- **`store.js` · `estEnLigne()`** — consulte `navigator.onLine` **et** `Native.isOnline()`, les
  événements du navigateur n'étant pas fiables dans un WebView Android.
- **`store.js` · `surveillerConnexion(cb)`** — écoute `online`/`offline` et sonde toutes les 5 s en
  secours ; rappelle `cb` à chaque transition hors ligne → en ligne, jamais deux fois de suite.
- **`store.js` · `migrerDonneesLocalesVersFile()`** — au premier lancement, pousse le contenu local
  hérité de la 1.3.10 dans la file de synchronisation puis **vide les caches locaux**. Les réglages,
  la session et la file survivent. Un marqueur `eq.migration.v1.4` garantit que l'opération ne se
  rejoue pas.

Le démarrage (`app.js` · `demarrerSynchronise()`) refuse donc l'entrée sans session, exécute la
migration une fois, puis tire les données depuis Supabase avant d'afficher quoi que ce soit.

> **Provenance de la base 1.3.10.** Le dépôt ne contenait plus le code correspondant à l'APK
> réellement installée. Cette base a été **restaurée à partir du paquet binaire**
> `telechargements/Equilibre-1.3.10.apk` (sha256 `b875d6c23b734de3d9e7a7725a295eb530902e4e7c0943cf25543215ebd3f8c6`,
> 161 875 octets, signé `META-INF/EQUILIBR.RSA`). Voir « Ce qui a pu être restauré » plus bas.

## Ce que fait l'application

| Fonction | Où |
|---|---|
| Pesées, mensurations, nutrition, séances | `assets/www/js/store.js`, `views.js` |
| Menus familiaux, recettes, liste de courses | `assets/www/js/menu.js`, `menu_views.js` |
| **Coach IA** : conversation persistante, analyse de journée, rapports validés | `assets/www/js/coach.js` |
| Synchronisation Supabase (authentification, file d'attente locale) | `assets/www/js/net.js` |
| Coque Android (WebView + pont natif) | `MainActivity.java`, `NativeBridge.java` |
| Application Streamlit de bureau | `app.py`, `menus.py`, `repas.py`, `seances.py`, `editeurs.py` |

Les deux arbres `app/src/main` et `android/app/src/main` sont maintenus identiques.

## Coach IA — ce qu'il faut savoir avant de l'utiliser

L'IA **n'est pas dans l'APK** : aucun SDK d'apprentissage n'est empaqueté. L'application est un
client HTTP d'un **Worker Cloudflare** dont l'adresse se règle dans ⚙ Réglages
(`regCoachUrl`, vide par défaut). Tant qu'elle n'est pas renseignée, `coach.js:55` refuse tout appel.

- **Endpoints appelés** : `/api/coach/chat`, `/api/coach/analyze`, `/api/coach/memory`,
  `/api/coach/history`, `/api/coach/reports`, `/api/coach/reports/approve`, `/api/health`
- **Authentification** : le jeton de session Supabase est réutilisé (`Authorization: Bearer …`, `coach.js:67`)
- **Recherche web** : effectuée côté Worker, sources affichées et cliquables (`coach.js:288`)
- **Secrets** : les clés Cloudflare et Tavily restent côté Worker, jamais dans l'application

**Données qui quittent l'appareil** vers `/api/coach/chat` (`construireContexteChat`, `coach.js:124`).
Le test `testContexteEnvoyeAuCoachIa` les borne explicitement :

- nutrition des **7 derniers jours** uniquement (totaux et moyennes, jamais le détail jour par jour)
- **4 dernières séances**, notes tronquées à **160 caractères**
- **la dernière mensuration** seulement
- les 7 dernières pesées (date + poids), pas, sommeil, énergie
- les objectifs du profil et les repas planifiés du jour

`/api/coach/analyze` envoie en plus la journée complète et le texte libre saisi.

## Synchronisation et stockage

`net.js` porte un transport Supabase authentifié avec file d'attente locale
(clé `eq.sync.queue.v1`). Les écritures utilisent le jeton de l'utilisateur afin de respecter les
règles RLS ; seule la clé publishable/anon est stockée sur l'appareil.

Depuis la 1.4, `localStorage` n'est plus qu'un **tampon** : les clés restent les mêmes
(`eq.logs.v1`, `eq.mensurations.v1`, `eq.seances.v1`, `eq.series.v1`, `eq.nutrition.v1`,
`eq.courses.v1`, `eq.profil.v1`, `eq.reglages.v1`, `eq.menu.*.v1`) mais leur contenu est reconstruit
depuis Supabase à chaque tirage. Une coupure réseau ne perd rien : les écritures s'accumulent dans
`eq.sync.queue.v1` et partent au retour de la connexion.

Le manifeste déclare `INTERNET`, `ACCESS_NETWORK_STATE` et `VIBRATE`. Les URL Streamlit ouvertes
depuis l'app le sont dans le navigateur système, hors du WebView qui porte le pont natif.

## Ce qui a pu être restauré, et ce qui ne l'a pas été

| Élément | État |
|---|---|
| 12 fichiers `assets/www/**` (HTML, CSS, 10 modules JS) | **Restaurés à l'octet près** depuis l'APK, vérifié par `cmp` sur les 12 |
| `coach.js` (37 866 o), `menu.js` (26 181 o), `menu_views.js` (33 535 o) | Absents du dépôt, **réintégrés** |
| `MainActivity.java`, `NativeBridge.java` | **Non décompilables** ici (pas de JDK). Les sources du dépôt exposent exactement la même surface : pont enregistré sous `Native`, 7 méthodes `isOnline`, `haptic`, `toast`, `openExternal`, `share`, `versionCode`, `versionName`. Seuls les numéros de version ont été mis à jour |
| `AndroidManifest.xml`, `res/` | Sources du dépôt conservées ; valeurs vérifiées sur le binaire (`fr.recomposition.suivi`, `.MainActivity`, `@string/app_name`) |
| Code Python / Streamlit | **Non issu de l'APK** — inchangé hormis `VERSION` |

## Garde-fous non repris

Le fork 1.0.12/1.0.13 publié depuis ce dépôt avait ajouté des protections qui **n'existent pas
dans la 1.3.10** et n'ont donc pas été réintroduites :

- `store.anciennesDonneesAverifier()` et le bandeau « Données locales antérieures à vérifier »
- la clé de migration `eq.revisionDonnees.v2`
- `reglages.profileConfigured` et le bandeau « Repères à vérifier — non personnalisés »
- les écrans de comparaison neutralisés tant que le profil n'est pas complet

La 1.3.10 préremplit les objectifs (130 g de protéines, 1 700 kcal, 140 g de glucides, 50 g de
lipides, TDEE 2 400 kcal, `store.js:29`). Ce sont des valeurs par défaut, pas des recommandations
personnalisées : à corriger dans Réglages avant de s'y fier.

## Correction appliquée au code restauré

Une seule modification de comportement a été apportée au code issu de l'APK :

- `ui.js:199` — `svgBarresProteines` produisait `x="NaN"` lorsqu'une **seule** journée de données
  était disponible (`gap` valait `264/0 = Infinity`, puis `0 × Infinity = NaN`). Garde ajoutée sur
  `donnees7j.length > 1`. Détecté par `testGraphiqueProteinesVideEtUneValeur`.

## Tests

```bash
node test_mobile.js                 # 9/9 — coque mobile, dont la synchro 1.4
.venv/bin/python test_integrite.py  # 12/12 — profils, macros, unités, séances
.venv/bin/python test_app.py        # 10/10 — pages Streamlit rendues
.venv/bin/python -m compileall -q .
bash -n build.sh
git diff --check
```

La suite mobile a été réalignée sur le contrat réel de la base restaurée ; les assertions qui
portaient sur les garde-fous supprimés ont été retirées et sont listées ci-dessus. Trois tests
couvrent la 1.4 : détection du réseau, déversement au retour en ligne, et migration locale.

## Compilation de l'APK

```bash
VERSION_NAME=1.4 VERSION_CODE=25 bash build.sh
```

JDK 17 et SDK Android (platform 34, build-tools 34.0.0) requis. Sans clé de signature configurée,
`build.sh` utilise une clé temporaire aléatoire supprimée en fin de build : l'APK produite ne peut
pas être installée par-dessus une version signée avec la clé de production.

La CI (`.github/workflows/apk.yml`) construit un artefact de vérification. La publication d'une
release reste bloquée tant que `APK_SYNC_READY` n'est pas passé à `true`.

## Historique récent

- Les releases `v1.0.12`, `v1.2.0` et `v1.0.13` et leurs tags ont été supprimés : elles
  correspondaient à une branche appauvrie (hors ligne seul, synchronisation neutralisée, ni Coach IA
  ni menus connectés), et non à l'application réellement utilisée.
- Les documents de suivi obsolètes ont été retirés (`AUDIT_1.0.8.md`, `AUDIT_COMPLET_2026-10-10.md`,
  `A_LIRE.md`, `EMPREINTES_MD5.txt`, `LIRE_MOI.md`, `PROCHAINES_ETAPES.md`). Ils restent consultables
  dans l'historique Git.
