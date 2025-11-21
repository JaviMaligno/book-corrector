# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Spanish text corrector using Google Gemini API. Detects orthographic errors and lexical confusions (homophones/homographs: vello/bello, vaca/baca, hojear/ojear). Preserves DOCX formatting while making token-level corrections.

**Two modes:**
- **CLI**: Command-line tool for local document correction
- **Server**: FastAPI REST API with user auth, projects, job scheduling, and **correction acceptance/rejection**

## Commands

### Setup
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -e .
cp .env.example .env  # Add GOOGLE_API_KEY
```

### Running CLI
```bash
# Basic (outputs to outputs/ directory)
python -m corrector.cli documento.docx

# With uv (preferred by user)
uv run python -m corrector.cli documento.docx

# Local mode (no API, for testing)
python -m corrector.cli documento.docx --local-heuristics

# Advanced options
python -m corrector.cli documento.docx --no-log-docx  # Skip DOCX report
python -m corrector.cli documento.docx --model gemini-2.5-pro  # Change model
python -m corrector.cli documento.docx --no-preserve-format  # Don't preserve formatting
```

### Running Server
```bash
# Local development (backend only)
uvicorn server.main:app --reload --port 8001

# Full stack with Docker (backend + frontend + database)
docker-compose -f docker-compose.dev.yml up  # Development with hot-reload
docker-compose up -d  # Production

# Frontend only (requires backend running)
cd web && npm install && npm run dev
```

**Service URLs:**
- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8001`
- API Docs: `http://localhost:8001/docs`

### Testing
```bash
# Unit tests (no API)
pytest tests/test_text_utils.py tests/test_engine_apply.py

# Single test
pytest tests/test_text_utils.py::test_tokenize_and_apply_replacement -v

# Mock tests
pytest tests/test_gemini_fake.py

# Live integration (requires GOOGLE_API_KEY and RUN_GEMINI_INTEGRATION=1 in .env)
pytest tests/test_gemini_live.py

# Server tests
pytest tests/test_server_basic.py
```

## Development Workflow

This project is deployed on **Render** (backend + frontend) with a **Neon PostgreSQL** database. Use this workflow when implementing new features:

### 1. Local Development & Testing

**Backend development:**
```bash
# Start local stack (backend + frontend + PostgreSQL in Docker)
docker-compose -f docker-compose.dev.yml up

# Watch logs
docker-compose -f docker-compose.dev.yml logs -f web

# Run tests against local stack
pytest tests/test_server_basic.py -v
```

**Frontend development:**
```bash
# Option 1: Full stack in Docker (hot-reload enabled)
docker-compose -f docker-compose.dev.yml up

# Option 2: Frontend standalone (requires backend running separately)
cd web
npm install
npm run dev
```

**CLI testing:**
```bash
# Test CLI changes locally (no Docker)
uv run python -m corrector.cli examples/ejemplo_test.docx
```

### 2. Database Operations (Neon MCP)

Use Neon MCP tools for database management during development:

**List projects and get connection info:**
```python
# Use mcp__neon__list_projects to find your database
# Use mcp__neon__get_connection_string to get connection URL
```

**Run migrations:**
```python
# Use mcp__neon__run_sql to execute schema changes
# Example: Adding a new column
mcp__neon__run_sql(
    projectId="your-project-id",
    sql="ALTER TABLE suggestion ADD COLUMN confidence FLOAT DEFAULT 0.0"
)
```

**Query data:**
```python
# Use mcp__neon__run_sql for SELECT queries
mcp__neon__run_sql(
    projectId="your-project-id",
    sql="SELECT COUNT(*) FROM suggestion WHERE status='pending'"
)
```

**Create branches for testing:**
```python
# Use mcp__neon__create_branch to create test branches
# Test schema changes safely before applying to main
```

### 3. Frontend Testing (Chrome MCP)

Use Chrome DevTools MCP for automated frontend testing:

**Navigate and interact:**
```python
# Open frontend
mcp__chrome-devtools__navigate_page(url="http://localhost:5173")

# Take snapshot to see page structure
mcp__chrome-devtools__take_snapshot()

# Click elements (use uid from snapshot)
mcp__chrome-devtools__click(uid="element-uid")

# Fill forms
mcp__chrome-devtools__fill(uid="email-input", value="test@example.com")
```

**Test corrections workflow:**
```python
# Login
mcp__chrome-devtools__navigate_page(url="http://localhost:5173/login")
mcp__chrome-devtools__fill(uid="email", value="demo@example.com")
mcp__chrome-devtools__fill(uid="password", value="demo123")
mcp__chrome-devtools__click(uid="login-button")

# Navigate to project
mcp__chrome-devtools__click(uid="project-link")

# Upload document
mcp__chrome-devtools__upload_file(uid="file-input", filePath="test.docx")

# Verify corrections table loads
mcp__chrome-devtools__wait_for(text="Correcciones")
mcp__chrome-devtools__take_screenshot()
```

**Check console for errors:**
```python
# List console messages
mcp__chrome-devtools__list_console_messages(types=["error", "warn"])
```

### 4. Deployment to Render

**Deploy via git push:**
```bash
# Commit your changes
git add .
git commit -m "feat: add new feature X"

# Push to trigger Render deployment
git push origin main

# Render will automatically:
# 1. Build Docker images for backend and frontend
# 2. Deploy to production
# 3. Run database migrations (if configured)
```

**Monitor deployment (Render MCP):**
```python
# List services
mcp__render__list_services()

# Check deployment status
mcp__render__list_deploys(serviceId="srv-xxx")

# Get specific deploy
mcp__render__get_deploy(serviceId="srv-xxx", deployId="dep-xxx")

# View logs
mcp__render__list_logs(
    resource=["srv-xxx"],
    startTime="2024-01-01T12:00:00Z",
    limit=100
)
```

**Update environment variables:**
```python
# Use Render MCP to update production config
mcp__render__update_environment_variables(
    serviceId="srv-xxx",
    envVars=[
        {"key": "GEMINI_MODEL", "value": "gemini-2.5-pro"},
        {"key": "SYSTEM_MAX_WORKERS", "value": "4"}
    ]
)
```

### 5. Production Testing

**Test deployed frontend:**
```python
# Open production URL
mcp__chrome-devtools__navigate_page(url="https://corrector-web.onrender.com")

# Run same test flows as local
mcp__chrome-devtools__take_snapshot()
# ... test login, upload, corrections, etc.
```

**Query production database:**
```python
# Use Neon MCP to check production data
mcp__neon__run_sql(
    projectId="your-prod-project-id",
    sql="SELECT status, COUNT(*) FROM run GROUP BY status"
)
```

**Monitor production metrics:**
```python
# Use Render MCP to get performance metrics
mcp__render__get_metrics(
    resourceId="srv-xxx",
    metricTypes=["cpu_usage", "memory_usage", "http_request_count"],
    startTime="2024-01-01T00:00:00Z"
)
```

### 6. Debugging Production Issues

**Check logs:**
```python
# Backend logs
mcp__render__list_logs(
    resource=["srv-backend-xxx"],
    level=["error"],
    limit=50
)

# Filter by path
mcp__render__list_logs(
    resource=["srv-backend-xxx"],
    path=["/api/runs/*"],
    statusCode=["500"]
)
```

**Database debugging:**
```python
# Check failed runs
mcp__neon__run_sql(
    projectId="prod-project-id",
    sql="SELECT id, status, created_at FROM run WHERE status='failed' ORDER BY created_at DESC LIMIT 10"
)

# Check pending suggestions
mcp__neon__run_sql(
    projectId="prod-project-id",
    sql="SELECT run_id, COUNT(*) FROM suggestion WHERE status='pending' GROUP BY run_id"
)
```

**Frontend debugging:**
```python
# Open production site
mcp__chrome-devtools__navigate_page(url="https://corrector-web.onrender.com")

# Check console errors
mcp__chrome-devtools__list_console_messages(types=["error"])

# Check network requests
mcp__chrome-devtools__list_network_requests(resourceTypes=["fetch", "xhr"])

# Get failed request details
mcp__chrome-devtools__get_network_request(reqid=123)
```

### Common Development Patterns

**Pattern 1: Add new API endpoint**
1. Add route to `server/routes_*.py`
2. Add schema to `server/schemas.py`
3. Test locally: `curl http://localhost:8001/your-endpoint`
4. Test with Chrome MCP if frontend integration needed
5. Push to deploy
6. Monitor with Render MCP logs

**Pattern 2: Database schema change**
1. Create Neon branch for testing: `mcp__neon__create_branch`
2. Test migration on branch: `mcp__neon__run_sql(branchId=...)`
3. Verify with queries
4. Apply to main: `mcp__neon__run_sql` (main branch)
5. Update SQLModel models in `server/models.py`
6. Deploy

**Pattern 3: Frontend feature**
1. Develop in `web/src/`
2. Test locally: `npm run dev`
3. Test with Chrome MCP: navigate, click, fill, screenshot
4. Check console/network with Chrome MCP
5. Push to deploy
6. Test production with Chrome MCP on live URL

## Architecture

### Token-Based Correction Pipeline

The corrector operates on **stable token IDs** rather than text positions:

1. **Tokenize entire document** → Each token gets global ID (never changes)
2. **Split into chunks** → Chunks reference token ranges (start_idx, end_idx)
3. **Send chunks to LLM** → Returns corrections as `{token_id, replacement, reason}`
4. **Filter false positives** → Skip invalid corrections
5. **Apply corrections** → Replace token text by ID
6. **Detokenize** → Reconstruct document with preserved formatting

**Why token IDs?** Allows corrections from different chunks to reference the same position without recalculating offsets when text changes.

### Key Data Flow

```
DOCX → paragraphs → full_text → tokens (with global IDs)
                                    ↓
                            chunk by token ranges
                                    ↓
                        [(0,847), (762,1609), ...]
                                    ↓
                    for each chunk: local_tokens → LLM → corrections
                                    ↓
                    map local IDs → global IDs
                                    ↓
                        filter + deduplicate
                                    ↓
                    apply_token_corrections(tokens, corrections)
                                    ↓
                        detokenize → corrected_text
                                    ↓
                    write DOCX (preserve formatting)
```

### Chunking Strategy

**Auto-chunking** (default): Uses 15% of context window (~300-1000 words/chunk)
- Calculation: `cli.py` lines 98-106
- Adjustable via `target_ratio` (0.0-1.0)
- 10% overlap between chunks for context continuity
- Aligns on natural boundaries (sentence endings, newlines)

**Why 15%?** Reduced from 70% for visible progress and faster iteration. Large chunks (3000+ words) take 5+ minutes each.

### False Positive Filtering

Three-layer filter in `engine.py` (lines 92-105):

1. **Identical replacement**: `tok.text == c.replacement` → skip
2. **Whitespace → word**: Token ID misalignment → skip
3. **Punctuation → word**: Gemini returned wrong ID → skip

**Common issue**: Gemini sometimes suggests "corrections" where original already correct (e.g., "cayó" → "cayó"). Filter catches these.

### Format Preservation

`docx_utils.py`: `write_docx_preserving_runs()`
- Unzips DOCX (it's a ZIP)
- Modifies only `<w:t>` text nodes in `word/document.xml`
- Preserves all formatting XML (bold, italic, fonts, colors, etc.)
- Re-zips to new DOCX

## Testing Practices

### Test Structure

```
tests/
├── test_text_utils.py       # Tokenization, detokenization, corrections
├── test_engine_apply.py     # End-to-end with HeuristicCorrector
├── test_gemini_fake.py      # Mock Gemini API responses
├── test_gemini_live.py      # Real API integration (gated)
└── outputs/                 # Test outputs (gitignored)
```

### Mock Testing Pattern

See `test_gemini_fake.py`:
- Mock `_client.responses.generate()` to return fake corrections
- Parse prompt with regex to find token IDs: `r"(\d+):W:baca\b"`
- Return corrections matching those IDs
- Validates full pipeline without API calls

### Integration Test Gating

`test_gemini_live.py`:
```python
load_dotenv()  # Load .env first
RUN_LIVE = os.getenv('RUN_GEMINI_INTEGRATION') == '1'
API_SET = bool(os.getenv('GOOGLE_API_KEY'))
pytestmark = pytest.mark.skipif(not (RUN_LIVE and API_SET), reason='...')
```

Only runs when explicitly enabled to avoid consuming API quota.

### Test Assertions

**Good pattern** (from `test_engine_apply.py`):
```python
# Create input DOCX programmatically
write_paragraphs(paragraphs, str(input_doc))

# Run engine
process_document(str(input_doc), str(output_doc), str(log_path), corrector, ...)

# Validate output content
out_paragraphs = read_paragraphs(str(output_doc))
full_text = "\n".join(out_paragraphs)
assert "La vaca del coche" in full_text  # Check correction applied

# Validate log structure
log_lines = log_path.read_text(encoding="utf-8").strip().splitlines()
assert len(log_lines) >= 2
assert '"original"' in log_lines[0]
```

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

**Core Configuration:**
- `SECRET_KEY`: JWT secret key (change in production!)
- `DATABASE_URL`: PostgreSQL connection URL (Neon or local)
- `STORAGE_DIR`: Local storage directory for artifacts (default: `./storage`)
- `LOG_LEVEL`: Logging level (`INFO`, `DEBUG`, `WARNING`, `ERROR`)
- `SYSTEM_MAX_WORKERS`: Max concurrent correction workers (default: `2`)
- `DEMO_PLAN`: Demo user plan (`free` or `premium`, default: `free`)
- `FRONTEND_URL`: Frontend URL for CORS (e.g., `https://corrector-web.onrender.com`)

**Google Gemini API (Primary LLM):**
- `GOOGLE_API_KEY`: **Required** - Get from https://aistudio.google.com/app/apikey
- `GEMINI_MODEL`: Model selection (default: `gemini-2.5-flash`)
  - Options: `gemini-2.5-flash`, `gemini-2.5-pro`
  - **Do NOT use** `gemini-1.5-pro-latest` (404 error)
- `RUN_GEMINI_INTEGRATION`: Set to `1` to enable live integration tests

**Azure OpenAI (Alternative LLM, optional):**
- `AZURE_OPENAI_ENDPOINT`: Azure endpoint URL
- `AZURE_OPENAI_API_KEY`: Azure API key
- `AZURE_OPENAI_DEPLOYMENT_NAME`: Deployment name (e.g., `gpt-4`)
- `AZURE_OPENAI_API_VERSION`: API version (e.g., `2024-02-15-preview`)
- `AZURE_OPENAI_MODEL_NAME`: Model name (e.g., `gpt-4`)
- `AZURE_OPENAI_FALLBACK_DEPLOYMENT_NAME`: Fallback deployment
- `AZURE_OPENAI_FALLBACK_API_VERSION`: Fallback API version

**Deployment (for automation scripts):**
- `RENDER_API_KEY`: Render API key for deployment management
- `TOKEN`: JWT token for testing scripts
- `TEST_EMAIL`: Test user email (default: `demo@example.com`)
- `TEST_PASSWORD`: Test user password (default: `demo123`)

**Production URLs:**
- Local: `http://localhost:8001` (backend), `http://localhost:5173` (frontend)
- Render: Auto-generated URLs (e.g., `https://corrector-api-xxx.onrender.com`)

### Plan Limits Configuration

Defined in `server/limits.py`:

**FREE plan:**
```python
max_runs_concurrent = 1      # Only 1 active run at a time
max_docs_per_run = 1         # Only 1 document per run
max_docs_concurrent = 1      # Only 1 document processing at a time
rate_limit_rpm = 60          # 60 requests per minute
ai_enabled = True
```

**PREMIUM plan:**
```python
max_runs_concurrent = 2      # Up to 2 concurrent runs
max_docs_per_run = 3         # Up to 3 documents per run
max_docs_concurrent = 3      # Up to 3 documents processing simultaneously
rate_limit_rpm = 300         # 300 requests per minute
ai_enabled = True
```

To change the demo user's plan, set `DEMO_PLAN=premium` in `.env`.

### Prompt Customization

Edit `docs/base-prompt.md` (loaded by `prompt.py:load_base_prompt()`):
- Keep concise (verbose prompts performed worse in testing)
- Explicitly list lexical confusion pairs (vaca/baca, vello/bello, etc.)
- Emphasize returning ONLY actual corrections (not explanations)
- Use examples to guide LLM behavior

## Key Files

### Core Logic
- `corrector/engine.py` - Main processing loop, chunking, filtering, output generation
- `corrector/model.py` - Gemini API integration (`GeminiCorrector`) and local fallback (`HeuristicCorrector`)
- `corrector/text_utils.py` - Tokenization, detokenization, chunking algorithms
- `corrector/cli.py` - CLI entry point, auto-chunking calculation

### Supporting
- `corrector/prompt.py` - Loads `docs/base-prompt.md`, builds JSON prompt with token list
- `corrector/docx_utils.py` - DOCX I/O with format preservation
- `corrector/llm.py` - Gemini client initialization
- `settings.py` - Environment config via Pydantic

### Critical Details

**Gemini API usage** (`model.py` lines 44-48):
```python
resp = self._client.models.generate_content(
    model=self.model_name,
    contents=[{"role": "user", "parts": [{"text": prompt}]}],
    config={"response_mime_type": "application/json"},
)
```
Uses `models.generate_content()` NOT `responses.generate()` (previous bug).

**Token ID mapping** (`engine.py` lines 79-85):
```python
# Chunk uses local IDs starting from 0
local_tokens = [Token(i - start, t.text, ...) for i, t in enumerate(tokens[start:end], start=start)]
corrections = corrector.correct_tokens(local_tokens)

# Map back to global IDs
for c in corrections:
    global_id = start + c.token_id
    if 0 <= global_id < len(tokens):
        # Apply correction to global token list
```

**Overlap deduplication** (`engine.py` lines 87-89):
```python
if global_id in applied_global:
    continue  # Already corrected in previous chunk
```

## Repository Structure

```
corrector/          # Core correction engine
  ├── cli.py        # CLI entry point
  ├── engine.py     # Main processing loop, chunking, filtering
  ├── model.py      # GeminiCorrector + HeuristicCorrector
  ├── text_utils.py # Tokenization, detokenization
  ├── docx_utils.py # DOCX I/O with format preservation
  ├── prompt.py     # Loads base-prompt.md
  └── llm.py        # Gemini client initialization

server/             # FastAPI server with scheduler
  ├── main.py       # App factory, CORS, artifact downloads
  ├── models.py     # SQLModel database schemas
  ├── schemas.py    # Pydantic API request/response models
  ├── routes_auth.py      # /auth endpoints (register, login)
  ├── routes_projects.py  # /projects endpoints
  ├── routes_documents.py # /documents endpoints
  ├── routes_runs.py      # /runs endpoints
  ├── routes_suggestions.py # /suggestions endpoints
  ├── scheduler.py        # InMemoryScheduler (fair-share queues)
  ├── scheduler_registry.py # Global scheduler instance
  ├── worker.py     # Background correction worker
  ├── limits.py     # Plan quotas (FREE/PREMIUM constants)
  ├── db.py         # SQLModel database initialization
  ├── auth.py       # JWT token creation/verification
  ├── deps.py       # FastAPI dependencies (get_current_user)
  ├── storage.py    # Artifact storage management
  ├── migrate.py    # Database migration utilities
  └── demo_data.py  # Demo user creation

web/                # React + Vite frontend
  ├── src/
  │   ├── components/
  │   │   ├── CorrectionsTable.tsx  # Main corrections display with 3 views
  │   │   └── ContextSnippet.tsx    # Context highlighting
  │   ├── pages/
  │   │   ├── Login.tsx             # Login page
  │   │   ├── Register.tsx          # Registration page
  │   │   ├── Projects.tsx          # Projects list
  │   │   ├── ProjectDetail.tsx     # Project details + upload
  │   │   ├── RunDetail.tsx         # Run status + progress
  │   │   ├── CorrectionsView.tsx   # Corrections review (server mode)
  │   │   └── Viewer.tsx            # Legacy JSONL viewer
  │   ├── contexts/
  │   │   └── AuthContext.tsx       # JWT auth state management
  │   ├── layouts/
  │   │   └── Layout.tsx            # Main layout with nav
  │   ├── lib/
  │   │   ├── api.ts                # API client functions
  │   │   ├── auth.ts               # Auth helpers
  │   │   └── types.ts              # TypeScript types
  │   └── main.tsx                  # React entry point
  ├── Dockerfile                    # Frontend container
  └── vite.config.ts                # Vite configuration

tests/
  ├── samples/      # Test DOCX files (tracked in git)
  ├── outputs/      # Test outputs (gitignored)
  ├── test_text_utils.py    # Tokenization tests
  ├── test_engine_apply.py  # End-to-end tests
  ├── test_gemini_fake.py   # Mock Gemini tests
  ├── test_gemini_live.py   # Live API integration tests
  └── test_server_basic.py  # Server integration tests

outputs/            # Production outputs (gitignored)
examples/           # User documents (gitignored except ejemplo_*.docx)
docs/               # Documentation including base-prompt.md
scripts/            # Debug scripts (gitignored)
Dockerfile          # Multi-stage backend image
docker-compose.yml  # Production deployment (backend + frontend + db)
docker-compose.dev.yml  # Development with hot-reload
```

**Gitignore strategy**: All `.docx` files excluded except `tests/samples/*.docx` and `examples/ejemplo_*.docx`. All generated outputs excluded.

## Frontend Architecture (React + Vite)

The frontend is a single-page application built with React, TypeScript, and Vite.

### Key Features

**Authentication Flow:**
- JWT-based authentication stored in localStorage
- `AuthContext` provides global auth state
- Protected routes redirect to login if not authenticated
- Auto-refresh on page load

**Corrections Review Interface:**
- **Three view modes**: Inline, Stacked, Side-by-side
- **Accept/Reject workflow**: Individual buttons or bulk selection with checkboxes
- **Progress bar**: Visual segmentation of pending/accepted/rejected
- **Filtering**: By status (pending/accepted/rejected) using tabs
- **Search**: Filter by original text, replacement, or reason
- **Export**: Download DOCX with only accepted corrections

**Server vs Legacy Mode:**
- **Server mode**: Suggestions stored in database, full accept/reject workflow
- **Legacy mode**: JSONL files only, read-only view (backward compatibility)

### Component Structure

**Pages:**
- `Login.tsx` / `Register.tsx`: Auth forms
- `Projects.tsx`: List all user projects
- `ProjectDetail.tsx`: Project details + document upload (multi-file)
- `RunDetail.tsx`: Run status, progress tracking, artifact downloads
- `CorrectionsView.tsx`: Main corrections review page (server mode with accept/reject)
- `Viewer.tsx`: Legacy JSONL viewer (read-only)

**Components:**
- `CorrectionsTable.tsx`: Main table with 3 view modes, accept/reject buttons
- `ContextSnippet.tsx`: Context highlighting with original/corrected

**State Management:**
- `AuthContext`: Global JWT token + user state
- Component-local state with `useState` for UI interactions
- API calls via `lib/api.ts` helper functions

### API Integration

All API calls in `web/src/lib/api.ts`:
```typescript
// Authentication
login(email, password) → {access_token}
register(email, password) → {access_token}

// Projects
listProjects() → Project[]
createProject(name) → Project
uploadDocuments(projectId, files) → Document[]

// Runs
createRun(projectId, documentIds, useAi) → {run_id}
getRun(runId) → Run with status + progress

// Suggestions
listSuggestions(runId, status?) → Suggestion[]
updateSuggestion(suggestionId, status) → Suggestion
bulkUpdateSuggestions(runId, suggestionIds, status) → void
acceptAllSuggestions(runId) → void
rejectAllSuggestions(runId) → void
exportWithAccepted(runId) → Blob (DOCX file)
```

### Styling

- **Tailwind CSS** for utility-first styling
- **shadcn/ui** components (Button, Card, Progress, etc.)
- Responsive design for mobile/tablet/desktop

## Database Models (SQLModel)

### Core Tables

**User:**
```python
- id: str (UUID)
- email: str (unique)
- password_hash: str
- role: Role (free | premium | admin)
- created_at: datetime
```

**Project:**
```python
- id: str (UUID)
- owner_id: str → User.id
- name: str
- lang_variant: str? (es-ES, es-MX)
- style_profile_id: str?
- config_json: str?
- created_at: datetime
```

**Document:**
```python
- id: str (UUID)
- project_id: str → Project.id
- name: str
- path: str? (storage path)
- kind: DocumentKind (docx | txt | md)
- checksum: str?
- status: DocumentStatus (new | queued | processing | ready)
- content_backup: str? (for ephemeral storage)
```

**Run:**
```python
- id: str (UUID)
- project_id: str → Project.id
- submitted_by: str → User.id
- mode: RunMode (rapido | profesional)
- status: RunStatus (queued | processing | exporting | completed | failed | canceled)
- params_json: str?
- created_at: datetime
- started_at: datetime?
- finished_at: datetime?
```

**RunDocument:**
```python
- id: str (UUID)
- run_id: str → Run.id
- document_id: str → Document.id
- status: RunDocumentStatus (queued | processing | completed | failed)
- use_ai: bool
- locked_by: str? (worker ID)
- locked_at: datetime?
- heartbeat_at: datetime?
- attempt_count: int
```

**Suggestion:**
```python
- id: str (UUID)
- run_id: str → Run.id
- document_id: str → Document.id
- token_id: int (stable token position)
- line: int (paragraph number)
- suggestion_type: SuggestionType (ortografia | puntuacion | concordancia | estilo | lexico | otro)
- severity: Severity (error | warning | info)
- before: str (original text)
- after: str (suggested replacement)
- reason: str (explanation)
- source: Source (rule | llm)
- confidence: float? (0.0-1.0 for AI)
- context: str? (surrounding text)
- sentence: str? (full sentence)
- status: SuggestionStatus (pending | accepted | rejected)
- created_at: datetime
```

### Key Relationships

```
User → Project (one-to-many)
Project → Document (one-to-many)
Project → Run (one-to-many)
Run → RunDocument (one-to-many)
Document → RunDocument (one-to-many)
Run → Suggestion (one-to-many)
Document → Suggestion (one-to-many)
```

## Batch Processing & Rate Limiting

### Rate Limits by Model

The system automatically applies rate limiting based on the Gemini model:

**gemini-2.5-pro:**
- Limit: 2 requests/minute
- Wait time: 30 seconds between chunks
- Use for: High-quality corrections, complex documents

**gemini-2.5-flash:**
- Limit: 15 requests/minute
- Wait time: 4 seconds between chunks
- Use for: Fast processing, large batches

### Retry Logic

**Exponential backoff:**
- Attempt 1: Immediate
- Attempt 2: Wait 2 seconds
- Attempt 3: Wait 4 seconds
- Attempt 4: Wait 8 seconds

**Fallback behavior:**
- If `gemini-2.5-pro` fails after retries → fallback to `gemini-2.5-flash` for that chunk
- Worker continues with remaining chunks

### Batch Processing Example

Processing 41 documents with `gemini-2.5-pro`:
- Time per document: ~30 seconds
- Total time: ~20 minutes
- Documents/hour: ~120

Processing 41 documents with `gemini-2.5-flash`:
- Time per document: ~4 seconds
- Total time: ~3 minutes
- Documents/hour: ~900

### Monitoring Batch Jobs

```python
# Start batch run
run_id = create_run(project_id, document_ids=[...])

# Poll for progress
while True:
    run = get_run(run_id)
    print(f"[{run['processed_documents']}/{run['total_documents']}] Status: {run['status']}")
    if run['status'] in ['completed', 'failed']:
        break
    time.sleep(10)
```

## Server Architecture

The FastAPI server provides a REST API for document correction with:
- **User limits** based on plan (free/premium)
- **Fair-share scheduler** with per-user queues
- **Concurrent job management** respecting quotas
- **System-wide worker limits**

### Scheduler Design

`server/scheduler.py`: `InMemoryScheduler`
- Per-user FIFO queues of `DocumentTask`
- Round-robin dispatch across users
- Enforces limits:
  - Free: 1 concurrent run, 1 doc/run, 1 concurrent doc
  - Premium: 2 concurrent runs, 3 docs/run, 3 concurrent docs
  - System: 2 total workers (configurable via `SYSTEM_MAX_WORKERS`)

**Why fair-share?** Prevents single user from monopolizing workers. Each user gets turns based on their plan.

### API Endpoints

**Authentication** (`/auth`):
```
POST /auth/register            # Register new user
POST /auth/login               # Login and get JWT token
GET  /auth/me                  # Get current user info
```

**Projects** (`/projects`):
```
GET    /projects                      # List user's projects
POST   /projects                      # Create project
GET    /projects/{project_id}         # Get project details
PATCH  /projects/{project_id}         # Update project
DELETE /projects/{project_id}         # Delete project
POST   /projects/{project_id}/documents/upload  # Upload documents
```

**Documents** (`/documents`):
```
GET    /documents/{document_id}       # Get document details
DELETE /documents/{document_id}       # Delete document
GET    /documents/{document_id}/download  # Download original
```

**Runs** (`/runs`):
```
POST /runs                     # Create correction run
GET  /runs/{run_id}            # Get run status + progress
GET  /runs/{run_id}/exports    # List downloadable artifacts
```

**Suggestions** (`/suggestions`):
```
GET   /suggestions/runs/{run_id}/suggestions  # List all suggestions
PATCH /suggestions/suggestions/{suggestion_id}  # Accept/reject one
POST  /suggestions/runs/{run_id}/suggestions/bulk-update  # Bulk accept/reject
POST  /suggestions/runs/{run_id}/suggestions/accept-all  # Accept all pending
POST  /suggestions/runs/{run_id}/suggestions/reject-all  # Reject all pending
POST  /suggestions/runs/{run_id}/export-with-accepted  # Export DOCX with accepted only
```

**System**:
```
GET  /health                   # Health check
GET  /me/limits                # Get user plan limits
GET  /artifacts/{run_id}/{filename}  # Download artifact (logs, reports, corrected docs)
```

See `server/routes_*.py` and `server/schemas.py` for full API spec.

## User Preferences

- **Use `uv`** when available for running commands
- **Use existing CLI** - don't create new debug scripts
- **Auto-chunking by default** - user wants smart chunking without manual flags
- **Smaller chunks preferred** - 300-1000 words for visible progress
- **Generate DOCX log by default** - professional reports expected

## Docker Deployment

### Build and Run
```bash
# Build image
docker-compose build

# Run in foreground (see logs)
docker-compose up

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Configuration
Set environment variables in `.env` file:
```bash
GOOGLE_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.5-flash
DEMO_PLAN=premium
SYSTEM_MAX_WORKERS=4
```

Docker Compose will automatically load `.env` and pass to container.

### Development Mode
```bash
# Hot-reload on code changes
docker-compose -f docker-compose.dev.yml up
```

Mounts source code as volumes so changes are reflected without rebuild.

## Common Issues

### "Models/gemini-1.5-pro-latest not found (404)"
Model name invalid. Use `gemini-2.5-flash` or `gemini-2.5-pro`.

### "Process hangs with no output"
Large chunks (3000+ words) take 5+ minutes. Check logs for progress. Reduce `target_ratio` in `cli.py` if needed.

### "False positives (word already correct)"
Filters should catch `original == replacement`. If not, add more specific filters in `engine.py` lines 92-105.

### "Whitespace being corrected to words"
Token ID misalignment from Gemini. Filter at `engine.py` line 99 should catch this.

### "Docker container exits immediately"
Check logs: `docker-compose logs corrector-api`. Likely missing `GOOGLE_API_KEY` in `.env`.

## Correction Acceptance/Rejection Feature (NEW)

The server now supports **full correction management**, allowing users to review, accept, or reject corrections before applying them to the final document.

### Overview

When a correction run completes, all suggestions are saved to the database with `status=pending`. Users can then:
- Review suggestions individually or by type
- Accept/reject corrections one by one or in bulk
- Export a final document with **only accepted corrections** applied

### Database Model

**`Suggestion` table:**
```python
- id: UUID
- run_id: FK to Run
- document_id: FK to Document
- token_id: int (stable token position)
- line: int (paragraph/line number)
- suggestion_type: ortografia | puntuacion | concordancia | estilo | lexico | otro
- severity: error | warning | info
- before: original text
- after: suggested replacement
- reason: explanation
- source: rule | llm
- confidence: float (0.0-1.0 for AI)
- context: surrounding text
- sentence: full sentence
- status: pending | accepted | rejected ← KEY FIELD
- created_at: timestamp
```

### API Endpoints

All endpoints under `/suggestions` prefix:

**List suggestions:**
```bash
GET /suggestions/runs/{run_id}/suggestions?status=pending
Authorization: Bearer {token}
```

**Accept/reject individual:**
```bash
PATCH /suggestions/suggestions/{suggestion_id}
Authorization: Bearer {token}
Content-Type: application/json

{"status": "accepted"}  # or "rejected"
```

**Bulk operations:**
```bash
# Bulk update
POST /suggestions/runs/{run_id}/suggestions/bulk-update
{"suggestion_ids": ["id1", "id2"], "status": "accepted"}

# Accept all pending
POST /suggestions/runs/{run_id}/suggestions/accept-all

# Reject all pending
POST /suggestions/runs/{run_id}/suggestions/reject-all
```

**Export with accepted corrections:**
```bash
POST /suggestions/runs/{run_id}/export-with-accepted
Authorization: Bearer {token}
# Returns DOCX file with only accepted corrections applied
```

### Worker Behavior

**`server/worker.py` changes:**
1. Uses `process_paragraphs()` instead of `process_document()` to get `LogEntry` objects
2. Persists each correction as a `Suggestion` record with `status=pending`
3. Auto-classifies suggestion type based on reason keywords
4. Maintains backward compatibility (still generates JSONL/CSV/DOCX logs)

**Classification logic:**
```python
# Keywords in reason → suggestion_type
"ortografía" → ortografia
"puntuación" → puntuacion
"léxico", "confusión" → lexico
"concordancia" → concordancia
"estilo" → estilo
```

### Example Workflows

**Example 1: Editorial Review**
```python
import requests

token = login("demo@example.com", "demo123")
run_id = "abc-123"

# 1. List all suggestions
suggs = requests.get(f"{API}/suggestions/runs/{run_id}/suggestions",
                     headers={"Authorization": f"Bearer {token}"}).json()

# 2. Auto-accept orthography
ortho_ids = [s["id"] for s in suggs["suggestions"] if s["suggestion_type"] == "ortografia"]
requests.post(f"{API}/suggestions/runs/{run_id}/suggestions/bulk-update",
              headers={"Authorization": f"Bearer {token}"},
              json={"suggestion_ids": ortho_ids, "status": "accepted"})

# 3. Review style manually
style = [s for s in suggs["suggestions"] if s["suggestion_type"] == "estilo"]
for s in style:
    print(f"{s['before']} → {s['after']}: {s['reason']}")
    # Decision logic here...

# 4. Export final document
response = requests.post(f"{API}/suggestions/runs/{run_id}/export-with-accepted",
                        headers={"Authorization": f"Bearer {token}"})
with open("final.docx", "wb") as f:
    f.write(response.content)
```

**Example 2: Quick Accept All**
```bash
# Accept all suggestions at once
curl -X POST "http://localhost:8000/suggestions/runs/{run_id}/suggestions/accept-all" \
  -H "Authorization: Bearer $TOKEN"

# Export
curl -X POST "http://localhost:8000/suggestions/runs/{run_id}/export-with-accepted" \
  -H "Authorization: Bearer $TOKEN" \
  -o final_accepted.docx
```

### Files Changed

- **`server/models.py`**: Added `Suggestion` model with enums
- **`server/schemas.py`**: Added API request/response schemas
- **`server/routes_suggestions.py`**: New router with all suggestion endpoints
- **`server/worker.py`**: Updated to persist suggestions and use `process_paragraphs()`
- **`server/main.py`**: Registered suggestions router
- **`docs/feature-correction-acceptance.md`**: Complete feature documentation
- **`docs/plan-backend.md`**: Updated with new model and endpoints
- **`examples/example_correction_workflow.py`**: Python example script
- **`examples/example_curl_commands.sh`**: Bash/curl example script

### Testing

**Quick test:**
```bash
# 1. Verify models load
uv run python -c "from server.models import Suggestion; print('OK')"

# 2. Start server
docker-compose up

# 3. Create a run (generates suggestions)
curl -X POST http://localhost:8000/runs \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"project_id":"...","documents":["..."]}'

# 4. List suggestions
curl http://localhost:8000/suggestions/runs/{run_id}/suggestions \
  -H "Authorization: Bearer $TOKEN"
```

**See full examples:**
- Python: `examples/example_correction_workflow.py`
- Bash: `examples/example_curl_commands.sh`

### Benefits

✅ **Full control**: Users decide which corrections to apply
✅ **Batch operations**: Efficient bulk accept/reject
✅ **Type filtering**: Accept all orthography, review style manually
✅ **Audit trail**: All decisions tracked in database
✅ **Format preservation**: Final document maintains original formatting
✅ **Backward compatible**: Existing JSONL/CSV/DOCX logs still generated

### Future Extensions

- **Learn from patterns**: Auto-accept/reject based on user history
- **Custom rules**: "Always accept type X, always reject type Y"
- **Comments**: Allow users to add notes to suggestions
- **Visual diff**: UI for side-by-side comparison
- **Track changes export**: Generate DOCX with Word track changes markup
