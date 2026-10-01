# Équilibre 1.0.8 — version **vérifiée par audit** · mode opératoire

Cette livraison contient **masse grasse en kilos**, **tableaux corrigeables**, et
**toutes les corrections trouvées pendant l'audit** (six défauts, dont un qui
pouvait faire perdre une journée de saisie — le rapport complet, en deux passages,
est fourni ici : `AUDIT_1.0.8.md`).

| | |
|---|---|
| Version | **1.0.8** (en bas de la barre de gauche) |
| Fichiers à copier | **6 fichiers** à la racine du dépôt : `app.py`, `content.py`, `corrections.py`, `db.py`, `tableaux.py`, `requirements.txt` |
| Secrets | **rien à changer** |
| Ce qui ne bouge pas | tes données, tes clés, tes liens, l'espace partagé, l'espace de Léa |

---

## 1. Les deux fonctions que tu as demandées

**Masse grasse en kilos** — la case de la page ⚖️ Pesée dit maintenant
**« Masse grasse (kg) »**, et juste en dessous : *« ↳ soit 18,8 % de ton poids
(80,0 kg) »*. Le tableau des 14 derniers jours a une colonne **« Masse grasse (kg) »**,
le 🏠 Tableau de bord affiche **15,1 kg** (avec le % en petit), et 📏 Mensurations
aussi. Le pourcentage reste rangé en base (c'est lui qui fait la moyenne 7 jours).

**Tableaux corrigeables** — tu cliques dans une case, tu corriges, tu cliques
**💾 Enregistrer les corrections**. Trois nouveautés :

- le **journal montre plusieurs jours** (sélecteur « Jours affichés » : Aujourd'hui ·
  7 · **14 derniers jours** · 30 · Tout) ;
- la **date est modifiable** dans le journal, la pesée et les mensurations :
  la ligne déménage sous le bon jour ;
- la **saisie rapide** demande **« Pour quel jour ? »** (pour un oubli d'hier).

---

## 2. Les corrections de l'audit (elles sont dans ces fichiers)

| Défaut trouvé | Ce qu'il provoquait | Correction |
|---|---|---|
| **① Déplacer une journée sur une date déjà remplie** | La journée d'arrivée était **écrasée sans avertissement** (perte de données) | La correction est **refusée**, avec la phrase : *« la journée du 29/09/2026 existe déjà : rien n'a été écrasé. Si tu veux vraiment la remplacer : coche 🗑️… »*. Même garde-fou pour les mensurations |
| **② Masse grasse en kg sur une journée sans poids** | La conversion était impossible et la correction **disparaissait sans rien dire** | Message clair : *« il faut d'abord le poids de cette journée… »* |
| **③ Bandeau « fichier d'avant »** | Il accusait un fichier **plus récent** que prévu, et ne voyait pas les fichiers « socle » restés en arrière | Les versions sont **comparées** (plus ancienne / plus récente), et **8 fichiers** sont surveillés au lieu de 4 |
| **④ `requirements.txt`** | Il autorisait une version de Streamlit trop ancienne pour le code livré | `streamlit>=1.50` (ta version actuelle est au-dessus) |

---

## 3. Installation (clic par clic)

1. **github.com** → dépôt `suivi-recomposition`.
2. Pour **chacun** des 6 fichiers : crayon **✏️** → **Ctrl+A** → supprimer →
   coller le nouveau → **Commit changes**.
   *`requirements.txt` est nouveau ? Non : il existe déjà dans ton dépôt (c'est lui
   qui installe Streamlit). Remplace-le comme les autres.*
3. **share.streamlit.io** → **Manage app** → **⋮** → **Reboot app**.
   *(Le redémarrage réinstalle les paquets selon le nouveau `requirements.txt` :
   c'est normal qu'il soit un peu plus long.)*
4. Navigateur : **Ctrl+Maj+R**.
5. **Vérifier** :
   - **v1.0.8** en bas de la barre de gauche ;
   - ⚖️ **Pesée** → la case dit **« Masse grasse (kg) »** et la conversion s'affiche
     dessous ;
   - 🥗 **Nutrition** → le journal a un sélecteur **« Jours affichés »** ;
   - aucune bandeau rouge : le contrôle des 8 fichiers est silencieux quand tout
     est à jour.
6. **Le test de non-perte** (30 secondes, facultatif mais rassurant) : dans ⚖️ Pesée,
   change la date d'une journée vers une date qui **existe déjà** → l'application
   doit **refuser** avec le message « rien n'a été écrasé ». C'est le défaut ①,
   corrigé.

---

## 4. Empreintes (les fichiers livrés sont ceux qui ont été testés)

| Fichier | MD5 |
|---|---|
| `MAJ_1.0.8/app.py` | `9bb006fc16c5ceb1ab06a6ab39b94e0e` |
| `MAJ_1.0.8/content.py` | `934371530a70896f9f2c8791275eed54` |
| `MAJ_1.0.8/corrections.py` | `8ffccb4c833693ce8055be8403fe9740` |
| `MAJ_1.0.8/db.py` | `10f5f37af77a18fdc1e48798df8cf4a1` |
| `MAJ_1.0.8/tableaux.py` | `635bd0964227f3a089c8a9e905066f2b` |
| `MAJ_1.0.8/requirements.txt` | `66e7f78c7b8921fbce604ca6efe3e1bf` |
| `MAJ_1.0.8/MAJ_1.0.8.zip` | *(voir le message d'accompagnement)* |

**Vérification sur ton PC** (facultatif) : `md5sum app.py` doit afficher
`9bb006fc16c5ceb1ab06a6ab39b94e0e`.

---

## 5. Rappel : ce qui reste de ton côté

- **Ta connexion** (Reset password du compte dans Supabase → lignes `email`/`password`
  des Secrets) : si ce n'est pas encore fait, l'application te guide maintenant en
  français et sans jargon.
- **Son compte à elle** (`Add user` → Auto Confirm User, puis `elle_email`,
  `elle_password`, `cle_elle` dans les Secrets) et son lien personnel.
- **Le téléphone** : `Equilibre-Android-1.0.7.apk` (durci par l'audit — c'est la
  seule APK à installer).
