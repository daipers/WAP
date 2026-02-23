# Phase 3: User Setup Required

**Generated:** 2026-02-23
**Phase:** 03-scoring-reporting
**Status:** Incomplete

Complete these items for LTI 1.3 launch and AGS grade passback to function.

## Environment Variables

| Status | Variable | Source | Add to |
|--------|----------|--------|--------|
| [ ] | `LTI_ISSUER` | LMS developer console → Platform issuer | `.env` |
| [ ] | `LTI_CLIENT_ID` | LMS tool registration → Client ID | `.env` |
| [ ] | `LTI_DEPLOYMENT_ID` | LMS deployment settings → Deployment ID | `.env` |
| [ ] | `LTI_KEYSET_URL` | LMS JWKS URL | `.env` |
| [ ] | `LTI_AUTH_URL` | LMS OIDC auth endpoint | `.env` |
| [ ] | `LTI_TOKEN_URL` | LMS OAuth2 token endpoint | `.env` |
| [ ] | `LTI_PRIVATE_KEY` | Tool private key for JWT signing | `.env` |

## Dashboard Configuration

- [ ] **Register tool with LTI 1.3 redirect/launch URLs**
  - Location: LMS developer console
  - Notes: Use `/lti/login` and `/lti/launch` endpoints for the tool URLs

- [ ] **Enable AGS scopes for line item and score services**
  - Location: LMS developer console
  - Notes: Enable scopes for line items and score submission

## Verification

After completing setup, verify with a test launch from the LMS:

- LTI 1.3 login completes and returns a launch context
- Grade passback updates the LMS gradebook

---

**Once all items complete:** Mark status as "Complete" at top of file.
