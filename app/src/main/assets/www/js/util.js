/* Utilitaires : formatage des nombres, dates, calculs et sécurité. */
(function (root) {
    'use strict';
    var EQ = root.EQ = root.EQ || {};

    function estNombre(x) {
        return typeof x === 'number' && isFinite(x);
    }

    function num(x, defaut) {
        var v = typeof x === 'string' ? parseFloat(String(x).replace(/\s/g, '').replace(',', '.')) : x;
        if (typeof v !== 'number' || !isFinite(v)) return defaut === undefined ? 0 : defaut;
        return v;
    }

    var fr = null;
    function frFmt(dec) {
        if (!fr) fr = {};
        if (!fr[dec]) {
            fr[dec] = new Intl.NumberFormat('fr-FR', { minimumFractionDigits: dec, maximumFractionDigits: dec });
        }
        return fr[dec];
    }

    function nombre(x, dec) {
        if (!estNombre(x)) x = 0;
        return frFmt(dec === undefined ? 1 : dec).format(x).replace(/[\u00a0\u202f]/g, ' ');
    }

    function formatKg(x, dec) {
        return nombre(x, dec === undefined ? 1 : dec) + ' kg';
    }

    function formatG(x, dec) {
        return nombre(x, dec === undefined ? 0 : dec) + ' g';
    }

    function formatKcal(x) {
        return nombre(x, 0) + ' kcal';
    }

    function signe(x) {
        return x > 0 ? '+' : (x < 0 ? '−' : '');
    }

    function pct(x, dec, avecSigne) {
        var d = dec === undefined ? 1 : dec;
        var s = avecSigne ? (x > 0 ? '+' : (x < 0 ? '−' : '')) : '';
        return s + nombre(avecSigne ? Math.abs(x) : x, d) + ' %';
    }

    function parseDate(val) {
        if (!val) return new Date();
        if (val instanceof Date) return val;
        var s = String(val).trim();
        var p = s.split('-');
        if (p.length === 3) {
            return new Date(parseInt(p[0], 10), parseInt(p[1], 10) - 1, parseInt(p[2], 10));
        }
        return new Date(val);
    }

    function dateIso(d) {
        d = parseDate(d);
        var y = d.getFullYear();
        var m = String(d.getMonth() + 1).padStart(2, '0');
        var day = String(d.getDate()).padStart(2, '0');
        return y + '-' + m + '-' + day;
    }

    var MOIS = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'];
    var MOIS_COURTS = ['janv.', 'févr.', 'mars', 'avr.', 'mai', 'juin', 'juil.', 'août', 'sept.', 'oct.', 'nov.', 'déc.'];
    var JOURS = ['Dimanche', 'Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi'];
    var JOURS_COURTS = ['Dim', 'Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam'];

    function dateFr(d, options) {
        d = parseDate(d);
        options = options || {};
        var j = d.getDate();
        var m = options.court ? MOIS_COURTS[d.getMonth()] : MOIS[d.getMonth()];
        var txt = j + ' ' + m;
        if (options.annee) txt += ' ' + d.getFullYear();
        if (options.jour) txt = (options.court ? JOURS_COURTS[d.getDay()] : JOURS[d.getDay()]) + ' ' + txt;
        return txt;
    }

    function jourCourt(d) {
        d = parseDate(d);
        return JOURS_COURTS[d.getDay()];
    }

    function echapper(s) {
        if (s == null) return '';
        return String(s)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    function moyenne(nombres) {
        if (!nombres || nombres.length === 0) return 0;
        var total = 0;
        for (var i = 0; i < nombres.length; i++) total += num(nombres[i]);
        return total / nombres.length;
    }

    EQ.util = {
        estNombre: estNombre,
        num: num,
        nombre: nombre,
        formatKg: formatKg,
        formatG: formatG,
        formatKcal: formatKcal,
        signe: signe,
        pct: pct,
        parseDate: parseDate,
        dateIso: dateIso,
        dateFr: dateFr,
        jourCourt: jourCourt,
        echapper: echapper,
        moyenne: moyenne
    };
})(typeof window !== 'undefined' ? window : this);
