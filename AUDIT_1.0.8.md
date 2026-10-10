# 🔍 Audit historique d'Équilibre — deux passages, 1ᵉʳ octobre 2026

> ⚠️ **Document périmé pour le checkout actuel.** Ce rapport décrivait un autre état du code, des fichiers livrés et de la base le 1ᵉʳ octobre 2026. Il n'est pas une preuve de l'état actuel et ses déclarations (« rien de bloquant », architecture Android, tests, accès Supabase et livraisons) ne doivent pas être reprises sans nouvelle vérification. Voir [`AUDIT_COMPLET_2026-10-10.md`](AUDIT_COMPLET_2026-10-10.md).

**Verdict : rien de bloquant, rien de cassé. 6 défauts trouvés — dont un qui pouvait
faire perdre une journée de saisie, et un qui laissait ta clé de signature Android
traîner dans une archive. Tous corrigés, puis tout a été re-testé.**

| | |
|---|---|
| Portée | 17 modules Python · l'application Android (Kotlin/Compose) · la base Supabase réelle · les archives livrées (.zip, .apk) |
| Tests exécutés | **5 batteries** · **65 pages × situations** · **295 vérifications Kotlin** · mesures de sécurité sur la **vraie base** |
| Résultat | 0 exception, 0 page vide, 0 message d'erreur ; 6 défauts corrigés ; 4 risques assumés documentés |
| Livraisons vérifiées | ordinateur **1.0.8** (6 fichiers) · Android **1.0.7** (durcie) |

> Les deux passages ont été faits séparément : le premier sur l'ensemble du code et de
> la base, le second **sur les fichiers réellement téléchargeables** (archives, APK,
> cohérence des numéros de version). C'est le second passage qui a révélé le défaut ⑥.

---

## 1. Ce qui a été testé, et comment

### A. Les 5 batteries (toutes les pages, dans 4 situations)

| Batterie | Contenu | Résultat |
|---|---|---|
| `audit_complet` | 10 pages × **historique** / **compte neuf** / **hors ligne** + 4 pages partagées | **34/34 ✅** |
| `test_kg_tableaux` | masse grasse en kilos, dates, corrections dans les tableaux | **11 ✅** |
| `test_identif_auto` | clé dans l'adresse, écran de connexion, refus expliqués | **6 ✅** |
| `test_partage` | espace du foyer sans compte, priorité du lien perso | **8 ✅** |
| `test_espaces` | isolation Léa / Flavien, pages filtrées | **tout est bon** |

Chaque page est vérifiée sur **deux critères** : aucune erreur affichée **et** du
contenu réellement rendu (textes, tableaux, champs, onglets). Une page qui « ne
plante pas mais n'affiche rien » est maintenant signalée — c'est un contrôle que le
premier passage ne faisait pas.

### B. Le code

| Contrôle | Résultat |
|---|---|
| Compilation des 17 modules | ✅ aucun ne casse |
| Fonctions dangereuses (`eval`, `exec`, `os.system`, `subprocess`, `pickle`) | ✅ **aucune** |
| HTML brut : 4 emplacements (style fixe, nom + version, noms d'exercices) | ✅ **aucune donnée saisie n'y entre** |
| SQL assemblé à la main | ✅ listes blanches internes, jamais de valeur utilisateur concaténée |
| Cohérence des numéros de version (fichier ↔ attendu par l'application) | ✅ les **8 fichiers surveillés concordent** |
| Fichiers de secrets dans les archives livrées | ✅ **aucun** |

### C. Tes données, mesurées sur la vraie base (lecture seule)

| Mesure | Résultat |
|---|---|
| Aliments | **161** · protéines **100 %** renseignées · lipides **100 %** · glucides **98,8 %** |
| Les 2 seuls trous | *Huile de tournesol* et *Reblochon* — **Ciqual lui-même les laisse vides** : l'huile (0 g de glucides par nature) et le reblochon (≈ 0,5 g/100 g, soit ~0,2 g par portion) |
| Recettes / ingrédients / repas planifiés | 105 · 333 · 79 lignes, lisibles (c'est le foyer partagé, voulu) |
| Tes 6 tables personnelles, lues **avec la seule clé publique** | 🔒 **0 ligne** sur les 6 |
| Écriture anonyme sur les 6 tables personnelles | 🛑 refusée **6/6** — `401` · `42501 row-level security policy` |

**Conséquence directe** : l'avertissement « moins de la moitié de tes aliments ont des
valeurs » **ne se déclenche pas** chez toi (100 % renseigné). Il n'apparaît que si
l'application tourne **sans aucune base branchée**, sur le jeu de démonstration — et
elle le dit alors elle-même à l'écran (« Mode aperçu »). Rien à corriger.

### D. Les fichiers téléchargeables

| Contrôle | Résultat |
|---|---|
| `unzip -t` sur les 3 archives | ✅ « no errors detected » |
| Le zip web contient-il **exactement** mes fichiers testés ? | ✅ **identiques octet pour octet** (comparaison 1 à 1) |
| Secrets / keystores / mots de passe dans les archives | ✅ **aucun** (voir défaut ⑥) |
| Version inscrite dans l'APK | ✅ `versionCode 8` · `1.0.7` · et l'APK **attend bien le web 1.0.8** |
| APK livré = APK compilé | ✅ `03e71bcc…760c`, même clé de signature que les versions précédentes |

### E. Android

| Contrôle | Résultat |
|---|---|
| Banc de tests | ✅ **295/295** (272 + 23 session) |
| Permissions | ✅ INTERNET · ACCESS_NETWORK_STATE · USE_BIOMETRIC (+ empreinte système). Rien d'autre |
| Sauvegarde automatique | ✅ désactivée (`allowBackup=false` + règles Android 12+) |
| Déconnexion | ✅ efface le jeton du téléphone |
| Mot de passe sur le téléphone | ✅ jamais écrit |
| Identifiants de test dans le code compilé | ✅ aucun |

---

## 2. Les 6 défauts trouvés — et corrigés

### ① 🔴 Déplacer une journée sur une date **déjà remplie** écrasait la journée d'arrivée
La base range les journées par *(compte, date)* : en changeant la date vers un jour
occupé, l'application recopiait par-dessus puis supprimait l'original — **les données
d'arrivée disparaissaient sans un mot**.
**Corrigé** : la correction est **refusée**, avec l'explication et la marche à suivre
(« coche 🗑️ sur cette journée-là pour la supprimer d'abord »). Même garde-fou pour
les **mensurations**. *Vérifié : les valeurs de la journée et de la mensuration
d'arrivée restent intactes.*

### ② 🟠 Masse grasse en kilos sur une journée **sans poids** : la correction disparaissait
La conversion kilos → % a besoin du poids du jour ; sans lui, la correction était
**ignorée en silence**.
**Corrigé** : message clair — « il faut d'abord le poids de cette journée ».

### ③ 🟠 Le bandeau « fichier d'avant » se trompait dans les deux sens
Il comparait les versions **par égalité** : un fichier *plus récent* déclenchait une
fausse alerte, et les 4 fichiers « socle » n'étaient **pas surveillés** — un fichier
oublié lors d'une mise à jour aurait dégradé l'application sans rien dire.
**Corrigé** : comparaison *plus ancien / plus récent*, et **8 fichiers suivis**, chacun
portant son numéro de version. *Vérifié : silence total quand tout est à jour ;
message explicite si l'on remet volontairement un fichier en arrière.*

### ④ 🟡 `requirements.txt` autorisait un Streamlit trop ancien pour le code livré
(`>=1.40` alors que le code utilise `st.context.headers`, `width="stretch"`…). Sur une
reconstruction de l'environnement, l'application aurait pu ne plus démarrer.
**Corrigé** : `streamlit>=1.50`.

### ⑤ 🟠 Android : le jeton de session pouvait partir dans la sauvegarde du téléphone
**Corrigé** : sauvegarde **et** transfert désactivés. *Contrepartie assumée : retaper
ton adresse une fois sur un nouveau téléphone (aucune donnée de suivi concernée).*

### ⑥ 🔴 **L'archive du code source Android contenait ta clé de signature**
Trouvé au second passage, dans le fichier `source_android_1.0.7.zip` :
`equilibre.jks` **et deux autres keystores**, plus `signature.properties` où le
**mot de passe de la clé était écrit en clair**. Un zip qui circule (mail, clé USB,
cloud) transportait donc de quoi **signer une fausse mise à jour** que ton téléphone
aurait acceptée comme la vraie.
**Corrigé** : archive **reconstruite sans aucun fichier de clé** (vérifié : plus de
`.jks`, plus de keystore, plus de fichier de mots de passe). La clé reste rangée dans
l'atelier — demande-la si tu veux la conserver hors ligne.
*Remarque* : le fichier de compilation portait encore le mot de passe *par défaut* ;
sans la clé il est inutilisable, et je le changerai lors de la prochaine compilation.

### Améliorations d'outillage (pour que ces erreurs ne se reproduisent pas)
- L'audit impose désormais son dossier de travail : lancé d'ailleurs, il testait
  silencieusement **tout en mode « aucune base branchée »** (donc sur la démonstration)
  et pouvait annoncer des « écarts » qui n'en étaient pas.
- Les 4 batteries imposent aussi leur dossier, et l'audit **compte le contenu affiché**
  page par page.

---

## 3. Sécurité de ta base : mesuré, pas supposé

Mesures faites avec **la seule clé publique** de l'application, telle qu'elle se trouve
dans l'APK — donc exactement ce que pourrait tenter un inconnu — et **sans jamais
écrire** (les tentatives d'écriture sont des requêtes vides ou visent des identifiants
inexistants : mesuré, `0 ligne` touchée).

| Table | Un inconnu peut lire | Un inconnu peut écrire |
|---|---|---|
| `ingredients` · `recipes` · `recipe_ingredients` · `planned_meals` | ✅ oui — **c'est l'espace du foyer, voulu** | ✅ oui |
| `sr_protein_entries` · `sr_daily_logs` · `sr_measurements` · `sr_workouts` · `sr_profiles` · `sr_shopping_state` | 🔒 **0 ligne** | 🛑 **refusé** (`42501`) |

**En clair** : ta partie personnelle n'est pas protégée par un écran de l'application
(un écran se contourne) mais **par la base elle-même**. Et chaque ligne porte
l'identifiant de son compte : Léa ne peut pas voir tes pesées, ni toi les siennes.

Ailleurs : mots de passe dans les **Secrets** Streamlit (jamais dans GitHub, jamais
dans une livraison) · ta clé personnelle comparée à temps constant, jamais écrite ·
espace partagé **sans** ton prénom, ton objectif ni aucune de tes lignes · HTTPS
partout.

---

## 4. Les risques assumés (je ne peux pas les supprimer : ce sont des choix)

1. **La base recettes/menus/courses est ouverte** — c'est ton choix (« le partagé
   suffit ») : qui a l'adresse peut lire **et modifier** les recettes du foyer. La
   parade est à un clic : `share.streamlit.io` → ton application → **⋮ → Settings →
   Sharing** → **privée** + **inviter l'adresse de Léa** (elle reçoit un lien magique
   une fois, puis seules les personnes invitées atteignent l'application).
2. **Ta clé personnelle voyage dans l'adresse** — si tu crains qu'elle ait fuité :
   change la ligne `cle` dans les Secrets, **Reboot**, refais ton favori.
3. **Le mot de passe du compte de Léa est dans les Secrets** — inévitable pour
   l'entrée automatique : ne réutilise pas un mot de passe sensible pour ce compte.
4. **Deux limites que je ne peux pas lever moi-même** : son compte n'existe pas encore
   (je vérifie l'isolation sur un Supabase simulé à deux comptes), et le bac à sable
   n'est pas Streamlit Cloud (les paquets se mettront à jour au redémarrage).

---

## 5. Ton contrôle final en 5 minutes (quand tout sera installé)

| # | Ce que tu fais | Ce que tu dois voir |
|---|---|---|
| 1 | Ouvre **ton** lien perso | tu es chez toi : **Mes séances**, ton objectif, tes données |
| 2 | ⚖️ Pesée | la case dit **« Masse grasse (kg) »**, la conversion en % juste dessous |
| 3 | Change la date d'une journée vers une date **déjà remplie** | **refus** — « rien n'a été écrasé… » ✅ |
| 4 | Corrige un poids → **💾 Enregistrer** | message vert, la valeur reste à la réouverture |
| 5 | Ouvre **son** lien (navigation privée) | pas de « Mes séances », aucun de tes chiffres |
| 6 | Ouvre `…?partage=1` (navigation privée) | 🍽️ Repas & menus, aucune page personnelle |
| 7 | Téléphone → ➕ Plus → Réglages | « **Suivi de mes séances** » présent ; coupé, l'onglet 💪 disparaît |

**Un point ne colle pas ? Dis-le moi avec la phrase exacte affichée** : j'ai des tests
écrits pour chacun de ces sept points.

---

## 6. Ce qu'il faut installer (et rien d'autre)

| Livraison | Fichiers | Où |
|---|---|---|
| **Ordinateur 1.0.8** | `app.py`, `content.py`, `corrections.py`, `db.py`, `tableaux.py`, `requirements.txt` | GitHub → **remplacer les 6** → **Reboot app** → **Ctrl+Maj+R** |
| **Android 1.0.7** | `Equilibre-Android-1.0.7.apk` | installer **par-dessus** (mise à jour, rien à retaper) |

**Empreintes des fichiers livrés** (vérifiées une à une après assemblage) :

| Fichier | MD5 |
|---|---|
| `MAJ_1.0.8/app.py` | `9bb006fc16c5ceb1ab06a6ab39b94e0e` |
| `MAJ_1.0.8/content.py` | `934371530a70896f9f2c8791275eed54` |
| `MAJ_1.0.8/corrections.py` | `8ffccb4c833693ce8055be8403fe9740` |
| `MAJ_1.0.8/db.py` | `10f5f37af77a18fdc1e48798df8cf4a1` |
| `MAJ_1.0.8/tableaux.py` | `635bd0964227f3a089c8a9e905066f2b` |
| `MAJ_1.0.8/requirements.txt` | `66e7f78c7b8921fbce604ca6efe3e1bf` |
| `APK_1.0.7/Equilibre-Android-1.0.7.apk` | `03e71bccfb08a6a28e7144a82b87760c` |
| `APK_1.0.7/source_android_1.0.7.zip` | `53f26fcc53e77b182376e62bf83eb76a` |

> L'empreinte **des archives .zip** téléchargeables est donnée dans mon message : elle
> change dès qu'un fichier du zip est retouché, donc elle ne peut pas figurer dedans.

⚠️ **L'APK 1.0.6 annoncée précédemment est retirée** : c'est la **1.0.7** qu'il faut
installer (même clé de signature → mise à jour par-dessus, sans désinstaller).

---

## 7. Ce qui n'a pas été touché (volontairement)

- **Tes données** : aucune écriture, aucune suppression, aucun changement de structure.
- **Les réglages Supabase** : ni « Confirm email », ni les politiques RLS, ni les comptes.
- **Le logo, les couleurs, les écrans, les calculs** : identiques.
