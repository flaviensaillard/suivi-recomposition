/* Modèles métier et données de référence pour la recomposition corporelle. */
(function (root) {
    'use strict';
    var EQ = root.EQ = root.EQ || {};
    var U = EQ.util;

    var DEFAUTS_PROFIL = {
        tailleCm: 185,
        poidsDepartKg: 85.0,
        poidsCibleKg: 77.0,
        objectifProteinesG: 130,
        objectifCaloriesKcal: 1700,
        objectifGlucidesG: 140,
        objectifLipidesG: 50,
        tdeeKcal: 2400
    };

    // ------------------------------------------------------------- Séances
    var SEANCE_A = {
        cle: 'A',
        titre: 'Séance A — Jambes & Poussée',
        duree: '30 min',
        description: '3 supersets avec 60 à 75 s de repos entre les tours. Intensité ciblée sans épuisement articulaire.',
        echauffement: [
            '30 squats au poids du corps (rythme soutenu)',
            '20 jumping jacks ou montées de genoux',
            '10 cercles de bras dans chaque sens',
            '10 rotations de hanches + chat-vache',
            '10 pompes lentes + 20 s de suspension à la barre'
        ],
        blocs: [
            {
                nom: 'Bloc 1 · Jambes + Poussée (superset)',
                reposSec: 60,
                exos: [
                    {
                        id: 'squat_bulgare',
                        nom: 'Squat bulgare',
                        cible: '10–12 / jambe',
                        unilateral: true,
                        variantes: ['N1 Assis-debout sur chaise', 'N2 Split squat au sol', 'N3 Bulgare avec 2×5 kg', 'N4 Bulgare + sac 10 kg', 'N5 Bulgare tempo 3 s + sac 15 kg'],
                        lests: ['Poids du corps', '2×5 kg', 'Sac 5 kg', 'Sac 10 kg', 'Sac 15 kg'],
                        description: 'Pied arrière sur banc ou canapé. Descente contrôlée en gardant le genou avant au-dessus de la cheville, buste légèrement penché pour engager le grand fessier.'
                    },
                    {
                        id: 'pompes',
                        nom: 'Pompes',
                        cible: '8–12 reps',
                        unilateral: false,
                        variantes: ['N1 Mains sur canapé', 'N2 Sur les genoux', 'N3 Au sol amplitude complète', 'N4 Pieds surélevés 40 cm', 'N5 Surélevées + sac 10 kg'],
                        lests: ['Poids du corps', 'Sac 5 kg', 'Sac 10 kg'],
                        description: 'Corps gainé des talons à la tête. Coudes à 45° du buste (pas en T). Poitrine qui frôle le sol, repousser en écartant les omoplates en haut.'
                    }
                ]
            },
            {
                nom: 'Bloc 2 · Chaîne postérieure + Tirage (superset)',
                reposSec: 60,
                exos: [
                    {
                        id: 'sdt_roumain',
                        nom: 'Soulevé de terre roumain unilatéral',
                        cible: '10–12 / jambe',
                        unilateral: true,
                        variantes: ['N1 Deux pieds au sol', 'N2 Unilatéral poids de corps', 'N3 Unilatéral avec sac 5 kg', 'N4 Unilatéral avec sac 10 kg'],
                        lests: ['Poids du corps', 'Sac 5 kg', 'Sac 10 kg'],
                        description: 'Charnière de hanche : pousser les fesses en arrière en gardant le dos droit. Légère flexion du genou d’appui, ressentir l’étirement de l’ischio-jambier.'
                    },
                    {
                        id: 'rowing_inverse',
                        nom: 'Rowing inversé',
                        cible: '8–12 reps',
                        unilateral: false,
                        variantes: ['N1 Corps incliné à 45°', 'N2 Corps presque horizontal', 'N3 Pieds surélevés sur chaise', 'N4 Pause 2 s en haut'],
                        lests: ['Poids du corps', 'Sac sur le torse'],
                        description: 'Sous la table ou barre basse. Tirer la poitrine vers la barre en resserrant fort les omoplates. Gaine abdominale verrouillée.'
                    }
                ]
            },
            {
                nom: 'Bloc 3 · Fessiers & Gainage (superset)',
                reposSec: 45,
                exos: [
                    {
                        id: 'fentes_arriere',
                        nom: 'Fentes arrière dynamiques',
                        cible: '12–15 / jambe',
                        unilateral: true,
                        variantes: ['N1 Fentes lentes', 'N2 Fentes avec impulsion', 'N3 Fentes avec charge 10 kg'],
                        lests: ['Poids du corps', 'Sac 5 kg', 'Sac 10 kg'],
                        description: 'Grand pas en arrière, descente verticale sans heurter le sol. Pousser sur le talon avant pour remonter.'
                    },
                    {
                        id: 'gainage_planche',
                        nom: 'Gainage planche abdominale',
                        cible: '45–60 s',
                        unilateral: false,
                        variantes: ['N1 Sur les genoux', 'N2 Sur pointes de pieds', 'N3 Planche RKC active'],
                        lests: ['Poids du corps'],
                        description: 'Rétroversion du bassin, fessiers et abdos contractés au maximum. Pousser activement dans les coudes pour éloigner les épaules des oreilles.'
                    }
                ]
            }
        ]
    };

    var SEANCE_B = {
        cle: 'B',
        titre: 'Séance B — Tirage & Épaules',
        duree: '30 min',
        description: 'Focus dos large, deltoïdes et stabilité centrale. Rythme dynamique.',
        echauffement: [
            '20 jumping jacks + 20 squats au poids du corps',
            '10 cercles de bras + rotations d’épaules',
            '10 pompes lentes + 2×5 tractions faciles ou descentes ralenties',
            '20 s de suspension à la barre (dead hang)'
        ],
        blocs: [
            {
                nom: 'Bloc 1 · Dorsaux & Deltoïdes (superset)',
                reposSec: 60,
                exos: [
                    {
                        id: 'tractions',
                        nom: 'Tractions (pronation ou supination)',
                        cible: '6–10 reps',
                        unilateral: false,
                        variantes: ['N1 Descentes ralenties (négatives)', 'N2 Tractions avec élastique', 'N3 Poids du corps strictes', 'N4 Tractions lestées +5 kg'],
                        lests: ['Poids du corps', 'Sac 5 kg', 'Sac 10 kg'],
                        description: 'Prise légèrement plus large que les épaules. Tirer avec les coudes vers le bas et l’arrière jusqu’à dépasser le menton. Contrôler la descente.'
                    },
                    {
                        id: 'pike_pushup',
                        nom: 'Pike push-up (épaules)',
                        cible: '8–12 reps',
                        unilateral: false,
                        variantes: ['N1 Pieds au sol hanches hautes', 'N2 Pieds sur chaise 40 cm', 'N3 Descente tempo 3 s', 'N4 Handstand push-up assisté'],
                        lests: ['Poids du corps'],
                        description: 'Corps en V inversé. Regarder entre les mains, descendre la tête vers l’avant pour former un trépied, puis repousser vers l’arrière.'
                    }
                ]
            },
            {
                nom: 'Bloc 2 · Dos dense & Épaules postérieures (superset)',
                reposSec: 60,
                exos: [
                    {
                        id: 'rowing_supination',
                        nom: 'Rowing inversé (supination)',
                        cible: '8–12 reps',
                        unilateral: false,
                        variantes: ['N1 Buste à 45°', 'N2 Buste horizontal', 'N3 Pieds surélevés', 'N4 Tempo 3-1-1'],
                        lests: ['Poids du corps', 'Sac 5 kg'],
                        description: 'Paumes tournées vers soi. Engage les biceps et le bas des dorsaux. Coudes serrés contre le buste.'
                    },
                    {
                        id: 'face_pull',
                        nom: 'Face pull / élastic row',
                        cible: '12–15 reps',
                        unilateral: false,
                        variantes: ['N1 Élastique moyen', 'N2 Élastique fort', 'N3 Pause 2 s en contraction'],
                        lests: ['Élastique'],
                        description: 'Tirer l’élastique vers les yeux en écartant les mains. Clé absolue de la posture et de la santé des épaules.'
                    }
                ]
            },
            {
                nom: 'Bloc 3 · Gainage latéral & Abdominaux (superset)',
                reposSec: 45,
                exos: [
                    {
                        id: 'planche_laterale',
                        nom: 'Planche latérale',
                        cible: '40 s / côté',
                        unilateral: true,
                        variantes: ['N1 Genou au sol', 'N2 Pieds empilés', 'N3 Avec levée de jambe'],
                        lests: ['Poids du corps'],
                        description: 'Corps parfaitement aligné. Pousser les hanches vers le haut, bras libre tendu vers le ciel.'
                    },
                    {
                        id: 'hollow_hold',
                        nom: 'Hollow hold (gainage gymnique)',
                        cible: '30–45 s',
                        unilateral: false,
                        variantes: ['N1 Genoux fléchis', 'N2 Une jambe tendue', 'N3 Position complète bras tendus'],
                        lests: ['Poids du corps'],
                        description: 'Bas du dos plaqué sans aucun jour contre le sol. Côtes aspirées, pointes de pieds tendues.'
                    }
                ]
            }
        ]
    };

    // -------------------------------------------------------- Repas types
    var REPAS_TYPES = [
        {
            cle: 'gamelle_midi',
            emoji: '🍱',
            nom: 'Gamelle de midi (type)',
            detail: '3 œufs durs (165 g) · 135 g edamames · 100 g lentilles corail cuites · 100 g crudités · 100 g skyr',
            prot: 58.0,
            gluc: 35.0,
            lip: 24.0,
            kcal: 588
        },
        {
            cle: 'gouter',
            emoji: '🍎',
            nom: 'Goûter (type)',
            detail: '20 amandes grillées à sec (≈ 24 g) · 1 belle pomme (≈ 150 g)',
            prot: 7.0,
            gluc: 20.0,
            lip: 13.0,
            kcal: 225
        },
        {
            cle: 'petit_dejeuner',
            emoji: '☕',
            nom: 'Petit déjeuner (type)',
            detail: 'Thé vert dans 25 cl d’eau chaude · 1 cuillère à café de jus de citron',
            prot: 0.0,
            gluc: 0.0,
            lip: 0.0,
            kcal: 2
        }
    ];

    // ------------------------------------------------------------- Menus & Courses
    var PLANNING_EXEMPLE = [
        { jour: 'Lundi', midi: 'Gamelle de midi (œufs, edamames, lentilles)', soir: 'Poulet rôti aux herbes & haricots verts', kcalMidi: 588, protMidi: 58, kcalSoir: 520, protSoir: 44 },
        { jour: 'Mardi', midi: 'Salade de thon, pois chiches & tomates', soir: 'Omelette champignons & salade verte', kcalMidi: 540, protMidi: 50, kcalSoir: 450, protSoir: 32 },
        { jour: 'Mercredi', midi: 'Gamelle de midi (type)', soir: 'Filet de cabillaud, riz basmati & brocolis', kcalMidi: 588, protMidi: 58, kcalSoir: 490, protSoir: 42 },
        { jour: 'Jeudi', midi: 'Aiguillettes de canard & poêlée courgettes', soir: 'Velouté de potimarron & tartines cottage cheese', kcalMidi: 560, protMidi: 46, kcalSoir: 420, protSoir: 28 },
        { jour: 'Vendredi', midi: 'Gamelle de midi (type)', soir: 'Burger maison steak 5 % & salade coleslaw', kcalMidi: 588, protMidi: 58, kcalSoir: 620, protSoir: 48 },
        { jour: 'Samedi', midi: 'Pavé de saumon, quinoa & épinards', soir: 'Assiette mezze (houmous, feta, carottes, œufs)', kcalMidi: 610, protMidi: 42, kcalSoir: 540, protSoir: 30 },
        { jour: 'Dimanche', midi: 'Rôti de bœuf familial & légumes rôtis', soir: 'Soupe paysanne & compote maison sans sucre', kcalMidi: 650, protMidi: 52, kcalSoir: 380, protSoir: 18 }
    ];

    var RECETTES_EXEMPLES = [
        {
            id: 'poulet_haricots',
            nom: 'Poulet aux herbes de Provence & haricots verts',
            temps: '25 min',
            convives: 4,
            kcalPortion: 420,
            protPortion: 45,
            ingredients: [
                { nom: 'Blancs de poulet', qte: '600 g' },
                { nom: 'Haricots verts frais ou surgelés', qte: '800 g' },
                { nom: 'Huile d’olive vierge', qte: '2 c. à soupe' },
                { nom: 'Ail & Herbes de Provence', qte: 'selon goût' }
            ],
            etapes: [
                'Faire dorer le poulet coupé en émincés dans une cuillère d’huile d’olive avec l’ail émincé.',
                'Cuire les haricots verts à la vapeur ou à l’eau bouillante 10 minutes.',
                'Mélanger les haricots avec le poulet, saupoudrer d’herbes de Provence et assaisonner.'
            ]
        },
        {
            id: 'cabillaud_riz',
            nom: 'Cabillaud au four, riz basmati & brocolis vapeur',
            temps: '20 min',
            convives: 2,
            kcalPortion: 460,
            protPortion: 41,
            ingredients: [
                { nom: 'Dos de cabillaud', qte: '350 g' },
                { nom: 'Riz basmati cru', qte: '120 g' },
                { nom: 'Brocolis en fleurettes', qte: '400 g' },
                { nom: 'Jus de citron & aneth', qte: '1 c. à soupe' }
            ],
            etapes: [
                'Préchauffer le four à 180°C. Déposer le cabillaud sur une plaque avec filet d’huile d’olive et citron.',
                'Cuire le riz basmati dans 2 fois son volume d’eau bouillante salée pendant 11 min.',
                'Cuire les brocolis à la vapeur 8 minutes pour les garder croquants.',
                'Servir immédiatement avec l’aneth frais.'
            ]
        },
        {
            id: 'gamelle_midi_recette',
            nom: 'Gamelle recomposition : œufs, edamames, lentilles',
            temps: '15 min (batch)',
            convives: 1,
            kcalPortion: 588,
            protPortion: 58,
            ingredients: [
                { nom: 'Œufs durs bio', qte: '3 unités' },
                { nom: 'Edamames écossés cuits', qte: '135 g' },
                { nom: 'Lentilles corail cuites', qte: '100 g' },
                { nom: 'Crudités mélangées (courgette, tomate)', qte: '100 g' },
                { nom: 'Skyr nature 0 %', qte: '100 g' }
            ],
            etapes: [
                'Préparer les œufs durs (9 min dans l’eau frémissante, puis refroidir immédiatement dans l’eau froide).',
                'Dans un bol hermétique, disposer le lit de lentilles et d’edamames.',
                'Ajouter les crudités émincées et les œufs écalés coupés en deux.',
                'Prendre le pot de skyr en dessert pour clore le repas à 58 g de protéines.'
            ]
        }
    ];

    var COURSES_DEFAUT = [
        { id: 'c1', rayon: 'Frais & Laiterie', produit: 'Œufs bio plein air', qte: '18 unités', pris: false },
        { id: 'c2', rayon: 'Frais & Laiterie', produit: 'Skyr nature 0 %', qte: '2 pots (500 g)', pris: false },
        { id: 'c3', rayon: 'Frais & Laiterie', produit: 'Fromage blanc 0 %', qte: '1 kg', pris: true },
        { id: 'c4', rayon: 'Boucherie & Poisson', produit: 'Blancs de poulet fermier', qte: '1,2 kg', pris: false },
        { id: 'c5', rayon: 'Boucherie & Poisson', produit: 'Dos de cabillaud frais', qte: '600 g', pris: false },
        { id: 'c6', rayon: 'Boucherie & Poisson', produit: 'Steaks hachés 5 %', qte: '4 unités', pris: false },
        { id: 'c7', rayon: 'Fruits & Légumes', produit: 'Courgettes', qte: '1,5 kg', pris: true },
        { id: 'c8', rayon: 'Fruits & Légumes', produit: 'Brocolis', qte: '2 têtes', pris: false },
        { id: 'c9', rayon: 'Fruits & Légumes', produit: 'Pommes gala', qte: '1 kg', pris: false },
        { id: 'c10', rayon: 'Fruits & Légumes', produit: 'Salade verte (roquette/mâche)', qte: '2 sachets', pris: false },
        { id: 'c11', rayon: 'Épicerie & Féculents', produit: 'Edamames surgelés', qte: '1 kg', pris: false },
        { id: 'c12', rayon: 'Épicerie & Féculents', produit: 'Lentilles corail', qte: '500 g', pris: true },
        { id: 'c13', rayon: 'Épicerie & Féculents', produit: 'Riz basmati complet', qte: '1 kg', pris: true },
        { id: 'c14', rayon: 'Épicerie & Féculents', produit: 'Amandes grillées non salées', qte: '250 g', pris: false },
        { id: 'c15', rayon: 'Boissons & Divers', produit: 'Thé vert sencha', qte: '1 boîte', pris: false }
    ];

    // ------------------------------------------------------------- Calculs
    function calculerImc(poidsKg, tailleCm) {
        if (!poidsKg || !tailleCm) return null;
        var t = tailleCm / 100;
        return Math.round((poidsKg / (t * t)) * 10) / 10;
    }

    function calculerMasseGrasse(poidsKg, pctGras) {
        if (!poidsKg || !pctGras) return null;
        return Math.round((poidsKg * (pctGras / 100)) * 10) / 10;
    }

    function calculerMasseMaigre(poidsKg, pctGras) {
        var mg = calculerMasseGrasse(poidsKg, pctGras);
        if (mg == null) return null;
        return Math.round((poidsKg - mg) * 10) / 10;
    }

    function calculerMoyennesPoids(logs) {
        if (!logs || logs.length === 0) {
            return { actuel: null, m7: null, m30: null, perteTotale: 0, tendance7j: 0 };
        }
        var copies = logs.slice().sort(function (a, b) {
            return new Date(b.date) - new Date(a.date);
        });
        var actuel = copies[0] ? copies[0].poids : null;
        var poids7 = [];
        var poids30 = [];
        var now = new Date(copies[0].date);

        for (var i = 0; i < copies.length; i++) {
            var diffJours = (now - new Date(copies[i].date)) / (1000 * 3600 * 24);
            if (diffJours <= 7) poids7.push(copies[i].poids);
            if (diffJours <= 30) poids30.push(copies[i].poids);
        }

        var m7 = U.moyenne(poids7);
        var m30 = U.moyenne(poids30);
        var depart = copies[copies.length - 1].poids;
        var perteTotale = actuel && depart ? Math.round((actuel - depart) * 10) / 10 : 0;
        var tendance7j = poids7.length >= 2 ? Math.round((poids7[0] - poids7[poids7.length - 1]) * 10) / 10 : 0;

        return {
            actuel: actuel,
            m7: Math.round(m7 * 10) / 10,
            m30: Math.round(m30 * 10) / 10,
            perteTotale: perteTotale,
            tendance7j: tendance7j
        };
    }

    EQ.modele = {
        DEFAUTS_PROFIL: DEFAUTS_PROFIL,
        SEANCE_A: SEANCE_A,
        SEANCE_B: SEANCE_B,
        REPAS_TYPES: REPAS_TYPES,
        PLANNING_EXEMPLE: PLANNING_EXEMPLE,
        RECETTES_EXEMPLES: RECETTES_EXEMPLES,
        COURSES_DEFAUT: COURSES_DEFAUT,
        calculerImc: calculerImc,
        calculerMasseGrasse: calculerMasseGrasse,
        calculerMasseMaigre: calculerMasseMaigre,
        calculerMoyennesPoids: calculerMoyennesPoids
    };
})(typeof window !== 'undefined' ? window : this);
