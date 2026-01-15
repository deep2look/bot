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
            role TEXT DEFAULT 'user',
            is_active INTEGER DEFAULT 1
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
            FOREIGN KEY (parent_id) REFERENCES buttons (id),
            FOREIGN KEY (created_by) REFERENCES users (id)
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
    def add_user(self, telegram_id, role="user"):
        self.cursor.execute(
            "INSERT OR IGNORE INTO users (telegram_id, role) VALUES (?, ?)",
            (telegram_id, role)
        )
        self.conn.commit()

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
    def add_button(self, text, btn_type, content, parent_id, created_by):
        self.cursor.execute("""
        INSERT INTO buttons (text, type, content, parent_id, created_by)
        VALUES (?, ?, ?, ?, ?)
        """, (text, btn_type, content, parent_id, created_by))
        self.conn.commit()

    def get_buttons(self, parent_id=None):
        if parent_id is None:
            self.cursor.execute(
                "SELECT * FROM buttons WHERE parent_id IS NULL AND is_active = 1"
            )
        else:
            self.cursor.execute(
                "SELECT * FROM buttons WHERE parent_id = ? AND is_active = 1",
                (parent_id,)
            )
        return self.cursor.fetchall()
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

def set_user_active(self, telegram_id, is_active: int):
    self.cursor.execute(
        "UPDATE users SET is_active = ? WHERE telegram_id = ?",
        (is_active, telegram_id)
    )
    self.conn.commit()
