/* Moteur des menus : cache local, calculs de recettes et liste de courses.
   Les tables ingrédients/recettes/planification sont partagées; le suivi
   quotidien reste dans ses tables personnelles sr_* protégées par RLS. */
(function (root) {
    'use strict';
    var EQ = root.EQ = root.EQ || {};
    var Store = EQ.store;

    var TABLES = ['ingredients', 'recipes', 'recipe_ingredients', 'planned_meals'];
    var UNITES = ['g', 'kg', 'ml', 'cl', 'l', 'unité', 'tranche', 'gousse', 'sachet', 'boîte',
        'barquette', 'c. à soupe', 'c. à café', 'pincée'];
    var RAYONS = ['Fruits & Légumes', 'Boucherie & Poissonnerie', 'Frais & Produits Laitiers',
        'Épicerie Salée', 'Épicerie Sucrée', 'Boissons', 'Surgelés', 'Autre'];
    var JOURS = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche'];
    var PORTIONS = {
        oeuf: 110, steak: 130, boeuf: 130, veau: 130, porc: 130, agneau: 130, poulet: 130,
        dinde: 130, escalope: 130, saucisse: 120, chipolata: 120, 'cordon bleu': 100,
        nugget: 100, lardon: 50, jambon: 50, saucisson: 40, poisson: 130, cabillaud: 130,
        saumon: 130, colin: 130, merlu: 130, thon: 100, crevette: 100, tofu: 130,
        gnocchi: 150, raviole: 150, nouille: 80, lentille: 70, 'pois chiche': 70,
        'pomme de terre': 200, 'patate douce': 200, riz: 80, semoule: 80, quinoa: 80,
        boulgour: 80, pate: 80, comte: 40, emmental: 40, parmesan: 25, chevre: 40,
        mozzarella: 60, feta: 40, 'fromage blanc': 150, fromage: 40, yaourt: 125, skyr: 150,
        creme: 50, beurre: 10, huile: 10, lait: 200, pain: 60, biscotte: 30, cereale: 40,
        sucre: 20, chocolat: 20, amande: 20, noix: 20, compote: 100, fruit: 150,
        salade: 100, tomate: 150, concombre: 100, carotte: 150, courgette: 200,
        aubergine: 200, 'haricot vert': 150, epinard: 150, champignon: 150, brocoli: 150,
        oignon: 50, soupe: 250, gratin: 250, quiche: 200, pizza: 200, sauce: 30,
        ail: 3, persil: 5, farine: 60
    };
    var PORTIONS_RAYON = {
        'Boucherie & Poissonnerie': 130, 'Fruits & Légumes': 200,
        'Frais & Produits Laitiers': 40, 'Épicerie Salée': 80,
        'Épicerie Sucrée': 25, 'Surgelés': 150, 'Boissons': 250, 'Autre': 100
    };

    function nombre(v) {
        if (v == null || v === '' || v === 'null') return 0;
        var n = Number(String(v).replace(',', '.'));
        return Number.isFinite(n) ? n : 0;
    }
    function sansAccent(v) {
        return String(v || '').toLowerCase().replace(/[œ]/g, 'oe').replace(/[æ]/g, 'ae')
            .normalize('NFD').replace(/[\u0300-\u036f]/g, '');
    }
    function nom(ing) { return ing && (ing.nom_affiche || ing.name) || '?'; }
    function id(ligne) { return ligne && ligne.id != null ? String(ligne.id) : ''; }
    function lignes(table) { return Store.getMenuTable(table); }
    function ingredientParId() {
        var map = Object.create(null);
        lignes('ingredients').forEach(function (i) { map[String(i.id)] = i; });
        return map;
    }
    function recetteParId() {
        var map = Object.create(null);
        lignes('recipes').forEach(function (r) { map[String(r.id)] = r; });
        return map;
    }
    function lignesParRecette() {
        var map = Object.create(null);
        lignes('recipe_ingredients').forEach(function (l) {
            var key = String(l.recipe_id || '');
            if (!map[key]) map[key] = [];
            map[key].push(l);
        });
        return map;
    }
    function ingredients(terme) {
        var q = sansAccent(terme || '');
        return lignes('ingredients').filter(function (i) {
            return !q || sansAccent(nom(i)).indexOf(q) >= 0 || sansAccent(i.category).indexOf(q) >= 0;
        }).sort(function (a, b) { return sansAccent(nom(a)).localeCompare(sansAccent(nom(b))); });
    }
    function estPersonnel(ing) {
        if (ing && ing.est_a_moi != null) return !!ing.est_a_moi;
        // nom_affiche n'est PAS un marqueur de propriété : c'est le nom court
        // affiché. Avec la convention retenue, tous les aliments de la base en
        // portent un — les compter comme personnels les rendrait modifiables et
        // leur ferait perdre le badge « base de référence ».
        return !!(ing && (!ing.code_ciqual || ing.exclude_from_list || ing.is_recurrent));
    }
    function recettes(terme, inclurePseudo) {
        var q = sansAccent(terme || '');
        return lignes('recipes').filter(function (r) {
            var n = String(r.name || '');
            if (!inclurePseudo && /^\[(Ing|Txt)\]/i.test(n)) return false;
            return !q || sansAccent(n).indexOf(q) >= 0;
        }).sort(function (a, b) { return sansAccent(a.name).localeCompare(sansAccent(b.name)); });
    }
    function portionStandard(ing) {
        var q = nombre(ing && ing.quantite_recommandee);
        if (!q) return 0;
        var g = quantiteGrammes(q, ing.unite_recommandee || ing.unit, ing);
        if (!g) g = quantiteGrammes(q, 'unité', ing);
        return g || q * 100;
    }
    function poidsUnite(ing, unite) {
        var u = sansAccent(unite || (ing && ing.unit) || 'g').trim();
        var q = nombre(ing && ing.poids_piece_g);
        var densite = nombre(ing && ing.densite) || 1;
        if (['g', 'gr', 'gramme', 'grammes', ''].indexOf(u) >= 0) return 1;
        if (['kg', 'kilo', 'kilos', 'kilogramme', 'kilogrammes'].indexOf(u) >= 0) return 1000;
        if (u === 'ml') return densite;
        if (u === 'cl') return 10 * densite;
        if (['l', 'litre', 'litres'].indexOf(u) >= 0) return 1000 * densite;
        if (['c. a s.', 'c. a soupe', 'cuillere a soupe', 'cas'].indexOf(u) >= 0) return 15;
        if (['c. a c.', 'c. a cafe', 'cuillere a cafe', 'cac'].indexOf(u) >= 0) return 5;
        if (q > 0) return q;
        var mini = { gousse: 5, pincee: 1, tranche: 30, sachet: 100, boite: 250, pot: 125,
            verre: 200, botte: 100, barquette: 150, filet: 100, portion: 100 };
        if (mini[u]) return mini[u];
        var food = sansAccent(ing && ing.name);
        if (u.indexOf('oeuf') >= 0 || food.indexOf('oeuf') >= 0) return 50;
        if (food.indexOf('tranche') >= 0) return 30;
        return 0;
    }
    function quantiteGrammes(qte, unite, ing) {
        var q = nombre(qte);
        if (q <= 0) return 0;
        return q * poidsUnite(ing, unite);
    }
    function gramsLine(line, ing, pseudo) {
        var q = nombre(line.quantity);
        var u = String(line.unit || '').trim();
        var ppg = nombre(ing && ing.poids_piece_g);
        if (!u && !pseudo && q > 0 && q <= 10 && Math.floor(q) === q && ppg >= 20 && ppg <= 600) {
            return { grams: q * ppg, estimate: true };
        }
        var g = quantiteGrammes(q, u || (ing && ing.unit), ing);
        if (pseudo) {
            if (g >= 25) return { grams: g, estimate: false };
            var p = portionStandard(ing);
            return { grams: p ? q * p : g, estimate: !!p };
        }
        if (g) return { grams: g, estimate: false };
        var portion = portionStandard(ing);
        if (portion && q >= 1 && q <= 1000) return { grams: q * portion, estimate: true };
        return { grams: g, estimate: false };
    }
    // 1.4 — Un même aliment n'a pas les mêmes macros pesé cru ou pesé cuit :
    // 100 g de pâtes sèches font 364 kcal, 100 g de pâtes cuites 167. Le choix
    // se fait à la saisie, pas dans la fiche aliment.
    //
    // Les colonnes historiques (kcal_100g, proteines_100g…) restent la
    // référence et servent de repli : aucun aliment existant n'est
    // re-labellisé, et une valeur d'état absente retombe sur elles.
    function etatDefaut(ing) {
        return String((ing && ing.etat_defaut) || 'cru') === 'cuit' ? 'cuit' : 'cru';
    }

    function macrosPourEtat(ing, etat) {
        ing = ing || {};
        var voulu = etat === 'cru' || etat === 'cuit' ? etat : etatDefaut(ing);
        var suffixe = '_' + voulu;
        var out = { etat: voulu };
        ['kcal', 'proteines', 'glucides', 'lipides'].forEach(function (f) {
            var specifique = ing[f + '_100g' + suffixe];
            out[f] = specifique == null || specifique === '' ? ing[f + '_100g'] : specifique;
        });
        return out;
    }

    // Le choix cru/cuit n'est proposé que si au moins une valeur d'état existe.
    // Inventer un coefficient de conversion donnerait des nombres faux : la
    // perte d'eau va de +1 % (pomme de terre) à -58 % (pois chiche) selon
    // l'aliment et la cuisson.
    function aChoixEtat(ing) {
        if (!ing) return false;
        return ['kcal', 'proteines', 'glucides', 'lipides'].some(function (f) {
            return ing[f + '_100g_cru'] != null || ing[f + '_100g_cuit'] != null;
        });
    }

    function calculerRecette(recetteId) {
        var rec = recetteParId()[String(recetteId)];
        if (!rec) return null;
        var mapIng = ingredientParId();
        var lignesRec = lignesParRecette()[String(recetteId)] || [];
        var pseudo = /^\[Ing\]/i.test(String(rec.name || ''));
        var total = { kcal: 0, proteines: 0, glucides: 0, lipides: 0 };
        var poids = 0, detail = [], inconnues = [], estimees = [];
        lignesRec.forEach(function (l) {
            var ing = mapIng[String(l.ingredient_id)] || {};
            var calc = gramsLine(l, ing, pseudo);
            var g = calc.grams;
            poids += g;
            if (calc.estimate) estimees.push(nom(ing));
            var macros = macrosPourEtat(ing, l.etat);
            var sansValeurs = !nombre(macros.kcal) && !nombre(macros.proteines);
            if (sansValeurs) inconnues.push(nom(ing));
            var values = {};
            ['kcal', 'proteines', 'glucides', 'lipides'].forEach(function (field) {
                var val = nombre(macros[field]) * g / 100;
                total[field] += val;
                values[field] = Math.round(val * 10) / 10;
            });
            detail.push({ id: id(l), ingredient_id: String(l.ingredient_id || ''), name: nom(ing),
                quantity: nombre(l.quantity), unit: l.unit || '', grams: Math.round(g * 10) / 10,
                kcal: values.kcal, proteines: values.proteines, glucides: values.glucides,
                lipides: values.lipides, sans_valeurs: sansValeurs, etat: macros.etat,
                etat_modifiable: aChoixEtat(ing), etats_manuels: ing.etats_manuels === true,
                estimate: calc.estimate });
        });
        var parts = nombre(rec.base_servings) || 1;
        var roundedTotal = {}, perPart = {};
        Object.keys(total).forEach(function (k) {
            roundedTotal[k] = Math.round(total[k] * 10) / 10;
            perPart[k] = Math.round(total[k] / parts * 10) / 10;
        });
        return { id: String(rec.id), recipe: rec.name || '', instructions: rec.instructions || '',
            parts: parts, total: roundedTotal, par_part: perPart, poids_g: Math.round(poids * 10) / 10,
            lignes: detail, inconnues: Array.from(new Set(inconnues)), estimees: Array.from(new Set(estimees)) };
    }
    function recetteLignes(recetteId) {
        return (lignesParRecette()[String(recetteId)] || []).slice();
    }
    function portionPersonne(ing) {
        var text = sansAccent((ing && ing.nom_affiche || '') + ' ' + (ing && ing.name || ''));
        var found = Object.keys(PORTIONS).filter(function (k) { return text.indexOf(sansAccent(k)) >= 0; })
            .sort(function (a, b) { return text.indexOf(sansAccent(a)) - text.indexOf(sansAccent(b)) || b.length - a.length; });
        if (found.length) return PORTIONS[found[0]];
        return PORTIONS_RAYON[ing && ing.category] || 100;
    }
    function uniteParDefaut(ing) {
        var u = String((ing && (ing.unite_liste_courses || ing.unit)) || 'g');
        var n = sansAccent(u);
        var poids = nombre(ing && ing.poids_piece_g);
        if (['g', 'gr', 'gramme', 'grammes', 'kg', 'ml', 'cl', 'l'].indexOf(n) >= 0 && poids >= 25 && poids <= 400) return 'unité';
        return u;
    }
    function unitesProposees(ing) {
        var u = uniteParDefaut(ing), n = sansAccent(u), p = nombre(ing && ing.poids_piece_g);
        var out = [u, 'convives'];
        var compte = ['unite', 'tranche', 'gousse', 'boite', 'sachet', 'pot', 'barquette', 'botte', 'filet', 'verre', 'portion'];
        if (compte.indexOf(n) >= 0) out = out.concat(['unité', 'tranche', 'gousse', 'boîte', 'sachet', 'pot', 'portion']);
        if (['g', 'gramme', 'grammes', 'kg', 'kilo', 'kilos'].indexOf(n) >= 0) out = out.concat(['g', 'kg']);
        if (['ml', 'cl', 'l', 'litre', 'litres'].indexOf(n) >= 0) out = out.concat(['ml', 'cl', 'l']);
        if (p > 0) out = out.concat(['unité', 'g']);
        if (['ml', 'cl', 'l', 'litre', 'litres', 'g', 'kg', 'gramme', 'grammes'].indexOf(n) < 0 && p <= 0) out = out.concat(['g', 'kg']);
        out = out.concat(['c. à soupe', 'c. à café', 'pincée']);
        return out.filter(function (x, i) { return out.indexOf(x) === i; });
    }
    function convertir(q, source, cible, ing) {
        var from = sansAccent(source), to = sansAccent(cible), grams = quantiteGrammes(q, source, ing);
        var p = nombre(ing && ing.poids_piece_g);
        if (['g', 'gr', 'gramme', 'grammes'].indexOf(to) >= 0) return grams || nombre(q);
        if (['kg', 'kilo', 'kilos'].indexOf(to) >= 0) return (grams || nombre(q) * (from === 'kg' ? 1000 : 1)) / 1000;
        if (['ml', 'millilitre'].indexOf(to) >= 0) return grams || nombre(q);
        if (['cl', 'centilitre'].indexOf(to) >= 0) return (grams || nombre(q)) / 10;
        if (['l', 'litre', 'litres'].indexOf(to) >= 0) return (grams || nombre(q) * (from === 'l' ? 1000 : 1)) / 1000;
        if (['unite', 'piece', 'tranche', 'gousse', 'sachet', 'boite', 'barquette', 'pot', 'botte', 'filet', 'verre', 'portion'].indexOf(to) >= 0) {
            if (p > 0 && grams) return grams / p;
            return nombre(q);
        }
        return nombre(q);
    }
    function fmtQuantite(q, unite, pieces) {
        q = nombre(q);
        if (q <= 0) return '—';
        var u = String(unite || '').trim();
        var low = sansAccent(u);
        if (low === 'unite') u = q <= 1 ? '' : 'unités';
        else if (q > 1 && ['tranche', 'gousse', 'sachet', 'boite', 'pot', 'barquette', 'verre', 'filet', 'botte', 'pincee'].indexOf(low) >= 0 && !u.endsWith('s')) u += 's';
        var v = String(Number(q.toFixed(1))).replace('.', ',');
        var base = (v + ' ' + u).trim();
        if (q >= 1000 && ['g', 'gr', 'gramme', 'grammes'].indexOf(low) >= 0) base = String(Number((q / 1000).toFixed(2))).replace('.', ',') + ' kg';
        if (pieces) base += ' (' + pieces + ' unité' + (pieces > 1 ? 's' : '') + ')';
        return base;
    }
    function lundiDe(date) {
        var d = new Date(String(date || '').slice(0, 10) + 'T12:00:00');
        if (isNaN(d.getTime())) d = new Date();
        d.setDate(d.getDate() - ((d.getDay() + 6) % 7));
        return d;
    }
    function dateIso(d) { return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0'); }
    function dateAffiche(s, options) {
        var d = new Date(String(s).slice(0, 10) + 'T12:00:00');
        if (isNaN(d.getTime())) return String(s || '');
        return new Intl.DateTimeFormat('fr-FR', options || { weekday: 'long', day: '2-digit', month: '2-digit' }).format(d);
    }
    function fmtNombre(n) { return String(Number((Number(n) || 0).toFixed(1))).replace('.', ','); }
    function courseFormat(item) {
        var q = nombre(item.quantite);
        var u = item.unite || '';
        var pieces = null;
        var p = nombre(item.poids_piece_g);
        var declaredG = ['g', 'gr', 'gramme', 'grammes'].indexOf(sansAccent(item.unite_declaree)) >= 0;
        if (declaredG && p >= 25 && p <= 400 && ['Fruits & Légumes', 'Frais & Produits Laitiers', 'Boucherie & Poissonnerie', 'Surgelés', 'Autre'].indexOf(item.rayon) >= 0) {
            var forbidden = /coulis|sauce|puree|jus|confit|conserve|surgel|plat|gratin|poudre|farine|boisson|sirop|huile|vinaigre|alcool|vin|biere/i;
            var n = (item.nom || '') + ' ' + (item.nom_complet || '');
            var nb = Math.round(q / p);
            if (!forbidden.test(n) && q / p >= 0.6 && nb >= 1 && nb <= 8) {
                pieces = nb; q = nb * p;
            }
        }
        var discrete = ['unite', 'tranche', 'gousse', 'botte', 'sachet', 'boite', 'pot', 'barquette', 'verre', 'filet', 'pincee'].indexOf(sansAccent(u)) >= 0;
        if (q > 0 && discrete) q = Math.ceil(q);
        else if (q > 0 && ['g', 'gr', 'gramme', 'grammes', ''].indexOf(sansAccent(u)) >= 0) {
            var step = q < 100 ? 5 : (q < 500 ? 50 : (q < 1000 ? 100 : 250));
            q = Math.max(step, Math.round(q / step) * step);
        } else if (q > 0 && ['ml', 'cl', 'l', 'litre'].indexOf(sansAccent(u)) >= 0) q = Math.ceil(q);
        return { quantity: q, unit: u, pieces: pieces, text: fmtQuantite(q, u, pieces) };
    }
    function courses(du, au, suivreConvives) {
        var meals = lignes('planned_meals'), recMap = recetteParId(), lineMap = lignesParRecette(), ingMap = ingredientParId();
        var besoin = Object.create(null), nRepas = 0, convives = [];
        var duS = String(du || '').slice(0, 10), auS = String(au || '').slice(0, 10);
        var portionFoyer = 3.2;
        meals.forEach(function (m) {
            var d = String(m.date_menu || '').slice(0, 10);
            if (!d || d < duS || d > auS) return;
            var rid = String(m.recipe_id || ''), rec = recMap[rid];
            if (!rec || !rid) return;
            var rname = String(rec.name || ''), ls = lineMap[rid] || [], parts = nombre(rec.base_servings) || 1;
            var conv = nombre(m.servings) || nombre(m.nb_persons);
            if (conv > 0) convives.push(conv);
            var coef = conv > 0 && suivreConvives !== false ? conv / parts : portionFoyer / parts;
            if (/^\[Ing\]/i.test(rname)) {
                var l = ls[0] || {}, ing = ingMap[String(l.ingredient_id)] || ingMap[String(m.ingredient_id)] || {};
                var key = String(l.ingredient_id || m.ingredient_id || '');
                if (!key || ing.exclude_from_list) return;
                var listUnit = ing.unite_liste_courses || ing.unit || 'g';
                var q = nombre(m.ingredient_qty) || nombre(m.servings) || 1;
                var srcUnit = String(m.ingredient_unit || ing.unit || '').toLowerCase();
                var outQ;
                if (srcUnit.indexOf('convive') === 0 || srcUnit.indexOf('personne') === 0) {
                    var g = q * portionPersonne(ing);
                    outQ = convertir(g, 'g', listUnit, ing);
                } else if (srcUnit === 'unité' || srcUnit === 'unite') {
                    outQ = ['unité', 'unite', 'pièce', 'piece', 'tranche', 'boîte', 'boite', 'sachet', 'gousse', 'barquette'].indexOf(sansAccent(listUnit)) >= 0
                        ? q : (nombre(ing.poids_piece_g) > 0 ? convertir(q * nombre(ing.poids_piece_g), 'g', listUnit, ing) : q);
                } else {
                    outQ = convertir(q, srcUnit || ing.unit, listUnit, ing);
                }
                ajouterBesoin(besoin, key, ing, listUnit, outQ, rname);
                nRepas++;
                return;
            }
            ls.forEach(function (l) {
                var ing = ingMap[String(l.ingredient_id)] || {};
                if (!l.ingredient_id || ing.exclude_from_list) return;
                var listU = ing.unite_liste_courses || ing.unit || l.unit || 'g';
                var q = convertir(nombre(l.quantity), l.unit || ing.unit, listU, ing) * coef;
                ajouterBesoin(besoin, String(l.ingredient_id), ing, listU, q, rname);
            });
            nRepas++;
        });
        // Les aliments signalés comme récurrents apparaissent même sans repas planifié.
        lignes('ingredients').forEach(function (ing) {
            if (!ing.is_recurrent || ing.exclude_from_list || !ing.id) return;
            var k = String(ing.id);
            if (!besoin[k]) besoin[k] = { id: k, nom: nom(ing), nom_complet: ing.name || nom(ing),
                unite: ing.unite_recommandee || ing.unit || '', unitDeclared: ing.unit || '', quantity: nombre(ing.quantite_recommandee),
                rayon: ing.category || 'Autre', poids: nombre(ing.poids_piece_g), recipes: [], recurrent: true };
            else besoin[k].recurrent = true;
        });
        var prior = Store.getCourses(), priorMap = Object.create(null);
        prior.forEach(function (c) { priorMap[String(c.id)] = !!c.pris; });
        var weekId = duS || dateIso(lundiDe(dateIso(new Date())));
        var items = Object.keys(besoin).map(function (k) {
            var b = besoin[k];
            var f = courseFormat({ quantite: b.quantity, unite: b.unite, poids_piece_g: b.poids,
                unite_declaree: b.unitDeclared, rayon: b.rayon, nom: b.nom, nom_complet: b.nom_complet });
            return { id: weekId + '|' + k, ingredient_id: k, produit: b.nom, qte: f.text,
                quantity: f.quantity, unit: f.unit, rayon: b.rayon, pris: !!priorMap[weekId + '|' + k],
                recurrent: !!b.recurrent, recettes: b.recipes || [] };
        });
        items.sort(function (a, b) { return a.rayon.localeCompare(b.rayon, 'fr') || a.produit.localeCompare(b.produit, 'fr'); });
        return { items: items, repas: nRepas, convives: Array.from(new Set(convives)), du: duS, au: auS };
    }
    function ajouterBesoin(map, key, ing, unite, qte, recette) {
        if (!key) return;
        if (!map[key]) map[key] = { id: key, nom: nom(ing), nom_complet: ing.name || nom(ing),
            unite: unite, unitDeclared: ing.unit || '', quantity: 0, rayon: ing.category || 'Autre',
            poids: nombre(ing.poids_piece_g), recipes: [] };
        map[key].quantity += nombre(qte);
        if (recette && map[key].recipes.indexOf(recette) < 0) map[key].recipes.push(recette);
    }
    function jourFr(date) {
        var d = new Date(String(date).slice(0, 10) + 'T12:00:00');
        return JOURS[(d.getDay() + 6) % 7] || '';
    }
    function planned(date) {
        return lignes('planned_meals').filter(function (m) { return String(m.date_menu || '').slice(0, 10) === String(date).slice(0, 10); })
            .sort(function (a, b) { return String(a.meal_type || '').localeCompare(String(b.meal_type || ''), 'fr') || Number(a.id || 0) - Number(b.id || 0); });
    }
    function detailsRepas(m) {
        var rec = recetteParId()[String(m.recipe_id || '')];
        var calc = rec ? calculerRecette(rec.id) : null;
        var rawName = String(rec && rec.name || '');
        var nomR = rec ? rawName.replace(/^\[(Ing|Txt)\]\s*/i, '') : (m.name || '—');
        if (rec && rawName.toLowerCase().indexOf('[ing]') === 0) {
            var line = (lignesParRecette()[String(rec.id)] || [])[0] || {};
            var ing = ingredientParId()[String(line.ingredient_id || m.ingredient_id || '')] || {};
            var unit = String(m.ingredient_unit || line.unit || ing.unit || 'g');
            var qty = nombre(m.ingredient_qty) || nombre(m.servings) || 1;
            var portion = unit.toLowerCase().indexOf('convive') === 0 || unit.toLowerCase().indexOf('personne') === 0
                ? portionPersonne(ing) : 0;
            var grams = portion ? qty * portion : quantiteGrammes(qty, unit, ing);
            if (!grams) grams = portionStandard(ing) || 0;
            var parts = nombre(m.servings) || nombre(m.nb_persons) || 1;
            var total = {}, per = {};
            ['kcal', 'proteines', 'glucides', 'lipides'].forEach(function (field) {
                total[field] = Math.round(nombre(ing[field + '_100g']) * grams / 100 * 10) / 10;
                per[field] = Math.round(total[field] / parts * 10) / 10;
            });
            calc = { total: total, par_part: per, parts: parts, poids_g: grams, lignes: [], inconnues: [] };
        }
        return { recipe: rec, calc: calc, name: nomR };
    }
    function ajouterRepas(date, moment, type, valeur, convivesNb, quantite, unite) {
        var recs = recettes('', true), ing = null, rec = null;
        var d = String(date).slice(0, 10), meal = String(moment || 'Midi');
        var conv = Math.max(1, nombre(convivesNb) || 4);
        if (type === 'ingredient') {
            ing = lignes('ingredients').find(function (x) { return String(x.id) === String(valeur); });
            if (!ing) throw new Error('Choisis un ingrédient disponible hors ligne.');
            var pseudoName = '[Ing] ' + nom(ing);
            rec = recs.find(function (r) { return r.name === pseudoName; });
            if (!rec) {
                rec = Store.upsertMenu('recipes', { name: pseudoName, base_servings: 1, instructions: '' }, 'insert');
                Store.upsertMenu('recipe_ingredients', { recipe_id: rec.id, ingredient_id: ing.id,
                    quantity: 1, unit: ing.unit || 'g' }, 'insert');
            }
        } else if (type === 'texte') {
            var text = String(valeur || '').trim();
            if (!text) throw new Error('Saisis un nom pour le repas.');
            var freeName = '[Txt] ' + text;
            rec = recs.find(function (r) { return r.name === freeName; });
            if (!rec) rec = Store.upsertMenu('recipes', { name: freeName, base_servings: 1, instructions: '' }, 'insert');
        } else {
            rec = recs.find(function (r) { return String(r.id) === String(valeur); });
            if (!rec) throw new Error('Choisis une recette disponible hors ligne.');
        }
        var row = { date_menu: d, day: jourFr(d), meal_type: meal, recipe_id: rec.id,
            servings: conv, nb_persons: conv };
        if (type === 'ingredient') {
            row.ingredient_qty = Math.max(0, nombre(quantite) || 1);
            row.ingredient_unit = unite || ing.unit || 'g';
        }
        return Store.upsertMenu('planned_meals', row, 'insert');
    }
    function modifierRepas(m, patch) {
        var row = Object.assign({}, m, patch || {});
        if (row.date_menu) row.day = jourFr(row.date_menu);
        return Store.upsertMenu('planned_meals', row, 'update');
    }
    function supprimerRepas(m) { Store.deleteMenu('planned_meals', m._local_id || m.id); }
    function supprimerRecette(recipeId) {
        recetteLignes(recipeId).forEach(function (l) { Store.deleteMenu('recipe_ingredients', l.id); });
        Store.deleteMenu('recipes', recipeId);
    }
    function supprimerIngredient(ingredientId) {
        var uses = lignes('recipe_ingredients').filter(function (l) { return String(l.ingredient_id) === String(ingredientId); });
        if (uses.length) throw new Error('Cet ingrédient est encore utilisé dans ' + uses.length + ' recette(s).');
        Store.deleteMenu('ingredients', ingredientId);
    }
    function majIngredientFlags(ingredientId, patch) {
        var ing = lignes('ingredients').find(function (x) { return String(x.id) === String(ingredientId); });
        if (!ing) return;
        Store.upsertMenu('ingredients', Object.assign({}, ing, patch || {}), 'update');
    }

    EQ.menu = {
        TABLES: TABLES, UNITES: UNITES, RAYONS: RAYONS, JOURS: JOURS,
        rows: lignes, ingredients: ingredients, recettes: recettes, estPersonnel: estPersonnel,
        ingredientParId: ingredientParId, recetteParId: recetteParId, lignesParRecette: lignesParRecette,
        calculerRecette: calculerRecette,
        macrosPourEtat: macrosPourEtat,
        aChoixEtat: aChoixEtat,
        etatDefaut: etatDefaut, recetteLignes: recetteLignes, portionPersonne: portionPersonne,
        unitesProposees: unitesProposees, uniteParDefaut: uniteParDefaut, courses: courses,
        poidsUnite: poidsUnite, quantiteGrammes: quantiteGrammes,
        lundiDe: lundiDe, dateIso: dateIso, dateAffiche: dateAffiche, fmtNombre: fmtNombre,
        planned: planned, detailsRepas: detailsRepas, ajouterRepas: ajouterRepas,
        modifierRepas: modifierRepas, supprimerRepas: supprimerRepas,
        supprimerRecette: supprimerRecette, supprimerIngredient: supprimerIngredient,
        majIngredientFlags: majIngredientFlags, nomIngredient: nom, sansAccent: sansAccent,
        fmtQuantite: fmtQuantite
    };
})(typeof window !== 'undefined' ? window : this);
