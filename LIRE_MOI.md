# 🔧 CROIX ❌ — 3 fichiers à recopier (5 minutes)

## Pourquoi ça ne marchait pas

Ta capture le prouve : **le fichier `editeurs.py` de ton GitHub est resté l'ancien.**
*(sur ton écran : le nom de l'ingrédient s'affiche en texte simple, et la quantité « 0,00 » —
c'est l'ancien éditeur ; le nouveau propose une liste déroulante et une case « base française »)*

L'application (v2.8) est bien à jour, mais **l'éditeur, lui, ne l'est pas** : donc la croix
n'a aucun effet, et tu ne peux pas supprimer un ingrédient.

## Ce que j'ai fait en plus

1. **La croix supprime maintenant TOUT DE SUITE** : plus besoin de cliquer sur « 💾 Enregistrer »,
   la ligne part vraiment de ta base, avec un message vert **« ✅ Ligne supprimée de la recette »**.
2. **La barre de gauche affiche les versions** des fichiers :
   `v2.8 · éditeur 2.8 · menus 2.8`
   Si tu lis `éditeur ancien`, c'est que le fichier n'a pas été remplacé.
3. **Un bandeau rouge s'affiche** en haut de l'écran Recettes si un fichier est resté ancien,
   avec la marche à suivre exacte.

## À faire (2 étapes seulement)

**1. GitHub** → github.com → ton dépôt **suivi-recomposition** → bouton **Add file** →
**Upload files** → fais glisser **les 3 fichiers** de ce dossier (`app.py`, `editeurs.py`, `menus.py`)
→ en bas, écris « Mise a jour editeurs 2.8 » → **Commit changes**.

> Si GitHub affiche les 3 fichiers en **rouge**, c'est qu'ils ne portent pas le bon nom :
> ils doivent s'appeler exactement `app.py`, `editeurs.py`, `menus.py`.

**2. Streamlit** → share.streamlit.io → ton application → **Manage app** (en bas à droite) →
**⋮** (en haut à droite du panneau) → **Reboot app** → puis **F5** dans le navigateur.

## Vérifie en 20 secondes

- En bas de la barre de gauche, tu dois lire : **`éditeur 2.8 · menus 2.8`**.
- 📖 **Recettes** → *Modifier une recette* → en haut de la liste des ingrédients, il y a
  maintenant la case **« 🌍 Proposer aussi la base française »** = bon fichier. ✅
- **Clique sur une ❌** : la ligne disparaît et un message vert confirme la suppression.
  Recharge la page (F5) : la ligne ne revient pas.

## Ce que j'ai testé avant de te l'envoyer

| Test | Résultat |
|---|---|
| Ajouter une ligne « Riz » puis cliquer sur sa ❌ | ligne retirée de l'écran ✅ |
| Cliquer sur la ❌ d'une vraie ligne de ta recette | retirée de l'écran **et de la base** (331 → 330 lignes) ✅ |
| Recharger l'écran (comme un F5) | la ligne **ne revient pas** ✅ |
| Message de confirmation | « ✅ Ligne supprimée de la recette (c'est enregistré). » ✅ |
| Bandeau si le fichier est ancien | s'affiche bien, avec la marche à suivre ✅ |
| Les 12 autres tests de l'application | tous verts ✅ |

Rien d'autre n'a changé : tes recettes, ton planning, tes pesées et tes séances ne sont pas touchés.
