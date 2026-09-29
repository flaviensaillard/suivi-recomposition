# 🔗 Jumeler les deux applications — la bonne façon de le faire

**Réponse courte : oui, c'est intéressant — mais pas en fusionnant les deux codes.**
Le bon jumelage se fait à **trois niveaux**, et les trois sont désormais en place. Voici lequel
apporte quoi, et pourquoi je te déconseille le quatrième.

| Niveau | Quoi | État | Bénéfice |
|---|---|---|---|
| **1. Les données** | Une seule base Supabase, deux familles de tables | ✅ déjà fait | Un seul compte, une seule sauvegarde, projet jamais mis en veille |
| **2. Les fonctionnalités** | Tes menus alimentent ton compteur de protéines | ✅ **fait aujourd'hui** | Zéro double saisie — c'est le vrai gain |
| **3. Le téléphone** | Un APK, deux applications, bouton ⇄ | ✅ **fait aujourd'hui** | Une icône, deux applis |
| **4. Le code** | Fusionner les deux applications Streamlit | ⛔ déconseillé | Risque élevé, gain faible — voir plus bas |

---

## Niveau 1 — Les données : déjà jumelées ✅

Tes deux applications vivent dans le **même projet Supabase** `gestion-menus`, mais dans deux
familles de tables totalement étanches :

```
   PROJET SUPABASE « gestion-menus »
   │
   ├── TES TABLES (application Menus)
   │     recipes · recipe_ingredient · ingredients · menu · menu_recipe
   │     menu_ingredients · planned_meals · recurring_items
   │
   └── NOS TABLES (application Suivi)  ← préfixe sr_
         sr_profiles · sr_daily_logs · sr_measurements · sr_workouts
         sr_workout_sets · sr_protein_entries · sr_shopping_state
         sr_integration_map   ← nouveau : la passerelle
```

Chaque table porte sa propre sécurité (RLS `user_id = auth.uid()`). Aucune requête de l'une ne peut
toucher les données de l'autre : **l'étanchéité est garantie par la base, pas par le code.**

**Trois bénéfices gratuits de ce choix :**
- un seul identifiant, une seule sauvegarde ;
- ton projet ne se met **jamais en pause** (ton app de menus le maintient éveillé), donc l'appli
  s'ouvre instantanément sur le téléphone ;
- moins d'1 Mo utilisé sur les 500 Mo offerts.

---

## Niveau 2 — Les fonctionnalités : le vrai jumelage ✅ (nouveau)

C'est ici que les deux applications se parlent enfin. Nouvelle page dans l'application :
**🍽️ Cuisine & menus**.

### Ce qu'elle fait

1. **Elle analyse ta base toute seule.** Elle cherche ses repères dans tes tables
   (`planned_meals`, `recipes`, `recipe_ingredient`, `ingredients`…) et, en lisant quelques lignes,
   elle **devine** où se trouvent : le nom du plat, le nom de l'ingrédient, les protéines pour 100 g,
   les quantités, la date du planning, le nombre de portions.
2. **Elle affiche les repas prévus aujourd'hui**, avec une estimation des protéines calculée en
   joignant tes recettes, tes ingrédients et leurs quantités.
3. **Un appui suffit** : `+42 g de protéines` → c'est ajouté au compteur du jour. Fini la double saisie.
4. **Elle te classe tes recettes les plus protéinées** — très utile les semaines où il faut atteindre
   140 g sans manger plus de viande.
5. **Le coach peut corriger la détection.** Si ta base n'utilise pas des noms de colonnes classiques,
   la page propose de corriger la correspondance à la main, et le choix est mémorisé dans la table
   `sr_integration_map`. Un « Diagnostic » copiable permet de tout me transmettre en cas de doute.

### Exemple concret

```
🍽️ CUISINE & MENUS
─────────────────────────────────────────────────────────
Repas prévus aujourd'hui
  Poulet basquaise + riz           · soir      ≈ 44 g de protéines   [Ajouter]
  Salade de lentilles aux œufs     · midi      ≈ 28 g de protéines   [Ajouter]
                                        → Compteur du jour : 72 / 140 g
```

### Mise en route (2 minutes)

1. **Relance `schema.sql`** dans Supabase (SQL Editor) : la requête est en `create table if not exists`,
   donc elle ajoute seulement la nouvelle table `sr_integration_map` et ne touche à rien d'autre.
2. Va sur la page **🍽️ Cuisine & menus** : l'analyse se lance toute seule.
3. Vérifie que les repas du jour sont justes. Sinon : *Étape 2 — Vérifier / corriger la correspondance*.

### Facultatif — un bouton vers ton application Menus

Dans les Secrets Streamlit, tu peux ajouter l'adresse de ton application de menus pour qu'un bouton
apparaisse dans la barre latérale du suivi :

```toml
[supabase]
url = "https://xxxxx.supabase.co"
anon_key = "sb_publishable_..."

[apps]
menus_url = "https://gestion-menus.streamlit.app"
```

---

## Niveau 3 — Le téléphone : un seul APK, deux applications ✅ (nouveau)

Le nouvel APK **`SuiviRecomposition-1.1.apk`** (« Mes apps ») peut héberger **tes deux
applications** :

- Au premier lancement, il demande **deux adresses** :
  1. l'application **Suivi** (obligatoire) ;
  2. l'application **Menus** (facultative — recettes, courses).
- Le bouton **⇄** dans la barre du haut passe de l'une à l'autre **sans quitter l'application**.
- Le titre affiche où tu te trouves (« Suivi » ou « Menus »).
- Les boutons **⟳** (recharger) et **⚙** (options, modifier les adresses) restent disponibles.

### Installation de la 1.1 par-dessus la 1.0

Bonne nouvelle : elle est signée **avec la même clé**, donc l'installation se fait **par-dessus**
la version existante — pas besoin de désinstaller, tes réglages sont conservés.

> ⚠️ Ne désinstalle pas l'ancienne version « pour être sûr » : même si ça marcherait, tu perdrais
> les adresses que tu y avais saisies.

---

## Niveau 4 — Fusionner le code : pourquoi je te le déconseille ⛔

Techniquement, c'est faisable (une seule application Streamlit avec les pages des deux mondes, un
seul dépôt GitHub). Mais je ne le ferais pas aujourd'hui, pour trois raisons concrètes :

1. **Ton application de menus fonctionne.** C'est ton outil du quotidien, probablement partagé avec
   ta femme et tes enfants. La refondre pour y greffer un module de suivi pondéral mettrait en risque
   un outil qui marche — pour un bénéfice qui est déjà obtenu par les niveaux 1 à 3.
2. **Deux publics différents.** L'un est un outil familial de cuisine (recettes, courses, menus de la
   semaine). L'autre est un outil strictement personnel (poids, masse grasse, mensurations). Les
   mélanger dans une même interface et un même écran d'accueil n'apporte rien et **complique la
   confidentialité**.
3. **Deux rythmes d'évolution.** Tu voudras faire évoluer ton suivi (nouveaux exercices, phases
   diététiques, indicateurs) sans avoir à redéployer, tester et risquer l'application de menus — et
   inversement.

**Ce que le jumelage apporte réellement — l'échange de données — est acquis.** Le reste n'est que de
la mise en forme.

### Si tu veux quand même la fusion, un jour

Ce serait un chantier propre et cadré, à faire **quand ton suivi aura tourné 2 à 3 mois** :
créer une application « maison » unique, avec les modules importés de chaque dépôt
(`import menus_pages` / `import suivi_pages`), les deux jeux de tables séparés comme aujourd'hui, et
une page d'accueil qui propose « Cuisine » ou « Suivi ». On garderait le second APK ou l'APK à deux
onglets comme filet de sécurité. Dis-le-moi si tu veux qu'on le prépare — mais pas maintenant : à ce
stade, ça ralentirait le démarrage de ton suivi, qui est l'objectif.

---

## 🔒 Un point de confidentialité à vérifier

Puisque les deux applications partagent le même projet Supabase, il y a **une** chose à choisir
consciemment : **avec quel compte te connectes-tu au suivi ?**

| Situation | Recommandation |
|---|---|
| Ton application de menus utilise **ton** compte personnel | ✅ Réutilise-le : le plus simple, un seul identifiant |
| Ton application de menus est utilisée par ta femme / tes enfants avec un **compte partagé** | ⚠️ **Crée un compte dédié** pour le suivi (Authentication → Users → Add user). Sinon toute personne qui a ce compte pourrait, en théorie, lire tes données de poids et de mensurations |

La sécurité RLS de Supabase isole déjà chaque utilisateur ligne par ligne — mais ce n'est vrai que
si les utilisateurs sont **distincts**. C'est le seul arbitrage à faire, et il te prend 30 secondes.

---

## ✅ Ta liste de vérification

- [ ] **Relancer `schema.sql`** dans Supabase → ajoute `sr_integration_map` (rien d'autre ne change)
- [ ] *(facultatif)* Ajouter `[apps] menus_url = "..."` dans les Secrets Streamlit
- [ ] Ouvrir la page **🍽️ Cuisine & menus** → vérifier que les repas du jour sont détectés
- [ ] Corriger la correspondance des colonnes si nécessaire → **Enregistrer**
- [ ] Installer **`SuiviRecomposition-1.1.apk`** par-dessus la 1.0 (même clé, aucune désinstallation)
- [ ] Renseigner les **deux adresses** au premier lancement → tester le bouton **⇄**
- [ ] Vérifier avec qui tu te connectes (compte personnel ou compte dédié — voir ci-dessus)

---

## Si la détection se trompe

C'est le seul point qui peut demander un aller-retour : je ne connais pas encore le nom exact de tes
colonnes. La page **Cuisine & menus** a un bloc **🔬 Diagnostic** qui affiche :

- les tables détectées et leurs colonnes,
- la correspondance déduite pour chaque champ (nom du plat, protéines, quantité…).

Copie-le-moi et je corrige la détection **côté code**, pour que ça marche tout seul ensuite. C'est
du travail de réglage, pas un problème de conception.
