/* Stockage local-first d'Équilibre.
   Les écritures restent sur l'appareil et sont placées dans une file d'attente
   pour la synchronisation Supabase quand une session est disponible. */
(function (root) {
    'use strict';
    var EQ = root.EQ = root.EQ || {};
    var U = EQ.util, M = EQ.modele;

    var CLE_REGLAGES = 'eq.reglages.v1';
    var CLE_LOGS = 'eq.logs.v1';
    var CLE_MENSURATIONS = 'eq.mensurations.v1';
    var CLE_SEANCES = 'eq.seances.v1';
    var CLE_SERIES = 'eq.series.v1';
    var CLE_NUTRITION = 'eq.nutrition.v1';
    var CLE_COURSES = 'eq.courses.v1';
    var CLE_PROFIL = 'eq.profil.v1';
    var CLE_FILE_SYNC = 'eq.sync.queue.v1';
    var TABLES_MENU = ['ingredients', 'recipes', 'recipe_ingredients', 'planned_meals'];
    var CLE_DERNIER_ONGLET = 'eq.onglet';
    // Corrections et ajouts de l'utilisateur sur les repas types du modèle.
    // Seuls les écarts sont stockés, jamais la liste complète.
    var CLE_REPAS_TYPES = 'eq.repasTypes.v1';

    function cleMenu(table, ligne) {
        if (!ligne) return '';
        if (table === 'planned_meals') return String(ligne._local_id || ligne.local_id || ligne.id || '');
        return String(ligne.id || ligne._local_id || '');
    }

    function cleMenuStockage(table) { return 'eq.menu.' + table + '.v1'; }

    var DEFAUTS_REGLAGES = {
        urlSuivi: 'https://suivi-recomposition.streamlit.app',
        urlMenus: 'https://fvfcxhwmrykqnzazttiksw.streamlit.app/',
        supabaseUrl: '',
        supabaseKey: '',
        coachApiUrl: '',
        empreinteActive: false,
        appCouranteWeb: 'suivi',
        profil: 'flavien',
        tailleCm: 185,
        poidsDepartKg: 85.0,
        poidsCibleKg: 77.0,
        objectifProteinesG: 130,
        objectifCaloriesKcal: 1700,
        objectifGlucidesG: 140,
        objectifLipidesG: 50,
        tdeeKcal: 2400
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
            if (root.localStorage) root.localStorage.setItem(cle, JSON.stringify(val));
            return true;
        } catch (e) {
            console.warn('Erreur de stockage local', e);
            return false;
        }
    }

    function copie(obj) {
        return obj == null ? obj : JSON.parse(JSON.stringify(obj));
    }

    function cleLocale(table, ligne) {
        if (!ligne) return '';
        if (table === 'daily_logs') return String(ligne.date || ligne.log_date || '');
        if (table === 'measurements') return String(ligne.date || ligne.meas_date || '');
        if (table === 'workouts') return [ligne.date || ligne.session_date, ligne.type || ligne.session].join('|');
        if (table === 'workout_sets') return [ligne.date || ligne.set_date, ligne.type || ligne.session,
            ligne.exercise, ligne.set_no].join('|');
        if (table === 'protein_entries') return String(ligne.local_id || ligne.id || '');
        if (table === 'profiles') return 'profile';
        if (table === 'shopping_state') return [ligne.item_key, ligne.week_of].join('|');
        return String(ligne.id || '');
    }

    var timerSyncAuto = null;
    function planifierSynchronisation() {
        if (!root.EQ || !root.EQ.net || !root.EQ.net.synchroniserSupabase || !Store || !Store.getRemoteSession()) return;
        try {
            if (root.navigator && root.navigator.onLine === false) return;
            if (root.Native && root.Native.isOnline && !root.Native.isOnline()) return;
        } catch (e) { }
        clearTimeout(timerSyncAuto);
        timerSyncAuto = setTimeout(function () {
            root.EQ.net.synchroniserSupabase(function () { /* la file reste en attente si hors ligne */ });
        }, 900);
    }

    function enfile(table, operation, key, row) {
        if (!key) return;
        var q = chargerJson(CLE_FILE_SYNC, []);
        var id = table + '|' + key;
        var item = {
            id: id,
            table: table,
            operation: operation,
            key: String(key),
            row: row ? copie(row) : null,
            modified_at: new Date().toISOString()
        };
        var i = q.findIndex(function (x) { return x.id === id; });
        if (i >= 0) q[i] = item; else q.push(item);
        sauverJson(CLE_FILE_SYNC, q);
        planifierSynchronisation();
    }

    function majListe(cle, table, row, cleFn) {
        var lignes = chargerJson(cle, []);
        var key = cleFn(row);
        var i = lignes.findIndex(function (x) { return cleFn(x) === key; });
        if (i >= 0) lignes[i] = Object.assign({}, lignes[i], row);
        else lignes.push(copie(row));
        lignes.sort(function (a, b) {
            return String(a.date || a.log_date || a.meas_date || a.session_date || a.entry_date || '')
                .localeCompare(String(b.date || b.log_date || b.meas_date || b.session_date || b.entry_date || ''));
        });
        sauverJson(cle, lignes);
        if (table) enfile(table, 'upsert', key, row);
        return lignes;
    }

    function uuidLocal() {
        if (root.crypto && root.crypto.randomUUID) return root.crypto.randomUUID();
        return 'local-' + Date.now().toString(36) + '-' + Math.random().toString(36).slice(2, 11);
    }

    // Les écrans doivent démarrer vides, pas avec un faux historique de pesées.
    // On initialise uniquement les conteneurs manquants et on conserve toutes
    // les données déjà présentes sur une version antérieure.
    [CLE_LOGS, CLE_MENSURATIONS, CLE_SEANCES, CLE_SERIES, CLE_NUTRITION, CLE_COURSES,
        CLE_FILE_SYNC].concat(TABLES_MENU.map(cleMenuStockage)).forEach(function (cle) {
        if (chargerJson(cle, null) === null) sauverJson(cle, []);
    });

    var Store = {
        getReglages: function () {
            var r = chargerJson(CLE_REGLAGES, {});
            return Object.assign({}, DEFAUTS_REGLAGES, r);
        },
        saveReglages: function (r) {
            return sauverJson(CLE_REGLAGES, Object.assign({}, Store.getReglages(), r));
        },
        getProfil: function () {
            // Le profil ne doit contenir que des champs personnels. En particulier,
            // ne pas y injecter les défauts Supabase vides qui écraseraient l'URL
            // et la clé dans les réglages lors d'une fusion de profil distant.
            var defaultsProfil = {
                displayName: '', tailleCm: 185, poidsDepartKg: 85.0, poidsCibleKg: 77.0,
                objectifProteinesG: 130, objectifCaloriesKcal: 1700,
                objectifGlucidesG: 140, objectifLipidesG: 50, tdeeKcal: 2400, phase: ''
            };
            return Object.assign({}, defaultsProfil, chargerJson(CLE_PROFIL, {}));
        },
        saveProfil: function (profil) {
            var p = Object.assign({}, Store.getProfil(), profil || {});
            sauverJson(CLE_PROFIL, p);
            sauverJson(CLE_REGLAGES, Object.assign({}, Store.getReglages(), p));
            enfile('profiles', 'upsert', 'profile', p);
            return p;
        },

        // Pesées et habitudes quotidiennes
        getLogs: function () {
            return chargerJson(CLE_LOGS, []).slice().sort(function (a, b) {
                return String(a.date || '').localeCompare(String(b.date || ''));
            });
        },
        saveLog: function (entree) {
            if (!entree || !entree.date) return Store.getLogs();
            return majListe(CLE_LOGS, 'daily_logs', entree, function (x) { return String(x.date || ''); });
        },
        deleteLog: function (date) {
            var lignes = Store.getLogs().filter(function (x) { return x.date !== date; });
            sauverJson(CLE_LOGS, lignes);
            enfile('daily_logs', 'delete', String(date));
            return lignes;
        },
        mergeRemoteLogs: function (rows) {
            fusionRemote(CLE_LOGS, 'daily_logs', rows, function (r) { return String(r.date || ''); });
        },

        // Mensurations : taille, hanches, poitrine, cou, bras, cuisse, photos et notes
        getMensurations: function () {
            return chargerJson(CLE_MENSURATIONS, []).slice().sort(function (a, b) {
                return String(a.date || '').localeCompare(String(b.date || ''));
            });
        },
        saveMensuration: function (m) {
            if (!m || !m.date) return Store.getMensurations();
            return majListe(CLE_MENSURATIONS, 'measurements', m, function (x) { return String(x.date || ''); });
        },
        deleteMensuration: function (date) {
            sauverJson(CLE_MENSURATIONS, Store.getMensurations().filter(function (x) { return x.date !== date; }));
            enfile('measurements', 'delete', String(date));
        },
        mergeRemoteMensurations: function (rows) {
            fusionRemote(CLE_MENSURATIONS, 'measurements', rows, function (r) { return String(r.date || ''); });
        },

        // Séances (A/B), historique et détails des séries
        getSeances: function () { return chargerJson(CLE_SEANCES, []); },
        saveSeance: function (s) {
            if (!s) return Store.getSeances();
            var k = function (x) { return [x.date || x.session_date, x.type || x.session].join('|'); };
            return majListe(CLE_SEANCES, 'workouts', s, k);
        },
        deleteSeance: function (date, type) {
            var k = [date, type].join('|');
            sauverJson(CLE_SEANCES, Store.getSeances().filter(function (x) {
                return [x.date || x.session_date, x.type || x.session].join('|') !== k;
            }));
            enfile('workouts', 'delete', k);
        },
        getSeries: function () { return chargerJson(CLE_SERIES, []); },
        saveSeries: function (rows) {
            (rows || []).forEach(function (row) {
                var k = function (x) { return [x.date || x.set_date, x.type || x.session, x.exercise, x.set_no].join('|'); };
                majListe(CLE_SERIES, 'workout_sets', row, k);
            });
            return Store.getSeries();
        },
        mergeRemoteWorkouts: function (rows) {
            fusionRemote(CLE_SEANCES, 'workouts', rows, function (r) {
                return [r.date || r.session_date, r.type || r.session].join('|');
            });
        },
        mergeRemoteSeries: function (rows) {
            fusionRemote(CLE_SERIES, 'workout_sets', rows, function (r) {
                return [r.date || r.set_date, r.type || r.session, r.exercise, r.set_no].join('|');
            });
        },

        // Journal nutrition (protéines, glucides, lipides, calories calculées)
        getNutrition: function () {
            return chargerJson(CLE_NUTRITION, []).slice().sort(function (a, b) {
                return String(a.date || '').localeCompare(String(b.date || '')) ||
                    String(a.local_id || a.id || '').localeCompare(String(b.local_id || b.id || ''));
            });
        },
        addNutrition: function (entry) {
            var x = Object.assign({ local_id: uuidLocal(), date: U.dateIso(new Date()),
                item: '', protein_g: 0, carbs_g: 0, fat_g: 0, qty: 1 }, entry || {});
            var rows = Store.getNutrition();
            rows.push(x);
            sauverJson(CLE_NUTRITION, rows);
            enfile('protein_entries', 'insert', x.local_id, x);
            return x;
        },
        updateNutrition: function (id, patch) {
            var rows = Store.getNutrition();
            var x = rows.find(function (a) { return String(a.id || a.local_id) === String(id); });
            if (!x) return false;
            Object.assign(x, patch || {});
            sauverJson(CLE_NUTRITION, rows);
            enfile('protein_entries', x.id ? 'update' : 'insert', String(x.id || x.local_id), x);
            return true;
        },
        deleteNutrition: function (id) {
            var rows = Store.getNutrition();
            var x = rows.find(function (a) { return String(a.id || a.local_id) === String(id); });
            if (!x) return;
            sauverJson(CLE_NUTRITION, rows.filter(function (a) { return a !== x; }));
            enfile('protein_entries', 'delete', String(x.id || x.local_id), x);
        },
        mergeRemoteNutrition: function (rows) {
            fusionRemote(CLE_NUTRITION, 'protein_entries', rows, function (r) {
                return String(r.id || r.local_id || '');
            });
        },
        attachNutritionServerId: function (localId, remoteRow) {
            var rows = Store.getNutrition();
            var x = rows.find(function (a) { return String(a.local_id) === String(localId); });
            if (!x || !remoteRow || remoteRow.id == null) return false;
            x.id = Number(remoteRow.id);
            x.date = String(remoteRow.entry_date || x.date).slice(0, 10);
            sauverJson(CLE_NUTRITION, rows);
            return true;
        },
        nutritionJour: function (date) {
            return Store.getNutrition().filter(function (x) { return x.date === date; });
        },
        totauxNutrition: function (date) {
            return Store.nutritionJour(date).reduce(function (t, x) {
                t.protein_g += Number(x.protein_g) || 0;
                t.carbs_g += Number(x.carbs_g) || 0;
                t.fat_g += Number(x.fat_g) || 0;
                return t;
            }, { protein_g: 0, carbs_g: 0, fat_g: 0 });
        },

        // Menus : cache des quatre tables Supabase et mutations local-first.
        getMenuTable: function (table) {
            if (TABLES_MENU.indexOf(table) < 0) return [];
            return chargerJson(cleMenuStockage(table), []);
        },
        getMenuData: function () {
            var out = {};
            TABLES_MENU.forEach(function (t) { out[t] = Store.getMenuTable(t); });
            return out;
        },
        mergeRemoteMenu: function (table, rows) {
            if (TABLES_MENU.indexOf(table) < 0) return;
            var locaux = Store.getMenuTable(table);
            var qTable = 'menu:' + table;
            var pending = Store.getSyncQueue().filter(function (x) { return x.table === qTable; });
            var dirty = {};
            pending.forEach(function (x) { dirty[String(x.key)] = true; });
            var locauxParCle = {};
            locaux.forEach(function (local) { locauxParCle[cleMenu(table, local)] = local; });
            var parCle = {};
            (rows || []).forEach(function (r) {
                var k = cleMenu(table, r);
                if (k) parCle[k] = Object.assign({}, copie(locauxParCle[k] || {}), copie(r));
            });
            locaux.forEach(function (local) {
                var k = cleMenu(table, local);
                if (k && dirty[k]) parCle[k] = copie(local);
            });
            sauverJson(cleMenuStockage(table), Object.keys(parCle).map(function (k) { return parCle[k]; }));
        },
        upsertMenu: function (table, row, operation) {
            if (TABLES_MENU.indexOf(table) < 0 || !row) return null;
            var x = copie(row);
            if (table === 'planned_meals' && (x.id == null || String(x.id).startsWith('local-')) && !x._local_id) {
                x._local_id = String(x.id || uuidLocal());
                delete x.id;
            } else if (table !== 'planned_meals' && !x.id) {
                x.id = uuidLocal();
            }
            var k = cleMenu(table, x);
            if (!k) return null;
            var rows = Store.getMenuTable(table);
            var i = rows.findIndex(function (r) { return cleMenu(table, r) === k; });
            if (i >= 0) rows[i] = Object.assign({}, rows[i], x);
            else rows.push(x);
            sauverJson(cleMenuStockage(table), rows);
            var qid = 'menu:' + table + '|' + k;
            var pending = Store.getSyncQueue().find(function (item) { return item.id === qid; });
            var op = pending && pending.operation === 'insert' && operation !== 'delete' ? 'insert' :
                (operation || (i >= 0 ? 'update' : 'insert'));
            enfile('menu:' + table, op, k, x);
            return copie(x);
        },
        deleteMenu: function (table, key) {
            if (TABLES_MENU.indexOf(table) < 0) return;
            var rows = Store.getMenuTable(table);
            var x = rows.find(function (r) { return cleMenu(table, r) === String(key); });
            if (!x) return;
            sauverJson(cleMenuStockage(table), rows.filter(function (r) { return r !== x; }));
            var qid = 'menu:' + table + '|' + String(key);
            var pending = Store.getSyncQueue().find(function (item) { return item.id === qid; });
            if (pending && pending.operation === 'insert') Store.removeSyncItem(qid);
            else enfile('menu:' + table, 'delete', String(key), x);
        },
        attachPlannedMealServerId: function (localId, remoteRow) {
            var rows = Store.getMenuTable('planned_meals');
            var x = rows.find(function (r) { return String(r._local_id || r.local_id || '') === String(localId); });
            if (!x || !remoteRow || remoteRow.id == null) return false;
            x.id = remoteRow.id;
            x.date_menu = remoteRow.date_menu || x.date_menu;
            delete x._local_id;
            delete x.local_id;
            sauverJson(cleMenuStockage('planned_meals'), rows);
            return true;
        },

        // Liste de courses locale (en attendant le port du module Menu complet)
        getCourses: function () { return chargerJson(CLE_COURSES, []); },
        saveCourses: function (lignes) { return sauverJson(CLE_COURSES, lignes || []); },
        toggleCourse: function (id) {
            var liste = Store.getCourses();
            var item = liste.find(function (x) { return String(x.id) === String(id); });
            if (item) {
                item.pris = !item.pris;
                Store.saveCourses(liste);
                var week = /^\\d{4}-\\d{2}-\\d{2}\\|/.test(String(item.id))
                    ? String(item.id).slice(0, 10) : semaineCourante();
                enfile('shopping_state', 'upsert', [item.id, week].join('|'), {
                    item_key: String(item.id), week_of: week, checked: !!item.pris
                });
            }
            return liste;
        },
        mergeRemoteShoppingState: function (rows) {
            var courses = Store.getCourses();
            var pending = Store.getSyncQueue().filter(function (x) { return x.table === 'shopping_state'; });
            var dirty = {};
            pending.forEach(function (x) { dirty[String(x.key)] = true; });
            (rows || []).forEach(function (r) {
                var key = [r.item_key, r.week_of].join('|');
                if (dirty[key]) return;
                var item = courses.find(function (c) { return String(c.id) === String(r.item_key); });
                if (item) item.pris = !!r.checked;
            });
            Store.saveCourses(courses);
        },

        getSyncQueue: function () { return chargerJson(CLE_FILE_SYNC, []); },
        removeSyncItem: function (id) {
            sauverJson(CLE_FILE_SYNC, Store.getSyncQueue().filter(function (x) { return x.id !== id; }));
        },
        replaceSyncItem: function (id, row) {
            var q = Store.getSyncQueue();
            var x = q.find(function (a) { return a.id === id; });
            if (x) { x.row = copie(row); sauverJson(CLE_FILE_SYNC, q); }
        },
        clearSyncQueue: function () { sauverJson(CLE_FILE_SYNC, []); },
        syncCount: function () { return Store.getSyncQueue().length; },

        reinitialiserDemo: function () {
            // L'ancien bouton est conservé pour compatibilité, mais ne recrée
            // plus de faux historique. Il efface seulement les données locales.
            [CLE_LOGS, CLE_MENSURATIONS, CLE_SEANCES, CLE_SERIES, CLE_NUTRITION,
                CLE_COURSES, CLE_FILE_SYNC].forEach(function (k) { sauverJson(k, []); });
        },
        getOnglet: function () {
            try { return (root.localStorage && root.localStorage.getItem(CLE_DERNIER_ONGLET)) || 'bord'; }
            catch (e) { return 'bord'; }
        },
        setOnglet: function (onglet) {
            try { if (root.localStorage) root.localStorage.setItem(CLE_DERNIER_ONGLET, onglet); } catch (e) { }
        },

        // À destination du moteur de synchro : ces méthodes n'ajoutent rien à la file.
        mergeRemote: fusionRemote,
        saveRemoteSession: function (session) { return sauverJson('eq.supabase.session.v1', session); },
        getRemoteSession: function () { return chargerJson('eq.supabase.session.v1', null); },
        clearRemoteSession: function () {
            try { root.localStorage.removeItem('eq.supabase.session.v1'); } catch (e) { }
        }
    };

    function semaineCourante() {
        var d = new Date();
        var jour = (d.getDay() + 6) % 7;
        d.setDate(d.getDate() - jour);
        return U.dateIso(d);
    }

    function fusionRemote(storageKey, table, remoteRows, keyFn) {
        var locaux = chargerJson(storageKey, []);
        var pending = Store.getSyncQueue().filter(function (x) { return x.table === table; });
        var dirty = {};
        pending.forEach(function (x) { dirty[x.key] = true; });
        var parCle = {};
        locaux.forEach(function (x) { parCle[keyFn(x)] = x; });
        (remoteRows || []).forEach(function (remote) {
            var k = keyFn(remote);
            if (!dirty[k]) parCle[k] = copie(remote);
        });
        sauverJson(storageKey, Object.keys(parCle).map(function (k) { return parCle[k]; }));
    }

    // ------------------------------------------------------------------
    // 1.4 — Supabase est la source de vérité. Le stockage local n'est plus
    // qu'un tampon : il sert quand le réseau est absent, et se déverse dans
    // Supabase dès que la connexion revient.
    // ------------------------------------------------------------------

    var CLE_MIGRATION_14 = 'eq.migration.v1.4';
    var CLE_PURGE_14 = 'eq.purge.v1.4';

    function estEnLigne() {
        try {
            if (root.navigator && root.navigator.onLine === false) return false;
            if (root.Native && root.Native.isOnline && !root.Native.isOnline()) return false;
        } catch (e) { /* l'absence de pont natif ne doit pas bloquer l'app */ }
        return true;
    }

    /**
     * Surveille la connectivité et rappelle `surRetourEnLigne` à chaque
     * transition hors ligne -> en ligne.
     *
     * Les événements `online`/`offline` ne sont pas fiables dans un WebView
     * Android, d'où le sondage de secours sur `Native.isOnline()`.
     *
     * Retourne une fonction qui arrête la surveillance.
     */
    function surveillerConnexion(surRetourEnLigne, intervalleMs) {
        var etaitEnLigne = estEnLigne();
        var timer = null;

        function verifier() {
            var enLigne = estEnLigne();
            if (enLigne && !etaitEnLigne && typeof surRetourEnLigne === 'function') {
                surRetourEnLigne();
            }
            etaitEnLigne = enLigne;
        }

        if (root.addEventListener) {
            root.addEventListener('online', verifier);
            root.addEventListener('offline', verifier);
        }
        timer = setInterval(verifier, intervalleMs || 5000);

        return function arreter() {
            if (root.removeEventListener) {
                root.removeEventListener('online', verifier);
                root.removeEventListener('offline', verifier);
            }
            if (timer) clearInterval(timer);
        };
    }

    // Collections locales et table Supabase correspondante.
    var TABLES_A_MIGRER = [
        { cle: CLE_LOGS, table: 'daily_logs' },
        { cle: CLE_MENSURATIONS, table: 'measurements' },
        { cle: CLE_SEANCES, table: 'workouts' },
        { cle: CLE_SERIES, table: 'workout_sets' },
        { cle: CLE_NUTRITION, table: 'protein_entries' }
    ];

    /**
     * Pousse tout le contenu local dans la file de synchronisation.
     *
     * Les caches locaux ne sont PAS vidés ici : `schema.sql` du dépôt ne
     * correspond pas aux tables réellement interrogées par net.js (tables
     * préfixées `sr_`, tables de menus absentes). Vider avant d'avoir la
     * preuve que l'envoi a abouti ferait disparaître les données de
     * l'interface. La purge est faite par `purgerCachesLocaux()`, appelé
     * seulement après une synchronisation sans erreur et file vide.
     *
     * Les réglages, la session et la file elle-même sont toujours conservés.
     */
    function migrerDonneesLocalesVersFile() {
        var compte = 0;

        var profil = chargerJson(CLE_PROFIL, null);
        if (profil && Object.keys(profil).length) {
            enfile('profiles', 'upsert', 'profile', profil);
            compte++;
        }

        TABLES_A_MIGRER.forEach(function (t) {
            chargerJson(t.cle, []).forEach(function (ligne) {
                var cle = cleLocale(t.table, ligne);
                if (!cle) return;
                enfile(t.table, 'upsert', cle, ligne);
                compte++;
            });
        });

        // L'état coché de la liste de courses vit dans shopping_state.
        var semaine = semaineCourante();
        chargerJson(CLE_COURSES, []).forEach(function (item) {
            if (!item || item.pris !== true) return;
            var week = /^\d{4}-\d{2}-\d{2}\|/.test(String(item.id))
                ? String(item.id).slice(0, 10) : semaine;
            enfile('shopping_state', 'upsert', [item.id, week].join('|'), {
                item_key: String(item.id), week_of: week, checked: true
            });
            compte++;
        });

        return compte;
    }

    /**
     * Vide les caches locaux, une fois seulement l'envoi vers Supabase
     * confirmé. À partir de là Supabase fait autorité, et le tirage suivant
     * reconstitue le contenu depuis le serveur.
     */
    function purgerCachesLocaux() {
        TABLES_A_MIGRER.forEach(function (t) { sauverJson(t.cle, []); });
        sauverJson(CLE_COURSES, []);
        sauverJson(CLE_PROFIL, {});
    }

    function migrationFaite() { return chargerJson(CLE_MIGRATION_14, false) === true; }
    function marquerMigrationFaite() { sauverJson(CLE_MIGRATION_14, true); }
    function cachesPurges() { return chargerJson(CLE_PURGE_14, false) === true; }
    function marquerCachesPurges() { sauverJson(CLE_PURGE_14, true); }

    Store.estEnLigne = estEnLigne;
    Store.surveillerConnexion = surveillerConnexion;
    Store.migrerDonneesLocalesVersFile = migrerDonneesLocalesVersFile;
    Store.purgerCachesLocaux = purgerCachesLocaux;
    Store.cachesPurges = cachesPurges;
    Store.marquerCachesPurges = marquerCachesPurges;
    Store.migrationFaite = migrationFaite;
    Store.marquerMigrationFaite = marquerMigrationFaite;
    Store.viderFileMaintenant = function () { planifierSynchronisation(); };

    /**
     * Repas types tels que l'utilisateur les veut : le modèle de models.js
     * sert de base, puis ses corrections et ses créations sont appliquées.
     * Un repas marqué `supprime` disparaît de la liste.
     */
    Store.getRepasTypes = function () {
        var modele = (EQ.modele && EQ.modele.REPAS_TYPES) || [];
        var modifs = chargerJson(CLE_REPAS_TYPES, {});
        var out = [];
        modele.forEach(function (r) {
            var m = modifs[r.cle];
            if (m && m.supprime) return;
            out.push(Object.assign({}, r, m || {}));
        });
        Object.keys(modifs).forEach(function (cle) {
            var cree = modifs[cle];
            if (cree && !cree.supprime && !modele.some(function (r) { return r.cle === cle; })) {
                out.push(cree);
            }
        });
        return out;
    };

    Store.saveRepasType = function (repas) {
        if (!repas || !repas.cle) return false;
        var modifs = chargerJson(CLE_REPAS_TYPES, {});
        modifs[repas.cle] = Object.assign({}, modifs[repas.cle], repas, { supprime: false });
        return sauverJson(CLE_REPAS_TYPES, modifs);
    };

    Store.supprimerRepasType = function (cle) {
        var modifs = chargerJson(CLE_REPAS_TYPES, {});
        modifs[cle] = Object.assign({}, modifs[cle], { supprime: true });
        return sauverJson(CLE_REPAS_TYPES, modifs);
    };

    EQ.store = Store;
})(typeof window !== 'undefined' ? window : this);
