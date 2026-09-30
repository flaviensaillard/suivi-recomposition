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


def vide(v) -> bool:
    """Vrai si la case est vide (None, NaN…)."""
    try:
        return v is None or bool(pd.isna(v))
    except (TypeError, ValueError):
        return v is None


# ---------------------------------------------------------------------------
#  Journée de pesée (table daily_logs)
# ---------------------------------------------------------------------------
COLONNES_JOUR = {"Poids": "weight_kg", "% gras": "body_fat_pct", "Pas": "steps",
                 "Sommeil (h)": "sleep_h", "Activité": "activity", "Énergie": "energy"}


def corriger_jour(store, jour, champs: dict) -> bool:
    """Corrige une journée : poids, masse grasse, pas, sommeil, activité, énergie."""
    ligne = {"log_date": str(jour)}
    for affiche, valeur in (champs or {}).items():
        cle = COLONNES_JOUR.get(affiche)
        if cle is None or vide(valeur):
            continue
        ligne[cle] = int(round(float(valeur))) if cle in ("steps", "energy") else float(valeur)
    if len(ligne) == 1:                       # rien à changer
        return True
    store.save_daily(ligne)
    return True


# ---------------------------------------------------------------------------
#  Mensurations (table measurements)
# ---------------------------------------------------------------------------
COLONNES_MENSURATION = {"Taille": "waist_cm", "Hanches": "hips_cm", "Poitrine": "chest_cm",
                        "Cou": "neck_cm", "Bras": "arm_cm", "Cuisse": "thigh_cm",
                        "Photos": "photos", "Notes": "notes"}


def corriger_mensuration(store, jour, champs: dict) -> bool:
    """Corrige une ligne de mensurations."""
    ligne = {"meas_date": str(jour)}
    for affiche, valeur in (champs or {}).items():
        cle = COLONNES_MENSURATION.get(affiche)
        if cle is None:
            continue
        if cle == "photos":
            ligne[cle] = 1 if valeur else 0
        elif cle == "notes":
            ligne[cle] = "" if vide(valeur) else str(valeur)
        elif not vide(valeur):
            ligne[cle] = float(valeur)
    if len(ligne) == 1:
        return True
    store.save_measurement(ligne)
    return True


# ---------------------------------------------------------------------------
#  Journal alimentaire (table protein_entries)
# ---------------------------------------------------------------------------
COLONNES_ENTREE = {"Repas": "item", "Protéines (g)": "protein_g", "Glucides (g)": "carbs_g",
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
        elif cle == "qty":
            valeurs[cle] = float(valeur)
        else:
            valeurs[cle] = int(round(float(valeur)))
    if not valeurs:
        return True
    store.maj_protein(entree, **valeurs)
    return True
