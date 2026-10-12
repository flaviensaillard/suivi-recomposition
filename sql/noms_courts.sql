-- ===========================================================================
--  NOMS COURTS À L'AFFICHAGE
--
--  Convention retenue : la base garde les libellés Ciqual complets, c'est
--  nom_affiche qui s'affiche partout dans l'application (menu.js:46 le
--  privilégie déjà devant name).
--
--  Règle : la partie avant la première virgule. Les 5 aliments où cette règle
--  donnait un doublon (« Boeuf » pour 2 aliments, « Porc » pour 3) sont
--  tranchés explicitement, pas par une règle.
--
--  Idempotent, et ne touche que les lignes où nom_affiche est encore vide :
--  un nom court saisi à la main dans l'application n'est jamais écrasé.
--
--  À exécuter APRÈS sql/etat_cru_cuit.sql, qui crée la colonne.
-- ===========================================================================

ALTER TABLE ingredients ADD COLUMN IF NOT EXISTS nom_affiche text;
UPDATE ingredients SET nom_affiche = 'Ail'
    WHERE name = 'Ail, cru'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Aubergine'
    WHERE name = 'Aubergine, crue'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Banane'
    WHERE name = 'Banane, chair sans peau, crue'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Betterave rouge'
    WHERE name = 'Betterave rouge, crue'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Beurre à 80% MG minimum'
    WHERE name = 'Beurre à 80% MG minimum, doux'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Boeuf faux-filet'
    WHERE name = 'Boeuf, faux-filet rôti/cuit au four'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Boeuf haché 15%'
    WHERE name = 'Boeuf, steak haché 15% MG cuit'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Bouillon de boeuf'
    WHERE name = 'Bouillon de boeuf, déshydraté reconstitué'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Bouillon de légumes'
    WHERE name = 'Bouillon de légumes, déshydraté reconstitué'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Bouillon de volaille'
    WHERE name = 'Bouillon de volaille, déshydraté'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Boulettes au boeuf'
    WHERE name = 'Boulettes au boeuf, à la sauce tomate, préemballées'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Brocoli'
    WHERE name = 'Brocoli, cru'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Cacao'
    WHERE name = 'Cacao, sans sucres ajoutés, poudre soluble'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Café'
    WHERE name = 'Café, non instantané, sans sucres ajoutés, prêt à boire'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Carotte'
    WHERE name = 'Carotte, crue'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Champignon de Paris ou champignon de couche'
    WHERE name = 'Champignon de Paris ou champignon de couche, cru'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Chocolat noir 50 % de cacao environ'
    WHERE name = 'Chocolat noir 50 % de cacao environ, tablette'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Chou-fleur'
    WHERE name = 'Chou-fleur, cru'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Citron'
    WHERE name = 'Citron, chair sans peau, sans pépins, cru'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Compote de pomme'
    WHERE name = 'Compote de pomme, préemballée'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Concombre'
    WHERE name = 'Concombre, chair et peau, cru'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Confiture ou marmelade ou gelée'
    WHERE name = 'Confiture ou marmelade ou gelée, tout type de fruits, non allégée en sucres (aliment moyen)'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Cordon bleu de volaille'
    WHERE name = 'Cordon bleu de volaille, préemballé'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Cornichon'
    WHERE name = 'Cornichon, au vinaigre'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Courge butternut (doubeurre)'
    WHERE name = 'Courge butternut (doubeurre), chair sans peau, crue'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Courgette'
    WHERE name = 'Courgette, chair et peau, crue'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Crème 30% MG'
    WHERE name = 'Crème 30% MG, fluide, UHT'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Cumin'
    WHERE name = 'Cumin, graine'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Curry'
    WHERE name = 'Curry, poudre'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Dinde'
    WHERE name = 'Dinde, viande crue'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Endive'
    WHERE name = 'Endive, crue'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Épinard'
    WHERE name = 'Épinard, cru'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Feuilleté ou friand au fromage'
    WHERE name = 'Feuilleté ou friand au fromage, préemballé, cuit'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Fève'
    WHERE name = 'Fève, pelée, fraîche, surgelée, crue'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Flammenkueche ou tarte flambée aux lardons'
    WHERE name = 'Flammenkueche ou tarte flambée aux lardons, préemballée'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Fraise'
    WHERE name = 'Fraise, crue'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Fromage blanc'
    WHERE name = 'Fromage blanc, nature, 0% MG'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Fromage frais ou spécialité fromagère non affinée'
    WHERE name = 'Fromage frais ou spécialité fromagère non affinée, nature, à tartiner, en barquette, non allégée en matière grasse'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Fromage type feta'
    WHERE name = 'Fromage type feta, au lait de vache 100%'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Glace ou crème glacée'
    WHERE name = 'Glace ou crème glacée, bac ou pot (aliment moyen)'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Gnocchi à la pomme de terre'
    WHERE name = 'Gnocchi à la pomme de terre, à cuire'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Graine de couscous (semoule de blé dur précuite)'
    WHERE name = 'Graine de couscous (semoule de blé dur précuite), à cuire'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Haricot rouge'
    WHERE name = 'Haricot rouge, appertisé, égoutté'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Haricot vert'
    WHERE name = 'Haricot vert, cru'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Herbes de Provence'
    WHERE name = 'Herbes de Provence, séchées'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Jambon cuit'
    WHERE name = 'Jambon cuit, supérieur'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Jus d''orange'
    WHERE name = 'Jus d''orange, frais'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Kiwi'
    WHERE name = 'Kiwi, chair sans peau, avec pépins, cru'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Lait demi-écrémé'
    WHERE name = 'Lait demi-écrémé, UHT'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Lardon nature'
    WHERE name = 'Lardon nature, cru'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Lentille blonde'
    WHERE name = 'Lentille blonde, sèche'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Lieu ou colin d''Alaska'
    WHERE name = 'Lieu ou colin d''Alaska, cru'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Macédoine de légumes'
    WHERE name = 'Macédoine de légumes, appertisée, égouttée'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Maïs doux'
    WHERE name = 'Maïs doux, appertisé, égoutté'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Maquereau'
    WHERE name = 'Maquereau, filet (grillé ou non), au naturel, appertisé, égoutté'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Melon cantaloup (par ex.: Charentais)'
    WHERE name = 'Melon cantaloup (par ex.: Charentais), chair sans peau, sans pépins, cru'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Myrtille'
    WHERE name = 'Myrtille, crue'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Navet'
    WHERE name = 'Navet, pelé, cru'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Noix'
    WHERE name = 'Noix, cerneau, séchée'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Oignon'
    WHERE name = 'Oignon, cru'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Orange'
    WHERE name = 'Orange, chair sans peau, sans pépins, crue'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Origan'
    WHERE name = 'Origan, séché'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Pain de mie blanc'
    WHERE name = 'Pain de mie blanc, préemballé'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Paprika'
    WHERE name = 'Paprika, poudre'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Patate douce'
    WHERE name = 'Patate douce, crue'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Pâte feuilletée'
    WHERE name = 'Pâte feuilletée, matière grasse végétale, crue'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Pâtes fraîches farcies (ex : raviolis'
    WHERE name = 'Pâtes fraîches farcies (ex : raviolis, tortellinis), cuites (aliment moyen)'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Pâtes sèches'
    WHERE name = 'Pâtes sèches, standard, crues'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Petits pois'
    WHERE name = 'Petits pois, crus'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Piment'
    WHERE name = 'Piment, cru'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Poire'
    WHERE name = 'Poire, chair et peau, crue'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Poireau'
    WHERE name = 'Poireau, cru'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Pois chiche'
    WHERE name = 'Pois chiche, sec'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Poisson pané'
    WHERE name = 'Poisson pané, surgelé, cru'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Poivre noir'
    WHERE name = 'Poivre noir, poudre'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Poivron vert'
    WHERE name = 'Poivron vert, cru'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Polenta ou semoule de maïs'
    WHERE name = 'Polenta ou semoule de maïs, précuite, à cuire'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Pomme de terre noisette'
    WHERE name = 'Pomme de terre noisette, surgelée, à cuire'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Pomme de terre'
    WHERE name = 'Pomme de terre, sans peau, crue'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Pomme'
    WHERE name = 'Pomme, chair et peau, crue'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Porc épaule'
    WHERE name = 'Porc, épaule crue'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Porc rôti'
    WHERE name = 'Porc, filet maigre, en rôti, cuit'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Porc filet mignon'
    WHERE name = 'Porc, filet mignon cru'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Potimarron'
    WHERE name = 'Potimarron, chair sans peau, cru'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Poulet'
    WHERE name = 'Poulet, viande crue'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Préparation à base de fromage(s) pour fondue savoyarde'
    WHERE name = 'Préparation à base de fromage(s) pour fondue savoyarde, préemballée'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Quatre-quarts (beurre'
    WHERE name = 'Quatre-quarts (beurre, oeufs, sucre, farine), artisanal'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Quenelle nature'
    WHERE name = 'Quenelle nature, à cuire'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Quinoa'
    WHERE name = 'Quinoa, cru'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Riz blanc'
    WHERE name = 'Riz blanc, cru'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Salade composée avec viande ou poisson'
    WHERE name = 'Salade composée avec viande ou poisson, appertisée'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Salade verte'
    WHERE name = 'Salade verte, crue, sans assaisonnement'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Sardine'
    WHERE name = 'Sardine, crue'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Sauce soja'
    WHERE name = 'Sauce soja, préemballée'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Saucisse de Strasbourg ou knack'
    WHERE name = 'Saucisse de Strasbourg ou knack, à cuire'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Saumon'
    WHERE name = 'Saumon, élevage, cru'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Sel blanc alimentaire'
    WHERE name = 'Sel blanc alimentaire, non iodé, non fluoré (marin, ignigène ou gemme)'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Taboulé ou salade de semoule aux légumes'
    WHERE name = 'Taboulé ou salade de semoule aux légumes, préemballé'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Thé infusé'
    WHERE name = 'Thé infusé, sans sucres ajoutés'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Thon à la tomate'
    WHERE name = 'Thon à la tomate, miettes, appertisées, égouttées'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Thon'
    WHERE name = 'Thon, cru'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Tofu nature'
    WHERE name = 'Tofu nature, préemballé'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Tomate sans précision'
    WHERE name = 'Tomate sans précision, crue (aliment moyen)'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Tomate'
    WHERE name = 'Tomate, concentré, appertisé'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Tortilla souple (à garnir)'
    WHERE name = 'Tortilla souple (à garnir), à base de blé'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Veau'
    WHERE name = 'Veau, escalope crue'
      AND (nom_affiche IS NULL OR nom_affiche = '');
UPDATE ingredients SET nom_affiche = 'Yaourt ou lait fermenté'
    WHERE name = 'Yaourt ou lait fermenté, nature'
      AND (nom_affiche IS NULL OR nom_affiche = '');

-- Contrôle : plus aucun aliment de la base ne doit afficher son libellé
-- Ciqual complet. Toute ligne renvoyée est un nom non couvert par ce script.
SELECT name, nom_affiche
  FROM ingredients
 WHERE (nom_affiche IS NULL OR nom_affiche = '')
   AND name IN ('Ail, cru',
           'Aubergine, crue',
           'Banane, chair sans peau, crue',
           'Betterave rouge, crue',
           'Beurre à 80% MG minimum, doux',
           'Boeuf, faux-filet rôti/cuit au four',
           'Boeuf, steak haché 15% MG cuit',
           'Bouillon de boeuf, déshydraté reconstitué',
           'Bouillon de légumes, déshydraté reconstitué',
           'Bouillon de volaille, déshydraté',
           'Boulettes au boeuf, à la sauce tomate, préemballées',
           'Brocoli, cru',
           'Cacao, sans sucres ajoutés, poudre soluble',
           'Café, non instantané, sans sucres ajoutés, prêt à boire',
           'Carotte, crue',
           'Champignon de Paris ou champignon de couche, cru',
           'Chocolat noir 50 % de cacao environ, tablette',
           'Chou-fleur, cru',
           'Citron, chair sans peau, sans pépins, cru',
           'Compote de pomme, préemballée',
           'Concombre, chair et peau, cru',
           'Confiture ou marmelade ou gelée, tout type de fruits, non allégée en sucres (aliment moyen)',
           'Cordon bleu de volaille, préemballé',
           'Cornichon, au vinaigre',
           'Courge butternut (doubeurre), chair sans peau, crue',
           'Courgette, chair et peau, crue',
           'Crème 30% MG, fluide, UHT',
           'Cumin, graine',
           'Curry, poudre',
           'Dinde, viande crue',
           'Endive, crue',
           'Épinard, cru',
           'Feuilleté ou friand au fromage, préemballé, cuit',
           'Fève, pelée, fraîche, surgelée, crue',
           'Flammenkueche ou tarte flambée aux lardons, préemballée',
           'Fraise, crue',
           'Fromage blanc, nature, 0% MG',
           'Fromage frais ou spécialité fromagère non affinée, nature, à tartiner, en barquette, non allégée en matière grasse',
           'Fromage type feta, au lait de vache 100%',
           'Glace ou crème glacée, bac ou pot (aliment moyen)',
           'Gnocchi à la pomme de terre, à cuire',
           'Graine de couscous (semoule de blé dur précuite), à cuire',
           'Haricot rouge, appertisé, égoutté',
           'Haricot vert, cru',
           'Herbes de Provence, séchées',
           'Jambon cuit, supérieur',
           'Jus d''orange, frais',
           'Kiwi, chair sans peau, avec pépins, cru',
           'Lait demi-écrémé, UHT',
           'Lardon nature, cru',
           'Lentille blonde, sèche',
           'Lieu ou colin d''Alaska, cru',
           'Macédoine de légumes, appertisée, égouttée',
           'Maïs doux, appertisé, égoutté',
           'Maquereau, filet (grillé ou non), au naturel, appertisé, égoutté',
           'Melon cantaloup (par ex.: Charentais), chair sans peau, sans pépins, cru',
           'Myrtille, crue',
           'Navet, pelé, cru',
           'Noix, cerneau, séchée',
           'Oignon, cru',
           'Orange, chair sans peau, sans pépins, crue',
           'Origan, séché',
           'Pain de mie blanc, préemballé',
           'Paprika, poudre',
           'Patate douce, crue',
           'Pâte feuilletée, matière grasse végétale, crue',
           'Pâtes fraîches farcies (ex : raviolis, tortellinis), cuites (aliment moyen)',
           'Pâtes sèches, standard, crues',
           'Petits pois, crus',
           'Piment, cru',
           'Poire, chair et peau, crue',
           'Poireau, cru',
           'Pois chiche, sec',
           'Poisson pané, surgelé, cru',
           'Poivre noir, poudre',
           'Poivron vert, cru',
           'Polenta ou semoule de maïs, précuite, à cuire',
           'Pomme de terre noisette, surgelée, à cuire',
           'Pomme de terre, sans peau, crue',
           'Pomme, chair et peau, crue',
           'Porc, épaule crue',
           'Porc, filet maigre, en rôti, cuit',
           'Porc, filet mignon cru',
           'Potimarron, chair sans peau, cru',
           'Poulet, viande crue',
           'Préparation à base de fromage(s) pour fondue savoyarde, préemballée',
           'Quatre-quarts (beurre, oeufs, sucre, farine), artisanal',
           'Quenelle nature, à cuire',
           'Quinoa, cru',
           'Riz blanc, cru',
           'Salade composée avec viande ou poisson, appertisée',
           'Salade verte, crue, sans assaisonnement',
           'Sardine, crue',
           'Sauce soja, préemballée',
           'Saucisse de Strasbourg ou knack, à cuire',
           'Saumon, élevage, cru',
           'Sel blanc alimentaire, non iodé, non fluoré (marin, ignigène ou gemme)',
           'Taboulé ou salade de semoule aux légumes, préemballé',
           'Thé infusé, sans sucres ajoutés',
           'Thon à la tomate, miettes, appertisées, égouttées',
           'Thon, cru',
           'Tofu nature, préemballé',
           'Tomate sans précision, crue (aliment moyen)',
           'Tomate, concentré, appertisé',
           'Tortilla souple (à garnir), à base de blé',
           'Veau, escalope crue',
           'Yaourt ou lait fermenté, nature')
 ORDER BY name;
