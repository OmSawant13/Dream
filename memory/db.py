"""
Phase E: Database Manager
SQLite + FTS5 backend for persistent memory.
All schema, migrations, and raw query helpers live here.
"""

import sqlite3
import logging
from pathlib import Path

logger = logging.getLogger("papper-db")

# Schema version — bump this when tables change
SCHEMA_VERSION = 3

# Path to the database file, sibling to this module's parent (project root)
DEFAULT_DB_PATH = Path(__file__).parent.parent / "papper.db"


class DatabaseManager:
    """Low-level SQLite interface. Owns the connection and schema."""

    def __init__(self, db_path=None):
        self.db_path = str(db_path or DEFAULT_DB_PATH)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=30)
        self.conn.row_factory = sqlite3.Row          # dict-like rows
        self.conn.execute("PRAGMA journal_mode=WAL")  # concurrent reads
        self.conn.execute("PRAGMA foreign_keys=ON")
        self._init_schema()
        logger.info(f"Database ready at {self.db_path}")

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------
    def _init_schema(self):
        """Create tables if they don't exist."""
        cur = self.conn.cursor()

        cur.executescript("""
            CREATE TABLE IF NOT EXISTS workflows (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                task_name   TEXT    NOT NULL,
                created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
                completed_at TEXT,
                success     INTEGER DEFAULT 0,
                total_steps INTEGER DEFAULT 0,
                notes       TEXT
            );

            CREATE TABLE IF NOT EXISTS actions (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                workflow_id     INTEGER NOT NULL,
                step            INTEGER NOT NULL,
                action_sequence INTEGER NOT NULL DEFAULT 1,
                action_type     TEXT    NOT NULL,
                action_params   TEXT,            -- JSON blob
                thought         TEXT,            -- LLM reasoning (from AutoGPT research)
                result_status   TEXT,            -- success / error
                result_msg      TEXT,
                state_changed   INTEGER DEFAULT 0,
                url             TEXT,
                timestamp       TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (workflow_id) REFERENCES workflows(id),
                UNIQUE(workflow_id, step, action_sequence)
            );

            CREATE TABLE IF NOT EXISTS patterns (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_type    TEXT    NOT NULL,   -- search, login, navigation …
                detection_rule  TEXT    NOT NULL,   -- JSON: sequence of action_types
                response_action TEXT    NOT NULL,   -- JSON: recommended next actions
                success_count   INTEGER DEFAULT 0,
                fail_count      INTEGER DEFAULT 0,
                last_used_at    TEXT
            );

            CREATE TABLE IF NOT EXISTS blockers (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                blocker_type      TEXT NOT NULL,    -- modal / paywall / captcha / rate_limit
                url_pattern       TEXT,             -- regex or domain
                detection_rule    TEXT,             -- JSON: how we detected it
                bypass_method     TEXT,             -- JSON: how we bypassed it
                success_count     INTEGER DEFAULT 0,
                fail_count        INTEGER DEFAULT 0,
                last_seen_at      TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS state_hashes (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                workflow_id  INTEGER NOT NULL,
                step         INTEGER NOT NULL,
                visual_hash  TEXT,
                text_hash    TEXT,
                url          TEXT,
                timestamp    TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (workflow_id) REFERENCES workflows(id),
                UNIQUE(workflow_id, step)
            );

            -- Schema version tracker
            CREATE TABLE IF NOT EXISTS meta (
                key   TEXT PRIMARY KEY,
                value TEXT
            );
        """)

        # FTS5 virtual table for fast keyword search on task names
        # Wrapped in try/except because CREATE VIRTUAL TABLE IF NOT EXISTS
        # is not supported by all SQLite builds.
        try:
            cur.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS workflows_fts
                USING fts5(task_name, content='workflows', content_rowid='id');
            """)
        except sqlite3.OperationalError:
            logger.warning("FTS5 not available — keyword search will fall back to LIKE.")

        # Indexes for common queries
        cur.executescript("""
            CREATE INDEX IF NOT EXISTS idx_actions_workflow
                ON actions(workflow_id);
            CREATE INDEX IF NOT EXISTS idx_actions_type
                ON actions(action_type);
            CREATE INDEX IF NOT EXISTS idx_state_workflow
                ON state_hashes(workflow_id);
            CREATE INDEX IF NOT EXISTS idx_blockers_type
                ON blockers(blocker_type);
        """)

        # Record schema version
        cur.execute(
            "INSERT OR REPLACE INTO meta(key, value) VALUES (?, ?)",
            ("schema_version", str(SCHEMA_VERSION)),
        )
        self.conn.commit()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def execute(self, sql, params=()):
        """Execute a single statement and return the cursor."""
        cur = self.conn.cursor()
        cur.execute(sql, params)
        self.conn.commit()
        return cur

    def executemany(self, sql, seq_of_params):
        cur = self.conn.cursor()
        cur.executemany(sql, seq_of_params)
        self.conn.commit()
        return cur

    def fetchone(self, sql, params=()):
        return self.conn.execute(sql, params).fetchone()

    def fetchall(self, sql, params=()):
        return self.conn.execute(sql, params).fetchall()

    def close(self):
        self.conn.close()
        logger.info("Database connection closed.")
