-- ============================================================================
--  ALIMENTS COURANTS — régénéré d'après VOTRE base
--
--  Votre table `ingredients` contient 164 entrées, dont 13 produits d'entretien.
--  136 portent un nom Ciqual exact, apparié ici par CODE (pas par nom, seule
--  méthode fiable).
--
--  Sur les 118 aliments initialement proposés :
--     39 sont déjà chez vous            -> retirés
--     16 sont devenus inutiles          -> retirés : l'état « cuit » de
--         sql/etats_ciqual.sql les remplace (vous avez déjà « Riz blanc, cru »,
--         « Pâtes sèches, standard, crues », « Oeuf cru »…)
--     63 restent à insérer
--
--  Noms courts, comme demandé — alors que votre base existante porte des noms
--  Ciqual complets. Les deux conventions coexisteront ; dites-moi si vous
--  préférez que je réaligne sur les noms Ciqual.
--
--  Macros relues par code Ciqual dans data/foods_ciqual.csv, jamais transcrites
--  à la main. `poids_piece_g` renseigné pour que le sélecteur d'unité
--  convertisse « 1 verre » ou « 2 œufs » en grammes.
--
--  Idempotent : relancer ce script n'insère rien de plus.
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
  ('Riz complet cuit', 'Épicerie Salée', 'g', 'g', NULL, 187.0, 4.06, 37.6, 1.8),  -- Ciqual 9103
  ('Boulgour cuit', 'Épicerie Salée', 'g', 'g', NULL, 131.0, 4.63, 24.1, 1.0),  -- Ciqual 9691
  ('Pomme de terre rôtie', 'Fruits & Légumes', 'g', 'g', 150, 91.9, 1.96, 20.1, 0.1),  -- Ciqual 4002
  ('Haricots rouges cuits', 'Épicerie Salée', 'g', 'g', NULL, 116.0, 9.63, 12.3, 0.6),  -- Ciqual 20503
  ('Haricots blancs cuits', 'Épicerie Salée', 'g', 'g', NULL, 112.0, 6.75, 12.0, 1.1),  -- Ciqual 20502
  ('Poulet filet grillé', 'Boucherie & Poissonnerie', 'g', 'g', 130, 141.0, 30.1, 0.0, 2.0),  -- Ciqual 36018
  ('Steak haché 5%', 'Boucherie & Poissonnerie', 'g', 'g', 100, 155.0, 25.5, 0.0, 5.85),  -- Ciqual 6251
  ('Steak haché 10%', 'Boucherie & Poissonnerie', 'g', 'g', 100, 210.0, 26.1, 0.0, 11.8),  -- Ciqual 6253
  ('Steak grillé', 'Boucherie & Poissonnerie', 'g', 'g', 130, 128.0, 27.6, 0.0, 1.95),  -- Ciqual 6200
  ('Entrecôte grillée', 'Boucherie & Poissonnerie', 'g', 'g', 150, 198.0, 25.5, 0.0, 10.7),  -- Ciqual 6100
  ('Bacon', 'Boucherie & Poissonnerie', 'tranche', 'tranche', 15, 118.0, 23.1, 0.7, 2.6),  -- Ciqual 28727
  ('Saucisse de Toulouse', 'Boucherie & Poissonnerie', 'g', 'g', 100, 279.0, 18.8, 1.28, 22.1),  -- Ciqual 30011
  ('Thon au naturel', 'Boucherie & Poissonnerie', 'g', 'g', NULL, 143.0, 26.8, 0.0, 3.94),  -- Ciqual 26039
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
  ('Yaourt 0%', 'Frais & Produits Laitiers', 'unité', 'unité', 125, 39.1, 4.08, 4.89, 0.1),  -- Ciqual 19594
  ('Fromage blanc 3%', 'Frais & Produits Laitiers', 'g', 'g', 100, 75.7, 7.13, 3.86, 3.23),  -- Ciqual 19646
  ('Skyr nature', 'Frais & Produits Laitiers', 'unité', 'unité', 150, 74.5, 9.1, 3.45, 2.7),  -- Ciqual 19724
  ('Mozzarella', 'Frais & Produits Laitiers', 'unité', 'unité', 125, 227.0, 16.1, 0.7, 17.7),  -- Ciqual 19590
  ('Emmental', 'Frais & Produits Laitiers', 'tranche', 'tranche', 30, 373.0, 27.3, NULL, 28.8),  -- Ciqual 12115
  ('Raisin', 'Fruits & Légumes', 'g', 'g', 5, 71.0, 0.7, 16.3, 0.25),  -- Ciqual 13395
  ('Abricot', 'Fruits & Légumes', 'unité', 'unité', 45, 44.1, 0.81, 9.01, 0.5),  -- Ciqual 13000
  ('Pêche', 'Fruits & Légumes', 'unité', 'unité', 120, 37.9, 0.91, 7.55, 0.25),  -- Ciqual 13043
  ('Avocat', 'Fruits & Légumes', 'unité', 'unité', 140, 203.0, 1.56, NULL, 20.6),  -- Ciqual 13004
  ('Tomate cerise', 'Fruits & Légumes', 'unité', 'unité', 15, 31.8, 1.31, 5.62, 0.5),  -- Ciqual 20172
  ('Salade', 'Fruits & Légumes', 'g', 'g', 60, 14.7, 1.35, 1.22, 0.2),  -- Ciqual 20031
  ('Poivron rouge', 'Fruits & Légumes', 'unité', 'unité', 120, 33.6, 1.06, 5.98, 0.5),  -- Ciqual 20087
  ('Céleri branche', 'Fruits & Légumes', 'g', 'g', 40, 15.4, 0.63, 2.41, 0.5),  -- Ciqual 20023
  ('Beurre demi-sel', 'Frais & Produits Laitiers', 'g', 'g', 10, 725.0, 0.75, 0.5, 80.0),  -- Ciqual 16402
  ('Huile de colza', 'Épicerie Salée', 'ml', 'ml', 10, 900.0, 0.0, 0.0, 100.0),  -- Ciqual 17130
  ('Confiture de pêche', 'Épicerie Sucrée', 'g', 'g', 30, 242.0, 0.27, 59.5, 0.075),  -- Ciqual 30993
  ('Amande', 'Épicerie Sucrée', 'g', 'g', 1.2, 615.0, 22.6, 9.51, 51.3),  -- Ciqual 15000
  ('Noisette', 'Épicerie Sucrée', 'g', 'g', 1.4, 632.0, 17.0, 7.16, 56.9),  -- Ciqual 15004
  ('Cacahuète', 'Épicerie Sucrée', 'g', 'g', 0.8, 623.0, 26.1, 14.8, 49.1),  -- Ciqual 15001
  ('Noix de cajou', 'Épicerie Sucrée', 'g', 'g', 1.5, 632.0, 18.0, 26.7, 49.5),  -- Ciqual 15019
  ('Noix de coco fraîche', 'Fruits & Légumes', 'g', 'g', 50, 369.0, 4.09, 4.69, 34.7),  -- Ciqual 15006
  ('Bière blonde', 'Boissons', 'ml', 'ml', 250, 39.0, 0.39, 3.12, 0.0),  -- Ciqual 5001
  ('Bière brune', 'Boissons', 'ml', 'ml', 250, 40.5, 0.43, 4.1, NULL),  -- Ciqual 5000
  ('Bière forte', 'Boissons', 'ml', 'ml', 250, 62.5, 0.51, 4.6, 0.0),  -- Ciqual 5002
  ('Vin rouge', 'Boissons', 'ml', 'ml', 120, 75.7, 0.16, 0.0, 0.5),  -- Ciqual 5214
  ('Champagne', 'Boissons', 'ml', 'ml', 120, 76.1, 0.3, 1.4, 0.0),  -- Ciqual 5207
  ('Cidre', 'Boissons', 'ml', 'ml', 250, 36.5, 0.075, 3.67, 0.18),  -- Ciqual 5003
  ('Whisky', 'Boissons', 'ml', 'ml', 40, 252.0, 0.0, 0.096, 0.0),  -- Ciqual 1005
  ('Vodka', 'Boissons', 'ml', 'ml', 40, 250.0, 0.0, 0.0, 0.0),  -- Ciqual 1008
  ('Gin', 'Boissons', 'ml', 'ml', 40, 265.0, 0.0, 0.0, 0.0),  -- Ciqual 1002
  ('Cognac', 'Boissons', 'ml', 'ml', 40, 222.0, 0.0, 0.76, 0.0),  -- Ciqual 1023
  ('Pastis', 'Boissons', 'ml', 'ml', 40, 274.0, 0.0, 2.86, 0.0),  -- Ciqual 1000
  ('Thé vert', 'Boissons', 'ml', 'ml', 200, 5.1, 0.0, 1.09, 0.0),  -- Ciqual 18155
  ('Thé noir', 'Boissons', 'ml', 'ml', 200, 1.26, 0.0, 0.3, 0.007),  -- Ciqual 18154
  ('Jus d''orange', 'Boissons', 'ml', 'ml', 200, 45.4, 0.61, 9.61, 0.11)  -- Ciqual 2070
) AS v(name, category, unit, unite_liste_courses, poids_piece_g,
       kcal_100g, proteines_100g, glucides_100g, lipides_100g)
WHERE NOT EXISTS (
  SELECT 1 FROM ingredients i WHERE lower(i.name) = lower(v.name)
);

-- Contrôle : les 63 aliments doivent être présents.
SELECT count(*) AS aliments_insérés
FROM ingredients i
WHERE EXISTS (SELECT 1 FROM (VALUES
  ('Pain blanc'),
  ('Pain complet'),
  ('Pain au levain'),
  ('Pain bis'),
  ('Pain de mie complet'),
  ('Riz complet cuit'),
  ('Boulgour cuit'),
  ('Pomme de terre rôtie'),
  ('Haricots rouges cuits'),
  ('Haricots blancs cuits'),
  ('Poulet filet grillé'),
  ('Steak haché 5%'),
  ('Steak haché 10%'),
  ('Steak grillé'),
  ('Entrecôte grillée'),
  ('Bacon'),
  ('Saucisse de Toulouse'),
  ('Thon au naturel'),
  ('Thon à l''huile'),
  ('Sardine à l''huile'),
  ('Sardine sauce tomate'),
  ('Saumon vapeur'),
  ('Saumon fumé'),
  ('Cabillaud cuit'),
  ('Maquereau cuit'),
  ('Crevette cuite'),
  ('Lait demi-écrémé'),
  ('Lait UHT'),
  ('Yaourt 0%'),
  ('Fromage blanc 3%'),
  ('Skyr nature'),
  ('Mozzarella'),
  ('Emmental'),
  ('Raisin'),
  ('Abricot'),
  ('Pêche'),
  ('Avocat'),
  ('Tomate cerise'),
  ('Salade'),
  ('Poivron rouge'),
  ('Céleri branche'),
  ('Beurre demi-sel'),
  ('Huile de colza'),
  ('Confiture de pêche'),
  ('Amande'),
  ('Noisette'),
  ('Cacahuète'),
  ('Noix de cajou'),
  ('Noix de coco fraîche'),
  ('Bière blonde'),
  ('Bière brune'),
  ('Bière forte'),
  ('Vin rouge'),
  ('Champagne'),
  ('Cidre'),
  ('Whisky'),
  ('Vodka'),
  ('Gin'),
  ('Cognac'),
  ('Pastis'),
  ('Thé vert'),
  ('Thé noir'),
  ('Jus d''orange')
) AS v(name) WHERE lower(i.name) = lower(v.name));
