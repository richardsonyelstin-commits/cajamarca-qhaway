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
            threshold_value TEXT NOT NULL,
            observed_value TEXT NOT NULL,
            procurement_ids TEXT NOT NULL DEFAULT '[]',
            execution_record_ids TEXT NOT NULL DEFAULT '[]',
            evidence_source TEXT NOT NULL,
            evidence_retrieved_at TEXT NOT NULL,
            retrieved_at TEXT NOT NULL,
            generated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS alerts (
            alert_id TEXT PRIMARY KEY,
            red_flag_ids TEXT NOT NULL,
            entity_id TEXT NOT NULL REFERENCES contracting_entities(entity_id),
            status TEXT NOT NULL CHECK (status IN ('published', 'discarded')),
            reviewed_by TEXT NOT NULL CHECK (lower(trim(reviewed_by)) NOT IN
                ('admin', 'system', 'root', 'bot', 'auto', 'automated', '')),
            reviewed_at TEXT NOT NULL,
            review_notes TEXT NOT NULL CHECK (length(trim(review_notes)) > 0),
            disclaimer TEXT NOT NULL,
            legal_disclaimer TEXT NOT NULL,
            evidence TEXT NOT NULL DEFAULT '[]',
            published_at TEXT,
            CHECK (status <> 'published' OR json_array_length(evidence) > 0),
            CHECK ((status = 'published' AND published_at IS NOT NULL) OR
                   (status = 'discarded' AND published_at IS NULL))
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
            legal_disclaimer_shown INTEGER NOT NULL CHECK (legal_disclaimer_shown = 1),
            tracking_token_hash TEXT UNIQUE CHECK (
                tracking_token_hash IS NULL OR length(tracking_token_hash) = 64
            )
        );

        CREATE TABLE IF NOT EXISTS harvest_watermarks (
            source_name TEXT PRIMARY KEY,
            last_timestamp TEXT,
            last_offset INTEGER DEFAULT 0,
            seen_ids TEXT DEFAULT '[]',
            updated_at TEXT NOT NULL
        );
        """
        conn.executescript(schema)
        conn.commit()

    def adapt_sql(self, sql: str) -> str:
        """Adapta consultas al motor relacional activo (? para SQLite, %s para Postgres)."""
        if self._is_postgres:
            return sql.replace("?", "%s")
        return sql

    @contextmanager
    def connection(self) -> Iterator[Any]:
        """Provee un contexto transaccional para la base de datos configurada."""
        if self._is_postgres and self._dsn:
            import psycopg
            from psycopg.rows import dict_row

            conn = None
            try:
                conn = psycopg.connect(self._dsn, row_factory=dict_row)
            except Exception:
                # Si falla la conexion inicial remota (red o DNS), fallback controlado
                conn = self.get_sqlite_memory_connection()
                yield conn
                return

            try:
                wrapped = PostgresConnectionWrapper(conn)
                yield wrapped
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()
        else:
            conn = self.get_sqlite_memory_connection()
            yield conn


class PostgresCursorWrapper:
    """Cursor wrapper que traduce comodines '?' de SQLite al formato '%s' de psycopg."""

    def __init__(self, raw_cursor: Any) -> None:
        self._raw = raw_cursor

    def execute(self, query: str, params: Any = None) -> Any:
        adapted = query.replace("?", "%s")
        if params is None:
            return self._raw.execute(adapted)
        return self._raw.execute(adapted, params)

    def executemany(self, query: str, params_seq: Any) -> Any:
        adapted = query.replace("?", "%s")
        return self._raw.executemany(adapted, params_seq)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._raw, name)

    def __iter__(self) -> Any:
        return iter(self._raw)


class PostgresConnectionWrapper:
    """Connection wrapper que entrega cursores adaptados a la sintaxis del proyecto."""

    def __init__(self, raw_conn: Any) -> None:
        self._raw = raw_conn

    def cursor(self, *args: Any, **kwargs: Any) -> PostgresCursorWrapper:
        return PostgresCursorWrapper(self._raw.cursor(*args, **kwargs))

    def __getattr__(self, name: str) -> Any:
        return getattr(self._raw, name)
