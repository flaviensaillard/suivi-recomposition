/* Composants graphiques et widgets interactifs : tuiles, graphiques SVG, feuilles modales. */
(function (root) {
    'use strict';
    var EQ = root.EQ = root.EQ || {};
    var U = EQ.util;

    var fileAttenteToast = null;

    function $(sel, parent) { return (parent || document).querySelector(sel); }
    function $$(sel, parent) { return Array.prototype.slice.call((parent || document).querySelectorAll(sel)); }

    function el(html) {
        var d = document.createElement('div');
        d.innerHTML = String(html).trim();
        return d.firstElementChild;
    }

    function h(s) { return U.echapper(s); }

    function haptic(ms) {
        if (typeof root.Native !== 'undefined' && root.Native.haptic) {
            try { root.Native.haptic(ms || 10); } catch (e) { }
        } else if (navigator.vibrate) {
            try { navigator.vibrate(ms || 10); } catch (e) { }
        }
    }

    function toast(message) {
        var t = $('#toast');
        if (!t) return;
        t.textContent = message;
        t.classList.add('ouvert');
        clearTimeout(fileAttenteToast);
        fileAttenteToast = setTimeout(function () { t.classList.remove('ouvert'); }, 2600);
        haptic(12);
    }

    function badge(texte, sorte) {
        return '<span class="badge ' + (sorte || 'mut') + '">' + h(texte) + '</span>';
    }

    function barre(pctVal, ciblePct, couleur) {
        pctVal = Math.max(0, Math.min(100, pctVal || 0));
        var style = 'width:' + pctVal + '%;';
        if (couleur) style += 'background:' + couleur + ';';
        var repere = ciblePct ? '<u style="left:' + Math.max(0, Math.min(100, ciblePct)) + '%"></u>' : '';
        return '<div class="barre"><i style="' + style + '"></i>' + repere + '</div>';
    }

    // ------------------------------------------------------------- Feuille modale
    function feuille(options) {
        var voile = $('#voile'), f = $('#feuille');
        if (!f) return { fermer: function () { } };

        var html = '<div class="poignee"></div>';
        if (options.titre) html += '<h3>' + h(options.titre) + '</h3>';
        if (options.aide) html += '<div class="aide">' + h(options.aide) + '</div>';
        html += options.html || '';

        f.innerHTML = html;
        voile.classList.add('ouvert');
        f.classList.add('ouvert');
        haptic(8);

        function fermer() {
            voile.classList.remove('ouvert');
            f.classList.remove('ouvert');
            if (options.onFermer) options.onFermer();
        }

        voile.onclick = fermer;
        var btnFermer = $('.btn-fermer', f);
        if (btnFermer) btnFermer.onclick = fermer;

        if (options.apresRendu) options.apresRendu(f, fermer);

        return { fermer: fermer, racine: f };
    }

    function fermerFeuille() {
        var voile = $('#voile'), f = $('#feuille');
        if (voile) voile.classList.remove('ouvert');
        if (f) f.classList.remove('ouvert');
    }

    // -------------------------------------------------- Graphique SVG d'évolution du poids
    function svgGraphiquePoids(points, cibleKg) {
        if (!points || points.length < 2) {
            return '<div class="vide">Pas assez de données pour tracer la courbe.</div>';
        }

        // Prendre jusqu'à 30 points récents
        var donnees = points.slice(-30);
        var poidsList = donnees.map(function (d) { return d.poids; });
        if (cibleKg) poidsList.push(cibleKg);

        var minP = Math.min.apply(null, poidsList) - 0.8;
        var maxP = Math.max.apply(null, poidsList) + 0.8;
        if (maxP - minP < 2) { maxP += 1; minP -= 1; }

        var w = 340;
        var h = 160;
        var padLeft = 34;
        var padRight = 16;
        var padTop = 16;
        var padBottom = 26;

        var chartW = w - padLeft - padRight;
        var chartH = h - padTop - padBottom;

        function getX(i) {
            return padLeft + (i / (donnees.length - 1)) * chartW;
        }

        function getY(val) {
            return padTop + chartH - ((val - minP) / (maxP - minP)) * chartH;
        }

        // Tracé de la courbe
        var pathD = '';
        var areaD = '';
        var svgPoints = [];

        for (var i = 0; i < donnees.length; i++) {
            var px = getX(i);
            var py = getY(donnees[i].poids);
            svgPoints.push({ x: px, y: py, p: donnees[i].poids, d: donnees[i].date });
            if (i === 0) {
                pathD += 'M ' + px + ' ' + py;
                areaD += 'M ' + px + ' ' + (padTop + chartH) + ' L ' + px + ' ' + py;
            } else {
                var prev = svgPoints[i - 1];
                var cpX1 = prev.x + (px - prev.x) / 2;
                var cpX2 = prev.x + (px - prev.x) / 2;
                pathD += ' C ' + cpX1 + ' ' + prev.y + ', ' + cpX2 + ' ' + py + ', ' + px + ' ' + py;
                areaD += ' C ' + cpX1 + ' ' + prev.y + ', ' + cpX2 + ' ' + py + ', ' + px + ' ' + py;
            }
        }
        areaD += ' L ' + getX(donnees.length - 1) + ' ' + (padTop + chartH) + ' Z';

        // Ligne de l'objectif
        var cibleY = cibleKg ? getY(cibleKg) : null;
        var cibleSvg = '';
        if (cibleY && cibleY >= padTop && cibleY <= padTop + chartH) {
            cibleSvg = '<line x1="' + padLeft + '" y1="' + cibleY + '" x2="' + (w - padRight) + '" y2="' + cibleY + '" ' +
                'stroke="#F5C451" stroke-dasharray="4,4" stroke-width="1.2" opacity="0.85" />' +
                '<text x="' + (w - padRight) + '" y="' + (cibleY - 4) + '" fill="#F5C451" font-size="10" font-weight="700" text-anchor="end">Cible ' + U.formatKg(cibleKg, 1) + '</text>';
        }

        // Graduations Y
        var yTicks = [minP + 0.8, (minP + maxP) / 2, maxP - 0.8];
        var gridLines = yTicks.map(function (val) {
            var y = getY(val);
            return '<line x1="' + padLeft + '" y1="' + y + '" x2="' + (w - padRight) + '" y2="' + y + '" stroke="rgba(255,255,255,0.06)" />' +
                   '<text x="' + (padLeft - 6) + '" y="' + (y + 3) + '" fill="#6B7789" font-size="9.5" text-anchor="end">' + val.toFixed(1) + '</text>';
        }).join('');

        // Graduations X (première et dernière date)
        var dateDebut = U.dateFr(donnees[0].date, { court: true });
        var dateFin = U.dateFr(donnees[donnees.length - 1].date, { court: true });
        var dateLabels = '<text x="' + padLeft + '" y="' + (h - 6) + '" fill="#6B7789" font-size="9.5" text-anchor="start">' + dateDebut + '</text>' +
                         '<text x="' + (w - padRight) + '" y="' + (h - 6) + '" fill="#6B7789" font-size="9.5" text-anchor="end">' + dateFin + '</text>';

        // Cercles interactifs
        var cercles = svgPoints.map(function (pt, idx) {
            var isLast = idx === svgPoints.length - 1;
            var r = isLast ? 4.5 : 2.5;
            var fill = isLast ? '#0D9488' : '#38BDF8';
            var stroke = isLast ? '#FFFFFF' : 'none';
            return '<circle class="point-poids" cx="' + pt.x + '" cy="' + pt.y + '" r="' + r + '" fill="' + fill + '" stroke="' + stroke + '" stroke-width="1.5" ' +
                   'data-date="' + pt.d + '" data-poids="' + pt.p + '" style="cursor:pointer;" />';
        }).join('');

        return '<div class="graphique-wrap">' +
            '<svg viewBox="0 0 ' + w + ' ' + h + '" class="svg-graphique" preserveAspectRatio="none">' +
                '<defs>' +
                    '<linearGradient id="degradePoids" x1="0" y1="0" x2="0" y2="1">' +
                        '<stop offset="0%" stop-color="#0D9488" stop-opacity="0.28"/>' +
                        '<stop offset="100%" stop-color="#0D9488" stop-opacity="0.00"/>' +
                    '</linearGradient>' +
                '</defs>' +
                gridLines +
                cibleSvg +
                '<path d="' + areaD + '" fill="url(#degradePoids)" />' +
                '<path d="' + pathD + '" fill="none" stroke="#0D9488" stroke-width="2.5" stroke-linecap="round" />' +
                cercles +
                dateLabels +
            '</svg>' +
            '<div class="graphique-info" id="graphiqueInfo">Touchez un point pour afficher la valeur exacte</div>' +
        '</div>';
    }

    // -------------------------------------------------- Barres protéines 7 jours
    function svgBarresProteines(donnees7j, cibleG) {
        var w = 320, h = 90;
        var padLeft = 14, padRight = 14, padBottom = 22, padTop = 10;
        var barW = 28;
        var chartH = h - padTop - padBottom;
        var jours = Array.isArray(donnees7j) ? donnees7j.filter(function (x) {
            return x && typeof x.proteinesG === 'number' && isFinite(x.proteinesG) && x.proteinesG >= 0;
        }) : [];

        if (!jours.length) {
            return '<div class="vide">Aucune saisie de protéines à afficher.</div>';
        }

        cibleG = U.num(cibleG, null);
        if (cibleG === null || cibleG <= 0) {
            return '<div class="vide">Le repère protéines doit être vérifié dans Réglages.</div>';
        }
        var maxSaisi = Math.max.apply(null, jours.map(function (x) { return x.proteinesG; }));
        var maxProt = Math.max(cibleG * 1.25, maxSaisi, 1);
        var cibleY = padTop + chartH - (cibleG / maxProt) * chartH;
        var pas = jours.length > 1 ? (w - padLeft - padRight - barW) / (jours.length - 1) : 0;

        var barres = jours.map(function (d, i) {
            var x = jours.length > 1 ? padLeft + i * pas : (w - barW) / 2;
            var val = d.proteinesG;
            var bH = Math.max(3, (val / maxProt) * chartH);
            var y = padTop + chartH - bH;
            var ok = val >= cibleG;
            var col = ok ? '#10B981' : '#38BDF8';
            var jour = U.jourCourt(d.date);

            return '<rect x="' + x + '" y="' + y + '" width="' + barW + '" height="' + bH + '" rx="5" fill="' + col + '" />' +
                   '<text x="' + (x + barW / 2) + '" y="' + (y - 4) + '" fill="#F2F5FA" font-size="9" font-weight="700" text-anchor="middle">' + val + '</text>' +
                   '<text x="' + (x + barW / 2) + '" y="' + (h - 6) + '" fill="#6B7789" font-size="9.5" text-anchor="middle">' + jour + '</text>';
        }).join('');

        var ligneCible = '<line x1="' + padLeft + '" y1="' + cibleY + '" x2="' + (w - padRight) + '" y2="' + cibleY + '" stroke="#F5C451" stroke-dasharray="3,3" stroke-width="1" />' +
                         '<text x="' + (w - padRight) + '" y="' + (cibleY - 3) + '" fill="#F5C451" font-size="8.5" text-anchor="end">Repère ' + cibleG + ' g</text>';

        return '<svg viewBox="0 0 ' + w + ' ' + h + '" class="svg-barres" preserveAspectRatio="none">' +
            ligneCible +
            barres +
        '</svg>';
    }

    EQ.ui = {
        $: $,
        $$: $$,
        el: el,
        h: h,
        haptic: haptic,
        toast: toast,
        badge: badge,
        barre: barre,
        feuille: feuille,
        fermerFeuille: fermerFeuille,
        svgGraphiquePoids: svgGraphiquePoids,
        svgBarresProteines: svgBarresProteines
    };
})(typeof window !== 'undefined' ? window : this);
