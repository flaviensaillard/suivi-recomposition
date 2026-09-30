# -*- coding: utf-8 -*-
"""Nouvelle mise en page de la fiche PDF — police adaptative (2.8.4).

Règles :
  • tout tient sur UNE feuille A4, rien ne sort de la page ;
  • chaque texte est mesuré avant d'être écrit : la police diminue jusqu'à ce que
    ça rentre dans sa case, et si c'est encore trop long le texte est coupé
    proprement (« Courgette râpée... ») — jamais de débordement ni de chevauchement ;
  • la liste de courses et les produits récurrents suivent la même règle.
"""
from __future__ import annotations

from datetime import timedelta


# ---------------------------------------------------------------------------
#  Les rayons (repris de ton application)
# ---------------------------------------------------------------------------
RAYONS = ["Fruits & Légumes", "Boucherie & Poissonnerie", "Frais & Produits Laitiers",
          "Épicerie Salée", "Épicerie Sucrée", "Boissons", "Surgelés", "Autre"]


# ---------------------------------------------------------------------------
#  Constantes de page
# ---------------------------------------------------------------------------
LARGEUR_PAGE = 210.0
HAUTEUR_PAGE = 297.0
MARGE = 10.0
MM_PAR_PT = 0.352778


# ---------------------------------------------------------------------------
#  Texte : nettoyage, mesure, découpe
# ---------------------------------------------------------------------------
def _propre(txt) -> str:
    """Texte imprimable en police standard (accents français conservés).

    Les caractères typographiques (apostrophes courbes, tirets longs, points de
    suspension) sont remplacés par leur équivalent simple, et tout ce qui n'est
    pas latin-1 (emoji…) est retiré : sinon fpdf refuse d'écrire la page.
    """
    if txt is None:
        return ""
    t = str(txt)
    for a, b in (("\u2019", "'"), ("\u2018", "'"), ("\u201c", '"'), ("\u201d", '"'),
                 ("\u2013", "-"), ("\u2014", "-"), ("\u2026", "..."), ("\u0153", "oe"),
                 ("\u0152", "OE"), ("\u00a0", " "), ("\u2022", "-")):
        t = t.replace(a, b)
    return "".join(c for c in t if c.isprintable() and ord(c) < 256)


def _lignes(pdf, texte, largeur, taille, style="") -> list:
    """Découpe `texte` en lignes qui tiennent dans `largeur` (mm) à cette taille."""
    pdf.set_font("Helvetica", style, taille)
    mots = _propre(texte).split()
    if not mots:
        return [""]
    out, cour = [], ""
    for mot in mots:
        # un mot plus long que la colonne : on le coupe caractère par caractère
        while pdf.get_string_width(mot) > largeur:
            part = ""
            for c in mot:
                if pdf.get_string_width(part + c) > largeur:
                    break
                part += c
            part = part or mot[0]
            if cour:
                out.append(cour)
                cour = ""
            out.append(part)
            mot = mot[len(part):]
        essai = f"{cour} {mot}".strip()
        if pdf.get_string_width(essai) <= largeur or not cour:
            cour = essai
        else:
            out.append(cour)
            cour = mot
    if cour:
        out.append(cour)
    return out


def _tronque(pdf, texte, largeur, taille, style="") -> str:
    """Coupe le texte à la largeur demandée, avec « ... » à la fin."""
    pdf.set_font("Helvetica", style, taille)
    txt = _propre(texte)
    if pdf.get_string_width(txt) <= largeur:
        return txt
    while txt and pdf.get_string_width(txt + "...") > largeur:
        txt = txt[:-1]
    return txt.rstrip() + "..."


def _h_ligne(taille, interligne=1.15) -> float:
    """Hauteur d'une ligne en mm pour une taille de police donnée."""
    return taille * MM_PAR_PT * interligne


def _taille_qui_tient(pdf, hauteur_necessaire, taille_max, taille_min=6.0, pas=0.5) -> float:
    """Renvoie la taille à utiliser, `taille_min` si même au minimum ça ne tient pas."""
    return max(taille_min, min(taille_max, hauteur_necessaire))


# ---------------------------------------------------------------------------
#  Bloc d'une demi-journée (Déjeuner / Dîner) — police adaptative
# ---------------------------------------------------------------------------
def _bloc_repas(pdf, x, y, largeur, hauteur, etiquette, items,
                taille_max=11.0, taille_min=6.5) -> None:
    """Écrit « Déjeuner (4) : » puis la liste des plats.

    La taille de la police descend (par pas de 0,5) jusqu'à ce que l'étiquette
    ET tous les plats tiennent dans la case. En dessous du minimum, les noms sont
    coupés, et s'il y a vraiment trop de plats les derniers sont résumés par
    « +N autre(s) ». Il n'y a donc jamais de texte hors du cadre.
    """
    if hauteur < 3 or largeur < 20:
        return
    noms = [_propre(i.get("name")) for i in items] or ["-"]
    taille = taille_max
    while True:
        pdf.set_font("Helvetica", "B", taille)
        decal = pdf.get_string_width(etiquette) + 1.5
        largeur_plats = largeur - decal - 3
        if largeur_plats < 12:                      # l'étiquette prend toute la place
            taille = round(taille - 0.5, 2)
            if taille < taille_min:
                return
            continue
        hl = _h_ligne(taille)
        besoin = sum(len(_lignes(pdf, n, largeur_plats, taille)) for n in noms) * hl
        if besoin <= hauteur - 1.2 or taille <= taille_min:
            break
        taille = round(taille - 0.5, 2)

    # --- il reste peut-être trop de plats (=plus de lignes que de place) :
    #     on n'affiche que ce qui rentre, et on résume le reste.
    hl = _h_ligne(taille)
    place = max(1, int((hauteur - 1.2) // hl))
    if place >= 1:
        place = max(place, 1)
    lignes_par_plat = []
    total = 0
    for n in noms:
        l = _lignes(pdf, n, largeur_plats, taille)
        lignes_par_plat.append(l)
        total += len(l)
    gardes, reste = len(noms), 0
    if total > place:
        gardes, cumul = 0, 0
        for i, l in enumerate(lignes_par_plat):
            if cumul + len(l) > place - 1:          # on garde 1 ligne pour « +N »
                break
            cumul += len(l)
            gardes += 1
        reste = len(noms) - gardes

    # --- dessin
    y0 = y + 0.6
    pdf.set_font("Helvetica", "B", taille)
    pdf.set_xy(x + 2, y0)
    pdf.cell(decal, hl, etiquette, border=0, align="L")

    yy = y0
    pdf.set_font("Helvetica", "", taille)
    if not items:
        pdf.set_font("Helvetica", "I", taille)
        pdf.set_xy(x + 2 + decal, yy)
        pdf.cell(largeur_plats, hl, "-", border=0, align="L")
        return
    for i, l in enumerate(lignes_par_plat[:gardes]):
        for ligne in l:
            if yy + hl > y + hauteur - 0.3:
                break
            pdf.set_font("Helvetica", "", taille)
            pdf.set_xy(x + 2 + decal, yy)
            pdf.cell(largeur_plats, hl, ligne, border=0, align="L")
            yy += hl
    if reste:
        libre = max(0.0, (y + hauteur - 0.3) - yy)
        if libre >= hl * 0.9:
            pdf.set_font("Helvetica", "I", taille)
            pdf.set_xy(x + 2 + decal, yy)
            pdf.cell(largeur_plats, hl, f"+ {reste} autre(s)", border=0, align="L")


# ---------------------------------------------------------------------------
#  Colonne de droite : liste de courses + produits récurrents
# ---------------------------------------------------------------------------
def _mise_en_forme():
    """Les petites fonctions de formatage de pdf_menus (import différé : pas de cycle)."""
    from pdf_menus import format_liste_quantity, format_quantity, format_servings
    return format_liste_quantity, format_quantity, format_servings


UNITES_PLURIEL = ("unité", "unite", "pièce", "piece", "tranche", "gousse", "sachet", "boîte",
                  "boite", "pot", "barquette", "verre", "filet", "botte")


def _pluriel(qty, unite: str) -> str:
    """« 3 unité » → « 3 unités », « 4 tranche » → « 4 tranches »."""
    u = (unite or "").strip()
    if not u:
        return ""
    try:
        q = float(qty)
    except (TypeError, ValueError):
        return u
    if q > 1 and u.lower() in UNITES_PLURIEL and not u.lower().endswith("s"):
        u = u + "s"
    if q <= 1 and u.lower() in ("unité", "unite"):
        u = ""                                   # « 1 » tout seul se comprend
    return u


def _items_liste(par_rayon, taille, pdf, largeur_txt, tronque=False):
    """[(type, texte)] de tout ce qui doit être écrit, avec la hauteur totale."""
    format_liste_quantity, format_quantity, _ = _mise_en_forme()
    hl = _h_ligne(taille)
    sortie, hauteur = [], 0.0
    for cat in RAYONS:
        items = par_rayon.get(cat)
        if not items:
            continue
        sortie.append(("cat", cat))
        hauteur += hl + 1.0
        for it in items:
            qty, unite = format_liste_quantity(it["qty"], it.get("unit", ""))
            if not (unite or "").strip():
                # unité inconnue : au-delà de 20 c'est un poids, en dessous c'est un
                # nombre d'unités (« Pâtes fourées : 2 unités »). Rien ne reste nu.
                try:
                    q = float(qty)
                    if q.is_integer() and 1 < q <= 20:
                        unite = "unité"
                except (TypeError, ValueError):
                    pass
            unite = _pluriel(qty, unite)
            txt = f"{it['name']} : {format_quantity(qty)} {unite}".strip()
            if tronque:
                txt = _tronque(pdf, txt, largeur_txt, taille)
                nl = 1
            else:
                nl = len(_lignes(pdf, txt, largeur_txt, taille))
            sortie.append(("item", txt))
            hauteur += nl * hl
        hauteur += 1.0
    return sortie, hauteur


def _bloc_courses(pdf, x, y, largeur, hauteur_max, par_rayon, recurrents) -> None:
    """Liste de courses par rayon + produits récurrents, le tout dans `hauteur_max`.

    Étapes : on essaie 10 pt, puis on descend, puis on coupe les noms trop longs
    (en gardant les quantités), et on descend encore. En tout dernier recours —
    si la liste est vraiment énorme — les lignes qui ne rentrent pas sont
    remplacées par « + N autres articles », pour que la feuille reste propre.
    """
    if hauteur_max < 20:
        return
    largeur_txt = largeur - 8                     # case à cocher + retrait
    col_rec = (largeur - 6) / 2                   # 2 colonnes pour les récurrents
    largeur_rec = col_rec - 4

    def h_recurrents(taille) -> float:
        if not recurrents:
            return 0.0
        return 7.0 + ((len(recurrents) + 1) // 2) * _h_ligne(taille) + 2.0

    # --- 1) la plus grande police qui fait tout tenir (10 pt → 5 pt)
    taille, tronque = 10.0, False
    liste, haut = _items_liste(par_rayon, taille, pdf, largeur_txt)
    if haut + h_recurrents(taille) > hauteur_max:
        tronque, taille = True, 8.0             # on coupe les noms, quantités gardées
        liste, haut = _items_liste(par_rayon, taille, pdf, largeur_txt, tronque=True)
    while haut + h_recurrents(taille) > hauteur_max and taille > 5.0:
        taille = round(taille - 0.5, 2)
        liste, haut = _items_liste(par_rayon, taille, pdf, largeur_txt, tronque=tronque)

    hl = _h_ligne(taille)
    yy = y
    pdf.set_font("Helvetica", "", taille)
    if not liste:
        pdf.set_xy(x + 2, yy)
        pdf.cell(largeur - 4, hl, "Aucun article", border=0)
        return

    limite = y + hauteur_max - h_recurrents(taille)
    ecrits, restants = 0, 0
    for i, (genre, txt) in enumerate(liste):
        if genre == "cat":
            if yy + hl + 1.0 > limite:
                restants = len([1 for g, _ in liste[i:] if g == "item"])
                break
            pdf.set_fill_color(255, 240, 220)
            pdf.rect(x, yy, largeur, hl + 1.0, "F")
            pdf.set_font("Helvetica", "B", taille)
            pdf.set_xy(x + 1.5, yy + 0.3)
            pdf.cell(largeur - 3, hl, _tronque(pdf, txt, largeur - 3, taille, "B"), border=0)
            yy += hl + 1.0
            pdf.set_font("Helvetica", "", taille)
            continue
        if yy + hl > limite:
            restants = len([1 for g, _ in liste[i:] if g == "item"])
            break
        pdf.set_draw_color(100, 100, 100)
        pdf.rect(x + 2, yy + 0.7, 2.2, 2.2, "D")
        if tronque:
            pdf.set_xy(x + 6, yy)
            pdf.cell(largeur_txt, hl, txt, border=0)
            yy += hl
        else:
            for ligne in _lignes(pdf, txt, largeur_txt, taille):
                pdf.set_xy(x + 6, yy)
                pdf.cell(largeur_txt, hl, ligne, border=0)
                yy += hl
        ecrits += 1
        pdf.set_font("Helvetica", "", taille)
    if restants:
        pdf.set_font("Helvetica", "I", taille)
        pdf.set_xy(x + 6, min(yy, limite - hl))
        pdf.cell(largeur_txt, hl, f"+ {restants} autre(s) article(s) — voir l'application",
                 border=0)

    # --- produits récurrents
    if not recurrents:
        return
    yy = max(yy + 2.0, y + hauteur_max - h_recurrents(taille) + 1.0)
    if yy > y + hauteur_max - 6:
        return
    pdf.set_fill_color(240, 240, 240)
    pdf.rect(x, yy, largeur, 6.0, "F")
    pdf.set_font("Helvetica", "B", taille)
    pdf.set_xy(x + 1.5, yy + 0.8)
    pdf.cell(largeur - 3, hl, _propre("Produits récurrents"), border=0, align="C")
    yy += 7.0
    pdf.set_font("Helvetica", "", taille)
    for idx, rec in enumerate(recurrents):
        if yy + hl > y + hauteur_max:
            break
        cx = x + (2 if idx % 2 == 0 else 5 + col_rec)
        pdf.set_draw_color(100, 100, 100)
        pdf.rect(cx, yy + 0.7, 2.2, 2.2, "D")
        pdf.set_xy(cx + 4, yy)
        pdf.cell(largeur_rec, hl, _tronque(pdf, rec.get("name", ""), largeur_rec, taille),
                 border=0)
        if idx % 2:
            yy += hl
    if len(recurrents) % 2:
        yy += hl


# ---------------------------------------------------------------------------
#  En-tête + planning des 7 jours
# ---------------------------------------------------------------------------
def _entete(pdf, left_x, left_width, start_date) -> float:
    """Titre, période, bandeau « Planning des Repas ». Renvoie le y du contenu."""
    y = MARGE
    taille = 26.0
    pdf.set_font("Helvetica", "B", taille)          # une police doit être posée avant de mesurer
    while taille > 12 and pdf.get_string_width(_propre("Menus de la semaine")) > left_width - 4:
        taille -= 1
    pdf.set_font("Helvetica", "B", taille)
    pdf.set_xy(left_x, y)
    pdf.cell(left_width, 12, _propre("Menus de la semaine"), align="C")
    y += 12
    if start_date:
        fin = start_date + timedelta(days=6)
        txt = f"Du {start_date.strftime('%d/%m/%Y')} au {fin.strftime('%d/%m/%Y')}"
        taille = 18.0
        pdf.set_font("Helvetica", "", taille)
        while taille > 9 and pdf.get_string_width(_propre(txt)) > left_width - 4:
            taille -= 1
        pdf.set_font("Helvetica", "", taille)
        pdf.set_xy(left_x, y)
        pdf.cell(left_width, 8, _propre(txt), align="C")
        y += 9
    else:
        y += 2
    pdf.set_fill_color(200, 230, 200)
    pdf.set_xy(left_x, y)
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(left_width, 7, "Planning des Repas", ln=True, fill=True, align="C")
    return y + 7 + 2


def _planning(pdf, week_days, schedule, x, y, largeur, hauteur_totale) -> None:
    """Les 7 jours : nom du jour à la verticale + Déjeuner / Dîner."""
    if not week_days:
        return
    hauteur_totale = hauteur_totale - 2.0        # petite marge de respiration en bas
    inter = 1.5
    h_jour = (hauteur_totale - (len(week_days) - 1) * inter) / len(week_days)
    largeur_jour = 13.0
    x_contenu = x + largeur_jour + 2
    largeur_contenu = (x + largeur) - x_contenu

    for i, info in enumerate(week_days):
        nom = info["day_name"]
        yj = y + i * (h_jour + inter)
        h_interne = h_jour - 1.0

        # --- bandeau du jour (nom vertical, police adaptative)
        pdf.set_fill_color(245, 245, 220)
        pdf.rect(x, yj, largeur_jour, h_interne, "F")
        pdf.set_draw_color(200, 200, 200)
        pdf.rect(x, yj, largeur_jour, h_interne, "D")
        taille = 13.0
        pdf.set_font("Helvetica", "B", taille)
        while taille > 7 and pdf.get_string_width(_propre(nom)) > h_interne - 4:
            taille -= 0.5
        pdf.set_font("Helvetica", "B", taille)
        with pdf.rotation(90, x + largeur_jour / 2, yj + h_interne / 2):
            lab = _tronque(pdf, nom, h_interne - 3, taille, "B")
            pdf.set_xy(x + largeur_jour / 2 - (h_interne - 3) / 2, yj + h_interne / 2 - 2)
            pdf.cell(h_interne - 3, 4, lab, align="C")

        # --- Déjeuner / Dîner : la place est partagée selon le nombre de plats
        midi = schedule[nom]["Midi"]
        soir = schedule[nom]["Soir"]
        n_midi = max(len(midi), 1)
        n_soir = max(len(soir), 1)
        espace = h_interne - 1.0
        h_midi = espace * n_midi / (n_midi + n_soir)
        h_soir = espace - h_midi

        pdf.set_fill_color(255, 250, 240)
        pdf.rect(x_contenu, yj, largeur_contenu, h_midi, "F")
        pdf.set_draw_color(220, 220, 220)
        pdf.rect(x_contenu, yj, largeur_contenu, h_midi, "D")
        items_midi = [{"name": it["name"]} for it in midi]
        if items_midi:                              # on n'écrit le nombre que s'il y a un plat
            convives = max([it["servings"] or 1 for it in midi], default=1)
            libelle = f"Déjeuner ({_mise_en_forme()[2](convives)}) :"
        else:
            libelle = "Déjeuner :"
        _bloc_repas(pdf, x_contenu, yj, largeur_contenu, h_midi, libelle, items_midi)

        y_soir = yj + h_midi + 1.0
        pdf.set_fill_color(240, 245, 255)
        pdf.rect(x_contenu, y_soir, largeur_contenu, h_soir, "F")
        pdf.set_draw_color(220, 220, 220)
        pdf.rect(x_contenu, y_soir, largeur_contenu, h_soir, "D")
        items_soir = [{"name": it["name"]} for it in soir]
        if items_soir:
            convives = max([it["servings"] or 1 for it in soir], default=1)
            libelle = f"Dîner ({_mise_en_forme()[2](convives)}) :"
        else:
            libelle = "Dîner :"
        _bloc_repas(pdf, x_contenu, y_soir, largeur_contenu, h_soir, libelle, items_soir)
