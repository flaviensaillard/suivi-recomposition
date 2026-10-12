/* Vues complètes des cinq écrans et des feuilles modales d'action. */
(function (root) {
    'use strict';
    var EQ = root.EQ = root.EQ || {};
    var U = EQ.util, M = EQ.modele, UI = EQ.ui, Store = EQ.store, Net = EQ.net, Menu = EQ.menu, h = UI.h;

    var sousOngletMenus = 'planning'; // 'planning', 'recettes', 'courses'
    var sousOngletSeances = 'A';       // 'A', 'B', 'historique'
    var dateNutrition = U.dateIso(new Date());
    var minuteurTimer = null;
    var minuteurRestant = 0;
    var minuteurTotal = 0;

    var JOURS_SEMAINE = ['dimanche', 'lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi'];
    function planningSeanceDuJour(jourSemaine) {
        var jour = jourSemaine == null ? new Date().getDay() : Number(jourSemaine);
        if (!isFinite(jour) || jour < 0 || jour > 6) jour = new Date().getDay();
        jour = Math.floor(jour);
        var planning = [
            { jour: 1, programme: M && M.SEANCE_A },
            { jour: 5, programme: M && M.SEANCE_B }
        ].filter(function (x) { return !!x.programme; });
        var seance = planning.find(function (x) { return x.jour === jour; }) || null;
        var prochaine = null;
        if (!seance) {
            var delaiMini = 8;
            planning.forEach(function (x) {
                var delai = (x.jour - jour + 7) % 7;
                if (delai === 0) delai = 7;
                if (delai < delaiMini) { delaiMini = delai; prochaine = x; }
            });
        }
        return {
            jour: jour,
            seance: seance,
            prochaine: prochaine,
            nomJour: JOURS_SEMAINE[jour],
            nomJourProchain: prochaine ? JOURS_SEMAINE[prochaine.jour] : ''
        };
    }

    // =========================================================================
    // 1. TABLEAU DE BORD (Bord)
    // =========================================================================
    function vueBord(ctx) {
        var logs = ctx.logs;
        var reglages = ctx.reglages;
        var statPoids = M.calculerMoyennesPoids(logs);
        var dernierLog = logs[logs.length - 1] || {};
        var poidsActuel = statPoids.actuel;
        var ecartCible = poidsActuel == null ? null : Math.round((poidsActuel - reglages.poidsCibleKg) * 10) / 10;
        var nutritionAuj = Store.totauxNutrition(U.dateIso(new Date()));
        var protAuj = nutritionAuj.protein_g;
        var kcalAuj = Math.round((nutritionAuj.protein_g + nutritionAuj.carbs_g) * 4 + nutritionAuj.fat_g * 9);
        var protCible = reglages.objectifProteinesG || 130;
        var kcalCible = reglages.objectifCaloriesKcal || 1700;
        var pctProt = protCible ? Math.min(100, Math.round((protAuj / protCible) * 100)) : 0;
        var pctKcal = kcalCible ? Math.min(100, Math.round((kcalAuj / kcalCible) * 100)) : 0;

        var aujourdhui = U.dateIso(new Date());
        var repasAuj = Menu ? Menu.planned(aujourdhui) : [];
        var detailsRepasAuj = repasAuj.map(function (r) {
            return { repas: r, detail: Menu.detailsRepas(r) };
        });
        var titreRepasAuj = !detailsRepasAuj.length ? 'Aucun repas prévu'
            : detailsRepasAuj.length === 1
                ? (detailsRepasAuj[0].repas.meal_type || 'Repas') + ' · ' + detailsRepasAuj[0].detail.name
                : detailsRepasAuj.length + ' repas prévus aujourd’hui';
        var metaRepasAuj = !detailsRepasAuj.length ? 'Ouvre Menus pour planifier'
            : detailsRepasAuj.map(function (x) {
                var d = x.detail, m = x.repas;
                var label = (m.meal_type || 'Repas') + ' : ' + d.name;
                return label + (d.calc
                    ? ' · ' + Math.round(d.calc.par_part.proteines) + ' g prot / ' + Math.round(d.calc.par_part.kcal) + ' kcal / part'
                    : ' · macros non renseignées');
            }).join(' · ');
        var badgeRepasAuj = !repasAuj.length ? 'À planifier'
            : repasAuj.length === 1
                ? (repasAuj[0].servings || repasAuj[0].nb_persons || 4) + ' convives'
                : repasAuj.length + ' repas planifiés';
        var planningSeance = planningSeanceDuJour(new Date().getDay());
        var seanceJour = planningSeance.seance;
        var historiqueSeances = ctx.seances || Store.getSeances() || [];
        var seanceEffectuee = !!(seanceJour && historiqueSeances.some(function (s) {
            return String(s.date || s.session_date || '').slice(0, 10) === aujourdhui &&
                String(s.type || s.session || '') === String(seanceJour.programme.cle);
        }));
        var titreSeanceAuj = seanceJour ? 'Séance ' + seanceJour.programme.cle : 'Aucune séance prévue';
        var metaSeanceAuj = seanceJour
            ? seanceJour.programme.titre.replace('Séance ' + seanceJour.programme.cle + ' — ', '') + ' · ' + (seanceJour.programme.duree || '30 min')
            : planningSeance.prochaine
                ? 'Prochaine séance : ' + planningSeance.nomJourProchain + ' · ' + planningSeance.prochaine.programme.titre + ' · ' + (planningSeance.prochaine.programme.duree || '30 min')
                : 'Aucune séance programmée';
        var badgeSeanceAuj = seanceJour ? (seanceEffectuee ? 'Terminée' : 'À faire') : 'Récupération';
        var debutSemaine = Menu ? Menu.dateIso(Menu.lundiDe(aujourdhui)) : aujourdhui;
        var finDateCourses = new Date(debutSemaine + 'T12:00:00'); finDateCourses.setDate(finDateCourses.getDate() + 6);
        var coursesCourantes = Menu ? Menu.courses(debutSemaine, Menu.dateIso(finDateCourses), true).items : Store.getCourses();
        var coursesRestantes = coursesCourantes.filter(function (c) { return !c.pris; }).length;

        var html = '';

        // --- CARTE HÉRO : POIDS & OBJECTIF
        html += '<div class="card hero teal">' +
            '<div class="lbl">Recomposition corporelle · Poids actuel</div>' +
            '<div class="hero-montant">' + (poidsActuel == null ? '—' : U.formatKg(poidsActuel, 1)) + '</div>' +
            '<div class="hero-sub">Cible ' + U.formatKg(reglages.poidsCibleKg, 1) + (ecartCible == null ? ' · note ta première pesée' : ' · Écart ' + (ecartCible > 0 ? '+' : '') + ecartCible.toFixed(1) + ' kg') + '</div>' +
            '<div style="margin-top:10px; display:flex; align-items:center; gap:8px; flex-wrap:wrap;">' +
                (poidsActuel == null ? '<span class="badge info">Aucune pesée enregistrée</span>' :
                 statPoids.tendance7j < 0 ? '<span class="badge ok">↘ ' + statPoids.tendance7j.toFixed(1) + ' kg sur 7 j</span>' :
                 statPoids.tendance7j > 0 ? '<span class="badge warn">↗ +' + statPoids.tendance7j.toFixed(1) + ' kg sur 7 j</span>' :
                 '<span class="badge info">→ Poids stable sur 7 j</span>') +
                '<span class="badge info">Suivi personnel</span>' +
                '<span class="dim" style="font-size:12px; margin-left:auto;">' + (dernierLog.date ? U.dateFr(dernierLog.date, { court: true }) : '—') + '</span>' +
            '</div>' +
            '<button class="btn btn-hero" id="btnAjoutPeseeRapide" style="margin-top:14px;">＋ Noter la pesée du jour</button>' +
        '</div>';

        // --- GRILLE DE TUILES INTERACTIVES (g2)
        html += '<div class="titre">Indicateurs clés du jour</div>' +
        '<div class="grille g2">' +
            // Tuile Protéines
            '<div class="mini tuile-cliquable" id="tuileProt">' +
                '<div class="l">Protéines</div>' +
                '<div class="v ' + (protAuj >= protCible ? 'up' : 'flat') + '">' + protAuj + ' g</div>' +
                '<div class="e">Cible ' + protCible + ' g (' + pctProt + ' %)</div>' +
                UI.barre(pctProt, 100, protAuj >= protCible ? '#31C98C' : '#65AEFF') +
            '</div>' +
            // Tuile Calories
            '<div class="mini tuile-cliquable" id="tuileKcal">' +
                '<div class="l">Calories</div>' +
                '<div class="v">' + kcalAuj + ' <span style="font-size:13px;font-weight:600;">kcal</span></div>' +
                '<div class="e">Objectif ' + kcalCible + ' kcal</div>' +
                UI.barre(pctKcal, 100, '#F5C451') +
            '</div>' +
            // Tuile Séance
            '<div class="mini tuile-cliquable" id="tuileSeance">' +
                '<div class="l">Séance du jour</div>' +
                '<div class="v" style="font-size:15px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">' + h(titreSeanceAuj) + '</div>' +
                '<div class="e" style="white-space:normal; overflow-wrap:anywhere;">' + h(metaSeanceAuj) + '</div>' +
                '<div style="margin-top:6px;"><span class="badge ' + (seanceJour ? (seanceEffectuee ? 'ok' : 'info') : 'mut') + '">' + h(badgeSeanceAuj) + '</span></div>' +
            '</div>' +
            // Tuile Menus / Repas — alimentée par le planning local synchronisable
            '<div class="mini tuile-cliquable" id="tuileMidi">' +
                '<div class="l">Repas · aujourd’hui</div>' +
                '<div class="v" style="font-size:15px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">' + h(titreRepasAuj) + '</div>' +
                '<div class="e" style="white-space:normal; overflow-wrap:anywhere;">' + h(metaRepasAuj) + '</div>' +
                '<div style="margin-top:6px;"><span class="badge info">' + h(badgeRepasAuj) + '</span></div>' +
            '</div>' +
        '</div>';

        // --- TUILE : LES 3 REPAS TYPES DE FLAVIEN (1-clic)
        html += '<div class="titre">⭐ Repas types de Flavien <span class="n">1 clic pour noter</span></div>' +
        '<div class="repas-carousel">';

        M.REPAS_TYPES.forEach(function (r) {
            html += '<div class="ligne-repas-type" data-repas="' + r.cle + '">' +
                '<div style="font-size:22px; width:32px;">' + r.emoji + '</div>' +
                '<div class="gr">' +
                    '<div class="tt">' + h(r.nom) + '</div>' +
                    '<div class="st">' + h(r.detail) + '</div>' +
                '</div>' +
                '<div class="dr">' +
                    '<div class="a up">' + r.prot + ' g P</div>' +
                    '<div class="b">' + r.kcal + ' kcal</div>' +
                '</div>' +
                '<button class="iconbtn btn-noter-repas" data-repas="' + r.cle + '" style="margin-left:6px;width:34px;height:34px;" title="Ajouter à ma journée">＋</button>' +
            '</div>';
        });

        html += '</div>';

        // --- TUILE GRAPHIQUE DES PROTÉINES SUR 7 JOURS
        var logs7j = [];
        for (var i7 = 6; i7 >= 0; i7--) {
            var d7 = new Date(); d7.setDate(d7.getDate() - i7);
            var iso7 = U.dateIso(d7);
            logs7j.push({ date: iso7, proteinesG: Math.round(Store.totauxNutrition(iso7).protein_g) });
        }
        html += '<div class="titre">Protéines des 7 derniers jours</div>' +
        '<div class="card tight">' +
            UI.svgBarresProteines(logs7j, protCible) +
        '</div>';

        // --- TUILE LISTE DE COURSES
        html += '<div class="titre">Courses de la semaine</div>' +
        '<div class="card tight tuile-cliquable" id="tuileCoursesBord">' +
            '<div style="display:flex; align-items:center; justify-content:space-between;">' +
                '<div>' +
                    '<div style="font-size:16px; font-weight:700;">' + coursesRestantes + ' article' + (coursesRestantes > 1 ? 's' : '') + ' à acheter</div>' +
                    '<div class="st">Semaine du foyer · Recettes &amp; base</div>' +
                '</div>' +
                '<button class="btn" style="width:auto; min-height:38px; padding:0 14px; font-size:13px;" id="btnVoirCoursesBord">Voir la liste</button>' +
            '</div>' +
        '</div>';

        return html;
    }

    // =========================================================================
    // 2. PESÉE & TENDANCE (Pesée)
    // =========================================================================
    function vuePesee(ctx) {
        var logs = ctx.logs;
        var reglages = ctx.reglages;
        var stats = M.calculerMoyennesPoids(logs);
        var mensurations = Store.getMensurations();
        var derniereMens = mensurations[mensurations.length - 1] || {};
        function afficheMesure(x) { return x == null || x === '' ? '—' : x; }

        var html = '';

        // --- Résumé en 3 mini-tuiles
        html += '<div class="grille g3" style="margin-bottom:12px;">' +
            '<div class="mini">' +
                '<div class="l">Moyenne 7 j</div>' +
                '<div class="v">' + (stats.m7 ? U.formatKg(stats.m7, 1) : '—') + '</div>' +
                '<div class="e">' + (stats.tendance7j < 0 ? '↘ ' + stats.tendance7j.toFixed(1) : (stats.tendance7j > 0 ? '↗ +' + stats.tendance7j.toFixed(1) : '→ stable')) + '</div>' +
            '</div>' +
            '<div class="mini">' +
                '<div class="l">Moyenne 30 j</div>' +
                '<div class="v">' + (stats.m30 ? U.formatKg(stats.m30, 1) : '—') + '</div>' +
                '<div class="e">lissé sur 1 mois</div>' +
            '</div>' +
            '<div class="mini">' +
                '<div class="l">Perte totale</div>' +
                '<div class="v up">' + (stats.perteTotale < 0 ? stats.perteTotale.toFixed(1) + ' kg' : '0,0 kg') + '</div>' +
                '<div class="e">depuis ' + reglages.poidsDepartKg + ' kg</div>' +
            '</div>' +
        '</div>';

        // --- Bouton d'ajout
        html += '<button class="btn" id="btnNouvPesee" style="margin-bottom:14px;">＋ Enregistrer une pesée</button>';

        // --- Graphique interactif
        html += '<div class="titre">Évolution et tendance du poids</div>' +
        '<div class="card">' +
            UI.svgGraphiquePoids(logs, reglages.poidsCibleKg) +
        '</div>';

        // --- Mensurations
        html += '<div class="titre">Mensurations <span class="n">dernière mesure : ' + (derniereMens.date ? U.dateFr(derniereMens.date, { court: true }) : '—') + '</span></div>' +
        '<div class="card card-mensurations">' +
            '<div class="grille g2 grille-mensurations">' +
                '<div class="mini tuile-mensuration"><div class="l">Tour de taille</div><div class="e">au niveau du nombril</div><div class="v">' + afficheMesure(derniereMens.tailleCm) + (derniereMens.tailleCm == null ? '' : ' <small>cm</small>') + '</div></div>' +
                '<div class="mini tuile-mensuration"><div class="l">Tour de hanches</div><div class="e">au plus large des fessiers</div><div class="v">' + afficheMesure(derniereMens.hanchesCm) + (derniereMens.hanchesCm == null ? '' : ' <small>cm</small>') + '</div></div>' +
                '<div class="mini tuile-mensuration"><div class="l">Tour de bras</div><div class="e">biceps contracté</div><div class="v">' + afficheMesure(derniereMens.brasCm) + (derniereMens.brasCm == null ? '' : ' <small>cm</small>') + '</div></div>' +
                '<div class="mini tuile-mensuration"><div class="l">Tour de cuisse</div><div class="e">mi-cuisse</div><div class="v">' + afficheMesure(derniereMens.cuisseCm) + (derniereMens.cuisseCm == null ? '' : ' <small>cm</small>') + '</div></div>' +
            '</div>' +
            '<button class="btn btn-flat" id="btnNouvMensurations" style="margin-top:10px; min-height:42px; font-size:13.5px;">＋ Noter mes mensurations</button>' +
        '</div>';

        // --- Historique des mensurations, modifiable sur l'appareil
        var historiqueMens = mensurations.slice().reverse().slice(0, 6);
        html += '<div class="titre">Historique des mensurations</div><div class="card tight">';
        if (!historiqueMens.length) {
            html += '<div class="vide" style="padding:14px;">Aucune mensuration enregistrée.</div>';
        } else {
            historiqueMens.forEach(function (m) {
                html += '<div class="ligne"><div class="gr">' +
                    '<div class="tt">' + U.dateFr(m.date, {jour:true}) + '</div>' +
                    '<div class="st">Taille ' + afficheMesure(m.tailleCm) + ' · hanches ' + afficheMesure(m.hanchesCm) +
                    ' · poitrine ' + afficheMesure(m.poitrineCm) + ' cm</div></div>' +
                    '<div style="display:flex;gap:5px;">' +
                    '<button class="iconbtn btn-mens-edit" data-date="' + h(m.date) + '" title="Corriger">✎</button>' +
                    '<button class="iconbtn btn-mens-delete" data-date="' + h(m.date) + '" title="Supprimer">×</button>' +
                    '</div></div>';
            });
        }
        html += '</div>';

        // --- Historique des pesées (les 10 dernières)
        var historique = logs.slice().reverse().slice(0, 10);
        html += '<div class="titre">Historique récent des pesées</div>' +
        '<div class="card tight">';
        if (!historique.length) {
            html += '<div class="vide" style="padding:16px;">Aucune pesée enregistrée. Note ta première journée pour commencer le suivi.</div>';
        }
        historique.forEach(function (log) {
            var nutritionJour = Store.totauxNutrition(log.date);
            var kcalJour = Math.round((nutritionJour.protein_g + nutritionJour.carbs_g) * 4 + nutritionJour.fat_g * 9);
            html += '<div class="ligne">' +
                '<div class="gr">' +
                    '<div class="tt">' + U.dateFr(log.date, { jour: true }) + '</div>' +
                    '<div class="st">' + (log.masseGrassePct ? log.masseGrassePct + ' % gras · ' : '') + Math.round(nutritionJour.protein_g) + ' g prot · ' + kcalJour + ' kcal</div>' +
                '</div>' +
                '<div style="display:flex;align-items:center;gap:6px;">' +
                    '<div class="a">' + (log.poids == null ? '—' : U.formatKg(log.poids, 1)) + '</div>' +
                    '<button class="iconbtn btn-log-edit" data-date="' + h(log.date) + '" title="Corriger">✎</button>' +
                    '<button class="iconbtn btn-log-delete" data-date="' + h(log.date) + '" title="Supprimer">×</button>' +
                '</div>' +
            '</div>';
        });
        html += '</div>';

        return html;
    }

    // =========================================================================
    // 3. JOURNAL NUTRITION (Suivi local)
    // =========================================================================
    function vueNutrition(ctx) {
        var date = dateNutrition || U.dateIso(new Date());
        var cibleP = Number(ctx.reglages.objectifProteinesG || 130);
        var cibleG = Number(ctx.reglages.objectifGlucidesG || 140);
        var cibleL = Number(ctx.reglages.objectifLipidesG || 50);
        var cibleK = Number(ctx.reglages.objectifCaloriesKcal || 1700);
        var lignes = Store.nutritionJour(date);
        var total = Store.totauxNutrition(date);
        var kcal = Math.round(total.protein_g * 4 + total.carbs_g * 4 + total.fat_g * 9);
        function pct(v, c) { return c > 0 ? Math.min(100, Math.round(v / c * 100)) : 0; }
        function tuile(nom, valeur, unite, cible, couleur) {
            var pourcent = pct(valeur, cible);
            return '<div class="mini"><div class="l">' + nom + '</div>' +
                '<div class="v">' + Math.round(valeur) + ' <small>' + unite + '</small></div>' +
                '<div class="e">Cible ' + cible + ' ' + unite + '</div>' +
                UI.barre(pourcent, 100, couleur) + '</div>';
        }
        var html = '<div class="card tight teal" style="margin-bottom:12px;">' +
            '<div class="lbl">Journal alimentaire</div>' +
            '<div class="st" style="margin-top:4px;">Saisies enregistrées sur le téléphone; synchronisation Supabase dès que tu es connecté et en ligne.</div>' +
            '<div class="champ" style="margin:10px 0 0;"><label>Journée</label><input type="date" id="nutriDate" value="' + h(date) + '" /></div>' +
        '</div>' +
        '<div class="grille g2">' +
            tuile('Protéines', total.protein_g, 'g', cibleP, '#31C98C') +
            tuile('Glucides', total.carbs_g, 'g', cibleG, '#65AEFF') +
            tuile('Lipides', total.fat_g, 'g', cibleL, '#F5C451') +
            tuile('Calories', kcal, 'kcal', cibleK, '#EF8E6C') +
        '</div>' +
        '<div class="card tight" style="margin-top:12px;">' +
            '<div style="display:flex;justify-content:space-between;align-items:center;gap:8px;">' +
                '<div><div class="lbl">Repas & aliments</div><div class="st">' + lignes.length + ' entrée' + (lignes.length > 1 ? 's' : '') + ' · ' + U.dateFr(date, {jour:true}) + '</div></div>' +
                '<button class="btn btn-hero" id="btnAjoutNutrition" style="width:auto;padding:0 14px;">＋ Ajouter</button>' +
            '</div>' +
        '</div>';

        html += '<div class="titre">Raccourcis</div><div class="card tight">';
        M.REPAS_TYPES.forEach(function (r) {
            html += '<div class="ligne-repas-type" style="padding:9px 0;">' +
                '<div style="font-size:21px;width:30px;">' + h(r.emoji) + '</div>' +
                '<div class="gr"><div class="tt">' + h(r.nom) + '</div><div class="st">' + Math.round(r.prot) + ' g protéines · ' + Math.round(r.kcal) + ' kcal</div></div>' +
                '<button class="iconbtn btn-nutri-preset" data-nutri-preset="' + h(r.cle) + '" aria-label="Ajouter ' + h(r.nom) + '">＋</button>' +
            '</div>';
        });
        html += '</div>';

        html += '<div class="titre">Journal de la journée</div><div class="card tight">';
        if (!lignes.length) {
            html += '<div class="vide" style="padding:18px 8px;">Aucune entrée pour cette journée. Ajoute un aliment ou utilise un raccourci.</div>';
        } else {
            lignes.slice().reverse().forEach(function (x) {
                var k = Math.round((Number(x.protein_g || 0) + Number(x.carbs_g || 0)) * 4 + Number(x.fat_g || 0) * 9);
                var id = String(x.id || x.local_id || '');
                html += '<div class="ligne">' +
                    '<div class="gr"><div class="tt">' + h(x.item || 'Repas') + '</div>' +
                    '<div class="st">' +
                    (x.qty != null && x.qty !== ''
                        ? h(Menu.fmtNombre(x.qty)) + (x.unite ? ' ' + h(x.unite) : '') + ' · '
                        : '') +
                    'P ' + Math.round(x.protein_g || 0) + ' g · G ' + Math.round(x.carbs_g || 0) + ' g · L ' + Math.round(x.fat_g || 0) + ' g · ' + k + ' kcal</div></div>' +
                    '<div style="display:flex;gap:5px;align-items:center;">' +
                    '<button class="iconbtn btn-nutri-edit" data-id="' + h(id) + '" title="Corriger">✎</button>' +
                    '<button class="iconbtn btn-nutri-delete" data-id="' + h(id) + '" title="Supprimer">×</button></div>' +
                '</div>';
            });
        }
        html += '</div>';

        var nutrition = Store.getNutrition();
        var total7 = 0, jours7 = 0;
        for (var i = 0; i < 7; i++) {
            var d = new Date(date + 'T12:00:00');
            d.setDate(d.getDate() - i);
            var iso = U.dateIso(d);
            var t = Store.totauxNutrition(iso).protein_g;
            if (t > 0) { total7 += t; jours7++; }
        }
        html += '<div class="titre">Moyenne sur 7 jours</div><div class="grille g2">' +
            '<div class="mini"><div class="l">Protéines moyennes</div><div class="v">' +
            (jours7 ? Math.round(total7 / 7) : '—') + ' <small>g / jour</small></div><div class="e">' + jours7 + ' jour' + (jours7 > 1 ? 's' : '') + ' avec saisie</div></div>' +
            '<div class="mini"><div class="l">Historique nutrition</div><div class="v">' + nutrition.length + '</div><div class="e">entrée' + (nutrition.length > 1 ? 's' : '') + ' enregistrée' + (nutrition.length > 1 ? 's' : '') + ' localement</div></div>' +
        '</div>';
        return html;
    }

    // Les charges disponibles sont ordonnées du plus léger au plus difficile.
    // Pour les mouvements sans charge externe, on utilise les variantes N1…Nn.
    function optionsIntensiteExercice(exo) {
        var charges = exo && Array.isArray(exo.lests) ? exo.lests.slice() : [];
        var variantes = exo && Array.isArray(exo.variantes) ? exo.variantes.slice() : [];
        if (charges.length > 1) return charges;
        if (variantes.length > 1) {
            var base = charges[0] || 'Poids du corps';
            return variantes.map(function (v) { return base + ' — ' + v; });
        }
        return charges.length ? charges : ['Poids du corps'];
    }
    function nombresDansOption(valeur) {
        return (String(valeur || '').match(/[0-9]+(?:[.,][0-9]+)?/g) || []).map(function (x) {
            return Number(x.replace(',', '.'));
        });
    }
    function indexIntensite(options, serie) {
        if (!serie) return 0;
        var variante = String(serie.variant || '').trim();
        var normalisee = variante.toLowerCase().split(' ').join('');
        var exact = options.findIndex(function (x) {
            return String(x).toLowerCase().split(' ').join('') === normalisee;
        });
        if (exact >= 0) return exact;
        if (normalisee === 'pdc' || normalisee.indexOf('poidsducorps') === 0) {
            var poidsDuCorps = options.findIndex(function (x) {
                var n = String(x).toLowerCase().split(' ').join('');
                return n.indexOf('poidsducorps') === 0 || n.indexOf('pdc') === 0;
            });
            if (poidsDuCorps >= 0) return poidsDuCorps;
        }
        var chiffres = nombresDansOption(variante);
        if (chiffres.length) {
            var correspondant = options.findIndex(function (x) {
                var nombres = nombresDansOption(x);
                return nombres.length === chiffres.length && nombres.every(function (n, i) { return n === chiffres[i]; });
            });
            if (correspondant >= 0) return correspondant;
        }
        if (serie.load_kg != null && isFinite(Number(serie.load_kg))) {
            var parCharge = options.findIndex(function (x) {
                var nombres = nombresDansOption(x);
                return nombres.length === 1 && nombres[0] === Number(serie.load_kg);
            });
            if (parCharge >= 0) return parCharge;
        }
        return 0;
    }
    function ressentiSeance(seance) {
        if (!seance) return '';
        var valeur = String(seance.ressenti || '').toLowerCase().trim();
        if (['facile', 'normal', 'difficile'].indexOf(valeur) >= 0) return valeur;
        var notes = String(seance.notes || '').toLowerCase();
        var debut = notes.indexOf('ressenti');
        if (debut < 0) return '';
        var reste = notes.slice(debut + 8).trim();
        if (reste.charAt(0) === ':' || reste.charAt(0) === '=') reste = reste.slice(1).trim();
        var mot = reste.split(' ')[0].split('·')[0].replace(/[.;,]/g, '');
        return ['facile', 'normal', 'difficile'].indexOf(mot) >= 0 ? mot : '';
    }
    function decalageSelonRessenti(valeur) {
        return valeur === 'facile' ? 1 : (valeur === 'difficile' ? -1 : 0);
    }
    function progressionDerniereSeance(type) {
        var seances = Store.getSeances().filter(function (s) {
            return String(s.type || s.session || 'A') === String(type);
        }).sort(function (a, b) {
            return String(b.date || b.session_date || '').localeCompare(String(a.date || a.session_date || ''));
        });
        var seance = seances[0] || null;
        var date = seance ? String(seance.date || seance.session_date || '').slice(0, 10) : '';
        var ressenti = ressentiSeance(seance);
        var series = seance ? Store.getSeries().filter(function (x) {
            return String(x.date || x.set_date || '').slice(0, 10) === date &&
                String(x.type || x.session || 'A') === String(type);
        }) : [];
        return { seance: seance, date: date, ressenti: ressenti,
            decalage: decalageSelonRessenti(ressenti), series: series };
    }
    function intensitePourSerie(exo, setNo, progression) {
        var options = optionsIntensiteExercice(exo);
        var serie = progression.series.find(function (x) {
            var memeExercice = String(x.exercise || '') === String(exo.id) || String(x.exercise || '') === String(exo.nom);
            return memeExercice && Number(x.set_no || 1) === Number(setNo);
        });
        if (!serie) serie = progression.series.find(function (x) {
            return String(x.exercise || '') === String(exo.id) || String(x.exercise || '') === String(exo.nom);
        });
        var index = serie ? indexIntensite(options, serie) + progression.decalage : 0;
        index = Math.max(0, Math.min(options.length - 1, index));
        return options[index];
    }

    // =========================================================================
    // 3. SÉANCES & MUSCULATION (Séances)
    // =========================================================================
    function vueSeances(ctx) {
        var html = '';

        // --- Chips de bascule Séance A / B / Historique
        html += '<div class="chips" style="margin-bottom:12px;">' +
            '<button class="chip ' + (sousOngletSeances === 'A' ? 'actif' : '') + '" data-seance="A">Séance A · Jambes &amp; Poussée</button>' +
            '<button class="chip ' + (sousOngletSeances === 'B' ? 'actif' : '') + '" data-seance="B">Séance B · Tirage &amp; Épaules</button>' +
            '<button class="chip ' + (sousOngletSeances === 'historique' ? 'actif' : '') + '" data-seance="historique">Historique</button>' +
        '</div>';

        if (sousOngletSeances === 'historique') {
            var seances = Store.getSeances().slice().sort(function (a, b) {
                return String(b.date || b.session_date || '').localeCompare(String(a.date || a.session_date || ''));
            });
            var seriesHistorique = Store.getSeries();
            html += '<div class="titre">Historique des séances d’entraînement</div><div class="card tight">';
            if (seances.length === 0) {
                html += '<div class="vide" style="padding:14px;">Aucune séance enregistrée pour l’instant.</div>';
            } else {
                seances.forEach(function (s) {
                    var dateSeance = String(s.date || s.session_date || '').slice(0, 10);
                    var typeSeance = String(s.type || s.session || 'A');
                    var programmeSeance = typeSeance === 'B' ? M.SEANCE_B : M.SEANCE_A;
                    var nomSeance = !s.nom || s.nom === 'Séance ' + typeSeance ? programmeSeance.titre : s.nom;
                    var nbSeries = seriesHistorique.filter(function (x) {
                        return String(x.date || x.set_date || '').slice(0, 10) === dateSeance &&
                            String(x.type || x.session || 'A') === typeSeance;
                    }).length;
                    var ressenti = ressentiSeance(s);
                    var retourEffort = ressenti ? 'Ressenti ' + ressenti.charAt(0).toUpperCase() + ressenti.slice(1)
                        : (s.rpe == null ? 'Ressenti non renseigné' : 'RPE ' + s.rpe + '/10');
                    var dureeSeance = s.dureeMin == null ? '—' : s.dureeMin;
                    html += '<div class="ligne ligne-seance-historique" role="button" tabindex="0" style="cursor:pointer;"' +
                        ' data-seance-date="' + h(dateSeance) + '" data-seance-type="' + h(typeSeance) + '"' +
                        ' aria-label="Voir les résultats de ' + h(nomSeance) + '">' +
                        '<div class="gr">' +
                            '<div class="tt">' + h(nomSeance) + '</div>' +
                            '<div class="st">' + U.dateFr(dateSeance, { jour: true, annee: true }) + ' · ' + h(retourEffort) + ' · ' + nbSeries + ' série(s)</div>' +
                        '</div>' +
                        '<div class="dr">' +
                            '<div class="a">' + h(dureeSeance) + ' min</div>' +
                            '<div class="b">Voir les résultats ›</div>' +
                        '</div>' +
                    '</div>';
                });
            }
            html += '</div>';
            return html;
        }

        var prog = sousOngletSeances === 'B' ? M.SEANCE_B : M.SEANCE_A;
        var progression = progressionDerniereSeance(prog.cle);
        var aideProgression = !progression.seance
            ? 'Première séance enregistrée : les choix commencent au niveau le plus léger.'
            : progression.ressenti === 'facile'
                ? 'Dernière séance facile : les charges ou variantes disponibles montent d’un cran.'
                : progression.ressenti === 'difficile'
                    ? 'Dernière séance difficile : les charges ou variantes disponibles baissent d’un cran.'
                    : progression.ressenti === 'normal'
                        ? 'Dernière séance normale : les charges ou variantes restent au même niveau.'
                        : 'Le dernier niveau enregistré est repris; le ressenti précédent n’était pas renseigné.';

        // --- Entête de la séance
        html += '<div class="card teal card-programme">' +
            '<div class="lbl">Programme 30 minutes</div>' +
            '<div style="font-size:20px; font-weight:750; margin:4px 0;">' + h(prog.titre) + '</div>' +
            '<div class="st">' + h(prog.description) + '</div>' +
            '<div class="st" style="margin-top:9px;">' + h(aideProgression) + '</div>' +
        '</div>';

        // --- Échauffement (Accordéon)
        html += '<div class="accordeon" data-acc="">' +
            '<div class="tete">' +
                '<span style="font-size:16px;">🔥</span>' +
                '<span class="p">Échauffement articulaire (4 minutes)</span>' +
                '<span class="chev">›</span>' +
            '</div>' +
            '<div class="corps" style="padding:10px 14px;">' +
                '<ul style="margin:0; padding-left:18px; color:var(--txt-2); font-size:13px; line-height:1.6;">' +
                    prog.echauffement.map(function (txt) { return '<li>' + h(txt) + '</li>'; }).join('') +
                '</ul>' +
            '</div>' +
        '</div>';

        // --- Blocs de supersets
        prog.blocs.forEach(function (bloc, bIdx) {
            html += '<div class="titre">' + h(bloc.nom) + ' <span class="n">repos ' + bloc.reposSec + ' s</span></div>';

            bloc.exos.forEach(function (exo, eIdx) {
                html += '<div class="card exercise-card" data-exercise="' + h(exo.id) + '" data-exercise-name="' + h(exo.nom) + '" style="margin-bottom:10px;">' +
                    '<div style="display:flex; align-items:baseline; justify-content:space-between; margin-bottom:6px;">' +
                        '<div style="font-size:16px; font-weight:700;">' + h(exo.nom) + '</div>' +
                        '<span class="badge info">' + h(exo.cible) + '</span>' +
                    '</div>' +
                    '<div class="st exercise-description" style="font-size:12.5px; margin-bottom:10px; line-height:1.45; color:var(--txt-2);">' +
                        h(exo.description) +
                    '</div>' +
                    '<div class="st" style="font-size:11.5px; margin-bottom:8px;">Choisis la charge ou la variante pour chaque série.</div>' +
                    // Séries interactives : charge/variante sélectionnable, avec progression depuis la séance précédente
                    '<div class="exercise-series" style="border-top:1px solid var(--line); padding-top:8px;">' +
                        [1, 2, 3].map(function (setNo) {
                            var optionsIntensite = optionsIntensiteExercice(exo);
                            var intensiteChoisie = intensitePourSerie(exo, setNo, progression);
                            return '<div class="ligne-serie">' +
                                '<span style="font-size:12.5px; font-weight:700; width:65px; color:var(--txt-3);">Série ' + setNo + '</span>' +
                                '<input type="number" class="in-mini in-reps" placeholder="Reps" value="10" />' +
                                '<select class="in-mini in-charge" aria-label="Charge ou variante, ' + h(exo.nom) + ', série ' + setNo + '" title="Charge ou variante">' +
                                    optionsIntensite.map(function (option) {
                                        return '<option value="' + h(option) + '"' + (option === intensiteChoisie ? ' selected' : '') + '>' + h(option) + '</option>';
                                    }).join('') +
                                '</select>' +
                                '<label class="check-serie">' +
                                    '<input type="checkbox" class="cb-serie" data-exo="' + h(exo.id) + '" data-set="' + setNo + '" />' +
                                    '<span class="cb-visuel">✓ Fait</span>' +
                                '</label>' +
                            '</div>';
                        }).join('') +
                    '</div>' +
                '</div>';
            });
            if (bIdx < prog.blocs.length - 1) {
                var cibleMinuteur = 'minuteurAffichageBloc' + (bIdx + 1);
                var selectMinuteur = 'dureeReposBloc' + (bIdx + 1);
                html += '<div class="card tight minuteur-card" style="margin:-2px 0 12px;">' +
                    '<div style="display:flex; align-items:center; justify-content:space-between; gap:8px; flex-wrap:wrap;">' +
                        '<div><div class="lbl">Repos avant le bloc ' + (bIdx + 2) + '</div>' +
                            '<div class="st">Minuteur prêt · 60 secondes par défaut</div></div>' +
                        '<div class="minuteur-temps" id="' + cibleMinuteur + '">01:00</div>' +
                        '<div style="display:flex; align-items:center; gap:6px;">' +
                            '<select class="select-minuteur" id="' + selectMinuteur + '" data-minuteur-cible="' + cibleMinuteur + '" aria-label="Durée du repos avant le bloc ' + (bIdx + 2) + '">' +
                                '<option value="45">45 s</option><option value="60" selected>60 s</option>' +
                                '<option value="75">75 s</option><option value="90">90 s</option>' +
                            '</select>' +
                            '<button class="btn btn-timer-start" data-sec="60" data-minuteur-cible="' + cibleMinuteur + '" style="width:auto;padding:0 12px;">▶ Démarrer</button>' +
                        '</div>' +
                    '</div>' +
                '</div>';
            }
        });

        html += '<div class="titre">Fin de séance</div>' +
            '<div class="card tight">' +
                '<div class="grille g2">' +
                    '<div class="champ"><label>Durée réelle (min)</label><input type="number" id="dureeSeance" min="1" max="240" value="30" /></div>' +
                    '<div class="champ"><label>Ressenti</label><select id="ressentiSeance">' +
                        '<option value="facile">Facile</option>' +
                        '<option value="normal" selected>Normal</option>' +
                        '<option value="difficile">Difficile</option>' +
                    '</select></div>' +
                '</div>' +
                '<div class="st" style="margin-top:8px;">Facile : difficulté +1 cran la prochaine fois pour cette séance. Normal : on garde le niveau. Difficile : −1 cran. Les choix restent dans les niveaux disponibles pour chaque exercice.</div>' +
            '</div>' +
            '<button class="btn btn-hero" id="btnValiderSeance" style="margin-top:12px; margin-bottom:20px;">' +
                '✔ Enregistrer la séance terminée' +
            '</button>';

        return html;
    }

    function feuilleDetailsSeance(date, type) {
        var dateCle = String(date || '').slice(0, 10);
        var typeCle = String(type || 'A');
        var seance = Store.getSeances().find(function (s) {
            return String(s.date || s.session_date || '').slice(0, 10) === dateCle &&
                String(s.type || s.session || 'A') === typeCle;
        });
        if (!seance) { UI.toast('Cette séance n’est plus dans l’historique local.'); return; }

        var programme = typeCle === 'B' ? M.SEANCE_B : M.SEANCE_A;
        var exercices = Object.create(null), groupes = Object.create(null), ordre = [];
        programme.blocs.forEach(function (bloc) {
            bloc.exos.forEach(function (exo) {
                var id = String(exo.id);
                exercices[id] = exo;
                ordre.push(id);
            });
        });
        var series = Store.getSeries().filter(function (s) {
            return String(s.date || s.set_date || '').slice(0, 10) === dateCle &&
                String(s.type || s.session || 'A') === typeCle;
        });
        series.forEach(function (s) {
            var id = String(s.exercise || 'autre');
            if (!groupes[id]) groupes[id] = [];
            groupes[id].push(s);
            if (ordre.indexOf(id) < 0) ordre.push(id);
        });
        Object.keys(groupes).forEach(function (id) {
            groupes[id].sort(function (a, b) { return Number(a.set_no || 0) - Number(b.set_no || 0); });
        });

        var totalReps = 0;
        series.forEach(function (s) {
            if (s.reps != null && isFinite(Number(s.reps))) totalReps += Number(s.reps);
        });
        var seriesPrevues = programme.blocs.reduce(function (n, bloc) { return n + bloc.exos.length * 3; }, 0);
        var duree = seance.dureeMin == null ? (seance.duration_min == null ? '—' : seance.duration_min) : seance.dureeMin;
        var ressenti = ressentiSeance(seance);
        var retourEffort = ressenti
            ? ressenti.charAt(0).toUpperCase() + ressenti.slice(1)
            : (seance.rpe == null ? 'Non renseigné' : 'Ancien RPE ' + U.nombre(Number(seance.rpe), 0) + '/10');
        var html = '<div class="grille g2" style="margin-bottom:12px;">' +
            '<div class="mini"><div class="l">Durée réelle</div><div class="v">' + h(duree) + ' <small>min</small></div></div>' +
            '<div class="mini"><div class="l">Ressenti global</div><div class="v">' + h(retourEffort) + '</div></div>' +
            '<div class="mini"><div class="l">Séries effectuées</div><div class="v">' + series.length + ' <small>/ ' + seriesPrevues + '</small></div></div>' +
            '<div class="mini"><div class="l">Répétitions / secondes</div><div class="v">' + (series.length ? U.nombre(totalReps, 0) : '—') + '</div></div>' +
        '</div>' +
        '<div class="titre">Détail des exercices</div>' +
        '<div class="card tight">';

        if (!series.length) {
            html += '<div class="vide" style="padding:14px;">Aucune série n’a été cochée lors de cette séance. La durée et le ressenti restent disponibles ci-dessus.</div>';
        } else {
            ordre.forEach(function (id) {
                var lignes = groupes[id];
                if (!lignes || !lignes.length) return;
                var exo = exercices[id];
                var nomExercice = exo ? exo.nom : id;
                var estChrono = String(exo && exo.cible || '').toLowerCase().indexOf(' s') >= 0;
                html += '<div class="ligne" style="align-items:flex-start;">' +
                    '<div class="gr"><div class="tt">' + h(nomExercice) + '</div>' +
                    (exo && exo.cible ? '<div class="st">Objectif : ' + h(exo.cible) + '</div>' : '');
                lignes.forEach(function (s) {
                    var nombre = s.reps == null ? '—' : U.nombre(Number(s.reps), 0);
                    var unite = estChrono ? ' s' : (exo && exo.unilateral ? ' reps / jambe' : ' reps');
                    var charge = s.variant
                        ? s.variant
                        : (s.load_kg != null && isFinite(Number(s.load_kg))
                            ? U.nombre(Number(s.load_kg), 1) + ' kg'
                            : 'sans charge indiquée');
                    var detailRpe = s.rpe == null ? '' : ' · RPE ' + h(s.rpe);
                    html += '<div class="st" style="margin-top:4px;"><b>Série ' + h(s.set_no == null ? '—' : s.set_no) + '</b> · ' +
                        h(nombre + unite) + ' · ' + h(charge) + detailRpe + '</div>';
                });
                html += '</div><span class="badge mut">' + lignes.length + ' série' + (lignes.length > 1 ? 's' : '') + '</span></div>';
            });
        }
        html += '</div><button class="btn btn-flat btn-fermer" style="margin-top:10px;">Fermer</button>';
        UI.feuille({
            titre: !seance.nom || seance.nom === 'Séance ' + typeCle ? programme.titre : seance.nom,
            aide: U.dateFr(dateCle, { jour: true, annee: true }) + ' · Résultats de la séance',
            html: html
        });
    }

    // =========================================================================
    // 4. MENUS & COURSES (Menus)
    // =========================================================================
    function vueMenus(ctx) {
        return EQ.menuViews.vueMenus(ctx);
    }

    // =========================================================================
    // 5. APPLICATIONS WEB STREAMLIT (Apps)
    // =========================================================================
    function vueApps(ctx) {
        var reglages = ctx.reglages;
        var courante = reglages.appCouranteWeb || 'suivi';
        var urlActive = courante === 'menus' ? reglages.urlMenus : reglages.urlSuivi;
        var labelActive = courante === 'menus' ? 'Menus & Recettes' : 'Suivi Recomposition';
        var labelAutre = courante === 'menus' ? 'Suivi Recomposition' : 'Menus & Recettes';

        var html = '';

        // Barre d'outils supérieure de la coque web
        html += '<div class="card tight app-toolbar" style="margin-bottom:8px; border-color:var(--teal); background:var(--card-2);">' +
            '<div style="display:flex; align-items:center; justify-content:space-between; gap:6px; flex-wrap:wrap;">' +
                '<div style="flex:1; min-width:180px;">' +
                    '<div class="lbl" style="color:var(--teal);">Application active</div>' +
                    '<div style="font-size:15px; font-weight:750; color:var(--txt);">' + h(labelActive) + '</div>' +
                    '<div class="st" style="font-size:11px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">' + h(urlActive) + '</div>' +
                '</div>' +
                '<div style="display:flex; gap:6px;">' +
                    '<button class="btn btn-flat" id="btnBasculeApp" style="width:auto; min-height:38px; padding:0 12px; font-size:12.5px;" title="Passer à ' + h(labelAutre) + '">' +
                        '⇄ ' + (courante === 'menus' ? 'Suivi' : 'Menus') +
                    '</button>' +
                    '<button class="iconbtn" id="btnReloadWeb" style="width:38px; height:38px;" title="Recharger la page">⟳</button>' +
                    '<button class="iconbtn" id="btnOuvrirNav" style="width:38px; height:38px;" title="Ouvrir dans le navigateur">↗</button>' +
                '</div>' +
            '</div>' +
        '</div>';

        // Cadre d'intégration WebView / Iframe plein écran
        html += '<div class="coque-web-wrapper" id="coqueWebWrapper">' +
            '<div class="chargement-frame" id="chargementFrame">' +
                '<div class="spin" style="font-size:24px; margin-bottom:8px;">⏳</div>' +
                '<div>Connexion à ' + h(labelActive) + '…</div>' +
                '<div style="font-size:11.5px; color:var(--txt-3); margin-top:4px;">Premier chargement : 10 à 25 s si Streamlit est en veille</div>' +
            '</div>' +
            '<iframe id="frameStreamlit" class="coque-frame" src="' + h(urlActive) + '" allow="clipboard-read; clipboard-write;" sandbox="allow-same-origin allow-scripts allow-forms allow-popups"></iframe>' +
        '</div>';

        return html;
    }

    // =========================================================================
    // MODALES D'ACTION (Feuilles)
    // =========================================================================

    // --- Modal : Pesée du jour (mêmes champs que le journal Suivi)
    function feuillePesee(ctx, apresEnregistrement, entree) {
        var reglages = ctx.reglages;
        var aujourdHui = U.dateIso(new Date());
        var precedent = entree || ctx.logs.find(function (x) { return x.date === aujourdHui; }) || (ctx.logs.length ? ctx.logs[ctx.logs.length - 1] : {});
        var dateInitiale = entree && entree.date ? entree.date : aujourdHui;
        var poidsInit = precedent.poids == null ? '' : precedent.poids;
        var grasKgInit = precedent.poids && precedent.masseGrassePct != null
            ? (Number(precedent.poids) * Number(precedent.masseGrassePct) / 100).toFixed(1) : '';
        var activites = ['Repos', 'Séance A', 'Séance B', 'Rugby', 'Marche', 'Musique', 'Autre'];
        var html = '<div class="grille g2">' +
            '<div class="champ"><label>Date</label><input type="date" id="inDatePesee" value="' + dateInitiale + '" max="' + aujourdHui + '" /></div>' +
            '<div class="champ"><label>Poids (kg)</label><input type="number" min="40" max="200" step="0.1" id="inPoids" placeholder="ex. 78,4" value="' + poidsInit + '" /></div>' +
            '<div class="champ"><label>Masse grasse (kg)</label><input type="number" min="2" max="90" step="0.1" id="inGrasKg" placeholder="lecture de la balance" value="' + grasKgInit + '" /></div>' +
            '<div class="champ"><label>Pas</label><input type="number" min="0" max="40000" step="250" id="inPas" value="' + (precedent.pas == null ? '' : precedent.pas) + '" placeholder="ex. 8 000" /></div>' +
            '<div class="champ"><label>Sommeil (h)</label><input type="number" min="0" max="24" step="0.5" id="inSommeil" value="' + (precedent.sommeilH == null ? '' : precedent.sommeilH) + '" placeholder="ex. 7,5" /></div>' +
            '<div class="champ"><label>Activité du jour</label><select id="inActivite">' + activites.map(function (a) {
                return '<option value="' + h(a) + '"' + (precedent.activity === a ? ' selected' : '') + '>' + h(a) + '</option>';
            }).join('') + '</select></div>' +
            '<div class="champ"><label>Énergie (1–10)</label><input type="number" min="1" max="10" step="1" id="inEnergie" value="' + (precedent.energy == null ? '' : precedent.energy) + '" placeholder="1–10" /></div>' +
        '</div>' +
        '<div class="champ"><label>Notes (faim, humeur, ressenti…)</label><textarea id="inNotesPesee" rows="3" placeholder="Facultatif">' + h(precedent.notes || '') + '</textarea></div>' +
        '<div class="st" id="lectureGras">La masse grasse en pourcentage sera calculée depuis les kilos saisis.</div>' +
        '<button class="btn btn-hero" id="btnValiderNouvellePesee">Enregistrer la journée</button>';

        UI.feuille({
            titre: 'Pesée & habitudes',
            aide: 'À jeun, à la même heure. La tendance sur 7 jours est plus utile qu’une pesée isolée.',
            html: html,
            apresRendu: function (racine, fermer) {
                function apercu() {
                    var p = U.num(UI.$('#inPoids', racine).value, null);
                    var g = U.num(UI.$('#inGrasKg', racine).value, null);
                    var sortie = UI.$('#lectureGras', racine);
                    if (!sortie) return;
                    sortie.textContent = p > 0 && g != null ? 'Masse grasse estimée : ' + (100 * g / p).toFixed(1) + ' % · masse maigre : ' + (p - g).toFixed(1) + ' kg.' : 'La masse grasse en pourcentage sera calculée depuis les kilos saisis.';
                }
                UI.$('#inPoids', racine).oninput = apercu;
                UI.$('#inGrasKg', racine).oninput = apercu;
                apercu();
                UI.$('#btnValiderNouvellePesee', racine).onclick = function () {
                    var d = UI.$('#inDatePesee', racine).value;
                    var p = U.num(UI.$('#inPoids', racine).value, null);
                    if (!d || !p || p < 40 || p > 200) { UI.toast('Indique une date et un poids valides'); return; }
                    var grasKg = U.num(UI.$('#inGrasKg', racine).value, null);
                    var bf = grasKg == null ? null : Math.round((grasKg / p) * 1000) / 10;
                    Store.saveLog({
                        date: d, poids: p, masseGrassePct: bf,
                        pas: U.num(UI.$('#inPas', racine).value, null),
                        sommeilH: U.num(UI.$('#inSommeil', racine).value, null),
                        activity: UI.$('#inActivite', racine).value,
                        energy: U.num(UI.$('#inEnergie', racine).value, null),
                        notes: UI.$('#inNotesPesee', racine).value.trim()
                    });
                    fermer();
                    UI.toast('Pesée enregistrée localement');
                    if (apresEnregistrement) apresEnregistrement();
                };
            }
        });
    }

    // --- Modal : mensurations complètes
    function feuilleMensurations(ctx, apresEnregistrement, entree) {
        var aujourdHui = U.dateIso(new Date());
        var ancien = entree || Store.getMensurations().slice(-1)[0] || {};
        var dateInitiale = entree && entree.date ? entree.date : aujourdHui;
        var html = '<div class="champ"><label>Date</label><input type="date" id="inDateMens" value="' + dateInitiale + '" max="' + aujourdHui + '" /></div>' +
            '<div class="grille g2">' +
                '<div class="champ"><label>Tour de taille · nombril (cm)</label><input type="number" min="40" max="200" step="0.1" id="inTailleCm" value="' + (ancien.tailleCm == null ? '' : ancien.tailleCm) + '" /></div>' +
                '<div class="champ"><label>Hanches (cm)</label><input type="number" min="40" max="200" step="0.1" id="inHanchesCm" value="' + (ancien.hanchesCm == null ? '' : ancien.hanchesCm) + '" /></div>' +
                '<div class="champ"><label>Poitrine (cm)</label><input type="number" min="40" max="200" step="0.1" id="inPoitrineCm" value="' + (ancien.poitrineCm == null ? '' : ancien.poitrineCm) + '" /></div>' +
                '<div class="champ"><label>Cou (cm)</label><input type="number" min="20" max="80" step="0.1" id="inCouCm" value="' + (ancien.couCm == null ? '' : ancien.couCm) + '" /></div>' +
                '<div class="champ"><label>Bras contracté (cm)</label><input type="number" min="15" max="70" step="0.1" id="inBrasCm" value="' + (ancien.brasCm == null ? '' : ancien.brasCm) + '" /></div>' +
                '<div class="champ"><label>Cuisse (cm)</label><input type="number" min="20" max="100" step="0.1" id="inCuisseCm" value="' + (ancien.cuisseCm == null ? '' : ancien.cuisseCm) + '" /></div>' +
            '</div>' +
            '<label class="check-serie" style="display:flex;gap:8px;align-items:center;margin:8px 0 12px;"><input type="checkbox" id="inPhotosMens"' + (ancien.photos ? ' checked' : '') + ' /><span class="cb-visuel">Photos face / profil / dos faites</span></label>' +
            '<div class="champ"><label>Observations</label><textarea id="inNotesMens" rows="2" placeholder="Facultatif">' + h(ancien.notes || '') + '</textarea></div>' +
            '<button class="btn btn-hero" id="btnValiderMens">Enregistrer les mensurations</button>';
        UI.feuille({
            titre: 'Mes mensurations',
            aide: 'Mesure au ruban le matin, à jeun. Les champs laissés vides restent inconnus.',
            html: html,
            apresRendu: function (racine, fermer) {
                UI.$('#btnValiderMens', racine).onclick = function () {
                    var d = UI.$('#inDateMens', racine).value;
                    if (!d) { UI.toast('Choisis une date'); return; }
                    Store.saveMensuration({
                        date: d,
                        tailleCm: U.num(UI.$('#inTailleCm', racine).value, null),
                        hanchesCm: U.num(UI.$('#inHanchesCm', racine).value, null),
                        poitrineCm: U.num(UI.$('#inPoitrineCm', racine).value, null),
                        couCm: U.num(UI.$('#inCouCm', racine).value, null),
                        brasCm: U.num(UI.$('#inBrasCm', racine).value, null),
                        cuisseCm: U.num(UI.$('#inCuisseCm', racine).value, null),
                        photos: UI.$('#inPhotosMens', racine).checked,
                        notes: UI.$('#inNotesMens', racine).value.trim()
                    });
                    fermer();
                    UI.toast('Mensurations enregistrées localement');
                    if (apresEnregistrement) apresEnregistrement();
                };
            }
        });
    }

    // --- Modal : ajouter/corriger une entrée nutrition
    function feuilleNutrition(ctx, entree, apresEnregistrement) {
        var x = entree || {};
        var date = x.date || dateNutrition || U.dateIso(new Date());
        var recettesBase = !entree && Menu ? Menu.recettes('', false) : [];
        var ingredientsBase = !entree && Menu ? Menu.ingredients('') : [];
        var htmlSource = '';
        if (!entree) {
            htmlSource = '<div class="champ"><label>Choisir dans la base</label><select id="inNutriType">' +
                '<option value="recette">Recette</option><option value="ingredient">Aliment</option><option value="libre">Saisie libre</option></select></div>' +
                '<div class="champ" id="inNutriRecipeWrap"><label>Recette de ma base</label><select id="inNutriRecipe">' +
                '<option value="">' + (recettesBase.length ? 'Choisir une recette…' : 'Aucune recette en cache') + '</option>' +
                recettesBase.map(function (r) {
                    return '<option value="' + h(r.id) + '">' + h(r.name || 'Recette') +
                        (r.base_servings ? ' · ' + h(r.base_servings) + ' parts' : '') + '</option>';
                }).join('') + '</select></div>' +
                '<div class="champ" id="inNutriIngredientWrap" style="display:none;"><label>Aliment de ma base</label><select id="inNutriIngredient">' +
                '<option value="">' + (ingredientsBase.length ? 'Choisir un aliment…' : 'Aucun aliment en cache') + '</option>' +
                ingredientsBase.map(function (i) {
                    var label = Menu.nomIngredient(i) + (i.category ? ' · ' + i.category : '');
                    return '<option value="' + h(i.id) + '">' + h(label) + '</option>';
                }).join('') + '</select></div>' +
                ((!recettesBase.length || !ingredientsBase.length)
                    ? '<div class="st" style="margin:-4px 0 10px;">Ces listes proviennent de la base Menus synchronisée sur l’appareil. Ouvre l’onglet Menus et synchronise si une liste est vide.</div>'
                    : '');
        }
        var html = '<div class="champ"><label>Date</label><input type="date" id="inNutriDate" value="' + h(date) + '" /></div>' +
            htmlSource +
            '<div class="champ"><label>Aliment ou repas</label><input id="inNutriItem" maxlength="120" value="' + h(x.item || '') + '" placeholder="Commence à taper : skyr, riz, poulet… (autocomplétion)" autocomplete="off" />' +
                '<div id="inNutriSuggestions" role="listbox" aria-label="Suggestions d’aliments et de recettes"></div></div>' +
            '<div class="champ"><label id="inNutriQtyLabel">Quantité</label>' +
                '<div style="display:flex;gap:8px;align-items:stretch;">' +
                    '<input type="number" id="inNutriQty" min="0.1" max="999.9" step="0.1" value="' + (x.qty == null ? 1 : Number(x.qty)) + '" style="flex:1;min-width:0;" />' +
                    '<select id="inNutriUnit" aria-label="Unité" style="width:132px;flex-shrink:0;"></select>' +
                '</div>' +
                '<div class="st" id="inNutriUnitInfo" style="margin-top:5px;"></div></div>' +
            '<div class="grille g2">' +
                '<div class="champ"><label>Protéines (g)</label><input type="number" id="inNutriP" min="0" max="5000" step="1" value="' + (x.protein_g || 0) + '" /></div>' +
                '<div class="champ"><label>Glucides (g)</label><input type="number" id="inNutriG" min="0" max="5000" step="1" value="' + (x.carbs_g || 0) + '" /></div>' +
                '<div class="champ"><label>Lipides (g)</label><input type="number" id="inNutriL" min="0" max="5000" step="1" value="' + (x.fat_g || 0) + '" /></div>' +
                '<div class="mini"><div class="l">Calories calculées</div><div class="v" id="inNutriKcal">' + Math.round((Number(x.protein_g || 0) + Number(x.carbs_g || 0)) * 4 + Number(x.fat_g || 0) * 9) + ' <small>kcal</small></div></div>' +
            '</div>' +
            '<button class="btn btn-hero" id="btnValiderNutrition">' + (entree ? 'Enregistrer les corrections' : 'Ajouter au journal') + '</button>';
        UI.feuille({
            titre: entree ? 'Corriger une entrée' : 'Ajouter au journal nutrition',
            aide: 'Choisis une recette ou un aliment de la base Menus : les macros sont reprises automatiquement. Les calories sont calculées depuis les macros.',
            html: html,
            apresRendu: function (racine, fermer) {
                var itemInput = UI.$('#inNutriItem', racine);
                var qtyInput = UI.$('#inNutriQty', racine);
                var qtyLabel = UI.$('#inNutriQtyLabel', racine);
                var inputP = UI.$('#inNutriP', racine), inputG = UI.$('#inNutriG', racine), inputL = UI.$('#inNutriL', racine);
                var uniteInput = UI.$('#inNutriUnit', racine);
                var uniteInfo = UI.$('#inNutriUnitInfo', racine);
                var baseMacros = null;
                // baseUnite dit ce que représente baseMacros : 'g' (macros par
                // gramme) ou 'part' (macros par portion, quand le poids d'une
                // part est inconnu).
                var baseUnite = 'g';
                var ingCourant = null;   // aliment choisi, sert aux conversions
                var poidsParPart = 0;    // grammes d'une part de recette, si connu

                /** Grammes correspondant à `qte` exprimée dans `unite`. */
                function grammesPour(qte, unite) {
                    if (!Menu) return null;
                    if (baseUnite === 'part') {
                        if (unite === 'part') return qte * poidsParPart;
                        if (unite === 'g') return qte;
                        return null;
                    }
                    var parUnite = Menu.poidsUnite(ingCourant, unite);
                    return parUnite > 0 ? qte * parUnite : null;
                }

                function remplirUnites(liste, defaut) {
                    if (!uniteInput) return;
                    var choix = (liste && liste.length) ? liste : (Menu ? Menu.UNITES : ['g']);
                    uniteInput.innerHTML = choix.map(function (u) {
                        return '<option value="' + h(u) + '">' + h(u) + '</option>';
                    }).join('');
                    var voulu = defaut && choix.indexOf(defaut) >= 0 ? defaut : choix[0];
                    uniteInput.value = voulu;
                }

                function calc() {
                    var p = U.num(inputP.value, 0);
                    var g = U.num(inputG.value, 0);
                    var l = U.num(inputL.value, 0);
                    UI.$('#inNutriKcal', racine).innerHTML = Math.round((p + g) * 4 + l * 9) + ' <small>kcal</small>';
                }
                function remplirMacros() {
                    if (!baseMacros) {
                        if (uniteInfo) uniteInfo.textContent = '';
                        calc();
                        return;
                    }
                    var q = Math.max(0, U.num(qtyInput.value, 1));
                    var unite = uniteInput ? uniteInput.value : 'g';
                    var grammes = grammesPour(q, unite);
                    if (grammes == null) {
                        // Unité sans équivalent en poids pour cet aliment : on
                        // n'invente pas de valeur, on le dit.
                        inputP.value = 0; inputG.value = 0; inputL.value = 0;
                        if (uniteInfo) uniteInfo.textContent =
                            'Impossible de convertir « ' + unite + ' » en poids pour cet aliment. ' +
                            'Renseigne son poids par pièce, ou choisis une autre unité.';
                        calc();
                        return;
                    }
                    if (uniteInfo) {
                        uniteInfo.textContent = baseUnite === 'part' && unite === 'part'
                            ? Math.round(grammes) + ' g au total'
                            : 'soit ' + Math.round(grammes) + ' g';
                    }
                    // baseMacros est toujours ramené au gramme.
                    var parGramme = baseUnite === 'part' && poidsParPart > 0
                        ? { p: baseMacros.p / poidsParPart, g: baseMacros.g / poidsParPart, l: baseMacros.l / poidsParPart }
                        : baseMacros;
                    inputP.value = Math.round(parGramme.p * grammes * 10) / 10;
                    inputG.value = Math.round(parGramme.g * grammes * 10) / 10;
                    inputL.value = Math.round(parGramme.l * grammes * 10) / 10;
                    calc();
                }
                function effacerValeursSource() {
                    baseMacros = null;
                    itemInput.value = '';
                    inputP.value = 0; inputG.value = 0; inputL.value = 0;
                    calc();
                }
                function appliquerRecette(recette) {
                    qtyLabel.textContent = 'Quantité';
                    ingCourant = null;
                    baseUnite = 'part';
                    poidsParPart = 0;
                    qtyInput.min = '0.1'; qtyInput.max = '20'; qtyInput.step = '0.5';
                    if (!recette) {
                        qtyInput.value = '1';
                        remplirUnites(['part'], 'part');
                        effacerValeursSource();
                        return;
                    }
                    var valeurs = Menu.calculerRecette(recette.id);
                    if (!valeurs) { UI.toast('Impossible de calculer cette recette'); return; }
                    itemInput.value = recette.name || 'Recette';
                    qtyInput.value = '1';
                    baseMacros = { p: valeurs.par_part.proteines, g: valeurs.par_part.glucides, l: valeurs.par_part.lipides };
                    var parts = Number(valeurs.parts) || 0;
                    poidsParPart = parts > 0 ? Number(valeurs.poids_g || 0) / parts : 0;
                    remplirUnites(poidsParPart > 0 ? ['part', 'g'] : ['part'], 'part');
                    remplirMacros();
                    if (valeurs.inconnues && valeurs.inconnues.length) {
                        UI.toast('Certaines valeurs d’ingrédients de cette recette manquent dans la base.');
                    }
                }
                function appliquerIngredient(ing) {
                    qtyLabel.textContent = 'Quantité';
                    baseUnite = 'g';
                    poidsParPart = 0;
                    qtyInput.min = '0.1'; qtyInput.max = '999.9'; qtyInput.step = '5';
                    if (!ing) {
                        ingCourant = null;
                        qtyInput.value = '100';
                        remplirUnites(Menu ? Menu.UNITES : ['g'], 'g');
                        effacerValeursSource();
                        return;
                    }
                    ingCourant = ing;
                    itemInput.value = Menu.nomIngredient(ing);
                    // « convives » n'a pas de sens pour une prise personnelle.
                    var unites = Menu.unitesProposees(ing).filter(function (u) { return u !== 'convives'; });
                    remplirUnites(unites, Menu.uniteParDefaut(ing));
                    var parUnite = Menu.poidsUnite(ing, uniteInput ? uniteInput.value : 'g');
                    qtyInput.value = parUnite > 0 ? String(Math.round(100 / parUnite * 10) / 10) : '100';
                    baseMacros = {
                        p: Number(ing.proteines_100g || 0) / 100,
                        g: Number(ing.glucides_100g || 0) / 100,
                        l: Number(ing.lipides_100g || 0) / 100
                    };
                    remplirMacros();
                    if (ing.proteines_100g == null && ing.glucides_100g == null && ing.lipides_100g == null) {
                        UI.toast('Les macros ne sont pas renseignées pour cet aliment dans la base.');
                    }
                }
                function choisirRecette() {
                    var select = UI.$('#inNutriRecipe', racine);
                    appliquerRecette(recettesBase.find(function (r) {
                        return String(r.id) === String(select && select.value || '');
                    }));
                }
                function choisirIngredient() {
                    var select = UI.$('#inNutriIngredient', racine);
                    appliquerIngredient(ingredientsBase.find(function (i) {
                        return String(i.id) === String(select && select.value || '');
                    }));
                }

                // Autocomplétion : proposer recettes et aliments dès la 2e lettre.
                var sugg = [];
                function rendreSuggestions() {
                    var box = UI.$('#inNutriSuggestions', racine);
                    if (!box) return;
                    if (!sugg.length) { box.innerHTML = ''; return; }
                    box.innerHTML = sugg.map(function (s2, i) {
                        return '<button type="button" class="btn btn-flat" data-sugg="' + i + '" ' +
                            'style="display:block;width:100%;text-align:left;margin-top:5px;">' +
                            (s2.type === 'recette' ? '📖 ' : '🥗 ') + h(s2.label) +
                            ' <span class="st" style="float:right;">' + (s2.type === 'recette' ? 'recette' : 'aliment') + '</span></button>';
                    }).join('');
                    UI.$$('[data-sugg]', box).forEach(function (btn) {
                        btn.onclick = function () {
                            var choix = sugg[Number(btn.getAttribute('data-sugg'))];
                            if (!choix) return;
                            if (choix.type === 'recette') appliquerRecette(choix.obj);
                            else appliquerIngredient(choix.obj);
                            sugg = [];
                            rendreSuggestions();
                        };
                    });
                }
                function suggerer() {
                    var box = UI.$('#inNutriSuggestions', racine);
                    if (!box || !Menu) return;
                    var q = String(itemInput.value || '').trim();
                    if (q.length < 2) { sugg = []; rendreSuggestions(); return; }
                    sugg = Menu.recettes(q, false).slice(0, 5).map(function (r) {
                        return { type: 'recette', obj: r, label: r.name || 'Recette' };
                    }).concat(Menu.ingredients(q).slice(0, 5).map(function (i) {
                        return { type: 'aliment', obj: i, label: Menu.nomIngredient(i) };
                    }));
                    rendreSuggestions();
                }
                if (itemInput) itemInput.oninput = suggerer;

                if (!entree) {
                    var typeSelect = UI.$('#inNutriType', racine);
                    var recipeWrap = UI.$('#inNutriRecipeWrap', racine);
                    var ingredientWrap = UI.$('#inNutriIngredientWrap', racine);
                    var recipeSelect = UI.$('#inNutriRecipe', racine);
                    var ingredientSelect = UI.$('#inNutriIngredient', racine);
                    if (typeSelect) typeSelect.onchange = function () {
                        var type = typeSelect.value;
                        recipeWrap.style.display = type === 'recette' ? '' : 'none';
                        ingredientWrap.style.display = type === 'ingredient' ? '' : 'none';
                        baseMacros = null;
                        if (type === 'recette') choisirRecette();
                        else if (type === 'ingredient') choisirIngredient();
                        else {
                            itemInput.value = '';
                            qtyLabel.textContent = 'Quantité';
                            ingCourant = null;
                            baseUnite = 'g';
                            poidsParPart = 0;
                            qtyInput.min = '0.1'; qtyInput.max = '999.9'; qtyInput.step = '0.1'; qtyInput.value = '1';
                            remplirUnites(Menu ? Menu.UNITES : ['g'], 'g');
                            inputP.value = 0; inputG.value = 0; inputL.value = 0; calc();
                        }
                    };
                    if (recipeSelect) recipeSelect.onchange = choisirRecette;
                    if (ingredientSelect) ingredientSelect.onchange = choisirIngredient;
                }
                qtyInput.oninput = remplirMacros;
                if (uniteInput) uniteInput.onchange = remplirMacros;
                if (entree) {
                    // Correction d'une entrée : on retrouve l'unité enregistrée,
                    // sans source en base puisque les listes ne sont pas chargées.
                    baseUnite = 'g';
                    ingCourant = null;
                    poidsParPart = 0;
                    qtyLabel.textContent = 'Quantité';
                    remplirUnites(Menu ? Menu.UNITES : ['g'], x.unite || 'g');
                }
                [inputP, inputG, inputL].forEach(function (input) { input.oninput = calc; });
                var valider = UI.$('#btnValiderNutrition', racine);
                valider.onclick = function () {
                    var nom = itemInput.value.trim();
                    var jour = UI.$('#inNutriDate', racine).value;
                    if (!nom || !jour) { UI.toast('Indique un aliment et une date'); return; }
                    var payload = {
                        date: jour, item: nom,
                        qty: U.num(qtyInput.value, 1),
                        unite: (uniteInput && uniteInput.value) || '',
                        protein_g: Math.round(U.num(inputP.value, 0)),
                        carbs_g: Math.round(U.num(inputG.value, 0)),
                        fat_g: Math.round(U.num(inputL.value, 0))
                    };
                    if (entree) Store.updateNutrition(entree.id || entree.local_id, payload);
                    else Store.addNutrition(payload);
                    dateNutrition = jour;
                    fermer();
                    UI.toast('Entrée nutrition enregistrée sur ce téléphone');
                    if (apresEnregistrement) apresEnregistrement();
                };
            }
        });
    }

    // --- Modal : Voir recette & ajuster convives
    function feuilleRecette(recetteId) {
        var r = M.RECETTES_EXEMPLES.find(function (x) { return x.id === recetteId; });
        if (!r) return;

        var nbConvives = r.convives;

        function renderCorps(c) {
            var ratio = c / r.convives;
            var html = '<div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:14px; background:var(--card); padding:10px 14px; border-radius:14px; border:1px solid var(--line);">' +
                '<span style="font-weight:700;">Nombre de convives :</span>' +
                '<div style="display:flex; align-items:center; gap:10px;">' +
                    '<button class="iconbtn" id="btnMoinsConvives" style="width:34px;height:34px;">−</button>' +
                    '<span style="font-size:18px; font-weight:800; min-width:24px; text-align:center;">' + c + '</span>' +
                    '<button class="iconbtn" id="btnPlusConvives" style="width:34px;height:34px;">＋</button>' +
                '</div>' +
            '</div>' +
            '<div class="lbl" style="margin-bottom:8px;">Ingrédients pour ' + c + ' personne' + (c > 1 ? 's' : '') + ' :</div>' +
            '<ul style="margin:0 0 16px; padding-left:18px; color:var(--txt-2); font-size:13.5px; line-height:1.6;">' +
                r.ingredients.map(function (ing) {
                    return '<li><b>' + h(ing.nom) + '</b> : ' + h(ing.qte) + '</li>';
                }).join('') +
            '</ul>' +
            '<div class="lbl" style="margin-bottom:8px;">Étapes de préparation :</div>' +
            '<ol style="margin:0 0 16px; padding-left:18px; color:var(--txt); font-size:13.5px; line-height:1.6;">' +
                r.etapes.map(function (etape) {
                    return '<li style="margin-bottom:6px;">' + h(etape) + '</li>';
                }).join('') +
            '</ol>';
            return html;
        }

        var instance = UI.feuille({
            titre: r.nom,
            aide: r.temps + ' · ' + r.protPortion + ' g protéines par portion · ' + r.kcalPortion + ' kcal',
            html: '<div id="zoneRecette">' + renderCorps(nbConvives) + '</div>',
            apresRendu: function (racine) {
                function attacherEvents() {
                    var bMoins = UI.$('#btnMoinsConvives', racine);
                    var bPlus = UI.$('#btnPlusConvives', racine);
                    if (bMoins) {
                        bMoins.onclick = function () {
                            if (nbConvives > 1) {
                                nbConvives--;
                                UI.$('#zoneRecette', racine).innerHTML = renderCorps(nbConvives);
                                attacherEvents();
                            }
                        };
                    }
                    if (bPlus) {
                        bPlus.onclick = function () {
                            if (nbConvives < 12) {
                                nbConvives++;
                                UI.$('#zoneRecette', racine).innerHTML = renderCorps(nbConvives);
                                attacherEvents();
                            }
                        };
                    }
                }
                attacherEvents();
            }
        });
    }

    // --- Modal : Réglages, profil et synchronisation
    function feuilleReglages(ctx, apresSauvegarde) {
        var r = ctx.reglages;
        var p = Store.getProfil();
        var sess = Store.getRemoteSession();
        var connecte = !!(sess && sess.user && sess.user.email);
        var statut = connecte
            ? '<div class="badge ok" id="supaConnectionStatus">Connecté : ' + h(sess.user.email) + '</div>'
            : '<div class="badge mut" id="supaConnectionStatus">Mode hors ligne · non connecté</div>';
        var html = '<div class="titre">Profil & objectifs</div>' +
            '<div class="champ"><label>Prénom</label><input id="profilNom" value="' + h(p.displayName || '') + '" placeholder="Ton prénom" /></div>' +
            '<div class="grille g2">' +
                '<div class="champ"><label>Taille (cm)</label><input type="number" step="0.5" id="profilTaille" value="' + (p.tailleCm || 185) + '" /></div>' +
                '<div class="champ"><label>Poids de départ (kg)</label><input type="number" step="0.1" id="profilDepart" value="' + (p.poidsDepartKg || 85) + '" /></div>' +
                '<div class="champ"><label>Poids cible (kg)</label><input type="number" step="0.1" id="regPoidsCible" value="' + (p.poidsCibleKg || r.poidsCibleKg || 77) + '" /></div>' +
                '<div class="champ"><label>Protéines / jour (g)</label><input type="number" id="regProtCible" value="' + (p.objectifProteinesG || r.objectifProteinesG || 130) + '" /></div>' +
                '<div class="champ"><label>Calories / jour (kcal)</label><input type="number" id="regKcalCible" value="' + (p.objectifCaloriesKcal || r.objectifCaloriesKcal || 1700) + '" /></div>' +
                '<div class="champ"><label>Glucides / jour (g)</label><input type="number" id="profilGlucides" value="' + (p.objectifGlucidesG || r.objectifGlucidesG || 140) + '" /></div>' +
                '<div class="champ"><label>Lipides / jour (g)</label><input type="number" id="profilLipides" value="' + (p.objectifLipidesG || r.objectifLipidesG || 50) + '" /></div>' +
                '<div class="champ"><label>Dépense estimée (kcal)</label><input type="number" id="profilTdee" value="' + (p.tdeeKcal || r.tdeeKcal || 2400) + '" /></div>' +
            '</div>' +
            '<button class="btn btn-flat" id="btnSauverProfil">Enregistrer le profil</button>' +
            '<div class="titre" style="margin-top:18px;">Synchronisation hors ligne + Supabase</div>' +
            '<div class="card tight" style="margin-bottom:10px;">' + statut +
                '<div class="st" id="syncPendingCount" style="margin-top:8px;">' + Store.syncCount() + ' modification(s) locale(s) en attente. Les saisies restent sur ce téléphone hors ligne.</div>' +
            '</div>' +
            '<div class="champ"><label>URL du projet Supabase</label><input type="url" id="regSupaUrl" value="' + h(r.supabaseUrl || '') + '" placeholder="https://xxxx.supabase.co" /></div>' +
            '<div class="champ"><label>Clé publique (publishable / anon uniquement)</label><input type="password" id="regSupaKey" value="' + h(r.supabaseKey || '') + '" placeholder="sb_publishable_… ou anon public" autocomplete="off" /></div>' +
            '<div class="st" style="margin:-4px 0 12px;">Ne colle jamais une clé <b>secret</b> ou <b>service_role</b> ici. La clé publique fonctionne avec ton compte et les règles RLS.</div>' +
            '<div class="champ" style="margin-top:14px;"><label>URL du Worker Coach IA (Cloudflare)</label><input type="url" id="regCoachUrl" value="' + h(r.coachApiUrl || '') + '" placeholder="https://equilibre-coach-ia.…workers.dev" autocapitalize="off" /></div>' +
            '<div class="st" style="margin:-4px 0 12px;">Cette adresse est publique. Les clés Cloudflare et Tavily restent côté Worker et ne doivent jamais être collées dans l’application.</div>' +
            '<button class="btn btn-flat" id="btnSauverReglages">Enregistrer Supabase et Coach IA</button>' +
            '<div class="titre" style="margin-top:18px;">Sécurité</div>' +
            '<div class="card tight" style="display:flex;align-items:center;justify-content:space-between;gap:12px;">' +
                '<div><div class="lbl">Ouvrir avec mon empreinte</div>' +
                '<div class="st" id="empreinteInfo">Vérification du capteur…</div></div>' +
                '<input type="checkbox" id="regEmpreinte"' + (r.empreinteActive ? ' checked' : '') +
                    ' style="width:22px;height:22px;flex-shrink:0;" />' +
            '</div>' +
            (connecte
                ? '<div class="champ" style="margin-top:12px;"><label>Compte Supabase</label><input value="' + h(sess.user.email) + '" readonly /></div>' +
                  '<div id="syncMessage" class="auth-message" role="status" aria-live="polite"></div>' +
                  '<div class="grille g2"><button class="btn btn-hero" id="btnSyncMaintenant">Synchroniser maintenant</button><button class="btn btn-flat" id="btnDeconnexion">Se déconnecter</button></div>'
                : '<div class="champ" style="margin-top:12px;"><label>E-mail Supabase</label><input type="email" id="authEmail" autocomplete="username" placeholder="toi@exemple.ch" /></div>' +
                  '<div class="champ"><label>Mot de passe Supabase</label><input type="password" id="authPassword" autocomplete="current-password" placeholder="Saisi sur cet appareil, non enregistré" /></div>' +
                  '<div id="authMessage" class="auth-message" role="alert" aria-live="polite"></div>' +
                  '<button class="btn btn-hero" id="btnConnexionSupabase">Se connecter et synchroniser</button>' +
                  '<button class="btn btn-flat" id="btnRetryAuthSync" style="display:none; margin-top:8px;">Réessayer la synchronisation</button>') +
            '<div class="titre" style="margin-top:18px;">Liens web de secours (facultatif)</div>' +
            '<div class="champ"><label>Adresse Suivi Streamlit</label><input type="url" id="regUrlSuivi" value="' + h(r.urlSuivi) + '" placeholder="https://…streamlit.app" /></div>' +
            '<div class="champ"><label>Adresse Menus & recettes Streamlit</label><input type="url" id="regUrlMenus" value="' + h(r.urlMenus) + '" placeholder="https://…streamlit.app" /></div>' +
            '<button class="btn btn-flat" id="btnSauverLiens">Enregistrer les liens</button>' +
            '<div style="margin-top:18px; padding-top:14px; border-top:1px solid var(--line); text-align:center;">' +
                '<button class="btn btn-flat" id="btnResetDemo" style="min-height:38px; font-size:12.5px; color:var(--txt-3);">Effacer les données locales</button>' +
                '<div style="font-size:11.5px; color:var(--txt-3); margin-top:10px;">Les données synchronisées dans Supabase ne sont pas supprimées.</div>' +
            '</div>';

        UI.feuille({
            titre: 'Réglages & données',
            aide: 'L’app fonctionne hors ligne. La connexion Supabase est facultative pour l’usage local et sert à synchroniser tes données.',
            html: html,
            apresRendu: function (racine, fermer) {
                var profileBtn = UI.$('#btnSauverProfil', racine);
                if (profileBtn) profileBtn.onclick = function () {
                    var nouveau = {
                        displayName: UI.$('#profilNom', racine).value.trim(),
                        tailleCm: U.num(UI.$('#profilTaille', racine).value, 185),
                        poidsDepartKg: U.num(UI.$('#profilDepart', racine).value, 85),
                        poidsCibleKg: U.num(UI.$('#regPoidsCible', racine).value, 77),
                        objectifProteinesG: Math.round(U.num(UI.$('#regProtCible', racine).value, 130)),
                        objectifCaloriesKcal: Math.round(U.num(UI.$('#regKcalCible', racine).value, 1700)),
                        objectifGlucidesG: Math.round(U.num(UI.$('#profilGlucides', racine).value, 140)),
                        objectifLipidesG: Math.round(U.num(UI.$('#profilLipides', racine).value, 50)),
                        tdeeKcal: Math.round(U.num(UI.$('#profilTdee', racine).value, 2400))
                    };
                    Store.saveProfil(nouveau);
                    var reglages = Object.assign({}, Store.getReglages(), nouveau);
                    Store.saveReglages(reglages);
                    UI.toast('Profil enregistré sur cet appareil');
                    if (apresSauvegarde) apresSauvegarde(reglages);
                };

                var configBtn = UI.$('#btnSauverReglages', racine);
                if (configBtn) configBtn.onclick = function () {
                    var nouv = Object.assign({}, Store.getReglages(), {
                        supabaseUrl: UI.$('#regSupaUrl', racine).value.trim().replace(/\/+$/, ''),
                        supabaseKey: UI.$('#regSupaKey', racine).value.trim(),
                        coachApiUrl: (UI.$('#regCoachUrl', racine).value || '').trim().replace(/\/+$/, '')
                    });
                    Store.saveReglages(nouv);
                    UI.toast('Configuration Supabase et Coach IA enregistrée');
                };

                // Empreinte : l'interrupteur n'a de sens que si l'appareil expose
                // un capteur biométrique et un verrouillage d'écran.
                var empreinteBox = UI.$('#regEmpreinte', racine);
                var empreinteInfo = UI.$('#empreinteInfo', racine);
                if (empreinteBox && empreinteInfo) {
                    var dispo = (typeof Native !== 'undefined' && Native && Native.biometrieDisponible)
                        ? Native.biometrieDisponible() : false;
                    empreinteInfo.textContent = dispo
                        ? 'Ton empreinte sera demandée à chaque ouverture de l’application.'
                        : 'Indisponible sur cet appareil (capteur ou verrouillage d’écran absent).';
                    empreinteBox.disabled = !dispo;
                    if (!dispo) empreinteBox.checked = false;
                    empreinteBox.onchange = function () {
                        var nouv2 = Object.assign({}, Store.getReglages(), {
                            empreinteActive: dispo && empreinteBox.checked
                        });
                        Store.saveReglages(nouv2);
                        UI.toast(empreinteBox.checked
                            ? 'Empreinte activée : elle sera demandée à l’ouverture'
                            : 'Empreinte désactivée');
                    };
                }

                var liensBtn = UI.$('#btnSauverLiens', racine);
                if (liensBtn) liensBtn.onclick = function () {
                    var nouv = Object.assign({}, Store.getReglages(), {
                        urlSuivi: UI.$('#regUrlSuivi', racine).value.trim(),
                        urlMenus: UI.$('#regUrlMenus', racine).value.trim()
                    });
                    Store.saveReglages(nouv);
                    UI.toast('Liens enregistrés');
                };

                var loginBtn = UI.$('#btnConnexionSupabase', racine);
                var retryAuthSyncBtn = UI.$('#btnRetryAuthSync', racine);
                var authMessage = UI.$('#authMessage', racine);
                var syncMessage = UI.$('#syncMessage', racine);
                var statusNode = UI.$('#supaConnectionStatus', racine);
                var pendingNode = UI.$('#syncPendingCount', racine);

                function afficherMessageAuth(noeud, message, estInfo) {
                    if (!noeud) return;
                    noeud.textContent = message || '';
                    noeud.className = 'auth-message' + (message ? ' visible' : '') + (estInfo ? ' info' : '');
                }
                function obtenirErreursSync(resultat) {
                    var erreurs = resultat && Array.isArray(resultat.erreurs) ? resultat.erreurs.slice() : [];
                    if (!erreurs.length && resultat && resultat.synchronise === false && resultat.raison) {
                        erreurs.push(resultat.raison);
                    }
                    return erreurs;
                }
                function afficherErreursSync(noeud, resultat, prefixe) {
                    var erreurs = obtenirErreursSync(resultat);
                    if (!noeud) return erreurs.length > 0;
                    if (!erreurs.length) {
                        afficherMessageAuth(noeud, '', false);
                        return false;
                    }
                    var lignes = erreurs.slice(0, 8).map(function (e) {
                        return '• ' + String(e).slice(0, 350);
                    });
                    if (erreurs.length > 8) lignes.push('… et ' + (erreurs.length - 8) + ' autre(s) erreur(s).');
                    noeud.textContent = prefixe + ' ' + erreurs.length + ' erreur(s). Les données restent enregistrées sur cet appareil.\n\n' + lignes.join('\n');
                    noeud.className = 'auth-message visible';
                    return true;
                }
                function actualiserAttente(resultat) {
                    if (!pendingNode) return;
                    var nombre = resultat && typeof resultat.enAttente === 'number'
                        ? resultat.enAttente : Store.syncCount();
                    pendingNode.textContent = nombre + ' modification(s) locale(s) en attente. Les saisies restent sur cet appareil jusqu’à leur synchronisation.';
                }
                function marquerConnecte(email) {
                    if (!statusNode) return;
                    statusNode.className = 'badge ok';
                    statusNode.textContent = 'Connecté : ' + (email || 'compte Supabase');
                }
                function detailErreur(e) {
                    var detail = e && e.message ? e.message : 'Erreur inattendue.';
                    if (e && e.status > 0) detail += ' (HTTP ' + e.status + ')';
                    return detail;
                }
                function afficherBoutonReessai() {
                    if (loginBtn) { loginBtn.disabled = true; loginBtn.style.display = 'none'; }
                    if (retryAuthSyncBtn) {
                        retryAuthSyncBtn.style.display = 'inline-flex';
                        retryAuthSyncBtn.disabled = false;
                        retryAuthSyncBtn.textContent = 'Réessayer la synchronisation';
                    }
                }

                if (loginBtn) loginBtn.onclick = function () {
                    var email = UI.$('#authEmail', racine).value.trim();
                    var password = UI.$('#authPassword', racine).value;
                    if (!email || !password) {
                        afficherMessageAuth(authMessage, 'Saisis ton e-mail et ton mot de passe Supabase.', false);
                        UI.toast('Saisis ton e-mail et ton mot de passe Supabase');
                        return;
                    }
                    var authentifie = false;
                    afficherMessageAuth(authMessage, 'Connexion à Supabase en cours…', true);
                    loginBtn.disabled = true;
                    loginBtn.textContent = 'Connexion…';
                    Store.saveReglages(Object.assign({}, Store.getReglages(), {
                        supabaseUrl: UI.$('#regSupaUrl', racine).value.trim().replace(/\/+$/, ''),
                        supabaseKey: UI.$('#regSupaKey', racine).value.trim()
                    }));
                    Net.connexion(email, password).then(function (compte) {
                        authentifie = true;
                        marquerConnecte(compte && compte.email || email);
                        UI.$('#authPassword', racine).value = '';
                        loginBtn.textContent = 'Synchronisation…';
                        afficherMessageAuth(authMessage, 'Connexion établie. Synchronisation en cours…', true);
                        return Net.synchroniser();
                    }).then(function (resultat) {
                        actualiserAttente(resultat);
                        if (afficherErreursSync(authMessage, resultat, 'Connexion établie, mais la synchronisation est partielle.')) {
                            afficherBoutonReessai();
                            UI.toast('Connecté; certaines données restent à synchroniser');
                            if (apresSauvegarde) apresSauvegarde(Store.getReglages());
                            return;
                        }
                        UI.toast('Connecté et synchronisé');
                        fermer();
                        if (apresSauvegarde) apresSauvegarde(Store.getReglages());
                    }).catch(function (e) {
                        var detail = detailErreur(e);
                        if (authentifie) {
                            var session = Store.getRemoteSession();
                            marquerConnecte(session && session.user && session.user.email || email);
                            afficherBoutonReessai();
                            afficherMessageAuth(authMessage,
                                'Connexion établie, mais la synchronisation a échoué :\n' + detail + '\nLes données locales sont conservées.', false);
                            UI.toast('Connecté; synchronisation en échec');
                        } else {
                            loginBtn.disabled = false;
                            loginBtn.textContent = 'Se connecter et synchroniser';
                            afficherMessageAuth(authMessage, 'Connexion impossible : ' + detail, false);
                            UI.toast('Connexion impossible : ' + detail);
                        }
                    });
                };

                if (retryAuthSyncBtn) retryAuthSyncBtn.onclick = function () {
                    retryAuthSyncBtn.disabled = true;
                    retryAuthSyncBtn.textContent = 'Synchronisation…';
                    afficherMessageAuth(authMessage, 'Compte connecté. Nouvelle tentative de synchronisation…', true);
                    Net.synchroniser().then(function (resultat) {
                        actualiserAttente(resultat);
                        if (afficherErreursSync(authMessage, resultat, 'Compte connecté, mais la synchronisation reste partielle.')) {
                            retryAuthSyncBtn.disabled = false;
                            retryAuthSyncBtn.textContent = 'Réessayer la synchronisation';
                            UI.toast('Des données restent à synchroniser');
                            if (apresSauvegarde) apresSauvegarde(Store.getReglages());
                            return;
                        }
                        afficherMessageAuth(authMessage, 'Toutes les données sont synchronisées.', true);
                        UI.toast('Synchronisation terminée');
                        fermer();
                        if (apresSauvegarde) apresSauvegarde(Store.getReglages());
                    }).catch(function (e) {
                        retryAuthSyncBtn.disabled = false;
                        retryAuthSyncBtn.textContent = 'Réessayer la synchronisation';
                        afficherMessageAuth(authMessage,
                            'Compte connecté, mais la synchronisation a échoué :\n' + detailErreur(e) + '\nLes données locales sont conservées.', false);
                        UI.toast('Synchronisation en échec');
                    });
                };

                var syncBtn = UI.$('#btnSyncMaintenant', racine);
                if (syncBtn) syncBtn.onclick = function () {
                    syncBtn.disabled = true;
                    syncBtn.textContent = 'Synchronisation…';
                    afficherMessageAuth(syncMessage, 'Synchronisation en cours…', true);
                    Net.synchroniser().then(function (resultat) {
                        syncBtn.disabled = false;
                        syncBtn.textContent = 'Synchroniser maintenant';
                        actualiserAttente(resultat);
                        if (afficherErreursSync(syncMessage, resultat, 'Compte connecté, mais la synchronisation est partielle.')) {
                            UI.toast('Des données restent à synchroniser');
                        } else {
                            afficherMessageAuth(syncMessage, 'Synchronisation terminée : ' + (resultat.recu || 0) + ' ligne(s) reçue(s).', true);
                            UI.toast('Synchronisé · ' + (resultat.recu || 0) + ' lignes reçues');
                        }
                        if (apresSauvegarde) apresSauvegarde(Store.getReglages());
                    }).catch(function (e) {
                        syncBtn.disabled = false;
                        syncBtn.textContent = 'Synchroniser maintenant';
                        afficherMessageAuth(syncMessage,
                            'Compte connecté, mais la synchronisation a échoué :\n' + detailErreur(e) + '\nLes données locales sont conservées.', false);
                        UI.toast('Synchronisation en échec');
                    });
                };

                var logoutBtn = UI.$('#btnDeconnexion', racine);
                if (logoutBtn) logoutBtn.onclick = function () {
                    Net.deconnexion().then(function () {
                        fermer(); UI.toast('Déconnecté · les données locales sont conservées');
                        if (apresSauvegarde) apresSauvegarde(Store.getReglages());
                    });
                };

                var btnReset = UI.$('#btnResetDemo', racine);
                if (btnReset) btnReset.onclick = function () {
                    if (confirm('Effacer les données locales, y compris les changements encore en attente de synchronisation ? Les données Supabase ne seront pas touchées.')) {
                        Store.reinitialiserDemo();
                        fermer();
                        UI.toast('Données locales effacées');
                        if (apresSauvegarde) apresSauvegarde(Store.getReglages());
                    }
                };
            }
        });
    }

    // Gestion du chronomètre de repos (une seule horloge active à la fois)
    function demarrerMinuteur(secondes, selecteurAffichage) {
        clearInterval(minuteurTimer);
        secondes = Math.max(1, parseInt(secondes, 10) || 60);
        minuteurTotal = secondes;
        minuteurRestant = secondes;
        UI.haptic(20);

        function maj() {
            var aff = UI.$(selecteurAffichage || '#minuteurAffichage');
            if (!aff) return;
            var m = Math.floor(minuteurRestant / 60);
            var s = minuteurRestant % 60;
            aff.textContent = (m < 10 ? '0' : '') + m + ':' + (s < 10 ? '0' : '') + s;
        }

        maj();
        minuteurTimer = setInterval(function () {
            minuteurRestant--;
            maj();
            if (minuteurRestant <= 0) {
                clearInterval(minuteurTimer);
                UI.haptic(80);
                UI.toast('⏰ Temps de repos terminé ! Reprenez votre série.');
            }
        }, 1000);
    }

    EQ.views = {
        vueBord: vueBord,
        vuePesee: vuePesee,
        vueNutrition: vueNutrition,
        vueSeances: vueSeances,
        vueMenus: vueMenus,
        vueApps: vueApps,
        planningSeanceDuJour: planningSeanceDuJour,
        feuillePesee: feuillePesee,
        feuilleDetailsSeance: feuilleDetailsSeance,
        feuilleMensurations: feuilleMensurations,
        feuilleNutrition: feuilleNutrition,
        feuilleRecette: feuilleRecette,
        feuilleReglages: feuilleReglages,
        demarrerMinuteur: demarrerMinuteur,
        setSousOngletMenus: function (tab) { EQ.menuViews.setTab(tab); },
        feuilleMenuRecette: function (id, apres) { EQ.menuViews.ouvrirEditeurRecette(id, apres); },
        feuilleMenuIngredient: function (id, apres) { EQ.menuViews.ouvrirEditeurIngredient(id, apres); },
        setSousOngletSeances: function (tab) { sousOngletSeances = tab; },
        setDateNutrition: function (date) { if (date) dateNutrition = date; },
        getDateNutrition: function () { return dateNutrition || U.dateIso(new Date()); }
    };
})(typeof window !== 'undefined' ? window : this);
