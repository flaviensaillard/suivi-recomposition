# -*- coding: utf-8 -*-
"""
ÉQUILIBRE — suivi de recomposition corporelle et de menus.

Stack : Streamlit (interface) + Supabase (base de données cloud) + GitHub (code)
Le mode SQLite mono-utilisateur est réservé au développement local explicite
(EQUILIBRE_SINGLE_USER_LOCAL=1) ; une absence de configuration ne donne pas
accès automatiquement aux données familiales.

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
VERSION = "1.0.13"
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
    • Sans clé personnelle configurée : pas de connexion automatique. Le compte
      personnel doit se connecter explicitement ; l'espace partagé est un parcours
      distinct et ne donne jamais accès aux journaux personnels.
    """
    import hmac
    if st.session_state.get("cle_ok"):
        return True
    rangees = [(nom, cle) for nom, cle, _c, _m in espaces_rangees(cfg) if cle]
    if not rangees:
        return False                    # aucune clé personnelle : connexion explicite requise
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
    if _os.environ.get("EQUILIBRE_SINGLE_USER_LOCAL") != "1":
        st.error("### 🔒 Mode local désactivé par défaut\n\n"
                 "Aucun accès aux journaux personnels n'est ouvert sans authentification. "
                 "Configure Supabase pour le foyer, ou active explicitement le mode de "
                 "développement **mono-utilisateur** avec `EQUILIBRE_SINGLE_USER_LOCAL=1`. "
                 "Ce mode local n'isole pas plusieurs membres et ne doit pas être exposé "
                 "sur Internet.")
        st.stop()
    store = LocalStore()
    st.session_state["store"] = store
    return store


store = init_store()
PROFILE = store.profile() or {}


def prof(key, default):
    v = PROFILE.get(key)
    return default if v in (None, "") else v


_PROFIL_CHAMPS_REQUIS = (
    "height_cm", "start_weight_kg", "target_weight_kg", "target_protein_g",
    "target_carbs_g", "target_fat_g", "target_kcal", "tdee_kcal")


def _profil_valeur_renseignee(valeur):
    try:
        return valeur not in (None, "") and bool(pd.notna(valeur)) and float(valeur) > 0
    except (TypeError, ValueError):
        return False


# Un profil partiel n'est pas utilisé comme s'il contenait toutes les données
# personnelles nécessaires. Les repères internes restent provisoires et ne
# déclenchent pas d'analyses personnelles tant que les champs requis manquent.
PROFIL_VIERGE = not PROFILE or any(
    not _profil_valeur_renseignee(PROFILE.get(cle)) for cle in _PROFIL_CHAMPS_REQUIS)
_NEUTRE = dict(height_cm=170.0, start_weight_kg=70.0, target_weight_kg=70.0,
               target_protein_g=100, target_carbs_g=140, target_fat_g=55,
               target_kcal=1900, tdee_kcal=2200)


def _rep(cle, valeur_perso):
    """Repère provisoire interne, utilisé seulement avant configuration du profil."""
    return _NEUTRE[cle] if PROFIL_VIERGE else valeur_perso


TARGET_W = float(prof("target_weight_kg", _rep("target_weight_kg", C.TARGET_WEIGHT)))
TARGET_P = int(prof("target_protein_g", _rep("target_protein_g", C.TARGET_PROTEIN)))
TARGET_G = int(prof("target_carbs_g", _rep("target_carbs_g", getattr(C, "TARGET_CARBS", 140))))
TARGET_L = int(prof("target_fat_g", _rep("target_fat_g", getattr(C, "TARGET_FAT", 50))))
TARGET_KCAL = int(prof("target_kcal", _rep("target_kcal", getattr(C, "TARGET_KCAL", 1700))))
START_W = float(prof("start_weight_kg", _rep("start_weight_kg", C.START_WEIGHT)))
HEIGHT = float(prof("height_cm", _rep("height_cm", C.HEIGHT_CM)))
TARGET_P_PERSONNEL = None if PROFIL_VIERGE else TARGET_P


def _enregistrer_profil(data: dict):
    """Enregistre le profil sans repli partiel qui masquerait une erreur ou écrirait à moitié."""
    try:
        store.save_profile(data)
        return True, ""
    except Exception as e:
        texte = str(e).lower()
        champs = ("target_carbs_g", "target_fat_g", "target_kcal")
        if any(champ in texte for champ in champs) or (
                "column" in texte and any(m in texte for m in ("does not exist", "schema cache"))):
            return False, ("Aucun changement de profil confirmé : le schéma Supabase semble ne pas "
                           "contenir toutes les colonnes d'objectifs. Une mise à niveau du schéma "
                           "est nécessaire avant d'enregistrer ; aucune migration n'est lancée par "
                           "l'application. Contacte l'administrateur pour vérifier la structure.")
        return False, f"Profil non enregistré : {type(e).__name__} — {e}"


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
    """Compte séparément les deux renforts et le rugby du calendrier confirmé."""
    monday = D.today() - dt.timedelta(days=D.today().weekday())
    df = store.workouts_df()
    if df.empty:
        return 0, [], 0
    df = df.copy()
    df["session_date"] = pd.to_datetime(df["session_date"], errors="coerce").dt.date
    df = df[df["session_date"] >= monday]
    codes = df["session"].astype(str).str.upper()
    renfo = sorted(set(df[codes.isin(["A", "B"])]["session"].astype(str).str.upper()))
    rugby = int((codes == "C").sum())
    return len(renfo), renfo, rugby


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
    if PROFIL_VIERGE:
        st.warning("Profil personnel non configuré ou incomplet. Aucun objectif ni conseil personnalisé n'est affiché.")
        st.info("Configure tes propres données dans **Réglages**. Les données déjà enregistrées ne sont ni modifiées ni supprimées.")
        return
    daily = load_daily()
    meas = load_meas()
    prot = protein_by_day()
    phase = str(PROFILE.get("phase") or "Non renseignée")

    w_avg = mean_since(daily, "weight_kg", 7)
    w_prev = mean_since(daily, "weight_kg", 7, D.today() - dt.timedelta(days=7))
    bf_avg = mean_since(daily, "body_fat_pct", 7)
    p_avg = mean_since(prot.rename(columns={"entry_date": "log_date", "total": "protein_g"}),
                       "protein_g", 7) if not prot.empty else None
    n_sess, sess_list, n_rugby = sessions_this_week()

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
            f"{lined(n_sess >= 2)} **Renforcement : {n_sess}/2 (lundi/vendredi)**"
            f"{' (' + ', '.join(sess_list) + ')' if sess_list else ''}")
        _etat.append(f"{lined(n_rugby >= 1)} **Rugby : {n_rugby} séance(s) cette semaine**")
    _etat.append(f"{lined(not meas.empty)} **Mensurations**")
    st.markdown("  ·  ".join(_etat))
    if row.empty:
        st.info("Pense à enregistrer ta pesée du matin (page **⚖️ Pesée**).")

    # alertes coach
    alertes = []
    if w_prev and w_avg and (w_prev - w_avg) / 7 > 0.115:
        alertes.append("La tendance enregistrée dépasse 0,8 kg/semaine : vérifie les pesées et le contexte avant toute décision. Aucun objectif alimentaire n'est modifié automatiquement.")
    if p_avg is not None and p_avg < TARGET_P - 15:
        alertes.append(f"La moyenne de protéines journalisée ({p_avg:.0f} g/j) est sous la cible saisie. Vérifie d'abord que le journal est complet ; aucune supplémentation n'est prescrite automatiquement.")
    if not ELLE and today.weekday() >= 4:
        seances_manquantes = []
        for code, jour_prevu in (("A", "lundi"), ("B", "vendredi")):
            if code not in sess_list:
                seances_manquantes.append(f"séance {code} prévue {jour_prevu}")
        if seances_manquantes:
            alertes.append("À vérifier dans le journal : " + ", ".join(seances_manquantes) +
                           " — le calendrier lundi/vendredi + rugby jeudi est conservé.")
    if alertes:
        with st.container(border=True):
            st.markdown("**🧭 Ce que dit ton coach cette semaine**")
            for a in alertes:
                st.markdown(f"- {a}")

    with st.expander("⚠️ Signes à ne pas banaliser"):
        st.markdown("Une perte rapide, une baisse persistante de force, un sommeil dégradé, une frilosité inhabituelle, une baisse de libido, une récupération anormalement longue ou des blessures répétées peuvent avoir plusieurs causes. L'application ne pose pas de diagnostic et ne doit pas ajuster seule les calories : en cas de symptômes persistants ou inquiétants, demande un avis médical ou diététique qualifié.")


# ============================================================================
#  PAGE 2 — PESÉE DU JOUR
# ============================================================================
def page_pesee():
    st.title("⚖️ Pesée & tendance")
    st.caption("À jeun, même balance, même heure — c'est la **moyenne 7 jours** qui compte.")
    if PROFIL_VIERGE:
        st.info("Profil incomplet : aucune cible de poids ni IMC personnel n'est affiché. Les mesures restent saisissables sans objectif.")
    daily = load_daily()
    today = D.today()
    existing = daily[daily["log_date"] == today]
    cur = existing.iloc[0] if not existing.empty else None

    ACTIVITES = ["Non renseignée", "Repos", "Séance A", "Séance B", "Rugby", "Marche", "Musique", "Autre"]
    deja = _val(cur, "activity")
    poids_deja = _val(cur, "weight_kg")
    gras_pct_deja = _val(cur, "body_fat_pct")
    poids_initial = None if poids_deja is None else float(MN.borne(poids_deja, 50.0, 140.0, 80.0))
    gras_kg_initial = (C.fat_mass_kg(poids_initial, gras_pct_deja)
                       if poids_initial is not None and gras_pct_deja is not None else None)
    pas_deja = _val(cur, "steps")
    sommeil_deja = _val(cur, "sleep_h")
    energie_deja = _val(cur, "energy")
    activite_initiale = ACTIVITES.index(deja) if deja in ACTIVITES else 0
    options_energie = ["Non renseignée"] + list(range(1, 11))
    energie_initiale = options_energie.index(energie_deja) if energie_deja in options_energie else 0

    with st.form("pesee"):
        c1, c2 = st.columns(2)
        with c1:
            d = st.date_input("Date", value=today, max_value=today, format="DD/MM/YYYY")
            poids = st.number_input("Poids (kg)", min_value=50.0, max_value=140.0, step=0.1,
                                    format="%.1f", value=poids_initial,
                                    placeholder="Saisir une mesure réelle")
            # La masse grasse est facultative et n'est préremplie que si une
            # valeur a déjà été enregistrée pour cette même journée.
            bf_kg = st.number_input(
                "Masse grasse (kg) — facultatif", min_value=2.0, max_value=90.0, step=0.1,
                format="%.1f", value=gras_kg_initial,
                placeholder="Laisser vide si non mesurée",
                help="Saisis la valeur de la balance. Le pourcentage est calculé uniquement "
                     "si le poids du même jour est renseigné.")
            bf = (C.masse_grasse_pct(poids, bf_kg)
                  if poids is not None and bf_kg is not None else None)
            if bf is not None:
                st.caption(f"↳ soit **{bf:.1f} %** de {poids:.1f} kg")
            pas = st.number_input("Pas — facultatif", min_value=0, max_value=40000, step=250,
                                  value=None if pas_deja is None else int(MN.borne(pas_deja, 0, 40000, 0)),
                                  placeholder="Laisser vide si non suivi")
        with c2:
            sommeil = st.number_input("Sommeil (h) — facultatif", min_value=3.0, max_value=12.0,
                                      step=0.5, format="%.1f",
                                      value=None if sommeil_deja is None else float(MN.borne(sommeil_deja, 3, 12, 7.5)),
                                      placeholder="Laisser vide si non suivi")
            activite = st.selectbox("Activité du jour", ACTIVITES, index=activite_initiale)
            energie = st.selectbox("Énergie (1–10)", options_energie, index=energie_initiale)
            notes = st.text_area("Notes (facultatif)",
                                 value=str(_val(cur, "notes") or ""), height=80)
        ok = st.form_submit_button("💾 Enregistrer la journée", type="primary", width="stretch")
    if ok:
        if bf_kg is not None and (poids is None or poids <= 0):
            st.warning("Renseigne le poids du même jour pour enregistrer la masse grasse.")
        else:
            row = {"log_date": d}
            if poids is not None:
                row["weight_kg"] = float(poids)
            if bf is not None:
                row["body_fat_pct"] = float(bf)
            if pas is not None:
                row["steps"] = int(pas)
            if sommeil is not None:
                row["sleep_h"] = float(sommeil)
            if activite != "Non renseignée":
                row["activity"] = activite
            if energie != "Non renseignée":
                row["energy"] = int(energie)
            if notes.strip():
                row["notes"] = notes.strip()
            if len(row) == 1:
                st.warning("Aucune mesure ou donnée du jour renseignée ; rien n'a été enregistré.")
            else:
                store.save_daily(row)
                st.success("Journée enregistrée.")
                st.rerun()

    if bf is not None and poids is not None:
        details = (f"**{C.fat_mass_kg(poids, bf)} kg de masse grasse** ({bf:.1f} % de "
                   f"{poids:.1f} kg) et **{C.lean_mass_kg(poids, bf)} kg de masse maigre**")
        if not PROFIL_VIERGE:
            details += f" · IMC {C.bmi(poids, HEIGHT)} (indicateur descriptif, pas un diagnostic)"
        st.caption("Lecture calculée à partir des valeurs saisies : " + details)

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
        if not PROFIL_VIERGE:
            ch = ch + alt.Chart(pd.DataFrame({"y": [TARGET_W]})).mark_rule(
                color="#fbbf24", strokeDash=[5, 4]).encode(y="y:Q")
        st.altair_chart(ch)

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
    if PROFIL_VIERGE:
        st.info("Profil incomplet : les mensurations réelles peuvent être saisies, mais aucune estimation dépendant de la taille du profil n'est affichée.")
    meas = load_meas()
    today = D.today()
    last_meas = None if meas.empty else meas.iloc[-1]
    existing_today = meas[meas["meas_date"] == today]
    cur = existing_today.iloc[0] if not existing_today.empty else None

    def mesure_du_jour(champ, minimum, maximum):
        valeur = _val(cur, champ)
        if valeur is None:
            return None
        try:
            valeur = float(valeur)
            return valeur if minimum <= valeur <= maximum else None
        except (TypeError, ValueError):
            return None

    with st.form("mens"):
        c1, c2 = st.columns(2)
        with c1:
            d = st.date_input("Date", value=today, max_value=today, format="DD/MM/YYYY")
            taille = st.number_input("Tour de taille — nombril (cm)", 50.0, 160.0, step=0.1,
                                     format="%.1f", value=mesure_du_jour("waist_cm", 50, 160),
                                     placeholder="Laisser vide si non mesuré")
            hanches = st.number_input("Hanches (cm)", 50.0, 160.0, step=0.1, format="%.1f",
                                      value=mesure_du_jour("hips_cm", 50, 160),
                                      placeholder="Laisser vide si non mesuré")
            poitrine = st.number_input("Poitrine (cm)", 50.0, 160.0, step=0.1, format="%.1f",
                                       value=mesure_du_jour("chest_cm", 50, 160),
                                       placeholder="Laisser vide si non mesuré")
        with c2:
            cou = st.number_input("Tour de cou (cm)", 25.0, 60.0, step=0.1, format="%.1f",
                                  value=mesure_du_jour("neck_cm", 25, 60),
                                  placeholder="Laisser vide si non mesuré",
                                  help="Facultatif. La formule Marine affichée plus bas est une estimation masculine, pas un diagnostic.")
            bras = st.number_input("Bras contracté (cm)", 20.0, 60.0, step=0.1, format="%.1f",
                                   value=mesure_du_jour("arm_cm", 20, 60),
                                   placeholder="Laisser vide si non mesuré")
            cuisse = st.number_input("Cuisse (cm)", 30.0, 90.0, step=0.1, format="%.1f",
                                     value=mesure_du_jour("thigh_cm", 30, 90),
                                     placeholder="Laisser vide si non mesuré")
            photos = st.checkbox("Photos face / profil / dos faites",
                                 value=bool(_val(cur, "photos", False)))
        notes = st.text_input("Observations", value=str(_val(cur, "notes", "") or ""))
        ok = st.form_submit_button("💾 Enregistrer", type="primary", width="stretch")
    if ok:
        ligne = {"meas_date": d}
        mesures = {"waist_cm": taille, "hips_cm": hanches, "chest_cm": poitrine,
                   "neck_cm": cou, "arm_cm": bras, "thigh_cm": cuisse}
        for champ, valeur in mesures.items():
            if valeur is not None:
                ligne[champ] = float(valeur)
        if cur is not None or photos:
            ligne["photos"] = bool(photos)
        if cur is not None or notes.strip():
            ligne["notes"] = notes.strip()
        if len(ligne) == 1 or (len(ligne) == 2 and "photos" in ligne and not photos):
            st.warning("Renseigne au moins une mesure, une note ou confirme des photos ; rien n'a été enregistré.")
        else:
            store.save_measurement(ligne)
            st.success("Mensurations enregistrées.")
            st.rerun()

    donnees_mesure = last_meas
    taille_enregistree = _val(donnees_mesure, "waist_cm")
    hanches_enregistrees = _val(donnees_mesure, "hips_cm")
    cou_enregistre = _val(donnees_mesure, "neck_cm")
    bf_navy = (None if PROFIL_VIERGE or ELLE or taille_enregistree is None or cou_enregistre is None
               else C.navy_body_fat(taille_enregistree, cou_enregistre, HEIGHT))
    daily = load_daily()
    w_avg = mean_since(daily, "weight_kg", 7)
    c1, c2, c3 = st.columns(3)
    ratio_taille_hanches = (float(taille_enregistree) / float(hanches_enregistrees)
                            if taille_enregistree is not None and hanches_enregistrees not in (None, 0)
                            else None)
    c1.metric("Ratio taille/hanches", fmt(ratio_taille_hanches, "", 2))
    _pct_7j = mean_since(daily, "body_fat_pct", 7)
    c2.metric("Masse grasse estimée (Marine)",
              fmt(None if (bf_navy is None or w_avg is None)
                  else C.fat_mass_kg(w_avg, bf_navy), " kg"),
              None if bf_navy is None else f"≈ {bf_navy:.1f} %",
              help="Formule Marine masculine (tour de taille, cou, taille), disponible seulement avec un profil configuré. Estimation indicative, pas un diagnostic.")
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
    """Renforcement lundi/vendredi + rugby jeudi : calendrier intentionnel."""
    if PROFIL_VIERGE:
        st.warning("Profil incomplet : le plan de base ci-dessous est générique, pas personnalisé. Toute proposition issue de l'historique reste à confirmer explicitement.")
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
                if calc and calc.get("complet", {}).get("proteines", False)
                else "protéines non renseignées ou incomplètes")
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
        st.caption(f"**{r['recette']}** — aucune recette n'est reliée à ce repas. "
                   "Pour l'ajouter au suivi des macros, saisis les valeurs vérifiées de ta portion.")
        c_p, c_g, c_l = st.columns(3)
        with c_p:
            prot_man = st.number_input("Protéines (g)", 0, 300, value=None, step=1,
                                       placeholder="Valeur vérifiée", key="pr_man_p")
        with c_g:
            gluc_man = st.number_input("Glucides (g)", 0, 500, value=None, step=1,
                                       placeholder="Valeur vérifiée", key="pr_man_g")
        with c_l:
            lip_man = st.number_input("Lipides (g)", 0, 300, value=None, step=1,
                                      placeholder="Valeur vérifiée", key="pr_man_l")
        macros_man_completes = all(v is not None for v in (prot_man, gluc_man, lip_man))
        if st.button("➕ Ajouter au compteur du jour", type="primary", key="pr_add",
                     width="stretch", disabled=not macros_man_completes):
            store.add_protein(jour, f"{r['recette']} (menu)", int(prot_man),
                              carbs=int(gluc_man), fat=int(lip_man))
            st.success(f"+{int(prot_man)} g de protéines ajoutés.")
            st.rerun()
        return

    texte_macros = R.ligne_macros(
        calc['par_part'], complet=calc.get('complet'),
        approximatif=calc.get('approximatif', False))
    st.markdown(f"### {texte_macros}")
    kcal_total = (f"{calc['total']['kcal']:.0f} kcal" if calc.get("complet", {}).get("kcal")
                  else "kcal inconnues")
    st.caption(f"1 part {r['recette']} (sur {calc['parts']:g}) · "
               f"plat entier : {kcal_total} · {calc['poids_g']:.0f} g")
    if calc.get("inconnues"):
        st.warning("Valeurs manquantes ou quantité non convertible : "
                   + ", ".join(calc["inconnues"][:6])
                   + ". Aucun inconnu n'est compté comme zéro.")

    # La portion est une quantité réellement servie, pas une part moyenne inventée.
    mode = st.radio("Ma part", ["Parts", "% du plat", "Poids (g)"],
                    horizontal=True, key="pr_mode",
                    help="Saisis uniquement la quantité réellement servie. Sans mesure ou estimation personnelle, laisse vide.")
    if mode == "Parts":
        val = st.number_input("Parts réellement servies", min_value=0.25, max_value=6.0,
                              value=None, step=0.25, format="%.2f",
                              placeholder="À renseigner", key="pr_v_parts")
        md = "parts"
    elif mode == "% du plat":
        val = st.number_input("Pourcentage réellement servi", min_value=5, max_value=100,
                              value=None, step=5, placeholder="À renseigner", key="pr_v_pct")
        md = "pourcent"
    else:
        val = st.number_input("Poids servi (g)", min_value=10, max_value=2000,
                              value=None, step=10, placeholder="À renseigner", key="pr_v_g")
        md = "poids"

    if val is None:
        st.info("Renseigne la quantité réellement servie pour calculer et journaliser ta portion.")
        return
    mp = MN.ma_part(calc, md, val, MN.portion_foyer())
    texte_ma_part = R.ligne_macros(
        mp['macros'], complet=mp['complet'], approximatif=mp['approximatif'])
    st.markdown(f"### {texte_ma_part}")
    st.caption(f"{mp['libelle']} ({mp['fraction'] * 100:.0f} % du plat · "
               f"{mp['grammes']:.0f} g servis)")

    macros_completes = all(mp["complet"].get(c, False)
                           for c in ("proteines", "glucides", "lipides"))
    libelle_ajout = (f"➕ Ajouter {mp['macros']['proteines']:.0f} g de protéines au journal"
                     if macros_completes else
                     "Valeurs nutritionnelles incomplètes — ajout désactivé")
    if st.button(libelle_ajout, type="primary", key="pr_add", width="stretch",
                 disabled=not macros_completes):
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
        sugg = ing.get("poids_piece")
        with c2:
            poids_piece = st.number_input(
                "Poids d'une unité (g)", min_value=1.0, max_value=2000.0,
                value=float(sugg) if sugg is not None else None, step=5.0,
                placeholder="Saisir le poids réel", key=f"ing_pp_{idx}",
                help="Une valeur déjà présente dans ta base est une référence : vérifie qu'elle correspond à l'unité réellement servie.")
        with c3:
            qte = st.number_input("Quantité", min_value=0.25, max_value=200.0,
                                  value=None, step=0.25, placeholder="À renseigner",
                                  key=f"ing_qp_{idx}")
    else:
        with c2:
            qte = st.number_input("Quantité", min_value=0.01, max_value=5000.0,
                                  value=None, step=10.0, placeholder="À renseigner",
                                  key=f"ing_q_{idx}_{unite}")

    if qte is None or (piece and poids_piece is None):
        st.info("Renseigne la quantité réellement servie" +
                (" et le poids de l'unité" if piece and poids_piece is None else "") +
                " avant de calculer les macros.")
        return
    grammes, explication = IT.convertir_grammes(qte, unite, poids_piece)
    base = st.radio("Dans ta base, les protéines sont indiquées…",
                    ["pour 100 g", "par portion ou par unité"],
                    horizontal=True, key=f"ing_base_{idx}")

    if base == "pour 100 g":
        facteur = grammes / 100.0
    else:
        facteur = qte

    valeurs = {}
    for cle, nom in (("prot100", "Protéines"), ("gluc100", "Glucides"), ("lip100", "Lipides")):
        valeur_base = ing.get(cle)
        if valeur_base is not None:
            valeurs[cle] = valeur_base * facteur
        else:
            st.warning(f"La valeur de {nom.lower()} manque dans ta base : saisis-la pour la portion réellement servie.")
            valeurs[cle] = st.number_input(
                f"{nom} (g) — saisie manuelle pour cette portion", min_value=0.0,
                max_value=500.0, value=None, step=1.0, placeholder="Valeur vérifiée",
                key=f"ing_man_{cle}_{idx}")

    apport, apport_g, apport_l = (valeurs["prot100"], valeurs["gluc100"], valeurs["lip100"])
    macros_completes = all(v is not None for v in (apport, apport_g, apport_l))
    kcal_portion = (4 * apport + 4 * apport_g + 9 * apport_l) if macros_completes else None
    fmt_nutri = lambda v, unite: f"{v:.0f}{unite}" if v is not None else "Inconnu"
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Protéines", fmt_nutri(apport, " g"))
    c2.metric("Glucides", fmt_nutri(apport_g, " g"), border=True)
    c3.metric("Lipides", fmt_nutri(apport_l, " g"), border=True)
    c4.metric("kcal", fmt_nutri(kcal_portion, " kcal"))
    with st.expander("D'où vient ce chiffre ?"):
        st.write(f"Calcul de quantité : {explication}. Les nutriments présents en base sont calculés depuis la valeur source ; les champs manquants doivent être saisis à partir d'une information vérifiée.")

    if not macros_completes:
        st.info("L'ajout est désactivé tant que protéines, glucides et lipides ne sont pas tous renseignés. Une valeur inconnue ne sera pas enregistrée comme zéro.")
    if st.button("➕ Ajouter au compteur du jour", type="primary", key="ing_add",
                 width="stretch", disabled=not macros_completes):
        libelle = f"{ing['nom']} {qte:g} {unite}"
        store.add_protein(D.today(), libelle, int(round(apport)), qty=qte,
                          carbs=round(apport_g), fat=round(apport_l))
        st.success(f"+{int(round(apport))} g de protéines ajoutés au journal du jour.")
        st.rerun()


def _bloc_repas_types(jour) -> None:
    """⭐ Repas types préenregistrés — saisie rapide, valeurs à vérifier.

    Les quantités et macros sont des repères historiques, pas des mesures
    universelles ni des recommandations. L'utilisateur doit les confronter à
    ses portions réelles avant de les ajouter au journal.

    AFFICHÉ UNIQUEMENT dans l'espace personnel configuré : ni dans l'espace
    partagé du foyer (`?partage=1`), ni dans l'espace d'un autre compte.
    """
    if st.session_state.get("mode_partage") or espace_actuel() != "flavien" or PROFIL_VIERGE:
        return
    with st.container(border=True):
        st.markdown("**⭐ Repas types personnels**")
        st.caption("Valeurs préenregistrées à vérifier par rapport à tes recettes et portions réelles avant utilisation. Un appui ajoute une ligne au journal.")
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
        resume = (f"Les trois ensemble : **{tot_kcal:.0f} kcal** · {tot['prot']:.0f} g P · "
                  f"{tot['gluc']:.0f} g G · {tot['lip']:.0f} g L (valeurs préenregistrées).")
        if not PROFIL_VIERGE:
            resume += (f" Sur la base de ton profil actuel, cela représenterait "
                       f"{max(0.0, TARGET_P - tot['prot']):.0f} g de protéines et "
                       f"{max(0.0, TARGET_KCAL - tot_kcal):.0f} kcal à répartir sur le reste de la journée.")
        st.caption(resume)
        st.caption("Un deuxième appui ajoute une deuxième ligne : jette un œil au journal ci-dessous.")


def _ajout_raccourcis():
    """Mode 3 : les repas types, les raccourcis rapides + saisie libre."""
    #  ⓘ le jour est réglable : un repas oublié hier se saisit ici, sur la bonne date.
    jour = st.date_input("Pour quel jour ?", value=D.today(), max_value=D.today(),
                         format="DD/MM/YYYY", key="rap_jour",
                         help="Laisse la date du jour, ou choisis hier si tu as oublié de noter.")
    #  ⭐ d'abord tes repas types (toi seulement), puis les raccourcis aliments.
    _bloc_repas_types(jour)
    st.caption("Raccourcis de saisie uniquement — ils ne recommandent pas la consommation d'un aliment ou supplément. Ils renseignent seulement les protéines ; glucides, lipides et calories restent inconnus, jamais comptés comme zéro.")
    cols = st.columns(2)
    for i, (label, g) in enumerate(C.PROTEIN_PRESETS):
        with cols[i % 2]:
            if st.button(f"{label} · +{g} g", key=f"p_{i}", width="stretch"):
                store.add_protein(jour, label, g)
                st.rerun()
    with st.form("custom"):
        c1, c2 = st.columns([2, 1])
        label = c1.text_input("Autre aliment / repas", placeholder="Ex. restaurant, repas chez des amis…")
        g = c2.number_input("Protéines (g)", 0, 200, value=None, step=1,
                            placeholder="Valeur vérifiée")
        if st.form_submit_button("Ajouter", width="stretch",
                                 disabled=not label.strip() or g is None) and label.strip():
            store.add_protein(jour, label.strip(), g)
            st.rerun()


def _bloc_reparation(store, a_completer: list, nb_jour: int):
    """Récupère les glucides et lipides des repas enregistrés avant la mise à jour.

    Rien n'est écrit sans que tu aies vu la liste.
    """
    n_jour = len(a_completer)
    with st.container(border=True):
        st.markdown(f"**{n_jour} entrée(s) d'aujourd'hui n'ont pas leurs glucides et/ou lipides.**")
        st.caption("Les macros inconnues ne sont pas comptées comme zéro ; les totaux et calories restent incomplets. L'application peut chercher une correspondance dans les recettes et aliments du foyer. Toute proposition est affichée avant application, et les lignes sans correspondance restent inchangées.")
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
    if PROFIL_VIERGE:
        st.warning("Profil personnel incomplet : aucun objectif ni comparaison personnalisée n'est affiché. Les journaux restent consultables.")
    else:
        st.caption(f"Objectifs enregistrés dans ton profil : **{TARGET_KCAL} kcal** · "
                   f"{TARGET_P} g P · {TARGET_G} g G · {TARGET_L} g L")
    st.caption("Les totaux ne couvrent que les lignes journalisées ; ne rien saisir ne signifie pas ne rien avoir consommé.")
    today = D.today()
    df = store.protein_df()
    if not df.empty:
        df["entry_date"] = pd.to_datetime(df["entry_date"], errors="coerce").dt.date
    p_today = 0 if df.empty else int(pd.to_numeric(
        df[df["entry_date"] == today]["protein_g"], errors="coerce").fillna(0).sum())
    auj0 = df[df["entry_date"] == today] if not df.empty else df

    def total_macro(cle):
        if auj0.empty:
            return 0.0, True
        if cle not in auj0.columns:
            return None, False
        serie = pd.to_numeric(auj0[cle], errors="coerce")
        connu = float(serie.dropna().sum())
        return connu, not bool(serie.isna().any())

    g_today, g_complet = total_macro("carbs_g")
    l_today, l_complet = total_macro("fat_g")

    if not PROFIL_VIERGE:
        st.progress(min(1.0, p_today / TARGET_P) if TARGET_P else 0.0,
                    text=f"**{p_today} g / {TARGET_P} g**" +
                    (" ✅ objectif atteint" if p_today >= TARGET_P else
                     f" — il reste {TARGET_P - p_today} g"))

    # Les calories ne sont calculées que si glucides et lipides sont connus pour
    # chaque entrée. Une valeur NULL ne devient jamais un faux zéro énergétique.
    kcal_complet = g_complet and l_complet
    kcal_today = (4.0 * p_today + 4.0 * g_today + 9.0 * l_today) if kcal_complet else None
    reste_kcal = TARGET_KCAL - kcal_today if not PROFIL_VIERGE and kcal_today is not None else None

    def texte_macro(valeur, complet, unite="g"):
        if valeur is None:
            return "Inconnu"
        texte = f"{valeur:.0f} {unite}"
        return texte if complet else f"{texte} connus · incomplet"

    st.markdown("**Aujourd'hui**")
    k1, k2, k3, k4 = st.columns(4)
    label_p = f"Protéines · cible {TARGET_P} g" if not PROFIL_VIERGE else "Protéines enregistrées"
    label_g = f"Glucides · cible {TARGET_G} g" if not PROFIL_VIERGE else "Glucides enregistrés"
    label_l = f"Lipides · cible {TARGET_L} g" if not PROFIL_VIERGE else "Lipides enregistrés"
    label_kcal = f"Calories estimées · cible {TARGET_KCAL} kcal" if not PROFIL_VIERGE else "Calories estimées calculables"
    k1.metric(label_p, f"{p_today} g")
    k2.metric(label_g, texte_macro(g_today, g_complet))
    k3.metric(label_l, texte_macro(l_today, l_complet))
    kcal_affiche = f"{kcal_today:.0f} kcal" if kcal_today is not None else "Inconnu"
    delta_kcal = (f"{reste_kcal:+.0f} kcal restantes" if kcal_today else "à compléter") if reste_kcal is not None else None
    k4.metric(label_kcal, kcal_affiche, delta_kcal, delta_color="off")
    st.caption("Énergie estimée par 4 kcal/g de protéines, 4 kcal/g de glucides et 9 kcal/g de lipides. Ce calcul à partir des macros n'est pas la valeur énergétique de référence Ciqual et peut différer ; il est omis si une macro manque.")

    if not PROFIL_VIERGE and kcal_today is not None:
        st.progress(min(1.0, kcal_today / TARGET_KCAL) if TARGET_KCAL else 0.0,
                    text=f"**Calories : {kcal_today:.0f} / {TARGET_KCAL} kcal**" +
                    (" ✅ objectif atteint" if kcal_today >= TARGET_KCAL else
                     f" — il reste {reste_kcal:.0f} kcal" if kcal_today else
                     " — rien d'enregistré pour l'instant"))
    elif not kcal_complet:
        st.info("Calories non calculées : une ou plusieurs entrées ont des glucides/lipides inconnus. Les valeurs connues restent visibles, sans assimiler l'inconnu à zéro.")

    # Signaler toutes les lignes incomplètes ; une vraie valeur 0 reste valide.
    a_completer = []
    if not auj0.empty:
        for r in auj0.itertuples():
            glucides = getattr(r, "carbs_g", None)
            lipides = getattr(r, "fat_g", None)
            if pd.isna(glucides) or pd.isna(lipides):
                a_completer.append(dict(id=r.id, item=r.item, protein_g=r.protein_g,
                                        qty=getattr(r, "qty", 1.0),
                                        entry_date=str(r.entry_date)))
    if a_completer:
        _bloc_reparation(store, a_completer, len(auj0))

    # Comparaison à une cible personnelle uniquement après configuration complète.
    if PROFIL_VIERGE:
        st.caption("Aucune comparaison à un objectif : il n'est pas configuré dans ce profil.")
    else:
        ecarts = [("Protéines", float(p_today), TARGET_P, True, "g"),
                  ("Glucides", g_today, TARGET_G, g_complet, "g"),
                  ("Lipides", l_today, TARGET_L, l_complet, "g"),
                  ("Calories", kcal_today, TARGET_KCAL, kcal_complet, "kcal")]
        lignes = []
        for nom, val, cible, complet, unite in ecarts:
            if val is None or not complet:
                val_txt = "Inconnu" if val is None else f"{val:.0f} {unite} connus · incomplet"
                verdict = "⚠️ données incomplètes — comparaison désactivée"
            elif val == 0:
                val_txt = f"0 {unite} enregistrés"
                verdict = "aucune valeur journalisée — cela ne signifie pas une consommation nulle"
            elif 0.85 * cible <= val <= 1.15 * cible:
                val_txt = f"{val:.0f} {unite}"
                verdict = "✅ dans la cible"
            elif val < cible:
                val_txt = f"{val:.0f} {unite}"
                verdict = f"🔻 il manque {cible - val:.0f} {unite} ({val / cible:.0%} de la cible)"
            else:
                val_txt = f"{val:.0f} {unite}"
                verdict = f"🔺 {val - cible:.0f} {unite} au-dessus de la cible ({val / cible:.0%})"
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
                Glucides=getattr(r, "carbs_g", None),
                Lipides=getattr(r, "fat_g", None),
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

    with st.expander("📈 Mes moyennes (7 jours · 30 jours)"):
        pb_all = protein_by_day()
        c1, c2, c3 = st.columns(3)
        c1.metric("Moyenne 7 j", fmt(mean_since(
            pb_all.rename(columns={"entry_date": "log_date", "total": "protein_g"}),
            "protein_g", 7) if not pb_all.empty else None, " g", 0))
        c2.metric("Moyenne 30 j", fmt(mean_since(
            pb_all.rename(columns={"entry_date": "log_date", "total": "protein_g"}),
            "protein_g", 30) if not pb_all.empty else None, " g", 0))
        pb_30 = protein_by_day(today - dt.timedelta(days=30))
        if PROFIL_VIERGE:
            c3.metric("Jours avec saisie (30 j)", len(pb_30), "jours")
        else:
            c3.metric("Jours ≥ objectif (30 j)",
                      int(sum(1 for _, t_ in pb_30.itertuples(index=False) if t_ >= TARGET_P)), "jours")
        if not df.empty:
            pb = protein_by_day(today - dt.timedelta(days=21))
            if not pb.empty:
                pb = pb.rename(columns={"entry_date": "date", "total": "Protéines"})
                graphique = alt.Chart(pb).mark_bar(color="#14b8a6").encode(
                    x=alt.X("date:T", title=None), y=alt.Y("Protéines:Q", title="g/jour"),
                ).properties(height=200, width="container")
                if not PROFIL_VIERGE:
                    graphique = graphique + alt.Chart(
                        pd.DataFrame({"y": [TARGET_P]})).mark_rule(color="#fbbf24",
                                                                   strokeDash=[5, 4]).encode(y="y:Q")
                st.altair_chart(graphique)

    with st.expander("🧊 Organisation des repas & batch cooking"):
        st.info("Cette page ne prescrit pas de menu quotidien, de complément ni de répartition des féculents. Les besoins et portions dépendent de la personne, de l'activité, de la santé et des préférences ; utilise les menus partagés comme outil de planification et vérifie les valeurs des aliments.")
        st.markdown("**Batch cooking**")
        for tps, txt in C.BATCH_COOKING:
            st.markdown(f"- *{tps}* — {txt}")


# ============================================================================
#  PAGE — CUISINE & MENUS (passerelle avec l'application gestion-menus)
# ============================================================================
def page_planifier():
    ms = menus_store()
    if ms is None:
        R.page_repas(store, menus_store, TARGET_P_PERSONNEL, partage=est_partage())
        return
    st.session_state.setdefault("_pid", None)
    ED.page_planifier(ms, TARGET_P_PERSONNEL, partage=est_partage())


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
            #  ⭐ 02/10 : on indique AUSSI la version attendue — le message disait
            #  « celui de 1.0.8 » sans dire quoi mettre à la place, et renvoyait à
            #  la ligne « éditeur … · menus … » de la barre de gauche, retirée à
            #  l'épuration de ce jour.
            manquants.append(f"**{fichier}** (le tien est le {vu} → il faut le {attendu})")
    if not manquants:
        return
    st.error(
        "⚠️ **Un de tes fichiers est resté en arrière : " + " et ".join(manquants)
        + ".**\n\n"
        "À faire : **github.com** → dépôt **suivi-recomposition** → ouvre le fichier "
        "cité → crayon **✏️** → **Ctrl+A** → colle celui de la mise à jour → "
        "**Commit changes**. Puis **Manage app → ⋮ → Reboot app** et **F5**.")


def page_recettes_edition():
    _bandeau_fichiers_a_jour()
    ms = menus_store()
    if ms is None:
        R.page_repas(store, menus_store, TARGET_P_PERSONNEL, partage=est_partage())
        return
    ED.page_recettes_edition(ms)


def page_ingredients():
    ms = menus_store()
    if ms is None:
        R.page_repas(store, menus_store, TARGET_P_PERSONNEL, partage=est_partage())
        return
    ED.page_ingredients(ms)


def page_cuisine():
    R.page_repas(store, menus_store, TARGET_P_PERSONNEL, partage=est_partage())


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
    if PROFIL_VIERGE:
        st.warning("Profil incomplet : aucun objectif personnel n'est confirmé. Les repères internes ne sont pas des recommandations ; renseigne tes propres valeurs ci-dessous avant les comparaisons et conseils.")
        st.caption("Aucun objectif personnel configuré.")
    else:
        st.caption(f"Objectifs actuels : **{TARGET_KCAL} kcal** · **{TARGET_P} g de protéines** · "
                   f"**{TARGET_G} g de glucides** · **{TARGET_L} g de lipides**")

    def valeur_profil_formulaire(cle):
        valeur = PROFILE.get(cle)
        if not _profil_valeur_renseignee(valeur):
            return None
        try:
            return float(valeur)
        except (TypeError, ValueError):
            return None

    with st.form("profil"):
        c1, c2 = st.columns(2)
        nom = c1.text_input("Prénom (facultatif)", value=str(prof("display_name", "")))
        taille_p = c2.number_input("Taille (cm)", value=valeur_profil_formulaire("height_cm"), step=0.5,
                                   placeholder="À renseigner")
        c3, c4 = st.columns(2)
        dep = c3.number_input("Poids de départ (kg)", value=valeur_profil_formulaire("start_weight_kg"),
                              step=0.5, placeholder="À renseigner")
        obj = c4.number_input("Poids objectif (kg)", value=valeur_profil_formulaire("target_weight_kg"),
                              step=0.5, placeholder="À renseigner")
        c5, c6 = st.columns(2)
        prot = c5.number_input("Protéines cibles (g/jour)", value=valeur_profil_formulaire("target_protein_g"),
                               step=5, placeholder="À renseigner")
        carb = c6.number_input("Glucides cibles (g/jour)", value=valeur_profil_formulaire("target_carbs_g"),
                               step=5, placeholder="À renseigner")
        c7, c8 = st.columns(2)
        lip = c7.number_input("Lipides cibles (g/jour)", value=valeur_profil_formulaire("target_fat_g"),
                              step=5, placeholder="À renseigner")
        kcal = c8.number_input("Calories cibles (kcal/jour)", value=valeur_profil_formulaire("target_kcal"),
                               step=50, placeholder="À renseigner")
        tdee = st.number_input("Dépense estimée (kcal/jour)", value=valeur_profil_formulaire("tdee_kcal"),
                               step=50, placeholder="À renseigner")
        if st.form_submit_button("💾 Enregistrer le profil", type="primary", width="stretch"):
            valeurs_profil = [taille_p, dep, obj, prot, carb, lip, kcal, tdee]
            if any(v is None or not _profil_valeur_renseignee(v) for v in valeurs_profil):
                st.error("Renseigne des valeurs positives dans tous les champs numériques. Rien n'a été modifié.")
            else:
                ok, msg = _enregistrer_profil(dict(
                    display_name=nom, height_cm=float(taille_p), start_weight_kg=float(dep),
                    target_weight_kg=float(obj), target_protein_g=int(round(prot)),
                    target_carbs_g=int(round(carb)), target_fat_g=int(round(lip)),
                    target_kcal=int(round(kcal)), tdee_kcal=int(round(tdee))))
                # Le message survit au rechargement et n'est créé qu'après une sauvegarde valide.
                st.session_state["_flash_profil"] = (
                    "✅ Profil enregistré — les nouveaux objectifs sont appliqués."
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
