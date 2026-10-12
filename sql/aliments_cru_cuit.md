# État cru / cuit — liste à trancher

Générée d'après **votre** base. Chaque ligne porte les macros Ciqual réelles des deux
états ; aucune n'est calculée.

Colonne **Défaut** : ma proposition. Dites-moi simplement quelles lignes vous changez.

| # | Votre aliment | Défaut | kcal cru | kcal cuit | P cru | P cuit |
|---|---|---|---|---|---|---|
| 1 | Pâtes sèches, standard, crues | **cuit** | 364 | 167 | 13.1 | 6.69 |
| 2 | Riz blanc, cru | **cuit** | 350 | 155 | 7.38 | 3.31 |
| 3 | Quinoa, cru | **cuit** | 358 | 149 | 14.1 | 5 |
| 4 | Pois chiche, sec | **cuit** | 350 | 148 | 20.5 | 8.31 |
| 5 | Lentille blonde, sèche | **cuit** | 339 | 122 | 26.1 | 9.7 |
| 6 | Pomme de terre, sans peau, crue | **cru** | 80 | 81 | 2.02 | 1.8 |
| 7 | Patate douce, crue | **cru** | 81.2 | 79.1 | 1.57 | 1.69 |
| 8 | Carotte, crue | **cru** | 30.2 | 29.6 | 0.78 | 0.25 |
| 9 | Épinard, cru | **cru** | 33.3 | 19.6 | 2.68 | 3.2 |
| 10 | Brocoli, cru | **cru** | 31.9 | 22.2 | 2.9 | 2.5 |
| 11 | Courgette, chair et peau, crue | **cru** | 16.7 | 15.5 | 1.21 | 0.93 |
| 12 | Chou-fleur, cru | **cru** | 24.9 | 20.9 | 1.81 | 1.6 |
| 13 | Haricot vert, cru | **cru** | 31.9 | 29.4 | 1.83 | 2 |
| 14 | Poireau, cru | **cru** | 30.4 | 24.7 | 1.5 | 2.56 |
| 15 | Oignon, cru | **cru** | 39 | 34.6 | 1.1 | 1.3 |
| 16 | Tomate sans précision, crue (aliment moyen) | **cru** | 19.2 | 19.8 | 0.6 | 0.97 |
| 17 | Poivron vert, cru | **cru** | 22.5 | 33 | 0.81 | 1.11 |
| 18 | Aubergine, crue | **cru** | 22.9 | 27.1 | 0.98 | 0.83 |
| 19 | Champignon de Paris ou champignon de couche, cru | **cru** | 21 | 28.7 | 2.11 | 2.17 |
| 20 | Saumon, élevage, cru | **cuit** | 193 | 199 | 20.5 | 23 |
| 21 | Poulet, viande crue | **cuit** | 109 | 204 | 20.9 | 28.9 |
| 22 | Dinde, viande crue | **cuit** | 108 | 151 | 22.6 | 29.1 |
| 23 | Veau, escalope crue | **cuit** | 114 | 147 | 20.5 | 31 |
| 24 | Porc, filet mignon cru | **cuit** | 123 | 168 | 21.2 | 26.1 |
| 25 | Thon, cru | **cuit** | 155 | 136 | 24 | 29.9 |
| 26 | Oeuf cru | **cuit** | 140 | 134 | 12.8 | 13.5 |
| 27 | Chipolata crue | **cuit** | 253 | 283 | 15.8 | 18.8 |

## Pourquoi ces défauts

Féculents, légumineuses, viandes, poissons et œuf partent sur **cuit** : c'est l'état où
vous les pesez réellement. Les légumes partent sur **cru**.

Rien n'est appliqué par coefficient : l'écart va de +1 % (pomme de terre) à −58 %
(pois chiche). Un multiplicateur unique donnerait des valeurs fausses.

## Non couverts, et pourquoi

- **Lieu / colin d'Alaska, Sardine crue** : Ciqual n'a pas de version cuite.
- **Riz complet, Boulgour, Poivron rouge, Céleri branche, Crevette, Cabillaud** :
  absents de votre base. `sql/aliments_courants.sql` peut les ajouter.
- **Maïs doux, Semoule/couscous, Steak haché, Faux-filet** : votre entrée est déjà à
  l'état cuit ou appertisé ; un second état n'apporterait rien.

Tant qu'aucune valeur d'état n'est renseignée, le sélecteur cru/cuit n'apparaît pas
dans l'app pour cet aliment : mieux vaut aucune valeur qu'une valeur inventée.
