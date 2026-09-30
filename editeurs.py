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

# ---------------------------------------------------------------------------
#  À quoi sert ce numéro : l'application l'affiche en bas de la barre de gauche
#  (« éditeur 2.8 »). S'il affiche autre chose, c'est que ce fichier n'a pas
#  été recopié sur GitHub.
# ---------------------------------------------------------------------------
VERSION = "2.9.1"

import datetime as dt
import traceback
import uuid

import pandas as pd
import streamlit as st

import menus as MN
import pdf_menus as PM

JOURS = PM.JOURS
JOURS_COURT = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
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


# Les noms de colonne qui peuvent jouer le rôle d'identifiant dans une base.
# On les essaie dans l'ordre : ainsi, que la clé s'appelle `id`, `recipe_id`,
# `uuid`… l'application s'en sort. C'est ce qui manquait quand tu as vu
# « KeyError : 'id' ».
CLES_ID = ("id", "uuid", "ID", "recipe_id", "ingredient_id", "planned_meal_id")


def _id(ligne) -> str | None:
    """L'identifiant d'une ligne, quel que soit le nom de la colonne. Ne plante jamais."""
    if not isinstance(ligne, dict):
        return None
    for cle in CLES_ID:
        v = ligne.get(cle)
        if v is not None and str(v).strip() not in ("", "null", "None"):
            return str(v)
    return None


def _colonnes(ms, table: str) -> list:
    """Les colonnes que la base renvoie VRAIMENT pour cette table (pour le diagnostic)."""
    try:
        lignes = ms.client.table(table).select("*").limit(1).execute().data or []
        return sorted(lignes[0].keys()) if lignes else []
    except Exception as e:
        return [f"⚠️ {type(e).__name__} : {e}"]


def bloc_diagnostic(ms):
    """Bouton « Diagnostic » : montre ce que ta base renvoie et teste une écriture."""
    with st.expander("🧪 Diagnostic de l'enregistrement (à ouvrir en cas de problème)"):
        st.caption("Cet outil **ne modifie rien** : il lit les colonnes de tes 4 tables, "
                   "puis fait un test d'écriture qu'il annule aussitôt.")
        c1, c2 = st.columns(2)
        relire = c2.button("🔄 Vider le cache et relire", key="diag_relire")
        if relire and mode_ecriture(ms):
            ms.vider_cache()
            st.success("Cache vidé : les compteurs ci-dessous sont relus en direct.")
        if c1.button("▶️ Lancer le diagnostic", key="diag_lancer") or relire:
            if not mode_ecriture(ms):
                st.warning("Pas de connexion Supabase : ouvre d'abord Réglages → clés.")
                return
            rapport = {}
            for t in ("ingredients", "recipes", "recipe_ingredients", "planned_meals"):
                cols = _colonnes(ms, t)
                nb = len(getattr(ms, {"ingredients": "ingredients", "recipes": "recettes",
                                      "recipe_ingredients": "lignes",
                                      "planned_meals": "planning"}[t])())
                st.markdown(f"**{t}** — {nb} ligne(s) lue(s)")
                st.code(", ".join(cols) if cols else "(aucune colonne)", language="text")
                rapport[t] = cols
            if getattr(ms, "erreur", None):
                st.error(f"⚠️ Erreur de lecture : {ms.erreur}")
            else:
                st.caption("Aucune erreur de lecture.")
            st.markdown("**Test d'écriture** (création puis suppression immédiate)")
            try:
                rid = _inserer(ms, "planned_meals", {
                    "day": "Lundi", "meal_type": "Test", "servings": 1, "nb_persons": 1,
                    "recipe_id": None}, identifiant=False)
                q = ms.client.table("planned_meals").delete()
                (q.eq("id", rid) if rid else q.eq("meal_type", "Test")).execute()
                ms.vider_cache()
                st.success("✅ Écriture et suppression : **OK** — l'enregistrement fonctionne.")
            except Exception as e:
                st.error(f"❌ Écriture impossible : {type(e).__name__} — {e}")
                st.caption("Envoie-moi cette phrase : elle contient la cause exacte.")
            st.caption("Si un tableau ci-dessus affiche « ⚠️ », cette table a un problème de "
                       "droits ou de nom : envoie-moi la capture.")

        st.divider()
        st.caption("**Rappel** : la page doit afficher 3492 ingrédients, 104 recettes, "
                   "161 lignes et 79 repas si ta base est complète.")


def mode_ecriture(ms) -> bool:
    """Peut-on vraiment enregistrer ? (faux en mode aperçu)"""
    return getattr(ms, "client", None) is not None


def _table(ms, nom: str):
    """Renvoie le nom de la table si l'écriture est possible, sinon None."""
    return nom if mode_ecriture(ms) else None


# Tables dont la colonne « id » est un UUID que NOUS fabriquons.
# `planned_meals` n'en fait PAS partie : sa colonne id est un ENTIER que la base
# numérote elle-même (162, 163…). Y mettre un UUID faisait échouer l'écriture
# avec « invalid input syntax for type bigint » — c'est maintenant corrigé.
ID_UUID = {"recipes": True, "recipe_ingredients": True, "ingredients": True,
           "planned_meals": False}


def _inserer(ms, table: str, charge: dict, identifiant: bool | None = None) -> str | None:
    """Enregistre une ligne et renvoie son identifiant (None si la base le gère).

    • Pour `recipes`, `recipe_ingredients` et `ingredients` : on fabrique l'UUID
      nous-mêmes avant l'envoi, donc on n'a rien à relire après.
    • Pour `planned_meals` : la base numérote (id entier) — on n'envoie pas d'id.
    """
    if identifiant is None:
        identifiant = ID_UUID.get(table, True)
    ligne = dict(charge)
    if identifiant:
        ligne.setdefault("id", str(uuid.uuid4()))
    else:
        ligne.pop("id", None)
    ms.client.table(table).insert(ligne).execute()
    return ligne.get("id")


def _erreur(action: str, e: Exception, details: dict | None = None):
    """Affiche une erreur compréhensible, avec le nécessaire pour la diagnostiquer."""
    st.error(f"**{action} — impossible.** {type(e).__name__} : {e}")
    with st.expander("🔍 Détail (à m'envoyer si ça recommence)"):
        st.markdown(f"- **Action** : {action}\n- **Type d'erreur** : `{type(e).__name__}`"
                    f"\n- **Message exact** : `{e}`")
        if details:
            st.json(details, expanded=False)
        st.code(traceback.format_exc(), language="text")
        st.caption("Copie-colle ce cadre (ou une capture) : il contient la ligne exacte "
                   "où ça bloque. Utilise aussi « 🧪 Diagnostic » en bas de la page Planifier.")


def nom_affiche(ing: dict) -> str:
    """Nom court et familier si on l'a (« Boeuf haché » plutôt que le nom Ciqual)."""
    return ing.get("nom_affiche") or ing.get("name") or "?"


def liste_recettes(ms) -> list[dict]:
    r = [r for r in ms.recettes()
         if not (r.get("name") or "").startswith(("[Ing]", "[Txt]"))]
    return sorted(r, key=lambda x: (x.get("name") or "").lower())


# Les deux cases de gestion des courses (mêmes mots que dans gestion-menus).
COL_FOND = "🚪 Fond de placard (hors liste)"
COL_RECUR = "🔁 Récurrent"
CASE_COLS = (COL_FOND, COL_RECUR)


def compteur_doublons(ingredients: list) -> dict:
    """{nom en minuscules: nombre de lignes} — pour repérer les doublons."""
    from collections import Counter
    c = Counter()
    for i in ingredients:
        nom = (i.get("name") or "").strip().lower()
        if nom:
            c[nom] += 1
    return dict(c)


def liste_ingredients(ms, tout: bool = False) -> list[dict]:
    """Tes ingrédients + ceux utilisés dans les recettes.

    `tout=True` ajoute les 3 339 aliments de la base française (ils servent aux
    valeurs nutritionnelles). Par défaut on ne montre que les tiens : sinon la
    liste est noyée sous 3 300 lignes d'aliments de référence.
    """
    if tout:
        return sorted(ms.ingredients(), key=lambda x: _sans_accent(nom_affiche(x)))
    utilises = {l.get("ingredient_id") for l in ms.lignes()}
    out = [i for i in ms.ingredients()
           if _est_a_moi(i) or i.get("id") in utilises]
    return sorted(out, key=lambda x: _sans_accent(nom_affiche(x)))


def _est_a_moi(i: dict) -> bool:
    """Un ingrédient « à toi » : le tien, ou une ligne que tu as réglée.

    Depuis la fusion des doublons, tes ingrédients portent souvent un code de la
    base française (la fusion a gardé une seule ligne). Sans cette règle, ton
    beurre ou ta bûche de chèvre n'apparaîtraient plus dans la liste.
    """
    marque = i.get("est_a_moi")
    if marque is not None:          # colonne remplie par 13_base_unique.sql
        return bool(marque)
    return (not i.get("code_ciqual") or bool(i.get("nom_affiche"))
            or bool(i.get("exclude_from_list")) or bool(i.get("is_recurrent")))


def _sans_accent(t: str) -> str:
    """minuscule sans accents (pour trier « Édamame » avec les E, pas après les Z)."""
    import unicodedata
    txt = unicodedata.normalize("NFD", str(t or "").lower())
    return "".join(c for c in txt if unicodedata.category(c) != "Mn")


# ---------------------------------------------------------------------------
#  1. PLANIFIER LA SEMAINE
# ---------------------------------------------------------------------------
def page_planifier(ms, target_p: float):
    st.title("📅 Planifier mes menus")
    st.caption("Ta semaine de repas. Un repas peut être une **recette**, un **ingrédient seul** "
               "(ex. un fruit) ou du **texte libre** (ex. « Restaurant »).")
    if st.session_state.pop("pl_sql_manquant", False):
        st.warning("Ton repas est bien enregistré, mais **l'unité n'a pas pu l'être** : "
                   "lance le fichier **`23_unite_par_repas.sql`** (dossier 2_SQL du zip) "
                   "sur Supabase, puis recharge la page. En attendant, l'application "
                   "recalcule l'unité automatiquement.")

    recettes = liste_recettes(ms)
    # TOUTE la base : tes ingrédients + les aliments de la base française
    # (sinon on ne pouvait pas planifier un repas à base de Skyr ou d'amandes grillées).
    ingredients = liste_ingredients(ms, tout=True)
    if not recettes and not ingredients:
        st.warning("Crée d'abord une recette ou un ingrédient (page « Recettes & ingrédients »).")
        return

    # ---- choix de la semaine
    c1, c2 = st.columns([2, 3])
    depart = c1.date_input("Premier jour affiché",
                           value=dt.date.today(),
                           format="DD/MM/YYYY", key="pl_debut",
                           help="Choisis le jour que tu veux : les 7 jours suivants s'affichent "
                                "à partir de celui-là (pas besoin que ce soit un lundi).")
    jours = [depart + dt.timedelta(days=i) for i in range(7)]
    c2.markdown("**" + f"Du {JOURS[jours[0].weekday()].lower()} "
                f"{jours[0].strftime('%d/%m')} au {JOURS[jours[-1].weekday()].lower()} "
                f"{jours[-1].strftime('%d/%m/%Y')}" + "**")
    c2.caption("Les 7 jours commencent bien par celui que tu as choisi.")

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
                c = MN.calculer_recette(lignes_par_recette.get(rid, []), ings,
                                        rec.get("base_servings"), nom_recette=rec.get("name"))
                tot += c["par_part"]["proteines"]
        if tot >= target_p - 15:
            jours_ok += 1
        else:
            jours_light.append((d, tot))
    c3, c4 = st.columns(2)
    c3.metric("Jours qui atteignent la cible", f"{jours_ok} / 7")
    c4.metric("À compléter",
              ", ".join(f"{JOURS_COURT[d.weekday()]} {d.strftime('%d/%m')}"
                        for d, _ in jours_light) or "aucun")
    if jours_light:
        st.caption("Pour ces jours, prévois un en-cas protéiné : shaker, œufs durs, skyr. "
                   "(Compter 20 à 30 g pour un shaker.)")

    st.divider()

    # ---- LA RECHERCHE EST DANS CHAQUE LISTE (choix du 30/09) ----
    #  Avant : une barre « 🔍 Rechercher une recette ou un ingrédient » en haut de
    #  page, que ce n'était pas ce qu'il voulait. Maintenant : on tape directement
    #  dans la case posée sur la liste déroulante, le jour concerné.
    st.caption("Pour chercher : tape directement dans la case au-dessus de la liste "
               "**Recette** ou **Ingrédient** du repas (les accents ne comptent pas).")

    # ---- grille de la semaine
    for i, d in enumerate(jours):
        repas = repas_du_jour(d)
        # le nom du jour vient de LA DATE (avant : c'était le rang 0,1,2… de la liste,
        # donc en choisissant un mercredi la page écrivait quand même « Lundi »).
        titre = f"{JOURS[d.weekday()]} {d.strftime('%d/%m')}"
        with st.expander(f"**{titre}** — {len(repas)} repas", expanded=(d == dt.date.today())):
            for p in repas:
                rid = p.get("recipe_id")
                rec = recettes_par_id.get(rid) or {}
                nom = PM.get_display_name(rec) if rec else "—"
                c1, c2, c3 = st.columns([5, 1.3, 1.3])
                libelle = f"{p.get('meal_type') or ''} · **{nom}**"
                if p.get("ingredient_qty"):
                    _ing = PM._trouve_ing(nom, ing_par_id) or PM._trouve_ing(nom, ingredients)
                    _portion = None
                    if _est_convives(p.get("ingredient_unit")):
                        _portion = _portion_du_repas(ms, _ing)[0]
                    _q = PM._quantite_lisible(p["ingredient_qty"], _ing,
                                              p.get("ingredient_unit"), _portion)
                    # avant : « Pâtes — 200 » (sans unité). Maintenant : « Pâtes — 200 g »
                    libelle += f" — {_q}" if _q else f" — {p['ingredient_qty']:g}"
                if p.get("servings"):
                    try:                       # une base peut renvoyer 6.0 : on écrit « 6 »
                        libelle += f" · {float(p['servings']):g} convives"
                    except (TypeError, ValueError):
                        libelle += f" · {p['servings']} convives"
                c1.markdown(libelle)
                pid = _id(p)
                cle_repas = f"{pid or p.get('date_menu')}_{p.get('meal_type') or ''}"
                # « quelqu'un vient manger à l'improviste » → on peut changer le
                # nombre de convives et la quantité d'un repas déjà prévu (30/09)
                if c2.button("✏️ Modifier", key=f"pl_edit_btn_{cle_repas}",
                             help="Changer le moment, le nombre de convives ou la quantité "
                                  "de ce repas (invité de dernière minute)."):
                    st.session_state["pl_edit"] = cle_repas
                    st.rerun()
                if c3.button("🗑️ Supprimer", key=f"pl_del_{pid or p.get('date_menu')}"):
                    if _table(ms, "planned_meals"):
                        q = ms.client.table("planned_meals").delete()
                        if pid:
                            q.eq("id", pid).execute()
                        else:                    # pas d'id : on supprime par son contenu
                            q.eq("date_menu", p.get("date_menu")).eq(
                                "meal_type", p.get("meal_type")).eq(
                                "recipe_id", p.get("recipe_id")).execute()
                        _recharger(ms, "Repas supprimé.")
                    else:
                        st.warning("Mode aperçu : la modification n'est pas enregistrée.")
                if st.session_state.get("pl_edit") == cle_repas:
                    _editer_repas(ms, p, nom, cle_repas)

            if not repas:
                st.caption("Rien de prévu.")

            # ---- ajout
            #  TOUTES LES CASES SONT HORS FORMULAIRE, exprès : dans un formulaire,
            #  Streamlit ne relance pas la page quand on change une case. Le type,
            #  l'ingrédient et l'unité ne réagissaient donc pas (bugs du 30/09).
            t1, t2 = st.columns([2, 2])
            genre = t1.selectbox("Type", ["Recette", "Ingrédient", "Texte libre"],
                                 key=f"pl_g_{d}")
            f1, f2 = st.columns([2, 1])
            moment = f1.selectbox("Moment", ["Midi", "Soir"], key=f"pl_m_{d}")
            convives = f2.number_input("Convives", 1, 12, 4, key=f"pl_c_{d}",
                                       help="Le nombre de personnes présentes : les quantités "
                                            "de la liste de courses en tiennent compte.")
            t2.caption("Chaque case réagit tout de suite — rien à valider avant de choisir.")
            choix, qte, unite, ids_ing = None, None, None, None

            if genre == "Recette":
                choix, _ = _recherche_dans_liste(
                    [r.get("name") for r in recettes], None, cle=f"pl_sr_{d}",
                    label="🔍 Chercher une recette", type_element="recette",
                    cle_liste=f"pl_r_{d}",
                    aide="Tape « bolognaise », « curry »… la liste se réduit au fur et à mesure.")

            elif genre == "Ingrédient":
                noms, ids_ing = _choix_ingredients(ms, tout=True)
                choix, ing_choisi = _recherche_dans_liste(
                    noms, ids_ing, cle=f"pl_si_{d}", cle_liste=f"pl_i_{d}",
                    label="🔍 Chercher un ingrédient (tape par ex. « pates »)",
                    type_element="ingrédient",
                    aide="Tape « pates » : la liste propose « Pâtes ». La barre du haut de "
                         "page et l'onglet « Recherche » ont été retirés : la recherche se "
                         "fait ici, à l'endroit où on choisit.")
                if not noms:
                    st.caption("Ta base d'ingrédients est vide : remplis-la page "
                               "« Recettes & ingrédients ».")
                fiche = next((i for i in ingredients if _id(i) == ing_choisi), None)
                # ✅ CHOIX DE L'UNITÉ : la quantité veut enfin dire quelque chose
                #    (4 unités de steak haché ≠ 4 g). La clé contient l'aliment :
                #    l'unité proposée suit donc l'ingrédient choisi.
                q1, q2 = st.columns([1, 1])
                options_u = MN.unites_proposees(fiche)
                cle_u = f"pl_u_{d}_{ing_choisi or 'x'}"
                # la case « Quantité » porte le nom de l'unité : « Quantité (unité) ».
                # Impossible de se demander « 1, mais 1 quoi ? » (remarque du 30/09).
                deja_choisie = st.session_state.get(cle_u) or options_u[0]
                qte = None
                q1.empty()                       # on réécrit le champ avec le bon libellé
                qte = q1.number_input(f"Quantité ({deja_choisie})", 0.0, 5000.0, 1.0, step=0.5,
                                      key=f"pl_q_{d}",
                                      help="Le nombre d'unités choisies juste à droite.")
                unite = q2.selectbox("Unité", options_u, key=cle_u,
                                     help="« unité » = 1 steak haché (125 g pièce). "
                                          "« convives » = un nombre de personnes : 3 convives "
                                          "de pâtes = 3 × 80 g = 240 g. La liste de courses et "
                                          "la fiche PDF suivent l'unité choisie.")
                if fiche:
                    # ⭐ unité « convives » : la quantité est un NOMBRE DE PERSONNES.
                    #   3 convives de steak haché → 3 × 130 g → 390 g sur la liste.
                    portion, source = (None, "")
                    if _est_convives(unite):
                        portion, source = _portion_du_repas(ms, fiche)
                    total = PM._quantite_lisible(qte, fiche, unite, portion)
                    cout = _cout_ingredient(fiche, qte, unite, portion)
                    if portion:
                        st.caption(f"→ Ce repas demandera **{total or '—'}** à la liste de "
                                   f"courses ({float(qte):g} convive{'s' if float(qte) > 1 else ''} "
                                   f"× {portion:g} g par personne — {source}). {cout}")
                    else:
                        st.caption(f"→ Ce repas demandera **{total or '—'}** à la liste de "
                                   f"courses ({cout})")

            else:
                choix = st.text_input("Texte", placeholder="Restaurant, pique-nique…",
                                      key=f"pl_t_{d}")

            if st.button("➕ Ajouter ce repas", key=f"pl_add_btn_{d}", type="primary",
                         width="stretch"):
                # on vide les cases du jour pour le repas suivant (l'équivalent du
                # « clear_on_submit » d'avant), puis on enregistre
                for cle in [f"pl_r_{d}", f"pl_i_{d}", f"pl_q_{d}", f"pl_t_{d}"]:
                    st.session_state.pop(cle, None)
                for cle in [k for k in list(st.session_state.keys())
                            if isinstance(k, str) and k.startswith(f"pl_u_{d}_")]:
                    st.session_state.pop(cle, None)
                _ajouter_repas(ms, d, moment, convives, genre, choix, qte, recettes,
                               ingredients, ids_ing if genre == "Ingrédient" else None,
                               unite=unite)

    # ---- diagnostic (en bas de page)
    bloc_diagnostic(ms)

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
                    pid = _id(p)
                    q = ms.client.table("planned_meals").delete()
                    (q.eq("id", pid) if pid else q.eq("date_menu", p.get("date_menu"))).execute()
                    n += 1
            _recharger(ms, f"Semaine vidée ({n} repas supprimés).")
        else:
            st.warning("Mode aperçu : rien n'est supprimé.")


def _cout_ingredient(fiche: dict | None, qte, unite, portion=None) -> str:
    """Phrase d'explication : « ≈ 750 kcal, 82 g de protéines » pour cet ajout."""
    if not fiche:
        return "aliment inconnu de la base"
    try:
        q = float(qte or 0)
    except (TypeError, ValueError):
        return "quantité à préciser"
    u = str(unite or "").lower()
    try:
        poids = float(fiche.get("poids_piece_g") or 0) if u in ("unité", "unite") else 0
    except (TypeError, ValueError):
        poids = 0
    if _est_convives(u) and portion:          # ⭐ 3 convives → 3 × 130 g = 390 g
        grammes = q * float(portion)
    else:
        grammes = q * poids if poids else q
    k, pr = fiche.get("kcal_100g"), fiche.get("proteines_100g")
    if not grammes or (k is None and pr is None):
        return "valeurs non renseignées dans ta base"
    bouts = []
    if k is not None:
        bouts.append(f"≈ {float(k) * grammes / 100:,.0f} kcal".replace(",", " "))
    if pr is not None:
        bouts.append(f"{float(pr) * grammes / 100:,.0f} g de protéines".replace(",", " "))
    return " · ".join(bouts)


def _fiche_du_repas(ms, p, nom) -> dict | None:
    """La fiche de l'aliment d'un repas « [Ing] X » (pour l'unité et les valeurs)."""
    try:
        ings = ms.ing_par_id()
    except Exception:
        ings = {}
    fiche = PM._trouve_ing(nom, ings)
    if fiche is None:
        rid = p.get("recipe_id")
        for l in (ms.lignes_par_recette().get(rid) or []):
            fiche = ings.get(l.get("ingredient_id"))
            break
    return fiche


def _unite_courante(p) -> str:
    """L'unité enregistrée sur un repas (vide = calcul automatique)."""
    return str(p.get("ingredient_unit") or "").strip()


def _ecrire_repas(ms, table, charge: dict, unite, viser):
    """Enregistre un repas AVEC son unité, même si le SQL 23 n'a pas encore été
    lancé : dans ce cas on réenregistre sans l'unité (le repas n'est jamais perdu)
    et on prévient gentiment."""
    try:
        viser(dict(charge, ingredient_unit=unite)).execute()
        return True
    except Exception as e:
        msg = str(e).lower()
        if "ingredient_unit" in msg or "column" in msg or "schema" in msg:
            viser(dict(charge)).execute()
            # le message doit SURVIVRE au rechargement de la page (sinon il disparaît)
            st.session_state["pl_sql_manquant"] = True
            return False
        raise


def _editer_repas(ms, p, nom, cle):
    """Modifier un repas DÉJÀ prévu : moment, nombre de convives, quantité.

    Demandé le 30/09 : « je ne peux pas modifier le nombre de convives ni la
    quantité d'une recette déjà prévue pour un jour, si par exemple quelqu'un
    vient manger à l'improviste ». C'est le rôle de ce petit panneau.
    """
    from_ing = bool(p.get("ingredient_qty")) or str(nom).startswith("[Ing]")
    #  Les cases sont HORS du formulaire, exprès : dans un formulaire, Streamlit ne
    #  relance pas la page, donc l'aperçu et le nom de la case « Quantité (unité) »
    #  ne suivaient pas le choix de l'unité. Seuls les deux boutons restent dedans.
    st.markdown(f"**✏️ Modifier — {nom}**")
    e1, e2 = st.columns(2)
    moment = e1.selectbox("Moment", ["Midi", "Soir"],
                          index=0 if (p.get("meal_type") or "Midi") == "Midi" else 1,
                          key=f"pe_m_{cle}")
    convives = e2.number_input(
        "Convives", 1, 12,
        int(p.get("servings") or p.get("nb_persons") or 4), key=f"pe_c_{cle}",
        help="Le nombre de personnes présentes à ce repas. La liste de courses "
             "et la fiche PDF recalculent les quantités avec ce nombre.")
    qte, unite = None, None
    if from_ing:
        fiche = _fiche_du_repas(ms, p, nom)
        actuelle = _unite_courante(p)
        options_u = MN.unites_proposees(fiche)
        proposee = actuelle or options_u[0]
        if proposee not in options_u:
            options_u = [proposee] + options_u
        e3, e4 = st.columns(2)
        deja = st.session_state.get(f"pe_u_{cle}") or proposee
        qte = e3.number_input(f"Quantité ({deja})", 0.0, 5000.0,
                              float(p.get("ingredient_qty") or 1.0), step=0.5,
                              key=f"pe_q_{cle}",
                              help="La quantité de cet ingrédient seul (4 unités, 200 g…).")
        unite = e4.selectbox("Unité", options_u, key=f"pe_u_{cle}",
                             help="« unité » = 1 pièce de l'aliment. « convives » = un nombre "
                                  "de personnes : 3 convives de pâtes = 3 × 80 g = 240 g.")
        if fiche:
            portion, source = (None, "")
            if _est_convives(unite):
                portion, source = _portion_du_repas(ms, fiche)
            total = PM._quantite_lisible(qte, fiche, unite, portion)
            cout = _cout_ingredient(fiche, qte, unite, portion)
            if portion:
                st.caption(f"→ Ce repas demandera **{total or '—'}** "
                           f"({float(qte):g} convive{'s' if float(qte) > 1 else ''} "
                           f"× {portion:g} g par personne — {source}). {cout}")
            else:
                st.caption(f"→ Ce repas demandera **{total or '—'}** ({cout})")
    with st.form(f"pl_edit_{cle}"):
        b1, b2 = st.columns(2)
        enregistrer = b1.form_submit_button("💾 Enregistrer", width="stretch")
        annuler = b2.form_submit_button("Annuler", width="stretch")
    if annuler:
        st.session_state.pop("pl_edit", None)
        st.rerun()
    if enregistrer:
        if not _table(ms, "planned_meals"):
            st.warning("Mode aperçu : la modification n'est pas enregistrée.")
            return
        charge = {"meal_type": moment, "servings": convives, "nb_persons": convives}
        if from_ing and qte is not None:
            charge["ingredient_qty"] = qte
            charge["ingredient_unit"] = unite
        pid = _id(p)

        def viser(c):
            q = ms.client.table("planned_meals").update(c)
            if pid:
                return q.eq("id", pid)
            return q.eq("date_menu", p.get("date_menu")).eq(
                "meal_type", p.get("meal_type")).eq("recipe_id", p.get("recipe_id"))

        _ecrire_repas(ms, "planned_meals", charge, unite, viser)
        st.session_state.pop("pl_edit", None)
        _recharger(ms, f"Repas modifié ({convives} convives). "
                       "La liste de courses et la fiche PDF sont recalculées.")


def _ajouter_repas(ms, jour, moment, convives, genre, choix, qte, recettes, ingredients,
                   ids_ing: dict | None = None, unite=None):
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
            rid = next((_id(r) for r in recettes if r.get("name") == choix), None)
            if rid is None:
                st.error("Cette recette n'a pas d'identifiant lisible dans la base. "
                         "Ouvre « 🧪 Diagnostic » en bas de page et envoie-moi le résultat.")
                return
            ms.client.table("planned_meals").insert({
                "day": jour_fr, "date_menu": jour.isoformat(), "meal_type": moment,
                "recipe_id": rid, "servings": convives, "nb_persons": convives}).execute()
        elif genre == "Ingrédient":
            # par identifiant d'abord (aucune ambiguïté de nom), sinon par nom
            ident = (ids_ing or {}).get(choix)
            ing = next((i for i in ingredients if _id(i) == ident), None) if ident else None
            if ing is None:
                ing = next((i for i in ingredients if nom_affiche(i) == choix), None)
            if ing is None:
                st.error("Ingrédient introuvable.")
                return
            # on réutilise (ou crée) la recette « [Ing] Nom » comme dans ton application
            nom_rec = f"[Ing] {nom_affiche(ing)}"
            existante = next((r for r in ms.recettes() if r.get("name") == nom_rec), None)
            rid = _id(existante) if existante else None
            if rid is None:                       # pas de recette « [Ing] » : on la crée
                rid = _inserer(ms, "recipes", {
                    "name": nom_rec, "base_servings": 1, "instructions": ""})
                _inserer(ms, "recipe_ingredients", {
                    "recipe_id": rid, "ingredient_id": _id(ing), "quantity": 1,
                    "unit": ing.get("unit")})
            charge = {"day": jour_fr, "date_menu": jour.isoformat(),
                      "meal_type": moment, "recipe_id": rid,
                      "servings": convives, "nb_persons": convives,
                      "ingredient_qty": qte}

            def viser_ing(c):
                return ms.client.table("planned_meals").insert(c)

            if unite:
                # l'unité choisie part avec le repas (SQL 23) ; si la colonne n'existe
                # pas encore, le repas est quand même enregistré (voir _ecrire_repas)
                _ecrire_repas(ms, "planned_meals", charge, unite, viser_ing)
            else:
                viser_ing(charge).execute()
        else:
            nom_rec = f"[Txt] {choix.strip()}"
            rid = _inserer(ms, "recipes", {
                "name": nom_rec, "base_servings": 1, "instructions": ""})
            _inserer(ms, "planned_meals", {
                "day": jour_fr, "date_menu": jour.isoformat(), "meal_type": moment,
                "recipe_id": rid, "servings": convives, "nb_persons": convives},
                identifiant=False)
        _recharger(ms, "Repas ajouté.")
    except Exception as e:
        _erreur("Ajout du repas", e, dict(jour=str(jour), moment=moment, genre=genre,
                                          choix=choix, convives=convives))


def _fiche_pdf(ms, jours, planning, recettes_par_id, ing_par_id, pour_foyer: bool = True):
    dates = [d.isoformat() for d in jours]
    semaine = [p for p in planning if str(p.get("date_menu") or "")[:10] in dates]
    if not semaine:
        st.warning("Aucun repas prévu cette semaine.")
        return
    with st.spinner("Préparation de la fiche…"):
        try:
            recettes_pdf = {k: dict(v, name=PM.get_display_name(v), name_brut=v.get("name"))
                            for k, v in recettes_par_id.items()}
            agg, recurrents = PM.construire_agregat(semaine, recettes_pdf, ing_par_id,
                                                    ms.lignes(),
                                                    portions_defaut=MN.portion_foyer())
            # mêmes arrondis que la liste de courses, et noms courts
            for v in agg.values():
                if v.get("libre"):
                    # aliment absent de la base : on garde le nombre saisi tel quel
                    # (l'arrondir à 5 g n'aurait aucun sens : c'est un nombre de pièces)
                    v["qty"] = float(v.get("qty") or 0)
                    v["unit"] = ""
                    continue
                ing = ing_par_id.get(v.get("ingredient_id"))
                if ing is None:
                    ing = next((i for i in ing_par_id.values()
                                if i.get("name") == v["name"]), None)
                # ⚠️ l'agrégat utilise « qty »/« unit » : arrondi_achat attend
                # « quantite »/« unite » → sans cette traduction, les arrondis de la
                # liste de courses n'étaient PAS appliqués dans la fiche PDF
                # (on lisait « 22,43 œufs »). Corrigé en 2.8.4.
                arr = MN.arrondi_achat(dict(
                    v, quantite=v.get("qty"), unite=v.get("unit"),
                    poids_piece_g=(ing or {}).get("poids_piece_g"),
                    nom=(ing or {}).get("name") or v.get("name"),
                    rayon=v.get("category"),
                    unite_declaree=(ing or {}).get("unite_liste_courses")
                    or (ing or {}).get("unit")))
                v["qty"] = arr.get("quantite", v.get("qty")) or 0.0
                v["unit"] = arr.get("unite") or v.get("unit")
                pieces = arr.get("pieces")
                # « Steak haché » (son nom, saisi dans le planning) plutôt que
                # « Boeuf haché » (le nom de la fiche de base)
                court = (v.get("nom_personnel") or v.get("nom")
                         or (MN.nom_court(ing) if ing else None) or v["name"])
                if pieces and pieces > 1:
                    v["name"] = f"{court} ({pieces} unités)"
                else:                              # 1 pièce : inutile de l'écrire
                    v["name"] = court
            recurrents = [dict(r, name=MN.nom_court(r)) for r in recurrents]
            pdf = PM.generate_pdf(semaine, agg, recurrents, recettes_par_id,
                                  ingredients_dict=ing_par_id, start_date=jours[0],
                                  recipe_ings=ms.lignes_par_recette())
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
        elif MN.unite_propre(u).lower() in ("unité", "tranche", "gousse", "boîte",
                                            "sachet", "barquette"):
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


def _recherche_dans_liste(libelles, ids, cle: str, label: str,
                          type_element: str = "ingrédient", aide: str = "",
                          cle_liste: str | None = None):
    """LE module de recherche (il n'y en a qu'un dans toute l'application).

    Il tape « pates » dans la case 🔍 : la liste des choix juste en dessous ne
    garde que ce qui correspond — accents et majuscules ignorés — puis il clique.
    Aucune autre recherche ne se cache dans la liste (avant, la liste déroulante
    de Streamlit avait la sienne et répondait « No results » à « pates »).

    Renvoie (libellé choisi, identifiant) ; « — » = aucun aliment choisi.
    """
    titre = "Recette" if type_element == "recette" else "Ingrédient"
    choix = MN.chercheur(
        titre, ["—"] + list(libelles), cle=cle, cle_liste=cle_liste,
        libelle_recherche=label, type_element=type_element, aide=aide,
        nombre=25, encadre=True)
    return choix, (ids or {}).get(choix)


def _portion_du_repas(ms, fiche):
    """La portion recommandée par personne pour cet aliment (source incluse)."""
    if not fiche:
        return None, ""
    try:
        return MN.portion_personne(fiche, ms.lignes(), ms.recette_par_id())
    except Exception:
        return MN.portion_personne(fiche)


def _est_convives(unite) -> bool:
    """Vrai si l'unité choisie est « convives » (ou « personnes »)."""
    return str(unite or "").strip().lower().startswith(("convive", "personne"))


def _choix_ingredients(ms, tout: bool = True):
    """Construit la liste déroulante des ingrédients : libellés → identifiant.

    On travaille par IDENTIFIANT (et non par nom) : c'est ce qui garantit que
    l'ingrédient choisi est exactement celui enregistré dans la recette.

    `tout=True` propose TOUTE la base (tes ingrédients + les 3 200 aliments de
    la base française) ; `tout=False` ne montre que les tiens.
    """
    libelles: list[str] = []
    ids: dict[str, str] = {}
    for i in liste_ingredients(ms, tout=tout):
        lib = nom_affiche(i)
        if lib in ids:                      # deux aliments au même nom : on précise
            base_lib, n = lib, 2
            while lib in ids:
                lib = f"{base_lib} ({n})"
                n += 1
        libelles.append(lib)
        ident = _id(i)
        if ident:
            ids[lib] = ident
    return libelles, ids


def _lignes_recette(ms, prefixe: str, actuelles: list | None = None,
                    tout: bool = True) -> list[dict]:
    """Éditeur des lignes « ingrédient + quantité + unité » d'une recette.

    • les lignes DÉJÀ dans la recette gardent leur identifiant (`ligne_id`) :
      on pourra les mettre à jour, et même changer leur ingrédient ;
    • les lignes ajoutées à l'écran n'ont pas d'identifiant : on les créera ;
    • chaque ligne a une clé stable (`uid`) : supprimer une ligne ne décale plus
      les choix des lignes suivantes (c'était une source d'erreurs).
    """
    import uuid as _uuid

    etat = f"{prefixe}_lignes"
    supp = f"{prefixe}_supprimees"

    def _nouvelle(l=None):
        return {"uid": _uuid.uuid4().hex[:8],
                "ligne_id": (l or {}).get("ligne_id"),
                "ingredient_id": (l or {}).get("ingredient_id"),
                "quantity": float((l or {}).get("quantity") or 100),
                "unit": (l or {}).get("unit") or "g"}

    if etat not in st.session_state:
        st.session_state[etat] = [_nouvelle(l) for l in (actuelles or [])] or [_nouvelle()]
        st.session_state[supp] = []

    libelles, ids = _choix_ingredients(ms, tout=tout)
    inverse: dict[str, str] = {}
    for lib, ident in ids.items():
        inverse.setdefault(str(ident), lib)
    # LA case de recherche de la page (une seule, accents ignorés) : elle filtre
    # les listes de choix de TOUTES les lignes de la recette.
    recherche = MN.champ_recherche(f"{prefixe}_rech", "🔍 Chercher un ingrédient",
                         placeholder="pates, courgette, fromage…")
    if recherche.strip():
        gardes = MN.filtre_recherche(libelles, recherche)
        if gardes:
            st.caption(f"**{len(gardes)}** ingrédient(s) sur {len(libelles)} correspondent "
                       f"à « {recherche} » — les listes de chaque ligne suivent. "
                       "Efface la case pour tout revoir.")
        else:
            st.warning(f"Rien ne correspond à « {recherche} ». Efface la case pour revoir "
                       f"les {len(libelles)} aliments.")
    options = ["—"] + libelles

    lignes = st.session_state[etat]
    for idx in list(range(len(lignes))):
        if idx >= len(st.session_state[etat]):        # supprimée entre-temps
            break
        ligne = st.session_state[etat][idx]
        cle = ligne["uid"]
        c1, c2, c3, c4 = st.columns([5, 1.6, 1.6, 0.7])
        k = f"{prefixe}_i_{cle}"
        # le choix de la ligne : le MÊME module de recherche que partout ailleurs
        # (les options suivent la case 🔍 du haut de page, aucune recherche cachée)
        courant = inverse.get(str(ligne.get("ingredient_id"))) or "—"
        with c1:
            choix_ligne = MN.chercheur(
                "Ingrédient", options, cle=k, terme=recherche, valeur=courant,
                nombre=10, encadre=False, horizontal=True, type_element="ingrédient")
        if choix_ligne and choix_ligne != "—":
            ligne["ingredient_id"] = ids.get(choix_ligne) or ligne.get("ingredient_id")
        elif choix_ligne == "—":
            ligne["ingredient_id"] = None
        ligne["quantity"] = c2.number_input(
            "Qté", 0.0, 100000.0, float(ligne.get("quantity") or 100), step=10.0,
            key=f"{prefixe}_q_{cle}", label_visibility="collapsed")
        ku = f"{prefixe}_u_{cle}"
        if ku not in st.session_state:
            u = ligne.get("unit") if ligne.get("unit") in UNITES else UNITES[0]
            st.session_state[ku] = u
        c3.selectbox("Unité", UNITES, key=ku, label_visibility="collapsed")
        ligne["unit"] = st.session_state[ku]
        if c4.button("❌", key=f"{prefixe}_x_{cle}"):
            lid = ligne.get("ligne_id")
            if lid:
                st.session_state[supp].append(lid)
                # LA SUPPRESSION EST IMMÉDIATE : plus besoin de cliquer sur
                # « 💾 Enregistrer » pour que la ligne disparaisse vraiment.
                if _table(ms, "recipe_ingredients"):
                    try:
                        ms.client.table("recipe_ingredients").delete().eq("id", lid).execute()
                        st.session_state[supp] = [x for x in st.session_state[supp] if x != lid]
                        # on vide le cache de lecture : sans ça, la ligne supprimée
                        # serait encore là au prochain rechargement de l'écran
                        if hasattr(ms, "vider_cache"):
                            ms.vider_cache()
                        st.session_state[f"{prefixe}_flash"] = (
                            "✅ Ligne supprimée de la recette (c'est enregistré).")
                    except Exception as e:                       # noqa: BLE001
                        st.session_state[f"{prefixe}_flash"] = (
                            f"⚠️ La ligne est retirée à l'écran, mais l'écriture dans la base "
                            f"a échoué ({type(e).__name__}). Clique sur **💾 Enregistrer** pour "
                            "confirmer la suppression.")
            st.session_state[etat].pop(idx)
            st.rerun()

    if st.button("➕ Ajouter une ligne", key=f"{prefixe}_add"):
        st.session_state[etat].append(_nouvelle())
        st.rerun()

    return [dict(l) for l in st.session_state[etat]]


def _lignes_a_enregistrer(lignes: list) -> list:
    """Ne garde que les lignes utilisables (un ingrédient a bien été choisi)."""
    return [l for l in lignes if l.get("ingredient_id")]


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
    st.caption("Choisis les ingrédients **dans toute ta base** : tes ingrédients, "
               "le Skyr et les amandes grillées que tu viens d'ajouter, et les "
               "3 200 aliments de la base française.")
    c1, c2 = st.columns([3, 1])
    nom = c1.text_input("Nom de la recette", key="cr_nom")
    parts = c2.number_input("Parts", 1, 20, 4, key="cr_parts")
    tout = st.checkbox("🌍 Proposer aussi la base française (3 200 aliments)",
                       value=True, key="cr_tout",
                       help="Décoche pour ne voir que TES ingrédients.")
    st.markdown("**Ingrédients**")
    lignes = _lignes_recette(ms, "cr", tout=tout)
    st.markdown("**Préparation**")
    etapes = _editeur_etapes("cr", "")
    if st.button("💾 Enregistrer la recette", type="primary", width="stretch", key="cr_save"):
        a_enregistrer = _lignes_a_enregistrer(lignes)
        if not nom.strip():
            st.error("Le nom est obligatoire.")
        elif not _table(ms, "recipes"):
            st.warning("Mode aperçu : l'enregistrement n'est pas possible sans tes clés Supabase.")
        elif not a_enregistrer:
            st.error("Ajoute au moins un ingrédient (et choisis-le dans la liste de gauche).")
        else:
            try:
                rid = _inserer(ms, "recipes", {
                    "name": nom.strip(), "base_servings": parts,
                    "instructions": PM.instructions_to_text(etapes)})
                n = 0
                for l in a_enregistrer:
                    _inserer(ms, "recipe_ingredients", {
                        "recipe_id": rid, "ingredient_id": l["ingredient_id"],
                        "quantity": l["quantity"], "unit": l["unit"]})
                    n += 1
                for cle in ("cr_lignes", "cr_etapes", "cr_nom"):
                    st.session_state.pop(cle, None)
                _recharger(ms, f"Recette « {nom} » créée avec {n} ingrédient(s).")
            except Exception as e:
                _erreur("Création de la recette", e,
                        dict(nom=nom, parts=parts, nb_ingredients=len(a_enregistrer)))


def _modifier_recette(ms):
    recettes = liste_recettes(ms)
    if not recettes:
        st.info("Aucune recette pour l'instant.")
        return
    noms = {r.get("name"): r.get("id") for r in recettes}
    # liste cherchable ET insensible aux accents (tape « pates » pour « Pâtes »)
    #  LE module de recherche de l'application (le seul) : « pates » suffit à
    #  trouver « Pâtes à la carbonara », accents et majuscules ignorés.
    choix = MN.selecteur_recherche("Recette à modifier", list(noms.keys()), "mr_choix")
    if choix is None:                      # rien trouvé : chercheur l'a déjà expliqué
        return
    rid = noms[choix]

    # Chaque recette a son propre brouillon : changer de recette repart de zéro
    # (avant, les lignes ajoutées et les étapes restaient d'une recette à l'autre).
    prefixe = "mr" + str(rid).replace("-", "")[:8]
    ancien = st.session_state.get("mr_prefixe")
    if ancien and ancien != prefixe:
        for cle in [k for k in list(st.session_state.keys()) if str(k).startswith(str(ancien))]:
            st.session_state.pop(cle, None)
    st.session_state["mr_prefixe"] = prefixe

    calc = ms.recette(rid)
    lignes_actuelles = list(ms.lignes_par_recette().get(rid, []))

    st.markdown("**Valeurs par part** *(recette entière divisée par le nombre de parts)*")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("kcal", f"{calc['par_part']['kcal']:.0f}")
    c2.metric("Protéines", f"{calc['par_part']['proteines']:.0f} g")
    c3.metric("Glucides", f"{calc['par_part']['glucides']:.0f} g")
    c4.metric("Lipides", f"{calc['par_part']['lipides']:.0f} g")
    c5.metric("Parts", f"{calc['parts']:g}")
    if calc.get("inconnues"):
        st.warning("Sans valeurs nutritionnelles dans ta base (comptés pour 0) : "
                   + ", ".join(calc["inconnues"]) + " → lance `7_nutrition.sql`.", icon="⚠️")
    if calc.get("estimees"):
        st.info("Quantités déduites automatiquement (une portion par personne) pour : "
                + ", ".join(calc["estimees"]) + ". Corrige-les ci-dessous si besoin.", icon="ℹ️")

    f1, f2 = st.columns([3, 1])
    nom = f1.text_input("Nom", value=choix, key=f"{prefixe}_nom")
    parts = f2.number_input("Parts", 1, 20, int(calc["parts"]), key=f"{prefixe}_parts")

    flash = st.session_state.pop(f"{prefixe}_flash", None)
    if flash:
        st.success(flash)

    st.markdown("**Ingrédients de la recette**")
    st.caption("La **❌** supprime la ligne **tout de suite** (c'est enregistré dans ta base). "
               "Tu peux aussi **changer l'ingrédient** de chaque ligne : choisis-en un autre "
               "dans la liste.")
    tout = st.checkbox("🌍 Proposer aussi la base française (3 200 aliments)",
                       value=True, key=f"{prefixe}_tout",
                       help="Décoche pour ne voir que TES ingrédients.")
    actuelles = [{"ligne_id": _id(l), "ingredient_id": l.get("ingredient_id"),
                  "quantity": l.get("quantity"), "unit": l.get("unit")}
                 for l in lignes_actuelles]
    lignes = _lignes_recette(ms, prefixe, actuelles=actuelles, tout=tout)

    st.markdown("**Préparation**")
    etapes = _editeur_etapes(prefixe, calc.get("instructions") or "")

    if st.button("💾 Sauvegarder les modifications", type="primary", width="stretch",
                 key=f"{prefixe}_save"):
        if not _table(ms, "recipes"):
            st.warning("Mode aperçu : l'enregistrement n'est pas possible sans tes clés Supabase.")
        else:
            try:
                ms.client.table("recipes").update({
                    "name": nom.strip(), "base_servings": parts,
                    "instructions": PM.instructions_to_text(etapes)}).eq("id", rid).execute()
                ajout = 0
                for l in lignes:
                    if not l.get("ingredient_id"):
                        continue
                    if l.get("ligne_id"):
                        ms.client.table("recipe_ingredients").update({
                            "ingredient_id": l["ingredient_id"],
                            "quantity": l["quantity"], "unit": l["unit"]}).eq(
                                "id", l["ligne_id"]).execute()
                    else:
                        _inserer(ms, "recipe_ingredients", {
                            "recipe_id": rid, "ingredient_id": l["ingredient_id"],
                            "quantity": l["quantity"], "unit": l["unit"]})
                        ajout += 1
                for lid in st.session_state.get(f"{prefixe}_supprimees") or []:
                    ms.client.table("recipe_ingredients").delete().eq("id", lid).execute()
                _recharger(ms, f"Modifications enregistrées ({ajout} ingrédient(s) ajouté(s)).")
            except Exception as e:
                _erreur("Modification de la recette", e, dict(recette=choix))

    st.divider()
    with st.expander("🗑️ Supprimer cette recette"):
        st.caption("La recette et ses lignes d'ingrédients seront supprimées. "
                   "Les repas déjà planifiés avec elle ne s'afficheront plus.")
        if st.button(f"Supprimer « {choix} »", key=f"{prefixe}_del"):
            if not _table(ms, "recipes"):
                st.warning("Mode aperçu : rien n'est supprimé.")
            else:
                try:
                    ms.client.table("recipe_ingredients").delete().eq("recipe_id", rid).execute()
                    ms.client.table("recipes").delete().eq("id", rid).execute()
                    _recharger(ms, "Recette supprimée.")
                except Exception as e:
                    _erreur("Suppression de la recette", e, dict(recette=choix))


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
    utilises = {l.get("ingredient_id") for l in ms.lignes()}

    if onglet.startswith("📋"):
        nb_perso = len([i for i in ms.ingredients() if _est_a_moi(i)])
        nb_base = len(ms.ingredients()) - nb_perso
        c0, c1, c2, c3 = st.columns([2, 3, 2, 2])
        inclus = c0.checkbox(f"🌍 Inclure la base française ({nb_base})",
                             value=False, key="ing_tout",
                             help="Les aliments de référence qui donnent les valeurs "
                                  "nutritionnelles. Décoche pour ne voir que TES "
                                  f"{nb_perso} ingrédients.")
        tous = liste_ingredients(ms, tout=inclus)
        #  la case du module de recherche (accents ignorés) — la même partout
        q = MN.champ_recherche("ing_rayon_q", "🔍 Chercher un ingrédient",
                               placeholder="lait, courgette, fromage…")
        rayon = c2.selectbox("Rayon", ["Tous"] + RAYONS)
        filtre = c3.selectbox("Afficher", ["Tout", "🚪 Fond de placard", "🔁 Récurrent",
                                           "⚠️ Doublons"])
        doublons = compteur_doublons(tous)
        #  on passe par LE module de recherche (accents ignorés, résultats justes :
        #  « lentille » ne propose plus les « dentelle »). Une seule fois, pour
        #  toute la liste, c'est instantané.
        gardes = None
        if str(q or "").strip():
            gardes = {str(x) for x in MN.filtre_recherche([nom_affiche(i) for i in tous], q)}
        vus, ids = [], []
        for i in tous:
            n = nom_affiche(i)
            if gardes is not None and str(n) not in gardes:
                continue
            if rayon != "Tous" and (i.get("category") or "Autre") != rayon:
                continue
            if filtre == "🚪 Fond de placard" and not i.get("exclude_from_list"):
                continue
            if filtre == "🔁 Récurrent" and not i.get("is_recurrent"):
                continue
            if filtre == "⚠️ Doublons" and doublons.get((i.get("name") or "").strip().lower(),
                                                        0) < 2:
                continue
            ids.append(i.get("id"))
            vus.append({"Ingrédient": n,
                        "Origine": ("le mien" if _est_a_moi(i) else "base française"),
                        "Rayon": i.get("category") or "Autre",
                        "Unité": i.get("unit"),
                        "kcal": i.get("kcal_100g"), "Protéines": i.get("proteines_100g"),
                        "Glucides": i.get("glucides_100g"), "Lipides": i.get("lipides_100g"),
                        "Poids unité (g)": i.get("poids_piece_g"),
                        "Dans mes recettes": "✓" if i.get("id") in utilises else "",
                        "⚠️": ("double" if doublons.get((i.get("name") or "").strip().lower(),
                                                        0) > 1 else ""),
                        COL_FOND: bool(i.get("exclude_from_list")),
                        COL_RECUR: bool(i.get("is_recurrent"))})
        noms_doubles = sum(1 for c in doublons.values() if c > 1)
        if noms_doubles and filtre != "⚠️ Doublons":
            st.warning(f"⚠️ **{noms_doubles} nom(s) existent en plusieurs lignes** "
                       f"(ex. deux « Aubergine »). Choisis **Afficher → ⚠️ Doublons** pour "
                       "les voir, et lance le script **`10_doublons.sql`** dans Supabase "
                       "pour regrouper les vraies paires.")
        st.caption(f"{len(vus)} ligne(s) affichée(s) sur {len(ms.ingredients())} au total "
                   f"— valeurs pour 100 g. "
                   f"Les deux dernières colonnes se cochent **directement dans le tableau** : "
                   f"**🚪 Fond de placard** = tu l'as toujours à la maison, il sort de la "
                   f"liste de courses · **🔁 Récurrent** = à racheter chaque semaine "
                   f"(il apparaît dans la liste même hors menus).")
        if not vus:
            st.info("Aucun ingrédient avec ce filtre.")
            return
        df = pd.DataFrame(vus)
        df.insert(0, "_id", ids)
        edite = st.data_editor(
            df, hide_index=True, width="stretch", height=460, key="ing_editeur",
            disabled=[c for c in df.columns if c not in CASE_COLS],
            column_config={"_id": None,
                           "⚠️": st.column_config.TextColumn("⚠️", width="small",
                                                             help="Ce nom apparaît sur "
                                                                  "plusieurs lignes."),
                           COL_FOND: st.column_config.CheckboxColumn(
                               COL_FOND, help="Coché = article que tu as toujours chez toi : "
                                              "il ne sort pas dans la liste de courses."),
                           COL_RECUR: st.column_config.CheckboxColumn(
                               COL_RECUR, help="Coché = à racheter toutes les semaines.")})
        modifs = []
        for pos in range(min(len(df), len(edite))):
            apres, avant = edite.iloc[pos], df.iloc[pos]
            change = {}
            for col in CASE_COLS:
                v_apres, v_avant = bool(apres[col]), bool(avant[col])
                if v_apres != v_avant:
                    change["exclude_from_list" if col == COL_FOND else "is_recurrent"] = v_apres
            if change:
                modifs.append((avant["_id"], change))
        if modifs:
            if not _table(ms, "ingredients"):
                st.warning("Mode aperçu : les cases ne sont pas enregistrées. "
                           "Il faut les clés Supabase (page Réglages).")
            else:
                try:
                    for cid, change in modifs:
                        ms.client.table("ingredients").update(change).eq("id", cid).execute()
                    _recharger(ms, f"{len(modifs)} ingrédient(s) mis à jour.")
                except Exception as e:
                    _erreur("Mise à jour des cases", e, dict(nb=len(modifs)))

    elif onglet.startswith("➕"):
        with st.form("ajouter_ingredient", clear_on_submit=True):
            c1, c2 = st.columns(2)
            nom = c1.text_input("Nom")
            unite = c2.selectbox("Unité", ["-"] + UNITES)
            c3, c4 = st.columns(2)
            rayon = c3.selectbox("Rayon", ["-"] + RAYONS)
            poids = c4.number_input("Poids d'une unité (g)", 0.0, 5000.0, 0.0, step=10.0)
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
                        _inserer(ms, "ingredients", {
                            "name": nom.strip(), "unit": unite,
                            "category": rayon, "exclude_from_list": hors,
                            "is_recurrent": recur,
                            "poids_piece_g": poids or None,
                            "unite_liste_courses": unite,
                            "kcal_100g": kcal or None, "proteines_100g": prot or None,
                            "glucides_100g": gluc or None, "lipides_100g": lip or None,
                            "source": "mes ingrédients"})
                        _recharger(ms, "Ingrédient ajouté.")
                    except Exception as e:
                        _erreur("Ajout de l'ingrédient", e, dict(nom=nom, unite=unite,
                                                                 rayon=rayon))

    else:
        # ⚠️ ici on n'est PAS passé par l'onglet « Consulter » : la liste complète
        # doit être rechargée, sinon la page plante (bug corrigé en 2.8.4).
        tous = liste_ingredients(ms, tout=True)
        mes = [i for i in tous if _est_a_moi(i)]
        if not mes:
            st.info("Aucun ingrédient personnel à modifier. Ceux de la base française ne se "
                    "modifient pas : ils servent de référence.")
            return
        noms = {nom_affiche(i): i for i in mes}
        choix = MN.selecteur_recherche("Ingrédient", list(noms.keys()), "ing_edit",
                                        nombre=15)
        if choix is None:                  # rien trouvé : chercheur l'a déjà expliqué
            return
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
            poids = c4.number_input("Poids d'une unité (g)", 0.0, 5000.0,
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
                        }).eq("id", _id(ing)).execute()
                        _recharger(ms, "Ingrédient modifié.")
                    except Exception as e:
                        _erreur("Modification de l'ingrédient", e, dict(nom=nom))

        with st.expander("🗑️ Supprimer cet ingrédient"):
            nb = sum(1 for l in ms.lignes() if l.get("ingredient_id") == _id(ing))
            if nb:
                st.warning(f"Cet ingrédient est utilisé dans {nb} ligne(s) de recettes. "
                           "Supprime-le d'abord de ces recettes.")
            elif st.button("Supprimer", key="ing_del"):
                if _table(ms, "ingredients"):
                    ms.client.table("ingredients").delete().eq("id", _id(ing)).execute()
                    _recharger(ms, "Ingrédient supprimé.")
