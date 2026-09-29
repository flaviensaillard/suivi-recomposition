# -*- coding: utf-8 -*-
"""MES SÉANCES — renforcement 30 min + rugby (version du 29/09)

CE QUI A CHANGÉ
  • Le VENDREDI ne sollicite plus les jambes : c'est le lendemain du rugby.
      → Séance A (lundi)  : BAS du corps + tronc   (jambes reposées depuis jeudi)
      → Séance B (vendredi): HAUT du corps + tronc (jambes laissées au repos)
  • Le RUGBY du jeudi est maintenant une séance à part entière : tu la valides
    comme les autres, avec durée, intensité, difficulté, ressenti, douleur…
  • Et cette validation compte : si le rugby de jeudi a été dur, la séance du
    vendredi s'allège automatiquement.

Les noms des mouvements sont ceux de Freeletics, pour que tu les retrouves en
deux secondes dans ton application.
"""
from __future__ import annotations

import datetime as dt
import json

import pandas as pd
import streamlit as st

MATERIEL = "2 haltères de 5 kg · 1 barre de traction · une chaise ou un banc · le sol"

# Le poids de corps sert seulement à estimer les calories du rugby.
POIDS_DEFAUT = 80.0

# ---------------------------------------------------------------------------
#  LES MOUVEMENTS — noms Freeletics + explications
# ---------------------------------------------------------------------------
EXOS: dict[str, dict] = {

    # ---- échauffement
    "Jumping Jacks": dict(
        cible="Tout le corps (échauffement)", objectif="Faire monter le cœur",
        comment=[
            "Debout, pieds joints, bras le long du corps.",
            "Saute en écartant les pieds (largeur des épaules) **et** en levant les bras "
            "au-dessus de la tête.",
            "Saute à nouveau pour revenir au départ. Tout s'enchaîne sans pause.",
        ],
        facile="Fais-le sans sauter : écarte une jambe puis l'autre en levant les bras.",
        dur="Rythme rapide et soutenu, deux sauts par seconde.",
        pourquoi="En 30 secondes, ton cœur s'accélère et tes épaules se lubrifient : "
                 "tu évites les blessures sur les pompes et les tractions.",
    ),
    "Arm Circles": dict(
        cible="Épaules", objectif="Échauffer les épaules",
        comment=[
            "Debout, pieds largeur des hanches, bras tendus sur les côtés.",
            "Fais des cercles de plus en plus grands : 15 dans un sens, 15 dans l'autre.",
            "Reste droit, épaules basses, respire calmement.",
        ],
        facile="Cercles plus petits, bras à moitié pliés.",
        dur="Cercles grands et rapides, puis change de sens sans t'arrêter.",
        pourquoi="Les épaules sont les articulations les plus sollicitées (tractions, développés, "
                 "pompes, rugby). Les échauffer, c'est éviter les tendinites.",
    ),
    "High Knees": dict(
        cible="Jambes + cardio", objectif="Réveiller les jambes",
        comment=[
            "Debout, pieds largeur des hanches.",
            "Cours sur place en montant **les genoux à hauteur de hanche**.",
            "Pose la pointe des pieds à chaque appui, reste droit (ne te penche pas).",
        ],
        facile="Monte les genoux moins haut, mais garde le rythme.",
        dur="Accélère la cadence en gardant les genoux hauts.",
        pourquoi="Prépare tes cuisses et tes hanches aux squats et aux fentes.",
    ),
    "Assisted Squats": dict(
        cible="Cuisses + fessiers", objectif="Apprendre le mouvement du squat",
        comment=[
            "Debout, pieds un peu plus larges que les hanches, pointes légèrement vers l'extérieur.",
            "Tiens le dossier d'une chaise devant toi et descends en **poussant tes fesses "
            "vers l'arrière**.",
            "Descends jusqu'à ce que tes cuisses soient parallèles au sol, puis remonte en "
            "poussant dans tes talons.",
        ],
        facile="Descends moins bas (un quart du chemin) et utilise la chaise sans lâcher.",
        dur="Lâche la chaise dès que tu descends bien droit (c'est le mouvement « Squats »).",
        pourquoi="C'est LE mouvement qui travaille les plus gros muscles de ton corps. "
                 "Plus tu en fais, plus tu brûles de calories au repos.",
    ),
    "Squats": dict(
        cible="Cuisses + fessiers", objectif="Le mouvement de base des jambes",
        comment=[
            "Debout, pieds largeur d'épaules, pointes légèrement ouvertes.",
            "Pousse les fesses vers l'arrière et descends, **genoux dans l'axe des pieds**, "
            "talons au sol.",
            "Remonte en serrant les fessiers. Le dos reste droit du début à la fin.",
        ],
        facile="Descends moins bas, ou reprends la version « Assisted Squats ».",
        dur="Descends en 3 secondes (tempo lent) : beaucoup plus dur, même sans poids.",
        pourquoi="Sans matériel, c'est l'exercice qui construit le plus de muscle utile, "
                 "et il protège tes genoux pour le rugby.",
    ),
    "Knee Pushups": dict(
        cible="Pectoraux + bras + gainage", objectif="Apprendre les pompes",
        comment=[
            "À quatre pattes, avance les mains (largeur des épaules), puis pose **tes genoux "
            "au sol**.",
            "Le corps reste droit comme une planche, des genoux jusqu'à la tête.",
            "Descends la poitrine vers le sol en pliant les coudes, puis remonte.",
        ],
        facile="Mets les mains sur une chaise ou le canapé : c'est plus facile que le sol.",
        dur="Fais les pompes classiques (voir « Pushups »).",
        pourquoi="C'est la version qui te permet de progresser sans t'écraser le nez au sol.",
    ),
    "Pushups": dict(
        cible="Pectoraux + bras + gainage", objectif="Le mouvement complet",
        comment=[
            "Mains au sol largeur des épaules, pieds joints, corps parfaitement droit.",
            "Serre les fessiers et le ventre : pas de dos qui se creuse.",
            "Descends jusqu'à 5 cm du sol, coudes vers l'arrière (pas sur les côtés), puis pousse.",
        ],
        facile="Repasse en « Knee Pushups » ou pose les mains sur une chaise.",
        dur="Descends en 3 secondes, ou remonte vite (pompes explosives).",
        pourquoi="Le meilleur exercice du haut du corps sans matériel : épaules, poitrine "
                 "et ventre travaillent ensemble.",
    ),
    "Crunches": dict(
        cible="Abdominaux", objectif="Renforcer le ventre",
        comment=[
            "Allongé sur le dos, genoux pliés, pieds au sol, mains le long de la tête.",
            "Décolle **les épaules** du sol en soufflant, le bas du dos reste collé au tapis.",
            "Redescends lentement. Le mouvement est court : c'est normal.",
        ],
        facile="Fais moins de répétitions, mais très lentement (2 s en montant).",
        dur="Passe aux « Situps » (tu montes plus haut) ou ajoute un haltère sur la poitrine.",
        pourquoi="Un ventre solide protège ton dos quand tu portes quelque chose — "
                 "et c'est essentiel pour le rugby.",
    ),
    "Situps": dict(
        cible="Abdominaux", objectif="Renforcer le ventre (niveau supérieur)",
        comment=[
            "Allongé sur le dos, genoux pliés, pieds calés sous un meuble (ou tenus).",
            "Monte le buste jusqu'à venir **toucher tes genoux**.",
            "Redescends en contrôlant, sans te laisser tomber.",
        ],
        facile="Repasse aux « Crunches ».",
        dur="Ajoute un haltère de 5 kg sur ta poitrine (version Freeletics « Weighted Crunch »).",
        pourquoi="Il travaille tout le ventre, y compris sous les côtes.",
    ),
    "Weighted Crunch": dict(
        cible="Abdominaux", objectif="Abdos avec charge",
        comment=[
            "Allongé sur le dos, genoux pliés, **un haltère de 5 kg tenu sur la poitrine**.",
            "Décolle les épaules en soufflant, bras tendus au-dessus de toi si tu peux.",
            "Redescends lentement, sans poser complètement la tête.",
        ],
        facile="Pose l'haltère et fais des « Crunches ».",
        dur="Tends les bras au-dessus de la tête : le bras de levier augmente, c'est plus dur.",
        pourquoi="Avec seulement 5 kg, la charge est petite — mais le gainage devient bien "
                 "plus exigeant.",
    ),

    # ---- bas du corps (séance A)
    "Dumbbell Goblet Squat": dict(
        cible="Cuisses + fessiers", objectif="Squat chargé (le meilleur exercice à domicile)",
        comment=[
            "Tiens **un haltère à deux mains devant ta poitrine**, comme un calice "
            "(coudes serrés).",
            "Pieds un peu plus larges que les hanches, pointes légèrement ouvertes.",
            "Descends entre tes jambes en gardant le buste droit, puis remonte en poussant "
            "dans les talons.",
        ],
        facile="Prends un seul haltère plus léger, ou fais des « Assisted Squats » à vide.",
        dur="Descends en 3 secondes et marque 1 seconde en bas.",
        pourquoi="C'est l'exercice le plus rentable pour tes jambes à la maison : il muscle "
                 "les cuisses et les fessiers sans tirer sur ton dos.",
    ),
    "Double Dumbbell Lunges": dict(
        cible="Cuisses + fessiers + équilibre", objectif="Jambes, une par une",
        comment=[
            "Un haltère dans chaque main, bras le long du corps.",
            "Fais un grand pas en avant et descends jusqu'à ce que **les deux genoux forment "
            "un angle droit**.",
            "Pousse dans le talon de devant pour revenir debout, puis change de jambe.",
        ],
        facile="Sans haltères, ou garde une main sur un mur ou une chaise pour l'équilibre.",
        dur="Fais 2 pas en avant, 2 en arrière, sans t'arrêter (fentes marchées).",
        pourquoi="Chaque jambe travaille toute seule : parfait pour corriger les déséquilibres "
                 "et muscler les fessiers.",
    ),
    "Single-Leg Deadlift": dict(
        cible="Arrière des cuisses + fessiers + équilibre", objectif="Bas du corps et stabilité",
        comment=[
            "Debout sur une jambe, un haltère dans la main opposée.",
            "Penche-toi vers l'avant en tendant l'autre jambe derrière toi : **ton dos reste "
            "droit**.",
            "Descends jusqu'à sentir l'arrière de ta cuisse tirer, puis remonte en serrant "
            "le fessier.",
        ],
        facile="Sans haltère, et pose la pointe du pied arrière au sol pour l'équilibre.",
        dur="Descends en 3 secondes et tiens 1 seconde en bas.",
        pourquoi="Il muscle l'arrière des cuisses (souvent oublié) et travaille ton équilibre : "
                 "utile pour éviter les blessures.",
    ),
    "Hanging Knee Raises": dict(
        cible="Ventre (abdos) + prise", objectif="Abdos suspendu à la barre",
        comment=[
            "Suspendu à la barre, bras tendus, épaules serrées.",
            "Monte **les genoux vers la poitrine** en enroulant le bas du dos.",
            "Redescends lentement, sans balancer.",
        ],
        facile="Monte les genoux moins haut, ou fais des « Crunches » au sol.",
        dur="Jambes tendues (version Freeletics « Hanging Leg Raise »).",
        pourquoi="Suspendu, le ventre travaille beaucoup plus fort qu'au sol — et tu améliores "
                 "aussi ta prise pour les tractions.",
    ),

    # ---- haut du corps (séance B)
    "Dumbbell Bent Row": dict(
        cible="Dos + biceps", objectif="Renforcer le dos (posture)",
        comment=[
            "Un genou et une main posés sur une chaise, l'autre pied au sol, dos bien plat.",
            "L'autre main tient l'haltère, bras tendu vers le sol.",
            "Tire l'haltère **vers ta hanche** en serrant le coude le long du corps, puis "
            "redescends.",
        ],
        facile="Sans haltère : tire ton poing vers la hanche, c'est le geste à apprendre.",
        dur="Marque 1 seconde en haut, redescends en 3 secondes.",
        pourquoi="Il équilibre les pompes : il tire au lieu de pousser. C'est ce qui redresse "
                 "les épaules et protège ton dos — précieux quand on dessine toute la journée.",
    ),
    "Jumping Pullups": dict(
        cible="Dos + bras (traction)", objectif="Apprendre la traction",
        comment=[
            "Attrape la barre, les mains un peu plus larges que les épaules.",
            "Saute légèrement pour t'aider, en tirant avec les bras.",
            "**Redescends lentement** (2-3 secondes) : c'est là que le muscle travaille.",
        ],
        facile="Saute plus fort et descends lentement. Ou pose un tabouret pour limiter la descente.",
        dur="Descends sans sauter (traction complète « Pullups ») dès que tu en fais une propre.",
        pourquoi="C'est LE test qui montre que tu ne perds pas de muscle. S'il progresse ou se "
                 "maintient, ton programme fonctionne.",
    ),
    "Pullups": dict(
        cible="Dos + bras (traction)", objectif="La traction complète",
        comment=[
            "Suspendu à la barre, bras tendus, épaules actives.",
            "Tire les coudes vers le bas et vers l'arrière pour amener ton menton au-dessus "
            "de la barre.",
            "Redescends jusqu'à bras tendus, sans te laisser tomber.",
        ],
        facile="Repasse en « Jumping Pullups » ou pose un pied sur un tabouret.",
        dur="Ajoute 2 secondes de pause en haut, ou serre un objet entre tes chevilles.",
        pourquoi="Le meilleur exercice de dos qui existe. Même 1 ou 2 répétitions produisent "
                 "des résultats.",
    ),
    "Dumbbell Shoulder Press": dict(
        cible="Épaules + bras", objectif="Épaules solides",
        comment=[
            "Debout ou assis, un haltère dans chaque main, **à hauteur d'épaule**, paumes "
            "vers l'avant.",
            "Pousse les haltères au-dessus de la tête sans cambrer le dos.",
            "Redescends lentement jusqu'aux épaules.",
        ],
        facile="Assis, dos appuyé au mur, ou un haltère à la fois.",
        dur="Redescends en 3 secondes, ou ne t'arrête jamais en bas.",
        pourquoi="Des épaules solides évitent les blessures au rugby et améliorent ta posture.",
    ),
    "Dumbbell Biceps Curl": dict(
        cible="Bras (biceps)", objectif="Bras plus forts",
        comment=[
            "Debout, un haltère dans chaque main, bras le long du corps, paumes vers l'avant.",
            "Monte les haltères en pliant les coudes, **sans bouger les épaules**.",
            "Redescends lentement, bras presque tendus.",
        ],
        facile="Un bras à la fois, ou appuie le coude contre ton corps.",
        dur="Redescends en 3 secondes et ne balance jamais le corps.",
        pourquoi="Avec 5 kg, c'est un exercice de finition : il renforce les bras pour les "
                 "tractions.",
    ),
}

# ---------------------------------------------------------------------------
#  LES ÉTIREMENTS — à faire à la fin, 4 minutes, jamais à froid
# ---------------------------------------------------------------------------
ETIREMENTS: dict[str, list[dict]] = {
    "A": [   # après la séance des jambes et du ventre
        dict(nom="Étirement des quadriceps", duree="30 s par jambe",
             comment=["Debout, une main sur un mur pour l'équilibre.",
                      "Attrape ta cheville derrière toi et ramène le talon vers ta fesse.",
                      "Garde les genoux serrés et avance légèrement le bassin. Change de jambe."],
             pourquoi="Détend les cuisses, très sollicitées par les squats et les fentes."),
        dict(nom="Étirement de l'arrière des cuisses", duree="30 s par jambe",
             comment=["Assis au sol, une jambe tendue devant toi, l'autre pliée sur le côté.",
                      "Penche doucement le buste vers le pied de la jambe tendue, **dos droit**.",
                      "Tu dois sentir l'arrière de la cuisse tirer, sans douleur. Change de jambe."],
             pourquoi="Ton exercice « Single-Leg Deadlift » cible exactement cette zone."),
        dict(nom="Étirement des fessiers", duree="30 s par côté",
             comment=["Allongé sur le dos, genoux pliés.",
                      "Croise ta cheville sur le genou opposé, puis attrape ta cuisse derrière.",
                      "Tire doucement vers toi, en gardant la tête au sol. Change de côté."],
             pourquoi="Les fessiers travaillent dans tous tes squats et tes fentes."),
        dict(nom="Étirement des mollets", duree="30 s par jambe",
             comment=["Mains au mur, une jambe tendue loin derrière toi, talon au sol.",
                      "Pousse doucement le bassin vers l'avant, sans décoller le talon.",
                      "Change de jambe."],
             pourquoi="Prépare tes mollets aux appuis du rugby — et évite la tendinite d'Achille."),
        dict(nom="Posture de l'enfant", duree="40 s",
             comment=["À genoux, assis sur tes talons, bras tendus devant toi.",
                      "Pose le front au sol et respire profondément par le nez.",
                      "Laisse le bas du dos s'allonger : c'est l'étirement qui te fera le plus de bien "
                      "après une journée assis à dessiner."],
             pourquoi="Détend le bas du dos et les lombaires, mis à contribution tout au long de la séance."),
    ],
    "B": [   # après la séance du haut du corps
        dict(nom="Étirement des pectoraux au mur", duree="30 s par côté",
             comment=["Place ton avant-bras contre un mur, à hauteur d'épaule, coude à 90°.",
                      "Tourne doucement le buste du côté opposé, jusqu'à sentir la poitrine s'ouvrir.",
                      "Change de côté."],
             pourquoi="Il ouvre la poitrine, très sollicitée par les pompes — et corrige la posture "
                      "penchée devant l'écran."),
        dict(nom="Étirement des dorsaux, suspendu à la barre", duree="20 s, deux fois",
             comment=["Attrape ta barre de traction, les deux mains.",
                      "Laisse tout ton poids tirer, épaules relâchées vers le haut.",
                      "Respire calmement. Descends, repose-toi 10 s, puis recommence."],
             pourquoi="Le meilleur étirement pour ton dos après les tirages et les tractions — "
                      "et tu as déjà la barre."),
        dict(nom="Étirement des épaules", duree="30 s par bras",
             comment=["Ramène un bras tendu en travers de ta poitrine.",
                      "Plaque-le contre toi avec l'autre bras, à hauteur du coude.",
                      "Relâche l'épaule, ne monte pas la tension. Change de bras."],
             pourquoi="Détend l'articulation la plus sollicitée le vendredi (développés, pompes, tractions)."),
        dict(nom="Étirement des triceps", duree="30 s par bras",
             comment=["Lève un bras, plie le coude et pose la main derrière ta nuque.",
                      "Avec l'autre main, tire doucement le coude vers le haut.",
                      "Garde le dos droit. Change de bras."],
             pourquoi="Les triceps travaillent à chaque pompe et chaque développé."),
        dict(nom="Étirement de la nuque et du haut du dos", duree="30 s",
             comment=["Mains croisées derrière la tête, coudes vers l'avant.",
                      "Laisse tomber le menton vers ta poitrine et monte doucement le haut du dos.",
                      "Respire profondément, sans tirer sur la nuque."],
             pourquoi="Relâche les trapèzes, souvent tendus quand on dessine toute la journée."),
        dict(nom="Chat-vache (mobilité du dos)", duree="30 s",
             comment=["À quatre pattes, mains sous les épaules, genoux sous les hanches.",
                      "Arrondis le dos en soufflant, puis creuse-le lentement en inspirant.",
                      "Fais 6 à 8 allers-retours tranquillement."],
             pourquoi="Il remet la colonne en mouvement : parfait après une séance de tirage."),
    ],
}


# Quand une séance est réussie 4 fois de suite, on passe au mouvement au-dessus.
UPGRADES = {
    "Knee Pushups": "Pushups",
    "Assisted Squats": "Squats",
    "Jumping Pullups": "Pullups",
    "Crunches": "Situps",
}

# ---------------------------------------------------------------------------
#  LES DEUX SÉANCES DE RENFORCEMENT
# ---------------------------------------------------------------------------
SEANCES: dict[str, dict] = {
    "A": dict(
        nom="Lundi", jour="Lundi", emoji="📅",
        sous_titre="Bas du corps + tronc (jambes, fessiers, ventre)",
        note="Tes jambes ont 4 jours de repos derrière elles depuis le rugby : c'est le bon "
             "moment pour les charger.",
        # Échauffement SPÉCIFIQUE : on prépare exactement ce qu'on va travailler
        echauffement=[
            dict(nom="Jumping Jacks", reps=30, but="fait monter le cœur et la température"),
            dict(nom="High Knees", reps=20, but="réveille les jambes et les hanches"),
            dict(nom="Assisted Squats", reps=12, but="ouvre les hanches pour les squats chargés"),
            dict(nom="Knee Pushups", reps=8, but="prépare les épaules et le gainage"),
        ],
        blocs=[
            dict(num=1, repos=75, exos=[
                dict(nom="Dumbbell Goblet Squat", reps=12, par_cote=False),
                dict(nom="Crunches", reps=15, par_cote=False)]),
            dict(num=2, repos=75, exos=[
                dict(nom="Double Dumbbell Lunges", reps=10, par_cote=True),
                dict(nom="Weighted Crunch", reps=12, par_cote=False)]),
            dict(num=3, repos=75, exos=[
                dict(nom="Single-Leg Deadlift", reps=10, par_cote=True),
                dict(nom="Hanging Knee Raises", reps=8, par_cote=False)]),
        ],
    ),
    "B": dict(
        nom="Vendredi", jour="Vendredi", emoji="📅",
        sous_titre="Haut du corps + tronc — JAMBES AU REPOS (lendemain de rugby)",
        note="Rien pour les jambes aujourd'hui : elles ont couru hier au rugby. On travaille "
             "le dos, la poitrine, les épaules et le ventre.",
        # Échauffement SPÉCIFIQUE : épaules et dos, car c'est ce qu'on utilise aujourd'hui
        echauffement=[
            dict(nom="Jumping Jacks", reps=30, but="fait monter le cœur et la température"),
            dict(nom="Arm Circles", reps=15, but="échauffe les épaules (tractions, développés)"),
            dict(nom="Knee Pushups", reps=8, but="prépare la poitrine et le gainage"),
            dict(nom="Jumping Pullups", reps=3, but="réveille le dos et la prise"),
            dict(nom="Crunches", reps=10, but="active le ventre"),
        ],
        blocs=[
            dict(num=1, repos=75, exos=[
                dict(nom="Dumbbell Bent Row", reps=10, par_cote=True),
                dict(nom="Knee Pushups", reps=8, par_cote=False)]),
            dict(num=2, repos=75, exos=[
                dict(nom="Dumbbell Shoulder Press", reps=10, par_cote=False),
                dict(nom="Crunches", reps=15, par_cote=False)]),
            dict(num=3, repos=75, exos=[
                dict(nom="Jumping Pullups", reps=5, par_cote=False),
                dict(nom="Dumbbell Biceps Curl", reps=12, par_cote=False)]),
        ],
    ),
}

TOURS = 3
JOURS_SEMAINE = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]

# Le rugby est une séance à part entière : il porte la lettre « C » dans ta base.
RUGBY = dict(
    code="C", nom="Rugby", emoji="🏉", jour="Jeudi",
    types=[("Touch / jeu réduit", 7.0), ("Entraînement", 7.5), ("Match", 8.3)],
)

# Ce qui est prévu les autres jours.
AUTRES_JOURS = {
    "Mardi": "🎵 Répétition de musique — jour de repos, on ne s'entraîne pas.",
    "Mercredi": "😌 Repos. Une marche tranquille si tu as le temps.",
    "Jeudi": "🏉 Rugby — valide ta séance dans l'onglet « 🏉 Rugby ».",
    "Samedi": "🛒 Courses + marche. Repos sportif.",
    "Dimanche": "🚶 Marche tranquille si tu peux, sinon repos.",
}


def _nombre(v, defaut=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return defaut


def _date_txt(d):
    if isinstance(d, dt.date):
        return d.strftime("%d/%m")
    return str(d or "")


def _facile(h: dict) -> bool:
    douleur = (h.get("douleur") or "").strip().lower()
    return (_nombre(h.get("difficulte"), 3) <= 3 and _nombre(h.get("rpe"), 8) <= 8
            and douleur in ("", "aucune", "aucun", "non", "ras"))


# ---------------------------------------------------------------------------
#  ADAPTATION AUTOMATIQUE
# ---------------------------------------------------------------------------
def analyse(historique: list[dict], sommeil_nuit: float | None = None,
            rugby_recent: dict | None = None) -> dict:
    """Décide ce qu'on change pour la prochaine séance — et POURQUOI.

    historique   : tes dernières séances de CETTE séance (la plus récente d'abord)
    sommeil_nuit : heures de sommeil notées pour la nuit précédente (facultatif)
    rugby_recent : ta dernière séance de rugby (facultatif)
    """
    messages: list[str] = []
    delta, repos_delta, tours, version_dure = 0, 0, TOURS, False

    reussies = 0
    for h in historique:
        if _facile(h):
            reussies += 1
        else:
            break

    if historique:
        dernier = historique[0]
        d = _nombre(dernier.get("difficulte"), 3)
        r = _nombre(dernier.get("rpe"), 8)
        quand = _date_txt(dernier.get("date"))

        if d <= 2 and r <= 6:
            delta, repos_delta = +2, -15
            messages.append(f"Ta dernière fois (**{quand}**) était notée « facile » ({d:.0f}/5) "
                            f"avec un ressenti léger ({r:.0f}/10) : **+2 répétitions** et "
                            f"**repos raccourci de 15 s**.")
        elif d >= 4 or r >= 9:
            delta, repos_delta = -2, +15
            messages.append(f"Ta dernière fois (**{quand}**) a été dure ({d:.0f}/5, ressenti "
                            f"{r:.0f}/10) : **-2 répétitions** et **+15 s de repos**. "
                            f"On consolide avant d'ajouter.")
        else:
            messages.append(f"Ta dernière fois (**{quand}**) était bien dosée ({d:.0f}/5, "
                            f"ressenti {r:.0f}/10) : on **garde la même chose** pour l'ancrer.")

        if (dernier.get("douleur") or "").strip().lower() not in ("", "aucune", "aucun", "non", "ras"):
            zone = dernier.get("zone_douleur") or "signalée"
            delta = min(delta, -2)
            messages.append(f"⚠️ Tu avais signalé une douleur (**{zone}**) : répétitions réduites "
                            f"et on évite de forcer sur la zone. Si ça dure plus d'une semaine, "
                            f"parle-en à un professionnel de santé.")
        if (dernier.get("pu_plus") or "").strip().lower().startswith("non"):
            if delta > 0:
                delta = 0
                messages.append("Tu avais précisé que tu ne pouvais pas faire plus : on ne monte "
                                "pas encore, même si la séance semblait facile.")

        if reussies >= 4:
            version_dure = True
            messages.append(f"**{reussies} séances réussies d'affilée** : tu peux passer aux "
                            f"versions « dures » (Pushups au lieu de Knee Pushups, Squats au lieu "
                            f"d'Assisted Squats…). Le détail est dans chaque exercice.")
    else:
        messages.append("**Première séance** : on part sur des répétitions prudentes. "
                        "Note bien ta difficulté à la fin : c'est ce qui règle la suite.")

    # ---- le rugby de la veille compte aussi
    if rugby_recent:
        quand = _date_txt(rugby_recent.get("date"))
        d = _nombre(rugby_recent.get("difficulte"), 3)
        r = _nombre(rugby_recent.get("rpe"), 7)
        try:
            jours = (dt.date.today() - rugby_recent["date"]).days
        except Exception:
            jours = None
        if d >= 4 or r >= 9:
            delta = min(delta, -2)
            messages.append(f"🏉 Ton rugby ({quand}) a été costaud ({d:.0f}/5, ressenti {r:.0f}/10) : "
                            f"**-2 répétitions** pour digérer la fatigue.")
        elif jours is not None and jours <= 2:
            messages.append(f"🏉 Rugby il y a {jours} jour(s) ({quand}, {d:.0f}/5) : on garde la "
                            f"séance telle quelle, tes jambes ne sont pas sollicitées aujourd'hui.")
        if (rugby_recent.get("douleur") or "").strip().lower() not in ("", "aucune", "aucun", "non", "ras"):
            delta = min(delta, -2)
            messages.append(f"⚠️ Douleur signalée au rugby "
                            f"(**{rugby_recent.get('zone_douleur') or 'zone non précisée'}**) : "
                            f"on allège aujourd'hui.")

    # ---- le sommeil compte : le muscle se construit la nuit
    if sommeil_nuit is not None and sommeil_nuit > 0:
        if sommeil_nuit < 6:
            tours = TOURS - 1
            messages.append(f"😴 Seulement **{sommeil_nuit:.1f} h de sommeil** notées : on passe à "
                            f"**{tours} tours au lieu de {TOURS}**. Une séance courte vaut mieux "
                            f"qu'une séance sautée — et ça ne casse pas ta progression.")
        elif sommeil_nuit >= 7.5:
            messages.append(f"😴 **{sommeil_nuit:.1f} h de sommeil** : ton corps est prêt, "
                            f"tu peux y aller franchement.")

    return dict(delta_reps=delta, repos=max(45, min(120, 75 + repos_delta)), tours=tours,
                version_dure=version_dure, messages=messages)


def appliquer(seance: dict, plan: dict) -> dict:
    """Le tableau de la séance, ajusté par les règles ci-dessus."""
    lignes = []
    for bloc in seance["blocs"]:
        for i, ex in enumerate(bloc["exos"]):
            nom = ex["nom"]
            if plan["version_dure"] and nom in UPGRADES:
                nom = UPGRADES[nom]
            base = ex["reps"] or 0
            lignes.append(dict(
                bloc=bloc["num"], tour=("①" if i == 0 else "②"), nom=nom, base=base,
                reps=max(4, base + plan["delta_reps"]) if base else 0,
                par_cote=ex["par_cote"],
            ))
    return dict(lignes=lignes, tours=plan["tours"], repos_apres_tour=plan["repos"])


def texte_reps(ligne: dict) -> str:
    t = f"{ligne['reps']} répétitions"
    return t + (" / côté" if ligne["par_cote"] else "")


# ---------------------------------------------------------------------------
#  LECTURE / ÉCRITURE
# ---------------------------------------------------------------------------
def _depuis_notes(notes: str) -> dict:
    """Relit les infos quand les colonnes détaillées n'existent pas encore."""
    if not notes or "[SEANCE]" not in notes:
        return {}
    try:
        return json.loads(notes.split("[SEANCE]", 1)[1].strip())
    except Exception:
        return {}


def lire_historique(store, session: str, limite: int = 8) -> list[dict]:
    """Tes dernières séances validées pour cette séance-là, la plus récente d'abord."""
    try:
        df = store.workouts_df()
    except Exception:
        return []
    if df is None or df.empty:
        return []
    df = df[df["session"].astype(str).str.upper() == session.upper()]
    if df.empty:
        return []
    df = df.sort_values("session_date", ascending=False).head(limite)
    out = []
    for _, r in df.iterrows():
        extra = _depuis_notes(r.get("notes"))
        out.append(dict(
            date=r.get("session_date"),
            difficulte=r.get("difficulte", extra.get("difficulte")),
            rpe=r.get("rpe", extra.get("rpe")),
            douleur=r.get("douleur", extra.get("douleur", "Aucune")),
            zone_douleur=r.get("zone_douleur", extra.get("zone_douleur", "")),
            pu_plus=r.get("pu_plus", extra.get("pu_plus")),
            duree=r.get("duration_min"),
            notes=(r.get("notes") or "").split("[SEANCE]")[0].strip(),
        ))
    return out


def rugby_recent(store, jours: int = 3) -> dict | None:
    """Le rugby le plus récent, s'il date d'au plus `jours` jours."""
    for h in lire_historique(store, RUGBY["code"], limite=3):
        d = h.get("date")
        if isinstance(d, dt.date) and (dt.date.today() - d).days <= jours:
            return h
    return None


def enregistrer(store, session: str, jour: dt.date, duree: int, difficulte: int, rpe: int,
                pu_plus: str, douleur: str, zone: str, energie: int, notes: str,
                plan: dict | None, lignes: list[dict] | None, infos: dict | None = None
                ) -> tuple[bool, str]:
    """Enregistre une séance (renforcement ou rugby) + ses séries. Renvoie (ok, message)."""
    extra = dict(difficulte=int(difficulte), rpe=int(rpe), pu_plus=pu_plus, douleur=douleur,
                 zone_douleur=zone, energie_avant=int(energie),
                 tours=(int(plan["tours"]) if plan else None))
    if infos:
        extra.update(infos)
    base = dict(session_date=str(jour), session=session, duration_min=int(duree),
                rpe=int(rpe), notes=(notes or "").strip())

    def _essai(charge):
        try:
            store.save_workout(charge)
            return True, ""
        except Exception as e:
            return False, f"{type(e).__name__} — {e}"

    ok, err = _essai({**base, **extra})                    # 1er essai : colonnes détaillées
    if not ok:
        base["notes"] = (base["notes"] + "\n[SEANCE]"
                         + json.dumps(extra, ensure_ascii=False)).strip()
        ok, err = _essai(base)                             # 2e essai : tout dans les notes
    if not ok:
        conseil = ""
        if "check" in err.lower() or "23514" in err:
            conseil = (" → Ta base n'autorise pas encore le rugby comme type de séance : "
                       "lance le script **6_seance_rugby.sql** dans Supabase (10 secondes).")
        elif "difficulte" in err or "column" in err.lower() or "PGRST" in err:
            conseil = (" → Lance le script **6_seance_rugby.sql** dans Supabase (10 secondes) "
                       "pour ajouter les colonnes du ressenti.")
        return False, f"Enregistrement impossible : {err}{conseil}"

    # les séries (uniquement pour le renforcement)
    series = []
    for l in (lignes or []):
        if not l["reps"]:
            continue
        for s in range(1, (plan["tours"] if plan else TOURS) + 1):
            series.append(dict(set_date=str(jour), session=session, exercise=l["nom"],
                               set_no=s, reps=int(l["reps"]),
                               load_kg=5.0 if "Dumbbell" in l["nom"] else 0.0,
                               variant="standard", rpe=int(rpe)))
    if series:
        try:
            store.save_sets(series)
        except Exception:
            pass                                           # la séance est déjà enregistrée
    return True, "Séance enregistrée. Le programme a déjà ajusté la prochaine. 💪"


# ---------------------------------------------------------------------------
#  OUTILS D'AFFICHAGE
# ---------------------------------------------------------------------------
def poids_corps(store) -> float:
    """Le poids le plus récent connu (pour estimer les calories du rugby)."""
    try:
        p = store.profile() or {}
        for cle in ("weight_kg", "poids_kg", "start_weight_kg"):
            if p.get(cle):
                return float(p[cle])
    except Exception:
        pass
    try:
        df = store.daily_df()
        if df is not None and not df.empty and "weight_kg" in df:
            v = df.dropna(subset=["weight_kg"]).sort_values("log_date").iloc[-1]["weight_kg"]
            if v:
                return float(v)
    except Exception:
        pass
    return POIDS_DEFAUT


def calories_rugby(poids: float, duree_min: int, met: float) -> int:
    return int(round(met * poids * (duree_min / 60.0)))


@st.fragment(run_every=1.0)
def _compte_a_rebours():
    """Le compteur se met à jour tout seul, seconde par seconde."""
    import time
    fin = st.session_state.get("rest_fin")
    if not fin:
        return
    reste = int(fin - time.time())
    if reste > 0:
        st.markdown(f"### ⏳ Repos : **{reste} s**")
        st.progress(min(1.0, max(0.0, 1 - reste / max(1, st.session_state.get("rest_total", 60)))))
    else:
        st.markdown("### ✅ Repos terminé — au travail !")
        st.session_state["rest_fin"] = None


def _chronometre(repos: int):
    import time
    c1, c2, c3 = st.columns([2, 2, 3])
    if c1.button(f"⏱️ Lancer {repos} s de repos", width="stretch", key="se_rest_go"):
        st.session_state["rest_fin"] = time.time() + int(repos)
        st.session_state["rest_total"] = int(repos)
    if c2.button("⏹️ Stop", width="stretch", key="se_rest_stop"):
        st.session_state["rest_fin"] = None
    with c3:
        st.caption("Un superset se finit par le repos : respire, bois une gorgée, "
                   "puis repars pour le tour suivant.")
    _compte_a_rebours()


# ---------------------------------------------------------------------------
#  PAGE — RENFORCEMENT
# ---------------------------------------------------------------------------
def _bloc_reps(store, session: str):
    """Le bloc « ce que l'application a décidé » + le tableau de la séance."""
    sommeil = None
    try:
        dfd = store.daily_df()
        if dfd is not None and not dfd.empty and "sleep_h" in dfd:
            hier = dt.date.today() - dt.timedelta(days=1)
            ligne = dfd[pd.to_datetime(dfd["log_date"]).dt.date.isin([hier, dt.date.today()])]
            if not ligne.empty:
                sommeil = _nombre(ligne.sort_values("log_date").iloc[-1].get("sleep_h"), 0) or None
    except Exception:
        sommeil = None

    S = SEANCES[session]
    histo = lire_historique(store, session)
    plan = analyse(histo, sommeil, rugby_recent(store))
    tab = appliquer(S, plan)

    with st.container(border=True):
        st.markdown(f"#### {S['emoji']} {S['nom']} — {S['sous_titre']}")
        st.markdown(f"**{tab['tours']} tours** par bloc · **repos {tab['repos_apres_tour']} s** "
                    f"entre les tours  \n"
                    f"Déroulé : 🔥 **4 min d'échauffement** → 3 blocs (≈ 22 min) → 🧘 **4 min "
                    f"d'étirements** = **30 minutes**  \n"
                    f"Matériel : {MATERIEL}")
        st.caption(S["note"])
        st.markdown("**Ce que l'application a décidé pour toi aujourd'hui :**")
        for m in plan["messages"]:
            st.markdown(f"- {m}")
        st.caption("Ces réglages viennent de **tes** validations de séance (et de ton rugby). "
                   "Rien n'est imposé : si tu te sens bien, tu peux ajouter un tour.")

    # ---- ÉCHAUFFEMENT (adapté à la séance) : AVANT LE BLOC 1
    _section_echauffement(S)

    # ---- LA SÉANCE
    st.subheader("Ta séance, ligne par ligne")
    st.caption("Fais l'exercice ① puis l'exercice ② **sans t'arrêter** (c'est un « superset »), "
               "puis souffle pendant le repos. Répète le bloc 3 fois au total.")
    for bloc in S["blocs"]:
        lignes_bloc = [l for l in tab["lignes"] if l["bloc"] == bloc["num"]]
        with st.container(border=True):
            st.markdown(f"**Bloc {bloc['num']}** — 3 tours · repos {tab['repos_apres_tour']} s "
                        f"après le 2ᵉ exercice de chaque tour")
            for l in lignes_bloc:
                st.markdown(f"- {l['tour']} **{l['nom']}** — {texte_reps(l)}")
            for l in lignes_bloc:
                ex = EXOS.get(l["nom"], {})
                with st.expander(f"❔ Comment faire — {l['nom']}  ·  {ex.get('cible', '')}"):
                    st.markdown(f"**À quoi ça sert :** {ex.get('pourquoi', '')}")
                    st.markdown("**Comment faire, étape par étape :**")
                    for i, e in enumerate(ex.get("comment", []), start=1):
                        st.markdown(f"{i}. {e}")
                    c1, c2 = st.columns(2)
                    c1.markdown(f"🟢 **Plus facile** — {ex.get('facile', '')}")
                    c2.markdown(f"🔴 **Plus dur** — {ex.get('dur', '')}")

    _chronometre(tab["repos_apres_tour"])

    # ---- ÉTIREMENTS (adaptés à la séance) : À LA FIN
    _section_etirements(S, session)
    return plan, tab, histo


def _section_echauffement(S: dict):
    """L'échauffement, avant le bloc 1 : court, adapté, et expliqué."""
    with st.container(border=True):
        st.markdown(f"### 🔥 Échauffement — 4 minutes  ·  *{S['nom']}*")
        st.markdown("Fais ces mouvements **2 fois de suite**, dans l'ordre, sans t'arrêter. "
                    "Tu dois finir un peu essoufflé — pas fatigué.")
        for e in S["echauffement"]:
            st.markdown(f"- **{e['nom']}** — {e['reps']} répétitions  ·  "
                        f"<span class='hint'>{e['but']}</span>", unsafe_allow_html=True)
        with st.expander("❔ Comment faire ces mouvements (détail) — et pourquoi cet échauffement"):
            st.markdown(f"**Pourquoi cet échauffement-là :** il prépare exactement les muscles que "
                        f"tu vas utiliser aujourd'hui.  \n→ {S['sous_titre']}")
            for e in S["echauffement"]:
                ex = EXOS.get(e["nom"], {})
                st.markdown(f"**{e['nom']}** — {ex.get('cible', '')}")
                for i, c in enumerate(ex.get("comment", []), start=1):
                    st.markdown(f"{i}. {c}")
                st.markdown(f"<span class='hint'>{ex.get('pourquoi', '')}</span>",
                            unsafe_allow_html=True)
                st.markdown("")
            st.caption("C'est ta vraie prévention des blessures pour le rugby : 4 minutes "
                       "maintenant t'évitent trois semaines d'arrêt plus tard.")


def _section_etirements(S: dict, code: str):
    """Les étirements, à la fin : ils réduisent les courbatures et gardent la mobilité."""
    et = ETIREMENTS.get(code, [])
    if not et:
        return
    with st.container(border=True):
        st.markdown(f"### 🧘 Étirements — 4 minutes  ·  *{S['nom']}*")
        st.markdown("À faire **juste après la dernière série**, pendant que les muscles sont "
                    "chauds. Reste **immobile** dans chaque position et **respire** : ça ne doit "
                    "jamais faire mal.")
        for e in et:
            st.markdown(f"- **{e['nom']}** — {e['duree']}")
        with st.expander("❔ Comment faire chaque étirement (détail)"):
            for e in et:
                st.markdown(f"**{e['nom']}** — {e['duree']}")
                for i, c in enumerate(e["comment"], start=1):
                    st.markdown(f"{i}. {c}")
                st.markdown(f"<span class='hint'>Pourquoi : {e['pourquoi']}</span>",
                            unsafe_allow_html=True)
                st.markdown("")
            st.caption("Ils réduisent les courbatures, gardent ta mobilité pour le rugby et "
                       "détendent le dos — le point faible de tous ceux qui dessinent assis.")


def _formulaire_validation(store, session: str, nom: str, plan, tab, cle: str,
                           duree_defaut: int = 30, infos: dict | None = None):
    """Le formulaire commun aux séances de renforcement ET au rugby."""
    with st.form(f"valider_{cle}"):
        f1, f2, f3 = st.columns([1, 1, 1])
        with f1:
            jour = st.date_input("Date", value=dt.date.today(), max_value=dt.date.today(),
                                 format="DD/MM/YYYY", key=f"{cle}_date")
            duree = st.number_input("Durée réelle (min)", 5, 180, duree_defaut, step=5,
                                    key=f"{cle}_duree")
        with f2:
            diff = st.select_slider("Difficulté", options=[1, 2, 3, 4, 5], value=3,
                                    format_func=lambda v: {1: "1 · très facile", 2: "2 · facile",
                                                           3: "3 · juste bien", 4: "4 · dur",
                                                           5: "5 · très dur"}[v], key=f"{cle}_diff")
            rpe = st.slider("Ressenti d'effort (1-10)", 1, 10, 7, key=f"{cle}_rpe")
        with f3:
            pu_plus = st.radio("J'aurais pu en faire plus ?",
                               ["Oui, assez", "Un peu", "Non, c'était le maximum"],
                               index=1, key=f"{cle}_plus")
            energie = st.select_slider("Énergie avant", options=[1, 2, 3, 4, 5], value=3,
                                       key=f"{cle}_energie")
        f4, f5 = st.columns([1, 2])
        with f4:
            douleur = st.radio("Douleur ?", ["Aucune", "Gêne", "Douleur"], key=f"{cle}_douleur")
        with f5:
            zone = st.text_input("Où ? (si gêne ou douleur)",
                                 placeholder="ex. épaule droite, genou…", key=f"{cle}_zone")
        notes = st.text_area("Notes (facultatif)", key=f"{cle}_notes", height=68,
                             placeholder="Un exercice qui coince, une bonne sensation, un détail…")
        ok = st.form_submit_button(f"💾 Enregistrer ma séance — {nom}", type="primary",
                                   width="stretch")
    if not ok:
        return
    if not getattr(store, "client", None):
        st.warning("Mode aperçu : rien n'est enregistré. Renseigne tes clés Supabase "
                   "(page Réglages) pour que le suivi et l'adaptation fonctionnent.")
        return
    bon, msg = enregistrer(store, session, jour, int(duree), int(diff), int(rpe), pu_plus,
                           douleur, zone, int(energie), notes, plan,
                           (tab["lignes"] if tab else None), infos)
    if bon:
        st.success(msg)
        st.balloons()
        st.rerun()
    else:
        st.error(msg)


# ---------------------------------------------------------------------------
#  PAGE — RUGBY
# ---------------------------------------------------------------------------
def page_rugby(store):
    st.subheader("🏉 Ma séance de rugby")
    st.caption("Le rugby, c'est de l'entraînement : il compte autant que les séances de "
               "renforcement. Valide-le ici — durée, intensité, ressenti, douleur — et "
               "l'application en tiendra compte pour la séance du lendemain.")

    poids = poids_corps(store)

    with st.container(border=True):
        c1, c2 = st.columns([2, 1])
        with c1:
            type_rugby = st.radio("Type de séance", [t for t, _ in RUGBY["types"]],
                                  horizontal=True, key="ru_type")
            met = dict(RUGBY["types"])[type_rugby]
        with c2:
            st.write("")
            st.caption(f"Estimation des calories brûlées calculée sur **{poids:.0f} kg** "
                       f"(ton poids le plus récent).")
        duree = st.slider("Durée prévue (minutes)", 15, 150, 75, step=5, key="ru_duree_prevue")
        kcal = calories_rugby(poids, int(duree), met)
        m1, m2, m3 = st.columns(3)
        m1.metric("Calories estimées", f"{kcal} kcal")
        m2.metric("Équivalent", f"≈ {kcal / 80:.1f} h de marche")
        m3.metric("Charge de la semaine", f"{_charge_semaine(store)} min")

    histo = lire_historique(store, RUGBY["code"], limite=6)
    if histo:
        dernier = histo[0]
        st.markdown(f"**Dernière séance de rugby** ({_date_txt(dernier['date'])}) : "
                    f"difficulté {_nombre(dernier['difficulte'], 0):.0f}/5 · ressenti "
                    f"{_nombre(dernier['rpe'], 0):.0f}/10 · {dernier['duree'] or '—'} min")
    else:
        st.info("Aucune séance de rugby enregistrée pour l'instant. Valide celle d'aujourd'hui "
                "et le suivi commencera.")

    # ---- le formulaire de validation (même logique que les séances)
    with st.container(border=True):
        st.markdown("**Valider ma séance de rugby**")
        _formulaire_validation(store, RUGBY["code"], "Rugby", None, None, cle="ru",
                               duree_defaut=int(duree),
                               infos=dict(type_seance=type_rugby, duree_prevue=int(duree),
                                          kcal_estimees=int(kcal), met=met))

    # ---- historique rugby
    if histo:
        st.divider()
        st.subheader("📈 Mon rugby, séance après séance")
        df = pd.DataFrame([{
            "Date": h["date"], "Durée (min)": h["duree"],
            "Difficulté /5": _nombre(h["difficulte"], 0) or None,
            "Ressenti /10": _nombre(h["rpe"], 0) or None,
            "Douleur": h["douleur"] or "Aucune",
            "Notes": (h["notes"] or "")[:50],
        } for h in histo])
        st.dataframe(df, hide_index=True, width="stretch")
        st.caption("Ce que l'application en fait : si le rugby du jeudi est noté « dur », la "
                   "séance du vendredi **allège de 2 répétitions** automatiquement. "
                   "Si une douleur est signalée, elle le rappelle aussi.")


def _charge_semaine(store) -> int:
    """Minutes d'activité (renforcement + rugby) sur les 7 derniers jours."""
    total = 0
    try:
        df = store.workouts_df()
        if df is not None and not df.empty:
            df = df.copy()
            df["session_date"] = pd.to_datetime(df["session_date"]).dt.date
            depuis = dt.date.today() - dt.timedelta(days=7)
            df = df[df["session_date"] >= depuis]
            total = int(pd.to_numeric(df["duration_min"], errors="coerce").fillna(0).sum())
    except Exception:
        return 0
    return total


# ---------------------------------------------------------------------------
#  PAGE PRINCIPALE
# ---------------------------------------------------------------------------
def page_seance(store, target_p: float | None = None):
    st.title("💪 Mes séances")
    st.caption("**Lundi** et **vendredi** : 30 minutes de renforcement — échauffement, 3 blocs, "
               "étirements. **Jeudi** : ton rugby. Tout se valide au même endroit, avec ton "
               "ressenti — et le programme s'ajuste tout seul.")

    auj = dt.date.today()
    jour_fr = JOURS_SEMAINE[auj.weekday()]
    onglet1, onglet2 = st.tabs(["🏋️ Lundi & Vendredi — renforcement", "🏉 Jeudi — rugby"])

    with onglet1:
        conseil = "A" if auj.weekday() == 0 else ("B" if auj.weekday() == 4 else None)
        c1, c2 = st.columns([2, 3])
        with c1:
            sess = st.radio("Séance", ["A", "B"], index=0 if conseil != "B" else 1,
                            horizontal=True,
                            format_func=lambda c: f"{SEANCES[c]['emoji']} {SEANCES[c]['nom']}",
                            key="se_choix")
        with c2:
            S = SEANCES[sess]
            if conseil == sess:
                st.success(f"**Aujourd'hui c'est {jour_fr}** → c'est bien ta séance du "
                           f"**{S['jour']}**.")
            elif jour_fr in AUTRES_JOURS:
                st.info(f"**{jour_fr}** — {AUTRES_JOURS[jour_fr]}")
            else:
                st.caption(f"Séance du **{S['jour']}** — {S['sous_titre']}")

        if sess == "B":
            st.caption("🦵 **Aucun exercice pour les jambes dans cette séance** : tu as rugby la "
                       "veille, elles ont déjà travaillé.")
        plan, tab, histo = _bloc_reps(store, sess)

        st.divider()
        st.subheader("✅ J'ai fini — je valide ma séance")
        st.caption("20 secondes. C'est **ça** qui fait progresser le programme : plus tu es "
                   "honnête, mieux il règle la suite.")
        _formulaire_validation(store, sess, f"Séance du {S['jour']}", plan, tab,
                               cle=f"se{sess}", duree_defaut=30)

        st.divider()
        st.subheader(f"📈 Mes dernières séances du {S['jour'].lower()}")
        _historique_renforcement(store, sess, histo)

    with onglet2:
        page_rugby(store)


def _historique_renforcement(store, sess: str, histo: list[dict]):
    if not histo:
        st.caption("Aucune séance enregistrée pour l'instant. Valide celle-ci et le suivi "
                   "commencera — avec un graphique de difficulté et de ressenti.")
        return
    df = pd.DataFrame([{
        "Date": h["date"], "Durée (min)": h["duree"],
        "Difficulté /5": _nombre(h["difficulte"], 0) or None,
        "Ressenti /10": _nombre(h["rpe"], 0) or None,
        "Douleur": h["douleur"] or "Aucune",
        "Notes": (h["notes"] or "")[:60],
    } for h in histo])
    st.dataframe(df, hide_index=True, width="stretch")
    try:
        import altair as alt
        g = df.dropna(subset=["Difficulté /5"]).copy()
        if not g.empty:
            g["Date"] = pd.to_datetime(g["Date"])
            g = g.melt(id_vars="Date", value_vars=["Difficulté /5", "Ressenti /10"],
                       var_name="Mesure", value_name="Valeur")
            st.altair_chart(alt.Chart(g).mark_line(point=True).encode(
                x=alt.X("Date:T", title=None),
                y=alt.Y("Valeur:Q", scale=alt.Scale(domain=[0, 10])),
                color="Mesure:N").properties(height=220, width="container"))
            st.caption("But du jeu : **rester dans la zone 3/5 de difficulté et 6-8/10 de "
                       "ressenti**. Trop facile → l'application ajoute du travail. Trop dur → "
                       "elle allège. C'est comme ça qu'on progresse sans se blesser.")
    except Exception:
        pass
