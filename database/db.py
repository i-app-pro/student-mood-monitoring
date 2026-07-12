# database/db.py (VERSI TURSO — dual mode: lokal SQLite / cloud Turso, dengan cache & throttled sync)
import os
import time
import random
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta

# ==========================================================
# DETEKSI MODE: TURSO (cloud) vs SQLITE LOKAL (dev)
# ==========================================================
def _get_turso_credentials():
    """Ambil kredensial Turso dari st.secrets (lokal: .streamlit/secrets.toml,
    cloud: Settings > Secrets di Streamlit Community Cloud)."""
    try:
        url = st.secrets.get("TURSO_DATABASE_URL")
        token = st.secrets.get("TURSO_AUTH_TOKEN")
        if url and token:
            return url, token
    except Exception:
        pass
    return None, None


TURSO_URL, TURSO_TOKEN = _get_turso_credentials()
USE_TURSO = bool(TURSO_URL and TURSO_TOKEN)

if USE_TURSO:
    import libsql as dbdriver
else:
    import sqlite3 as dbdriver

# Sync ke cloud paling cepat tiap sekian detik (bukan tiap query)
_SYNC_INTERVAL_SECONDS = 5
_last_sync_at = {"t": 0.0}


# ==========================================================
# KONEKSI (di-cache: hanya dibuat SEKALI per sesi app)
# ==========================================================
@st.cache_resource(show_spinner=False)
def _get_turso_connection():
    conn = dbdriver.connect(
        "local-replica.db",
        sync_url=TURSO_URL,
        auth_token=TURSO_TOKEN,
    )
    conn.sync()
    _last_sync_at["t"] = time.time()
    return conn


def get_db_connection():
    if USE_TURSO:
        conn = _get_turso_connection()
        # Sync ulang hanya kalau sudah lewat interval, biar hemat network round-trip
        now = time.time()
        if now - _last_sync_at["t"] > _SYNC_INTERVAL_SECONDS:
            conn.sync()
            _last_sync_at["t"] = now
        return conn
    else:
        if not os.path.exists('database'):
            os.makedirs('database')
        return dbdriver.connect('database/database.db')


def _release_connection(conn):
    """Tutup koneksi HANYA kalau mode lokal SQLite.
    Koneksi Turso itu shared/cached, jangan ditutup di sini."""
    if not USE_TURSO:
        conn.close()


def _commit_and_sync(conn, force_sync=True):
    """Commit lokal, lalu push ke Turso cloud (dipaksa sync setelah nulis data,
    supaya device lain langsung lihat data terbaru)."""
    conn.commit()
    if USE_TURSO and force_sync:
        conn.sync()
        _last_sync_at["t"] = time.time()


# ==========================================================
# HELPER: query -> DataFrame TANPA pandas.read_sql_query
# (read_sql_query kadang bermasalah dengan koneksi non-sqlite3 murni,
#  jadi kita bangun manual dari cursor supaya kompatibel di kedua mode)
# ==========================================================
def _query_to_df(conn, query, params=()):
    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description] if cursor.description else []
    return pd.DataFrame(rows, columns=columns)


# ==========================================================
# INIT DB
# ==========================================================
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS student_mood_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            student_name TEXT NOT NULL,
            class_name TEXT NOT NULL,
            emotion TEXT NOT NULL,
            confidence REAL NOT NULL,
            timestamp DATETIME NOT NULL
        )
    ''')
    _commit_and_sync(conn)

    cursor.execute("SELECT COUNT(*) FROM student_mood_logs")
    count = cursor.fetchone()[0]

    if count == 0:
        students = [
            ("#ST-2024-001", "John Doe", "CS-401A"),
            ("#ST-2024-023", "Sarah Miller", "ENG-102B"),
            ("#ST-2024-045", "Alex Kim", "MATH-201"),
            ("#ST-2024-012", "Emma Lawson", "CS-401A"),
            ("#ST-2024-009", "Robert Chen", "CS-401A"),
            ("#ST-2024-015", "Alice Thompson", "ENG-102B"),
            ("#ST-2024-032", "Michael Watts", "MATH-201"),
            ("#ST-2024-055", "Sophia Davis", "PHYS-301"),
            ("#ST-2024-077", "David Wilson", "PHYS-301"),
            ("#ST-2024-088", "Lily Evans", "CHEM-101"),
            ("#ST-2024-099", "James Potter", "CHEM-101"),
            ("#ST-2024-110", "Tom Riddle", "CS-401A")
        ]

        emotions = ["Happy", "Neutral", "Sad", "Angry", "Surprise"]
        emotion_weights = [0.47, 0.33, 0.12, 0.05, 0.03]

        now = datetime.now()

        for _ in range(180):
            student_id, name, class_name = random.choice(students)
            emotion = random.choices(emotions, weights=emotion_weights, k=1)[0]

            if emotion == "Happy":
                confidence = round(random.uniform(85.0, 99.5), 1)
            elif emotion == "Neutral":
                confidence = round(random.uniform(75.0, 95.0), 1)
            else:
                confidence = round(random.uniform(65.0, 90.0), 1)

            days_ago = random.randint(0, 6)
            hour = random.randint(8, 17)
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            log_time = now - timedelta(days=days_ago)
            log_time = log_time.replace(hour=hour, minute=minute, second=second)

            cursor.execute('''
                INSERT INTO student_mood_logs (student_id, student_name, class_name, emotion, confidence, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (student_id, name, class_name, emotion, confidence, log_time.strftime('%Y-%m-%d %H:%M:%S')))

        _commit_and_sync(conn)

    _release_connection(conn)


# ==========================================================
# QUERY: mood stats
# ==========================================================
def get_mood_stats_all(time_filter="Minggu Ini (Weekly View)"):
    conn = get_db_connection()

    query = "SELECT * FROM student_mood_logs WHERE 1=1"

    if time_filter == "Hari Ini (Today)":
        query += " AND date(timestamp) = date('now', 'localtime')"
    elif time_filter == "Minggu Ini (Weekly View)":
        query += " AND date(timestamp) >= date('now', 'weekday 1', '-7 days')"

    query += " ORDER BY timestamp DESC"

    df = _query_to_df(conn, query)
    _release_connection(conn)
    return df


# ==========================================================
# QUERY: daily trends
# ==========================================================
def get_daily_trends(time_filter="Minggu Ini (Weekly View)"):
    conn = get_db_connection()

    query = """
        SELECT strftime('%w', timestamp) as day_num,
               emotion,
               COUNT(*) as count
        FROM student_mood_logs
        WHERE 1=1
    """

    if time_filter == "Hari Ini (Today)":
        query += " AND date(timestamp) = date('now', 'localtime')"
    elif time_filter == "Minggu Ini (Weekly View)":
        query += " AND date(timestamp) >= date('now', 'weekday 1', '-7 days')"

    query += " GROUP BY day_num, emotion"

    df = _query_to_df(conn, query)
    _release_connection(conn)

    day_map = {'0': 'Sun', '1': 'Mon', '2': 'Tue', '3': 'Wed', '4': 'Thu', '5': 'Fri', '6': 'Sat'}
    if not df.empty:
        df['day_name'] = df['day_num'].map(day_map)
    else:
        df['day_name'] = pd.Series(dtype='object')

    return df


# ==========================================================
# QUERY: dashboard metrics
# ==========================================================
def get_dashboard_metrics():
    conn = get_db_connection()
    cursor = conn.cursor()

    today_str = datetime.now().strftime('%Y-%m-%d')
    cursor.execute("SELECT COUNT(*) FROM student_mood_logs WHERE date(timestamp) = ?", (today_str,))
    scans_today = cursor.fetchone()[0]

    if scans_today == 0:
        cursor.execute("SELECT date(timestamp) FROM student_mood_logs ORDER BY timestamp DESC LIMIT 1")
        res = cursor.fetchone()
        if res:
            today_str = res[0]
            cursor.execute("SELECT COUNT(*) FROM student_mood_logs WHERE date(timestamp) = ?", (today_str,))
            scans_today = cursor.fetchone()[0]

    cursor.execute("""
        SELECT emotion, COUNT(*)
        FROM student_mood_logs
        WHERE date(timestamp) = ?
        GROUP BY emotion
    """, (today_str,))
    counts = dict(cursor.fetchall())

    cursor.execute("SELECT COUNT(DISTINCT student_id) FROM student_mood_logs")
    unique_students_in_db = cursor.fetchone()[0]
    total_students = max(120, unique_students_in_db)

    _release_connection(conn)

    return {
        "scans_today": scans_today,
        "happy_count": counts.get("Happy", 0),
        "neutral_count": counts.get("Neutral", 0),
        "sad_count": counts.get("Sad", 0) + counts.get("Angry", 0),
        "total_students": total_students,
        "date_str": today_str
    }