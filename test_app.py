# -*- coding: utf-8 -*-
"""Vérifie le rendu des pages Streamlit dans une SQLite jetable, hors dépôt."""
import os
import shutil
import sys
import tempfile

from streamlit.testing.v1 import AppTest

# Les tests ouvrent certaines pages qui créent/écrivent un store. Ne jamais les
# laisser toucher data/suivi.db ni une base Supabase configurée pour l'utilisateur.
_TEST_DIR = tempfile.mkdtemp(prefix="equilibre-test-")
os.environ["EQUILIBRE_SINGLE_USER_LOCAL"] = "1"
os.environ["EQUILIBRE_DB_PATH"] = os.path.join(_TEST_DIR, "suivi.db")

PAGES = ["dashboard", "pesee", "seance", "proteines", "cuisine", "planifier",
         "recettes", "ingredients", "mensurations", "reglages"]
ko = 0
try:
    for p in PAGES:
        os.environ["APP_TEST_PAGE"] = p
        try:
            at = AppTest.from_file("app.py", default_timeout=60)
            at.run()
            if at.exception:
                ko += 1
                print(f"❌ {p} : {at.exception[0].value}")
            else:
                n = len(at.markdown) + len(at.metric) + len(at.button)
                print(f"✅ {p} : rendu OK ({n} éléments)")
        except Exception as e:
            ko += 1
            print(f"❌ {p} : EXCEPTION {type(e).__name__}: {e}")
finally:
    os.environ.pop("APP_TEST_PAGE", None)
    os.environ.pop("EQUILIBRE_SINGLE_USER_LOCAL", None)
    os.environ.pop("EQUILIBRE_DB_PATH", None)
    shutil.rmtree(_TEST_DIR, ignore_errors=True)

print("\nRésultat :", "toutes les pages passent" if ko == 0 else f"{ko} page(s) en erreur")
sys.exit(1 if ko else 0)
