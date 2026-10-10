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
    var CLE_REVISION_DONNEES = 'eq.revisionDonnees.v2';
    var CLE_DONNEES_ANTERIEURES_A_VERIFIER = 'eq.donneesAnterieuresAverifier.v1';

    var DEFAUTS_REGLAGES = {
        urlSuivi: 'https://suivi-recomposition.streamlit.app',
        urlMenus: 'https://gestion-menus.streamlit.app',
        appCouranteWeb: 'suivi', // 'suivi' ou 'menus'
        tailleCm: null,
        poidsDepartKg: null,
        poidsCibleKg: null,
        objectifProteinesG: null,
        objectifCaloriesKcal: null,
        profileConfigured: false
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

    // Les installations existantes peuvent contenir les exemples créés par les anciennes versions.
    // Les conserver sans les prendre silencieusement pour des données vérifiées.
    if (chargerJson(CLE_REVISION_DONNEES, null) === null) {
        var clesAvecDonneesLocales = [CLE_LOGS, CLE_MENSURATIONS, CLE_SEANCES, CLE_COURSES];
        var avaitDonneesLocales = clesAvecDonneesLocales.some(function (cle) {
            var valeur = chargerJson(cle, null);
            return Array.isArray(valeur) && valeur.length > 0;
        });
        sauverJson(CLE_DONNEES_ANTERIEURES_A_VERIFIER, avaitDonneesLocales);
        sauverJson(CLE_REVISION_DONNEES, 2);
    }

    // ------------------------------------------------------- Données locales
    // Un premier lancement commence vide : aucune pesée, macro ou séance fictive.
    [CLE_LOGS, CLE_MENSURATIONS, CLE_SEANCES, CLE_COURSES].forEach(function (cle) {
        if (chargerJson(cle, null) === null) sauverJson(cle, []);
    });

    // ------------------------------------------------------------- Méthodes API
    var Store = {
        getReglages: function () {
            var r = chargerJson(CLE_REGLAGES, {});
            return Object.assign({}, DEFAUTS_REGLAGES, r);
        },
        saveReglages: function (r) {
            sauverJson(CLE_REGLAGES, r);
        },
        anciennesDonneesAverifier: function () {
            if (chargerJson(CLE_DONNEES_ANTERIEURES_A_VERIFIER, false) !== true) return false;
            var cles = [CLE_LOGS, CLE_MENSURATIONS, CLE_SEANCES, CLE_COURSES];
            var aEncoreDesDonnees = cles.some(function (cle) {
                var valeur = chargerJson(cle, null);
                return Array.isArray(valeur) && valeur.length > 0;
            });
            if (!aEncoreDesDonnees) {
                sauverJson(CLE_DONNEES_ANTERIEURES_A_VERIFIER, false);
                return false;
            }
            return true;
        },
        masquerAvertissementDonneesPreexistantes: function () {
            sauverJson(CLE_DONNEES_ANTERIEURES_A_VERIFIER, false);
        },
        effacerAnciennesCles: function () {
            var r = chargerJson(CLE_REGLAGES, {});
            if (!r || typeof r !== 'object' || Array.isArray(r)) r = {};
            delete r.supabaseUrl;
            delete r.supabaseKey;
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
            var c = chargerJson(CLE_COURSES, []);
            return Array.isArray(c) ? c : [];
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
