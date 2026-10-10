# -*- coding: utf-8 -*-
"""Base alimentaire Ciqual (Anses) — mise au format de l'application.

Source cible : Anses, Table Ciqual 2025, https://doi.org/10.57745/RDMHWY,
licence ouverte Etalab, valeurs de référence pour 100 g de partie comestible.
La table officielle annonce 3 484 aliments ; le CSV suivi dans ce dépôt contient
3 339 lignes et n'a pas été validé contre le classeur 2025 pendant cet audit.
Ne pas présenter le CSV embarqué comme un export complet de l'édition 2025 avant
réconciliation et attribution de version.

Deux usages :
  • `convertir_vers_csv(xlsx, csv)` : transforme le fichier Excel officiel en CSV léger
    (fait une fois, le CSV est ensuite embarqué dans l'application) ;
  • `charger_csv()` / `importer_dans_supabase(client, table, csv)` : alimente la table `foods`.
"""
from __future__ import annotations

import csv
import os
import unicodedata

DOSSIER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
CSV_DEFAUT = os.path.join(DOSSIER, "foods_ciqual.csv")

# Colonnes du CSV de l'application
CHAMPS = ["code", "nom", "groupe", "kcal", "proteines", "glucides", "lipides", "fibres", "sel"]


def _nombre_ciqual(v):
    """Convertit une valeur Ciqual numérique ; une borne « < x » reste inconnue.

    Le schéma de l'application ne stocke pas de borne supérieure. La convertir
    en x ferait passer une limite analytique pour une mesure exacte.
    """
    if v is None:
        return None
    texte = str(v).strip().replace(",", ".").replace(" ", "")
    if not texte or texte.lower() in ("-", "nan", "none", "null", "traces", "trace"):
        return None
    if texte.startswith("<"):
        return None
    try:
        nombre = float(texte)
    except ValueError:
        return None
    return round(nombre, 3) if nombre >= 0 else None


def _sans_accent(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", str(s or ""))
                   if unicodedata.category(c) != "Mn").lower()


def _trouver_colonne(colonnes, mots_obligatoires, mots_exclus=(), mots_preferes=()):
    """Retrouve une colonne de Ciqual malgré des intitulés multi-lignes et variables."""
    for col in colonnes:
        norme = _sans_accent(col).replace("\n", " ")
        norme = " ".join(norme.split())
        if all(m in norme for m in mots_obligatoires) and not any(e in norme for e in mots_exclus):
            return col
    return None


def convertir_vers_csv(xlsx: str, csv_sortie: str = CSV_DEFAUT) -> int:
    """Convertit le fichier Excel officiel Ciqual en CSV léger pour l'application."""
    import pandas as pd

    df = pd.read_excel(xlsx, sheet_name="composition nutritionnelle", dtype=str)
    cols = list(df.columns)

    # « alim_grp_code » / « alim_grp_nom_fr » contiennent aussi « alim » : on les exclut
    c_code = _trouver_colonne(cols, ["alim", "code"], mots_exclus=["grp"]) or \
        _trouver_colonne(cols, ["alim", "code"])
    c_nom = _trouver_colonne(cols, ["alim", "nom", "fr"], mots_exclus=["grp", "sci"]) or \
        _trouver_colonne(cols, ["alim", "nom"], mots_exclus=["grp", "sci"])
    c_grp = _trouver_colonne(cols, ["grp", "nom"], mots_exclus=["ssgrp", "ssss"])
    c_kcal = _trouver_colonne(cols, ["energie"], mots_exclus=["kj", "jones"])
    c_prot = _trouver_colonne(cols, ["proteines", "6.25"]) or \
        _trouver_colonne(cols, ["proteines"], mots_exclus=["jones"])
    c_gluc = _trouver_colonne(cols, ["glucides"], mots_exclus=["sucres"])
    c_lip = _trouver_colonne(cols, ["lipides"])
    c_fib = _trouver_colonne(cols, ["fibres"])
    c_sel = _trouver_colonne(cols, ["sel"])

    manquantes = [n for n, c in [("code", c_code), ("nom", c_nom), ("kcal", c_kcal),
                                 ("proteines", c_prot), ("glucides", c_gluc),
                                 ("lipides", c_lip)] if c is None]
    if manquantes:
        raise ValueError(f"Colonnes introuvables dans le fichier Ciqual : {manquantes}")

    os.makedirs(os.path.dirname(csv_sortie), exist_ok=True)
    n = 0
    with open(csv_sortie, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(CHAMPS)
        for _, r in df.iterrows():
            nom = str(r.get(c_nom) or "").strip()
            code = str(r.get(c_code) or "").strip()
            if not nom or not code or code.lower() == "nan":
                continue
            grp = str(r.get(c_grp) or "").strip()
            grp = "" if grp.lower() in ("nan", "none") else grp
            nom = str(r.get(c_nom) or "").strip()
            nom = nom if nom.lower() not in ("nan", "none") else ""
            ligne = [code, nom, grp,
                     _nombre_ciqual(r.get(c_kcal)), _nombre_ciqual(r.get(c_prot)),
                     _nombre_ciqual(r.get(c_gluc)), _nombre_ciqual(r.get(c_lip)),
                     _nombre_ciqual(r.get(c_fib)),
                     _nombre_ciqual(r.get(c_sel)) if c_sel else None]
            if ligne[3] is None:          # pas de calories → aliment inutilisable
                continue
            w.writerow(["" if v is None else v for v in ligne])
            n += 1
    return n


def charger_csv(chemin: str = CSV_DEFAUT) -> list:
    """Renvoie la liste des aliments depuis le CSV embarqué."""
    with open(chemin, encoding="utf-8", newline="") as f:
        lecteur = csv.DictReader(f, delimiter=";")
        sortie = []
        for r in lecteur:
            def num(k):
                v = (r.get(k) or "").strip()
                try:
                    return float(v)
                except ValueError:
                    return None
            sortie.append({
                "code": r["code"], "nom": r["nom"], "groupe": r.get("groupe") or "",
                "kcal": num("kcal"), "proteines": num("proteines"), "glucides": num("glucides"),
                "lipides": num("lipides"), "fibres": num("fibres"), "sel": num("sel"),
            })
    return sortie


def importer_dans_supabase(client, table: str, chemin: str = CSV_DEFAUT, progression=None):
    """Écrit la base alimentaire dans Supabase, par lots. Renvoie le nombre d'aliments importés."""
    aliments = charger_csv(chemin)
    total, lot = len(aliments), 400
    envoyes = 0
    for i in range(0, total, lot):
        paquet = [{
            "code": a["code"], "nom": a["nom"], "groupe": a["groupe"],
            "kcal_100g": a["kcal"], "proteines_100g": a["proteines"],
            "glucides_100g": a["glucides"], "lipides_100g": a["lipides"],
            "fibres_100g": a["fibres"], "sel_100g": a["sel"], "source": "Ciqual 2025",
        } for a in aliments[i:i + lot]]
        client.table(table).upsert(paquet, on_conflict="code").execute()
        envoyes += len(paquet)
        if progression:
            progression(envoyes, total)
    return envoyes


if __name__ == "__main__":
    import sys
    source = sys.argv[1] if len(sys.argv) > 1 else "/tmp/ciqual.xlsx"
    n = convertir_vers_csv(source)
    print(f"{n} aliments écrits dans {CSV_DEFAUT}")
