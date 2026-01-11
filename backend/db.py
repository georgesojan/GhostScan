import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "ghostscan.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Devices table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT NOT NULL,
            ports TEXT, -- Comma-separated list of ports
            services TEXT, -- JSON-like string of service info
            location TEXT, -- Country/City
            last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
            source TEXT -- "scanner" or "api"
        )
    ''')
    
    # Intelligence Cache (e.g. Shodan results)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS intel_cache (
            ip TEXT PRIMARY KEY,
            data TEXT, -- Full JSON dump
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"GhostScan Database initialized at {DB_PATH}")

if __name__ == "__main__":
    init_db()
