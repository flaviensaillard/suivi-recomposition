# -*- coding: utf-8 -*-
"""Régressions d'intégrité des profils, macros et séances (SQLite jetable)."""
import datetime as dt
import os
import tempfile
import unittest

import pandas as pd

import ciqual as CQ
import menus as MN
import seances as SE
from db import LocalStore


class StoreIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="equilibre-integrite-")
        self.store = LocalStore(os.path.join(self.tmp.name, "test.db"))

    def tearDown(self):
        self.tmp.cleanup()

    def test_no_profile_is_seeded_automatically(self):
        self.assertIsNone(self.store.profile())

    def test_unknown_macros_are_null_not_zero(self):
        self.store.add_protein(dt.date(2026, 10, 9), "Saisie protéine seule", 24)
        row = self.store.protein_df().iloc[0]
        self.assertTrue(pd.isna(row["carbs_g"]))
        self.assertTrue(pd.isna(row["fat_g"]))

    def test_known_zero_macros_remain_zero(self):
        self.store.add_protein(dt.date(2026, 10, 9), "Aliment vérifié", 0,
                               carbs=0, fat=0)
        row = self.store.protein_df().iloc[0]
        self.assertEqual(int(row["carbs_g"]), 0)
        self.assertEqual(int(row["fat_g"]), 0)


class NutritionSourceTests(unittest.TestCase):
    def test_ciqual_limits_remain_unknown_not_exact_upper_bounds(self):
        self.assertIsNone(CQ._nombre_ciqual("< 0,5"))
        self.assertIsNone(CQ._nombre_ciqual("Traces"))
        self.assertEqual(CQ._nombre_ciqual("0,5"), 0.5)
        self.assertEqual(CQ._nombre_ciqual("0"), 0.0)

    def test_missing_unit_is_not_silently_assumed_to_be_grams(self):
        self.assertEqual(MN.quantite_en_grammes(125, "", {"unit": None}), 0.0)
        self.assertEqual(MN.quantite_en_grammes(2, "", {"unit": "kg"}), 2000.0)

    def test_unconvertible_recipe_quantity_marks_macros_incomplete(self):
        ingredient = {
            "name": "Aliment sans unité connue", "unit": None,
            "kcal_100g": 100, "proteines_100g": 10,
            "glucides_100g": 20, "lipides_100g": 5,
        }
        resultat = MN.calculer_recette(
            [{"ingredient_id": 1, "quantity": 125, "unit": ""}],
            {1: ingredient}, base_servings=1)
        self.assertEqual(resultat["poids_g"], 0.0)
        self.assertTrue(all(not resultat["complet"][c] for c in MN.CHAMPS_NUTR))
        self.assertTrue(resultat["lignes"][0]["quantite_non_convertie"])


class FakeStore:
    def __init__(self, daily=None):
        self.saved_workouts = []
        self.saved_sets = []
        self._daily = daily if daily is not None else pd.DataFrame(
            columns=["log_date", "weight_kg"])

    def save_workout(self, row):
        self.saved_workouts.append(dict(row))

    def save_sets(self, rows):
        self.saved_sets.extend(rows)

    def daily_df(self):
        return self._daily.copy()

    def profile(self):
        return None


class SessionIntegrityTests(unittest.TestCase):
    def test_incomplete_validation_does_not_write_a_workout(self):
        store = FakeStore()
        ok, message = SE.enregistrer(
            store, "A", dt.date(2026, 10, 9), None, 3, 6,
            "Un peu", "Aucune", "", 3, "", None, None)
        self.assertFalse(ok)
        self.assertIn("incomplètes", message)
        self.assertEqual(store.saved_workouts, [])

    def test_reported_pain_requires_a_zone_before_saving(self):
        store = FakeStore()
        ok, message = SE.enregistrer(
            store, "A", dt.date(2026, 10, 9), 30, 3, 6,
            "Un peu", "Douleur", "  ", 3, "", None, None)
        self.assertFalse(ok)
        self.assertIn("zone", message)
        self.assertEqual(store.saved_workouts, [])

    def test_plan_repetitions_are_not_written_as_executed_sets(self):
        store = FakeStore()
        plan = {"tours": 3, "delta_reps": 2, "repos": 60,
                "version_dure": False, "proposition_appliquee": True}
        lignes_prevues = [{"exercise": "Squat", "set_no": 1, "reps": 12}]
        ok, _ = SE.enregistrer(
            store, "A", dt.date(2026, 10, 9), 30, 3, 6,
            "Un peu", "Aucune", "", 3, "", plan, lignes_prevues)
        self.assertTrue(ok)
        self.assertEqual(len(store.saved_workouts), 1)
        self.assertEqual(store.saved_sets, [])
        self.assertNotIn("exercise", store.saved_workouts[0])

    def test_unknown_pain_is_not_a_successful_easy_session(self):
        inconnue = {"difficulte": 1, "rpe": 5, "douleur": None}
        sans_douleur = {"difficulte": 1, "rpe": 5, "douleur": "Aucune"}
        self.assertFalse(SE._facile(inconnue))
        self.assertTrue(SE._facile(sans_douleur))
        self.assertEqual(SE.analyse([inconnue])["delta_reps"], 0)
        self.assertEqual(SE.analyse([sans_douleur])["delta_reps"], 2)

    def test_rugby_estimate_omitted_without_a_real_weight(self):
        store = FakeStore()
        infos = SE.infos_seance_reelle(
            store, "C", 30,
            {"type_seance": "Entraînement", "duree_prevue": 90,
             "met": 7.5, "kcal_estimees": 999})
        self.assertNotIn("kcal_estimees", infos)

    def test_rugby_estimate_uses_actual_duration_not_planned_duration(self):
        today = dt.date(2026, 10, 9)
        store = FakeStore(pd.DataFrame([{"log_date": today, "weight_kg": 80.0}]))
        infos = SE.infos_seance_reelle(
            store, "C", 30,
            {"type_seance": "Entraînement", "duree_prevue": 90, "met": 7.5})
        self.assertEqual(infos["kcal_estimees"], SE.calories_rugby(80, 30, 7.5))
        self.assertEqual(infos["kcal_estimees"], 300)


if __name__ == "__main__":
    unittest.main()
