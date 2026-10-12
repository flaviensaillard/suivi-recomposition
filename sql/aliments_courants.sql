-- ============================================================================
--  Équilibre — aliments courants pour la base nutritionnelle
-- ============================================================================
--  Cible  : table `ingredients` (sans préfixe), lue par l'onglet Menus et par
--           l'autocomplétion de l'onglet Nutrition.
--  Noms   : courts et parlants (« Pain blanc », « Riz complet cuit », « Thon à
--           la tomate »), pas les libellés Ciqual complets.
--  Unités : valeurs pour 100 g / 100 ml de partie comestible.
--  Source : table Ciqual 2025 de l'ANSES (extrait data/foods_ciqual.csv).
--           Le code Ciqual de chaque ligne est rappelé en fin de ligne.
--
--  `poids_piece_g` permet au sélecteur d'unité de convertir « 2 œufs » ou
--  « 1 verre » en grammes pour calculer les macros.
--
--  Une valeur absente de Ciqual est insérée en NULL, jamais en 0 : une macro
--  manquante reste inconnue et n'est pas comptée.
--
--  Script idempotent : un nom déjà présent n'est pas recréé.
--  À exécuter dans l'éditeur SQL de Supabase.
--
--  Licence : conserver l'attribution ANSES et la licence Ciqual en cas de
--  redistribution.
-- ============================================================================

INSERT INTO ingredients
  (name, category, unit, unite_liste_courses, poids_piece_g,
   kcal_100g, proteines_100g, glucides_100g, lipides_100g)
SELECT v.name, v.category, v.unit, v.unite_liste_courses, v.poids_piece_g,
       v.kcal_100g, v.proteines_100g, v.glucides_100g, v.lipides_100g
FROM (VALUES
  ('Pain blanc', 'Épicerie Salée', 'g', 'g', 30, 287.0, 9.06, 58.3, 1.4),  -- Ciqual 7001
  ('Pain complet', 'Épicerie Salée', 'g', 'g', 30, 234.0, 9.5, 41.2, 1.7),  -- Ciqual 7110
  ('Pain au levain', 'Épicerie Salée', 'g', 'g', 30, 261.0, 8.13, 53.1, 1.3),  -- Ciqual 7002
  ('Pain bis', 'Épicerie Salée', 'g', 'g', 30, 265.0, 9.43, 54.0, 0.33),  -- Ciqual 7010
  ('Pain de mie complet', 'Épicerie Salée', 'g', 'g', 35, 257.0, 8.0, 41.8, 4.1),  -- Ciqual 7111
  ('Riz blanc cuit', 'Épicerie Salée', 'g', 'g', NULL, 155.0, 3.31, 33.2, 0.7),  -- Ciqual 9104
  ('Riz complet cuit', 'Épicerie Salée', 'g', 'g', NULL, 187.0, 4.06, 37.6, 1.8),  -- Ciqual 9103
  ('Pâtes cuites', 'Épicerie Salée', 'g', 'g', NULL, 167.0, 6.69, 31.4, 1.1),  -- Ciqual 9811
  ('Pâtes crues', 'Épicerie Salée', 'g', 'g', NULL, 364.0, 13.1, 72.7, 1.6),  -- Ciqual 9810
  ('Semoule cuite', 'Épicerie Salée', 'g', 'g', NULL, 164.0, 6.38, 31.0, 0.9),  -- Ciqual 9683
  ('Quinoa cuit', 'Épicerie Salée', 'g', 'g', NULL, 149.0, 5.0, 27.9, 1.1),  -- Ciqual 9341
  ('Boulgour cuit', 'Épicerie Salée', 'g', 'g', NULL, 131.0, 4.63, 24.1, 1.0),  -- Ciqual 9691
  ('Pomme de terre cuite', 'Fruits & Légumes', 'g', 'g', 150, 81.0, 1.8, 16.8, 0.34),  -- Ciqual 4003
  ('Pomme de terre rôtie', 'Fruits & Légumes', 'g', 'g', 150, 91.9, 1.96, 20.1, 0.1),  -- Ciqual 4002
  ('Patate douce cuite', 'Fruits & Légumes', 'g', 'g', 200, 79.1, 1.69, 16.3, 0.15),  -- Ciqual 4102
  ('Lentilles cuites', 'Épicerie Salée', 'g', 'g', NULL, 125.0, 10.1, 16.2, 0.57),  -- Ciqual 20360
  ('Pois chiches cuits', 'Épicerie Salée', 'g', 'g', NULL, 148.0, 8.31, 17.7, 3.0),  -- Ciqual 20507
  ('Haricots rouges cuits', 'Épicerie Salée', 'g', 'g', NULL, 116.0, 9.63, 12.3, 0.6),  -- Ciqual 20503
  ('Haricots blancs cuits', 'Épicerie Salée', 'g', 'g', NULL, 112.0, 6.75, 12.0, 1.1),  -- Ciqual 20502
  ('Maïs doux cuit', 'Fruits & Légumes', 'g', 'g', 150, 106.0, 3.41, 18.6, 1.5),  -- Ciqual 20049
  ('Tofu nature', 'Frais & Produits Laitiers', 'g', 'g', 125, 147.0, 14.7, 2.87, 8.5),  -- Ciqual 20904
  ('Œuf dur', 'Frais & Produits Laitiers', 'unité', 'unité', 50, 134.0, 13.5, 0.52, 8.62),  -- Ciqual 22010
  ('Œuf à la coque', 'Frais & Produits Laitiers', 'unité', 'unité', 50, 142.0, 12.2, 1.08, 9.82),  -- Ciqual 22014
  ('Œuf au plat', 'Frais & Produits Laitiers', 'unité', 'unité', 50, 157.0, 14.6, 1.4, 10.4),  -- Ciqual 22505
  ('Blanc d''œuf cuit', 'Frais & Produits Laitiers', 'g', 'g', 33, 47.3, 10.3, 1.12, 0.17),  -- Ciqual 22008
  ('Jaune d''œuf cuit', 'Frais & Produits Laitiers', 'g', 'g', 17, 340.0, 16.0, 1.31, 30.1),  -- Ciqual 22009
  ('Poulet filet grillé', 'Boucherie & Poissonnerie', 'g', 'g', 130, 141.0, 30.1, 0.0, 2.0),  -- Ciqual 36018
  ('Steak haché 5%', 'Boucherie & Poissonnerie', 'g', 'g', 100, 155.0, 25.5, 0.0, 5.85),  -- Ciqual 6251
  ('Steak haché 10%', 'Boucherie & Poissonnerie', 'g', 'g', 100, 210.0, 26.1, 0.0, 11.8),  -- Ciqual 6253
  ('Steak grillé', 'Boucherie & Poissonnerie', 'g', 'g', 130, 128.0, 27.6, 0.0, 1.95),  -- Ciqual 6200
  ('Entrecôte grillée', 'Boucherie & Poissonnerie', 'g', 'g', 150, 198.0, 25.5, 0.0, 10.7),  -- Ciqual 6100
  ('Jambon cuit', 'Boucherie & Poissonnerie', 'tranche', 'tranche', 40, 113.0, 21.0, 0.76, 2.83),  -- Ciqual 28900
  ('Bacon', 'Boucherie & Poissonnerie', 'tranche', 'tranche', 15, 118.0, 23.1, 0.7, 2.6),  -- Ciqual 28727
  ('Saucisse de Toulouse', 'Boucherie & Poissonnerie', 'g', 'g', 100, 279.0, 18.8, 1.28, 22.1),  -- Ciqual 30011
  ('Thon au naturel', 'Boucherie & Poissonnerie', 'g', 'g', NULL, 143.0, 26.8, 0.0, 3.94),  -- Ciqual 26039
  ('Thon à la tomate', 'Boucherie & Poissonnerie', 'g', 'g', NULL, 140.0, 13.0, 4.33, 7.67),  -- Ciqual 26242
  ('Thon à l''huile', 'Boucherie & Poissonnerie', 'g', 'g', NULL, 206.0, 23.3, 0.76, 12.2),  -- Ciqual 26180
  ('Sardine à l''huile', 'Boucherie & Poissonnerie', 'unité', 'unité', 30, 217.0, 23.3, 0.31, 13.7),  -- Ciqual 26034
  ('Sardine sauce tomate', 'Boucherie & Poissonnerie', 'unité', 'unité', 30, 194.0, 20.2, 1.83, 11.6),  -- Ciqual 26035
  ('Saumon vapeur', 'Boucherie & Poissonnerie', 'g', 'g', 130, 199.0, 23.0, 0.9, 11.5),  -- Ciqual 26038
  ('Saumon fumé', 'Boucherie & Poissonnerie', 'tranche', 'tranche', 20, 201.0, 21.2, 0.37, 12.8),  -- Ciqual 25993
  ('Cabillaud cuit', 'Boucherie & Poissonnerie', 'g', 'g', 130, 100.0, 23.3, NULL, 0.76),  -- Ciqual 25997
  ('Maquereau cuit', 'Boucherie & Poissonnerie', 'g', 'g', 130, 228.0, 21.5, NULL, 15.8),  -- Ciqual 26019
  ('Crevette cuite', 'Boucherie & Poissonnerie', 'unité', 'unité', 10, 89.4, 19.4, 0.47, 1.1),  -- Ciqual 10006
  ('Lait demi-écrémé', 'Frais & Produits Laitiers', 'ml', 'ml', 200, 47.5, 3.38, 4.97, 1.55),  -- Ciqual 19033
  ('Lait UHT', 'Frais & Produits Laitiers', 'ml', 'ml', 200, 47.7, 3.41, 4.97, 1.57),  -- Ciqual 19039
  ('Yaourt nature', 'Frais & Produits Laitiers', 'unité', 'unité', 125, 50.1, 3.75, 4.26, 1.68),  -- Ciqual 19593
  ('Yaourt 0%', 'Frais & Produits Laitiers', 'unité', 'unité', 125, 39.1, 4.08, 4.89, 0.1),  -- Ciqual 19594
  ('Fromage blanc 0%', 'Frais & Produits Laitiers', 'g', 'g', 100, 48.4, 7.19, 4.22, 0.1),  -- Ciqual 19644
  ('Fromage blanc 3%', 'Frais & Produits Laitiers', 'g', 'g', 100, 75.7, 7.13, 3.86, 3.23),  -- Ciqual 19646
  ('Skyr nature', 'Frais & Produits Laitiers', 'unité', 'unité', 150, 74.5, 9.1, 3.45, 2.7),  -- Ciqual 19724
  ('Mozzarella', 'Frais & Produits Laitiers', 'unité', 'unité', 125, 227.0, 16.1, 0.7, 17.7),  -- Ciqual 19590
  ('Emmental', 'Frais & Produits Laitiers', 'tranche', 'tranche', 30, 373.0, 27.3, NULL, 28.8),  -- Ciqual 12115
  ('Comté', 'Frais & Produits Laitiers', 'tranche', 'tranche', 30, 413.0, 27.2, NULL, 33.8),  -- Ciqual 12110
  ('Parmesan', 'Frais & Produits Laitiers', 'g', 'g', 25, 411.0, 30.5, 1.14, 31.0),  -- Ciqual 12120
  ('Banane', 'Fruits & Légumes', 'unité', 'unité', 120, 87.6, 1.06, 19.7, 0.5),  -- Ciqual 13005
  ('Pomme', 'Fruits & Légumes', 'unité', 'unité', 150, 54.0, 0.25, 11.6, 0.25),  -- Ciqual 13039
  ('Poire', 'Fruits & Légumes', 'unité', 'unité', 160, 56.6, 0.36, 12.3, 0.27),  -- Ciqual 13037
  ('Orange', 'Fruits & Légumes', 'unité', 'unité', 150, 42.0, 0.75, 8.03, 0.5),  -- Ciqual 13034
  ('Kiwi', 'Fruits & Légumes', 'unité', 'unité', 80, 60.9, 0.88, 11.0, 0.6),  -- Ciqual 13021
  ('Fraise', 'Fruits & Légumes', 'g', 'g', 15, 35.1, 0.63, 6.03, 0.5),  -- Ciqual 13014
  ('Raisin', 'Fruits & Légumes', 'g', 'g', 5, 71.0, 0.7, 16.3, 0.25),  -- Ciqual 13395
  ('Abricot', 'Fruits & Légumes', 'unité', 'unité', 45, 44.1, 0.81, 9.01, 0.5),  -- Ciqual 13000
  ('Pêche', 'Fruits & Légumes', 'unité', 'unité', 120, 37.9, 0.91, 7.55, 0.25),  -- Ciqual 13043
  ('Avocat', 'Fruits & Légumes', 'unité', 'unité', 140, 203.0, 1.56, NULL, 20.6),  -- Ciqual 13004
  ('Citron', 'Fruits & Légumes', 'unité', 'unité', 60, 24.3, 0.25, 1.56, 0.5),  -- Ciqual 13009
  ('Tomate', 'Fruits & Légumes', 'unité', 'unité', 120, 19.2, 0.6, 3.69, 0.5),  -- Ciqual 20385
  ('Tomate cerise', 'Fruits & Légumes', 'unité', 'unité', 15, 31.8, 1.31, 5.62, 0.5),  -- Ciqual 20172
  ('Concombre', 'Fruits & Légumes', 'g', 'g', 300, 16.8, 0.65, 2.87, 0.11),  -- Ciqual 20019
  ('Carotte crue', 'Fruits & Légumes', 'unité', 'unité', 60, 30.2, 0.78, 5.16, 0.5),  -- Ciqual 20009
  ('Carotte cuite', 'Fruits & Légumes', 'g', 'g', 60, 33.0, 0.37, 6.24, 0.2),  -- Ciqual 20353
  ('Salade', 'Fruits & Légumes', 'g', 'g', 60, 14.7, 1.35, 1.22, 0.2),  -- Ciqual 20031
  ('Courgette', 'Fruits & Légumes', 'g', 'g', 200, 16.7, 1.21, 1.75, 0.32),  -- Ciqual 20020
  ('Brocoli', 'Fruits & Légumes', 'g', 'g', 150, 31.9, 2.9, 2.15, 0.36),  -- Ciqual 20057
  ('Épinard cru', 'Fruits & Légumes', 'g', 'g', 100, 33.3, 2.68, 3.06, 0.39),  -- Ciqual 20059
  ('Épinard cuit', 'Fruits & Légumes', 'g', 'g', 100, 19.6, 3.2, 0.25, 0.14),  -- Ciqual 20027
  ('Champignon de Paris', 'Fruits & Légumes', 'unité', 'unité', 20, 21.0, 2.11, 1.83, 0.36),  -- Ciqual 20056
  ('Poivron rouge', 'Fruits & Légumes', 'unité', 'unité', 120, 33.6, 1.06, 5.98, 0.5),  -- Ciqual 20087
  ('Poivron vert', 'Fruits & Légumes', 'unité', 'unité', 120, 22.5, 0.81, 3.43, 0.5),  -- Ciqual 20085
  ('Aubergine', 'Fruits & Légumes', 'g', 'g', 250, 22.9, 0.98, 2.7, 0.18),  -- Ciqual 20053
  ('Haricot vert', 'Fruits & Légumes', 'g', 'g', 100, 31.9, 1.83, 4.14, 0.22),  -- Ciqual 20061
  ('Chou-fleur', 'Fruits & Légumes', 'g', 'g', 150, 24.9, 1.81, 2.13, 0.7),  -- Ciqual 20016
  ('Oignon', 'Fruits & Légumes', 'unité', 'unité', 100, 39.0, 1.1, 6.25, 0.62),  -- Ciqual 20034
  ('Ail', 'Fruits & Légumes', 'gousse', 'gousse', 5, 109.0, 5.31, 18.6, 0.5),  -- Ciqual 11000
  ('Poireau', 'Fruits & Légumes', 'g', 'g', 100, 30.4, 1.5, 4.55, 0.3),  -- Ciqual 20039
  ('Céleri branche', 'Fruits & Légumes', 'g', 'g', 40, 15.4, 0.63, 2.41, 0.5),  -- Ciqual 20023
  ('Beurre doux', 'Frais & Produits Laitiers', 'g', 'g', 10, 753.0, 0.63, 0.71, 83.0),  -- Ciqual 16400
  ('Beurre demi-sel', 'Frais & Produits Laitiers', 'g', 'g', 10, 725.0, 0.75, 0.5, 80.0),  -- Ciqual 16402
  ('Huile d''olive', 'Épicerie Salée', 'ml', 'ml', 10, 899.0, 0.25, NULL, 99.9),  -- Ciqual 17270
  ('Huile de colza', 'Épicerie Salée', 'ml', 'ml', 10, 900.0, 0.0, 0.0, 100.0),  -- Ciqual 17130
  ('Beurre de cacahuète', 'Épicerie Sucrée', 'g', 'g', 15, 643.0, 25.4, 17.3, 51.4),  -- Ciqual 15202
  ('Miel', 'Épicerie Sucrée', 'g', 'g', 20, 331.0, 0.65, 82.1, 0.0),  -- Ciqual 31008
  ('Sucre blanc', 'Épicerie Sucrée', 'g', 'g', 8, 399.0, 0.0, 99.7, 0.0),  -- Ciqual 31016
  ('Confiture de pêche', 'Épicerie Sucrée', 'g', 'g', 30, 242.0, 0.27, 59.5, 0.075),  -- Ciqual 30993
  ('Chocolat noir', 'Épicerie Sucrée', 'unité', 'unité', 10, 521.0, 5.98, 53.0, 29.6),  -- Ciqual 31005
  ('Amande', 'Épicerie Sucrée', 'g', 'g', 1.2, 615.0, 22.6, 9.51, 51.3),  -- Ciqual 15000
  ('Noix', 'Épicerie Sucrée', 'g', 'g', 5, 709.0, 15.7, 6.88, 67.3),  -- Ciqual 15005
  ('Noisette', 'Épicerie Sucrée', 'g', 'g', 1.4, 632.0, 17.0, 7.16, 56.9),  -- Ciqual 15004
  ('Cacahuète', 'Épicerie Sucrée', 'g', 'g', 0.8, 623.0, 26.1, 14.8, 49.1),  -- Ciqual 15001
  ('Noix de cajou', 'Épicerie Sucrée', 'g', 'g', 1.5, 632.0, 18.0, 26.7, 49.5),  -- Ciqual 15019
  ('Noix de coco fraîche', 'Fruits & Légumes', 'g', 'g', 50, 369.0, 4.09, 4.69, 34.7),  -- Ciqual 15006
  ('Bière blonde', 'Boissons', 'ml', 'ml', 250, 39.0, 0.39, 3.12, 0.0),  -- Ciqual 5001
  ('Bière brune', 'Boissons', 'ml', 'ml', 250, 40.5, 0.43, 4.1, NULL),  -- Ciqual 5000
  ('Bière forte', 'Boissons', 'ml', 'ml', 250, 62.5, 0.51, 4.6, 0.0),  -- Ciqual 5002
  ('Vin rouge', 'Boissons', 'ml', 'ml', 120, 75.7, 0.16, 0.0, 0.5),  -- Ciqual 5214
  ('Vin blanc sec', 'Boissons', 'ml', 'ml', 120, 55.3, 0.25, 0.17, 0.0),  -- Ciqual 5215
  ('Champagne', 'Boissons', 'ml', 'ml', 120, 76.1, 0.3, 1.4, 0.0),  -- Ciqual 5207
  ('Cidre', 'Boissons', 'ml', 'ml', 250, 36.5, 0.075, 3.67, 0.18),  -- Ciqual 5003
  ('Whisky', 'Boissons', 'ml', 'ml', 40, 252.0, 0.0, 0.096, 0.0),  -- Ciqual 1005
  ('Vodka', 'Boissons', 'ml', 'ml', 40, 250.0, 0.0, 0.0, 0.0),  -- Ciqual 1008
  ('Rhum', 'Boissons', 'ml', 'ml', 40, 234.0, 0.0, 0.0, 0.0),  -- Ciqual 1004
  ('Gin', 'Boissons', 'ml', 'ml', 40, 265.0, 0.0, 0.0, 0.0),  -- Ciqual 1002
  ('Cognac', 'Boissons', 'ml', 'ml', 40, 222.0, 0.0, 0.76, 0.0),  -- Ciqual 1023
  ('Pastis', 'Boissons', 'ml', 'ml', 40, 274.0, 0.0, 2.86, 0.0),  -- Ciqual 1000
  ('Café', 'Boissons', 'ml', 'ml', 100, 5.78, 0.25, 1.35, 0.018),  -- Ciqual 18004
  ('Thé vert', 'Boissons', 'ml', 'ml', 200, 5.1, 0.0, 1.09, 0.0),  -- Ciqual 18155
  ('Thé noir', 'Boissons', 'ml', 'ml', 200, 1.26, 0.0, 0.3, 0.007),  -- Ciqual 18154
  ('Jus d''orange', 'Boissons', 'ml', 'ml', 200, 45.4, 0.61, 9.61, 0.11)   -- Ciqual 2070
) AS v(name, category, unit, unite_liste_courses, poids_piece_g,
          kcal_100g, proteines_100g, glucides_100g, lipides_100g)
WHERE NOT EXISTS (
  SELECT 1 FROM ingredients i WHERE lower(i.name) = lower(v.name)
);

-- Contrôle après insertion.
SELECT count(*) AS nb_aliments,
       count(kcal_100g) AS avec_kcal,
       count(proteines_100g) AS avec_proteines,
       count(glucides_100g) AS avec_glucides,
       count(lipides_100g) AS avec_lipides
FROM ingredients;
