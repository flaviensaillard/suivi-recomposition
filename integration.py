# -*- coding: utf-8 -*-
"""
Passerelle entre l'application de menus (gestion-menus) et le suivi de recomposition.

Objectif : ne plus jamais saisir deux fois la même chose.
  • le repas prévu aujourd'hui dans gestion-menus  →  un appui pour compter ses protéines
  • les recettes les plus protéinées               →  pour choisir quoi cuisiner

Tout est conçu pour être **découvert automatiquement** : on ne connaît pas à l'avance
le nom exact des colonnes de ta base, donc on les devine (nom, quantité, protéines…)
et tu peux corriger d'un clic si besoin.
"""
from __future__ import annotations

import re
import unicodedata

# Tables usuelles d'une application de gestion de menus
TABLES_PLAN = ["planned_meals", "planning", "planning_repas", "meals", "repas_planifies"]
TABLES_RECETTES = ["recipes", "recettes", "recipe"]
TABLES_INGREDIENTS = ["ingredients", "ingredient", "ingrédients"]
TABLES_LIAISON = ["recipe_ingredient", "recipe_ingredients", "recette_ingredients",
                  "menu_ingredients", "menu_recipe", "recipe_ingredient_list"]

# Champs sémantiques recherchés, avec les noms de colonnes probables
CHAMPS = {
    "recipe_name": ("Nom de la recette", ["name", "nom", "title", "titre", "libelle", "recipe_name", "recette"]),
    "ingredient_name": ("Nom de l'ingrédient", ["name", "nom", "title", "libelle", "designation",
                                                "ingredient", "ingredient_name"]),
    "protein_100g": ("Protéines pour 100 g", ["protein", "proteines", "protein_g", "proteines_g",
                                              "prot", "protein_per_100g", "proteines_100g",
                                              "protein_per_100_g", "protein_grams"]),
    "kcal_100g": ("Calories pour 100 g", ["kcal", "calories", "energy", "energie", "kcal_100g"]),
    "quantity_g": ("Quantité (nombre)", ["quantity", "quantite", "qty", "amount", "nombre", "quantite_g"]),
    "unit": ("Unité (g, ml, pcs…)", ["unit", "unite", "unit_id", "unite_id", "units"]),
    "ingredient_ref": ("Lien vers l'ingrédient", ["ingredient_id", "id_ingredient", "ingredient", "ingredients_id"]),
    "recipe_ref": ("Lien vers la recette", ["recipe_id", "id_recipe", "recette_id", "id_recette", "recipes_id"]),
    "meal_date": ("Date du repas prévu", ["date", "day", "meal_date", "date_repas", "planned_date",
                                          "date_prevue", "jour", "planned_for", "date_planifiee"]),
    "meal_slot": ("Moment (midi, soir…)", ["meal_type", "type", "moment", "repas", "slot", "meal",
                                           "meal_time", "moment_repas"]),
    "servings": ("Nombre de portions", ["servings", "portions", "nb_personnes", "persons", "serves",
                                        "nombre_personnes"]),
    "piece_weight": ("Poids d'une pièce (g)", ["poids_piece", "weight_per_unit", "grams_per_piece",
                                               "poids_unitaire", "unit_weight", "portion_g",
                                               "poids_moyen", "piece_weight"]),
}


# Poids moyens constatés, utilisés seulement comme SUGGESTION quand l'unité est « pièce ».
# La clé la plus longue gagne : « pomme de terre » passe avant « pomme ».
POIDS_PIECE = {
    "pommedeterre": 150, "patatedouce": 200, "blancdepoulet": 150, "filetdepoulet": 150,
    "escalopedepoulet": 120, "steakhache": 100, "saumon": 130, "cabillaud": 120, "colin": 120,
    "tranchedepain": 30, "tranchedejambon": 40, "fromageblanc": 100, "pomme": 150, "poire": 170,
    "banane": 120, "orange": 130, "clementine": 70, "kiwi": 75, "avocat": 200, "tomate": 120,
    "carotte": 80, "courgette": 200, "poivron": 150, "oignon": 80, "concombre": 300,
    "oeuf": 50, "oeufs": 50, "yaourt": 125, "skyr": 150, "pain": 30, "tranche": 30,
    "jambon": 40, "ail": 5, "salade": 100,
}

# Facteurs de conversion vers les grammes
FACTEURS = {
    "g": 1.0, "gr": 1.0, "gramme": 1.0, "grammes": 1.0,
    "kg": 1000.0, "kilo": 1000.0, "kilos": 1000.0, "kilogramme": 1000.0,
    "ml": 1.0, "cl": 10.0, "dl": 100.0, "l": 1000.0, "litre": 1000.0, "litres": 1000.0,
    "cas": 15.0, "cuillereasoupe": 15.0, "cuilleresasoupe": 15.0,
    "cac": 5.0, "cuillereacafe": 5.0, "cuilleresacafe": 5.0,
}

UNITES_PIECE = ("piece", "pieces", "unite", "unites", "portion", "portions",
                "tranche", "tranches", "verre", "verres", "bol", "bols", "gousse", "gousses")

# Unités proposées dans la liste déroulante de l'application
UNITES_UI = ["g", "kg", "ml", "cl", "l", "pièce(s)", "tranche(s)", "portion(s)",
             "c. à s.", "c. à c."]


def poids_piece_suggere(nom: str) -> int:
    """Poids moyen d'une pièce pour un aliment donné (suggestion). 50 g par défaut."""
    n = _norm(nom or "")
    for cle in sorted(POIDS_PIECE, key=len, reverse=True):
        if cle in n:
            return POIDS_PIECE[cle]
    return 50


def est_unite_piece(u: str) -> bool:
    """Vrai si l'unité désigne un objet comptable (pièce, tranche, portion…)."""
    return _norm(u or "") in UNITES_PIECE


def convertir_grammes(qte: float, unite: str, poids_piece: float = None):
    """Convertit une quantité + unité en grammes.

    Retourne (grammes, explication lisible). L'application affiche toujours
    l'hypothèse retenue : jamais un chiffre opaque.
    """
    qte = float(qte or 0)
    u = _norm(unite or "")
    if u in ("", "g", "gr", "gramme", "grammes"):
        return qte, f"{qte:g} g"
    if u in FACTEURS:
        g = qte * FACTEURS[u]
        return g, f"{qte:g} {unite} ≈ {g:g} g"
    if u in UNITES_PIECE:
        poids = float(poids_piece or 0) or 50.0
        return qte * poids, f"{qte:g} × {poids:g} g = {qte * poids:g} g"
    return qte, f"{qte:g} (unité inconnue : prise comme des grammes)"


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]", "", s)  # les underscores sont ignorés


def scorer(colonne: str, candidats: list[str]) -> int:
    """Score de ressemblance entre un nom de colonne réel et nos noms probables."""
    c = _norm(colonne)
    best = 0
    for cand in candidats:
        k = _norm(cand)
        if c == k:
            best = max(best, 100)
        elif c.startswith(k) or k.startswith(c):
            best = max(best, 80)
        elif k in c or c in k:
            best = max(best, 60)
    return best


# --------------------------------------------------------------------------
#  Découverte : quelles tables existent, et avec quelles colonnes ?
# --------------------------------------------------------------------------
def analyser(client, tables_a_tester: list[str]) -> dict:
    """Retourne {table: [colonnes]} pour les tables accessibles contenant au moins une ligne.

    Astuce : PostgREST ne laisse pas lire information_schema, mais on peut déduire les
    colonnes en lisant une ligne. Si la table est vide, on retombe sur une colonne vide.
    """
    trouvees: dict[str, list[str]] = {}
    for t in tables_a_tester:
        try:
            res = client.table(t).select("*").limit(3).execute()
            lignes = res.data or []
            if lignes:
                cols = list(lignes[0].keys())
            else:
                # table accessible mais vide : on tente une limite 0 pour récupérer la forme
                cols = []
            trouvees[t] = cols
        except Exception:
            continue
    return trouvees


def deviner_mapping(tables: dict) -> dict:
    """Construit une proposition de correspondance à partir des colonnes détectées."""
    def choisir(cle: str, tables_possibles: list[str], colonnes_ponderees: dict | None = None):
        nom_champ, candidats = CHAMPS[cle]
        meilleur, meilleur_score, meilleure_table = None, 0, None
        for t in tables_possibles:
            for c in tables.get(t, []):
                s = scorer(c, candidats)
                if colonnes_ponderees and c in colonnes_ponderees:
                    s += colonnes_ponderees[c]
                if s > meilleur_score:
                    meilleur, meilleur_score, meilleure_table = c, s, t
        return (meilleure_table, meilleur) if meilleur_score >= 60 else (None, None)

    m = {"tables": {}, "cols": {}}
    # 1. identifier les tables
    for cle, possibles in (("plan", TABLES_PLAN), ("recettes", TABLES_RECETTES),
                           ("ingredients", TABLES_INGREDIENTS), ("liaison", TABLES_LIAISON)):
        for p in possibles:
            if p in tables:
                m["tables"][cle] = p
                break
        m["tables"].setdefault(cle, None)

    # 2. colonnes, table par table
    t_rec, t_ing, t_lia, t_plan = (m["tables"].get("recettes"), m["tables"].get("ingredients"),
                                   m["tables"].get("liaison"), m["tables"].get("plan"))
    for cle, cibles in (
            ("recipe_name", [t_rec, t_lia, t_plan]),
            ("ingredient_name", [t_ing, t_lia]),
            ("protein_100g", [t_ing]),
            ("kcal_100g", [t_ing]),
            ("quantity_g", [t_lia, t_ing]),
            ("unit", [t_lia, t_ing]),
            ("ingredient_ref", [t_lia]),
            ("recipe_ref", [t_lia, t_plan]),
            ("meal_date", [t_plan]),
            ("meal_slot", [t_plan]),
            ("servings", [t_rec, t_lia, t_plan]),
            ("piece_weight", [t_ing]),
    ):
        cibles = [t for t in cibles if t]
        t, c = choisir(cle, cibles)
        m["cols"][cle] = {"table": t, "col": c}
    return m


# --------------------------------------------------------------------------
#  Affinage : on regarde ce que contiennent vraiment les colonnes candidates
# --------------------------------------------------------------------------
def _remplissage(client, table: str, col: str, limite: int = 5) -> float:
    """Part de valeurs réellement exploitables dans une colonne (0 à 1)."""
    try:
        r = client.table(table).select(col).limit(limite).execute()
        vals = [x.get(col) for x in (r.data or [])]
        if not vals:
            return 0.0
        utiles = sum(1 for v in vals
                     if v not in (None, "") and not (isinstance(v, str) and _est_un_id(v)))
        return utiles / len(vals)
    except Exception:
        return 0.0


def affiner_mapping(client, mapping: dict, tables: dict) -> dict:
    """Départage les colonnes candidates en regardant lesquelles sont réellement remplies.

    Exemple typique : ta table `recipes` contient à la fois `titre` et `nom_recette`.
    Les deux collent au mot-clé « nom » — alors on ouvre les données et on choisit
    celle qui contient vraiment les noms des recettes.
    """
    cibles = {
        "recipe_name": [mapping["tables"].get("recettes"), mapping["tables"].get("liaison")],
        "ingredient_name": [mapping["tables"].get("ingredients"), mapping["tables"].get("liaison")],
        "protein_100g": [mapping["tables"].get("ingredients")],
        "meal_date": [mapping["tables"].get("plan")],
    }
    for cle, tables_cibles in cibles.items():
        _, candidats = CHAMPS[cle]
        propositions = []
        for t in [x for x in tables_cibles if x]:
            for c in tables.get(t, []):
                sc = scorer(c, candidats)
                if sc >= 60:
                    propositions.append((t, c, sc))
        if len(propositions) <= 1:
            continue
        notes = []
        for t, c, sc in propositions:
            notes.append((_remplissage(client, t, c), sc, t, c))
        # priorité au taux de remplissage, puis au score de ressemblance
        notes.sort(key=lambda x: (-x[0], -x[1]))
        if notes[0][0] > 0:
            mapping["cols"][cle] = {"table": notes[0][2], "col": notes[0][3]}
    return mapping


# --------------------------------------------------------------------------
#  Lecture des repas prévus
# --------------------------------------------------------------------------
def _jours_candidats(d) -> list[str]:
    """Formats de date possibles pour comparer sans casser (date, texte, timestamp)."""
    return [d.isoformat(), d.strftime("%d/%m/%Y"), d.strftime("%d/%m/%y"),
            d.strftime("%Y-%m-%dT"), str(d), d.strftime("%Y-%m-%d %H:%M:%S")]


def repas_du_jour(client, mapping: dict, jour) -> list[dict]:
    """Repas prévus aujourd'hui, avec une estimation des protéines quand c'est possible."""
    t_plan = (mapping.get("tables") or {}).get("plan")
    if not t_plan:
        return []
    col_date = (mapping["cols"].get("meal_date") or {}).get("col")
    try:
        if col_date:
            q = client.table(t_plan).select("*")
            # on tente plusieurs écritures de la date jusqu'à obtenir des lignes
            lignes = []
            for fmt in _jours_candidats(jour)[:4]:
                try:
                    r = q.like(col_date, f"{fmt}%").execute()
                    if r.data:
                        lignes = r.data
                        break
                except Exception:
                    continue
            if not lignes:
                r = client.table(t_plan).select("*").limit(50).execute()
                lignes = [x for x in (r.data or [])
                          if str(x.get(col_date, "")).startswith(str(jour))] or (r.data or [])[:0]
        else:
            r = client.table(t_plan).select("*").limit(20).execute()
            lignes = r.data or []
    except Exception:
        return []

    resultats = []
    for ligne in lignes:
        nom = _nom_du_plat(client, mapping, ligne)
        poids = _proteines_du_plat(client, mapping, ligne)
        moment = _valeur(ligne, mapping, "meal_slot")
        resultats.append({"nom": nom, "moment": moment, "proteines": poids, "brut": ligne})
    return [r for r in resultats if r["nom"]]


def _valeur(ligne: dict, mapping: dict, cle: str):
    info = mapping["cols"].get(cle) or {}
    col = info.get("col")
    if col and col in ligne:
        return ligne[col]
    return None


def _nom_du_plat(client, mapping, ligne) -> str | None:
    """Retrouve le nom du plat : colonne directe, sinon jointure sur la table recettes."""
    col_nom = (mapping["cols"].get("recipe_name") or {})
    t_nom = col_nom.get("table")
    c_nom = col_nom.get("col")
    if c_nom and c_nom in ligne and isinstance(ligne[c_nom], str) and not _est_un_id(ligne[c_nom]):
        return ligne[c_nom]
    # sinon : on cherche une référence de recette dans la ligne du planning
    ref = None
    for k, v in ligne.items():
        if _norm(k) in ("recipeid", "idrecipe", "recetteid", "idrecette", "recipesid") and v is not None:
            ref = v
            break
    t_rec = (mapping.get("tables") or {}).get("recettes")
    if ref is not None and t_rec:
        cible = (mapping["cols"].get("recipe_name") or {}).get("col") or "name"
        for cible_try in [cible, "name", "nom", "title", "titre"]:
            try:
                r = client.table(t_rec).select("*").eq("id", ref).limit(1).execute()
                if r.data:
                    for k, v in r.data[0].items():
                        if isinstance(v, str) and not _est_un_id(v) and _norm(k) in (
                                "name", "nom", "title", "titre", "libelle"):
                            return v
                    break
            except Exception:
                continue
    return f"Repas (id {ref})" if ref is not None else None


def _est_un_id(v) -> bool:
    s = str(v)
    return bool(re.fullmatch(r"[0-9a-f]{8}-[0-9a-f]{4}.*", s)) or s.isdigit()


def _proteines_du_plat(client, mapping, ligne):
    """Somme les protéines des ingrédients de la recette, si la base le permet."""
    t_lia = (mapping.get("tables") or {}).get("liaison")
    t_ing = (mapping.get("tables") or {}).get("ingredients")
    ref_rec = None
    for k, v in ligne.items():
        if _norm(k) in ("recipeid", "idrecipe", "recetteid", "idrecette", "recipesid"):
            ref_rec = v
            break
    if not (t_lia and t_ing and ref_rec is not None):
        return None

    col_ref_rec = (mapping["cols"].get("recipe_ref") or {}).get("col")
    col_ref_ing = (mapping["cols"].get("ingredient_ref") or {}).get("col")
    col_qte = (mapping["cols"].get("quantity_g") or {}).get("col")
    col_unit = (mapping["cols"].get("unit") or {}).get("col")
    col_prot = (mapping["cols"].get("protein_100g") or {}).get("col")
    col_nom_ing = (mapping["cols"].get("ingredient_name") or {}).get("col")
    if not (col_ref_rec and col_ref_ing and col_prot):
        return None
    try:
        res = client.table(t_lia).select("*").eq(col_ref_rec, ref_rec).execute()
        liaisons = res.data or []
    except Exception:
        return None
    if not liaisons:
        return None

    total = 0.0
    compte = 0
    for l in liaisons:
        ident = l.get(col_ref_ing)
        qte = float(l.get(col_qte) or 0) if col_qte else 0
        unite = str(l.get(col_unit) or "").lower() if col_unit else ""
        if ident is None or qte <= 0:
            continue
        try:
            r = client.table(t_ing).select("*").eq("id", ident).limit(1).execute()
            if not r.data:
                continue
            ing = r.data[0]
            prot = float(ing.get(col_prot) or 0)
        except Exception:
            continue
        nom_ing = str(ing.get(col_nom_ing) or "") if col_nom_ing else ""
        grammes, _ = convertir_grammes(qte, unite, poids_piece_suggere(nom_ing))
        total += prot * grammes / 100.0
        compte += 1
    if compte == 0:
        return None
    portions = _valeur(ligne, mapping, "servings")
    try:
        portions = float(portions) if portions else 1
    except Exception:
        portions = 1
    return round(total / max(1.0, portions))


def recettes_proteinees(client, mapping: dict, limite: int = 8) -> list[dict]:
    """Les recettes les plus riches en protéines (si la base contient l'information)."""
    t_rec = (mapping.get("tables") or {}).get("recettes")
    if not t_rec:
        return []
    col_nom = (mapping["cols"].get("recipe_name") or {}).get("col")
    if not col_nom:
        return []
    try:
        res = client.table(t_rec).select("*").limit(300).execute()
        recettes = res.data or []
    except Exception:
        return []
    sortie = []
    for r in recettes[:80]:
        nom = r.get(col_nom)
        if not isinstance(nom, str) or _est_un_id(nom):
            continue
        p = _proteines_du_plat(client, mapping, {**r, "recipe_id": r.get("id")})
        if p:
            sortie.append({"nom": nom, "proteines": p})
    sortie.sort(key=lambda x: -x["proteines"])
    return sortie[:limite]


# --------------------------------------------------------------------------
#  Listes pour les listes déroulantes de l'application
# --------------------------------------------------------------------------
def ingredients_liste(client, mapping: dict, limite: int = 1500) -> list:
    """Tous tes ingrédients, prêts pour une liste déroulante.

    Chaque entrée : {"id", "nom", "prot100", "kcal100", "unite", "poids_piece"}
    """
    t_ing = (mapping.get("tables") or {}).get("ingredients")
    if not t_ing:
        return []
    c_nom = (mapping["cols"].get("ingredient_name") or {}).get("col")
    c_prot = (mapping["cols"].get("protein_100g") or {}).get("col")
    c_kcal = (mapping["cols"].get("kcal_100g") or {}).get("col")
    c_unit = (mapping["cols"].get("unit") or {}).get("col")
    c_piece = (mapping["cols"].get("piece_weight") or {}).get("col")

    def _num(v):
        try:
            return float(str(v).replace(",", "."))
        except Exception:
            return None

    try:
        lignes = client.table(t_ing).select("*").limit(limite).execute().data or []
    except Exception:
        return []
    sortie = []
    for r in lignes:
        nom = r.get(c_nom) if c_nom else None
        if not isinstance(nom, str) or not nom.strip() or _est_un_id(nom):
            continue
        sortie.append({
            "id": r.get("id"),
            "nom": nom.strip(),
            "prot100": _num(r.get(c_prot)) if c_prot else None,
            "kcal100": _num(r.get(c_kcal)) if c_kcal else None,
            "unite": (str(r.get(c_unit)) if c_unit and r.get(c_unit) else ""),
            "poids_piece": _num(r.get(c_piece)) if c_piece else None,
        })
    sortie.sort(key=lambda x: x["nom"].casefold())
    return sortie


def parser_date(v):
    """Transforme une valeur de date quelconque en objet date, ou None."""
    import datetime as _dt
    if v is None:
        return None
    if isinstance(v, _dt.datetime):
        return v.date()
    if isinstance(v, _dt.date):
        return v
    txt = str(v).strip()
    for essai in (txt[:19], txt[:10], txt):
        for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S",
                    "%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y"):
            try:
                return _dt.datetime.strptime(essai, fmt).date()
            except Exception:
                continue
    return None


def repas_planifies(client, mapping, du, au, limite: int = 400) -> list:
    """Repas prévus entre deux dates, avec les protéines pour UNE portion."""
    t_plan = (mapping.get("tables") or {}).get("plan")
    if not t_plan:
        return []
    c_date = (mapping["cols"].get("meal_date") or {}).get("col")
    try:
        lignes = client.table(t_plan).select("*").limit(limite).execute().data or []
    except Exception:
        return []
    sortie = []
    for ligne in lignes:
        d = parser_date(ligne.get(c_date)) if c_date else None
        if d is None or not (du <= d <= au):
            continue
        portions = _valeur(ligne, mapping, "servings")
        try:
            portions = float(portions) if portions else 1.0
        except Exception:
            portions = 1.0
        sortie.append({
            "date": d,
            "moment": _valeur(ligne, mapping, "meal_slot"),
            "nom": _nom_du_plat(client, mapping, ligne),
            "prot_portion": _proteines_du_plat(client, mapping, ligne),
            "portions": portions,
            "brut": ligne,
        })
    sortie = [x for x in sortie if x["nom"]]
    sortie.sort(key=lambda x: (x["date"], str(x["moment"] or "")))
    return sortie


# --------------------------------------------------------------------------
#  Diagnostic lisible (à recopier au coach si quelque chose ne colle pas)
# --------------------------------------------------------------------------
def diagnostic(tables: dict, mapping: dict) -> str:
    lignes = ["TABLES DÉTECTÉES"]
    for t, cols in tables.items():
        lignes.append(f"  • {t} ({len(cols)} colonnes) : {', '.join(cols[:14])}"
                      + ("…" if len(cols) > 14 else ""))
    if not tables:
        lignes.append("  (aucune — la clé Supabase a-t-elle été configurée ?)")
    lignes.append("")
    lignes.append("CORRESPONDANCES DÉDUITES")
    for cle, (label, _) in CHAMPS.items():
        info = mapping["cols"].get(cle) or {}
        t, c = info.get("table"), info.get("col")
        etat = f"{t}.{c}" if (t and c) else "— non trouvé"
        lignes.append(f"  • {label} : {etat}")
    return "\n".join(lignes)
