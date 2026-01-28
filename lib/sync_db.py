import sqlite3

def init_db(db_path: str = "sync.db"):
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS canvas_task_map (
            canvas_assignment_id INTEGER PRIMARY KEY,
            course_id INTEGER NOT NULL,
            google_task_id TEXT NOT NULL,
            canvas_updated_at TEXT,
            canvas_due_at TEXT,
            last_synced_at TEXT
        )
    """)
    conn.commit()
    return conn

def get_mapping(conn, canvas_assignment_id: int):
    cur = conn.execute(
        "SELECT google_task_id, canvas_updated_at, canvas_due_at FROM canvas_task_map WHERE canvas_assignment_id=?",
        (canvas_assignment_id,)
    )
    return cur.fetchone()

def upsert_mapping(conn, canvas_assignment_id: int, course_id: int, google_task_id: str, canvas_updated_at: str, canvas_due_at: str = None, last_synced_at: str = None):
    from datetime import datetime
    if last_synced_at is None:
        last_synced_at = datetime.utcnow().isoformat()
    
    conn.execute("""
        INSERT INTO canvas_task_map (canvas_assignment_id, course_id, google_task_id, canvas_updated_at, canvas_due_at, last_synced_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(canvas_assignment_id) DO UPDATE SET
          google_task_id=excluded.google_task_id,
          canvas_updated_at=excluded.canvas_updated_at,
          canvas_due_at=excluded.canvas_due_at,
          last_synced_at=excluded.last_synced_at
    """, (canvas_assignment_id, course_id, google_task_id, canvas_updated_at, canvas_due_at, last_synced_at))
    conn.commit()