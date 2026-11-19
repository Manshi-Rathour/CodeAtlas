# CodeAtlas

CodeAtlas is a full-stack codebase understanding platform. Import a project from a ZIP archive or a public GitHub repository, analyze it locally, and explore its files, architecture, dependencies, detected HTTP APIs, AI-generated documentation and an AI chat assistant that answers questions about the code.

The application runs entirely on your machine. Imported code is scanned as text and is **never executed**.

---

## Features

### Project import

- ZIP upload with safe extraction (path traversal and archive-size protection).
- Public GitHub repository import through the GitHub archive API.
- Imported files are inventoried in PostgreSQL with language, size and path metadata.
- Deleting a project also removes its extracted source folder.

### Code intelligence

- Symbol extraction (functions, methods, classes) for supported languages using tree-sitter.
- Searchable code chunks for retrieval.
- Import and dependency extraction, including resolved internal file references and external libraries.
- Framework, language, library and database detection from manifests and imports.
- Architecture summary with an optional local-AI explanation.
- Internal dependency graph (files as nodes, resolved imports as edges).
- HTTP API endpoint detection for Flask, FastAPI, Django, Express, NestJS, Next.js, Spring, Go, PHP/Laravel, Ruby on Rails, ASP.NET, Rust, Swift and Phoenix source patterns.
- Project metrics: files, bytes, languages, symbols, chunks, resolved dependencies, API endpoints, conversations and documentation status.

### AI features (local Ollama)

- Codebase chat with retrieval over analyzed code chunks and conversation history.
- Generated project documentation with setup files (README, dependency manifests, Procfile, Docker files and similar) supplied as grounding context.
- Documentation is sanitized before it is returned: Markdown links are reduced to plain text, images are removed, and boilerplate License/Contributing sections are dropped. Fenced code blocks with real commands are preserved.

### Frontend

- React 19 + Vite single-page application.
- Dashboard with project summaries (file counts fetched in one request).
- File explorer with a nested folder tree, language filter and search.
- Architecture, documentation, dependency graph, chat and APIs & Metrics pages for every project.
- JWT authentication with protected routes.

---

## Architecture

```text
CodeAtlas/
├── backend/                 FastAPI application
│   ├── alembic/             Database migrations
│   ├── app/
│   │   ├── api/routes/      HTTP routers
│   │   ├── core/            Settings and security helpers
│   │   ├── database/        SQLAlchemy engine and session
│   │   ├── models/          ORM models
│   │   ├── schemas/         Pydantic request/response schemas
│   │   ├── services/        Import, analysis, AI and documentation logic
│   │   └── storage/         Extracted project sources (git-ignored)
│   └── tests/               Pytest suite
├── frontend/                React + Vite application
│   └── src/
│       ├── components/      Shared UI components
│       ├── context/         Auth context
│       ├── pages/           Route-level pages
│       └── services/        Axios API clients
└── docker-compose.yml       Local PostgreSQL service
```

The backend keeps a clear separation between routers, services and persistence. Each service receives the SQLAlchemy session and the owning project, and every project route verifies ownership before returning data.

---

## Technology stack

| Layer | Technology |
| --- | --- |
| Backend | Python, FastAPI, SQLAlchemy 2, Alembic, Pydantic v2 |
| Database | PostgreSQL 17 |
| Authentication | JWT (PyJWT) with Argon2 password hashing |
| Parsing | tree-sitter language pack |
| AI | Local Ollama server (`qwen2.5-coder:7b` by default) |
| Frontend | React 19, React Router, Vite, Axios |
| Visualization | React Flow (`@xyflow/react`), Monaco Editor |
| Testing | Pytest, HTTPX, FastAPI TestClient |

---

## Prerequisites

- Python 3.11 or newer
- Node.js 20 or newer (with npm)
- Docker (recommended for PostgreSQL) or an existing PostgreSQL 17 instance
- Ollama installed and running locally, if you want chat and documentation features

---

## Setup

### 1. Start PostgreSQL

Create a root `.env` file from the example and choose local credentials:

```bash
cp .env.example .env
```

Then start the database container:

```bash
docker compose up -d db
```

This exposes PostgreSQL on the port set by `POSTGRES_PORT` (default `5432`) and persists data in the `postgres_data` volume.

### 2. Configure the backend

```bash
cd backend
cp .env.example .env
```

Edit `backend/.env` so `DATABASE_URL` matches the credentials in the root `.env`. Set `SECRET_KEY` to a long random string. The full variable list:

| Variable | Purpose | Default |
| --- | --- | --- |
| `DATABASE_URL` | PostgreSQL connection string | required |
| `SECRET_KEY` | JWT signing key | development placeholder |
| `ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime | `30` |
| `UPLOAD_DIR` | Extracted project storage, relative to `backend/` | `app/storage/projects` |
| `MAX_UPLOAD_SIZE_MB` | ZIP upload limit | `100` |
| `OLLAMA_URL` | Local Ollama server | `http://localhost:11434` |
| `OLLAMA_MODEL` | Model used for chat and documentation | `qwen2.5-coder:3b` |

### 3. Install backend dependencies

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

On Windows, activate the virtual environment with `venv\Scripts\activate`.

### 4. Run database migrations

From `backend/` with the virtual environment active:

```bash
alembic upgrade head
```

### 5. Start the backend

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Useful endpoints:

- API root: `http://127.0.0.1:8000/`
- Health check: `http://127.0.0.1:8000/health`
- Database health: `http://127.0.0.1:8000/health/database`
- Interactive API docs: `http://127.0.0.1:8000/docs`

### 6. Start the frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`.

The API client reads `VITE_API_BASE_URL` and falls back to `http://127.0.0.1:8000`. To point the frontend at another backend, create `frontend/.env`:

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000
```

### 7. Prepare Ollama (optional)

Chat, architecture explanations and generated documentation call a local model:

```bash
ollama pull qwen2.5-coder:7b
ollama serve
```

Set `OLLAMA_MODEL` in `backend/.env` if you use a different model. Other features (import, analysis, file browsing, API detection, metrics) work without Ollama.

---

## Testing

The backend suite uses an in-memory SQLite database, so it does not touch your PostgreSQL data:

```bash
cd backend
source venv/bin/activate
python -m pytest -q
```

Current result on this machine:

```text
210 passed, 1 skipped
```

The skipped test is an opt-in live Ollama integration test. It runs only when Ollama is explicitly enabled for the test session; unit tests mock the AI service so the suite stays fast and deterministic.

Frontend checks:

```bash
cd frontend
npm run lint
npm run build
```

`npm run build` produces a production bundle in `frontend/dist/`. Vite reports a chunk-size warning because the application is a single bundle; this is a known optimization opportunity, not a build failure.

---

## API overview

All project routes require a Bearer token and return only the caller's own projects.

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/api/auth/signup` | Create an account |
| `POST` | `/api/auth/login` | Obtain a JWT |
| `GET` | `/api/auth/me` | Current user |
| `GET` / `POST` | `/api/projects/` | List or create projects |
| `GET` | `/api/projects/summary` | Projects with file counts |
| `GET` / `PATCH` / `DELETE` | `/api/projects/{id}` | Read, update or delete a project |
| `POST` | `/api/uploads/zip` | Import a ZIP archive |
| `POST` | `/api/github/import` | Import a public GitHub repository |
| `POST` | `/api/projects/{id}/analyze` | Run code analysis |
| `GET` | `/api/projects/{id}/analysis` | Symbols, dependencies and technologies |
| `GET` | `/api/projects/{id}/files` | Paginated file inventory |
| `GET` | `/api/projects/{id}/file-tree` | Nested folder tree |
| `GET` | `/api/projects/{id}/files/{file_id}/content` | File source content |
| `GET` | `/api/projects/{id}/architecture` | Architecture summary and optional AI explanation |
| `GET` | `/api/projects/{id}/graph` | Internal dependency graph |
| `GET` | `/api/projects/{id}/apis` | Detected HTTP endpoints |
| `GET` | `/api/projects/{id}/metrics` | Project metrics |
| `POST` | `/api/projects/{id}/chat` | Ask a question about the codebase |
| `GET` | `/api/projects/{id}/chats` | Conversation list |
| `GET` | `/api/projects/{id}/chats/{conversation_id}` | Conversation messages |
| `POST` / `GET` | `/api/projects/{id}/documentation` | Generate or read documentation |
| `GET` | `/api/projects/{id}/documentation/status` | Documentation status |

---

## Security notes

- Imported code is parsed and searched as text; it is never imported or executed.
- ZIP extraction validates archive members and blocks unsafe paths and oversized archives.
- Project storage folders are resolved inside the configured upload area, and deletion only removes the owner's own import folder.
- Every project endpoint checks project ownership and returns `404` for projects the caller does not own.
- Uploaded files are scanned with a sensitive-file filter before route detection reads them.
- Secrets are read from environment files that are git-ignored; no credentials are committed.

---

## Known limitations

- API endpoint detection is pattern-based. Routes created dynamically or through unsupported frameworks may not be found.
- Framework detection depends on manifest and import evidence; a library listed in a manifest is not treated as the project's web framework.
- Generated documentation and chat answers depend on the local model. Output can be incomplete or contain mistakes even though setup context is supplied; the documentation view strips links and boilerplate sections, not factual errors.
- The dependency graph currently covers internal resolved file references; external packages are shown in the dependencies list but not as graph nodes.
- The frontend is built as a single bundle, so the initial download is larger than ideal.
- There is no browser-based end-to-end test suite in the repository; verification is done through the backend API and manual UI checks.

---

## Development notes

- Database schema changes should go through Alembic (`alembic revision --autogenerate -m "..."` from `backend/`).
- Keep new project routes behind `get_current_user` and verify ownership before reading project data.
- Backend tests live in `backend/tests/` and use fixtures from `conftest.py`.
- Imported project sources live under `backend/app/storage/projects/` and are excluded from version control.
