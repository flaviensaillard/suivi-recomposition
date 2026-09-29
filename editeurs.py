# -*- coding: utf-8 -*-
"""
LES 4 ÉCRANS D'ÉDITION — repris de ton application, dans la version fusionnée.

  1. 📅 Planifier      : la semaine, ajouter / modifier / supprimer un repas
  2. 🥣 Recettes       : créer, modifier, supprimer une recette
  3. 🥕 Ingrédients    : ajouter, modifier, supprimer un ingrédient
  4. 📄 Fiche PDF      : la même que la tienne (planning + liste de courses)

Rien n'est perdu : j'ai repris tes colonnes, tes libellés et tes gestes.
Ce qui change : le calcul des macros, qui vient maintenant de la base française.
"""
from __future__ import annotations

import datetime as dt
import uuid

import pandas as pd
import streamlit as st

import menus as MN
import pdf_menus as PM

JOURS = PM.JOURS
RAYONS = PM.RAYONS
UNITES = PM.UNITES


# ---------------------------------------------------------------------------
#  OUTILS COMMUNS
# ---------------------------------------------------------------------------
def _recharger(ms, message: str):
    ms.vider_cache()
    st.success(message)
    st.rerun()


# Nom de la table à écrire — ou None quand on est en mode aperçu (pas de clés).
# Chaque appel reçoit le lecteur de menus « ms » : sans ça, la page plantait
# dès qu'on validait un formulaire (erreur corrigée le 29/09).
TABLES_ECRITURE = ("planned_meals", "recipes", "recipe_ingredients", "ingredients")


def mode_ecriture(ms) -> bool:
    """Peut-on vraiment enregistrer ? (faux en mode aperçu)"""
    return getattr(ms, "client", None) is not None


def _table(ms, nom: str):
    """Renvoie le nom de la table si l'écriture est possible, sinon None."""
    return nom if mode_ecriture(ms) else None


def nom_affiche(ing: dict) -> str:
    """Nom court et familier si on l'a (« Boeuf haché » plutôt que le nom Ciqual)."""
    return ing.get("nom_affiche") or ing.get("name") or "?"


def liste_recettes(ms) -> list[dict]:
    r = [r for r in ms.recettes()
         if not (r.get("name") or "").startswith(("[Ing]", "[Txt]"))]
    return sorted(r, key=lambda x: (x.get("name") or "").lower())


def liste_ingredients(ms) -> list[dict]:
    """Tes ingrédients + ceux utilisés dans les recettes (pas les 3 339 de la base)."""
    utilises = {l.get("ingredient_id") for l in ms.lignes()}
    out = [i for i in ms.ingredients()
           if not i.get("code_ciqual") or i.get("id") in utilises]
    return sorted(out, key=lambda x: nom_affiche(x).lower())


# ---------------------------------------------------------------------------
#  1. PLANIFIER LA SEMAINE
# ---------------------------------------------------------------------------
def page_planifier(ms, target_p: float):
    st.title("📅 Planifier mes menus")
    st.caption("Ta semaine de repas. Un repas peut être une **recette**, un **ingrédient seul** "
               "(ex. un fruit) ou du **texte libre** (ex. « Restaurant »).")

    recettes = liste_recettes(ms)
    ingredients = liste_ingredients(ms)
    if not recettes and not ingredients:
        st.warning("Crée d'abord une recette ou un ingrédient (page « Recettes & ingrédients »).")
        return

    # ---- choix de la semaine
    c1, c2 = st.columns([2, 3])
    lundi = c1.date_input("Semaine du (lundi)",
                          value=dt.date.today() - dt.timedelta(days=dt.date.today().weekday()),
                          format="DD/MM/YYYY", key="pl_lundi")
    jours = [lundi + dt.timedelta(days=i) for i in range(7)]
    c2.markdown("**" + f"Semaine du {jours[0].strftime('%d/%m')} au {jours[-1].strftime('%d/%m/%Y')}"
                + "**")

    planning = ms.planning()
    recettes_par_id = ms.recette_par_id()
    ing_par_id = ms.ing_par_id()

    def repas_du_jour(d):
        out = [p for p in planning if str(p.get("date_menu") or "")[:10] == str(d)]
        return sorted(out, key=lambda x: (x.get("meal_type") or "", x.get("id") or 0))

    # ---- résumé protéines de la semaine
    lignes_par_recette = ms.lignes_par_recette()
    ings = ing_par_id
    jours_ok, jours_light = 0, []
    for d in jours:
        tot = 0.0
        for p in repas_du_jour(d):
            rid = p.get("recipe_id")
            rec = recettes_par_id.get(rid) or {}
            if rid and rid in recettes_par_id:
                c = MN.calculer_recette(lignes_par_recette.get(rid, []), ings, rec.get("base_servings"))
                tot += c["par_part"]["proteines"]
        if tot >= target_p - 15:
            jours_ok += 1
        else:
            jours_light.append((d, tot))
    c3, c4 = st.columns(2)
    c3.metric("Jours qui atteignent la cible", f"{jours_ok} / 7")
    c4.metric("À compléter", ", ".join(d.strftime('%a') for d, _ in jours_light) or "aucun")
    if jours_light:
        st.caption("Pour ces jours, prévois un en-cas protéiné : shaker, œufs durs, skyr. "
                   "(Compter 20 à 30 g pour un shaker.)")

    st.divider()

    # ---- grille de la semaine
    for i, d in enumerate(jours):
        repas = repas_du_jour(d)
        titre = f"{JOURS[i]} {d.strftime('%d/%m')}"
        with st.expander(f"**{titre}** — {len(repas)} repas", expanded=(d == dt.date.today())):
            for p in repas:
                rid = p.get("recipe_id")
                rec = recettes_par_id.get(rid) or {}
                nom = PM.get_display_name(rec) if rec else "—"
                c1, c2 = st.columns([5, 2])
                libelle = f"{p.get('meal_type') or ''} · **{nom}**"
                if p.get("ingredient_qty"):
                    libelle += f" — {p['ingredient_qty']:g}"
                if p.get("servings"):
                    libelle += f" · {p['servings']} convives"
                c1.markdown(libelle)
                if c2.button("🗑️ Supprimer", key=f"pl_del_{p['id']}"):
                    if _table(ms, "planned_meals"):
                        ms.client.table("planned_meals").delete().eq("id", p["id"]).execute()
                        _recharger(ms, "Repas supprimé.")
                    else:
                        st.warning("Mode aperçu : la modification n'est pas enregistrée.")

            if not repas:
                st.caption("Rien de prévu.")

            # ---- ajout
            with st.form(f"pl_add_{d}", clear_on_submit=True):
                f1, f2 = st.columns([2, 1])
                moment = f1.selectbox("Moment", ["Midi", "Soir"], key=f"pl_m_{d}")
                convives = f2.number_input("Convives", 1, 12, 4, key=f"pl_c_{d}")
                f3, f4 = st.columns([2, 2])
                genre = f3.selectbox("Type", ["Recette", "Ingrédient", "Texte libre"],
                                     key=f"pl_g_{d}")
                if genre == "Recette":
                    noms = [r.get("name") for r in recettes]
                    choix = f4.selectbox("Recette", ["—"] + noms, key=f"pl_r_{d}")
                    qte = None
                elif genre == "Ingrédient":
                    noms = [nom_affiche(i) for i in ingredients]
                    choix = f4.selectbox("Ingrédient", ["—"] + noms, key=f"pl_i_{d}")
                    qte = st.number_input("Quantité", 0.0, 5000.0, 1.0, step=0.5, key=f"pl_q_{d}")
                else:
                    choix = f4.text_input("Texte", placeholder="Restaurant, pique-nique…",
                                          key=f"pl_t_{d}")
                    qte = None
                if st.form_submit_button("➕ Ajouter ce repas", width="stretch"):
                    _ajouter_repas(ms, d, moment, convives, genre, choix, qte, recettes, ingredients)

    # ---- outils de semaine
    st.divider()
    c1, c2 = st.columns(2)
    if c1.button("📄 Générer la fiche PDF de la semaine", type="primary", width="stretch"):
        _fiche_pdf(ms, jours, planning, recettes_par_id, ing_par_id)
    if c2.button("🗑️ Vider toute la semaine", width="stretch"):
        if _table(ms, "planned_meals"):
            n = 0
            for d in jours:
                for p in repas_du_jour(d):
                    ms.client.table("planned_meals").delete().eq("id", p["id"]).execute()
                    n += 1
            _recharger(ms, f"Semaine vidée ({n} repas supprimés).")
        else:
            st.warning("Mode aperçu : rien n'est supprimé.")


def _ajouter_repas(ms, jour, moment, convives, genre, choix, qte, recettes, ingredients):
    if not _table(ms, "planned_meals"):
        st.warning("Mode aperçu : l'ajout n'est pas enregistré. Renseigne tes clés Supabase "
                   "pour que tout soit sauvegardé.")
        return
    if choix in (None, "", "—"):
        st.error("Choisis d'abord une recette, un ingrédient ou un texte.")
        return
    jour_fr = JOURS[jour.weekday()]
    try:
        if genre == "Recette":
            rid = next((r["id"] for r in recettes if r.get("name") == choix), None)
            ms.client.table("planned_meals").insert({
                "day": jour_fr, "date_menu": jour.isoformat(), "meal_type": moment,
                "recipe_id": rid, "servings": convives, "nb_persons": convives}).execute()
        elif genre == "Ingrédient":
            ing = next((i for i in ingredients if nom_affiche(i) == choix), None)
            if ing is None:
                st.error("Ingrédient introuvable.")
                return
            # on réutilise (ou crée) la recette « [Ing] Nom » comme dans ton application
            nom_rec = f"[Ing] {nom_affiche(ing)}"
            existante = next((r for r in ms.recettes() if r.get("name") == nom_rec), None)
            if existante:
                rid = existante["id"]
            else:
                res = ms.client.table("recipes").insert({
                    "name": nom_rec, "base_servings": 1, "instructions": ""}).execute()
                rid = res.data[0]["id"]
                ms.client.table("recipe_ingredients").insert({
                    "recipe_id": rid, "ingredient_id": ing["id"], "quantity": 1,
                    "unit": ing.get("unit")}).execute()
            ms.client.table("planned_meals").insert({
                "day": jour_fr, "date_menu": jour.isoformat(), "meal_type": moment,
                "recipe_id": rid, "servings": convives, "nb_persons": convives,
                "ingredient_qty": qte}).execute()
        else:
            nom_rec = f"[Txt] {choix.strip()}"
            res = ms.client.table("recipes").insert({
                "name": nom_rec, "base_servings": 1, "instructions": ""}).execute()
            ms.client.table("planned_meals").insert({
                "day": jour_fr, "date_menu": jour.isoformat(), "meal_type": moment,
                "recipe_id": res.data[0]["id"], "servings": convives,
                "nb_persons": convives}).execute()
        _recharger(ms, "Repas ajouté.")
    except Exception as e:
        st.error(f"Enregistrement impossible : {e}")


def _fiche_pdf(ms, jours, planning, recettes_par_id, ing_par_id, pour_foyer: bool = True):
    dates = [d.isoformat() for d in jours]
    semaine = [p for p in planning if str(p.get("date_menu") or "")[:10] in dates]
    if not semaine:
        st.warning("Aucun repas prévu cette semaine.")
        return
    with st.spinner("Préparation de la fiche…"):
        try:
            recettes_pdf = {k: dict(v, name=PM.get_display_name(v))
                            for k, v in recettes_par_id.items()}
            agg, recurrents = PM.construire_agregat(semaine, recettes_pdf, ing_par_id,
                                                    ms.lignes())
            # mêmes arrondis que la liste de courses, et noms courts
            for v in agg.values():
                ing = next((i for i in ing_par_id.values() if i.get("name") == v["name"]), None)
                v["poids_piece_g"] = (ing or {}).get("poids_piece_g")
                MN.arrondi_achat(v)
                pieces = v.pop("pieces", None)
                court = MN.nom_court(ing)
                v["name"] = f"{court} ({pieces} pièces)" if pieces else court
            recurrents = [dict(r, name=MN.nom_court(r)) for r in recurrents]
            pdf = PM.generate_pdf(semaine, agg, recurrents, recettes_par_id,
                                  ingredients_dict=ing_par_id, start_date=jours[0])
        except Exception as e:
            st.error(f"La fiche n'a pas pu être générée : {type(e).__name__} — {e}")
            return
    if not pdf:
        st.error("La fiche est vide. Vérifie que ta semaine contient des recettes avec ingrédients.")
        return
    st.session_state["pdf_semaine"] = pdf
    st.success(f"Fiche prête ({len(pdf)//1024} Ko).")
    PM.open_pdf_button(pdf)


def arrondir_agregat(agg: dict) -> None:
    """Arrondit les quantités à ce qui s'achète (500 g et pas 499,95 g)."""
    import math
    for v in agg.values():
        q, u = v.get("qty") or 0, (v.get("unit") or "").lower()
        if q <= 0:
            continue
        if u in ("g", "gramme"):
            v["qty"] = math.ceil(q / 5.0) * 5 if q < 1000 else math.ceil(q / 50.0) * 50
        elif u in ("ml", "cl"):
            v["qty"] = math.ceil(q)
        elif u in ("unité", "pièce", "tranche", "gousse", "boîte", "sachet", "barquette"):
            v["qty"] = math.ceil(q)
        else:
            v["qty"] = round(q, 1)


# ---------------------------------------------------------------------------
#  2. RECETTES — CRÉER / MODIFIER
# ---------------------------------------------------------------------------
def page_recettes_edition(ms):
    st.title("🥣 Mes recettes")
    st.caption("Créer, modifier ou supprimer une recette. Une recette se compose "
               "d'ingrédients et d'étapes numérotées.")

    onglet = st.radio("Action", ["✏️ Modifier une recette", "➕ Créer une recette"],
                      horizontal=True, label_visibility="collapsed")

    if onglet.startswith("➕"):
        _creer_recette(ms)
    else:
        _modifier_recette(ms)


def _editeur_ingredients(ms, ingredients, prefixe: str, defaut: list | None = None) -> list[dict]:
    """Petit éditeur de lignes « ingrédient + quantité + unité »."""
    etat = f"{prefixe}_lignes"
    if etat not in st.session_state:
        st.session_state[etat] = defaut or [{"ingredient": None, "quantity": 100.0, "unit": "g"}]
    noms = sorted({nom_affiche(i) for i in ingredients})
    for idx, ligne in enumerate(st.session_state[etat]):
        c1, c2, c3, c4 = st.columns([4, 2, 2, 1])
        choix = c1.selectbox("Ingrédient", ["—"] + noms,
                             index=(["—"] + noms).index(ligne["ingredient"])
                             if ligne.get("ingredient") in noms else 0,
                             key=f"{prefixe}_i_{idx}", label_visibility="collapsed")
        qte = c2.number_input("Qté", 0.0, 100000.0, float(ligne.get("quantity") or 100),
                              step=10.0, key=f"{prefixe}_q_{idx}", label_visibility="collapsed")
        unite = c3.selectbox("Unité", UNITES,
                             index=UNITES.index(ligne["unit"]) if ligne.get("unit") in UNITES else 0,
                             key=f"{prefixe}_u_{idx}", label_visibility="collapsed")
        if c4.button("❌", key=f"{prefixe}_x_{idx}"):
            st.session_state[etat].pop(idx)
            st.rerun()
        st.session_state[etat][idx] = {"ingredient": choix if choix != "—" else None,
                                       "quantity": qte, "unit": unite}
    if st.button("➕ Ajouter une ligne", key=f"{prefixe}_add"):
        st.session_state[etat].append({"ingredient": None, "quantity": 100.0, "unit": "g"})
        st.rerun()
    return [l for l in st.session_state[etat] if l.get("ingredient")]


def _editeur_etapes(prefixe: str, instructions: str) -> list[str]:
    etapes = st.session_state.get(f"{prefixe}_etapes")
    if etapes is None:
        texte = (instructions or "").replace("\\n", "\n")
        etapes = [l.strip() for l in texte.split("\n") if l.strip()] or [""]
        st.session_state[f"{prefixe}_etapes"] = etapes
    for idx in range(len(st.session_state[f"{prefixe}_etapes"])):
        c1, c2 = st.columns([10, 1])
        st.session_state[f"{prefixe}_etapes"][idx] = c1.text_input(
            f"Étape {idx+1}", value=st.session_state[f"{prefixe}_etapes"][idx],
            key=f"{prefixe}_e_{idx}", label_visibility="collapsed")
        if c2.button("❌", key=f"{prefixe}_ex_{idx}"):
            st.session_state[f"{prefixe}_etapes"].pop(idx)
            st.rerun()
    if st.button("➕ Ajouter une étape", key=f"{prefixe}_eadd"):
        st.session_state[f"{prefixe}_etapes"].append("")
        st.rerun()
    return [e for e in st.session_state[f"{prefixe}_etapes"] if e.strip()]


def _creer_recette(ms):
    ingredients = liste_ingredients(ms)
    c1, c2 = st.columns([3, 1])
    nom = c1.text_input("Nom de la recette", key="cr_nom")
    parts = c2.number_input("Parts", 1, 20, 4, key="cr_parts")
    st.markdown("**Ingrédients**")
    lignes = _editeur_ingredients(ms, ingredients, "cr")
    st.markdown("**Préparation**")
    etapes = _editeur_etapes("cr", "")
    if st.button("💾 Enregistrer la recette", type="primary", width="stretch", key="cr_save"):
        if not nom.strip():
            st.error("Le nom est obligatoire.")
        elif not _table(ms, "recipes"):
            st.warning("Mode aperçu : l'enregistrement n'est pas possible sans tes clés Supabase.")
        elif not lignes:
            st.error("Ajoute au moins un ingrédient.")
        else:
            try:
                res = ms.client.table("recipes").insert({
                    "name": nom.strip(), "base_servings": parts,
                    "instructions": PM.instructions_to_text(etapes)}).execute()
                rid = res.data[0]["id"]
                n = 0
                for l in lignes:
                    ing = next((i for i in ingredients if nom_affiche(i) == l["ingredient"]), None)
                    if ing:
                        ms.client.table("recipe_ingredients").insert({
                            "recipe_id": rid, "ingredient_id": ing["id"],
                            "quantity": l["quantity"], "unit": l["unit"]}).execute()
                        n += 1
                for cle in ("cr_lignes", "cr_etapes", "cr_nom"):
                    st.session_state.pop(cle, None)
                _recharger(ms, f"Recette « {nom} » créée avec {n} ingrédient(s).")
            except Exception as e:
                st.error(f"Enregistrement impossible : {e}")


def _modifier_recette(ms):
    recettes = liste_recettes(ms)
    if not recettes:
        st.info("Aucune recette pour l'instant.")
        return
    noms = {r.get("name"): r.get("id") for r in recettes}
    choix = st.selectbox("Recette à modifier", list(noms.keys()), key="mr_choix")
    rid = noms[choix]
    calc = ms.recette(rid)
    lignes_actuelles = list(ms.lignes_par_recette().get(rid, []))
    ings = ms.ing_par_id()

    c1, c2, c3 = st.columns(3)
    c1.metric("Par part", f"{calc['par_part']['kcal']:.0f} kcal")
    c2.metric("Protéines", f"{calc['par_part']['proteines']:.0f} g")
    c3.metric("Parts", f"{calc['parts']:g}")

    f1, f2 = st.columns([3, 1])
    nom = f1.text_input("Nom", value=choix, key=f"mr_nom_{rid}")
    parts = f2.number_input("Parts", 1, 20, int(calc["parts"]), key=f"mr_parts_{rid}")

    st.markdown("**Ingrédients de la recette**")
    supprimer = []
    modifs = []
    for l in lignes_actuelles:
        ing = ings.get(l.get("ingredient_id")) or {}
        c1, c2, c3, c4 = st.columns([4, 2, 2, 1])
        c1.markdown(nom_affiche(ing))
        qte = c2.number_input("Qté", 0.0, 100000.0, float(l.get("quantity") or 0), step=10.0,
                              key=f"mr_q_{l['id']}", label_visibility="collapsed")
        unite = c3.selectbox("Unité", UNITES,
                             index=UNITES.index(l.get("unit")) if l.get("unit") in UNITES else 0,
                             key=f"mr_u_{l['id']}", label_visibility="collapsed")
        if c4.button("❌", key=f"mr_x_{l['id']}"):
            supprimer.append(l["id"])
        modifs.append((l["id"], qte, unite))

    st.markdown("**Ajouter des ingrédients**")
    nouveaux = _editeur_ingredients(ms, liste_ingredients(ms), "mr", defaut=[])

    st.markdown("**Préparation**")
    etapes = _editeur_etapes("mr", calc.get("instructions") or "")

    if st.button("💾 Sauvegarder les modifications", type="primary", width="stretch",
                 key=f"mr_save_{rid}"):
        if not _table(ms, "recipes"):
            st.warning("Mode aperçu : l'enregistrement n'est pas possible sans tes clés Supabase.")
        else:
            try:
                ms.client.table("recipes").update({
                    "name": nom.strip(), "base_servings": parts,
                    "instructions": PM.instructions_to_text(etapes)}).eq("id", rid).execute()
                for lid, qte, unite in modifs:
                    if lid in supprimer:
                        ms.client.table("recipe_ingredients").delete().eq("id", lid).execute()
                    else:
                        ms.client.table("recipe_ingredients").update({
                            "quantity": qte, "unit": unite}).eq("id", lid).execute()
                n = 0
                for l in nouveaux:
                    ing = next((i for i in liste_ingredients(ms)
                                if nom_affiche(i) == l["ingredient"]), None)
                    if ing:
                        ms.client.table("recipe_ingredients").insert({
                            "recipe_id": rid, "ingredient_id": ing["id"],
                            "quantity": l["quantity"], "unit": l["unit"]}).execute()
                        n += 1
                st.session_state.pop("mr_lignes", None)
                st.session_state.pop("mr_etapes", None)
                _recharger(ms, f"Modifications enregistrées ({n} ingrédient(s) ajouté(s)).")
            except Exception as e:
                st.error(f"Enregistrement impossible : {e}")

    st.divider()
    with st.expander("🗑️ Supprimer cette recette"):
        st.caption("La recette et ses lignes d'ingrédients seront supprimées. "
                   "Les repas déjà planifiés avec elle ne s'afficheront plus.")
        if st.button(f"Supprimer « {choix} »", key=f"mr_del_{rid}"):
            if not _table(ms, "recipes"):
                st.warning("Mode aperçu : rien n'est supprimé.")
            else:
                try:
                    ms.client.table("recipe_ingredients").delete().eq("recipe_id", rid).execute()
                    ms.client.table("recipes").delete().eq("id", rid).execute()
                    _recharger(ms, "Recette supprimée.")
                except Exception as e:
                    st.error(f"Suppression impossible : {e}")


# ---------------------------------------------------------------------------
#  3. INGRÉDIENTS
# ---------------------------------------------------------------------------
def page_ingredients(ms):
    st.title("🥕 Mes ingrédients")
    st.caption("Tes ingrédients (ceux que tu utilises) et ceux de tes recettes. "
               "La base française de 3 339 aliments est là pour les valeurs nutritionnelles — "
               "tu n'as pas à la gérer.")

    onglet = st.radio("Action", ["📋 Consulter", "➕ Ajouter", "✏️ Modifier"],
                      horizontal=True, label_visibility="collapsed")
    tous = liste_ingredients(ms)
    utilises = {l.get("ingredient_id") for l in ms.lignes()}

    if onglet.startswith("📋"):
        c1, c2 = st.columns([3, 2])
        q = c1.text_input("Rechercher", placeholder="lait, courgette, fromage…")
        rayon = c2.selectbox("Rayon", ["Tous"] + RAYONS)
        vus = []
        for i in tous:
            n = nom_affiche(i)
            if q and q.lower() not in n.lower():
                continue
            if rayon != "Tous" and (i.get("category") or "Autre") != rayon:
                continue
            vus.append(dict(Ingrédient=n, Rayon=i.get("category") or "Autre",
                            Unité=i.get("unit"),
                            kcal=i.get("kcal_100g"), Protéines=i.get("proteines_100g"),
                            Glucides=i.get("glucides_100g"), Lipides=i.get("lipides_100g"),
                            Pièce_g=i.get("poids_piece_g"),
                            Dans_mes_recettes="✓" if i.get("id") in utilises else "",
                            Hors_liste="✓" if i.get("exclude_from_list") else "",
                            Récurrent="✓" if i.get("is_recurrent") else ""))
        st.caption(f"{len(vus)} ingrédient(s) — les valeurs sont pour 100 g "
                   "(celles de la base française). Tes propres ingrédients gardent leurs "
                   "valeurs si tu les as renseignées.")
        st.dataframe(pd.DataFrame(vus), hide_index=True, width="stretch", height=460)

    elif onglet.startswith("➕"):
        with st.form("ajouter_ingredient", clear_on_submit=True):
            c1, c2 = st.columns(2)
            nom = c1.text_input("Nom")
            unite = c2.selectbox("Unité", ["-"] + UNITES)
            c3, c4 = st.columns(2)
            rayon = c3.selectbox("Rayon", ["-"] + RAYONS)
            poids = c4.number_input("Poids d'une pièce (g)", 0.0, 5000.0, 0.0, step=10.0)
            c5, c6, c7 = st.columns(3)
            kcal = c5.number_input("kcal / 100 g", 0.0, 1000.0, 0.0, step=1.0)
            prot = c6.number_input("Protéines / 100 g", 0.0, 100.0, 0.0, step=0.5)
            gluc = c7.number_input("Glucides / 100 g", 0.0, 100.0, 0.0, step=0.5)
            c8, c9, c10 = st.columns(3)
            lip = c8.number_input("Lipides / 100 g", 0.0, 100.0, 0.0, step=0.5)
            hors = c9.checkbox("Fond de placard (hors liste de courses)")
            recur = c10.checkbox("Récurrent (toujours à racheter)")
            if st.form_submit_button("💾 Enregistrer", type="primary", width="stretch"):
                if not nom.strip() or unite == "-" or rayon == "-":
                    st.error("Il faut au moins un nom, une unité et un rayon.")
                elif not _table(ms, "ingredients"):
                    st.warning("Mode aperçu : l'ajout n'est pas enregistré.")
                else:
                    try:
                        ms.client.table("ingredients").insert({
                            "id": str(uuid.uuid4()), "name": nom.strip(), "unit": unite,
                            "category": rayon, "exclude_from_list": hors,
                            "is_recurrent": recur,
                            "poids_piece_g": poids or None,
                            "unite_liste_courses": unite,
                            "kcal_100g": kcal or None, "proteines_100g": prot or None,
                            "glucides_100g": gluc or None, "lipides_100g": lip or None,
                            "source": "mes ingrédients"}).execute()
                        _recharger(ms, "Ingrédient ajouté.")
                    except Exception as e:
                        st.error(f"Enregistrement impossible : {e}")

    else:
        mes = [i for i in tous if not i.get("code_ciqual")]
        if not mes:
            st.info("Aucun ingrédient personnel à modifier. Ceux de la base française ne se "
                    "modifient pas : ils servent de référence.")
            return
        noms = {nom_affiche(i): i for i in mes}
        choix = st.selectbox("Ingrédient", list(noms.keys()), key="ing_edit")
        ing = noms[choix]
        with st.form("modifier_ingredient"):
            c1, c2 = st.columns(2)
            nom = c1.text_input("Nom", value=ing.get("name") or "")
            unite = c2.selectbox("Unité", UNITES,
                                 index=UNITES.index(ing.get("unit")) if ing.get("unit") in UNITES else 0)
            c3, c4 = st.columns(2)
            rayon = c3.selectbox("Rayon", RAYONS,
                                 index=RAYONS.index(ing.get("category"))
                                 if ing.get("category") in RAYONS else 0)
            poids = c4.number_input("Poids d'une pièce (g)", 0.0, 5000.0,
                                    float(ing.get("poids_piece_g") or 0), step=10.0)
            c5, c6, c7 = st.columns(3)
            kcal = c5.number_input("kcal / 100 g", 0.0, 1000.0, float(ing.get("kcal_100g") or 0))
            prot = c6.number_input("Protéines / 100 g", 0.0, 100.0, float(ing.get("proteines_100g") or 0))
            gluc = c7.number_input("Glucides / 100 g", 0.0, 100.0, float(ing.get("glucides_100g") or 0))
            c8, c9, c10 = st.columns(3)
            lip = c8.number_input("Lipides / 100 g", 0.0, 100.0, float(ing.get("lipides_100g") or 0))
            hors = c9.checkbox("Fond de placard", value=bool(ing.get("exclude_from_list")))
            recur = c10.checkbox("Récurrent", value=bool(ing.get("is_recurrent")))
            if st.form_submit_button("💾 Enregistrer", type="primary", width="stretch"):
                if not _table(ms, "ingredients"):
                    st.warning("Mode aperçu : l'enregistrement n'est pas possible.")
                else:
                    try:
                        ms.client.table("ingredients").update({
                            "name": nom.strip(), "unit": unite, "category": rayon,
                            "poids_piece_g": poids or None, "exclude_from_list": hors,
                            "is_recurrent": recur,
                            "kcal_100g": kcal or None, "proteines_100g": prot or None,
                            "glucides_100g": gluc or None, "lipides_100g": lip or None,
                        }).eq("id", ing["id"]).execute()
                        _recharger(ms, "Ingrédient modifié.")
                    except Exception as e:
                        st.error(f"Enregistrement impossible : {e}")

        with st.expander("🗑️ Supprimer cet ingrédient"):
            nb = sum(1 for l in ms.lignes() if l.get("ingredient_id") == ing["id"])
            if nb:
                st.warning(f"Cet ingrédient est utilisé dans {nb} ligne(s) de recettes. "
                           "Supprime-le d'abord de ces recettes.")
            elif st.button("Supprimer", key="ing_del"):
                if _table(ms, "ingredients"):
                    ms.client.table("ingredients").delete().eq("id", ing["id"]).execute()
                    _recharger(ms, "Ingrédient supprimé.")
