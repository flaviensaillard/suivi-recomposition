/* Contrôleur principal de l'application Équilibre.
   Navigation, routage entre les écrans et gestion des événements interactifs. */
(function (root) {
    'use strict';
    var EQ = root.EQ;
    var U = EQ.util, M = EQ.modele, UI = EQ.ui, Store = EQ.store, Views = EQ.views, Net = EQ.net;
    var Menu = EQ.menu, MenuViews = EQ.menuViews, Coach = EQ.coach;

    var ONGLETS = {
        bord: { titre: 'Tableau de bord', sous: 'recomposition corporelle' },
        pesee: { titre: 'Pesée & Tendance', sous: 'mesures & graphiques' },
        seances: { titre: 'Mes séances', sous: 'programme 30 min & séries' },
        menus: { titre: 'Menus & Courses', sous: 'planning, recettes & foyer' },
        nutrition: { titre: 'Nutrition', sous: 'journal alimentaire & objectifs' },
        coach: { titre: 'Coach IA', sous: 'bien-être & accompagnement' }
    };

    var etat = {
        onglet: 'bord',
        chargement: false,
        contexte: null
    };

    function obtenirContexte() {
        return {
            reglages: Store.getReglages(),
            logs: Store.getLogs(),
            mensurations: Store.getMensurations(),
            seances: Store.getSeances(),
            nutrition: Store.getNutrition(),
            profil: Store.getProfil()
        };
    }

    function rafraichirVue() {
        etat.contexte = obtenirContexte();
        var main = UI.$('#view');
        if (!main) return;

        var html = '';
        switch (etat.onglet) {
            case 'bord':
                html = Views.vueBord(etat.contexte);
                break;
            case 'pesee':
                html = Views.vuePesee(etat.contexte);
                break;
            case 'seances':
                html = Views.vueSeances(etat.contexte);
                break;
            case 'menus':
                html = Views.vueMenus(etat.contexte);
                break;
            case 'nutrition':
                html = Views.vueNutrition(etat.contexte);
                break;
            case 'coach':
                html = Coach ? Coach.vue(etat.contexte) : '<div class="card">Le module Coach IA est indisponible.</div>';
                break;
            default:
                html = Views.vueBord(etat.contexte);
        }

        main.innerHTML = html;
        main.classList.remove('enter');
        void main.offsetWidth; // Reflow pour redéclencher l'animation
        main.classList.add('enter');

        attacherEvenementsVue();
    }

    function naviguer(onglet) {
        if (!ONGLETS[onglet]) onglet = 'bord';
        etat.onglet = onglet;
        Store.setOnglet(onglet);

        // Mise à jour de la barre supérieure
        var tInfo = ONGLETS[onglet];
        var titreEl = UI.$('#titreOnglet');
        if (titreEl) {
            titreEl.innerHTML = U.echapper(tInfo.titre) +
                '<span class="sub" id="sousTitre">' + U.echapper(tInfo.sous) + '</span>';
        }

        // Mise à jour de la barre inférieure
        var boutons = UI.$$('#nav button[data-onglet]');
        boutons.forEach(function (b) {
            if (b.getAttribute('data-onglet') === onglet) {
                b.classList.add('actif');
            } else {
                b.classList.remove('actif');
            }
        });

        UI.haptic(8);
        window.scrollTo(0, 0);
        rafraichirVue();
    }

    function attacherEvenementsVue() {
        var main = UI.$('#view');
        if (!main) return;
        if (etat.onglet === 'coach' && Coach) {
            Coach.attacher(main, etat.contexte, rafraichirVue);
            return;
        }

        // ----------------------------------------------------------- Écran Bord
        var btnAjoutPesee = UI.$('#btnAjoutPeseeRapide', main);
        if (btnAjoutPesee) {
            btnAjoutPesee.onclick = function () {
                Views.feuillePesee(etat.contexte, rafraichirVue);
            };
        }

        var tuileProt = UI.$('#tuileProt', main);
        if (tuileProt) {
            tuileProt.onclick = function () {
                Views.feuillePesee(etat.contexte, rafraichirVue);
            };
        }

        var tuileKcal = UI.$('#tuileKcal', main);
        if (tuileKcal) {
            tuileKcal.onclick = function () {
                Views.feuillePesee(etat.contexte, rafraichirVue);
            };
        }

        var tuileSeance = UI.$('#tuileSeance', main);
        if (tuileSeance) {
            tuileSeance.onclick = function () {
                naviguer('seances');
            };
        }

        var tuileMidi = UI.$('#tuileMidi', main);
        if (tuileMidi) {
            tuileMidi.onclick = function () {
                Views.setSousOngletMenus('planning');
                naviguer('menus');
            };
        }

        var tuileCoursesBord = UI.$('#tuileCoursesBord', main);
        if (tuileCoursesBord) {
            tuileCoursesBord.onclick = function () {
                Views.setSousOngletMenus('courses');
                naviguer('menus');
            };
        }

        // Boutons 1-clic repas types
        var btnsRepas = UI.$$('.btn-noter-repas', main);
        btnsRepas.forEach(function (btn) {
            btn.onclick = function (e) {
                e.stopPropagation();
                var cle = btn.getAttribute('data-repas');
                var r = M.REPAS_TYPES.find(function (x) { return x.cle === cle; });
                if (r) {
                    Store.addNutrition({
                        date: U.dateIso(new Date()),
                        item: r.nom,
                        protein_g: Math.round(r.prot),
                        carbs_g: Math.round(r.gluc || 0),
                        fat_g: Math.round(r.lip || 0),
                        qty: 1
                    });
                    UI.toast('✅ ' + r.nom + ' ajouté au journal nutrition');
                    rafraichirVue();
                }
            };
        });

        // ---------------------------------------------------------- Écran Pesée
        var btnNouvP = UI.$('#btnNouvPesee', main);
        if (btnNouvP) {
            btnNouvP.onclick = function () {
                Views.feuillePesee(etat.contexte, rafraichirVue);
            };
        }

        var btnNouvM = UI.$('#btnNouvMensurations', main);
        if (btnNouvM) {
            btnNouvM.onclick = function () {
                Views.feuilleMensurations(etat.contexte, rafraichirVue);
            };
        }
        UI.$$('.btn-log-edit', main).forEach(function (btn) {
            btn.onclick = function () {
                var date = btn.getAttribute('data-date');
                var entree = Store.getLogs().find(function (x) { return x.date === date; });
                if (entree) Views.feuillePesee(etat.contexte, rafraichirVue, entree);
            };
        });
        UI.$$('.btn-log-delete', main).forEach(function (btn) {
            btn.onclick = function () {
                var date = btn.getAttribute('data-date');
                if (confirm('Supprimer la pesée du ' + date + ' ?')) {
                    Store.deleteLog(date);
                    UI.toast('Pesée supprimée');
                    rafraichirVue();
                }
            };
        });
        UI.$$('.btn-mens-edit', main).forEach(function (btn) {
            btn.onclick = function () {
                var date = btn.getAttribute('data-date');
                var entree = Store.getMensurations().find(function (x) { return x.date === date; });
                if (entree) Views.feuilleMensurations(etat.contexte, rafraichirVue, entree);
            };
        });
        UI.$$('.btn-mens-delete', main).forEach(function (btn) {
            btn.onclick = function () {
                var date = btn.getAttribute('data-date');
                if (confirm('Supprimer les mensurations du ' + date + ' ?')) {
                    Store.deleteMensuration(date);
                    UI.toast('Mensurations supprimées');
                    rafraichirVue();
                }
            };
        });

        // Points interactifs du graphique
        var cercles = UI.$$('.point-poids', main);
        cercles.forEach(function (c) {
            c.onclick = function () {
                var d = c.getAttribute('data-date');
                var p = c.getAttribute('data-poids');
                var info = UI.$('#graphiqueInfo');
                if (info) {
                    info.innerHTML = '<b>' + U.dateFr(d, { jour: true, court: true }) + '</b> : <span class="up" style="font-weight:700;">' + U.formatKg(p, 1) + '</span>';
                }
                UI.haptic(10);
            };
        });

        // -------------------------------------------------------- Écran Séances
        var chipsSeance = UI.$$('.chips button[data-seance]', main);
        chipsSeance.forEach(function (b) {
            b.onclick = function () {
                Views.setSousOngletSeances(b.getAttribute('data-seance'));
                rafraichirVue();
            };
        });
        UI.$$('.ligne-seance-historique', main).forEach(function (ligne) {
            function ouvrirResultats() {
                Views.feuilleDetailsSeance(
                    ligne.getAttribute('data-seance-date'),
                    ligne.getAttribute('data-seance-type')
                );
            }
            ligne.onclick = ouvrirResultats;
            ligne.onkeydown = function (e) {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    ouvrirResultats();
                }
            };
        });

        // Minuteurs entre les blocs : 60 secondes par défaut, ajustables si besoin
        UI.$$('.select-minuteur', main).forEach(function (select) {
            select.onchange = function () {
                var sec = Math.max(1, parseInt(select.value, 10) || 60);
                var cible = select.getAttribute('data-minuteur-cible');
                var affichage = cible ? UI.$('#' + cible, main) : null;
                var bouton = cible ? UI.$('.btn-timer-start[data-minuteur-cible="' + cible + '"]', main) : null;
                if (affichage) {
                    var minutes = Math.floor(sec / 60), secondes = sec % 60;
                    affichage.textContent = (minutes < 10 ? '0' : '') + minutes + ':' + (secondes < 10 ? '0' : '') + secondes;
                }
                if (bouton) bouton.setAttribute('data-sec', String(sec));
            };
        });
        UI.$$('.btn-timer-start', main).forEach(function (b) {
            b.onclick = function () {
                var sec = Math.max(1, parseInt(b.getAttribute('data-sec'), 10) || 60);
                var cible = b.getAttribute('data-minuteur-cible');
                Views.demarrerMinuteur(sec, cible ? '#' + cible : undefined);
            };
        });

        // Accordéons
        var accordeons = UI.$$('.accordeon', main);
        accordeons.forEach(function (acc) {
            var tete = UI.$('.tete', acc);
            if (tete) {
                tete.onclick = function () {
                    acc.classList.toggle('ouvert');
                    UI.haptic(6);
                };
            }
        });

        // Validation de la séance
        var btnValider = UI.$('#btnValiderSeance', main);
        if (btnValider) {
            btnValider.onclick = function () {
                var jour = U.dateIso(new Date());
                var ongletSeance = UI.$('.chip.actif[data-seance]', main);
                var type = ongletSeance ? ongletSeance.getAttribute('data-seance') : 'A';
                var programme = type === 'B' ? M.SEANCE_B : M.SEANCE_A;
                var duree = Math.max(1, Math.round(U.num((UI.$('#dureeSeance', main) || {}).value, 30)));
                var selectRessenti = UI.$('#ressentiSeance', main);
                var ressenti = selectRessenti ? selectRessenti.value : 'normal';
                if (['facile', 'normal', 'difficile'].indexOf(ressenti) < 0) ressenti = 'normal';
                var series = [];
                UI.$$('.cb-serie:checked', main).forEach(function (cb) {
                    var ligne = cb.closest('.ligne-serie');
                    var carte = cb.closest('.exercise-card');
                    var chargeTxt = ligne && UI.$('.in-charge', ligne) ? UI.$('.in-charge', ligne).value.trim() : '';
                    var nombreCharge = /([0-9]+(?:[.,][0-9]+)?)\s*kg/i.exec(chargeTxt);
                    series.push({
                        date: jour, type: type,
                        exercise: cb.getAttribute('data-exo') || (carte && carte.getAttribute('data-exercise')) || 'exercice',
                        set_no: Number(cb.getAttribute('data-set') || 1),
                        reps: Math.max(0, Math.round(U.num(ligne && UI.$('.in-reps', ligne) ? UI.$('.in-reps', ligne).value : 0, 0))),
                        load_kg: nombreCharge ? Number(nombreCharge[1].replace(',', '.')) : null,
                        variant: chargeTxt || null
                    });
                });
                Store.saveSeance({
                    date: jour, type: type, nom: programme.titre,
                    dureeMin: duree, rpe: null, ressenti: ressenti,
                    notes: 'Ressenti: ' + ressenti + ' · ' + series.length + ' série(s) enregistrée(s)'
                });
                Store.saveSeries(series);
                UI.toast('🎉 Séance et séries enregistrées localement');
                Views.setSousOngletSeances('historique');
                rafraichirVue();
            };
        }

        // ---------------------------------------------------------- Écran Menus
        var chipsMenu = UI.$$('.chips button[data-menu-tab]', main);
        chipsMenu.forEach(function (b) {
            b.onclick = function () {
                Views.setSousOngletMenus(b.getAttribute('data-menu-tab'));
                rafraichirVue();
            };
        });

        // Liste de courses interactive
        var lignesCourses = UI.$$('.ligne-course', main);
        lignesCourses.forEach(function (l) {
            l.onclick = function () {
                var id = l.getAttribute('data-course-id') || l.getAttribute('data-id');
                Store.toggleCourse(id);
                UI.haptic(10);
                rafraichirVue();
            };
        });

        var btnResetCourses = UI.$('#btnResetCourses', main);
        if (btnResetCourses) {
            btnResetCourses.onclick = function () {
                var liste = Store.getCourses();
                liste.forEach(function (x) { if (x.pris) Store.toggleCourse(x.id); });
                UI.toast('Tous les articles sont décochés');
                rafraichirVue();
            };
        }

        // Voir recette
        var btnsVoirRecette = UI.$$('.btn-voir-recette', main);
        btnsVoirRecette.forEach(function (b) {
            b.onclick = function () {
                var id = b.getAttribute('data-id');
                Views.feuilleRecette(id);
            };
        });

        // Recherche instantanée de recettes
        var inRecherche = UI.$('#rechercheRecette', main);
        if (inRecherche) {
            inRecherche.oninput = function () {
                var q = inRecherche.value.toLowerCase().trim();
                var cartes = UI.$$('.card-recette', main);
                cartes.forEach(function (card) {
                    var texte = card.textContent.toLowerCase();
                    card.style.display = texte.indexOf(q) >= 0 ? '' : 'none';
                });
            };
        }

        // ---------------------------------------------------------- Menus local-first
        function afficherChampsPlan(form) {
            var selectType = UI.$('[data-pl-type]', form);
            var type = selectType ? selectType.value : 'recette';
            Array.prototype.forEach.call(form.querySelectorAll('[data-plan-field]'), function (el) {
                el.style.display = el.getAttribute('data-plan-field') === type ? '' : 'none';
            });
        }
        Array.prototype.forEach.call(main.querySelectorAll('[data-menu-form]'), function (form) {
            var type = UI.$('[data-pl-type]', form);
            if (type) { type.onchange = function () { afficherChampsPlan(form); }; afficherChampsPlan(form); }
            var choixIng = UI.$('[data-pl-ingredient]', form);
            var choixUnit = UI.$('[data-pl-unite]', form);
            if (choixIng && choixUnit) {
                choixIng.onchange = function () {
                    var fiche = Menu.ingredientParId()[String(choixIng.value)];
                    if (!fiche) return;
                    var courant = choixUnit.value;
                    var unites = Menu.unitesProposees(fiche);
                    choixUnit.innerHTML = unites.map(function (u) {
                        return '<option value="' + U.echapper(u) + '"' + (u === courant ? ' selected' : '') + '>' + U.echapper(u) + '</option>';
                    }).join('');
                    if (unites.indexOf(courant) < 0) choixUnit.value = unites[0];
                };
            }
        });

        var dateDebutMenu = UI.$('#menuDateDebut', main);
        if (dateDebutMenu) dateDebutMenu.onchange = function () {
            MenuViews.setPlanningStart(dateDebutMenu.value); rafraichirVue();
        };
        var dateCourses = UI.$('#courseDateStart', main);
        if (dateCourses) dateCourses.onchange = function () {
            MenuViews.setCoursesStart(dateCourses.value); rafraichirVue();
        };
        var modeCourses = UI.$('#courseMode', main);
        if (modeCourses) modeCourses.onchange = function () {
            MenuViews.setCoursesMode(modeCourses.value); rafraichirVue();
        };
        var btnsSyncMenu = UI.$$('[data-menu-sync]', main);
        btnsSyncMenu.forEach(function (btn) {
            btn.onclick = function () {
                btn.disabled = true;
                UI.toast('Synchronisation des données en cours…');
                Net.synchroniser().then(function (result) {
                    btn.disabled = false;
                    if (result.raison) UI.toast(result.raison);
                    else if (result.erreurs && result.erreurs.length) UI.toast('Synchronisation partielle : ' + result.erreurs[0]);
                    else UI.toast('Menus synchronisés avec Supabase');
                    rafraichirVue();
                }).catch(function (e) { btn.disabled = false; UI.toast(e.message || 'Synchronisation impossible'); });
            };
        });
        UI.$$('[data-plan-open]', main).forEach(function (btn) {
            btn.onclick = function () { MenuViews.setEditorPlan(btn.getAttribute('data-plan-open')); rafraichirVue(); };
        });
        UI.$$('[data-meal-edit]', main).forEach(function (btn) {
            btn.onclick = function () { MenuViews.setEditingMeal(btn.getAttribute('data-meal-edit')); rafraichirVue(); };
        });
        UI.$$('[data-plan-cancel]', main).forEach(function (btn) {
            btn.onclick = function () { MenuViews.cancelPlan(); rafraichirVue(); };
        });
        UI.$$('[data-plan-save]', main).forEach(function (btn) {
            btn.onclick = function () {
                var form = btn.closest('[data-menu-form]');
                if (!form) return;
                var date = btn.getAttribute('data-plan-save');
                var key = btn.getAttribute('data-meal-key') || '';
                var type = (UI.$('[data-pl-type]', form) || {}).value || 'recette';
                var moment = (UI.$('[data-pl-moment]', form) || {}).value || 'Midi';
                var convives = Number((UI.$('[data-pl-convives]', form) || {}).value) || 4;
                try {
                    if (key) {
                        var row = Store.getMenuTable('planned_meals').find(function (x) {
                            return String(x._local_id || x.local_id || x.id) === String(key);
                        });
                        if (!row) throw new Error('Ce repas n’est plus présent dans le planning.');
                        var patch = { meal_type: moment, servings: convives, nb_persons: convives };
                        if (type === 'ingredient') {
                            patch.ingredient_qty = Number((UI.$('[data-pl-qte]', form) || {}).value) || 1;
                            patch.ingredient_unit = (UI.$('[data-pl-unite]', form) || {}).value || 'g';
                        }
                        Menu.modifierRepas(row, patch);
                    } else if (type === 'recette') {
                        var recipeId = (UI.$('[data-pl-recipe]', form) || {}).value;
                        if (!recipeId) throw new Error('Choisis une recette.');
                        Menu.ajouterRepas(date, moment, 'recette', recipeId, convives);
                    } else if (type === 'ingredient') {
                        var ingredientId = (UI.$('[data-pl-ingredient]', form) || {}).value;
                        var quantity = Number((UI.$('[data-pl-qte]', form) || {}).value) || 1;
                        var unit = (UI.$('[data-pl-unite]', form) || {}).value || 'g';
                        Menu.ajouterRepas(date, moment, 'ingredient', ingredientId, convives, quantity, unit);
                    } else {
                        var label = (UI.$('[data-pl-texte]', form) || {}).value || '';
                        Menu.ajouterRepas(date, moment, 'texte', label, convives);
                    }
                    MenuViews.cancelPlan();
                    UI.toast('Repas enregistré localement' + (Store.getRemoteSession() ? ' · synchronisation en attente' : ''));
                    rafraichirVue();
                } catch (e) { UI.toast(e.message || 'Enregistrement impossible'); }
            };
        });
        UI.$$('[data-meal-delete]', main).forEach(function (btn) {
            btn.onclick = function () {
                var key = btn.getAttribute('data-meal-delete');
                var row = Store.getMenuTable('planned_meals').find(function (x) { return String(x._local_id || x.local_id || x.id) === String(key); });
                if (row && (!window.confirm || window.confirm('Supprimer ce repas du planning ?'))) {
                    Menu.supprimerRepas(row); UI.toast('Repas supprimé'); rafraichirVue();
                }
            };
        });
        UI.$$('[data-meal-log]', main).forEach(function (btn) {
            btn.onclick = function () {
                var key = btn.getAttribute('data-meal-log');
                var row = Store.getMenuTable('planned_meals').find(function (x) { return String(x._local_id || x.local_id || x.id) === String(key); });
                if (!row) return;
                var detail = Menu.detailsRepas(row);
                if (!detail.calc) { UI.toast('Valeurs nutritionnelles indisponibles'); return; }
                var c = detail.calc.par_part;
                Store.addNutrition({ date: row.date_menu || U.dateIso(new Date()), item: detail.name + ' (menu)',
                    protein_g: c.proteines, carbs_g: c.glucides, fat_g: c.lipides, qty: 1 });
                UI.toast('Une part ajoutée au journal Nutrition');
                rafraichirVue();
            };
        });
        var searchRecipeMenu = UI.$('#menuSearchRecipe', main);
        if (searchRecipeMenu) searchRecipeMenu.oninput = function () {
            var q = Menu.sansAccent(searchRecipeMenu.value);
            MenuViews.setRecipeSearch(searchRecipeMenu.value);
            UI.$$('[data-recipe-card]', main).forEach(function (card) {
                card.style.display = Menu.sansAccent(card.getAttribute('data-search')).indexOf(q) >= 0 ? '' : 'none';
            });
        };
        UI.$$('[data-recipe-view]', main).forEach(function (btn) {
            btn.onclick = function () { MenuViews.toggleRecipe(btn.getAttribute('data-recipe-view')); rafraichirVue(); };
        });
        UI.$$('[data-menu-new-recipe]', main).forEach(function (btn) {
            btn.onclick = function () { Views.feuilleMenuRecette(null, rafraichirVue); };
        });
        UI.$$('[data-recipe-edit]', main).forEach(function (btn) {
            btn.onclick = function () { Views.feuilleMenuRecette(btn.getAttribute('data-recipe-edit'), rafraichirVue); };
        });
        UI.$$('[data-recipe-delete]', main).forEach(function (btn) {
            btn.onclick = function () {
                var id = btn.getAttribute('data-recipe-delete');
                if (!window.confirm || window.confirm('Supprimer cette recette et ses ingrédients ?')) {
                    Menu.supprimerRecette(id); UI.toast('Recette supprimée'); rafraichirVue();
                }
            };
        });
        var searchIngredientMenu = UI.$('#menuSearchIngredient', main);
        if (searchIngredientMenu) searchIngredientMenu.oninput = function () {
            var value = searchIngredientMenu.value, pos = searchIngredientMenu.selectionStart;
            MenuViews.setIngredientSearch(value);
            rafraichirVue();
            var next = UI.$('#menuSearchIngredient', main);
            if (next) { next.focus(); try { next.setSelectionRange(pos, pos); } catch (e) { } }
        };
        var rayonIngredientMenu = UI.$('#menuFilterRayon', main);
        if (rayonIngredientMenu) rayonIngredientMenu.onchange = function () {
            MenuViews.setIngredientRayon(rayonIngredientMenu.value); rafraichirVue();
        };
        UI.$$('[data-menu-new-ingredient]', main).forEach(function (btn) {
            btn.onclick = function () { Views.feuilleMenuIngredient(null, rafraichirVue); };
        });
        UI.$$('[data-ing-edit]', main).forEach(function (btn) {
            btn.onclick = function () { Views.feuilleMenuIngredient(btn.getAttribute('data-ing-edit'), rafraichirVue); };
        });
        UI.$$('[data-ing-toggle]', main).forEach(function (btn) {
            btn.onclick = function () {
                var patch = {}, field = btn.getAttribute('data-ing-toggle');
                patch[field] = btn.getAttribute('data-ing-value') === 'true';
                Menu.majIngredientFlags(btn.getAttribute('data-ing-id'), patch);
                UI.toast(patch[field] ? 'Préférence enregistrée' : 'Préférence retirée');
                rafraichirVue();
            };
        });

        // ------------------------------------------------------ Écran Nutrition
        var dateNutrition = UI.$('#nutriDate', main);
        if (dateNutrition) {
            dateNutrition.onchange = function () {
                Views.setDateNutrition(dateNutrition.value);
                rafraichirVue();
            };
        }
        var btnAjoutNutrition = UI.$('#btnAjoutNutrition', main);
        if (btnAjoutNutrition) {
            btnAjoutNutrition.onclick = function () {
                Views.feuilleNutrition(etat.contexte, null, rafraichirVue);
            };
        }
        UI.$$('.btn-nutri-preset', main).forEach(function (btn) {
            btn.onclick = function () {
                var recette = M.REPAS_TYPES.find(function (x) { return x.cle === btn.getAttribute('data-nutri-preset'); });
                if (!recette) return;
                Store.addNutrition({
                    date: Views.getDateNutrition(), item: recette.nom,
                    protein_g: Math.round(recette.prot), carbs_g: Math.round(recette.gluc || 0),
                    fat_g: Math.round(recette.lip || 0), qty: 1
                });
                UI.toast('Ajouté au journal nutrition');
                rafraichirVue();
            };
        });
        UI.$$('.btn-nutri-edit', main).forEach(function (btn) {
            btn.onclick = function () {
                var id = btn.getAttribute('data-id');
                var item = Store.getNutrition().find(function (x) { return String(x.id || x.local_id) === String(id); });
                if (item) Views.feuilleNutrition(etat.contexte, item, rafraichirVue);
            };
        });
        UI.$$('.btn-nutri-delete', main).forEach(function (btn) {
            btn.onclick = function () {
                var id = btn.getAttribute('data-id');
                if (confirm('Supprimer cette entrée du journal nutrition ?')) {
                    Store.deleteNutrition(id);
                    UI.toast('Entrée supprimée');
                    rafraichirVue();
                }
            };
        });

        // ----------------------------------------------------------- Écran Apps
        var btnBascule = UI.$('#btnBasculeApp', main);
        if (btnBascule) {
            btnBascule.onclick = function () {
                var r = Store.getReglages();
                r.appCouranteWeb = r.appCouranteWeb === 'menus' ? 'suivi' : 'menus';
                Store.saveReglages(r);
                UI.haptic(10);
                rafraichirVue();
            };
        }

        var btnReload = UI.$('#btnReloadWeb', main);
        if (btnReload) {
            btnReload.onclick = function () {
                var frame = UI.$('#frameStreamlit', main);
                var chargement = UI.$('#chargementFrame', main);
                if (frame) {
                    if (chargement) chargement.style.display = 'flex';
                    frame.src = frame.src;
                }
            };
        }

        var btnOuvrirNav = UI.$('#btnOuvrirNav', main);
        if (btnOuvrirNav) {
            btnOuvrirNav.onclick = function () {
                var r = Store.getReglages();
                var url = r.appCouranteWeb === 'menus' ? r.urlMenus : r.urlSuivi;
                if (typeof root.Native !== 'undefined' && root.Native.openExternal) {
                    root.Native.openExternal(url);
                } else {
                    window.open(url, '_blank');
                }
            };
        }

        var frame = UI.$('#frameStreamlit', main);
        if (frame) {
            frame.onload = function () {
                var chargement = UI.$('#chargementFrame', main);
                if (chargement) chargement.style.display = 'none';
            };
        }
    }

    // ------------------------------------------------------------- Démarrage
    function demarrer() {
        // Barre de navigation inférieure
        var nav = UI.$('#nav');
        if (nav) {
            nav.addEventListener('click', function (e) {
                var b = e.target.closest ? e.target.closest('button[data-onglet]') : null;
                if (!b) return;
                naviguer(b.getAttribute('data-onglet'));
            });
        }

        // Bouton Rafraîchir
        var btnRefresh = UI.$('#btnRefresh');
        if (btnRefresh) {
            btnRefresh.addEventListener('click', function () {
                btnRefresh.classList.add('spin');
                UI.toast('Actualisation…');
                Net.synchroniserSupabase(function (resultat) {
                    btnRefresh.classList.remove('spin');
                    if (resultat && resultat.synchronise) {
                        UI.toast(resultat.erreurs && resultat.erreurs.length
                            ? 'Synchronisation partielle · ' + (resultat.enAttente || 0) + ' en attente'
                            : 'Synchronisation terminée');
                    } else if (resultat && resultat.raison) {
                        UI.toast(resultat.raison);
                    }
                    rafraichirVue();
                });
            });
        }

        // Bouton Réglages
        var btnReglages = UI.$('#btnReglages');
        if (btnReglages) {
            btnReglages.addEventListener('click', function () {
                Views.feuilleReglages(obtenirContexte(), function () {
                    rafraichirVue();
                });
            });
        }

        var ongletInitial = Store.getOnglet() || 'bord';
        if (ongletInitial === 'apps') ongletInitial = 'nutrition';
        naviguer(ongletInitial);

        surveillerReseau();
        demarrerSynchronise();
    }

    /**
     * 1.4 — Supabase fait autorité. Sans session on n'entre pas dans
     * l'application : l'écran de connexion (porté par la feuille Réglages)
     * s'ouvre. Hors ligne, le tampon local prend le relais et se déverse
     * dans Supabase au retour du réseau.
     */
    function demarrerSynchronise() {
        if (!Store.getRemoteSession()) {
            UI.toast('Connecte ton compte Supabase pour utiliser Équilibre');
            Views.feuilleReglages(obtenirContexte(), function () {
                rafraichirVue();
                demarrerSynchronise();
            });
            return;
        }

        // Une seule fois : le contenu local hérité de la 1.3.10 est poussé
        // vers Supabase, puis les caches locaux sont vidés.
        if (!Store.migrationFaite()) {
            var migres = Store.migrerDonneesLocalesVersFile();
            Store.marquerMigrationFaite();
            if (migres) UI.toast(migres + ' enregistrements locaux envoyés vers Supabase');
        }

        if (!Store.estEnLigne()) {
            UI.toast('Hors ligne · les saisies partiront à la reconnexion');
            return;
        }

        Net.synchroniserSupabase(function (resultat) {
            if (resultat && resultat.synchronise) rafraichirVue();
        });
    }

    /** Déverse le tampon local dans Supabase dès que la connexion revient. */
    function surveillerReseau() {
        Store.surveillerConnexion(function () {
            if (!Store.getRemoteSession()) return;
            UI.toast('Connexion rétablie · synchronisation…');
            Net.synchroniserSupabase(function (resultat) {
                if (resultat && resultat.raison) UI.toast(resultat.raison);
                else if (resultat && resultat.enAttente) {
                    UI.toast('Synchronisation partielle · ' + resultat.enAttente + ' en attente');
                } else {
                    UI.toast('Synchronisation terminée');
                }
                rafraichirVue();
            });
        }, 5000);
    }

    // Gestion du bouton retour Android
    function onBack() {
        var voile = UI.$('#voile');
        if (voile && voile.classList.contains('ouvert')) {
            UI.fermerFeuille();
            return true;
        }
        if (etat.onglet !== 'bord') {
            naviguer('bord');
            return true;
        }
        return false;
    }

    root.App = {
        demarrer: demarrer,
        naviguer: naviguer,
        rafraichir: rafraichirVue,
        onBack: onBack
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', demarrer);
    } else {
        demarrer();
    }
})(typeof window !== 'undefined' ? window : this);
