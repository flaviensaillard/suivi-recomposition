# -*- coding: utf-8 -*-
"""Vérifie que chaque page de l'application se rend sans erreur (sans navigateur)."""
import os
import sys
from streamlit.testing.v1 import AppTest

PAGES = ["dashboard", "pesee", "seance", "proteines", "cuisine", "mensurations", "courses", "reglages"]
ko = 0
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
print("\nRésultat :", "toutes les pages passent" if ko == 0 else f"{ko} page(s) en erreur")
sys.exit(1 if ko else 0)
