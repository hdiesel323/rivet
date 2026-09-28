from __future__ import annotations

import csv
import io
import json
import os
import sqlite3
from typing import Any, Optional

SCHEMA = """
CREATE TABLE IF NOT EXISTS receipts (
  id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL,
  request_hash TEXT NOT NULL,
  cluster TEXT NOT NULL,
  classifier_id TEXT NOT NULL,
  labels_json TEXT,
  confidence REAL,
  model_used TEXT NOT NULL,
  provider TEXT NOT NULL,
  experiment_cell TEXT NOT NULL,
  input_tokens INTEGER NOT NULL,
  output_tokens INTEGER NOT NULL,
  vendor_usd REAL NOT NULL,
  rivet_usd REAL NOT NULL,
  latency_ms INTEGER NOT NULL,
  fallback INTEGER NOT NULL,
  cache_hit INTEGER NOT NULL,
  why TEXT NOT NULL,
  prompt TEXT,
  response TEXT,
  slot TEXT,
  escalated INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_receipts_hash ON receipts(request_hash);
CREATE INDEX IF NOT EXISTS idx_receipts_cluster ON receipts(cluster);
CREATE INDEX IF NOT EXISTS idx_receipts_created ON receipts(created_at);
"""

COLUMNS = [
    "id",
    "created_at",
    "request_hash",
    "cluster",
    "classifier_id",
    "labels_json",
    "confidence",
    "model_used",
    "provider",
    "experiment_cell",
    "input_tokens",
    "output_tokens",
    "vendor_usd",
    "rivet_usd",
    "latency_ms",
    "fallback",
    "cache_hit",
    "why",
    "prompt",
    "response",
    "slot",
    "escalated",
]


def connect(path: str) -> sqlite3.Connection:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def init_db(path: str) -> None:
    conn = connect(path)
    conn.close()


def insert(path: str, row: dict[str, Any]) -> None:
    conn = connect(path)
    try:
        placeholders = ",".join("?" for _ in COLUMNS)
        cols = ",".join(COLUMNS)
        values = [row.get(col) for col in COLUMNS]
        conn.execute(f"INSERT INTO receipts ({cols}) VALUES ({placeholders})", values)
        conn.commit()
    finally:
        conn.close()


def lookup_exact(path: str, request_hash: str) -> Optional[dict[str, Any]]:
    conn = connect(path)
    try:
        cur = conn.execute(
            "SELECT * FROM receipts WHERE request_hash = ? AND cache_hit = 0 "
            "ORDER BY created_at ASC LIMIT 1",
            (request_hash,),
        )
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get(path: str, receipt_id: str) -> Optional[dict[str, Any]]:
    conn = connect(path)
    try:
        cur = conn.execute("SELECT * FROM receipts WHERE id = ?", (receipt_id,))
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def list_rows(
    path: str,
    limit: int = 50,
    cluster: str | None = None,
    cell: str | None = None,
    slot: str | None = None,
) -> list[dict[str, Any]]:
    conn = connect(path)
    try:
        clauses = []
        args: list[Any] = []
        if cluster:
            clauses.append("cluster = ?")
            args.append(cluster)
        if cell:
            clauses.append("experiment_cell = ?")
            args.append(cell)
        if slot:
            clauses.append("slot = ?")
            args.append(slot)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        cur = conn.execute(
            f"SELECT * FROM receipts {where} ORDER BY created_at DESC LIMIT ?",
            [*args, limit],
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def count(path: str) -> int:
    conn = connect(path)
    try:
        cur = conn.execute("SELECT COUNT(*) FROM receipts")
        return int(cur.fetchone()[0])
    finally:
        conn.close()


def to_csv(rows: list[dict[str, Any]]) -> str:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=COLUMNS, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        clean = {}
        for col in COLUMNS:
            value = row.get(col)
            if isinstance(value, str) and value[:1] in {"=", "+", "-", "@"}:
                value = "'" + value
            clean[col] = value
        writer.writerow(clean)
    return buf.getvalue()


def labels_from_row(row: dict[str, Any]) -> dict[str, Any] | None:
    raw = row.get("labels_json")
    if not raw:
        return None
    return json.loads(raw)
