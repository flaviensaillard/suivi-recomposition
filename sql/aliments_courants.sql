-- ============================================================================
--  Équilibre 1.4 — aliments courants pour la base nutritionnelle
-- ============================================================================
--  Cible  : table `ingredients`, celle lue par l'onglet Menus et par la
--           recherche de l'onglet Nutrition (Menu.ingredients()).
--  Unités : valeurs pour 100 g / 100 ml de partie comestible.
--  Source : table Ciqual 2025 de l'ANSES, extrait suivi dans
--           data/foods_ciqual.csv. Le code Ciqual de chaque ligne est rappelé
--           en commentaire, pour vérification.
--
--  Une valeur absente de Ciqual est insérée en NULL, jamais en 0 : dans cette
--  application une macro manquante reste inconnue et n'est pas comptée.
--
--  Script idempotent : une ligne dont le nom existe déjà n'est pas recréée.
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
  ('Pain blanc (baguette)', 'Boulangerie', 'g', 'g', NULL, 287, 9.06, 58.3, 1.4)  -- Ciqual 7001 : Pain blanc (par ex. : baguette, boule…),
  ('Pain de tradition française', 'Boulangerie', 'g', 'g', NULL, 279, 8.94, 56.7, 1)  -- Ciqual 7007 : Pain de tradition française (par ex. : baguette, boule…),
  ('Pain bis (T80/T110)', 'Boulangerie', 'g', 'g', NULL, 265, 9.43, 54, 0.33)  -- Ciqual 7010 : Pain bis (à la farine T80 ou T110),
  ('Pain aux céréales et graines', 'Boulangerie', 'unité', 'unité', 50, 282, 9.06, 39.7, 7.6)  -- Ciqual 7098 : Pain aux céréales et/ou aux graines, préemballé,
  ('Noix (cerneau)', 'Fruits à coque', 'g', 'g', NULL, 709, 15.7, 6.88, 67.3)  -- Ciqual 15005 : Noix, cerneau, séchée,
  ('Amande', 'Fruits à coque', 'g', 'g', 1.2, 615, 22.6, 9.51, 51.3)  -- Ciqual 15000 : Amande, avec peau, sans sel ajouté,
  ('Noisette', 'Fruits à coque', 'g', 'g', 1.5, 632, 17, 7.16, 56.9)  -- Ciqual 15004 : Noisette, sans sel ajouté,
  ('Cacahuète', 'Fruits à coque', 'g', 'g', 0.7, 623, 26.1, 14.8, 49.1)  -- Ciqual 15001 : Cacahuète, sans sel ajouté,
  ('Beurre de cacahuète', 'Fruits à coque', 'g', 'g', NULL, 643, 25.4, 17.3, 51.4)  -- Ciqual 15202 : Beurre de cacahuète ou pâte d'arachide,
  ('Lait de coco', 'Épicerie', 'ml', 'ml', NULL, 199, 1.94, 4.29, 19.2)  -- Ciqual 18041 : Lait de coco,
  ('Noix de coco (chair)', 'Fruits', 'g', 'g', NULL, 369, 4.09, 4.69, 34.7)  -- Ciqual 15006 : Noix de coco, chair, fraîche,
  ('Bière brune', 'Boissons', 'ml', 'ml', NULL, 40.5, 0.43, 4.1, NULL)  -- Ciqual 5000 : Bière brune,
  ('Vin rouge', 'Boissons', 'ml', 'ml', NULL, 75.7, 0.16, 0, 0.5)  -- Ciqual 5214 : Vin rouge,
  ('Café (infusé, sans sucre)', 'Boissons', 'ml', 'ml', NULL, 5.78, 0.25, 1.35, 0.018)  -- Ciqual 18004 : Café, non instantané, sans sucres ajoutés, prêt à boire,
  ('Lait (UHT, aliment moyen)', 'Produits laitiers', 'ml', 'ml', NULL, 47.7, 3.41, 4.97, 1.57)  -- Ciqual 19039 : Lait, sans précision sur la teneur en matière grasse, UHT (aliment moyen),
  ('Riz blanc cuit', 'Féculents', 'g', 'g', NULL, 155, 3.31, 33.2, 0.7)  -- Ciqual 9104 : Riz blanc, cuit, sans sel ajouté,
  ('Riz complet cuit', 'Féculents', 'g', 'g', NULL, 187, 4.06, 37.6, 1.8)  -- Ciqual 9103 : Riz complet, cuit, sans sel ajouté,
  ('Pomme de terre cuite à l''eau', 'Féculents', 'g', 'g', 150, 81, 1.8, 16.8, 0.34)  -- Ciqual 4003 : Pomme de terre, bouillie/cuite à l'eau,
  ('Poulet (filet, grillé)', 'Viandes', 'g', 'g', NULL, 141, 30.1, 0, 2)  -- Ciqual 36018 : Poulet, filet sans peau grillé/poêlé,
  ('Saumon cuit à la vapeur', 'Poissons', 'g', 'g', NULL, 199, 23, 0.9, 11.5)  -- Ciqual 26038 : Saumon, cuit à la vapeur,
  ('Thon au naturel (conserve)', 'Poissons', 'g', 'g', NULL, 143, 26.8, 0, 3.94)  -- Ciqual 26039 : Thon, au naturel, appertisé, égoutté,
  ('Blanc d''oeuf cru', 'Viandes', 'unité', 'unité', 33, 48.1, 10.9, 0.73, 0.17)  -- Ciqual 22001 : Oeuf, blanc (blanc d'oeuf), cru,
  ('Jaune d''oeuf cru', 'Viandes', 'unité', 'unité', 17, 307, 15.5, 1.09, 26.7)  -- Ciqual 22002 : Oeuf, jaune (jaune d'oeuf), cru,
  ('Fromage blanc nature 0%', 'Produits laitiers', 'g', 'g', NULL, 48.4, 7.19, 4.22, 0.1)  -- Ciqual 19644 : Fromage blanc, nature, 0% MG,
  ('Fromage blanc nature 2-3%', 'Produits laitiers', 'g', 'g', NULL, 75.7, 7.13, 3.86, 3.23)  -- Ciqual 19646 : Fromage blanc, nature, 2-3% MG,
  ('Skyr / spécialité protéinée nature', 'Produits laitiers', 'g', 'g', NULL, 74.5, 9.1, 3.45, 2.7)  -- Ciqual 19724 : Spécialité laitière riche en protéines, nature,
  ('Emmental', 'Produits laitiers', 'g', 'g', NULL, 373, 27.3, NULL, 28.8)  -- Ciqual 12115 : Emmental ou emmenthal,
  ('Mozzarella (lait de vache)', 'Produits laitiers', 'g', 'g', NULL, 227, 16.1, 0.7, 17.7)  -- Ciqual 19590 : Mozzarella au lait de vache,
  ('Beurre doux 80% MG', 'Matières grasses', 'g', 'g', NULL, 753, 0.63, 0.71, 83)  -- Ciqual 16400 : Beurre à 80% MG minimum, doux,
  ('Huile d''olive vierge extra', 'Matières grasses', 'ml', 'ml', NULL, 899, 0.25, NULL, 99.9)  -- Ciqual 17270 : Huile d'olive vierge extra,
  ('Huile de coco vierge', 'Matières grasses', 'ml', 'ml', NULL, 899, 0.16, NULL, 99.9)  -- Ciqual 16050 : Huile ou graisse de coco, vierge,
  ('Banane', 'Fruits', 'unité', 'unité', 120, 87.6, 1.06, 19.7, 0.5)  -- Ciqual 13005 : Banane, chair sans peau, crue,
  ('Pomme', 'Fruits', 'unité', 'unité', 150, 54, 0.25, 11.6, 0.25)  -- Ciqual 13039 : Pomme, chair et peau, crue,
  ('Avocat', 'Fruits', 'unité', 'unité', 150, 203, 1.56, NULL, 20.6)  -- Ciqual 13004 : Avocat, chair sans peau, sans noyau, cru,
  ('Brocoli cuit à la vapeur', 'Légumes', 'g', 'g', NULL, 38, 4.13, 2.53, 0.7)  -- Ciqual 20304 : Brocoli, cuit à la vapeur,
  ('Courgette cuite', 'Légumes', 'g', 'g', NULL, 15.5, 0.93, 1.4, 0.36)  -- Ciqual 20021 : Courgette, chair et peau, cuite,
  ('Tomate cerise crue', 'Légumes', 'unité', 'unité', 15, 31.8, 1.31, 5.62, 0.5)  -- Ciqual 20172 : Tomate cerise, crue,
  ('Lentilles cuites', 'Légumineuses', 'g', 'g', NULL, 125, 10.1, 16.2, 0.57)  -- Ciqual 20360 : Lentille, bouillie/cuite à l'eau (aliment moyen),
  ('Tofu fumé', 'Légumineuses', 'g', 'g', NULL, 164, 16.4, 2.91, 9.5)  -- Ciqual 20912 : Tofu fumé, préemballé
) AS v (name, category, unit, unite_liste_courses, poids_piece_g,
        kcal_100g, proteines_100g, glucides_100g, lipides_100g)
WHERE NOT EXISTS (
  SELECT 1 FROM ingredients i WHERE lower(i.name) = lower(v.name)
);

-- Contrôle : ce qui a été ajouté.
SELECT name, category, unit, kcal_100g, proteines_100g, glucides_100g, lipides_100g
FROM ingredients
ORDER BY category, name;
