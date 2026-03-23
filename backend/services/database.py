import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "file_contents.db")

def init_db():
    """Create the database and table if they don't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS file_contents (
            filename TEXT PRIMARY KEY,
            content  TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def save_content(filename: str, content: str):
    """Save or update extracted content for a file."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO file_contents (filename, content)
        VALUES (?, ?)
        ON CONFLICT(filename) DO UPDATE SET content=excluded.content, updated_at=CURRENT_TIMESTAMP
    """, (filename, content))
    conn.commit()
    conn.close()

def get_all_contents() -> dict:
    """Return a dict of { filename: content } for all stored files."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT filename, content FROM file_contents")
    rows = cursor.fetchall()
    conn.close()
    return {row[0]: row[1] for row in rows}

def delete_content(filename: str):
    """Remove content entry when a file is deleted."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM file_contents WHERE filename = ?", (filename,))
    conn.commit()
    conn.close()

# Auto-init on import
init_db()
