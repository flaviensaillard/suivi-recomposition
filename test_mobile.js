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

const TESTS = [
    testPremierLancementVide,
    testConservationDonneesLocalesApresMonteeDeVersion,
    testGraphiqueProteinesVideEtUneValeur,
    testReglagesExposentCoachIaEtSupabase,
    testContexteEnvoyeAuCoachIa,
    testSurfaceDesModulesRestaures,
    testEstEnLigneSuitLeReseau,
    testRetourEnLigneDeclencheLeDeversement,
    testMigrationLocaleVersSupabase
];
let passes = 0;
TESTS.forEach((test) => {
    test();
    passes += 1;
    console.log('✓', test.name);
});
console.log('\n%d/%d tests mobiles passent.', passes, TESTS.length);
