# -*- coding: utf-8 -*-
"""Couche de données : Supabase (cloud, synchronisé) ou SQLite local (hors ligne).

Le reste de l'application ne connaît que l'interface commune :
    daily_df / save_daily / delete_daily
    meas_df / save_measurement
    sets_df / save_sets
    workouts_df / save_workout
    protein_df / add_protein / delete_protein
    shopping_dict / set_shopping
    profile / save_profile
    export_all
"""
from __future__ import annotations

import datetime as dt
import json
import os
import sqlite3
import pandas as pd

LOCAL_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "suivi.db")
USER = "local"

DDL = """
create table if not exists profiles(
  user_id text primary key, display_name text, height_cm real, start_weight_kg real,
  target_weight_kg real, target_protein_g integer, tdee_kcal integer, phase text);
create table if not exists daily_logs(
  user_id text, log_date text, weight_kg real, body_fat_pct real, steps integer,
  sleep_h real, protein_g integer, kcal integer, activity text, energy integer, notes text,
  primary key(user_id, log_date));
create table if not exists measurements(
  user_id text, meas_date text, waist_cm real, hips_cm real, chest_cm real, arm_cm real,
  thigh_cm real, neck_cm real, photos integer, notes text, primary key(user_id, meas_date));
create table if not exists workouts(
  user_id text, session_date text, session text, duration_min integer, rpe integer, notes text,
  primary key(user_id, session_date, session));
create table if not exists workout_sets(
  user_id text, set_date text, session text, exercise text, set_no integer, reps integer,
  load_kg real, variant text, rpe integer,
  primary key(user_id, set_date, session, exercise, set_no));
create table if not exists protein_entries(
  id integer primary key autoincrement, user_id text, entry_date text, item text,
  protein_g integer, qty real);
create table if not exists shopping_state(
  user_id text, item_key text, week_of text, checked integer, primary key(user_id, item_key, week_of));
create table if not exists integration_map(
  user_id text primary key, mapping text);
"""


def _df(rows, cols=()):
    if not rows:
        return pd.DataFrame(columns=list(cols))
    return pd.DataFrame(rows)


def _upsert_sql(table, keys, row):
    cols = list(row.keys())
    ph = ", ".join("?" for _ in cols)
    updates = ", ".join(f"{c}=excluded.{c}" for c in cols if c not in keys)
    sql = (f"insert into {table} ({', '.join(cols)}) values ({ph}) "
           f"on conflict({', '.join(keys)}) do update set {updates}")
    return sql, [row[c] for c in cols]


class LocalStore:
    """Mode local : un simple fichier SQLite. Aucun compte, aucun cloud, marche hors ligne."""

    kind = "local"
    label = "Local (SQLite)"

    def __init__(self, path: str = LOCAL_DB):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.path = path
        with sqlite3.connect(self.path) as con:
            con.executescript(DDL)
        self.user_id = USER
        self._ensure_profile()

    # -------- outils
    def _con(self):
        return sqlite3.connect(self.path)

    def _q(self, sql, params=()):
        with self._con() as con:
            return pd.read_sql_query(sql, con, params=params)

    def _ensure_profile(self):
        if self.profile() is None:
            self.save_profile(dict(display_name="Jérôme", height_cm=185, start_weight_kg=85.0,
                                   target_weight_kg=77.0, target_protein_g=140, tdee_kcal=2670,
                                   phase="Bloc 0 — Remise à niveau"))

    # -------- profil
    def profile(self):
        df = self._q("select * from profiles where user_id=?", (self.user_id,))
        return None if df.empty else df.iloc[0].to_dict()

    def save_profile(self, data: dict):
        row = dict(data); row["user_id"] = self.user_id
        sql, params = _upsert_sql("profiles", ["user_id"], row)
        with self._con() as con:
            con.execute(sql, params)

    # -------- journal quotidien
    def daily_df(self, since=None):
        sql = "select * from daily_logs where user_id=?"
        p = [self.user_id]
        if since:
            sql += " and log_date>=?"; p.append(str(since))
        return self._q(sql + " order by log_date", tuple(p))

    def save_daily(self, row: dict):
        row = dict(row); row["user_id"] = self.user_id
        row["log_date"] = str(row["log_date"])
        sql, params = _upsert_sql("daily_logs", ["user_id", "log_date"], row)
        with self._con() as con:
            con.execute(sql, params)

    def delete_daily(self, d):
        with self._con() as con:
            con.execute("delete from daily_logs where user_id=? and log_date=?", (self.user_id, str(d)))

    # -------- mensurations
    def meas_df(self):
        df = self._q("select * from measurements where user_id=? order by meas_date", (self.user_id,))
        if not df.empty:
            df["meas_date"] = pd.to_datetime(df["meas_date"]).dt.date
        return df

    def save_measurement(self, row: dict):
        row = dict(row); row["user_id"] = self.user_id
        row["meas_date"] = str(row["meas_date"])
        row["photos"] = int(bool(row.get("photos")))
        sql, params = _upsert_sql("measurements", ["user_id", "meas_date"], row)
        with self._con() as con:
            con.execute(sql, params)

    # -------- séances
    def workouts_df(self):
        df = self._q("select * from workouts where user_id=? order by session_date", (self.user_id,))
        if not df.empty:
            df["session_date"] = pd.to_datetime(df["session_date"]).dt.date
        return df

    def save_workout(self, row: dict):
        row = dict(row); row["user_id"] = self.user_id
        row["session_date"] = str(row["session_date"])
        sql, params = _upsert_sql("workouts", ["user_id", "session_date", "session"], row)
        with self._con() as con:
            con.execute(sql, params)

    def sets_df(self, since=None):
        sql = "select * from workout_sets where user_id=?"
        p = [self.user_id]
        if since:
            sql += " and set_date>=?"; p.append(str(since))
        df = self._q(sql + " order by set_date desc", tuple(p))
        if not df.empty:
            df["set_date"] = pd.to_datetime(df["set_date"]).dt.date
        return df

    def save_sets(self, rows: list[dict]):
        for r in rows:
            r = dict(r); r["user_id"] = self.user_id; r["set_date"] = str(r["set_date"])
            sql, params = _upsert_sql(
                "workout_sets", ["user_id", "set_date", "session", "exercise", "set_no"], r)
            with self._con() as con:
                con.execute(sql, params)

    # -------- protéines
    def protein_df(self, since=None, until=None):
        sql = "select * from protein_entries where user_id=?"
        p = [self.user_id]
        if since:
            sql += " and entry_date>=?"; p.append(str(since))
        if until:
            sql += " and entry_date<=?"; p.append(str(until))
        return self._q(sql + " order by entry_date desc, id desc", tuple(p))

    def add_protein(self, d, item, grams, qty=1.0):
        with self._con() as con:
            con.execute("insert into protein_entries (user_id, entry_date, item, protein_g, qty)"
                        " values (?,?,?,?,?)", (self.user_id, str(d), item, int(grams), float(qty)))

    def delete_protein(self, entry_id):
        with self._con() as con:
            con.execute("delete from protein_entries where id=? and user_id=?", (int(entry_id), self.user_id))

    # -------- courses
    def shopping_dict(self, week_of):
        df = self._q("select item_key, checked from shopping_state where user_id=? and week_of=?",
                     (self.user_id, str(week_of)))
        return {r.item_key: bool(r.checked) for r in df.itertuples()}

    def set_shopping(self, item_key, week_of, checked):
        row = dict(user_id=self.user_id, item_key=item_key, week_of=str(week_of), checked=int(bool(checked)))
        sql, params = _upsert_sql("shopping_state", ["user_id", "item_key", "week_of"], row)
        with self._con() as con:
            con.execute(sql, params)

    # -------- passerelle menus (indisponible en mode local)
    @property
    def client(self):
        return None

    def get_map(self):
        df = self._q("select mapping from integration_map where user_id=?", (self.user_id,))
        if df.empty:
            return {}
        try:
            return json.loads(df.iloc[0]["mapping"] or "{}")
        except Exception:
            return {}

    def save_map(self, mapping: dict):
        with self._con() as con:
            con.execute("insert into integration_map (user_id, mapping) values (?,?) "
                        "on conflict(user_id) do update set mapping=excluded.mapping",
                        (self.user_id, json.dumps(mapping, ensure_ascii=False)))

    # -------- passerelle avec l'application de menus
    def get_map(self):
        try:
            r = (self.client.table(self._t("integration_map"))
                 .select("mapping").eq("user_id", self.user_id).limit(1).execute())
            if r.data:
                m = r.data[0].get("mapping") or {}
                return m if isinstance(m, dict) else json.loads(m)
        except Exception:
            pass
        return {}

    def save_map(self, mapping: dict):
        self.client.table(self._t("integration_map")).upsert(
            dict(user_id=self.user_id, mapping=mapping),
            on_conflict="user_id").execute()

    # -------- export
    def export_all(self):
        return {
            "daily_logs": self.daily_df(),
            "measurements": self.meas_df(),
            "workouts": self.workouts_df(),
            "workout_sets": self.sets_df(),
            "protein_entries": self.protein_df(),
        }


class SupaStore:
    """Mode cloud : Supabase (Postgres + Auth + RLS). Synchronise PC et mobile."""

    kind = "supabase"
    label = "Supabase (synchronisé)"

    # Toutes les tables portent ce préfixe : le schéma peut donc être installé
    # dans un projet Supabase déjà utilisé pour autre chose, sans collision.
    PREFIX = "sr_"

    def _t(self, name: str) -> str:
        return f"{self.PREFIX}{name}"

    def __init__(self, url: str, anon_key: str):
        from supabase import create_client
        self.client = create_client(url, anon_key)
        self.user_id = None
        self.email = None

    # -------- auth
    def sign_in(self, email, password):
        res = self.client.auth.sign_in_with_password({"email": email, "password": password})
        self.user_id = res.user.id
        self.email = email
        return dict(access_token=res.session.access_token,
                    refresh_token=res.session.refresh_token,
                    user_id=res.user.id, email=email)

    def sign_up(self, email, password):
        res = self.client.auth.sign_up({"email": email, "password": password})
        return bool(res.user)

    def resume(self, sess: dict):
        self.client.auth.set_session(sess["access_token"], sess["refresh_token"])
        self.user_id = sess["user_id"]
        self.email = sess.get("email")

    def sign_out(self):
        try:
            self.client.auth.sign_out()
        except Exception:
            pass

    # -------- outils
    def _select(self, table, filters=None, order=None, desc=False):
        q = self.client.table(self._t(table)).select("*").eq("user_id", self.user_id)
        for k, v in (filters or {}).items():
            q = q.eq(k, v)
        if order:
            q = q.order(order, desc=desc)
        return pd.DataFrame(q.execute().data or [])

    # -------- profil
    def profile(self):
        df = self._select("profiles")
        return None if df.empty else df.iloc[0].to_dict()

    def save_profile(self, data: dict):
        row = dict(data); row["user_id"] = self.user_id
        self.client.table(self._t("profiles")).upsert(row, on_conflict="user_id").execute()

    # -------- journal quotidien
    def daily_df(self, since=None):
        f = {"log_date": str(since)} if since else None
        df = self._select("daily_logs", f, "log_date")
        if not df.empty:
            df["log_date"] = pd.to_datetime(df["log_date"]).dt.date
        return df

    def save_daily(self, row: dict):
        row = dict(row); row["user_id"] = self.user_id; row["log_date"] = str(row["log_date"])
        self.client.table(self._t("daily_logs")).upsert(row, on_conflict="user_id,log_date").execute()

    def delete_daily(self, d):
        self.client.table(self._t("daily_logs")).delete().eq("user_id", self.user_id).eq("log_date", str(d)).execute()

    # -------- mensurations
    def meas_df(self):
        df = self._select("measurements", None, "meas_date")
        if not df.empty:
            df["meas_date"] = pd.to_datetime(df["meas_date"]).dt.date
        return df

    def save_measurement(self, row: dict):
        row = dict(row); row["user_id"] = self.user_id; row["meas_date"] = str(row["meas_date"])
        self.client.table(self._t("measurements")).upsert(row, on_conflict="user_id,meas_date").execute()

    # -------- séances
    def workouts_df(self):
        df = self._select("workouts", None, "session_date")
        if not df.empty:
            df["session_date"] = pd.to_datetime(df["session_date"]).dt.date
        return df

    def save_workout(self, row: dict):
        row = dict(row); row["user_id"] = self.user_id; row["session_date"] = str(row["session_date"])
        self.client.table(self._t("workouts")).upsert(row, on_conflict="user_id,session_date,session").execute()

    def sets_df(self, since=None):
        f = {"set_date": str(since)} if since else None
        df = self._select("workout_sets", f, "set_date", desc=True)
        if not df.empty:
            df["set_date"] = pd.to_datetime(df["set_date"]).dt.date
        return df

    def save_sets(self, rows: list[dict]):
        payload = []
        for r in rows:
            r = dict(r); r["user_id"] = self.user_id; r["set_date"] = str(r["set_date"])
            payload.append(r)
        if payload:
            self.client.table(self._t("workout_sets")).upsert(
                payload, on_conflict="user_id,set_date,session,exercise,set_no").execute()

    # -------- protéines
    def protein_df(self, since=None, until=None):
        q = self.client.table(self._t("protein_entries")).select("*").eq("user_id", self.user_id)
        if since:
            q = q.gte("entry_date", str(since))
        if until:
            q = q.lte("entry_date", str(until))
        df = pd.DataFrame(q.order("entry_date", desc=True).execute().data or [])
        if not df.empty:
            df["entry_date"] = pd.to_datetime(df["entry_date"]).dt.date
        return df

    def add_protein(self, d, item, grams, qty=1.0):
        self.client.table(self._t("protein_entries")).insert(
            dict(user_id=self.user_id, entry_date=str(d), item=item,
                 protein_g=int(grams), qty=float(qty))).execute()

    def delete_protein(self, entry_id):
        self.client.table(self._t("protein_entries")).delete().eq("user_id", self.user_id).eq("id", int(entry_id)).execute()

    # -------- courses
    def shopping_dict(self, week_of):
        df = self._select("shopping_state", {"week_of": str(week_of)})
        return {} if df.empty else {r.item_key: bool(r.checked) for r in df.itertuples()}

    def set_shopping(self, item_key, week_of, checked):
        self.client.table(self._t("shopping_state")).upsert(
            dict(user_id=self.user_id, item_key=item_key, week_of=str(week_of),
                 checked=bool(checked)), on_conflict="user_id,item_key,week_of").execute()

    # -------- export
    def export_all(self):
        return {
            "daily_logs": self.daily_df(),
            "measurements": self.meas_df(),
            "workouts": self.workouts_df(),
            "workout_sets": self.sets_df(),
            "protein_entries": self.protein_df(),
        }
