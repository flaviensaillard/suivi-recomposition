/* Tests ciblés de la coque mobile, sans navigateur ni dépendance externe.
 * Exécuter avec : node test_mobile.js
 */
'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const JS_DIR = path.join(__dirname, 'app/src/main/assets/www/js');
const SOURCES = ['util.js', 'models.js', 'store.js', 'ui.js', 'views.js'];

function creerAppli(stockInitial) {
    const donnees = new Map(Object.entries(stockInitial || {}));
    const localStorage = {
        getItem(cle) { return donnees.has(cle) ? donnees.get(cle) : null; },
        setItem(cle, valeur) { donnees.set(cle, String(valeur)); },
        removeItem(cle) { donnees.delete(cle); }
    };
    const contexte = { localStorage, console, Date, Intl, Math, JSON, Array, Object, String, Number, isFinite };
    contexte.window = contexte;
    vm.createContext(contexte);
    for (const fichier of SOURCES) {
        vm.runInContext(fs.readFileSync(path.join(JS_DIR, fichier), 'utf8'), contexte, { filename: fichier });
    }
    return { EQ: contexte.EQ, localStorage, donnees };
}

function testPremierLancementVide() {
    const { EQ, donnees } = creerAppli();
    assert.deepEqual(Array.from(EQ.store.getLogs()), []);
    assert.deepEqual(Array.from(EQ.store.getMensurations()), []);
    assert.deepEqual(Array.from(EQ.store.getSeances()), []);
    assert.deepEqual(Array.from(EQ.store.getCourses()), []);
    assert.equal(EQ.store.getReglages().profileConfigured, false);
    assert.equal(EQ.store.anciennesDonneesAverifier(), false);
    assert.equal(JSON.parse(donnees.get('eq.revisionDonnees.v2')), 2);
}

function testConservationEtAvertissementAncienStockage() {
    const logsAnciens = [{ date: '2026-01-01', poids: 80, proteinesG: 47, caloriesKcal: 1234 }];
    const { EQ } = creerAppli({
        'eq.logs.v1': JSON.stringify(logsAnciens),
        'eq.courses.v1': JSON.stringify([{ id: 'old', produit: 'Article', pris: false }])
    });
    assert.deepEqual(JSON.parse(JSON.stringify(EQ.store.getLogs())), logsAnciens);
    assert.equal(EQ.store.getCourses().length, 1);
    assert.equal(EQ.store.anciennesDonneesAverifier(), true);
    const html = EQ.views.vueBord({ reglages: EQ.store.getReglages(), logs: EQ.store.getLogs() });
    assert.match(html, /Données locales antérieures à vérifier/);
    EQ.store.masquerAvertissementDonneesPreexistantes();
    assert.equal(EQ.store.anciennesDonneesAverifier(), false);
    assert.deepEqual(JSON.parse(JSON.stringify(EQ.store.getLogs())), logsAnciens);
}

function testGraphiqueProteinesVideEtUneValeur() {
    const { EQ } = creerAppli();
    const vide = EQ.ui.svgBarresProteines([], 130);
    assert.match(vide, /Aucune saisie de protéines/);
    const uneBarre = EQ.ui.svgBarresProteines([{ date: '2026-01-01', proteinesG: 42 }], 130);
    assert.match(uneBarre, /<svg/);
    assert.match(uneBarre, /42/);
    assert.doesNotMatch(uneBarre, /NaN|Infinity/);
    assert.match(EQ.ui.svgBarresProteines([{ date: '2026-01-01', proteinesG: null }], 130), /Aucune saisie/);
    assert.match(EQ.ui.svgBarresProteines([{ date: '2026-01-01', proteinesG: 42 }], 0), /vérifié dans Réglages/);
}

function testFormulairePeseeSansMacrosPreremplies() {
    const { EQ } = creerAppli();
    const champs = {
        '#inDatePesee': { value: '2026-01-02' },
        '#inPoids': { value: '80.2' },
        '#inGras': { value: '' },
        '#inProt': { value: '' },
        '#inKcal': { value: '' },
        '#btnValiderNouvellePesee': { onclick: null }
    };
    let configFeuille;
    let fermee = false;
    EQ.ui.$ = (selecteur) => champs[selecteur] || null;
    EQ.ui.toast = () => {};
    EQ.ui.feuille = (config) => {
        configFeuille = config;
        config.apresRendu({}, () => { fermee = true; });
    };
    EQ.views.feuillePesee({ reglages: EQ.store.getReglages(), logs: [] });
    for (const id of ['inGras', 'inProt', 'inKcal']) {
        assert.match(configFeuille.html, new RegExp(`id="${id}"[^>]*value=""`));
    }
    champs['#btnValiderNouvellePesee'].onclick();
    const [saisie] = EQ.store.getLogs();
    assert.equal(saisie.poids, 80.2);
    assert.equal(Object.hasOwn(saisie, 'proteinesG'), false);
    assert.equal(Object.hasOwn(saisie, 'caloriesKcal'), false);
    assert.equal(Object.hasOwn(saisie, 'masseGrassePct'), false);
    assert.equal(fermee, true);
}

function testRepèresMobilesVidesSansConfirmation() {
    const { EQ } = creerAppli();
    const reglages = EQ.store.getReglages();
    assert.equal(reglages.profileConfigured, false);
    let feuille;
    EQ.ui.feuille = (config) => { feuille = config; };
    EQ.views.feuilleReglages({ reglages }, () => {});
    for (const id of ['regPoidsCible', 'regProtCible', 'regKcalCible']) {
        assert.match(feuille.html, new RegExp(`id="${id}" value=""`));
    }
    assert.match(feuille.html, /Repères à vérifier — non personnalisés/);
}

function testMensurationPartielleEtSeanceGenerique() {
    const { EQ } = creerAppli();
    const champs = {
        '#inDateMens': { value: '2026-01-03' },
        '#inTailleCm': { value: '84.5' },
        '#inHanchesCm': { value: '' },
        '#inBrasCm': { value: '' },
        '#inCuisseCm': { value: '' },
        '#btnValiderMens': { onclick: null }
    };
    EQ.ui.$ = (selecteur) => champs[selecteur] || null;
    EQ.ui.toast = () => {};
    EQ.ui.feuille = (config) => config.apresRendu({}, () => {});
    EQ.views.feuilleMensurations({}, () => {});
    champs['#btnValiderMens'].onclick();
    const [mesure] = EQ.store.getMensurations();
    assert.equal(mesure.tailleCm, 84.5);
    assert.equal(Object.hasOwn(mesure, 'hanchesCm'), false);
    assert.equal(Object.hasOwn(mesure, 'brasCm'), false);

    EQ.views.setSousOngletSeances('B');
    const html = EQ.views.vueSeances({});
    assert.match(html, /Programme générique/);
    assert.match(html, /data-type="B"/);
    assert.match(html, /data-nom="Séance B/);
    assert.doesNotMatch(html, /value="10"|value="PDC"/);
    assert.match(html, /saisies de séries restent temporaires/);
}

[
    testPremierLancementVide,
    testConservationEtAvertissementAncienStockage,
    testGraphiqueProteinesVideEtUneValeur,
    testFormulairePeseeSansMacrosPreremplies,
    testRepèresMobilesVidesSansConfirmation,
    testMensurationPartielleEtSeanceGenerique
].forEach((test) => {
    test();
    console.log(`✓ ${test.name}`);
});

console.log('Tous les tests mobiles ciblés passent.');
