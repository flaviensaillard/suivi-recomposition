/* Couche réseau : synchronisation Supabase et requêtes asynchrones. */
(function (root) {
    'use strict';
    var EQ = root.EQ = root.EQ || {};

    var callbacks = {};
    var callbackSeq = 0;
    var decodeur = (typeof root.TextDecoder !== 'undefined') ? new root.TextDecoder('utf-8') : null;

    function b64versTexte(b64) {
        try {
            var bin = root.atob(b64);
            var octets = new Uint8Array(bin.length);
            for (var i = 0; i < bin.length; i++) octets[i] = bin.charCodeAt(i);
            if (decodeur) return decodeur.decode(octets);
            var s = '';
            for (var j = 0; j < bin.length; j++) s += String.fromCharCode(octets[j]);
            return decodeURIComponent(escape(s));
        } catch (e) {
            return '';
        }
    }

    function requete(methode, url, headers, body, cb) {
        headers = headers || {};

        // Si le pont natif Android est présent, passage direct sans restriction CORS
        if (typeof root.Native !== 'undefined' && root.Native.httpAsync) {
            var id = 'cb_' + (++callbackSeq) + '_' + Date.now();
            callbacks[id] = function (res) {
                if (res && res.body_b64) {
                    res.body = b64versTexte(res.body_b64);
                }
                cb(res);
            };
            try {
                root.Native.httpAsync(
                    methode,
                    url,
                    JSON.stringify(headers),
                    body ? (typeof body === 'string' ? body : JSON.stringify(body)) : '',
                    id
                );
                return;
            } catch (e) {
                console.warn('Native.httpAsync a échoué, repli fetch', e);
            }
        }

        // Repli standard fetch pour le navigateur / aperçu
        if (typeof root.fetch !== 'undefined') {
            var opts = {
                method: methode,
                headers: headers
            };
            if (body && methode !== 'GET' && methode !== 'HEAD') {
                opts.body = typeof body === 'string' ? body : JSON.stringify(body);
                if (!headers['Content-Type']) headers['Content-Type'] = 'application/json';
            }
            root.fetch(url, opts)
                .then(function (r) {
                    return r.text().then(function (txt) {
                        cb({ ok: r.ok, status: r.status, body: txt });
                    });
                })
                .catch(function (err) {
                    cb({ ok: false, status: -1, error: String(err && err.message) });
                });
            return;
        }

        cb({ ok: false, status: -1, error: 'Aucun transport disponible' });
    }

    // Réception du rappel depuis Java (NativeBridge)
    function _fin(callbackId, res) {
        var fn = callbacks[callbackId];
        if (fn) {
            delete callbacks[callbackId];
            fn(res);
        }
    }

    // Synchronisation avec Supabase (PostgREST)
    function synchroniserSupabase(cb) {
        var reglages = EQ.store.getReglages();
        if (!reglages.supabaseUrl || !reglages.supabaseKey) {
            if (cb) cb({ synchronise: false, raison: 'Pas de clés configurées' });
            return;
        }

        var url = reglages.supabaseUrl.replace(/\/+$/, '') + '/rest/v1/sr_daily_logs?select=*&order=log_date.desc&limit=60';
        var headers = {
            'apikey': reglages.supabaseKey,
            'Authorization': 'Bearer ' + reglages.supabaseKey,
            'Accept': 'application/json'
        };

        requete('GET', url, headers, null, function (res) {
            if (res.ok) {
                try {
                    var data = JSON.parse(res.body);
                    if (Array.isArray(data) && data.length > 0) {
                        data.forEach(function (row) {
                            EQ.store.saveLog({
                                date: row.log_date,
                                poids: row.weight_kg,
                                masseGrassePct: row.body_fat_pct,
                                proteinesG: row.protein_g,
                                caloriesKcal: row.kcal,
                                pas: row.steps,
                                sommeilH: row.sleep_h
                            });
                        });
                        if (cb) cb({ synchronise: true, count: data.length });
                        return;
                    }
                } catch (e) {
                }
            }
            if (cb) cb({ synchronise: false, status: res.status });
        });
    }

    EQ.net = {
        requete: requete,
        _fin: _fin,
        synchroniserSupabase: synchroniserSupabase
    };
})(typeof window !== 'undefined' ? window : this);
