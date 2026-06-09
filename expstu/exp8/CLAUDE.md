# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is **Experiment 8** of a university recommendation systems course — a simple web community for sharing and favoriting PDF/Markdown files. It consists of a single-file FastAPI backend (`exp8codes/webmain.py`) and a jQuery/Bootstrap SPA frontend (`exp8codes/static/index.html`).

## Commands

```bash
# Activate the virtual environment
source venv/bin/activate

# Start the development server
cd exp8codes && python webmain.py
# Server runs at http://0.0.0.0:5246

# Install dependencies (first-time setup)
python -m pip install fastapi uvicorn sqlmodel python-multipart

# Export current dependency list
python -m pip freeze > requirements.txt
```

## Architecture

**Backend** (`exp8codes/webmain.py`, ~350 lines):

- **Framework**: FastAPI with `lifespan` context manager that creates directories and initializes SQLite tables on startup.
- **ORM**: SQLModel (SQLAlchemy + Pydantic) with three tables: `User`, `Post`, `Favor`.
- **Auth**: Custom bearer token scheme via `OAuth2PasswordBearer`. Tokens expire after 7 days. Users whose username starts with `"admin"` get `userclass="admin"` on registration.
- **File storage**: Uploaded files (`.pdf` or `.md`) are saved to `data/post/{postid}/main/main{ext}` and served via FastAPI's `StaticFiles` mount at `/post`.
- **API routes** (all prefixed with `/user/`):
  - `POST /user/register` — register with username/password (min 5 chars each)
  - `POST /user/login` — login, returns bearer token
  - `POST /user/userinfo` — get current user info from token
  - `POST /user/getposts` — list posts with scope/ordering/pagination (token optional)
  - `POST /user/setpost` — delete (own or admin) or toggle favor on a post
  - `POST /user/uploadfile` — upload a PDF or MD file

**Frontend** (`exp8codes/static/index.html`, ~970 lines):

- Single-page application using jQuery 1.12, Bootstrap 3.3, jQuery Cookie, and marked.js.
- Renders uploaded Markdown files in-browser. PDF files are displayed via browser's native PDF viewer.
- Warm-toned, custom CSS design with Chinese font stack (`PingFang SC`, `Microsoft YaHei`).

**Data layer**:

- SQLite database at `data/sqlite_database.db` (auto-created on startup).
- Uploaded files stored under `data/post/` directory tree.
- Note: there are two `data/` directories — one inside `exp8codes/` and one at the project root. The code uses the one inside `exp8codes/` (configured via `BASE_DIR`).

## Key Design Details

- Passwords are stored in **plain text** (no hashing) — this is a course lab, not production code.
- The `/user/getposts` endpoint accepts an **optional** token — unauthenticated users can browse, authenticated users also see their own favor status per post.
- The `Favor` table stores a copy of `rdir` (redundant denormalization) alongside `userid` and `postid`.
- Registration auto-assigns `userclass`: usernames starting with `"admin"` → `"admin"`, all others → `"normal"`.
