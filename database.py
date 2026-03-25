import sqlite3

DATABASE = "network.db"


def get_db():
    """Open a new database connection."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # So we can access columns by name
    conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key support
    return conn


def init_db():
    """Create tables if they don't exist."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS nodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS edges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            destination TEXT NOT NULL,
            latency REAL NOT NULL,
            FOREIGN KEY (source) REFERENCES nodes(name),
            FOREIGN KEY (destination) REFERENCES nodes(name),
            UNIQUE(source, destination)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS route_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            destination TEXT NOT NULL,
            total_latency REAL,
            path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
