-- ============================================================================
--  VALEURS CRU / CUIT — régénéré d'après VOTRE base
--
--  À exécuter APRÈS sql/etat_cru_cuit.sql (qui crée les colonnes).
--
--  Les UPDATE sont appariés sur VOS noms exacts, retrouvés par code Ciqual
--  dans la liste que vous m'avez envoyée. La version précédente de ce fichier
--  cherchait des noms courts (« Carotte », « Pâtes ») qui n'existent pas chez
--  vous : elle se serait exécutée sans erreur et sans rien modifier.
--
--  Chaque macro est recopiée d'une entrée Ciqual réelle, aucune n'est calculée.
-- ============================================================================

-- Pâtes            votre ligne : « Pâtes sèches, standard, crues »
--                  Ciqual 9810 (cru) / 9811 (cuit)
UPDATE ingredients SET
    kcal_100g_cru = 364,
    proteines_100g_cru = 13.1,
    glucides_100g_cru = 72.7,
    lipides_100g_cru = 1.6,
    kcal_100g_cuit = 167,
    proteines_100g_cuit = 6.69,
    glucides_100g_cuit = 31.4,
    lipides_100g_cuit = 1.1,
    etat_defaut = 'cuit'
WHERE name = 'Pâtes sèches, standard, crues';

-- Riz blanc        votre ligne : « Riz blanc, cru »
--                  Ciqual 9100 (cru) / 9104 (cuit)
UPDATE ingredients SET
    kcal_100g_cru = 350,
    proteines_100g_cru = 7.38,
    glucides_100g_cru = 77.5,
    lipides_100g_cru = 0.79,
    kcal_100g_cuit = 155,
    proteines_100g_cuit = 3.31,
    glucides_100g_cuit = 33.2,
    lipides_100g_cuit = 0.7,
    etat_defaut = 'cuit'
WHERE name = 'Riz blanc, cru';

-- Quinoa           votre ligne : « Quinoa, cru »
--                  Ciqual 9340 (cru) / 9341 (cuit)
UPDATE ingredients SET
    kcal_100g_cru = 358,
    proteines_100g_cru = 14.1,
    glucides_100g_cru = 58.1,
    lipides_100g_cru = 6.07,
    kcal_100g_cuit = 149,
    proteines_100g_cuit = 5,
    glucides_100g_cuit = 27.9,
    lipides_100g_cuit = 1.1,
    etat_defaut = 'cuit'
WHERE name = 'Quinoa, cru';

-- Pois chiche      votre ligne : « Pois chiche, sec »
--                  Ciqual 20516 (cru) / 20507 (cuit)
UPDATE ingredients SET
    kcal_100g_cru = 350,
    proteines_100g_cru = 20.5,
    glucides_100g_cru = 47.5,
    lipides_100g_cru = 6.04,
    kcal_100g_cuit = 148,
    proteines_100g_cuit = 8.31,
    glucides_100g_cuit = 17.7,
    lipides_100g_cuit = 3,
    etat_defaut = 'cuit'
WHERE name = 'Pois chiche, sec';

-- Lentille         votre ligne : « Lentille blonde, sèche »
--                  Ciqual 20586 (cru) / 20588 (cuit)
UPDATE ingredients SET
    kcal_100g_cru = 339,
    proteines_100g_cru = 26.1,
    glucides_100g_cru = 48.3,
    lipides_100g_cru = 1.9,
    kcal_100g_cuit = 122,
    proteines_100g_cuit = 9.7,
    glucides_100g_cuit = 16.3,
    lipides_100g_cuit = 0.7,
    etat_defaut = 'cuit'
WHERE name = 'Lentille blonde, sèche';

-- Pomme de terre   votre ligne : « Pomme de terre, sans peau, crue »
--                  Ciqual 4008 (cru) / 4003 (cuit)
UPDATE ingredients SET
    kcal_100g_cru = 80,
    proteines_100g_cru = 2.02,
    glucides_100g_cru = 16.2,
    lipides_100g_cru = 0.09,
    kcal_100g_cuit = 81,
    proteines_100g_cuit = 1.8,
    glucides_100g_cuit = 16.8,
    lipides_100g_cuit = 0.34,
    etat_defaut = 'cru'
WHERE name = 'Pomme de terre, sans peau, crue';

-- Patate douce     votre ligne : « Patate douce, crue »
--                  Ciqual 4101 (cru) / 4102 (cuit)
UPDATE ingredients SET
    kcal_100g_cru = 81.2,
    proteines_100g_cru = 1.57,
    glucides_100g_cru = 17.1,
    lipides_100g_cru = 0.05,
    kcal_100g_cuit = 79.1,
    proteines_100g_cuit = 1.69,
    glucides_100g_cuit = 16.3,
    lipides_100g_cuit = 0.15,
    etat_defaut = 'cru'
WHERE name = 'Patate douce, crue';

-- Carotte          votre ligne : « Carotte, crue »
--                  Ciqual 20009 (cru) / 20306 (cuit)
UPDATE ingredients SET
    kcal_100g_cru = 30.2,
    proteines_100g_cru = 0.78,
    glucides_100g_cru = 5.16,
    lipides_100g_cru = 0.5,
    kcal_100g_cuit = 29.6,
    proteines_100g_cuit = 0.25,
    glucides_100g_cuit = 5.73,
    lipides_100g_cuit = 0.3,
    etat_defaut = 'cru'
WHERE name = 'Carotte, crue';

-- Épinard          votre ligne : « Épinard, cru »
--                  Ciqual 20059 (cru) / 20027 (cuit)
UPDATE ingredients SET
    kcal_100g_cru = 33.3,
    proteines_100g_cru = 2.68,
    glucides_100g_cru = 3.06,
    lipides_100g_cru = 0.39,
    kcal_100g_cuit = 19.6,
    proteines_100g_cuit = 3.2,
    glucides_100g_cuit = 0.25,
    lipides_100g_cuit = 0.14,
    etat_defaut = 'cru'
WHERE name = 'Épinard, cru';

-- Brocoli          votre ligne : « Brocoli, cru »
--                  Ciqual 20057 (cru) / 20302 (cuit)
UPDATE ingredients SET
    kcal_100g_cru = 31.9,
    proteines_100g_cru = 2.9,
    glucides_100g_cru = 2.15,
    lipides_100g_cru = 0.36,
    kcal_100g_cuit = 22.2,
    proteines_100g_cuit = 2.5,
    glucides_100g_cuit = 1.23,
    lipides_100g_cuit = 0.4,
    etat_defaut = 'cru'
WHERE name = 'Brocoli, cru';

-- Courgette        votre ligne : « Courgette, chair et peau, crue »
--                  Ciqual 20020 (cru) / 20021 (cuit)
UPDATE ingredients SET
    kcal_100g_cru = 16.7,
    proteines_100g_cru = 1.21,
    glucides_100g_cru = 1.75,
    lipides_100g_cru = 0.32,
    kcal_100g_cuit = 15.5,
    proteines_100g_cuit = 0.93,
    glucides_100g_cuit = 1.4,
    lipides_100g_cuit = 0.36,
    etat_defaut = 'cru'
WHERE name = 'Courgette, chair et peau, crue';

-- Chou-fleur       votre ligne : « Chou-fleur, cru »
--                  Ciqual 20016 (cru) / 20017 (cuit)
UPDATE ingredients SET
    kcal_100g_cru = 24.9,
    proteines_100g_cru = 1.81,
    glucides_100g_cru = 2.13,
    lipides_100g_cru = 0.7,
    kcal_100g_cuit = 20.9,
    proteines_100g_cuit = 1.6,
    glucides_100g_cuit = 1.6,
    lipides_100g_cuit = 0.46,
    etat_defaut = 'cru'
WHERE name = 'Chou-fleur, cru';

-- Haricot vert     votre ligne : « Haricot vert, cru »
--                  Ciqual 20061 (cru) / 20030 (cuit)
UPDATE ingredients SET
    kcal_100g_cru = 31.9,
    proteines_100g_cru = 1.83,
    glucides_100g_cru = 4.14,
    lipides_100g_cru = 0.22,
    kcal_100g_cuit = 29.4,
    proteines_100g_cuit = 2,
    glucides_100g_cuit = 3,
    lipides_100g_cuit = 0.17,
    etat_defaut = 'cru'
WHERE name = 'Haricot vert, cru';

-- Poireau          votre ligne : « Poireau, cru »
--                  Ciqual 20039 (cru) / 20327 (cuit)
UPDATE ingredients SET
    kcal_100g_cru = 30.4,
    proteines_100g_cru = 1.5,
    glucides_100g_cru = 4.55,
    lipides_100g_cru = 0.3,
    kcal_100g_cuit = 24.7,
    proteines_100g_cuit = 2.56,
    glucides_100g_cuit = 2.23,
    lipides_100g_cuit = 0.3,
    etat_defaut = 'cru'
WHERE name = 'Poireau, cru';

-- Oignon           votre ligne : « Oignon, cru »
--                  Ciqual 20034 (cru) / 20035 (cuit)
UPDATE ingredients SET
    kcal_100g_cru = 39,
    proteines_100g_cru = 1.1,
    glucides_100g_cru = 6.25,
    lipides_100g_cru = 0.62,
    kcal_100g_cuit = 34.6,
    proteines_100g_cuit = 1.3,
    glucides_100g_cuit = 6.2,
    lipides_100g_cuit = 0.2,
    etat_defaut = 'cru'
WHERE name = 'Oignon, cru';

-- Tomate           votre ligne : « Tomate sans précision, crue (aliment moyen) »
--                  Ciqual 20385 (cru) / 20358 (cuit)
UPDATE ingredients SET
    kcal_100g_cru = 19.2,
    proteines_100g_cru = 0.6,
    glucides_100g_cru = 3.69,
    lipides_100g_cru = 0.5,
    kcal_100g_cuit = 19.8,
    proteines_100g_cuit = 0.97,
    glucides_100g_cuit = 3.06,
    lipides_100g_cuit = 0.21,
    etat_defaut = 'cru'
WHERE name = 'Tomate sans précision, crue (aliment moyen)';

-- Poivron vert     votre ligne : « Poivron vert, cru »
--                  Ciqual 20085 (cru) / 19999 (cuit)
UPDATE ingredients SET
    kcal_100g_cru = 22.5,
    proteines_100g_cru = 0.81,
    glucides_100g_cru = 3.43,
    lipides_100g_cru = 0.5,
    kcal_100g_cuit = 33,
    proteines_100g_cuit = 1.11,
    glucides_100g_cuit = 5.42,
    lipides_100g_cuit = 0.33,
    etat_defaut = 'cru'
WHERE name = 'Poivron vert, cru';

-- Aubergine        votre ligne : « Aubergine, crue »
--                  Ciqual 20053 (cru) / 20002 (cuit)
UPDATE ingredients SET
    kcal_100g_cru = 22.9,
    proteines_100g_cru = 0.98,
    glucides_100g_cru = 2.7,
    lipides_100g_cru = 0.18,
    kcal_100g_cuit = 27.1,
    proteines_100g_cuit = 0.83,
    glucides_100g_cuit = 4.17,
    lipides_100g_cuit = 0.23,
    etat_defaut = 'cru'
WHERE name = 'Aubergine, crue';

-- Champignon       votre ligne : « Champignon de Paris ou champignon de couche, cru »
--                  Ciqual 20056 (cru) / 20102 (cuit)
UPDATE ingredients SET
    kcal_100g_cru = 21,
    proteines_100g_cru = 2.11,
    glucides_100g_cru = 1.83,
    lipides_100g_cru = 0.36,
    kcal_100g_cuit = 28.7,
    proteines_100g_cuit = 2.17,
    glucides_100g_cuit = 3,
    lipides_100g_cuit = 0.47,
    etat_defaut = 'cru'
WHERE name = 'Champignon de Paris ou champignon de couche, cru';

-- Saumon           votre ligne : « Saumon, élevage, cru »
--                  Ciqual 26036 (cru) / 26038 (cuit)
UPDATE ingredients SET
    kcal_100g_cru = 193,
    proteines_100g_cru = 20.5,
    glucides_100g_cru = NULL,
    lipides_100g_cru = 12.4,
    kcal_100g_cuit = 199,
    proteines_100g_cuit = 23,
    glucides_100g_cuit = 0.9,
    lipides_100g_cuit = 11.5,
    etat_defaut = 'cuit'
WHERE name = 'Saumon, élevage, cru';

-- ---------------------------------------------------------------------------
--  Contrôle : chaque UPDATE doit toucher exactement 1 ligne
-- ---------------------------------------------------------------------------

SELECT name, etat_defaut,
       kcal_100g_cru, kcal_100g_cuit,
       proteines_100g_cru, proteines_100g_cuit
FROM ingredients
WHERE kcal_100g_cru IS NOT NULL OR kcal_100g_cuit IS NOT NULL
ORDER BY name;
