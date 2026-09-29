# -*- coding: utf-8 -*-
"""
Suivi Recomposition — application mobile de suivi
Stack : Streamlit (interface) + Supabase (base de données cloud) + GitHub (code)
Fonctionne aussi 100 % hors ligne en mode local (SQLite) tant que Supabase n'est pas configuré.

Lancement :  streamlit run app.py
"""
from __future__ import annotations

import datetime as dt
import io
import re
import time
import zipfile

import altair as alt
import pandas as pd
import streamlit as st

import content as C
import integration as IT
import editeurs as ED
import menus as MN
import repas as R
from db import LocalStore, SupaStore

# ============================================================================
#  CONFIGURATION
# ============================================================================
st.set_page_config(page_title="Suivi Recomposition", page_icon="💪",
                   layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
<style>
  .block-container{padding-top:1.6rem; padding-bottom:3rem; max-width:900px}
  h1{font-size:1.5rem !important} h2{font-size:1.2rem !important} h3{font-size:1.05rem !important}
  [data-testid="stMetricValue"]{font-size:1.5rem}
  .stButton>button{white-space:normal; text-align:left}
  @media (max-width:640px){
    .stButton>button{width:100%; padding:.55rem .7rem; font-size:.95rem}
    .block-container{padding-left:.8rem; padding-right:.8rem}
  }
  .bloc-card{background:#f4f7fa; border:1px solid #dfe6ec; border-radius:12px;
             padding:.8rem 1rem; margin:.3rem 0 .9rem 0}
  .bloc-title{font-weight:700; color:#0f2a43; font-size:1rem}
  .hint{color:#5b6b7c; font-size:.85rem}
  .sess-a{color:#0d9488; font-weight:700}
  .sess-b{color:#1b4b6b; font-weight:700}
</style>
""", unsafe_allow_html=True)

D = dt.date
VERSION = "2.0"   # affichée dans la barre latérale : permet de vérifier que le déploiement est à jour


# ============================================================================
#  INITIALISATION : stockage + authentification
# ============================================================================
def read_secrets():
    """Lit les Secrets (`.streamlit/secrets.toml` ou Streamlit Cloud) et nettoie les valeurs."""
    try:
        if "supabase" in st.secrets:
            cfg = st.secrets["supabase"]
            url = str(cfg.get("url", "") or "").strip().rstrip("/")
            key = str(cfg.get("anon_key", "") or "").strip()
            if url and key:
                return {"url": url, "anon_key": key}
    except Exception:
        return None
    return None


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


def login_page(store: SupaStore):
    st.title("💪 Suivi Recomposition")
    st.caption("Connexion à ton espace (Supabase)")
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
                st.rerun()
        except Exception as e:
            st.error(f"Échec : {e}")
    st.stop()


import json as _json
import os as _os


def menus_store():
    """Lecteur de la base de menus (tes 4 tables), mis en cache pour la session.

    Sans Supabase configuré : renvoie un extrait de démonstration, pour que tu
    puisses voir la page tout de suite (les chiffres sont alors incomplets).
    """
    VERSION_STORE = "29-09-2026b"      # à changer à chaque mise à jour du moteur
    ms = st.session_state.get("_menus_store")
    if ms is not None and st.session_state.get("_menus_version") == VERSION_STORE:
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
        sess = st.session_state.get("sb_session")
        if sess:
            try:
                store.resume(sess)
            except Exception:
                st.session_state.pop("sb_session", None)
        if not st.session_state.get("sb_session"):
            login_page(store)
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


TARGET_W = float(prof("target_weight_kg", C.TARGET_WEIGHT))
TARGET_P = int(prof("target_protein_g", C.TARGET_PROTEIN))
START_W = float(prof("start_weight_kg", C.START_WEIGHT))
HEIGHT = float(prof("height_cm", C.HEIGHT_CM))


# ============================================================================
#  OUTILS
# ============================================================================
def load_daily() -> pd.DataFrame:
    df = store.daily_df()
    if df.empty:
        return pd.DataFrame(columns=["log_date", "weight_kg", "body_fat_pct", "steps",
                                     "sleep_h", "protein_g", "kcal", "activity", "energy", "notes"])
    df["log_date"] = pd.to_datetime(df["log_date"]).dt.date
    for c in ("weight_kg", "body_fat_pct", "sleep_h"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df.sort_values("log_date").reset_index(drop=True)


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
    mapping = st.session_state.get("it_map") or lire_map(store) or ctx["mapping"]
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
    meas = store.meas_df()
    if not meas.empty:
        meas["meas_date"] = pd.to_datetime(meas["meas_date"]).dt.date
    prot = protein_by_day()
    phase, kcal_t = C.phase_for(D.today())

    w_avg = mean_since(daily, "weight_kg", 7)
    w_prev = mean_since(daily, "weight_kg", 7, D.today() - dt.timedelta(days=7))
    bf_avg = mean_since(daily, "body_fat_pct", 7)
    p_avg = mean_since(prot.rename(columns={"entry_date": "log_date", "total": "protein_g"}),
                       "protein_g", 7) if not prot.empty else None
    n_sess, sess_list = sessions_this_week()

    st.markdown(f"**Phase actuelle :** {phase} · cibles **{kcal_t[0]} kcal** (repos) / "
                f"**{kcal_t[1]} kcal** (entraînement) / **{kcal_t[2]} kcal** (rugby) · "
                f"**{TARGET_P} g de protéines**")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Poids moyen 7 j", fmt(w_avg, " kg", 2),
              None if (w_avg is None or w_prev is None) else f"{w_avg - w_prev:+.2f} kg")
    waist = None if meas.empty else (None if meas["waist_cm"].dropna().empty else float(meas["waist_cm"].dropna().iloc[-1]))
    waist_start = None if meas.empty else (None if meas["waist_cm"].dropna().empty else float(meas["waist_cm"].dropna().iloc[0]))
    c2.metric("Tour de taille", fmt(waist, " cm"),
              None if (waist is None or waist_start is None) else f"{waist - waist_start:+.1f} cm")
    c3.metric("Masse grasse (7 j)", fmt(bf_avg, " %"),
              None if (bf_avg is None or w_avg is None) else f"≈ {C.fat_mass_kg(w_avg, bf_avg):.1f} kg de gras")
    c4.metric("Protéines (7 j)", fmt(p_avg, " g", 0), f"cible {TARGET_P} g")

    # progression vers l'objectif
    if w_avg:
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
                domain=["Poids", "Moyenne 7 jours"], range=["#9ec9d9", "#0d9488"]),
                legend=alt.Legend(orient="bottom")),
            strokeWidth=alt.condition(alt.datum["Série"] == "Moyenne 7 jours",
                                      alt.value(3), alt.value(1.4)),
        ).properties(height=260, width="container")
        rule = alt.Chart(pd.DataFrame({"y": [TARGET_W]})).mark_rule(
            color="#d97706", strokeDash=[5, 4]).encode(y="y:Q")
        st.altair_chart(line + rule)

    # état du jour
    st.subheader("Aujourd'hui")
    today = D.today()
    row = daily[daily["log_date"] == today]
    p_today = 0 if prot.empty else int(prot[prot["entry_date"] == today]["total"].sum())
    lined = lambda ok: "✅" if ok else "⬜"
    st.markdown(
        f"{lined(not row.empty)} **Pesée du matin**  ·  "
        f"{lined(p_today >= TARGET_P)} **Protéines {p_today}/{TARGET_P} g**  ·  "
        f"{lined(n_sess >= (2 if today.weekday() >= 4 else 1))} **Séances cette semaine : {n_sess}/2**"
        f"{' (' + ', '.join(sess_list) + ')' if sess_list else ''}  ·  "
        f"{lined(not meas.empty)} **Mensurations**")
    if row.empty:
        st.info("Pense à enregistrer ta pesée du matin (page **⚖️ Pesée**).")

    # alertes coach
    alertes = []
    if w_prev and w_avg and (w_prev - w_avg) / 7 > 0.115:
        alertes.append("Perte > 0,8 kg/semaine → **ajoute 200 kcal** (glucides).")
    if p_avg is not None and p_avg < TARGET_P - 15:
        alertes.append(f"Protéines à {p_avg:.0f} g/j : c'est le levier n°1. Ajoute un shaker à 10 h 30 et 200 g de fromage blanc à 16 h.")
    if n_sess < 2 and today.weekday() >= 4:
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
                    "- Récupération du rugby > 3 jours, blessures à répétition")


# ============================================================================
#  PAGE 2 — PESÉE DU JOUR
# ============================================================================
def page_pesee():
    st.title("⚖️ Pesée du matin")
    st.caption("À jeun, après les toilettes, nu, même balance, même heure. Le chiffre du jour ne compte pas : "
               "c'est la **moyenne 7 jours** qui pilote les décisions.")
    daily = load_daily()
    today = D.today()
    existing = daily[daily["log_date"] == today]
    cur = existing.iloc[0] if not existing.empty else None

    with st.form("pesee"):
        c1, c2 = st.columns(2)
        with c1:
            d = st.date_input("Date", value=today, max_value=today, format="DD/MM/YYYY")
            poids = st.number_input("Poids (kg)", min_value=50.0, max_value=140.0, step=0.1,
                                    format="%.1f", value=float(cur["weight_kg"]) if cur is not None
                                    and pd.notna(cur["weight_kg"]) else (float(daily["weight_kg"].dropna().iloc[-1])
                                    if not daily["weight_kg"].dropna().empty else 80.0))
            bf = st.number_input("Masse grasse balance (%)", min_value=3.0, max_value=55.0, step=0.1,
                                 format="%.1f", value=float(cur["body_fat_pct"]) if cur is not None
                                 and pd.notna(cur["body_fat_pct"]) else 18.8,
                                 help="Balance à impédance (Tefal) : utile en tendance, pas en valeur absolue.")
            pas = st.number_input("Pas", min_value=0, max_value=40000, step=250,
                                  value=int(cur["steps"]) if cur is not None and pd.notna(cur["steps"]) else 10000)
        with c2:
            sommeil = st.number_input("Sommeil (h)", min_value=3.0, max_value=12.0, step=0.5, format="%.1f",
                                      value=float(cur["sleep_h"]) if cur is not None and pd.notna(cur["sleep_h"]) else 7.5)
            activite = st.selectbox("Activité du jour", ["Repos", "Séance A", "Séance B", "Rugby",
                                                        "Marche", "Musique", "Autre"],
                                    index=(["Repos", "Séance A", "Séance B", "Rugby", "Marche", "Musique", "Autre"]
                                           .index(cur["activity"]) if cur is not None and cur["activity"] in
                                           ["Repos", "Séance A", "Séance B", "Rugby", "Marche", "Musique", "Autre"] else 0))
            energie = st.slider("Énergie (1-10)", 1, 10, int(cur["energy"]) if cur is not None
                                and pd.notna(cur["energy"]) else 7)
            notes = st.text_area("Notes (faim, humeur, écart…)", value="" if cur is None else (cur["notes"] or ""),
                                 height=80)
        ok = st.form_submit_button("💾 Enregistrer la journée", type="primary", width="stretch")
    if ok:
        store.save_daily(dict(log_date=d, weight_kg=poids, body_fat_pct=bf, steps=int(pas),
                              sleep_h=sommeil, activity=activite, energy=int(energie), notes=notes))
        st.success("Journée enregistrée.")
        st.rerun()

    if bf:
        st.caption(f"Lecture : {bf:.1f} % de {poids:.1f} kg → **{C.fat_mass_kg(poids, bf)} kg de masse grasse** "
                   f"et **{C.lean_mass_kg(poids, bf)} kg de masse maigre** · IMC {C.bmi(poids, HEIGHT)}.")

    st.subheader("Tendance")
    r = rolling(daily, "weight_kg")
    if not r.empty:
        r2 = r.rename(columns={"log_date": "date", "weight_kg": "Poids", "moy7": "Moyenne 7 jours"})
        melt = r2.melt("date", ["Poids", "Moyenne 7 jours"], var_name="Série", value_name="kg")
        ch = alt.Chart(melt).mark_line().encode(
            x=alt.X("date:T", title=None), y=alt.Y("kg:Q", scale=alt.Scale(zero=False), title="kg"),
            color=alt.Color("Série:N", legend=alt.Legend(orient="bottom"), scale=alt.Scale(
                domain=["Poids", "Moyenne 7 jours"], range=["#c8d8e2", "#0d9488"])),
            strokeWidth=alt.condition(alt.datum["Série"] == "Moyenne 7 jours", alt.value(3), alt.value(1.2)),
        ).properties(height=240, width="container")
        st.altair_chart(ch + alt.Chart(pd.DataFrame({"y": [TARGET_W]})).mark_rule(
            color="#d97706", strokeDash=[5, 4]).encode(y="y:Q"))

    if not daily.empty:
        last = daily.sort_values("log_date", ascending=False).head(14)[
            ["log_date", "weight_kg", "body_fat_pct", "steps", "sleep_h", "activity", "energy"]]
        st.dataframe(last.rename(columns={
            "log_date": "Date", "weight_kg": "Poids", "body_fat_pct": "% gras", "steps": "Pas",
            "sleep_h": "Sommeil", "activity": "Activité", "energy": "Énergie"}),
            hide_index=True, width="stretch", height=330)


# ============================================================================
#  PAGE 3 — MENSURATIONS
# ============================================================================
def page_mensurations():
    st.title("📏 Mensurations")
    st.caption("Le **tour de taille au nombril** est ta vraie mesure de perte de gras — bien plus fiable que la balance. "
               "Lundi matin, à jeun, sans serrer, ventre relâché.")
    meas = store.meas_df()
    if not meas.empty:
        meas["meas_date"] = pd.to_datetime(meas["meas_date"]).dt.date
    today = D.today()
    last_meas = None if meas.empty else meas.iloc[-1]

    with st.form("mens"):
        c1, c2 = st.columns(2)
        with c1:
            d = st.date_input("Date", value=today, max_value=today, format="DD/MM/YYYY")
            taille = st.number_input("Tour de taille — nombril (cm)", 50.0, 160.0, step=0.1, format="%.1f",
                                     value=float(last_meas["waist_cm"]) if last_meas is not None
                                     and pd.notna(last_meas["waist_cm"]) else 90.0)
            hanches = st.number_input("Hanches (cm)", 50.0, 160.0, step=0.1, format="%.1f",
                                      value=float(last_meas["hips_cm"]) if last_meas is not None
                                      and pd.notna(last_meas.get("hips_cm")) else 98.0)
            poitrine = st.number_input("Poitrine (cm)", 50.0, 160.0, step=0.1, format="%.1f",
                                       value=float(last_meas["chest_cm"]) if last_meas is not None
                                       and pd.notna(last_meas.get("chest_cm")) else 102.0)
        with c2:
            cou = st.number_input("Tour de cou (cm)", 25.0, 60.0, step=0.1, format="%.1f",
                                  value=float(last_meas["neck_cm"]) if last_meas is not None
                                  and pd.notna(last_meas.get("neck_cm")) else 39.0,
                                  help="Sert au calcul Marine — deuxième estimation du % de graisse.")
            bras = st.number_input("Bras contracté (cm)", 20.0, 60.0, step=0.1, format="%.1f",
                                   value=float(last_meas["arm_cm"]) if last_meas is not None
                                   and pd.notna(last_meas.get("arm_cm")) else 36.0)
            cuisse = st.number_input("Cuisse (cm)", 30.0, 90.0, step=0.1, format="%.1f",
                                     value=float(last_meas["thigh_cm"]) if last_meas is not None
                                     and pd.notna(last_meas.get("thigh_cm")) else 57.0)
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
    c2.metric("Masse grasse estimée (Marine)", fmt(bf_navy, " %"), help="Formule US Navy : tour de taille, cou, taille.")
    c3.metric("Masse grasse balance 7 j", fmt(mean_since(daily, "body_fat_pct", 7), " %"),
              help="Impédancemètre : lecture en tendance uniquement.")
    if w_avg and bf_navy:
        st.caption(f"À {w_avg:.1f} kg avec {bf_navy:.1f} % → **{C.fat_mass_kg(w_avg, bf_navy)} kg de gras** "
                   f"et **{C.lean_mass_kg(w_avg, bf_navy)} kg de masse maigre**. "
                   f"Masse maigre stable = muscle préservé ✅")

    if not meas.empty and meas["waist_cm"].dropna().shape[0] >= 2:
        m = meas.dropna(subset=["waist_cm"]).rename(columns={"meas_date": "date", "waist_cm": "Tour de taille"})
        st.altair_chart(
            alt.Chart(m).mark_line(point=True, color="#0f2a43").encode(
                x=alt.X("date:T", title=None),
                y=alt.Y("Tour de taille:Q", scale=alt.Scale(zero=False), title="cm"),
            ).properties(height=230, width="container"))
    if not meas.empty:
        st.dataframe(meas.rename(columns={
            "meas_date": "Date", "waist_cm": "Taille", "hips_cm": "Hanches", "chest_cm": "Poitrine",
            "neck_cm": "Cou", "arm_cm": "Bras", "thigh_cm": "Cuisse", "photos": "Photos", "notes": "Notes"})[
            ["Date", "Taille", "Hanches", "Poitrine", "Cou", "Bras", "Cuisse", "Photos", "Notes"]],
            hide_index=True, width="stretch")


# ============================================================================
#  PAGE 4 — SÉANCE (30 MIN)
# ============================================================================
@st.fragment(run_every=1.0)
def rest_timer():
    until = st.session_state.get("rest_until", 0)
    if until <= time.time():
        return
    total = st.session_state.get("rest_total", 60)
    left = int(round(until - time.time()))
    st.progress(max(0.0, min(1.0, 1 - left / total)), text=f"⏱️ Repos en cours — **{left} s**  (chrono {total} s)")


def page_seance():
    st.title("💪 Séance — 30 minutes")
    st.caption("Format **supersets** : deux exercices enchaînés, 3 tours, repos court entre les tours. "
               "C'est ce qui permet de tout faire tenir en 30 minutes sans rien perdre en résultats.")
    daily = load_daily()
    today = D.today()
    default = "A" if today.weekday() in (0, 1, 2) else "B"
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        sess = st.radio("Séance", ["A", "B"], index=0 if default == "A" else 1, horizontal=True)
    with c2:
        d = st.date_input("Date", value=today, max_value=today, format="DD/MM/YYYY")
    with c3:
        rest_default = st.number_input("Repos (s)", 30, 120, step=15, value=60)

    S = C.SESSIONS[sess]
    cls = "sess-a" if sess == "A" else "sess-b"
    total_min = 4 + sum(b.get("min", 8) for b in S["blocs"])
    st.markdown(f"<div class='bloc-card'><span class='{cls}'>{S['nom']}</span><br>"
                f"<span class='hint'>Créneau habituel : {S['jour']} · format supersets : 4 min d'échauffement + "
                f"3 blocs × 3 tours ≈ <b>{total_min} min</b>. Enchaîne les deux exercices du bloc sans t'arrêter, "
                f"puis souffle pendant le repos. Débordement de 2 min ? Coupe le 3ᵉ tour du dernier bloc.</span></div>",
                unsafe_allow_html=True)

    # chrono de repos
    b1, b2 = st.columns([1, 1])
    if b1.button(f"⏱️ Démarrer un repos de {rest_default} s", width="stretch"):
        st.session_state["rest_until"] = time.time() + int(rest_default)
        st.session_state["rest_total"] = int(rest_default)
    if b2.button("⏹️ Stop chrono", width="stretch"):
        st.session_state["rest_until"] = 0
    rest_timer()

    with st.expander("🔥 Échauffement — 4 minutes (jamais sauté)", expanded=False):
        for w in S["warmup"]:
            st.markdown(f"- {w}")
        st.caption("Objectif : température corporelle + mobilité + préparation de la barre de traction. "
                   "C'est ta prévention des blessures pour le rugby.")

    rows_to_save = []
    for bloc in S["blocs"]:
        with st.container(border=True):
            st.markdown(f"**{bloc['bloc']}** · 3 tours · repos {bloc['repos']} s entre les tours"
                        f" · <span class='hint'>≈ {bloc.get('min', 8)} min</span>", unsafe_allow_html=True)
            for ex in bloc["exos"]:
                st.markdown(f"###### {ex['nom']} — cible {ex['cible']}")
                prev = last_sets(ex["nom"], sess, d)
                if prev:
                    st.caption(f"Dernière fois ({prev['date'].strftime('%d/%m')}) : {prev['reps']} reps · "
                               f"{prev['variant']}")
                    top = top_of_range(ex["cible"])
                    if top and all(int(x) >= top for x in re.findall(r"\d+", prev["reps"]) or []):
                        st.caption("⬆️ Haut de fourchette atteint sur toutes les séries → **monte d'un niveau** "
                                   "ou ajoute du lest.")
                var = st.selectbox("Variante (niveau)", ex["variantes"],
                                   index=min(2, len(ex["variantes"]) - 1), key=f"v{sess}{ex['nom']}{d}",
                                   label_visibility="collapsed")
                lest = st.selectbox("Lest", ex["lests"], key=f"l{sess}{ex['nom']}{d}",
                                    label_visibility="collapsed")
                cols = st.columns(3)
                reps = []
                for i, col in enumerate(cols, start=1):
                    with col:
                        reps.append(st.number_input(f"S{i}", min_value=0, max_value=60, value=0, step=1,
                                                    key=f"r{sess}{ex['nom']}{d}{i}"))
                for i, r in enumerate(reps, start=1):
                    if r and r > 0:
                        load = None
                        m = re.search(r"(\d+(?:[.,]\d+)?)\s*kg", lest)
                        if m:
                            load = float(m.group(1).replace(",", "."))
                        elif lest.strip().lower() == "poids du corps":
                            load = 0.0
                        rows_to_save.append(dict(set_date=d, session=sess, exercise=ex["nom"], set_no=i,
                                                 reps=int(r), load_kg=load, variant=var.split(" ", 1)[0],
                                                 rpe=None))
    with st.form("fin_seance"):
        c1, c2 = st.columns([1, 2])
        rpe = c1.slider("RPE global (1-10)", 1, 10, 8)
        notes = c2.text_input("Notes de séance", "")
        ok = st.form_submit_button("✅ Terminer et enregistrer la séance", type="primary", width="stretch")
    if ok:
        if not rows_to_save:
            st.warning("Saisis au moins une série avant de valider.")
        else:
            store.save_sets(rows_to_save)
            store.save_workout(dict(session_date=d, session=sess, duration_min=S["minutes"],
                                    rpe=int(rpe), notes=notes))
            st.success(f"Séance {sess} enregistrée : {len(rows_to_save)} séries.")
            st.rerun()

    st.subheader("Historique récent")
    df = store.sets_df()
    if df.empty:
        st.caption("Aucune série enregistrée pour l'instant.")
    else:
        df["set_date"] = pd.to_datetime(df["set_date"]).dt.date
        st.dataframe(df.sort_values(["set_date", "set_no"], ascending=[False, True]).head(40)[
            ["set_date", "session", "exercise", "set_no", "reps", "load_kg", "variant"]].rename(columns={
            "set_date": "Date", "session": "Séance", "exercise": "Exercice", "set_no": "Série",
            "reps": "Reps", "load_kg": "Lest (kg)", "variant": "Niveau"}),
            hide_index=True, width="stretch", height=300)
        trac = df[df["exercise"].str.contains("Tractions", case=False, na=False)]
        if not trac.empty:
            g = trac.groupby("set_date", as_index=False)["reps"].max().rename(columns={"set_date": "date"})
            st.caption("📈 **Suivi des tractions** — le meilleur indicateur de muscle préservé : "
                       "stable ou en hausse = tu ne perds pas de muscle.")
            st.altair_chart(alt.Chart(g).mark_line(point=True, color="#0d9488").encode(
                x=alt.X("date:T", title=None), y=alt.Y("reps:Q", title="meilleure série"),
            ).properties(height=200, width="container"))


# ============================================================================
#  PAGE 5 — PROTÉINES  (3 modes de saisie)
# ============================================================================
def _ajout_repas_prevu():
    """Mode 1 : choisir un repas prévu dans gestion-menus, avec la quantité mangée."""
    client, tables, mapping = contexte_menus()
    if not client:
        st.info("Ce mode lit ta base de menus : il a besoin des clés Supabase "
                "(voir le guide, étape « Les 2 clés »). En attendant, l'onglet **Mes raccourcis** "
                "fonctionne normalement.")
        return
    if not (mapping.get("tables") or {}).get("plan"):
        st.warning("Ta table de planning n'a pas été reconnue. Va sur la page **🍽️ Cuisine & menus "
                   "→ Étape 2** pour la désigner en deux clics.")
        return

    c1, c2 = st.columns([1, 2])
    with c1:
        jour = st.date_input("Jour", value=D.today(), format="DD/MM/YYYY", key="pr_jour")
    with c2:
        st.write("")
        st.caption("Les repas viennent directement de ton application **gestion-menus** "
                   "(`planned_meals` + `recipes` + `ingredients`).")

    repas = IT.repas_planifies(client, mapping, jour, jour)
    if not repas:
        st.caption("Aucun repas prévu à cette date dans gestion-menus. Change la date ci-dessus, "
                   "ajoute le repas dans ton application de menus, ou utilise l'onglet "
                   "**🥕 Ingrédient + quantité**.")
        return

    def _etiquette(i):
        r = repas[i]
        moment = f"{str(r['moment']).capitalize()} · " if r["moment"] else ""
        base = f"{r['prot_portion']:.0f} g de protéines par portion" if r["prot_portion"] \
            else "protéines non renseignées"
        return f"{moment}{r['nom']}  —  {base}"

    idx = st.selectbox("Repas prévu", range(len(repas)), format_func=_etiquette, key="pr_idx")
    r = repas[idx]

    c1, c2 = st.columns([1, 2])
    with c1:
        choix = st.radio("Quantité mangée", ["½", "1", "1½", "2", "autre"],
                         horizontal=True, index=1, key="pr_choix")
    with c2:
        if choix == "autre":
            portions = st.number_input("Portions (libre)", 0.1, 8.0, 1.0, 0.1,
                                       format="%.1f", key="pr_libre")
        else:
            portions = {"½": 0.5, "1": 1.0, "1½": 1.5, "2": 2.0}[choix]
            st.write("")
            st.caption("1 portion = ce que ta recette est censée représenter "
                       f"(ton planning indique {r['portions']:g} portion(s) pour ce plat).")

    if r["prot_portion"]:
        total_apport = r["prot_portion"] * portions
        st.metric(f"Protéines pour {portions:g} portion(s)", f"{total_apport:.0f} g",
                  f"{r['prot_portion']:.0f} g × {portions:g}")
    else:
        total_apport = st.number_input("Protéines (g) — à estimer à la main : ta recette n'a pas "
                                       "de valeurs nutritionnelles", 0, 300, 30, 5, key="pr_man")

    if st.button("➕ Ajouter au compteur du jour", type="primary", key="pr_add",
                 width="stretch"):
        libelle = f"{r['nom']} ({portions:g} portion" + ("s" if portions > 1 else "") + ")"
        store.add_protein(D.today(), libelle, int(round(total_apport)), qty=portions)
        st.success(f"+{int(round(total_apport))} g de protéines ajoutés.")
        st.rerun()

    autres = [x for x in repas if x is not r]
    if autres:
        with st.expander(f"Les autres repas de ce jour ({len(autres)})"):
            for x in autres:
                moment = f"{str(x['moment']).capitalize()} · " if x["moment"] else ""
                p = f"≈ {x['prot_portion']:.0f} g/portion" if x["prot_portion"] else "protéines inconnues"
                st.markdown(f"- {moment}**{x['nom']}** — {p}")


def _ajout_ingredient():
    """Mode 2 : choisir un ingrédient de sa base, avec quantité et unité."""
    client, tables, mapping = contexte_menus()
    if not client:
        st.info("Ce mode lit ta table `ingredients` : il a besoin des clés Supabase. "
                "En attendant, l'onglet **Mes raccourcis** fonctionne normalement.")
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
        st.caption(f"{len(liste)} ingrédients chargés depuis ta base — tape les premières lettres "
                   "pour filtrer la liste.")

    noms = [x["nom"] for x in liste]
    idx = st.selectbox("Ingrédient", range(len(noms)), format_func=lambda i: noms[i], key="ing_idx")
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
                                          float(sugg), 5.0, key=f"ing_pp_{idx}")
        with c3:
            qte = st.number_input("Quantité", 0.25, 200.0, 1.0, 0.25, key=f"ing_qp_{idx}")
    else:
        with c2:
            qte = st.number_input("Quantité", 0.0, 5000.0, 100.0, 10.0, key=f"ing_q_{idx}_{unite}")
        with c3:
            st.write("")
            st.caption("Tu peux taper une valeur précise.")

    grammes, explication = IT.convertir_grammes(qte, unite, poids_piece)
    base = st.radio("Dans ta base, les protéines sont indiquées…",
                    ["pour 100 g", "par portion ou par pièce"],
                    horizontal=True, key=f"ing_base_{idx}")

    if ing["prot100"] is None:
        st.warning("Pas de valeur de protéines pour cet ingrédient dans ta base.")
        apport = st.number_input("Protéines (g) — saisie manuelle", 0, 300, 20, 1, key="ing_man")
    elif base == "pour 100 g":
        apport = ing["prot100"] * grammes / 100.0
    else:
        apport = ing["prot100"] * qte

    c1, c2 = st.columns([1, 2])
    c1.metric("Protéines", f"{apport:.0f} g")
    with c2:
        st.write("")
        st.caption(f"Calcul : {explication}"
                   + (f" × {ing['prot100']:g} g/100 g = **{apport:.0f} g**" if base == "pour 100 g"
                      and ing["prot100"] is not None else ""))

    if st.button("➕ Ajouter au compteur du jour", type="primary", key="ing_add", width="stretch"):
        libelle = f"{ing['nom']} {qte:g} {unite}"
        store.add_protein(D.today(), libelle, int(round(apport)), qty=qte)
        st.success(f"+{int(round(apport))} g de protéines ajoutés.")
        st.rerun()


def _ajout_raccourcis():
    """Mode 3 : les raccourcis rapides + saisie libre."""
    st.caption("Pour les aliments que tu manges tous les jours : un appui, c'est compté.")
    cols = st.columns(2)
    for i, (label, g) in enumerate(C.PROTEIN_PRESETS):
        with cols[i % 2]:
            if st.button(f"{label} · +{g} g", key=f"p_{i}", width="stretch"):
                store.add_protein(D.today(), label, g)
                st.rerun()
    with st.form("custom"):
        c1, c2 = st.columns([2, 1])
        label = c1.text_input("Autre aliment / repas", placeholder="Ex. restaurant, repas chez des amis…")
        g = c2.number_input("Protéines (g)", 0, 200, 30, step=5)
        if st.form_submit_button("Ajouter", width="stretch") and label:
            store.add_protein(D.today(), label, g)
            st.rerun()


def page_proteines():
    st.title("🥗 Protéines du jour")
    st.caption(f"Objectif : **{TARGET_P} g/jour** (plancher 130 g). Le levier n°1 pour perdre du gras "
               "sans perdre de muscle.")
    today = D.today()
    df = store.protein_df()
    if not df.empty:
        df["entry_date"] = pd.to_datetime(df["entry_date"]).dt.date
    p_today = 0 if df.empty else int(df[df["entry_date"] == today]["protein_g"].sum())

    st.progress(min(1.0, p_today / TARGET_P),
                text=f"**{p_today} g / {TARGET_P} g**" + (" ✅ objectif atteint" if p_today >= TARGET_P
                else f" — il reste {TARGET_P - p_today} g"))
    pb_all = protein_by_day()
    c1, c2, c3 = st.columns(3)
    c1.metric("Moyenne 7 j", fmt(mean_since(pb_all.rename(columns={"entry_date": "log_date",
                                                                  "total": "protein_g"}),
                                             "protein_g", 7) if not pb_all.empty else None, " g", 0))
    c2.metric("Moyenne 30 j", fmt(mean_since(pb_all.rename(columns={"entry_date": "log_date",
                                                                   "total": "protein_g"}),
                                              "protein_g", 30) if not pb_all.empty else None, " g", 0))
    c3.metric("Jours ≥ objectif (30 j)",
              int(sum(1 for _, t_ in protein_by_day(today - dt.timedelta(days=30)).itertuples(index=False)
                      if t_ >= TARGET_P)), "jours")

    t1, t2, t3 = st.tabs(["🍽️ Repas prévu", "🥕 Ingrédient + quantité", "⚡ Mes raccourcis"])
    with t1:
        _ajout_repas_prevu()
    with t2:
        _ajout_ingredient()
    with t3:
        _ajout_raccourcis()

    if not df.empty:
        auj = df[df["entry_date"] == today]
        if not auj.empty:
            st.markdown("**Détail du jour**")
            for r in auj.itertuples():
                c1, c2 = st.columns([5, 1])
                c1.markdown(f"• {r.item} — **{r.protein_g} g**")
                if c2.button("✕", key=f"del_{r.id}"):
                    store.delete_protein(r.id)
                    st.rerun()

        pb = protein_by_day(today - dt.timedelta(days=21))
        if not pb.empty:
            pb = pb.rename(columns={"entry_date": "date", "total": "Protéines"})
            st.altair_chart(alt.Chart(pb).mark_bar(color="#0d9488").encode(
                x=alt.X("date:T", title=None), y=alt.Y("Protéines:Q", title="g/jour"),
            ).properties(height=200, width="container") + alt.Chart(
                pd.DataFrame({"y": [TARGET_P]})).mark_rule(color="#d97706", strokeDash=[5, 4]).encode(y="y:Q"))

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
        R.page_repas(store, menus_store, TARGET_P)
        return
    st.session_state.setdefault("_pid", None)
    ED.page_planifier(ms, TARGET_P)


def page_recettes_edition():
    ms = menus_store()
    if ms is None:
        R.page_repas(store, menus_store, TARGET_P)
        return
    ED.page_recettes_edition(ms)


def page_ingredients():
    ms = menus_store()
    if ms is None:
        R.page_repas(store, menus_store, TARGET_P)
        return
    ED.page_ingredients(ms)


def page_cuisine():
    R.page_repas(store, menus_store, TARGET_P)


# ============================================================================
#  PAGE 6 — COURSES
# ============================================================================
def page_courses():
    st.title("🛒 Courses de la semaine")
    st.caption("Une seule sortie par semaine (samedi). Coche au fur et à mesure.")

    # ---- ce que demandent tes menus (calculé depuis ton planning)
    try:
        R.bloc_courses_auto(store, menus_store)
    except Exception as e:
        st.caption(f"(Liste automatique indisponible pour l'instant : {type(e).__name__})")

    st.divider()
    st.subheader("✅ Ma liste type — à cocher samedi")
    monday = D.today() - dt.timedelta(days=D.today().weekday())
    week = st.date_input("Semaine du (lundi)", value=monday, format="DD/MM/YYYY")
    state = store.shopping_dict(week)

    total = sum(p for _, _, _, p, _, _ in C.SHOPPING)
    checked = sum(1 for rayon, prod, q, p, r_, u in C.SHOPPING if state.get(prod, False))
    st.progress(checked / len(C.SHOPPING), text=f"{checked}/{len(C.SHOPPING)} articles cochés · "
                                                f"panier complet ≈ **{total:.2f} €** "
                                                f"(ma part protéines ≈ 39 €/semaine)")
    for rayon in ["ÉPICERIE", "CONGÉLATEUR", "FRIGO"]:
        st.subheader(rayon.capitalize() + (" (zéro place au frigo)" if rayon == "ÉPICERIE" else ""))
        for r_, prod, q, p, ou_, usage in [x for x in C.SHOPPING if x[0] == rayon]:
            c1, c2 = st.columns([6, 1])
            on = c1.checkbox(f"**{prod}** — {q} · {p:.2f} € · *{ou_}* — {usage}",
                             value=state.get(prod, False), key=f"shop_{prod}_{week}")
            if on != state.get(prod, False):
                store.set_shopping(prod, week, on)
                st.rerun()
            c2.caption("")
    st.caption("★ = indispensable. Les prix sont des ordres de grandeur (sept. 2026) : adapte-les à tes enseignes.")


# ============================================================================
#  PAGE 7 — RÉGLAGES / DONNÉES
# ============================================================================
def page_reglages():
    st.title("⚙️ Réglages & données")
    st.caption(f"Stockage actuel : **{store.label}**")
    if store.kind == "local":
        st.info("**Mode local** : tes données sont dans un fichier SQLite sur cet appareil — aucune synchronisation "
                "entre ton PC et ton téléphone. Pour passer sur Supabase (gratuit) : suis le README du dépôt, "
                "puis renseigne `.streamlit/secrets.toml`.")
    else:
        if st.button("Se déconnecter"):
            store.sign_out()
            st.session_state.pop("sb_session", None)
            st.session_state.pop("store", None)
            st.rerun()

    st.subheader("Mon profil et mes objectifs")
    with st.form("profil"):
        c1, c2 = st.columns(2)
        nom = c1.text_input("Prénom", value=str(prof("display_name", "")))
        taille_p = c2.number_input("Taille (cm)", 140.0, 220.0, HEIGHT, step=0.5)
        c3, c4 = st.columns(2)
        dep = c3.number_input("Poids de départ (kg)", 40.0, 200.0, START_W, step=0.5)
        obj = c4.number_input("Poids objectif (kg)", 40.0, 200.0, TARGET_W, step=0.5)
        c5, c6 = st.columns(2)
        prot = c5.number_input("Protéines cibles (g/jour)", 80, 250, TARGET_P, step=5)
        tdee = c6.number_input("Dépense estimée (kcal/jour)", 1500, 4000,
                               int(prof("tdee_kcal", C.TDEE)), step=50)
        if st.form_submit_button("💾 Enregistrer le profil", type="primary", width="stretch"):
            store.save_profile(dict(display_name=nom, height_cm=taille_p, start_weight_kg=dep,
                                    target_weight_kg=obj, target_protein_g=int(prot), tdee_kcal=int(tdee),
                                    phase=C.phase_for(D.today())[0]))
            st.success("Profil enregistré. Recharge la page pour appliquer.")
            st.rerun()

    st.subheader("Export de mes données")
    data = store.export_all()
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name, df in data.items():
            z.writestr(f"{name}.csv", df.to_csv(index=False))
    st.download_button("⬇️ Télécharger un ZIP de sauvegarde (CSV)", buf.getvalue(),
                       file_name=f"suivi_{D.today().isoformat()}.zip", mime="application/zip",
                       width="stretch")
    for name, df in data.items():
        st.caption(f"{name} : {len(df)} lignes")

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

    with st.expander("🔧 Comment ça marche / déploiement"):
        st.markdown(
            "- **Code** : GitHub (versionné, gratuit, privé si tu veux)\n"
            "- **Données** : Supabase — Postgres gratuit, protégé par RLS (chacun ne voit que ses lignes)\n"
            "- **Interface** : Streamlit, hébergée gratuitement sur Streamlit Community Cloud\n"
            "- **Mobile** : ouvre l'URL de l'app dans Chrome/Safari → *Ajouter à l'écran d'accueil* "
            "→ elle se lance comme une appli, plein écran\n\n"
            "Tout le détail de l'installation est dans le `README.md` du projet.")


# ============================================================================
#  NAVIGATION
# ============================================================================
pages = [
    st.Page(page_safe(page_dashboard), title="Tableau de bord", icon="🏠", default=True),
    st.Page(page_safe(page_pesee), title="Pesée & tendance", icon="⚖️"),
    st.Page(page_safe(page_seance), title="Séance 30 min", icon="💪"),
    st.Page(page_safe(page_proteines), title="Protéines", icon="🥗"),
    st.Page(page_safe(page_cuisine), title="Repas & menus", icon="🍽️"),
    st.Page(page_safe(page_planifier), title="Planifier", icon="📅"),
    st.Page(page_safe(page_recettes_edition), title="Mes recettes", icon="🥣"),
    st.Page(page_safe(page_ingredients), title="Mes ingrédients", icon="🥕"),
    st.Page(page_safe(page_mensurations), title="Mensurations", icon="📏"),
    st.Page(page_safe(page_courses), title="Courses", icon="🛒"),
    st.Page(page_safe(page_reglages), title="Réglages", icon="⚙️"),
]
st.sidebar.markdown(f"**Suivi Recomposition** <span class='hint'>v{VERSION}</span>  \n<span class='hint'>{store.label}</span>",
                    unsafe_allow_html=True)
st.sidebar.caption(f"Objectif : {TARGET_W:.0f} kg · {TARGET_P} g de protéines/jour")

# Lien facultatif vers l'application de menus (à déclarer dans les Secrets, section [apps])
try:
    _menus_url = st.secrets.get("apps", {}).get("menus_url")
except Exception:
    _menus_url = None
if _menus_url:
    st.sidebar.link_button("🍽️ Ouvrir Menus & recettes", _menus_url, width="stretch")

# Hook de test (utilisé par test_app.py pour vérifier chaque page sans navigateur)
import os

_test_page = os.environ.get("APP_TEST_PAGE")
if _test_page:
    {"dashboard": page_dashboard, "pesee": page_pesee, "seance": page_seance,
     "proteines": page_proteines, "mensurations": page_mensurations,
     "courses": page_courses, "reglages": page_reglages, "cuisine": page_cuisine,
     "planifier": page_planifier, "recettes": page_recettes_edition,
     "ingredients": page_ingredients}[_test_page]()
else:
    st.navigation(pages).run()
