# Dependency security maintenance (2026-10-22)

Python 3.11.17 with uv 0.13.5 uses `uv sync --frozen`; the application is installed from the copied local source. Both backend Dockerfiles consume the root `uv.lock`, and the server requirements file is a hashed export of that same lock. Build either backend from the repository root. Node 24.22.1 uses `npm ci --ignore-scripts` in `web/`; Render's declared frontend build uses the same frozen install.

Google GenAI remains on its existing 1.x API, OpenAI on 2.x, and the FastAPI/Starlette pair resolves together. bcrypt 4.1.3 preserves the original server's passlib-compatible runtime pin. The HS256 algorithm, claims, key selection and password policy remain unchanged. React stays on 18; React Router moves to corrected 7.x with an offline contract over the actual route patterns.

Selected offline checks: `uv run --frozen pytest -q tests/test_text_utils.py tests/test_engine_apply.py tests/test_auth_dependencies.py` and, from `web/`, `node --test --test-concurrency=2 tests/router-contract.test.mjs` plus `npm run build`. Authentication contracts use a synthetic key and deny network connections; the DOCX engine uses temporary synthetic files. Standalone `tsc --noEmit` also exposes existing CorrectionsTable/CorrectionsView typing errors; the existing frontend build is Vite's bundle check and must not be described as a passing typecheck.

Pull-request CI keeps lint and bundle checks in draft, and runs selected tests and Linux container builds on Ready. Local Docker and provider/database calls were not run. Unfixed advisories, including the ECDSA dependency selected by python-jose, require separate risk assessment; these changes do not replace the public JWT API or claim a globally clean graph.

The development Compose bind mount protects `/app/.venv` with its own volume, retaining the Linux environment from the image rather than exposing a Windows host environment. Recreate that volume after lock changes.

## Current advisory scope and residuals

Fresh exact-name public OSV comparison retains `braces` 3.0.3 (GHSA-vfj7-8cjw-p6xm, no fixed release recorded) and Tailwind 3's `postcss-selector-parser` 6.1.5 (GHSA-rj75-hqrm-r3gf, correction requires major 7 and a tested parent migration). Python also retains the python-jose/ECDSA advisory families with no fixed versions established by the current query; HS256 remains explicitly allowlisted and the public authentication API is preserved. This is unresolved dependency risk, not a claim that every affected API is reachable.

Public OSV queries transmit only public registry package names and versions, with exact package matching; no source, repository identifiers or private dependency edges are uploaded. The earlier cached 317-record comparison is supplemental and does not replace these current queries.
