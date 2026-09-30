# -*- coding: utf-8 -*-
"""« 🍳 Plats à préparer » — la liste simple des plats de tes menus.

Remplace l'ancien onglet « Aujourd'hui » (qui affichait « ma part », le journal,
etc.) par ce que tu as demandé :

  • la liste des plats à préparer, jour par jour ;
  • pour chaque plat : un lien vers la recette (« 📖 Voir la recette ») qui
    l'ouvre juste en dessous — ingrédients, quantités et préparation ;
  • et un lien vers l'éditeur de recettes pour la modifier.

Rien n'est calculé ici en double : tout vient de menus.py (les mêmes chiffres
que dans le reste de l'application).
"""
from __future__ import annotations

import datetime as dt

VERSION = "2.9.1"        # la version du lot de fichiers déposé sur GitHub
import streamlit as st

import menus as MN
import pdf_menus as PM

JOURS_FR = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]


def _titre_jour(d: dt.date) -> str:
    auj = dt.date.today()
    delta = (d - auj).days
    if delta == 0:
        return f"Aujourd'hui — {JOURS_FR[d.weekday()]} {d.strftime('%d/%m')}"
    if delta == 1:
        return f"Demain — {JOURS_FR[d.weekday()]} {d.strftime('%d/%m')}"
    return f"{JOURS_FR[d.weekday()]} {d.strftime('%d/%m')}"


def _fiche_recette(ms, calc: dict, nom_recette: str, ing_par_id: dict, recipe_id=None,
                   instructions: str | None = None):
    """Le détail de la recette : ingrédients avec quantités, puis préparation."""
    if not calc:
        st.info("Cette entrée n'a pas de recette détaillée (c'est un texte libre ou un "
                "aliment seul de ton planning).")
        return

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Par part", f"{calc['par_part']['kcal']:.0f} kcal")
    c2.metric("Protéines", f"{calc['par_part']['proteines']:.0f} g")
    c3.metric("Glucides", f"{calc['par_part']['glucides']:.0f} g")
    c4.metric("Lipides", f"{calc['par_part']['lipides']:.0f} g")
    st.caption(f"{calc['parts']:g} parts · plat entier : {calc['total']['kcal']:.0f} kcal · "
               f"{calc['poids_g']:.0f} g")

    st.markdown("**Ingrédients**")
    for l in calc["lignes"]:
        qte = l.get("quantite")
        unite = (l.get("unite") or "").strip()
        qte_txt = ""
        if qte:
            qte_txt = f"{qte:g}".replace(".", ",") + (f" {unite}" if unite else " g")
        poids = "-" if l.get("sans_valeurs") else f"{l['grammes']:.0f} g"
        st.markdown(f"- **{l.get('nom_court') or l.get('nom')}** — {qte_txt} "
                    f"({poids})" + ("  ⚠️ sans valeurs nutritionnelles" if l.get("sans_valeurs") else ""))

    prep = (instructions or calc.get("instructions") or "").strip()
    if prep:
        st.markdown("**Préparation**")
        for ligne in prep.split("\n"):
            ligne = ligne.strip()
            if ligne:
                st.markdown(f"{ligne}")
    if calc.get("estimees"):
        st.caption("Quantités déduites automatiquement pour : " + ", ".join(calc["estimees"]))

    # --- lien vers l'éditeur de recettes (page « Recettes »)
    page = st.session_state.get("_page_recettes")
    if page is not None:
        try:
            st.page_link(page, label="Modifier cette recette dans l'éditeur", icon="📝")
        except Exception:
            pass
        if recipe_id:
            st.caption("Dans l'éditeur : choisis cette recette dans « Recette à modifier ».")


def page_plats_a_preparer(ms, jours_visibles: int = 10):
    """L'onglet principal de « Repas & menus » : les plats à préparer."""
    st.caption("Les plats de tes menus, avec un lien direct vers la recette. "
               "Ouvre **📖 Voir la recette** pour les ingrédients et la préparation.")

    aujourdhui = dt.date.today()
    quand = st.selectbox("Période", [
        "Aujourd'hui",
        "Les 3 prochains jours",
        "Cette semaine (7 jours)",
        "Les 14 prochains jours",
        "Tout mon planning",
    ], index=2, key="plats_periode")

    if quand == "Aujourd'hui":
        fin = aujourdhui
    elif quand == "Les 3 prochains jours":
        fin = aujourdhui + dt.timedelta(days=2)
    elif quand == "Cette semaine (7 jours)":
        fin = aujourdhui + dt.timedelta(days=6)
    elif quand == "Les 14 prochains jours":
        fin = aujourdhui + dt.timedelta(days=13)
    else:
        fin = dt.date(2100, 1, 1)

    planning = ms.planning()
    recettes = ms.recette_par_id()
    lignes_par_recette = ms.lignes_par_recette()
    ings = ms.ing_par_id()

    par_jour: dict[str, list] = {}
    for m in planning:
        d = str(m.get("date_menu") or "")[:10]
        if not d:
            continue
        try:
            jour = dt.date.fromisoformat(d)
        except ValueError:
            continue
        if jour < aujourdhui or jour > fin:
            continue
        par_jour.setdefault(d, []).append(m)

    if not par_jour:
        st.info(f"Aucun plat prévu sur cette période (à partir du {aujourdhui.strftime('%d/%m/%Y')}). "
                "Ajoute tes repas dans l'onglet **📅 Planifier la semaine**, ou choisis une "
                "autre période ci-dessus.")
        return

    nb_plats = 0
    for d in sorted(par_jour):
        jour = dt.date.fromisoformat(d)
        repas = sorted(par_jour[d], key=lambda x: x.get("meal_type") or "")
        st.markdown(f"#### {_titre_jour(jour)}")
        for m in repas:
            rid = m.get("recipe_id")
            rec = recettes.get(rid) or {}
            nom = rec.get("name") or "(plat sans nom)"
            # ligne « ingrédient seul » ([Ing]) : on rappelle la quantité prévue,
            # avec son unité (« Pâtes — 200 g » et non « Pâtes (200) »).
            if str(nom).startswith("[Ing] "):
                _ing = PM._trouve_ing(PM.get_display_name(rec), ings)
                # ⭐ unité « convives » : 3 convives de pâtes s'affichent « 240 g »
                _portion = None
                if str(m.get("ingredient_unit") or "").strip().lower().startswith(
                        ("convive", "personne")):
                    try:
                        _portion = MN.portion_personne(_ing)[0]   # menus déjà importé en haut
                    except Exception:
                        _portion = None
                _q = PM._quantite_lisible(m.get("ingredient_qty"), _ing,
                                          m.get("ingredient_unit"), _portion)
                nom = PM.get_display_name(rec) + (f" — {_q}" if _q else "")
            elif str(nom).startswith("[Txt] "):
                nom = PM.get_display_name(rec)
            nb_personnes = m.get("nb_persons") or m.get("servings")
            try:
                nb_personnes = float(nb_personnes) if nb_personnes not in (None, "") else None
            except (TypeError, ValueError):
                nb_personnes = None
            moment = m.get("meal_type") or ""
            with st.container(border=True):
                gauche, droite = st.columns([3, 1])
                gauche.markdown(f"**{nom}**")
                gauche.caption(" · ".join(x for x in [
                    moment,
                    f"{nb_personnes:g} personnes" if nb_personnes else None,
                ] if x))
                calc = None
                if rid and rid in recettes:
                    calc = MN.calculer_recette(lignes_par_recette.get(rid, []), ings,
                                               rec.get("base_servings"), nom_recette=rec.get("name"))
                    if calc:
                        droite.caption(f"{calc['par_part']['kcal']:.0f} kcal / part\n\n"
                                       f"{calc['par_part']['proteines']:.0f} g de protéines")
                with st.expander("📖 Voir la recette"):
                    _fiche_recette(ms, calc, nom, ings, rid,
                                   rec.get("instructions"))
            nb_plats += 1

    st.caption(f"{nb_plats} plat(s) à préparer sur la période choisie. "
               "La ➕ des courses se fait dans **Planifier la semaine**.")
