"""
Database module for chat history management.
Uses SQLite for persistent storage of conversations.
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

DB_PATH = Path("data/chat_history.db")


class ChatDatabase:
    """Manages chat history in SQLite database."""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or str(DB_PATH)
        self._ensure_directory()
        self._init_db()
        self._migrate_schema()  # Add migration step
    
    def _ensure_directory(self):
        """Ensure the database directory exists."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    
    def _init_db(self):
        """Initialize database schema."""
        with self._get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS chats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL DEFAULT 'Nouvelle conversation',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_archived INTEGER DEFAULT 0,
                    metadata TEXT
                );
                
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
                    content TEXT NOT NULL,
                    sources TEXT,
                    tokens_used INTEGER DEFAULT 0,
                    response_time_ms INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (chat_id) REFERENCES chats(id) ON DELETE CASCADE
                );
                
                CREATE INDEX IF NOT EXISTS idx_messages_chat_id ON messages(chat_id);
                CREATE INDEX IF NOT EXISTS idx_chats_updated ON chats(updated_at DESC);
            """)
    
    def _migrate_schema(self):
        """Migrate old database schema to new version."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Get existing columns in chats table
            cursor.execute("PRAGMA table_info(chats)")
            chat_columns = {row[1] for row in cursor.fetchall()}
            
            # Add missing columns to chats table
            if 'is_archived' not in chat_columns:
                print("🔄 Migration: Adding is_archived column to chats table...")
                conn.execute("ALTER TABLE chats ADD COLUMN is_archived INTEGER DEFAULT 0")
            
            if 'metadata' not in chat_columns:
                print("🔄 Migration: Adding metadata column to chats table...")
                conn.execute("ALTER TABLE chats ADD COLUMN metadata TEXT")
            
            # Get existing columns in messages table
            cursor.execute("PRAGMA table_info(messages)")
            message_columns = {row[1] for row in cursor.fetchall()}
            
            # Add missing columns to messages table
            if 'tokens_used' not in message_columns:
                print("🔄 Migration: Adding tokens_used column to messages table...")
                conn.execute("ALTER TABLE messages ADD COLUMN tokens_used INTEGER DEFAULT 0")
            
            if 'response_time_ms' not in message_columns:
                print("🔄 Migration: Adding response_time_ms column to messages table...")
                conn.execute("ALTER TABLE messages ADD COLUMN response_time_ms INTEGER DEFAULT 0")
            
            conn.commit()
            print("✅ Database schema migration completed!")
    
    # ==================== CHAT OPERATIONS ====================
    
    def create_chat(self, title: str = "Nouvelle conversation") -> int:
        """Create a new chat session."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO chats (title) VALUES (?)", 
                (title,)
            )
            return cursor.lastrowid
    
    def get_chat(self, chat_id: int) -> Optional[Dict[str, Any]]:
        """Get a single chat by ID."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM chats WHERE id = ?", 
                (chat_id,)
            ).fetchone()
            return dict(row) if row else None
    
    def get_all_chats(self, include_archived: bool = False) -> List[Dict[str, Any]]:
        """Get all chats ordered by most recent."""
        query = """
            SELECT c.*, COUNT(m.id) as message_count
            FROM chats c
            LEFT JOIN messages m ON c.id = m.chat_id
            {}
            GROUP BY c.id
            ORDER BY c.updated_at DESC
        """.format("" if include_archived else "WHERE c.is_archived = 0")
        
        with self._get_connection() as conn:
            rows = conn.execute(query).fetchall()
            return [dict(row) for row in rows]
    
    def update_chat_title(self, chat_id: int, title: str):
        """Update chat title."""
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE chats SET title = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (title[:100], chat_id)
            )
    
    def archive_chat(self, chat_id: int):
        """Archive a chat instead of deleting."""
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE chats SET is_archived = 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (chat_id,)
            )
    
    def delete_chat(self, chat_id: int):
        """Permanently delete a chat and all its messages."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM chats WHERE id = ?", (chat_id,))
    
    def delete_all_chats(self):
        """Delete all chats and messages."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM messages")
            conn.execute("DELETE FROM chats")
    
    # ==================== MESSAGE OPERATIONS ====================
    
    def add_message(
        self, 
        chat_id: int, 
        role: str, 
        content: str, 
        sources: Optional[List[Dict]] = None,
        tokens_used: int = 0,
        response_time_ms: int = 0
    ) -> int:
        """Add a message to a chat."""
        sources_json = json.dumps(sources, ensure_ascii=False) if sources else None
        
        with self._get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO messages (chat_id, role, content, sources, tokens_used, response_time_ms)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (chat_id, role, content, sources_json, tokens_used, response_time_ms))
            
            conn.execute(
                "UPDATE chats SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (chat_id,)
            )
            return cursor.lastrowid
    
    def get_messages(self, chat_id: int, limit: int = None) -> List[Dict[str, Any]]:
        """Get all messages for a chat."""
        query = """
            SELECT * FROM messages 
            WHERE chat_id = ? 
            ORDER BY created_at ASC
        """
        if limit:
            query += f" LIMIT {limit}"
        
        with self._get_connection() as conn:
            rows = conn.execute(query, (chat_id,)).fetchall()
            messages = []
            for row in rows:
                msg = dict(row)
                if msg['sources']:
                    try:
                        msg['sources'] = json.loads(msg['sources'])
                    except json.JSONDecodeError:
                        msg['sources'] = []
                messages.append(msg)
            return messages
    
    def get_recent_messages(self, chat_id: int, count: int = 10) -> List[Dict[str, Any]]:
        """Get the most recent messages for context."""
        query = """
            SELECT * FROM (
                SELECT * FROM messages 
                WHERE chat_id = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            ) ORDER BY created_at ASC
        """
        with self._get_connection() as conn:
            rows = conn.execute(query, (chat_id, count)).fetchall()
            messages = []
            for row in rows:
                msg = dict(row)
                if msg['sources']:
                    try:
                        msg['sources'] = json.loads(msg['sources'])
                    except json.JSONDecodeError:
                        msg['sources'] = []
                messages.append(msg)
            return messages
    
    # ==================== STATISTICS ====================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        with self._get_connection() as conn:
            stats = {}
            stats['total_chats'] = conn.execute(
                "SELECT COUNT(*) FROM chats WHERE is_archived = 0"
            ).fetchone()[0]
            stats['archived_chats'] = conn.execute(
                "SELECT COUNT(*) FROM chats WHERE is_archived = 1"
            ).fetchone()[0]
            stats['total_messages'] = conn.execute(
                "SELECT COUNT(*) FROM messages"
            ).fetchone()[0]
            stats['total_tokens'] = conn.execute(
                "SELECT COALESCE(SUM(tokens_used), 0) FROM messages"
            ).fetchone()[0]
            return stats
    
    def search_messages(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search through message content."""
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT m.*, c.title as chat_title
                FROM messages m
                JOIN chats c ON m.chat_id = c.id
                WHERE m.content LIKE ?
                ORDER BY m.created_at DESC
                LIMIT ?
            """, (f"%{query}%", limit)).fetchall()
            return [dict(row) for row in rows]


# Global database instance
db = ChatDatabase()


# ==================== CONVENIENCE FUNCTIONS ====================

def create_chat(title: str = "Nouvelle conversation") -> int:
    return db.create_chat(title)

def get_all_chats(include_archived: bool = False) -> List[Dict[str, Any]]:
    return db.get_all_chats(include_archived)

def get_chat_messages(chat_id: int) -> List[Dict[str, Any]]:
    return db.get_messages(chat_id)

def add_message(chat_id: int, role: str, content: str, sources: Optional[List[Dict]] = None, **kwargs) -> int:
    return db.add_message(chat_id, role, content, sources, **kwargs)

def update_chat_title(chat_id: int, title: str):
    return db.update_chat_title(chat_id, title)

def delete_chat(chat_id: int):
    return db.delete_chat(chat_id)

def get_stats() -> Dict[str, Any]:
    return db.get_stats()

def search_messages(query: str) -> List[Dict[str, Any]]:
    return db.search_messages(query)