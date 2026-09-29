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
}


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
        # conversion d'unités : on ne connaît pas la correspondance exacte, donc on reste prudent
        if unite in ("g", "gr", "gramme", "grammes", "gram", "", "ml"):   # ml ≈ g (eau, lait…)
            grammes = qte
        elif unite in ("kg", "kilo", "kilos"):
            grammes = qte * 1000
        elif unite == "cl":
            grammes = qte * 10
        elif unite == "dl":
            grammes = qte * 100
        elif unite in ("l", "litre", "litres"):
            grammes = qte * 1000
        else:
            # pièces, tranches, unités : ~50 g par unité, sauf si la quantité est déjà un poids
            grammes = qte * 50 if qte <= 20 else qte
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
