"""
Stark Database — Persistent Memory for the Nexus.
Handles storage of 1,280+ modules, repo ingestion history, and adversarial maps.
"""

import sqlite3
import os
import json
from datetime import datetime

class StarkDatabase:
    def __init__(self, db_path="stark_nexus.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """Initializes the persistent schema for the Stark Intelligence Nexus."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Table for specialized modules
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS modules (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT,
                capabilities TEXT,
                last_active DATETIME,
                metadata TEXT
            )
        ''')
        
        # Table for repository ingestion history
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ingestion_history (
                repo_url TEXT PRIMARY KEY,
                repo_name TEXT,
                ingestion_date DATETIME,
                protocols_used TEXT,
                status TEXT
            )
        ''')
        
        # Table for adversarial threat maps
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS threat_map (
                threat_id TEXT PRIMARY KEY,
                target_model TEXT,
                attack_vector TEXT,
                mitigation_status TEXT,
                last_seen DATETIME
            )
        ''')
        
        conn.commit()
        conn.close()

    def register_module(self, module_id, name, category, capabilities, metadata=None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO modules (id, name, category, capabilities, last_active, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (module_id, name, category, json.dumps(capabilities), datetime.now(), json.dumps(metadata or {})))
        conn.commit()
        conn.close()

    def log_ingestion(self, repo_url, repo_name, protocols, status="COMPLETED"):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO ingestion_history (repo_url, repo_name, ingestion_date, protocols_used, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (repo_url, repo_name, datetime.now(), json.dumps(protocols), status))
        conn.commit()
        conn.close()

    def update_threat_map(self, threat_id, target_model, vector, status="MITIGATED"):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO threat_map (threat_id, target_model, attack_vector, mitigation_status, last_seen)
            VALUES (?, ?, ?, ?, ?)
        ''', (threat_id, target_model, vector, status, datetime.now()))
        conn.commit()
        conn.close()

# Global instance for the Nexus
stark_db = StarkDatabase()
