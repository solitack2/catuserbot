import sqlite3
import json
import datetime
from typing import List, Dict, Optional, Tuple
from config import Config

class DatabaseManager:
    def __init__(self):
        self.db_name = Config.DATABASE_NAME
        self.init_database()
    
    def get_connection(self):
        return sqlite3.connect(self.db_name)
    
    def init_database(self):
        """Initialize database tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Accounts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    phone VARCHAR(20) UNIQUE NOT NULL,
                    session_name VARCHAR(100) NOT NULL,
                    api_id INTEGER NOT NULL,
                    api_hash VARCHAR(100) NOT NULL,
                    first_name VARCHAR(100),
                    last_name VARCHAR(100),
                    username VARCHAR(100),
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_used TIMESTAMP,
                    total_sent INTEGER DEFAULT 0
                )
            ''')
            
            # Messages table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id INTEGER,
                    target_user_id BIGINT,
                    target_username VARCHAR(100),
                    message_text TEXT,
                    message_type VARCHAR(20) DEFAULT 'text',
                    status VARCHAR(20) DEFAULT 'pending',
                    sent_at TIMESTAMP,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (account_id) REFERENCES accounts (id)
                )
            ''')
            
            # Analytics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL,
                    account_id INTEGER,
                    total_sent INTEGER DEFAULT 0,
                    successful_sent INTEGER DEFAULT 0,
                    failed_sent INTEGER DEFAULT 0,
                    unique_recipients INTEGER DEFAULT 0,
                    FOREIGN KEY (account_id) REFERENCES accounts (id)
                )
            ''')
            
            # Settings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    key VARCHAR(50) PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Templates table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(100) UNIQUE NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
    
    def add_account(self, phone: str, session_name: str, api_id: int, api_hash: str, 
                   first_name: str = None, last_name: str = None, username: str = None) -> int:
        """Add new account to database"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO accounts (phone, session_name, api_id, api_hash, first_name, last_name, username)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (phone, session_name, api_id, api_hash, first_name, last_name, username))
            conn.commit()
            return cursor.lastrowid
    
    def get_accounts(self, active_only: bool = True) -> List[Dict]:
        """Get all accounts from database"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM accounts"
            if active_only:
                query += " WHERE is_active = 1"
            cursor.execute(query)
            
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def update_account_usage(self, account_id: int):
        """Update account last used timestamp and increment sent count"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE accounts 
                SET last_used = CURRENT_TIMESTAMP, total_sent = total_sent + 1
                WHERE id = ?
            ''', (account_id,))
            conn.commit()
    
    def log_message(self, account_id: int, target_user_id: int, target_username: str,
                   message_text: str, message_type: str = 'text') -> int:
        """Log message to database"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO messages (account_id, target_user_id, target_username, message_text, message_type)
                VALUES (?, ?, ?, ?, ?)
            ''', (account_id, target_user_id, target_username, message_text, message_type))
            conn.commit()
            return cursor.lastrowid
    
    def update_message_status(self, message_id: int, status: str, error_message: str = None):
        """Update message status"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if status == 'sent':
                cursor.execute('''
                    UPDATE messages 
                    SET status = ?, sent_at = CURRENT_TIMESTAMP, error_message = ?
                    WHERE id = ?
                ''', (status, error_message, message_id))
            else:
                cursor.execute('''
                    UPDATE messages 
                    SET status = ?, error_message = ?
                    WHERE id = ?
                ''', (status, error_message, message_id))
            conn.commit()
    
    def get_analytics(self, days: int = 7) -> Dict:
        """Get analytics data for specified number of days"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get daily statistics
            cursor.execute('''
                SELECT DATE(created_at) as date,
                       COUNT(*) as total_messages,
                       SUM(CASE WHEN status = 'sent' THEN 1 ELSE 0 END) as successful,
                       SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed
                FROM messages 
                WHERE created_at >= date('now', '-{} days')
                GROUP BY DATE(created_at)
                ORDER BY date DESC
            '''.format(days))
            
            daily_stats = cursor.fetchall()
            
            # Get account statistics
            cursor.execute('''
                SELECT a.phone, a.first_name, a.total_sent,
                       COUNT(m.id) as messages_today
                FROM accounts a
                LEFT JOIN messages m ON a.id = m.account_id AND DATE(m.created_at) = DATE('now')
                WHERE a.is_active = 1
                GROUP BY a.id
            ''')
            
            account_stats = cursor.fetchall()
            
            return {
                'daily_stats': daily_stats,
                'account_stats': account_stats
            }
    
    def add_template(self, name: str, content: str) -> int:
        """Add message template"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO templates (name, content)
                VALUES (?, ?)
            ''', (name, content))
            conn.commit()
            return cursor.lastrowid
    
    def get_templates(self) -> List[Dict]:
        """Get all message templates"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM templates ORDER BY name')
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def set_setting(self, key: str, value: str):
        """Set a setting value"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO settings (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            ''', (key, value))
            conn.commit()
    
    def get_setting(self, key: str, default: str = None) -> str:
        """Get a setting value"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
            result = cursor.fetchone()
            return result[0] if result else default