/* Tests ciblés de la coque mobile, sans navigateur ni dépendance externe.
 * Exécuter avec : node test_mobile.js
 *
 * Cette suite a été réalignée sur la version 1.3.10 restaurée depuis l'APK
 * téléversé dans telechargements/. L'ordre de chargement reprend celui
 * d'index.html. app.js est volontairement exclu : il démarre l'interface et
 * exige un DOM.
 *
 * Trois assertions de l'ancienne suite ont été retirées parce que la fonction
 * qu'elles couvraient n'existe pas en 1.3.10 :
 *   - store.anciennesDonneesAverifier() et store.masquerAvertissementDonneesPreexistantes()
 *   - la clé localStorage eq.revisionDonnees.v2
 *   - reglages.profileConfigured et le bandeau « Repères à vérifier — non personnalisés »
 * Ces garde-fous avaient été ajoutés par le fork 1.0.12/1.0.13 ; voir README,
 * section « Garde-fous non repris ».
 */
'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const JS_DIR = path.join(__dirname, 'app/src/main/assets/www/js');
// Ordre réel des <script> dans index.html, app.js exclu.
const SOURCES = ['util.js', 'models.js', 'store.js', 'net.js', 'menu.js',
    'ui.js', 'menu_views.js', 'views.js', 'coach.js'];

function creerAppli(stockInitial, options) {
    const opt = options || {};
    const donnees = new Map(Object.entries(stockInitial || {}));
    const localStorage = {
        getItem(cle) { return donnees.has(cle) ? donnees.get(cle) : null; },
        setItem(cle, valeur) { donnees.set(cle, String(valeur)); },
        removeItem(cle) { donnees.delete(cle); }
    };
    const listeners = {};
    const contexte = {
        localStorage, console, Date, Intl, Math, JSON, Array, Object, String, Number, isFinite,
        setTimeout: () => 0, clearTimeout: () => {}, setInterval: () => 0, clearInterval: () => {},
        navigator: opt.navigator || {},
        Native: opt.Native || null,
        addEventListener(type, fn) { (listeners[type] = listeners[type] || []).push(fn); },
        removeEventListener(type, fn) { listeners[type] = (listeners[type] || []).filter((f) => f !== fn); }
    };
    contexte.window = contexte;
    vm.createContext(contexte);
    for (const fichier of SOURCES) {
        vm.runInContext(fs.readFileSync(path.join(JS_DIR, fichier), 'utf8'), contexte, { filename: fichier });
    }
    return {
        EQ: contexte.EQ, localStorage, donnees, contexte,
        declencher: (type) => (listeners[type] || []).slice().forEach((f) => f())
    };
}

function dateIso(decalageJours) {
    const d = new Date();
    d.setHours(12, 0, 0, 0);
    d.setDate(d.getDate() + decalageJours);
    return d.toISOString().slice(0, 10);
}

function testPremierLancementVide() {
    const { EQ } = creerAppli();
    assert.deepEqual(Array.from(EQ.store.getLogs()), []);
    assert.deepEqual(Array.from(EQ.store.getMensurations()), []);
    assert.deepEqual(Array.from(EQ.store.getSeances()), []);
    assert.deepEqual(Array.from(EQ.store.getCourses()), []);
    // Valeurs par défaut lues dans DEFAUTS_REGLAGES (store.js).
    const r = EQ.store.getReglages();
    assert.equal(r.coachApiUrl, '', 'l’URL du Worker Coach IA ne doit pas être préremplie');
    assert.equal(r.supabaseUrl, '', 'l’URL Supabase ne doit pas être préremplie');
    assert.equal(r.supabaseKey, '', 'la clé Supabase ne doit pas être préremplie');
    assert.equal(r.urlSuivi, 'https://suivi-recomposition.streamlit.app');
    // Le profil personnel démarre vide, sans identifiant.
    assert.equal(EQ.store.getProfil().displayName, '');
}

function testConservationDonneesLocalesApresMonteeDeVersion() {
    // Les clés de stockage sont inchangées entre le fork 1.0.13 et la 1.3.10 :
    // une installation existante doit retrouver ses données telles quelles.
    const logs = [{ date: '2026-01-01', poids: 80, proteinesG: 47 }];
    const courses = [{ id: 'old', produit: 'Article', pris: false }];
    const { EQ } = creerAppli({
        'eq.logs.v1': JSON.stringify(logs),
        'eq.courses.v1': JSON.stringify(courses),
        'eq.mensurations.v1': JSON.stringify([{ date: '2026-01-01', tailleCm: 84 }]),
        'eq.seances.v1': JSON.stringify([{ date: '2026-01-01', type: 'A' }])
    });
    assert.deepEqual(JSON.parse(JSON.stringify(EQ.store.getLogs())), logs);
    assert.equal(EQ.store.getCourses().length, 1);
    assert.equal(EQ.store.getMensurations().length, 1);
    assert.equal(EQ.store.getSeances().length, 1);
}

function testGraphiqueProteinesVideEtUneValeur() {
    const { EQ } = creerAppli();
    // Comportement réel de ui.js:194 en 1.3.10 : sans donnée, le graphique
    // trace seulement la ligne de cible. Le texte « Aucune saisie de protéines »
    // était un ajout du fork réduit, il n'existe pas ici.
    const vide = EQ.ui.svgBarresProteines([], 130);
    assert.match(vide, /<svg/);
    assert.match(vide, /Cible 130 g/);
    assert.doesNotMatch(vide, /<rect/, 'aucune barre ne doit être tracée sans donnée');
    assert.doesNotMatch(vide, /NaN|Infinity/);

    const uneBarre = EQ.ui.svgBarresProteines([{ date: '2026-01-01', proteinesG: 42 }], 130);
    assert.match(uneBarre, /<rect/);
    assert.match(uneBarre, />42</);
    assert.doesNotMatch(uneBarre, /NaN|Infinity/);

    // Une protéine absente compte pour 0 (barre à la hauteur minimale), pas pour une erreur.
    const nulle = EQ.ui.svgBarresProteines([{ date: '2026-01-01', proteinesG: null }], 130);
    assert.match(nulle, /<rect/);
    assert.doesNotMatch(nulle, /NaN|Infinity/);

    // cibleG falsy retombe sur 130 (ui.js:195), il n'y a pas d'état « à vérifier ».
    assert.match(EQ.ui.svgBarresProteines([{ date: '2026-01-01', proteinesG: 42 }], 0), /Cible 130 g/);
}

function testReglagesExposentCoachIaEtSupabase() {
    const { EQ } = creerAppli();
    let feuille;
    EQ.ui.feuille = (config) => { feuille = config; };
    EQ.views.feuilleReglages({ reglages: EQ.store.getReglages() }, () => {});
    // Le champ du Worker Coach IA existe et démarre vide (coach.js:55 refuse
    // tout appel tant qu'il n'est pas renseigné).
    assert.match(feuille.html, /id="regCoachUrl"[^>]*value=""/);
    assert.match(feuille.html, /Worker Coach IA/);
    assert.match(feuille.html, /id="regSupaUrl"/);
    assert.match(feuille.html, /id="regSupaKey"/);
}

function testContexteEnvoyeAuCoachIa() {
    // Documente précisément ce qui quitte l'appareil vers /api/coach/chat.
    const { EQ } = creerAppli();
    const noteLongue = 'x'.repeat(200);
    const ctx = {
        reglages: EQ.store.getReglages(),
        logs: [{ date: dateIso(0), poids: 78, pas: 8000, sommeilH: 7, energy: 6 }],
        nutrition: [
            { date: dateIso(0), item: 'Repas midi', protein_g: 40, carbs_g: 60, fat_g: 15 },
            { date: dateIso(-10), item: 'Hors fenêtre', protein_g: 99, carbs_g: 99, fat_g: 99 }
        ],
        // Six séances : seules les quatre dernières doivent partir.
        seances: [-5, -4, -3, -2, -1, 0].map((j, i) => ({
            date: dateIso(j), type: 'A', dureeMin: 40 + i, ressenti: 'ok', notes: noteLongue
        })),
        mensurations: [{ date: dateIso(-30), tailleCm: 84 }, { date: dateIso(-1), tailleCm: 83 }]
    };
    const c = EQ.coach.construireContexteChat(ctx);

    assert.equal(c.nutrition_7j.jours_avec_saisie, 1, 'la saisie de plus de 7 jours doit être exclue');
    assert.equal(c.nutrition_7j.totaux_saisis.proteines_g, 40);
    assert.equal(c.seances_recentes.length, 4, 'seules les 4 dernières séances partent');
    assert.equal(c.seances_recentes[3].date, dateIso(0));
    assert.equal(c.seances_recentes[0].notes.length, 160, 'les notes doivent être tronquées à 160 caractères');
    assert.equal(c.derniere_mensuration.tailleCm, 83, 'seule la dernière mensuration part');
    assert.equal(c.objectifs.proteines_g, 130, 'les objectifs par défaut partent tels quels');
    assert.match(c.nutrition_7j.avertissement, /approximatifs/);
}

function testSurfaceDesModulesRestaures() {
    // Vérifie que les trois modules absents du fork réduit sont bien chargés
    // et initialisés dans l'ordre d'index.html.
    const { EQ } = creerAppli();
    for (const m of ['store', 'ui', 'views', 'menu', 'menuViews', 'coach']) {
        assert.ok(EQ[m], `module manquant : EQ.${m}`);
    }
    for (const f of ['vue', 'attacher', 'construireContexteChat', 'construireJournee']) {
        assert.equal(typeof EQ.coach[f], 'function', `EQ.coach.${f} absent`);
    }
    assert.equal(typeof EQ.menu.planned, 'function');
    assert.equal(typeof EQ.net.synchroniserSupabase, 'function');
    // La synchronisation n'est plus neutralisée d'office comme dans le fork
    // réduit : net.js ne doit plus renvoyer l'état « desactivee » en dur.
    const sourceNet = fs.readFileSync(path.join(JS_DIR, 'net.js'), 'utf8');
    assert.doesNotMatch(sourceNet, /etat:\s*'desactivee'/,
        'net.js renvoie encore l’état « desactivee » en dur');
    assert.match(sourceNet, /access_token|Authorization|jwt/i,
        'net.js doit porter un transport authentifié');
}

function testEstEnLigneSuitLeReseau() {
    // Sans aucune information contraire, l'app se considère en ligne.
    assert.equal(creerAppli().EQ.store.estEnLigne(), true);
    // navigator.onLine === false (navigateur) …
    assert.equal(creerAppli({}, { navigator: { onLine: false } }).EQ.store.estEnLigne(), false);
    // … et Native.isOnline() (WebView Android) doivent tous deux être entendus.
    assert.equal(creerAppli({}, { Native: { isOnline: () => false } }).EQ.store.estEnLigne(), false);
    assert.equal(creerAppli({}, { Native: { isOnline: () => true } }).EQ.store.estEnLigne(), true);
}

function testRetourEnLigneDeclencheLeDeversement() {
    const navigator = { onLine: false };
    const { EQ, declencher } = creerAppli({}, { navigator });
    let appels = 0;
    const arreter = EQ.store.surveillerConnexion(() => { appels += 1; }, 60000);

    // Toujours hors ligne : rien ne doit partir.
    declencher('online');
    assert.equal(appels, 0, 'aucun déversement tant que le réseau est absent');

    // Retour du réseau : le tampon doit être déversé une fois.
    navigator.onLine = true;
    declencher('online');
    assert.equal(appels, 1, 'le retour en ligne doit déclencher la synchronisation');

    // Un second événement alors qu'on est déjà en ligne ne relance rien.
    declencher('online');
    assert.equal(appels, 1, 'pas de synchronisation répétée sans nouvelle coupure');

    // Nouvelle coupure puis nouveau retour : un second déversement.
    navigator.onLine = false;
    declencher('offline');
    navigator.onLine = true;
    declencher('online');
    assert.equal(appels, 2);

    arreter();
    navigator.onLine = false;
    declencher('offline');
    navigator.onLine = true;
    declencher('online');
    assert.equal(appels, 2, 'arreter() doit couper la surveillance');
}

function testMigrationLocaleVersSupabase() {
    const session = { access_token: 'tk', refresh_token: 'rk', user: { id: 'u1' } };
    const { EQ, donnees } = creerAppli({
        'eq.supabase.session.v1': JSON.stringify(session),
        'eq.logs.v1': JSON.stringify([{ date: '2026-01-01', poids: 80 }, { date: '2026-01-02', poids: 79.6 }]),
        'eq.mensurations.v1': JSON.stringify([{ date: '2026-01-01', tailleCm: 84 }]),
        'eq.seances.v1': JSON.stringify([{ date: '2026-01-01', type: 'A' }]),
        'eq.series.v1': JSON.stringify([{ date: '2026-01-01', type: 'A', exercise: 'squat', set_no: 1 }]),
        'eq.nutrition.v1': JSON.stringify([{ local_id: 'n1', item: 'Repas', protein_g: 40 }]),
        'eq.profil.v1': JSON.stringify({ displayName: 'Flavien', tailleCm: 185 }),
        'eq.courses.v1': JSON.stringify([{ id: 'c1', produit: 'Riz', pris: true },
            { id: 'c2', produit: 'Huile', pris: false }])
    });

    assert.equal(EQ.store.migrationFaite(), false);
    const migres = EQ.store.migrerDonneesLocalesVersFile();
    EQ.store.marquerMigrationFaite();

    // 2 pesées + 1 mensuration + 1 séance + 1 série + 1 nutrition + 1 profil
    // + 1 article coché (l'article non coché ne part pas).
    assert.equal(migres, 8);
    assert.equal(EQ.store.syncCount(), 8);

    const tables = EQ.store.getSyncQueue().map((x) => x.table).sort();
    assert.deepEqual(tables, ['daily_logs', 'daily_logs', 'measurements', 'profiles',
        'protein_entries', 'shopping_state', 'workout_sets', 'workouts']);

    // Tant que l'envoi vers Supabase n'est pas confirmé, les caches restent en
    // place : l'interface continue d'afficher les données héritées.
    assert.equal(EQ.store.getLogs().length, 2);
    assert.equal(EQ.store.getMensurations().length, 1);
    assert.equal(EQ.store.getCourses().length, 2);

    // Une fois l'envoi confirmé, la purge vide les caches.
    assert.equal(EQ.store.cachesPurges(), false);
    EQ.store.purgerCachesLocaux();
    EQ.store.marquerCachesPurges();
    assert.deepEqual(EQ.store.getLogs(), []);
    assert.deepEqual(EQ.store.getMensurations(), []);
    assert.deepEqual(EQ.store.getSeances(), []);
    assert.deepEqual(EQ.store.getCourses(), []);

    // La file, les réglages et la session survivent à la purge.
    assert.equal(EQ.store.syncCount(), 8, 'la purge ne doit pas vider la file');
    assert.deepEqual(EQ.store.getRemoteSession(), session);
    assert.equal(EQ.store.getReglages().coachApiUrl, '');

    assert.equal(EQ.store.migrationFaite(), true, 'la migration ne doit pas se rejouer');
    assert.equal(EQ.store.cachesPurges(), true, 'la purge ne doit pas se rejouer');
    // Second passage : il ne reste rien à pousser.
    assert.equal(EQ.store.migrerDonneesLocalesVersFile(), 0);
    assert.equal(EQ.store.syncCount(), 8);
}


// ---------------------------------------------------------------------------
// 1.4 — DOM minimal : juste assez pour que UI.feuille rende dans une racine
// inspectable, sans navigateur. Les éléments sont résolus par sélecteur depuis
// `document` comme depuis une racine, ce qui reproduit UI.$(sel, racine).
// ---------------------------------------------------------------------------
function creerDomStub() {
    const parSelecteur = new Map();
    function creerElement(selecteur) {
        const e = {
            selecteur: selecteur || '', style: {}, innerHTML: '', value: '',
            textContent: '', min: '', max: '', step: '', disabled: false,
            checked: false, files: [], onclick: null, oninput: null, onchange: null,
            classList: {
                add() { }, remove() { }, toggle() { }, contains() { return false; }
            },
            setAttribute() { }, appendChild() { },
            getAttribute(nom) { return e._attrs && nom in e._attrs ? e._attrs[nom] : null; }
        };
        e._attrs = {};
        e.querySelector = (s) => resoudre(s);
        // Les suggestions rendues sont relues depuis innerHTML pour pouvoir
        // simuler un clic sur l'une d'elles.
        e.querySelectorAll = (s) => {
            if (s !== '[data-sugg]') return [];
            // Les mêmes instances doivent être renvoyées à chaque appel : le
            // code testé y pose ses gestionnaires onclick.
            if (e._suggCache && e._suggCache.html === e.innerHTML) return e._suggCache.nodes;
            const trouves = [...String(e.innerHTML).matchAll(/data-sugg="(\d+)"/g)];
            const nodes = trouves.map((m) => {
                const b = creerElement('bouton-suggestion-' + m[1]);
                b._attrs['data-sugg'] = m[1];
                return b;
            });
            e._suggCache = { html: e.innerHTML, nodes };
            return nodes;
        };
        return e;
    }
    function resoudre(selecteur) {
        if (!parSelecteur.has(selecteur)) parSelecteur.set(selecteur, creerElement(selecteur));
        return parSelecteur.get(selecteur);
    }
    return {
        document: {
            querySelector: resoudre,
            querySelectorAll: () => [],
            createElement: () => creerElement(''),
            addEventListener() { }, removeEventListener() { }
        },
        resoudre, parSelecteur
    };
}

/** Amorcer les tables de menus partagées lues par Menu via Store.getMenuTable. */
function amorcerMenus(app, tables) {
    for (const [table, lignes] of Object.entries(tables)) {
        app.localStorage.setItem('eq.menu.' + table + '.v1', JSON.stringify(lignes));
    }
}

const MENUS_TEST = {
    ingredients: [
        { id: 'i1', name: 'Poulet', unit: 'g', poids_piece_g: 130, category: 'Boucherie & Poissonnerie',
          kcal_100g: 165, proteines_100g: 31, glucides_100g: 0, lipides_100g: 3.6 },
        { id: 'i2', name: 'Riz blanc', unit: 'g', poids_piece_g: 80, category: 'Épicerie Salée',
          kcal_100g: 350, proteines_100g: 7, glucides_100g: 78, lipides_100g: 1 }
    ],
    recipes: [
        { id: 'r1', name: 'Poulet au riz', base_servings: 2,
          instructions: 'Cuire le poulet, servir avec le riz.' }
    ],
    recipe_ingredients: [
        { id: 'l1', recipe_id: 'r1', ingredient_id: 'i1', quantity: 260, unit: 'g' },
        { id: 'l2', recipe_id: 'r1', ingredient_id: 'i2', quantity: 160, unit: 'g' }
    ]
};

function testEditeurAlimentSaisitLesValeursCuit() {
    // 1.4 — critère d'acceptation : les valeurs cuit manquantes doivent être
    // saisissables à la main, et signalées comme telles. Ciqual ne fournit pas
    // toutes les paires (les glucides du poisson, par exemple) : sans cette
    // saisie, l'état cuit resterait indisponible pour ces aliments.
    const app = creerAppli();
    amorcerMenus(app, {
        ingredients: [{
            id: 'c1', name: 'Carotte', unit: 'g', category: 'Légumes', est_a_moi: true,
            kcal_100g: 30, proteines_100g: 0.9, glucides_100g: 5.9, lipides_100g: 0.2
        }],
        recipes: [], recipe_ingredients: [], planned_meals: []
    });
    const dom = creerDomStub();
    app.contexte.document = dom.document;
    app.contexte.Native = { toast: () => { } };

    app.EQ.menuViews.ouvrirEditeurIngredient('c1');

    // L'éditeur doit proposer les deux jeux de valeurs et l'état par défaut.
    assert.ok(dom.resoudre('#menuIngKcalCuit'), 'un champ kcal cuit doit exister');
    assert.ok(dom.resoudre('#menuIngEtatDefaut'), 'un sélecteur d’état par défaut doit exister');

    // On ne saisit que l'état cuit : le cru reste vide et retombe sur la
    // colonne historique, jamais sur un calcul.
    //
    // Le stub ne parse pas le HTML rendu : un vrai WebView hydrate input.value
    // depuis l'attribut value="30" que l'éditeur écrit. Sans cette hydratation,
    // l'enregistrement écraserait les colonnes historiques avec null et le test
    // échouerait sur le stub plutôt que sur le comportement testé.
    dom.resoudre('#menuIngName').value = 'Carotte';
    dom.resoudre('#menuIngKcal').value = '30';
    dom.resoudre('#menuIngProtein').value = '0.9';
    dom.resoudre('#menuIngCarbs').value = '5.9';
    dom.resoudre('#menuIngFat').value = '0.2';
    dom.resoudre('#menuIngKcalCuit').value = '29.6';
    dom.resoudre('#menuIngProteinCuit').value = '0.72';
    dom.resoudre('#menuIngEtatDefaut').value = 'cuit';
    dom.resoudre('#btnMenuSaveIngredient').onclick();

    const sauve = app.EQ.menu.rows('ingredients').find((i) => String(i.id) === 'c1');
    assert.equal(sauve.kcal_100g_cuit, 29.6, 'la valeur cuite saisie doit être enregistrée');
    assert.equal(sauve.proteines_100g_cuit, 0.72, 'les protéines cuites aussi');
    assert.equal(sauve.etat_defaut, 'cuit', 'l’état par défaut doit suivre le choix');
    assert.equal(sauve.etats_manuels, true,
        'une valeur tapée à la main doit être signalée comme telle');

    // Le cru laissé vide retombe sur la colonne historique (30), pas sur 0.
    const m = app.EQ.menu.macrosPourEtat(sauve, 'cru');
    assert.equal(m.kcal, 30, 'le cru vide doit retomber sur la colonne historique');
    // Et l'état cuit porte bien la valeur saisie.
    assert.equal(app.EQ.menu.macrosPourEtat(sauve, 'cuit').kcal, 29.6,
        'l’état cuit doit porter la valeur saisie');
    // Avec un seul jeu renseigné, le sélecteur devient disponible.
    assert.equal(app.EQ.menu.aChoixEtat(sauve), true,
        'un seul jeu d’état suffit à rendre le sélecteur disponible');
}

function testEtatIngredientOmisSiLesColonnesManquent() {
    // 1.4 — l'éditeur d'aliment écrit désormais etat_defaut, etats_manuels et
    // les huit colonnes d'état à chaque enregistrement. Sans la migration,
    // PostgREST rejette la ligne entière : l'aliment resterait bloqué dans la
    // file de synchronisation. Le repli doit le renvoyer sans ces colonnes.
    const appels = [];

    const Native = {
        httpAsync(methode, url, entetes, corps, callbackId) {
            appels.push({ methode, url, corps: JSON.parse(corps || '{}') });
            const premier = appels.length === 1;
            setTimeout(() => {
                if (premier) {
                    app.EQ.net._fin(callbackId, {
                        ok: false, status: 400,
                        body: '{"message":"column ingredients.kcal_100g_cuit does not exist"}'
                    });
                } else {
                    app.EQ.net._fin(callbackId, { ok: true, status: 201, body: '[{"id":"ing-1"}]' });
                }
            }, 0);
        }
    };

    const app = creerAppli({
        'eq.reglages.v1': JSON.stringify({
            supabaseUrl: 'https://test.supabase.co', supabaseKey: 'cle-anon-publique'
        })
    }, { Native });

    const session = { access_token: 'jeton', user: { id: '1' } };
    return app.EQ.net._pushMenuItem(
        { table: 'menu:ingredients', key: 'ing-1', operation: 'insert',
          row: { id: 'ing-1', name: 'Carotte', unit: 'g', kcal_100g: 30, proteines_100g: 0.9,
                 etat_defaut: 'cru', etats_manuels: true,
                 kcal_100g_cru: 30.2, proteines_100g_cru: 0.93,
                 kcal_100g_cuit: 29.6, proteines_100g_cuit: 0.72 } },
        session
    ).then(() => {
        assert.equal(appels.length, 2, 'un second envoi doit avoir lieu après l’échec');
        assert.equal(appels[0].corps.kcal_100g_cuit, 29.6,
            'le premier envoi porte bien les valeurs d’état');
        ['etat_defaut', 'etats_manuels', 'kcal_100g_cru', 'kcal_100g_cuit',
         'proteines_100g_cru', 'proteines_100g_cuit'].forEach((c) => {
            assert.ok(!(c in appels[1].corps),
                'le repli doit retirer ' + c + ' plutôt que de bloquer la file');
        });
        assert.equal(appels[1].corps.kcal_100g, 30, 'la colonne historique est préservée');
        assert.equal(appels[1].corps.name, 'Carotte', 'le nom est préservé');
    });
}

function testFicheRecetteRappelleEtatCruCuit() {
    // 1.4 — « carottes cuites » dans un velouté et « carottes crues » en
    // salade ne donnent pas les mêmes macros. Rien d'autre que la fiche ne
    // distingue les deux à la lecture : l'état pesé doit y être rappelé.
    const app = creerAppli();
    amorcerMenus(app, {
        ingredients: [{
            id: 'c1', name: 'Carotte', unit: 'g', category: 'Légumes',
            kcal_100g: 30, proteines_100g: 0.9, glucides_100g: 5.9, lipides_100g: 0.2,
            etat_defaut: 'cru', etats_manuels: true,
            kcal_100g_cru: 30.2, proteines_100g_cru: 0.93, glucides_100g_cru: 5.9, lipides_100g_cru: 0.24,
            kcal_100g_cuit: 29.6, proteines_100g_cuit: 0.72, glucides_100g_cuit: 5.2, lipides_100g_cuit: 0.18
        }],
        recipes: [{ id: 'v1', name: 'Velouté de carotte', base_servings: 2, instructions: 'Cuire et mixer.' }],
        recipe_ingredients: [
            { id: 'x1', recipe_id: 'v1', ingredient_id: 'c1', quantity: 400, unit: 'g', etat: 'cuit' }
        ],
        planned_meals: []
    });
    const dom = creerDomStub();
    app.contexte.document = dom.document;
    app.contexte.Native = { toast: () => { } };

    app.EQ.menuViews.ouvrirFicheRecette('v1');

    const feuille = dom.resoudre('#feuille');
    assert.match(feuille.innerHTML, /Velouté de carotte/, 'la fiche doit s’ouvrir');
    assert.match(feuille.innerHTML, /cuit/, 'la fiche doit rappeler l’état pesé');
    // Une valeur d'état tapée à la main ne vaut pas une mesure Ciqual : elle
    // doit être signalée comme telle là où on la lit.
    assert.match(feuille.innerHTML, /saisi à la main/,
        'la fiche doit signaler les valeurs saisies à la main');

    // Les macros doivent suivre l'état de la ligne, pas la colonne historique :
    // 400 g × 29,6 kcal/100 g = 118,4 kcal, et non 400 × 30 / 100 = 120.
    const calc = app.EQ.menu.calculerRecette('v1');
    assert.equal(Math.round(calc.lignes[0].kcal), 118,
        'la ligne doit porter les valeurs cuites, pas la colonne historique');
}

function testFicheRecetteDepuisLePlanning() {
    // 1.4 : un plat planifié doit permettre de consulter sa recette. La fiche
    // est lue dans la base synchronisée, pas dans la liste statique d'exemples.
    const app = creerAppli();
    amorcerMenus(app, MENUS_TEST);
    const dom = creerDomStub();
    app.contexte.document = dom.document;

    app.contexte.Native = { toast: () => { } };

    app.EQ.menuViews.ouvrirFicheRecette('r1');

    const feuille = dom.resoudre('#feuille');
    assert.match(feuille.innerHTML, /Poulet au riz/,
        'la fiche doit porter le nom de la recette');
    assert.match(feuille.innerHTML, /Cuire le poulet/,
        'la fiche doit afficher la préparation');
    assert.match(feuille.innerHTML, /Poulet/, 'la fiche doit lister les ingrédients');
    assert.match(feuille.innerHTML, /kcal/, 'la fiche doit afficher les macros par part');

    // Une recette absente de la base ne doit rien afficher ni lever d'erreur.
    const avant = feuille.innerHTML;
    feuille.innerHTML = '';
    app.EQ.menuViews.ouvrirFicheRecette('inconnue');
    assert.equal(feuille.innerHTML, '', 'aucune fiche ne doit s’ouvrir sur un id inconnu');
    // UI.toast écrit dans l'élément #toast de la page.
    assert.match(dom.resoudre('#toast').textContent, /absente/,
        'un toast doit expliquer l’absence');
    assert.notEqual(avant, '', 'sanity : la première fiche avait bien rendu');
}

function testAutocompletionNutritionProposeRecettesEtAliments() {
    // 1.4 : taper le début d'un nom dans le journal nutrition doit proposer
    // les recettes et les aliments correspondants de la base.
    const app = creerAppli();
    amorcerMenus(app, MENUS_TEST);
    const dom = creerDomStub();
    app.contexte.document = dom.document;
    app.contexte.Native = { toast: () => { } };

    const ctx = { reglages: app.EQ.store.getReglages() };
    app.EQ.views.feuilleNutrition(ctx, null, () => { });

    const racine = dom.resoudre('#feuille');
    const saisie = dom.resoudre('#inNutriItem');
    const boites = dom.resoudre('#inNutriSuggestions');

    assert.equal(typeof saisie.oninput, 'function',
        'le champ de saisie doit être branché sur l’autocomplétion');

    // Moins de deux lettres : aucune suggestion.
    saisie.value = 'p';
    saisie.oninput();
    assert.equal(boites.innerHTML, '', 'rien à proposer avant 2 caractères');

    saisie.value = 'poul';
    saisie.oninput();
    assert.match(boites.innerHTML, /Poulet au riz/, 'la recette doit être proposée');
    assert.match(boites.innerHTML, /Poulet/, 'l’aliment doit être proposé');

    // Cliquer sur la première suggestion (la recette) remplit le formulaire.
    const boutons = boites.querySelectorAll('[data-sugg]');
    assert.ok(boutons.length >= 1, 'au moins une suggestion cliquable');
    boutons[0].onclick();
    assert.equal(saisie.value, 'Poulet au riz', 'le nom choisi doit remplir le champ');
    assert.equal(boites.innerHTML, '', 'la liste se referme après le choix');
    assert.notEqual(Number(dom.resoudre('#inNutriP').value), 0,
        'les protéines doivent être calculées depuis la recette');
}

function testBoutonRecettePresentSurLesPlatsACuisiner() {
    // 1.4 : c'est le point de départ de la demande — depuis les plats à
    // cuisiner, il n'y avait aucun moyen de consulter la recette. Le bouton
    // doit apparaître sur chaque plat dont la recette est dans la base.
    const app = creerAppli();
    const aujourd_hui = new Date();
    aujourd_hui.setHours(12, 0, 0, 0);
    const dateMenu = aujourd_hui.toISOString().slice(0, 10);
    amorcerMenus(app, Object.assign({}, MENUS_TEST, {
        planned_meals: [
            { id: 'p1', date_menu: dateMenu, meal_type: 'Midi', recipe_id: 'r1', servings: 2 },
            { id: 'p2', date_menu: dateMenu, meal_type: 'Soir', name: 'Restes', servings: 2 }
        ]
    }));
    const dom = creerDomStub();
    app.contexte.document = dom.document;
    app.contexte.Native = { toast: () => { } };

    const ctx = { reglages: app.EQ.store.getReglages() };
    app.EQ.menuViews.setTab('planning');
    app.EQ.menuViews.setPlanningStart(dateMenu);
    const html = app.EQ.menuViews.vueMenus(ctx);

    assert.match(html, /data-meal-recipe="r1"/,
        'le plat lié à une recette de la base doit exposer le bouton « Voir la recette »');
    assert.match(html, /title="Voir la recette"/, 'le bouton doit être libellé');

    // Un repas libre, sans recette en base, ne doit pas proposer de fiche.
    const boutons = [...html.matchAll(/data-meal-recipe="([^"]+)"/g)].map((m) => m[1]);
    assert.deepEqual(boutons, ['r1'],
        'seul le plat réellement lié à une recette doit porter le bouton');

    // Et le bouton doit bien ouvrir la fiche correspondante.
    app.EQ.menuViews.ouvrirFicheRecette(boutons[0]);
    assert.match(dom.resoudre('#feuille').innerHTML, /Poulet au riz/,
        'le bouton doit ouvrir la fiche de la bonne recette');
}

function testUniteChoisieDansLeJournalNutrition() {
    // 1.4 : la quantité saisie doit pouvoir être exprimée dans l'unité de son
    // choix (g, unité, cuillère à soupe…) et les macros doivent suivre.
    const app = creerAppli();
    // Œuf : 50 g par pièce, 13 g de protéines pour 100 g.
    amorcerMenus(app, {
        ingredients: [{
            id: 'i9', name: 'Œuf', unit: 'g', poids_piece_g: 50,
            category: 'Frais & Produits Laitiers',
            kcal_100g: 143, proteines_100g: 13, glucides_100g: 1.1, lipides_100g: 11
        }],
        recipes: [], recipe_ingredients: []
    });
    const dom = creerDomStub();
    app.contexte.document = dom.document;
    app.contexte.Native = { toast: () => { } };

    const ctx = { reglages: app.EQ.store.getReglages() };
    app.EQ.views.feuilleNutrition(ctx, null, () => { });

    const ing = app.EQ.menu.ingredients('')[0];
    const saisie = dom.resoudre('#inNutriItem');
    const unites = dom.resoudre('#inNutriUnit');
    const qte = dom.resoudre('#inNutriQty');
    const prot = dom.resoudre('#inNutriP');
    const info = dom.resoudre('#inNutriUnitInfo');

    // Choisir l'aliment via l'autocomplétion remplit aussi le sélecteur d'unité.
    saisie.value = 'œuf';
    saisie.oninput();
    const boites = dom.resoudre('#inNutriSuggestions');
    const boutons = boites.querySelectorAll('[data-sugg]');
    const choix = boutons.find((b) => b.getAttribute('data-sugg') != null);
    assert.ok(choix, 'l’aliment doit être proposé');
    choix.onclick();

    assert.equal(saisie.value, 'Œuf', 'l’aliment choisi remplit le champ');
    assert.match(unites.innerHTML, /c\. à soupe/, 'les unités culinaires doivent être proposées');
    assert.equal(unites.value, 'unité',
        'l’unité par défaut d’un aliment à 50 g la pièce est l’unité');
    // 100 g de référence ÷ 50 g par pièce = 2 unités.
    assert.equal(Number(qte.value), 2, 'la quantité par défaut vaut 100 g exprimée en unités');
    assert.equal(Number(prot.value), 13, '2 œufs = 100 g = 13 g de protéines');

    // Même aliment, exprimé en grammes : résultat identique.
    unites.value = 'g';
    unites.onchange();
    qte.value = '100';
    qte.oninput();
    assert.equal(Number(prot.value), 13, '100 g donnent les mêmes 13 g de protéines');

    // En cuillères à soupe (15 g chacune) : 2 × 15 g = 30 g.
    unites.value = 'c. à soupe';
    unites.onchange();
    qte.value = '2';
    qte.oninput();
    assert.equal(Number(prot.value), 3.9, '2 c. à soupe = 30 g = 3,9 g de protéines');
    assert.match(info.textContent, /30 g/, 'l’équivalence en grammes doit être affichée');

    // L'unité choisie est enregistrée avec l'entrée.
    dom.resoudre('#inNutriDate').value = new Date().toISOString().slice(0, 10);
    dom.resoudre('#btnValiderNutrition').onclick();
    const enregistrees = app.EQ.store.getNutrition();
    assert.equal(enregistrees.length, 1, 'une entrée doit être enregistrée');
    assert.equal(enregistrees[0].unite, 'c. à soupe', 'l’unité doit être conservée');
    assert.equal(Number(enregistrees[0].qty), 2, 'la quantité doit être conservée');
}

function testUnitePartDansLaSynchronisation() {
    // 1.4 : l'unité choisie à la saisie doit partir vers Supabase et revenir
    // dans la ligne locale. Les tables de suivi sont préfixées « sr_ » côté
    // serveur (net.js:347), la colonne visée est donc sr_protein_entries.unite.
    const { EQ } = creerAppli();

    const ligne = {
        date: '2026-10-12', item: 'Œuf', qty: 2, unite: 'c. à soupe',
        protein_g: 13, carbs_g: 1, fat_g: 11
    };
    const envoyee = EQ.net._rowProtein(ligne, 'uid-1');

    assert.equal(envoyee.unite, 'c. à soupe', 'l’unité doit être transmise à Supabase');
    assert.equal(envoyee.user_id, 'uid-1');
    assert.equal(envoyee.entry_date, '2026-10-12', 'la date locale doit devenir entry_date');
    assert.equal(Number(envoyee.qty), 2);

    // Sans unité renseignée, la colonne n'est pas envoyée du tout : une base
    // qui n'aurait pas encore la colonne continue d'accepter l'insertion.
    const sansUnite = EQ.net._rowProtein(
        { date: '2026-10-12', item: 'Riz', qty: 1, protein_g: 7 }, 'uid-1');
    assert.ok(!('unite' in sansUnite),
        'une entrée sans unité ne doit pas exiger la colonne unite');

    // Au retour du serveur, l'unité doit être restituée à l'interface.
    const relue = EQ.net._localProtein({
        id: 42, entry_date: '2026-10-12', item: 'Œuf', qty: 2,
        unite: 'c. à soupe', protein_g: 13, carbs_g: 1, fat_g: 11
    });
    assert.equal(relue.unite, 'c. à soupe', 'l’unité doit revenir du serveur');
    assert.equal(relue.date, '2026-10-12', 'entry_date doit redevenir date');

    // Une ligne serveur sans colonne unite ne doit pas casser la lecture.
    assert.equal(EQ.net._localProtein({
        id: 43, entry_date: '2026-10-12', item: 'Riz', qty: 1, protein_g: 7
    }).unite, '', 'l’absence de colonne unite doit donner une chaîne vide');
}

function testRepasTypesEditables() {
    // 1.4 : les repas types étaient figés dans models.js, impossible de corriger
    // un aliment faux ou changé. Les corrections se stockent séparément et se
    // substituent au modèle à la lecture.
    const app = creerAppli();
    const { EQ } = app;
    const modele = EQ.modele.REPAS_TYPES;
    assert.ok(modele.length >= 3, 'le modèle doit contenir les repas types d’origine');

    // Sans aucune modification, on retrouve exactement le modèle.
    const avant = EQ.store.getRepasTypes();
    assert.equal(avant.length, modele.length, 'aucun ajout ni retrait au départ');
    assert.deepEqual(avant.map((r) => r.cle), modele.map((r) => r.cle));

    // Corriger un repas existant : mêmes clés, valeurs remplacées.
    const cible = modele[0];
    EQ.store.saveRepasType({
        cle: cible.cle, nom: 'Gamelle corrigée', detail: '2 œufs · 80 g lentilles',
        prot: 42, gluc: 30, lip: 18, kcal: 450
    });
    const apres = EQ.store.getRepasTypes();
    assert.equal(apres.length, modele.length, 'une correction ne doit pas dupliquer la ligne');
    const corrige = apres.find((r) => r.cle === cible.cle);
    assert.equal(corrige.nom, 'Gamelle corrigée', 'le nom corrigé doit être lu');
    assert.equal(Number(corrige.prot), 42, 'les macros corrigées doivent être lues');
    assert.equal(corrige.emoji, cible.emoji,
        'les champs non modifiés doivent rester ceux du modèle');

    // Créer un repas personnel : il s’ajoute à la liste.
    EQ.store.saveRepasType({ cle: 'perso_test', emoji: '🍲', nom: 'Mon repas',
        detail: '', prot: 30, gluc: 20, lip: 10, kcal: 310 });
    assert.equal(EQ.store.getRepasTypes().length, modele.length + 1,
        'un repas créé doit s’ajouter');

    // Supprimer : le repas disparaît, le modèle reste intact.
    EQ.store.supprimerRepasType(cible.cle);
    const restants = EQ.store.getRepasTypes();
    assert.ok(!restants.some((r) => r.cle === cible.cle), 'le repas supprimé ne doit plus apparaître');
    assert.equal(restants.length, modele.length, 'le repas personnel est toujours là');
    assert.ok(modele.some((r) => r.cle === cible.cle),
        'le modèle d’origine ne doit jamais être modifié');

    // Les corrections survivent à une relecture depuis le stockage.
    const app2 = creerAppli(Object.fromEntries(app.donnees));
    assert.ok(!app2.EQ.store.getRepasTypes().some((r) => r.cle === cible.cle),
        'la suppression doit persister');
    assert.equal(app2.EQ.store.getRepasTypes().find((r) => r.cle === 'perso_test').nom,
        'Mon repas', 'le repas créé doit persister');
}

function testEtatCruCuitChangeLesMacros() {
    // 1.4 : le même aliment n'a pas les mêmes macros pesé cru ou pesé cuit.
    // 100 g de pâtes sèches font 364 kcal, cuites 167. Le choix se fait à la
    // saisie (journal nutrition ou ligne de recette), pas dans la fiche aliment.
    //
    // Aucun coefficient de conversion n'est appliqué : la perte d'eau va de
    // +1 % (pomme de terre) à -58 % (pois chiche) selon l'aliment et la cuisson.
    const app = creerAppli();
    amorcerMenus(app, {
        ingredients: [
            { id: 'ing-pates', name: 'Pâtes', category: 'Épicerie Salée', unit: 'g',
              kcal_100g: 364, proteines_100g: 12, glucides_100g: 75, lipides_100g: 1.5,
              etat_defaut: 'cru',
              kcal_100g_cru: 364, proteines_100g_cru: 12, glucides_100g_cru: 75, lipides_100g_cru: 1.5,
              kcal_100g_cuit: 167, proteines_100g_cuit: 6, glucides_100g_cuit: 33, lipides_100g_cuit: 0.9 },
            { id: 'ing-carotte', name: 'Carotte', category: 'Fruits & Légumes', unit: 'g',
              kcal_100g: 30.2, proteines_100g: 0.77, glucides_100g: 4.74, lipides_100g: 0.24 },
            { id: 'ing-pdt', name: 'Pomme de terre', category: 'Fruits & Légumes', unit: 'g',
              kcal_100g: 80, proteines_100g: 2, glucides_100g: 17, lipides_100g: 0.1,
              etat_defaut: 'cru', kcal_100g_cuit: 81, proteines_100g_cuit: 2,
              glucides_100g_cuit: 17.5, lipides_100g_cuit: 0.1 }
        ],
        recipes: [
            { id: 'rec-veloute', name: 'Velouté de carotte', base_servings: 2 },
            { id: 'rec-pates', name: 'Pâtes', base_servings: 1 }
        ],
        recipe_ingredients: [
            { id: 'li-1', recipe_id: 'rec-veloute', ingredient_id: 'ing-carotte',
              quantity: 400, unit: 'g', etat: 'cuit' }
        ]
    });
    const M = app.EQ.menu;

    // 1. Le choix n'est proposé que si l'aliment a au moins une valeur d'état.
    const parId = M.ingredientParId();
    const pates = parId['ing-pates'];
    const carotte = parId['ing-carotte'];
    assert.ok(pates, 'les pâtes doivent être lues depuis le cache des menus');
    assert.equal(M.aChoixEtat(pates), true, 'les pâtes ont deux états renseignés');
    assert.equal(M.aChoixEtat(carotte), false,
        'sans valeur d’état, pas de sélecteur : on n’invente pas de coefficient');

    // 2. Les macros suivent l'état choisi.
    assert.equal(Number(M.macrosPourEtat(pates, 'cru').kcal), 364, 'pâtes crues = 364 kcal');
    assert.equal(Number(M.macrosPourEtat(pates, 'cuit').kcal), 167, 'pâtes cuites = 167 kcal');
    assert.equal(Number(M.macrosPourEtat(pates, 'cuit').glucides), 33, 'les glucides suivent aussi');

    // 3. Sans choix explicite, l'état par défaut de l'aliment s'applique.
    assert.equal(M.etatDefaut(pates), 'cru', 'l’état par défaut est lu sur l’aliment');
    assert.equal(M.macrosPourEtat(pates, '').etat, 'cru', 'un état vide retombe sur le défaut');
    assert.equal(Number(M.macrosPourEtat(pates, '').kcal), 364);

    // 4. Valeur d'état absente : repli sur la colonne historique, jamais sur 0.
    const seulementCuit = { id: 'x', kcal_100g: 80, proteines_100g: 2,
        glucides_100g: 17, lipides_100g: 0.1, kcal_100g_cuit: 81 };
    assert.equal(Number(M.macrosPourEtat(seulementCuit, 'cru').kcal), 80,
        'état cru absent : on retombe sur la valeur historique');
    assert.equal(Number(M.macrosPourEtat(seulementCuit, 'cuit').kcal), 81);

    // 5. Une ligne de recette porte son propre état : le velouté utilise des
    //    carottes cuites, pas crues.
    const veloute = M.calculerRecette('rec-veloute');
    assert.ok(veloute, 'la recette doit se calculer');
    assert.equal(veloute.lignes[0].etat, 'cuit', 'la ligne retient l’état choisi');
    assert.equal(veloute.lignes[0].etat_modifiable, false,
        'la carotte n’a pas de valeur d’état : rien à choisir');

    // 6. Même recette avec des pâtes : l'état change bien le total.
    function lignePates(etat) {
        amorcerMenus(app, {
            recipe_ingredients: [
                { id: 'li-2', recipe_id: 'rec-pates', ingredient_id: 'ing-pates',
                  quantity: 100, unit: 'g', etat: etat }
            ]
        });
        return M.calculerRecette('rec-pates');
    }
    const cru = lignePates('cru');
    const cuit = lignePates('cuit');
    assert.equal(Math.round(cru.total.kcal), 364, '100 g de pâtes crues = 364 kcal');
    assert.equal(Math.round(cuit.total.kcal), 167, '100 g de pâtes cuites = 167 kcal');
    assert.ok(cru.total.kcal - cuit.total.kcal > 150,
        'l’écart cru/cuit doit être visible sur le total de la recette');
    assert.equal(cuit.lignes[0].etat_modifiable, true,
        'les pâtes ont deux états : le sélecteur doit être proposé');
}

function testEtatOmisSiLaColonneManque() {
    // 1.4 : la colonne recipe_ingredients.etat n'existe que si
    // sql/etat_cru_cuit.sql a été exécuté. Si l'application est lancée avant la
    // migration, l'envoi doit retomber sur une ligne sans `etat` au lieu de
    // laisser l'élément bloqué dans la file de synchronisation.
    const appels = [];
    let repondreColonneManquante = true;

    const Native = {
        httpAsync(methode, url, entetes, corps, callbackId) {
            appels.push({ methode, url, corps: JSON.parse(corps || '{}') });
            const premier = appels.length === 1;
            setTimeout(() => {
                if (premier && repondreColonneManquante) {
                    app.EQ.net._fin(callbackId, {
                        ok: false, status: 400,
                        body: '{"message":"column recipe_ingredients.etat does not exist"}'
                    });
                } else {
                    app.EQ.net._fin(callbackId, { ok: true, status: 201, body: '[{"id":"li-1"}]' });
                }
            }, 0);
        }
    };

    // config() lit eq.reglages.v1 (champs supabaseUrl / supabaseKey), pas une
    // clé dédiée : semer autre chose ferait échouer le test pour la mauvaise raison.
    const app = creerAppli({
        'eq.reglages.v1': JSON.stringify({
            supabaseUrl: 'https://test.supabase.co', supabaseKey: 'cle-anon-publique'
        })
    }, { Native });

    // Le prédicat seul ne prouve rien : c'est le repli qui compte.
    assert.equal(app.EQ.net._erreurColonneAbsente(new Error('column x.etat does not exist')), true);
    assert.equal(app.EQ.net._erreurColonneAbsente(new Error('violation de contrainte')), false);

    const session = { access_token: 'jeton', user: { id: '1' } };
    return app.EQ.net._pushMenuItem(
        { table: 'menu:recipe_ingredients', key: 'li-1', operation: 'insert',
          row: { id: 'li-1', recipe_id: 'r1', ingredient_id: 'i1', quantity: 400, unit: 'g', etat: 'cuit' } },
        session
    ).then(() => {
        assert.equal(appels.length, 2, 'un second envoi doit avoir lieu après l’échec');
        assert.equal(appels[0].corps.etat, 'cuit', 'le premier envoi porte bien l’état');
        assert.ok(!('etat' in appels[1].corps),
            'le repli doit retirer `etat` plutôt que de bloquer la file');
        assert.equal(appels[1].corps.quantity, 400, 'le reste de la ligne est préservé');
    });
}

const TESTS = [
    testPremierLancementVide,
    testConservationDonneesLocalesApresMonteeDeVersion,
    testGraphiqueProteinesVideEtUneValeur,
    testReglagesExposentCoachIaEtSupabase,
    testContexteEnvoyeAuCoachIa,
    testSurfaceDesModulesRestaures,
    testEstEnLigneSuitLeReseau,
    testRetourEnLigneDeclencheLeDeversement,
    testMigrationLocaleVersSupabase,
    testFicheRecetteDepuisLePlanning,
    testAutocompletionNutritionProposeRecettesEtAliments,
    testBoutonRecettePresentSurLesPlatsACuisiner,
    testUniteChoisieDansLeJournalNutrition,
    testUnitePartDansLaSynchronisation,
    testRepasTypesEditables,
    testEtatCruCuitChangeLesMacros,
    testEtatOmisSiLaColonneManque,
    testEditeurAlimentSaisitLesValeursCuit,
    testEtatIngredientOmisSiLesColonnesManquent,
    testFicheRecetteRappelleEtatCruCuit
];
let passes = 0;
(async () => {
    for (const test of TESTS) {
        // Les tests asynchrones doivent être attendus : sans `await`, un test
        // renvoyant une promesse serait compté réussi sans avoir rien vérifié.
        await test();
        passes += 1;
        console.log('✓', test.name);
    }
    console.log('\n%d/%d tests mobiles passent.', passes, TESTS.length);
    if (passes !== TESTS.length) process.exitCode = 1;
})().catch((e) => {
    console.error('\n✗', e && e.message);
    console.error('   %d/%d tests mobiles passent avant l\'échec.', passes, TESTS.length);
    process.exitCode = 1;
});
