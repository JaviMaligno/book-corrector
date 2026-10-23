# Dependency security maintenance (2026-10-22)

Python 3.11.17 with uv 0.13.5 uses `uv sync --frozen`; the application is installed from the copied local source. Both backend Dockerfiles consume the root `uv.lock`, and the server requirements file is a hashed export of that same lock. Build either backend from the repository root. Node 24.22.1 uses `npm ci --ignore-scripts` in `web/`; Render's declared frontend build uses the same frozen install.

Google GenAI remains on its existing 1.x API, OpenAI on 2.x, and the FastAPI/Starlette pair resolves together. bcrypt 4.1.3 preserves the original server's passlib-compatible runtime pin. HS256, claim names, key selection and password policy remain; the later [JWT migration](docs/jwt-migration.md) documents stricter date validation and corrected UTC issuance. React stays on 18; React Router moves to corrected 7.x with an offline contract over the actual route patterns.

Selected offline checks: `uv run --frozen pytest -q tests/test_text_utils.py tests/test_engine_apply.py tests/test_auth_dependencies.py tests/test_model_enum_contracts.py` and, from `web/`, `node --test --test-concurrency=2 tests/router-contract.test.mjs tests/corrections-contract.test.mjs` plus `npm run build`. Authentication contracts use a synthetic key and deny network connections; the DOCX engine uses temporary synthetic files. Standalone `tsc --noEmit` now passes and is an explicit lightweight CI gate, alongside the Vite bundle build.

Pull-request CI keeps lint and bundle checks in draft, and runs selected tests and Linux container builds on Ready. Local Docker and provider/database calls were not run. The later [JWT migration](docs/jwt-migration.md) replaces python-jose/ECDSA dependencies while preserving the public API; other advisory matches retain their recorded scope and do not establish a globally clean graph.

The development Compose bind mount protects `/app/.venv` with its own volume, retaining the Linux environment from the image rather than exposing a Windows host environment. Recreate that volume after lock changes.

## Current advisory scope and residuals

The exact-name OSV comparison retains `braces` 3.0.3 (GHSA-vfj7-8cjw-p6xm, no fixed release recorded). Its raw finding also includes Tailwind 3's `postcss-selector-parser` 6.1.5 under a `<7.1.6` range, but [the official 6.1.5 changelog](https://raw.githubusercontent.com/postcss/postcss-selector-parser/6.1.5/CHANGELOG.md) records the 19 October security backport from 7.1.6 for CVE-2026-104844. Book's lock integrity matches the independently verified published 6.1.5 tarball; the source audit confirms its Set-based fixes. The raw advisory row and the upstream range discrepancy remain recorded, rather than suppressing the finding or forcing parser 7 outside Tailwind 3's range. This is source/integrity evidence for the backport, not a claim that OSV has reconciled its range.

Python's jose/ECDSA advisory families remain unfixed upstream, but both packages are removed from this application's regenerated lock/export by the [JWT migration](docs/jwt-migration.md). The public authentication API remains compatible, with the documented date hardenings and UTC correction.

Public OSV queries transmit only public registry package names and versions, with exact package matching; no source, repository identifiers or private dependency edges are uploaded. The earlier cached 317-record comparison is supplemental and does not replace these current queries.


## Draft-blocker follow-up (2026-10-23)

The 11 existing Ruff UP042 diagnostics are resolved with a shared `StrEnum` base that explicitly retains `Enum.__str__` and `Enum.__format__`. All member names/values and model fields remain unchanged. Eleven contracts pass over the actual model enums, Pydantic/JSON values and SQLAlchemy bind/result processors; the same contracts passed before the migration and all 11 failed for a naive StrEnum replacement. No database connection or schema migration was used. Python documents the string behavior and supported method reassignment at https://docs.python.org/3.11/library/enum.html#notes.

The review screen now uses TanStack Query 5's filter object to invalidate only suggestion queries for the reviewed run. A real QueryClient regression test fails with the old array argument because it also invalidates unrelated runs and projects; it passes with the corrected prefix filter. All seven mutation callbacks use that helper. Reference: https://tanstack.com/query/latest/docs/framework/react/guides/query-invalidation.

Legacy JSONL parsing, union narrowing and document-name filtering retain their previous behavior with sound TypeScript types. The individual suggestion update type also permits `pending`, matching the existing backend revert endpoint; bulk updates still allow only accepted/rejected. The test checks actual table rendering and the actual Axios helper with a synthetic adapter. JSONL tests exercise malformed syntax tolerance, not arbitrary input schema validation.

Local verification: Ruff and Black checks pass, 15 selected backend cases and four Node/router/UI cases pass, standalone frontend TypeScript and the Vite build pass. Formatting the eight pre-existing noncompliant Python files preserves their ASTs (50 tracked/new Python files compared across the formatter). No Azure/Gemini example or integration test was executed. The first sandbox build could not read esbuild configuration; an additional root-directory invocation failed to find Tailwind's relative config. The same build from the actual web working directory passed. CI Ready still must verify the final committed SHA and all three Linux image paths; local Docker remains unexecuted.
