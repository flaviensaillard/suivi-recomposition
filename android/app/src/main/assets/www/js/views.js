/* Vues complètes des cinq écrans et des feuilles modales d'action. */
(function (root) {
    'use strict';
    var EQ = root.EQ = root.EQ || {};
    var U = EQ.util, M = EQ.modele, UI = EQ.ui, Store = EQ.store, h = EQ.ui.h;

    var sousOngletMenus = 'planning'; // 'planning', 'recettes', 'courses'
    var sousOngletSeances = 'A';       // 'A', 'B', 'historique'
    var minuteurTimer = null;
    var minuteurRestant = 0;
    var minuteurTotal = 0;

    function avertissementDonneesPreexistantes() {
        if (!Store.anciennesDonneesAverifier()) return '';
        return '<div class="card" role="alert" style="border:1px solid var(--warn,#F5C451);">' +
            '<strong>Données locales antérieures à vérifier</strong>' +
            '<p>Une ancienne version pouvait générer automatiquement des exemples. Ces données ont été conservées, mais leur origine ne peut pas être déterminée automatiquement. Vérifie-les avant de les utiliser comme mesures réelles ; cette version ne les supprime ni ne permet encore de les trier par origine.</p>' +
            '<button class="btn btn-flat" id="btnMasquerAvertissementDonnees" style="min-height:38px; font-size:12.5px;">J’ai compris — masquer (origine non vérifiée)</button>' +
        '</div>';
    }

    // =========================================================================
    // 1. TABLEAU DE BORD (Bord)
    // =========================================================================
    function vueBord(ctx) {
        var logs = ctx.logs || [];
        var reglages = ctx.reglages;
        var statPoids = M.calculerMoyennesPoids(logs);
        var dernierLog = logs[logs.length - 1] || {};
        var aPoids = statPoids.actuel !== null && statPoids.actuel !== undefined;
        var poidsActuel = aPoids ? statPoids.actuel : null;
        var profilConfirme = reglages.profileConfigured === true;
        var protCible = profilConfirme ? reglages.objectifProteinesG : null;
        var kcalCible = profilConfirme ? reglages.objectifCaloriesKcal : null;
        var protAuj = dernierLog.proteinesG;
        var kcalAuj = dernierLog.caloriesKcal;
        var pctProt = protCible && protAuj != null ? Math.min(100, Math.round((protAuj / protCible) * 100)) : 0;
        var pctKcal = kcalCible && kcalAuj != null ? Math.min(100, Math.round((kcalAuj / kcalCible) * 100)) : 0;
        var courses = Store.getCourses();
        var coursesRestantes = courses.filter(function (c) { return !c.pris; }).length;
        var seances = Store.getSeances();

        var html = avertissementDonneesPreexistantes() + '<div class="card hero teal">' +
            '<div class="lbl">Suivi personnel · stockage local sur cet appareil</div>' +
            '<div class="hero-montant">' + (aPoids ? U.formatKg(poidsActuel, 1) : '—') + '</div>' +
            '<div class="hero-sub">' + (aPoids ? 'Dernier poids enregistré' : 'Aucune pesée enregistrée') + '</div>' +
            '<div style="margin-top:10px; display:flex; align-items:center; gap:8px; flex-wrap:wrap;">' +
                (logs.length >= 2 && statPoids.tendance7j < 0 ? '<span class="badge ok">↘ ' + statPoids.tendance7j.toFixed(1) + ' kg sur 7 j</span>' :
                 logs.length >= 2 && statPoids.tendance7j > 0 ? '<span class="badge warn">↗ +' + statPoids.tendance7j.toFixed(1) + ' kg sur 7 j</span>' :
                 '<span class="badge info">' + (logs.length >= 2 ? 'Tendance stable sur 7 j' : 'Tendance indisponible') + '</span>') +
                (dernierLog.date ? '<span class="dim" style="font-size:12px; margin-left:auto;">' + U.dateFr(dernierLog.date, { court: true }) + '</span>' : '') +
            '</div>' +
            '<button class="btn btn-hero" id="btnAjoutPeseeRapide" style="margin-top:14px;">＋ Noter mes données</button>' +
        '</div>';

        html += '<div class="titre">Mes suivis locaux</div>' +
        '<div class="grille g2">' +
            '<div class="mini tuile-cliquable" id="tuileProt">' +
                '<div class="l">Protéines du dernier relevé</div>' +
                '<div class="v">' + (protAuj == null ? '—' : protAuj + ' g') + '</div>' +
                '<div class="e">' + (profilConfirme ? 'Objectif : ' + protCible + ' g/j' : 'Repère à confirmer dans Réglages') + '</div>' +
                UI.barre(pctProt, 100, '#0D9488') +
            '</div>' +
            '<div class="mini tuile-cliquable" id="tuileKcal">' +
                '<div class="l">Calories du dernier relevé</div>' +
                '<div class="v">' + (kcalAuj == null ? '—' : kcalAuj + ' kcal') + '</div>' +
                '<div class="e">' + (profilConfirme ? 'Repère : ' + kcalCible + ' kcal/j' : 'Repère à confirmer dans Réglages') + '</div>' +
                UI.barre(pctKcal, 100, '#F5C451') +
            '</div>' +
            '<div class="mini tuile-cliquable" id="tuileSeance">' +
                '<div class="l">Séances saisies sur cet appareil</div>' +
                '<div class="v">' + seances.length + '</div>' +
                '<div class="e">Programme générique, non synchronisé</div>' +
            '</div>' +
            '<div class="mini tuile-cliquable" id="tuileMidi">' +
                '<div class="l">Menus du foyer</div>' +
                '<div class="v" style="font-size:15px;">Streamlit</div>' +
                '<div class="e">Pas de planning hors ligne dans cette version</div>' +
            '</div>' +
        '</div>';

        html += '<div class="titre">Protéines saisies récemment</div>' +
            '<div class="card tight">' +
            (profilConfirme
                ? UI.svgBarresProteines(logs.slice(-7), protCible)
                : '<div class="vide">Confirme les repères dans Réglages pour afficher la comparaison à un objectif.</div>') +
            '</div>';

        html += '<div class="titre">Courses familiales</div>' +
            '<div class="card tight tuile-cliquable" id="tuileCoursesBord">' +
                '<div style="font-size:15px; font-weight:700;">' +
                    (courses.length ? coursesRestantes + ' article(s) local(aux)' : 'Aucune liste familiale hors ligne') +
                '</div>' +
                '<div class="st">La liste partagée reste dans Streamlit jusqu’à la synchronisation de l’APK.</div>' +
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

        var html = avertissementDonneesPreexistantes();

        // --- Résumé en 3 mini-tuiles
        html += '<div class="grille g3" style="margin-bottom:12px;">' +
            '<div class="mini">' +
                '<div class="l">Moyenne 7 j</div>' +
                '<div class="v">' + (stats.m7 ? U.formatKg(stats.m7, 1) : '—') + '</div>' +
                '<div class="e">' + (logs.length < 2 ? 'pas assez de mesures' : (stats.tendance7j < 0 ? '↘ ' + stats.tendance7j.toFixed(1) : (stats.tendance7j > 0 ? '↗ +' + stats.tendance7j.toFixed(1) : '→ stable'))) + '</div>' +
            '</div>' +
            '<div class="mini">' +
                '<div class="l">Moyenne 30 j</div>' +
                '<div class="v">' + (stats.m30 ? U.formatKg(stats.m30, 1) : '—') + '</div>' +
                '<div class="e">lissé sur 1 mois</div>' +
            '</div>' +
            '<div class="mini">' +
                '<div class="l">Perte totale</div>' +
                '<div class="v up">' + (logs.length >= 2 ? stats.perteTotale.toFixed(1) + ' kg' : '—') + '</div>' +
                '<div class="e">depuis le début du suivi</div>' +
            '</div>' +
        '</div>';

        // --- Bouton d'ajout
        html += '<button class="btn" id="btnNouvPesee" style="margin-bottom:14px;">＋ Enregistrer une pesée</button>';

        // --- Graphique interactif
        html += '<div class="titre">Évolution et tendance du poids</div>' +
        '<div class="card">' +
            UI.svgGraphiquePoids(logs, reglages.profileConfigured ? reglages.poidsCibleKg : null) +
        '</div>';

        // --- Mensurations
        html += '<div class="titre">Mensurations <span class="n">dernière mesure : ' + (derniereMens.date ? U.dateFr(derniereMens.date, { court: true }) : 'aucune') + '</span></div>' +
        '<div class="card tight">' +
            '<div class="ligne">' +
                '<div class="gr"><div class="tt">Tour de taille</div><div class="st">au niveau du nombril</div></div>' +
                '<div class="dr"><div class="a">' + (derniereMens.tailleCm == null ? '—' : derniereMens.tailleCm) + (derniereMens.tailleCm == null ? '' : ' cm') + '</div></div>' +
            '</div>' +
            '<div class="ligne">' +
                '<div class="gr"><div class="tt">Tour de hanches</div><div class="st">au plus large des fessiers</div></div>' +
                '<div class="dr"><div class="a">' + (derniereMens.hanchesCm == null ? '—' : derniereMens.hanchesCm) + (derniereMens.hanchesCm == null ? '' : ' cm') + '</div></div>' +
            '</div>' +
            '<div class="ligne">' +
                '<div class="gr"><div class="tt">Tour de bras</div><div class="st">biceps contracté</div></div>' +
                '<div class="dr"><div class="a">' + (derniereMens.brasCm == null ? '—' : derniereMens.brasCm) + (derniereMens.brasCm == null ? '' : ' cm') + '</div></div>' +
            '</div>' +
            '<div class="ligne">' +
                '<div class="gr"><div class="tt">Tour de cuisse</div><div class="st">mi-cuisse</div></div>' +
                '<div class="dr"><div class="a">' + (derniereMens.cuisseCm == null ? '—' : derniereMens.cuisseCm) + (derniereMens.cuisseCm == null ? '' : ' cm') + '</div></div>' +
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
                    '<div class="st">' + (log.masseGrassePct ? log.masseGrassePct + ' % gras · ' : '') + (log.proteinesG == null ? 'protéines non renseignées' : log.proteinesG + ' g prot') + ' · ' + (log.caloriesKcal == null ? 'calories non renseignées' : log.caloriesKcal + ' kcal') + '</div>' +
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
        var html = avertissementDonneesPreexistantes();

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
                            '<div class="st">' + U.dateFr(s.date, { jour: true, annee: true }) + (s.type ? ' · séance ' + h(s.type) : '') + '</div>' +
                        '</div>' +
                        '<div class="dr">' +
                            '<div class="a">Terminée</div>' +
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
            '<div class="lbl">Programme générique · durée indicative ' + h(prog.duree) + '</div>' +
            '<div style="font-size:20px; font-weight:750; margin:4px 0;">' + h(prog.titre) + '</div>' +
            '<div class="st">' + h(prog.description) + '</div>' +
            '<div class="st" style="margin-top:8px;">Ce modèle n’est pas personnalisé selon ton profil. Adapte les mouvements et arrête ceux qui te font mal. Les saisies de séries restent temporaires ; seule la validation de la séance est conservée.</div>' +
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
                                '<input type="number" class="in-mini in-reps" placeholder="Reps effectuées" value="" />' +
                                '<input type="text" class="in-mini in-charge" placeholder="Charge utilisée" value="" />' +
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

        html += '<button class="btn btn-hero" id="btnValiderSeance" data-type="' + h(prog.cle) + '" data-nom="' + h(prog.titre) + '" style="margin-top:12px; margin-bottom:20px;">' +
            '✔ Confirmer une séance terminée' +
        '</button>';

        return html;
    }

    // =========================================================================
    // 4. MENUS & COURSES (Menus)
    // =========================================================================
    function vueMenus(ctx) {
        var html = avertissementDonneesPreexistantes();

        // --- Sous-onglets
        html += '<div class="chips" style="margin-bottom:12px;">' +
            '<button class="chip ' + (sousOngletMenus === 'planning' ? 'actif' : '') + '" data-menu-tab="planning">Planning semaine</button>' +
            '<button class="chip ' + (sousOngletMenus === 'recettes' ? 'actif' : '') + '" data-menu-tab="recettes">Recettes &amp; Plats</button>' +
            '<button class="chip ' + (sousOngletMenus === 'courses' ? 'actif' : '') + '" data-menu-tab="courses">Liste de courses</button>' +
        '</div>';

        // Le planning et les recettes du foyer sont partagés dans Streamlit.
        // Ne pas présenter les anciennes fixtures de démonstration comme des données réelles.
        if (sousOngletMenus === 'planning') {
            return html + '<div class="card"><div class="lbl">Menus partagés du foyer</div>' +
                '<p>Le planning familial n’est pas disponible hors ligne dans cette version de l’APK.</p>' +
                '<p>Ouvre l’application Streamlit depuis l’onglet <strong>Applications Web</strong>. La synchronisation mobile sera ajoutée avec des comptes individuels et une file locale.</p></div>';
        }

        if (sousOngletMenus === 'recettes') {
            return html + '<div class="card"><div class="lbl">Recettes du foyer</div>' +
                '<p>La base partagée de recettes n’est pas chargée dans l’APK. Les exemples intégrés ont été retirés de l’écran pour ne pas les confondre avec vos recettes.</p>' +
                '<p>Ouvre l’application Streamlit depuis l’onglet <strong>Applications Web</strong>.</p></div>';
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
            '</div>';

            if (!courses.length) {
                html += '<div class="card"><div class="vide">Aucune liste de courses locale. La liste familiale partagée est dans l’application Streamlit ; elle n’est pas encore disponible hors ligne dans l’APK.</div></div>';
                return html;
            }

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

        return '<div class="card tight" style="margin-bottom:10px; border-color:var(--teal); background:var(--card-2);">' +
            '<div style="display:flex; align-items:center; justify-content:space-between; gap:8px; flex-wrap:wrap;">' +
                '<div style="flex:1; min-width:180px;">' +
                    '<div class="lbl" style="color:var(--teal);">Application sélectionnée</div>' +
                    '<div style="font-size:15px; font-weight:750; color:var(--txt);">' + h(labelActive) + '</div>' +
                    '<div class="st" style="font-size:11px; overflow-wrap:anywhere;">' + h(urlActive) + '</div>' +
                '</div>' +
                '<div style="display:flex; gap:6px;">' +
                    '<button class="btn btn-flat" id="btnBasculeApp" style="width:auto; min-height:38px; padding:0 12px; font-size:12.5px;" title="Passer à ' + h(labelAutre) + '">' +
                        '⇄ ' + (courante === 'menus' ? 'Suivi' : 'Menus') +
                    '</button>' +
                    '<button class="btn btn-hero" id="btnOuvrirNav" style="width:auto; min-height:38px; padding:0 12px; font-size:12.5px;">↗ Ouvrir</button>' +
                '</div>' +
            '</div>' +
        '</div>' +
        '<div class="card">' +
            '<h3 style="margin-top:0;">Accès aux applications Web</h3>' +
            '<p>Les applications Streamlit s’ouvrent dans le navigateur du système ; aucune page distante ne s’exécute dans le WebView privilégié.</p>' +
            '<p><strong>Mode actuel : stockage local uniquement.</strong> Les suivis saisis dans l’APK restent sur cet appareil. La synchronisation Supabase est désactivée : cette version ne lit ni n’envoie ces données.</p>' +
            '<p>La synchronisation hors ligne entre membres/appareils n’est pas encore implémentée. Elle nécessitera une authentification individuelle, une file d’attente locale et une résolution explicite des conflits.</p>' +
            '<p style="margin-bottom:0; color:var(--txt-3);">L’espace partagé des menus et les suivis privés restent gérés séparément par l’application Streamlit.</p>' +
        '</div>';
    }

    // =========================================================================
    // MODALES D'ACTION (Feuilles)
    // =========================================================================

    // --- Modal : Noter la pesée du jour
    function feuillePesee(ctx, apresEnregistrement) {
        var aujourdHui = U.dateIso(new Date());

        var formHtml = '<div class="champ">' +
            '<label>Date de la pesée</label>' +
            '<input type="date" id="inDatePesee" value="' + aujourdHui + '" />' +
        '</div>' +
        '<div class="champ">' +
            '<label>Poids sur la balance (kg) — obligatoire</label>' +
            '<input type="number" step="0.1" id="inPoids" placeholder="Saisir le poids mesuré" value="" />' +
        '</div>' +
        '<div class="champ">' +
            '<label>Masse grasse (%) — facultatif</label>' +
            '<input type="number" step="0.1" id="inGras" placeholder="Laisser vide si non mesuré" value="" />' +
        '</div>' +
        '<div class="champ">' +
            '<label>Protéines du jour (g) — facultatif</label>' +
            '<input type="number" id="inProt" placeholder="Laisser vide si non suivi" value="" />' +
        '</div>' +
        '<div class="champ">' +
            '<label>Calories du jour (kcal) — facultatif</label>' +
            '<input type="number" id="inKcal" placeholder="Laisser vide si non suivi" value="" />' +
        '</div>' +
        '<button class="btn btn-hero" id="btnValiderNouvellePesee" style="margin-top:8px;">' +
            'Enregistrer la pesée' +
        '</button>';

        UI.feuille({
            titre: 'Noter ma journée',
            aide: 'Poids mesuré obligatoire ; masse grasse, protéines et calories sont facultatives.',
            html: formHtml,
            apresRendu: function (racine, fermer) {
                var btn = UI.$('#btnValiderNouvellePesee', racine);
                btn.onclick = function () {
                    var d = UI.$('#inDatePesee', racine).value;
                    var p = U.num(UI.$('#inPoids', racine).value, null);
                    if (!d || p === null || p <= 0) {
                        UI.toast('Veuillez indiquer une date et un poids valide');
                        return;
                    }
                    var gras = U.num(UI.$('#inGras', racine).value, null);
                    var prot = U.num(UI.$('#inProt', racine).value, null);
                    var kcal = U.num(UI.$('#inKcal', racine).value, null);
                    if ((gras !== null && (gras <= 0 || gras > 100)) ||
                        (prot !== null && prot < 0) || (kcal !== null && kcal < 0)) {
                        UI.toast('Protéines et calories doivent être non négatives ; masse grasse > 0 et ≤ 100 %');
                        return;
                    }

                    var entree = { date: d, poids: p };
                    if (gras !== null) entree.masseGrassePct = gras;
                    if (prot !== null) entree.proteinesG = Math.round(prot);
                    if (kcal !== null) entree.caloriesKcal = Math.round(kcal);
                    Store.saveLog(entree);

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
            '<input type="number" step="0.5" id="inTailleCm" placeholder="Laisser vide si non mesuré" value="" />' +
        '</div>' +
        '<div class="champ">' +
            '<label>Tour de hanches (cm)</label>' +
            '<input type="number" step="0.5" id="inHanchesCm" placeholder="Laisser vide si non mesuré" value="" />' +
        '</div>' +
        '<div class="champ">' +
            '<label>Tour de bras (cm biceps contracté)</label>' +
            '<input type="number" step="0.5" id="inBrasCm" placeholder="Laisser vide si non mesuré" value="" />' +
        '</div>' +
        '<div class="champ">' +
            '<label>Tour de cuisse (cm)</label>' +
            '<input type="number" step="0.5" id="inCuisseCm" placeholder="Laisser vide si non mesuré" value="" />' +
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
                    var t = U.num(UI.$('#inTailleCm', racine).value, null);
                    var h = U.num(UI.$('#inHanchesCm', racine).value, null);
                    var b = U.num(UI.$('#inBrasCm', racine).value, null);
                    var c = U.num(UI.$('#inCuisseCm', racine).value, null);
                    var mesures = [t, h, b, c];
                    if (!d || !mesures.some(function (v) { return v !== null; })) {
                        UI.toast('Indique une date et au moins une mensuration');
                        return;
                    }
                    if (mesures.some(function (v) { return v !== null && v <= 0; })) {
                        UI.toast('Les mensurations doivent être supérieures à zéro');
                        return;
                    }

                    var entree = { date: d };
                    if (t !== null) entree.tailleCm = t;
                    if (h !== null) entree.hanchesCm = h;
                    if (b !== null) entree.brasCm = b;
                    if (c !== null) entree.cuisseCm = c;
                    Store.saveMensuration(entree);

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
        var afficherRepere = r.profileConfigured === true;
        function valeurRepere(cle) {
            return afficherRepere && r[cle] != null ? h(r[cle]) : '';
        }
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
            '<input type="number" step="0.5" id="regPoidsCible" value="' + valeurRepere('poidsCibleKg') + '" placeholder="À renseigner" />' +
        '</div>' +
        '<div class="champ">' +
            '<label>Objectif protéines par jour (g)</label>' +
            '<input type="number" id="regProtCible" value="' + valeurRepere('objectifProteinesG') + '" placeholder="À renseigner" />' +
        '</div>' +
        '<div class="champ">' +
            '<label>Objectif calories par jour (kcal)</label>' +
            '<input type="number" id="regKcalCible" value="' + valeurRepere('objectifCaloriesKcal') + '" placeholder="À renseigner" />' +
        '</div>' +
        '<div class="card" style="margin:12px 0;">' +
            '<strong>Repères à vérifier — non personnalisés</strong>' +
            '<p>Les valeurs affichées ci-dessus ne sont pas des recommandations personnelles. Vérifie-les avant d’activer toute comparaison.</p>' +
            '<label style="display:flex; align-items:flex-start; gap:9px; line-height:1.45;">' +
                '<input type="checkbox" id="regConfirmerRepere" ' + (r.profileConfigured ? 'checked' : '') + ' style="margin-top:3px;" />' +
                'J’ai vérifié ces repères pour mon profil et souhaite les utiliser dans les graphiques.' +
            '</label>' +
        '</div>' +
        '<div class="card" style="margin:12px 0;">' +
            '<strong>Synchronisation désactivée</strong>' +
            '<p>Cette version stocke les données sur cet appareil dans un profil local unique. Les suivis ne sont pas séparés par membre : ne partage pas cet appareil pour saisir des données personnelles.</p>' +
            '<p style="margin-bottom:8px;">Ne saisis aucune clé Supabase ici : il n’y a ni authentification individuelle, ni synchronisation sécurisée.</p>' +
            '<button class="btn btn-flat" id="btnEffacerAnciennesCles" style="min-height:38px; font-size:12.5px;">Effacer une ancienne clé Supabase de cet appareil</button>' +
        '</div>' +
        '<button class="btn btn-hero" id="btnSauverReglages" style="margin-top:10px;">Enregistrer les réglages</button>' +
        '<div style="margin-top:18px; padding-top:14px; border-top:1px solid var(--line); text-align:center;">' +
            '<div style="font-size:11.5px; color:var(--txt-3);">Équilibre · stockage local sur cet appareil</div>' +
        '</div>';

        UI.feuille({
            titre: 'Réglages &amp; Connexions',
            aide: 'Configurez les adresses Web et vos repères locaux ; aucune synchronisation n’est active.',
            html: html,
            apresRendu: function (racine, fermer) {
                var btnSave = UI.$('#btnSauverReglages', racine);
                btnSave.onclick = function () {
                    var poidsCible = U.num(UI.$('#regPoidsCible', racine).value, null);
                    var protCible = U.num(UI.$('#regProtCible', racine).value, null);
                    var kcalCible = U.num(UI.$('#regKcalCible', racine).value, null);
                    var confirmerRepere = UI.$('#regConfirmerRepere', racine).checked;
                    var valeurs = [poidsCible, protCible, kcalCible];
                    if (valeurs.some(function (v) { return v !== null && v <= 0; }) ||
                        (protCible !== null && Math.round(protCible) <= 0) ||
                        (kcalCible !== null && Math.round(kcalCible) <= 0)) {
                        UI.toast('Les repères numériques doivent être supérieurs à zéro');
                        return;
                    }
                    if (confirmerRepere && valeurs.some(function (v) { return v === null; })) {
                        UI.toast('Renseigne tous les repères avant de les confirmer');
                        return;
                    }
                    var nouv = Object.assign({}, r, {
                        urlSuivi: UI.$('#regUrlSuivi', racine).value.trim(),
                        urlMenus: UI.$('#regUrlMenus', racine).value.trim(),
                        poidsCibleKg: poidsCible === null ? r.poidsCibleKg : poidsCible,
                        objectifProteinesG: protCible === null ? r.objectifProteinesG : Math.round(protCible),
                        objectifCaloriesKcal: kcalCible === null ? r.objectifCaloriesKcal : Math.round(kcalCible),
                        profileConfigured: confirmerRepere
                    });
                    Store.saveReglages(nouv);
                    fermer();
                    UI.toast('✅ Réglages enregistrés');
                    if (apresSauvegarde) apresSauvegarde(nouv);
                };

                var btnClearLegacyKey = UI.$('#btnEffacerAnciennesCles', racine);
                btnClearLegacyKey.onclick = function () {
                    if (confirm('Effacer les anciennes URL et clé Supabase stockées localement sur cet appareil ?')) {
                        Store.effacerAnciennesCles();
                        delete r.supabaseUrl;
                        delete r.supabaseKey;
                        UI.toast('Anciennes clés locales supprimées');
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
