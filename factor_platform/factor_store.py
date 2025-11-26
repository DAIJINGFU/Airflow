from __future__ import annotations

import json
import sqlite3
import threading
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

from . import WORKSPACE_ROOT

DEFAULT_DB_PATH = WORKSPACE_ROOT / "metadata" / "factor_platform.db"
DEFAULT_FACTOR_CATALOG = WORKSPACE_ROOT / "configs" / "factors.json"


def _now_ts() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


def _normalize_list(value: Optional[Iterable[str]]) -> List[str]:
    if value is None:
        return []
    result: List[str] = []
    for item in value:
        if item is None:
            continue
        token = str(item).strip()
        if token:
            result.append(token)
    return result


@dataclass
class FactorJob:
    job_id: int
    factor_code: str
    factor_version: int
    expression: str
    start_date: str
    end_date: str
    freq: str
    instruments: List[str]
    owner: Optional[str]
    tags: List[str]
    callback_url: Optional[str]
    context: Dict[str, Any]


class FactorStore:
    """
    Persist factor metadata, versions, and evaluation jobs in SQLite.

    The store is purposely lightweight but provides the minimum guarantees the
    DAG requires:

    * unique factor codes with semantic metadata and version tracking
    * job queue with status transitions (PENDING -> RUNNING -> SUCCESS/FAILED)
    * result persistence + optional webhook callback
    """

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self.db_path = Path(db_path or DEFAULT_DB_PATH)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._init_schema()

    # ------------------------------------------------------------------ schema
    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS factors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    category TEXT,
                    owner TEXT,
                    tags TEXT,
                    description TEXT,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    latest_version INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS factor_versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    factor_id INTEGER NOT NULL,
                    version INTEGER NOT NULL,
                    expression TEXT NOT NULL,
                    note TEXT,
                    checksum TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(factor_id) REFERENCES factors(id),
                    UNIQUE(factor_id, version)
                );

                CREATE TABLE IF NOT EXISTS factor_jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    factor_code TEXT NOT NULL,
                    factor_version INTEGER NOT NULL,
                    expression TEXT NOT NULL,
                    start_date TEXT NOT NULL,
                    end_date TEXT NOT NULL,
                    freq TEXT NOT NULL,
                    instruments TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'PENDING',
                    priority INTEGER NOT NULL DEFAULT 5,
                    owner TEXT,
                    tags TEXT,
                    callback_url TEXT,
                    context_json TEXT,
                    metrics_json TEXT,
                    error_message TEXT,
                    result_path TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_factor_jobs_status
                    ON factor_jobs(status, priority, created_at);
                """
            )

    # --------------------------------------------------------------- factor ops
    def register_factor(
        self,
        *,
        code: str,
        expression: str,
        name: Optional[str] = None,
        category: Optional[str] = None,
        owner: Optional[str] = None,
        tags: Optional[Sequence[str]] = None,
        description: Optional[str] = None,
        note: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Register (or update) a factor.

        Returns the persisted factor metadata, including the new version.
        """
        code = code.strip()
        if not code:
            raise ValueError("factor code is required")
        expression = expression.strip()
        if not expression:
            raise ValueError("expression is required")
        ts = _now_ts()
        with self._connect() as conn:
            row = conn.execute("SELECT id, latest_version FROM factors WHERE code=?", (code,)).fetchone()
            tags_blob = json.dumps(_normalize_list(tags), ensure_ascii=False) if tags else None
            if row:
                factor_id = row["id"]
                next_version = int(row["latest_version"] or 0) + 1
                conn.execute(
                    """
                    UPDATE factors
                    SET name = COALESCE(?, name),
                        category = COALESCE(?, category),
                        owner = COALESCE(?, owner),
                        tags = COALESCE(?, tags),
                        description = COALESCE(?, description),
                        latest_version = ?,
                        updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        name or code,
                        category,
                        owner,
                        tags_blob,
                        description,
                        next_version,
                        ts,
                        factor_id,
                    ),
                )
            else:
                next_version = 1
                conn.execute(
                    """
                    INSERT INTO factors(code, name, category, owner, tags, description, latest_version, created_at, updated_at)
                    VALUES(?,?,?,?,?,?,?, ?, ?)
                    """,
                    (
                        code,
                        name or code,
                        category,
                        owner,
                        tags_blob,
                        description,
                        next_version,
                        ts,
                        ts,
                    ),
                )
                factor_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

            conn.execute(
                """
                INSERT INTO factor_versions(factor_id, version, expression, note, created_at)
                VALUES(?,?,?,?,?)
                """,
                (factor_id, next_version, expression, note, ts),
            )

        return {
            "code": code,
            "name": name or code,
            "category": category,
            "owner": owner,
            "tags": _normalize_list(tags),
            "version": next_version,
            "expression": expression,
            "description": description,
        }

    def list_factors(self) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT code, name, category, owner, tags, description, latest_version, created_at, updated_at
                FROM factors
                WHERE is_active = 1
                ORDER BY code
                """
            ).fetchall()
        result = []
        for row in rows:
            tags = json.loads(row["tags"]) if row["tags"] else []
            result.append(
                {
                    "code": row["code"],
                    "name": row["name"],
                    "category": row["category"],
                    "owner": row["owner"],
                    "tags": tags,
                    "description": row["description"],
                    "latest_version": row["latest_version"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                }
            )
        return result

    # ----------------------------------------------------------------- job ops
    def submit_job(
        self,
        *,
        factor_code: str,
        start_date: str,
        end_date: str,
        freq: str,
        instruments: Sequence[str],
        priority: int = 5,
        owner: Optional[str] = None,
        tags: Optional[Sequence[str]] = None,
        callback_url: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        version: Optional[int] = None,
    ) -> Dict[str, Any]:
        factor_code = factor_code.strip()
        if not factor_code:
            raise ValueError("factor_code is required")
        with self._connect() as conn:
            factor_row = conn.execute(
                "SELECT id, name, latest_version, owner, tags FROM factors WHERE code=? AND is_active=1",
                (factor_code,),
            ).fetchone()
            if not factor_row:
                raise ValueError(f"factor {factor_code} not found")
            version_to_use = version or factor_row["latest_version"]
            version_row = conn.execute(
                "SELECT expression FROM factor_versions WHERE factor_id=? AND version=?",
                (factor_row["id"], version_to_use),
            ).fetchone()
            if not version_row:
                raise ValueError(f"factor {factor_code} version {version_to_use} not found")
            ts = _now_ts()
            context_payload = dict(context or {})
            context_payload.setdefault("factor_name", factor_row["name"])
            payload = {
                "factor_code": factor_code,
                "factor_version": version_to_use,
                "expression": version_row["expression"],
                "start_date": start_date,
                "end_date": end_date,
                "freq": freq,
                "instruments": json.dumps(_normalize_list(instruments), ensure_ascii=False),
                "status": "PENDING",
                "priority": priority,
                "owner": owner or factor_row["owner"],
                "tags": json.dumps(_normalize_list(tags) or json.loads(factor_row["tags"] or "[]"), ensure_ascii=False)
                if (tags or factor_row["tags"])
                else None,
                "callback_url": callback_url,
                "context_json": json.dumps(context_payload, ensure_ascii=False),
                "created_at": ts,
                "updated_at": ts,
            }
            conn.execute(
                """
                INSERT INTO factor_jobs(
                    factor_code, factor_version, expression, start_date, end_date, freq,
                    instruments, status, priority, owner, tags, callback_url, context_json,
                    created_at, updated_at
                )
                VALUES(
                    :factor_code, :factor_version, :expression, :start_date, :end_date, :freq,
                    :instruments, :status, :priority, :owner, :tags, :callback_url, :context_json,
                    :created_at, :updated_at
                )
                """,
                payload,
            )
            job_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        return {
            "job_id": job_id,
            "factor_code": factor_code,
            "factor_version": version_to_use,
            "start_date": start_date,
            "end_date": end_date,
            "freq": freq,
        }

    def dequeue_jobs(self, limit: int = 8) -> List[Dict[str, Any]]:
        limit = max(limit, 1)
        with self._lock:
            with self._connect() as conn:
                conn.execute("BEGIN IMMEDIATE")
                rows = conn.execute(
                    """
                    SELECT *
                    FROM factor_jobs
                    WHERE status='PENDING'
                    ORDER BY priority ASC, created_at ASC
                    LIMIT ?
                    """,
                    (limit,),
                ).fetchall()
                if not rows:
                    conn.execute("COMMIT")
                    return []
                job_ids = [row["id"] for row in rows]
                ts = _now_ts()
                conn.executemany(
                    "UPDATE factor_jobs SET status='RUNNING', updated_at=? WHERE id=?",
                    [(ts, job_id) for job_id in job_ids],
                )
                conn.execute("COMMIT")
        jobs: List[Dict[str, Any]] = []
        for row in rows:
            context = json.loads(row["context_json"]) if row["context_json"] else {}
            jobs.append(
                {
                    "job_id": row["id"],
                    "factor_code": row["factor_code"],
                    "factor_version": row["factor_version"],
                    "expression": row["expression"],
                    "start_date": row["start_date"],
                    "end_date": row["end_date"],
                    "freq": row["freq"],
                    "instruments": json.loads(row["instruments"]) if row["instruments"] else [],
                    "owner": row["owner"],
                    "tags": json.loads(row["tags"]) if row["tags"] else [],
                    "callback_url": row["callback_url"],
                    "name": context.get("factor_name", row["factor_code"]),
                    "context": context,
                }
            )
        return jobs

    def mark_job_failed(self, job_id: int, error_message: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE factor_jobs
                SET status='FAILED', error_message=?, updated_at=?
                WHERE id=?
                """,
                (error_message[:1000], _now_ts(), job_id),
            )

    def mark_job_succeeded(
        self,
        job_id: int,
        metrics: Dict[str, Any],
        result_path: Optional[str] = None,
    ) -> None:
        payload = json.dumps(metrics, ensure_ascii=False)
        ts = _now_ts()
        with self._connect() as conn:
            row = conn.execute(
                "SELECT callback_url FROM factor_jobs WHERE id=?",
                (job_id,),
            ).fetchone()
            conn.execute(
                """
                UPDATE factor_jobs
                SET status='SUCCESS', metrics_json=?, result_path=?, error_message=NULL, updated_at=?
                WHERE id=?
                """,
                (payload, result_path, ts, job_id),
            )
        callback_url = row["callback_url"] if row else None
        if callback_url:
            self._fire_callback(callback_url, job_id, metrics, result_path)

    def attach_result_path(self, job_ids: Sequence[int], result_path: str) -> None:
        if not job_ids:
            return
        ts = _now_ts()
        with self._connect() as conn:
            conn.executemany(
                "UPDATE factor_jobs SET result_path=?, updated_at=? WHERE id=?",
                [(result_path, ts, job_id) for job_id in job_ids],
            )

    def list_jobs(self, status: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        query = "SELECT * FROM factor_jobs"
        params: List[Any] = []
        if status:
            query += " WHERE status=?"
            params.append(status)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        result = []
        for row in rows:
            result.append(
                {
                    "job_id": row["id"],
                    "factor_code": row["factor_code"],
                    "factor_version": row["factor_version"],
                    "status": row["status"],
                    "start_date": row["start_date"],
                    "end_date": row["end_date"],
                    "freq": row["freq"],
                    "priority": row["priority"],
                    "owner": row["owner"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                    "error_message": row["error_message"],
                    "metrics_json": row["metrics_json"],  # 添加metrics_json字段
                }
            )
        return result

    def ensure_seed_factors(self, catalog_path: Optional[Path] = None) -> None:
        """
        When the registry is empty, bootstrap it from configs/factors.json.
        """
        catalog = Path(catalog_path or DEFAULT_FACTOR_CATALOG)
        if not catalog.exists():
            return
        factors = json.loads(catalog.read_text(encoding="utf-8"))
        with self._connect() as conn:
            existing = conn.execute("SELECT COUNT(*) AS cnt FROM factors").fetchone()["cnt"]
        if existing:
            return
        for item in factors:
            self.register_factor(
                code=item.get("code"),
                expression=item.get("expression"),
                name=item.get("name"),
                category=item.get("category"),
            )

    # ------------------------------------------------------------ helper utils
    def _fire_callback(
        self,
        url: str,
        job_id: int,
        metrics: Dict[str, Any],
        result_path: Optional[str],
    ) -> None:
        """
        Fire-and-forget HTTP callback; errors are swallowed to avoid breaking DAG runs.
        """
        payload = json.dumps(
            {
                "job_id": job_id,
                "status": "SUCCESS",
                "metrics": metrics,
                "result_path": result_path,
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            urllib.request.urlopen(req, timeout=3)
        except Exception:
            # Deliberately ignore errors; callback is best-effort.
            pass
