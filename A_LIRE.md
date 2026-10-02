# 🧹 Équilibre 1.0.11 — **interface épurée** · mode opératoire

Le même grand nettoyage que sur le téléphone : les phrases qui expliquent comment
l'application marche ont été retirées, il ne reste que ce qui te sert. **La barre de
gauche est vidée** : plus de numéros de version de fichiers, plus de mode de stockage,
plus de phrases — juste tes menus, tes recettes, tes chiffres.

**Les descriptions des mouvements de tes séances sont conservées** (tu me l'as demandé).

| | |
|---|---|
| Version | **1.0.11** (petite ligne « v1.0.11 » en bas de la barre de gauche, dans ton espace) |
| Fichiers à copier | **4 fichiers** à la racine du dépôt : `app.py`, `editeurs.py`, `menus.py`, `repas.py` |
| Secrets | **rien à changer** |
| Ce qui ne bouge pas | tes données, tes clés, tes liens, l'espace partagé, l'espace de Léa |

---

## 1. Ce qui disparaît de ton écran

| Avant | Après |
|---|---|
| `éditeur 1.0.10 · menus 1.0.10` / `Supabase (synchronisé)` dans la barre de gauche | *(supprimé)* |
| « 👨‍👩‍👧‍👦 **Espace partagé** — recettes, menus et courses de la famille. Rien de personnel ici. » | *(supprimé)* |
| « 🔑 Je suis Flavien : revenir à mon espace » | *(supprimé)* |
| « Cette page lit ta base de menus, qui vit dans Supabase. Déploie l'application… » | « Cette page a besoin des clés Supabase (⚙️ Réglages). » |
| « Ta semaine de repas. Un repas peut être une recette, un ingrédient seul… » | *(supprimé)* |
| « Chaque ligne a sa liste déroulante : déroule-la et clique, ou tape « pates »… » | « 12 aliments — **tape pour chercher** dans la liste. » |
| « Ces chiffres viennent directement de ta base Supabase, en direct. » | *(supprimé)* |

**Total : 46 textes retirés ou raccourcis** dans la barre de gauche, le tableau de bord,
la pesée, la nutrition, les menus, la planification, les recettes et les ingrédients.

⚠️ **Comment revenir dans ton espace** depuis l'espace partagé (le bouton a été retiré) :
utilise **ton lien personnel** — celui qui finit par `?cle=…`, celui que tu as mis en
favori. C'est aussi celui que tu peux retrouver dans ⚙️ **Réglages**.

---

## 2. Ce qui est GARDÉ (exprès)

- **toutes les descriptions des mouvements** de tes séances ;
- **tes chiffres** : objectifs, protéines, glucides, lipides, calories, poids, masse grasse
  en kg **et** en % ;
- **les avertissements utiles** : journée déjà notée (« rien n'a été écrasé »), masse grasse
  sans poids, aliments sans valeurs, mode local, clés manquantes ;
- **les messages d'erreur** en français, avec quoi faire ;
- la case **Convives sans plafond** et la carte **⭐ Mes repas types**.

---

## 3. Installation (clic par clic)

1. **github.com** → dépôt `suivi-recomposition`.
2. Pour **chacun des 4 fichiers** (`app.py`, `editeurs.py`, `menus.py`, `repas.py`) :
   crayon **✏️** → **Ctrl+A** → supprimer → coller le nouveau → **Commit changes**.
   *(Si tu n'as pas encore installé la 1.0.9 : prends aussi son `content.py` dans
   `MAJ_1.0.9/`. Les autres fichiers sont déjà à jour.)*
3. **share.streamlit.io** → **Manage app** → **⋮** → **Reboot app**.
4. Navigateur : **Ctrl+Maj+R**.
5. **Vérifier** : « **v1.0.11** » en bas de la barre de gauche, et une barre de gauche
   **vide de tout texte technique**.

---

## 4. Empreintes (les fichiers livrés sont ceux qui ont été testés)

| Fichier | MD5 |
|---|---|
| `MAJ_1.0.11/app.py` | `47958cfea79dec74e31cdbdb1c80d62e` |
| `MAJ_1.0.11/editeurs.py` | `cfedbdb5c41a8d0c00b3cf35e26c6c2f` |
| `MAJ_1.0.11/menus.py` | `6b8f367108e14ab4c79bc9f13d9bcd35` |
| `MAJ_1.0.11/repas.py` | `d3101c6ca2197df8b87b68c1f11ac783` |
| `MAJ_1.0.11/MAJ_1.0.11.zip` | *(voir le message d'accompagnement)* |

---

## 5. Ce qui a été vérifié avant de te livrer ça

- **les 9 pages** de l'application : aucune exception, aucun message d'erreur ;
- **connexion** (6 vérifications), **espace partagé** (8 vérifications), **espaces séparés**
  (tes données jamais chez Léa, les siennes jamais chez toi), **tableaux et masse grasse**
  (12), **repas types** (35), **convives sans plafond** (28) — toutes vertes ;
- **17 fichiers Python** recompilés un par un : 0 erreur ;
- contrôle des **blocs vides** et des **variables orphelines** après nettoyage : aucun.

---

## 6. Rappel

- **Le téléphone** a droit au même nettoyage : livraison **`TELECHARGER_APK_Equilibre_1.0.10.zip`**.
- Si un texte te manque, dis-le : je le remets en une ligne.
