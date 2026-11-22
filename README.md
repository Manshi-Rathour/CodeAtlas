# CodeAtlas

CodeAtlas is a codebase intelligence platform. Import a project from a ZIP archive or a public GitHub repository, analyze it on your machine, and explore its files, symbols, architecture, dependencies, detected HTTP APIs, metrics, generated documentation, and an AI assistant that answers questions about the code.

## Overview

![CodeAtlas landing page](Webpage_images/landingpage.png)

CodeAtlas helps developers understand unfamiliar repositories by transforming ZIP files or public GitHub repositories into searchable, interactive codebase maps.

1. Import a project through ZIP or GitHub.
2. Inventory files and analyze code to extract symbols, chunks, imports, dependencies, and technologies.
3. Explore the codebase through:
   - File explorer and Monaco source viewer
   - Architecture overview and dependency graph
   - API endpoints and project metrics
   - AI-generated documentation
   - Retrieval-based AI chat with source citations
4. Deleting a project or account also removes its stored project files.

The platform runs locally using PostgreSQL, FastAPI, React, and optional Ollama for AI features.

## Features

### Authentication and Account

![Login page](Webpage_images/login.png)

![Signup page](Webpage_images/signup.png)
- JWT-based signup and login with Argon2 password hashing.
- Protected routes and session validation.
- Profile management, password changes, and account deletion.

### Project Import

![Project upload](Webpage_images/upload.png)
- Secure ZIP extraction with path traversal, symlink, and size protections.
- Public GitHub repository import with branch selection.
- File metadata and per-user project storage in PostgreSQL and local storage.

### Code Intelligence
- Tree-sitter-based extraction of functions, classes, methods, and code chunks.
- Import and dependency analysis, including internal references and external libraries.
- Detection of languages, frameworks, databases, and technologies.
- Architecture summaries and interactive dependency graphs.
- HTTP API endpoint detection across multiple frameworks.
- Project metrics covering files, symbols, dependencies, endpoints, and AI activity.
- Sensitive-file filtering during source analysis.

### AI Features (Optional Ollama)
- **Codebase Chat:** Retrieval-based answers with conversation history and file/line citations.
- **Documentation Generation:** Creates project documentation using source files, manifests, and setup configurations.
- **Architecture Explanation:** Generates on-demand AI explanations with browser-side caching.

### Frontend Experience

![Dashboard](Webpage_images/dashboard.png)

![All projects](Webpage_images/allprojects.png)

![Project overview](Webpage_images/projectOverview1.png)

![Project overview details](Webpage_images/projectOverview2.png)

![File explorer and source viewer](Webpage_images/files.png)

![Architecture overview](Webpage_images/architecture1.png)

![Architecture details](Webpage_images/architecture2.png)

![Dependency graph](Webpage_images/graph.png)

![API explorer](Webpage_images/api1.png)

![API details](Webpage_images/api2.png)

![Generated documentation](Webpage_images/documentation.png)

![AI codebase chat](Webpage_images/aichat.png)

![User profile](Webpage_images/profile.png)
- Dashboard with project summaries and analysis status.
- Searchable file explorer with nested folders and language filters.
- Monaco-based source viewer and React Flow dependency graph.
- Dedicated pages for architecture, documentation, chat, APIs, metrics, and profiles.

### Request flow

```text
React page
   │  Axios (Bearer JWT)
   ▼
FastAPI router  ──verifies user + project ownership──► SQLAlchemy session
   │
   ▼
Service layer
   ├── source/         import + extract + delete local folders
   ├── analysis/       read source text, build symbols/chunks/dependencies
   ├── architecture/   database facts + optional Ollama explanation
   ├── documentation/  retrieve grounding context + Ollama + sanitize
   └── ai/             retrieve chunks + conversation history + Ollama
```

### Database tables

| Table | Purpose |
| --- | --- |
| `users` | Accounts, hashed passwords and activation flag |
| `projects` | Project metadata, source type, status and local source path |
| `project_files` | File inventory with language, size and relative path |
| `code_symbols` | Extracted functions, methods, classes and other symbols |
| `code_chunks` | Searchable source chunks for retrieval |
| `dependencies` | Imports and resolved internal file references |
| `chats` | Conversation messages (user/assistant) with source references |
| `project_documentations` | Generated documentation content per project |

### Local storage layout

```text
backend/app/storage/projects/
└── <user_id>/
    └── <storage_id>/            UUID folder per imported project
        └── source/              Extracted ZIP/GitHub source
```

- Project deletion removes its `<storage_id>` folder.
- Deleting the last project also removes the now-empty `<user_id>` folder.
- Account deletion removes the entire `<user_id>` folder.
- All cleanup paths are resolved and constrained to the configured upload directory.


## Technology stack

| Layer | Technology |
| --- | --- |
| Backend framework | Python, FastAPI, Uvicorn |
| ORM and migrations | SQLAlchemy 2, Alembic |
| Database | PostgreSQL 17 (Docker Compose) |
| Validation | Pydantic v2, pydantic-settings, email-validator |
| Authentication | PyJWT (HS256), `pwdlib[argon2]` |
| Parsing | `tree-sitter-language-pack` |
| Source import | `requests` (GitHub archive API), `python-multipart` (uploads) |
| AI | Local Ollama server (`qwen2.5-coder:7b` in `.env.example`) |
| Frontend | React 19, React Router 7, Vite 8 |
| HTTP client | Axios |
| UI and icons | Lucide React, hand-written CSS, Tailwind CSS 4 (Vite plugin) |
| Visualization | React Flow (`@xyflow/react`), Monaco Editor |
| Markdown | `react-markdown` |
| Testing | Pytest, HTTPX, FastAPI TestClient, Vitest (installed) |
| Linting | oxlint |


## Prerequisites

- **Python 3.11+**
- **Node.js 20+** and npm
- **Docker** (recommended for PostgreSQL) or an existing PostgreSQL 17 instance
- **Ollama** (optional) for chat, documentation and architecture explanations


## Setup

### 1. Clone and start PostgreSQL

From the repository root:

```bash
cp .env.example .env
```

Edit `.env` and choose local database credentials, then start the database:

```bash
docker compose up -d db
```

PostgreSQL is exposed on `${POSTGRES_PORT:-5432}` and persisted in the `postgres_data` Docker volume.

If you already run PostgreSQL locally, skip Docker and point `DATABASE_URL` at that instance instead.

### 2. Configure the backend

```bash
cd backend
cp .env.example .env
```

Edit `backend/.env`:

- set `DATABASE_URL` to match the credentials from the root `.env`,
- set `SECRET_KEY` to a long random string.

See [Configuration](#configuration) for every variable.

### 3. Install backend dependencies

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

On Windows, activate with `venv\Scripts\activate`.

### 4. Run database migrations

```bash
alembic upgrade head
```

Run this from `backend/` with the virtual environment active. Re-run it after pulling new migrations.

### 5. Start the backend

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 6. Start the frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`.

The API client reads `VITE_API_BASE_URL` and falls back to `http://127.0.0.1:8000`. To point it elsewhere, create `frontend/.env`:

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000
```

### 7. Prepare Ollama (optional)

Chat, architecture explanations and generated documentation call a local model:

```bash
ollama pull qwen2.5-coder:7b
ollama serve
```

Set `OLLAMA_MODEL` in `backend/.env` to use a different model. Import, analysis, file browsing, API detection and metrics work without Ollama; AI-dependent actions return a `503` when the server or model is unavailable.

### 8. Create an account

Open the frontend, sign up, and import a ZIP or public GitHub repository from the dashboard.


## Configuration

### Backend (`backend/.env`)

| Variable | Purpose | Default |
| --- | --- | --- |
| `DATABASE_URL` | PostgreSQL connection string | required |
| `SECRET_KEY` | JWT signing key; use a long random value | development placeholder |
| `ALGORITHM` | JWT signing algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access-token lifetime in minutes | `30` |
| `UPLOAD_DIR` | Extracted project storage, relative to `backend/` | `app/storage/projects` |
| `MAX_UPLOAD_SIZE_MB` | Maximum ZIP upload size | `100` |
| `OLLAMA_URL` | Local Ollama base URL | `http://localhost:11434` |
| `OLLAMA_MODEL` | Model used for chat, docs and explanations | `qwen2.5-coder:3b` (config default; `.env.example` uses `7b`) |

### Root `.env` (Docker Compose)

| Variable | Purpose | Default |
| --- | --- | --- |
| `POSTGRES_DB` | Database name | `your-codeatlas-db` |
| `POSTGRES_USER` | Database user | `your-codeatlas-db-user` |
| `POSTGRES_PASSWORD` | Database password | `choose-a-local-password ` |
| `POSTGRES_PORT` | Host port for PostgreSQL | `5432` |

### Frontend (`frontend/.env`, optional)

| Variable | Purpose | Default |
| --- | --- | --- |
| `VITE_API_BASE_URL` | Backend base URL | `http://127.0.0.1:8000` |

Environment files are git-ignored. Never commit real secrets.


## Using the application

1. **Sign up or log in.** The JWT is stored in `localStorage`.
2. **Import a project** from the dashboard:
   - upload a `.zip` file, or
   - paste a public GitHub repository URL and optional branch.
3. **Open the project** from the dashboard or **My Projects**.
4. **Run codebase analysis** from the project **Overview** page before exploring. While a project has not been analyzed, the Overview shows a notice pointing to the **Codebase Analysis** section; dependencies, detected APIs, metrics, architecture details and the graph stay empty until **Run Analysis** completes.
5. **Explore:**
   - **Overview** – languages, frameworks, counts, extracted symbols and the analysis action.
   - **Files** – folder tree, file list, filters and source viewer.
   - **Architecture** – structural facts and an optional AI explanation.
   - **Documentation** – generate or read AI documentation.
   - **Dependencies** – internal import graph.
   - **Chat** – ask questions; answers cite source files and line ranges.
   - **APIs & Metrics** – detected HTTP endpoints and project statistics.
6. **Manage your account** by clicking your email/avatar in the topbar or your user block in the sidebar:
   - update your display name,
   - change your password,
   - delete your account.
7. **Delete a project** from its page or the project list. Its extracted source folder is removed from local storage. Deleting your account removes all owned projects and the entire per-user storage folder.


## API reference

### Conventions

- Base URL: `http://127.0.0.1:8000`
- Protected endpoints require:

  ```http
  Authorization: Bearer <access_token>
  ```

- Project-scoped endpoints only return data for projects owned by the caller; otherwise they return `404`.
- Request and response bodies are JSON unless noted as multipart.
- Validation errors return `422`.
- AI-dependent endpoints return `503` when Ollama is unavailable.
- Interactive, always-current documentation is available at `/docs`.

### Health and root

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| `GET` | `/` | No | Application name and running status |
| `GET` | `/health` | No | Application health |
| `GET` | `/health/database` | No | PostgreSQL connectivity (`503` on failure) |

### Authentication

| Method | Path | Auth | Body / notes |
| --- | --- | --- | --- |
| `POST` | `/api/auth/signup` | No | `{ "full_name": "...", "email": "...", "password": "..." }` → `201` with user + token |
| `POST` | `/api/auth/login` | No | `{ "email": "...", "password": "..." }` → user + token |
| `GET` | `/api/auth/me` | Yes | Current user: `id`, `full_name`, `email`, `is_active`, `created_at` |


### Users and profile

| Method | Path | Auth | Body / notes |
| --- | --- | --- | --- |
| `PATCH` | `/api/users/me` | Yes | `{ "full_name": "New Name" }`; returns the updated user |
| `POST` | `/api/users/me/password` | Yes | `{ "current_password": "...", "new_password": "..." }`; current password is required and reuse is rejected |
| `DELETE` | `/api/users/me` | Yes | Permanently deletes the account, owned projects and local storage |

No email verification is involved in password changes. After account deletion, the existing JWT no longer resolves to a user.

### Projects

| Method | Path | Auth | Body / notes |
| --- | --- | --- | --- |
| `POST` | `/api/projects/` | Yes | `{ "name", "description?", "source_type?", "repository_url?" }` → `201` |
| `GET` | `/api/projects/` | Yes | List the caller's projects |
| `GET` | `/api/projects/summary` | Yes | Projects with `total_files` and `has_analysis` for the dashboard |
| `GET` | `/api/projects/{project_id}` | Yes | One project |
| `PATCH` | `/api/projects/{project_id}` | Yes | `{ "name?", "description?" }` |
| `DELETE` | `/api/projects/{project_id}` | Yes | Delete the project and its extracted source folder |
| `POST` | `/api/projects/{project_id}/analyze` | Yes | Run the full analysis pipeline |
| `GET` | `/api/projects/{project_id}/analysis` | Yes | Stored symbols, dependencies and technologies |


### Imports

| Method | Path | Auth | Body / notes |
| --- | --- | --- | --- |
| `POST` | `/api/uploads/zip` | Yes | `multipart/form-data`: `name`, `description?`, `file` (`.zip`) → `201` |
| `POST` | `/api/github/import` | Yes | `{ "repository_url", "branch?" (default "main"), "name?", "description?" }` → `201` |

ZIP uploads are limited by `MAX_UPLOAD_SIZE_MB` (default 100). GitHub imports accept public repositories only.

### Files and source viewer

| Method | Path | Auth | Query / notes |
| --- | --- | --- | --- |
| `GET` | `/api/projects/{project_id}/files` | Yes | `page` (default 1), `page_size` (1–100, default 50), `language?`, `search?` |
| `GET` | `/api/projects/{project_id}/file-tree` | Yes | Nested folder tree (up to 2000 files per tree payload) |
| `GET` | `/api/projects/{project_id}/files/{file_id}/content` | Yes | Source text; symlinks are rejected |

### Chat

| Method | Path | Auth | Body / notes |
| --- | --- | --- | --- |
| `POST` | `/api/projects/{project_id}/chat` | Yes | `{ "question": "...", "conversation_id?": "<uuid>" }` |
| `GET` | `/api/projects/{project_id}/chats` | Yes | Conversation list with titles |
| `GET` | `/api/projects/{project_id}/chats/{conversation_id}` | Yes | Messages with `role`, `content`, `sources`, `created_at` |


### Documentation

| Method | Path | Auth | Body / notes |
| --- | --- | --- | --- |
| `POST` | `/api/projects/{project_id}/documentation` | Yes | Generate (or regenerate) documentation with the local model |
| `GET` | `/api/projects/{project_id}/documentation` | Yes | Read stored documentation (sanitized) |
| `GET` | `/api/projects/{project_id}/documentation/status` | Yes | `{ "project_id", "exists", "message" }` |

### Architecture, graph, APIs and metrics

| Method | Path | Auth | Query / notes |
| --- | --- | --- | --- |
| `GET` | `/api/projects/{project_id}/architecture` | Yes | `include_ai` (default `true`); set `false` for database facts only |
| `GET` | `/api/projects/{project_id}/graph` | Yes | Nodes are files; edges are resolved internal imports |
| `GET` | `/api/projects/{project_id}/apis` | Yes | Detected HTTP endpoints with method, path, framework and source location |
| `GET` | `/api/projects/{project_id}/metrics` | Yes | Files, bytes, languages, functions/classes, chunks, dependencies, APIs, conversations and documentation status |

### Status codes used

| Code | Meaning |
| --- | --- |
| `200` | Success |
| `201` | Created (signup, project creation, import) |
| `400` | Invalid import, incorrect current password, same password, or model input problem |
| `401` | Missing, invalid or expired token; deleted account |
| `403` | Forbidden file access (for example, a symlink) |
| `404` | Project, conversation, file or account not found |
| `409` | Email already registered |
| `422` | Request validation failed |
| `500` | Unexpected server error |
| `503` | Database or Ollama unavailable |


## Security

- Imported code is parsed as text only and never executed.
- ZIP extraction blocks unsafe paths, symlinks, and oversized archives.
- File access validates paths and rejects symlinks; deletion is restricted to the configured storage directory.
- Project ownership is verified on every endpoint; unauthorized access returns `404`.
- Passwords are hashed using Argon2; JWTs are signed with `SECRET_KEY` and expire after the configured duration (default: 30 minutes).
- CORS allows only the local frontend origins.
- Sensitive files are filtered before route detection.
- Environment files and local storage are git-ignored to prevent credential exposure.
- **Deployment:** Designed for local use, not hardened for public internet exposure.


## Local data and cleanup

| Action | Database effect | Local disk effect |
| --- | --- | --- |
| Delete a project | Project row and its related rows are removed | `<UPLOAD_DIR>/<user_id>/<storage_id>` is removed; the user folder is removed if empty |
| Delete an account | User and all owned projects/related rows are removed | Entire `<UPLOAD_DIR>/<user_id>` folder is removed |

Manual projects have no source folder on disk.

To inspect storage:

```bash
find backend/app/storage/projects -maxdepth 3 -type d
```

The storage directory is excluded from version control. Removing it only removes imported sources; run a fresh import to restore a project.


## Testing

The backend suite uses an in-memory SQLite database, so it never touches your PostgreSQL data:

```bash
cd backend
source venv/bin/activate
python -m pytest -q
```

Current result on this machine:

```text
212 passed, 1 skipped
```

The skipped test is an opt-in live Ollama integration test. AI calls are mocked elsewhere, keeping the suite fast and deterministic.

Frontend checks:

```bash
cd frontend
npm run lint
npm run build
```

`npm run build` writes the production bundle to `frontend/dist/`. Vite reports a chunk-size warning because the application is currently a single bundle; this is a known optimization opportunity, not a build failure.


## Project structure

```text
backend/
├── alembic.ini
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       ├── b7d44c241201_create_users_table.py
│       ├── f8dc37b511ae_create_projects_table.py
│       ├── 0f808623a9eb_add_project_files_table.py
│       ├── ba423f05e89b_add_code_symbols_table.py
│       ├── 97c64ca78e1a_add_code_chunks_table.py
│       ├── 9221d311bac7_add_dependencies_table.py
│       ├── 15962fab8837_add_resolved_file_to_dependencies.py
│       ├── cb39a4238632_add_chat_messages_table.py
│       └── be1dbfeea9ad_add_project_documentation_table.py
├── requirements.txt
├── tests/                          Pytest suite
│   ├── conftest.py                 In-memory DB and shared fixtures
│   ├── test_auth.py                Signup, login, current user
│   ├── test_users.py               Profile, password, account deletion
│   ├── test_projects.py            CRUD, analysis, summary, storage cleanup
│   ├── test_upload.py              ZIP validation and extraction
│   ├── test_github.py              Repository import
│   ├── test_files.py               File inventory and source viewer
│   ├── test_parsers.py             Language detection and tree-sitter parsing
│   ├── test_dependencies.py        Import extraction and resolution
│   ├── test_framework_detection.py Framework and technology detection
│   ├── test_search.py              Chunking and retrieval
│   ├── test_architecture.py        Architecture facts and explanation
│   ├── test_graph.py               Dependency graph
│   ├── test_apis.py                Endpoint detection and metrics
│   ├── test_chat.py                Conversations and source references
│   ├── test_documentation.py       Generation, sanitizing and status
│   ├── test_ollama.py              AI client behaviour and failures
│   └── test_ollama_integration.py  Opt-in live test (skipped by default)
└── app/
    ├── main.py                     App factory, CORS, router registration
    ├── api/
    │   ├── dependencies.py         JWT → current user
    │   └── routes/
    │       ├── auth.py             Signup, login, current user
    │       ├── users.py            Profile, password, account deletion
    │       ├── projects.py         CRUD, analysis run/results, summaries
    │       ├── uploads.py          ZIP import
    │       ├── github.py           GitHub import
    │       ├── files.py            File list, tree, content
    │       ├── chat.py             Questions and conversations
    │       ├── documentation.py    Generate, read, status
    │       ├── architecture.py     Facts and AI explanation
    │       ├── graph.py            Dependency graph
    │       └── apis.py             API detection and metrics
    ├── core/
    │   ├── config.py               Environment-backed settings
    │   └── security.py             JWT and password hashing
    ├── database/
    │   ├── base.py                 Declarative base
    │   └── connection.py           Engine, session factory, get_db
    ├── models/
    │   ├── user.py
    │   ├── project.py
    │   ├── project_file.py
    │   ├── code_symbol.py
    │   ├── code_chunk.py
    │   ├── dependency.py
    │   ├── chat.py
    │   └── documentation.py
    ├── schemas/
    │   ├── auth.py
    │   ├── analysis.py
    │   ├── chat.py
    │   ├── documentation.py
    │   ├── project.py
    │   └── project_file.py
    ├── services/
    │   ├── ai/
    │   │   ├── ollama_service.py   HTTP client for the local model
    │   │   ├── chat_service.py     Retrieval, history and generation
    │   │   └── prompt_builder.py   Grounded prompt assembly
    │   ├── analysis/
    │   │   ├── analysis_service.py        Orchestrates a full run
    │   │   ├── file_inventory_service.py  Builds file records
    │   │   ├── file_scanner.py            Walks and filters sources
    │   │   ├── parser_manager.py          Chooses grammar per language
    │   │   ├── tree_sitter_parser.py      Tree-sitter wrapper
    │   │   ├── symbol_extractor.py        Functions, methods, classes
    │   │   ├── chunk_extractor.py         Structural chunks
    │   │   ├── generic_chunk_extractor.py Fallback chunking
    │   │   ├── dependency_extractor.py    Imports per file
    │   │   ├── dependency_resolver.py     Internal path resolution
    │   │   ├── dependency_analyzer.py     Dependency records
    │   │   ├── framework_detector.py      Framework/technology detection
    │   │   ├── api_detector.py            HTTP route patterns
    │   │   └── metrics_service.py         Project metrics
    │   ├── architecture/
    │   │   ├── architecture_service.py              Structural facts
    │   │   └── architecture_explanation_service.py  Optional AI narrative
    │   ├── documentation/
    │   │   └── documentation_service.py   Grounding, generation, sanitizing
    │   ├── search/
    │   │   └── search_service.py          Retrieval over stored chunks
    │   └── source/
    │       ├── import_service.py          Import orchestration
    │       ├── upload_service.py          Upload validation and storage
    │       ├── github_service.py          Archive download
    │       ├── zip_extractor.py           Safe extraction
    │       └── storage_service.py         Path resolution and cleanup
    └── storage/projects/                  Extracted sources (git-ignored)

frontend/
├── index.html
├── package.json
├── vite.config.js
├── .oxlintrc.json
├── public/network.svg
└── src/
    ├── main.jsx
    ├── App.jsx
    ├── App.css
    ├── index.css
    ├── components/
    │   ├── chat/          ChatWindow, ChatInput, ChatMessage, SourceReference
    │   ├── common/        Sidebar, DashboardTopbar, Navbar, ProjectNav,
    │   │                  ProtectedRoute, CollapsibleSection, EmptyState,
    │   │                  ErrorMessage, LoadingSpinner
    │   ├── dashboard/     StatCard, ProjectCard
    │   ├── documentation/ MarkdownViewer
    │   ├── explorer/      FileTree, FileTreeNode, CodeViewer, SymbolList
    │   ├── graph/         DependencyGraph (React Flow)
    │   └── upload/        ZipUpload, GitHubImport, ImportStatus
    ├── context/
    │   └── AuthContext.jsx
    ├── hooks/
    │   └── useAuth.js
    ├── pages/             LandingPage, LoginPage, SignupPage, DashboardPage,
    │                      AllProjectsPage, CreateProjectPage,
    │                      ProjectOverviewPage, FileExplorerPage,
    │                      ArchitecturePage, DependencyGraphPage,
    │                      ApiExplorerPage, DocumentationPage,
    │                      CodebaseChatPage, ProfilePage
    ├── services/          api (Axios instance), authService, projectService,
    │                      uploadService, analysisService,
    │                      architectureService, graphService,
    │                      documentationService, chatService
    └── utils/             constants, formatters, buildFileTree,
                           architectureExplanationCache, navigation
```


## Known Limitations

- **AI reliability:** Generated answers, documentation, and explanations may be incomplete or incorrect.
- **Ollama dependency:** AI features require a running local model; otherwise, requests return `503`.
- **Detection limitations:** API detection is pattern-based, framework detection relies on evidence, and unsupported languages use generic file/chunk handling.
- **Dependency graph:** Displays only resolved internal imports; external packages are listed separately.
- **Authentication:** No email verification, password reset, token refresh, or server-side token revocation. Tokens remain in `localStorage`, which is not XSS-hardened.
- **Deployment:** Designed for local use, without production hardening such as rate limiting, TLS configuration, or audit logging.
- **Performance and testing:** Large repositories may exceed the model context window; the frontend uses a single bundle and has no browser E2E test suite.
  

## Development notes

- Schema changes go through Alembic:

  ```bash
  cd backend
  alembic revision --autogenerate -m "describe the change"
  alembic upgrade head
  ```

- Keep new project routes behind `get_current_user` and verify ownership before reading project data.
- Backend tests live in `backend/tests/` and use fixtures from `conftest.py`.
- Imported sources live under `backend/app/storage/projects/` and must stay out of version control.
- After changing backend dependencies, run `pip install -r requirements.txt` inside the virtual environment.
- The frontend uses custom CSS rather than a component library; keep page styles consistent with neighbouring pages.
- Do not commit `.env` files, uploaded sources or generated build output.
