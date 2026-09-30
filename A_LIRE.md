# ⚖️ **ÉQUILIBRE** — version **1.0**
## « Suivi Recomposition » change de nom, et devient une application finie

**Six fichiers à déposer sur GitHub** (les 5 programmes + le logo), **puis F5**.
C'est tout. Aucun fichier SQL à lancer pour cette mise à jour.

---

## 🆕 Ce qui change dans cette 1.0

### ① Le nom et le logo
L'application s'appelle **Équilibre** — la balance, parce que c'est ton objectif :
perdre le gras **sans** perdre le muscle. Nouvelle icône (la balance) dans la barre
de gauche, dans l'onglet du navigateur et **sur l'écran de ton téléphone**.

### ② Les Réglages sortent du sous-dossier
Fini le dossier « ⚙️ Réglages » avec un seul élément dedans : **Réglages** est
maintenant **au même niveau** que Nutrition, Mensurations… et **toujours en dernier**.

```
👨‍👩‍👧‍👦 Menus & courses (partagé)     👤 Mon suivi (personnel)
   🍽️ Repas & menus                     🏠 Tableau de bord
   📅 Planifier la semaine              ⚖️ Pesée & tendance
   🥣 Recettes                          💪 Mes séances
   🥕 Ingrédients                       🥗 Nutrition
                                        📏 Mensurations
                                        ⚙️ Réglages   ← ici, en dernier
```

### ③ Le bouton « Ouvrir Menus & recettes » est supprimé
Tu ne l'utilisais pas : il a disparu de la barre de gauche.

### ④ La version PC, retravaillée
- **Page plus large** (1 080 px au lieu de 900) : les chiffres respirent, les
  tableaux ne sont plus tassés.
- **« Modifier / Créer » ressemblent à de vrais boutons** : celui qui est actif est
  encadré en vert — on voit tout de suite où on est.
- **Le « appuyez sur Entrée » a disparu** : tout réagit *pendant* la frappe.
- **Les tableaux et les cadres** sont arrondis et lisibles.
- **La page Nutrition est réorganisée** : en haut ce qui sert tous les jours
  (tes compteurs, tes 3 façons d'ajouter un repas), et les moyennes 7 / 30 jours
  descendent dans un cadre replié en bas — c'était du texte qui t'obligeait à
  scroller avant d'atteindre les boutons utiles.
- **La page d'accueil** affiche chaque plat sur une ligne claire
  (`Midi · 4 personnes · 420 kcal et 32 g de protéines par part`), et un lien
  direct vers ce que ça demande à tes courses.
- **Réglages** : un seul bouton « 🗓️ Tout d'un coup (ZIP) » ou **chaque table en
  CSV direct**, plus le nombre de lignes affiché d'un coup d'œil.

### ⑤ Le ménage dans les textes
Toutes les phrases d'outil ont été enlevées des pages : plus de
« lance le script 7_nutrition.sql », plus de « Streamlit garde les fichiers en
mémoire », plus de « bug corrigé en 2.8.4 ». Il ne reste que ce qui **te sert
pendant que tu utilises l'application**.
Les nombres ne sont plus écrits en dur : l'application **compte tes aliments en
direct** (le fameux « 3 200 aliments » s'adapte tout seul).

### ⑥ Deux bugs corrigés (trouvés par le nouveau test de solidité)
- **Réglages** : si une ancienne valeur enregistrée sortait des bornes (par
  exemple 0 kcal), **la page entière refusait de s'afficher**. Corrigé : toutes
  les valeurs de la base sont désormais ramenées dans les bornes — 15 endroits.
- **Journal incomplet** : si une colonne manquait dans une ancienne base, la page
  s'arrêtait. Corrigé : colonnes garanties, lecture sans risque partout.

---

## 1️⃣ GitHub — dépose ces **6 fichiers** dans `suivi-recomposition`

**Add file → Upload files** → glisse les 6 fichiers du dossier
(*pas de sous-dossier, pas de zip à ouvrir*) → **Commit changes** : « Équilibre 1.0 ».

| Fichier | Ce qu'il apporte |
|---|---|
| **app.py** | le nom, le logo, la mise en page PC, les Réglages remontés |
| **menus.py** | les textes + les garde-fous de calcul |
| **editeurs.py** | les écrans Planifier / Recettes / Ingrédients affinés |
| **repas_plats.py** | la page d'accueil « Repas & menus » |
| **pdf_menus.py** | la fiche PDF + son numéro de version |
| **equilibre.png** | ⭐ **le logo** (nouveau : il n'y en avait pas avant) |

Les 11 autres fichiers `.py` de ton dépôt **ne changent pas**.

> ⚠️ **Le logo est un fichier en plus** : c'est le seul de cette mise à jour.
> Si tu l'oublies, l'application marche quand même — elle affiche juste ⚖️ au lieu
> de la balance dessinée.

## 2️⃣ Streamlit — **F5**

En bas de la barre de gauche tu dois lire :

```
Équilibre  v1.0
éditeur 1.0 · menus 1.0
```

Si tu lis encore **2.9.3** : **Manage app → ⋮ → Reboot app**, puis **F5**.

## 3️⃣ Sur ton téléphone (2 minutes, pour le logo)
Ouvre l'adresse de l'application dans Chrome → **⋮** → *Ajouter à l'écran d'accueil*.
Tu auras la balance en icône, et l'application s'ouvrira en plein écran.

**Aucun fichier SQL à lancer.** Tes recettes, tes menus, tes courses, tes séances,
tes objectifs et tes données ne bougent pas d'un chiffre.

---

## 🧪 Tests (faits avant de t'envoyer ce dossier — **32 verts, 0 échec**)

- **Toute la batterie** (widget, recherche, unités, convives, courses, PDF,
  séances, tableaux, objectifs, noms de courses, jours, éditeurs) → **repassée
  intégralement ✅**
- **La liste qui cherche** pilotée dans un navigateur simulé → **29/29 ✅**
  · filtre identique à l'application (JS = Python) → **26/26 ✅**
- **Le widget est vraiment servi** par Streamlit (HTTP 200, 16 040 octets) → **14/14 ✅**
- 🆕 **Solidité** : base vide, objectifs à zéro, colonnes manquantes, recette sans
  parts, aliment sans valeurs, planning en 2030 → **22/22 ✅**
  *(c'est ce test qui a débusqué les deux bugs corrigés ci-dessus)*
- Les 10 pages s'ouvrent sans erreur, avec la vraie base (158 aliments, 104 recettes,
  79 repas) → **10/10 ✅**

## 🆘 Si quelque chose cloche

| Ce que tu vois | Ce que tu fais |
|---|---|
| l'ancien écran, version 2.9.3 | **Reboot app** (Manage app → ⋮) puis **F5** |
| pas de logo, juste ⚖️ | vérifie que **equilibre.png** est bien sur GitHub, à côté de `app.py` |
| un texte bizarre ou une erreur | envoie-moi une capture : le cadre « Détail » contient tout ce qu'il me faut |
