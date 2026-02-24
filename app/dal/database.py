import duckdb
import os
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class DuckDBManager:
    def __init__(self, db_path: str = "data/app.duckdb"):
        self.db_path = db_path
        # Initialize or migrate schema
        self._init_schema()

    def _init_schema(self):
        """Initializes the database schema."""
        try:
            with self.get_connection() as con:
                con.execute("""
                    CREATE TABLE IF NOT EXISTS interaction_logs (
                        id INTEGER PRIMARY KEY,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        prompt TEXT,
                        response TEXT,
                        latency_ms INTEGER
                    );
                    CREATE SEQUENCE IF NOT EXISTS seq_interaction_id START 1;
                    
                    CREATE TABLE IF NOT EXISTS photos (
                        id UUID PRIMARY KEY,
                        session_id VARCHAR,
                        filename VARCHAR,
                        content BLOB,
                        creation_date DATE,
                        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        md5_hash VARCHAR,
                        analysis_results VARCHAR,
                        analysis_date VARCHAR
                    );
                    -- Migration for existing tables
                    ALTER TABLE photos ADD COLUMN IF NOT EXISTS md5_hash VARCHAR;
                    ALTER TABLE photos ADD COLUMN IF NOT EXISTS analysis_results VARCHAR;
                    ALTER TABLE photos ADD COLUMN IF NOT EXISTS analysis_date VARCHAR;
                """)
                logger.info("Database schema initialized.")
        except Exception as e:
            logger.error(f"Failed to init schema: {e}")

    @contextmanager
    def get_connection(self):
        """Yields a DuckDB connection."""
        # DuckDB handles concurrency well, but creating a connection per request is safe for persistence
        con = duckdb.connect(self.db_path)
        try:
            yield con
        finally:
            con.close()

    def log_interaction(self, prompt: str, response: str, latency_ms: int):
        try:
            with self.get_connection() as con:
                con.execute("""
                    INSERT INTO interaction_logs (id, prompt, response, latency_ms)
                    VALUES (nextval('seq_interaction_id'), ?, ?, ?)
                """, [prompt, response, latency_ms])
        except Exception as e:
            logger.error(f"Failed to log interaction: {e}")

db_manager = DuckDBManager(db_path=os.getenv("DUCKDB_PATH", "data/app.duckdb"))
