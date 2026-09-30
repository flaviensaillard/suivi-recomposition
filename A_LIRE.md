# ⚖️ **ÉQUILIBRE** — version **1.0.1**
## Le mercredi ne s'ouvre plus tout seul (et deux petits plus)

**Correctif rapide.** Tu remplaces les **5 fichiers `.py`**, tu appuies sur **F5**,
c'est fini. **Le logo ne change pas** : `equilibre.png` reste celui de la 1.0,
tu n'as rien à refaire de ce côté. **Aucun SQL à lancer.**

---

## 🆕 Ce qui change

### ① Les 7 jours arrivent tous repliés ⭐ (ta remarque)
Avant, le jour d'aujourd'hui s'ouvrait automatiquement — c'est ce que tu as vu
avec le mercredi. **Maintenant les 7 jours sont fermés**, et c'est toi qui ouvres
celui que tu veux remplir. Pour ne pas le chercher, aujourd'hui est simplement
**signalé dans son titre** :

```
▸ Mercredi 30/09  ·  aujourd'hui — 3 repas      ← fermé, comme les autres
▸ Jeudi 01/10 — 1 repas
▸ Vendredi 02/10 — 2 repas
▸ Samedi 03/10 — 0 repas
▸ Dimanche 04/10 — 0 repas
▸ Lundi 05/10 — 0 repas
▸ Mardi 06/10 — 0 repas
```

La semaine se lit donc d'un seul coup d'œil, du premier au dernier jour.

### ② Le résumé de la semaine ne débordait plus…
Sur ta capture, la ligne **« À compléter »** était coupée par le bord de la page
(« … Dim 04/… »). C'est corrigé : le compteur affiche un **nombre**
(`Jours à compléter : 5 / 7`) et la liste des jours s'écrit **en entier juste en
dessous**, chaque jour en gras :

> Il manque des protéines le **Mer 30/09**, **Jeu 01/10**, **Ven 02/10**,
> **Sam 03/10**, **Dim 04/10**. Prévois un en-cas : shaker, œufs durs, skyr (20 à 30 g).

### ③ Les boutons prennent la couleur du logo
Le bouton rouge « Ajouter ce repas » (c'était la couleur par défaut de Streamlit)
passe au **vert d'Équilibre**, comme la balance. Tout est cohérent maintenant.
*(Si tu préférais le rouge, dis-le-moi : c'est une ligne à changer.)*

---

## 1️⃣ GitHub — remplace ces **5 fichiers** dans `suivi-recomposition`

**Add file → Upload files** → glisse les 5 fichiers du dossier
(*pas de sous-dossier, pas de zip à ouvrir*) → **Commit changes** : « Équilibre 1.0.1 ».

| Fichier | Ce qu'il apporte |
|---|---|
| **editeurs.py** | ⭐ **les 7 jours repliés** + le résumé de la semaine réparé |
| **app.py** | la couleur des boutons (le vert du logo) + le numéro 1.0.1 |
| **menus.py** | le numéro de version (pour le contrôle) |
| **pdf_menus.py** | le numéro de version (pour le contrôle) |
| **repas_plats.py** | le numéro de version (pour le contrôle) |

> Les 4 derniers ne changent que par leur numéro de version : ils servent à ce que
> l'application **te dise** qu'elle tourne bien sur la 1.0.1.

**`equilibre.png` : à ne pas toucher**, il est déjà bon.

## 2️⃣ Streamlit — **F5**

En bas de la barre de gauche tu dois lire :

```
Équilibre  v1.0.1
éditeur 1.0.1 · menus 1.0.1
```

Si tu lis encore **1.0** : **Manage app → ⋮ → Reboot app**, puis **F5**.

---

## 🧪 Tests (avant de t'envoyer ce dossier — **33 verts, 0 échec**)

- **Nouveau test « les 7 jours s'ouvrent repliés » → 10/10 ✅**
  Il regarde l'**état réel** envoyé au navigateur (pas seulement le code) :
  les 7 jours sont là, **les 7 sont fermés**, aujourd'hui est signalé sans être
  ouvert, **et ça reste vrai quand tu décales « Premier jour affiché » d'une
  semaine**. C'est ce test qui empêchera le problème de revenir.
- **Toute la batterie** (widget dans un navigateur simulé 29/29, recherche unique,
  unités, convives, courses, PDF, séances, tableaux, objectifs, éditeurs,
  solidité 22/22…) → **repassée intégralement ✅**
- Les 10 pages s'ouvrent sans erreur avec ta vraie base (158 aliments, 104 recettes,
  79 repas) → **10/10 ✅**

## 🆘 Si quelque chose cloche

| Ce que tu vois | Ce que tu fais |
|---|---|
| les jours s'ouvrent encore tout seuls | **Reboot app** (Manage app → ⋮) puis **F5** |
| version encore 1.0 en bas à gauche | tu as oublié un fichier : vérifie les 5 |
| un bouton encore rouge | dis-le-moi : je regarde le thème de ton déploiement |
