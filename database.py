# database.py

import sqlite3
from config import DATABASE_NAME


class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DATABASE_NAME, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self.create_tables()

    # ======================
    # Tables
    # ======================
    def create_tables(self):
        # Users
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            telegram_id INTEGER UNIQUE,
            username TEXT,
            full_name TEXT,
            role TEXT DEFAULT 'user',
            is_active INTEGER DEFAULT 1,
            joined_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Permissions
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            permission TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """)

        # Buttons
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS buttons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            type TEXT NOT NULL,
            content TEXT,
            parent_id INTEGER,
            is_active INTEGER DEFAULT 1,
            created_by INTEGER,
            position INTEGER,
            FOREIGN KEY (parent_id) REFERENCES buttons (id),
            FOREIGN KEY (created_by) REFERENCES users (id)
        )
        """)

        # Messages (Support System)
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS support_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            admin_id INTEGER,
            message_text TEXT,
            is_from_admin INTEGER DEFAULT 0,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Pending Supervisors
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS pending_supervisors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            role TEXT DEFAULT 'supervisor'
        )
        """)

        self.conn.commit()

    # ======================
    # Pending supervisors
    # ======================
    def add_pending_supervisor(self, username):
        self.cursor.execute(
            "INSERT OR IGNORE INTO pending_supervisors (username) VALUES (?)",
            (username.lower(),)
        )
        self.conn.commit()

    def get_pending_by_username(self, username):
        self.cursor.execute(
            "SELECT * FROM pending_supervisors WHERE username = ?",
            (username.lower(),)
        )
        return self.cursor.fetchone()

    def remove_pending(self, username):
        self.cursor.execute(
            "DELETE FROM pending_supervisors WHERE username = ?",
            (username.lower(),)
        )
        self.conn.commit()

    # ======================
    # Users
    # ======================
    def add_user(self, telegram_id, username=None, full_name=None, role="user"):
        self.cursor.execute(
            "INSERT OR IGNORE INTO users (telegram_id, username, full_name, role) VALUES (?, ?, ?, ?)",
            (telegram_id, username, full_name, role)
        )
        self.conn.commit()

    def update_user_info(self, telegram_id, username, full_name):
        self.cursor.execute(
            "UPDATE users SET username = ?, full_name = ? WHERE telegram_id = ?",
            (username, full_name, telegram_id)
        )
        self.conn.commit()

    def get_total_users_count(self):
        self.cursor.execute("SELECT COUNT(*) FROM users")
        return self.cursor.fetchone()[0]

    def get_user_by_telegram_id(self, telegram_id):
        self.cursor.execute(
            "SELECT * FROM users WHERE telegram_id = ?",
            (telegram_id,)
        )
        return self.cursor.fetchone()

    # ======================
    # Permissions
    # ======================
    def add_permission(self, user_id, permission):
        self.cursor.execute(
            "INSERT INTO permissions (user_id, permission) VALUES (?, ?)",
            (user_id, permission)
        )
        self.conn.commit()

    def get_permissions(self, user_id):
        self.cursor.execute(
            "SELECT permission FROM permissions WHERE user_id = ?",
            (user_id,)
        )
        return [row["permission"] for row in self.cursor.fetchall()]

    # ======================
    # Buttons
    # ======================
    def add_button(self, text, btn_type, content, parent_id=None, created_by=None):
        self.cursor.execute("SELECT COUNT(*) FROM buttons")
        count = self.cursor.fetchone()[0]
        self.cursor.execute("""
        INSERT INTO buttons (text, type, content, parent_id, created_by, position)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (text, btn_type, content, parent_id, created_by, count))
        self.conn.commit()

    def get_buttons(self, parent_id=None):
        if parent_id is None:
            self.cursor.execute(
                "SELECT * FROM buttons WHERE parent_id IS NULL AND is_active = 1 ORDER BY position ASC"
            )
        else:
            self.cursor.execute(
                "SELECT * FROM buttons WHERE parent_id = ? AND is_active = 1 ORDER BY position ASC",
                (parent_id,)
            )
        return self.cursor.fetchall()

    def move_button(self, button_id, direction):
        # direction: 'up' or 'down'
        self.cursor.execute("SELECT position FROM buttons WHERE id = ?", (button_id,))
        current_pos = self.cursor.fetchone()[0]
        
        if direction == 'up':
            self.cursor.execute("SELECT id, position FROM buttons WHERE position < ? ORDER BY position DESC LIMIT 1", (current_pos,))
        else:
            self.cursor.execute("SELECT id, position FROM buttons WHERE position > ? ORDER BY position ASC LIMIT 1", (current_pos,))
            
        other = self.cursor.fetchone()
        if other:
            other_id, other_pos = other
            self.cursor.execute("UPDATE buttons SET position = ? WHERE id = ?", (other_pos, button_id))
            self.cursor.execute("UPDATE buttons SET position = ? WHERE id = ?", (current_pos, other_id))
            self.conn.commit()
            return True
        return False

    def delete_button(self, button_id):
        self.cursor.execute("DELETE FROM buttons WHERE id = ?", (button_id,))
        self.conn.commit()

    def update_button(self, button_id, text=None, content=None):
        if text:
            self.cursor.execute("UPDATE buttons SET text = ? WHERE id = ?", (text, button_id))
        if content:
            self.cursor.execute("UPDATE buttons SET content = ? WHERE id = ?", (content, button_id))
        self.conn.commit()

    def get_button_by_id(self, button_id):
        self.cursor.execute("SELECT * FROM buttons WHERE id = ?", (button_id,))
        return self.cursor.fetchone()

    # ======================
    # Admins / Supervisors
    # ======================
    def get_admins(self):
        self.cursor.execute(
            "SELECT * FROM users WHERE role IN ('admin', 'supervisor')"
        )
        return self.cursor.fetchall()

    def update_user_role(self, telegram_id, role):
        self.cursor.execute(
            "UPDATE users SET role = ? WHERE telegram_id = ?",
            (role, telegram_id)
        )
        self.conn.commit()

    # ======================
    # Permissions & Features
    # ======================
    def get_features(self):
        self.cursor.execute("SELECT * FROM features")
        return self.cursor.fetchall()

    def get_supervisor_permissions(self, telegram_id):
        self.cursor.execute("SELECT feature_id FROM supervisor_permissions WHERE telegram_id = ?", (telegram_id,))
        return [row['feature_id'] for row in self.cursor.fetchall()]

    def set_supervisor_permission(self, telegram_id, feature_id, granted):
        if granted:
            self.cursor.execute("INSERT OR IGNORE INTO supervisor_permissions (telegram_id, feature_id) VALUES (?, ?)", (telegram_id, feature_id))
        else:
            self.cursor.execute("DELETE FROM supervisor_permissions WHERE telegram_id = ? AND feature_id = ?", (telegram_id, feature_id))
        self.conn.commit()

    def has_permission(self, telegram_id, feature_id):
        user = self.get_user_by_telegram_id(telegram_id)
        if not user: return False
        if user['role'] in ('super_admin', 'admin'): return True
        self.cursor.execute("SELECT 1 FROM supervisor_permissions WHERE telegram_id = ? AND feature_id = ?", (telegram_id, feature_id))
        return bool(self.cursor.fetchone())

    def delete_supervisor(self, telegram_id):
        self.cursor.execute("DELETE FROM users WHERE telegram_id = ?", (telegram_id,))
        self.cursor.execute("DELETE FROM supervisor_permissions WHERE telegram_id = ?", (telegram_id,))
        self.conn.commit()
    def add_support_message(self, user_id, message_text, is_from_admin=0, admin_id=None, button_id=None, admin_name=None):
        self.cursor.execute("""
            INSERT INTO support_messages (user_id, message_text, is_from_admin, admin_id, button_id, admin_name)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, message_text, is_from_admin, admin_id, button_id, admin_name))
        self.conn.commit()

    def get_messages_by_button(self, button_id):
        self.cursor.execute("""
            SELECT sm.*, u.username, u.full_name 
            FROM support_messages sm 
            LEFT JOIN users u ON sm.user_id = u.telegram_id 
            WHERE sm.button_id = ? 
            ORDER BY sm.timestamp ASC
        """, (button_id,))
        return self.cursor.fetchall()

    def add_admin_log(self, admin_id, admin_name, action_type, section, details):
        self.cursor.execute("""
            INSERT INTO admin_logs (admin_id, admin_name, action_type, section, details)
            VALUES (?, ?, ?, ?, ?)
        """, (admin_id, admin_name, action_type, section, details))
        self.conn.commit()

    def get_admin_logs(self, limit=20):
        self.cursor.execute("SELECT * FROM admin_logs ORDER BY timestamp DESC LIMIT ?", (limit,))
        return self.cursor.fetchall()

    def get_contact_buttons(self):
        self.cursor.execute("SELECT * FROM buttons WHERE type = 'contact' AND is_active = 1")
        return self.cursor.fetchall()
