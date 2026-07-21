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
                monthly_budget REAL NOT NULL DEFAULT 20000,
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

        existing_columns = {
            row["name"] for row in conn.execute("PRAGMA table_info(users)")
        }
        if "monthly_budget" not in existing_columns:
            conn.execute(
                "ALTER TABLE users ADD COLUMN monthly_budget REAL NOT NULL DEFAULT 20000"
            )

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


def get_user_by_email(email):
    """Look up a user by email. Returns a Row (or None if not found)."""
    conn = get_db()
    try:
        return conn.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()
    finally:
        conn.close()


def get_user_by_id(user_id):
    """Look up a user by id. Returns a Row (or None if not found)."""
    conn = get_db()
    try:
        return conn.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    finally:
        conn.close()


def get_expense_summary(user_id):
    """Return {count, total} all-time spend stats for a user."""
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT COUNT(*) AS count, COALESCE(SUM(amount), 0) AS total "
            "FROM expenses WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        return {"count": row["count"], "total": row["total"]}
    finally:
        conn.close()


def get_category_breakdown(user_id):
    """Return each category's all-time total for a user, highest first."""
    conn = get_db()
    try:
        return conn.execute(
            "SELECT category, SUM(amount) AS total FROM expenses "
            "WHERE user_id = ? GROUP BY category ORDER BY total DESC",
            (user_id,),
        ).fetchall()
    finally:
        conn.close()


def get_recent_expenses(user_id, limit=10):
    """Return a user's most recent expenses, newest first."""
    conn = get_db()
    try:
        return conn.execute(
            "SELECT date, description, category, amount FROM expenses "
            "WHERE user_id = ? ORDER BY date DESC, id DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    finally:
        conn.close()


DEMO_USER = {
    "name": "Demo User",
    "email": "demo@spendly.com",
    "password": "demo123",
}

# (category, amount, description, day_of_month)
# Days kept <= 24 so every value is valid in any month, spread across the
# current month. Two entries per category (14 rows) so the profile page's
# stats and category breakdown look populated out of the box.
SAMPLE_EXPENSES = [
    ("Food", 450.00, "Groceries", 2),
    ("Food", 320.50, "Dinner out", 21),
    ("Food", 180.00, "Coffee & snacks", 15),
    ("Transport", 550.00, "Fuel", 4),
    ("Transport", 120.00, "Metro card recharge", 11),
    ("Bills", 2200.00, "Electricity bill", 5),
    ("Bills", 899.00, "Internet bill", 9),
    ("Health", 750.00, "Pharmacy", 8),
    ("Health", 1200.00, "Doctor visit", 18),
    ("Entertainment", 649.00, "Netflix subscription", 6),
    ("Entertainment", 899.00, "Movie night", 14),
    ("Shopping", 3200.00, "New shoes & clothes", 12),
    ("Shopping", 1499.00, "Headphones", 20),
    ("Other", 450.00, "Miscellaneous", 24),
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
