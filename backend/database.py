"""SQLite database module for persistent Brand Voice Memory and user preferences."""
import os
import sqlite3
import json
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "socialspark.db"


def get_connection():
    """Get a connection to the SQLite database."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database tables if they do not exist."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS brand_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_email TEXT UNIQUE,
                brand_name TEXT NOT NULL,
                brand_description TEXT,
                industry TEXT,
                preferred_tone TEXT,
                previous_posts TEXT,
                sample_content TEXT,
                personality TEXT,
                vocabulary TEXT,
                sentence_structure TEXT,
                communication_tone TEXT,
                preferred_expressions TEXT,
                voice_summary TEXT,
                updated_at TEXT
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS emotion_replies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_email TEXT,
                platform TEXT,
                commenter TEXT,
                comment TEXT,
                emotion TEXT,
                sentiment TEXT,
                intent TEXT,
                context TEXT,
                requirement TEXT,
                friendly_response TEXT,
                professional_response TEXT,
                empathetic_response TEXT,
                brand_name TEXT,
                created_at TEXT
            );
        """)
        conn.commit()


# Auto-initialize on module load
init_db()


def save_brand_profile(data: dict, user_email: str = "default") -> bool:
    """Save or update the brand voice profile in SQLite."""
    init_db()
    user_email = (user_email or "default").strip().lower()
    now_str = datetime.now(timezone.utc).isoformat()
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO brand_profiles (
                user_email, brand_name, brand_description, industry,
                preferred_tone, previous_posts, sample_content,
                personality, vocabulary, sentence_structure,
                communication_tone, preferred_expressions, voice_summary, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_email) DO UPDATE SET
                brand_name = excluded.brand_name,
                brand_description = excluded.brand_description,
                industry = excluded.industry,
                preferred_tone = excluded.preferred_tone,
                previous_posts = excluded.previous_posts,
                sample_content = excluded.sample_content,
                personality = excluded.personality,
                vocabulary = excluded.vocabulary,
                sentence_structure = excluded.sentence_structure,
                communication_tone = excluded.communication_tone,
                preferred_expressions = excluded.preferred_expressions,
                voice_summary = excluded.voice_summary,
                updated_at = excluded.updated_at
        """, (
            user_email,
            data.get("brand_name", "").strip(),
            data.get("brand_description", "").strip(),
            data.get("industry", "").strip(),
            data.get("preferred_tone", "").strip(),
            data.get("previous_posts", "").strip(),
            data.get("sample_content", "").strip(),
            data.get("personality", "").strip(),
            data.get("vocabulary", "").strip(),
            data.get("sentence_structure", "").strip(),
            data.get("communication_tone", "").strip(),
            data.get("preferred_expressions", "").strip(),
            data.get("voice_summary", "").strip(),
            now_str,
        ))
        conn.commit()
    return True


def get_brand_profile(user_email: str = "default") -> dict | None:
    """Retrieve the brand voice profile from SQLite.
    
    If no profile is found for the given user_email, checks for a 'default' profile.
    """
    init_db()
    user_email = (user_email or "default").strip().lower()
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM brand_profiles WHERE user_email = ?", (user_email,))
        row = cursor.fetchone()
        
        # Fallback to default if not found
        if not row and user_email != "default":
            cursor.execute("SELECT * FROM brand_profiles WHERE user_email = 'default'")
            row = cursor.fetchone()
            
        if row:
            return dict(row)
    return None


def reset_brand_profile(user_email: str = "default") -> bool:
    """Reset / delete the brand voice profile from SQLite."""
    init_db()
    user_email = (user_email or "default").strip().lower()
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM brand_profiles WHERE user_email = ?", (user_email,))
        if user_email != "default":
            cursor.execute("DELETE FROM brand_profiles WHERE user_email = 'default'")
        conn.commit()
    return True


def save_emotion_reply(data: dict, user_email: str = "default") -> int:
    """Save an emotion-aware reply generation record to SQLite."""
    init_db()
    user_email = (user_email or "default").strip().lower()
    now_str = datetime.now(timezone.utc).isoformat()

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO emotion_replies (
                user_email, platform, commenter, comment,
                emotion, sentiment, intent, context, requirement,
                friendly_response, professional_response, empathetic_response,
                brand_name, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_email,
            data.get("platform", "Instagram"),
            data.get("commenter", ""),
            data.get("comment", ""),
            data.get("emotion", "Neutral"),
            data.get("sentiment", "Neutral"),
            data.get("intent", ""),
            data.get("context", ""),
            data.get("requirement", ""),
            data.get("friendly_response", ""),
            data.get("professional_response", ""),
            data.get("empathetic_response", ""),
            data.get("brand_name", ""),
            now_str,
        ))
        conn.commit()
        return cursor.lastrowid


def get_saved_emotion_replies(user_email: str = "default", limit: int = 10) -> list[dict]:
    """Retrieve recently saved emotion-aware replies from SQLite."""
    init_db()
    user_email = (user_email or "default").strip().lower()

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM emotion_replies
            WHERE user_email = ? OR user_email = 'default'
            ORDER BY id DESC
            LIMIT ?
        """, (user_email, limit))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

