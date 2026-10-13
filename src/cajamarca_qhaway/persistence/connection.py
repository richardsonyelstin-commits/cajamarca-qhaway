"""Gestion de conexiones a base de datos (PostgreSQL/Supabase y SQLite local/memoria) (Pilar 2)."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Any, Iterator

from cajamarca_qhaway.persistence.config import DatabaseConfig


class DatabaseManager:
    """Administrador desacoplado de conexiones relacionales."""

    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self.config = config or DatabaseConfig()
        self._is_postgres = False
        self._dsn: str | None = None
        if self.config.database_url:
            self._dsn = self.config.database_url.get_secret_value()
            if self._dsn.startswith("postgres://") or self._dsn.startswith("postgresql://"):
                self._is_postgres = True

        self._sqlite_conn: sqlite3.Connection | None = None

    @property
    def is_postgres(self) -> bool:
        return self._is_postgres

    def get_sqlite_memory_connection(self) -> sqlite3.Connection:
        """Obtiene o inicializa una conexion SQLite en memoria para tests y fallback local."""
        if self._sqlite_conn is None:
            self._sqlite_conn = sqlite3.connect(":memory:", check_same_thread=False)
            self._sqlite_conn.row_factory = sqlite3.Row
            self._init_sqlite_schema(self._sqlite_conn)
        return self._sqlite_conn

    def _init_sqlite_schema(self, conn: sqlite3.Connection) -> None:
        """Inicializa las 6 tablas operativas en SQLite respetando los esquemas canónicos."""
        schema = """
        CREATE TABLE IF NOT EXISTS contracting_entities (
            entity_id TEXT PRIMARY KEY,
            official_name TEXT NOT NULL,
            entity_level TEXT NOT NULL,
            province TEXT,
            ruc TEXT NOT NULL UNIQUE,
            consucode_id TEXT,
            department TEXT NOT NULL DEFAULT 'CAJAMARCA',
            verified_at TEXT NOT NULL,
            active INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS procurement_records (
            procurement_id TEXT PRIMARY KEY,
            ocid TEXT NOT NULL,
            entity_id TEXT NOT NULL REFERENCES contracting_entities(entity_id),
            title TEXT NOT NULL,
            procurement_method TEXT,
            awarded_amount REAL,
            executed_amount REAL,
            number_of_bidders INTEGER,
            supplier_name TEXT,
            supplier_ruc TEXT,
            raw_payload TEXT NOT NULL DEFAULT '{}',
            source TEXT NOT NULL DEFAULT 'seace-ocds',
            retrieved_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS budget_execution_records (
            execution_record_id TEXT PRIMARY KEY,
            entity_id TEXT NOT NULL REFERENCES contracting_entities(entity_id),
            fiscal_year INTEGER NOT NULL,
            budgeted_amount REAL NOT NULL DEFAULT 0.0,
            executed_amount REAL NOT NULL DEFAULT 0.0,
            budget_category TEXT,
            raw_payload TEXT NOT NULL DEFAULT '{}',
            source TEXT NOT NULL DEFAULT 'mef-datastore',
            retrieved_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS red_flags (
            red_flag_id TEXT PRIMARY KEY,
            indicator_code TEXT NOT NULL,
            formula_description TEXT NOT NULL,
            threshold TEXT NOT NULL,
            observed_value TEXT NOT NULL,
            procurement_ids TEXT NOT NULL DEFAULT '[]',
            execution_record_ids TEXT NOT NULL DEFAULT '[]',
            evidence_source TEXT NOT NULL,
            evidence_retrieved_at TEXT NOT NULL,
            generated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS alerts (
            alert_id TEXT PRIMARY KEY,
            red_flag_ids TEXT NOT NULL,
            entity_id TEXT NOT NULL REFERENCES contracting_entities(entity_id),
            status TEXT NOT NULL CHECK (status IN ('published', 'discarded')),
            reviewed_by TEXT NOT NULL,
            reviewed_at TEXT NOT NULL,
            review_notes TEXT,
            disclaimer TEXT NOT NULL,
            published_at TEXT
        );

        CREATE TABLE IF NOT EXISTS citizen_reports (
            report_id TEXT PRIMARY KEY,
            submitted_at TEXT NOT NULL,
            channel TEXT NOT NULL,
            raw_text TEXT NOT NULL,
            related_entity_id TEXT REFERENCES contracting_entities(entity_id),
            moderation_status TEXT NOT NULL,
            moderated_by TEXT,
            moderated_at TEXT,
            legal_disclaimer_shown INTEGER NOT NULL CHECK (legal_disclaimer_shown = 1)
        );
        """
        conn.executescript(schema)
        conn.commit()

    @contextmanager
    def connection(self) -> Iterator[Any]:
        """Provee un contexto transaccional para la base de datos configurada."""
        if self._is_postgres and self._dsn:
            try:
                import psycopg
                from psycopg.rows import dict_row

                with psycopg.connect(self._dsn, row_factory=dict_row) as conn:
                    yield conn
            except Exception:
                # Si falla la conexion remota, fallback controlado
                conn = self.get_sqlite_memory_connection()
                yield conn
        else:
            conn = self.get_sqlite_memory_connection()
            yield conn
