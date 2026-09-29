# -*- coding: utf-8 -*-
"""Génère 6 semaines de données de démonstration dans la base locale (data/suivi.db).

Usage :  python seed_demo.py
But    : voir l'application remplie immédiatement, sans attendre 3 semaines de saisie.
"""
import datetime as dt
import random

from db import LocalStore

random.seed(7)
store = LocalStore()

start = dt.date(2026, 8, 15)
today = dt.date.today()

# --- poids : 85 kg -> 80 kg, avec du bruit réaliste
w = 85.0
weight_curve = {}
d = start
while d <= today:
    w -= random.uniform(0.06, 0.16) + (0.06 if d.weekday() in (1, 5) else 0)
    weight_curve[d] = round(w + random.uniform(-0.35, 0.35), 1)
    d += dt.timedelta(days=1)
# recalage pour être cohérent avec la réalité (80 kg aujourd'hui)
scale = (list(weight_curve.values())[-1] - 80.0)
for k in weight_curve:
    weight_curve[k] = round(weight_curve[k] - scale, 1)

bf = 21.5
d = start
while d <= today:
    dow = d.weekday()
    activity = {0: "Séance A", 4: "Séance B", 3: "Rugby", 5: "Marche"}.get(dow, "Repos")
    bf = max(17.4, bf - random.uniform(0.02, 0.09))
    store.save_daily(dict(
        log_date=d,
        weight_kg=weight_curve[d],
        body_fat_pct=round(bf + random.uniform(-0.5, 0.5), 1),
        steps=random.randint(6500, 13500),
        sleep_h=round(random.uniform(6.5, 8.5), 1),
        activity=activity,
        energy=random.randint(5, 9),
        notes="",
    ))
    d += dt.timedelta(days=1)

# --- mensurations hebdo (lundi)
waist = 92.5
d = start
while d <= today:
    if d.weekday() == 0:
        waist -= random.uniform(0.1, 0.5)
        store.save_measurement(dict(
            meas_date=d, waist_cm=round(waist, 1), hips_cm=round(100 - (92.5 - waist) * 0.6, 1),
            chest_cm=102.0, neck_cm=39.0, arm_cm=36.5, thigh_cm=58.0,
            photos=(d.day < 5), notes=""))
    d += dt.timedelta(days=1)

# --- séances + séries (les 4 dernières semaines)
exos_a = [("Squat bulgare", 12), ("Pompes", 11), ("Soulevé de terre roumain unilatéral", 11),
          ("Rowing inversé", 10), ("Fentes arrière", 13), ("Nordic curl (ischios)", 7),
          ("Mollets debout unilatéral", 17), ("Gainage (planche)", 45)]
exos_b = [("Tractions", 6), ("Pike push-up (épaules)", 10), ("Rowing inversé (supination)", 10),
          ("Face pull / rowing menton (élastique)", 14), ("Planche latérale (gauche)", 40),
          ("Planche latérale (droite)", 40), ("Relevés de jambes suspendu à la barre)", 9),
          ("Hollow hold", 35)]
d = today - dt.timedelta(days=28)
while d <= today:
    if d.weekday() in (0, 4):
        sess = "A" if d.weekday() == 0 else "B"
        store.save_workout(dict(session_date=d, session=sess, duration_min=30, rpe=8, notes=""))
        rows = []
        gain = (d - (today - dt.timedelta(days=28))).days // 7
        for ex, base in (exos_a if sess == "A" else exos_b):
            for i in (1, 2, 3):
                rows.append(dict(set_date=d, session=sess, exercise=ex, set_no=i,
                                 reps=max(1, base - (i - 1) * 2 + gain), load_kg=5.0,
                                 variant="N3", rpe=None))
        store.save_sets(rows)
    d += dt.timedelta(days=1)

# --- protéines des 21 derniers jours
for i in range(21):
    d = today - dt.timedelta(days=i)
    for item, g, n in [("Shaker whey (30 g)", 24, 1), ("Gamelle déjeuner complète", 58, 1),
                       ("200 g fromage blanc 0 %", 16, 1), ("3 œufs durs", 19, 1),
                       ("180 g poulet / dinde", 42, 1), ("150 g skyr", 17, random.choice([0, 1]))]:
        for _ in range(n):
            if random.random() > 0.1:
                store.add_protein(d, item, g)

# --- courses : semaine en cours, tout décoché
monday = today - dt.timedelta(days=today.weekday())
from content import SHOPPING
for rayon, prod, q, p, ou, usage in SHOPPING:
    store.set_shopping(prod, monday, random.random() < 0.35)

print("Données de démonstration créées dans data/suivi.db")
