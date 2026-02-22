---
phase: 01-content-bank-identity
plan: 03
type: execute
wave: 1
depends_on: []
files_modified:
  - dev_package/src/audit_ledger_service/ledger.py
  - dev_package/src/audit_ledger_service/events.py
  - dev_package/src/audit_ledger_service/__init__.py
autonomous: true
user_setup: []

must_haves:
  truths:
    - "System records immutable audit log entries for each assessment attempt"
    - "System captures delivery events including start, answer, submit, and terminate actions"
  artifacts:
    - path: "dev_package/src/audit_ledger_service/ledger.py"
      provides: "Immutable audit ledger with hash chain"
      exports: ["AuditLedger", "LedgerEntry"]
    - path: "dev_package/src/audit_ledger_service/events.py"
      provides: "Event types and payload schemas"
      exports: ["AuditEvent", "EventType", "create_event"]
    - path: "dev_package/src/audit_ledger_service/__init__.py"
      provides: "Public API exports"
  key_links:
    - from: "ledger.py"
      to: "events.py"
      via: "AuditEvent dataclass"
      pattern: "AuditEvent|EventType"
---

<objective>
Build Audit Ledger foundations with immutable event logging and delivery event capture.

Purpose: Establish the audit trail foundation required for compliance and assessment integrity.
Output: Extended ledger.py with event types, events.py with schemas, proper module exports.
</objective>

<execution_context>
@./.opencode/get-shit-done/workflows/execute-plan.md
@./.opencode/get-shit-done/templates/summary.md
</execution_context>

<context>
@./dev_package/src/audit_ledger_service/ledger.py
@./dev_package/scripts/run_demo.py
</context>

<tasks>

<task type="auto">
  <name>Define audit event types and schemas</name>
  <files>dev_package/src/audit_ledger_service/events.py</files>
  <action>
    Create events.py with:
    - EventType enum: SESSION_START, SESSION_END, CONSENT_RECORDED, DIAGNOSTIC_START, DIAGNOSTIC_SUBMIT, INTERVIEW_START, INTERVIEW_SUBMIT, ANSWER_SUBMITTED, ITEM_VIEWED, TERMINATE, TIMEOUT
    - AuditEvent dataclass: event_type (EventType), session_id (str), candidate_id (str), timestamp (float), actor (str), payload (dict), metadata (dict)
    - create_event(event_type: EventType, session_id: str, candidate_id: str, actor: str, payload: dict = None, metadata: dict = None) -> AuditEvent helper
    Include payload schemas for each event type (what fields each event must include).
  </action>
  <verify>
    Run: cd dev_package && python3 -c "
from src.audit_ledger_service.events import EventType, AuditEvent, create_event
e = create_event(EventType.SESSION_START, 'sess-1', 'cand-1', 'system', {'ip': '127.0.0.1'})
assert e.event_type == EventType.SESSION_START
assert e.session_id == 'sess-1'
assert e.payload['ip'] == '127.0.0.1'
print('Audit events tests passed')
"
  </verify>
  <done>
    EventType enum covers all delivery events; AuditEvent captures all required fields; create_event helper works
  </done>
</task>

<task type="auto">
  <name>Extend AuditLedger with event recording</name>
  <files>dev_package/src/audit_ledger_service/ledger.py</files>
  <action>
    Extend AuditLedger:
    - Add record_audit_event(event: AuditEvent) -> LedgerEntry - records event with hash chain
    - Add get_events_by_session(session_id: str) -> List[LedgerEntry]
    - Add get_events_by_candidate(candidate_id: str) -> List[LedgerEntry]
    - Add get_events_by_type(event_type: EventType) -> List[LedgerEntry]
    - Add get_session_attempt_events(session_id: str) -> dict - groups events by type for an attempt
    - Add export_audit_log(output_path: str) - exports to JSON lines format
    Keep existing record_event and verify_chain for backward compatibility.
  </action>
  <verify>
    Run: cd dev_package && python3 -c "
from src.audit_ledger_service.ledger import AuditLedger
from src.audit_ledger_service.events import EventType, create_event
ledger = AuditLedger()
event = create_event(EventType.SESSION_START, 'sess-1', 'cand-1', 'system')
entry = ledger.record_audit_event(event)
assert entry.session_id == 'sess-1'
events = ledger.get_events_by_session('sess-1')
assert len(events) == 1
events_by_type = ledger.get_events_by_type(EventType.SESSION_START)
assert len(events_by_type) == 1
print('AuditLedger extended tests passed')
"
  </verify>
  <done>
    AuditLedger records audit events, queries by session/candidate/type, exports to JSON lines
  </done>
</task>

<task type="auto">
  <name>Add immutability guarantees and chain verification</name>
  <files>dev_package/src/audit_ledger_service/ledger.py</files>
  <action>
    Enhance AuditLedger with:
    - Add _genesis_hash: str class attribute - hardcoded initial hash
    - Modify _compute_hash to include genesis check
    - Add verify_session_events(session_id: str) -> tuple[bool, list] - verifies hash chain for specific session
    - Add get_last_event_hash(session_id: str) -> str - gets most recent hash for session
    - Add export_for_attestation(session_id: str, output_path: str) - exports session events with signatures for third-party attestation
    Ensure first entry in chain uses genesis hash as prev_hash.
  </action>
  <verify>
    Run: cd dev_package && python3 -c "
from src.audit_ledger_service.ledger import AuditLedger
from src.audit_ledger_service.events import EventType, create_event
ledger = AuditLedger()
# Record multiple events for session
for i in range(3):
    event = create_event(EventType.SESSION_START, f'sess-{i}', f'cand-{i}', 'system')
    ledger.record_audit_event(event)
# Verify chain
valid, invalid_entries = ledger.verify_session_events('sess-0')
assert valid == True
# Export for attestation
ledger.export_for_attestation('sess-0', '/tmp/attestation.json')
print('Immutability tests passed')
"
  </verify>
  <done>
    Hash chain integrity verified per-session; attestation export produces verifiable log; genesis hash ensures chain origin
  </done>
</task>

</tasks>

<verification>
- Event types cover all delivery events (start, answer, submit, terminate)
- AuditLedger records events with hash chain
- Query methods work (by session, candidate, type)
- Chain verification and attestation export work
</verification>

<success_criteria>
1. Immutable audit log entries are recorded for each assessment attempt
2. Delivery events (start, answer, submit, terminate) are captured with proper payloads
3. Hash chain provides tamper evidence
4. Events can be queried and exported
</success_criteria>

<output>
After completion, create `.planning/phases/01-content-bank-identity/01-audit-ledger-SUMMARY.md`
</output>
