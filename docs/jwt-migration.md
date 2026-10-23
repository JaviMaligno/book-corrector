# JWT dependency migration (23 October 2026)

This change follows reviewed source head `d68fb8cf29816c2b97a7dbf0cdd7b17633ac7940`. The application now uses
`PyJWT[crypto]>=2.15.1,<3`, with the existing corrected cryptography cohort. Both
python-jose and ECDSA are absent from the regenerated production lock/export.
Their upstream advisories remain unfixed: [DER/HMAC confusion in python-jose](https://github.com/advisories/GHSA-3qf3-8w2g-rqmx)
and [Minerva in python-ecdsa](https://github.com/tlsfuzzer/python-ecdsa/security/advisories/GHSA-wj6h-64fc-37mp).
This removes those application dependencies; it does not invent an upstream fix
or establish that every other package, deployment key or image layer is safe.

## Compatibility and validation

Signing algorithms come from the same trusted configuration, never the token
header. Book keeps its fixed HS256 policy and subject-string return value. Claim names, token strings, key selection, account permissions
and the existing token-error result remain compatible. No signing-key rotation,
refresh-token storage transformation, schema migration or provider call occurs.

Signature, expiration, not-before, subject, JWT-ID and audience validation remain
enabled. Since these callers provide no audience or OIDC access-token context,
any present `aud` or `at_hash` is rejected after signature verification, including
empty values that a simple import replacement would otherwise accept. Optional
claims keep their existing presence policy; application token-type/subject checks
stay at their original callers. Malformed numeric claims use the token failure
API rather than escaping as decoder type errors.

Two documented security tightenings use the new library defaults: future `iat`
values are rejected, and `exp == now` is expired. No leeway or verification bypass
is added. Legacy tokens retain their signed timestamps and are accepted while
valid under that policy. [PyJWT's API](https://pyjwt.readthedocs.io/en/stable/api.html)
and [2.15.1 source](https://github.com/jpadilla/pyjwt/tree/2.15.1) document the
signature/claim options and DER-key rejection with the crypto extra.

Book continues to obtain permissions from the database and has no refresh-token
API. The migration exposed a pre-existing UTC bug: `utcnow().timestamp()` treated
a naive UTC reading as local time. On the observed UTC+1 machine, issuance was
3,600 seconds early and a 60-minute token could expire at creation. Two explicit
RED contracts reproduce the real offset and a portable synthetic UTC+1 clock.
Issuance now uses `datetime.now(UTC)`, preserving the requested lifetime and UTC
NumericDate values. The 17-minute fixture and current-UTC bounds pass without
changing machine timezone or weakening expiration. Legacy signed timestamps are
not extended.

## Focused evidence

The three original implementations all accepted the synthetic DER-as-HMAC,
future-iat and exact-expiry cases: nine expected RED failures. The configurable
RSA implementations additionally exposed four migration RED failures for a
private PEM used by both issuance/verification and for a PEM certificate. Those
contracts pass with the explicit RSA verification-key adaptation.

One HS256 legacy tokens were generated using python-jose 3.5.0 with invented
identities and keys. Across all three repositories, eleven algorithm/repository
pairs verify in both directions with PyJWT 2.15.1. Committed fixtures contain
synthetic tokens and public keys only, plus an explicitly invented shared test
secret; RSA/EC private keys exist only in memory. Future tests load these fixtures
without adding jose back as a development dependency.

The final focused selection passes 24 cases with one additional intentional skip for the absent refresh API. It covers old/new tokens, refresh
semantics where present, malformed claims, algorithm/key mismatch, unsigned
input, approved date tightenings, and actual authentication dependencies. Real
HTTP/DNS, subprocess startup, provider constructors, database connections and
dotenv-file loading are denied; application imports receive only synthetic
settings. A signed role claim cannot replace the database principal returned by
the dependency mock. No application lifespan, business job or persistent data is
used.

```sh
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/test_jwt_migration.py tests/test_auth_dependencies.py::test_token_subject_expiry_and_algorithm_are_preserved -q --tb=short -p no:cacheprovider
```

Scoped Ruff and Black checks pass for the three affected Python files. Black ran one file per invocation after a bounded Windows multi-file worker timeout. The pip-free UV environment passes `uv pip check`. The formatter preserves the compared ASTs. Some deliberately short
negative-test keys produce PyJWT key-length warnings; no warning filter or
production key-policy change is introduced. Local verification reused isolated
focus environments, which may still contain the former packages for legacy
proof; complete fresh installs use the committed lock. Final-head hosted CI,
independent review and image checks remain separate gates. No full local suite,
server, browser, Docker build, push, deployment or merge is part of this patch.
