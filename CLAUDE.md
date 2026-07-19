# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Spendly is a personal expense-tracking web app built as a learning project (Flask backend, server-rendered Jinja2 templates, vanilla JS/CSS — no frontend framework, no build step). Several core pieces are intentionally unfinished stubs left for future implementation steps (see Architecture below); don't assume missing functionality is a bug.

## Commands

Run all commands from the repo root with the virtualenv active.

```bash
# Setup
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt

# Run the app (http://localhost:5001)
python app.py

# Run tests (pytest + pytest-flask are installed, but no tests exist yet)
pytest
pytest path/to/test_file.py::test_name   # single test
```

There is no linter, formatter, or JS/CSS build step configured in this project.

## Architecture

- **`app.py`** — single-file Flask app. All routes are defined here directly on `app` (no blueprints). Routes fall into two groups:
  - Implemented pages: `/`, `/register`, `/login`, `/terms`, `/privacy` — each just does `render_template(...)`.
  - Placeholder routes (`/logout`, `/profile`, `/expenses/add`, `/expenses/<id>/edit`, `/expenses/<id>/delete`) — return plain strings marking them as "coming in Step N". These are scaffolding for a step-by-step build-out (auth, then expense CRUD) — implement real behavior only when asked to build that step, and follow the existing route naming/shape when you do.
  - Dev server runs on port **5001**, `debug=True`.

- **`database/`** — SQLite data layer, not yet implemented.
  - `db.py` currently only has a comment contract: it must eventually expose `get_db()` (SQLite connection with `row_factory` and foreign keys enabled), `init_db()` (creates tables with `CREATE TABLE IF NOT EXISTS`), and `seed_db()` (sample data for dev). Implement against this contract rather than inventing a different shape.
  - `__init__.py` is empty.
  - The SQLite file itself (`expense_tracker.db`) is gitignored and created at runtime.

- **`templates/`** — Jinja2 templates, all extending `templates/base.html`.
  - `base.html` defines the shared shell: nav (brand, sign in, get started), a `{% block content %}` for page body, and a footer with Terms/Privacy links. It links `static/css/style.css` globally and `static/js/main.js` at the bottom of `<body>`.
  - Page templates add their own stylesheet via `{% block head %}` (e.g. `landing.html` pulls in `landing.css` for hero/dashboard-mock styling) and override `{% block title %}` / `{% block content %}`.
  - Always use `url_for('endpoint')` for internal links/assets rather than hardcoded paths, matching the existing templates.

- **`static/css/`** — `style.css` holds global/shared styles (nav, footer, base typography); page-specific styles (e.g. `landing.css`) are split out and loaded only by the pages that need them. Follow this split when adding new pages instead of dumping everything into `style.css`.

- **`static/js/main.js`** — currently an empty placeholder; JS is added here incrementally per-feature (e.g. the "See how it works" modal), vanilla JS only, no libraries/frameworks.

## Working conventions specific to this repo

- This project builds features in discrete, numbered steps (auth, then expense add/edit/delete, etc.) — `app.py`'s placeholder route comments and `database/db.py`'s stub comment are the source of truth for what's expected next.
- When editing a page (e.g. hero section, a modal, a footer link), scope changes tightly to what's asked — this codebase has a history of narrowly-scoped, single-purpose commits (e.g. "add terms and privacy links to footer", "redesign hero section to match mockup") and expects the same discipline: don't touch unrelated markup/CSS/routes in the same change.
