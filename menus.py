# -*- coding: utf-8 -*-
"""
MENUS & NUTRITION — lecture exacte de la base « gestion-menus ».

Après la migration, tes tables sont enfin complètes :
  • ingredients        : tes 153 ingrédients + les 3 339 aliments de la base française
                         (colonnes code_ciqual, kcal_100g, proteines_100g,
                          glucides_100g, lipides_100g)
  • recipes            : 104 recettes, toutes ramenées à 4 personnes
  • recipe_ingredients : 331 lignes, TOUTES reliées à un aliment de la base
  • planned_meals      : 79 repas planifiés (date_menu, meal_type, recipe_id…)

Ce module en déduit, sans aucune saisie :
  • les calories et macros d'une recette entière et d'une part
  • « ma part » (3 façons de la définir, avec un défaut proposé)
  • la liste de courses de la semaine, rangée par rayon
  • les repas du jour, prêts à être ajoutés au journal de protéines

Aucune écriture ici : que de la lecture et du calcul. Tu peux tester sans risque.
"""
from __future__ import annotations

import datetime as dt
import math

# ---------------------------------------------------------------------------
#  CONVERSIONS — les unités de ton application
# ---------------------------------------------------------------------------
#  Cuillères et centilitres : valeurs retenues par ton application.
CUIL_A_SOUPE = 15.0   # g
CUIL_A_CAFE = 5.0     # g
CL = 10.0             # g   (1 cl d'eau = 10 g)

UNITES_PIECE = (
    "unité", "unite", "pièce", "piece", "tranche", "sachet", "boîte", "boite",
    "gousse", "botte", "pot", "verre", "ramequin", "pincée", "pincee", "filet",
    "c. à s.", "c. à c.", "cuillère", "cuillere", "tasse", "bouquet", "brin",
)
UNITES_MASSE = ("g", "gr", "gramme", "grammes", "kg", "kilogramme")
UNITES_VOLUME = ("ml", "cl", "l", "litre", "litres", "centilitre")

#  Poids par défaut quand la ligne donne une petite unité sans poids de pièce
#  (« 1 pincée de poivre » pèse 0,5 g — pas 100 g).
POIDS_UNITE_MINI = {
    "pincée": 0.5, "pincee": 0.5, "gousse": 5.0, "brin": 2.0, "feuille": 1.0,
    "bouquet": 10.0, "filet": 5.0, "goutte": 0.05, "tasse": 200.0,
    "ramequin": 100.0, "c. à c.": 5.0, "c. à s.": 15.0, "cuillère": 5.0,
    "cuillere": 5.0, "sachet": 100.0, "pot": 125.0, "verre": 200.0,
}

#  Aliments qui se dosent en toutes petites quantités : on ne leur applique
#  jamais la « portion de référence » (100 g de cumin serait absurde).
MOTS_PETITES_QUANTITES = (
    "sel", "poivre", "épice", "epice", "herbe", "origan", "thym", "cumin", "curry",
    "paprika", "cannelle", "muscade", "curcuma", "levure", "bicarbonate", "bouillon",
    "concentré", "concentre", "moutarde", "vinaigre", "gélatine", "gelatine",
    "extrait", "arôme", "arome", "colorant", "sucre vanillé", "vanille",
)

POIDS_PIECE_DEFAUT = {
    "oeuf": 50.0, "œuf": 50.0, "tranche": 30.0, "gousse": 5.0, "sachet": 100.0,
    "boîte": 250.0, "boite": 250.0, "botte": 100.0, "pot": 125.0, "verre": 200.0,
}


def _nombre(v) -> float:
    """Convertit ce qui vient de la base en nombre, sans jamais planter."""
    if v in (None, "", "null"):
        return 0.0
    try:
        return float(str(v).replace(",", "."))
    except (TypeError, ValueError):
        return 0.0


def unite_est_piece(unite: str) -> bool:
    u = (unite or "").strip().lower()
    return u in UNITES_PIECE or u in POIDS_PIECE_DEFAUT


def quantite_en_grammes(qte, unite: str, ingredient: dict | None) -> float:
    """Convertit (quantité, unité) en grammes.

    ingredient : la ligne de la table « ingredients » (poids_piece_g, densite, unit).
    Renvoie 0 si on ne sait pas convertir — les totaux restent justes, jamais faux.
    """
    qte = _nombre(qte)
    if qte <= 0:
        return 0.0
    ing = ingredient or {}
    poids_piece = _nombre(ing.get("poids_piece_g"))
    densite = _nombre(ing.get("densite")) or 1.0
    u = (unite or ing.get("unit") or "").strip().lower()
    if u in ("", "null", "none"):
        u = (ing.get("unit") or "g").strip().lower()

    if u in ("g", "gr", "gramme", "grammes", ""):
        return qte
    if u in ("kg", "kilogramme", "kilogrammes"):
        return qte * 1000.0
    if u in ("ml",):
        return qte * densite
    if u in ("cl",):
        return qte * CL * densite
    if u in ("l", "litre", "litres"):
        return qte * 1000.0 * densite
    if u in ("c. à s.", "c. à soupe", "cuillère à soupe", "cuillere a soupe", "cas"):
        return qte * CUIL_A_SOUPE
    if u in ("c. à c.", "c. à café", "cuillère à café", "cuillere a cafe", "cac"):
        return qte * CUIL_A_CAFE
    # unités « comptables » : unité, tranche, gousse, boîte…
    if poids_piece > 0:
        return qte * poids_piece
    mini = POIDS_UNITE_MINI.get(u)
    if mini:
        return qte * mini
    for cle, g in POIDS_PIECE_DEFAUT.items():
        if cle in (ing.get("name") or "").lower():
            return qte * g
    return 0.0


# ---------------------------------------------------------------------------
#  CALCUL DES MACROS
# ---------------------------------------------------------------------------
CHAMPS_NUTR = ("kcal", "proteines", "glucides", "lipides")


def portion_standard(ing: dict | None) -> float:
    """Portion de référence d'un aliment, en grammes (la valeur de ta base).

    C'est le « quantite_recommandee » + « unite_recommandee » de ta table :
    par exemple 100 g pour les aliments Ciqual, 200 g pour un brocoli,
    0,5 unité (150 g) pour une aubergine.
    """
    ing = ing or {}
    q = _nombre(ing.get("quantite_recommandee"))
    if not q:
        return 0.0
    u = ing.get("unite_recommandee") or ing.get("unit")
    g = quantite_en_grammes(q, u, ing)
    if not g:
        g = quantite_en_grammes(q, "unité", ing)
    if not g:
        g = q * 100.0          # dernier recours : une portion = 100 g
    return g or 0.0


def est_pseudo_ingredient(nom) -> bool:
    """Vrai pour les entrées « [Ing] Pâtes », « [Txt] Salade » du planning.

    Pour ces entrées, la quantité enregistrée est un NOMBRE DE PERSONNES,
    pas un poids : c'est la cause du bug de comptage des protéines.
    """
    return str(nom or "").strip().lower().startswith("[ing]")


def grammes_de_ligne(l: dict, ing: dict | None, pseudo: bool = False) -> tuple:
    """Grammes d'une ligne de recette + drapeau « quantité estimée ».

    `pseudo=True` pour les entrées « [Ing] X » : la quantité est un nombre de
    personnes → on la multiplie par la portion de référence de l'aliment.
    Sinon on convertit normalement, et si l'unité ne donne rien on retombe
    sur la portion de référence au lieu de compter 0 g en silence.
    """
    ing = ing or {}
    q = _nombre(l.get("quantity"))
    u = str(l.get("unit") or "").strip().lower()
    vide = u in ("", "null", "none")
    ppg = _nombre(ing.get("poids_piece_g"))
    petit = any(mot in (ing.get("name") or "").lower() for mot in MOTS_PETITES_QUANTITES)

    # --- « 1 oignon » écrit sans unité = 1 PIÈCE (80 g), pas 1 gramme.
    #     Uniquement pour de petits nombres entiers : « 500 » sans unité reste 500 g.
    if vide and not pseudo and 0 < q <= 10 and q == int(q) and 20 <= ppg <= 600:
        return q * ppg, True

    g = quantite_en_grammes(q, l.get("unit"), ing)
    if pseudo:
        if g >= 25:                       # une vraie quantité (300 g, 4 œufs…)
            return g, False
        p = portion_standard(ing)
        if p:
            return q * p, True
        return g, False
    if g:
        return g, False
    # unité inexploitable : on retombe sur la portion de référence, sauf pour
    # les aliments qui se dosent en pincées (toujours comptés très petit)
    if petit:
        mini = POIDS_UNITE_MINI.get(u) or 1.0
        return q * mini, True
    p = portion_standard(ing)
    if p and 2 <= q <= 12:
        return q * p, True
    return g, False


def nom_court(ing: dict | None) -> str:
    """Nom familier s'il existe (« Boeuf haché »), sinon le nom complet de la base."""
    ing = ing or {}
    return ing.get("nom_affiche") or ing.get("name") or "?"


def _vider() -> dict:
    return {c: 0.0 for c in CHAMPS_NUTR}


def _ajouter(totaux: dict, valeur_100g, grammes: float, champ: str):
    v = _nombre(valeur_100g)
    if v and grammes:
        totaux[champ] += v * grammes / 100.0


def calculer_recette(lignes: list[dict], ing_par_id: dict, base_servings=None,
                     nom_recette=None) -> dict:
    """Calcule les macros d'une recette à partir de ses lignes d'ingrédients.

    lignes        : [{ingredient_id, quantity, unit}, …]
    ing_par_id    : {ingredient_id: {name, poids_piece_g, densite, unit,
                                     kcal_100g, proteines_100g, …}}
    base_servings : nombre de parts de la recette (4 après la migration)
    nom_recette   : nom de la recette — sert à reconnaître les entrées
                    « [Ing] X », où la quantité est un nombre de personnes

    Renvoie un dict :
      total      : macros de la recette entière
      par_part   : macros d'une part
      poids_g    : poids total reconstitué
      lignes     : détail par ingrédient (pour l'affichage)
      inconnues  : ingrédients sans valeurs nutritionnelles
      estimees   : lignes dont la quantité a été déduite (portion standard)
    """
    pseudo = est_pseudo_ingredient(nom_recette)
    total = _vider()
    poids = 0.0
    detail = []
    inconnues = []
    estimees = []

    for l in lignes:
        ing = ing_par_id.get(l.get("ingredient_id")) or {}
        if not ing and l.get("ingredient_id"):
            inconnues.append("aliment introuvable dans la base")
        g, estime = grammes_de_ligne(l, ing, pseudo)
        if estime:
            estimees.append(nom_court(ing))
        poids += g
        if not ing.get("kcal_100g") and not ing.get("proteines_100g"):
            inconnues.append(nom_court(ing))
        for champ in CHAMPS_NUTR:
            _ajouter(total, ing.get(f"{champ}_100g"), g, champ)
        detail.append(dict(nom=ing.get("name"), nom_court=nom_court(ing), grammes=round(g, 1),
                           unite=l.get("unit"), quantite=_nombre(l.get("quantity")),
                           kcal=round(_nombre(ing.get("kcal_100g")) * g / 100.0, 1),
                           proteines=round(_nombre(ing.get("proteines_100g")) * g / 100.0, 1),
                           glucides=round(_nombre(ing.get("glucides_100g")) * g / 100.0, 1),
                           lipides=round(_nombre(ing.get("lipides_100g")) * g / 100.0, 1),
                           # « sans_valeurs » : l'aliment n'a aucune donnée nutritionnelle.
                           # Ses grammes comptent dans le poids, mais pas dans les macros :
                           # c'est LA cause d'un total de protéines trop bas.
                           sans_valeurs=not (ing.get("kcal_100g") or ing.get("proteines_100g")),
                           estime=estime))

    parts = _nombre(base_servings) or 1.0
    par_part = {c: total[c] / parts for c in CHAMPS_NUTR}
    return dict(total={c: round(total[c], 1) for c in CHAMPS_NUTR},
                par_part={c: round(par_part[c], 1) for c in CHAMPS_NUTR},
                poids_g=round(poids, 1), parts=parts,
                lignes=detail, inconnues=sorted(set(inconnues)),
                estimees=sorted(set(estimees)))


def ma_part(calcul: dict, mode: str = "parts", valeur: float = 1.0,
            portion_foyer: float = 1.0) -> dict:
    """Calcule les macros de « ma part » de 3 façons possibles.

    mode « parts »     : valeur = nombre de parts prises (défaut 1)
    mode « pourcent »  : valeur = part du plat en % (défaut 25 % = 1 part sur 4)
    mode « poids »     : valeur = poids servi en grammes
    portion_foyer      : part d'un adulte dans le plat (les enfants comptant moins),
                         sert seulement au mode « pourcent » par défaut.

    Renvoie {fraction, macros, libelle}.
    """
    parts = calcul.get("parts") or 1.0
    mode = (mode or "parts").strip().lower()

    if mode.startswith("poids"):
        g = max(0.0, _nombre(valeur))
        poids = calcul.get("poids_g") or 0.0
        fraction = (g / poids) if poids else 0.0
        libelle = f"{g:.0f} g servis"
    elif mode.startswith("pour") or mode == "%":
        fraction = max(0.0, _nombre(valeur)) / 100.0
        libelle = f"{_nombre(valeur):.0f} % du plat"
    else:  # parts
        n = max(0.0, _nombre(valeur))
        fraction = n / parts if parts else 0.0
        libelle = f"{n:g} part" + ("s" if n > 1 else "")

    macros = {c: round(calcul["total"][c] * fraction, 1) for c in CHAMPS_NUTR}
    return dict(fraction=fraction, macros=macros, libelle=libelle,
                grammes=round((calcul.get("poids_g") or 0) * fraction, 1))


DESSERTS = ("glace", "sorbet", "yaourt", "fromage blanc", "compote", "fruit", "gâteau",
            "gateau", "crème", "creme", "chocolat", "tarte", "quatre-quarts", "biscuit")
PLATS_LEGERS = ("salade", "soupe", "velouté", "veloute", "potage", "crudité", "crudite")


def part_defaut(base_servings, nom: str = "", moment: str = "") -> float:
    """Nombre de parts proposé par défaut, selon ce qu'est le plat.

    • un dessert ou un laitage      → 0,5 part (on en mange moins)
    • une soupe ou une salade       → 1 part
    • un plat principal             → 1 part
    C'est une proposition : tu peux toujours la changer en un appui.
    """
    n = (nom or "").lower()
    if any(m in n for m in DESSERTS):
        return 0.5
    return 1.0


def portion_foyer(adultes: float = 2.0, enfants: float = 2.0,
                  coef_enfant: float = 0.6) -> float:
    """Portions mangées par la famille, en équivalents « part d'adulte ».

    Chez toi : 2 adultes + 2 enfants × 0,6  →  3,2 portions.
    Une recette recadrée sur 4 parts laisse donc un petit reste (ou une part
    plus généreuse) : c'est normal et c'est voulu.
    """
    return adultes + enfants * coef_enfant


# ---------------------------------------------------------------------------
#  ACCÈS AUX DONNÉES
# ---------------------------------------------------------------------------
TABLES = ("ingredients", "recipes", "recipe_ingredients", "planned_meals")
PAGE_SUPABASE = 1000  # Supabase ne renvoie que 1 000 lignes par requête


class MenusStore:
    """Lecture de la base de menus (tes 4 tables), avec pagination complète.

    Fonctionne de deux façons :
      • client = le client Supabase connecté  → tes vraies données
      • client = None                          → données de démonstration locales
    """

    def __init__(self, client=None):
        self.client = client
        self._cache: dict[str, list] = {}
        self.erreur: str | None = None

    @property
    def erreurs(self) -> list[str]:
        """Toutes les erreurs de lecture rencontrées (pour le diagnostic)."""
        e = getattr(self, "erreur", None)
        return [e] if e else []

    # -- outils
    def _tous(self, table: str, colonnes: str = "*", ordre: str | None = None) -> list[dict]:
        """Lit toute une table, en entier (Supabase ne renvoie que 1 000 lignes à la fois).

        On demande TOUJOURS toutes les colonnes (« * ») : c'est ce qui manquait —
        une colonne demandée par erreur empêchait de retrouver les identifiants.
        """
        # garde-fous : un argument mal passé ne doit JAMAIS casser une lecture
        if not isinstance(colonnes, str) or not colonnes.strip():
            colonnes = "*"
        if not isinstance(ordre, str) or not ordre.strip():
            ordre = None
        if table in self._cache:
            return self._cache[table]
        if self.client is None:
            return []
        lignes: list[dict] = []
        debut = 0
        echec = None
        while True:
            try:
                q = self.client.table(table).select(colonnes)
                if ordre:
                    q = q.order(ordre)
                if debut == 0:
                    # 1re page : on demande simplement « les N premières lignes »
                    res = q.limit(PAGE_SUPABASE).execute()
                else:
                    res = q.range(debut, debut + PAGE_SUPABASE - 1).execute()
                lot = res.data or []
            except Exception as e:                       # table absente, droits, réseau…
                echec = f"{table} : {type(e).__name__} — {e}"
                break
            if not lot:
                break
            lignes.extend(lot)
            if len(lot) < PAGE_SUPABASE:
                break
            debut += PAGE_SUPABASE
        if echec:
            # IMPORTANT : on ne met JAMAIS une lecture ratée en cache.
            # C'est ce qui affichait « 0 ligne » alors que la base répondait bien.
            self.erreur = echec
            return lignes
        self._cache[table] = lignes
        return lignes

    def vider_cache(self):
        self._cache.clear()
        self.erreur = None

    # -- collections
    def ingredients(self) -> list[dict]:
        return self._tous("ingredients", "*", order_col("ingredients"))

    def recettes(self) -> list[dict]:
        return self._tous("recipes", "*", order_col("recipes"))

    def lignes(self) -> list[dict]:
        return self._tous("recipe_ingredients", "*", order_col("recipe_ingredients"))

    def planning(self) -> list[dict]:
        return self._tous("planned_meals", "*", order_col("planned_meals"))

    # -- index
    def ing_par_id(self) -> dict:
        return {i.get("id"): i for i in self.ingredients()}

    def recette_par_id(self) -> dict:
        return {r.get("id"): r for r in self.recettes()}

    def lignes_par_recette(self) -> dict:
        out: dict = {}
        for l in self.lignes():
            out.setdefault(l.get("recipe_id"), []).append(l)
        return out

    # -- calculs
    def recette(self, recipe_id) -> dict | None:
        rec = self.recette_par_id().get(recipe_id)
        if not rec:
            return None
        lgn = self.lignes_par_recette().get(recipe_id, [])
        calc = calculer_recette(lgn, self.ing_par_id(), rec.get("base_servings"),
                                nom_recette=rec.get("name"))
        calc["recette"] = rec.get("name")
        calc["instructions"] = rec.get("instructions")
        calc["id"] = recipe_id
        return calc

    def repas_du_jour(self, jour: dt.date | None = None) -> list[dict]:
        """Les repas prévus ce jour-là, avec leurs macros."""
        jour = jour or dt.date.today()
        cible = str(jour)
        recettes = self.recette_par_id()
        lignes = self.lignes_par_recette()
        ings = self.ing_par_id()
        out = []
        for m in self.planning():
            if str(m.get("date_menu") or "")[:10] != cible:
                continue
            rid = m.get("recipe_id")
            rec = recettes.get(rid) or {}
            repas = dict(heure=m.get("meal_type"), jour=m.get("day"),
                         recette=rec.get("name") or m.get("ingredient_id") or "—",
                         recipe_id=rid, nb_persons=m.get("nb_persons") or m.get("servings"),
                         id=m.get("id"))
            if rid and rid in recettes:
                repas["calcul"] = calculer_recette(lignes.get(rid, []), ings,
                                                   rec.get("base_servings"),
                                                   nom_recette=rec.get("name"))
            out.append(repas)
        ordre = {"Midi": 0, "Soir": 1}
        return sorted(out, key=lambda r: (ordre.get(r["heure"], 2), r["recette"]))

    def semaine(self, debut: dt.date | None = None, jours: int = 7) -> list[dict]:
        debut = debut or dt.date.today()
        return [dict(jour=debut + dt.timedelta(days=i),
                     repas=[r for r in self.planning()
                            if str(r.get("date_menu") or "")[:10] == str(debut + dt.timedelta(days=i))]
                     ) for i in range(jours)]

    # ------------------------------------------------------------------
    #  LISTE DE COURSES
    # ------------------------------------------------------------------
    def courses(self, du: dt.date, au: dt.date, pour_foyer: bool = True,
                adultes: float = 2.0, enfants: float = 2.0,
                coef_enfant: float = 0.6) -> dict:
        """Liste de courses entre deux dates, rangée par rayon.

        Les quantités des recettes sont additionnées (recette par recette),
        puis ajustées aux portions du foyer si « pour_foyer ».
        Les articles cochés « ne pas mettre dans la liste » sont exclus ;
        les articles récurrents sont toujours ajoutés.
        """
        recettes = self.recette_par_id()
        lignes = self.lignes_par_recette()
        ings = self.ing_par_id()
        portion = portion_foyer(adultes, enfants, coef_enfant) if pour_foyer else None

        besoin: dict = {}
        repas_comptes = 0
        for m in self.planning():
            d = str(m.get("date_menu") or "")[:10]
            if not d or not (str(du) <= d <= str(au)):
                continue
            rid = m.get("recipe_id")
            if not rid or rid not in recettes:
                continue
            repas_comptes += 1
            rec = recettes[rid]
            parts = _nombre(rec.get("base_servings")) or 1.0
            coef = (portion / parts) if portion else 1.0
            for l in lignes.get(rid, []):
                ing = ings.get(l.get("ingredient_id")) or {}
                if ing.get("exclude_from_list"):
                    continue
                q = _nombre(l.get("quantity")) * coef
                u = l.get("unit") or ing.get("unit")
                cle = l.get("ingredient_id")
                if cle not in besoin:
                    besoin[cle] = dict(nom=nom_court(ing), nom_complet=ing.get("name"),
                                       unite=u, unite_declaree=ing.get("unit"),
                                       quantite=0.0, rayon=ing.get("category") or "Autre",
                                       quantite_recommandee=ing.get("quantite_recommandee"),
                                       unite_recommandee=ing.get("unite_recommandee"),
                                       poids_piece_g=ing.get("poids_piece_g"),
                                       recettes=[])
                besoin[cle]["quantite"] += q
                nom_rec = rec.get("name")
                if nom_rec and nom_rec not in besoin[cle]["recettes"]:
                    besoin[cle]["recettes"].append(nom_rec)

        # articles récurrents (pain, lait, PQ…) : toujours dans la liste
        for ing in self.ingredients():
            if ing.get("is_recurrent") and not ing.get("exclude_from_list"):
                cle = ing.get("id")
                besoin.setdefault(cle, dict(nom=nom_court(ing), nom_complet=ing.get("name"),
                                            unite=ing.get("unit"), unite_declaree=ing.get("unit"),
                                            quantite=0.0, rayon=ing.get("category") or "Autre",
                                            quantite_recommandee=ing.get("quantite_recommandee"),
                                            unite_recommandee=ing.get("unite_recommandee"),
                                            poids_piece_g=ing.get("poids_piece_g"),
                                            recettes=[]))
                besoin[cle]["recurrent"] = True

        # arrondi « achetable »
        for v in besoin.values():
            arrondi_achat(v)
            v["nb_recettes"] = len(v["recettes"])
        rayons: dict = {}
        for v in besoin.values():
            rayons.setdefault(v["rayon"], []).append(v)
        for r in rayons:
            rayons[r].sort(key=lambda x: (not x.get("recurrent"), x["nom"].lower()))
        return dict(rayons=rayons, repas=repas_comptes,
                    portions_foyer=portion, du=str(du), au=str(au))


def order_col(table: str) -> str | None:
    return {"ingredients": "name", "recipes": "name"}.get(table)


def arrondi_achat(v: dict) -> dict:
    """Arrondit une quantité à ce qu'on achète RÉELLEMENT.

    Trois cas, dans l'ordre :

    1. L'aliment se vend à la pièce et on connaît son poids (courgette, œuf,
       citron, pomme…) → on arrondit au NOMBRE DE PIÈCES le plus proche.
       450 g de courgette (200 g pièce) → 2 courgettes, soit 400 g.
       C'est ce qu'on fait naturellement en magasin.

    2. L'aliment se compte (tranche, gousse, boîte, sachet) → on arrondit à
       l'unité supérieure : on n'achète pas 3,2 tranches de jambon.

    3. Le reste (viande au poids, farine, riz, huile…) → on arrondit à un
       poids « rond » qui existe en rayon : 5 g près en dessous de 100 g,
       50 g près jusqu'à 500 g, 100 g près au-delà. 450,8 g → 450 g ;
       860 g → 900 g ; 1 240 g → 1,25 kg.

    La quantité de départ reste dans « quantite_brute » : rien n'est perdu.
    """
    import math

    q = float(v.get("quantite") or 0.0)
    v["quantite_brute"] = q
    unite = (v.get("unite") or "").strip().lower()
    piece = v.get("poids_piece_g") or 0.0
    v["pieces"] = None

    if q <= 0:
        v["quantite"] = 0.0
        return v

    # --- 1) vendu à la pièce
    declare_g = (v.get("unite_declaree") or "").strip().lower() in ("g", "gr", "gramme", "grammes")
    plausible = bool(piece) and 25 <= piece <= 400
    # on ne compte en pièces que ce qui s'achète vraiment à la pièce :
    # produits frais bruts (fruits, légumes, œufs, pain…) — pas les conserves,
    # sauces, plats préparés ni les poudres.
    nom = ((v.get("nom") or "") + " " + (v.get("nom_complet") or "")).lower()
    pas_une_piece = any(mot in nom for mot in (
        "coulis", "appertis", "préemball", "preemball", "sauce", "purée", "puree",
        "jus", "confit", "conserve", "surgel", "plat", "gratin", "poudre", "farine",
        "boisson", "sirop", "huile", "vinaigre", "alcool", "vin", "bière"))
    rayon_ok = (v.get("rayon") or "") in ("Fruits & Légumes", "Frais & Produits Laitiers",
                                          "Boucherie & Poissonnerie", "Surgelés", "Autre", "")
    if declare_g and plausible and rayon_ok and not pas_une_piece \
       and unite in ("g", "gr", "gramme", "grammes", ""):
        n = q / piece
        if n >= 0.6:
            nb = int(round(n))              # au nombre de pièces le plus proche
            if nb < 1:
                nb = 1
            if 1 <= nb <= 8:                # au-delà, on reste au poids (plus lisible)
                v["pieces"] = nb
                v["quantite"] = round(nb * piece, 1)
                return v

    # --- 2) unités qui se comptent
    if unite in ("unité", "unite", "pièce", "piece", "tranche", "gousse", "botte",
                 "sachet", "boîte", "boite", "pot", "barquette", "verre", "filet",
                 "tranche(s)", "pincée", "pincee"):
        v["quantite"] = float(math.ceil(q))
        return v

    # --- 3) poids « rond »
    if unite in ("g", "gr", "gramme", "grammes", ""):
        if q < 100:
            pas = 5
        elif q < 500:
            pas = 50
        elif q < 1000:
            pas = 100
        else:
            pas = 250
        v["quantite"] = float(int(round(q / pas)) * pas)
        if v["quantite"] <= 0:
            v["quantite"] = pas
        return v

    if unite in ("ml", "cl", "l", "litre"):
        v["quantite"] = float(math.ceil(q))
        return v

    v["quantite"] = round(q, 1)
    return v


def fmt_quantite(v: dict) -> str:
    """Texte lisible : « 400 g (2 pièces) », « 450 g », « 4 tranches »…"""
    q = v.get("quantite") or 0
    u = (v.get("unite") or "").strip()
    nb = v.get("pieces")
    # pluriels naturels : « 4 tranches », « 3 gousses »
    ul = u.lower()
    if ul in ("unité", "unite"):
        u = "" if q <= 1 else "unités"
    elif ul in ("tranche", "gousse", "sachet", "boîte", "boite", "pot", "barquette",
                "verre", "filet", "botte", "pièce", "piece", "pincée", "pincee") and q > 1:
        u = u + ("s" if not u.endswith("s") else "")
    txt_q = (f"{q:g}".replace(".", ","))
    base = f"{txt_q} {u}".strip() if u else txt_q
    if q >= 100 and ul in ("cl",):
        base = (f"{q/100:.2f}".rstrip("0").rstrip(".").replace(".", ",") + " L")
    if q >= 1000 and ul in ("g", "gr", "gramme", "grammes"):
        base = (f"{q/1000:.2f}".rstrip("0").rstrip(".").replace(".", ",") + " kg")
    if nb:
        return f"{base} ({nb} pièce{'s' if nb > 1 else ''})"
    return base
