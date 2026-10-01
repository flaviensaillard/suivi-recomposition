# -*- coding: utf-8 -*-
"""Tableaux modifiables — corriger une valeur directement dans le tableau.

Principe (demandé par Flavien) : quand une valeur a été mal saisie, on doit
pouvoir la corriger **sur place**, dans le tableau, sans ressaisir la ligne
entière ni passer par un formulaire.

Utilisation :

    res = T.tableau_editable(
        df,                                   # index = identifiant de la ligne
        cle="pesee",
        sauver=lambda jour, champs: store.save_daily(...),
        colonnes={"Poids": T.col_nombre(step=0.1, mini=40, maxi=150)},
        supprimer=lambda jour: store.delete_daily(jour),   # optionnel : case 🗑️
    )

Règles de sécurité (importantes pour ne rien casser) :

* rien n'est écrit tant que la personne n'a pas cliqué sur **💾 Enregistrer** ;
* on ne sauvegarde QUE les cases réellement modifiées ;
* une ligne oubliée / non modifiée n'est jamais réécrite ;
* l'identifiant de la ligne (l'index du tableau) n'est jamais modifiable.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

COL_SUPPR = "🗑️"


VERSION = "1.0.8"        # vérifié au démarrage par app.py
# ---------------------------------------------------------------------------
#  petites fabriques de colonnes (pour un affichage propre)
# ---------------------------------------------------------------------------
def col_nombre(libelle: str, mini=None, maxi=None, pas=None, decimales=1, aide=None, fmt=None):
    return st.column_config.NumberColumn(libelle, min_value=mini, max_value=maxi, step=pas,
                                         format=fmt or f"%.{decimales}f", help=aide)


def col_entier(libelle: str, mini=None, maxi=None, pas=1, aide=None):
    return st.column_config.NumberColumn(libelle, min_value=mini, max_value=maxi, step=pas,
                                         format="%d", help=aide)


def col_texte(libelle: str, largeur="medium", aide=None):
    return st.column_config.TextColumn(libelle, width=largeur, help=aide)


def col_choix(libelle: str, options, aide=None):
    return st.column_config.SelectboxColumn(libelle, options=list(options), help=aide)


def col_jour(libelle: str = "Date", aide=None):
    return st.column_config.DateColumn(libelle, format="DD/MM/YYYY", help=aide)


def col_oui_non(libelle: str, aide=None):
    return st.column_config.CheckboxColumn(libelle, help=aide)


# ---------------------------------------------------------------------------
#  comparaison de valeurs (tolérante : 3.0 et 3 doivent être « égaux »)
# ---------------------------------------------------------------------------
def _vide(v) -> bool:
    try:
        return v is None or (not isinstance(v, (list, tuple, dict)) and bool(pd.isna(v)))
    except Exception:
        return v is None


def _egal(a, b) -> bool:
    if _vide(a) and _vide(b):
        return True
    if _vide(a) or _vide(b):
        return False
    try:
        fa, fb = float(a), float(b)
        return abs(fa - fb) < 1e-9
    except (TypeError, ValueError):
        return str(a).strip() == str(b).strip()


def lignes_modifiees(avant: pd.DataFrame, apres: pd.DataFrame, ignore=()) -> list[tuple]:
    """Les lignes réellement corrigées : [(identifiant, {colonne: nouvelle valeur})].

    Le tri se fait par **position** (comme le fait Streamlit), l'identifiant
    servant seulement à retrouver la bonne ligne en base.
    """
    out: list[tuple] = []
    colonnes = [c for c in avant.columns if c not in set(ignore)]
    for pos in range(min(len(avant), len(apres))):
        ligne_avant, ligne_apres = avant.iloc[pos], apres.iloc[pos]
        change = {}
        for col in colonnes:
            v_avant = ligne_avant.get(col) if hasattr(ligne_avant, "get") else ligne_avant[col]
            v_apres = ligne_apres.get(col) if hasattr(ligne_apres, "get") else ligne_apres[col]
            if not _egal(v_avant, v_apres):
                change[col] = v_apres
        if change:
            out.append((avant.index[pos], change))
    return out


def lignes_cochees(apres: pd.DataFrame, avant: pd.DataFrame) -> list:
    """Les identifiants des lignes cochées dans la colonne 🗑️."""
    if COL_SUPPR not in getattr(apres, "columns", []):
        return []
    out = []
    for pos in range(min(len(avant), len(apres))):
        try:
            if bool(apres.iloc[pos][COL_SUPPR]):
                out.append(avant.index[pos])
        except Exception:
            continue
    return out


# ---------------------------------------------------------------------------
#  le tableau modifiable
# ---------------------------------------------------------------------------
def tableau_editable(df: pd.DataFrame, cle: str, sauver=None, colonnes=None, desactive=(),
                     hauteur=None, aide=None, supprimer=None,
                     libelle_sauver="💾 Enregistrer les corrections",
                     message_vide=None, lecture_seule=False) -> dict:
    """Affiche `df` en tableau modifiable et enregistre les corrections au clic.

    `df`      : index = identifiant de la ligne (date, id…), colonnes = libellés affichés.
    `sauver`  : fonction(identifiant, {colonne: nouvelle valeur}) → True si enregistré.
    `supprimer` : fonction(identifiant) → True. Affiche une case 🗑️ pour supprimer la ligne.
    Renvoie un résumé : {"modifs": n, "suppr": n, "enregistre": bool}.
    """
    res = {"modifs": 0, "suppr": 0, "enregistre": False}
    if df is None or len(df) == 0:
        return res

    avant = df.copy()
    a_afficher = avant.copy()
    if supprimer is not None:
        a_afficher[COL_SUPPR] = False

    # message de confirmation du tour précédent (la sauvegarde déclenche un rerun)
    flash = st.session_state.pop(f"tblflash_{cle}", None)
    if flash:
        st.success(flash)

    version = st.session_state.get(f"tblv_{cle}", 0)
    widget = f"tbl_{cle}_{version}"
    for k in [k for k in list(st.session_state.keys()) if str(k).startswith(f"tbl_{cle}_")]:
        if k != widget:                       # états des versions précédentes : à jeter
            st.session_state.pop(k, None)

    conf = dict(colonnes or {})
    if supprimer is not None:
        conf[COL_SUPPR] = st.column_config.CheckboxColumn(
            COL_SUPPR, width="small", default=False,
            help="Coche cette case si tu veux **supprimer** la ligne, puis clique sur "
                 "« 💾 Enregistrer les corrections ».")

    commun = dict(hide_index=True, width="stretch", column_config=conf)
    if hauteur:                                # Streamlit refuse height=None
        commun["height"] = hauteur

    if lecture_seule:
        st.dataframe(a_afficher, **commun)
        if aide:
            st.caption(aide)
        return res

    edite = st.data_editor(a_afficher, key=widget, **commun,
                           disabled=list(desactive) + ([COL_SUPPR] if supprimer is None else []),
                           num_rows="fixed")

    modifs = lignes_modifiees(avant, edite, ignore=(COL_SUPPR,))
    a_supprimer = lignes_cochees(edite, avant) if supprimer is not None else []
    res.update(modifs=len(modifs), suppr=len(a_supprimer))

    if not modifs and not a_supprimer:
        if aide:
            st.caption(aide)
        return res

    quoi = []
    if modifs:
        quoi.append(f"**{len(modifs)} ligne(s) corrigée(s)**")
    if a_supprimer:
        quoi.append(f"**{len(a_supprimer)} ligne(s) à supprimer**")
    st.warning("🖊️ " + " et ".join(quoi) + " — clique sur le bouton pour valider.")
    if modifs:
        apercu = []
        for ident, ch in modifs[:5]:
            dedans = " · ".join(f"{c} → {_affiche(v)}" for c, v in ch.items())
            apercu.append(f"• {ident} : {dedans}")
        st.caption("\n".join(apercu))

    c1, c2 = st.columns([2, 1])
    if c1.button(libelle_sauver, type="primary", key=f"tblsave_{cle}", width="stretch"):
        erreurs = []
        for ident, ch in modifs:
            if sauver is None:
                continue
            try:
                r = sauver(ident, ch)
                if isinstance(r, tuple):
                    r = r[0]
                if isinstance(r, str) and r:
                    #  la correction explique elle-même pourquoi elle n'a pas pu
                    #  être enregistrée (ex. la date existe déjà) : on l'affiche
                    erreurs.append(f"**{_affiche(ident)}** — {r}")
                elif r is False:
                    erreurs.append(f"{ident} : refusé")
            except Exception as e:                     # noqa: BLE001
                erreurs.append(f"{ident} : {type(e).__name__} — {e}")
        for ident in a_supprimer:
            if supprimer is None:
                continue
            try:
                if supprimer(ident) is False:
                    erreurs.append(f"{ident} : suppression refusée")
            except Exception as e:                     # noqa: BLE001
                erreurs.append(f"{ident} : {type(e).__name__} — {e}")
        if erreurs:
            st.error("Rien n'a pu être enregistré :\n\n- " + "\n- ".join(erreurs))
        else:
            faits = []
            if modifs:
                faits.append(f"{len(modifs)} correction(s) enregistrée(s)")
            if a_supprimer:
                faits.append(f"{len(a_supprimer)} ligne(s) supprimée(s)")
            st.session_state[f"tblflash_{cle}"] = "✅ " + " et ".join(faits) + "."
            st.session_state[f"tblv_{cle}"] = version + 1      # remet le tableau à neuf
            res["enregistre"] = True
            st.rerun()
    if c2.button("↩️ Annuler", key=f"tblannule_{cle}", width="stretch"):
        st.session_state[f"tblv_{cle}"] = version + 1
        st.rerun()
    if aide:
        st.caption(aide)
    return res


def _affiche(v) -> str:
    if _vide(v):
        return "—"
    if isinstance(v, float):
        return f"{v:g}".replace(".", ",")
    return str(v)
