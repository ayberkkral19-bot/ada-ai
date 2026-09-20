import sqlite3
import threading
import json
from datetime import datetime
from config import DB_PATH


class Memory:
    def __init__(self):
        self._local = threading.local()
        self._init_db()

    def _get_conn(self):
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            self._local.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn

    def _init_db(self):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS command_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            command TEXT NOT NULL,
            result TEXT,
            success INTEGER DEFAULT 1,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS preferences (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')
        conn.commit()

    def save_message(self, role, content):
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO chat_history (role, content) VALUES (?, ?)',
                (role, content)
            )
            conn.commit()
            return True
        except Exception as e:
            print(f'[Memory] Save message error: {e}')
            return False

    def get_history(self, limit=50):
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute(
                'SELECT role, content, timestamp FROM chat_history ORDER BY id DESC LIMIT ?',
                (limit,)
            )
            rows = cursor.fetchall()
            return [{'role': r['role'], 'content': r['content'], 'timestamp': r['timestamp']} for r in reversed(rows)]
        except Exception as e:
            print(f'[Memory] Get history error: {e}')
            return []

    def clear_history(self):
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM chat_history')
            conn.commit()
            return True
        except Exception as e:
            print(f'[Memory] Clear history error: {e}')
            return False

    def log_command(self, command, result='', success=True):
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO command_log (command, result, success) VALUES (?, ?, ?)',
                (command, result, 1 if success else 0)
            )
            conn.commit()
            return True
        except Exception as e:
            print(f'[Memory] Log command error: {e}')
            return False

    def get_command_log(self, limit=20):
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute(
                'SELECT command, result, success, timestamp FROM command_log ORDER BY id DESC LIMIT ?',
                (limit,)
            )
            rows = cursor.fetchall()
            return [{'command': r['command'], 'result': r['result'], 'success': r['success'], 'timestamp': r['timestamp']} for r in reversed(rows)]
        except Exception as e:
            print(f'[Memory] Get command log error: {e}')
            return []

    def set_preference(self, key, value):
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute(
                'INSERT OR REPLACE INTO preferences (key, value, updated_at) VALUES (?, ?, ?)',
                (key, value, datetime.now().isoformat())
            )
            conn.commit()
            return True
        except Exception as e:
            print(f'[Memory] Set preference error: {e}')
            return False

    def get_preference(self, key, default=None):
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute('SELECT value FROM preferences WHERE key = ?', (key,))
            row = cursor.fetchone()
            return row['value'] if row else default
        except Exception as e:
            print(f'[Memory] Get preference error: {e}')
            return default

    def get_chat_count(self):
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) as cnt FROM chat_history')
            row = cursor.fetchone()
            return row['cnt'] if row else 0
        except Exception:
            return 0
