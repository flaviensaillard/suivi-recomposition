/* Coach IA — interface et client de l'API Cloudflare.
   Les appels authentifiés réutilisent la session Supabase déjà présente sur l'appareil.
   Aucun secret Cloudflare/Tavily n'est conservé dans l'application. */
(function (root) {
    'use strict';
    var EQ = root.EQ = root.EQ || {};
    var UI = EQ.ui, Store = EQ.store, Net = EQ.net, U = EQ.util, M = EQ.modele;
    var CACHE_MESSAGES = 'eq.coach.messages.cache.v1';
    var cacheUserKey = cleCacheUtilisateur();
    var messages = lireCache(cacheUserKey);
    var reports = [];
    var memoryText = '';
    var memoryLoaded = false;
    var memoryUpdated = null;
    var draft = null;
    var busyChat = false;
    var busyAnalysis = false;
    var busyMemory = false;
    var busyReport = false;
    var loadedBase = '';
    var h = UI && UI.h ? UI.h : function (s) { return U.echapper(s); };

    function cleCacheUtilisateur() {
        try {
            var session = Store && Store.getRemoteSession ? Store.getRemoteSession() : null;
            var id = session && session.user && session.user.id ? String(session.user.id) : 'sans-compte';
            return CACHE_MESSAGES + '.' + id;
        } catch (e) { return CACHE_MESSAGES + '.sans-compte'; }
    }
    function synchroniserCacheUtilisateur() {
        var next = cleCacheUtilisateur();
        if (next !== cacheUserKey) {
            cacheUserKey = next;
            messages = lireCache(cacheUserKey);
            reports = [];
            memoryText = '';
            memoryLoaded = false;
            memoryUpdated = null;
        }
    }
    function lireCache(cle) {
        try {
            var value = root.localStorage && root.localStorage.getItem(cle || CACHE_MESSAGES);
            var parsed = value ? JSON.parse(value) : [];
            return Array.isArray(parsed) ? parsed.slice(-60) : [];
        } catch (e) { return []; }
    }
    function sauverCache() {
        try {
            if (root.localStorage) root.localStorage.setItem(cacheUserKey, JSON.stringify(messages.slice(-60)));
        } catch (e) { /* le cache local est facultatif */ }
    }
    function baseWorker() {
        var url = String(Store.getReglages().coachApiUrl || '').trim().replace(/\/+$/, '');
        if (!url) throw new Error('Renseigne d’abord l’URL du Worker Coach IA dans ⚙ Réglages.');
        if (!/^https:\/\//i.test(url)) throw new Error('L’URL du Worker doit commencer par https://.');
        return url;
    }
    async function api(path, method, body, authRequired) {
        var url = baseWorker() + path;
        var headers = { 'Accept': 'application/json' };
        if (body != null) headers['Content-Type'] = 'application/json';
        if (authRequired !== false) {
            if (!Net || !Net.sessionValide) throw new Error('La connexion Supabase n’est pas disponible.');
            var session = await Net.sessionValide(false);
            if (!session || !session.access_token) throw new Error('Connecte-toi à Supabase dans ⚙ Réglages avant d’utiliser le Coach IA.');
            headers.Authorization = 'Bearer ' + session.access_token;
        }
        var result = await Net.requeteP(method || 'GET', url, headers, body == null ? null : body);
        return result.data || {};
    }
    function erreurTexte(error) {
        return error && error.message ? String(error.message) : 'Erreur réseau. Vérifie la connexion et réessaie.';
    }
    function isoAujourdhui() { return U.dateIso(new Date()); }
    function huer(n) { return Math.max(0, Math.min(100, Number(n) || 0)); }
    function dateEgale(row, date) {
        return String(row && (row.date || row.log_date || row.meas_date || row.session_date || row.set_date || row.entry_date || row.date_menu) || '').slice(0, 10) === date;
    }
    function kcalMacros(t) {
        return Math.round((Number(t.protein_g || 0) + Number(t.carbs_g || 0)) * 4 + Number(t.fat_g || 0) * 9);
    }
    function nomExercice(id, type) {
        var programme = type === 'B' ? M.SEANCE_B : M.SEANCE_A;
        var nom = String(id || '');
        (programme && programme.blocs || []).forEach(function (bloc) {
            (bloc.exos || []).forEach(function (exo) {
                if (String(exo.id) === nom) nom = exo.nom;
            });
        });
        return nom;
    }
    function construireCatalogue() {
        var menu = EQ.menu;
        var catalogue = { recettes: [], aliments: [] };
        if (!menu || !Store) return catalogue;
        try {
            catalogue.recettes = menu.recettes('', false).slice(0, 18).map(function (r) {
                var calc = menu.calculerRecette(r.id);
                return {
                    nom: r.name || '',
                    portions: calc ? calc.parts : (Number(r.base_servings) || null),
                    macros_par_portion: calc ? calc.par_part : null,
                    ingredients: calc ? calc.lignes.map(function (x) { return x.name; }).slice(0, 16) : []
                };
            });
        } catch (e) { catalogue.recettes = []; }
        try {
            catalogue.aliments = Store.getMenuTable('ingredients').filter(function (x) {
                return !!(x.nom_affiche || x.name);
            }).slice(0, 35).map(function (x) {
                return {
                    nom: String(x.nom_affiche || x.name || '').slice(0, 100),
                    categorie: String(x.category || '').slice(0, 80),
                    kcal_100g: x.kcal_100g == null ? null : Number(x.kcal_100g),
                    proteines_100g: x.proteines_100g == null ? null : Number(x.proteines_100g),
                    glucides_100g: x.glucides_100g == null ? null : Number(x.glucides_100g),
                    lipides_100g: x.lipides_100g == null ? null : Number(x.lipides_100g)
                };
            });
        } catch (e2) { catalogue.aliments = []; }
        return catalogue;
    }
    function construireContexteChat(ctx) {
        ctx = ctx || {};
        var logs = (ctx.logs || []).slice().sort(function (a, b) { return String(a.date).localeCompare(String(b.date)); });
        var aujourd = isoAujourdhui();
        var start = new Date(aujourd + 'T12:00:00');
        start.setDate(start.getDate() - 6);
        var debut7j = U.dateIso(start);
        var logs7 = logs.filter(function (x) { return String(x.date || '') >= debut7j && String(x.date || '') <= aujourd; });
        var nutrition = (ctx.nutrition || []).filter(function (x) { return String(x.date || x.entry_date || '').slice(0, 10) >= debut7j; });
        var seances = (ctx.seances || []).slice().sort(function (a, b) {
            return String(a.date || a.session_date || '').localeCompare(String(b.date || b.session_date || ''));
        }).slice(-4).map(function (x) {
            return { date: String(x.date || x.session_date || '').slice(0, 10), type: x.type || x.session || '',
                duree_min: x.dureeMin == null ? x.duration_min : x.dureeMin,
                ressenti: x.ressenti || '', notes: String(x.notes || '').slice(0, 160) };
        });
        var mesures = (ctx.mensurations || []).slice().sort(function (a, b) { return String(a.date).localeCompare(String(b.date)); });
        var total7 = { protein_g: 0, carbs_g: 0, fat_g: 0 };
        nutrition.forEach(function (x) {
            total7.protein_g += Number(x.protein_g || 0);
            total7.carbs_g += Number(x.carbs_g || 0);
            total7.fat_g += Number(x.fat_g || 0);
        });
        var joursAvecNutrition = {};
        nutrition.forEach(function (x) { joursAvecNutrition[String(x.date || x.entry_date || '').slice(0, 10)] = true; });
        var plannedMeals = [];
        if (EQ.menu && EQ.menu.planned) {
            try {
                plannedMeals = EQ.menu.planned(aujourd).map(function (row) {
                    var detail = EQ.menu.detailsRepas(row);
                    return { planifie: true, repas: row.meal_type || 'Repas', recette: detail && detail.name || 'Recette non disponible' };
                }).slice(0, 8);
            } catch (e) { plannedMeals = []; }
        }
        var r = ctx.reglages || {};
        return {
            date_du_resume: aujourd,
            objectifs: { calories_kcal: Number(r.objectifCaloriesKcal || 0), proteines_g: Number(r.objectifProteinesG || 0),
                glucides_g: Number(r.objectifGlucidesG || 0), lipides_g: Number(r.objectifLipidesG || 0), poids_cible_kg: Number(r.poidsCibleKg || 0) },
            dernieres_pesees: logs.slice(-7).map(function (x) { return { date: x.date, poids_kg: x.poids == null ? null : Number(x.poids) }; }),
            habitudes_7j: logs7.map(function (x) { return { date: x.date, pas: x.pas, sommeil_h: x.sommeilH, activite: x.activity || '', energie_1_10: x.energy == null ? null : Number(x.energy) }; }),
            nutrition_7j: { jours_avec_saisie: Object.keys(joursAvecNutrition).length,
                totaux_saisis: { proteines_g: Math.round(total7.protein_g), glucides_g: Math.round(total7.carbs_g), lipides_g: Math.round(total7.fat_g) },
                moyenne_par_jour_avec_saisie: Object.keys(joursAvecNutrition).length ? {
                    proteines_g: Math.round(total7.protein_g / Object.keys(joursAvecNutrition).length),
                    glucides_g: Math.round(total7.carbs_g / Object.keys(joursAvecNutrition).length),
                    lipides_g: Math.round(total7.fat_g / Object.keys(joursAvecNutrition).length),
                    kcal_approx: Math.round(kcalMacros(total7) / Object.keys(joursAvecNutrition).length)
                } : null,
                avertissement: 'Journal et portions potentiellement approximatifs; aucune précision supérieure aux saisies.' },
            seances_recentes: seances,
            derniere_mensuration: mesures.length ? mesures[mesures.length - 1] : null,
            repas_planifies_aujourdhui: plannedMeals,
            catalogue_recettes_et_aliments: construireCatalogue()
        };
    }
    function construireJournee(ctx, date, fatigue, notes) {
        ctx = ctx || {};
        var logs = ctx.logs || [];
        var log = logs.find(function (x) { return String(x.date || '') === date; }) || null;
        var mensurations = (ctx.mensurations || []).filter(function (x) { return dateEgale(x, date); });
        var mesuresPrecedentes = (ctx.mensurations || []).filter(function (x) { return String(x.date || '') <= date; })
            .sort(function (a, b) { return String(a.date || '').localeCompare(String(b.date || '')); });
        var poidsRecents = logs.filter(function (x) { return String(x.date || '') <= date; }).slice(-7).map(function (x) {
            return { date: x.date, poids_kg: x.poids == null ? null : Number(x.poids) };
        });
        var nutrition = (ctx.nutrition || []).filter(function (x) { return dateEgale(x, date); }).map(function (x) {
            return { aliment_ou_repas: String(x.item || 'Repas').slice(0, 140), quantite: x.qty == null ? null : Number(x.qty),
                proteines_g: Number(x.protein_g || 0), glucides_g: Number(x.carbs_g || 0), lipides_g: Number(x.fat_g || 0) };
        });
        var totaux = Store.totauxNutrition(date);
        var seances = (ctx.seances || []).filter(function (x) { return dateEgale(x, date); }).map(function (x) {
            var type = String(x.type || x.session || 'A');
            var sets = (Store.getSeries() || []).filter(function (s) {
                return dateEgale(s, date) && String(s.type || s.session || 'A') === type;
            }).map(function (s) {
                return { exercice: nomExercice(s.exercise, type), serie: s.set_no, repetitions_ou_secondes: s.reps,
                    charge_kg: s.load_kg == null ? null : Number(s.load_kg), variante: s.variant || '', ressenti_serie: s.rpe == null ? null : s.rpe };
            });
            return { type: type, duree_min: x.dureeMin == null ? x.duration_min : x.dureeMin,
                ressenti: x.ressenti || '', notes: String(x.notes || '').slice(0, 250), series: sets };
        });
        var planned = [];
        if (EQ.menu && EQ.menu.planned) {
            try {
                planned = EQ.menu.planned(date).map(function (row) {
                    var detail = EQ.menu.detailsRepas(row);
                    return { statut: 'planifié, non confirmé comme consommé', repas: row.meal_type || 'Repas', recette: detail && detail.name || 'Recette non disponible' };
                }).slice(0, 12);
            } catch (e) { planned = []; }
        }
        var r = ctx.reglages || {};
        return {
            date: date,
            poids_recents_jusqu_a_date: poidsRecents,
            derniere_mensuration_connue: mesuresPrecedentes.length ? mesuresPrecedentes[mesuresPrecedentes.length - 1] : null,
            poids_et_habitudes: log ? { poids_kg: log.poids == null ? null : Number(log.poids), masse_grasse_pct: log.masseGrassePct == null ? null : Number(log.masseGrassePct),
                pas: log.pas == null ? null : Number(log.pas), sommeil_h: log.sommeilH == null ? null : Number(log.sommeilH),
                activite: log.activity || '', energie_1_10: log.energy == null ? null : Number(log.energy), notes: String(log.notes || '').slice(0, 1000) } : null,
            fatigue_ressentie_1_10: fatigue == null || fatigue === '' ? null : Number(fatigue),
            mensurations_du_jour: mensurations,
            repas_saisis_dans_le_journal: nutrition,
            totaux_nutrition_saisis: { proteines_g: Math.round(totaux.protein_g), glucides_g: Math.round(totaux.carbs_g), lipides_g: Math.round(totaux.fat_g), calories_approx_kcal: kcalMacros(totaux) },
            avertissement_nutrition: 'Les saisies, quantités, marques et poids crus/cuits peuvent être approximatifs.',
            entrainements_realises_enregistres: seances,
            repas_planifies_non_confirmes: planned,
            cibles_actives: { calories_kcal: Number(r.objectifCaloriesKcal || 0), proteines_g: Number(r.objectifProteinesG || 0), glucides_g: Number(r.objectifGlucidesG || 0), lipides_g: Number(r.objectifLipidesG || 0) },
            catalogue_recettes_et_aliments: construireCatalogue(),
            precision_utilisateur: String(notes || '').trim().slice(0, 1500)
        };
    }
    function setStatus(text, type) {
        var node = UI.$('#coachStatus');
        if (!node) return;
        node.textContent = text;
        node.className = 'badge ' + (type || 'mut');
    }
    function setMemoryStatus(text) {
        var node = UI.$('#coachMemoryStatus');
        if (node) node.textContent = text;
    }
    function boutonOuvrirReglages() {
        var b = UI.$('#btnReglages');
        if (b) b.click();
    }
    function dateFr(date) {
        try { return U.dateFr(date, { jour: true, annee: true }); } catch (e) { return date; }
    }
    function creerEl(tag, cls, texte) {
        var el = root.document.createElement(tag);
        if (cls) el.className = cls;
        if (texte != null) el.textContent = texte;
        return el;
    }
    function lienSource(source) {
        if (!source || !/^https:\/\//i.test(String(source.url || ''))) return null;
        var a = creerEl('a', 'coach-source', String(source.title || source.url));
        a.href = source.url;
        a.target = '_blank';
        a.rel = 'noopener noreferrer';
        a.title = source.url;
        a.addEventListener('click', function (event) {
            if (root.Native && root.Native.openExternal) {
                event.preventDefault();
                root.Native.openExternal(source.url);
            }
        });
        return a;
    }
    function rendreMessages(main) {
        var host = UI.$('#coachMessages', main);
        if (!host) return;
        host.textContent = '';
        if (!messages.length) {
            host.appendChild(creerEl('div', 'coach-empty', 'Le chat est prêt. Importe d’abord ton manifeste validé, puis écris librement au coach.'));
        }
        messages.slice(-60).forEach(function (m) {
            var item = creerEl('article', 'coach-message ' + (m.role === 'user' ? 'user' : 'assistant'));
            item.appendChild(creerEl('div', 'coach-message-who', m.role === 'user' ? 'Toi' : 'Coach IA'));
            var copy = creerEl('div', 'coach-message-copy', String(m.content || ''));
            item.appendChild(copy);
            var sources = Array.isArray(m.sources) ? m.sources : [];
            if (sources.length) {
                var box = creerEl('div', 'coach-sources');
                box.appendChild(creerEl('div', 'coach-sources-title', '🔎 Recherche web effectuée · sources'));
                sources.forEach(function (s, i) {
                    var row = root.document.createElement('div');
                    row.className = 'coach-source-row';
                    row.appendChild(creerEl('span', 'coach-source-number', '[' + (i + 1) + ']'));
                    var a = lienSource(s);
                    if (a) row.appendChild(a);
                    box.appendChild(row);
                });
                item.appendChild(box);
            }
            if (m.pending) item.classList.add('pending');
            host.appendChild(item);
        });
        if (busyChat) host.appendChild(creerEl('div', 'coach-thinking', 'Le coach prépare sa réponse…'));
        host.scrollTop = host.scrollHeight;
    }
    function rendreBrouillon(main) {
        var host = UI.$('#coachDraftHost', main);
        if (!host) return;
        host.textContent = '';
        if (!draft) {
            host.appendChild(creerEl('div', 'coach-empty coach-draft-empty', 'Aucun brouillon en attente. Le rapport ne sera ajouté au journal qu’après ta validation.'));
            return;
        }
        var card = creerEl('section', 'card coach-draft');
        card.appendChild(creerEl('div', 'coach-draft-title', '📝 Brouillon du ' + dateFr(draft.date) + ' · non enregistré'));
        card.appendChild(creerEl('div', 'coach-draft-help', 'Relis et corrige directement le texte ci-dessous, puis valide. Annuler ne crée aucune entrée de journal.'));
        var area = root.document.createElement('textarea');
        area.id = 'coachDraftText';
        area.className = 'coach-textarea coach-draft-edit';
        area.rows = 12;
        area.maxLength = 8000;
        area.value = draft.text;
        card.appendChild(area);
        var actions = creerEl('div', 'grille g2 coach-draft-actions');
        var approve = creerEl('button', 'btn btn-hero', '✔ Valider et enregistrer au journal');
        approve.type = 'button';
        approve.id = 'btnCoachApproveDraft';
        var cancel = creerEl('button', 'btn btn-flat', 'Annuler le brouillon');
        cancel.type = 'button';
        cancel.id = 'btnCoachCancelDraft';
        actions.appendChild(approve); actions.appendChild(cancel); card.appendChild(actions);
        host.appendChild(card);
        approve.onclick = async function () {
            var text = area.value.trim();
            if (!text) { UI.toast('Le rapport est vide'); return; }
            if (text.length > 8000) { UI.toast('Le rapport est limité à 8 000 caractères'); return; }
            approve.disabled = true; approve.textContent = 'Enregistrement…';
            try {
                await api('/api/coach/reports/approve', 'POST', { date: draft.date, report_text: text }, true);
                draft = null;
                await chargerRapports(main);
                rendreBrouillon(main);
                UI.toast('Rapport validé et ajouté au journal IA');
            } catch (e) {
                approve.disabled = false; approve.textContent = '✔ Valider et enregistrer au journal';
                UI.toast('Impossible d’enregistrer : ' + erreurTexte(e));
            }
        };
        cancel.onclick = function () {
            draft = null;
            rendreBrouillon(main);
            UI.toast('Brouillon annulé — aucun rapport enregistré');
        };
    }
    async function chargerRapports(main) {
        var host = UI.$('#coachReports', main);
        if (!host) return;
        try {
            var data = await api('/api/coach/reports?limit=20', 'GET', null, true);
            reports = Array.isArray(data.reports) ? data.reports : [];
            rendreRapports(main);
        } catch (e) {
            if (!reports.length) host.textContent = 'Journal IA indisponible pour le moment : ' + erreurTexte(e);
        }
    }
    function rendreRapports(main) {
        var host = UI.$('#coachReports', main);
        if (!host) return;
        host.textContent = '';
        if (!reports.length) {
            host.appendChild(creerEl('div', 'coach-empty', 'Aucun rapport validé. Les brouillons annulés ou non validés ne sont pas conservés ici.'));
            return;
        }
        reports.forEach(function (r) {
            var card = creerEl('details', 'coach-report');
            var summary = root.document.createElement('summary');
            summary.appendChild(creerEl('span', 'coach-report-date', dateFr(r.report_date)));
            summary.appendChild(creerEl('span', 'coach-report-hint', 'Ouvrir le rapport'));
            card.appendChild(summary);
            var body = creerEl('div', 'coach-report-body', String(r.report_text || ''));
            card.appendChild(body);
            var remove = creerEl('button', 'btn btn-flat coach-delete-report', 'Supprimer ce rapport');
            remove.type = 'button';
            remove.setAttribute('data-report-id', String(r.id || ''));
            card.appendChild(remove);
            host.appendChild(card);
        });
        host.querySelectorAll('.coach-delete-report').forEach(function (button) {
            button.onclick = async function () {
                var id = button.getAttribute('data-report-id');
                if (!id || !root.confirm('Supprimer ce rapport IA du journal ?')) return;
                button.disabled = true;
                try {
                    await api('/api/coach/reports/' + encodeURIComponent(id), 'DELETE', null, true);
                    reports = reports.filter(function (x) { return String(x.id) !== id; });
                    rendreRapports(main);
                    UI.toast('Rapport supprimé');
                } catch (e) { button.disabled = false; UI.toast('Suppression impossible : ' + erreurTexte(e)); }
            };
        });
    }
    async function chargerMemoire(main) {
        try {
            var data = await api('/api/coach/memory', 'GET', null, true);
            memoryLoaded = !!(data.memory && data.memory.loaded);
            memoryText = data.memory && data.memory.manifest || '';
            memoryUpdated = data.memory && data.memory.updated_at || null;
            loadedBase = memoryText;
            var area = UI.$('#coachManifest', main);
            if (area && (!area.value.trim() || area.value === loadedBase)) area.value = memoryText;
            setMemoryStatus(memoryLoaded
                ? 'Base importée · dernière mise à jour ' + (memoryUpdated ? dateFr(String(memoryUpdated).slice(0, 10)) : '—')
                : 'Aucune base importée. Colle le manifeste validé ci-dessous.');
        } catch (e) {
            setMemoryStatus('Base non chargée : ' + erreurTexte(e));
        }
    }
    async function chargerHistorique(main) {
        try {
            var data = await api('/api/coach/history?limit=60', 'GET', null, true);
            messages = Array.isArray(data.messages) ? data.messages : [];
            sauverCache();
            rendreMessages(main);
        } catch (e) {
            rendreMessages(main);
        }
    }
    async function chargerTout(main) {
        synchroniserCacheUtilisateur();
        var url;
        try { url = baseWorker(); } catch (e) {
            setStatus('URL du Worker à configurer', 'warn');
            rendreMessages(main);
            return;
        }
        if (url !== loadedBaseWorker) loadedBaseWorker = url;
        try {
            await api('/api/health', 'GET', null, false);
        } catch (e) {
            setStatus('Worker injoignable : ' + erreurTexte(e), 'warn');
            rendreMessages(main);
            return;
        }
        try {
            var session = await Net.sessionValide(false);
            if (!session || !session.access_token) {
                setStatus('Connecte-toi à Supabase dans Réglages', 'warn');
                setMemoryStatus('Connexion Supabase nécessaire pour charger ta base et ton historique.');
                rendreMessages(main);
                return;
            }
        } catch (e2) {
            setStatus('Session Supabase à renouveler dans Réglages', 'warn');
            rendreMessages(main);
            return;
        }
        setStatus('Worker en ligne · accès protégé par Supabase', 'ok');
        await Promise.all([chargerHistorique(main), chargerRapports(main), chargerMemoire(main)]);
    }
    var loadedBaseWorker = '';
    function vue(ctx) {
        var date = isoAujourdhui();
        var configured = !!String(Store.getReglages().coachApiUrl || '').trim();
        return '<div class="coach-page">' +
            '<div class="card teal coach-hero">' +
                '<div class="coach-hero-top"><div><div class="lbl">Équilibre · accompagnement personnel</div><div class="coach-hero-title">Coach IA</div></div>' +
                    '<span class="badge ' + (configured ? 'info' : 'warn') + '" id="coachStatus">' + (configured ? 'Connexion…' : 'Configuration requise') + '</span></div>' +
                '<div class="st">Bien-être général, habitudes, alimentation et entraînement. Ce coach ne remplace pas un professionnel de santé.</div>' +
                '<button class="btn btn-flat coach-config-button" id="btnCoachSettings" type="button">⚙ Configurer le Worker / le compte</button>' +
            '</div>' +
            '<section class="card coach-analysis">' +
                '<div class="coach-section-title">Analyse d’une journée</div>' +
                '<div class="st">Les chiffres disponibles sont rassemblés en lecture seule. Le résultat reste un brouillon jusqu’à ta validation.</div>' +
                '<div class="grille g2 coach-analysis-inputs">' +
                    '<div class="champ"><label for="coachAnalysisDate">Date à analyser</label><input type="date" id="coachAnalysisDate" value="' + date + '" max="' + date + '" /></div>' +
                    '<div class="champ"><label for="coachFatigue">Fatigue ressentie (facultatif)</label><input type="number" id="coachFatigue" min="1" max="10" step="1" placeholder="1 faible · 10 forte" /></div>' +
                '</div>' +
                '<div class="champ"><label for="coachExtraNotes">Précision ou correction pour cette analyse (facultatif)</label><textarea id="coachExtraNotes" class="coach-textarea" rows="2" maxlength="1500" placeholder="Ex. repas incomplet dans le journal, gêne ressentie, contexte de la journée…"></textarea></div>' +
                '<button class="btn btn-hero" id="btnCoachAnalyze" type="button"' + (busyAnalysis ? ' disabled' : '') + '>' + (busyAnalysis ? 'Analyse en cours…' : '✦ Analyser et créer un brouillon') + '</button>' +
                '<div id="coachDraftHost" class="coach-draft-host"></div>' +
            '</section>' +
            '<section class="card coach-chat-card">' +
                '<div class="coach-chat-head"><div><div class="coach-section-title">Conversation persistante</div><div class="st">Questions libres · recherche web automatique si utile · sources cliquables</div></div>' +
                    '<button class="btn btn-flat coach-small-button" id="btnCoachClearChat" type="button">Effacer l’historique</button></div>' +
                '<div id="coachMessages" class="coach-messages" role="log" aria-live="polite"></div>' +
                '<form id="coachChatForm" class="coach-chat-form">' +
                    '<textarea id="coachChatInput" class="coach-textarea" rows="3" maxlength="2000" placeholder="Écris au coach…" aria-label="Message au coach"></textarea>' +
                    '<input type="file" id="coachChatFiles" multiple hidden accept="image/*,application/pdf,text/plain,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" />' +
                    '<div id="coachAttachments" class="coach-attachments"></div>' +
                    '<div style="display:flex;gap:8px;align-items:center;">' +
                        '<button class="btn btn-flat" id="btnCoachAttach" type="button"' + (busyChat ? ' disabled' : '') + ' title="Joindre des photos, captures d’écran ou documents">📎 Fichiers</button>' +
                        '<button class="btn btn-hero" id="btnCoachSend" type="submit"' + (busyChat ? ' disabled' : '') + ' style="flex:1;">Envoyer</button>' +
                    '</div>' +
                '</form>' +
            '</section>' +
            '<details class="card coach-memory-card" id="coachMemoryDetails">' +
                '<summary><span class="coach-section-title">Base de référence du coach</span><span class="st" id="coachMemoryStatus">Chargement de la base…</span></summary>' +
                '<p class="st">Colle ici le manifeste que tu as validé. Il sera stocké dans ton espace Coach IA Cloudflare, séparé par ton compte Supabase. Tu peux le corriger ou le supprimer.</p>' +
                '<textarea id="coachManifest" class="coach-textarea coach-manifest" rows="10" maxlength="40000" placeholder="Colle le contenu du fichier Manifeste-coach-IA-v2.md"></textarea>' +
                '<div class="grille g2 coach-memory-actions">' +
                    '<button class="btn btn-flat" id="btnCoachSaveMemory" type="button"' + (busyMemory ? ' disabled' : '') + '>Enregistrer / mettre à jour</button>' +
                    '<button class="btn btn-flat" id="btnCoachDeleteMemory" type="button">Supprimer la base</button>' +
                '</div>' +
            '</details>' +
            '<section class="card coach-journal-card">' +
                '<div class="coach-chat-head"><div><div class="coach-section-title">Journal IA</div><div class="st">Uniquement les rapports que tu as validés</div></div>' +
                    '<button class="btn btn-flat coach-small-button" id="btnCoachRefreshReports" type="button">Actualiser</button></div>' +
                '<div id="coachReports" class="coach-reports"><div class="coach-empty">Chargement des rapports validés…</div></div>' +
            '</section>' +
            '<div class="coach-footer">Données brutes non modifiées · conversation et base conservées dans le service Coach IA · usage gratuit plafonné.</div>' +
        '</div>';
    }
    function attacher(main, ctx, rafraichir) {
        if (!main) return;
        synchroniserCacheUtilisateur();
        rendreMessages(main);
        rendreBrouillon(main);
        rendreRapports(main);
        var settings = UI.$('#btnCoachSettings', main);
        if (settings) settings.onclick = boutonOuvrirReglages;
        var attach = UI.$('#btnCoachAttach', main);
        var fichier = UI.$('#coachChatFiles', main);
        if (attach && fichier) {
            attach.onclick = function () { fichier.click(); };
            fichier.onchange = function () {
                ajouterPieces(main, fichier.files);
                fichier.value = '';
            };
            rendrePieces(main);
        }
        var form = UI.$('#coachChatForm', main);
        if (form) form.onsubmit = function (event) {
            event.preventDefault();
            envoyerMessage(main, ctx);
        };
        var analyze = UI.$('#btnCoachAnalyze', main);
        if (analyze) analyze.onclick = function () { analyserJournee(main, ctx); };
        var saveMemory = UI.$('#btnCoachSaveMemory', main);
        if (saveMemory) saveMemory.onclick = function () { enregistrerMemoire(main); };
        var deleteMemory = UI.$('#btnCoachDeleteMemory', main);
        if (deleteMemory) deleteMemory.onclick = function () { supprimerMemoire(main); };
        var clearChat = UI.$('#btnCoachClearChat', main);
        if (clearChat) clearChat.onclick = function () { effacerHistorique(main); };
        var refresh = UI.$('#btnCoachRefreshReports', main);
        if (refresh) refresh.onclick = function () { chargerRapports(main); chargerHistorique(main); };
        chargerTout(main);
    }
    // Pièces jointes du chat (photos, captures d'écran, documents).
    // 1.4 : elles sont envoyées au Worker Coach IA dans le champ `attachments`.
    var piecesJointes = [];
    var LIMITE_FICHIERS = 4;
    var LIMITE_OCTETS = 4 * 1024 * 1024; // 4 Mo par fichier

    function lireEnBase64(fichier) {
        return new Promise(function (resolve, reject) {
            var fr = new FileReader();
            fr.onerror = function () { reject(new Error('Lecture impossible : ' + fichier.name)); };
            fr.onload = function () {
                var chaine = String(fr.result || '');
                var i = chaine.indexOf(',');
                resolve(i >= 0 ? chaine.slice(i + 1) : chaine);
            };
            fr.readAsDataURL(fichier);
        });
    }

    async function ajouterPieces(main, fichiers) {
        var liste = Array.prototype.slice.call(fichiers || []);
        for (var i = 0; i < liste.length; i++) {
            var f = liste[i];
            if (piecesJointes.length >= LIMITE_FICHIERS) {
                UI.toast('Maximum ' + LIMITE_FICHIERS + ' fichiers par message');
                break;
            }
            if (f.size > LIMITE_OCTETS) {
                UI.toast(f.name + ' dépasse ' + Math.round(LIMITE_OCTETS / 1024 / 1024) + ' Mo');
                continue;
            }
            if (piecesJointes.some(function (p) { return p.name === f.name && p.size === f.size; })) continue;
            try {
                piecesJointes.push({
                    name: f.name, type: f.type || 'application/octet-stream',
                    size: f.size, data: await lireEnBase64(f)
                });
            } catch (e) { UI.toast(erreurTexte(e)); }
        }
        rendrePieces(main);
    }

    function rendrePieces(main) {
        var box = UI.$('#coachAttachments', main);
        if (!box) return;
        if (!piecesJointes.length) { box.innerHTML = ''; return; }
        box.innerHTML = piecesJointes.map(function (p, i) {
            return '<span class="badge" style="margin:4px 6px 0 0;display:inline-block;">📎 ' + h(p.name) +
                ' · ' + Math.max(1, Math.round(p.size / 1024)) + ' ko ' +
                '<a href="#" data-detach="' + i + '" style="margin-left:6px;">✕</a></span>';
        }).join('');
        UI.$$('[data-detach]', box).forEach(function (lien) {
            lien.onclick = function (ev) {
                ev.preventDefault();
                piecesJointes.splice(Number(lien.getAttribute('data-detach')), 1);
                rendrePieces(main);
            };
        });
    }

    async function envoyerMessage(main, ctx) {
        if (busyChat) return;
        var input = UI.$('#coachChatInput', main);
        var message = input ? input.value.trim() : '';
        if (!message) { UI.toast('Écris un message avant d’envoyer'); return; }
        if (message.length > 2000) { UI.toast('Limite de 2 000 caractères par message'); return; }
        var jointes = piecesJointes.slice();
        var pending = {
            id: 'pending-' + Date.now(), role: 'user', content: message, sources: [], pending: true,
            attachments: jointes.map(function (p) { return { name: p.name, type: p.type, size: p.size }; })
        };
        messages.push(pending);
        piecesJointes = [];
        rendrePieces(main);
        busyChat = true;
        if (input) { input.value = ''; input.disabled = true; }
        var send = UI.$('#btnCoachSend', main);
        if (send) { send.disabled = true; send.textContent = 'Envoi…'; }
        rendreMessages(main);
        try {
            var result = await api('/api/coach/chat', 'POST', {
                message: message,
                appContext: construireContexteChat(ctx),
                attachments: jointes
            }, true);
            messages = messages.filter(function (x) { return !x.pending; });
            if (result.message) messages.push(result.message);
            if (!result.message && result.answer) messages.push({ role: 'assistant', content: result.answer, sources: result.sources || [] });
            // Recharger pour obtenir aussi la ligne utilisateur persistée côté D1.
            try {
                var history = await api('/api/coach/history?limit=60', 'GET', null, true);
                messages = Array.isArray(history.messages) ? history.messages : messages;
            } catch (e2) { }
            sauverCache();
            if (result.search && result.search.status === 'quota_reached') UI.toast('Réponse reçue · quota gratuit de recherche atteint');
        } catch (e) {
            messages = messages.filter(function (x) { return !x.pending; });
            UI.toast('Message non envoyé : ' + erreurTexte(e));
            if (input) input.value = message;
        } finally {
            busyChat = false;
            if (input) input.disabled = false;
            if (send) { send.disabled = false; send.textContent = 'Envoyer'; }
            rendreMessages(main);
            if (input) input.focus();
        }
    }
    async function analyserJournee(main, ctx) {
        if (busyAnalysis) return;
        var dateInput = UI.$('#coachAnalysisDate', main);
        var date = dateInput ? dateInput.value : isoAujourdhui();
        var fatigueInput = UI.$('#coachFatigue', main);
        var fatigue = fatigueInput && fatigueInput.value !== '' ? Number(fatigueInput.value) : null;
        if (!date || date > isoAujourdhui()) { UI.toast('Choisis une date passée ou aujourd’hui'); return; }
        if (fatigue != null && (fatigue < 1 || fatigue > 10)) { UI.toast('La fatigue doit être entre 1 et 10'); return; }
        var notes = UI.$('#coachExtraNotes', main);
        busyAnalysis = true;
        var button = UI.$('#btnCoachAnalyze', main);
        if (button) { button.disabled = true; button.textContent = 'Analyse en cours…'; }
        try {
            var dayData = construireJournee(ctx, date, fatigue, notes ? notes.value : '');
            var response = await api('/api/coach/analyze', 'POST', {
                date: date, dayData: dayData, additionalNotes: notes ? notes.value.trim() : ''
            }, true);
            draft = { id: response.draft_id, date: response.date || date, text: response.draft || '' };
            rendreBrouillon(main);
            UI.toast('Brouillon prêt : relis-le avant de le valider');
        } catch (e) {
            UI.toast('Analyse impossible : ' + erreurTexte(e));
        } finally {
            busyAnalysis = false;
            if (button) { button.disabled = false; button.textContent = '✦ Analyser et créer un brouillon'; }
        }
    }
    async function enregistrerMemoire(main) {
        if (busyMemory) return;
        var area = UI.$('#coachManifest', main);
        var text = area ? area.value.trim() : '';
        if (text.length < 20) { UI.toast('Colle le texte du manifeste validé avant de l’enregistrer'); return; }
        if (text.length > 40000) { UI.toast('La base est trop longue (limite de 40 000 caractères)'); return; }
        if (!root.confirm('Enregistrer cette base de référence dans ton espace Coach IA ? Elle sera associée à ton compte Supabase.')) return;
        busyMemory = true;
        var button = UI.$('#btnCoachSaveMemory', main);
        if (button) { button.disabled = true; button.textContent = 'Enregistrement…'; }
        try {
            var result = await api('/api/coach/memory', 'POST', { manifest: text }, true);
            memoryText = text; memoryLoaded = true; memoryUpdated = result.updated_at || null; loadedBase = text;
            setMemoryStatus('Base importée · mise à jour ' + dateFr(isoAujourdhui()));
            UI.toast('Base de référence enregistrée');
        } catch (e) { UI.toast('Enregistrement impossible : ' + erreurTexte(e)); }
        finally {
            busyMemory = false;
            if (button) { button.disabled = false; button.textContent = 'Enregistrer / mettre à jour'; }
        }
    }
    async function supprimerMemoire(main) {
        if (!memoryLoaded) { UI.toast('Aucune base enregistrée'); return; }
        if (!root.confirm('Supprimer définitivement la base de référence du Coach IA ?')) return;
        try {
            await api('/api/coach/memory', 'DELETE', null, true);
            memoryText = ''; memoryLoaded = false; memoryUpdated = null; loadedBase = '';
            var area = UI.$('#coachManifest', main); if (area) area.value = '';
            setMemoryStatus('Aucune base importée.');
            UI.toast('Base supprimée');
        } catch (e) { UI.toast('Suppression impossible : ' + erreurTexte(e)); }
    }
    async function effacerHistorique(main) {
        if (!messages.length) { UI.toast('Aucun historique chargé'); return; }
        if (!root.confirm('Effacer les messages de cette conversation enregistrés dans le Coach IA ? Les rapports validés restent dans le journal.')) return;
        try {
            await api('/api/coach/history', 'DELETE', null, true);
            messages = []; sauverCache(); rendreMessages(main);
            UI.toast('Historique du chat effacé');
        } catch (e) { UI.toast('Effacement impossible : ' + erreurTexte(e)); }
    }

    EQ.coach = {
        vue: vue,
        attacher: attacher,
        construireContexteChat: construireContexteChat,
        construireJournee: construireJournee
    };
})(typeof window !== 'undefined' ? window : this);
