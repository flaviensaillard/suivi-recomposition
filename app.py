# -*- coding: utf-8 -*-
"""
ÉQUILIBRE — suivi de recomposition corporelle et de menus.

Stack : Streamlit (interface) + Supabase (base de données cloud) + GitHub (code)
Fonctionne aussi 100 % hors ligne en mode local (SQLite) tant que Supabase
n'est pas configuré.

    streamlit run app.py
"""
from __future__ import annotations

import datetime as dt
import io
import os as _os
import re
import time
import zipfile

import altair as alt
import pandas as pd
import streamlit as st

import sys as _sys   # pour surveiller les modules chargés

import content as C
import seances as SE
import integration as IT
import editeurs as ED
import menus as MN
import corrections as CO
import repas as R
import tableaux as T
from db import LocalStore, SupaStore

#  Le numéro de version du lot de fichiers déposé sur GitHub : les 5 fichiers
#  (celui-ci, editeurs.py, menus.py, pdf_menus.py, repas_plats.py) le portent.
VERSION = "1.0.11"
#  La version attendue de CHAQUE fichier compagnon (voir `_bandeau_fichiers_a_jour`) :
#  ainsi, l'application peut évoluer sans que le bandeau accuse à tort les
#  fichiers qui n'ont pas changé.
VERSIONS_FICHIERS = {"editeurs": "1.0.11", "menus": "1.0.11",
                     "pdf_menus": "1.0.1", "repas_plats": "1.0.1",
                     #  les fichiers « socle » : si l'un d'eux est resté en
                     #  arrière, le bandeau le dit au lieu de dégrader en silence
                     "content": "1.0.9", "corrections": "1.0.8",
                     "tableaux": "1.0.8", "db": "1.0.8"}
APP = "Équilibre"


# ---------------------------------------------------------------------------
#  🧩 TES FICHIERS ARRIVENT-ILS JUSQU'À L'APPLICATION ? (30/09)
#
#  Streamlit garde en mémoire les fichiers .py chargés AU DÉMARRAGE. Quand tu
#  remplaces un fichier sur GitHub et que tu appuies seulement sur F5, le
#  fichier `app.py` est bien relu… mais `editeurs.py` et `menus.py` continuent
#  de tourner dans leur ANCIENNE version. C'est exactement pour ça que la barre
#  de gauche affichait « éditeur 2.8.9 · menus 2.8.9 » alors que tes fichiers
#  étaient bien arrivés (vérifié : ils étaient identiques aux miens).
#
#  Ici, on regarde la date des fichiers sur le disque : ceux qui sont arrivés
#  APRÈS le démarrage de l'application sont rechargés tout de suite, dans
#  l'application en marche. Plus besoin de chercher « Reboot app ».
# ---------------------------------------------------------------------------
def _heure_de_demarrage():
    """L'instant où l'application a démarré (pour reconnaître un fichier arrivé après)."""
    import os as _os
    try:                      # Linux : /proc/self = dossier créé au démarrage du programme
        return _os.stat("/proc/self").st_mtime
    except OSError:
        return None


def _mise_a_jour_sans_redemarrage():
    """Recharge les fichiers .py qui sont plus récents que le démarrage.

    Renvoie la liste des noms de fichiers rechargés (« editeurs.py »…).
    Rien à faire de spécial : si la liste est vide, c'est que tout était déjà
    à jour.
    """
    import importlib
    import json as _json
    import os as _os
    import sys as _sys
    import tempfile

    dossier = _os.path.dirname(_os.path.abspath(__file__))
    demarrage = _heure_de_demarrage()
    #  ce qu'on a DÉJÀ rechargé pendant cette exécution de l'application
    #  (sinon on rechargerait en boucle à chaque clic)
    marque = _os.path.join(tempfile.gettempdir(), f"equilibre_{_os.getpid()}.json")
    try:
        deja = _json.load(open(marque, encoding="utf-8"))
    except Exception:
        deja = {}

    a_recharger = []
    for nom, module in list(_sys.modules.items()):
        if nom in ("__main__", "__mp_main__", "app") or module is None:
            continue
        chemin = getattr(module, "__file__", None)
        if not chemin:
            continue
        chemin = _os.path.abspath(chemin)
        if _os.path.dirname(chemin) != dossier:
            continue                       # ce n'est pas un fichier de l'application
        try:
            mtime = _os.path.getmtime(chemin)
        except OSError:
            continue
        if deja.get(chemin) == mtime:
            continue                       # déjà rechargé, rien de neuf
        #  Le fichier a-t-il été REMPLACÉ pendant que l'application tournait ?
        if demarrage is not None and mtime > demarrage + 2:
            a_recharger.append((nom, chemin, mtime))

    recharges = []
    for nom, chemin, mtime in a_recharger:
        module = _sys.modules.get(nom)
        try:
            importlib.reload(module)
            recharges.append(_os.path.basename(chemin))
            deja[chemin] = mtime
        except Exception:
            pass                           # tant pis : le message ci-dessous prend le relais
    try:
        with open(marque, "w", encoding="utf-8") as f:
            _json.dump(deja, f)
    except Exception:
        pass
    return recharges


FICHIERS_RECHARGES = _mise_a_jour_sans_redemarrage()
if FICHIERS_RECHARGES:
    #  les objets gardés en mémoire (base de menus, connexion) viennent d'une
    #  ancienne version : on les jette pour repartir sur le code rechargé
    for _cle in ("_menus_store", "_menus_version"):
        st.session_state.pop(_cle, None)
    if any(f.startswith("db") for f in FICHIERS_RECHARGES):
        st.session_state.pop("store", None)

# ============================================================================
#  CONFIGURATION
# ============================================================================
#  Le logo (déposé à côté de ce fichier sur GitHub) : s'il n'est pas là,
#  l'application se rabat sur la balance ⚖️ — elle ne plantera jamais pour ça.
LOGO = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "equilibre.png")
ICONE = LOGO if _os.path.exists(LOGO) else "⚖️"

st.set_page_config(page_title=APP, page_icon=ICONE,
                   layout="centered", initial_sidebar_state="collapsed")

# ---------------------------------------------------------------------------
#  MISE EN PAGE (ordinateur d'abord, téléphone ensuite)
#  Objectif : peu de texte, des chiffres qui se lisent d'un coup d'œil, aucune
#  phrase technique à l'écran, et une page qui tient sans scroller pour rien.
# ---------------------------------------------------------------------------
st.markdown("""
<style>
  /* --- la page : large mais pas étirée, et bien respirante --------------- */
  .block-container{padding-top:2.4rem; padding-bottom:4rem; max-width:1080px}
  h1{font-size:1.55rem !important; margin:0 0 .35rem 0 !important; padding:0 !important}
  h2{font-size:1.16rem !important; margin:1.2rem 0 .4rem 0 !important}
  h3{font-size:1.02rem !important; margin:.9rem 0 .3rem 0 !important}
  p, li{line-height:1.55}
  hr{margin:1.1rem 0 !important}

  /* --- les chiffres clés ------------------------------------------------ */
  [data-testid="stMetricValue"]{font-size:1.42rem; line-height:1.25}
  [data-testid="stMetricLabel"]{font-size:.82rem}
  [data-testid="stMetricDelta"]{font-size:.78rem}

  /* --- les boutons : arrondis, jamais coupés --------------------------- */
  .stButton>button{white-space:normal; text-align:center; border-radius:8px;
                   font-weight:500}

  /* --- la couleur de l'application (le vert du logo) sur les boutons
         d'action : sans ça, Streamlit met son rouge par défaut.
         En mode sombre, le vert est ÉCLAIRCI (#14b8a6) et le texte posé
         dessus est foncé : c'est ce qui se lit le mieux. --- */
  [data-testid^="stBaseButton-primary"],
  [data-testid^="stDownloadButton"] button {
      background-color:#14b8a6 !important; border-color:#14b8a6 !important}
  [data-testid^="stBaseButton-primary"]:hover,
  [data-testid^="stDownloadButton"] button:hover {
      background-color:#0fa89a !important; border-color:#0fa89a !important}
  [data-testid^="stBaseButton-primary"] p {color:#04201c !important}

  /* --- les choix horizontaux (« Modifier / Créer ») : de vrais onglets --- */
  div[role="radiogroup"]{gap:.3rem; flex-wrap:wrap}
  div[role="radiogroup"] > label{background:#1f2c36; border:1px solid #2c3b47;
      border-radius:9px; padding:.3rem .65rem; margin:0 .2rem .2rem 0; transition:.12s}
  div[role="radiogroup"] > label:hover{border-color:#3e5261}
  div[role="radiogroup"] > label:has(input:checked){background:#123b38; border-color:#14b8a6}
  div[role="radiogroup"] > label p{font-size:.92rem}

  /* --- les tableaux ---------------------------------------------------- */
  [data-testid="stDataFrame"], [data-testid="stDataEditor"]{font-size:.86rem}

  /* --- les cadres ------------------------------------------------------ */
  .stExpander{border-radius:10px !important}
  [data-testid="stVerticalBlockBorderWrapper"]{border-radius:12px}
  [data-testid="stForm"]{border:1px solid #2c3b47; border-radius:12px; padding:1rem 1.1rem}

  /* --- le petit texte d'aide ------------------------------------------- */
  [data-testid="stCaptionContainer"] p{font-size:.86rem; color:#9fb0bc}

  /* --- « appuie sur Entrée » : inutile, tout réagit tout de suite ------- */
  [data-testid="InputInstructions"]{display:none !important}

  .hint{color:#9fb0bc; font-size:.85rem}
  .bloc-card{background:#17212a; border:1px solid #2c3b47; border-radius:12px;
             padding:.8rem 1rem; margin:.3rem 0 .9rem 0}
  .bloc-title{font-weight:700; color:#eaf2f6; font-size:1rem}
  .sess-a{color:#14b8a6; font-weight:700}
  .sess-b{color:#60a5fa; font-weight:700}

  /* --- téléphone ------------------------------------------------------- */
  @media (max-width:640px){
    .block-container{padding:1rem .8rem 3rem .8rem}
    h1{font-size:1.35rem !important}
    .stButton>button{width:100%; padding:.55rem .7rem; font-size:.95rem}
    [data-testid="stMetricValue"]{font-size:1.25rem}
  }
</style>
""", unsafe_allow_html=True)

D = dt.date


def _libelles_uniques(libelles: list) -> list:
    """Rend une liste de libellés unique (l'application exige des choix distincts).

    Deux aliments peuvent avoir le même nom court (« Yaourt ou lait fermenté ») :
    on ajoute alors un petit numéro « (2) », « (3) » pour pouvoir les distinguer.
    """
    vus, sortie = {}, []
    for lib in libelles:
        n = vus.get(lib, 0) + 1
        vus[lib] = n
        sortie.append(lib if n == 1 else f"{lib}  ({n})")
    return sortie   # affichée dans la barre latérale : permet de vérifier que le déploiement est à jour


# ============================================================================
#  INITIALISATION : stockage + authentification
# ============================================================================
def read_secrets():
    """Lit les Secrets (`.streamlit/secrets.toml` ou Streamlit Cloud) et nettoie les valeurs.

    Depuis la 1.0.3, on peut y ranger aussi ton adresse et ton mot de passe :
    l'application entre alors TOUTE SEULE, sans écran de connexion. Ces deux
    lignes restent dans les Secrets (chez Streamlit), jamais dans le dépôt GitHub
    et jamais visibles par un visiteur.
    """
    try:
        if "supabase" in st.secrets:
            cfg = st.secrets["supabase"]
            url = str(cfg.get("url", "") or "").strip().rstrip("/")
            key = str(cfg.get("anon_key", "") or "").strip()
            if url and key:
                return {
                    "url": url, "anon_key": key,
                    "email": str(cfg.get("email", "") or "").strip(),
                    "password": str(cfg.get("password", "") or ""),
                    #  ta clé personnelle : elle vit dans l'adresse (…?cle=…) et
                    #  n'apparaît nulle part à l'écran, jamais dans GitHub.
                    "cle": str(cfg.get("cle", "") or "").strip(),
                    #  FACULTATIF — le compte « Public » (espace partagé du foyer).
                    #  S'il est renseigné, l'espace partagé ouvre une session avec
                    #  ce compte ; sinon il lit et écrit avec la clé publique de
                    #  l'application (ce qui suffit : vérifié sur la base réelle).
                    "partage_email": str(cfg.get("partage_email", "") or "").strip(),
                    "partage_password": str(cfg.get("partage_password", "") or ""),
                    #  SON ESPACE À ELLE (facultatif) : son compte et sa clé.
                    #  Ses données vivent dans les mêmes tables que les tiennes,
                    #  mais chaque ligne porte son identifiant de compte : la
                    #  base ne lui rend que les siennes (comme à toi les tiennes).
                    "elle_email": str(cfg.get("elle_email", "") or "").strip(),
                    "elle_password": str(cfg.get("elle_password", "") or ""),
                    "cle_elle": str(cfg.get("cle_elle", "") or "").strip(),
                }
    except Exception:
        return None
    return None


def cle_personnelle() -> str:
    """La clé que tu portes dans l'adresse de ton lien personnel (?cle=…)."""
    try:
        v = st.query_params.get("cle", "")
    except Exception:
        return ""
    if isinstance(v, (list, tuple)):
        v = v[0] if v else ""
    return str(v or "").strip()


def espace_actuel() -> str:
    """Dans quel espace suis-je ? « flavien » (toi) ou « elle »."""
    return str(st.session_state.get("espace", "flavien"))


def espaces_rangees(cfg) -> list:
    """Les espaces personnels rangés dans les Secrets : (nom, clé, compte, mdp).

    • « flavien » — ton espace (lignes `cle`, `email`, `password`) ;
    • « elle »    — son espace à elle (lignes `cle_elle`, `elle_email`,
                    `elle_password`), s'il est renseigné.
    """
    out = []
    cfg = cfg or {}
    if (cfg.get("cle") or "").strip() or (cfg.get("email") or "").strip():
        out.append(("flavien", (cfg.get("cle") or "").strip(),
                    (cfg.get("email") or "").strip(), cfg.get("password") or ""))
    if (cfg.get("cle_elle") or "").strip() or (cfg.get("elle_email") or "").strip():
        out.append(("elle", (cfg.get("cle_elle") or "").strip(),
                    (cfg.get("elle_email") or "").strip(), cfg.get("elle_password") or ""))
    return out


def acces_libere(cfg) -> bool:
    """AI-JE LE DROIT D'ENTRER SANS RIEN TAPER ?

    • Si une clé personnelle est rangée dans les Secrets : il faut la retrouver
      dans l'adresse (c'est ton lien personnel, celui que tu mets en favori).
      Quelqu'un qui ouvre l'adresse normale tombe sur l'écran de connexion.
    • Si aucune clé n'est rangée : l'application entre toute seule (comme la
      1.0.3) — tu es chez toi, l'application n'est de toute façon pas accessible
      sans être passé par le compte Streamlit qui la détient.
    """
    import hmac
    if st.session_state.get("cle_ok"):
        return True
    rangees = [(nom, cle) for nom, cle, _c, _m in espaces_rangees(cfg) if cle]
    if not rangees:
        return True                     # aucune clé rangée : comme la 1.0.3
    apportee = cle_personnelle()
    if apportee:
        for nom, cle in rangees:
            if hmac.compare_digest(apportee, cle):
                st.session_state["cle_ok"] = True
                st.session_state["espace"] = nom
                return True
    return False


def adresse_application() -> str:
    """L'adresse de l'application, pour construire ton lien personnel."""
    try:
        entetes = st.context.headers
        hote = (entetes.get("Host") or entetes.get("host") or "").strip()
        if hote:
            protocole = "http" if (":" in hote and "streamlit.app" not in hote) else "https"
            return f"{protocole}://{hote}"
    except Exception:
        pass
    return ""


def lien_personnel(cle: str) -> str:
    base = adresse_application()
    if base:
        return f"{base}/?cle={cle}"
    return f"l'adresse de ton application + ?cle={cle}"


ADRESSE_COMPTES = ("https://supabase.com/dashboard/project/jwqaspdomehuzqwvflri"
                   "/auth/users")


def explique_refus(e) -> str:
    """Traduit un refus de la base en français, avec la marche à suivre.

    La base répond en anglais (« Invalid login credentials ») : personne ne peut
    comprendre ça. On dit ce qui s'est passé et quoi faire, sans jargon.
    """
    t = str(e).lower()
    if "invalid login credentials" in t or "invalid_credentials" in t:
        return ("**l'e-mail ou le mot de passe a été refusé par la base.**\n\n"
                "*Ce n'est pas une panne : l'un des deux ne correspond pas au compte.*\n"
                "1. Vérifie l'adresse exacte du compte : "
                f"[Supabase → Authentication → Users]({ADRESSE_COMPTES}).\n"
                "2. Sur la ligne de ton compte, menu **…** → **Reset password** : "
                "tu reçois un e-mail pour en choisir un nouveau.\n"
                "3. Recopie **cette adresse et ce nouveau mot de passe** dans les "
                "Secrets (lignes `email` et `password`), puis **Reboot** et remets "
                "le lien personnel en favori.")
    if "email not confirmed" in t:
        return ("**l'adresse du compte n'a pas été confirmée dans Supabase.**\n\n"
                f"Va sur [Authentication → Users]({ADRESSE_COMPTES}), menu **…** → "
                "**Confirm email** sur la ligne de ton compte.")
    if any(mot in t for mot in ("name or service not known", "connect", "timed out",
                                "timeout", "network", "temporary failure")):
        return ("**la base n'est pas joignable** (internet, ou projet Supabase en pause).\n\n"
                "Regarde sur [supabase.com/dashboard](https://supabase.com/dashboard) "
                "si le projet est en pause, puis « Restore ». Sinon réessaie dans un "
                "moment.")
    return f"la base a répondu : {e}"


#  « Elle » = son espace personnel (voir les Secrets : `cle_elle`). Ses pages
#  s'adaptent : pas de séances (elle n'en fait pas), pas de séances dans les
#  alertes du tableau de bord.
ELLE = espace_actuel() == "elle"

#  Identifiant neutre, utilisé par l'espace partagé (voir `entrer_en_partage`).
IDENTIFIANT_PARTAGE = "00000000-0000-0000-0000-000000000000"


def demande_partage() -> bool:
    """Vrai quand l'adresse contient `?partage=1` — le lien de la famille.

    C'est le lien que ta femme met en favori : elle l'ouvre, elle est dans
    l'espace partagé. Aucun mot de passe, aucun compte à créer.
    """
    try:
        v = str(st.query_params.get("partage", "") or "").strip().lower()
    except Exception:
        return False
    return v not in ("", "0", "non", "false")


def est_partage() -> bool:
    """Vrai quand cette session est dans l'espace partagé (recettes, menus, courses)."""
    return bool(st.session_state.get("mode_partage"))


def entrer_en_partage(store, cfg) -> None:
    """Ouvrir l'espace partagé — sans rien taper.

    Deux façons, dans cet ordre :
      ① le compte « Public » (lignes `partage_email` / `partage_password` des
         Secrets) : l'application ouvre une session avec lui ;
      ② s'il n'existe pas : la clé publique de l'application suffit — c'est ce
         qui est vérifié sur la base réelle (recettes, menus et courses
         entièrement accessibles ; ton suivi personnel renvoie zéro ligne).
    """
    #  ⓘ Pourquoi cet identifiant « vide » :
    #  l'application lit le profil au démarrage. Sans compte, cette lecture
    #  partait avec la valeur « None », que PostgreSQL refuse
    #  (« invalid input syntax for type uuid »). Avec cet identifiant neutre,
    #  la requête est valide et la base répond « rien » : c'est exactement ce
    #  qu'on veut — l'espace partagé ne voit aucune donnée personnelle.
    store.user_id = IDENTIFIANT_PARTAGE
    pe = str((cfg or {}).get("partage_email") or "").strip()
    pm = str((cfg or {}).get("partage_password") or "")
    if pe and pm:
        try:
            st.session_state["sb_session"] = store.sign_in(pe, pm)
            st.session_state.pop("_echec_partage", None)
        except Exception as e:
            st.session_state["_echec_partage"] = explique_refus(e)
    st.session_state["mode_partage"] = True


def connexion_automatique(store: "SupaStore", cfg) -> bool:
    """ENTRER SANS RIEN TAPER.

    Tes identifiants sont rangés dans les Secrets : on s'en sert pour ouvrir ta
    session au démarrage. Si ça ne marche pas (mot de passe changé depuis, par
    exemple), on retombe proprement sur l'écran de connexion, avec l'explication.
    """
    if st.session_state.get("sans_auto"):
        return False                     # tu as demandé à te déconnecter : on respecte
    if not acces_libere(cfg):
        #  pas de clé personnelle dans l'adresse : on ne donne rien, on demande
        #  à se connecter. C'est ce que voit quelqu'un qui n'a pas ton lien.
        return False
    #  GARDE-FOU : si la session ne tient pas (panne, réseau, réglage), on ne
    #  s'acharne pas — au bout de 3 essais on affiche l'écran de connexion.
    essais = st.session_state.get("_auto_essais", 0)
    if essais >= 3:
        st.session_state["_echec_auto"] = ("la session n'a pas tenu après 3 essais "
                                           "(internet instable ?).")
        return False
    espace_voulu = st.session_state.get("espace", "flavien")
    comptes = {nom: (c, m) for nom, _cle, c, m in espaces_rangees(cfg)}
    email, mdp = comptes.get(espace_voulu, ("", ""))
    if not (email and mdp):
        if espace_voulu == "elle":
            st.session_state["_echec_auto"] = (
                "**l'espace de ton épouse n'est pas encore configuré.**\n\n"
                "Ajoute ses trois lignes dans les Secrets (`elle_email`, "
                "`elle_password`, `cle_elle`), puis **Reboot**.")
        return False
    st.session_state["_auto_essais"] = essais + 1
    try:
        st.session_state["sb_session"] = store.sign_in(email, mdp)
        st.session_state.pop("_echec_auto", None)
        return True
    except Exception as e:
        st.session_state["_echec_auto"] = explique_refus(e)
        return False


def problemes_secrets(cfg) -> list:
    """Contrôles de bon sens : mieux vaut s'arrêter net que d'écrire au mauvais endroit."""
    pbs = []
    if not cfg["url"].startswith("http") or ".supabase.co" not in cfg["url"]:
        pbs.append("**url** doit ressembler à `https://xxxxx.supabase.co`. Tu as peut-être collé "
                   "l'adresse du tableau de bord (`supabase.com/dashboard/project/...`) au lieu de "
                   "la « Project URL ».")
    k = cfg["anon_key"]
    if k.startswith("sb_secret_") or "service_role" in k:
        pbs.append("Tu as collé une **clé secrète** (`sb_secret_...` ou `service_role`). Cette clé "
                   "contourne toutes les sécurités : elle ne doit jamais servir ici. Prends la clé "
                   "**publishable** (`sb_publishable_...`) ou l'ancienne clé **anon public** "
                   "(commençant par `eyJ`).")
    elif not (k.startswith("sb_publishable_") or k.startswith("eyJ")):
        pbs.append("**anon_key** ne ressemble ni à une clé `sb_publishable_...`, ni à une ancienne "
                   "clé `anon` commençant par `eyJ`. Vérifie que tu n'as pas copié un mot de passe "
                   "de base de données ou une référence de projet.")
    return pbs


def login_page(store: SupaStore, cfg=None):
    # ---- d'abord : entrer tout seul, si les identifiants sont dans les Secrets
    if connexion_automatique(store, cfg):
        st.rerun()
    if _os.path.exists(LOGO):
        st.image(LOGO, width=96)
    st.title(APP)
    st.caption("Connexion à ton espace")
    echec = st.session_state.pop("_echec_auto", None)
    if echec:
        st.warning("L'identification automatique n'a pas fonctionné : " + echec +
                   "\n\n*(Tu peux te connecter à la main ci-dessous, puis remettre à "
                   "jour les lignes `email` et `password` dans les Secrets.)*")
    elif (cfg or {}).get("cle"):
        st.caption("🔒 Tu es arrivé sur l'adresse normale : l'entrée directe demande ton "
                   "**lien personnel** (celui qui finit par `?cle=…`). Mets-le en favori sur "
                   "tes appareils — sinon connecte-toi ci-dessous.")
    elif (cfg or {}).get("email"):
        st.info("L'identification automatique est prête mais désactivée pour cette session. "
                "Tu peux la relancer ci-dessous.")
    mode = st.radio("Action", ["Se connecter", "Créer un compte"], horizontal=True, label_visibility="collapsed")
    with st.form("login"):
        email = st.text_input("Email")
        pwd = st.text_input("Mot de passe", type="password")
        ok = st.form_submit_button("Valider", type="primary")
    if ok:
        try:
            if mode == "Créer un compte":
                if store.sign_up(email, pwd):
                    st.success("Compte créé. Connecte-toi maintenant (valide l'email si Supabase le demande).")
            else:
                sess = store.sign_in(email, pwd)
                st.session_state["sb_session"] = sess
                #  ⓘ on note QUI vient de se connecter : si c'est l'adresse de
                #  son espace, ses pages s'adaptent (pas de séances, pas de
                #  réglages de Flavien) et la barre de gauche affiche son nom.
                for _nom, _cle, _c, _m in espaces_rangees(cfg or {}):
                    if _c and _c.lower() == str(email).strip().lower():
                        st.session_state["espace"] = _nom
                st.rerun()
        except Exception as e:
            st.error("Échec : " + explique_refus(e))
    st.divider()
    st.markdown("#### 👨‍👩‍👧‍👦 Espace partagé (Public)")
    st.caption("Les recettes, les menus de la semaine et la liste de courses — pour la "
               "famille. **Aucun mot de passe à taper**, et aucun accès à ton suivi "
               "personnel (repas, pesées, séances, mesures).")
    if st.button("👨‍👩‍👧‍👦 Entrer dans l'espace partagé", use_container_width=True):
        st.session_state["_vers_partage"] = True
        st.rerun()
    st.caption("💡 Le lien à mettre en favori : **l'adresse de l'application suivie de "
               "`?partage=1`** — il ouvre directement cet espace.")
    if (cfg or {}).get("email") and st.session_state.get("sans_auto"):
        if st.button("🔓 Revenir à l'identification automatique"):
            st.session_state.pop("sans_auto", None)
            st.session_state.pop("store", None)
            st.rerun()
    st.stop()


import json as _json
import os as _os


def menus_store():
    """Lecteur de la base de menus (tes 4 tables), mis en cache pour la session.

    Sans Supabase configuré : renvoie un extrait de démonstration, pour que tu
    puisses voir la page tout de suite (les chiffres sont alors incomplets).
    """
    VERSION_STORE = "30-09-2026r"      # à changer à chaque mise à jour du moteur
    ms = st.session_state.get("_menus_store")
    force = st.session_state.get("_menus_store_forcee")     # magasin imposé (tests)
    if ms is not None and (force or st.session_state.get("_menus_version") == VERSION_STORE):
        return ms
    st.session_state.pop("_menus_store", None)      # version plus ancienne : on repart
    if getattr(store, "kind", None) == "supabase" and getattr(store, "client", None) is not None:
        ms = MN.MenusStore(store.client)
    else:
        chemin = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)),
                               "data", "demo_menus.json")
        if not _os.path.exists(chemin):
            return None
        try:
            with open(chemin, encoding="utf-8") as f:
                donnees = _json.load(f)
            ms = MN.MenusStore(None)
            ms._cache = donnees
            ms.demo = True
        except Exception:
            return None
    st.session_state["_menus_store"] = ms
    st.session_state["_menus_version"] = VERSION_STORE
    return ms


def init_store():
    if "store" in st.session_state:
        return st.session_state["store"]
    cfg = read_secrets()
    if cfg:
        pbs = problemes_secrets(cfg)
        if pbs:
            st.error("### ⛔ Configuration Supabase à corriger\n\n"
                     + "\n\n".join(f"- {p}" for p in pbs)
                     + "\n\n**Où corriger :** Streamlit Cloud → ton application → **⋮ → Settings → "
                       "Secrets**, puis **Save** et **Reboot**. *(En local : le fichier "
                       "`.streamlit/secrets.toml`.)*")
            st.stop()
        store = SupaStore(cfg["url"], cfg["anon_key"])
        st.session_state["auto_connexion"] = bool(cfg.get("email") and cfg.get("password"))
        sess = st.session_state.get("sb_session")
        if sess:
            try:
                store.resume(sess)
                #  le droit d'accès expire au bout d'une heure : on vérifie qu'il
                #  est encore bon, sinon on se reconnecte tout seul (avec les
                #  identifiants des Secrets) au lieu d'afficher une erreur.
                if not store.session_valide():
                    st.session_state.pop("sb_session", None)
            except Exception:
                st.session_state.pop("sb_session", None)
        if not st.session_state.get("sb_session"):
            #  ⓘ L'ESPACE PARTAGÉ PASSE AVANT L'ÉCRAN DE CONNEXION.
            #  Si l'adresse contient ?partage=1 (ou si on a appuyé sur le bouton
            #  « Entrer dans l'espace partagé »), on ouvre l'espace du foyer :
            #  recettes, menus, courses. Rien à taper.
            #  Ta clé personnelle garde la priorité : avec elle, ton espace.
            #  (la clé personnelle, si elle est RÉGLÉE et CORRECTE, garde la
            #   priorité : `acces_libere` seul ne suffit pas ici, parce qu'il
            #   répond « oui » quand aucune clé n'est rangée du tout.)
            _cle_perso_ok = bool(str((cfg or {}).get("cle") or "").strip()) and acces_libere(cfg)
            if not _cle_perso_ok and (st.session_state.pop("_vers_partage", False)
                                      or demande_partage()):
                entrer_en_partage(store, cfg)
            else:
                login_page(store, cfg)
        st.session_state["store"] = store
        return store
    store = LocalStore()
    st.session_state["store"] = store
    return store


store = init_store()
PROFILE = store.profile() or {}


def prof(key, default):
    v = PROFILE.get(key)
    return default if v in (None, "") else v


#  ⓘ PROFIL VIERGE (l'espace de ta femme au premier jour) : on n'affiche
#  AUCUNE de tes valeurs. Tant qu'elle n'a pas enregistré son profil dans
#  ⚙️ Réglages, l'application travaille avec des repères neutres — jamais les
#  tiens (sinon ses écrans afficheraient ton poids et tes 130 g de protéines).
PROFIL_VIERGE = not PROFILE
_NEUTRE = dict(height_cm=170.0, start_weight_kg=70.0, target_weight_kg=70.0,
               target_protein_g=100, target_carbs_g=140, target_fat_g=55,
               target_kcal=1900, tdee_kcal=2200)


def _rep(cle, valeur_perso):
    """Le repère à utiliser : tes valeurs, ou des repères neutres si profil vide."""
    return _NEUTRE[cle] if PROFIL_VIERGE else valeur_perso


TARGET_W = float(prof("target_weight_kg", _rep("target_weight_kg", C.TARGET_WEIGHT)))
TARGET_P = int(prof("target_protein_g", _rep("target_protein_g", C.TARGET_PROTEIN)))
TARGET_G = int(prof("target_carbs_g", _rep("target_carbs_g", getattr(C, "TARGET_CARBS", 140))))
TARGET_L = int(prof("target_fat_g", _rep("target_fat_g", getattr(C, "TARGET_FAT", 50))))
TARGET_KCAL = int(prof("target_kcal", _rep("target_kcal", getattr(C, "TARGET_KCAL", 1700))))
START_W = float(prof("start_weight_kg", _rep("start_weight_kg", C.START_WEIGHT)))
HEIGHT = float(prof("height_cm", _rep("height_cm", C.HEIGHT_CM)))


def _enregistrer_profil(data: dict):
    """Enregistre le profil. Si la base n'a pas encore les colonnes glucides/lipides/calories,
    on enregistre quand même le reste et on le dit clairement à l'utilisateur."""
    try:
        store.save_profile(data)
        return True, ""
    except Exception:
        leger = {k: v for k, v in data.items()
                 if k not in ("target_carbs_g", "target_fat_g", "target_kcal")}
        try:
            store.save_profile(leger)
        except Exception as e:
            return False, f"Impossible d'enregistrer le profil : {e}"
        return False, ("Le reste du profil est bien enregistré, mais tes cibles glucides / lipides / "
                       "calories n'existent pas encore dans ta base. Lance le fichier "
                       "19_objectifs.sql dans Supabase (SQL Editor), puis réenregistre.")


# ============================================================================
#  OUTILS
# ============================================================================
def _val(ligne, cle, defaut=None):
    """Lit une valeur d'une ligne sans jamais planter (colonne absente, case vide…)."""
    if ligne is None:
        return defaut
    try:
        v = ligne.get(cle)
    except Exception:
        return defaut
    if v is None:
        return defaut
    try:
        if pd.isna(v):
            return defaut
    except (TypeError, ValueError):
        pass
    return v


def _dernier(daily, cur, champ, defaut):
    """La valeur à proposer : celle du jour, sinon la plus récente, sinon un défaut."""
    v = _val(cur, champ)
    if v is not None:
        return v
    try:
        if not daily.empty and champ in daily.columns:
            serie = pd.to_numeric(daily[champ], errors="coerce").dropna()
            if not serie.empty:
                return serie.iloc[-1]
    except Exception:
        pass
    return defaut


COLS_DAILY = ("log_date", "weight_kg", "body_fat_pct", "steps", "sleep_h", "protein_g",
              "kcal", "activity", "energy", "notes")
COLS_MES = ("meas_date", "waist_cm", "hips_cm", "chest_cm", "neck_cm", "arm_cm",
            "thigh_cm", "photos", "notes")


def _colonnes(df: pd.DataFrame, attendues) -> pd.DataFrame:
    """Garantit que les colonnes existent : une colonne absente ne fait plus planter
    une page (cas d'une base plus ancienne)."""
    for c in attendues:
        if c not in df.columns:
            df[c] = None
    return df


def load_daily() -> pd.DataFrame:
    df = store.daily_df()
    if df.empty:
        return pd.DataFrame(columns=list(COLS_DAILY))
    df = _colonnes(df, COLS_DAILY)
    df["log_date"] = pd.to_datetime(df["log_date"], errors="coerce").dt.date
    for c in ("weight_kg", "body_fat_pct", "sleep_h"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df.sort_values("log_date").reset_index(drop=True)


def load_meas() -> pd.DataFrame:
    """Les mensurations, avec toutes les colonnes attendues (jamais d'erreur)."""
    df = _colonnes(store.meas_df(), COLS_MES)
    if df.empty:
        return df
    df["meas_date"] = pd.to_datetime(df["meas_date"], errors="coerce").dt.date
    for c in ("waist_cm", "hips_cm", "chest_cm", "neck_cm", "arm_cm", "thigh_cm"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df.sort_values("meas_date").reset_index(drop=True)


def rolling(df: pd.DataFrame, col: str, n=7) -> pd.DataFrame:
    out = df[["log_date", col]].dropna().copy()
    if out.empty:
        return out
    out["moy7"] = out[col].rolling(n, min_periods=1).mean()
    return out


def mean_since(df, col, days, end=None):
    if df.empty or col not in df:
        return None
    end = end or D.today()
    start = end - dt.timedelta(days=days)
    s = df[(df["log_date"] > start) & (df["log_date"] <= end)][col].dropna()
    return None if s.empty else float(s.mean())


def protein_by_day(since=None):
    df = store.protein_df(since=since)
    if df.empty:
        return pd.DataFrame(columns=["entry_date", "total"])
    df["entry_date"] = pd.to_datetime(df["entry_date"]).dt.date
    return df.groupby("entry_date", as_index=False)["protein_g"].sum().rename(columns={"protein_g": "total"})


def days_since_start():
    return (D.today() - D(2026, 8, 15)).days


def sessions_this_week():
    monday = D.today() - dt.timedelta(days=D.today().weekday())
    df = store.workouts_df()
    if df.empty:
        return 0, []
    df = df.copy()
    df["session_date"] = pd.to_datetime(df["session_date"]).dt.date
    df = df[df["session_date"] >= monday]
    return len(df), sorted(df["session"].tolist())


def last_sets(exercise, session, before: D):
    df = store.sets_df()
    if df.empty:
        return None
    df = df.copy()
    df["set_date"] = pd.to_datetime(df["set_date"]).dt.date
    sub = df[(df["exercise"] == exercise) & (df["session"] == session) & (df["set_date"] < before)]
    if sub.empty:
        return None
    d = sub["set_date"].max()
    rows = sub[sub["set_date"] == d].sort_values("set_no")
    return dict(date=d, reps=" / ".join(str(int(r)) for r in rows["reps"].dropna()),
                variant=rows["variant"].iloc[0] if "variant" in rows else "",
                load=rows["load_kg"].iloc[0] if "load_kg" in rows else None)


def top_of_range(cible: str):
    nums = [int(n) for n in re.findall(r"\d+", cible)]
    return max(nums) if nums else None


TABS_A_ANALYSER = list(dict.fromkeys(
    IT.TABLES_PLAN + IT.TABLES_RECETTES + IT.TABLES_INGREDIENTS + IT.TABLES_LIAISON))


def contexte_menus():
    """Analyse la base de menus une seule fois et renvoie (client, tables, correspondance)."""
    if store.kind != "supabase":
        return None, {}, {}
    client = store.client
    if "it_ctx" not in st.session_state:
        tables = IT.analyser(client, TABS_A_ANALYSER)
        mapping = IT.affiner_mapping(client, IT.deviner_mapping(tables), tables) if tables else {}
        st.session_state["it_ctx"] = {"tables": tables, "mapping": mapping}
    ctx = st.session_state["it_ctx"]
    sauve = st.session_state.get("it_map") or lire_map(store) or {}
    # La correspondance enregistrée peut être ANCIENNE (créée avant l'import de la
    # base française) : on la complète, et on la réenregistre si elle a changé.
    mapping = IT.mapping_a_jour(sauve, ctx["mapping"], ctx["tables"])
    if mapping and mapping != sauve:
        ecrire_map(store, mapping)
        st.session_state["it_map"] = mapping
    return client, ctx["tables"], mapping


def fmt(v, suffix="", nd=1):
    return "—" if v is None or (isinstance(v, float) and pd.isna(v)) else f"{v:.{nd}f}{suffix}"


def lire_map(st) -> dict:
    """Lit la correspondance de colonnes sans jamais faire planter la page.

    Si la méthode n'existe pas (version ancienne du fichier db.py) ou si la table
    n'est pas encore créée, on renvoie simplement un dictionnaire vide : la page
    se contente alors de relancer la détection automatique.
    """
    f = getattr(st, "get_map", None)
    if callable(f):
        try:
            return f() or {}
        except Exception:
            return {}
    return {}


def ecrire_map(st, mapping: dict) -> bool:
    f = getattr(st, "save_map", None)
    if callable(f):
        try:
            f(mapping)
            return True
        except Exception:
            return False
    return False


def page_safe(fonction):
    """Filet de sécurité : une page ne doit jamais afficher une erreur brute."""
    def enveloppe(*args, **kwargs):
        try:
            return fonction(*args, **kwargs)
        except Exception as e:
            st.error("**Cette page a rencontré un problème — le reste de l'application fonctionne normalement.**")
            st.markdown(f"Type : `{type(e).__name__}` · Message : `{e}`")
            with st.expander("🔬 Détail technique (à copier au coach)"):
                import traceback
                st.code(traceback.format_exc(), language="text")
                st.caption("Copie-moi ce bloc et je corrige en une réponse.")
            st.info("Pistes rapides : l'application est-elle bien en **Supabase (synchronisé)** ? "
                    "As-tu bien relancé **`schema.sql`** après la dernière mise à jour ?")
            return None
    enveloppe.__name__ = getattr(fonction, "__name__", "page")
    return enveloppe


# ============================================================================
#  PAGE 1 — TABLEAU DE BORD
# ============================================================================
def page_dashboard():
    st.title("🏠 Tableau de bord")
    daily = load_daily()
    meas = load_meas()
    prot = protein_by_day()
    phase, kcal_t = C.phase_for(D.today())

    w_avg = mean_since(daily, "weight_kg", 7)
    w_prev = mean_since(daily, "weight_kg", 7, D.today() - dt.timedelta(days=7))
    bf_avg = mean_since(daily, "body_fat_pct", 7)
    p_avg = mean_since(prot.rename(columns={"entry_date": "log_date", "total": "protein_g"}),
                       "protein_g", 7) if not prot.empty else None
    n_sess, sess_list = sessions_this_week()

    st.markdown(f"**Phase actuelle :** {phase} · objectif **{TARGET_KCAL} kcal** / jour · "
                f"**{TARGET_P} g de protéines** · **{TARGET_G} g de glucides** · **{TARGET_L} g de lipides**")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Poids moyen 7 j", fmt(w_avg, " kg", 2),
              None if (w_avg is None or w_prev is None) else f"{w_avg - w_prev:+.2f} kg")
    waist = None if meas.empty else (None if meas["waist_cm"].dropna().empty else float(meas["waist_cm"].dropna().iloc[-1]))
    waist_start = None if meas.empty else (None if meas["waist_cm"].dropna().empty else float(meas["waist_cm"].dropna().iloc[0]))
    c2.metric("Tour de taille", fmt(waist, " cm"),
              None if (waist is None or waist_start is None) else f"{waist - waist_start:+.1f} cm")
    #  La masse grasse s'affiche en KILOS (demandé le 01/10) : c'est ce que dit
    #  la balance, et c'est plus parlant que le pourcentage. Le % reste écrit
    #  en dessous, parce qu'il ne dépend pas du poids du jour.
    _gras_kg = None if (bf_avg is None or w_avg is None) else C.fat_mass_kg(w_avg, bf_avg)
    c3.metric("Masse grasse (7 j)", fmt(_gras_kg, " kg"),
              None if bf_avg is None else f"≈ {bf_avg:.1f} % de ton poids")
    c4.metric("Protéines (7 j)", fmt(p_avg, " g", 0), f"cible {TARGET_P} g")

    # progression vers l'objectif
    if w_avg and abs(START_W - TARGET_W) > 0.01:
        done = START_W - w_avg
        total = START_W - TARGET_W
        st.progress(max(0.0, min(1.0, done / total)),
                    text=f"Objectif 31 déc : **{TARGET_W:.0f} kg** — "
                         f"{done:.1f} kg perdus sur {total:.1f} kg ({max(0, min(100, int(done/total*100)))} %) · "
                         f"reste {max(0.0, w_avg - TARGET_W):.1f} kg")

    # graphique poids
    if not daily["weight_kg"].dropna().empty:
        r = rolling(daily, "weight_kg")
        r = r.rename(columns={"log_date": "date", "weight_kg": "Poids", "moy7": "Moyenne 7 jours"})
        melt = r.melt("date", ["Poids", "Moyenne 7 jours"], var_name="Série", value_name="kg")
        line = alt.Chart(melt).mark_line().encode(
            x=alt.X("date:T", title=None),
            y=alt.Y("kg:Q", scale=alt.Scale(zero=False), title="kg"),
            color=alt.Color("Série:N", scale=alt.Scale(
                domain=["Poids", "Moyenne 7 jours"], range=["#7dd3fc", "#14b8a6"]),
                legend=alt.Legend(orient="bottom")),
            strokeWidth=alt.condition(alt.datum["Série"] == "Moyenne 7 jours",
                                      alt.value(3), alt.value(1.4)),
        ).properties(height=260, width="container")
        rule = alt.Chart(pd.DataFrame({"y": [TARGET_W]})).mark_rule(
            color="#fbbf24", strokeDash=[5, 4]).encode(y="y:Q")
        st.altair_chart(line + rule)

    # état du jour
    st.subheader("Aujourd'hui")
    today = D.today()
    row = daily[daily["log_date"] == today]
    p_today = 0 if prot.empty else int(prot[prot["entry_date"] == today]["total"].sum())
    lined = lambda ok: "✅" if ok else "⬜"
    _etat = [f"{lined(not row.empty)} **Pesée du matin**",
             f"{lined(p_today >= TARGET_P)} **Protéines {p_today}/{TARGET_P} g**"]
    if not ELLE:
        _etat.append(
            f"{lined(n_sess >= (2 if today.weekday() >= 4 else 1))} "
            f"**Séances cette semaine : {n_sess}/2**"
            f"{' (' + ', '.join(sess_list) + ')' if sess_list else ''}")
    _etat.append(f"{lined(not meas.empty)} **Mensurations**")
    st.markdown("  ·  ".join(_etat))
    if row.empty:
        st.info("Pense à enregistrer ta pesée du matin (page **⚖️ Pesée**).")

    # alertes coach
    alertes = []
    if w_prev and w_avg and (w_prev - w_avg) / 7 > 0.115:
        alertes.append("Perte > 0,8 kg/semaine → **ajoute 200 kcal** (glucides).")
    if p_avg is not None and p_avg < TARGET_P - 15:
        alertes.append(f"Protéines à {p_avg:.0f} g/j : c'est le levier n°1. Ajoute un shaker à 10 h 30 et 200 g de fromage blanc à 16 h.")
    if not ELLE and n_sess < 2 and today.weekday() >= 4:
        alertes.append("Il te reste une séance à faire cette semaine (lundi/vendredi).")
    if alertes:
        with st.container(border=True):
            st.markdown("**🧭 Ce que dit ton coach cette semaine**")
            for a in alertes:
                st.markdown(f"- {a}")

    with st.expander("⚡ Signaux d'alerte : le déficit est trop fort"):
        st.markdown("Si **deux** de ces signes apparaissent : +200 kcal immédiatement (glucides).\n\n"
                    "- Perte > 0,8 kg/semaine après la 2ᵉ semaine de déficit\n"
                    "- Baisse de force > 10 % sur 2 semaines\n"
                    "- Sommeil agité, réveils nocturnes\n"
                    "- Frilosité, mains froides\n"
                    "- Libido en chute, envies de sucre incontrôlables\n"
                    + ("" if ELLE else
                       "\n- Récupération du rugby > 3 jours, blessures à répétition"))


# ============================================================================
#  PAGE 2 — PESÉE DU JOUR
# ============================================================================
def page_pesee():
    st.title("⚖️ Pesée & tendance")
    st.caption("À jeun, même balance, même heure — c'est la **moyenne 7 jours** qui compte.")
    daily = load_daily()
    today = D.today()
    existing = daily[daily["log_date"] == today]
    cur = existing.iloc[0] if not existing.empty else None

    ACTIVITES = ["Repos", "Séance A", "Séance B", "Rugby", "Marche", "Musique", "Autre"]
    deja = _val(cur, "activity")
    with st.form("pesee"):
        c1, c2 = st.columns(2)
        with c1:
            d = st.date_input("Date", value=today, max_value=today, format="DD/MM/YYYY")
            poids = st.number_input("Poids (kg)", min_value=50.0, max_value=140.0, step=0.1,
                                    format="%.1f",
                                    value=float(MN.borne(
                                        _dernier(daily, cur, "weight_kg", 80.0),
                                        50.0, 140.0, 80.0)))
            #  ⓘ LA MASSE GRASSE SE SAISIT EN KILOS (01/10) : c'est ce que la
            #  balance affiche, et plus besoin de calculer un pourcentage.
            #  L'application convertit en % pour le rangement : c'est le % que
            #  suit la moyenne 7 jours.
            _pct_prec = float(MN.borne(_dernier(daily, cur, "body_fat_pct", 18.8),
                                       3.0, 60.0, 18.8))
            bf_kg = st.number_input(
                "Masse grasse (kg)", min_value=2.0, max_value=90.0, step=0.1,
                format="%.1f",
                value=float(MN.borne(C.fat_mass_kg(poids, _pct_prec) or 14.0, 2.0, 90.0, 14.0)),
                help="Balance à impédance (Tefal) : la valeur en kilos, telle qu'elle "
                     "s'affiche. L'application en déduit le pourcentage et garde les deux.")
            bf = float(C.masse_grasse_pct(poids, bf_kg) or _pct_prec)
            st.caption(f"↳ soit **{bf:.1f} %** de ton poids ({poids:.1f} kg)")
            pas = st.number_input("Pas", min_value=0, max_value=40000, step=250,
                                  value=int(MN.borne(_dernier(daily, cur, "steps", 10000),
                                                     0, 40000, 10000)))
        with c2:
            sommeil = st.number_input("Sommeil (h)", min_value=3.0, max_value=12.0, step=0.5,
                                      format="%.1f",
                                      value=float(MN.borne(
                                          _dernier(daily, cur, "sleep_h", 7.5),
                                          3.0, 12.0, 7.5)))
            activite = st.selectbox("Activité du jour", ACTIVITES,
                                    index=ACTIVITES.index(deja) if deja in ACTIVITES else 0)
            energie = st.slider("Énergie (1-10)", 1, 10,
                                int(MN.borne(_dernier(daily, cur, "energy", 7), 1, 10, 7)))
            notes = st.text_area("Notes (faim, humeur, écart…)",
                                 value=str(_val(cur, "notes") or ""), height=80)
        ok = st.form_submit_button("💾 Enregistrer la journée", type="primary", width="stretch")
    if ok:
        store.save_daily(dict(log_date=d, weight_kg=poids, body_fat_pct=bf, steps=int(pas),
                              sleep_h=sommeil, activity=activite, energy=int(energie), notes=notes))
        st.success("Journée enregistrée.")
        st.rerun()

    if bf and poids:
        st.caption(f"Lecture : **{C.fat_mass_kg(poids, bf)} kg de masse grasse** ({bf:.1f} % de "
                   f"{poids:.1f} kg) et **{C.lean_mass_kg(poids, bf)} kg de masse maigre** · "
                   f"IMC {C.bmi(poids, HEIGHT)}.")

    st.subheader("Tendance")
    r = rolling(daily, "weight_kg")
    if not r.empty:
        r2 = r.rename(columns={"log_date": "date", "weight_kg": "Poids", "moy7": "Moyenne 7 jours"})
        melt = r2.melt("date", ["Poids", "Moyenne 7 jours"], var_name="Série", value_name="kg")
        ch = alt.Chart(melt).mark_line().encode(
            x=alt.X("date:T", title=None), y=alt.Y("kg:Q", scale=alt.Scale(zero=False), title="kg"),
            color=alt.Color("Série:N", legend=alt.Legend(orient="bottom"), scale=alt.Scale(
                domain=["Poids", "Moyenne 7 jours"], range=["#7dd3fc", "#14b8a6"])),
            strokeWidth=alt.condition(alt.datum["Série"] == "Moyenne 7 jours", alt.value(3), alt.value(1.2)),
        ).properties(height=240, width="container")
        st.altair_chart(ch + alt.Chart(pd.DataFrame({"y": [TARGET_W]})).mark_rule(
            color="#fbbf24", strokeDash=[5, 4]).encode(y="y:Q"))

    if not daily.empty:
        st.markdown("**Mes 14 derniers jours** — *clique dans une case pour corriger*")
        last = daily.sort_values("log_date", ascending=False).head(14)[
            ["log_date", "weight_kg", "body_fat_pct", "steps", "sleep_h", "activity", "energy"]]
        last = last.set_index(last["log_date"].astype(str))
        last = last.rename(columns={
            "log_date": "Date", "weight_kg": "Poids", "steps": "Pas",
            "sleep_h": "Sommeil (h)", "activity": "Activité", "energy": "Énergie"})
        last["Date"] = pd.to_datetime(last["Date"]).dt.date
        #  la masse grasse est AFFICHÉE ET MODIFIÉE EN KILOS (la base garde le %) :
        #  on la calcule à partir du poids de la journée.
        last["Masse grasse (kg)"] = [
            C.fat_mass_kg(p, pct) if (p and pct) else None
            for p, pct in zip(last["Poids"], last["body_fat_pct"])]
        last = last[["Date", "Poids", "Masse grasse (kg)", "Pas", "Sommeil (h)",
                     "Activité", "Énergie"]]
        T.tableau_editable(
            last, cle="pesee",
            colonnes={"Date": T.col_jour("Date"),
                      "Poids": T.col_nombre("Poids", 40, 150, 0.1),
                      "Masse grasse (kg)": T.col_nombre("Masse grasse (kg)", 2, 90, 0.1),
                      "Pas": T.col_entier("Pas", 0, 40000, 500),
                      "Sommeil (h)": T.col_nombre("Sommeil", 3, 12, 0.5, 1),
                      "Activité": T.col_choix("Activité", ["Repos", "Séance A", "Séance B",
                                                           "Rugby", "Marche", "Musique", "Autre"]),
                      "Énergie": T.col_entier("Énergie (1-10)", 1, 10)},
            sauver=lambda jour, ch: CO.corriger_jour(store, jour, ch),
            supprimer=lambda jour: (store.delete_daily(jour), True)[1],
            hauteur=330,
            aide="Corrige ici si tu t'es trompé : le poids, la **masse grasse en kilos**, les pas, "
                 "le sommeil… Tu peux même **changer la date** d'une journée (si tu l'as saisie "
                 "le mauvais jour) : la ligne sera recopiée sous le bon jour. Coche 🗑️ pour "
                 "supprimer une journée. Rien n'est enregistré tant que tu n'as pas cliqué sur "
                 "**💾 Enregistrer les corrections**.")


# ============================================================================
#  PAGE 3 — MENSURATIONS
# ============================================================================
def page_mensurations():
    st.title("📏 Mensurations")
    st.caption("Tour de taille au nombril, lundi matin à jeun.")
    meas = load_meas()
    today = D.today()
    last_meas = None if meas.empty else meas.iloc[-1]

    with st.form("mens"):
        c1, c2 = st.columns(2)
        with c1:
            d = st.date_input("Date", value=today, max_value=today, format="DD/MM/YYYY")
            taille = st.number_input("Tour de taille — nombril (cm)", 50.0, 160.0, step=0.1,
                                     format="%.1f",
                                     value=float(MN.borne(
                                         _dernier(meas, last_meas, "waist_cm", 90.0),
                                         50.0, 160.0, 90.0)))
            hanches = st.number_input("Hanches (cm)", 50.0, 160.0, step=0.1, format="%.1f",
                                      value=float(MN.borne(
                                          _dernier(meas, last_meas, "hips_cm", 98.0),
                                          50.0, 160.0, 98.0)))
            poitrine = st.number_input("Poitrine (cm)", 50.0, 160.0, step=0.1, format="%.1f",
                                       value=float(MN.borne(
                                           _dernier(meas, last_meas, "chest_cm", 102.0),
                                           50.0, 160.0, 102.0)))
        with c2:
            cou = st.number_input("Tour de cou (cm)", 25.0, 60.0, step=0.1, format="%.1f",
                                  value=float(MN.borne(
                                      _dernier(meas, last_meas, "neck_cm", 39.0),
                                      25.0, 60.0, 39.0)),
                                  help="Sert au calcul Marine — deuxième estimation du % "
                                       "de graisse.")
            bras = st.number_input("Bras contracté (cm)", 20.0, 60.0, step=0.1, format="%.1f",
                                   value=float(MN.borne(
                                       _dernier(meas, last_meas, "arm_cm", 36.0),
                                       20.0, 60.0, 36.0)))
            cuisse = st.number_input("Cuisse (cm)", 30.0, 90.0, step=0.1, format="%.1f",
                                     value=float(MN.borne(
                                         _dernier(meas, last_meas, "thigh_cm", 57.0),
                                         30.0, 90.0, 57.0)))
            photos = st.checkbox("Photos face / profil / dos faites", value=False)
        notes = st.text_input("Observations", value="")
        ok = st.form_submit_button("💾 Enregistrer", type="primary", width="stretch")
    if ok:
        store.save_measurement(dict(meas_date=d, waist_cm=taille, hips_cm=hanches, chest_cm=poitrine,
                                    neck_cm=cou, arm_cm=bras, thigh_cm=cuisse, photos=photos, notes=notes))
        st.success("Mensurations enregistrées.")
        st.rerun()

    bf_navy = C.navy_body_fat(taille, cou, HEIGHT)
    daily = load_daily()
    w_avg = mean_since(daily, "weight_kg", 7)
    c1, c2, c3 = st.columns(3)
    c1.metric("Ratio taille/hanches", fmt(taille / hanches, "", 2))
    _pct_7j = mean_since(daily, "body_fat_pct", 7)
    c2.metric("Masse grasse estimée (Marine)",
              fmt(None if (bf_navy is None or w_avg is None)
                  else C.fat_mass_kg(w_avg, bf_navy), " kg"),
              None if bf_navy is None else f"≈ {bf_navy:.1f} %",
              help="Formule US Navy (tour de taille, cou, taille), convertie en kilos "
                   "avec ton poids moyen des 7 derniers jours.")
    c3.metric("Masse grasse balance 7 j",
              fmt(None if (w_avg is None or _pct_7j is None)
                  else C.fat_mass_kg(w_avg, _pct_7j), " kg"),
              None if _pct_7j is None else f"≈ {_pct_7j:.1f} %",
              help="Impédancemètre (Tefal) : lecture en tendance uniquement.")
    if w_avg and bf_navy:
        st.caption(f"À {w_avg:.1f} kg avec {bf_navy:.1f} % de gras → **{C.fat_mass_kg(w_avg, bf_navy)} kg de gras** "
                   f"et **{C.lean_mass_kg(w_avg, bf_navy)} kg de masse maigre**. "
                   f"Masse maigre stable = muscle préservé ✅")

    if not meas.empty and meas["waist_cm"].dropna().shape[0] >= 2:
        m = meas.dropna(subset=["waist_cm"]).rename(columns={"meas_date": "date", "waist_cm": "Tour de taille"})
        st.altair_chart(
            alt.Chart(m).mark_line(point=True, color="#eaf2f6").encode(
                x=alt.X("date:T", title=None),
                y=alt.Y("Tour de taille:Q", scale=alt.Scale(zero=False), title="cm"),
            ).properties(height=230, width="container"))
    if not meas.empty:
        st.markdown("**Mon historique** — *clique dans une case pour corriger une mesure*")
        m = meas.set_index(meas["meas_date"].astype(str)).rename(columns={
            "meas_date": "Date", "waist_cm": "Taille", "hips_cm": "Hanches", "chest_cm": "Poitrine",
            "neck_cm": "Cou", "arm_cm": "Bras", "thigh_cm": "Cuisse", "photos": "Photos",
            "notes": "Notes"})[
            ["Date", "Taille", "Hanches", "Poitrine", "Cou", "Bras", "Cuisse", "Photos", "Notes"]]
        m["Date"] = pd.to_datetime(m["Date"], errors="coerce").dt.date
        T.tableau_editable(
            m, cle="mensurations",
            colonnes={"Date": T.col_jour("Date"),
                      "Taille": T.col_nombre("Taille (cm)", 40, 200, 0.1),
                      "Hanches": T.col_nombre("Hanches (cm)", 40, 200, 0.1),
                      "Poitrine": T.col_nombre("Poitrine (cm)", 40, 200, 0.1),
                      "Cou": T.col_nombre("Cou (cm)", 20, 80, 0.1),
                      "Bras": T.col_nombre("Bras (cm)", 15, 70, 0.1),
                      "Cuisse": T.col_nombre("Cuisse (cm)", 20, 90, 0.1),
                      "Photos": T.col_oui_non("Photos"),
                      "Notes": T.col_texte("Notes", "large")},
            desactive=["Date"], hauteur=300,
            sauver=lambda jour, ch: CO.corriger_mensuration(store, jour, ch),
            supprimer=lambda jour: (store.delete_measurement(jour), True)[1],
            aide="Corrige un tour de taille, de hanches… puis clique sur "
                 "**💾 Enregistrer les corrections**. Coche 🗑️ pour supprimer une ligne.")


# ============================================================================
#  PAGE 4 — SÉANCE (30 MIN)
# ============================================================================
@st.fragment(run_every=1.0)
def rest_timer():
    until = st.session_state.get("rest_until", 0)
    if until <= time.time():
        return
    total = st.session_state.get("rest_total", 60) or 60
    left = int(round(until - time.time()))
    st.progress(max(0.0, min(1.0, 1 - left / total)), text=f"⏱️ Repos en cours — **{left} s**  (chrono {total} s)")


def page_seance():
    """Renforcement 30 min (lundi/vendredi) + rugby (jeudi) : noms Freeletics,
    explications, validation du ressenti et adaptation automatique."""
    SE.page_seance(store, TARGET_P)


# ============================================================================
#  PAGE 5 — PROTÉINES  (3 modes de saisie)
# ============================================================================
def _ajout_repas_prevu():
    """Mode 1 : choisir un repas prévu dans ta base de menus, avec « ma part ».

    Lit EXACTEMENT comme la page « Repas & menus » (même moteur, mêmes chiffres) :
    c'est ce qui manquait le 30/09 — cette page passait par la correspondance de
    colonnes enregistrée, qui ne retrouvait pas la date, et affichait « aucun repas ».
    """
    ms = menus_store()
    if ms is None:
        st.info("Cette page a besoin des clés Supabase (⚙️ Réglages).")
        return

    c1, c2 = st.columns([1, 2])
    with c1:
        jour = st.date_input("Jour", value=D.today(), format="DD/MM/YYYY", key="pr_jour")
    with st.spinner("Lecture de ton planning…"):
        try:
            repas = ms.repas_du_jour(jour)
        except Exception as e:
            repas = []
            st.warning(f"Lecture impossible pour l'instant ({type(e).__name__}). "
                       "Réessaie dans quelques secondes.")
    if not repas:
        st.info(f"Rien de prévu le **{jour.strftime('%d/%m/%Y')}**.")
        return

    def _etiquette(i):
        r = repas[i]
        moment = f"{str(r['heure']).capitalize()} · " if r["heure"] else ""
        calc = r.get("calcul")
        base = (f"{calc['par_part']['proteines']:.0f} g de protéines par part"
                if calc else "protéines non renseignées")
        return f"{moment}{r['recette']}  —  {base}"

    # Les libellés servent d'options : la case de recherche trouve donc le repas par son nom.
    libelles_repas = _libelles_uniques([_etiquette(i) for i in range(len(repas))])
    # liste cherchable sans accent : « poulet curry » trouve « Poulet au curry »
    #  LE module de recherche de l'application (le seul) : on tape « pates »,
    #  la liste ne garde que les repas qui correspondent, on clique le sien.
    choix_repas = MN.selecteur_recherche("Repas prévu", libelles_repas, "pr_idx")
    if choix_repas is None:                # rien trouvé : chercheur l'a déjà expliqué
        return
    rang = libelles_repas.index(choix_repas)
    r = repas[rang]
    calc = r.get("calcul")

    if not calc:
        st.caption(f"**{r['recette']}** — aucune recette n'est reliée à ce repas : "
                   "estime les protéines à la main.")
        apport = st.number_input("Protéines (g)", 0, 300, 30, 5, key="pr_man")
        if st.button("➕ Ajouter au compteur du jour", type="primary", key="pr_add",
                     width="stretch"):
            store.add_protein(jour, f"{r['recette']} (menu)", int(apport))
            st.success(f"+{int(apport)} g de protéines ajoutés.")
            st.rerun()
        return

    st.markdown(f"### {R.ligne_macros(calc['par_part'])}")
    st.caption(f"1 part {r['recette']} (sur {calc['parts']:g}) · "
               f"plat entier : {calc['total']['kcal']:.0f} kcal · {calc['poids_g']:.0f} g")

    # « Ma part » : 3 façons de la définir, avec la proposition par défaut.
    defaut = MN.part_defaut(calc["parts"], r["recette"], r["heure"])
    mode = st.radio("Ma part", ["Parts", "% du plat", "Poids (g)"],
                    horizontal=True, key="pr_mode",
                    help="« Parts » = nombre de parts de la recette. Le défaut proposé "
                         "est une estimation, change-le quand tu veux.")
    if mode == "Parts":
        val = st.number_input("Parts", 0.25, 6.0,
                              float(MN.borne(defaut, 0.25, 6.0, 1.0)), 0.25,
                              format="%.2f", key="pr_v_parts")
        md = "parts"
    elif mode == "% du plat":
        val = st.number_input("% du plat", 5, 100,
                              int(MN.borne(100 / (calc["parts"] or 1), 5, 100, 25)),
                              5, key="pr_v_pct")
        md = "pourcent"
    else:
        val = st.number_input("Poids servi (g)", 10, 2000,
                              int(MN.borne(calc["poids_g"] / (calc["parts"] or 1),
                                           10, 2000, 250)), 10, key="pr_v_g")
        md = "poids"

    mp = MN.ma_part(calc, md, val, MN.portion_foyer())
    st.markdown(f"### {R.ligne_macros(mp['macros'])}")
    st.caption(f"{mp['libelle']} ({mp['fraction'] * 100:.0f} % du plat · "
               f"{mp['grammes']:.0f} g servis)")

    if st.button(f"➕ Ajouter {mp['macros']['proteines']:.0f} g de protéines au journal",
                 type="primary", key="pr_add", width="stretch"):
        store.add_protein(jour, f"{r['recette']} ({mp['libelle']})",
                          int(round(mp["macros"]["proteines"])),
                          qty=float(val),
                          carbs=round(mp["macros"]["glucides"]),
                          fat=round(mp["macros"]["lipides"]))
        st.success(f"+{int(round(mp['macros']['proteines']))} g de protéines ajoutés "
                   f"pour « {r['recette']} » ({mp['libelle']}).")
        st.rerun()

    autres = [x for x in repas if x is not r]
    if autres:
        with st.expander(f"Les autres repas de ce jour ({len(autres)})"):
            for x in autres:
                moment = f"{str(x['heure']).capitalize()} · " if x["heure"] else ""
                c = x.get("calcul")
                p = (f"≈ {c['par_part']['proteines']:.0f} g de protéines par part"
                     if c else "protéines inconnues")
                st.markdown(f"- {moment}**{x['recette']}** — {p}")


def _ajout_ingredient():
    """Mode 2 : choisir un ingrédient de sa base, avec quantité et unité."""
    client, tables, mapping = contexte_menus()
    if not client:
        st.info("Cette page a besoin des clés Supabase (⚙️ Réglages).")
        return

    c1, c2 = st.columns([3, 1])
    with c2:
        st.write("")
        if st.button("🔄 Rafraîchir la liste", key="ing_refresh", width="stretch"):
            st.session_state.pop("it_ingredients", None)
            st.rerun()
    liste = st.session_state.get("it_ingredients")
    if liste is None:
        with st.spinner("Chargement de tes ingrédients…"):
            liste = IT.ingredients_liste(client, mapping)
        st.session_state["it_ingredients"] = liste

    if not liste:
        st.warning("Aucun ingrédient trouvé. Vérifie la correspondance des colonnes sur la page "
                   "**🍽️ Cuisine & menus → Étape 2**.")
        return
    with c1:
        st.caption(f"{len(liste)} ingrédients — tape pour filtrer.")

    compte = {}
    for x in liste:
        cle = x["nom"].strip().lower()
        compte[cle] = compte.get(cle, 0) + 1

    def etiquette(i):
        x = liste[i]
        if compte.get(x["nom"].strip().lower(), 0) < 2:
            return x["nom"]
        # même nom sur deux lignes : on précise unité et valeurs pour ne pas se tromper
        prec = [x["unite"] or "unité ?"]
        if x["prot100"] is not None:
            prec.append(f"{x['prot100']:g} g P/100 g")
        if x["kcal100"] is not None:
            prec.append(f"{x['kcal100']:g} kcal")
        return f"{x['nom']}  —  {' · '.join(prec)}"

    noms = [etiquette(i) for i in range(len(liste))]
    # Idem ici : les libellés servent d'options, donc la recherche fonctionne.
    options_ing = _libelles_uniques(noms)
    # liste cherchable sans accent : tape « pates » → « Pâtes », « epinard » → « Épinard »
    choix_ing = MN.selecteur_recherche("Ingrédient", options_ing, "ing_idx")
    if choix_ing is None:                  # rien trouvé : chercheur l'a déjà expliqué
        return
    idx = options_ing.index(choix_ing)
    ing = liste[idx]

    info = []
    if ing["prot100"] is not None:
        info.append(f"{ing['prot100']:g} g de protéines / 100 g")
    if ing["kcal100"] is not None:
        info.append(f"{ing['kcal100']:g} kcal / 100 g")
    if info:
        st.caption("**" + ing["nom"] + "** — " + " · ".join(info))
    else:
        st.caption(f"**{ing['nom']}** — aucune valeur nutritionnelle dans ta base pour cet ingrédient.")

    c1, c2, c3 = st.columns([2, 2, 2])
    with c1:
        unite = st.selectbox("Unité", IT.UNITES_UI, key=f"ing_unite_{idx}")
    piece = IT.est_unite_piece(unite)
    poids_piece = None
    if piece:
        sugg = ing["poids_piece"] or IT.poids_piece_suggere(ing["nom"])
        with c2:
            poids_piece = st.number_input("Poids d'une unité (g)", 1.0, 2000.0,
                                          float(MN.borne(sugg, 1.0, 2000.0, 50.0)), 5.0,
                                          key=f"ing_pp_{idx}")
        with c3:
            qte = st.number_input("Quantité", 0.25, 200.0, 1.0, 0.25, key=f"ing_qp_{idx}")
    else:
        with c2:
            qte = st.number_input("Quantité", 0.0, 5000.0, 100.0, 10.0, key=f"ing_q_{idx}_{unite}")
    grammes, explication = IT.convertir_grammes(qte, unite, poids_piece)
    base = st.radio("Dans ta base, les protéines sont indiquées…",
                    ["pour 100 g", "par portion ou par unité"],
                    horizontal=True, key=f"ing_base_{idx}")

    if ing["prot100"] is None:
        st.warning("Pas de valeur de protéines pour cet ingrédient dans ta base. "
                   "Tu peux saisir la valeur à la main ci-dessous : elle comptera pour ce repas.")
        apport = st.number_input("Protéines (g) — saisie manuelle", 0, 300, 20, 1, key="ing_man")
    elif base == "pour 100 g":
        apport = ing["prot100"] * grammes / 100.0
    else:
        apport = ing["prot100"] * qte

    # glucides et lipides, si la base les connaît
    def _macro(cle):
        v = ing.get(cle)
        if v is None:
            return None
        return v * grammes / 100.0 if base == "pour 100 g" else v * qte

    apport_g, apport_l = _macro("gluc100"), _macro("lip100")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Protéines", f"{apport:.0f} g")
    c2.metric("Glucides", fmt(apport_g, " g", 0), border=True)
    c3.metric("Lipides", fmt(apport_l, " g", 0), border=True)
    c4.metric("kcal", fmt((apport * 4 + (apport_g or 0) * 4 + (apport_l or 0) * 9), "", 0))
    with st.expander("D'où vient ce chiffre ?"):
        st.write(f"Calcul : {explication}"
                 + (f" × {ing['prot100']:g} g de protéines/100 g = **{apport:.0f} g**"
                    if base == "pour 100 g" and ing["prot100"] is not None else ""))

    if st.button("➕ Ajouter au compteur du jour", type="primary", key="ing_add", width="stretch"):
        libelle = f"{ing['nom']} {qte:g} {unite}"
        store.add_protein(D.today(), libelle, int(round(apport)), qty=qte,
                          carbs=round(apport_g or 0), fat=round(apport_l or 0))
        st.success(f"+{int(round(apport))} g de protéines ajoutés au journal du jour.")
        st.rerun()


def _bloc_repas_types(jour) -> None:
    """⭐ TES REPAS TYPES — un appui, la journée est notée.

    Les trois repas que Flavien mange quasiment tous les jours (gamelle de midi,
    goûter, petit déjeuner), avec les protéines, les glucides, les lipides et les
    calories déjà calculés. C'est le même contenu que la carte « ⭐ Mes repas
    types » du téléphone — mais ici, c'est l'application ordinateur qui écrit
    directement dans ta base : tu retrouveras la ligne sur ton téléphone.

    AFFICHÉ POUR FLAVIEN UNIQUEMENT : ni dans l'espace partagé du foyer
    (`?partage=1`), ni dans l'espace de son épouse. Ses chiffres ne peuvent donc
    jamais apparaître ailleurs.
    """
    if st.session_state.get("mode_partage") or espace_actuel() != "flavien":
        return
    with st.container(border=True):
        st.markdown("**⭐ Mes repas types**")
        st.caption("Un appui, la journée est notée — et la ligne arrive sur ton téléphone.")
        cols = st.columns(3)
        for i, r in enumerate(C.REPAS_TYPES):
            kcal = C.kcal_repas_type(r)
            with cols[i]:
                st.markdown(f"**{r['emoji']} {r['nom']}**")
                st.caption(r["detail"])
                st.markdown(f"**{kcal:.0f} kcal** · {r['prot']:.0f} g P · "
                            f"{r['gluc']:.0f} G · {r['lip']:.0f} L")
                if st.button(f"➕ Ajouter {kcal:.0f} kcal", key=f"rt_{i}", width="stretch"):
                    store.add_protein(jour, r["nom"], r["prot"], 1.0,
                                      carbs=r["gluc"], fat=r["lip"])
                    st.rerun()
        tot = C.total_repas_types()
        tot_kcal = tot["prot"] * 4 + tot["gluc"] * 4 + tot["lip"] * 9
        st.caption(f"Les trois ensemble : **{tot_kcal:.0f} kcal** · {tot['prot']:.0f} g P · "
                   f"{tot['gluc']:.0f} G · {tot['lip']:.0f} L — il te resterait "
                   f"**{max(0.0, TARGET_P - tot['prot']):.0f} g de protéines** et "
                   f"**{max(0.0, TARGET_KCAL - tot_kcal):.0f} kcal** pour le dîner.")
        st.caption("Un deuxième appui ajoute une deuxième ligne : jette un œil au journal ci-dessous.")


def _ajout_raccourcis():
    """Mode 3 : les repas types, les raccourcis rapides + saisie libre."""
    #  ⓘ le jour est réglable : un repas oublié hier se saisit ici, sur la bonne date.
    jour = st.date_input("Pour quel jour ?", value=D.today(), max_value=D.today(),
                         format="DD/MM/YYYY", key="rap_jour",
                         help="Laisse la date du jour, ou choisis hier si tu as oublié de noter.")
    #  ⭐ d'abord tes repas types (toi seulement), puis les raccourcis aliments.
    _bloc_repas_types(jour)
    cols = st.columns(2)
    for i, (label, g) in enumerate(C.PROTEIN_PRESETS):
        with cols[i % 2]:
            if st.button(f"{label} · +{g} g", key=f"p_{i}", width="stretch"):
                store.add_protein(jour, label, g)
                st.rerun()
    with st.form("custom"):
        c1, c2 = st.columns([2, 1])
        label = c1.text_input("Autre aliment / repas", placeholder="Ex. restaurant, repas chez des amis…")
        g = c2.number_input("Protéines (g)", 0, 200, 30, step=5)
        if st.form_submit_button("Ajouter", width="stretch") and label:
            store.add_protein(jour, label, g)
            st.rerun()


def _bloc_reparation(store, a_completer: list, nb_jour: int):
    """Récupère les glucides et lipides des repas enregistrés avant la mise à jour.

    Rien n'est écrit sans que tu aies vu la liste.
    """
    n_jour = len(a_completer)
    with st.container(border=True):
        st.markdown(f"**{n_jour} repas d'aujourd'hui n'ont pas encore leurs glucides et "
                    "lipides.**")
        st.caption("Ils ont été enregistrés avant la mise à jour : les protéines sont justes, "
                   "mais les deux autres compteurs étaient vides. L'application peut les "
                   "retrouver dans tes recettes et tes aliments — **et vérifie** que les "
                   "protéines recalculées correspondent bien à celles déjà enregistrées.")
        if st.button("🔍 Chercher les valeurs manquantes", key="pr_cherche", width="stretch"):
            ms = menus_store()
            if ms is None:
                st.warning("Tes données de menus ne sont pas accessibles : vérifie les clés "
                           "Supabase dans les Réglages.")
            else:
                with st.spinner("Lecture de tes recettes et de tes aliments…"):
                    try:
                        props, perdues = ms.reparer_macros(a_completer)
                    except Exception as e:
                        props, perdues = [], a_completer
                        st.error(f"Recherche impossible ({type(e).__name__}) : {e}")
                    st.session_state["pr_props"] = props
                    st.session_state["pr_perdues"] = len(perdues)
            st.rerun()

        props = st.session_state.get("pr_props")
        if props is None:
            return
        perdues = st.session_state.get("pr_perdues", 0)
        if not props:
            st.info("Aucune correspondance dans tes recettes : ressaisis ces repas en un appui.")
            return
        st.dataframe(pd.DataFrame([
            dict(Repas=p["item"], Retrouvé=p["source"], Protéines=f"{p['proteines']:.0f} g",
                 Glucides=f"{p['glucides']:.0f} g", Lipides=f"{p['lipides']:.0f} g",
                 Vérification="✅ cohérent" if p["coherent"] else f"⚠️ écart de {p['ecart_proteines']:.0f} g")
            for p in props]), hide_index=True, width="stretch")
        n_surs = sum(1 for p in props if p["coherent"])
        if st.button(f"✅ Compléter {n_surs} repas sur {len(props)} (seuls les cohérents)",
                     key="pr_applique", type="primary", width="stretch"):
            ok, ko, refus = 0, 0, 0
            for p in props:
                if not p["coherent"]:
                    refus += 1
                    continue
                try:
                    if store.maj_macros_protein(p["id"], p["glucides"], p["lipides"]):
                        ok += 1
                    else:
                        ko += 1
                except Exception:
                    ko += 1
            if ko:
                st.error(
                    f"{ko} repas n'ont pas pu être mis à jour. Dans ta base, il manque les "
                    "colonnes `carbs_g` et `fat_g` sur la table `sr_protein_entries`.\n\n"
                    "C'est la **PARTIE 1** du script **`8_valeurs_manquantes.sql`** "
                    "(`alter table ... add column if not exists carbs_g / fat_g`) : "
                    "réouvre ce fichier dans Supabase, copie la partie 1 dans le "
                    "SQL Editor et clique sur Run, puis reviens ici et réessaie.")
            if ok:
                st.session_state.pop("pr_props", None)
                st.session_state.pop("pr_perdues", None)
                st.success(f"{ok} repas complétés ✅" + (f" · {refus} laissés de côté "
                           "(valeurs incertaines)" if refus else ""))
                st.rerun()


def page_proteines():
    st.title("🥗 Nutrition")
    st.caption(f"Objectif du jour : **{TARGET_KCAL} kcal** · {TARGET_P} g P · "
               f"{TARGET_G} G · {TARGET_L} L")
    today = D.today()
    df = store.protein_df()
    if not df.empty:
        df["entry_date"] = pd.to_datetime(df["entry_date"]).dt.date
    p_today = 0 if df.empty else int(df[df["entry_date"] == today]["protein_g"].sum())

    st.progress(min(1.0, p_today / TARGET_P) if TARGET_P else 0.0,
                text=f"**{p_today} g / {TARGET_P} g**" + (" ✅ objectif atteint" if p_today >= TARGET_P
                else f" — il reste {TARGET_P - p_today} g"))

    # --- glucides et lipides du jour (mêmes entrées que les protéines)
    auj0 = df[df["entry_date"] == today] if not df.empty else df
    g_today = l_today = 0.0
    if not auj0.empty:
        if "carbs_g" in auj0.columns:
            g_today = float(auj0["carbs_g"].fillna(0).sum())
        if "fat_g" in auj0.columns:
            l_today = float(auj0["fat_g"].fillna(0).sum())

    # --- calories du jour : calculées depuis tes saisies (protéines 4, glucides 4,
    #     lipides 9 kcal par gramme). C'est le total « consommé » de la journée.
    kcal_today = 4.0 * p_today + 4.0 * g_today + 9.0 * l_today
    reste_kcal = TARGET_KCAL - kcal_today

    st.markdown("**Aujourd'hui**")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric(f"Protéines · cible {TARGET_P} g", fmt(p_today, " g", 0))
    k2.metric(f"Glucides · cible {TARGET_G} g", fmt(g_today, " g", 0))
    k3.metric(f"Lipides · cible {TARGET_L} g", fmt(l_today, " g", 0))
    k4.metric(f"Calories · cible {TARGET_KCAL} kcal", f"{kcal_today:.0f} kcal",
              f"{reste_kcal:+.0f} kcal restantes" if kcal_today else "à compléter",
              delta_color="off")
    st.progress(min(1.0, kcal_today / TARGET_KCAL) if TARGET_KCAL else 0.0,
                text=f"**Calories : {kcal_today:.0f} / {TARGET_KCAL} kcal**"
                     + (" ✅ objectif atteint" if kcal_today >= TARGET_KCAL else
                        f" — il reste {reste_kcal:.0f} kcal" if kcal_today else
                        " — rien d'enregistré pour l'instant"))

    # --- repas saisis AVANT l'ajout des glucides/lipides : on peut les compléter
    a_completer = []
    if not auj0.empty:
        for r in auj0.itertuples():
            if not (getattr(r, "carbs_g", 0) or getattr(r, "fat_g", 0)):
                a_completer.append(dict(id=r.id, item=r.item, protein_g=r.protein_g,
                                        qty=getattr(r, "qty", 1.0),
                                        entry_date=str(r.entry_date)))
    if a_completer:
        _bloc_reparation(store, a_completer, len(auj0))

    # comparaison « trop ou pas assez » — ce qui reste à prendre sur la journée
    rien_g = bool(p_today) and not g_today
    rien_l = bool(p_today) and not l_today
    ecarts = [("Protéines", p_today, TARGET_P, False, "g"),
              ("Glucides", g_today, TARGET_G, rien_g, "g"),
              ("Lipides", l_today, TARGET_L, rien_l, "g"),
              ("Calories", kcal_today, TARGET_KCAL, bool(p_today and not kcal_today), "kcal")]
    lignes = []
    for nom, val, cible, non_renseigne, unite in ecarts:
        reste = cible - val
        if val <= 0 and non_renseigne:
            verdict = "non renseigné — repas saisis avant la mise à jour"
            val_txt = "—"
        elif val <= 0:
            verdict = "à compléter — rien d'enregistré pour l'instant"
            val_txt = f"0 {unite}"
        elif 0.85 * cible <= val <= 1.15 * cible:
            verdict = "✅ dans la cible"
            val_txt = f"{val:.0f} {unite}"
        elif not cible:
            verdict = "aucune cible fixée"
            val_txt = f"{val:.0f} {unite}"
        elif val < cible:
            verdict = f"🔻 il manque {reste:.0f} {unite} ({val / cible:.0%} de la cible)"
            val_txt = f"{val:.0f} {unite}"
        else:
            verdict = f"🔺 {abs(reste):.0f} {unite} de trop ({val / cible:.0%} de la cible)"
            val_txt = f"{val:.0f} {unite}"
        lignes.append(dict(Nutriment=nom, Aujourdhui=val_txt, Cible=f"{cible} {unite}",
                           Verdict=verdict))
    st.dataframe(pd.DataFrame(lignes), hide_index=True, width="stretch")
    t1, t2, t3 = st.tabs(["🍽️ Repas prévu", "🥕 Ingrédient + quantité", "⚡ Mes raccourcis"])
    with t1:
        _ajout_repas_prevu()
    with t2:
        _ajout_ingredient()
    with t3:
        _ajout_raccourcis()

    if not df.empty:
        #  ⓘ ON VOIT PLUSIEURS JOURS (01/10) : avant, seules les lignes du jour
        #  étaient affichées — impossible de réparer un oubli d'hier. On peut
        #  aussi **changer la date** d'une ligne pour la déplacer.
        _c1, _c2 = st.columns([2, 3])
        _per = _c1.selectbox("Jours affichés", ["Aujourd'hui", "7 derniers jours",
                                                "14 derniers jours", "30 derniers jours",
                                                "Tout"], index=2, key="jr_periode")
        _lim = {"Aujourd'hui": 0, "7 derniers jours": 6, "14 derniers jours": 13,
                "30 derniers jours": 29, "Tout": None}[_per]
        _dates = pd.to_datetime(df["entry_date"], errors="coerce").dt.date
        auj = df if _lim is None else df[_dates >= (today - dt.timedelta(days=_lim))]
        _c2.caption(f"{len(auj)} ligne(s) — clique dans une case pour corriger, "
                    f"y compris la **date** (pour un oubli d'hier).")
        if not auj.empty:
            st.markdown("**Mon journal** — *corrige ici en cas d'erreur*")
            _detail = pd.DataFrame([dict(
                Date=r.entry_date,
                Repas=r.item,
                Proteines=getattr(r, "protein_g", 0),
                Glucides=getattr(r, "carbs_g", 0),
                Lipides=getattr(r, "fat_g", 0),
                Quantite=getattr(r, "qty", 1.0),
            ) for r in auj.itertuples()], index=[str(r.id) for r in auj.itertuples()])
            _detail = _detail.rename(columns={"Proteines": "Protéines (g)", "Glucides": "Glucides (g)",
                                              "Lipides": "Lipides (g)", "Quantite": "Quantité"})
            T.tableau_editable(
                _detail, cle="journal",
                colonnes={"Date": T.col_jour("Date"),
                          "Repas": T.col_texte("Repas", "large"),
                          "Protéines (g)": T.col_entier("Protéines (g)", 0, 500),
                          "Glucides (g)": T.col_entier("Glucides (g)", 0, 500),
                          "Lipides (g)": T.col_entier("Lipides (g)", 0, 500),
                          "Quantité": T.col_nombre("Quantité (×)", 0.1, 20, 0.5)},
                hauteur=min(600, 40 + 35 * len(_detail)),
                sauver=lambda entree, ch: CO.corriger_entree(store, entree, ch),
                supprimer=lambda entree: (store.delete_protein(entree), True)[1],
                aide="Une erreur de saisie (20 g au lieu de 40, un mauvais aliment…) se corrige "
                     "**ici** : les totaux du jour et les calories se recalculent aussitôt. "
                     "Change la **date** si tu as saisi un repas le mauvais jour. Coche 🗑️ pour "
                     "supprimer la ligne.")

    with st.expander("📈 Mes moyennes (7 jours · 30 jours · jours réussis)"):
        pb_all = protein_by_day()
        c1, c2, c3 = st.columns(3)
        c1.metric("Moyenne 7 j", fmt(mean_since(
            pb_all.rename(columns={"entry_date": "log_date", "total": "protein_g"}),
            "protein_g", 7) if not pb_all.empty else None, " g", 0))
        c2.metric("Moyenne 30 j", fmt(mean_since(
            pb_all.rename(columns={"entry_date": "log_date", "total": "protein_g"}),
            "protein_g", 30) if not pb_all.empty else None, " g", 0))
        c3.metric("Jours ≥ objectif (30 j)",
                  int(sum(1 for _, t_ in protein_by_day(today - dt.timedelta(days=30)).itertuples(index=False)
                          if t_ >= TARGET_P)), "jours")
        if not df.empty:
            pb = protein_by_day(today - dt.timedelta(days=21))
            if not pb.empty:
                pb = pb.rename(columns={"entry_date": "date", "total": "Protéines"})
                st.altair_chart(alt.Chart(pb).mark_bar(color="#14b8a6").encode(
                    x=alt.X("date:T", title=None), y=alt.Y("Protéines:Q", title="g/jour"),
                ).properties(height=200, width="container") + alt.Chart(
                    pd.DataFrame({"y": [TARGET_P]})).mark_rule(color="#fbbf24",
                                                               strokeDash=[5, 4]).encode(y="y:Q"))

    with st.expander("🧊 Repas type & batch cooking du dimanche (45 min)"):
        st.markdown("**7 h** — Thé vert, citron, 500 ml d'eau\n\n"
                    "**10 h 30** — Café + shaker 30 g de whey (24 g) *ou* 40 g de lait en poudre "
                    "+ 200 g de fromage blanc\n\n"
                    "**12 h 30** — Gamelle : 300 g légumes + 150 g lentilles/pois chiches + 3 œufs "
                    "+ 150 g skyr + 100 g edamames ou 1 boîte de thon (58 g)\n\n"
                    "**16 h** — Pomme + 200 g fromage blanc + 15-20 g d'amandes (18 g)\n\n"
                    "**20 h** — 160-180 g de protéine + 300 g légumes + 150 g skyr + 10 g chocolat 85 % "
                    "(58 g). Féculents uniquement les jours de sport.")
        st.markdown("**Batch cooking**")
        for tps, txt in C.BATCH_COOKING:
            st.markdown(f"- *{tps}* — {txt}")


# ============================================================================
#  PAGE — CUISINE & MENUS (passerelle avec l'application gestion-menus)
# ============================================================================
def page_planifier():
    ms = menus_store()
    if ms is None:
        R.page_repas(store, menus_store, TARGET_P, partage=est_partage())
        return
    st.session_state.setdefault("_pid", None)
    ED.page_planifier(ms, TARGET_P, partage=est_partage())


def _plus_ancienne(vue, attendue) -> bool:
    """La version du fichier est-elle PLUS ANCIENNE que celle attendue ?

    On ne se contente pas de comparer « égal ou pas » : un fichier plus récent
    que prévu (parce qu'on a installé une mise à jour à l'avance) ne doit pas
    déclencher l'avertissement.
    """
    def nombres(v):
        return [int(x) for x in _re.findall(r"\d+", str(v or ""))] or [0]
    try:
        return nombres(vue) < nombres(attendue)
    except Exception:
        return str(vue) != str(attendue)


def _bandeau_fichiers_a_jour():
    """Avertit si les fichiers posés sur GitHub ne sont pas ceux de cette version."""
    manquants = []
    for nom, fichier, attendu in (
            ("editeurs", "editeurs.py", VERSIONS_FICHIERS["editeurs"]),
            ("menus", "menus.py", VERSIONS_FICHIERS["menus"]),
            ("pdf_menus", "pdf_menus.py", VERSIONS_FICHIERS["pdf_menus"]),
            ("repas_plats", "repas_plats.py", VERSIONS_FICHIERS["repas_plats"]),
            ("content", "content.py", VERSIONS_FICHIERS["content"]),
            ("corrections", "corrections.py", VERSIONS_FICHIERS["corrections"]),
            ("tableaux", "tableaux.py", VERSIONS_FICHIERS["tableaux"]),
            ("db", "db.py", VERSIONS_FICHIERS["db"])):
        module = _sys.modules.get(nom)
        if module is None:
            continue                       # ce fichier n'est pas encore utilisé par cette page
        vu = getattr(module, "VERSION", attendu)
        if _plus_ancienne(vu, attendu):
            #  ⓘ on compare chaque fichier à LA SIENNE, et non à la version de
            #  l'application : sinon le bandeau criait au loup dès qu'une seule
            #  version changeait (menus.py resté en 1.0.1, par exemple).
            manquants.append(f"**{fichier}** (celui de {vu})")
    if not manquants:
        return
    st.error(
        "⚠️ **Un fichier encore en mémoire est celui d'avant : " + " et ".join(manquants)
        + "**\n\n"
        f"À faire : **github.com** → dépôt **suivi-recomposition** → **Add file → "
        f"Upload files** → dépose les fichiers de la mise à jour {VERSION} → "
        "**Commit changes**. Puis **Manage app → ⋮ → Reboot app** et **F5**.\n\n"
        f"En bas de la barre de gauche, tu dois alors lire **éditeur {VERSION} · "
        f"menus {VERSION}**.")


def page_recettes_edition():
    _bandeau_fichiers_a_jour()
    ms = menus_store()
    if ms is None:
        R.page_repas(store, menus_store, TARGET_P, partage=est_partage())
        return
    ED.page_recettes_edition(ms)


def page_ingredients():
    ms = menus_store()
    if ms is None:
        R.page_repas(store, menus_store, TARGET_P, partage=est_partage())
        return
    ED.page_ingredients(ms)


def page_cuisine():
    R.page_repas(store, menus_store, TARGET_P, partage=est_partage())


# ============================================================================
#  PAGE 7 — RÉGLAGES / DONNÉES
# ============================================================================
def page_reglages():
    st.title("⚙️ Réglages")
    flash = st.session_state.pop("_flash_profil", None)
    if flash:
        (st.success if flash.startswith("✅") else st.warning)(flash)
    st.caption(f"Stockage : **{store.label}**")
    if store.kind == "local":
        st.warning("**Mode local** : tes données restent sur cet appareil (pas de synchronisation "
                   "entre le PC et le téléphone).")
    else:
        cle = ""
        try:
            cle = (read_secrets() or {}).get("cle") or ""
        except Exception:
            cle = st.session_state.get("_cle_pour_reglages", "")
        if cle:
            st.caption("🔒 Accès protégé par ta clé personnelle.")
            st.code(lien_personnel(cle), language=None)
            st.caption("⬆️ En favori sur ton ordinateur : il t'ouvre l'application sans rien taper.")
        _cle_elle = ""
        try:
            _cle_elle = (read_secrets() or {}).get("cle_elle") or ""
        except Exception:
            _cle_elle = ""
        if _cle_elle:
            st.caption("👤 Son lien à elle :")
            st.code(lien_personnel(_cle_elle), language=None)
        if st.session_state.get("auto_connexion"):
            st.caption("✅ Identification automatique active.")
            if st.button("🚪 Me déconnecter (afficher l'écran de connexion)"):
                store.sign_out()
                st.session_state.pop("sb_session", None)
                st.session_state.pop("store", None)
                st.session_state["sans_auto"] = True
                st.rerun()
        else:
            if st.button("Se déconnecter"):
                store.sign_out()
                st.session_state.pop("sb_session", None)
                st.session_state.pop("store", None)
                st.rerun()

    st.subheader("Mon profil et mes objectifs")
    st.caption(f"Objectifs actuels : **{TARGET_KCAL} kcal** · **{TARGET_P} g de protéines** · "
               f"**{TARGET_G} g de glucides** · **{TARGET_L} g de lipides**")
    #  Les valeurs sont RAMENÉES dans les bornes de chaque case : sans ça, une
    #  valeur enregistrée hors bornes (0, ou 70 g de protéines) faisait planter
    #  la page entière (vérifié par le test de solidité du 30/09).
    def bornes(valeur, mini, maxi, defaut):
        try:
            return min(max(float(valeur), float(mini)), float(maxi))
        except (TypeError, ValueError):
            return defaut

    with st.form("profil"):
        c1, c2 = st.columns(2)
        nom = c1.text_input("Prénom", value=str(prof("display_name", "")))
        taille_p = c2.number_input("Taille (cm)", 140.0, 220.0,
                                   bornes(HEIGHT, 140, 220, 185.0), step=0.5)
        c3, c4 = st.columns(2)
        dep = c3.number_input("Poids de départ (kg)", 40.0, 200.0,
                              bornes(START_W, 40, 200, 80.0), step=0.5)
        obj = c4.number_input("Poids objectif (kg)", 40.0, 200.0,
                              bornes(TARGET_W, 40, 200, 75.0), step=0.5)
        c5, c6 = st.columns(2)
        prot = c5.number_input("Protéines cibles (g/jour)", 80, 250,
                               int(bornes(TARGET_P, 80, 250, 130)), step=5)
        carb = c6.number_input("Glucides cibles (g/jour)", 40, 400,
                               int(bornes(TARGET_G, 40, 400, 140)), step=5)
        c7, c8 = st.columns(2)
        lip = c7.number_input("Lipides cibles (g/jour)", 20, 150,
                              int(bornes(TARGET_L, 20, 150, 50)), step=5)
        kcal = c8.number_input("Calories cibles (kcal/jour)", 1000, 4000,
                               int(bornes(TARGET_KCAL, 1000, 4000, 1700)), step=50)
        tdee = st.number_input("Dépense estimée (kcal/jour)", 1500, 4000,
                               int(bornes(prof("tdee_kcal", _rep("tdee_kcal", C.TDEE)), 1500, 4000, 2400)),
                               step=50)
        if st.form_submit_button("💾 Enregistrer le profil", type="primary", width="stretch"):
            ok, msg = _enregistrer_profil(dict(
                display_name=nom, height_cm=taille_p, start_weight_kg=dep,
                target_weight_kg=obj, target_protein_g=int(prot), target_carbs_g=int(carb),
                target_fat_g=int(lip), target_kcal=int(kcal), tdee_kcal=int(tdee),
                phase=C.phase_for(D.today())[0]))
            #  le message survit au rechargement : on le range et on l'affiche
            #  en haut de la page juste après (sinon il disparaissait aussitôt)
            st.session_state["_flash_profil"] = (
                "✅ Profil enregistré — les nouveaux objectifs sont déjà appliqués."
                if ok else f"⚠️ {msg}")
            st.rerun()

    # ---- export : chaque table à part (CSV direct) ou tout d'un coup (ZIP) ----
    st.subheader("Mes données")
    data = store.export_all()
    st.caption(" · ".join(f"{nom} : {len(df)}" for nom, df in data.items()))
    c1, c2 = st.columns([3, 2])
    with c1:
        table = st.selectbox("Quelle table ?", list(data.keys()), key="exp_table")
        st.download_button(
            f"⬇️ Télécharger « {table} » en CSV",
            data[table].to_csv(index=False).encode("utf-8-sig"),
            file_name=f"equilibre_{table}_{D.today().isoformat()}.csv",
            mime="text/csv", width="stretch")
    with c2:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
            for name, df in data.items():
                z.writestr(f"{name}.csv", df.to_csv(index=False))
        st.write("")
        st.download_button(
            "🗂️ Tout d'un coup (ZIP)", buf.getvalue(),
            file_name=f"equilibre_{D.today().isoformat()}.zip",
            mime="application/zip", width="stretch",
            help="Sauvegarde complète, un fichier CSV par table.")

    with st.expander("🗑️ Supprimer une entrée"):
        daily = load_daily()
        if daily.empty:
            st.caption("Rien à supprimer.")
        else:
            d = st.selectbox("Journée à supprimer", options=sorted(daily["log_date"].tolist(), reverse=True),
                             format_func=lambda x: x.strftime("%d/%m/%Y"))
            if st.button("Supprimer la journée sélectionnée"):
                store.delete_daily(d)
                st.rerun()

    with st.expander("🔧 Comment ça marche"):
        st.markdown(
            "- **Tes données** : Supabase, protégé — toi seul y accèdes.\n"
            "- **Sur le téléphone** : ouvre l'adresse de l'application dans Chrome → "
            "*Ajouter à l'écran d'accueil*.")


# ============================================================================
#  NAVIGATION
# ============================================================================
# Deux espaces, et rien d'autre :
#   👨‍👩‍👧‍👦 PARTAGÉ   — les recettes, les menus, les courses (utiles à la famille)
#   👤 PERSONNEL — ton suivi à toi, avec les réglages tout en bas (1.0)
# --------------------------------------------------------------------------
pages = {
    "👨‍👩‍👧‍👦 Menus & courses (partagé)": [
        st.Page(page_safe(page_cuisine), title="Repas & menus", icon="🍽️", default=True),
        st.Page(page_safe(page_planifier), title="Planifier la semaine", icon="📅"),
        st.Page(page_safe(page_recettes_edition), title="Recettes", icon="🥣"),
        st.Page(page_safe(page_ingredients), title="Ingrédients", icon="🥕"),
    ],
    "👤 Mon suivi (personnel)": [
        st.Page(page_safe(page_dashboard), title="Tableau de bord", icon="🏠"),
        st.Page(page_safe(page_pesee), title="Pesée & tendance", icon="⚖️"),
        st.Page(page_safe(page_seance), title="Mes séances", icon="💪"),
        st.Page(page_safe(page_proteines), title="Nutrition", icon="🥗"),
        st.Page(page_safe(page_mensurations), title="Mensurations", icon="📏"),
        #  les réglages ne sont plus dans un sous-dossier : ils sont au même
        #  niveau que les autres pages, mais toujours en dernier (demandé le 30/09)
        st.Page(page_safe(page_reglages), title="Réglages", icon="⚙️"),
    ],
}
# la page « Recettes » est mise de côté : la page « Repas & menus » s'en sert pour
# proposer un lien « 📖 Voir la recette » sur chaque plat à préparer.
try:
    st.session_state["_page_recettes"] = pages["👨‍👩‍👧‍👦 Menus & courses (partagé)"][2]
    #  la page d'accueil s'en sert pour le raccourci « 🧾 Voir ce que ça demande
    #  à mes courses » (30/09)
    st.session_state["_page_planifier"] = pages["👨‍👩‍👧‍👦 Menus & courses (partagé)"][1]
except Exception:
    pass

# ---------------------------------------------------------------------------
#  EN MODE PARTAGÉ, la barre de gauche ne montre QUE les pages du foyer.
#  « Mon suivi (personnel) » et « Réglages » ne sont même pas construits :
#  ils n'existent donc pas pour un visiteur — pas de page vide, pas de lien.
# ---------------------------------------------------------------------------
if est_partage():
    #  (attention à la majuscule et à l'accent : le titre est « … (partagé) »)
    pages = {titre: liste for titre, liste in pages.items()
             if "partag" in titre.lower()}
elif ELLE:
    #  Son espace : elle n'a pas de séances (elle n'en fait pas) — la page
    #  disparaît, avec ce qui l'accompagne (compteurs, alertes du tableau de bord).
    pages = {titre: [pg for pg in liste
                     if getattr(pg, "title", "") != "Mes séances"]
             for titre, liste in pages.items()}

#  Pour les tests : la liste des pages réellement construites pour cette session.
try:
    st.session_state["_pages_vues"] = [getattr(pg, "title", "")
                                       for liste in pages.values() for pg in liste]
except Exception:
    pass

if FICHIERS_RECHARGES:
    st.sidebar.success("♻️ Fichiers rechargés à l'instant : "
                       + ", ".join(sorted(set(FICHIERS_RECHARGES))))

#  Le logo de l'application, en haut de la barre de gauche.
if _os.path.exists(LOGO) and hasattr(st, "logo"):
    try:
        st.logo(LOGO, size="large")
    except Exception:
        pass

#  ⭐ 02/10 — BARRE DE GAUCHE ÉPURÉE. Elle affichait les numéros de version de
#  chaque fichier, le mode de stockage et des phrases d'explication : du bruit
#  technique, inutile au quotidien (et incompréhensible pour un invité). Il ne
#  reste que la version, une ligne discrète, et seulement dans ton espace : c'est
#  elle qui te permet de vérifier d'un coup d'œil qu'une mise à jour est arrivée.
#  Dans l'espace partagé et chez Léa : plus rien.
if not est_partage() and espace_actuel() != "elle":
    st.sidebar.caption(f"v{VERSION}")

# Hook de test (utilisé par test_app.py pour vérifier chaque page sans navigateur)
_test_page = _os.environ.get("APP_TEST_PAGE")
if _test_page:
    {"dashboard": page_dashboard, "pesee": page_pesee, "seance": page_seance,
     "proteines": page_proteines, "mensurations": page_mensurations,
     "reglages": page_reglages, "cuisine": page_cuisine,
     "planifier": page_planifier, "recettes": page_recettes_edition,
     "ingredients": page_ingredients}[_test_page]()
else:
    st.navigation(pages).run()
