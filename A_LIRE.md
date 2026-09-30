# 🎯 LES 5 FICHIERS À REMPLACER — version **2.8.8** (unité au choix)

Ta capture d'écran montre l'ancienne version (2.8.7) : la case **Unité** n'y est pas encore.
Voici **uniquement les fichiers qui ont changé**, rien d'autre à toucher.

---

## 1️⃣ GitHub — dépose ces **5 fichiers** dans ton dépôt `suivi-recomposition`

*(glisse-dépose sur la page du dépôt comme d'habitude : Add file → Upload files)*

| Fichier | Ce qu'il apporte |
|---|---|
| **editeurs.py** | ⭐ **la case « Unité »** dans Planifier la semaine + l'aperçu + ✏️ Modifier |
| **menus.py** | la liste des unités adaptée à chaque aliment + « Quantité (unité) » |
| **pdf_menus.py** | la fiche PDF respecte l'unité choisie |
| **repas_plats.py** | l'accueil (« Aujourd'hui ») affiche l'unité choisie |
| **app.py** | le numéro de version (bandeau 2.8.8) |

⚠️ **Les 5 ensemble** : ils vont par paire (editeurs ↔ menus ↔ pdf_menus).
Les 11 autres fichiers `.py` de ton dépôt **ne changent pas** : ne les touche pas.

Commit : **MAJ 2.8.8** → Commit changes.

---

## 2️⃣ Supabase — le fichier SQL n°23 (dans le dossier `2_SQL`)

**`23_unite_par_repas.sql`** → SQL Editor → New query → colle → **Run**.
🔎 Ligne 3 = **`--  >>> VERSION CORRIGÉE « 2.8.8 » — fichier 23 <<<`**
En bas : **« OUI ✅ »** = c'est bon. Il ne touche à aucune donnée, relançable.

*(Il sert à **retenir** l'unité choisie. Si tu ne le lances pas, tout marche quand même :
l'unité est recalculée automatiquement et l'application te le dit une fois.)*

---

## 3️⃣ Streamlit — **Manage app → ⋮ → Reboot app**, puis **F5**

Bandeau à vérifier : **éditeur 2.8.8 · menus 2.8.8**.

---

## 🔎 CE QUE TU DOIS VOIR MAINTENANT

Dans **📅 Planifier la semaine → Type = Ingrédient**, trois cases sur deux lignes :

```
Ingrédient   [ Cordon bleu                       ▾ ]
Quantité (unité)  [ 1,00 ]        Unité  [ unité ▾ ]
→ Ce repas demandera 1 unité à la liste de courses (≈ 226 kcal · 15 g de protéines)
```

- Le mot entre parenthèses **suit ton choix** : « Quantité (unité) », « Quantité (g) »,
  « Quantité (kg) »… Plus jamais « 1, mais 1 quoi ? ».
- La case **Unité** propose **les unités qui ont du sens pour l'aliment** :
  - **Cordon bleu** → unité, tranche, gousse, boîte, sachet, pot, portion
  - **Pâtes, Riz** → g, kg
  - **Lait, Crème** → ml, cl, l
  - **Steak haché** (125 g la pièce) → **unité** en premier : 4 = 4 steaks = 500 g
- Chaque changement **recalcule l'aperçu tout de suite**.
- **➕ Ajouter ce repas** enregistre **ton unité**, et **✏️ Modifier** la repropose.

---

## 🧪 Tests (faits avant de t'envoyer ce dossier)

- L'unité : page · base · liste de courses · fiche PDF · ✏️ Modifier · SQL absent → **34/34 ✅**
- Type / modification / convives → **25/25 ✅** · tes noms (« Steak haché ») → **14/14 ✅**
- Unités + recherche sans accent → **60/60 ✅** · fiche PDF → **33/33 ✅**
- Toutes les pages de l'application **passent ✅**
