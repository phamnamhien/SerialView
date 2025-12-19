"""
Logger - SQLite database logging for serial data
Thread-safe logging system
"""
import sqlite3
import os
from datetime import datetime
from threading import Lock
from typing import Optional, List, Dict, Any
from enum import Enum


class DataDirection(Enum):
    """Data direction"""
    TX = "TX"
    RX = "RX"


class SerialLogger:
    """Logger for serial data"""
    
    def __init__(self, db_path: str = "logs/serial_monitor.db"):
        self.db_path = db_path
        self.lock = Lock()
        self._ensure_db_dir()
        self._init_database()
    
    def _ensure_db_dir(self):
        """Ensure logs directory exists"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            try:
                os.makedirs(db_dir, exist_ok=True)
            except (FileExistsError, OSError):
                pass  # Directory already exists or is a file, ignore
    
    def _init_database(self):
        """Initialize database schema"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # logs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    port TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    data BLOB NOT NULL,
                    display_mode TEXT,
                    session_id INTEGER,
                    FOREIGN KEY (session_id) REFERENCES sessions(id)
                )
            ''')
            
            # sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    port TEXT NOT NULL,
                    baudrate INTEGER,
                    databits INTEGER,
                    parity TEXT,
                    stopbits INTEGER,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    notes TEXT
                )
            ''')
            
            # scripts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scripts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            ''')
            
            # Indexes
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_logs_timestamp 
                ON logs(timestamp)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_logs_session 
                ON logs(session_id)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_logs_port 
                ON logs(port)
            ''')
            
            conn.commit()
            conn.close()
    
    def start_session(self, port: str, baudrate: int, databits: int, 
                      parity: str, stopbits: int, notes: str = "") -> int:
        """Start new session and return session_id"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            timestamp = datetime.now().isoformat()
            cursor.execute('''
                INSERT INTO sessions (port, baudrate, databits, parity, stopbits, start_time, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (port, baudrate, databits, parity, stopbits, timestamp, notes))
            
            session_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return session_id
    
    def end_session(self, session_id: int):
        """End session"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            timestamp = datetime.now().isoformat()
            cursor.execute('''
                UPDATE sessions SET end_time = ? WHERE id = ?
            ''', (timestamp, session_id))
            
            conn.commit()
            conn.close()
    
    def log_data(self, port: str, direction: DataDirection, data: bytes, 
                 display_mode: str = None, session_id: int = None):
        """Log serial data"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            timestamp = datetime.now().isoformat()
            cursor.execute('''
                INSERT INTO logs (timestamp, port, direction, data, display_mode, session_id)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (timestamp, port, direction.value, data, display_mode, session_id))
            
            conn.commit()
            conn.close()
    
    def get_logs(self, port: Optional[str] = None, session_id: Optional[int] = None,
                 start_time: Optional[str] = None, end_time: Optional[str] = None,
                 limit: int = 1000) -> List[Dict[str, Any]]:
        """Get logs with filters"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = "SELECT * FROM logs WHERE 1=1"
            params = []
            
            if port:
                query += " AND port = ?"
                params.append(port)
            
            if session_id:
                query += " AND session_id = ?"
                params.append(session_id)
            
            if start_time:
                query += " AND timestamp >= ?"
                params.append(start_time)
            
            if end_time:
                query += " AND timestamp <= ?"
                params.append(end_time)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()
            
            return [dict(row) for row in rows]
    
    def get_sessions(self, port: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get session list"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = "SELECT * FROM sessions WHERE 1=1"
            params = []
            
            if port:
                query += " AND port = ?"
                params.append(port)
            
            query += " ORDER BY start_time DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()
            
            return [dict(row) for row in rows]
    
    def save_script(self, name: str, content: str, description: str = ""):
        """Save script"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            timestamp = datetime.now().isoformat()
            cursor.execute('''
                INSERT OR REPLACE INTO scripts (name, description, content, created_at, updated_at)
                VALUES (?, ?, ?, 
                    COALESCE((SELECT created_at FROM scripts WHERE name = ?), ?),
                    ?)
            ''', (name, description, content, name, timestamp, timestamp))
            
            conn.commit()
            conn.close()
    
    def get_script(self, name: str) -> Optional[Dict[str, Any]]:
        """Get script by name"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM scripts WHERE name = ?", (name,))
            row = cursor.fetchone()
            conn.close()
            
            return dict(row) if row else None
    
    def get_all_scripts(self) -> List[Dict[str, Any]]:
        """Get all scripts"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM scripts ORDER BY updated_at DESC")
            rows = cursor.fetchall()
            conn.close()
            
            return [dict(row) for row in rows]
    
    def delete_script(self, name: str):
        """Delete script"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM scripts WHERE name = ?", (name,))
            conn.commit()
            conn.close()
    
    def clear_logs(self, older_than_days: Optional[int] = None):
        """Clear old logs"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if older_than_days:
                cutoff_date = datetime.now().timestamp() - (older_than_days * 24 * 3600)
                cutoff_iso = datetime.fromtimestamp(cutoff_date).isoformat()
                cursor.execute("DELETE FROM logs WHERE timestamp < ?", (cutoff_iso,))
            else:
                cursor.execute("DELETE FROM logs")
            
            conn.commit()
            conn.close()
    
    def get_database_size(self) -> int:
        """Get database size in bytes"""
        if os.path.exists(self.db_path):
            return os.path.getsize(self.db_path)
        return 0
    
    def vacuum_database(self):
        """Optimize database"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("VACUUM")
            conn.close()