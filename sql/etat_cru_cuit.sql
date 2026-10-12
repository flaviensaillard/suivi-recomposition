-- ============================================================================
--  ÉTAT CRU / CUIT DES ALIMENTS
--
--  Le même aliment n'a pas les mêmes macros pesé cru ou pesé cuit :
--      100 g de pâtes sèches      364 kcal
--      100 g de pâtes cuites      167 kcal      (-54 %)
--      100 g de pois chiche sec   350 kcal
--      100 g de pois chiche cuit  148 kcal      (-58 %)
--      100 g de pomme de terre     80 kcal  ->  81 kcal cuites (+1 %)
--
--  Aucun coefficient de conversion n'est appliqué : la perte d'eau dépend de
--  l'aliment ET du mode de cuisson. Une valeur d'état absente retombe sur la
--  colonne historique correspondante, jamais sur un calcul.
--
--  Les tables de menus ne sont PAS préfixées (net.js:449), contrairement au
--  suivi personnel qui est en sr_ (net.js:352).
--
--  Idempotent : relancer ce script ne fait rien.
-- ============================================================================


-- ---------------------------------------------------------------------------
-- 1. INGRÉDIENTS : un jeu de macros par état
--
--    Les colonnes historiques (kcal_100g, proteines_100g, …) restent la
--    référence et servent de repli. Aucun aliment existant n'est re-labellisé :
--    « Riz blanc cuit » garde ses valeurs telles quelles.
-- ---------------------------------------------------------------------------

ALTER TABLE ingredients ADD COLUMN IF NOT EXISTS etat_defaut        text;

ALTER TABLE ingredients ADD COLUMN IF NOT EXISTS kcal_100g_cru      numeric(7,2);
ALTER TABLE ingredients ADD COLUMN IF NOT EXISTS proteines_100g_cru numeric(6,2);
ALTER TABLE ingredients ADD COLUMN IF NOT EXISTS glucides_100g_cru  numeric(6,2);
ALTER TABLE ingredients ADD COLUMN IF NOT EXISTS lipides_100g_cru   numeric(6,2);

ALTER TABLE ingredients ADD COLUMN IF NOT EXISTS kcal_100g_cuit      numeric(7,2);
ALTER TABLE ingredients ADD COLUMN IF NOT EXISTS proteines_100g_cuit numeric(6,2);
ALTER TABLE ingredients ADD COLUMN IF NOT EXISTS glucides_100g_cuit  numeric(6,2);
ALTER TABLE ingredients ADD COLUMN IF NOT EXISTS lipides_100g_cuit   numeric(6,2);

-- Par défaut tout est considéré cru, sauf mention contraire sur l'aliment.
UPDATE ingredients SET etat_defaut = 'cru' WHERE etat_defaut IS NULL;


-- ---------------------------------------------------------------------------
-- 2. LIGNES DE RECETTE : l'état pesé se choisit par ingrédient
--
--    « Carottes râpées » utilise des carottes crues, « Velouté de carotte »
--    des carottes cuites : deux recettes, même ingrédient, états différents.
--    NULL = état par défaut de l'ingrédient.
-- ---------------------------------------------------------------------------

ALTER TABLE recipe_ingredients ADD COLUMN IF NOT EXISTS etat text;


-- ---------------------------------------------------------------------------
-- 3. VÉRIFICATION
-- ---------------------------------------------------------------------------

SELECT table_name, column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'public'
  AND ((table_name = 'ingredients' AND column_name IN
        ('etat_defaut','kcal_100g_cru','proteines_100g_cru','glucides_100g_cru','lipides_100g_cru',
         'kcal_100g_cuit','proteines_100g_cuit','glucides_100g_cuit','lipides_100g_cuit'))
    OR (table_name = 'recipe_ingredients' AND column_name = 'etat'))
ORDER BY table_name, column_name;


-- ---------------------------------------------------------------------------
-- 4. RENSEIGNER LES VALEURS D'ÉTAT
--
--    Exemple — la carotte, depuis Ciqual 20009 (crue) et 20353 (cuite) :
--
--    UPDATE ingredients SET
--        kcal_100g_cru = 30.2, proteines_100g_cru = 0.77,
--        glucides_100g_cru = 4.74, lipides_100g_cru = 0.24,
--        kcal_100g_cuit = 33.0, proteines_100g_cuit = 0.70,
--        glucides_100g_cuit = 5.90, lipides_100g_cuit = 0.20
--    WHERE lower(name) = 'carotte';
--
--    Tant qu'aucune valeur d'état n'est renseignée, le sélecteur cru/cuit
--    n'apparaît pas pour cet aliment : mieux vaut aucune valeur qu'une
--    valeur inventée.
-- ---------------------------------------------------------------------------
