import os
import sqlite3
from datetime import date

from werkzeug.security import generate_password_hash

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "expense_tracker.db")


class DuplicateEmailError(Exception):
    """Raised by create_user() when the email is already registered."""


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                date TEXT NOT NULL,
                description TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        conn.commit()
    finally:
        conn.close()


def create_user(name, email, password):
    """Create a new user with a securely hashed password.

    Returns the new user's id. Raises DuplicateEmailError if the
    email is already registered.
    """
    password_hash = generate_password_hash(password)
    conn = get_db()
    try:
        cursor = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, password_hash),
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        raise DuplicateEmailError(f"email '{email}' is already registered") from None
    finally:
        conn.close()


DEMO_USER = {
    "name": "Demo User",
    "email": "demo@spendly.com",
    "password": "demo123",
}

# (category, amount, description, day_of_month)
# Days kept <= 24 so every value is valid in any month, spread across the
# current month. Food appears twice to reach 8 rows across 7 categories.
SAMPLE_EXPENSES = [
    ("Food", 42.50, "Groceries", 2),
    ("Transport", 18.00, "Bus pass", 4),
    ("Bills", 120.00, "Electricity bill", 5),
    ("Health", 60.00, "Pharmacy", 8),
    ("Entertainment", 15.99, "Movie ticket", 11),
    ("Shopping", 89.99, "New shoes", 14),
    ("Other", 25.00, "Miscellaneous", 18),
    ("Food", 22.30, "Dinner out", 21),
]


def seed_db():
    conn = get_db()
    try:
        row = conn.execute("SELECT COUNT(*) AS count FROM users").fetchone()
        if row["count"] > 0:
            return

        password_hash = generate_password_hash(DEMO_USER["password"])
        cursor = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (DEMO_USER["name"], DEMO_USER["email"], password_hash),
        )
        user_id = cursor.lastrowid

        today = date.today()
        for category, amount, description, day in SAMPLE_EXPENSES:
            expense_date = today.replace(day=day).isoformat()
            conn.execute(
                """
                INSERT INTO expenses (user_id, amount, category, date, description)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, amount, category, expense_date, description),
            )

        conn.commit()
    finally:
        conn.close()
