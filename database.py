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
            
            # Enhanced Accounts table
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
                    status VARCHAR(20) DEFAULT 'active',
                    is_premium BOOLEAN DEFAULT 0,
                    category_id INTEGER,
                    proxy_id INTEGER,
                    total_sent INTEGER DEFAULT 0,
                    successful_sent INTEGER DEFAULT 0,
                    failed_sent INTEGER DEFAULT 0,
                    last_error TEXT,
                    flood_wait_until TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_used TIMESTAMP,
                    FOREIGN KEY (category_id) REFERENCES categories (id),
                    FOREIGN KEY (proxy_id) REFERENCES proxies (id)
                )
            ''')
            
            # Categories table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(100) UNIQUE NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Proxies table  
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS proxies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type VARCHAR(10) NOT NULL,
                    host VARCHAR(255) NOT NULL,
                    port INTEGER NOT NULL,
                    username VARCHAR(100),
                    password VARCHAR(100),
                    is_active BOOLEAN DEFAULT 1,
                    accounts_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Members table for analysis
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS members (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id BIGINT NOT NULL,
                    username VARCHAR(100),
                    first_name VARCHAR(100),
                    last_name VARCHAR(100),
                    phone VARCHAR(20),
                    chat_id BIGINT NOT NULL,
                    chat_title VARCHAR(200),
                    extracted_by INTEGER,
                    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (extracted_by) REFERENCES accounts (id)
                )
            ''')
            
            # Enhanced Messages table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id INTEGER,
                    target_user_id BIGINT,
                    target_username VARCHAR(100),
                    message_text TEXT,
                    media_path VARCHAR(500),
                    message_type VARCHAR(20) DEFAULT 'text',
                    status VARCHAR(20) DEFAULT 'pending',
                    category_id INTEGER,
                    sent_at TIMESTAMP,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (account_id) REFERENCES accounts (id),
                    FOREIGN KEY (category_id) REFERENCES categories (id)
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
            
            # Analytics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL,
                    account_id INTEGER,
                    category_id INTEGER,
                    total_sent INTEGER DEFAULT 0,
                    successful_sent INTEGER DEFAULT 0,
                    failed_sent INTEGER DEFAULT 0,
                    unique_recipients INTEGER DEFAULT 0,
                    FOREIGN KEY (account_id) REFERENCES accounts (id),
                    FOREIGN KEY (category_id) REFERENCES categories (id)
                )
            ''')
            
            conn.commit()
    
    # Account Management
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
    
    def get_accounts(self, category_id: int = None) -> List[Dict]:
        """Get all accounts or accounts from specific category"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if category_id:
                cursor.execute('''
                    SELECT a.*, c.name as category_name, p.host as proxy_host 
                    FROM accounts a 
                    LEFT JOIN categories c ON a.category_id = c.id
                    LEFT JOIN proxies p ON a.proxy_id = p.id
                    WHERE a.category_id = ?
                ''', (category_id,))
            else:
                cursor.execute('''
                    SELECT a.*, c.name as category_name, p.host as proxy_host 
                    FROM accounts a 
                    LEFT JOIN categories c ON a.category_id = c.id
                    LEFT JOIN proxies p ON a.proxy_id = p.id
                ''')
            
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def update_account_status(self, account_id: int, status: str, error_msg: str = None):
        """Update account status"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE accounts SET status = ?, last_error = ?, last_used = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (status, error_msg, account_id))
            conn.commit()
    
    def assign_account_to_category(self, account_id: int, category_id: int):
        """Assign account to category"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE accounts SET category_id = ? WHERE id = ?', (category_id, account_id))
            conn.commit()
    
    def assign_proxy_to_account(self, account_id: int, proxy_id: int):
        """Assign proxy to account"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE accounts SET proxy_id = ? WHERE id = ?', (proxy_id, account_id))
            conn.commit()
    
    # Category Management
    def create_category(self, name: str, description: str = None) -> int:
        """Create new category"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO categories (name, description) VALUES (?, ?)', (name, description))
            conn.commit()
            return cursor.lastrowid
    
    def get_categories(self) -> List[Dict]:
        """Get all categories"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT c.*, COUNT(a.id) as account_count 
                FROM categories c 
                LEFT JOIN accounts a ON c.id = a.category_id 
                GROUP BY c.id
            ''')
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    # Proxy Management
    def add_proxy(self, proxy_type: str, host: str, port: int, username: str = None, password: str = None) -> int:
        """Add new proxy"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO proxies (type, host, port, username, password) 
                VALUES (?, ?, ?, ?, ?)
            ''', (proxy_type, host, port, username, password))
            conn.commit()
            return cursor.lastrowid
    
    def get_proxies(self) -> List[Dict]:
        """Get all proxies"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT p.*, COUNT(a.id) as accounts_count 
                FROM proxies p 
                LEFT JOIN accounts a ON p.id = a.proxy_id 
                GROUP BY p.id
            ''')
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_available_proxy(self) -> Optional[Dict]:
        """Get proxy with least accounts assigned"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT p.*, COUNT(a.id) as accounts_count 
                FROM proxies p 
                LEFT JOIN accounts a ON p.id = a.proxy_id 
                WHERE p.is_active = 1
                GROUP BY p.id
                HAVING COUNT(a.id) < ?
                ORDER BY COUNT(a.id) ASC
                LIMIT 1
            ''', (Config.MAX_ACCOUNTS_PER_PROXY,))
            
            row = cursor.fetchone()
            if row:
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, row))
            return None
    
    # Member Management
    def save_members(self, members: List[Dict], extracted_by: int):
        """Save extracted members"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for member in members:
                cursor.execute('''
                    INSERT OR REPLACE INTO members 
                    (user_id, username, first_name, last_name, phone, chat_id, chat_title, extracted_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    member.get('id'), member.get('username'), member.get('first_name'),
                    member.get('last_name'), member.get('phone'), member.get('chat_id'),
                    member.get('chat_title'), extracted_by
                ))
            conn.commit()
    
    def get_members(self, limit: int = None) -> List[Dict]:
        """Get extracted members"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = 'SELECT * FROM members ORDER BY extracted_at DESC'
            if limit:
                query += f' LIMIT {limit}'
            cursor.execute(query)
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    # Settings Management
    def save_setting(self, key: str, value: str):
        """Save setting"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO settings (key, value, updated_at) 
                VALUES (?, ?, CURRENT_TIMESTAMP)
            ''', (key, value))
            conn.commit()
    
    def get_setting(self, key: str, default=None):
        """Get setting value"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
            row = cursor.fetchone()
            return row[0] if row else default
    
    def get_all_settings(self) -> Dict:
        """Get all settings"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT key, value FROM settings')
            return dict(cursor.fetchall())
    
    # Message Management
    def log_message(self, account_id: int, target_user_id: int, message_text: str, 
                   status: str, category_id: int = None, media_path: str = None):
        """Log sent message"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO messages 
                (account_id, target_user_id, message_text, media_path, status, category_id, sent_at)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (account_id, target_user_id, message_text, media_path, status, category_id))
            conn.commit()
    
    # Statistics
    def get_account_stats(self) -> List[Dict]:
        """Get account statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    a.id, a.phone, a.first_name, a.status,
                    COUNT(m.id) as total_messages,
                    SUM(CASE WHEN m.status = 'sent' THEN 1 ELSE 0 END) as successful,
                    SUM(CASE WHEN m.status = 'failed' THEN 1 ELSE 0 END) as failed,
                    c.name as category_name
                FROM accounts a 
                LEFT JOIN messages m ON a.id = m.account_id 
                LEFT JOIN categories c ON a.category_id = c.id
                GROUP BY a.id
            ''')
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]