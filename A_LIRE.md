# Équilibre 1.0.10 — **le nombre de convives n'a plus de plafond** · mode opératoire

Tu ne pouvais pas faire tes menus de la semaine pour plus de 12 personnes : la case
**« Convives »** s'arrêtait à 12. C'est corrigé, **sur l'ordinateur comme sur le
téléphone** — et j'ai trouvé deux autres endroits où le même plafond se cachait.

| | |
|---|---|
| Version | **1.0.10** (en bas de la barre de gauche) |
| Fichiers à copier | **3 fichiers** à la racine du dépôt : `app.py`, `editeurs.py`, `menus.py` |
| Secrets | **rien à changer** |
| Ce qui ne bouge pas | tes données, tes clés, tes liens, l'espace partagé, l'espace de Léa |

---

## 1. Ce qui était bloqué à 12 (il y avait trois endroits, pas un)

| Endroit | Ce que ça faisait |
|---|---|
| **① La case « Convives »** de 📅 Planifier la semaine | Impossible de monter au-dessus de 12 : la case refusait 13, 20, 40… |
| **② La fenêtre « ✏️ Modifier »** d'un repas déjà prévu | Même plafond, donc impossible de dire « finalement on est 20 » |
| **③ Le calcul des quantités** (le plus sournois) | Un aliment noté « **20 convives** » comptait **0 g** dans la liste de courses : au-delà de 12 portions, mon calcul ne prenait plus la quantité et achetait… rien. Tu ne le voyais pas dans la case : ça se passait dans le calcul, en silence |

Et une cerise : « **1 convive** » d'un aliment comptait aussi **0 g** (le calcul
démarrait à 2). Un repas pour une personne n'achetait rien. Réparé en même temps.

---

## 2. Ce que tu peux faire maintenant

Dans 📅 **Planifier la semaine**, la case **« Convives »** accepte **n'importe quel
nombre** : 15, 20, 40, 60, 200… Tape-le ou utilise les flèches, il n'y a plus de
plafond. Idem dans **✏️ Modifier** pour un repas déjà prévu, et dans la liste de
courses : 20 convives de pâtes achètent maintenant **20 × 80 g = 1,6 kg** (avant :
0 g).

Le texte d'aide de la case le dit maintenant en clair : *« Aucun plafond : mets le
nombre que tu veux. »*

---

## 3. Installation (clic par clic)

1. **github.com** → dépôt `suivi-recomposition`.
2. Pour **chacun des 3 fichiers** (`app.py`, `editeurs.py`, `menus.py`) : crayon **✏️**
   → **Ctrl+A** → supprimer → coller le nouveau → **Commit changes**.
3. **Si tu n'as pas encore installé la 1.0.9** (les repas types sur l'ordinateur) :
   prends aussi son **`content.py`** dans le dossier `MAJ_1.0.9/` — c'est lui qui
   contient les trois repas types. Les trois autres fichiers de la 1.0.9 sont déjà
   remplacés par ceux-ci.
4. **share.streamlit.io** → **Manage app** → **⋮** → **Reboot app**.
5. Navigateur : **Ctrl+Maj+R**.
6. **Vérifier** :
   - **v1.0.10** en bas de la barre de gauche ;
   - 📅 **Planifier la semaine** → la case **Convives** du jour → tape **20** : elle
     le garde (avant, elle revenait à 12) ;
   - en bas de page, **Générer la fiche PDF** de la semaine si tu veux la liste de
     courses d'un repas nombreux : les quantités suivent le nombre de convives.

> Si le bandeau rouge du haut cite un fichier resté « d'avant », c'est qu'une copie
> n'a pas abouti : refais l'étape 2 pour le fichier cité, puis Reboot app.

---

## 4. Empreintes (les fichiers livrés sont ceux qui ont été testés)

| Fichier | MD5 |
|---|---|
| `MAJ_1.0.10/app.py` | `05cf44b0ce89c71e3b7012b2f35a5ebb` |
| `MAJ_1.0.10/editeurs.py` | `424db14f0277a377a491da1f3aaf6b74` |
| `MAJ_1.0.10/menus.py` | `1187e9242f4bb014505ec8784f911709` |
| `MAJ_1.0.10/MAJ_1.0.10.zip` | *(voir le message d'accompagnement)* |

Vérification sur ton PC (facultatif) : `md5sum menus.py` doit afficher
`1187e9242f4bb014505ec8784f911709`.

---

## 5. Ce qui a été vérifié avant de te livrer ça

**Test complet joué sur l'application, sans navigateur — 28 vérifications, 0 échec :**

- la case Convives garde **13, 20, 40 et 60** (elle refusait tout ça avant) ;
- la fenêtre **✏️ Modifier** accepte 60 et l'**enregistre vraiment** dans la base
  (relu après coup, dans `nb_persons` et dans `servings`) ;
- un repas **ajouté à 40 convives** est bien écrit avec 40 dans la base ;
- les quantités suivent : **20 convives de pâtes = 1 600 g**, 13 convives = 1 040 g,
  **1 convive = 80 g** (c'était 0 g avant), et une quantité en kilos n'est pas
  touchée (2 kg = 2 000 g).

**Et les six suites habituelles, toutes vertes :** audit des 9 pages, connexion,
espace partagé, espaces séparés, tableaux et masse grasse, repas types (35
vérifications).

**Côté téléphone :** banc de calculs Kotlin étendu avec les mêmes contrôles
(1, 12, 13, 20, 40, 200 convives) — APK **1.0.9** fournie à part, avec sa notice.

---

## 6. Rappel : ce qui reste de ton côté

- **Le téléphone** : installer **`TELECHARGER_APK_Equilibre_1.0.9.zip`** (l'APK 1.0.9
  avec sa notice) — même correction, plus les repas types.
- Si ce n'est pas encore fait : ta **connexion** (Reset password dans Supabase →
  lignes `email`/`password` des Secrets) et **son compte à elle** (`elle_email`,
  `elle_password`, `cle_elle`).
