# Spec: Registration

## Overview
This feature implements user account creation for Spendly. It builds directly on the Step 1 database layer (`users` table) and turns the existing `/register` page — currently a static GET-only template render — into a working signup flow: submitting the form validates input, hashes the password, inserts a new row into `users`, and sends the visitor to the login page. This is the first step in the auth sequence that later steps (login, logout, profile) depend on.

## Depends on
- Step 1 — Database setup (`database/db.py`: `get_db()`, `init_db()`, `users` table schema)

## Routes
- `GET /register` — render the registration form (already implemented, unchanged) — public
- `POST /register` — validate submitted name/email/password, create the user, redirect to `/login` on success or re-render the form with an error on failure — public

## Database changes
No database changes. The existing `users` table (`id`, `name`, `email`, `password_hash`, `created_at`) already has every column registration needs. Verified against `database/db.py`.

## Templates
- **Create:** none
- **Modify:** none — `templates/register.html` already posts to `/register` with `name`, `email`, `password` fields and already renders an `{% if error %}` block, so it works unchanged once the route handles `POST`

## Files to change
- `app.py` — change `register()` to accept `["GET", "POST"]`, validate form input, call the new user-creation helper, handle duplicate-email and validation errors by re-rendering `register.html` with `error`, and redirect to `url_for('login')` on success
- `database/db.py` — add a small helper (e.g. `create_user(name, email, password)`) that hashes the password with `werkzeug.security.generate_password_hash` and inserts the row, raising/handling `sqlite3.IntegrityError` for duplicate emails
- `database/__init__.py` — export the new helper alongside `get_db`, `init_db`, `seed_db`

## Files to create
None

## New dependencies
No new dependencies

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed with werkzeug
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Do not implement login/session handling here — registration only creates the account and redirects to `/login`; logging the user in is out of scope for this step
- Validate on the server even though the form has HTML5 `required`/`type=email` attributes (name non-empty, email format, password length ≥ 8, email not already registered)

## Definition of done
- [ ] Visiting `/register` still renders the existing form unchanged
- [ ] Submitting valid name/email/password creates a new row in the `users` table with a hashed (not plaintext) password
- [ ] After successful registration, the browser is redirected to `/login`
- [ ] Submitting an email that already exists in `users` re-renders `register.html` with an error message and does not create a duplicate row
- [ ] Submitting a password shorter than 8 characters, or a missing name/email, re-renders `register.html` with an error and does not insert a row
- [ ] App starts and runs without errors after the change (`python app.py`)
