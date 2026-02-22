---
phase: 01-content-bank-identity
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - dev_package/src/identity_service/identity.py
  - dev_package/src/utils/auth.py
  - dev_package/configs/auth_config.yaml
  - dev_package/src/identity_service/__init__.py
autonomous: true
user_setup: []

must_haves:
  truths:
    - "User can create, view, update, and delete identity records for assessment candidates"
    - "User can authenticate and authorize access to assessment sessions with proper credentials"
    - "Session persists across browser refresh and maintains attempt state"
  artifacts:
    - path: "dev_package/src/identity_service/identity.py"
      provides: "Candidate CRUD and Session management"
      exports: ["Candidate", "Session", "IdentityService"]
    - path: "dev_package/src/utils/auth.py"
      provides: "Authentication and authorization logic"
      exports: ["create_token", "verify_token", "require_auth"]
    - path: "dev_package/configs/auth_config.yaml"
      provides: "Auth configuration (JWT settings, session expiry)"
  key_links:
    - from: "identity_service/identity.py"
      to: "utils/auth.py"
      via: "import authentication functions"
      pattern: "from.*auth import"
---

<objective>
Build Identity & Session Service to handle candidate identity records and session management with authentication.

Purpose: Establish the foundation for user management and secure session handling required by all downstream services.
Output: Extended identity.py with CRUD operations, auth module with JWT support, and session persistence.
</objective>

<execution_context>
@./.opencode/get-shit-done/workflows/execute-plan.md
@./.opencode/get-shit-done/templates/summary.md
</execution_context>

<context>
@./dev_package/src/identity_service/identity.py
@./dev_package/scripts/run_demo.py
@./dev_package/configs/state_machine.yaml
</context>

<tasks>

<task type="auto">
  <name>Add Candidate CRUD operations</name>
  <files>dev_package/src/identity_service/identity.py</files>
  <action>
    Extend IdentityService with full CRUD for candidates:
    - Add get_candidate(candidate_id) method returning Candidate or raise KeyError
    - Add update_candidate(candidate_id, email, consent_version) method
    - Add delete_candidate(candidate_id) method - soft delete (mark as inactive)
    - Add list_candidates() method returning list of active candidates
    - Add is_active field to Candidate dataclass
    Keep existing create_candidate and record_consent methods.
  </action>
  <verify>
    Run: cd dev_package && python3 -c "
from src.identity_service.identity import IdentityService
svc = IdentityService('configs/state_machine.yaml')
c = svc.create_candidate('test@example.com', '1.0')
assert c.email == 'test@example.com'
found = svc.get_candidate(c.candidate_id)
assert found.email == 'test@example.com'
svc.update_candidate(c.candidate_id, 'new@example.com')
assert svc.get_candidate(c.candidate_id).email == 'new@example.com'
candidates = svc.list_candidates()
assert len(candidates) == 1
svc.delete_candidate(c.candidate_id)
assert svc.get_candidate(c.candidate_id).is_active == False
print('All CRUD tests passed')
"
  </verify>
  <done>
    Candidate CRUD operations work: create returns candidate with ID, get retrieves by ID, update modifies fields, delete soft-deletes, list returns active candidates
  </done>
</task>

<task type="auto">
  <name>Implement JWT authentication module</name>
  <files>dev_package/src/utils/auth.py</files>
  <action>
    Create auth.py module with JWT-based authentication:
    - Use jose library (Python JWT) for JWT encoding/decoding
    - create_token(candidate_id: str, expires_delta: timedelta) -> str
    - verify_token(token: str) -> dict with candidate_id and claims
    - require_auth(authorization_header: str) -> dict - validates Bearer token
    - Store secret in config, not hardcoded
    - Use HS256 algorithm for simplicity
    Create configs/auth_config.yaml with jwt_secret, jwt_algorithm, access_token_expire_minutes, refresh_token_expire_days
  </action>
  <verify>
    Run: cd dev_package && python3 -c "
from src.utils.auth import create_token, verify_token
import time
token = create_token('candidate-123', expires_delta=timedelta(minutes=15))
claims = verify_token(token)
assert claims['candidate_id'] == 'candidate-123'
print('JWT auth tests passed')
"
  </verify>
  <done>
    JWT tokens can be created with candidate_id claims and verified; invalid/expired tokens raise exceptions
  </done>
</task>

<task type="auto">
  <name>Add session persistence with state serialization</name>
  <files>dev_package/src/identity_service/identity.py</files>
  <action>
    Extend IdentityService with session persistence:
    - Add save_session(session_id: str) -> dict method - serializes session to dict
    - Add load_session(session_data: dict) -> Session method - deserializes session from dict
    - Add get_session_by_candidate(candidate_id: str) -> Optional[Session] for resume
    - Add session expiry mechanism (check and remove expired sessions)
    - Store sessions with created_at timestamp for expiry calculation
    Session should persist: session_id, candidate_id, state, consent_version, assessment_version, selected_challenges, selected_injections, created_at
  </action>
  <verify>
    Run: cd dev_package && python3 -c "
from src.identity_service.identity import IdentityService
svc = IdentityService('configs/state_machine.yaml')
c = svc.create_candidate('test@example.com')
session = svc.start_session(c.candidate_id)
# Serialize
data = svc.save_session(session.session_id)
assert 'session_id' in data
# Resume
restored = svc.load_session(data)
assert restored.session_id == session.session_id
# Find by candidate
found = svc.get_session_by_candidate(c.candidate_id)
assert found.session_id == session.session_id
print('Session persistence tests passed')
"
  </verify>
  <done>
    Sessions can be serialized to dict, deserialized back to Session object, and retrieved by candidate_id; maintains state across "refresh"
  </done>
</task>

</tasks>

<verification>
- All CRUD operations (create, get, update, delete, list) work correctly
- JWT token creation and verification works with proper expiry handling
- Session serialization/deserialization preserves all state
- Integration with existing demo script still works
</verification>

<success_criteria>
1. Identity records can be created, viewed, updated, and deleted (soft delete)
2. JWT-based authentication allows secure session access
3. Session state can be serialized and restored (simulating browser refresh persistence)
</success_criteria>

<output>
After completion, create `.planning/phases/01-content-bank-identity/01-identity-session-SUMMARY.md`
</output>
