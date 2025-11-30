import sqlite3
import json
from typing import Dict, Any, Optional

class Database:
    def __init__(self, db_path: str = 'game_data.db'):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS user_progress (
                    user_id INTEGER PRIMARY KEY,
                    current_level INTEGER DEFAULT 0,
                    xp INTEGER DEFAULT 0,
                    message_count INTEGER DEFAULT 0,
                    game_state TEXT DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS user_stats (
                    user_id INTEGER PRIMARY KEY,
                    total_moves INTEGER DEFAULT 0,
                    total_messages INTEGER DEFAULT 0,
                    highest_level INTEGER DEFAULT 0,
                    play_time INTEGER DEFAULT 0
                )
            ''')

    def get_user_progress(self, user_id: int) -> Dict[str, Any]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                'SELECT current_level, xp, message_count, game_state FROM user_progress WHERE user_id = ?',
                (user_id,)
            )
            result = cursor.fetchone()
            
            if result:
                return {
                    'current_level': result[0],
                    'xp': result[1],
                    'message_count': result[2],
                    'game_state': json.loads(result[3]) if result[3] else {}
                }
            else:
                # Create new user
                default_state = {
                    'grid': [],
                    'selected': [],
                    'max_number': 8,
                    'active_bonus': None
                }
                conn.execute(
                    'INSERT INTO user_progress (user_id, game_state) VALUES (?, ?)',
                    (user_id, json.dumps(default_state))
                )
                conn.execute(
                    'INSERT INTO user_stats (user_id) VALUES (?)',
                    (user_id,)
                )
                return {
                    'current_level': 0,
                    'xp': 0,
                    'message_count': 0,
                    'game_state': default_state
                }

    def update_user_progress(self, user_id: int, progress: Dict[str, Any]):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                UPDATE user_progress 
                SET current_level = ?, xp = ?, message_count = ?, game_state = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (
                progress['current_level'],
                progress['xp'],
                progress['message_count'],
                json.dumps(progress['game_state']),
                user_id
            ))

    def update_user_stats(self, user_id: int, moves: int = 0, messages: int = 0, level: int = 0):
        with sqlite3.connect(self.db_path) as conn:
            if moves > 0:
                conn.execute(
                    'UPDATE user_stats SET total_moves = total_moves + ? WHERE user_id = ?',
                    (moves, user_id)
                )
            if messages > 0:
                conn.execute(
                    'UPDATE user_stats SET total_messages = total_messages + ? WHERE user_id = ?',
                    (messages, user_id)
                )
            if level > 0:
                conn.execute(
                    'UPDATE user_stats SET highest_level = ? WHERE user_id = ? AND highest_level < ?',
                    (level, user_id, level)
                )
