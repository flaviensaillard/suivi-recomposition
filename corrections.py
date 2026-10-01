# -*- coding: utf-8 -*-
"""Correction des saisies : traduire une case modifiée en enregistrement.

Chaque fonction reçoit l'identifiant de la ligne (la date, ou l'id de l'entrée)
et le dictionnaire {colonne affichée: nouvelle valeur} renvoyé par
`tableaux.tableau_editable`. Elle n'écrit **que** les cases corrigées : le reste
de la ligne n'est jamais touché.

C'est ce qui permet, par exemple, de corriger un tour de taille sans effacer la
note ou les photos de la même ligne.
"""
from __future__ import annotations

import pandas as pd

import content as C


VERSION = "1.0.8"        # vérifié au démarrage par app.py
def vide(v) -> bool:
    """Vrai si la case est vide (None, NaN…)."""
    try:
        return v is None or bool(pd.isna(v))
    except (TypeError, ValueError):
        return v is None


# ---------------------------------------------------------------------------
#  Journée de pesée (table daily_logs)
# ---------------------------------------------------------------------------
def _fr(iso) -> str:
    """« 2026-09-30 » → « 30/09/2026 » (les messages sont lus par un humain)."""
    t = str(iso)[:10].split("-")
    return f"{t[2]}/{t[1]}/{t[0]}" if len(t) == 3 else str(iso)


def _jour_occupe(store, date, table: str, colonne: str) -> bool:
    """Une ligne existe-t-elle déjà à cette date ? (pour ne JAMAIS écraser)"""
    try:
        if table == "daily_logs":
            df = store.daily_df()
        elif table == "measurements":
            df = store.meas_df()
        else:
            return False
        if df is None or df.empty or colonne not in df.columns:
            return False
        return bool((df[colonne].astype(str).str[:10] == str(date)[:10]).any())
    except Exception:
        return False        # en cas de doute on ne bloque pas : l'écriture reste possible


COLONNES_JOUR = {"Poids": "weight_kg", "% gras": "body_fat_pct",
                  "Masse grasse (kg)": "body_fat_kg", "Pas": "steps",
                 "Sommeil (h)": "sleep_h", "Activité": "activity", "Énergie": "energy"}


COLONNES_JOUR_SAUVEES = ("weight_kg", "body_fat_pct", "steps", "sleep_h",
                          "protein_g", "kcal", "activity", "energy", "notes")


def corriger_jour(store, jour, champs: dict) -> bool:
    """Corrige une journée : poids, masse grasse, pas, sommeil, activité, énergie.

    Trois choses particulières, demandées le 01/10 :
      • la **masse grasse se saisit en kilos** (la base garde le pourcentage) :
        on la convertit avec le poids de la journée ;
      • on peut **changer la date** d'une journée (erreur de jour) : la journée
        est recopiée sous la nouvelle date, puis l'ancienne est effacée ;
      • rien d'autre n'est touché : on n'écrit que les cases modifiées.
    """
    ligne = {}
    nouvelle_date = None
    for affiche, valeur in (champs or {}).items():
        if affiche == "Date":
            nouvelle_date = str(valeur)
            continue
        cle = COLONNES_JOUR.get(affiche)
        if cle is None or vide(valeur):
            continue
        ligne[cle] = int(round(float(valeur))) if cle in ("steps", "energy") else float(valeur)

    #  ── la journée telle qu'elle est rangée aujourd'hui (pour la conversion
    #     kg → % et pour déplacer une journée entière si la date change)
    actuelle = {}
    try:
        df = store.daily_df()
        if df is not None and not df.empty:
            trouve = df[df["log_date"].astype(str) == str(jour)]
            if not trouve.empty:
                actuelle = {k: v for k, v in trouve.iloc[0].to_dict().items()
                            if k in COLONNES_JOUR_SAUVEES}
    except Exception:
        actuelle = {}

    poids = float(ligne.get("weight_kg") or actuelle.get("weight_kg") or 0) or None
    if "body_fat_kg" in ligne:
        kg = float(ligne.pop("body_fat_kg"))
        if not poids:
            return ("il faut d'abord le poids de cette journée pour convertir les kilos de "
                    "masse grasse en pourcentage. Renseigne le poids, puis enregistre.")
        pct = C.masse_grasse_pct(poids, kg)
        if pct is None:
            return "la masse grasse saisie n'est pas un nombre valable."
        ligne["body_fat_pct"] = pct

    if nouvelle_date and nouvelle_date != str(jour) and not actuelle and not ligne:
        return True                    # rien à déplacer : la ligne n'existe plus

    if nouvelle_date and nouvelle_date != str(jour):
        #  ⚠️ GARDE-FOU : si une journée existe DÉJÀ à la date d'arrivée, on ne
        #  l'écrase pas — on s'arrête et on explique (sinon les données de cette
        #  journée-là seraient perdues en silence).
        if _jour_occupe(store, nouvelle_date, "daily_logs", "log_date"):
            return (f"la journée du {_fr(nouvelle_date)} existe déjà : **rien n'a été "
                    f"écrasé**. Si tu veux vraiment la remplacer : coche 🗑️ sur cette "
                    f"journée-là pour la supprimer d'abord, puis recommence.")
        #  on recopie TOUTE la journée sous la nouvelle date, puis on efface l'ancienne
        fusion = dict(actuelle)
        fusion.update(ligne)
        fusion["log_date"] = nouvelle_date
        store.save_daily(fusion)
        store.delete_daily(jour)
        return True

    if not ligne:
        return True
    ligne["log_date"] = str(jour)
    store.save_daily(ligne)
    return True


# ---------------------------------------------------------------------------
#  Mensurations (table measurements)
# ---------------------------------------------------------------------------
COLONNES_MENSURATION = {"Date": "meas_date", "Taille": "waist_cm", "Hanches": "hips_cm", "Poitrine": "chest_cm",
                        "Cou": "neck_cm", "Bras": "arm_cm", "Cuisse": "thigh_cm",
                        "Photos": "photos", "Notes": "notes"}


COLONNES_MENSURATION_SAUVEES = ("waist_cm", "hips_cm", "chest_cm", "arm_cm",
                                 "thigh_cm", "neck_cm", "photos", "notes")


def corriger_mensuration(store, jour, champs: dict) -> bool:
    """Corrige une ligne de mensurations (et permet de changer la date)."""
    ligne = {}
    nouvelle_date = None
    for affiche, valeur in (champs or {}).items():
        cle = COLONNES_MENSURATION.get(affiche)
        if cle is None:
            continue
        if cle == "meas_date":
            nouvelle_date = str(valeur)
            continue
        if cle == "photos":
            ligne[cle] = 1 if valeur else 0
        elif cle == "notes":
            ligne[cle] = "" if vide(valeur) else str(valeur)
        elif not vide(valeur):
            ligne[cle] = float(valeur)

    if nouvelle_date and nouvelle_date != str(jour):
        #  on recopie la ligne sous la nouvelle date, puis on efface l'ancienne
        actuelle = {}
        try:
            df = store.meas_df()
            if df is not None and not df.empty:
                trouve = df[df["meas_date"].astype(str) == str(jour)]
                if not trouve.empty:
                    actuelle = {k: v for k, v in trouve.iloc[0].to_dict().items()
                                if k in COLONNES_MENSURATION_SAUVEES}
        except Exception:
            actuelle = {}
        if not actuelle and not ligne:
            return True
        if _jour_occupe(store, nouvelle_date, "measurements", "meas_date"):
            return (f"une mensuration du {_fr(nouvelle_date)} existe déjà : **rien n'a été "
                    f"écrasé**. Supprime d'abord cette ligne-là (case 🗑️), puis recommence.")
        fusion = dict(actuelle)
        fusion.update(ligne)
        fusion["meas_date"] = nouvelle_date
        store.save_measurement(fusion)
        store.delete_measurement(jour)
        return True

    if not ligne:
        return True
    ligne["meas_date"] = str(jour)
    store.save_measurement(ligne)
    return True


# ---------------------------------------------------------------------------
#  Journal alimentaire (table protein_entries)
# ---------------------------------------------------------------------------
COLONNES_ENTREE = {"Date": "entry_date", "Repas": "item", "Protéines (g)": "protein_g",
                   "Glucides (g)": "carbs_g",
                   "Lipides (g)": "fat_g", "Quantité": "qty"}


def corriger_entree(store, entree, champs: dict) -> bool:
    """Corrige une entrée du journal du jour."""
    valeurs = {}
    for affiche, valeur in (champs or {}).items():
        cle = COLONNES_ENTREE.get(affiche)
        if cle is None or vide(valeur):
            continue
        if cle == "item":
            valeurs[cle] = str(valeur).strip()
        elif cle == "entry_date":
            valeurs[cle] = str(valeur)          # changer de jour = corriger un oubli
        elif cle == "qty":
            valeurs[cle] = float(valeur)
        else:
            valeurs[cle] = int(round(float(valeur)))
    if not valeurs:
        return True
    store.maj_protein(entree, **valeurs)
    return True
