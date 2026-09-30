# -*- coding: utf-8 -*-
"""Rapproche les ingrédients de l'utilisateur avec la base Ciqual.

Produit un fichier de correspondances à valider par l'utilisateur.
Aucune valeur n'est inventée : si le doute est trop grand, la ligne est marquée
« À CHOISIR » et l'utilisateur décide.
"""
from __future__ import annotations

import csv
import re
import unicodedata

CIQUAL = "/home/user/app/data/foods_ciqual.csv"

# Mots trop courants pour être discriminants
MOTS_VIDES = {
    "de", "du", "des", "d", "la", "le", "les", "l", "au", "aux", "et", "a", "en",
    "avec", "sans", "ou", "pour", "sur", "frais", "fraiche", "frais", "type", "style",
    "bio", "environ", "environ", "cru", "crue", "cuit", "cuite", "nature", "pur",
}

# Équivalences explicites : le nom chez l'utilisateur -> un mot-clé Ciqual
SYNONYMES = {
    "oeuf": "oeuf", "oeufs": "oeuf", "oeufs frais": "oeuf",
    "blanc de poulet": "poulet, filet", "filet de poulet": "poulet, filet",
    "escalope de poulet": "poulet, filet", "poulet": "poulet",
    "steak hache": "boeuf, steak hache", "viande hachee": "boeuf, hache",
    "jambon": "jambon, blanc", "lardons": "lardon",
    "poisson": "poisson", "filet de poisson": "poisson",
    "creme fraiche": "creme fraiche", "creme liquide": "creme, liquide",
    "fromage blanc": "fromage blanc", "fromage rape": "fromage, rape",
    "emmental": "emmental", "gruyere": "gruyere", "comte": "comte",
    "yaourt": "yaourt", "yaourts": "yaourt", "skyr": "skyr",
    "lait": "lait, demi-ecreme", "lait demi ecreme": "lait, demi-ecreme",
    "lait ecreme": "lait, ecreme", "lait entier": "lait, entier",
    "beurre": "beurre", "huile d olive": "huile d'olive", "huile d'olive": "huile d'olive",
    "huile de tournesol": "huile de tournesol", "huile": "huile",
    "farine": "farine de ble", "farine de ble": "farine de ble",
    "sucre": "sucre blanc", "sucre blanc": "sucre blanc", "sucre roux": "sucre roux",
    "riz": "riz, blanc", "riz basmati": "riz, basmati", "riz complet": "riz, complet",
    "pates": "pates", "pates alimentaires": "pates",
    "spaghetti": "spaghetti", "macaroni": "macaroni",
    "semoule": "semoule de ble dur", "quinoa": "quinoa",
    "lentilles": "lentille", "lentille": "lentille",
    "pois chiches": "pois chiche", "haricots rouges": "haricot rouge",
    "haricots blancs": "haricot blanc", "haricots verts": "haricot vert",
    "pommes de terre": "pomme de terre", "pomme de terre": "pomme de terre",
    "patate douce": "patate douce", "patates douces": "patate douce",
    "tomates": "tomate", "tomate": "tomate",
    "oignon": "oignon", "oignons": "oignon", "ail": "ail",
    "carotte": "carotte", "carottes": "carotte",
    "courgette": "courgette", "courgettes": "courgette",
    "aubergine": "aubergine", "poivron": "poivron", "brocoli": "brocoli",
    "epinards": "epinard", "epinard": "epinard", "salade": "salade verte",
    "concombre": "concombre", "champignons": "champignon",
    "avocat": "avocat", "banane": "banane", "pomme": "pomme", "poire": "poire",
    "orange": "orange", "citron": "citron", "fraises": "fraise",
    "pain": "pain", "baguette": "baguette", "pain complet": "pain complet",
    "chocolat": "chocolat", "chocolat noir": "chocolat noir",
    "amandes": "amande", "noix": "noix", "noisettes": "noisette",
    "thon": "thon", "thon au naturel": "thon, au naturel",
    "sardines": "sardine", "maquereau": "maquereau", "saumon": "saumon",
    "cabillaud": "cabillaud", "colin": "colin", "crevettes": "crevette",
    "miel": "miel", "confiture": "confiture", "compote": "compote",
    "flocons d avoine": "flocon d'avoine", "avoine": "flocon d'avoine",
    "cereales": "cereales", "whey": "proteine en poudre",
    "champagne": "vin", "vin": "vin", "biere": "biere",
    "eau": "eau", "jus d orange": "jus d'orange", "jus de pomme": "jus de pomme",
    # ajouts constatés sur la base réelle
    "pave de saumon": "saumon", "saumon": "saumon", "rosbeef": "boeuf, roti",
    "roastbeef": "boeuf, roti", "champi de paris": "champignon de paris",
    "champis": "champignon de paris", "champignon de paris": "champignon de paris",
    "tomate concassee": "tomate, pulpe", "tomates concassees": "tomate, pulpe",
    "saute de porc": "porc, epaule", "farce a tomate": "farce",
    "pates fourrees": "pates, fourrees", "flammekueche": "tarte flambee",
    "knacki": "saucisse de strasbourg", "knack": "saucisse de strasbourg",
    "edamames": "feve de soja", "edamame": "feve de soja",
    "crozet": "crozet", "cube bouillon de poule": "bouillon de volaille",
    "cube bouillon de boeuf": "bouillon de boeuf", "cube bouillon de legumes": "bouillon de legumes",
    "herbes de provences": "herbes de provence", "comte rape": "comte",
    "creme liquide": "creme, liquide", "salade sodebo": "salade composee",
    "charcuterie": "charcuterie", "chevre frais": "fromage de chevre frais",
    "creme liquide": "Crème 30% MG, fluide, UHT", "creme": "Crème 30% MG, fluide, UHT",
    "citron": "Citron, chair sans peau, sans pépins, cru",
    "taboule": "Taboulé ou salade de semoule aux légumes, préemballé",
    "vin blanc": "Vin blanc sec", "vin rouge": "Vin rouge", "vin": "Vin (aliment moyen)",
    "edamames": "Fève, fraîche, surgelée, bouillie/cuite à l'eau",
    "edamame": "Fève, fraîche, surgelée, bouillie/cuite à l'eau",
    "pates fourees": "Pâtes fraîches farcies (ex : raviolis, tortellinis, raviolis chinois), préemballées",
    "crozet": "Pâtes sèches, standard, crues",
    "cube bouillon de poule": "Bouillon de volaille, déshydraté",
    "champi de paris": "Champignon de Paris ou champignon de couche, cru",
    "champignon de paris": "Champignon de Paris ou champignon de couche, cru",
    "farine": "Farine de blé tendre ou froment T110",
    "cacao": "Cacao, sans sucres ajoutés, poudre",
    "melon": "Melon cantaloup (par ex.: Charentais), pulpe, cru",
    "butternut": "Courge butternut (doubeurre), chair sans peau, cuite",
    "tomate concassee": "tomate, pulpe, appertisee", "sel": "sel, blanc",
    "compote": "compote de pomme", "cacao": "cacao, sans sucres ajoutes, poudre",
    "feta": "fromage type feta", "origan": "origan, seche",
    "poivre": "Poivre noir, poudre",
}

# Produits qui ne sont pas des aliments : on ne cherche pas de valeurs nutritionnelles
NON_ALIMENTAIRE = (
    "gel douche", "savon", "shampoing", "shampooing", "dentifrice", "lingettes", "couches",
    "essuie tout", "essuietout", "papier toilette", "lessive", "adoucissant", "liquide vaisselle",
    "eponge", "sacs poubelle", "aluminium", "film etirable", "sopalin", "mouchoirs",
    "soda stream", "sodastream", "senseo", "capsule", "dosette", "cafe moulu", "the vert",
    "sac congelation", "curseur", "piles", "ampoule", "batterie", "insecticide", "souris",
)

UNITES_PIECE = ("unite", "unites", "piece", "pieces", "tranche", "tranches", "boite",
                "boites", "sachet", "sachets", "gousse", "gousses", "pincee", "pincees")


def norm(txt: str) -> str:
    t = unicodedata.normalize("NFD", str(txt or ""))
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    t = t.lower().replace("'", " ").replace("-", " ").replace("_", " ")
    t = re.sub(r"[^a-z0-9 ]", " ", t)
    return " ".join(t.split())


def mots(txt: str) -> set:
    return {m for m in norm(txt).split() if m not in MOTS_VIDES and len(m) > 1}


def charger_ciqual() -> list:
    with open(CIQUAL, encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter=";"))


def _vers_float(v):
    try:
        return float(str(v).replace(",", "."))
    except Exception:
        return None


class IndexCiqual:
    def __init__(self, aliments):
        self.aliments = aliments
        self.par_nom = {}
        for a in aliments:
            self.par_nom.setdefault(norm(a["nom"]), a)
        self.mots_index = []
        for a in aliments:
            self.mots_index.append((mots(a["nom"]), a))

    def chercher(self, requete: str, seuil: float = 0.6):
        """Renvoie (aliment, score) ou (None, score)."""
        n = norm(requete)
        # 1) synonyme déclaré
        cle = SYNONYMES.get(n)
        cible = norm(cle) if cle else n

        # 2) correspondance exacte
        if cible in self.par_nom:
            return self.par_nom[cible], 1.0

        # 3) correspondance par mots
        mq = mots(cible)
        if not mq:
            return None, 0.0
        meilleur, score_max = None, 0.0
        for mc, a in self.mots_index:
            if not mc:
                continue
            communs = mq & mc
            if not communs:
                continue
            # couverture du mot-clé + bonus si l'aliment Ciqual n'ajoute pas trop
            couverture = len(communs) / len(mq)
            finesse = len(communs) / len(mc)
            score = couverture * 0.75 + finesse * 0.25
            if mq <= mc:                      # tous les mots de la requête sont là
                score = min(1.0, score + 0.15)
            # le mot de tête doit être présent : « Poivre » ne doit pas donner « Pâté au poivre vert »
            tete_q = list(mq)[0] if len(mq) == 1 else None
            if tete_q:
                premier_mot = mc and sorted(mc, key=lambda m: a["nom"].lower().find(m))[0]
                if tete_q != premier_mot:
                    score *= 0.45
            if score > score_max:
                meilleur, score_max = a, score
        return (meilleur, score_max) if score_max >= seuil else (None, score_max)

    def propositions(self, requete: str, n: int = 6) -> list:
        mq = mots(SYNONYMES.get(norm(requete)) or requete)
        scores = []
        for mc, a in self.mots_index:
            if not mc or not (mq & mc):
                continue
            couv = len(mq & mc) / len(mq)
            fin = len(mq & mc) / len(mc)
            scores.append((couv * 0.75 + fin * 0.25, a))
        scores.sort(key=lambda x: (-x[0], len(x[1]["nom"])))
        return scores[:n]


def grammes(quantite, unite, ing) -> tuple:
    """Convertit en grammes en utilisant les infos de l'ingrédient."""
    try:
        q = float(str(quantite).replace(",", "."))
    except Exception:
        q = 0.0
    u = norm(unite or "")
    densite = _vers_float(ing.get("densite")) or 1.0
    piece = _vers_float(ing.get("poids_piece_g"))
    u_ing = norm(ing.get("unit") or "")

    if u in ("g", "gramme", "grammes", ""):
        # unité vide : on prend l'unité par défaut de l'ingrédient
        if not u and u_ing in UNITES_PIECE:
            return (q * piece) if piece else (q * 50), f"{q:g} × {piece or 50:g} g ({u_ing})"
        return q, f"{q:g} g"
    if u in ("kg", "kilo", "kilos"):
        return q * 1000, f"{q:g} kg"
    if u in ("ml", "cl", "dl", "l", "litre", "litres", "centilitre", "millilitre"):
        facteur = {"ml": 1, "cl": 10, "dl": 100, "l": 1000, "litre": 1000, "litres": 1000,
                   "centilitre": 10, "millilitre": 1}[u]
        return q * facteur * densite, f"{q:g} {unite} × {densite:g} = {q * facteur * densite:.0f} g"
    if u in ("c. a soupe", "cuillere a soupe", "cas", "c a soupe"):
        return q * 15 * densite, f"{q:g} c. à soupe × 15 × {densite:g}"
    if u in ("c. a cafe", "cuillere a cafe", "cac", "c a cafe"):
        return q * 5 * densite, f"{q:g} c. à café × 5 × {densite:g}"
    if u in ("pincee", "pincees"):
        return q * 1, f"{q:g} pincée(s) ≈ 1 g"
    # unités « objet » : boîte, sachet, tranche, gousse, unité…
    if piece:
        return q * piece, f"{q:g} {unite} × {piece:g} g"
    return q * 50, f"{q:g} {unite} × 50 g (estimation)"


if __name__ == "__main__":
    import sys
    source = sys.argv[1] if len(sys.argv) > 1 else "/home/user/uploads/Supabase Snippet Untitled query (1).csv"
    ciqual = charger_ciqual()
    index = IndexCiqual(ciqual)

    with open(source, encoding="utf-8-sig", newline="") as f:
        ing = list(csv.DictReader(f))

    sortie, stats = [], {"exact": 0, "sur": 0, "moyen": 0, "faible": 0, "non_alim": 0}
    for i in ing:
        nom = i.get("name") or ""
        if any(mot in norm(nom) for mot in NON_ALIMENTAIRE):
            sortie.append({
                "mon_ingredient": nom, "categorie": i.get("category", ""),
                "unite": i.get("unit", ""), "poids_piece_g": i.get("poids_piece_g", ""),
                "correspondance_ciqual": "", "code": "", "kcal_100g": "", "proteines_100g": "",
                "glucides_100g": "", "lipides_100g": "", "fibres_100g": "",
                "confiance": "non alimentaire", "autres_pistes": "",
            })
            stats["non_alim"] = stats.get("non_alim", 0) + 1
            continue
        trouve, score = index.chercher(nom)
        if score >= 1.0:
            niveau, stats["exact"] = "exact", stats["exact"] + 1
        elif score >= 0.85:
            niveau, stats["sur"] = "sûr", stats["sur"] + 1
        elif score >= 0.6:
            niveau, stats["moyen"] = "à vérifier", stats["moyen"] + 1
        else:
            niveau, stats["faible"] = "À CHOISIR", stats["faible"] + 1
            trouve = None
        alternatives = [a["nom"] for _, a in index.propositions(nom, 3)] if niveau != "exact" else []
        sortie.append({
            "mon_ingredient": nom,
            "categorie": i.get("category", ""),
            "unite": i.get("unit", ""),
            "poids_piece_g": i.get("poids_piece_g", ""),
            "correspondance_ciqual": trouve["nom"] if trouve else "",
            "code": trouve["code"] if trouve else "",
            "kcal_100g": trouve["kcal"] if trouve else "",
            "proteines_100g": trouve["proteines"] if trouve else "",
            "glucides_100g": trouve["glucides"] if trouve else "",
            "lipides_100g": trouve["lipides"] if trouve else "",
            "fibres_100g": trouve["fibres"] if trouve else "",
            "confiance": niveau,
            "autres_pistes": " | ".join(alternatives),
        })

    chemin = "/home/user/correspondances_aliments.csv"
    with open(chemin, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(sortie[0].keys()), delimiter=";")
        w.writeheader()
        w.writerows(sortie)

    total = len(sortie)
    print(f"{total} ingrédients traités\n")
    print(f"  correspondance exacte          : {stats['exact']:>3}")
    print(f"  correspondance sûre            : {stats['sur']:>3}")
    print(f"  à vérifier (proposition faite) : {stats['moyen']:>3}")
    print(f"  à choisir (aucune trouvée)     : {stats['faible']:>3}")
    print(f"  non alimentaires (ignorés)     : {stats.get('non_alim', 0):>3}")
    utiles = total - stats.get("non_alim", 0)
    reussis = stats["exact"] + stats["sur"]
    print(f"\n  → {reussis}/{utiles} aliments reliés automatiquement ({reussis / max(utiles,1) * 100:.0f} %)")
    print(f"\nfichier écrit : {chemin}")
