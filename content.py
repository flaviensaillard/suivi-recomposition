# -*- coding: utf-8 -*-
"""Données de contenu : programme 30 min, liste de courses, presets protéines, calculs."""

# ---------------------------------------------------------------- PROFIL / OBJECTIFS
HEIGHT_CM = 185
START_WEIGHT = 85.0          # mi-août 2026
TARGET_WEIGHT = 77.0         # 31 décembre 2026
TARGET_PROTEIN = 140         # g / jour (plancher 130)
TDEE = 2670

PHASES = [
    ("2026-09-29", "2026-10-11", "Bloc 0 — Remise à niveau",   (2300, 2400, 2400)),
    ("2026-10-12", "2026-12-06", "Bloc 1 — Déficit propre",    (2000, 2250, 2350)),
    ("2026-12-07", "2026-12-20", "Bloc 2 — Pause diététique",  (2400, 2500, 2500)),
    ("2026-12-21", "2027-03-31", "Bloc 3 — Derniers kilos",    (2000, 2250, 2350)),
]


def phase_for(d):
    for start, end, label, kcal in PHASES:
        if start <= d.isoformat() <= end:
            return label, kcal
    return PHASES[-1][2], PHASES[-1][3]


# ---------------------------------------------------------------- PROGRAMME 30 MIN
# Structure : 3 blocs de supersets, 3 tours, 60-75 s de repos entre les tours.
WARMUP_A = [
    "30 squats au poids du corps (rythme soutenu)",
    "20 jumping jacks ou montées de genoux",
    "10 cercles de bras dans chaque sens",
    "10 rotations de hanches + 10 chat-vache",
    "10 pompes lentes + 20 s de dead hang à la barre",
]
WARMUP_B = [
    "20 jumping jacks + 20 squats au poids du corps",
    "10 cercles de bras + 10 rotations d'épaules",
    "10 pompes lentes + 2 × 5 tractions faciles (ou descentes lentes)",
    "20 s de dead hang (préparation de la barre)",
]

# Chaque exercice : nom, cible en reps, options de variante (progression), options de lest
EXOS_A = [
    dict(bloc="Bloc 1 — Jambes + Poussée (superset)", repos=60, min=8,
         exos=[
             dict(nom="Squat bulgare", par_cote=True, cible="10-12 / jambe",
                  variantes=["N1 Assis-debout sur chaise", "N2 Split squat au sol",
                             "N3 Bulgare 2×5 kg", "N4 Bulgare + sac à dos 10 kg",
                             "N5 Bulgare tempo 3 s + sac 15 kg"],
                  lests=["Poids du corps", "2×5 kg", "Sac 5 kg", "Sac 10 kg", "Sac 15 kg"]),
             dict(nom="Pompes", par_cote=False, cible="8-12",
                  variantes=["N1 Mains sur canapé", "N2 Sur les genoux", "N3 Au sol mains sur livres",
                             "N4 Pieds surélevés 40 cm", "N5 Surélevées + sac", "N6 Archer"],
                  lests=["Poids du corps", "Sac 5 kg", "Sac 10 kg", "Sac 15 kg"]),
         ]),
    dict(bloc="Bloc 2 — Chaîne postérieure + Tirage (superset)", repos=60, min=8,
         exos=[
             dict(nom="Soulevé de terre roumain unilatéral", par_cote=True, cible="10-12 / jambe",
                  variantes=["N1 Hip thrust bilatéral au sol", "N2 SDT roumain bilatéral 5 kg",
                             "N3 Unilatéral 5 kg descente 3 s", "N4 Unilatéral + sac à dos"],
                  lests=["2×5 kg", "Sac 5 kg", "Sac 10 kg"]),
             dict(nom="Rowing inversé", par_cote=False, cible="8-12",
                  variantes=["N1 Rowing haltères 5 kg buste penché", "N2 Rowing inversé barre haute",
                             "N3 Corps horizontal talons au sol", "N4 Pieds surélevés", "N5 Une main / lesté"],
                  lests=["Poids du corps", "Sac 5 kg", "Sac 10 kg"]),
         ]),
    dict(bloc="Bloc 3 — Unilatéral + Anti-claquage + Gainage", repos=45, min=10,
         exos=[
             dict(nom="Fentes arrière", par_cote=True, cible="12 / jambe",
                  variantes=["N1 Fentes statiques", "N2 Fentes marchées 5 kg",
                             "N3 Fentes arrière 5 kg tempo 3 s", "N4 + sac à dos"],
                  lests=["Poids du corps", "2×5 kg", "Sac 5 kg", "Sac 10 kg"]),
             dict(nom="Nordic curl (ischios)", par_cote=False, cible="6-8",
                  variantes=["N1 Descente 5 s retenue par les bras", "N2 Descente 8 s",
                             "N3 Descente contrôlée sans les mains"],
                  lests=["Assisté bras", "Assisté partiel", "Libre"]),
             dict(nom="Mollets debout unilatéral", par_cote=True, cible="15-20 / jambe",
                  variantes=["N1 Talon dans le vide", "N2 + sac à dos"],
                  lests=["Poids du corps", "Sac 5 kg", "Sac 10 kg"]),
             dict(nom="Gainage (planche)", par_cote=False, cible="40-45 s",
                  variantes=["Planche avant", "Planche + sac à dos", "Planche bras tendus"],
                  lests=["Poids du corps", "Sac 5 kg", "Sac 10 kg"]),
         ]),
]

EXOS_B = [
    dict(bloc="Bloc 1 — Traction + Poussée verticale (superset)", repos=75, min=9,
         exos=[
             dict(nom="Tractions", par_cote=False, cible="4-10",
                  variantes=["N1 Dead hang 20 s + 5 descentes 5 s", "N2 Descentes lentes 8 s",
                             "N3 Assistées (élastique / pied sur chaise)", "N4 Complètes",
                             "N5 Complètes + sac à dos"],
                  lests=["Poids du corps", "Sac 5 kg", "Sac 10 kg", "Élastique"]),
             dict(nom="Pike push-up (épaules)", par_cote=False, cible="8-12",
                  variantes=["N1 Élévations latérales 5 kg", "N2 Développé assis 5 kg tempo 3 s",
                             "N3 Pike push-up pieds sur chaise", "N4 Pike pieds surélevés 40 cm"],
                  lests=["2×5 kg", "Poids du corps", "Sac 5 kg"]),
         ]),
    dict(bloc="Bloc 2 — Tirage horizontal + Épaules (superset)", repos=60, min=8,
         exos=[
             dict(nom="Rowing inversé (supination)", par_cote=False, cible="8-12",
                  variantes=["N1 Rowing haltère 5 kg", "N2 Barre haute incliné",
                             "N3 Corps horizontal", "N4 Pieds surélevés"],
                  lests=["Poids du corps", "Sac 5 kg", "Sac 10 kg"]),
             dict(nom="Face pull / rowing menton (élastique)", par_cote=False, cible="12-15",
                  variantes=["N1 Rowing menton haltères 5 kg", "N2 Face pull élastique",
                             "N3 Face pull élastique + pause 1 s"],
                  lests=["2×5 kg", "Élastique léger", "Élastique fort"]),
         ]),
    dict(bloc="Bloc 3 — Circuit gainage complet", repos=45, min=9,
         exos=[
             dict(nom="Planche latérale (gauche)", par_cote=False, cible="40 s",
                  variantes=["Sur les genoux", "Sur le pied", "Sur le pied + sac"],
                  lests=["Poids du corps", "Sac 5 kg"]),
             dict(nom="Planche latérale (droite)", par_cote=False, cible="40 s",
                  variantes=["Sur les genoux", "Sur le pied", "Sur le pied + sac"],
                  lests=["Poids du corps", "Sac 5 kg"]),
             dict(nom="Relevés de jambes suspendu à la barre", par_cote=False, cible="8-12",
                  variantes=["Genoux pliés", "Jambes semi-tendues", "Jambes tendues"],
                  lests=["Poids du corps"]),
             dict(nom="Hollow hold", par_cote=False, cible="30-40 s",
                  variantes=["Genoux pliés", "Jambes tendues", "Jambes tendues + bras au-dessus de la tête"],
                  lests=["Poids du corps"]),
         ]),
]

SESSIONS = {
    "A": dict(nom="SÉANCE A — Jambes & Poussée", jour="Lundi soir",
              blocs=EXOS_A, warmup=WARMUP_A, minutes=30,
              couleur="#0d9488"),
    "B": dict(nom="SÉANCE B — Haut du corps & Gainage", jour="Vendredi soir",
              blocs=EXOS_B, warmup=WARMUP_B, minutes=30,
              couleur="#1b4b6b"),
}

# ---------------------------------------------------------------- PROTÉINES : ajout rapide
PROTEIN_PRESETS = [
    ("Shaker whey (30 g)", 24),
    ("3 œufs durs", 19),
    ("4 œufs", 25),
    ("Gamelle déjeuner complète", 58),
    ("100 g edamames", 11),
    ("150 g lentilles/pois chiches cuits", 13),
    ("1 boîte de thon (140 g égoutté)", 28),
    ("200 g fromage blanc 0 %", 16),
    ("150 g skyr", 17),
    ("180 g poulet / dinde", 42),
    ("150 g poisson blanc", 30),
    ("40 g lait écrémé en poudre", 14),
    ("20 g amandes", 4),
    ("Repas au restaurant (estimation)", 35),
]

# ---------------------------------------------------------------- LISTE DE COURSES
# (rayon, produit, quantité, prix indicatif €, où le ranger, usage)
SHOPPING = [
    ("ÉPICERIE", "★ Lentilles sèches", "500 g", 1.50, "Placard (12 mois)", "Déjeuners — cuites le dimanche"),
    ("ÉPICERIE", "★ Pois chiches secs", "500 g", 1.50, "Placard (12 mois)", "Déjeuners + dîners sport"),
    ("ÉPICERIE", "★ Thon au naturel / sardines", "3 boîtes", 3.50, "Placard", "Déjeuners, dépannage"),
    ("ÉPICERIE", "★ Whey 1 kg (pot de 3 semaines)", "1 pot / 3 sem.", 9.30, "Placard", "30 g à 10 h 30 au bureau"),
    ("ÉPICERIE", "★ Lait écrémé en poudre 1 kg", "1 kg / 3 sem.", 2.30, "Placard", "Boost shakers / fromage blanc"),
    ("ÉPICERIE", "Flocons d'avoine", "1 kg / 3 sem.", 0.70, "Placard", "Avant les séances"),
    ("ÉPICERIE", "Amandes", "150-200 g", 3.00, "Placard", "Collation (comptée !)"),
    ("ÉPICERIE", "Chocolat noir 85 %", "1 plaquette / 2 sem.", 0.75, "Placard", "Rituel du soir"),
    ("CONGÉLATEUR", "★ Filets de poulet / dinde surgelés", "1 kg", 7.50, "Congélateur (portionné)", "Dîners — sachets de 160-180 g"),
    ("CONGÉLATEUR", "★ Poisson blanc surgelé", "500 g", 4.00, "Congélateur", "Dîners"),
    ("CONGÉLATEUR", "Edamames", "500 g", 3.00, "Congélateur", "Déjeuners (variété)"),
    ("CONGÉLATEUR", "Légumes surgelés (brocoli, haricots, épinards)", "1 kg", 2.50, "Congélateur", "Jours de rush"),
    ("FRIGO", "★ Œufs", "30 (2 boîtes de 15)", 6.50, "Frigo / placard", "3/jour au déjeuner + dîners"),
    ("FRIGO", "★ Fromage blanc 0 % (seau de 1 kg)", "1,5 kg", 4.20, "Frigo", "Collation 200 g + déjeuner 150 g"),
    ("FRIGO", "Skyr", "2 pots de 500 g", 4.60, "Frigo", "Déjeuner / dîner (variété)"),
    ("FRIGO", "Lait demi-écrémé", "1,5 L", 1.70, "Frigo", "Café, cuisine"),
    ("FRIGO", "Légumes frais (salade, tomates, courgettes, poivrons)", "2-3 kg", 6.00, "Frigo", "Déjeuners + dîners (famille)"),
    ("FRIGO", "Pommes", "1,5 kg", 3.00, "Frigo", "Collation (famille)"),
    ("FRIGO", "Citrons", "4-5", 1.50, "Frigo", "Rituel du matin"),
]

BATCH_COOKING = [
    ("20 min main + 30 min cuisson", "Cuire 500 g de lentilles + 500 g de pois chiches SECS (trempe la veille, une pincée de bicarbonate) = ~2,5 kg cuits, se gardent 4 jours au frigo."),
    ("10 min", "Cuire 15 œufs durs = déjeuners jusqu'au mercredi (5 jours au frigo, non écalés)."),
    ("10 min", "Portionner 1 kg de poulet surgelé en sachets de 160-180 g, retour au congélateur."),
    ("10 min", "Laver et couper les légumes, stocker en boîtes hermétiques."),
    ("10 min", "Assembler 5 gamelles : légumes + légumineuses + œufs + part de fromage blanc."),
]

# ---------------------------------------------------------------- CALCULS
import math


def navy_body_fat(waist_cm, neck_cm, height_cm=HEIGHT_CM):
    """Estimation du % de masse grasse — formule Marine (US Navy), hommes, mesures en cm."""
    try:
        waist_cm, neck_cm, height_cm = float(waist_cm), float(neck_cm), float(height_cm)
        if waist_cm <= neck_cm or neck_cm <= 0:
            return None
        bf = 495 / (1.0324 - 0.19077 * math.log10(waist_cm - neck_cm)
                    + 0.15456 * math.log10(height_cm)) - 450
        return round(max(3.0, min(60.0, bf)), 1)
    except Exception:
        return None


def bmi(weight_kg, height_cm=HEIGHT_CM):
    try:
        return round(float(weight_kg) / ((float(height_cm) / 100) ** 2), 1)
    except Exception:
        return None


def fat_mass_kg(weight_kg, bf_pct):
    try:
        return round(float(weight_kg) * float(bf_pct) / 100, 1)
    except Exception:
        return None


def lean_mass_kg(weight_kg, bf_pct):
    fm = fat_mass_kg(weight_kg, bf_pct)
    return None if fm is None else round(float(weight_kg) - fm, 1)
