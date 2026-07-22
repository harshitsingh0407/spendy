from datetime import datetime

from database.db import (
    get_user_by_id as _get_user_row,
    get_expense_summary,
    get_category_breakdown as _get_category_rows,
    get_recent_expenses,
)


def get_user_by_id(user_id):
    """Look up a user by id and return profile-safe display fields.

    Returns None if the user doesn't exist.
    """
    row = _get_user_row(user_id)
    if row is None:
        return None

    member_since = datetime.strptime(
        row["created_at"], "%Y-%m-%d %H:%M:%S"
    ).strftime("%B %Y")

    return {
        "name": row["name"],
        "email": row["email"],
        "member_since": member_since,
    }


def get_summary_stats(user_id):
    """Return {total_spent, transaction_count, top_category} for a user."""
    summary = get_expense_summary(user_id)
    if summary["count"] == 0:
        return {"total_spent": 0, "transaction_count": 0, "top_category": "—"}

    breakdown = _get_category_rows(user_id)
    return {
        "total_spent": summary["total"],
        "transaction_count": summary["count"],
        "top_category": breakdown[0]["category"],
    }


def get_recent_transactions(user_id, limit=10):
    """Return a user's most recent expenses, newest first."""
    rows = get_recent_expenses(user_id, limit=limit)
    return [
        {
            "date": row["date"],
            "description": row["description"],
            "category": row["category"],
            "amount": row["amount"],
        }
        for row in rows
    ]


def get_category_breakdown(user_id):
    """Return each category's all-time total and share of spend, highest first.

    Percentages are integers that always sum to exactly 100 — truncated
    per-category, with the largest category absorbing the rounding remainder.
    """
    rows = _get_category_rows(user_id)
    if not rows:
        return []

    total = sum(row["total"] for row in rows)
    if total == 0:
        return [
            {"name": row["category"], "amount": row["total"], "pct": 0}
            for row in rows
        ]

    floor_pcts = [int(row["total"] / total * 100) for row in rows]
    remainder = 100 - sum(floor_pcts)
    floor_pcts[0] += remainder

    return [
        {"name": rows[i]["category"], "amount": rows[i]["total"], "pct": floor_pcts[i]}
        for i in range(len(rows))
    ]
