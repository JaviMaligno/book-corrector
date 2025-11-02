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
```

### Running Server
```bash
# Local development
uvicorn server.main:app --reload

# With Docker
docker-compose up --build

# Development with hot-reload
docker-compose -f docker-compose.dev.yml up

# Production
docker-compose up -d
```

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
```

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

**CLI:**
- `GOOGLE_API_KEY`: Required for Gemini (get from https://aistudio.google.com/app/apikey)
- `GEMINI_MODEL`: Default `gemini-2.5-flash` (do NOT use `gemini-1.5-pro-latest` - 404 error)
- `RUN_GEMINI_INTEGRATION`: Set to `1` to enable live integration tests

**Server:**
- `GOOGLE_API_KEY`: Required for Gemini API
- `GEMINI_MODEL`: Model selection (default: `gemini-2.5-flash`)
- `DEMO_PLAN`: Demo user plan (`free` or `premium`, default: `free`)
- `SYSTEM_MAX_WORKERS`: Max concurrent jobs system-wide (default: `2`)

### Prompt Customization
Edit `docs/base-prompt.md` (loaded by `prompt.py:load_base_prompt()`)
- Keep concise (verbose prompts performed worse)
- Explicitly list lexical confusion pairs
- Emphasize returning ONLY actual corrections (not explanations)

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
server/             # FastAPI server with scheduler
  ├── main.py       # App factory and routes
  ├── scheduler.py  # Fair-share job scheduler
  ├── limits.py     # Plan quotas (free/premium)
  └── schemas.py    # Pydantic models
tests/
  ├── samples/      # Test DOCX files (tracked in git)
  ├── outputs/      # Test outputs (gitignored)
  └── test_server_basic.py  # Server integration tests
outputs/            # Production outputs (gitignored)
examples/           # User documents (gitignored except ejemplo_*.docx)
docs/               # Documentation including base-prompt.md
scripts/            # Debug scripts (gitignored)
Dockerfile          # Multi-stage production image
docker-compose.yml  # Production deployment
docker-compose.dev.yml  # Development with hot-reload
```

**Gitignore strategy**: All `.docx` files excluded except `tests/samples/*.docx` and `examples/ejemplo_*.docx`. All generated outputs excluded.

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

```
GET  /health                   # Health check
GET  /me/limits                # Get user plan limits
POST /runs                     # Create correction run
GET  /runs/{run_id}            # Get run status
```

See `server/main.py` and `server/schemas.py` for full API spec.

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
