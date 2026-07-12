# services/save_mood.py
import sqlite3
from datetime import datetime

def save_mood(student_id, student_name, class_name, emotion, confidence):
    """Menyimpan data log mood ke dalam tabel terpadu student_mood_logs"""
    conn = sqlite3.connect("database/database.db")
    cursor = conn.cursor()
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.execute("""
        INSERT INTO student_mood_logs
        (student_id, student_name, class_name, emotion, confidence, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (student_id, student_name, class_name, emotion, confidence, timestamp))
    
    conn.commit()
    conn.close()