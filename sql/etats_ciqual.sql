-- ============================================================================
--  VALEURS CRU / CUIT — source Ciqual ANSES 2025
--
--  À exécuter APRÈS sql/etat_cru_cuit.sql (qui crée les colonnes).
--
--  Chaque valeur est recopiée d'une entrée Ciqual réelle. Rien n'est calculé :
--  la perte d'eau va de +1 % (pomme de terre 80 -> 81 kcal) à -58 %
--  (pois chiche 350 -> 148 kcal) selon l'aliment et le mode de cuisson.
--
--  Les UPDATE ne touchent que les aliments déjà présents dans votre table,
--  appariés sur lower(name). Un aliment absent n'est pas créé : c'est le rôle
--  de sql/aliments_courants.sql.
--
--  etat_defaut : proposition à valider ligne par ligne. Les féculents et
--  légumineuses partent sur « cuit » parce que leur état cru est sec et
--  immangeable ; les légumes sur « cru ».
--
--  Glucides à NULL : Ciqual ne les renseigne pas pour le poisson (saumon,
--  cabillaud). L'application retombe alors sur la colonne historique, elle
--  n'invente pas de valeur.
-- ============================================================================

-- Pâtes              Ciqual 9810 (cru) / 9811 (cuit) — défaut : cuit
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
WHERE lower(name) = lower('Pâtes');

-- Riz blanc          Ciqual 9100 (cru) / 9104 (cuit) — défaut : cuit
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
WHERE lower(name) = lower('Riz blanc');

-- Riz complet        Ciqual 9102 (cru) / 9103 (cuit) — défaut : cuit
UPDATE ingredients SET
    kcal_100g_cru = 350,
    proteines_100g_cru = 7.38,
    glucides_100g_cru = 71.4,
    lipides_100g_cru = 2.8,
    kcal_100g_cuit = 187,
    proteines_100g_cuit = 4.06,
    glucides_100g_cuit = 37.6,
    lipides_100g_cuit = 1.8,
    etat_defaut = 'cuit'
WHERE lower(name) = lower('Riz complet');

-- Semoule            Ciqual 9610 (cru) / 9683 (cuit) — défaut : cuit
UPDATE ingredients SET
    kcal_100g_cru = 350,
    proteines_100g_cru = 13,
    glucides_100g_cru = 69.8,
    lipides_100g_cru = 1.28,
    kcal_100g_cuit = 164,
    proteines_100g_cuit = 6.38,
    glucides_100g_cuit = 31,
    lipides_100g_cuit = 0.9,
    etat_defaut = 'cuit'
WHERE lower(name) = lower('Semoule');

-- Quinoa             Ciqual 9340 (cru) / 9341 (cuit) — défaut : cuit
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
WHERE lower(name) = lower('Quinoa');

-- Boulgour           Ciqual 9690 (cru) / 9691 (cuit) — défaut : cuit
UPDATE ingredients SET
    kcal_100g_cru = 347,
    proteines_100g_cru = 12.6,
    glucides_100g_cru = 65.8,
    lipides_100g_cru = 1.42,
    kcal_100g_cuit = 131,
    proteines_100g_cuit = 4.63,
    glucides_100g_cuit = 24.1,
    lipides_100g_cuit = 1,
    etat_defaut = 'cuit'
WHERE lower(name) = lower('Boulgour');

-- Lentilles          Ciqual 20359 (cru) / 20360 (cuit) — défaut : cuit
UPDATE ingredients SET
    kcal_100g_cru = 327,
    proteines_100g_cru = 25.1,
    glucides_100g_cru = 44.5,
    lipides_100g_cru = 1.8,
    kcal_100g_cuit = 125,
    proteines_100g_cuit = 10.1,
    glucides_100g_cuit = 16.2,
    lipides_100g_cuit = 0.57,
    etat_defaut = 'cuit'
WHERE lower(name) = lower('Lentilles');

-- Pois chiches       Ciqual 20516 (cru) / 20507 (cuit) — défaut : cuit
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
WHERE lower(name) = lower('Pois chiches');

-- Haricots rouges    Ciqual 20525 (cru) / 20503 (cuit) — défaut : cuit
UPDATE ingredients SET
    kcal_100g_cru = 314,
    proteines_100g_cru = 22.5,
    glucides_100g_cru = 46.1,
    lipides_100g_cru = 1.06,
    kcal_100g_cuit = 116,
    proteines_100g_cuit = 9.63,
    glucides_100g_cuit = 12.3,
    lipides_100g_cuit = 0.6,
    etat_defaut = 'cuit'
WHERE lower(name) = lower('Haricots rouges');

-- Haricots blancs    Ciqual 20501 (cru) / 20502 (cuit) — défaut : cuit
UPDATE ingredients SET
    kcal_100g_cru = 307,
    proteines_100g_cru = 23.4,
    glucides_100g_cru = 43.9,
    lipides_100g_cru = 0.85,
    kcal_100g_cuit = 112,
    proteines_100g_cuit = 6.75,
    glucides_100g_cuit = 12,
    lipides_100g_cuit = 1.1,
    etat_defaut = 'cuit'
WHERE lower(name) = lower('Haricots blancs');

-- Maïs doux          Ciqual 20233 (cru) / 20049 (cuit) — défaut : cuit
UPDATE ingredients SET
    kcal_100g_cru = 105,
    proteines_100g_cru = 3.28,
    glucides_100g_cru = 19.8,
    lipides_100g_cru = 0.78,
    kcal_100g_cuit = 106,
    proteines_100g_cuit = 3.41,
    glucides_100g_cuit = 18.6,
    lipides_100g_cuit = 1.5,
    etat_defaut = 'cuit'
WHERE lower(name) = lower('Maïs doux');

-- Pomme de terre     Ciqual 4008 (cru) / 4003 (cuit) — défaut : cru
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
WHERE lower(name) = lower('Pomme de terre');

-- Patate douce       Ciqual 4101 (cru) / 4102 (cuit) — défaut : cru
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
WHERE lower(name) = lower('Patate douce');

-- Carotte            Ciqual 20009 (cru) / 20306 (cuit) — défaut : cru
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
WHERE lower(name) = lower('Carotte');

-- Épinard            Ciqual 20059 (cru) / 20027 (cuit) — défaut : cru
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
WHERE lower(name) = lower('Épinard');

-- Brocoli            Ciqual 20057 (cru) / 20302 (cuit) — défaut : cru
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
WHERE lower(name) = lower('Brocoli');

-- Courgette          Ciqual 20020 (cru) / 20021 (cuit) — défaut : cru
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
WHERE lower(name) = lower('Courgette');

-- Chou-fleur         Ciqual 20016 (cru) / 20017 (cuit) — défaut : cru
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
WHERE lower(name) = lower('Chou-fleur');

-- Haricot vert       Ciqual 20061 (cru) / 20030 (cuit) — défaut : cru
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
WHERE lower(name) = lower('Haricot vert');

-- Poireau            Ciqual 20039 (cru) / 20327 (cuit) — défaut : cru
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
WHERE lower(name) = lower('Poireau');

-- Oignon             Ciqual 20034 (cru) / 20035 (cuit) — défaut : cru
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
WHERE lower(name) = lower('Oignon');

-- Tomate             Ciqual 20385 (cru) / 20358 (cuit) — défaut : cru
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
WHERE lower(name) = lower('Tomate');

-- Poivron rouge      Ciqual 20087 (cru) / 19999 (cuit) — défaut : cru
UPDATE ingredients SET
    kcal_100g_cru = 33.6,
    proteines_100g_cru = 1.06,
    glucides_100g_cru = 5.98,
    lipides_100g_cru = 0.5,
    kcal_100g_cuit = 33,
    proteines_100g_cuit = 1.11,
    glucides_100g_cuit = 5.42,
    lipides_100g_cuit = 0.33,
    etat_defaut = 'cru'
WHERE lower(name) = lower('Poivron rouge');

-- Aubergine          Ciqual 20053 (cru) / 20002 (cuit) — défaut : cru
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
WHERE lower(name) = lower('Aubergine');

-- Champignon         Ciqual 20056 (cru) / 20102 (cuit) — défaut : cru
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
WHERE lower(name) = lower('Champignon');

-- Céleri branche     Ciqual 20023 (cru) / 20354 (cuit) — défaut : cru
UPDATE ingredients SET
    kcal_100g_cru = 15.4,
    proteines_100g_cru = 0.63,
    glucides_100g_cru = 2.41,
    lipides_100g_cru = 0.5,
    kcal_100g_cuit = 13.1,
    proteines_100g_cuit = 0.63,
    glucides_100g_cuit = 1.38,
    lipides_100g_cuit = 0.15,
    etat_defaut = 'cru'
WHERE lower(name) = lower('Céleri branche');

-- Poulet             Ciqual 36017 (cru) / 36018 (cuit) — défaut : cuit
UPDATE ingredients SET
    kcal_100g_cru = 110,
    proteines_100g_cru = 23.4,
    glucides_100g_cru = 0,
    lipides_100g_cru = 1.5,
    kcal_100g_cuit = 141,
    proteines_100g_cuit = 30.1,
    glucides_100g_cuit = 0,
    lipides_100g_cuit = 2,
    etat_defaut = 'cuit'
WHERE lower(name) = lower('Poulet');

-- Steak              Ciqual 6201 (cru) / 6200 (cuit) — défaut : cuit
UPDATE ingredients SET
    kcal_100g_cru = 229,
    proteines_100g_cru = 18.7,
    glucides_100g_cru = 0.06,
    lipides_100g_cru = 17.2,
    kcal_100g_cuit = 128,
    proteines_100g_cuit = 27.6,
    glucides_100g_cuit = 0,
    lipides_100g_cuit = 1.95,
    etat_defaut = 'cuit'
WHERE lower(name) = lower('Steak');

-- Steak haché 5%     Ciqual 6250 (cru) / 6251 (cuit) — défaut : cuit
UPDATE ingredients SET
    kcal_100g_cru = 130,
    proteines_100g_cru = 21.9,
    glucides_100g_cru = 0.3,
    lipides_100g_cru = 4.59,
    kcal_100g_cuit = 155,
    proteines_100g_cuit = 25.5,
    glucides_100g_cuit = 0,
    lipides_100g_cuit = 5.85,
    etat_defaut = 'cuit'
WHERE lower(name) = lower('Steak haché 5%');

-- Steak haché 10%    Ciqual 6252 (cru) / 6253 (cuit) — défaut : cuit
UPDATE ingredients SET
    kcal_100g_cru = 170,
    proteines_100g_cru = 20,
    glucides_100g_cru = 0,
    lipides_100g_cru = 10,
    kcal_100g_cuit = 210,
    proteines_100g_cuit = 26.1,
    glucides_100g_cuit = 0,
    lipides_100g_cuit = 11.8,
    etat_defaut = 'cuit'
WHERE lower(name) = lower('Steak haché 10%');

-- Saumon             Ciqual 26036 (cru) / 26038 (cuit) — défaut : cuit
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
WHERE lower(name) = lower('Saumon');

-- Cabillaud          Ciqual 26043 (cru) / 25997 (cuit) — défaut : cuit
UPDATE ingredients SET
    kcal_100g_cru = 77.4,
    proteines_100g_cru = 18.1,
    glucides_100g_cru = NULL,
    lipides_100g_cru = 0.57,
    kcal_100g_cuit = 100,
    proteines_100g_cuit = 23.3,
    glucides_100g_cuit = NULL,
    lipides_100g_cuit = 0.76,
    etat_defaut = 'cuit'
WHERE lower(name) = lower('Cabillaud');

-- Crevette           Ciqual 10021 (cru) / 10007 (cuit) — défaut : cuit
UPDATE ingredients SET
    kcal_100g_cru = 99,
    proteines_100g_cru = 19.7,
    glucides_100g_cru = 3.21,
    lipides_100g_cru = 0.84,
    kcal_100g_cuit = 91.3,
    proteines_100g_cuit = 20.5,
    glucides_100g_cuit = 0.2,
    lipides_100g_cuit = 0.79,
    etat_defaut = 'cuit'
WHERE lower(name) = lower('Crevette');

-- ---------------------------------------------------------------------------
--  Contrôle : ce qui a été renseigné
-- ---------------------------------------------------------------------------

SELECT name, etat_defaut,
       kcal_100g_cru, kcal_100g_cuit,
       proteines_100g_cru, proteines_100g_cuit
FROM ingredients
WHERE kcal_100g_cru IS NOT NULL OR kcal_100g_cuit IS NOT NULL
ORDER BY name;

-- Si une ligne attendue manque ci-dessus, c'est que le nom diffère chez vous
-- (« Pâtes » vs « Pâtes sèches », par exemple). Ce bloc liste ce qui reste
-- sans valeur d'état :
--
-- SELECT name FROM ingredients
-- WHERE kcal_100g_cru IS NULL AND kcal_100g_cuit IS NULL
-- ORDER BY name;
