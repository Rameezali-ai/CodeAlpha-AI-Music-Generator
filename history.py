
import sqlite3

DB_NAME = "music_history.db"


def create_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS music_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            track_name TEXT NOT NULL,
            mood TEXT NOT NULL,
            style TEXT NOT NULL,
            duration INTEGER NOT NULL,
            bpm INTEGER NOT NULL,
            file_path TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def save_track(name, mood, style, duration, bpm, file_path):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO music_history
        (track_name, mood, style, duration, bpm, file_path)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (name, mood, style, duration, bpm, file_path))

    conn.commit()
    conn.close()


def get_history():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM music_history
        ORDER BY created_at DESC
    """)

    records = cursor.fetchall()
    conn.close()

    return records


def delete_track(track_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM music_history WHERE id = ?",
        (track_id,)
    )

    conn.commit()
    conn.close()
