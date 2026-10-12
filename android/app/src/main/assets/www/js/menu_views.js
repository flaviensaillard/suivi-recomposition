/* Interface locale des menus : planification, recettes, ingrédients et courses. */
(function (root) {
    'use strict';
    var EQ = root.EQ = root.EQ || {};
    var Menu = EQ.menu, Store = EQ.store, UI = EQ.ui, h = EQ.ui.h;
    var tab = 'planning';
    var debutPlanning = Menu.dateIso(new Date());
    var lundiCourses = Menu.dateIso(Menu.lundiDe(Menu.dateIso(new Date())));
    var modeCourses = 'convives';
    var rechercheRecette = '';
    var rechercheIngredient = '';
    var filtreRayon = 'Tous';
    var editionPlanDate = '';
    var editionRepas = '';
    var recetteOuverte = '';

    function attribut(x) { return h(String(x == null ? '' : x)); }
    function identRepas(m) { return String(m && (m._local_id || m.local_id || m.id) || ''); }
    function optionSelect(val, courant, label) {
        return '<option value="' + attribut(val) + '"' + (String(val) === String(courant) ? ' selected' : '') + '>' + h(label) + '</option>';
    }
    function semaine(date) {
        var d = new Date(String(date || debutPlanning).slice(0, 10) + 'T12:00:00');
        var jours = [];
        for (var i = 0; i < 7; i++) {
            var c = new Date(d); c.setDate(c.getDate() + i);
            jours.push(Menu.dateIso(c));
        }
        return jours;
    }
    function listeRecettes(courant) {
        return Menu.recettes('', false).map(function (r) {
            return optionSelect(r.id, courant, r.name || 'Recette');
        }).join('');
    }
    function listeIngredients(courant) {
        return Menu.ingredients('').map(function (i) {
            return optionSelect(i.id, courant, Menu.nomIngredient(i) + (i.category ? ' · ' + i.category : ''));
        }).join('');
    }
    function formulaireRepas(date, meal) {
        var edit = !!meal;
        var detail = edit ? Menu.detailsRepas(meal) : { recipe: null };
        var recipeName = detail.recipe && String(detail.recipe.name || '');
        var type = edit && /^\[Ing\]/i.test(recipeName) ? 'ingredient' :
            (edit && /^\[Txt\]/i.test(recipeName) ? 'texte' : 'recette');
        var linkedIng = edit ? (Menu.recetteLignes(meal.recipe_id)[0] || {}).ingredient_id : '';
        var mealKey = edit ? identRepas(meal) : '';
        var mealLabel = edit ? (detail.name || 'Repas') : '';
        var ing = linkedIng ? Menu.ingredientParId()[String(linkedIng)] : null;
        var unit = edit ? (meal.ingredient_unit || (ing && Menu.uniteParDefaut(ing)) || 'g') :
            (Menu.uniteParDefaut(Menu.ingredients('')[0]) || 'g');
        var qte = edit ? (meal.ingredient_qty == null ? 1 : meal.ingredient_qty) : 1;
        var typeOptions = optionSelect('recette', type, 'Recette') +
            optionSelect('ingredient', type, 'Ingrédient seul') + optionSelect('texte', type, 'Texte libre');
        var html = '<div class="card tight" data-menu-form="' + attribut(date) + '" data-meal-key="' + attribut(mealKey) + '" style="margin:8px 0 10px;">' +
            '<div class="lbl">' + (edit ? 'Modifier ce repas' : 'Ajouter un repas · ' + h(Menu.dateAffiche(date, { weekday: 'long', day: 'numeric', month: 'long' })) ) + '</div>' +
            '<div class="grille g2" style="margin-top:10px;">' +
                '<div class="champ"><label>Type</label><select data-pl-type ' + (edit ? 'disabled' : '') + '>' + typeOptions + '</select></div>' +
                '<div class="champ"><label>Moment</label><select data-pl-moment>' + optionSelect('Midi', meal && meal.meal_type || 'Midi', 'Midi') + optionSelect('Soir', meal && meal.meal_type || 'Midi', 'Soir') + '</select></div>' +
                '<div class="champ"><label>Convives</label><input data-pl-convives type="number" min="1" max="1000000" step="1" value="' + attribut(meal && (meal.servings || meal.nb_persons) || 4) + '"></div>' +
                '<div class="champ menu-plan-field" data-plan-field="recette"><label>Recette</label><select data-pl-recipe><option value="">Choisir une recette…</option>' + listeRecettes(meal && type === 'recette' ? meal.recipe_id : '') + '</select></div>' +
                '<div class="champ menu-plan-field" data-plan-field="ingredient"><label>Ingrédient</label><select data-pl-ingredient><option value="">Choisir un ingrédient…</option>' + listeIngredients(linkedIng) + '</select></div>' +
                '<div class="champ menu-plan-field" data-plan-field="ingredient"><label>Quantité</label><input data-pl-qte type="number" min="0" max="100000" step="0.5" value="' + attribut(qte) + '"></div>' +
                '<div class="champ menu-plan-field" data-plan-field="ingredient"><label>Unité de saisie</label><select data-pl-unite>' +
                    (function () { var values = ['convives'].concat(Menu.UNITES); if (values.indexOf(unit) < 0) values.unshift(unit); return values.map(function (u) { return optionSelect(u, unit, u); }).join(''); })() +
                '</select></div>' +
                '<div class="champ menu-plan-field" data-plan-field="texte"><label>Libellé</label><input data-pl-texte maxlength="120" value="' + (type === 'texte' ? attribut(mealLabel) : '') + '" placeholder="Restaurant, pique-nique…"></div>' +
            '</div>' +
            '<div class="grille g2">' +
                '<button class="btn" data-plan-save="' + attribut(date) + '" data-meal-key="' + attribut(mealKey) + '">' + (edit ? '💾 Enregistrer' : '＋ Ajouter ce repas') + '</button>' +
                '<button class="btn btn-flat" data-plan-cancel="' + attribut(date) + '">Annuler</button>' +
            '</div>' +
        '</div>';
        return html;
    }
    function ligneRepas(m) {
        var detail = Menu.detailsRepas(m), calc = detail.calc;
        var key = identRepas(m);
        var qte = m.ingredient_qty != null ? Menu.fmtNombre(m.ingredient_qty) + ' ' + (m.ingredient_unit || '') : '';
        var stats = calc ? Math.round(calc.par_part.proteines) + ' g P · ' + Math.round(calc.par_part.kcal) + ' kcal / part' : 'Repas libre';
        return '<div class="ligne" style="align-items:flex-start;">' +
            '<div class="pastille" style="background:rgba(245,196,81,.12);">' + (m.meal_type === 'Soir' ? '🌙' : '☀️') + '</div>' +
            '<div class="gr"><div class="tt">' + h(m.meal_type || 'Repas') + ' · ' + h(detail.name) + '</div>' +
                '<div class="st">' + h(stats) + (qte ? ' · ' + h(qte) : '') + ' · ' + h(m.servings || m.nb_persons || 4) + ' convives</div>' +
                (Menu.recettes('', true).find(function (r) { return String(r.id) === String(m.recipe_id); }) && /^\[(Ing|Txt)\]/i.test(String((Menu.recetteParId()[String(m.recipe_id)] || {}).name || '')) ? '<div class="st">Repas rapide · liste de courses recalculée</div>' : '') +
            '</div>' +
            '<div style="display:flex;gap:5px;flex-shrink:0;">' +
                (String(m.recipe_id || '') && Menu.recetteParId()[String(m.recipe_id)]
                    ? '<button class="iconbtn" data-meal-recipe="' + attribut(m.recipe_id) + '" title="Voir la recette">📖</button>' : '') +
                (calc ? '<button class="iconbtn" data-meal-log="' + attribut(key) + '" title="Ajouter au journal nutrition">＋</button>' : '') +
                '<button class="iconbtn" data-meal-edit="' + attribut(key) + '" title="Modifier">✎</button>' +
                '<button class="iconbtn" data-meal-delete="' + attribut(key) + '" title="Supprimer">×</button>' +
            '</div>' +
        '</div>';
    }
    function vuePlanning() {
        var days = semaine(debutPlanning), html = '<div class="card tight teal" style="margin-bottom:12px;">' +
            '<div class="lbl">Planning hebdomadaire du foyer</div><div class="st">Choisis les repas, les convives et les quantités. Les courses sont calculées hors ligne à partir des recettes.</div>' +
            '<div class="champ" style="margin:10px 0 0;"><label>Premier jour affiché</label><input id="menuDateDebut" type="date" value="' + attribut(debutPlanning) + '"></div>' +
            '</div>';
        days.forEach(function (date, index) {
            var rows = Menu.planned(date);
            var title = Menu.dateAffiche(date, { weekday: 'long', day: '2-digit', month: '2-digit' });
            html += '<div class="card jour-card" style="margin-bottom:10px;">' +
                '<div style="display:flex;justify-content:space-between;align-items:center;gap:8px;"><div style="font-weight:750;color:var(--gold);">' + h(title) + (date === Menu.dateIso(new Date()) ? ' · aujourd’hui' : '') + '</div><span class="badge mut">' + rows.length + ' repas</span></div>';
            if (!rows.length) html += '<div class="st" style="padding:8px 0;">Rien de prévu.</div>';
            rows.forEach(function (m) {
                var key = identRepas(m);
                html += ligneRepas(m);
                if (editionRepas === key) html += formulaireRepas(date, m);
            });
            if (editionPlanDate === date) html += formulaireRepas(date, null);
            else html += '<button class="btn btn-flat" data-plan-open="' + attribut(date) + '" style="margin-top:8px;">＋ Ajouter un repas</button>';
            html += '</div>';
        });
        var cpt = Store.getMenuTable('planned_meals').length;
        html += '<div class="st" style="text-align:center;padding:6px 0 12px;">' + cpt + ' repas au planning · dates conservées sur cet appareil et synchronisées à la prochaine connexion.</div>';
        return html;
    }
    function carteRecette(r) {
        var calc = Menu.calculerRecette(r.id), open = recetteOuverte === String(r.id);
        var html = '<div class="card card-recette" data-recipe-card data-search="' + attribut(r.name || '') + '" style="margin-bottom:10px;">' +
            '<div style="display:flex;justify-content:space-between;align-items:flex-start;gap:8px;">' +
                '<div style="font-weight:750;font-size:15px;">' + h(r.name || 'Recette') + '</div>' +
                '<span class="badge ok">' + (calc ? Math.round(calc.par_part.proteines) + ' g P / part' : 'Macros —') + '</span>' +
            '</div>' +
            '<div class="st" style="margin:5px 0 9px;">' + (calc ? Math.round(calc.par_part.kcal) + ' kcal · ' + Math.round(calc.par_part.glucides) + ' g G · ' + Math.round(calc.par_part.lipides) + ' g L par part · ' + calc.parts + ' parts' : 'Aucun ingrédient détaillé') + '</div>' +
            '<div class="grille g2">' +
                '<button class="btn btn-flat" data-recipe-view="' + attribut(r.id) + '">' + (open ? 'Masquer la fiche' : '📖 Voir la fiche') + '</button>' +
                '<button class="btn btn-flat" data-recipe-edit="' + attribut(r.id) + '">✎ Modifier</button>' +
            '</div>';
        if (open && calc) {
            html += '<div class="card flat tight" style="margin-top:9px;"><div class="lbl">Ingrédients</div>';
            if (!calc.lignes.length) html += '<div class="st">Aucune ligne d’ingrédient.</div>';
            calc.lignes.forEach(function (l) {
                html += '<div class="ligne"><div class="gr"><div class="tt">' + h(l.name) + '</div><div class="st">' + h(Menu.fmtNombre(l.quantity)) + ' ' + h(l.unit) + ' · ' + Math.round(l.grams) + ' g</div></div><div class="dr"><div class="a">' + Math.round(l.kcal) + ' kcal</div><div class="b">' + Math.round(l.proteines) + ' g P</div></div></div>';
            });
            if (r.instructions) html += '<div class="lbl" style="margin-top:10px;">Préparation</div><div class="st" style="white-space:pre-wrap;margin-top:5px;">' + h(String(r.instructions).replace(/\\n/g, '\n')) + '</div>';
            if (calc.inconnues.length) html += '<div class="badge warn" style="margin-top:9px;white-space:normal;">Valeurs nutritionnelles manquantes : ' + h(calc.inconnues.join(', ')) + '</div>';
            html += '</div>';
        }
        html += '<button class="btn btn-flat" data-recipe-delete="' + attribut(r.id) + '" style="margin-top:7px;color:var(--down);">🗑️ Supprimer</button></div>';
        return html;
    }
    function vueRecettes() {
        var rs = Menu.recettes(rechercheRecette, false), html = '<div class="card tight teal" style="margin-bottom:12px;">' +
            '<div class="lbl">Carnet de recettes</div><div class="st">Calcul des macros depuis les ingrédients et portions de la base enregistrée localement.</div>' +
            '<div class="champ" style="margin:10px 0;"><label>Rechercher</label><input id="menuSearchRecipe" type="search" value="' + attribut(rechercheRecette) + '" placeholder="pâtes, curry, poulet…"></div>' +
            '<button class="btn" data-menu-new-recipe>＋ Créer une recette</button></div>';
        if (!rs.length) html += '<div class="card"><div class="vide">Aucune recette trouvée. Synchronise la base ou crée ta première recette.</div></div>';
        rs.forEach(function (r) { html += carteRecette(r); });
        return html;
    }
    function vueIngredients() {
        var all = Menu.ingredients(rechercheIngredient);
        if (filtreRayon !== 'Tous') all = all.filter(function (i) { return (i.category || 'Autre') === filtreRayon; });
        var cap = rechercheIngredient ? 300 : 80;
        var visibles = all.slice(0, cap);
        var html = '<div class="card tight teal" style="margin-bottom:12px;">' +
            '<div class="lbl">Ingrédients &amp; base nutritionnelle</div><div class="st">' + Menu.rows('ingredients').length + ' ingrédients enregistrés · valeurs nutritionnelles pour 100 g.</div>' +
            '<div class="champ" style="margin:10px 0;"><label>Rechercher un ingrédient</label><input id="menuSearchIngredient" type="search" value="' + attribut(rechercheIngredient) + '" placeholder="lait, courgette, fromage…"></div>' +
            '<div class="champ"><label>Rayon</label><select id="menuFilterRayon"><option>Tous</option>' + Menu.RAYONS.map(function (r) { return optionSelect(r, filtreRayon, r); }).join('') + '</select></div>' +
            '<button class="btn" data-menu-new-ingredient>＋ Ajouter un ingrédient</button></div>';
        html += '<div class="st" style="margin:0 3px 8px;">' + visibles.length + ' sur ' + all.length + ' résultats' + (all.length > cap ? ' · saisis une recherche pour affiner' : '') + '.</div>';
        if (!visibles.length) html += '<div class="card"><div class="vide">Aucun ingrédient trouvé.</div></div>';
        visibles.forEach(function (i) {
            var owned = Menu.estPersonnel(i);
            html += '<div class="card tight" data-ingredient-card data-search="' + attribut(Menu.nomIngredient(i)) + '" style="margin-bottom:9px;">' +
                '<div style="display:flex;justify-content:space-between;gap:8px;align-items:flex-start;"><div><div style="font-weight:750;">' + h(Menu.nomIngredient(i)) + '</div><div class="st">' + h(i.category || 'Autre') + ' · ' + h(i.unit || 'g') + (owned ? ' · personnel' : ' · base de référence') + '</div></div><span class="badge mut">' + (i.code_ciqual ? 'Ciqual' : (owned ? 'À moi' : 'Base')) + '</span></div>' +
                '<div class="st" style="margin:8px 0;">' + (i.kcal_100g == null ? '—' : Math.round(Number(i.kcal_100g) || 0)) + ' kcal · P ' + (i.proteines_100g == null ? '—' : Menu.fmtNombre(i.proteines_100g)) + ' g · G ' + (i.glucides_100g == null ? '—' : Menu.fmtNombre(i.glucides_100g)) + ' g · L ' + (i.lipides_100g == null ? '—' : Menu.fmtNombre(i.lipides_100g)) + ' g / 100 g' + (i.poids_piece_g ? ' · ' + Menu.fmtNombre(i.poids_piece_g) + ' g / unité' : '') + '</div>' +
                '<div class="grille g2"><button class="btn btn-flat" data-ing-toggle="exclude_from_list" data-ing-id="' + attribut(i.id) + '" data-ing-value="' + (!i.exclude_from_list) + '">' + (i.exclude_from_list ? '🚪 Fond de placard ✓' : '🚪 Fond de placard') + '</button><button class="btn btn-flat" data-ing-toggle="is_recurrent" data-ing-id="' + attribut(i.id) + '" data-ing-value="' + (!i.is_recurrent) + '">' + (i.is_recurrent ? '🔁 Récurrent ✓' : '🔁 Récurrent') + '</button></div>' +
                (owned ? '<button class="btn btn-flat" data-ing-edit="' + attribut(i.id) + '" style="margin-top:7px;">✎ Modifier</button>' : '') + '</div>';
        });
        return html;
    }
    function vueCourses() {
        var start = Menu.dateIso(Menu.lundiDe(lundiCourses));
        var endDate = new Date(start + 'T12:00:00'); endDate.setDate(endDate.getDate() + 6);
        var end = Menu.dateIso(endDate);
        var data = Menu.courses(start, end, modeCourses === 'convives');
        Store.saveCourses(data.items);
        var restants = data.items.filter(function (x) { return !x.pris; }).length;
        var html = '<div class="card tight teal" style="margin-bottom:12px;">' +
            '<div class="lbl">Liste de courses automatique</div><div style="font-size:18px;font-weight:750;margin:3px 0;">' + restants + ' article' + (restants === 1 ? '' : 's') + ' à acheter</div>' +
            '<div class="st">Calculée depuis le planning et les recettes · fonctionne avec le cache hors ligne.</div>' +
            '<div class="champ" style="margin:10px 0 6px;"><label>Semaine</label><input id="courseDateStart" type="date" value="' + attribut(start) + '"></div>' +
            '<div class="champ"><label>Quantités calculées</label><select id="courseMode">' + optionSelect('convives', modeCourses, 'Selon les convives de chaque repas') + optionSelect('foyer', modeCourses, 'Portions du foyer (3,2 parts)') + '</select></div>' +
            '<div class="st">' + data.repas + ' repas planifié(s) · ' + h(Menu.dateAffiche(start, { day: '2-digit', month: '2-digit' })) + ' au ' + h(Menu.dateAffiche(end, { day: '2-digit', month: '2-digit' })) + '</div>' +
            '<button class="btn btn-flat" id="btnResetCourses" style="margin-top:8px;">↻ Décocher tous les articles</button></div>';
        if (!data.items.length) return html + '<div class="card"><div class="vide">Aucun repas ou article récurrent sur cette semaine. Ajoute un repas au planning pour générer les courses.</div></div>';
        var groups = {};
        data.items.forEach(function (x) { (groups[x.rayon] = groups[x.rayon] || []).push(x); });
        Object.keys(groups).sort(function (a, b) { return a.localeCompare(b, 'fr'); }).forEach(function (rayon) {
            html += '<div class="titre">' + h(rayon) + '<span class="n">' + groups[rayon].length + ' article' + (groups[rayon].length === 1 ? '' : 's') + '</span></div><div class="card tight">';
            groups[rayon].forEach(function (x) {
                var detail = x.recettes && x.recettes.length ? '<div class="st">' + h(x.recettes.slice(0, 2).join(', ')) + (x.recurrent ? ' · récurrent' : '') + '</div>' : (x.recurrent ? '<div class="st">Article récurrent</div>' : '');
                html += '<div class="ligne-course ' + (x.pris ? 'pris' : '') + '" data-course-id="' + attribut(x.id) + '"><div class="case-check ' + (x.pris ? 'coche' : '') + '">✓</div><div class="gr"><div class="tt item-nom">' + h(x.produit) + '</div><div class="st">' + h(x.qte) + '</div>' + detail + '</div></div>';
            });
            html += '</div>';
        });
        return html;
    }
    function vueMenus(ctx) {
        var counts = { ingredients: Menu.rows('ingredients').length, recipes: Menu.rows('recipes').length,
            planned: Menu.rows('planned_meals').length };
        var queued = Store.getSyncQueue().filter(function (x) { return String(x.table).indexOf('menu:') === 0; }).length;
        var connected = !!Store.getRemoteSession();
        var html = '<div class="card tight teal" style="margin-bottom:10px;"><div style="display:flex;justify-content:space-between;gap:8px;align-items:center;">' +
            '<div><div class="lbl">Données des menus</div><div class="st">' + counts.recipes + ' recettes · ' + counts.ingredients + ' ingrédients · ' + counts.planned + ' repas' + (queued ? ' · ' + queued + ' modification(s) en attente' : '') + '</div></div>' +
            '<button class="iconbtn" data-menu-sync title="Synchroniser avec Supabase">↻</button></div>' +
            (!connected && !counts.ingredients ? '<div class="st" style="margin-top:8px;">Connecte-toi à Supabase dans ⚙ Réglages puis synchronise une première fois pour télécharger les menus. Les modifications locales seront conservées hors ligne.</div>' : '') +
            '</div>';
        html += '<div class="chips" style="margin-bottom:9px;">' +
            '<button class="chip ' + (tab === 'planning' ? 'actif' : '') + '" data-menu-tab="planning">📅 Planning</button>' +
            '<button class="chip ' + (tab === 'recettes' ? 'actif' : '') + '" data-menu-tab="recettes">📖 Recettes</button>' +
            '<button class="chip ' + (tab === 'ingredients' ? 'actif' : '') + '" data-menu-tab="ingredients">🥕 Ingrédients</button>' +
            '<button class="chip ' + (tab === 'courses' ? 'actif' : '') + '" data-menu-tab="courses">🛒 Courses</button></div>';
        if (tab === 'planning') html += vuePlanning();
        else if (tab === 'recettes') html += vueRecettes();
        else if (tab === 'ingredients') html += vueIngredients();
        else html += vueCourses();
        return html;
    }

    function ligneIngredientEditeur(line) {
        var ingredients = Menu.ingredients('');
        var unit = line && line.unit || 'g';
        var units = Menu.UNITES.slice(); if (units.indexOf(unit) < 0) units.unshift(unit);
        var ingChoisi = ingredients.filter(function (i) { return line && String(i.id) === String(line.ingredient_id); })[0];
        return '<div class="card flat tight menu-recipe-line" data-line-id="' + attribut(line && line.id || '') + '" style="margin:7px 0;">' +
            '<div class="champ"><label>Ingrédient</label><select data-line-ingredient><option value="">Choisir…</option>' + ingredients.map(function (i) { return optionSelect(i.id, line && line.ingredient_id, Menu.nomIngredient(i)); }).join('') + '</select></div>' +
            // 1.4 — le même ingrédient n'a pas les mêmes macros pesé cru ou pesé
            // cuit. Le choix se fait ici, par ligne de recette.
            '<div class="champ" data-line-etat-box style="display:none;"><label>État pesé</label>' + selectEtat(line && line.etat) + '</div>' +
            '<div class="grille g2"><div class="champ"><label>Quantité</label><input data-line-quantity type="number" min="0" step="0.5" value="' + attribut(line && line.quantity != null ? line.quantity : 100) + '"></div>' +
            '<div class="champ"><label>Unité</label><select data-line-unit>' + units.map(function (u) { return optionSelect(u, unit, u); }).join('') + '</select></div></div>' +
            '<button class="btn btn-flat" data-line-remove>Supprimer cette ligne</button></div>';
    }

    function selectEtat(etat) {
        return '<select data-line-etat>' +
            '<option value="">' + (etat ? '' : 'Par défaut') + '</option>' +
            '<option value="cru"' + (etat === 'cru' ? ' selected' : '') + '>Cru</option>' +
            '<option value="cuit"' + (etat === 'cuit' ? ' selected' : '') + '>Cuit</option></select>';
    }

    // Le sélecteur n'est proposé que si l'ingrédient possède au moins une
    // valeur par état. Sans donnée réelle, on refuse d'inventer un coefficient.
    function majEtatLigne(box) {
        if (!box) return;
        var select = UI.$('[data-line-ingredient]', box);
        var etatBox = UI.$('[data-line-etat-box]', box);
        if (!select || !etatBox) return;
        var ing = Menu.ingredientParId()[String(select.value)];
        etatBox.style.display = Menu.aChoixEtat(ing) ? '' : 'none';
    }
    /**
     * Fiche de lecture d'une recette de la base synchronisée, ouvrable depuis
     * n'importe quel écran — en particulier depuis les plats du planning, où
     * il n'était pas possible de consulter la recette avant la 1.4.
     */
    function ouvrirFicheRecette(recipeId) {
        var rec = Menu.recetteParId()[String(recipeId)];
        if (!rec) { UI.toast('Recette absente de la base synchronisée'); return; }
        var calc = Menu.calculerRecette(recipeId);
        var corps = '<div class="card tight teal"><div class="lbl">Par part</div>' +
            '<div class="st">' + (calc
                ? Math.round(calc.par_part.kcal) + ' kcal · ' + Math.round(calc.par_part.proteines) + ' g P · ' +
                  Math.round(calc.par_part.glucides) + ' g G · ' + Math.round(calc.par_part.lipides) + ' g L · ' +
                  calc.parts + ' part(s)'
                : 'Aucun ingrédient détaillé : les macros ne peuvent pas être calculées.') + '</div></div>';
        if (calc) {
            corps += '<div class="card"><div class="lbl">Ingrédients</div>';
            if (!calc.lignes.length) corps += '<div class="st">Aucune ligne d’ingrédient.</div>';
            calc.lignes.forEach(function (l) {
                corps += '<div class="ligne"><div class="gr"><div class="tt">' + h(l.name) + '</div>' +
                    '<div class="st">' + h(Menu.fmtNombre(l.quantity)) + ' ' + h(l.unit) + ' · ' +
                    Math.round(l.grams) + ' g</div></div>' +
                    '<div class="dr"><div class="a">' + Math.round(l.kcal) + ' kcal</div>' +
                    '<div class="b">' + Math.round(l.proteines) + ' g P</div></div></div>';
            });
            corps += '</div>';
            if (rec.instructions) {
                corps += '<div class="card"><div class="lbl">Préparation</div>' +
                    '<div class="st" style="white-space:pre-wrap;">' +
                    h(String(rec.instructions)) + '</div></div>';
            }
            if (calc.inconnues.length) {
                corps += '<div class="badge warn" style="white-space:normal;">Valeurs nutritionnelles ' +
                    'manquantes pour : ' + h(calc.inconnues.join(', ')) + '</div>';
            }
        }
        UI.feuille({
            titre: rec.name || 'Recette',
            aide: 'Recette issue de la base Menus synchronisée.',
            html: corps,
            apresRendu: function () { }
        });
    }

    function ouvrirEditeurRecette(recipeId, apresSauvegarde) {
        var all = Menu.rows('recipes'), recipe = recipeId ? all.find(function (r) { return String(r.id) === String(recipeId); }) : null;
        var initial = recipe ? Menu.recetteLignes(recipe.id) : [];
        var lignesInitiales = initial.map(function (l) { return String(l.id); });
        var html = '<div class="champ"><label>Nom de la recette</label><input id="menuRecipeName" maxlength="120" value="' + attribut(recipe && recipe.name || '') + '" placeholder="Ex. Poulet au curry"></div>' +
            '<div class="grille g2"><div class="champ"><label>Parts de la recette</label><input id="menuRecipeParts" type="number" min="1" max="1000" step="1" value="' + attribut(recipe && recipe.base_servings || 4) + '"></div></div>' +
            '<div class="titre">Ingrédients</div><div id="menuRecipeLines">' + (initial.length ? initial.map(ligneIngredientEditeur).join('') : ligneIngredientEditeur(null)) + '</div>' +
            '<button class="btn btn-flat" id="btnMenuAddRecipeLine">＋ Ajouter un ingrédient</button>' +
            '<div class="champ" style="margin-top:12px;"><label>Préparation / étapes</label><textarea id="menuRecipeInstructions" rows="5" placeholder="Une étape par ligne…">' + h(recipe && recipe.instructions || '') + '</textarea></div>' +
            '<button class="btn btn-hero" id="btnMenuSaveRecipe">💾 Enregistrer la recette</button>';
        UI.feuille({ titre: recipe ? 'Modifier la recette' : 'Créer une recette', aide: 'Les changements sont enregistrés localement puis synchronisés avec Supabase.', html: html,
            apresRendu: function (racine, fermer) {
                function brancherLignes() {
                    Array.prototype.forEach.call(racine.querySelectorAll('[data-line-remove]'), function (b) {
                        b.onclick = function () { b.closest('.menu-recipe-line').remove(); };
                    });
                    Array.prototype.forEach.call(racine.querySelectorAll('.menu-recipe-line'), function (box) {
                        var sel = UI.$('[data-line-ingredient]', box);
                        if (sel) sel.onchange = function () {
                            var etat = UI.$('[data-line-etat]', box);
                            if (etat) etat.value = '';
                            majEtatLigne(box);
                        };
                        majEtatLigne(box);
                    });
                }
                brancherLignes();
                var add = UI.$('#btnMenuAddRecipeLine', racine);
                if (add) add.onclick = function () {
                    var box = UI.$('#menuRecipeLines', racine);
                    box.insertAdjacentHTML('beforeend', ligneIngredientEditeur(null));
                    brancherLignes();
                };
                var save = UI.$('#btnMenuSaveRecipe', racine);
                if (!save) return;
                save.onclick = function () {
                    var name = String(UI.$('#menuRecipeName', racine).value || '').trim();
                    var parts = Math.max(1, Number(UI.$('#menuRecipeParts', racine).value) || 4);
                    var instructions = String(UI.$('#menuRecipeInstructions', racine).value || '').trim();
                    var items = Array.prototype.map.call(racine.querySelectorAll('.menu-recipe-line'), function (box) {
                        var etatSel = UI.$('[data-line-etat]', box);
                        return { id: box.getAttribute('data-line-id') || '', ingredient_id: UI.$('[data-line-ingredient]', box).value,
                            quantity: Number(UI.$('[data-line-quantity]', box).value) || 0, unit: UI.$('[data-line-unit]', box).value || 'g',
                            etat: etatSel && etatSel.value || '' };
                    }).filter(function (x) { return x.ingredient_id && x.quantity > 0; });
                    if (!name) { UI.toast('Le nom de la recette est obligatoire'); return; }
                    if (!items.length) { UI.toast('Ajoute au moins un ingrédient avec une quantité'); return; }
                    var rec = Store.upsertMenu('recipes', { id: recipe && recipe.id, name: name, base_servings: parts, instructions: instructions }, recipe ? 'update' : 'insert');
                    var keep = {};
                    items.forEach(function (line) {
                        var row = { id: line.id || undefined, recipe_id: rec.id, ingredient_id: line.ingredient_id,
                            quantity: line.quantity, unit: line.unit, etat: line.etat || null };
                        var saved = Store.upsertMenu('recipe_ingredients', row, line.id ? 'update' : 'insert');
                        if (saved) keep[String(saved.id)] = true;
                    });
                    lignesInitiales.forEach(function (id) { if (!keep[id]) Store.deleteMenu('recipe_ingredients', id); });
                    UI.toast('Recette enregistrée sur cet appareil' + (Store.getRemoteSession() ? ' · synchronisation en attente' : ''));
                    fermer();
                    if (apresSauvegarde) apresSauvegarde();
                };
            }
        });
    }
    function ouvrirEditeurIngredient(ingredientId, apresSauvegarde) {
        var ingredient = ingredientId ? Menu.rows('ingredients').find(function (i) { return String(i.id) === String(ingredientId); }) : null;
        if (ingredient && !Menu.estPersonnel(ingredient)) { UI.toast('Les aliments de référence ne sont pas modifiables'); return; }
        var units = Menu.UNITES.slice();
        if (ingredient && ingredient.unit && units.indexOf(ingredient.unit) < 0) units.unshift(ingredient.unit);
        var categories = Menu.RAYONS.slice();
        if (ingredient && ingredient.category && categories.indexOf(ingredient.category) < 0) categories.unshift(ingredient.category);
        function val(key, fallback) { return ingredient && ingredient[key] != null ? ingredient[key] : fallback; }
        var html = '<div class="champ"><label>Nom</label><input id="menuIngName" maxlength="120" value="' + attribut(val('name', '')) + '"></div>' +
            '<div class="grille g2"><div class="champ"><label>Unité principale</label><select id="menuIngUnit">' + units.map(function (u) { return optionSelect(u, val('unit', 'g'), u); }).join('') + '</select></div>' +
            '<div class="champ"><label>Rayon</label><select id="menuIngCategory">' + categories.map(function (x) { return optionSelect(x, val('category', 'Autre'), x); }).join('') + '</select></div></div>' +
            '<div class="champ"><label>Poids d’une unité (g)</label><input id="menuIngWeight" type="number" min="0" max="5000" step="1" value="' + attribut(val('poids_piece_g', '')) + '"></div>' +
            '<div class="titre">Valeurs pour 100 g</div><div class="grille g2">' +
                '<div class="champ"><label>Calories (kcal)</label><input id="menuIngKcal" type="number" min="0" max="1000" step="1" value="' + attribut(val('kcal_100g', '')) + '"></div>' +
                '<div class="champ"><label>Protéines (g)</label><input id="menuIngProtein" type="number" min="0" max="100" step="0.1" value="' + attribut(val('proteines_100g', '')) + '"></div>' +
                '<div class="champ"><label>Glucides (g)</label><input id="menuIngCarbs" type="number" min="0" max="100" step="0.1" value="' + attribut(val('glucides_100g', '')) + '"></div>' +
                '<div class="champ"><label>Lipides (g)</label><input id="menuIngFat" type="number" min="0" max="100" step="0.1" value="' + attribut(val('lipides_100g', '')) + '"></div></div>' +
            '<div class="grille g2"><label class="st"><input type="checkbox" id="menuIngExclude" ' + (val('exclude_from_list', false) ? 'checked' : '') + '> Fond de placard (exclure des courses)</label>' +
                '<label class="st"><input type="checkbox" id="menuIngRecurrent" ' + (val('is_recurrent', false) ? 'checked' : '') + '> Récurrent chaque semaine</label></div>' +
            '<button class="btn btn-hero" id="btnMenuSaveIngredient" style="margin-top:12px;">💾 Enregistrer l’ingrédient</button>' +
            (ingredient ? '<button class="btn btn-flat" id="btnMenuDeleteIngredient" style="margin-top:7px;color:var(--down);">🗑️ Supprimer l’ingrédient</button>' : '');
        UI.feuille({ titre: ingredient ? 'Modifier l’ingrédient' : 'Ajouter un ingrédient', aide: 'Tes ajouts sont disponibles hors ligne; ils se synchronisent avec Supabase plus tard.', html: html,
            apresRendu: function (racine, fermer) {
                var save = UI.$('#btnMenuSaveIngredient', racine);
                if (!save) return;
                save.onclick = function () {
                    var name = String(UI.$('#menuIngName', racine).value || '').trim();
                    if (!name) { UI.toast('Le nom de l’ingrédient est obligatoire'); return; }
                    function valNum(sel) { var v = UI.$(sel, racine).value; return v === '' ? null : Number(v); }
                    var row = { id: ingredient && ingredient.id, name: name, nom_affiche: ingredient && ingredient.nom_affiche || null,
                        unit: UI.$('#menuIngUnit', racine).value, category: UI.$('#menuIngCategory', racine).value,
                        poids_piece_g: valNum('#menuIngWeight'), unite_liste_courses: ingredient && ingredient.unite_liste_courses || UI.$('#menuIngUnit', racine).value,
                        kcal_100g: valNum('#menuIngKcal'), proteines_100g: valNum('#menuIngProtein'),
                        glucides_100g: valNum('#menuIngCarbs'), lipides_100g: valNum('#menuIngFat'),
                        exclude_from_list: UI.$('#menuIngExclude', racine).checked,
                        is_recurrent: UI.$('#menuIngRecurrent', racine).checked,
                        source: ingredient && ingredient.source || 'mes ingrédients' };
                    Store.upsertMenu('ingredients', row, ingredient ? 'update' : 'insert');
                    UI.toast('Ingrédient enregistré sur cet appareil');
                    fermer(); if (apresSauvegarde) apresSauvegarde();
                };
                var del = UI.$('#btnMenuDeleteIngredient', racine);
                if (del) del.onclick = function () {
                    if (window.confirm && !window.confirm('Supprimer cet ingrédient ?')) return;
                    try {
                        Menu.supprimerIngredient(ingredient.id);
                        UI.toast('Ingrédient supprimé');
                        fermer(); if (apresSauvegarde) apresSauvegarde();
                    } catch (e) { UI.toast(e.message || 'Suppression impossible'); }
                };
            }
        });
    }

    EQ.menuViews = {
        vueMenus: vueMenus,
        setTab: function (value) { if (['planning', 'recettes', 'ingredients', 'courses'].indexOf(value) >= 0) tab = value; },
        setPlanningStart: function (value) { if (value) { debutPlanning = String(value).slice(0, 10); editionPlanDate = ''; editionRepas = ''; } },
        setCoursesStart: function (value) { if (value) lundiCourses = Menu.dateIso(Menu.lundiDe(value)); },
        setCoursesMode: function (value) { if (value === 'convives' || value === 'foyer') modeCourses = value; },
        setEditorPlan: function (date) { editionPlanDate = date || ''; editionRepas = ''; },
        setEditingMeal: function (key) { editionRepas = String(key || ''); editionPlanDate = ''; },
        cancelPlan: function () { editionPlanDate = ''; editionRepas = ''; },
        setRecipeSearch: function (value) { rechercheRecette = String(value || ''); },
        setIngredientSearch: function (value) { rechercheIngredient = String(value || ''); },
        setIngredientRayon: function (value) { filtreRayon = value || 'Tous'; },
        toggleRecipe: function (id) { recetteOuverte = recetteOuverte === String(id) ? '' : String(id); },
        ouvrirEditeurRecette: ouvrirEditeurRecette,
        ouvrirFicheRecette: ouvrirFicheRecette,
        ouvrirEditeurIngredient: ouvrirEditeurIngredient
    };
})(typeof window !== 'undefined' ? window : this);
