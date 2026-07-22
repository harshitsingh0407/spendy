import re

import database.db as db
import database.queries as queries


def _expected_summary():
    """Compute the demo user's expected totals from the seed data itself,
    so these tests stay correct if SAMPLE_EXPENSES ever changes."""
    total = sum(amount for _, amount, _, _ in db.SAMPLE_EXPENSES)
    count = len(db.SAMPLE_EXPENSES)

    category_totals = {}
    for category, amount, _, _ in db.SAMPLE_EXPENSES:
        category_totals[category] = category_totals.get(category, 0) + amount
    top_category = max(category_totals, key=category_totals.get)

    return total, count, top_category, category_totals


def _demo_user_id(db_path):
    row = db.get_user_by_email(db.DEMO_USER["email"])
    return row["id"]


# ------------------------------------------------------------------ #
# Unit tests — database.queries                                       #
# ------------------------------------------------------------------ #

def test_get_user_by_id_returns_profile_fields(db_path):
    user_id = _demo_user_id(db_path)
    user = queries.get_user_by_id(user_id)

    assert user["name"] == db.DEMO_USER["name"]
    assert user["email"] == db.DEMO_USER["email"]
    assert re.match(r"^[A-Z][a-z]+ \d{4}$", user["member_since"])


def test_get_user_by_id_missing_user_returns_none(db_path):
    assert queries.get_user_by_id(999999) is None


def test_get_summary_stats_for_seeded_user(db_path):
    total, count, top_category, _ = _expected_summary()
    user_id = _demo_user_id(db_path)

    summary = queries.get_summary_stats(user_id)

    assert summary["total_spent"] == total
    assert summary["transaction_count"] == count
    assert summary["top_category"] == top_category


def test_get_summary_stats_for_empty_user(db_path):
    new_user_id = db.create_user("New User", "new-user@example.com", "password123")

    summary = queries.get_summary_stats(new_user_id)

    assert summary == {"total_spent": 0, "transaction_count": 0, "top_category": "—"}


def test_get_recent_transactions_for_seeded_user(db_path):
    user_id = _demo_user_id(db_path)

    transactions = queries.get_recent_transactions(user_id)

    assert len(transactions) > 0
    for tx in transactions:
        assert set(tx.keys()) == {"date", "description", "category", "amount"}

    dates = [tx["date"] for tx in transactions]
    assert dates == sorted(dates, reverse=True)


def test_get_recent_transactions_for_empty_user(db_path):
    new_user_id = db.create_user("New User", "new-user2@example.com", "password123")

    assert queries.get_recent_transactions(new_user_id) == []


def test_get_category_breakdown_for_seeded_user(db_path):
    _, _, _, category_totals = _expected_summary()
    user_id = _demo_user_id(db_path)

    breakdown = queries.get_category_breakdown(user_id)

    assert {row["name"] for row in breakdown} == set(category_totals.keys())
    amounts = [row["amount"] for row in breakdown]
    assert amounts == sorted(amounts, reverse=True)

    pcts = [row["pct"] for row in breakdown]
    assert all(isinstance(pct, int) for pct in pcts)
    assert sum(pcts) == 100


def test_get_category_breakdown_for_empty_user(db_path):
    new_user_id = db.create_user("New User", "new-user3@example.com", "password123")

    assert queries.get_category_breakdown(new_user_id) == []


# ------------------------------------------------------------------ #
# Route tests — GET /profile                                          #
# ------------------------------------------------------------------ #

def test_profile_redirects_when_logged_out(client):
    response = client.get("/profile")

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_profile_shows_seeded_user_data(logged_in_client):
    total, count, top_category, category_totals = _expected_summary()

    response = logged_in_client.get("/profile")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Demo User" in body
    assert "demo@spendly.com" in body
    assert "₹" in body
    assert f"₹{total:.2f}" in body
    assert f">{count}<" in body
    assert top_category in body
    for category in category_totals:
        assert category in body


def test_profile_shows_zero_state_for_new_user(client):
    client.post(
        "/register",
        data={
            "name": "Fresh User",
            "email": "fresh-user@example.com",
            "password": "password123",
        },
    )
    client.post(
        "/login",
        data={"email": "fresh-user@example.com", "password": "password123"},
    )

    response = client.get("/profile")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "₹0.00" in body
    assert "No expenses logged yet." in body
