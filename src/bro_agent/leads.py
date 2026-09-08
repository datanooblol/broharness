"""Persistent per-lead state -- survives across turns, unlike execute_skill's state dict.

Deliberately stdlib-only (sqlite3): one inspectable file, no ORM, structurally
close to what a real CRM table looks like.
"""
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from .skills import REPO_ROOT

DEFAULT_DB_PATH = REPO_ROOT / "data" / "leads.db"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def init_db(path: Path = DEFAULT_DB_PATH) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS leads (
                id TEXT PRIMARY KEY,
                contact TEXT NOT NULL,
                stage TEXT NOT NULL,
                fields TEXT NOT NULL,
                history TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS handoffs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id TEXT NOT NULL,
                notes TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
    return path


def create_lead(lead_id: str, contact: str, stage: str = "qualify", path: Path = DEFAULT_DB_PATH) -> dict:
    lead = {
        "id": lead_id,
        "contact": contact,
        "stage": stage,
        "fields": {},
        "history": [],
        "created_at": _now(),
        "updated_at": _now(),
    }
    with sqlite3.connect(path) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO leads (id, contact, stage, fields, history, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (lead["id"], lead["contact"], lead["stage"], json.dumps(lead["fields"]),
             json.dumps(lead["history"]), lead["created_at"], lead["updated_at"]),
        )
    return lead


def get_lead(lead_id: str, path: Path = DEFAULT_DB_PATH) -> dict:
    with sqlite3.connect(path) as conn:
        row = conn.execute(
            "SELECT id, contact, stage, fields, history, created_at, updated_at FROM leads WHERE id = ?",
            (lead_id,),
        ).fetchone()
    if row is None:
        raise KeyError(f"no such lead: {lead_id}")
    return {
        "id": row[0],
        "contact": row[1],
        "stage": row[2],
        "fields": json.loads(row[3]),
        "history": json.loads(row[4]),
        "created_at": row[5],
        "updated_at": row[6],
    }


def update_lead(lead_id: str, stage: str = None, fields: dict = None, append_history: dict = None,
                 path: Path = DEFAULT_DB_PATH) -> dict:
    lead = get_lead(lead_id, path)
    if stage is not None:
        lead["stage"] = stage
    if fields:
        lead["fields"].update(fields)
    if append_history is not None:
        lead["history"].append(append_history)
    lead["updated_at"] = _now()
    with sqlite3.connect(path) as conn:
        conn.execute(
            "UPDATE leads SET stage = ?, fields = ?, history = ?, updated_at = ? WHERE id = ?",
            (lead["stage"], json.dumps(lead["fields"]), json.dumps(lead["history"]), lead["updated_at"], lead_id),
        )
    return lead


def create_handoff(lead_id: str, notes: str, path: Path = DEFAULT_DB_PATH) -> str:
    with sqlite3.connect(path) as conn:
        conn.execute(
            "INSERT INTO handoffs (lead_id, notes, created_at) VALUES (?, ?, ?)",
            (lead_id, notes, _now()),
        )
    return f"handoff created for lead {lead_id}: {notes}"
