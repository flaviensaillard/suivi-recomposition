# -*- coding: utf-8 -*-
"""
Pages « Repas & menus » et « Courses » — version fusionnée.

Elles lisent directement tes 4 tables (ingredients, recipes, recipe_ingredients,
planned_meals) et calculent tout à partir de la base alimentaire française
importée : plus aucune saisie, plus aucun doublon.

Ce fichier ne fait que de la lecture et de l'affichage. Toute erreur de
connexion est rattrapée et affichée en clair, jamais en message technique.
"""
from __future__ import annotations

import datetime as dt

import pandas as pd
import streamlit as st

import menus as MN
try:
    import repas_plats as RP
except ImportError:                      # fichier pas recopié sur GitHub
    RP = None


# ---------------------------------------------------------------------------
#  OUTILS D'AFFICHAGE
# ---------------------------------------------------------------------------
def ligne_macros(m: dict, taille: str = "normal") -> str:
    txt = (f"**{m['kcal']:.0f}** kcal · **{m['proteines']:.0f} g** de protéines · "
           f"{m['glucides']:.0f} g G · {m['lipides']:.0f} g L")
    return txt if taille == "normal" else f"<span class='hint'>{txt}</span>"


def jauge_proteines(prises: float, cible: float) -> None:
    st.progress(min(1.0, prises / cible if cible else 0.0),
                text=f"**{prises:.0f} g** de protéines prévues aujourd'hui "
                     f"— objectif {cible:.0f} g")


def alerte_quantites(calc: dict) -> list[str]:
    """Repère les recettes dont les quantités semblent fausses."""
    pb = []
    par_part = calc["par_part"]["kcal"]
    if calc["poids_g"] and calc["poids_g"] < 40:
        pb.append(f"poids total très faible ({calc['poids_g']:.0f} g)")
    elif par_part and par_part < 60:
        pb.append(f"seulement {par_part:.0f} kcal par part pour {calc['parts']:g} parts")
    if calc["inconnues"]:
        pb.append("sans valeurs nutritionnelles : " + ", ".join(calc["inconnues"][:3]))
    return pb


def _bouton_journal(store, quand, nom: str, proteines: float, cle: str,
                    glucides: float = 0, lipides: float = 0):
    if st.button(f"➕ Ajouter {proteines:.0f} g de protéines au journal", key=cle, width="stretch"):
        store.add_protein(quand, f"{nom} (menu)", round(proteines),
                          carbs=round(glucides), fat=round(lipides))
        st.toast(f"+{proteines:.0f} g de protéines pour « {nom} »")
        st.rerun()


# ---------------------------------------------------------------------------
#  PAGE — REPAS & MENUS
# ---------------------------------------------------------------------------
def page_repas(store, menus_store, target_p: float, jours_visibles: int = 10):
    st.title("🍽️ Repas & menus")
    st.caption("Tes menus, tes recettes, tes macros — **sans rien ressaisir**. "
               "Tout vient de ta base : les quantités, les parts et la composition des aliments.")

    ms = menus_store()
    if ms is None:
        st.info("**Cette page lit ta base de menus, qui vit dans Supabase.**\n\n"
                "Déploie l'application (guide de démarrage) et renseigne tes deux clés : "
                "tu verras ici tes repas du jour, tes recettes et leurs macros.\n\n"
                "Tout le reste de l'application (pesée, séances, protéines, mensurations) "
                "fonctionne déjà sans ça.")
        return

    with st.spinner("Lecture de ta base…"):
        try:
            nb_ing = len(ms.ingredients())
            nb_rec = len(ms.recettes())
            nb_lig = len(ms.lignes())
            nb_rep = len(ms.planning())
        except Exception as e:
            st.error(f"Lecture impossible : {type(e).__name__}. Vérifie la clé Supabase (Réglages).")
            return

    if not nb_rec:
        st.warning("Aucune recette trouvée. Vérifie que la clé utilisée est bien celle du projet "
                   "`gestion-menus`.")
        return

    if ms.erreur:
        st.warning(f"Un détail : {ms.erreur}")

    if getattr(ms, "demo", False):
        st.warning("**Mode aperçu — ce n'est pas encore ta base.** Cet extrait est livré avec "
                   "l'application pour que tu puisses cliquer partout. Il contient tes 104 "
                   "recettes, tes 153 ingrédients et ton planning, mais seulement **161 des 331 "
                   "lignes d'ingrédients** de tes recettes : certaines recettes affichent donc "
                   "des calories partielles. Dès que tes clés Supabase seront branchées, tout "
                   "sera complet.\n\n"
                   "**Dis-moi ce que tu voudrais changer** : je corrige et je relance l'aperçu.")

    onglets = st.tabs(["🍳 Plats à préparer", "🗓️ Ma semaine", "📖 Mes recettes"])

    # ------------------------------------------------- plats à préparer (avec la recette)
    with onglets[0]:
        if RP is None:
            st.error("⚠️ **Le fichier `repas_plats.py` n'a pas été recopié sur GitHub.**\n\n"
                     "C'est le fichier qui affiche la liste des plats avec le lien vers la "
                     "recette. Recopie **tous** les fichiers `.py` du dossier "
                     "`1_a_copier_dans_GITHUB`, puis **Reboot app** sur share.streamlit.io.\n\n"
                     "En attendant, l'ancien écran est affiché ci-dessous.")
            _onglet_jour(store, ms, target_p)
        else:
            RP.page_plats_a_preparer(ms, jours_visibles)

    # ---------------------------------------------------------------- semaine
    with onglets[1]:
        _onglet_semaine(ms, target_p)

    # ---------------------------------------------------------------- recettes
    with onglets[2]:
        _onglet_recettes(ms, nb_ing, nb_rec, nb_lig, nb_rep)


def _onglet_jour(store, ms, target_p: float):
    """⚠️ Ancien onglet « Aujourd'hui » — il n'est plus affiché.

    Tu m'as dit : « enlève de Repas & menus ce qui se trouve dans aujourd'hui,
    je veux simplement les plats à préparer avec un lien vers la recette ».
    C'est désormais `repas_plats.page_plats_a_preparer`. La fonction reste ici
    (elle ne s'affiche pas) pour ne rien casser si tu la cherches.
    """
    quand = st.date_input("Jour", value=dt.date.today(), format="DD/MM/YYYY", key="rep_jour")
    with st.spinner("Calcul…"):
        repas = ms.repas_du_jour(quand)
    if not repas:
        st.info(f"Rien de prévu le {quand.strftime('%d/%m/%Y')} dans ton planning. "
                "Choisis une autre date, ou ajoute ce repas dans ton application de menus.")
        return

    total_1_part = sum(r["calcul"]["par_part"]["proteines"] for r in repas if r.get("calcul"))
    jauge_proteines(total_1_part, target_p)
    st.caption("Estimation si tu manges **une part** de chaque plat. Ajuste ci-dessous repas par repas.")

    pf = MN.portion_foyer()
    for i, r in enumerate(sorted(repas, key=lambda x: x["heure"] or "")):
        calc = r.get("calcul")
        with st.container(border=True):
            c1, c2 = st.columns([3, 2])
            c1.markdown(f"**{r['recette']}**")
            c1.caption(f"{r['heure'] or ''} · {r['nb_persons'] or '?'} personnes prévues")
            if not calc:
                c2.caption("Pas de recette liée : ce repas n'a pas d'ingrédients à calculer.")
                continue

            mode = c2.radio("Ma part", ["Parts", "% du plat", "Poids (g)"],
                            key=f"mode_{i}", horizontal=True, label_visibility="collapsed")
            if mode == "Parts":
                val = c2.number_input("Parts", 0.25, 6.0,
                                      MN.part_defaut(calc["parts"], r["recette"], r["heure"]), step=0.25,
                                      key=f"v_{i}", label_visibility="collapsed")
                md = "parts"
            elif mode == "% du plat":
                val = c2.number_input("%", 5, 100, int(round(100 / (calc["parts"] or 1))), step=5,
                                      key=f"v_{i}", label_visibility="collapsed")
                md = "pourcent"
            else:
                val = c2.number_input("g", 10, 1200, int(calc["poids_g"] / (calc["parts"] or 1)),
                                      step=10, key=f"v_{i}", label_visibility="collapsed")
                md = "poids"

            mp = MN.ma_part(calc, md, val, pf)
            st.markdown(f"### {ligne_macros(mp['macros'])}")
            st.caption(f"{mp['libelle']} ({mp['fraction']*100:.0f} % du plat · {mp['grammes']:.0f} g) "
                       f"— plat entier : {calc['total']['kcal']:.0f} kcal pour {calc['parts']:g} parts")
            for pb in alerte_quantites(calc):
                st.warning(f"Quantités à vérifier : {pb}", icon="⚠️")
            _bouton_journal(store, quand, f"{r['recette']} ({mp['libelle']})",
                            mp["macros"]["proteines"], f"jr_{i}_{r['id']}",
                            glucides=mp["macros"]["glucides"], lipides=mp["macros"]["lipides"])


def _onglet_semaine(ms, target_p: float):
    debut = st.date_input("À partir du", value=dt.date.today(), format="DD/MM/YYYY", key="rep_debut")
    planning = ms.planning()
    recettes = ms.recette_par_id()
    lignes = ms.lignes_par_recette()
    ings = ms.ing_par_id()

    jours = {}
    for m in planning:
        d = str(m.get("date_menu") or "")[:10]
        if d:
            jours.setdefault(d, []).append(m)
    if not jours:
        st.info("Ton planning est vide.")
        return

    dates = sorted(d for d in jours if d >= str(debut))[:7]
    if not dates:
        st.info("Aucun repas après cette date.")
        return

    st.caption("Protéines estimées pour **une part** de chaque plat. "
               "La ligne « total » te dit si la journée tient sur ta cible.")
    for d in dates:
        repas = sorted(jours[d], key=lambda x: x.get("meal_type") or "")
        jour_dt = dt.date.fromisoformat(d)
        titre = f"{['Lun','Mar','Mer','Jeu','Ven','Sam','Dim'][jour_dt.weekday()]} {jour_dt.strftime('%d/%m')}"
        tot = {"kcal": 0.0, "proteines": 0.0, "glucides": 0.0, "lipides": 0.0}
        lines = []
        for m in repas:
            rid = m.get("recipe_id")
            rec = recettes.get(rid) or {}
            nom = rec.get("name") or "—"
            if rid and rid in recettes:
                c = MN.calculer_recette(lignes.get(rid, []), ings, rec.get("base_servings"),
                                        nom_recette=rec.get("name"))
                for k in tot:
                    tot[k] += c["par_part"][k]
                pp = f"{c['par_part']['kcal']:.0f} kcal · {c['par_part']['proteines']:.0f} g P"
            else:
                pp = "—"
            lines.append((m.get("meal_type") or "", nom, pp))
        manque = max(0.0, target_p - tot["proteines"])
        with st.container(border=True):
            c1, c2 = st.columns([2, 5])
            c1.markdown(f"**{titre}**")
            c1.caption(f"{tot['kcal']:.0f} kcal · **{tot['proteines']:.0f} g P**"
                       + (f"  ·  il manque {manque:.0f} g" if manque > 5 else "  ·  cible atteinte ✅"))
            c2.dataframe(pd.DataFrame(lines, columns=["Repas", "Plat", "1 part"]),
                         hide_index=True, width="stretch")


def _verif_calcul(ms, recettes, c=None):
    """Outil de vérification du calcul, affiché dans la liste des recettes."""
    with st.expander("🔎 Vérifier le calcul (à ouvrir si un chiffre te paraît faux)"):
        try:
            ings = ms.ingredients()
        except Exception as e:
            st.error(f"Impossible de lire tes ingrédients : {type(e).__name__} — {e}")
            return
        avec = [i for i in ings if i.get("proteines_100g")]
        st.markdown(f"- Aliments chargés depuis ta base : **{len(ings)}**")
        st.markdown(f"- Aliments **avec valeurs nutritionnelles** : **{len(avec)}** "
                    f"({len(ings) - len(avec)} sans — ils comptent pour 0)")
        if len(avec) < len(ings) * 0.5:
            st.error("❌ Moins de la moitié de tes aliments ont des valeurs nutritionnelles : "
                     "c'est ce qui fausse les totaux. Lance le script **`7_nutrition.sql`** "
                     "dans Supabase (10 s) : il remplit automatiquement les valeurs manquantes "
                     "depuis la table Ciqual.")
        sans = [dict(Aliment=(i.get("nom_affiche") or i.get("name")),
                     Rayon=i.get("category"), Utilisé="oui" if i.get("code_ciqual") else "perso")
                for i in ings if not i.get("proteines_100g")]
        if sans:
            st.markdown(f"**{len(sans)} aliments sans valeurs** (les 20 premiers) :")
            st.dataframe(pd.DataFrame(sans[:20]), hide_index=True, width="stretch")
        st.caption("Ces chiffres viennent directement de ta base Supabase, en direct.")


def _onglet_recettes(ms, nb_ing, nb_rec, nb_lig, nb_rep):
    st.caption(f"Ta base : **{nb_ing} aliments** · "
               f"**{nb_rec} recettes** · **{nb_lig} lignes d'ingrédients** · "
               f"**{nb_rep} repas planifiés**. Toutes les lignes sont reliées : "
               f"les macros sont calculées pour de vrai.")

    vraies = [r for r in ms.recettes()
              if not (r.get("name") or "").startswith(("[Ing]", "[Txt]"))]
    vraies.sort(key=lambda r: (r.get("name") or "").lower())
    noms = {"— toutes —": None}
    noms.update({r.get("name") or "?": r.get("id") for r in vraies})
    # liste cherchable, accents ignorés (« pates » → « Pâtes »)
    choix = MN.selecteur_recherche("Choisis une recette", list(noms.keys()), "rec_choix")
    if choix is None:
        choix = "— toutes —"
    if choix == "— toutes —":
        st.caption(f"{len(vraies)} vraies recettes (les entrées « [Ing] » et « [Txt] » de ton "
                   "planning — ingrédient seul ou texte libre — sont masquées).")
        data = []
        for r in vraies:
            c = ms.recette(r["id"])
            if not c:
                continue
            c_part = c["par_part"]
            data.append(dict(Recette=r.get("name"), Parts=f"{c['parts']:g}",
                             kcal_plat=f"{c['total']['kcal']:.0f}",
                             kcal_part=f"{c_part['kcal']:.0f}",
                             proteines_part=f"{c_part['proteines']:.0f}",
                             glucides_part=f"{c_part['glucides']:.0f}",
                             lipides_part=f"{c_part['lipides']:.0f}",
                             ingredients=len(c["lignes"])))
        st.dataframe(pd.DataFrame(data), hide_index=True, width="stretch",
                     column_config={
                         "kcal_part": st.column_config.NumberColumn("kcal / part"),
                         "proteines_part": st.column_config.NumberColumn("P / part (g)"),
                         "glucides_part": st.column_config.NumberColumn("G / part (g)"),
                         "lipides_part": st.column_config.NumberColumn("L / part (g)"),
                     })
        nb_vides = sum(1 for d in data if float(d["kcal_part"]) < 5)
        st.caption("**Toutes les valeurs sont par part** (une part = ce que tu mets dans ton "
                   "assiette). Trie une colonne d'un appui : par exemple sur **P / part** pour "
                   "voir tes recettes les plus protéinées. Clique une ligne pour l'ouvrir en "
                   "entier, ingrédient par ingrédient.")
        if nb_vides:
            st.info(f"ℹ️ {nb_vides} ligne(s) affichent moins de 5 kcal par part : ce sont les "
                    f"entrées **« [Ing] … »** de ton planning (un ingrédient seul, ex. « [Ing] "
                    f"Pâtes ») — leur quantité est un **nombre de personnes**, pas un poids. "
                    f"C'est normal, ce ne sont pas de vraies recettes.")
        _verif_calcul(ms, vraies, None)
        return

    c = ms.recette(noms[choix])
    if not c:
        return
    st.subheader(choix)
    a, b, c3, c4 = st.columns(4)
    a.metric("Par part", f"{c['par_part']['kcal']:.0f} kcal")
    b.metric("Protéines", f"{c['par_part']['proteines']:.0f} g")
    c3.metric("Glucides", f"{c['par_part']['glucides']:.0f} g")
    c4.metric("Lipides", f"{c['par_part']['lipides']:.0f} g")
    st.caption(f"**Recette complète** ({c['parts']:g} parts, {c['poids_g']:.0f} g) : "
               f"{c['total']['kcal']:.0f} kcal · {c['total']['proteines']:.0f} g P · "
               f"{c['total']['glucides']:.0f} g G · {c['total']['lipides']:.0f} g L")
    if c["inconnues"]:
        st.warning("**Ces ingrédients n'ont aucune valeur nutritionnelle dans ta base : "
                   + ", ".join(dict.fromkeys(c["inconnues"]))
                   + ".** Leurs grammes comptent, mais pas leurs protéines/calories : les "
                     "totaux sont donc **sous-estimés**. Lance le script **`7_nutrition.sql`** "
                     "dans Supabase (10 s) : il remplit ces valeurs depuis la table Ciqual.",
                   icon="⚠️")
    for pb in alerte_quantites(c):
        st.warning(f"Quantités à vérifier : {pb}", icon="⚠️")

    col1, col2 = st.columns([3, 2])
    with col1:
        st.markdown("**Ingrédients**")
        st.dataframe(pd.DataFrame([
            dict(Ingrédient=l["nom_court"] + (" *" if l["estime"] else ""),
                 Quantité=f"{l['quantite']:g} {l['unite'] or ''}".strip(),
                 Poids=f"{l['grammes']:.0f} g", kcal=f"{l['kcal']:.0f}",
                 Protéines=f"{l['proteines']:.1f}", Glucides=f"{l['glucides']:.1f}",
                 Lipides=f"{l['lipides']:.1f}")
            for l in c["lignes"]]), hide_index=True, width="stretch",
            column_config={"Protéines": st.column_config.NumberColumn("P (g)"),
                           "Glucides": st.column_config.NumberColumn("G (g)"),
                           "Lipides": st.column_config.NumberColumn("L (g)")})
        st.caption("Ces valeurs sont pour **la recette entière**, ligne par ligne. "
                   "Divise par le nombre de parts pour avoir ton assiette.")
        if c["estimees"]:
            st.info("**(*) quantité déduite automatiquement** pour : "
                    + ", ".join(f"**{n}**" for n in c["estimees"][:6])
                    + ". Dans ta base, la ligne ne donne pas d'unité exploitable : "
                      "l'application a compté **une portion standard par personne** "
                      "(100 g pour les aliments Ciqual). Si ce n'est pas la bonne "
                      "quantité, corrige-la dans **Recettes → modifier** : le calcul "
                      "suivra tout seul.", icon="ℹ️")
        if c["inconnues"]:
            st.caption("Aliments **sans valeurs nutritionnelles** dans ta base (comptés pour 0) : "
                       + ", ".join(c["inconnues"]) + " → script `7_nutrition.sql`.")
    with col2:
        st.markdown("**Ma part**")
        mp = MN.ma_part(c, "parts", MN.part_defaut(c["parts"]))
        st.markdown(f"### {ligne_macros(mp['macros'])}")
        st.caption(f"1 part sur {c['parts']:g} · {mp['grammes']:.0f} g")
        st.caption(f"Foyer (2 adultes + 2 enfants) : {MN.portion_foyer():.1f} portions "
                   f"→ il reste {max(0.0, c['parts'] - MN.portion_foyer()):.1f} portion de rab.")
    if c.get("instructions"):
        with st.expander("📋 Préparation", expanded=False):
            st.markdown(str(c["instructions"]).replace("\\n", "\n"))

    with st.expander("🔎 Vérifier le calcul (à ouvrir si un chiffre te paraît faux)"):
        ing_ok = sum(1 for i in ms.ingredients() if i.get("proteines_100g"))
        tot_ing = len(ms.ingredients())
        st.markdown(f"- Aliments chargés depuis ta base : **{tot_ing}**")
        st.markdown(f"- Aliments **avec valeurs nutritionnelles** : **{ing_ok}**")
        st.markdown(f"- Lignes de cette recette : **{len(c['lignes'])}**")
        st.markdown(f"- Poids reconstitué : **{c['poids_g']:.0f} g**")
        vides = [l for l in c["lignes"] if l["sans_valeurs"]]
        if vides:
            st.error(f"❌ {len(vides)} ingrédient(s) sans valeurs nutritionnelles : "
                     + ", ".join(l["nom_court"] for l in vides)
                     + " → **c'est la cause d'un total trop bas.** Lance `7_nutrition.sql`.")
        else:
            st.success("✅ Tous les ingrédients de cette recette ont leurs valeurs : le calcul "
                       "est complet.")
        st.caption("Si un chiffre te paraît encore faux, envoie-moi une capture de ce cadre.")


# ---------------------------------------------------------------------------
#  PAGE — COURSES AUTOMATIQUES
# ---------------------------------------------------------------------------
def bloc_courses_auto(store, menus_store):
    ms = menus_store()
    if ms is None:
        return
    st.subheader("🧾 Ce que demandent tes menus")
    st.caption("Calculé à partir de ton planning : les quantités de chaque recette sont "
               "additionnées, puis ajustées aux portions du foyer (3,2). "
               "Les articles marqués « hors liste » sont ignorés.")
    c1, c2 = st.columns(2)
    du = c1.date_input("Du", value=dt.date.today(), format="DD/MM/YYYY", key="co_du")
    au = c2.date_input("Au", value=dt.date.today() + dt.timedelta(days=6), format="DD/MM/YYYY",
                       key="co_au")
    if au < du:
        st.error("La date de fin doit être après la date de début.")
        return
    try:
        res = ms.courses(du, au)
    except Exception as e:
        st.error(f"Calcul impossible : {type(e).__name__}")
        return
    if not res["rayons"]:
        st.info("Aucun repas planifié sur cette période.")
        return
    st.caption(f"**{res['repas']} repas** sur {res['du']} → {res['au']} · "
               f"portions du foyer : **{res['portions_foyer']:.1f}**")
    for rayon, articles in sorted(res["rayons"].items()):
        with st.expander(f"**{rayon}** — {len(articles)} article(s)", expanded=True):
            for a in articles:
                etoile = "🔁 " if a.get("recurrent") else ""
                detail = ""
                if a["recettes"]:
                    detail = " · " + ", ".join(a["recettes"][:2])
                    if len(a["recettes"]) > 2:
                        detail += f" +{len(a['recettes'])-2}"
                st.markdown(f"- {etoile}**{MN.fmt_quantite(a)}** — {a['nom']}{detail}")
