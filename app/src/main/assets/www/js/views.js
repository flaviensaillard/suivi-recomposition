/* Vues complètes des cinq écrans et des feuilles modales d'action. */
(function (root) {
    'use strict';
    var EQ = root.EQ = root.EQ || {};
    var U = EQ.util, M = EQ.modele, UI = EQ.ui, Store = EQ.store;

    var sousOngletMenus = 'planning'; // 'planning', 'recettes', 'courses'
    var sousOngletSeances = 'A';       // 'A', 'B', 'historique'
    var minuteurTimer = null;
    var minuteurRestant = 0;
    var minuteurTotal = 0;

    // =========================================================================
    // 1. TABLEAU DE BORD (Bord)
    // =========================================================================
    function vueBord(ctx) {
        var logs = ctx.logs;
        var reglages = ctx.reglages;
        var statPoids = M.calculerMoyennesPoids(logs);
        var dernierLog = logs[logs.length - 1] || {};

        var poidsActuel = statPoids.actuel || reglages.poidsDepartKg;
        var ecartCible = Math.round((poidsActuel - reglages.poidsCibleKg) * 10) / 10;
        var protAuj = dernierLog.proteinesG || 138;
        var kcalAuj = dernierLog.caloriesKcal || 1680;
        var protCible = reglages.objectifProteinesG || 130;
        var kcalCible = reglages.objectifCaloriesKcal || 1700;
        var pctProt = Math.min(100, Math.round((protAuj / protCible) * 100));
        var pctKcal = Math.min(100, Math.round((kcalAuj / kcalCible) * 100));

        var courses = Store.getCourses();
        var coursesRestantes = courses.filter(function (c) { return !c.pris; }).length;

        var html = '';

        // --- CARTE HÉRO : POIDS & OBJECTIF
        html += '<div class="card hero teal">' +
            '<div class="lbl">Recomposition corporelle · Poids actuel</div>' +
            '<div class="hero-montant">' + U.formatKg(poidsActuel, 1) + '</div>' +
            '<div class="hero-sub">Cible ' + U.formatKg(reglages.poidsCibleKg, 1) + ' · Écart ' + (ecartCible > 0 ? '+' : '') + ecartCible.toFixed(1) + ' kg</div>' +
            '<div style="margin-top:10px; display:flex; align-items:center; gap:8px; flex-wrap:wrap;">' +
                (statPoids.tendance7j < 0 ? '<span class="badge ok">↘ ' + statPoids.tendance7j.toFixed(1) + ' kg sur 7 j</span>' :
                 statPoids.tendance7j > 0 ? '<span class="badge warn">↗ +' + statPoids.tendance7j.toFixed(1) + ' kg sur 7 j</span>' :
                 '<span class="badge info">→ Poids stable sur 7 j</span>') +
                '<span class="badge info">Déficit contrôlé</span>' +
                '<span class="dim" style="font-size:12px; margin-left:auto;">' + U.dateFr(dernierLog.date || new Date(), { court: true }) + '</span>' +
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
                UI.barre(pctProt, 100, protAuj >= protCible ? '#10B981' : '#0D9488') +
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
                '<div class="l">Séance prévue</div>' +
                '<div class="v" style="font-size:16px;">Séance A</div>' +
                '<div class="e">Jambes &amp; Poussée · 30 min</div>' +
                '<div style="margin-top:6px;"><span class="badge ok">Prête</span></div>' +
            '</div>' +
            // Tuile Menus / Repas
            '<div class="mini tuile-cliquable" id="tuileMidi">' +
                '<div class="l">Midi au planning</div>' +
                '<div class="v" style="font-size:15px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">Gamelle type</div>' +
                '<div class="e">58 g prot · 588 kcal</div>' +
                '<div style="margin-top:6px;"><span class="badge info">3 œufs · edamames</span></div>' +
            '</div>' +
        '</div>';

        // --- TUILE : LES 3 REPAS TYPES DE FLAVIEN (1-clic)
        html += '<div class="titre">⭐ Repas types de Flavien <span class="n">1 clic pour noter</span></div>' +
        '<div class="card tight">' +
            '<div style="display:flex; flex-direction:column; gap:8px;">';

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

        html += '</div></div>';

        // --- TUILE GRAPHIQUE DES PROTÉINES SUR 7 JOURS
        var logs7j = logs.slice(-7);
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
        var derniereMens = mensurations[mensurations.length - 1] || { tailleCm: 84.5, hanchesCm: 98.0, brasCm: 37.0, cuisseCm: 58.5 };

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
        html += '<div class="titre">Mensurations <span class="n">dernière mesure : ' + (derniereMens.date ? U.dateFr(derniereMens.date, { court: true }) : 'récent') + '</span></div>' +
        '<div class="card tight">' +
            '<div class="ligne">' +
                '<div class="gr"><div class="tt">Tour de taille</div><div class="st">au niveau du nombril</div></div>' +
                '<div class="dr"><div class="a">' + derniereMens.tailleCm + ' cm</div></div>' +
            '</div>' +
            '<div class="ligne">' +
                '<div class="gr"><div class="tt">Tour de hanches</div><div class="st">au plus large des fessiers</div></div>' +
                '<div class="dr"><div class="a">' + derniereMens.hanchesCm + ' cm</div></div>' +
            '</div>' +
            '<div class="ligne">' +
                '<div class="gr"><div class="tt">Tour de bras</div><div class="st">biceps contracté</div></div>' +
                '<div class="dr"><div class="a">' + derniereMens.brasCm + ' cm</div></div>' +
            '</div>' +
            '<div class="ligne">' +
                '<div class="gr"><div class="tt">Tour de cuisse</div><div class="st">mi-cuisse</div></div>' +
                '<div class="dr"><div class="a">' + derniereMens.cuisseCm + ' cm</div></div>' +
            '</div>' +
            '<button class="btn btn-flat" id="btnNouvMensurations" style="margin-top:10px; min-height:42px; font-size:13.5px;">＋ Noter mes mensurations</button>' +
        '</div>';

        // --- Historique des pesées (les 10 dernières)
        var historique = logs.slice().reverse().slice(0, 10);
        html += '<div class="titre">Historique récent des pesées</div>' +
        '<div class="card tight">';
        historique.forEach(function (log) {
            html += '<div class="ligne">' +
                '<div class="gr">' +
                    '<div class="tt">' + U.dateFr(log.date, { jour: true }) + '</div>' +
                    '<div class="st">' + (log.masseGrassePct ? log.masseGrassePct + ' % gras · ' : '') + log.proteinesG + ' g prot · ' + log.caloriesKcal + ' kcal</div>' +
                '</div>' +
                '<div class="dr">' +
                    '<div class="a">' + U.formatKg(log.poids, 1) + '</div>' +
                '</div>' +
            '</div>';
        });
        html += '</div>';

        return html;
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
            var seances = Store.getSeances().slice().reverse();
            html += '<div class="titre">Historique des séances d’entraînement</div><div class="card tight">';
            if (seances.length === 0) {
                html += '<div class="vide" style="padding:14px;">Aucune séance enregistrée pour l’instant.</div>';
            } else {
                seances.forEach(function (s) {
                    html += '<div class="ligne">' +
                        '<div class="gr">' +
                            '<div class="tt">' + h(s.nom) + '</div>' +
                            '<div class="st">' + U.dateFr(s.date, { jour: true, annee: true }) + ' · RPE ' + s.rpe + '/10</div>' +
                        '</div>' +
                        '<div class="dr">' +
                            '<div class="a">' + s.dureeMin + ' min</div>' +
                        '</div>' +
                    '</div>';
                });
            }
            html += '</div>';
            return html;
        }

        var prog = sousOngletSeances === 'B' ? M.SEANCE_B : M.SEANCE_A;

        // --- Entête de la séance
        html += '<div class="card teal">' +
            '<div class="lbl">Programme 30 minutes</div>' +
            '<div style="font-size:20px; font-weight:750; margin:4px 0;">' + h(prog.titre) + '</div>' +
            '<div class="st">' + h(prog.description) + '</div>' +
        '</div>';

        // --- Chronomètre de repos intégré
        html += '<div class="card tight minuteur-card" id="minuteurCard">' +
            '<div style="display:flex; align-items:center; justify-content:space-between;">' +
                '<div>' +
                    '<div class="lbl">Chronomètre de repos</div>' +
                    '<div class="minuteur-temps" id="minuteurAffichage">00:00</div>' +
                '</div>' +
                '<div style="display:flex; gap:6px;">' +
                    '<button class="chip btn-timer" data-sec="45">45 s</button>' +
                    '<button class="chip btn-timer" data-sec="60">60 s</button>' +
                    '<button class="chip btn-timer" data-sec="75">75 s</button>' +
                    '<button class="chip btn-timer" data-sec="90">90 s</button>' +
                '</div>' +
            '</div>' +
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
                html += '<div class="card" style="margin-bottom:10px;">' +
                    '<div style="display:flex; align-items:baseline; justify-content:space-between; margin-bottom:6px;">' +
                        '<div style="font-size:16px; font-weight:700;">' + h(exo.nom) + '</div>' +
                        '<span class="badge info">' + h(exo.cible) + '</span>' +
                    '</div>' +
                    '<div class="st" style="font-size:12.5px; margin-bottom:10px; line-height:1.45; color:var(--txt-2);">' +
                        h(exo.description) +
                    '</div>' +
                    '<div style="display:flex; gap:6px; flex-wrap:wrap; margin-bottom:10px;">' +
                        exo.lests.map(function (lest) {
                            return '<span class="badge mut" style="font-size:10.5px;">' + h(lest) + '</span>';
                        }).join('') +
                    '</div>' +
                    // Séries interactives
                    '<div style="border-top:1px solid var(--line); padding-top:8px;">' +
                        [1, 2, 3].map(function (setNo) {
                            return '<div class="ligne-serie">' +
                                '<span style="font-size:12.5px; font-weight:700; width:65px; color:var(--txt-3);">Série ' + setNo + '</span>' +
                                '<input type="number" class="in-mini in-reps" placeholder="Reps" value="10" />' +
                                '<input type="text" class="in-mini in-charge" placeholder="Lest" value="PDC" />' +
                                '<label class="check-serie">' +
                                    '<input type="checkbox" class="cb-serie" data-exo="' + exo.id + '" data-set="' + setNo + '" />' +
                                    '<span class="cb-visuel">✓ Fait</span>' +
                                '</label>' +
                            '</div>';
                        }).join('') +
                    '</div>' +
                '</div>';
            });
        });

        html += '<button class="btn btn-hero" id="btnValiderSeance" style="margin-top:12px; margin-bottom:20px;">' +
            '✔ Enregistrer la séance terminée' +
        '</button>';

        return html;
    }

    // =========================================================================
    // 4. MENUS & COURSES (Menus)
    // =========================================================================
    function vueMenus(ctx) {
        var html = '';

        // --- Sous-onglets
        html += '<div class="chips" style="margin-bottom:12px;">' +
            '<button class="chip ' + (sousOngletMenus === 'planning' ? 'actif' : '') + '" data-menu-tab="planning">Planning semaine</button>' +
            '<button class="chip ' + (sousOngletMenus === 'recettes' ? 'actif' : '') + '" data-menu-tab="recettes">Recettes &amp; Plats</button>' +
            '<button class="chip ' + (sousOngletMenus === 'courses' ? 'actif' : '') + '" data-menu-tab="courses">Liste de courses</button>' +
        '</div>';

        // --- VUE 1 : PLANNING SEMAINE
        if (sousOngletMenus === 'planning') {
            html += '<div class="card tight teal" style="margin-bottom:12px;">' +
                '<div class="lbl">Planning hebdomadaire du foyer</div>' +
                '<div style="font-size:13.5px; color:var(--txt-2); margin-top:2px;">' +
                    'Déjeuners équilibrés et dîners légers, synchronisés avec les courses de la semaine.' +
                '</div>' +
            '</div>';

            M.PLANNING_EXEMPLE.forEach(function (jour) {
                html += '<div class="card" style="margin-bottom:10px;">' +
                    '<div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:8px;">' +
                        '<div style="font-size:15px; font-weight:750; color:var(--gold);">' + h(jour.jour) + '</div>' +
                        '<span class="badge mut">' + (jour.protMidi + jour.protSoir) + ' g prot au total</span>' +
                    '</div>' +
                    // Midi
                    '<div class="ligne" style="padding:6px 0;">' +
                        '<div class="pastille" style="background:rgba(13,148,136,0.18);">☀️</div>' +
                        '<div class="gr">' +
                            '<div class="tt" style="font-size:14px;">Midi : ' + h(jour.midi) + '</div>' +
                            '<div class="st">' + jour.protMidi + ' g prot · ' + jour.kcalMidi + ' kcal</div>' +
                        '</div>' +
                    '</div>' +
                    // Soir
                    '<div class="ligne" style="padding:6px 0;">' +
                        '<div class="pastille" style="background:rgba(56,189,248,0.18);">🌙</div>' +
                        '<div class="gr">' +
                            '<div class="tt" style="font-size:14px;">Soir : ' + h(jour.soir) + '</div>' +
                            '<div class="st">' + jour.protSoir + ' g prot · ' + jour.kcalSoir + ' kcal</div>' +
                        '</div>' +
                    '</div>' +
                '</div>';
            });
            return html;
        }

        // --- VUE 2 : RECETTES & PLATS
        if (sousOngletMenus === 'recettes') {
            html += '<div class="champ" style="margin-bottom:12px;">' +
                '<input type="search" id="rechercheRecette" placeholder="🔍 Rechercher une recette ou un ingrédient…" />' +
            '</div>';

            html += '<div id="listeRecettes">';
            M.RECETTES_EXEMPLES.forEach(function (r) {
                html += '<div class="card card-recette" data-id="' + r.id + '" style="margin-bottom:12px;">' +
                    '<div style="display:flex; justify-content:space-between; align-items:baseline;">' +
                        '<div style="font-size:16px; font-weight:750;">' + h(r.nom) + '</div>' +
                        '<span class="badge ok">' + r.protPortion + ' g prot / portion</span>' +
                    '</div>' +
                    '<div style="display:flex; gap:8px; margin:6px 0 10px; font-size:12px; color:var(--txt-3);">' +
                        '<span>⏱ ' + h(r.temps) + '</span>' +
                        '<span>👥 ' + r.convives + ' convives</span>' +
                        '<span>🔥 ' + r.kcalPortion + ' kcal</span>' +
                    '</div>' +
                    '<div class="st" style="margin-bottom:10px;"><b>Ingrédients principaux :</b> ' +
                        r.ingredients.map(function (ing) { return ing.nom + ' (' + ing.qte + ')'; }).join(', ') +
                    '</div>' +
                    '<button class="btn btn-flat btn-voir-recette" data-id="' + r.id + '" style="min-height:40px; font-size:13.5px;">' +
                        '📖 Voir la préparation &amp; convives' +
                    '</button>' +
                '</div>';
            });
            html += '</div>';
            return html;
        }

        // --- VUE 3 : LISTE DE COURSES
        if (sousOngletMenus === 'courses') {
            var courses = Store.getCourses();
            var restantes = courses.filter(function (c) { return !c.pris; }).length;

            html += '<div class="card tight" style="margin-bottom:12px; display:flex; align-items:center; justify-content:space-between;">' +
                '<div>' +
                    '<div class="lbl">Liste de courses interactive</div>' +
                    '<div style="font-size:17px; font-weight:750; color:var(--txt);">' +
                        restantes + ' article' + (restantes > 1 ? 's' : '') + ' restant' + (restantes > 1 ? 's' : '') +
                    '</div>' +
                '</div>' +
                '<button class="btn btn-flat" id="btnResetCourses" style="width:auto; min-height:36px; padding:0 12px; font-size:12px;">' +
                    '↻ Réinitialiser' +
                '</button>' +
            '</div>';

            // Grouper par rayon
            var parRayon = {};
            courses.forEach(function (c) {
                if (!parRayon[c.rayon]) parRayon[c.rayon] = [];
                parRayon[c.rayon].push(c);
            });

            Object.keys(parRayon).forEach(function (rayon) {
                html += '<div class="titre">' + h(rayon) + '</div>' +
                '<div class="card tight" style="margin-bottom:10px;">';

                parRayon[rayon].forEach(function (item) {
                    html += '<div class="ligne-course ' + (item.pris ? 'pris' : '') + '" data-id="' + item.id + '">' +
                        '<div class="case-check ' + (item.pris ? 'coche' : '') + '">✓</div>' +
                        '<div class="gr">' +
                            '<div class="tt item-nom">' + h(item.produit) + '</div>' +
                            '<div class="st">' + h(item.qte) + '</div>' +
                        '</div>' +
                    '</div>';
                });

                html += '</div>';
            });

            return html;
        }

        return html;
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
        html += '<div class="card tight" style="margin-bottom:8px; border-color:var(--teal); background:var(--card-2);">' +
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

    // --- Modal : Noter la pesée du jour
    function feuillePesee(ctx, apresEnregistrement) {
        var reglages = ctx.reglages;
        var aujourdHui = U.dateIso(new Date());
        var dernier = ctx.logs[ctx.logs.length - 1] || {};

        var formHtml = '<div class="champ">' +
            '<label>Date de la pesée</label>' +
            '<input type="date" id="inDatePesee" value="' + aujourdHui + '" />' +
        '</div>' +
        '<div class="champ">' +
            '<label>Poids sur la balance (kg)</label>' +
            '<input type="number" step="0.1" id="inPoids" placeholder="ex: 78.4" value="' + (dernier.poids || 78.4) + '" />' +
        '</div>' +
        '<div class="champ">' +
            '<label>Masse grasse (% — facultatif)</label>' +
            '<input type="number" step="0.1" id="inGras" placeholder="ex: 17.8" value="' + (dernier.masseGrassePct || '') + '" />' +
        '</div>' +
        '<div class="champ">' +
            '<label>Protéines du jour (g)</label>' +
            '<input type="number" id="inProt" placeholder="ex: 130" value="' + (dernier.proteinesG || 130) + '" />' +
        '</div>' +
        '<div class="champ">' +
            '<label>Calories du jour (kcal)</label>' +
            '<input type="number" id="inKcal" placeholder="ex: 1700" value="' + (dernier.caloriesKcal || 1700) + '" />' +
        '</div>' +
        '<button class="btn btn-hero" id="btnValiderNouvellePesee" style="margin-top:8px;">' +
            'Enregistrer la journée' +
        '</button>';

        UI.feuille({
            titre: 'Noter ma journée',
            aide: 'Poids à jeun le matin, protéines et calories consommées.',
            html: formHtml,
            apresRendu: function (racine, fermer) {
                var btn = UI.$('#btnValiderNouvellePesee', racine);
                btn.onclick = function () {
                    var d = UI.$('#inDatePesee', racine).value;
                    var p = U.num(UI.$('#inPoids', racine).value, null);
                    if (!p || p <= 0) {
                        UI.toast('Veuillez indiquer un poids valide');
                        return;
                    }
                    var gras = U.num(UI.$('#inGras', racine).value, null);
                    var prot = Math.round(U.num(UI.$('#inProt', racine).value, reglages.objectifProteinesG));
                    var kcal = Math.round(U.num(UI.$('#inKcal', racine).value, reglages.objectifCaloriesKcal));

                    Store.saveLog({
                        date: d,
                        poids: p,
                        masseGrassePct: gras,
                        proteinesG: prot,
                        caloriesKcal: kcal
                    });

                    fermer();
                    UI.toast('✅ Pesée enregistrée : ' + U.formatKg(p, 1));
                    if (apresEnregistrement) apresEnregistrement();
                };
            }
        });
    }

    // --- Modal : Noter mensurations
    function feuilleMensurations(ctx, apresEnregistrement) {
        var aujourdHui = U.dateIso(new Date());
        var formHtml = '<div class="champ">' +
            '<label>Date</label>' +
            '<input type="date" id="inDateMens" value="' + aujourdHui + '" />' +
        '</div>' +
        '<div class="champ">' +
            '<label>Tour de taille (cm au nombril)</label>' +
            '<input type="number" step="0.5" id="inTailleCm" placeholder="ex: 84.5" value="84.5" />' +
        '</div>' +
        '<div class="champ">' +
            '<label>Tour de hanches (cm)</label>' +
            '<input type="number" step="0.5" id="inHanchesCm" placeholder="ex: 98.0" value="98.0" />' +
        '</div>' +
        '<div class="champ">' +
            '<label>Tour de bras (cm biceps contracté)</label>' +
            '<input type="number" step="0.5" id="inBrasCm" placeholder="ex: 37.0" value="37.0" />' +
        '</div>' +
        '<div class="champ">' +
            '<label>Tour de cuisse (cm)</label>' +
            '<input type="number" step="0.5" id="inCuisseCm" placeholder="ex: 58.5" value="58.5" />' +
        '</div>' +
        '<button class="btn btn-hero" id="btnValiderMens" style="margin-top:8px;">' +
            'Enregistrer les mensurations' +
        '</button>';

        UI.feuille({
            titre: 'Mes mensurations',
            aide: 'Mesure au ruban le matin à jeun pour suivre la perte de taille.',
            html: formHtml,
            apresRendu: function (racine, fermer) {
                var btn = UI.$('#btnValiderMens', racine);
                btn.onclick = function () {
                    var d = UI.$('#inDateMens', racine).value;
                    var t = U.num(UI.$('#inTailleCm', racine).value);
                    var h = U.num(UI.$('#inHanchesCm', racine).value);
                    var b = U.num(UI.$('#inBrasCm', racine).value);
                    var c = U.num(UI.$('#inCuisseCm', racine).value);

                    Store.saveMensuration({
                        date: d,
                        tailleCm: t,
                        hanchesCm: h,
                        brasCm: b,
                        cuisseCm: c
                    });

                    fermer();
                    UI.toast('✅ Mensurations enregistrées');
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

    // --- Modal : Réglages (⚙)
    function feuilleReglages(ctx, apresSauvegarde) {
        var r = ctx.reglages;
        var html = '<div class="champ">' +
            '<label>Adresse application Suivi (Streamlit)</label>' +
            '<input type="url" id="regUrlSuivi" value="' + h(r.urlSuivi) + '" placeholder="https://suivi-recomposition.streamlit.app" />' +
        '</div>' +
        '<div class="champ">' +
            '<label>Adresse application Menus &amp; Recettes (Streamlit)</label>' +
            '<input type="url" id="regUrlMenus" value="' + h(r.urlMenus) + '" placeholder="https://gestion-menus.streamlit.app" />' +
        '</div>' +
        '<div class="champ">' +
            '<label>Poids cible (kg)</label>' +
            '<input type="number" step="0.5" id="regPoidsCible" value="' + r.poidsCibleKg + '" />' +
        '</div>' +
        '<div class="champ">' +
            '<label>Objectif protéines par jour (g)</label>' +
            '<input type="number" id="regProtCible" value="' + r.objectifProteinesG + '" />' +
        '</div>' +
        '<div class="champ">' +
            '<label>Objectif calories par jour (kcal)</label>' +
            '<input type="number" id="regKcalCible" value="' + r.objectifCaloriesKcal + '" />' +
        '</div>' +
        '<div class="champ">' +
            '<label>URL Supabase (optionnel pour synchronisation directe)</label>' +
            '<input type="url" id="regSupaUrl" value="' + h(r.supabaseUrl || '') + '" placeholder="https://xxxx.supabase.co" />' +
        '</div>' +
        '<div class="champ">' +
            '<label>Clé Supabase (anon ou service)</label>' +
            '<input type="password" id="regSupaKey" value="' + h(r.supabaseKey || '') + '" placeholder="eyJhbGciOi..." />' +
        '</div>' +
        '<div class="champ">' +
            '<label>Espace utilisateur</label>' +
            '<select id="regProfil">' +
                '<option value="flavien"' + (r.profil === 'flavien' ? ' selected' : '') + '>Flavien (Suivi personnel + Repas types)</option>' +
                '<option value="lea"' + (r.profil === 'lea' ? ' selected' : '') + '>Léa (Suivi &amp; nutrition)</option>' +
                '<option value="partage"' + (r.profil === 'partage' ? ' selected' : '') + '>Espace partagé du foyer (Menus &amp; Courses)</option>' +
            '</select>' +
        '</div>' +
        '<button class="btn btn-hero" id="btnSauverReglages" style="margin-top:10px;">Enregistrer les réglages</button>' +
        '<div style="margin-top:18px; padding-top:14px; border-top:1px solid var(--line); text-align:center;">' +
            '<button class="btn btn-flat" id="btnResetDemo" style="min-height:38px; font-size:12.5px; color:var(--txt-3);">' +
                'Réinitialiser les données de démonstration' +
            '</button>' +
            '<div style="font-size:11.5px; color:var(--txt-3); margin-top:10px;">Équilibre v' +
                ((typeof Native !== 'undefined' && Native.versionName) ? Native.versionName() : '1.0.12') +
                ' · Coque Android native &amp; Web</div>' +
        '</div>';

        UI.feuille({
            titre: 'Réglages &amp; Connexions',
            aide: 'Configurez les adresses Streamlit et vos objectifs personnels.',
            html: html,
            apresRendu: function (racine, fermer) {
                var btnSave = UI.$('#btnSauverReglages', racine);
                btnSave.onclick = function () {
                    var nouv = Object.assign({}, r, {
                        urlSuivi: UI.$('#regUrlSuivi', racine).value.trim(),
                        urlMenus: UI.$('#regUrlMenus', racine).value.trim(),
                        poidsCibleKg: U.num(UI.$('#regPoidsCible', racine).value, 77.0),
                        objectifProteinesG: Math.round(U.num(UI.$('#regProtCible', racine).value, 130)),
                        objectifCaloriesKcal: Math.round(U.num(UI.$('#regKcalCible', racine).value, 1700)),
                        supabaseUrl: UI.$('#regSupaUrl', racine).value.trim(),
                        supabaseKey: UI.$('#regSupaKey', racine).value.trim(),
                        profil: UI.$('#regProfil', racine).value
                    });
                    Store.saveReglages(nouv);
                    fermer();
                    UI.toast('✅ Réglages enregistrés');
                    if (apresSauvegarde) apresSauvegarde(nouv);
                };

                var btnReset = UI.$('#btnResetDemo', racine);
                btnReset.onclick = function () {
                    if (confirm('Voulez-vous recharger le jeu de démonstration initial ?')) {
                        Store.reinitialiserDemo();
                        fermer();
                        UI.toast('Données démo rechargées');
                        if (apresSauvegarde) apresSauvegarde(Store.getReglages());
                    }
                };
            }
        });
    }

    // Gestion du chronomètre de repos
    function demarrerMinuteur(secondes) {
        clearInterval(minuteurTimer);
        minuteurTotal = secondes;
        minuteurRestant = secondes;
        UI.haptic(20);

        function maj() {
            var aff = UI.$('#minuteurAffichage');
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
        vueSeances: vueSeances,
        vueMenus: vueMenus,
        vueApps: vueApps,
        feuillePesee: feuillePesee,
        feuilleMensurations: feuilleMensurations,
        feuilleRecette: feuilleRecette,
        feuilleReglages: feuilleReglages,
        demarrerMinuteur: demarrerMinuteur,
        setSousOngletMenus: function (tab) { sousOngletMenus = tab; },
        setSousOngletSeances: function (tab) { sousOngletSeances = tab; }
    };
})(typeof window !== 'undefined' ? window : this);
