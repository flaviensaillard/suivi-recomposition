/* Gestion de l'état local, cache et persistance des données. */
(function (root) {
    'use strict';
    var EQ = root.EQ = root.EQ || {};
    var U = EQ.util, M = EQ.modele;

    var CLE_REGLAGES = 'eq.reglages.v1';
    var CLE_LOGS = 'eq.logs.v1';
    var CLE_MENSURATIONS = 'eq.mensurations.v1';
    var CLE_SEANCES = 'eq.seances.v1';
    var CLE_COURSES = 'eq.courses.v1';
    var CLE_DERNIER_ONGLET = 'eq.onglet';

    var DEFAUTS_REGLAGES = {
        urlSuivi: 'https://suivi-recomposition.streamlit.app',
        urlMenus: 'https://gestion-menus.streamlit.app',
        supabaseUrl: '',
        supabaseKey: '',
        appCouranteWeb: 'suivi', // 'suivi' ou 'menus'
        profil: 'flavien', // 'flavien', 'lea', 'partage'
        tailleCm: 185,
        poidsDepartKg: 85.0,
        poidsCibleKg: 77.0,
        objectifProteinesG: 130,
        objectifCaloriesKcal: 1700
    };

    function chargerJson(cle, defaut) {
        try {
            var s = root.localStorage ? root.localStorage.getItem(cle) : null;
            if (!s) return defaut;
            return JSON.parse(s);
        } catch (e) {
            return defaut;
        }
    }

    function sauverJson(cle, val) {
        try {
            if (root.localStorage) {
                root.localStorage.setItem(cle, JSON.stringify(val));
            }
        } catch (e) {
            console.warn('Erreur localStorage', e);
        }
    }

    // -------------------------------------------------------- Génération démo
    function genererDonneesInitiales() {
        var logs = [];
        var mensurations = [];
        var seances = [];
        var now = new Date();
        var poids = 85.0;
        var gras = 21.5;

        // 42 jours en arrière
        for (var i = 42; i >= 0; i--) {
            var d = new Date(now.getFullYear(), now.getMonth(), now.getDate() - i);
            var dateStr = U.dateIso(d);
            var dow = d.getDay(); // 0 = Dimanche, 1 = Lundi, etc.

            // Perte progressive réaliste
            poids -= 0.15 + (Math.sin(i) * 0.08);
            if (poids < 78.2) poids = 78.4;
            gras -= 0.09;
            if (gras < 17.6) gras = 17.8;

            var prot = 120 + Math.floor(Math.sin(i * 2) * 20) + 10;
            var kcal = 1650 + Math.floor(Math.cos(i) * 120);

            logs.push({
                date: dateStr,
                poids: Math.round(poids * 10) / 10,
                masseGrassePct: Math.round(gras * 10) / 10,
                proteinesG: Math.max(105, prot),
                caloriesKcal: Math.max(1520, kcal),
                pas: 7500 + (i % 5) * 1200,
                sommeilH: 7.2 + (Math.sin(i) * 0.6)
            });

            // Mensurations hebdomadaires (Lundi)
            if (dow === 1) {
                var tailleTaille = Math.round((93.0 - (42 - i) * 0.18) * 10) / 10;
                mensurations.push({
                    date: dateStr,
                    tailleCm: Math.max(84.0, tailleTaille),
                    hanchesCm: Math.round((102.0 - (42 - i) * 0.12) * 10) / 10,
                    brasCm: 37.0,
                    cuisseCm: 58.5
                });
            }

            // Séances 2 à 3 fois par semaine (Lundi, Vendredi)
            if (dow === 1 || dow === 5) {
                seances.push({
                    date: dateStr,
                    type: dow === 1 ? 'A' : 'B',
                    nom: dow === 1 ? 'Séance A (Jambes & Poussée)' : 'Séance B (Tirage & Épaules)',
                    dureeMin: 32,
                    rpe: 8
                });
            }
        }

        sauverJson(CLE_LOGS, logs);
        sauverJson(CLE_MENSURATIONS, mensurations);
        sauverJson(CLE_SEANCES, seances);
        sauverJson(CLE_COURSES, M.COURSES_DEFAUT);
    }

    // Initialisation au premier lancement
    if (!chargerJson(CLE_LOGS, null)) {
        genererDonneesInitiales();
    }

    // ------------------------------------------------------------- Méthodes API
    var Store = {
        getReglages: function () {
            var r = chargerJson(CLE_REGLAGES, {});
            return Object.assign({}, DEFAUTS_REGLAGES, r);
        },
        saveReglages: function (r) {
            sauverJson(CLE_REGLAGES, r);
        },
        getLogs: function () {
            return chargerJson(CLE_LOGS, []);
        },
        saveLog: function (entree) {
            var logs = Store.getLogs();
            var index = logs.findIndex(function (l) { return l.date === entree.date; });
            if (index >= 0) {
                logs[index] = Object.assign({}, logs[index], entree);
            } else {
                logs.push(entree);
            }
            logs.sort(function (a, b) { return new Date(a.date) - new Date(b.date); });
            sauverJson(CLE_LOGS, logs);
            return logs;
        },
        getMensurations: function () {
            return chargerJson(CLE_MENSURATIONS, []);
        },
        saveMensuration: function (m) {
            var liste = Store.getMensurations();
            var index = liste.findIndex(function (item) { return item.date === m.date; });
            if (index >= 0) {
                liste[index] = Object.assign({}, liste[index], m);
            } else {
                liste.push(m);
            }
            liste.sort(function (a, b) { return new Date(a.date) - new Date(b.date); });
            sauverJson(CLE_MENSURATIONS, liste);
            return liste;
        },
        getSeances: function () {
            return chargerJson(CLE_SEANCES, []);
        },
        saveSeance: function (s) {
            var liste = Store.getSeances();
            liste.push(s);
            sauverJson(CLE_SEANCES, liste);
            return liste;
        },
        getCourses: function () {
            var c = chargerJson(CLE_COURSES, null);
            if (!c || c.length === 0) {
                c = M.COURSES_DEFAUT;
                sauverJson(CLE_COURSES, c);
            }
            return c;
        },
        toggleCourse: function (id) {
            var liste = Store.getCourses();
            var item = liste.find(function (x) { return x.id === id; });
            if (item) {
                item.pris = !item.pris;
                sauverJson(CLE_COURSES, liste);
            }
            return liste;
        },
        reinitialiserDemo: function () {
            genererDonneesInitiales();
            sauverJson(CLE_REGLAGES, DEFAUTS_REGLAGES);
        },
        getOnglet: function () {
            try {
                return (root.localStorage && root.localStorage.getItem(CLE_DERNIER_ONGLET)) || 'bord';
            } catch (e) {
                return 'bord';
            }
        },
        setOnglet: function (onglet) {
            try {
                if (root.localStorage) root.localStorage.setItem(CLE_DERNIER_ONGLET, onglet);
            } catch (e) {
            }
        }
    };

    EQ.store = Store;
})(typeof window !== 'undefined' ? window : this);
