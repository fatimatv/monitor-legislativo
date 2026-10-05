from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from .models import Proposition


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class StateStore:
    """Estado técnico local; Sheets no es la fuente de idempotencia."""

    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(path)
        self.connection.row_factory = sqlite3.Row
        self._migrate()

    def _migrate(self) -> None:
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS propositions (
              official_id TEXT PRIMARY KEY,
              source_hash TEXT NOT NULL,
              source_json TEXT NOT NULL,
              first_seen_at TEXT NOT NULL,
              last_seen_at TEXT NOT NULL,
              processing_status TEXT NOT NULL DEFAULT 'PENDIENTE',
              last_error TEXT
            );
            CREATE TABLE IF NOT EXISTS documents (
              official_id TEXT NOT NULL,
              document_id TEXT NOT NULL,
              sha256 TEXT,
              drive_file_id TEXT,
              status TEXT NOT NULL,
              PRIMARY KEY (official_id, document_id)
            );
            CREATE TABLE IF NOT EXISTS runs (
              run_id INTEGER PRIMARY KEY AUTOINCREMENT,
              mode TEXT NOT NULL,
              started_at TEXT NOT NULL,
              ended_at TEXT,
              status TEXT,
              summary_json TEXT
            );
            """
        )
        self.connection.commit()

    @staticmethod
    def source_hash(proposition: Proposition) -> str:
        source = json.dumps(proposition.source_data, ensure_ascii=False, sort_keys=True, default=str)
        return hashlib.sha256(source.encode("utf-8")).hexdigest()

    def upsert_proposition(self, proposition: Proposition) -> tuple[bool, bool]:
        digest = self.source_hash(proposition)
        previous = self.connection.execute(
            "SELECT source_hash FROM propositions WHERE official_id = ?", (proposition.official_id,)
        ).fetchone()
        now = utc_now()
        is_new = previous is None
        changed = is_new or previous["source_hash"] != digest
        self.connection.execute(
            """INSERT INTO propositions(official_id, source_hash, source_json, first_seen_at, last_seen_at)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(official_id) DO UPDATE SET source_hash=excluded.source_hash,
               source_json=excluded.source_json, last_seen_at=excluded.last_seen_at""",
            (proposition.official_id, digest, json.dumps(proposition.source_data, ensure_ascii=False, default=str), now, now),
        )
        self.connection.commit()
        return is_new, changed

    def save_document(self, official_id: str, document_id: str, sha256: str | None, drive_file_id: str | None, status: str) -> None:
        self.connection.execute(
            """INSERT INTO documents(official_id, document_id, sha256, drive_file_id, status) VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(official_id, document_id) DO UPDATE SET sha256=excluded.sha256,
               drive_file_id=COALESCE(excluded.drive_file_id, documents.drive_file_id), status=excluded.status""",
            (official_id, document_id, sha256, drive_file_id, status),
        )
        self.connection.commit()

    def document_known(self, official_id: str, document_id: str) -> bool:
        return self.connection.execute(
            "SELECT 1 FROM documents WHERE official_id = ? AND document_id = ? AND status = 'LISTO'", (official_id, document_id)
        ).fetchone() is not None

    def set_status(self, official_id: str, status: str, error: str | None = None) -> None:
        self.connection.execute(
            "UPDATE propositions SET processing_status=?, last_error=? WHERE official_id=?", (status, error, official_id)
        )
        self.connection.commit()

    def processing_status(self, official_id: str) -> str | None:
        row = self.connection.execute(
            "SELECT processing_status FROM propositions WHERE official_id=?", (official_id,)
        ).fetchone()
        return str(row["processing_status"]) if row else None

    def start_run(self, mode: str) -> int:
        cursor = self.connection.execute("INSERT INTO runs(mode, started_at) VALUES (?, ?)", (mode, utc_now()))
        self.connection.commit()
        return int(cursor.lastrowid)

    def finish_run(self, run_id: int, status: str, summary: dict) -> None:
        self.connection.execute(
            "UPDATE runs SET ended_at=?, status=?, summary_json=? WHERE run_id=?",
            (utc_now(), status, json.dumps(summary, ensure_ascii=False), run_id),
        )
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()
