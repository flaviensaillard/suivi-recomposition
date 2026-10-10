# -*- coding: utf-8 -*-
"""MES SÉANCES — renforcement 30 min + rugby (version du 29/09)

CE QUI A CHANGÉ
  • Le VENDREDI ne sollicite plus les jambes : c'est le lendemain du rugby.
      → Séance A (lundi)  : BAS du corps + tronc   (jambes reposées depuis jeudi)
      → Séance B (vendredi): HAUT du corps + tronc (jambes laissées au repos)
  • Le RUGBY du jeudi est maintenant une séance à part entière : tu la valides
    comme les autres, avec durée, intensité, difficulté, ressenti, douleur…
  • Les adaptations calculées à partir des validations sont proposées, puis
    appliquées uniquement après accord explicite pour la séance affichée.

Les noms des mouvements sont ceux de Freeletics, pour que tu les retrouves en
deux secondes dans ton application.
"""
from __future__ import annotations

import datetime as dt
import json

import pandas as pd
import streamlit as st

import menus as MN
import tableaux as T

MATERIEL = "2 haltères de 5 kg · 1 barre de traction · une chaise ou un banc · le sol"

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
        pourquoi="Mouvement dynamique pour commencer progressivement ; adapte l'amplitude ou choisis la version sans saut selon tes sensations. Aucun échauffement ne garantit l'absence de blessure.",
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
        pourquoi="Mouvement léger et contrôlé pour mobiliser les épaules avant l'effort. Il ne garantit pas la prévention d'une tendinite ou d'une blessure.",
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
        pourquoi="Variante assistée pour pratiquer le squat et solliciter cuisses et fessiers. La dépense énergétique et l'adaptation varient selon la personne et la séance.",
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
        pourquoi="Exercice de renforcement des cuisses et des fessiers. Il ne protège pas à lui seul les genoux ; choisis une amplitude confortable et arrête en cas de douleur.",
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
        pourquoi="Variante de poussée au poids du corps qui sollicite la poitrine, les triceps, les épaules et le tronc. Choisis une inclinaison adaptée à ton niveau.",
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
        pourquoi="Travaille les abdominaux. Le renforcement du tronc ne garantit pas à lui seul la prévention des douleurs ou blessures du dos.",
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
        cible="Abdominaux", objectif="Crunch — charge facultative",
        comment=[
            "Allongé sur le dos, genoux pliés. Commence sans charge ; un lest léger n'est facultatif que s'il est disponible et confortable.",
            "Décolle les épaules en soufflant, sans tirer sur la nuque.",
            "Redescends lentement ; arrête si le mouvement gêne ou fait mal.",
        ],
        facile="Reste sans charge ou fais moins de répétitions.",
        dur="N'augmente pas la charge sans maîtrise confortable de la version actuelle.",
        pourquoi="Le lest n'est pas nécessaire. L'exercice cible le tronc ; la variante doit être adaptée à la personne.",
    ),

    # ---- bas du corps (séance A)
    "Dumbbell Goblet Squat": dict(
        cible="Cuisses + fessiers", objectif="Squat avec haltère (charge à adapter)",
        comment=[
            "Tiens **un haltère à deux mains devant ta poitrine**, comme un calice "
            "(coudes serrés).",
            "Pieds un peu plus larges que les hanches, pointes légèrement ouvertes.",
            "Descends entre tes jambes en gardant le buste droit, puis remonte en poussant "
            "dans les talons.",
        ],
        facile="Prends un seul haltère plus léger, ou fais des « Assisted Squats » à vide.",
        dur="Descends en 3 secondes et marque 1 seconde en bas.",
        pourquoi="Variante de squat qui sollicite les cuisses et les fessiers. Choisis une charge et une amplitude confortables ; aucune variante ne garantit l'absence de douleur.",
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
        pourquoi="Travaille chaque jambe séparément et sollicite les fessiers. Une différence droite-gauche n'est pas un diagnostic ; augmente la charge progressivement.",
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
        pourquoi="Sollicite l'arrière des cuisses et l'équilibre. Une progression adaptée peut aider à développer ces capacités, sans garantir l'absence de blessure.",
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
        pourquoi="Sollicite le tronc et la prise en suspension. La barre et la suspension doivent être confortables et adaptées à tes capacités ; une variante au sol est possible.",
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
        pourquoi="Mouvement de tirage qui complète les pompes en sollicitant le dos et les bras. Il ne corrige pas à lui seul la posture et ne garantit pas la prévention du mal de dos.",
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
        pourquoi="Une performance de traction peut aider à suivre une capacité donnée, mais ne mesure pas à elle seule la masse musculaire ni l'efficacité globale du programme.",
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
        pourquoi="Exercice de tirage au poids du corps. La difficulté et les résultats dépendent du niveau, de la technique, de la récupération et d'une progression adaptée.",
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
        pourquoi="Exercice de renforcement des épaules. Il ne prévient pas à lui seul les blessures ; ajuste la charge et l'amplitude à tes capacités.",
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
        pourquoi="Exercice ciblant les fléchisseurs du coude. Une charge réelle et adaptée ainsi qu'une technique confortable sont nécessaires ; aucun poids d'haltère n'est présumé par l'application.",
    ),
}

# ---------------------------------------------------------------------------
#  MOBILITÉ / ÉTIREMENTS — optionnels, selon le confort
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
             pourquoi="Étirement doux des mollets, à utiliser seulement si confortable ; il ne prévient pas à lui seul la tendinopathie d'Achille."),
        dict(nom="Posture de l'enfant", duree="40 s",
             comment=["À genoux, assis sur tes talons si c'est confortable, bras tendus devant toi.",
                      "Pose le front au sol si cela convient et respire normalement.",
                      "Reste dans une amplitude confortable ; passe à une autre position si les genoux ou le dos gênent."],
             pourquoi="Option de mobilité du tronc ; elle n'est pas indispensable et ne traite pas une douleur."),
    ],
    "B": [   # après la séance du haut du corps
        dict(nom="Étirement des pectoraux au mur", duree="30 s par côté",
             comment=["Place ton avant-bras contre un mur, à hauteur d'épaule, coude à 90°.",
                      "Tourne doucement le buste du côté opposé, jusqu'à sentir la poitrine s'ouvrir.",
                      "Change de côté."],
             pourquoi="Peut servir de mouvement de mobilité de la poitrine si cela reste confortable ; ne corrige pas à lui seul la posture."),
        dict(nom="Étirement des dorsaux, suspendu à la barre", duree="20 s, deux fois",
             comment=["Attrape ta barre de traction, les deux mains.",
                      "Laisse tout ton poids tirer, épaules relâchées vers le haut.",
                      "Respire calmement. Descends, repose-toi 10 s, puis recommence."],
             pourquoi="Option de mobilité des épaules et du dos, uniquement si la suspension est confortable et si la barre est stable. Une variante sans suspension est possible."),
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
    """Une séance incomplètement renseignée ne compte pas comme réussite facile."""
    if h.get("difficulte") in (None, "") or h.get("rpe") in (None, ""):
        return False
    douleur = str(h.get("douleur") or "").strip().lower()
    # Une case vide signifie « inconnu », pas « aucune douleur ».
    return (_nombre(h.get("difficulte"), 3) <= 3 and _nombre(h.get("rpe"), 8) <= 8
            and douleur in ("aucune", "aucun", "non", "ras"))


# ---------------------------------------------------------------------------
#  ADAPTATION AUTOMATIQUE
# ---------------------------------------------------------------------------
def analyse(historique: list[dict], sommeil_nuit: float | None = None,
            rugby_recent: dict | None = None) -> dict:
    """Calcule une proposition explicable ; aucun ajustement n'est appliqué ici.

    Une douleur signalée bloque la proposition de renforcement. Les valeurs
    manquantes ne sont jamais assimilées à une séance facile.
    """
    messages: list[str] = []
    delta, repos_delta, tours, version_dure = 0, 0, TOURS, False
    bloquee = False

    reussies = 0
    for h in historique:
        if _facile(h):
            reussies += 1
        else:
            break

    dernier = historique[0] if historique else {}
    pu_plus_non = str(dernier.get("pu_plus") or "").strip().lower().startswith("non")
    if historique:
        d = _nombre(dernier.get("difficulte"), 3)
        r = _nombre(dernier.get("rpe"), 8)
        quand = _date_txt(dernier.get("date"))

        if d <= 2 and r <= 6 and _facile(dernier):
            delta, repos_delta = +2, -15
            messages.append(f"Ta dernière fois (**{quand}**) était notée « facile » ({d:.0f}/5) "
                            f"avec un ressenti léger ({r:.0f}/10) : proposition de **+2 répétitions** "
                            f"et **15 s de repos en moins**.")
        elif d >= 4 or r >= 9:
            delta, repos_delta = -2, +15
            messages.append(f"Ta dernière fois (**{quand}**) a été dure ({d:.0f}/5, ressenti "
                            f"{r:.0f}/10) : proposition de **-2 répétitions** et **15 s de repos en plus**.")
        else:
            messages.append(f"Ta dernière fois (**{quand}**) était renseignée : le plan de base est conservé.")

        douleur = str(dernier.get("douleur") or "").strip().lower()
        if douleur and douleur not in ("aucune", "aucun", "non", "ras"):
            zone = dernier.get("zone_douleur") or "zone non précisée"
            bloquee = True
            messages.append(f"⚠️ Une gêne/douleur (**{zone}**) est enregistrée : aucun exercice de "
                            "renforcement ne sera proposé. Ne force pas sur une zone douloureuse ; "
                            "si la douleur est importante ou persiste, demande un avis professionnel.")

        if pu_plus_non:
            delta = 0
            version_dure = False
            messages.append("Tu avais indiqué que tu ne pouvais pas en faire plus : aucune hausse "
                            "de répétitions ni de variante n'est proposée.")
        elif reussies >= 4:
            version_dure = True
            messages.append(f"**{reussies} séances renseignées et faciles d'affilée** : proposition "
                            "de passer aux variantes plus difficiles. À valider avant affichage.")
    else:
        messages.append("**Première séance** : le plan de base est affiché. Note ton ressenti à la fin.")

    # ---- le rugby récent compte aussi, sans imposer l'ajustement
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
            repos_delta = max(repos_delta, 15)
            messages.append(f"🏉 Ton rugby ({quand}) a été costaud ({d:.0f}/5, ressenti {r:.0f}/10) : "
                            "proposition d'allègement de la séance.")
        elif jours is not None and jours <= 2:
            messages.append(f"🏉 Rugby il y a {jours} jour(s) ({quand}) : garde à l'esprit la fatigue "
                            "récente avant de commencer.")
        douleur_rugby = str(rugby_recent.get("douleur") or "").strip().lower()
        if douleur_rugby and douleur_rugby not in ("aucune", "aucun", "non", "ras"):
            bloquee = True
            messages.append(f"⚠️ Une gêne/douleur au rugby ({rugby_recent.get('zone_douleur') or 'zone non précisée'}) "
                            "est enregistrée : aucun exercice de renforcement ne sera proposé.")

    if sommeil_nuit is not None and sommeil_nuit > 0:
        if sommeil_nuit < 6:
            tours = TOURS - 1
            messages.append(f"😴 **{sommeil_nuit:.1f} h de sommeil** notées : proposition de réduire à "
                            f"**{tours} tours** au lieu de {TOURS}.")
        elif sommeil_nuit >= 7.5:
            messages.append(f"😴 **{sommeil_nuit:.1f} h de sommeil** notées ; prends en compte ton état "
                            "du jour, sans hausse automatique de charge.")

    return dict(delta_reps=delta, repos=max(45, min(120, 75 + repos_delta)), tours=tours,
                version_dure=version_dure, messages=messages, bloquee=bloquee,
                proposition_appliquee=False)


def appliquer(seance: dict, plan: dict) -> dict:
    """Le tableau d'une séance ; une douleur enregistrée ne montre aucun exercice."""
    if plan.get("bloquee"):
        return dict(lignes=[], tours=0, repos_apres_tour=75)
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


def planifier_seance(seance: dict, proposition: dict, accepter: bool = False) -> tuple[dict, dict]:
    """Applique une proposition seulement après accord explicite de l'utilisateur."""
    plan = dict(proposition)
    if plan.get("bloquee"):
        plan["proposition_appliquee"] = False
        return plan, appliquer(seance, plan)
    if accepter:
        plan["proposition_appliquee"] = True
    else:
        plan.update(delta_reps=0, repos=75, tours=TOURS, version_dure=False,
                    proposition_appliquee=False)
    return plan, appliquer(seance, plan)


def a_ajustement(proposition: dict) -> bool:
    """Vrai si la proposition modifie le plan de base."""
    return (proposition.get("delta_reps", 0) != 0
            or proposition.get("repos", 75) != 75
            or proposition.get("tours", TOURS) != TOURS
            or bool(proposition.get("version_dure")))


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

        def val(nom, nom_json=None, defaut=None):
            """La colonne si elle est remplie, sinon l'info rangée dans les notes."""
            v = r.get(nom)
            if v is None or (isinstance(v, float) and pd.isna(v)) or v == "":
                return extra.get(nom_json or nom, defaut)
            return v

        out.append(dict(
            date=r.get("session_date"),
            difficulte=val("difficulte"),
            rpe=val("rpe"),
            douleur=val("douleur", defaut=None),
            zone_douleur=val("zone_douleur", defaut=""),
            pu_plus=val("pu_plus"),
            duree=val("duration_min", "duree"),
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
    """Enregistre une séance validée ; refuse les ressentis absents ou incohérents."""
    if any(v is None or v == "" for v in (duree, difficulte, rpe, pu_plus, douleur, energie)):
        return False, "Données réelles incomplètes : aucune séance n'a été enregistrée."
    try:
        duree, difficulte, rpe, energie = map(int, (duree, difficulte, rpe, energie))
    except (TypeError, ValueError):
        return False, "Valeurs de séance invalides : aucune séance n'a été enregistrée."
    if not 5 <= duree <= 180 or not 1 <= difficulte <= 5 or not 1 <= rpe <= 10 or not 1 <= energie <= 5:
        return False, "Valeurs hors limites : aucune séance n'a été enregistrée."
    if pu_plus not in ("Oui, assez", "Un peu", "Non, c'était le maximum"):
        return False, "Réponse sur la réserve invalide : aucune séance n'a été enregistrée."
    if douleur not in ("Aucune", "Gêne", "Douleur"):
        return False, "Présence ou absence de douleur à préciser : aucune séance n'a été enregistrée."
    if douleur in ("Gêne", "Douleur") and not str(zone or "").strip():
        return False, "Précise la zone concernée : aucune séance n'a été enregistrée."
    extra = dict(difficulte=int(difficulte), rpe=int(rpe), pu_plus=pu_plus, douleur=douleur,
                 zone_douleur=zone, energie_avant=int(energie),
                 tours=(int(plan["tours"]) if plan else None))
    if plan:
        extra.update(proposition_appliquee=bool(plan.get("proposition_appliquee")),
                     delta_reps_applique=int(plan.get("delta_reps", 0)),
                     repos_apres_tour=int(plan.get("repos", 75)),
                     variante_dure=bool(plan.get("version_dure", False)))
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
            conseil = (" → Ta base n'autorise pas encore le rugby comme type de séance. "
                       "Dis-le moi : j'ajoute ce qu'il faut.")
        elif "difficulte" in err or "column" in err.lower() or "PGRST" in err:
            conseil = (" → Il manque des colonnes de ressenti dans ta base. "
                       "Dis-le moi : je les ajoute.")
        return False, f"Enregistrement impossible : {err}{conseil}"

    # Le plan décrit des répétitions proposées, pas des répétitions réellement
    # exécutées. Sans saisie effective des séries, ne rien écrire dans workout_sets.
    return True, "Séance enregistrée. La prochaine séance affichera une proposition à valider. 💪"


# ---------------------------------------------------------------------------
#  OUTILS D'AFFICHAGE
# ---------------------------------------------------------------------------
def poids_corps(store) -> float | None:
    """Dernier poids réellement enregistré ; aucun poids de remplacement fictif."""
    try:
        df = store.daily_df()
        if df is not None and not df.empty and "weight_kg" in df:
            lignes = df.dropna(subset=["weight_kg"]).copy()
            if not lignes.empty:
                lignes["weight_kg"] = pd.to_numeric(lignes["weight_kg"], errors="coerce")
                lignes = lignes.dropna(subset=["weight_kg"]).sort_values("log_date")
                if not lignes.empty:
                    poids = float(lignes.iloc[-1]["weight_kg"])
                    return poids if poids > 0 else None
    except Exception:
        pass
    try:
        profil = store.profile() or {}
        for cle in ("weight_kg", "poids_kg"):
            valeur = profil.get(cle)
            if valeur not in (None, "") and float(valeur) > 0:
                return float(valeur)
    except Exception:
        pass
    return None


def calories_rugby(poids: float, duree_min: int, met: float) -> int:
    return int(round(met * poids * (duree_min / 60.0)))


def infos_seance_reelle(store, session: str, duree_reelle: int,
                        infos: dict | None = None) -> dict | None:
    """Prépare les métadonnées validées ; l'estimation rugby utilise la durée réelle."""
    resultat = dict(infos or {})
    if session.upper() == RUGBY["code"]:
        poids = poids_corps(store)
        met = resultat.get("met")
        if poids is not None and met is not None:
            resultat["kcal_estimees"] = calories_rugby(poids, int(duree_reelle), float(met))
        else:
            resultat.pop("kcal_estimees", None)
    return resultat or None


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
    """Affiche le plan de base et demande un accord avant toute adaptation."""
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
    rugby = rugby_recent(store)
    proposition = analyse(histo, sommeil, rugby)
    if proposition.get("bloquee"):
        plan, tab = planifier_seance(S, proposition, accepter=False)
        with st.container(border=True):
            st.markdown(f"#### {S['emoji']} {S['nom']} — {S['sous_titre']}")
            st.error("Séance de renforcement masquée : une gêne ou douleur récente a été enregistrée.")
            for m in plan["messages"]:
                st.markdown(f"- {m}")
            st.caption("Aucune séance n'est enregistrée ni modifiée automatiquement. "
                       "Si l'entrée est erronée, corrige l'historique ; ne force pas sur une douleur.")
        return plan, tab, histo

    accepter = False
    if a_ajustement(proposition):
        derniere_date = str(histo[0].get("date")) if histo else "premiere"
        date_rugby = str((rugby or {}).get("date") or "aucun")
        cle = (f"se_accept_{session}_{derniere_date}_{date_rugby}_"
               f"{proposition['delta_reps']}_{proposition['repos']}_"
               f"{proposition['tours']}_{int(proposition['version_dure'])}_{sommeil}")
        cle = cle.replace(" ", "_").replace(":", "_").replace(".", "_")
        accepter = st.checkbox(
            "Appliquer cette proposition à la séance affichée",
            value=False, key=cle,
            help="Sans validation, le plan de base reste affiché. Aucune adaptation n'est appliquée automatiquement.")
    plan, tab = planifier_seance(S, proposition, accepter=accepter)

    with st.container(border=True):
        st.markdown(f"#### {S['emoji']} {S['nom']} — {S['sous_titre']}")
        st.markdown(f"**{tab['tours']} tours** par bloc · **repos {tab['repos_apres_tour']} s** "
                    f"entre les tours  \n"
                    f"Déroulé : 🔥 **4 min d'échauffement** → 3 blocs (≈ 22 min) → 🧘 **4 min "
                    f"d'étirements** = **30 minutes**  \n"
                    f"Matériel : {MATERIEL}")
        st.caption(S["note"])
        st.markdown("**Proposition de l'application :**" if a_ajustement(proposition)
                    else "**Plan de base :**")
        for m in plan["messages"]:
            st.markdown(f"- {m}")
        if a_ajustement(proposition):
            st.info("Proposition appliquée pour cette séance." if accepter else
                    "Proposition non appliquée : le plan de base reste affiché.")
        st.caption("Les changements de répétitions, repos, tours ou variante restent des suggestions : "
                   "ils ne s'appliquent qu'après validation explicite.")

    _section_echauffement(S)
    st.subheader("Ta séance, ligne par ligne")
    st.caption("Fais l'exercice ① puis l'exercice ② **sans t'arrêter** (c'est un « superset »), "
               "puis souffle pendant le repos.")
    for bloc in S["blocs"]:
        lignes_bloc = [l for l in tab["lignes"] if l["bloc"] == bloc["num"]]
        with st.container(border=True):
            st.markdown(f"**Bloc {bloc['num']}** — {tab['tours']} tours · repos "
                        f"{tab['repos_apres_tour']} s après le 2ᵉ exercice de chaque tour")
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
            st.caption("Cet échauffement progressif peut préparer à la séance, mais ne garantit pas l'absence de blessure. Adapte-le à tes sensations et à la charge du jour.")


def _section_etirements(S: dict, code: str):
    """Propose quelques mouvements de mobilité ou étirements optionnels."""
    et = ETIREMENTS.get(code, [])
    if not et:
        return
    with st.container(border=True):
        st.markdown(f"### 🧘 Étirements — 4 minutes  ·  *{S['nom']}*")
        st.markdown("Ces positions sont facultatives : reste dans une amplitude confortable, respire normalement et relâche si tu ressens une douleur, un engourdissement ou une gêne inhabituelle. Elles ne sont pas un traitement et ne garantissent pas moins de courbatures.")
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
            st.caption("Ces options peuvent travailler l'amplitude de mouvement si elles te conviennent ; elles ne corrigent pas une posture ou une douleur et ne sont pas obligatoires.")


def _formulaire_validation(store, session: str, nom: str, plan, tab, cle: str,
                           infos: dict | None = None):
    """Le formulaire commun aux séances de renforcement ET au rugby."""
    with st.form(f"valider_{cle}"):
        f1, f2, f3 = st.columns([1, 1, 1])
        with f1:
            jour = st.date_input("Date", value=dt.date.today(), max_value=dt.date.today(),
                                 format="DD/MM/YYYY", key=f"{cle}_date")
            duree = st.number_input("Durée réelle (min)", min_value=5, max_value=180,
                                    value=None, step=5, key=f"{cle}_duree",
                                    placeholder="Saisir la durée mesurée")
        with f2:
            diff = st.select_slider("Difficulté", options=[1, 2, 3, 4, 5], value=None,
                                    format_func=lambda v: {1: "1 · très facile", 2: "2 · facile",
                                                           3: "3 · juste bien", 4: "4 · dur",
                                                           5: "5 · très dur"}[v], key=f"{cle}_diff")
            rpe = st.selectbox("Ressenti d'effort (1–10)", options=list(range(1, 11)),
                               index=None, placeholder="Choisir une valeur", key=f"{cle}_rpe")
        with f3:
            pu_plus = st.radio("J'aurais pu en faire plus ?",
                               ["Oui, assez", "Un peu", "Non, c'était le maximum"],
                               index=None, key=f"{cle}_plus")
            energie = st.select_slider("Énergie avant", options=[1, 2, 3, 4, 5], value=None,
                                       key=f"{cle}_energie")
        f4, f5 = st.columns([1, 2])
        with f4:
            douleur = st.radio("Douleur ?", ["Aucune", "Gêne", "Douleur"],
                               index=None, key=f"{cle}_douleur")
        with f5:
            zone = st.text_input("Où ? (si gêne ou douleur)",
                                 placeholder="ex. épaule droite, genou…", key=f"{cle}_zone")
        notes = st.text_area("Notes (facultatif)", key=f"{cle}_notes", height=68,
                             placeholder="Un exercice qui coince, une bonne sensation, un détail…")
        ok = st.form_submit_button(f"💾 Enregistrer ma séance — {nom}", type="primary",
                                   width="stretch")
    if not ok:
        return
    manquants = []
    if duree is None:
        manquants.append("la durée réelle")
    if diff is None:
        manquants.append("la difficulté")
    if rpe is None:
        manquants.append("le ressenti d'effort")
    if pu_plus is None:
        manquants.append("la réponse sur la réserve")
    if energie is None:
        manquants.append("l'énergie avant séance")
    if douleur is None:
        manquants.append("la présence ou l'absence de douleur")
    if manquants:
        st.error("Renseigne les données réellement observées : " + ", ".join(manquants) + ". Rien n'a été enregistré.")
        return
    if douleur in ("Gêne", "Douleur") and not zone.strip():
        st.error("Précise la zone concernée par la gêne ou la douleur avant l'enregistrement.")
        return
    infos_reelles = infos_seance_reelle(store, session, int(duree), infos)
    bon, msg = enregistrer(store, session, jour, int(duree), int(diff), int(rpe), pu_plus,
                           douleur, zone, int(energie), notes, plan,
                           (tab["lignes"] if tab else None), infos_reelles)
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
               "une éventuelle adaptation sera proposée pour la prochaine séance, à confirmer.")

    poids = poids_corps(store)

    with st.container(border=True):
        type_rugby = st.radio("Type de séance", [t for t, _ in RUGBY["types"]],
                              horizontal=True, key="ru_type")
        met = dict(RUGBY["types"])[type_rugby]
        duree = st.slider("Durée prévue (minutes)", 15, 150, 75, step=5, key="ru_duree_prevue")
        c1, c2 = st.columns(2)
        c1.metric("Charge de la semaine", f"{_charge_semaine(store)} min")
        kcal = calories_rugby(poids, int(duree), met) if poids is not None else None
        if kcal is None:
            c2.metric("Énergie dépensée", "—")
            st.info("Pas de poids réellement enregistré : l'application omet l'estimation calorique.")
        else:
            c2.metric("Estimation indicative", f"≈ {kcal} kcal")
            st.caption("Ordre de grandeur calculé à partir du type, de la durée prévue et du dernier poids enregistré ; grande incertitude, à ne pas utiliser pour ajuster automatiquement l'alimentation.")

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
        infos = dict(type_seance=type_rugby, duree_prevue=int(duree), met=met)
        _formulaire_validation(store, RUGBY["code"], "Rugby", None, None,
                               cle="ru", infos=infos)

    # ---- historique rugby
    if histo:
        st.divider()
        st.subheader("📈 Mon rugby, séance après séance")
        _tableau_seances(store, RUGBY["code"], histo, cle="histo_rugby")
        st.caption("Une séance de rugby difficile peut déclencher une proposition d'allègement "
                   "pour le renforcement ; tu la valides ou l'ignores. Une gêne/douleur récente "
                   "masque la séance de renforcement au lieu de conserver les exercices.")


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
    st.caption("**Lundi** et **vendredi** : renforcement. **Jeudi** : rugby. Les adaptations "
               "du plan sont des propositions explicites ; elles ne s'appliquent qu'après validation.")

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

        if not plan.get("bloquee"):
            st.divider()
            st.subheader("✅ J'ai fini — je valide ma séance")
            st.caption("20 secondes. C'est **ça** qui permet de préparer une proposition pour la suite.")
            _formulaire_validation(store, sess, f"Séance du {S['jour']}", plan, tab,
                                   cle=f"se{sess}")

        st.divider()
        st.subheader(f"📈 Mes dernières séances du {S['jour'].lower()}")
        _historique_renforcement(store, sess, histo)

    with onglet2:
        page_rugby(store)


def _sauver_seance(store, base: dict, extra: dict) -> bool:
    """Enregistre une séance corrigée (colonnes détaillées, sinon dans les notes)."""
    try:
        store.save_workout({**base, **extra})
        return True
    except Exception:
        pass
    base = dict(base)
    base["notes"] = ((base.get("notes") or "") + "\n[SEANCE]"
                     + json.dumps(extra, ensure_ascii=False)).strip()
    store.save_workout(base)
    return True


def corriger_seance(store, session: str, jour, champs: dict) -> bool:
    """Corrige une séance déjà enregistrée (durée, difficulté, ressenti, douleur, notes).

    On ne réécrit que les champs corrigés : les informations détaillées de la
    séance (nombre de tours, énergie du jour…) restent intactes.
    """
    colonnes = {"Durée (min)": "duration_min", "Difficulté /5": "difficulte",
                "Ressenti /10": "rpe", "Douleur": "douleur", "Notes": "notes"}
    # 1) la ligne existante : on relit ses notes pour ne rien perdre
    base, extra = None, {}
    try:
        df = store.workouts_df()
        if df is not None and not df.empty:
            lignes = df[(df["session_date"].astype(str) == str(jour)) &
                        (df["session"].astype(str).str.upper() == str(session).upper())]
            if not lignes.empty:
                r = lignes.iloc[0]
                extra = dict(_depuis_notes(r.get("notes")))
                base = dict(session_date=str(jour), session=session,
                            notes=(r.get("notes") or "").split("[SEANCE]")[0].strip())
                if r.get("duration_min") is not None and not pd.isna(r.get("duration_min")):
                    base["duration_min"] = int(r["duration_min"])
                if r.get("rpe") is not None and not pd.isna(r.get("rpe")):
                    base["rpe"] = int(r["rpe"])
    except Exception:
        pass
    if base is None:
        base = dict(session_date=str(jour), session=session, notes="")

    # 2) on applique uniquement ce qui a été corrigé
    for affiche, valeur in (champs or {}).items():
        cle = colonnes.get(affiche)
        if cle is None:
            continue
        if cle == "notes":
            base["notes"] = "" if valeur is None else str(valeur).strip()
        elif cle == "douleur":
            base["douleur"] = "Aucune" if valeur in (None, "") else str(valeur)
            extra["douleur"] = base["douleur"]
        elif valeur is None or (isinstance(valeur, float) and pd.isna(valeur)):
            continue
        elif cle == "duration_min":
            base["duration_min"] = int(round(float(valeur)))
            extra["duree"] = base["duration_min"]
        elif cle == "difficulte":
            extra["difficulte"] = int(round(float(valeur)))
        elif cle == "rpe":
            base["rpe"] = int(round(float(valeur)))
            extra["rpe"] = base["rpe"]
    return _sauver_seance(store, base, extra)


def _tableau_seances(store, session: str, histo: list[dict], cle: str):
    """L'historique d'une séance, modifiable pour corriger une erreur de saisie."""
    if not histo:
        return
    df = pd.DataFrame([{
        "Date": h["date"], "Durée (min)": h["duree"],
        "Difficulté /5": _nombre(h["difficulte"], 0) or None,
        "Ressenti /10": _nombre(h["rpe"], 0) or None,
        "Douleur": h["douleur"] or "Aucune",
        "Notes": (h["notes"] or ""),
    } for h in histo])
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce").dt.date
    df.index = pd.Index([str(h["date"]) for h in histo])   # identifiant de la ligne = la date
    T.tableau_editable(
        df, cle=cle,
        colonnes={"Date": T.col_jour("Date"),
                  "Durée (min)": T.col_entier("Durée (min)", 5, 300, 5),
                  "Difficulté /5": T.col_entier("Difficulté /5", 1, 5),
                  "Ressenti /10": T.col_entier("Ressenti /10", 1, 10),
                  "Douleur": T.col_texte("Douleur", "medium"),
                  "Notes": T.col_texte("Notes", "large")},
        desactive=["Date"], hauteur=None,
        sauver=lambda jour, ch: corriger_seance(store, session, jour, ch),
        aide="Une séance mal notée (durée, difficulté, ressenti, douleur, note) se corrige "
             "**ici** : clique dans la case, puis sur **💾 Enregistrer les corrections**.")


def _historique_renforcement(store, sess: str, histo: list[dict]):
    if not histo:
        st.caption("Aucune séance enregistrée pour l'instant. Valide celle-ci et le suivi "
                   "commencera — avec un graphique de difficulté et de ressenti.")
        return
    _tableau_seances(store, sess, histo, cle=f"histo_{sess}")
    df = pd.DataFrame([{
        "Date": h["date"], "Durée (min)": h["duree"],
        "Difficulté /5": _nombre(h["difficulte"], 0) or None,
        "Ressenti /10": _nombre(h["rpe"], 0) or None,
    } for h in histo])
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
