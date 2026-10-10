# Audit technique et produit — Équilibre

**Date :** 10 octobre 2026 · **Branche :** `arena/3af282d0-suivi-recomposition` · **Checkout audité :** `f767740ea38369caac293354adab80e0ca110d61` (travail local non commité)

## Synthèse exécutive

L’application a deux cibles qu’il ne faut pas confondre : **Streamlit est l’expérience familiale connectée** (menus partagés, suivis personnels séparés) ; **l’APK est actuellement une interface Android locale**, sans authentification ni synchronisation. La demande d’un véritable client hors ligne synchronisé **n’est donc pas satisfaite**. Aucune nouvelle APK ne doit être annoncée comme telle ni publiée avant réalisation et validation de la synchronisation.

L’audit a également constaté un décalage entre le schéma SQL suivi dans Git et les fonctions de profil/sport de Streamlit, ainsi qu’un décalage entre le CSV Ciqual présent et la taille annoncée pour l’édition officielle 2025. Les modifications locales améliorent les garde-fous de profil/macros, corrigent deux calculs nutritionnels à risque de fausse précision, atténuent des promesses sport/santé et ferment la publication APK dans le workflow actuel. Elles **n’ont touché ni la base, ni les permissions, ni les objectifs personnels, ni la production**.

### Décision de mise en service

| Sujet | Décision de l’audit |
|---|---|
| APK 1.0.13 / code 14 | Cible de développement uniquement. Pas compilée ici, pas installée ni publiée. Ne pas la qualifier de synchronisée. |
| Dernière release connue | `v1.0.12`, publiée le 6 octobre 2026, APK `versionCode 13` — consultée en lecture seule sur GitHub. |
| Streamlit / Supabase réels | Pas de requête à la base ni au service hébergé. RLS, comptes, secrets et politiques de menus restent non vérifiés en production. |
| Calendrier sportif | **Lundi A / jeudi rugby / vendredi B conservé intentionnellement**, selon la consigne produit. |
| Données et migration | Aucune écriture, aucun changement de permissions, aucune migration, aucun déploiement, commit ou push. |

## 1. Périmètre, méthode et niveau de preuve

L’examen porte sur le code et les artefacts **présents dans ce checkout** : Python/Streamlit, Java/WebView et JavaScript Android, schéma SQL suivi, données de démonstration, script de build, workflow GitHub Actions et documentation. Les tests Streamlit ont été lancés avec SQLite jetable ; les tests de persistance ne lisent pas les données familiales.

Les résultats sont marqués ainsi :

- **Vérifié dans le code ou les fichiers** : observation directe, reproductible dans le dépôt.
- **Testé localement** : résultat d’un test exécuté dans le bac à sable ; ne vaut pas test sur appareil ou en production.
- **Non vérifié** : nécessite la base, les comptes, l’hébergement, une clé de publication ou un terminal réel. Aucune déduction de sécurité n’est faite à partir d’un commentaire de code.
- **Recommandation** : proposition de conception, pas une prescription médicale ou nutritionnelle.

Aucun APK n’a pu être compilé : le bac à sable ne possède pas le SDK Android (et ne présente ni `java`, ni `javac`, ni `keytool` dans le `PATH`). La commande `bash build.sh` s’arrête sur `SDK Android introuvable dans /home/user/.cache/android-sdk`.

## 2. Architecture et matrice APK / Streamlit

### Architecture observée

- **Streamlit** : application Python dans `app.py`, stockage connecté via `SupaStore` dans `db.py`, magasin de menus via `MenusStore` dans `menus.py`. Le mode SQLite mono-utilisateur est maintenant conditionné par `EQUILIBRE_SINGLE_USER_LOCAL=1` ; sans Supabase configuré, le site ne bascule plus silencieusement sur un journal personnel local.
- **Données personnelles** : le code filtre les tables `sr_*` par `user_id`. `schema.sql` définit des règles RLS fondées sur `auth.uid()`. C’est une preuve de l’intention du schéma suivi, **pas une mesure de la configuration Supabase actuelle**.
- **Menus familiaux** : Streamlit possède un parcours `?partage=1` et peut utiliser un compte de partage ou une clé publique. Les tables et politiques effectives du service de menus ne sont pas décrites intégralement par `schema.sql` et n’ont pas été contrôlées.
- **Android** : `MainActivity.java` charge les actifs embarqués dans une WebView. JavaScript utilise `localStorage` ; `NativeBridge` offre des fonctions natives simples (haptique, partage, ouverture HTTPS), pas de client HTTP. `net.js` renvoie systématiquement `synchronise: false`. Le WebView bloque les requêtes réseau et ouvre les pages HTTPS dans le navigateur système.
- Les arbres `app/src/main/` (utilisé par `build.sh`) et `android/app/src/main/` (copie Gradle) sont identiques dans le checkout audité.

### Matrice fonctionnelle

| Capacité | Streamlit | APK Android actuelle | Écart vis-à-vis du besoin confirmé |
|---|---|---|---|
| Menus partagés du foyer | Menus, recettes, planification et courses connectés, avec parcours de partage. Accès réel dépend des comptes/politiques non vérifiés ici. | Écrans/données locaux au téléphone ; aucune synchronisation du planning ou de la liste avec les autres membres/appareils. | **Partage familial hors ligne absent sur APK.** |
| Suivis personnels | Compte Supabase et filtres `user_id` dans le code ; séparation effective à tester avec deux comptes réels. | Un magasin local unique ; pas de login ni de séparation par personne. | Ne pas saisir de données de plusieurs personnes sur le même profil APK. |
| Hors ligne | Le cloud requiert le réseau. Le mode SQLite local sert au développement et ne se synchronise pas. | Les actifs et la saisie locale restent disponibles hors réseau. | Hors ligne local ≠ client hors ligne synchronisé. |
| Synchronisation multi-appareils | PC ↔ Supabase pour l’application Streamlit configurée. | Aucune lecture/écriture cloud, file d’attente, reprise, fusion ou résolution de conflits. | **Exigence P0 non remplie.** |
| Protection locale | Données dans Supabase, sous réserve de configuration de production vérifiée. | Données dans `localStorage` de la WebView ; `allowBackup=false`, pas de chiffrement applicatif ni de sauvegarde/récupération. | Risque de perte au changement/désinstallation du téléphone ; stratégie d’export à concevoir. |
| Liens vers le Web | Service Streamlit lui-même. | Ouverture du navigateur système ; les pages distantes ne tournent pas dans la WebView privilégiée. | L’onglet « Apps Web » n’est pas une session Streamlit embarquée. |

## 3. Registre des risques et actions P0–P3

Échelle : **P0** bloque la conformité du besoin ou une publication ; **P1** peut affecter l’intégrité, la confidentialité ou la justesse ; **P2** fiabilité/documentation ; **P3** amélioration non bloquante.

| ID | Priorité | Constat / risque | Action et critère de clôture | État |
|---|---|---|---|---|
| R-01 | **P0** | L’APK n’a ni authentification individuelle ni synchronisation ; le transport est explicitement désactivé et le WebView bloque le réseau. | Concevoir authentification, base locale durable, journal d’opérations idempotent, reprise, suppressions/tombstones, gestion des conflits, export/récupération et tests à deux comptes/deux appareils. | **Ouvert — bloquant.** La release est bloquée dans le workflow local. |
| R-02 | **P0** | Les permissions réelles Supabase des données personnelles et du magasin partagé ne sont pas vérifiées. Le code prévoit une voie par clé publique quand aucun compte de partage n’est configuré. | Vérification en lecture seule des politiques et tests d’isolation avec comptes de test, y compris parcours famille ; documenter précisément qui peut lire/écrire chaque table. | **Ouvert — production non auditée.** |
| R-03 | **P1** | `schema.sql` n’a pas `target_carbs_g`, `target_fat_g`, `target_kcal`, alors que l’écran de profil les exige. Le fichier `19_objectifs.sql` mentionné auparavant n’est pas présent dans le dépôt. | Réconcilier le schéma suivi avec le modèle applicatif ; éprouver une migration sur une base de test avant toute proposition de changement en production. | **Ouvert — aucune migration faite.** Le code local refuse maintenant l’écriture partielle du profil. |
| R-04 | **P1** | Le schéma suivi limite `sr_workouts.session` à `('A','B')`, alors que le rugby est enregistré avec le code `C`. Une base créée strictement depuis ce schéma rejettera cette validation ; le repli dans `notes` ne contourne pas la contrainte. | Prévoir et tester une évolution de schéma autorisant le code rugby, sans confondre séance planifiée et séance réalisée. | **Ouvert — base réelle inconnue, aucune migration faite.** |
| R-05 | **P1** | Le schéma suivi de `sr_protein_entries` ne définit pas `carbs_g` / `fat_g` ; le code tolère leur absence, mais les calories et macros restent alors incomplètes et ne peuvent être enregistrées/corrigées complètement. | Aligner schéma, scripts d’installation et UI ; tester les anciens et nouveaux profils avant migration. | **Ouvert — la gestion reste prudente, données réelles non vérifiées.** |
| R-06 | **P1** | `data/foods_ciqual.csv` a 3 339 codes, tandis que `ciqual.py` vise l’édition officielle 2025 annoncée à 3 484 aliments. Version exacte du CSV non établie ; couverture nutriments incomplète. | Réconcilier le CSV avec le classeur officiel, noter date/version/licence/attribution et publier un rapport de couverture. | **Ouvert — la conversion `< x` → valeur inconnue est corrigée localement ; CSV inchangé.** |
| R-07 | **P1** | Données de santé stockées localement sur un profil Android unique, sans chiffrement applicatif, compte, backup ou récupération. Partage d’appareil et perte du téléphone exposent à une perte ou à une confusion de personne. | Avant activation de la sync : modèle de menace, isolation membre, protection des secrets et données au repos, révocation/déconnexion, export et parcours de récupération. | **Ouvert.** |
| R-08 | **P1** | La séance Streamlit enregistre ressenti/durée et plan proposé, mais pas les séries réellement exécutées. Les plans ne doivent pas être présentés comme une mesure du volume ou de la progression par exercice. | Ajouter la saisie facultative des séries réellement faites (répétitions/charge/variante), conserver séparément prévu et exécuté, tester doublons et corrections. | **Ouvert — le code évite déjà d’écrire les répétitions prévues comme réelles.** |
| R-09 | **P1** | Exemples nutritionnels et affirmations sportives historiques pouvaient paraître prescriptifs ou garantir prévention/blessure. | Remplacer les promesses par des formulations prudentes ; éviter la journée alimentaire restrictive par défaut ; faire relire les contenus par un professionnel. | **Partiellement corrigé localement** (bannière, texte nutrition, messages d’exercices) ; revue complète encore requise. |
| R-10 | **P1** | Le lien personnel `?cle=…` est un secret porteur d’accès placé dans une URL ; fuite possible par historique, capture ou journal. | Préférer une authentification individuelle standard ; si le lien persiste, rotation, durée limitée et consignes anti-partage. | **Ouvert — aucun secret de production consulté.** |
| R-11 | **P2** | Les versions ne sont pas harmonisées : Android cible `1.0.13/14`, `app.py` déclare encore `1.0.12`, les modules Python ont des marqueurs plus anciens. Plusieurs documents/URLs historiques divergeaient. | Définir une version Streamlit distincte ou alignée, vérifier les versions des modules et confirmer les URL de déploiement avant une release. | **À planifier.** README actuel nettoyé ; aucun déploiement effectué. |
| R-12 | **P2** | La copie Gradle et la source de `build.sh` divergeaient dans le dépôt initial ; un build futur pouvait compiler un autre code. | Garder une source unique ou un contrôle automatique de parité. | **Corrigé localement** par synchronisation ; comparaison finale sans différence. |
| R-13 | **P2** | L’ancien rapport `AUDIT_1.0.8.md` décrivait un snapshot différent et pouvait être lu comme un audit actuel. | Marquer les rapports datés comme historiques et référencer le rapport courant. | **Corrigé** par un avertissement visible en tête du fichier. |
| R-14 | **P3** | Les portions par défaut, densités et conversions de pièces peuvent être approximatives, même lorsque la donnée de base existe. | Ajouter une source/indicateur de confiance par unité et permettre de laisser inconnu plutôt que de fabriquer une précision. | **Amélioration continue.** L’UI signale déjà des lignes incomplètes/approximatives. |

## 4. Analyse Streamlit, partage et confidentialité

### Points positifs vérifiés dans le code

- Sans configuration Supabase, le mode mono-utilisateur SQLite exige maintenant l’opt-in `EQUILIBRE_SINGLE_USER_LOCAL=1` et avertit qu’il ne convient pas à Internet.
- L’accès personnel n’est plus automatiquement accordé lorsqu’aucune clé personnelle n’est configurée ; le parcours demande une connexion explicite.
- Les pages de données personnelles filtrent par `user_id`, et le schéma SQL versionné définit RLS par utilisateur. Il s’agit d’une défense en profondeur utile, **à condition que le schéma et les politiques réellement déployés soient conformes**.
- Le mode profil incomplet ne montre pas de comparaison à une cible personnelle. Les formulaires de pesée, mensurations et nutrition acceptent les champs facultatifs sans leur substituer des valeurs inventées.
- Les pages partagées masquent les données personnelles prévues par le code ; les tests locaux n’établissent toutefois pas l’isolation en production.

### Limites et cas à éprouver

- `?partage=1` peut s’appuyer sur un compte partagé défini dans les Secrets ou sur le client avec clé publique. Le statut des politiques des tables `ingredients`, `recipes`, `recipe_ingredients`, `planned_meals` et de la liste de courses n’est pas contrôlable depuis les seuls fichiers de ce dépôt.
- Une clé personnelle dans l’URL fonctionne comme un bearer secret. Ne pas confondre sa comparaison en temps constant avec une authentification à durée limitée.
- La base réelle peut avoir reçu des changements manuels non présents dans `schema.sql`. Cet audit n’a ni vérifié ces changements ni testé les refus RLS.
- Aucun test de bascule de session entre un lien personnel et le lien partagé, dans un navigateur déjà authentifié, n’a été réalisé sur Streamlit hébergé.

**Conclusion confidentialité :** l’architecture exprimée dans le code vise à séparer suivi personnel et menus partagés ; l’affirmation « seule la famille autorisée voit les menus, chaque personne ne voit que ses suivis » doit rester **non vérifiée** jusqu’aux tests réels et à l’inspection en lecture seule des politiques de production.

## 5. Analyse nutritionnelle

### Données présentes et limites de provenance

- Le CSV embarqué comporte **3 339 lignes et 3 339 codes uniques**. Champs absents : protéines **8**, glucides **144**, lipides **10**, fibres **3 281**, sel **120** (toutes proportions calculées sur ce fichier local).
- `data/demo_menus.json` est un **jeu de démonstration**, pas une extraction de la base actuelle : 216 ingrédients, 104 recettes, 161 relations recette-ingrédient, 79 menus planifiés. Parmi ces ingrédients de démonstration, 63 seulement portent un code Ciqual ; 63 ont des calories/protéines/lipides et 59 des glucides. Ces chiffres ne permettent pas de conclure à la couverture des menus du foyer en production.
- Le convertisseur `ciqual.py` vise Ciqual 2025, dont la documentation ANSES annonce 3 484 aliments. Sans fichier Excel source/versionné ni comparaison ligne à ligne, il est impossible de savoir si les 145 lignes d’écart viennent d’une ancienne édition, d’aliments sans énergie exploitable, d’un filtre ou d’un autre export.
- La Table Ciqual indique des valeurs nutritionnelles de référence pour 100 g de partie comestible. La documentation énergétique utilise des facteurs pouvant différer d’un calcul simplifié par macros. Pour une redistribution, conserver l’attribution ANSES et la licence ouverte applicable.

### Calculs et saisie

- Les recettes utilisent les champs kcal/protéines/glucides/lipides par 100 g. `menus.calculer_recette` porte un indicateur de complétude par nutriment et rend visibles les quantités non convertibles ou estimées.
- Le journal Streamlit additionne les macros connues, mais marque les calories incomplètes dès qu’une ligne manque de glucides ou de lipides. Un champ manquant n’est pas assimilé à 0 ; une valeur explicite égale à 0 reste valide. Les calories « estimées » sur journal utilisent `4×protéines + 4×glucides + 9×lipides` et sont maintenant libellées comme estimation, distincte de l’énergie Ciqual.
- Les raccourcis de protéines ne sont que des raccourcis de saisie ; ils ne devraient pas être interprétés comme une recommandation de whey ou autre supplément.
- `ciqual.py` convertissait auparavant `< x` en `x`, ce qui confondait une borne analytique avec une mesure exacte. Le parseur local laisse désormais les valeurs `< x` et « traces » inconnues.
- `menus.quantite_en_grammes` supposait auparavant des grammes si l’unité et celle de l’aliment étaient absentes. Le code local traite maintenant ce cas comme non convertible ; il ne doit pas produire de total complet silencieusement.
- Les valeurs par défaut de portions, les unités « pièce/verre/cuillère » et les correspondances approchées peuvent donner des estimations. Les propositions de réparation/macros doivent rester visibles avant validation par l’utilisateur.

### Objectifs et pertinence des contenus

`content.py` et `schema.sql` contiennent encore des valeurs historiques et divergentes pour plusieurs champs d’objectifs ; elles ne constituent **pas des recommandations** et n’ont pas été modifiées dans cet audit. Le profil n’est traité comme personnalisé que si les champs requis sont présents ; aucun profil réel n’a été lu.

Une journée d’exemple particulièrement restrictive, dont les féculents n’étaient proposés que les jours de sport, a été retirée de l’écran Nutrition. Le texte indique désormais que la page ne prescrit ni menu, ni complément, ni répartition alimentaire. Aucune cible personnalisée ne peut être déduite sans profil validé, contexte de santé et avis approprié.

### Proposition nutritionnelle — non personnalisée

- Utiliser les objectifs saisis par la personne comme repères d’observation, pas comme diagnostic ni obligation quotidienne.
- Avant de conclure à une baisse de protéines ou de calories, vérifier que les repas saisis, portions, unités et aliments Ciqual sont complets.
- Conserver explicitement les inconnues et la provenance, ne pas « compléter » les traces par zéro, une marque générique ou une correspondance floue non confirmée.
- Ne pas proposer d’ajustement automatique des calories à partir d’un seul poids, d’un seul entraînement ou d’une dépense MET.
- Faire établir les cibles individuelles avec un professionnel qualifié si la personne présente une pathologie, un traitement, des symptômes persistants ou un besoin clinique.

## 6. Analyse sportive et proposition

### Code et calendrier

- Calendrier constaté : **A bas du corps lundi, rugby jeudi, B haut du corps vendredi**. Le tableau de bord compte maintenant les deux séances de renforcement distinctement du rugby ; ce calendrier est préservé.
- Le programme de renforcement présente trois blocs, trois tours et des repos configurables/proposés. Plusieurs variantes supposent du matériel (haltères, barre, chaise) et des capacités qui ne sont pas confirmées dans cet audit.
- L’adaptation se base sur le dernier ressenti, le RPE/difficulté, une réponse sur la réserve, le sommeil renseigné et le rugby récent. Elle propose des changements ; une adaptation n’est appliquée qu’après confirmation. Une douleur/gêne saisie bloque la proposition de renforcement.
- Ces signaux ne suffisent pas à mesurer la récupération, le maintien musculaire ou une blessure. Une traction ou un RPE isolé n’est pas un indicateur global.
- L’estimation rugby utilise `MET × poids × durée_en_heures`, les MET étant codés par type (touch 7, entraînement 7,5, match 8,3). Le code emploie la durée réelle validée et omet l’estimation si le poids manque ; l’ordre de grandeur reste fortement incertain et ne doit pas corriger l’alimentation.
- Le plan de répétitions n’est pas une trace des répétitions réellement faites. `enregistrer()` n’écrit pas ces propositions dans `workout_sets` ; c’est préférable à l’invention d’un volume, mais cela limite l’analyse de progression. De plus, le schéma suivi n’autorise que `A/B` alors que le rugby utilise `C` (R-04).

Les affirmations visibles garantissant que l’échauffement ou un exercice « évite » une blessure, prévient une tendinite, protège le dos ou conserve nécessairement le muscle ont été reformulées dans les descriptions concernées. Une revue humaine complète de tous les contenus sportifs reste requise.

### Proposition d’organisation, sans modifier le calendrier

1. **Lundi — renforcement A** : conserver un mouvement de squat, une charnière de hanche, un mouvement unilatéral et du tronc ; choisir une variante réellement maîtrisée et réduire le volume si la récupération n’est pas bonne.
2. **Jeudi — rugby** : considérer comme séance principale variable ; consigner durée effective, difficulté, RPE et gêne éventuelle. Ne pas convertir automatiquement l’estimation MET en calories alimentaires.
3. **Vendredi — renforcement B** : tirage, poussée, épaules et tronc ; garder le travail de jambes au repos si le rugby du jeudi l’exige, conformément au plan actuel.
4. **Progression** : modifier un seul paramètre après plusieurs séances consignées et tolérées. Les propositions algorithmiques ne remplacent ni l’auto-évaluation ni un avis professionnel ; arrêter ou adapter en cas de douleur inhabituelle/persistante.
5. **Récupération** : laisser les autres jours disponibles pour repos ou activité légère choisie. Aucun entraînement compensatoire n’est requis pour une séance manquée.

## 7. Tests exécutés et résultats

| Contrôle | Résultat local | Portée et limite |
|---|---|---|
| `node test_mobile.js` | **6/6** passent. | Tests JavaScript ciblés, `localStorage` simulé, pas de WebView Android réel. |
| `.venv/bin/python test_integrite.py` | **12/12** passent. | SQLite temporaire, intégrité profil/macros/unités et séances ; ne teste pas le schéma Supabase réel. |
| `.venv/bin/python test_app.py` | **10/10 pages** rendues sans exception. | Streamlit `AppTest`, SQLite jetable, mode mono-utilisateur test ; smoke test de rendu, pas tests complets d’interactions/permissions. Avertissements `ScriptRunContext` attendus en bare mode. |
| `.venv/bin/python -m compileall -q .` | Passe. | Syntaxe des modules Python. |
| `bash -n build.sh` | Passe. | Syntaxe shell seulement. |
| `git diff --check` | Passe après correction d’un espace final. | Hygiène diff. |
| `diff -qr app/src/main android/app/src/main` | Aucun écart. | Parité des deux sources Android locales. |
| Parse YAML PyYAML du workflow | Passe, 10 étapes dans le job. | Pas d’exécution GitHub Actions ; PyYAML 1.1 interprète `on` comme booléen dans sa représentation, sans erreur de syntaxe. |
| `bash build.sh` | **Non compilé** : SDK Android absent. | Aucun APK ni signature généré. Pas de compilation Gradle, émulateur ou téléphone. |

Le `AppTest` est un test de fumée : il confirme que les pages ne lèvent pas d’exception dans la configuration isolée, pas que tous les parcours affichent le contenu attendu sur Streamlit Cloud. Le contrôle d’intégrité du schéma et la validation de deux comptes restent à faire.

## 8. Changements locaux apportés pendant l’audit

- Refus de l’ouverture implicite du mode SQLite mono-utilisateur, de l’accès personnel sans clé/connexion et des objectifs personnalisés sur un profil incomplet.
- Champs perso/macro mobiles vides au premier lancement, préservation des anciennes saisies locales avec avertissement ; synchronisation explicitement désactivée et absence de promesse de partage offline.
- Prévention de l’enregistrement partiel du profil si la base refuse ses colonnes ; les données ne sont pas écrites pendant l’audit.
- Valeurs Ciqual « `< x` » et traces conservées comme inconnues ; unité vide non transformée arbitrairement en grammes ; tests de régression ajoutés.
- Suppression de l’exemple nutritionnel prescriptif de l’écran et reformulation de messages sportifs qui garantissaient un résultat de santé.
- Sources Android réconciliées, version cible Android portée à `1.0.13 / code 14`, trousseau par défaut rendu éphémère et aléatoire ; `.jks` ignoré par Git.
- Workflow GitHub : publication non automatique, entrée manuelle désactivée par défaut, blocage explicite tant que `APK_SYNC_READY=false`, permissions GitHub en lecture seule et trousseau de release prévu via secrets.
- README remis à jour ; l’audit 1.0.8 marqué comme historique.

Aucun changement n’a été apporté à `schema.sql`, aux données, aux permissions Supabase, aux objectifs personnels, aux comptes ou à une instance hébergée.

## 9. Version, livrables et limites de conclusion

La release distante lue via GitHub est [`v1.0.12`](https://github.com/flaviensaillard/suivi-recomposition/releases/tag/v1.0.12) (6 octobre 2026, `versionCode 13`). La branche locale cible `1.0.13 / 14` mais n’a produit aucun APK. `app.py` déclare encore `1.0.12` et plusieurs modules gardent des marqueurs plus anciens : la version Streamlit et la version Android ne sont pas harmonisées.

Références Ciqual : [documentation ANSES 2025](https://ciqual.anses.fr/cms/sites/default/files/inline-files/Table%20Ciqual%202025%20doc%20FR_2025_11_19.pdf) · [notice Data.gouv / DOI 10.57745/RDMHWY](https://entrepot.recherche.data.gouv.fr/dataset.xhtml?persistentId=doi%3A10.57745%2FRDMHWY).

### Ce que cet audit ne peut pas conclure

- que les politiques RLS et comptes du Supabase réel correspondent au `schema.sql` suivi ;
- que les menus partagés sont accessibles uniquement à la famille, ou que les suivis personnels sont isolés dans l’instance actuellement déployée ;
- que le profil réellement enregistré ou les objectifs actuels sont exacts ;
- que les ingrédients de production ont la même couverture que le JSON de démonstration ;
- qu’une APK se compile, s’installe, conserve les données après mise à jour ou fonctionne sur toutes versions Android ;
- qu’un futur mécanisme de synchronisation est résistant aux pertes, conflits, doublons et révocation d’accès.

**Verdict final :** Streamlit dispose d’une base de fonctions cohérente avec le produit familial souhaité, sous réserve de valider schéma et permissions réels. L’APK est un prototype local hors ligne, **pas encore le client hors ligne synchronisé demandé**. Pas de publication ni d’activation de synchronisation avant clôture des P0.
