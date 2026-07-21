# Spec: Login and Logout

## Overview
This feature implements session-based authentication for Spendly. It turns the existing `/login` page — currently a static GET-only template render — into a working sign-in flow: submitting the form checks the email/password against the `users` table and, on success, starts a Flask session. It also turns the `/logout` placeholder into a real route that clears that session. This is the second step in the auth sequence (after Step 2 registration) and the foundation that later steps (profile, expense CRUD) depend on to know which user is currently signed in.

## Depends on
- Step 1 — Database setup (`database/db.py`: `get_db()`, `users` table schema)
- Step 2 — Registration (`create_user()`, hashed passwords already being written to `users`)

## Routes
- `GET /login` — render the login form, or redirect to `/` if already logged in — public
- `POST /login` — validate submitted email/password against `users`, start a session on success, redirect to `/` (landing page) on success or re-render `login.html` with an error on failure — public
- `GET /logout` — clear the session and redirect to `/login` — logged-in

## Database changes
No database changes. Session state is stored in the signed Flask session cookie (the user's `id`), not in a new table. Verified against `database/db.py` — the existing `users` table (`id`, `name`, `email`, `password_hash`, `created_at`) has everything needed to look up and verify a user.

## Templates
- **Create:** none
- **Modify:** `templates/base.html` — nav currently always shows "Sign in" / "Get started". Make it conditional on session state: when a user is logged in, show a "Sign out" link (`url_for('logout')`) in place of those two links; otherwise keep the existing links unchanged.
- `templates/login.html` — no change needed; it already posts `email`/`password` to `/login` and already renders an `{% if error %}` block.

## Files to change
- `app.py` — set `app.secret_key` (required for signed sessions; a hardcoded dev value is fine at this stage, matching the project's no-env-config simplicity); change `login()` to accept `["GET", "POST"]`, verify credentials via the new lookup helper and `werkzeug.security.check_password_hash`, store `user_id` in `session` on success, redirect to `url_for('profile')`, or re-render `login.html` with an error on failure; implement `logout()` to call `session.clear()` and redirect to `url_for('login')`
- `database/db.py` — add a `get_user_by_email(email)` helper that runs a parameterised `SELECT` and returns the row (or `None`)
- `database/__init__.py` — export `get_user_by_email` alongside the existing helpers

## Files to create
None

## New dependencies
No new dependencies (uses Flask's built-in `session` and the already-installed `werkzeug.security.check_password_hash`)

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed with werkzeug (verify with `check_password_hash`, never compare plaintext)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Do not build the real `/profile` page here — it stays an unchanged placeholder string response; because it isn't rendered through `base.html`, it can't show the nav yet, so `/` (landing page) is the post-login redirect target instead
- Don't touch the `/expenses/*` placeholder routes — out of scope for this step

## Definition of done
- [ ] Visiting `/login` still renders the existing form unchanged (GET)
- [ ] Submitting the seeded demo user's credentials (`demo@spendly.com` / `demo123`) logs in successfully and redirects to `/`
- [ ] Submitting a correct email with the wrong password re-renders `login.html` with an error and does not start a session
- [ ] Submitting an email that doesn't exist in `users` re-renders `login.html` with an error (without revealing whether the email exists)
- [ ] After logging in, the nav bar shows "Sign out" instead of "Sign in" / "Get started" on every page
- [ ] Visiting `/logout` while logged in clears the session and redirects to `/login`, after which the nav reverts to "Sign in" / "Get started"
- [ ] Visiting `/login` while already logged in redirects to `/` instead of showing the form
- [ ] App starts and runs without errors after the change (`python app.py`)
