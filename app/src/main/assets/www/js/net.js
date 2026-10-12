/* Transport, authentification Supabase et synchronisation local-first.
   Seule la clé publishable/anon est acceptée; les tables personnelles sont
   toujours appelées avec le JWT de l'utilisateur pour respecter RLS. */
(function (root) {
    'use strict';
    var EQ = root.EQ = root.EQ || {};
    var Store = EQ.store;
    var callbacks = {};
    var callbackSeq = 0;

    function b64versTexte(b64) {
        try {
            var bin = root.atob(b64);
            var octets = new Uint8Array(bin.length);
            for (var i = 0; i < bin.length; i++) octets[i] = bin.charCodeAt(i);
            return typeof root.TextDecoder !== 'undefined'
                ? new root.TextDecoder('utf-8').decode(octets)
                : decodeURIComponent(escape(bin));
        } catch (e) { return ''; }
    }

    function requete(methode, url, headers, body, cb) {
        headers = Object.assign({}, headers || {});
        var donnees = body == null ? null : (typeof body === 'string' ? body : JSON.stringify(body));
        if (donnees && !headers['Content-Type']) headers['Content-Type'] = 'application/json';

        // Le transport natif évite les restrictions CORS du fichier Android local.
        if (typeof root.Native !== 'undefined' && root.Native.httpAsync) {
            var id = 'cb_' + (++callbackSeq) + '_' + Date.now();
            callbacks[id] = function (res) {
                if (res && res.body_b64) res.body = b64versTexte(res.body_b64);
                if (cb) cb(res || { ok: false, status: -1, error: 'Réponse vide' });
            };
            try {
                root.Native.httpAsync(methode, url, JSON.stringify(headers), donnees || '', id);
                return;
            } catch (e) {
                delete callbacks[id];
                console.warn('Native.httpAsync a échoué, repli fetch', e);
            }
        }

        if (typeof root.fetch === 'function') {
            var options = { method: methode, headers: headers };
            if (donnees && methode !== 'GET' && methode !== 'HEAD') options.body = donnees;
            root.fetch(url, options).then(function (r) {
                return r.text().then(function (txt) {
                    if (cb) cb({ ok: r.ok, status: r.status, body: txt });
                });
            }).catch(function (e) {
                if (cb) cb({ ok: false, status: -1, error: String(e && e.message || e) });
            });
            return;
        }
        if (cb) cb({ ok: false, status: -1, error: 'Aucun transport réseau disponible' });
    }

    function _fin(callbackId, res) {
        var fn = callbacks[callbackId];
        if (fn) { delete callbacks[callbackId]; fn(res); }
    }

    function requeteP(methode, url, headers, body) {
        return new Promise(function (resolve, reject) {
            requete(methode, url, headers, body, function (res) {
                if (res && res.ok) {
                    var data = null;
                    try { data = res.body ? JSON.parse(res.body) : null; } catch (e) { data = res.body; }
                    resolve({ response: res, data: data });
                } else {
                    var message = res && (res.error || res.body) || 'Erreur réseau';
                    try {
                        var obj = JSON.parse(message);
                        message = obj.msg || obj.message || obj.error_description || obj.error || message;
                    } catch (e) { }
                    var err = new Error(String(message));
                    err.status = res && res.status;
                    err.response = res;
                    reject(err);
                }
            });
        });
    }

    function config() {
        var r = Store.getReglages();
        var url = String(r.supabaseUrl || '').trim().replace(/\/+$/, '');
        var key = String(r.supabaseKey || '').trim();
        if (!url || !/^https:\/\//i.test(url) || !/\.supabase\.co$/i.test(url.replace(/^https:\/\//i, '').split('/')[0])) {
            throw new Error('Renseigne l’URL du projet Supabase (https://….supabase.co) dans ⚙ Réglages.');
        }
        if (!key) throw new Error('Renseigne la clé publishable/anon Supabase dans ⚙ Réglages.');
        if (/^sb_secret_/i.test(key) || /service_role/i.test(key)) {
            throw new Error('La clé fournie est une clé secrète. Utilise uniquement la clé publishable/anon; la clé secrète ne doit jamais être dans l’APK.');
        }
        return { url: url, key: key };
    }

    function headersAuth(session, extra) {
        var c = config();
        return Object.assign({
            'apikey': c.key,
            'Authorization': 'Bearer ' + (session && session.access_token ? session.access_token : c.key),
            'Accept': 'application/json'
        }, extra || {});
    }

    function sauvegarderSession(session) {
        session.expires_at = session.expires_at || (Math.floor(Date.now() / 1000) + Number(session.expires_in || 3600));
        Store.saveRemoteSession(session);
        return session;
    }

    async function connexion(email, password) {
        var c = config();
        var rep = await requeteP('POST', c.url + '/auth/v1/token?grant_type=password', {
            'apikey': c.key, 'Content-Type': 'application/json', 'Accept': 'application/json'
        }, { email: String(email || '').trim(), password: String(password || '') });
        var s = rep.data || {};
        if (!s.access_token || !s.user || !s.user.id) throw new Error('Supabase n’a pas renvoyé de session valide.');
        sauvegarderSession(s);
        return { email: s.user.email || email, user_id: s.user.id };
    }

    async function sessionValide(force) {
        var s = Store.getRemoteSession();
        if (!s || !s.refresh_token) return null;
        if (!force && s.access_token && Number(s.expires_at || 0) > Math.floor(Date.now() / 1000) + 90) return s;
        var c = config();
        try {
            var rep = await requeteP('POST', c.url + '/auth/v1/token?grant_type=refresh_token', {
                'apikey': c.key, 'Content-Type': 'application/json', 'Accept': 'application/json'
            }, { refresh_token: s.refresh_token });
            var nouv = Object.assign({}, s, rep.data || {});
            if (!nouv.user && s.user) nouv.user = s.user;
            if (!nouv.access_token) throw new Error('Session Supabase expirée. Reconnecte-toi.');
            return sauvegarderSession(nouv);
        } catch (e) {
            Store.clearRemoteSession();
            throw new Error('La session Supabase a expiré. Reconnecte-toi pour synchroniser.');
        }
    }

    async function deconnexion() {
        var s = Store.getRemoteSession();
        if (s && s.access_token) {
            try {
                var c = config();
                await requeteP('POST', c.url + '/auth/v1/logout', headersAuth(s), null);
            } catch (e) { /* une déconnexion locale reste possible hors ligne */ }
        }
        Store.clearRemoteSession();
        return true;
    }

    function uuid(s) { return encodeURIComponent(String(s == null ? '' : s)); }
    function rowDaily(x, userId) {
        return {
            user_id: userId, log_date: x.date || x.log_date,
            weight_kg: x.poids == null ? x.weight_kg : x.poids,
            body_fat_pct: x.masseGrassePct == null ? x.body_fat_pct : x.masseGrassePct,
            steps: x.pas == null ? x.steps : x.pas,
            sleep_h: x.sommeilH == null ? x.sleep_h : x.sommeilH,
            protein_g: x.proteinesG == null ? x.protein_g : x.proteinesG,
            kcal: x.caloriesKcal == null ? x.kcal : x.caloriesKcal,
            activity: x.activity || null, energy: x.energy == null ? null : x.energy,
            notes: x.notes || null
        };
    }
    function localDaily(x) {
        return { date: String(x.log_date || x.date || '').slice(0, 10),
            poids: x.weight_kg == null ? null : Number(x.weight_kg),
            masseGrassePct: x.body_fat_pct == null ? null : Number(x.body_fat_pct),
            pas: x.steps == null ? null : Number(x.steps),
            sommeilH: x.sleep_h == null ? null : Number(x.sleep_h),
            proteinesG: x.protein_g == null ? 0 : Number(x.protein_g),
            caloriesKcal: x.kcal == null ? 0 : Number(x.kcal),
            activity: x.activity || '', energy: x.energy == null ? null : Number(x.energy),
            notes: x.notes || '' };
    }
    function rowMeasurement(x, userId) {
        return { user_id: userId, meas_date: x.date || x.meas_date,
            waist_cm: x.tailleCm == null ? x.waist_cm : x.tailleCm,
            hips_cm: x.hanchesCm == null ? x.hips_cm : x.hanchesCm,
            chest_cm: x.poitrineCm == null ? x.chest_cm : x.poitrineCm,
            neck_cm: x.couCm == null ? x.neck_cm : x.couCm,
            arm_cm: x.brasCm == null ? x.arm_cm : x.brasCm,
            thigh_cm: x.cuisseCm == null ? x.thigh_cm : x.cuisseCm,
            photos: !!x.photos, notes: x.notes || null };
    }
    function localMeasurement(x) {
        return { date: String(x.meas_date || x.date || '').slice(0, 10),
            tailleCm: x.waist_cm == null ? null : Number(x.waist_cm),
            hanchesCm: x.hips_cm == null ? null : Number(x.hips_cm),
            poitrineCm: x.chest_cm == null ? null : Number(x.chest_cm),
            couCm: x.neck_cm == null ? null : Number(x.neck_cm),
            brasCm: x.arm_cm == null ? null : Number(x.arm_cm),
            cuisseCm: x.thigh_cm == null ? null : Number(x.thigh_cm),
            photos: !!x.photos, notes: x.notes || '' };
    }
    function rowWorkout(x, userId) {
        return { user_id: userId, session_date: x.date || x.session_date,
            session: x.type || x.session || 'A', duration_min: x.dureeMin == null ? x.duration_min : x.dureeMin,
            rpe: x.rpe == null ? null : x.rpe, notes: x.notes || null };
    }
    function ressentiDepuisNotes(notes) {
        var texte = String(notes || '').toLowerCase();
        var debut = texte.indexOf('ressenti');
        if (debut < 0) return '';
        var reste = texte.slice(debut + 8).trim();
        if (reste.charAt(0) === ':' || reste.charAt(0) === '=') reste = reste.slice(1).trim();
        var valeur = reste.split(' ')[0].split('·')[0].replace(/[.;,]/g, '');
        return ['facile', 'normal', 'difficile'].indexOf(valeur) >= 0 ? valeur : '';
    }
    function localWorkout(x) {
        var ressenti = String(x.ressenti || '').toLowerCase();
        if (['facile', 'normal', 'difficile'].indexOf(ressenti) < 0) ressenti = ressentiDepuisNotes(x.notes);
        return { date: String(x.session_date || x.date || '').slice(0, 10),
            type: x.session || x.type || 'A', nom: x.nom || ('Séance ' + (x.session || x.type || 'A')),
            dureeMin: x.duration_min == null ? null : Number(x.duration_min),
            rpe: x.rpe == null ? null : Number(x.rpe), ressenti: ressenti, notes: x.notes || '' };
    }
    function rowSet(x, userId) {
        return { user_id: userId, set_date: x.date || x.set_date,
            session: x.type || x.session || 'A', exercise: x.exercise,
            set_no: Number(x.set_no), reps: x.reps == null ? null : Number(x.reps),
            load_kg: x.load_kg == null ? null : Number(x.load_kg),
            variant: x.variant || null, rpe: x.rpe == null ? null : Number(x.rpe) };
    }
    function localSet(x) {
        return { date: String(x.set_date || x.date || '').slice(0, 10), type: x.session || x.type || 'A',
            exercise: x.exercise, set_no: Number(x.set_no), reps: x.reps == null ? null : Number(x.reps),
            load_kg: x.load_kg == null ? null : Number(x.load_kg), variant: x.variant || '',
            rpe: x.rpe == null ? null : Number(x.rpe) };
    }
    function rowProtein(x, userId) {
        var r = { user_id: userId, entry_date: x.date || x.entry_date,
            item: String(x.item || 'Repas'), protein_g: Number(x.protein_g || 0),
            qty: Number(x.qty == null ? 1 : x.qty) };
        if (x.carbs_g != null) r.carbs_g = Number(x.carbs_g);
        if (x.fat_g != null) r.fat_g = Number(x.fat_g);
        if (x.id && /^\d+$/.test(String(x.id))) r.id = Number(x.id);
        return r;
    }
    function localProtein(x) {
        return { id: x.id, local_id: String(x.id), date: String(x.entry_date || x.date || '').slice(0, 10),
            item: x.item || '', protein_g: Number(x.protein_g || 0), carbs_g: Number(x.carbs_g || 0),
            fat_g: Number(x.fat_g || 0), qty: Number(x.qty == null ? 1 : x.qty) };
    }
    function rowProfile(x, userId) {
        var r = { user_id: userId, display_name: x.displayName || x.display_name || '',
            height_cm: Number(x.tailleCm || x.height_cm || 185),
            start_weight_kg: Number(x.poidsDepartKg || x.start_weight_kg || 85),
            target_weight_kg: Number(x.poidsCibleKg || x.target_weight_kg || 77),
            target_protein_g: Number(x.objectifProteinesG || x.target_protein_g || 130),
            tdee_kcal: Number(x.tdeeKcal || x.tdee_kcal || 2400),
            phase: x.phase || 'Bloc 0 — remise à niveau' };
        // Certaines bases ont les colonnes étendues; le serveur réessaie sans elles si besoin.
        r.target_carbs_g = Number(x.objectifGlucidesG || x.target_carbs_g || 140);
        r.target_fat_g = Number(x.objectifLipidesG || x.target_fat_g || 50);
        r.target_kcal = Number(x.objectifCaloriesKcal || x.target_kcal || 1700);
        return r;
    }
    function localProfile(x) {
        return { displayName: x.display_name || '', tailleCm: Number(x.height_cm || 185),
            poidsDepartKg: Number(x.start_weight_kg || 85), poidsCibleKg: Number(x.target_weight_kg || 77),
            objectifProteinesG: Number(x.target_protein_g || 130),
            objectifGlucidesG: Number(x.target_carbs_g || 140),
            objectifLipidesG: Number(x.target_fat_g || 50),
            objectifCaloriesKcal: Number(x.target_kcal || 1700), tdeeKcal: Number(x.tdee_kcal || 2400),
            phase: x.phase || '' };
    }

    function tableUrl(table, params) {
        var c = config();
        var qs = Object.keys(params || {}).map(function (k) {
            return encodeURIComponent(k) + '=' + encodeURIComponent(params[k]);
        }).join('&');
        return c.url + '/rest/v1/' + table + (qs ? '?' + qs : '');
    }

    function lignesSupabase(table) {
        return ['ingredients', 'recipes', 'recipe_ingredients', 'planned_meals'].indexOf(table) >= 0;
    }

    function nettoyerLigneMenu(table, source) {
        var row = Object.assign({}, source || {});
        delete row._local_id;
        delete row.local_id;
        delete row._pending;
        if (table === 'planned_meals' && row.id != null && !/^\\d+$/.test(String(row.id))) delete row.id;
        return row;
    }

    async function pushMenuItem(item, session) {
        var table = String(item.table || '').replace(/^menu:/, '');
        if (!lignesSupabase(table)) return true;
        var base = config().url + '/rest/v1/' + table;
        var source = item.row || {};
        var id = source.id != null ? source.id : (table === 'planned_meals' ? null : item.key);
        var aId = id != null && (table !== 'planned_meals' || /^\\d+$/.test(String(id)));
        if (item.operation === 'delete') {
            if (!aId) return true;
            await requeteP('DELETE', base + '?id=eq.' + uuid(id),
                headersAuth(session, { 'Prefer': 'return=minimal' }), null);
            return true;
        }
        var row = nettoyerLigneMenu(table, source);
        if (table !== 'planned_meals' && !row.id) row.id = item.key;
        if ((item.operation === 'update' || item.operation === 'upsert') && aId) {
            delete row.id;
            try {
                await requeteP('PATCH', base + '?id=eq.' + uuid(id),
                    headersAuth(session, { 'Prefer': 'return=minimal' }), row);
            } catch (e) {
                if (table !== 'planned_meals' || !('ingredient_unit' in row) || !/ingredient_unit|column|schema/i.test(e.message)) throw e;
                delete row.ingredient_unit;
                await requeteP('PATCH', base + '?id=eq.' + uuid(id),
                    headersAuth(session, { 'Prefer': 'return=minimal' }), row);
            }
            return true;
        }
        var url = base;
        var prefer = 'return=representation';
        if (table !== 'planned_meals') {
            url += '?on_conflict=id';
            prefer = 'resolution=merge-duplicates,return=representation';
        }
        var rep;
        try {
            rep = await requeteP('POST', url, headersAuth(session, { 'Prefer': prefer }), row);
        } catch (e) {
            if (table !== 'planned_meals' || !('ingredient_unit' in row) || !/ingredient_unit|column|schema/i.test(e.message)) throw e;
            delete row.ingredient_unit;
            rep = await requeteP('POST', url, headersAuth(session, { 'Prefer': prefer }), row);
        }
        var localId = source._local_id || source.local_id ||
            (table === 'planned_meals' && !aId ? item.key : null);
        if (table === 'planned_meals' && localId && rep.data && rep.data[0] && Store.attachPlannedMealServerId) {
            Store.attachPlannedMealServerId(localId, rep.data[0]);
        }
        return true;
    }

    async function pushItem(item, userId, session) {
        if (String(item.table || '').indexOf('menu:') === 0) return pushMenuItem(item, session);
        var table = 'sr_' + item.table;
        var base = config().url + '/rest/v1/' + table;
        var h = headersAuth(session, { 'Content-Type': 'application/json' });
        var row, url, resp;
        if (item.operation === 'delete') {
            if (item.table === 'daily_logs') {
                url = base + '?user_id=eq.' + uuid(userId) + '&log_date=eq.' + uuid(item.key);
            } else if (item.table === 'measurements') {
                url = base + '?user_id=eq.' + uuid(userId) + '&meas_date=eq.' + uuid(item.key);
            } else if (item.table === 'workouts') {
                var wk = item.key.split('|');
                url = base + '?user_id=eq.' + uuid(userId) + '&session_date=eq.' + uuid(wk[0]) + '&session=eq.' + uuid(wk[1]);
            } else if (item.table === 'workout_sets') {
                var sk = item.key.split('|');
                url = base + '?user_id=eq.' + uuid(userId) + '&set_date=eq.' + uuid(sk[0]) + '&session=eq.' + uuid(sk[1]) +
                    '&exercise=eq.' + uuid(sk[2]) + '&set_no=eq.' + uuid(sk[3]);
            } else if (item.table === 'protein_entries') {
                var pId = item.row && item.row.id;
                if (!pId || !/^\d+$/.test(String(pId))) return true; // ligne jamais envoyée au cloud
                url = base + '?user_id=eq.' + uuid(userId) + '&id=eq.' + uuid(pId);
            } else if (item.table === 'shopping_state') {
                var ck = item.key.split('|');
                url = base + '?user_id=eq.' + uuid(userId) + '&item_key=eq.' + uuid(ck[0]) + '&week_of=eq.' + uuid(ck[1]);
            } else {
                return true;
            }
            await requeteP('DELETE', url, headersAuth(session, { 'Prefer': 'return=minimal' }), null);
            return true;
        }

        var conflict = '';
        if (item.table === 'daily_logs') {
            row = rowDaily(item.row || {}, userId); conflict = 'user_id,log_date';
        } else if (item.table === 'measurements') {
            row = rowMeasurement(item.row || {}, userId); conflict = 'user_id,meas_date';
        } else if (item.table === 'workouts') {
            row = rowWorkout(item.row || {}, userId); conflict = 'user_id,session_date,session';
        } else if (item.table === 'workout_sets') {
            row = rowSet(item.row || {}, userId); conflict = 'user_id,set_date,session,exercise,set_no';
        } else if (item.table === 'profiles') {
            row = rowProfile(item.row || {}, userId); conflict = 'user_id';
        } else if (item.table === 'shopping_state') {
            row = Object.assign({}, item.row || {}, { user_id: userId });
            conflict = 'user_id,item_key,week_of';
        } else if (item.table === 'protein_entries') {
            row = rowProtein(item.row || {}, userId);
            if (item.operation === 'update' && row.id) {
                var id = row.id; delete row.id;
                url = base + '?user_id=eq.' + uuid(userId) + '&id=eq.' + uuid(id);
                await requeteP('PATCH', url, headersAuth(session, { 'Prefer': 'return=minimal' }), row);
                return true;
            }
            // L'identifiant serveur est attribué lors de l'envoi; on le rattache
            // ensuite à la ligne locale pour que les modifications/suppressions suivantes visent la bonne ligne.
            var localId = String((item.row || {}).local_id || item.key);
            try {
                resp = await requeteP('POST', base, headersAuth(session, { 'Prefer': 'return=representation' }), row);
            } catch (e) {
                if (!('carbs_g' in row) && !('fat_g' in row)) throw e;
                delete row.carbs_g; delete row.fat_g;
                resp = await requeteP('POST', base, headersAuth(session, { 'Prefer': 'return=representation' }), row);
            }
            if (resp.data && resp.data[0] && Store.attachNutritionServerId) {
                Store.attachNutritionServerId(localId, resp.data[0]);
            }
            return true;
        } else {
            return true;
        }

        url = base + '?on_conflict=' + encodeURIComponent(conflict);
        try {
            await requeteP('POST', url, headersAuth(session, {
                'Prefer': 'resolution=merge-duplicates,return=minimal'
            }), row);
        } catch (e) {
            // Compatibilité avec les bases qui n'ont pas encore ajouté les macros au profil.
            if (item.table !== 'profiles' || (!('target_carbs_g' in row) && !('target_fat_g' in row) && !('target_kcal' in row))) throw e;
            delete row.target_carbs_g; delete row.target_fat_g; delete row.target_kcal;
            await requeteP('POST', url, headersAuth(session, {
                'Prefer': 'resolution=merge-duplicates,return=minimal'
            }), row);
        }
        return true;
    }

    async function lireTable(table, userId, session, order) {
        var params = { select: '*', user_id: 'eq.' + userId, limit: '1000' };
        if (order) params.order = order;
        var rep = await requeteP('GET', tableUrl('sr_' + table, params), headersAuth(session), null);
        return Array.isArray(rep.data) ? rep.data : [];
    }

    async function lireTableMenu(table, session) {
        if (!lignesSupabase(table)) throw new Error('Table de menus inconnue.');
        var lignes = [], offset = 0, taille = 1000;
        while (offset < 20000) {
            var rep = await requeteP('GET', tableUrl(table, {
                select: '*', limit: String(taille), offset: String(offset), order: 'id.asc'
            }), headersAuth(session), null);
            var page = Array.isArray(rep.data) ? rep.data : [];
            lignes = lignes.concat(page);
            if (page.length < taille) break;
            offset += page.length;
        }
        return lignes;
    }

    async function executerSynchronisation() {
        var s = await sessionValide(false);
        if (!s || !s.user || !s.user.id) {
            return { synchronise: false, raison: 'Connecte-toi à Supabase dans ⚙ Réglages pour synchroniser.' };
        }
        var userId = s.user.id;
        var erreurs = [], envoyes = 0;
        var queue = Store.getSyncQueue().slice();
        for (var i = 0; i < queue.length; i++) {
            try {
                await pushItem(queue[i], userId, s);
                Store.removeSyncItem(queue[i].id);
                envoyes++;
            } catch (e) {
                erreurs.push(queue[i].table + ' : ' + e.message);
                // Une erreur de schéma sur une table ne doit pas empêcher les autres de se synchroniser.
            }
        }

        var nLus = 0;
        var lectures = [
            ['profiles', 'created_at.asc'], ['daily_logs', 'log_date.asc'],
            ['measurements', 'meas_date.asc'], ['workouts', 'session_date.asc'],
            ['workout_sets', 'set_date.asc'], ['protein_entries', 'entry_date.asc'],
            ['shopping_state', 'week_of.asc']
        ];
        for (var j = 0; j < lectures.length; j++) {
            var nom = lectures[j][0];
            try {
                var rows = await lireTable(nom, userId, s, lectures[j][1]);
                nLus += rows.length;
                if (nom === 'profiles' && rows.length) {
                    var p = localProfile(rows[0]);
                    Store.mergeRemote('eq.profil.v1', 'profiles', [p], function () { return 'profile'; });
                    // Ne fusionner que les champs reçus du profil : getReglages
                    // conserve ainsi l'URL et la clé Supabase configurées localement.
                    Store.saveReglages(Object.assign(Store.getReglages(), p));
                } else if (nom === 'daily_logs') {
                    Store.mergeRemoteLogs(rows.map(localDaily));
                } else if (nom === 'measurements') {
                    Store.mergeRemoteMensurations(rows.map(localMeasurement));
                } else if (nom === 'workouts') {
                    Store.mergeRemoteWorkouts(rows.map(localWorkout));
                } else if (nom === 'workout_sets') {
                    Store.mergeRemoteSeries(rows.map(localSet));
                } else if (nom === 'protein_entries') {
                    Store.mergeRemoteNutrition(rows.map(localProtein));
                } else if (nom === 'shopping_state') {
                    Store.mergeRemoteShoppingState(rows);
                }
            } catch (e) {
                erreurs.push(nom + ' : ' + e.message);
            }
        }
        var tablesMenu = ['ingredients', 'recipes', 'recipe_ingredients', 'planned_meals'];
        for (var m = 0; m < tablesMenu.length; m++) {
            var tableMenu = tablesMenu[m];
            try {
                var rowsMenu = await lireTableMenu(tableMenu, s);
                nLus += rowsMenu.length;
                Store.mergeRemoteMenu(tableMenu, rowsMenu);
            } catch (e) {
                erreurs.push(tableMenu + ' : ' + e.message);
            }
        }
        if (erreurs.length) {
            return { synchronise: envoyes > 0 || nLus > 0, envoye: envoyes, recu: nLus,
                enAttente: Store.syncCount(), erreurs: erreurs };
        }
        return { synchronise: true, envoye: envoyes, recu: nLus, enAttente: Store.syncCount() };
    }

    var synchronisationEnCours = null;
    function synchroniser() {
        if (!synchronisationEnCours) {
            synchronisationEnCours = executerSynchronisation().finally(function () { synchronisationEnCours = null; });
        }
        return synchronisationEnCours;
    }

    function synchroniserSupabase(cb) {
        synchroniser().then(function (result) { if (cb) cb(result); }).catch(function (e) {
            if (cb) cb({ synchronise: false, raison: e.message, status: e.status });
        });
    }

    EQ.net = {
        requete: requete,
        requeteP: requeteP,
        _fin: _fin,
        config: config,
        connexion: connexion,
        deconnexion: deconnexion,
        sessionValide: sessionValide,
        synchroniser: synchroniser,
        synchroniserSupabase: synchroniserSupabase
    };
})(typeof window !== 'undefined' ? window : this);
