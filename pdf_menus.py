# -*- coding: utf-8 -*-
"""
Fiche PDF et conversions — REPRIS TEL QUEL de ton application « gestion-menus ».

Pourquoi tel quel : ta fiche PDF fonctionne bien et tu en es content. Je ne la
réécris pas, je la garde à l'identique — c'est la même mise en page, la même
liste de courses, le même récapitulatif de la semaine.

Seule modification : les fonctions de calcul de quantité ont été branchées sur
le moteur de la version 2.0 (elles donnent les mêmes résultats).
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional
import base64
import difflib
import re

import streamlit as st
import streamlit.components.v1 as components
from fpdf import FPDF

import pdf_page as PG

# ---------------------------------------------------------------------------
#  CONSTANTES — reprises de ton application (mêmes libellés, mêmes rayons)
# ---------------------------------------------------------------------------
UNITES = ["g", "kg", "ml", "cl", "l", "unité", "pièce", "tranche", "gousse",
          "sachet", "boîte", "barquette", "c. à soupe", "c. à café", "pincée"]

RAYONS = ["Fruits & Légumes", "Boucherie & Poissonnerie", "Frais & Produits Laitiers",
          "Épicerie Salée", "Épicerie Sucrée", "Boissons", "Surgelés", "Autre"]

JOURS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
REPAS = ["Midi", "Soir"]

JOURS_FR = {"Monday": "Lundi", "Tuesday": "Mardi", "Wednesday": "Mercredi",
            "Thursday": "Jeudi", "Friday": "Vendredi", "Saturday": "Samedi",
            "Sunday": "Dimanche"}

REPAS_LABELS = {"Midi": "Déjeuner", "Soir": "Dîner"}


def clean_pdf_str(text: Any) -> str:
    if not text:
        return ""
    
    replacements = {
        '✂️': '-', '🍽️': '', '📖': '', '📝': '', '🛒': '', '•': '-',
        'é': 'e', 'è': 'e', 'ê': 'e', 'à': 'a', 'ç': 'c', 'ù': 'u',
        'ô': 'o', 'î': 'i', 'ï': 'i', 'É': 'E', 'È': 'E', 'Ê': 'E',
        'À': 'A', 'Ç': 'C', 'Ù': 'U', 'Ô': 'O', 'Î': 'I', 'Ï': 'I',
        '€': 'EUR', '"': '"', '"': '"', ''': "'", ''': "'",
    }
    
    result = str(text)
    for old, new in replacements.items():
        result = result.replace(old, new)
    
    return result.encode('latin-1', 'replace').decode('latin-1')

def format_quantity(qty: float) -> str:
    if isinstance(qty, float) and qty.is_integer():
        return str(int(qty))
    return f"{qty:.2f}".rstrip('0').rstrip('.')

def format_servings(servings: float) -> str:
    if servings == int(servings):
        return str(int(servings))
    return str(servings)

def format_liste_quantity(qty: float, unit: str) -> tuple:
    if unit in ['g', 'gramme', 'grammes'] and qty >= 1000:
        return qty / 1000, 'kg'
    elif unit in ['ml', 'millilitre'] and qty >= 1000:
        return qty / 1000, 'l'
    else:
        return qty, unit

def instructions_to_text(instructions_list: List[str]) -> str:
    if not instructions_list:
        return ""
    return "\n".join([f"{i+1}. {instr}" for i, instr in enumerate(instructions_list) if instr.strip()])

def text_to_instructions(text: str) -> List[str]:
    if not text:
        return [""]
    
    lines = text.split('\n')
    instructions = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        match = re.match(r'^\d+\.\s*', line)
        if match:
            instructions.append(line[match.end():])
        else:
            instructions.append(line)
    
    return instructions if instructions else [""]

def sort_list_by_name(items: List[Dict]) -> List[Dict]:
    return sorted(items, key=lambda x: x.get('name', '').lower())

def get_display_name(recipe: Dict) -> str:
    name = recipe.get('name', '')
    if name.startswith('[Ing] '):
        return name[6:]
    if name.startswith('[Txt] '):
        return name[6:]
    return name

def open_pdf_button(pdf_bytes: bytes):
    b64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
    
    html_component = f"""
    <button id="open-pdf-btn" style="
        width: 100%;
        padding: 12px 20px;
        color: white;
        background-color: #4CAF50;
        border: none;
        border-radius: 8px;
        font-weight: bold;
        font-size: 16px;
        cursor: pointer;
        margin-bottom: 10px;">
        📄 Ouvrir le PDF dans un nouvel onglet
    </button>
    <script>
    document.getElementById("open-pdf-btn").addEventListener("click", function() {{
        const b64Data = "{b64_pdf}";
        const byteCharacters = atob(b64Data);
        const byteNumbers = new Array(byteCharacters.length);
        for (let i = 0; i < byteCharacters.length; i++) {{
            byteNumbers[i] = byteCharacters.charCodeAt(i);
        }}
        const byteArray = new Uint8Array(byteNumbers);
        const blob = new Blob([byteArray], {{ type: "application/pdf" }});
        const url = URL.createObjectURL(blob);
        window.open(url, "_blank");
        
        setTimeout(() => {{
            URL.revokeObjectURL(url);
        }}, 60000);
    }});
    </script>
    """
    
    components.html(html_component, height=60)

def convert_to_unit(quantity: float, unit_source: str, unit_cible: str, poids_piece_g: float = None) -> float:
    # un nombre peut arriver en texte ou en Decimal (selon d'où viennent les données)
    try:
        quantity = float(quantity)
    except (TypeError, ValueError):
        quantity = 0.0
    try:
        poids_piece_g = float(poids_piece_g) if poids_piece_g is not None else None
    except (TypeError, ValueError):
        poids_piece_g = None
    unit_source = unit_source.lower().strip() if unit_source else ""
    unit_cible = unit_cible.lower().strip() if unit_cible else ""
    
    if unit_source in ['g', 'gramme', 'grammes']:
        qty_kg = quantity / 1000
    elif unit_source in ['kg', 'kilo', 'kilos']:
        qty_kg = quantity
    elif unit_source in ['ml', 'millilitre']:
        qty_kg = quantity / 1000
    elif unit_source in ['cl', 'centilitre']:
        qty_kg = quantity / 100
    elif unit_source in ['l', 'litre']:
        qty_kg = quantity
    elif unit_source in ['c. à soupe', 'cuillère à soupe']:
        qty_kg = quantity * 0.015
    elif unit_source in ['c. à café', 'cuillère à café']:
        qty_kg = quantity * 0.005
    elif unit_source in ['unité', 'pièce', 'tranche', 'gousse', 'sachet', 'boîte', 'barquette']:
        if poids_piece_g is not None and poids_piece_g > 0:
            qty_kg = (quantity * poids_piece_g) / 1000
        else:
            qty_kg = quantity
    else:
        qty_kg = quantity
    
    if unit_cible in ['g', 'gramme', 'grammes']:
        return qty_kg * 1000
    elif unit_cible in ['kg', 'kilo', 'kilos']:
        return qty_kg
    elif unit_cible in ['ml', 'millilitre']:
        return qty_kg * 1000
    elif unit_cible in ['cl', 'centilitre']:
        return qty_kg * 100
    elif unit_cible in ['l', 'litre']:
        return qty_kg
    elif unit_cible in ['unité', 'pièce', 'tranche', 'gousse', 'sachet', 'boîte', 'barquette']:
        if poids_piece_g is not None and poids_piece_g > 0:
            return qty_kg * 1000 / poids_piece_g
        else:
            return qty_kg
    else:
        return qty_kg

# ------------------------------

def generate_pdf(planned_meals: List[Dict], aggregated_items: Dict,
                 recurrent_items: List[Dict], recipes_dict: Dict,
                 ingredients_dict: Dict = None,
                 start_date: date = None) -> bytes:
    """La fiche A4 de la semaine — tout doit tenir sur une seule feuille.

    Mise en page 2.8.4 : chaque texte est mesuré avant d'être écrit et la police
    diminue automatiquement (voir `pdf_page.py`), donc plus rien ne sort du cadre
    ni ne chevauche une autre ligne. La liste de courses et les produits
    récurrents suivent la même règle.
    """
    try:
        pdf = FPDF(format="A4", unit="mm")
        pdf.set_auto_page_break(auto=False)
        pdf.add_page()

        margin = PG.MARGE
        left_width = 115.0
        right_width = 210.0 - 2 * margin - left_width - 5.0
        left_x = margin
        right_x = left_x + left_width + 5.0

        # ---- les 7 jours
        if start_date:
            week_days = []
            for i in range(7):
                d = start_date + timedelta(days=i)
                week_days.append({"day_name": JOURS_FR.get(d.strftime("%A"), d.strftime("%A")),
                                  "date": d})
        else:
            week_days = [{"day_name": d, "date": None} for d in JOURS]

        # ---- le planning, jour par jour
        schedule = {}
        for info in week_days:
            nom, jour = info["day_name"], info["date"]
            schedule[nom] = {"Midi": [], "Soir": []}
            for pm in planned_meals:
                if jour and pm.get("date_menu"):
                    if str(pm.get("date_menu"))[:10] != jour.isoformat():
                        continue
                elif pm.get("day") != nom:
                    continue

                rec = recipes_dict.get(pm.get("recipe_id")) or {}
                brut = str(rec.get("name_brut") or rec.get("name") or "")
                est_ing = brut.startswith("[Ing] ") or bool(pm.get("ingredient_id"))
                nom_plat = get_display_name(rec) if rec else "Inconnu"

                # ingrédient seul : on rappelle la quantité prévue
                if est_ing and pm.get("ingredient_qty"):
                    unite = ""
                    if ingredients_dict:
                        for ing in ingredients_dict.values():
                            if ing.get("name") == nom_plat or PG._propre(
                                    ing.get("name")) == PG._propre(nom_plat):
                                unite = ing.get("unit") or ""
                                break
                    qte = PG._propre(format_quantity(pm["ingredient_qty"]))
                    nom_plat = f"{nom_plat} ({qte}{(' ' + unite) if unite else ''})".strip()

                moment = pm.get("meal_type")
                if moment in schedule[nom]:
                    schedule[nom][moment].append({
                        "name": nom_plat,
                        "servings": pm.get("nb_persons") or pm.get("servings") or 1,
                        "has_recipe": pm.get("recipe_id") is not None,
                    })

        # ---- colonne de gauche : titre + planning
        y_contenu = PG._entete(pdf, left_x, left_width, start_date)

        # ---- colonne de droite : liste de courses + récurrents
        y_liste = margin + 10.0
        pdf.set_fill_color(255, 220, 180)
        pdf.set_xy(right_x, margin)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(right_width, 8, "Liste de Courses", ln=True, fill=True, align="C")

        par_rayon = defaultdict(list)
        for item in aggregated_items.values():
            par_rayon[item.get("category") or "Autre"].append(item)
        for cat in par_rayon:
            par_rayon[cat] = sort_list_by_name(par_rayon[cat])

        # ---- trait de séparation (avant de savoir jusqu'où va la colonne de gauche)
        pdf.set_draw_color(150, 150, 150)
        pdf.set_dash_pattern(dash=1, gap=2)
        pdf.line(right_x - 2.5, margin, right_x - 2.5, PG.HAUTEUR_PAGE - margin)
        pdf.set_dash_pattern()

        # ---- la liste de courses (police adaptative) puis les récurrents
        PG._bloc_courses(pdf, right_x, y_liste, right_width,
                         PG.HAUTEUR_PAGE - margin - y_liste, par_rayon, recurrent_items)

        # ---- le planning (le reste de la page, en bas à droite compris)
        PG._planning(pdf, week_days, schedule, left_x, y_contenu, left_width,
                     PG.HAUTEUR_PAGE - margin - y_contenu)

        if pdf.pages_count > 1:                 # sécurité : jamais plus d'une feuille
            for n in range(pdf.pages_count - 1, 0, -1):
                pdf.pages.pop(n)
            pdf.page = 1
        return bytes(pdf.output())

    except Exception as e:
        st.error(f"Erreur lors de la génération du PDF : {type(e).__name__} — {e}")
        return b""


# ------------------------------
# INTERFACE PRINCIPALE
# ------------------------------

def _nom_brut(rec: dict) -> str:
    """Le nom d'origine de la recette ([Ing] / [Txt] compris).

    ⚠️ Précaution importante : l'application passe parfois un dictionnaire dont le
    champ `name` a déjà été nettoyé du préfixe « [Ing] ». Sans `name_brut`, les
    repas « ingrédient seul » étaient pris pour des recettes normales et la liste
    de courses comptait la quantité écrite DANS la ligne [Ing] (souvent fausse)
    au lieu de la quantité prévue au planning. Corrigé en 2.8.4.
    """
    return str(rec.get("name_brut") or rec.get("name") or "")


def _trouve_ing(nom: str, ingredients_dict: dict):
    """Retrouve un aliment par son nom, même écrit un peu différemment.

    Exemples réels : « [Ing] Steak haché » doit tomber sur « Boeuf, steak haché
    15% MG cuit » (nom affiché « Boeuf haché »), et « [Ing] Pâtes fourées »
    (petite faute de frappe) sur « Pâtes fourrées ». On compare donc les mots du
    nom, sans accent ni majuscule, avec une tolérance pour les fautes de frappe —
    mais seulement si la ressemblance est franche, sinon on préfère ne rien dire
    plutôt que d'afficher le mauvais aliment.
    """
    if not nom:
        return None
    cible = _cle_aliment(nom)
    if not cible:
        return None
    mots = cible.split()
    meilleur, score_max = None, 0.0
    for i in ingredients_dict.values():
        for champ in ("nom_affiche", "name"):
            cl = _cle_aliment(i.get(champ))
            if not cl:
                continue
            if cl == cible:
                return i
            score = _ressemblance(mots, cl.split())
            if score > score_max:
                meilleur, score_max = i, score
    return meilleur if score_max >= 0.8 else None


def _ressemblance(mots: list, candidats: list) -> float:
    """Part des mots cherchés que l'on retrouve dans le nom candidat (0 → 1)."""
    if not candidats or not mots:
        return 0.0
    trouves = 0.0
    for mot in mots:
        if mot in candidats:
            trouves += 1.0
            continue
        if len(mot) < 4:                     # « sel », « riz » : pas de tolérance
            continue
        r = max((difflib.SequenceMatcher(None, mot, c).ratio() for c in candidats), default=0.0)
        if r >= 0.85:
            trouves += 1.0
        elif r >= 0.75:
            trouves += 0.5
    return trouves / len(mots)


def _cle_aliment(txt) -> str:
    """Comparaison de noms : sans accent, sans majuscule, sans virgule ni espaces doubles."""
    t = clean_pdf_str(txt or "").lower()
    for a, b in (("é", "e"), ("è", "e"), ("ê", "e"), ("à", "a"), ("â", "a"), ("î", "i"),
                 ("ô", "o"), ("û", "u"), ("ù", "u"), ("ç", "c"), ("œ", "oe"), ("'", " "),
                 (",", " "), ("-", " ")):
        t = t.replace(a, b)
    return " ".join(t.split())


COMPTE_UNITES = ("unité", "unite", "pièce", "piece", "tranche", "gousse", "sachet",
                 "boîte", "boite", "pot", "barquette", "verre", "filet")


def _quantite_ligne_ing(qty_source, ing: dict, unite_liste):
    """Traduit le nombre saisi sur une ligne « [Ing] » en vraie quantité de courses.

    Sur une ligne « [Ing] », on tape un petit nombre entier : « 4 » pour 4 steaks,
    « 3 » pour 3 cordons bleus. Avant, ce 4 était lu comme 4 GRAMMES → la liste
    affichait « Boeuf haché : 4 g » ou « Cordon bleu : 0 unité ». Maintenant :

      • aliment vendu au poids (steak haché, poids d'une pièce connu) →
        4 × 125 g = 500 g ;
      • aliment qui se compte (cordon bleu, chipolata) → 3 unités, 6 unités ;
      • aliment sans poids de pièce et vendu au poids → on garde le nombre tel quel.
    """
    try:
        q = float(qty_source)
    except (TypeError, ValueError):
        return None
    unite_ing = (ing.get("unit") or "").strip().lower()
    cible = (unite_liste or "").strip().lower()
    try:
        poids = float(ing.get("poids_piece_g")) if ing.get("poids_piece_g") else 0.0
    except (TypeError, ValueError):
        poids = 0.0
    pese = unite_ing in ("g", "gr", "gramme", "grammes", "kg", "ml", "cl", "l", "litre", "")
    petit_entier = abs(q - round(q)) < 1e-9 and 1 <= q <= 20
    if petit_entier and pese:
        if cible in COMPTE_UNITES:               # ça se compte : 3 cordons bleus
            return q
        if 25 <= poids <= 400:                   # poids d'une pièce connu : 4 × 125 g
            return convert_to_unit(q * poids, "g", cible or "g", None)
    return convert_to_unit(q, unite_ing, unite_liste, poids or None)


def construire_agregat(week_meals, recipes_dict, ingredients_dict, recipe_ings):
    """Liste de courses de la semaine — même logique que l'application de menus.

    Renvoie (aggregated, recurrent) au format attendu par generate_pdf().
    """
    aggregated = {}
    for pm in week_meals:
        rec = recipes_dict.get(pm.get("recipe_id"))
        if not rec:
            continue
        nom = _nom_brut(rec)
        if nom.startswith("[Ing] ") or pm.get("ingredient_id"):
            ing = (_trouve_ing(get_display_name(rec), ingredients_dict)
                   or _trouve_ing(pm.get("ingredient_id"), ingredients_dict))
            if ing is None and get_display_name(rec):
                # l'aliment n'est pas dans la base (nom mal orthographié, aliment
                # supprimé…) : on garde quand même la ligne dans la liste, sinon
                # l'article serait tout simplement oublié au moment des courses.
                cle = f"libre::{_cle_aliment(get_display_name(rec))}"
                if cle not in aggregated:
                    aggregated[cle] = {"name": get_display_name(rec), "qty": 0, "unit": "",
                                       "category": "Autre", "libre": True,
                                       "nom": get_display_name(rec)}
                aggregated[cle]["qty"] += float(pm.get("ingredient_qty") or 1)
            elif ing is not None and not ing.get("exclude_from_list"):
                unite_liste = ing.get("unite_liste_courses") or ing.get("unit")
                qty_source = pm.get("ingredient_qty") or pm.get("servings") or 1
                qty = _quantite_ligne_ing(qty_source, ing, unite_liste)
                if ing["id"] not in aggregated:
                    aggregated[ing["id"]] = {"name": ing["name"], "qty": 0,
                                             "unit": unite_liste,
                                             "category": ing.get("category", "Autre")}
                aggregated[ing["id"]]["qty"] += qty or 0
        elif not nom.startswith("[Txt] "):
            ratio = (pm.get("servings") or 1) / (rec.get("base_servings") or 1)
            for ri in recipe_ings:
                if ri.get("recipe_id") != pm.get("recipe_id"):
                    continue
                ing = ingredients_dict.get(ri.get("ingredient_id"))
                if not ing or ing.get("exclude_from_list"):
                    continue
                ri_unit = ri.get("unit") or ing.get("unit")
                unite_liste = ing.get("unite_liste_courses") or ing.get("unit")
                qty = convert_to_unit((ri.get("quantity") or 0) * ratio, ri_unit, unite_liste,
                                      ing.get("poids_piece_g"))
                if ing["id"] not in aggregated:
                    aggregated[ing["id"]] = {"name": ing["name"], "qty": 0,
                                             "unit": unite_liste,
                                             "category": ing.get("category", "Autre")}
                aggregated[ing["id"]]["qty"] += qty or 0
    recurrent = [i for i in ingredients_dict.values() if i.get("is_recurrent")]
    return aggregated, recurrent
