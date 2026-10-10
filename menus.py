# -*- coding: utf-8 -*-
"""
MENUS & NUTRITION — lecture exacte de la base « gestion-menus ».

Après la migration, tes tables sont enfin complètes :
  • ingredients        : tes 153 ingrédients + les 3 339 aliments de la base française
                         (colonnes code_ciqual, kcal_100g, proteines_100g,
                          glucides_100g, lipides_100g)
  • recipes            : 104 recettes, toutes ramenées à 4 personnes
  • recipe_ingredients : 331 lignes, TOUTES reliées à un aliment de la base
  • planned_meals      : 79 repas planifiés (date_menu, meal_type, recipe_id…)

Ce module en déduit, sans aucune saisie :
  • les calories et macros d'une recette entière et d'une part
  • « ma part » (3 façons de la définir, avec un défaut proposé)
  • la liste de courses de la semaine, rangée par rayon
  • les repas du jour, prêts à être ajoutés au journal de protéines

Aucune écriture ici : que de la lecture et du calcul. Tu peux tester sans risque.
"""

VERSION = "1.0.11"        # affiché dans la barre de gauche (contrôle des fichiers à jour)

import datetime as dt
import math
import re

# ---------------------------------------------------------------------------
#  CONVERSIONS — les unités de ton application
# ---------------------------------------------------------------------------
#  Cuillères et centilitres : valeurs retenues par ton application.
CUIL_A_SOUPE = 15.0   # g
CUIL_A_CAFE = 5.0     # g
CL = 10.0             # g   (1 cl d'eau = 10 g)

#  ⚠️ « pièce » et « unité », c'est la même chose : on ne garde QUE « unité »
#     à l'affichage (décision du 30/09). Les anciennes écritures restent
#     comprises, mais elles sont ramenées à « unité » par `unite_propre()`.
UNITES_PIECE = (
    "unité", "unite", "pièce", "piece", "tranche", "sachet", "boîte", "boite",
    "gousse", "botte", "pot", "verre", "ramequin", "pincée", "pincee", "filet",
    "c. à s.", "c. à c.", "cuillère", "cuillere", "tasse", "bouquet", "brin",
)
UNITES_MASSE = ("g", "gr", "gramme", "grammes", "kg", "kilogramme")
UNITES_VOLUME = ("ml", "cl", "l", "litre", "litres", "centilitre")

#  Poids par défaut quand la ligne donne une petite unité sans poids de pièce
#  (« 1 pincée de poivre » pèse 0,5 g — pas 100 g).
POIDS_UNITE_MINI = {
    "pincée": 0.5, "pincee": 0.5, "gousse": 5.0, "brin": 2.0, "feuille": 1.0,
    "bouquet": 10.0, "filet": 5.0, "goutte": 0.05, "tasse": 200.0,
    "ramequin": 100.0, "c. à c.": 5.0, "c. à s.": 15.0, "cuillère": 5.0,
    "cuillere": 5.0, "sachet": 100.0, "pot": 125.0, "verre": 200.0,
}

#  Aliments qui se dosent en toutes petites quantités : on ne leur applique
#  jamais la « portion de référence » (100 g de cumin serait absurde).
MOTS_PETITES_QUANTITES = (
    "sel", "poivre", "épice", "epice", "herbe", "origan", "thym", "cumin", "curry",
    "paprika", "cannelle", "muscade", "curcuma", "levure", "bicarbonate", "bouillon",
    "concentré", "concentre", "moutarde", "vinaigre", "gélatine", "gelatine",
    "extrait", "arôme", "arome", "colorant", "sucre vanillé", "vanille",
)

POIDS_PIECE_DEFAUT = {
    "oeuf": 50.0, "œuf": 50.0, "tranche": 30.0, "gousse": 5.0, "sachet": 100.0,
    "boîte": 250.0, "boite": 250.0, "botte": 100.0, "pot": 125.0, "verre": 200.0,
}


def _nombre(v) -> float:
    """Convertit une valeur en nombre fini, sans jamais planter."""
    if v is None or str(v).strip().lower() in ("", "null", "none", "nan"):
        return 0.0
    try:
        nombre = float(str(v).replace(",", "."))
        return nombre if math.isfinite(nombre) else 0.0
    except (TypeError, ValueError):
        return 0.0


def valeur_nutriment(v):
    """Renvoie un nutriment valide (0 est valide), ou None s'il est absent/invalide."""
    if v is None or str(v).strip().lower() in ("", "null", "none", "nan"):
        return None
    try:
        nombre = float(str(v).replace(",", "."))
    except (TypeError, ValueError):
        return None
    if not math.isfinite(nombre) or nombre < 0:
        return None
    return nombre


def nutriment_present(v) -> bool:
    return valeur_nutriment(v) is not None


def unite_est_piece(unite: str) -> bool:
    u = (unite or "").strip().lower()
    return u in UNITES_PIECE or u in POIDS_PIECE_DEFAUT


def quantite_en_grammes(qte, unite: str, ingredient: dict | None) -> float:
    """Convertit (quantité, unité) en grammes.

    ingredient : la ligne de la table « ingredients » (poids_piece_g, densite, unit).
    Renvoie 0 si on ne sait pas convertir — les totaux restent justes, jamais faux.
    """
    qte = _nombre(qte)
    if qte <= 0:
        return 0.0
    ing = ingredient or {}
    poids_piece = _nombre(ing.get("poids_piece_g"))
    densite = _nombre(ing.get("densite"))
    u = (unite or ing.get("unit") or "").strip().lower()
    if u in ("", "null", "none"):
        u = str(ing.get("unit") or "").strip().lower()
    if u in ("", "null", "none"):
        return 0.0  # unité inconnue : ne pas la supposer en grammes

    if u in ("g", "gr", "gramme", "grammes"):
        return qte
    if u in ("kg", "kilogramme", "kilogrammes"):
        return qte * 1000.0
    if u in ("ml",):
        return qte * densite if densite > 0 else 0.0
    if u in ("cl",):
        return qte * CL * densite if densite > 0 else 0.0
    if u in ("l", "litre", "litres"):
        return qte * 1000.0 * densite if densite > 0 else 0.0
    if u in ("c. à s.", "c. à soupe", "cuillère à soupe", "cuillere a soupe", "cas"):
        return qte * CUIL_A_SOUPE * densite if densite > 0 else 0.0
    if u in ("c. à c.", "c. à café", "cuillère à café", "cuillere a cafe", "cac"):
        return qte * CUIL_A_CAFE * densite if densite > 0 else 0.0
    # unités « comptables » : unité, tranche, gousse, boîte…
    if poids_piece > 0:
        return qte * poids_piece
    mini = POIDS_UNITE_MINI.get(u)
    if mini:
        return qte * mini
    for cle, g in POIDS_PIECE_DEFAUT.items():
        if cle in (ing.get("name") or "").lower():
            return qte * g
    return 0.0


# ---------------------------------------------------------------------------
#  CALCUL DES MACROS
# ---------------------------------------------------------------------------
CHAMPS_NUTR = ("kcal", "proteines", "glucides", "lipides")


def portion_standard(ing: dict | None) -> float:
    """Portion de référence d'un aliment, en grammes (la valeur de ta base).

    C'est le « quantite_recommandee » + « unite_recommandee » de ta table :
    par exemple 100 g pour les aliments Ciqual, 200 g pour un brocoli,
    0,5 unité (150 g) pour une aubergine.
    """
    ing = ing or {}
    q = _nombre(ing.get("quantite_recommandee"))
    if not q:
        return 0.0
    u = ing.get("unite_recommandee") or ing.get("unit")
    g = quantite_en_grammes(q, u, ing)
    if not g:
        g = quantite_en_grammes(q, "unité", ing)
    # Ne pas transformer silencieusement un volume ou une unité inconnue en 100 g.
    # La recette sera signalée comme incomplète tant que le poids n'est pas connu.
    return g or 0.0


def est_pseudo_ingredient(nom) -> bool:
    """Vrai pour les entrées « [Ing] Pâtes », « [Txt] Salade » du planning.

    Pour ces entrées, la quantité enregistrée est un NOMBRE DE PERSONNES,
    pas un poids : c'est la cause du bug de comptage des protéines.
    """
    return str(nom or "").strip().lower().startswith("[ing]")


def grammes_de_ligne(l: dict, ing: dict | None, pseudo: bool = False) -> tuple:
    """Grammes d'une ligne de recette + drapeau « quantité estimée ».

    `pseudo=True` pour les entrées « [Ing] X » : la quantité est un nombre de
    personnes → on la multiplie par la portion de référence de l'aliment.
    Sinon on convertit normalement, et si l'unité ne donne rien on retombe
    sur la portion de référence au lieu de compter 0 g en silence.
    """
    ing = ing or {}
    q = _nombre(l.get("quantity"))
    u = str(l.get("unit") or "").strip().lower()
    vide = u in ("", "null", "none")
    ppg = _nombre(ing.get("poids_piece_g"))
    petit = any(mot in (ing.get("name") or "").lower() for mot in MOTS_PETITES_QUANTITES)

    # --- « 1 oignon » écrit sans unité = 1 PIÈCE (80 g), pas 1 gramme.
    #     Uniquement pour de petits nombres entiers : « 500 » sans unité reste 500 g.
    if vide and not pseudo and 0 < q <= 10 and q == int(q) and 20 <= ppg <= 600:
        return q * ppg, True

    g = quantite_en_grammes(q, l.get("unit"), ing)
    if pseudo:
        if g >= 25:                       # une vraie quantité (300 g, 4 œufs…)
            return g, False
        p = portion_standard(ing)
        if p:
            return q * p, True
        return g, False
    if g:
        return g, False
    # unité inexploitable : on retombe sur la portion de référence, sauf pour
    # les aliments qui se dosent en pincées (toujours comptés très petit)
    if petit:
        mini = POIDS_UNITE_MINI.get(u) or 1.0
        return q * mini, True
    p = portion_standard(ing)
    #  ⭐ le plafond était à 12 portions (02/10) : au-delà, l'aliment comptait
    #     0 g dans la liste de courses — un repas de 20 personnes n'était donc
    #     plus compté du tout. La borne haute est repoussée très loin : il n'y a
    #     plus de limite pratique au nombre de convives.
    if p and 1 <= q <= 1000:
        return q * p, True
    return g, False


# ===========================================================================
#  RECHERCHE INSENSIBLE AUX ACCENTS  (demandé le 30/09)
#  « pates » doit proposer « Pâtes », « epinard » doit trouver « Épinard »,
#  quel que soit l'onglet. Ces fonctions servent à TOUTE l'application.
# ===========================================================================
def sans_accent(t) -> str:
    """Minuscules, sans accent, œ → oe (« Pâtes » → « pates »)."""
    import unicodedata
    x = str(t or "").lower().replace("œ", "oe").replace("æ", "ae")
    x = unicodedata.normalize("NFD", x)
    return "".join(c for c in x if unicodedata.category(c) != "Mn")


def cle_recherche(t) -> str:
    """Forme comparable : sans accent, ponctuation réduite à des espaces."""
    x = sans_accent(t)
    for a in ("'", "’", "-", ",", "(", ")", "/", "."):
        x = x.replace(a, " ")
    return " ".join(x.split())


def correspond(texte, requete) -> bool:
    """Vrai si le texte contient tous les mots de la requête (accents ignorés).

    Une petite faute de frappe est pardonnée sur les mots de 4 lettres et plus
    (« courgete » trouve « courgette ») ; les mots plus courts doivent être exacts,
    sinon « riz » trouverait n'importe quoi.
    """
    import difflib
    cible = cle_recherche(texte)
    if not cible:
        return False
    mots = [m for m in cle_recherche(requete).split() if m]
    if not mots:
        return True
    decoupes = cible.split()
    for mot in mots:
        if mot in cible:
            continue
        if len(mot) < 4:
            return False
        if not any(difflib.SequenceMatcher(None, mot, m).ratio() >= 0.75 for m in decoupes):
            return False
    return True


def _pertinence(cible: str, mots: list) -> tuple:
    """Classe les résultats : ce qui COMMENCE par la recherche d'abord.

    « pates » → « Pâtes » (n°1), puis « Pâtes à lasagnes », puis les aliments
    qui contiennent seulement le mot. À pertinence égale, le plus court gagne
    (c'est presque toujours le bon).
    """
    if cible.startswith(" ".join(mots)):
        rang = 0
    elif any(m.startswith(mots[0]) for m in cible.split()) or cible.startswith(mots[0]):
        rang = 1
    else:
        rang = 2
    return (rang, len(cible), cible)


def filtre_recherche(options, requete, maximum: int | None = None) -> list:
    """Les options qui correspondent à la requête, les plus justes d'abord.

    Accents, majuscules et ponctuation ne comptent pas. La recherche est
    d'abord EXACTE (« lentille » ne propose pas « dentelle ») : elle ne
    pardonne une faute de frappe (« courgete » → « courgette ») que s'il n'y a
    aucun résultat exact. Sinon « pates » ramenait toutes les pizzas.
    """
    import difflib
    options = list(options or [])
    req = cle_recherche(requete or "")
    if not req:
        return options[:maximum] if maximum else options
    mots = [m for m in req.split() if m]
    exacts, flous = [], []
    for o in options:
        cible = cle_recherche(o)
        if not cible:
            continue
        if all(m in cible for m in mots):                     # exact (accents ignorés)
            exacts.append((_pertinence(cible, mots), o))
        elif all(len(m) >= 4 for m in mots):                  # tolérance aux fautes
            decoupes = cible.split()
            notes = []
            for m in mots:
                note = max(difflib.SequenceMatcher(None, m, d).ratio() for d in decoupes)
                if note < 0.75:
                    break
                notes.append(note)
            if len(notes) == len(mots):
                flous.append(((-sum(notes) / len(notes), len(cible), cible), o))
    if exacts:
        exacts.sort()
        gardes = [o for _, o in exacts]
    else:
        flous.sort()
        gardes = [o for _, o in flous]
    return gardes[:maximum] if maximum else gardes


def champ_recherche(cle_etat: str, label: str = "🔍 Rechercher",
                    placeholder: str = "tape quelques lettres, les accents ne comptent pas"):
    """La case de recherche (à mettre HORS d'un formulaire, pour filtrer tout de suite)."""
    import streamlit as st
    return st.text_input(label, key=cle_etat, placeholder=placeholder,
                         help="Tu peux taper sans accent : « pates » trouve « Pâtes », "
                              "« epinard » trouve « Épinard ».")

# ===========================================================================
#  LA LISTE QUI CHERCHE TOUTE SEULE — LE SEUL MODULE DE RECHERCHE (30/09, soir)
#
#  « je n'en veux qu'une seule qui fasse les deux : liste déroulante où je
#    sélectionne sans faire de recherche ET quand je tape "pate" ça trouve les
#    correspondances (de manière dynamique au fur et à mesure que je tape les
#    lettres, je ne veux pas avoir à appuyer sur entrer) peu importe les accents
#    ou non ! on fait ça pour toute l'application »
#
#  La liste déroulante de Streamlit ne sait pas faire ça : sa recherche
#  interne ne compare que les minuscules (`toLowerCase`) — taper « pate » n'y
#  trouve donc JAMAIS « Pâtes » (c'est le « No results » de la capture).
#  Vérifié dans le code de Streamlit : fuzzyFilterSelectOptions…js, fonction
#  `gn()` qui ne fait que toLowerCase().
#
#  D'où ce widget, appelé comme une liste déroulante normale :
#    • fermé : UNE ligne, on la déroule et on clique (aucune recherche à faire) ;
#    • ouvert : un champ de recherche EST DANS le widget (rien de plus à
#      l'écran) et filtre PENDANT la frappe, sans appuyer sur Entrée.
#  Sa logique de recherche est la copie exacte de filtre_recherche() ci-dessus
#  (vérifié : 26 requêtes donnent le même résultat en Python et en JavaScript).
#
#  Le widget est un « composant » Streamlit : le fichier HTML ci-dessous est
#  écrit dans un dossier temporaire au démarrage, puis déclaré. Aucun fichier
#  ni paquet en plus à installer.
# ===========================================================================
_HTML_LISTE = r"""<!DOCTYPE html>
<!--
  LA LISTE QUI CHERCHE TOUTE SEULE  (30/09/2026)

  Un seul widget, qui fait les deux :
    • fermé  : une seule ligne, comme une liste déroulante normale — on la déroule
               et on clique sa ligne, sans rien taper ;
    • ouvert : un champ de recherche EST DANS le widget (rien de plus sur la page)
               et filtre PENDANT la frappe, sans appuyer sur Entrée, en IGNORANT
               LES ACCENTS (« pate » trouve « Pâtes fourrées »).

  Ce fichier est un « composant » Streamlit : il parle à l'application par
  messages (postMessage). Il est écrit par menus.py dans un dossier temporaire,
  donc rien à installer et aucun fichier en plus à déposer sur GitHub.

  La logique de recherche est la copie exacte de `filtre_recherche` (menus.py) :
  accents et majuscules ignorés, correspondance EXACTE d'abord, et tolérance aux
  petites fautes de frappe seulement s'il n'y a aucun résultat exact.
-->
<html lang="fr">
<head>
<meta charset="utf-8">
<style>
  :root{
    --fond:#ffffff; --texte:#31333f; --bord:#d5dae5; --bord-fonce:#a3a8b8;
    --primaire:#ff4b4b; --survol:#f2f4f9; --doux:#808495; --ombre:0 2px 8px rgba(0,0,0,.12);
  }
  *{box-sizing:border-box}
  html,body{margin:0;padding:0;background:transparent;overflow:hidden}
  body{font-family:"Source Sans Pro","Source Sans 3",-apple-system,BlinkMacSystemFont,
        "Segoe UI",Roboto,sans-serif;color:var(--texte);font-size:14px}
  #racine{padding:2px 1px 4px 1px}

  .etiquette{display:flex;align-items:center;gap:5px;font-size:14px;line-height:1.4;
             margin:0 0 4px 1px;color:var(--texte)}
  .aide{width:14px;height:14px;border-radius:50%;border:1px solid var(--bord-fonce);
        color:var(--doux);font-size:10px;line-height:12px;text-align:center;
        cursor:help;flex:0 0 auto;user-select:none}

  .boite{display:flex;align-items:center;gap:8px;min-height:38px;padding:7px 10px;
         border:1px solid var(--bord);border-radius:8px;background:var(--fond);
         cursor:pointer;user-select:none}
  .boite:hover{border-color:var(--primaire)}
  .boite.ouvert{border-color:var(--primaire);border-bottom-left-radius:0;border-bottom-right-radius:0}
  .valeur{flex:1 1 auto;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .valeur.vide{color:var(--doux)}
  .chevron{flex:0 0 auto;color:var(--doux);font-size:11px;transition:transform .12s}
  .boite.ouvert .chevron{transform:rotate(180deg)}

  .panneau{border:1px solid var(--primaire);border-top:0;border-bottom-left-radius:8px;
           border-bottom-right-radius:8px;background:var(--fond);overflow:hidden}
  .panneau.cache{display:none}

  .barre{padding:7px 8px;border-bottom:1px solid var(--bord)}
  .barre input{width:100%;border:1px solid var(--bord);border-radius:6px;padding:6px 8px;
               font-size:14px;font-family:inherit;color:var(--texte);background:var(--fond);outline:none}
  .barre input:focus{border-color:var(--primaire)}

  .liste{max-height:246px;overflow-y:auto;padding:4px 0;overscroll-behavior:contain}
  .ligne{padding:7px 12px;cursor:pointer;display:flex;align-items:center;gap:8px;
         line-height:1.3;white-space:normal}
  .ligne .marque{flex:0 0 14px;color:var(--primaire);font-size:12px}
  .ligne.survol{background:var(--survol)}
  .ligne.choisie .marque::before{content:"✓"}
  .vide{padding:10px 12px;color:var(--doux);font-style:italic}
  .vide.cache{display:none}
  .compte{padding:5px 12px;color:var(--doux);font-size:12px;border-top:1px solid var(--bord)}
  .compte.cache{display:none}
</style>
</head>
<body>
<div id="racine">
  <div class="etiquette" id="etiquette">
    <span id="texte-etiquette"></span>
    <span class="aide" id="aide" title="">?</span>
  </div>
  <div class="boite" id="boite" tabindex="0" role="button" aria-haspopup="listbox">
    <span class="valeur vide" id="valeur">—</span>
    <span class="chevron" id="chevron">v</span>
  </div>
  <div class="panneau cache" id="panneau">
    <div class="barre">
      <input id="filtre" type="text" autocomplete="off" spellcheck="false"
             placeholder="tape pour filtrer (les accents ne comptent pas)…">
    </div>
    <div class="liste" id="liste" role="listbox"></div>
    <div class="vide cache" id="vide">Rien ne correspond à ta recherche…</div>
    <div class="compte cache" id="compte"></div>
  </div>
</div>
<script>
(function () {
  "use strict";
  var OPTIONS = [], VALEUR = null, SURBRILLE = 0, VISIBLES = [], OUVERT = false;
  var ARGS_PREC = undefined, PLACEHOLDER = "—", DESACTIVE = false;

  // ---------------------------------------------------------------- accents
  // Copie exacte de cle_recherche() de menus.py : minuscules, œ → oe, accents
  // enlevés, ponctuation transformée en espaces.
  function plie(t) {
    var x = (t === null || t === undefined) ? "" : String(t);
    x = x.toLowerCase().replace(/œ/g, "oe").replace(/æ/g, "ae");
    if (x.normalize) { x = x.normalize("NFD").replace(/[\u0300-\u036f]/g, ""); }
    x = x.replace(/['’\u2019\-,()/.]/g, " ");
    return x.replace(/\s+/g, " ").trim();
  }

  function pertinence(cible, mots) {
    var entier = mots.join(" ");
    if (cible.indexOf(entier) === 0) { return [0, cible.length, cible]; }
    var parties = cible.split(" ");
    for (var i = 0; i < parties.length; i++) {
      if (parties[i].indexOf(mots[0]) === 0) { return [1, cible.length, cible]; }
    }
    if (cible.indexOf(mots[0]) === 0) { return [1, cible.length, cible]; }
    return [2, cible.length, cible];
  }

  // ≈ difflib.SequenceMatcher(...).ratio() : bigrammes communs.
  function similarite(a, b) {
    if (a === b) { return 1; }
    if (!a || !b) { return 0; }
    var A = {}, B = {}, k, i, total = 0, commun = 0;
    for (i = 0; i < a.length - 1; i++) { k = a.substr(i, 2); A[k] = (A[k] || 0) + 1; }
    for (i = 0; i < b.length - 1; i++) { k = b.substr(i, 2); B[k] = (B[k] || 0) + 1; }
    for (k in A) { total += A[k]; commun += Math.min(A[k], B[k] || 0); }
    for (k in B) { total += B[k]; }
    return total ? (2 * commun) / total : 0;
  }

  function compare(t1, t2) {
    for (var i = 0; i < t1.length; i++) {
      if (t1[i] < t2[i]) { return -1; }
      if (t1[i] > t2[i]) { return 1; }
    }
    return 0;
  }

  // LA recherche : mêmes règles que filtre_recherche() de menus.py
  function filtre(options, requete) {
    var req = plie(requete);
    if (!req) { return options.slice(); }
    var mots = req.split(" ").filter(function (m) { return m.length > 0; });
    var exacts = [], flous = [], i, j;
    for (i = 0; i < options.length; i++) {
      var o = options[i], cible = plie(o);
      if (!cible) { continue; }
      var tous = true;
      for (j = 0; j < mots.length; j++) { if (cible.indexOf(mots[j]) < 0) { tous = false; break; } }
      if (tous) {
        exacts.push([pertinence(cible, mots), o]);
        continue;
      }
      var assez_longs = true;
      for (j = 0; j < mots.length; j++) { if (mots[j].length < 4) { assez_longs = false; break; } }
      if (!assez_longs) { continue; }
      var decoupes = cible.split(" "), notes = [], ok = true;
      for (j = 0; j < mots.length; j++) {
        var note = 0;
        for (var d = 0; d < decoupes.length; d++) {
          var s = similarite(mots[j], decoupes[d]);
          if (s > note) { note = s; }
        }
        if (note < 0.75) { ok = false; break; }
        notes.push(note);
      }
      if (ok) {
        var somme = notes.reduce(function (a, b) { return a + b; }, 0);
        flous.push([[-somme / notes.length, cible.length, cible], o]);
      }
    }
    var gardes = exacts.length ? exacts : flous;
    gardes.sort(function (a, b) { return compare(a[0], b[0]); });
    return gardes.map(function (p) { return p[1]; });
  }

  // ---------------------------------------------------------------- messages
  function versStreamlit(message) {
    window.parent.postMessage(Object.assign({ isStreamlitMessage: true }, message), "*");
  }
  function envoyerValeur(valeur) {
    VALEUR = valeur;
    versStreamlit({ type: "streamlit:setComponentValue", value: valeur, dataType: "json" });
  }
  function ajusterHauteur() {
    //  la hauteur réelle du widget : on la MESURE dans la page…
    var haut = 0;
    try {
      var r = document.getElementById("racine").getBoundingClientRect();
      haut = Math.ceil(r.bottom);
      if (!haut || haut < 24) { haut = Math.ceil(document.body.scrollHeight); }
    } catch (e) { haut = 0; }
    //  …et si la mesure n'est pas possible, on prend une valeur sûre
    if (!haut || haut < 24) { haut = OUVERT ? 348 : 46; }
    versStreamlit({ type: "streamlit:setFrameHeight", height: haut + 4 });
  }

  // ---------------------------------------------------------------- affichage
  var el = {
    etiquette: document.getElementById("etiquette"),
    texte: document.getElementById("texte-etiquette"),
    aide: document.getElementById("aide"),
    boite: document.getElementById("boite"),
    valeur: document.getElementById("valeur"),
    chevron: document.getElementById("chevron"),
    panneau: document.getElementById("panneau"),
    filtre: document.getElementById("filtre"),
    liste: document.getElementById("liste"),
    vide: document.getElementById("vide"),
    compte: document.getElementById("compte")
  };

  function therme() { return el.filtre.value || ""; }

  function rendreListe() {
    VISIBLES = filtre(OPTIONS, therme());
    el.liste.innerHTML = "";
    if (SURBRILLE >= VISIBLES.length) { SURBRILLE = 0; }
    for (var i = 0; i < VISIBLES.length; i++) {
      var ligne = document.createElement("div");
      ligne.className = "ligne" + (i === SURBRILLE ? " survol" : "")
                      + (VISIBLES[i] === VALEUR ? " choisie" : "");
      ligne.setAttribute("role", "option");
      var marque = document.createElement("span");
      marque.className = "marque";
      ligne.appendChild(marque);
      var texte = document.createElement("span");
      texte.textContent = VISIBLES[i];
      ligne.appendChild(texte);
      ligne.setAttribute("data-i", String(i));
      ligne.addEventListener("mouseenter", (function (n) {
        return function () { SURBRILLE = n; rafraichirSurvol(); };
      })(i));
      ligne.addEventListener("mousedown", (function (v) {
        return function (ev) { ev.preventDefault(); choisir(v); };
      })(VISIBLES[i]));
      el.liste.appendChild(ligne);
    }
    el.vide.className = "vide" + (VISIBLES.length ? " cache" : "");
    el.compte.className = "compte" + (therme().trim() ? "" : " cache");
    el.compte.textContent = VISIBLES.length + " sur " + OPTIONS.length
                          + " (accents et majuscules ignorés)";
  }

  function rafraichirSurvol() {
    var enfants = el.liste.children;
    for (var i = 0; i < enfants.length; i++) {
      enfants[i].className = "ligne" + (i === SURBRILLE ? " survol" : "")
                           + (VISIBLES[i] === VALEUR ? " choisie" : "");
    }
    var cible = enfants[SURBRILLE];
    if (cible && cible.scrollIntoView) { cible.scrollIntoView({ block: "nearest" }); }
  }

  function montrerValeur() {
    var v = (VALEUR === null || VALEUR === undefined || VALEUR === "") ? null : VALEUR;
    el.valeur.textContent = v === null ? PLACEHOLDER : v;
    el.valeur.className = "valeur" + (v === null ? " vide" : "");
  }

  function ouvrir() {
    if (DESACTIVE) { return; }
    OUVERT = true;
    el.boite.className = "boite ouvert";
    el.panneau.className = "panneau";
    el.filtre.value = "";
    var i = OPTIONS.indexOf(VALEUR);
    SURBRILLE = i >= 0 ? i : 0;
    rendreListe();
    ajusterHauteur();
    setTimeout(function () { el.filtre.focus(); }, 10);
  }

  function fermer() {
    OUVERT = false;
    el.boite.className = "boite";
    el.panneau.className = "panneau cache";
    ajusterHauteur();
  }

  function choisir(valeur) {
    envoyerValeur(valeur);
    montrerValeur();
    fermer();
  }

  el.boite.addEventListener("mousedown", function (ev) {
    ev.preventDefault();
    if (OUVERT) { fermer(); } else { ouvrir(); }
    el.boite.focus();
  });
  el.boite.addEventListener("keydown", function (ev) {
    if (ev.key === "Enter" || ev.key === " " || ev.key === "ArrowDown") {
      ev.preventDefault();
      if (!OUVERT) { ouvrir(); }
    }
  });
  el.filtre.addEventListener("input", function () { SURBRILLE = 0; rendreListe(); ajusterHauteur(); });
  el.filtre.addEventListener("keydown", function (ev) {
    if (ev.key === "ArrowDown" || ev.key === "ArrowUp") {
      ev.preventDefault();
      if (!VISIBLES.length) { return; }
      SURBRILLE = (SURBRILLE + (ev.key === "ArrowDown" ? 1 : VISIBLES.length - 1)) % VISIBLES.length;
      rafraichirSurvol();
    } else if (ev.key === "Enter") {
      ev.preventDefault();
      if (VISIBLES.length) { choisir(VISIBLES[Math.min(SURBRILLE, VISIBLES.length - 1)]); }
    } else if (ev.key === "Escape") {
      ev.preventDefault();
      fermer();
      el.boite.focus();
    }
  });
  // clic ailleurs dans la page : le widget se referme tout seul
  window.addEventListener("blur", function () { if (OUVERT) { fermer(); } });
  document.addEventListener("click", function (ev) {
    if (OUVERT && !el.racine_bis && ev.target && !el.panneau.contains(ev.target)
        && !el.boite.contains(ev.target)) { fermer(); }
  });

  // ---------------------------------------------------------------- thème
  function appliquerTheme(theme) {
    if (!theme) { return; }
    var r = document.documentElement.style;
    if (theme.backgroundColor) { r.setProperty("--fond", theme.backgroundColor); }
    if (theme.textColor) { r.setProperty("--texte", theme.textColor); }
    if (theme.primaryColor) { r.setProperty("--primaire", theme.primaryColor); }
    var bg = theme.backgroundColor || "#ffffff";
    var sombre = false;
    if (/^#?[0-9a-f]{6}$/i.test(bg.replace("#", ""))) {
      var n = parseInt(bg.replace("#", ""), 16);
      var lum = (0.299 * ((n >> 16) & 255) + 0.587 * ((n >> 8) & 255) + 0.114 * (n & 255)) / 255;
      sombre = lum < 0.5;
    }
    if (sombre) {
      r.setProperty("--bord", "rgba(255,255,255,.22)");
      r.setProperty("--bord-fonce", "rgba(255,255,255,.45)");
      r.setProperty("--doux", "rgba(255,255,255,.6)");
      r.setProperty("--survol", "rgba(255,255,255,.10)");
    }
    if (theme.secondaryBackgroundColor) { r.setProperty("--survol", theme.secondaryBackgroundColor); }
  }

  // ---------------------------------------------------------------- rendu reçu
  function surMessage(ev) {
    var d = ev.data;
    if (!d || d.type !== "streamlit:render") { return; }
    var args = d.args || {};
    appliquerTheme(d.theme);
    DESACTIVE = !!d.disabled;
    PLACEHOLDER = args.placeholder || "—";
    var options = args.options || [];
    var premiere = (ARGS_PREC === undefined);
    var change = premiere || (args.value !== ARGS_PREC.value);
    ARGS_PREC = { value: args.value };
    OPTIONS = options;
    if (change && args.value !== undefined && args.value !== null
        && OPTIONS.indexOf(args.value) >= 0) {
      VALEUR = args.value;                  // valeur imposée par l'application
    }
    if (VALEUR !== null && OPTIONS.indexOf(VALEUR) < 0) { VALEUR = null; }
    if (args.label !== undefined) { el.texte.textContent = args.label; }
    if (args.aide) { el.aide.title = args.aide; el.aide.style.display = ""; }
    else { el.aide.style.display = "none"; }
    el.boite.style.opacity = DESACTIVE ? "0.5" : "1";
    el.boite.style.cursor = DESACTIVE ? "not-allowed" : "pointer";
    if (OUVERT) { rendreListe(); }
    montrerValeur();
    ajusterHauteur();
    if (!rendreListe.__initialise) { rendreListe.__initialise = true; }
  }

  window.addEventListener("message", surMessage);
  versStreamlit({ type: "streamlit:componentReady", apiVersion: 1 });
  if (window.ResizeObserver) {
    new ResizeObserver(function () { ajusterHauteur(); }).observe(document.body);
  }
  ajusterHauteur();

  //  tests automatisés (node) : on expose la logique de recherche
  window.__suivi_liste = { plie: plie, filtre: filtre, similarite: similarite };
})();
</script>
</body>
</html>
"""

_COMPOSANT = None
_COMPOSANT_ERREUR = ""


def _ecrire_le_widget() -> str:
    """Écrit la page du widget dans un dossier temporaire et renvoie le dossier."""
    import os
    import tempfile
    dossier = os.path.join(tempfile.gettempdir(), "equilibre_liste")
    os.makedirs(dossier, exist_ok=True)
    chemin = os.path.join(dossier, "index.html")
    try:
        deja = open(chemin, encoding="utf-8").read()
    except OSError:
        deja = None
    if deja != _HTML_LISTE:
        with open(chemin, "w", encoding="utf-8") as f:
            f.write(_HTML_LISTE)
    return dossier


def _composant_liste():
    """Le widget, créé une seule fois. Renvoie None si ce n'est pas possible."""
    global _COMPOSANT, _COMPOSANT_ERREUR
    if _COMPOSANT is not None:
        return _COMPOSANT
    if _COMPOSANT_ERREUR:
        return None
    try:
        from streamlit.components.v1 import declare_component
        _COMPOSANT = declare_component("liste_chercheuse", path=_ecrire_le_widget())
    except Exception as e:                      # pragma: no cover - filet de sécurité
        _COMPOSANT_ERREUR = f"{type(e).__name__}: {e}"[:200]
        _COMPOSANT = None
    return _COMPOSANT


def _liste_native_pour_les_tests() -> bool:
    """Vrai quand on fait tourner l'application sans navigateur (tests automatiques).

    Les tests ne peuvent pas cliquer dans un composant ; ils utilisent alors la
    liste déroulante de Streamlit, avec EXACTEMENT les mêmes options. Pour la
    vraie recherche (accents ignorés), ce sont les tests de `filtre_recherche`
    (Python) et du JavaScript du widget qui tranchent.
    """
    import os
    return os.environ.get("SUIVI_LISTE_NATIVE", "") not in ("", "0", "non")


def chercheur(label: str, options, cle: str, terme: str | None = None,
              valeur: str | None = None, nombre: int = 20,
              libelle_recherche: str | None = None, aide: str = "",
              type_element: str = "choix", encadre: bool = True,
              cle_liste: str | None = None, horizontal: bool = False,
              garder_valeur: bool = True) -> str | None:
    """LA liste déroulante qui cherche toute seule : le seul module de recherche.

    Renvoie la ligne choisie (un texte), ou None tant que rien n'est choisi.
    On l'appelle comme avant — les anciens réglages (`nombre`, `terme`,
    `libelle_recherche`, `type_element`, `encadre`, `horizontal`) ne servent
    plus : il n'y a plus de case 🔍 à côté de la liste, tout est dedans.
    """
    import streamlit as st
    options = [str(o) for o in (options or [])]
    if not options:
        st.info(f"Aucune option disponible pour « {label} ».")
        return None

    #  ce qui était déjà choisi (une recette à modifier, l'ingrédient d'une ligne…)
    defaut = None
    if garder_valeur and valeur is not None and str(valeur) in options:
        defaut = str(valeur)
    cle_liste = cle_liste or cle

    if _liste_native_pour_les_tests():          # tests automatiques (pas de navigateur)
        index = options.index(defaut) if defaut in options else 0
        return st.selectbox(label, options, index=index, key=cle_liste, help=aide or None)

    widget = _composant_liste()
    if widget is None:                          # repli : le widget n'a pas pu se créer
        st.caption(f"⚠️ {_COMPOSANT_ERREUR or 'widget indisponible'}")
        index = options.index(defaut) if defaut in options else 0
        return st.selectbox(label, options, index=index, key=cle_liste, help=aide or None)

    retour = widget(options=options, value=defaut, label=label, aide=aide,
                    placeholder="— Choisir —", key=cle_liste, default=defaut)
    if retour is None:
        return None
    retour = str(retour)
    return retour if retour in options else None


def selecteur_recherche(label: str, options, cle_etat: str, **reste):
    """Ancien nom, gardé pour les pages qui l'appelaient : c'est le même module.

    Il n'existe qu'un seul module de recherche dans toute l'application :
    `chercheur`. Celui-ci ne fait que l'appeler.
    """
    return chercheur(label, options, cle_etat, **reste)


#  Unités proposées quand il ajoute un ingrédient à un repas (30/09)
UNITES_SAISIE = ["unité", "g", "kg", "ml", "cl", "l", "tranche", "gousse",
                 "tranche(s)", "boîte", "sachet", "barquette", "pot", "botte",
                 "filet", "verre", "c. à soupe", "c. à café", "pincée", "portion"]


def unite_par_defaut(ing: dict | None) -> str:
    """L'unité proposée pour un ingrédient — celle qu'on écrit naturellement.

    • un aliment qui se compte (œuf, cordon bleu, tranche de jambon) → « unité » ;
    • un aliment vendu au poids mais qu'on compte (steak haché 125 g, courgette
      200 g) → « unité » aussi : quand il tape « 4 », il pense 4 steaks, et
      l'application convertit en 500 g pour la liste de courses ;
    • le reste → son unité d'achat (g, ml, boîte…).
    """
    ing = ing or {}
    u = unite_propre(ing.get("unite_liste_courses") or ing.get("unit")) or "g"
    if u.lower() in ("g", "gr", "gramme", "grammes", "kg", "ml", "cl", "l"):
        try:
            poids = float(ing.get("poids_piece_g") or 0)
        except (TypeError, ValueError):
            poids = 0.0
        if 25 <= poids <= 400:
            return "unité"
    return u


def unites_proposees(ing: dict | None) -> list:
    """Les unités qui ont du SENS pour cet aliment (rien d'inutile proposé).

    • steak haché (vendu au poids, 125 g la pièce) → unité, g, kg…
    • pâtes → g, kg (+ cuillères) : « 3 unités de pâtes » ne veut rien dire
    • cordon bleu → unité, tranche… : on n'achète pas des grammes de cordon bleu
    La première de la liste est celle qu'on propose par défaut.
    """
    ing = ing or {}
    u = unite_par_defaut(ing)
    bas = _sans_accent(u).strip()
    try:
        poids = float(ing.get("poids_piece_g") or 0)
    except (TypeError, ValueError):
        poids = 0.0
    grands = ("unite", "tranche", "gousse", "boite", "sachet", "pot", "barquette",
              "botte", "filet", "verre", "portion")
    masse = ("g", "gramme", "grammes", "kg", "kilo", "kilos")
    volume = ("ml", "cl", "l", "litre", "litres")
    choix = [u, "convives"]     # unite "convives" = portion par personne
    if bas in grands:
        choix += ["unité", "tranche", "gousse", "boîte", "sachet", "pot", "portion"]
    if bas in masse or (bas in ("", "?") and not poids):
        choix += ["g", "kg"]
    if bas in volume:
        choix += ["ml", "cl", "l"]
    if poids > 0:                        # on peut toujours dire « 4 unités »
        choix += ["unité", "g"]
    if bas not in volume and poids <= 0 and bas not in masse:
        choix += ["g", "kg"]
    choix += ["c. à soupe", "c. à café", "pincée"]
    vus, propre = set(), []
    for c in choix:
        c = unite_propre(c)
        if c and c.lower() not in vus:
            vus.add(c.lower())
            propre.append(c)
    return propre


# ===========================================================================
#  UNITÉ « CONVIVES » — combien acheter pour N personnes  (demandé le 30/09)
#
#  Il choisit « convives » comme unité et écrit 3 : l'application multiplie par
#  la portion recommandée pour UNE personne, puis traduit dans l'unité de la
#  liste de courses (g, kg, unités…).
#
#  D'où viennent les portions ? Dans l'ordre :
#    1. les repères ci-dessous (grammages par personne du guide courant) ;
#    2. sinon, la MOYENNE de ses propres recettes (ses quantités pour 4 parts ÷ 4) ;
#    3. sinon la portion du rayon (200 g de légumes, 130 g de viande…).
#  La source est écrite dans l'aperçu : il sait toujours d'où vient le chiffre.
# ===========================================================================
PORTION_PERSONNE_G = {                 # portions « repère » par mot-clé
    "oeuf": 110,                       # 2 œufs
    "steak": 130, "boeuf": 130, "veau": 130, "porc": 130, "agneau": 130,
    "poulet": 130, "dinde": 130, "escalope": 130, "saucisse": 120, "chipolata": 120,
    "cordon bleu": 100, "nugget": 100, "lardon": 50, "jambon": 50, "saucisson": 40,
    "poisson": 130, "cabillaud": 130, "saumon": 130, "colin": 130, "merlu": 130,
    "maquereau": 120, "sardine": 100, "thon": 100, "crevette": 100, "tofu": 130,
    "gnocchi": 150, "raviole": 150, "quenelle": 150, "nouille": 80, "lasagne": 200,
    "lentille": 70, "pois chiche": 70, "flageolet": 70, "haricot sec": 70,
    "polenta": 80, "pomme de terre": 200, "patate douce": 200,
    "riz": 80, "semoule": 80, "quinoa": 80, "boulgour": 80, "pate": 80,
    "comte": 40, "emmental": 40, "parmesan": 25, "chevre": 40, "mozzarella": 60,
    "feta": 40, "fromage blanc": 150, "fromage": 40, "yaourt": 125, "skyr": 150,
    "creme": 50, "beurre": 10, "huile": 10, "margarine": 10,
    "lait": 200, "jus": 200, "soda": 250, "cafe": 200, "the": 200, "boisson": 250,
    "pain de mie": 60, "pain": 60, "baguette": 60, "biscotte": 30, "cereale": 40,
    "sucre": 20, "confiture": 20, "miel": 20, "chocolat": 20, "biscuit": 30,
    "amande": 20, "noix": 20, "cacahuete": 20, "compote": 100, "fruit": 150,
    "salade": 100, "crudite": 100, "tomate": 150, "concombre": 100, "carotte": 150,
    "courgette": 200, "aubergine": 200, "haricot vert": 150, "epinard": 150,
    "champignon": 150, "brocoli": 150, "betterave": 100, "oignon": 50, "petits pois": 150,
    "soupe": 250, "gratin": 250, "quiche": 200, "pizza": 200, "tarte": 150,
    "croque": 150, "sauce": 30, "mayonnaise": 20, "ketchup": 20, "moutarde": 10,
    "vinaigre": 10, "sel": 3, "poivre": 2, "epice": 2, "ail": 3, "persil": 5,
    "herbe": 5, "bouillon": 5, "levure": 3, "farine": 60, "maizena": 10,
}
PORTION_RAYON_G = {                    # si aucun mot-clé ne correspond
    "Boucherie & Poissonnerie": 130,
    "Fruits & Légumes": 200,
    "Frais & Produits Laitiers": 40,
    "Épicerie Salée": 80,
    "Épicerie Sucrée": 25,
    "Surgelés": 150,
    "Boissons": 250,
    "Autre": 100,
}
PORTION_DEFAUT_G = 100                 # rien de connu : 100 g par personne


def portion_personne(ing: dict | None, lignes=None, recettes=None) -> tuple:
    """Portion recommandée pour UNE personne : (grammes, « d'où ça vient »).

    1. le repère par mot-clé (« steak » → 130 g, « pâtes » → 80 g…) ;
    2. sinon la moyenne de ses recettes (ses quantités pour 4 parts ÷ 4) ;
    3. sinon la portion du rayon (200 g de légumes, 130 g de viande…).
    """
    ing = ing or {}
    nom = _sans_accent(f"{ing.get('nom_affiche') or ''} {ing.get('name') or ''}")
    # on cherche des MOTS ENTIERS (sinon « Boeuf » contenait « oeuf » !) ;
    # le mot qui arrive LE PLUS À GAUCHE gagne, le plus long en cas d'égalité
    # (« Thon à la tomate » → thon, pas tomate ; « Pain de mie » → pain de mie)
    trouves = []
    for mot in PORTION_PERSONNE_G:
        m = re.search(r"\b" + _sans_accent(mot) + r"s?\b", nom)
        if m:
            trouves.append((m.start(), -len(mot), mot))
    if trouves:
        mot = min(trouves)[2]
        return float(PORTION_PERSONNE_G[mot]), f"repère « {mot} »"
    if lignes and recettes:                       # 2) ses propres recettes
        # « lignes » arrive en dictionnaire par recette (application) ou en liste
        # plate (fiche PDF) : on accepte les deux.
        liste = (list(lignes) if isinstance(lignes, (list, tuple))
                 else [l for v in lignes.values() for l in (v or [])])
        tot, nb = 0.0, 0
        for l in liste:
            if str(l.get("ingredient_id")) != str(ing.get("id")):
                continue
            rec = (recettes or {}).get(l.get("recipe_id")) or {}
            parts = _nombre(rec.get("base_servings")) or 4.0
            try:
                import pdf_menus as PM
                g = PM.convert_to_unit(_nombre(l.get("quantity")),
                                       l.get("unit") or ing.get("unit"),
                                       "g", ing.get("poids_piece_g"))
            except Exception:
                g = _nombre(l.get("quantity"))
            if g and parts:
                tot += float(g) / float(parts)
                nb += 1
        if nb and tot > 0:
            return tot / nb, f"moyenne de tes recettes ({nb} recette{'s' if nb > 1 else ''})"
    rayon = ing.get("category") or "Autre"
    return float(PORTION_RAYON_G.get(rayon, PORTION_DEFAUT_G)), f"portion du rayon {rayon}"


def portion_en_unites(portion_g: float, ing: dict | None) -> str:
    """« 110 g » → « ≈ 2 unités » quand l'aliment se compte (œufs…)."""
    ing = ing or {}
    try:
        poids = float(ing.get("poids_piece_g") or 0)
    except (TypeError, ValueError):
        poids = 0.0
    if poids > 0:
        return f"≈ {portion_g / poids:.1f} unité".replace(".0", "")
    return f"{portion_g:g} g"


def borne(valeur, mini, maxi, defaut=None):
    """Ramène une valeur dans les bornes d'une case.

    Les valeurs viennent de la base : elles peuvent être absentes, vides ou hors
    bornes (0, 300 g…). Sans ce garde-fou, Streamlit refuse de dessiner la page
    entière (« value 0 is less than the min_value 80 »). Vérifié le 30/09.
    """
    try:
        v = float(valeur)
    except (TypeError, ValueError):
        v = None
    if v is None or v != v:                      # aucune valeur, ou NaN
        return mini if defaut is None else defaut
    return min(max(v, float(mini)), float(maxi))


def unite_propre(unite) -> str:
    """Ramène « pièce », « pièces », « piece(s) », « unités »… à « unité ».

    Une seule écriture pour l'utilisateur : « unité » (et « unités » au pluriel).
    """
    u = str(unite or "").strip()
    if not u:
        return ""
    c = _sans_accent(u)
    if c in ("piece", "pieces", "unite", "unites", "unite(s)", "piece(s)", "u"):
        return "unité"
    return u


def _convertir(q, u_source, u_cible, poids=None) -> float:
    """Convertit une quantité vers l'unité de la liste de courses.

    « 6 unités » de pommes de terre (100 g l'unité) → 600 g. Sans ça, on
    additionnait des grammes avec des unités (« 310 unités »). Jamais None.
    """
    try:
        import pdf_menus as PM
        v = PM.convert_to_unit(q, u_source, u_cible, poids)
        return float(v) if v is not None else float(q or 0)
    except Exception:
        return float(q or 0)


def nom_court(ing: dict | None) -> str:
    """Nom familier s'il existe (« Boeuf haché »), sinon le nom complet de la base."""
    ing = ing or {}
    return ing.get("nom_affiche") or ing.get("name") or "?"


def _vider() -> dict:
    return {c: 0.0 for c in CHAMPS_NUTR}


def _ajouter(totaux: dict, valeur_100g, grammes: float, champ: str):
    v = valeur_nutriment(valeur_100g)
    if v is not None and grammes > 0:
        totaux[champ] += v * grammes / 100.0


def calculer_recette(lignes: list[dict], ing_par_id: dict, base_servings=None,
                     nom_recette=None) -> dict:
    """Calcule les macros sans assimiler une valeur inconnue à zéro.

    Les totaux numériques restent des sommes partielles pour compatibilité ;
    ``complet`` et ``champs_manquants`` disent explicitement si chaque macro
    peut être interprétée comme un total fiable.
    """
    pseudo = est_pseudo_ingredient(nom_recette)
    total = _vider()
    poids = 0.0
    detail = []
    estimees = []
    manquants = {c: set() for c in CHAMPS_NUTR}
    if not lignes:
        for c in CHAMPS_NUTR:
            manquants[c].add("aucune ligne d'ingrédient")

    for l in lignes:
        ing = ing_par_id.get(l.get("ingredient_id")) or {}
        nom = nom_court(ing) if ing else "aliment introuvable dans la base"
        g, estime = grammes_de_ligne(l, ing, pseudo)
        if estime:
            estimees.append(nom)
        poids += g

        qte = _nombre(l.get("quantity"))
        quantite_inconnue = qte > 0 and g <= 0
        valeurs = {}
        manquants_ligne = []
        for champ in CHAMPS_NUTR:
            valeur = valeur_nutriment(ing.get(f"{champ}_100g"))
            valeurs[champ] = valeur
            if valeur is None or quantite_inconnue:
                raison = f"{nom} (quantité non convertible)" if quantite_inconnue else nom
                manquants[champ].add(raison)
                manquants_ligne.append(champ)
            else:
                _ajouter(total, valeur, g, champ)

        detail.append(dict(
            nom=ing.get("name"), nom_court=nom, grammes=round(g, 1),
            unite=l.get("unit"), quantite=qte,
            kcal=round((valeurs["kcal"] or 0.0) * g / 100.0, 1),
            proteines=round((valeurs["proteines"] or 0.0) * g / 100.0, 1),
            glucides=round((valeurs["glucides"] or 0.0) * g / 100.0, 1),
            lipides=round((valeurs["lipides"] or 0.0) * g / 100.0, 1),
            sans_valeurs=all(valeurs[c] is None for c in CHAMPS_NUTR),
            champs_manquants=manquants_ligne, estime=estime,
            quantite_non_convertie=quantite_inconnue))

    parts = _nombre(base_servings) or 1.0
    par_part = {c: total[c] / parts for c in CHAMPS_NUTR}
    champs_manquants = {c: sorted(noms) for c, noms in manquants.items()}
    complet = {c: not champs_manquants[c] for c in CHAMPS_NUTR}
    inconnues = sorted({nom for noms in champs_manquants.values() for nom in noms})
    return dict(total={c: round(total[c], 1) for c in CHAMPS_NUTR},
                par_part={c: round(par_part[c], 1) for c in CHAMPS_NUTR},
                poids_g=round(poids, 1), parts=parts,
                lignes=detail, inconnues=inconnues,
                estimees=sorted(set(estimees)), complet=complet,
                champs_manquants=champs_manquants,
                approximatif=bool(estimees))


# ---------------------------------------------------------------------------
#  RETROUVER LES MACROS D'UNE ANCIENNE LIGNE DU JOURNAL
# ---------------------------------------------------------------------------
#  Quand « Glucides » affiche 0 g alors que des repas sont enregistrés, c'est
#  que la ligne a été saisie avant l'ajout des colonnes glucides/lipides.
#  On relit son libellé et on retrouve les valeurs dans la base.

_RE_SUFFIXE = re.compile(
    r"\s*\((?:menu|\d+(?:[.,]\d+)?\s*parts?|\d+(?:[.,]\d+)?\s*portions?"
    r"|\d+(?:[.,]\d+)?\s*g servis|\d+(?:[.,]\d+)?\s*%\s*du plat)\)\s*$",
    re.IGNORECASE)
_RE_DEBUT_QTE = re.compile(r"^\s*(\d+(?:[.,]\d+)?)\s*(.*)$")

#  ce qui suit un nombre et qui est une unité, pas un aliment
UNITES_ECRITES = {
    "g": "g", "gr": "g", "gramme": "g", "grammes": "g", "kg": "kg",
    "ml": "ml", "cl": "cl", "l": "l", "litre": "l", "litres": "l",
    "unite": "unité", "unites": "unité", "unité": "unité", "unités": "unité",
    "piece": "unité", "pieces": "unité", "pièce": "unité", "pièces": "unité",
    "tranche": "tranche", "tranches": "tranche", "gousse": "gousse",
    "gousses": "gousse", "boite": "boîte", "boîtes": "boîte", "boite": "boîte",
    "sachet": "sachet", "sachets": "sachet", "pot": "pot", "pots": "pot",
    "verre": "verre", "verres": "verre", "pincee": "pincée", "pincée": "pincée",
    "c": "c. à c.", "cuillere": "cuillère", "cuillères": "cuillère",
}


def _sans_accent(t: str) -> str:
    import unicodedata
    t = str(t or "").lower().replace("œ", "oe").replace("æ", "ae")
    t = unicodedata.normalize("NFD", t)
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def _mots_ordonnes(t: str) -> list:
    """Mots significatifs, dans l'ordre (« fromage blanc » → [fromage, blanc])."""
    out = []
    for mot in re.split(r"[^a-z0-9]+", _sans_accent(t)):
        if len(mot) > 2:
            out.append(mot[:-1] if len(mot) > 4 and mot.endswith("s") else mot)
    return out


def _mots(t: str) -> set:
    """Mots utiles d'un libellé (pluriel simplifié : « oeufs » → « oeuf »)."""
    out = set()
    for m in re.split(r"[^a-z0-9]+", _sans_accent(t)):
        if len(m) > 2:
            out.add(m[:-1] if len(m) > 4 and m.endswith("s") else m)
    return out


def _proche(libelle: str, candidat: str) -> float:
    """Ressemblance entre un libellé et un nom, de 0 à 1.

    On mesure la part du LIBELLÉ qui est couverte par le nom : « poulet/dinde »
    face à « Poulet, filet sans peau cru » → la moitié des mots du libellé.
    """
    a, b = _mots(libelle), _mots(candidat)
    if not a or not b:
        return 0.0
    score = len(a & b) / len(a)
    if _sans_accent(candidat).startswith(_sans_accent(libelle)[:12]):
        score += 0.3
    return round(min(score, 1.3), 3)


def _macros_recette(base: str, qty, recettes, lignes_par_recette, ings, coherents_seuls=True):
    """Essaie chaque recette ressemblante et garde celle qui colle aux protéines."""
    parts = max(_nombre(qty) or 1.0, 1.0)
    essais = []
    for r in recettes.values():
        sc = _proche(base, r.get("name") or "")
        if sc < 0.5:
            continue
        c = calculer_recette(lignes_par_recette.get(r["id"], []), ings,
                             r.get("base_servings"), nom_recette=r.get("name"))
        if not all(c.get("complet", {}).get(k, False)
                   for k in ("proteines", "glucides", "lipides")):
            continue
        essais.append(dict(score=sc, source=f"recette « {r['name']} »",
                           glucides=round(c["par_part"]["glucides"] * parts, 1),
                           lipides=round(c["par_part"]["lipides"] * parts, 1),
                           proteines=round(c["par_part"]["proteines"] * parts, 1),
                           detail=f"{c['par_part']['glucides']:.0f} g G et "
                                  f"{c['par_part']['lipides']:.0f} g L par part"))
    essais.sort(key=lambda x: -x["score"])
    return essais


def _macros_aliment(base: str, ings):
    """« 180 g poulet / dinde », « 3 œufs durs », « 150 g skyr »…"""
    m = _RE_DEBUT_QTE.match(base or "")
    if not m:
        return []
    q = _nombre(m.group(1))
    reste = (m.group(2) or "").strip()
    if not q or not reste:
        return []
    # le premier mot est-il une unité écrite (« g », « tranches »…) ?
    premier = _sans_accent(reste.split()[0]).strip(".,")
    unite = UNITES_ECRITES.get(premier)
    nom = reste.split(" ", 1)[1].strip() if unite and " " in reste else reste
    if not unite and re.match(r"^(oeuf)", _sans_accent(nom)):
        unite = "unité"                       # « 3 œufs » : on compte en pièces
    premiers = _mots_ordonnes(nom)
    if not premiers:
        return []
    essais = []
    for i in ings.values():
        cible = _mots_ordonnes(i.get("name") or "")
        # le mot PRINCIPAL du libellé doit correspondre au mot principal de
        # l'aliment : « fromage blanc » ne doit pas tomber sur « riz blanc ».
        if not cible or cible[0] != premiers[0]:
            continue
        sc = _proche(nom, i.get("name") or "")
        if sc < 0.5 or any(not nutriment_present(i.get(f"{champ}_100g"))
                           for champ in ("proteines", "glucides", "lipides")):
            continue
        g = quantite_en_grammes(q, unite or i.get("unit"), i)
        if not g:
            continue
        essais.append(dict(score=sc, source=f"{g:.0f} g de « {nom_court(i)} »",
                           glucides=round(_nombre(i.get("glucides_100g")) * g / 100.0, 1),
                           lipides=round(_nombre(i.get("lipides_100g")) * g / 100.0, 1),
                           proteines=round(_nombre(i.get("proteines_100g")) * g / 100.0, 1),
                           detail=f"{g:.0f} g reconstitués"))
    essais.sort(key=lambda x: -x["score"])
    return essais


def deviner_macros(libelle: str, qty, proteines_connues, recettes, lignes_par_recette, ings):
    """Propose (glucides, lipides) pour une ligne de journal, avec vérification.

    Renvoie None si rien de cohérent n'a été trouvé : on ne devine jamais.
    La proposition retenue est celle dont les protéines recalculées collent le
    mieux à celles déjà enregistrées (±25 %, ou ±4 g).
    """
    base = _RE_SUFFIXE.sub("", str(libelle or "")).strip() or str(libelle or "")
    connues = _nombre(proteines_connues)

    # on essaie le libellé tel quel, puis à partir du premier chiffre
    # (utile si la ligne commence par un mot en trop : « Repas : 180 g poulet »)
    variantes = [base]
    m_chiffre = re.search(r"\d", base)
    if m_chiffre and m_chiffre.start() > 0:
        variantes.append(base[m_chiffre.start():])
    essais = []
    for v in variantes:
        essais += _macros_recette(v, qty, recettes, lignes_par_recette, ings)
        essais += _macros_aliment(v, ings)
    if not essais:
        return None

    def ecart(e):
        return abs(e["proteines"] - connues) if connues else 0.0

    # On n'accepte que si les protéines recalculées sont TRÈS proches de celles
    # enregistrées (12 % ou 2 g). C'est ce qui évite les fausses pistes :
    # « 200 g fromage blanc » ne tombe pas sur un autre fromage au hasard.
    valides = [e for e in essais
               if not connues or (ecart(e) <= max(2.0, 0.12 * connues) and e["score"] >= 0.4)]
    if valides:
        valides.sort(key=lambda e: (-e["score"], ecart(e)))
        e = dict(valides[0])
        e["coherent"] = True
        e["confiance"] = "sûre"
        e["ecart_proteines"] = round(ecart(e), 1)
        return e
    # 2) rien de cohérent : on ne propose rien (mieux vaut ne rien écrire)
    return None


def ma_part(calcul: dict, mode: str = "parts", valeur: float = 1.0,
            portion_foyer: float = 1.0) -> dict:
    """Calcule les macros de « ma part » de 3 façons possibles.

    mode « parts »     : valeur = nombre de parts prises (défaut 1)
    mode « pourcent »  : valeur = part du plat en % (défaut 25 % = 1 part sur 4)
    mode « poids »     : valeur = poids servi en grammes
    portion_foyer      : part d'un adulte dans le plat (les enfants comptant moins),
                         sert seulement au mode « pourcent » par défaut.

    Renvoie {fraction, macros, libelle}.
    """
    parts = calcul.get("parts") or 1.0
    mode = (mode or "parts").strip().lower()

    if mode.startswith("poids"):
        g = max(0.0, _nombre(valeur))
        poids = calcul.get("poids_g") or 0.0
        fraction = (g / poids) if poids else 0.0
        libelle = f"{g:.0f} g servis"
    elif mode.startswith("pour") or mode == "%":
        fraction = max(0.0, _nombre(valeur)) / 100.0
        libelle = f"{_nombre(valeur):.0f} % du plat"
    else:  # parts
        n = max(0.0, _nombre(valeur))
        fraction = n / parts if parts else 0.0
        libelle = f"{n:g} part" + ("s" if n > 1 else "")

    macros = {c: round(calcul["total"][c] * fraction, 1) for c in CHAMPS_NUTR}
    return dict(fraction=fraction, macros=macros, libelle=libelle,
                complet=dict(calcul.get("complet") or {c: False for c in CHAMPS_NUTR}),
                approximatif=bool(calcul.get("approximatif")),
                grammes=round((calcul.get("poids_g") or 0) * fraction, 1))


DESSERTS = ("glace", "sorbet", "yaourt", "fromage blanc", "compote", "fruit", "gâteau",
            "gateau", "crème", "creme", "chocolat", "tarte", "quatre-quarts", "biscuit")
PLATS_LEGERS = ("salade", "soupe", "velouté", "veloute", "potage", "crudité", "crudite")


def part_defaut(base_servings, nom: str = "", moment: str = "") -> float:
    """Nombre de parts proposé par défaut, selon ce qu'est le plat.

    • un dessert ou un laitage      → 0,5 part (on en mange moins)
    • une soupe ou une salade       → 1 part
    • un plat principal             → 1 part
    C'est une proposition : tu peux toujours la changer en un appui.
    """
    n = (nom or "").lower()
    if any(m in n for m in DESSERTS):
        return 0.5
    return 1.0


def portion_foyer(adultes: float = 2.0, enfants: float = 2.0,
                  coef_enfant: float = 0.6) -> float:
    """Portions mangées par la famille, en équivalents « part d'adulte ».

    Chez toi : 2 adultes + 2 enfants × 0,6  →  3,2 portions.
    Une recette recadrée sur 4 parts laisse donc un petit reste (ou une part
    plus généreuse) : c'est normal et c'est voulu.
    """
    return adultes + enfants * coef_enfant


# ---------------------------------------------------------------------------
#  ACCÈS AUX DONNÉES
# ---------------------------------------------------------------------------
TABLES = ("ingredients", "recipes", "recipe_ingredients", "planned_meals")
PAGE_SUPABASE = 1000  # Supabase ne renvoie que 1 000 lignes par requête


class MenusStore:
    """Lecture de la base de menus (tes 4 tables), avec pagination complète.

    Fonctionne de deux façons :
      • client = le client Supabase connecté  → tes vraies données
      • client = None                          → données de démonstration locales
    """

    def __init__(self, client=None):
        self.client = client
        self._cache: dict[str, list] = {}
        self.erreur: str | None = None

    @property
    def erreurs(self) -> list[str]:
        """Toutes les erreurs de lecture rencontrées (pour le diagnostic)."""
        e = getattr(self, "erreur", None)
        return [e] if e else []

    # -- outils
    def _tous(self, table: str, colonnes: str = "*", ordre: str | None = None) -> list[dict]:
        """Lit toute une table, en entier (Supabase ne renvoie que 1 000 lignes à la fois).

        On demande TOUJOURS toutes les colonnes (« * ») : c'est ce qui manquait —
        une colonne demandée par erreur empêchait de retrouver les identifiants.
        """
        # garde-fous : un argument mal passé ne doit JAMAIS casser une lecture
        if not isinstance(colonnes, str) or not colonnes.strip():
            colonnes = "*"
        if not isinstance(ordre, str) or not ordre.strip():
            ordre = None
        if table in self._cache:
            return self._cache[table]
        if self.client is None:
            return []
        lignes: list[dict] = []
        debut = 0
        echec = None
        while True:
            try:
                q = self.client.table(table).select(colonnes)
                if ordre:
                    q = q.order(ordre)
                if debut == 0:
                    # 1re page : on demande simplement « les N premières lignes »
                    res = q.limit(PAGE_SUPABASE).execute()
                else:
                    res = q.range(debut, debut + PAGE_SUPABASE - 1).execute()
                lot = res.data or []
            except Exception as e:                       # table absente, droits, réseau…
                echec = f"{table} : {type(e).__name__} — {e}"
                break
            if not lot:
                break
            lignes.extend(lot)
            if len(lot) < PAGE_SUPABASE:
                break
            debut += PAGE_SUPABASE
        if echec:
            # IMPORTANT : on ne met JAMAIS une lecture ratée en cache.
            # C'est ce qui affichait « 0 ligne » alors que la base répondait bien.
            self.erreur = echec
            return lignes
        self._cache[table] = lignes
        return lignes

    def vider_cache(self):
        self._cache.clear()
        self.erreur = None

    # -- collections
    def ingredients(self) -> list[dict]:
        return self._tous("ingredients", "*", order_col("ingredients"))

    def recettes(self) -> list[dict]:
        return self._tous("recipes", "*", order_col("recipes"))

    def lignes(self) -> list[dict]:
        return self._tous("recipe_ingredients", "*", order_col("recipe_ingredients"))

    def planning(self) -> list[dict]:
        return self._tous("planned_meals", "*", order_col("planned_meals"))

    # -- index
    def ing_par_id(self) -> dict:
        return {i.get("id"): i for i in self.ingredients()}

    def recette_par_id(self) -> dict:
        return {r.get("id"): r for r in self.recettes()}

    def lignes_par_recette(self) -> dict:
        out: dict = {}
        for l in self.lignes():
            out.setdefault(l.get("recipe_id"), []).append(l)
        return out

    # -- calculs
    def recette(self, recipe_id) -> dict | None:
        rec = self.recette_par_id().get(recipe_id)
        if not rec:
            return None
        lgn = self.lignes_par_recette().get(recipe_id, [])
        calc = calculer_recette(lgn, self.ing_par_id(), rec.get("base_servings"),
                                nom_recette=rec.get("name"))
        calc["recette"] = rec.get("name")
        calc["instructions"] = rec.get("instructions")
        calc["id"] = recipe_id
        return calc

    def reparer_macros(self, entrees: list[dict]) -> tuple:
        """Cherche les glucides/lipides manquants des lignes du journal.

        `entrees` : les lignes de la table protein_entries.
        Renvoie (propositions, non_trouvees) — rien n'est écrit ici.
        """
        recettes = self.recette_par_id()
        lignes_par_recette = self.lignes_par_recette()
        ings = self.ing_par_id()
        trouvees, perdues = [], []
        for e in entrees or []:
            deja = _nombre(e.get("carbs_g")) or _nombre(e.get("fat_g"))
            if deja:
                continue                       # déjà complète, on n'y touche pas
            d = deviner_macros(e.get("item"), e.get("qty"), e.get("protein_g"),
                               recettes, lignes_par_recette, ings)
            if not d:
                perdues.append(e)
                continue
            trouvees.append(dict(id=e.get("id"), item=e.get("item"),
                                 proteines_enregistrees=_nombre(e.get("protein_g")),
                                 date=str(e.get("entry_date") or "")[:10], **d))
        return trouvees, perdues

    def repas_du_jour(self, jour: dt.date | None = None) -> list[dict]:
        """Les repas prévus ce jour-là, avec leurs macros."""
        jour = jour or dt.date.today()
        cible = str(jour)
        recettes = self.recette_par_id()
        lignes = self.lignes_par_recette()
        ings = self.ing_par_id()
        out = []
        for m in self.planning():
            if str(m.get("date_menu") or "")[:10] != cible:
                continue
            rid = m.get("recipe_id")
            rec = recettes.get(rid) or {}
            repas = dict(heure=m.get("meal_type"), jour=m.get("day"),
                         recette=rec.get("name") or m.get("ingredient_id") or "—",
                         recipe_id=rid, nb_persons=m.get("nb_persons") or m.get("servings"),
                         id=m.get("id"))
            if rid and rid in recettes:
                repas["calcul"] = calculer_recette(lignes.get(rid, []), ings,
                                                   rec.get("base_servings"),
                                                   nom_recette=rec.get("name"))
            out.append(repas)
        ordre = {"Midi": 0, "Soir": 1}
        return sorted(out, key=lambda r: (ordre.get(r["heure"], 2), r["recette"]))

    def semaine(self, debut: dt.date | None = None, jours: int = 7) -> list[dict]:
        debut = debut or dt.date.today()
        return [dict(jour=debut + dt.timedelta(days=i),
                     repas=[r for r in self.planning()
                            if str(r.get("date_menu") or "")[:10] == str(debut + dt.timedelta(days=i))]
                     ) for i in range(jours)]

    # ------------------------------------------------------------------
    #  LISTE DE COURSES
    # ------------------------------------------------------------------
    def courses(self, du: dt.date, au: dt.date, pour_foyer: bool = True,
                adultes: float = 2.0, enfants: float = 2.0,
                coef_enfant: float = 0.6, suivre_convives: bool = True) -> dict:
        """Liste de courses entre deux dates, rangée par rayon.

        Les quantités des recettes sont additionnées (recette par recette) et
        **recalculées avec le nombre de convives écrit sur chaque repas** :
        un repas prévu pour 6 personnes achète donc 1,5 fois une recette de 4
        (demandé le 30/09). Si un repas n'indique personne, on retombe sur les
        portions du foyer (« pour_foyer », 3,2 par défaut).

        Les articles cochés « ne pas mettre dans la liste » sont exclus ;
        les articles récurrents sont toujours ajoutés.
        """
        recettes = self.recette_par_id()
        lignes = self.lignes_par_recette()
        lignes_all = [l for lst in lignes.values() for l in (lst or [])]   # pour les portions
        ings = self.ing_par_id()
        portion = portion_foyer(adultes, enfants, coef_enfant) if pour_foyer else None

        besoin: dict = {}
        repas_comptes = 0
        convives_par_repas: list = []          # pour l'afficher dans la page
        for m in self.planning():
            d = str(m.get("date_menu") or "")[:10]
            if not d or not (str(du) <= d <= str(au)):
                continue
            rid = m.get("recipe_id")
            if not rid or rid not in recettes:
                continue
            repas_comptes += 1
            rec = recettes[rid]
            nom_rec = str(rec.get("name") or "")
            parts = _nombre(rec.get("base_servings")) or 1.0
            # NOMBRE DE CONVIVES écrit sur ce repas (« 6 » si un invité arrive).
            # C'est lui qui commande les quantités ; les portions du foyer ne
            # servent que si le repas n'indique personne.
            convives = _nombre(m.get("servings")) or _nombre(m.get("nb_persons")) or 0.0
            if convives > 0:
                convives_par_repas.append(convives)
            if convives > 0 and suivre_convives:
                coef = convives / parts          # ← le nombre d'invités commande
            else:
                coef = (portion / parts) if portion else 1.0
            # ligne « [Ing] Steak haché » : le nombre saisi est un nombre d'unités
            # (4 steaks), pas 4 g. On le traduit avec la fiche de l'aliment, comme
            # le fait la fiche PDF → 4 × 125 g = 500 g. Et on garde SON nom.
            if nom_rec.startswith("[Ing] "):
                ligne = (lignes.get(rid) or [{}])[0]
                ing = ings.get(ligne.get("ingredient_id")) or ings.get(m.get("ingredient_id")) or {}
                cle = ligne.get("ingredient_id") or m.get("ingredient_id")
                if cle and not ing.get("exclude_from_list"):
                    unite_liste = ing.get("unite_liste_courses") or ing.get("unit") or "g"
                    qte_saisie = m.get("ingredient_qty") or m.get("servings") or 1
                    # ⭐ unité « convives » : « 3 convives » de pâtes = 3 × 80 g.
                    #   La portion par personne vient des repères (voir plus haut),
                    #   ou de la moyenne de ses recettes.
                    u_saisie = m.get("ingredient_unit")
                    portion_pers = None            # ⚠️ nom distinct : « portion » = le foyer
                    if str(u_saisie or "").strip().lower().startswith(("convive", "personne")):
                        portion_pers = portion_personne(ing, lignes_all, recettes)[0]
                    try:
                        import pdf_menus as PM
                        q = PM._quantite_ligne_ing(qte_saisie, ing, unite_liste,
                                                   u_saisie, portion_pers)
                    except Exception:
                        q = _nombre(qte_saisie)
                    if cle not in besoin:
                        besoin[cle] = dict(id=cle, nom=nom_court(ing),
                                       nom_complet=ing.get("name"),
                                       unite=unite_liste, unite_declaree=ing.get("unit"),
                                       quantite=0.0, rayon=ing.get("category") or "Autre",
                                           quantite_recommandee=ing.get("quantite_recommandee"),
                                           unite_recommandee=ing.get("unite_recommandee"),
                                           poids_piece_g=ing.get("poids_piece_g"), recettes=[])
                    besoin[cle]["quantite"] += _nombre(q)
                    if nom_rec not in besoin[cle]["recettes"]:
                        besoin[cle]["recettes"].append(nom_rec)
                continue
            for l in lignes.get(rid, []):
                ing = ings.get(l.get("ingredient_id")) or {}
                if ing.get("exclude_from_list"):
                    continue
                u = l.get("unit") or ing.get("unit")
                cle = l.get("ingredient_id")
                # on ramène TOUJOURS à l'unité de la liste de courses : « 6 unités »
                # de pommes de terre (100 g l'unité) deviennent 600 g. Sinon on
                # additionnait des grammes et des unités (« Pomme de terre : 310
                # unités »). Corrigé le 30/09 — la liste dit enfin la même chose
                # que la fiche PDF.
                unite_liste = ing.get("unite_liste_courses") or ing.get("unit") or u
                q = _convertir(_nombre(l.get("quantity")), u, unite_liste,
                               ing.get("poids_piece_g")) * coef
                if cle not in besoin:
                    besoin[cle] = dict(id=cle, nom=nom_court(ing),
                                       nom_complet=ing.get("name"),
                                       unite=unite_liste, unite_declaree=ing.get("unit"),
                                       quantite=0.0, rayon=ing.get("category") or "Autre",
                                       quantite_recommandee=ing.get("quantite_recommandee"),
                                       unite_recommandee=ing.get("unite_recommandee"),
                                       poids_piece_g=ing.get("poids_piece_g"),
                                       recettes=[])
                besoin[cle]["quantite"] += q
                nom_rec = rec.get("name")
                if nom_rec and nom_rec not in besoin[cle]["recettes"]:
                    besoin[cle]["recettes"].append(nom_rec)

        # articles récurrents (pain, lait, PQ…) : toujours dans la liste.
        #   Ils n'ont pas de quantité calculée : on prend alors la QUANTITÉ
        #   RECOMMANDÉE de la fiche (« 1 boîte », « 200 ml ») — sinon la liste
        #   affichait « 0 g » pour tous les articles du fond de placard.
        # --- SES NOMS À LUI -------------------------------------------------
        #  Une ligne de planning « [Ing] Steak haché » doit apparaître sous ce
        #  nom-là dans la liste de courses (« Steak haché »), et non sous le nom
        #  de la ligne de base (« Boeuf haché ») : au magasin, ce n'est pas la
        #  même chose. C'est lui qui l'a écrit, c'est son mot qui gagne.
        noms_a_lui: dict = {}
        for m in self.planning():
            rec = recettes.get(m.get("recipe_id")) or {}
            nom_rec = str(rec.get("name") or "")
            if not nom_rec.startswith("[Ing] "):
                continue
            sien = nom_rec[6:].strip()
            if not sien:
                continue
            ident = m.get("ingredient_id")
            if not ident:
                for l in lignes.get(m.get("recipe_id"), []):
                    ident = l.get("ingredient_id")
                    break
            if ident:
                noms_a_lui.setdefault(str(ident), sien)

        for ing in self.ingredients():
            if ing.get("is_recurrent") and not ing.get("exclude_from_list"):
                cle = ing.get("id")
                q_rec = _nombre(ing.get("quantite_recommandee")) or 0.0
                u_rec = (ing.get("unite_recommandee") or ing.get("unit")
                         if q_rec else ing.get("unit"))
                besoin.setdefault(cle, dict(id=cle, nom=nom_court(ing),
                                            nom_complet=ing.get("name"),
                                            unite=u_rec, unite_declaree=ing.get("unit"),
                                            quantite=q_rec, rayon=ing.get("category") or "Autre",
                                            quantite_recommandee=ing.get("quantite_recommandee"),
                                            unite_recommandee=ing.get("unite_recommandee"),
                                            poids_piece_g=ing.get("poids_piece_g"),
                                            recettes=[]))
                besoin[cle]["recurrent"] = True

        # son nom à lui remplace le nom de la base (Steak haché, pas Boeuf haché)
        for cle, v in besoin.items():
            sien = noms_a_lui.get(str(cle))
            if sien:
                v["nom_complet"] = v.get("nom_complet") or v.get("nom")
                v["nom"] = sien
            # dans « utilisé par », on n'écrit pas le préfixe technique « [Ing] »,
            # et on ne répète pas le nom de l'article lui-même
            v["recettes"] = [n[6:].strip() if n.startswith("[Ing] ") else n for n in v["recettes"]]
            v["recettes"] = [n for n in v["recettes"] if n.lower() != (v.get("nom") or "").lower()]

        # arrondi « achetable »
        for v in besoin.values():
            arrondi_achat(v)
            v["nb_recettes"] = len(v["recettes"])
        rayons: dict = {}
        for v in besoin.values():
            rayons.setdefault(v["rayon"], []).append(v)
        for r in rayons:
            rayons[r].sort(key=lambda x: (not x.get("recurrent"), x["nom"].lower()))
        return dict(rayons=rayons, repas=repas_comptes,
                    portions_foyer=portion, convives=convives_par_repas,
                    du=str(du), au=str(au))


def order_col(table: str) -> str | None:
    return {"ingredients": "name", "recipes": "name"}.get(table)


def arrondi_achat(v: dict) -> dict:
    """Arrondit une quantité à ce qu'on achète RÉELLEMENT.

    Trois cas, dans l'ordre :

    1. L'aliment se vend à la pièce et on connaît son poids (courgette, œuf,
       citron, pomme…) → on arrondit au NOMBRE DE PIÈCES le plus proche.
       450 g de courgette (200 g pièce) → 2 courgettes, soit 400 g.
       C'est ce qu'on fait naturellement en magasin.

    2. L'aliment se compte (tranche, gousse, boîte, sachet) → on arrondit à
       l'unité supérieure : on n'achète pas 3,2 tranches de jambon.

    3. Le reste (viande au poids, farine, riz, huile…) → on arrondit à un
       poids « rond » qui existe en rayon : 5 g près en dessous de 100 g,
       50 g près jusqu'à 500 g, 100 g près au-delà. 450,8 g → 450 g ;
       860 g → 900 g ; 1 240 g → 1,25 kg.

    La quantité de départ reste dans « quantite_brute » : rien n'est perdu.
    """
    import math

    def _f(x):
        """Accepte un nombre en texte ou en Decimal (selon d'où viennent les données)."""
        try:
            return float(x)
        except (TypeError, ValueError):
            return 0.0

    q = _f(v.get("quantite"))
    v["quantite_brute"] = q
    unite = (v.get("unite") or "").strip().lower()
    piece = _f(v.get("poids_piece_g"))
    v["pieces"] = None

    if q <= 0:
        v["quantite"] = 0.0
        return v

    # --- 1) vendu à la pièce
    declare_g = (v.get("unite_declaree") or "").strip().lower() in ("g", "gr", "gramme", "grammes")
    plausible = bool(piece) and 25 <= piece <= 400
    # on ne compte en pièces que ce qui s'achète vraiment à la pièce :
    # produits frais bruts (fruits, légumes, œufs, pain…) — pas les conserves,
    # sauces, plats préparés ni les poudres.
    nom = ((v.get("nom") or "") + " " + (v.get("nom_complet") or "")).lower()
    pas_une_piece = any(mot in nom for mot in (
        "coulis", "appertis", "préemball", "preemball", "sauce", "purée", "puree",
        "jus", "confit", "conserve", "surgel", "plat", "gratin", "poudre", "farine",
        "boisson", "sirop", "huile", "vinaigre", "alcool", "vin", "bière"))
    rayon_ok = (v.get("rayon") or "") in ("Fruits & Légumes", "Frais & Produits Laitiers",
                                          "Boucherie & Poissonnerie", "Surgelés", "Autre", "")
    if declare_g and plausible and rayon_ok and not pas_une_piece \
       and unite in ("g", "gr", "gramme", "grammes", ""):
        n = q / piece
        if n >= 0.6:
            nb = int(round(n))              # au nombre de pièces le plus proche
            if nb < 1:
                nb = 1
            if 1 <= nb <= 8:                # au-delà, on reste au poids (plus lisible)
                v["pieces"] = nb
                v["quantite"] = round(nb * piece, 1)
                return v

    # --- 2) unités qui se comptent
    if unite_propre(unite).lower() in ("unité", "tranche", "gousse", "botte",
                                       "sachet", "boîte", "boite", "pot", "barquette",
                                       "verre", "filet", "tranche(s)", "pincée", "pincee"):
        v["quantite"] = float(math.ceil(q))
        v["unite"] = unite_propre(v.get("unite")) or v.get("unite")
        return v

    # --- 3) poids « rond »
    if unite in ("g", "gr", "gramme", "grammes", ""):
        if q < 100:
            pas = 5
        elif q < 500:
            pas = 50
        elif q < 1000:
            pas = 100
        else:
            pas = 250
        v["quantite"] = float(int(round(q / pas)) * pas)
        if v["quantite"] <= 0:
            v["quantite"] = pas
        return v

    if unite in ("ml", "cl", "l", "litre"):
        v["quantite"] = float(math.ceil(q))
        v["unite"] = unite_propre(v.get("unite")) or v.get("unite")
        return v

    v["quantite"] = round(q, 1)
    return v


def quantite_ligne(qte, ing: dict | None) -> str:
    """« [Ing] Pâtes : 200 » → « 200 g » ; « [Ing] Cordon bleu : 3 » → « 3 unités ».

    Sans cette fonction, les lignes « ingrédient seul » du planning s'affichaient
    sans unité (« Pâtes (200) ») : impossible de savoir s'il fallait 200 g ou
    200 unités. C'est corrigé (30/09). Une seule règle pour toute l'application :
    elle est écrite dans `pdf_menus._quantite_lisible`.
    """
    try:
        import pdf_menus as PM
        return PM._quantite_lisible(qte, ing)
    except Exception:                                   # jamais de plantage ici
        try:
            q = float(qte or 0)
        except (TypeError, ValueError):
            return ""
        if q <= 0:
            return ""
        u = unite_propre((ing or {}).get("unite_liste_courses") or (ing or {}).get("unit"))
        return f"{q:g} {u}".strip()


def fmt_quantite(v: dict) -> str:
    """Texte lisible : « 400 g (2 unités) », « 450 g », « 4 tranches »…"""
    q = v.get("quantite") or 0
    if q <= 0:                      # pas de quantité calculée (article récurrent)
        return "—"
    u = (v.get("unite") or "").strip()
    nb = v.get("pieces")
    # pluriels naturels : « 4 tranches », « 3 gousses »
    ul = u.lower()
    if ul in ("unité", "unite"):
        u = "" if q <= 1 else "unités"
    elif ul in ("tranche", "gousse", "sachet", "boîte", "boite", "pot", "barquette",
                "verre", "filet", "botte", "pièce", "piece", "pincée", "pincee") and q > 1:
        u = u + ("s" if not u.endswith("s") else "")
    txt_q = (f"{q:g}".replace(".", ","))
    base = f"{txt_q} {u}".strip() if u else txt_q
    if q >= 100 and ul in ("cl",):
        base = (f"{q/100:.2f}".rstrip("0").rstrip(".").replace(".", ",") + " L")
    if q >= 1000 and ul in ("g", "gr", "gramme", "grammes"):
        base = (f"{q/1000:.2f}".rstrip("0").rstrip(".").replace(".", ",") + " kg")
    if nb:
        # demande du 30/09 : on écrit « unités », jamais « pièces »
        return f"{base} ({nb} unité{'s' if nb > 1 else ''})"
    return base
