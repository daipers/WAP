---
phase: 01-content-bank-identity
plan: 02
type: execute
wave: 1
depends_on: []
files_modified:
  - dev_package/src/content_bank_service/content_bank.py
  - dev_package/src/content_bank_service/qti_parser.py
  - dev_package/src/content_bank_service/models.py
autonomous: true
user_setup: []

must_haves:
  truths:
    - "User can import assessment items from QTI packages into the system"
    - "User can export items to QTI format for portability and reuse"
    - "User can store items with metadata including tags, difficulty ratings, and time limits"
    - "User can version items and track changes over time"
  artifacts:
    - path: "dev_package/src/content_bank_service/content_bank.py"
      provides: "Content bank service with CRUD, versioning, metadata"
      exports: ["ContentBankService"]
    - path: "dev_package/src/content_bank_service/qti_parser.py"
      provides: "QTI 1.2/3.0 import and export"
      exports: ["QTIImporter", "QTIExporter"]
    - path: "dev_package/src/content_bank_service/models.py"
      provides: "Item and version models"
      exports: ["AssessmentItem", "ItemVersion", "ItemMetadata"]
  key_links:
    - from: "content_bank.py"
      to: "qti_parser.py"
      via: "QTIImporter/QTIExporter classes"
      pattern: "QTIImporter|QTIExporter"
    - from: "content_bank.py"
      to: "models.py"
      via: "AssessmentItem dataclass"
      pattern: "AssessmentItem"
---

<objective>
Extend Content Bank Service with QTI import/export and full item versioning.

Purpose: Enable portable assessment content management with industry-standard QTI format support and complete version history.
Output: Enhanced content_bank.py, qti_parser.py with QTI 1.2/3.0 support, models.py with versioning.
</objective>

<execution_context>
@./.opencode/get-shit-done/workflows/execute-plan.md
@./.opencode/get-shit-done/templates/summary.md
</execution_context>

<context>
@./dev_package/src/content_bank_service/content_bank.py
@./dev_package/data/challenge_bank.json
@./dev_package/scripts/run_demo.py
</context>

<tasks>

<task type="auto">
  <name>Create item models with versioning</name>
  <files>dev_package/src/content_bank_service/models.py</files>
  <action>
    Create models.py with:
    - ItemMetadata dataclass: tags (List[str]), difficulty (int), time_limit_minutes (int), domain (str), skill_tags (List[str])
    - ItemVersion dataclass: version (str), created_at (float), created_by (str), changes (str), content (dict)
    - AssessmentItem dataclass: item_id (str), current_version (str), metadata (ItemMetadata), versions (List[ItemVersion]), is_active (bool)
    Include helper methods: add_version(content: dict, created_by: str, changes: str), get_version(version: str) -> ItemVersion
  </action>
  <verify>
    Run: cd dev_package && python3 -c "
from src.content_bank_service.models import AssessmentItem, ItemMetadata, ItemVersion
import time
metadata = ItemMetadata(tags=['test'], difficulty=3, time_limit_minutes=10, domain='math', skill_tags=['algebra'])
item = AssessmentItem('item-1', '1.0', metadata, [], True)
item.add_version({'prompt': 'Test'}, 'admin', 'Initial version')
assert len(item.versions) == 1
assert item.get_version('1.0').content['prompt'] == 'Test'
print('Item models tests passed')
"
  </verify>
  <done>
    AssessmentItem supports metadata storage, multiple versions with change tracking, and version retrieval
  </done>
</task>

<task type="auto">
  <name>Build QTI import/export parser</name>
  <files>dev_package/src/content_bank_service/qti_parser.py</files>
  <action>
    Create qti_parser.py with:
    - QTIImporter class:
      - import_from_file(path: str) -> List[AssessmentItem] - handles QTI 1.2 (XML) and QTI 3.0 (JSON) packages
      - parse_qti_manifest(manifest_path: str) -> dict - extracts item references
      - parse_item(item_path: str) -> dict - converts QTI item to internal format
      Extract: identifier, prompt, response_type, gold_criteria, allowed_tools, constraints
    - QTIExporter class:
      - export_items(items: List[AssessmentItem], output_path: str) - writes QTI 1.2 XML format
      - item_to_qti(item: AssessmentItem) -> str - converts single item to QTI XML
    Use xml.etree.ElementTree for QTI 1.2 parsing. Handle basic item types (multiple-choice, text-response).
  </action>
  <verify>
    Run: cd dev_package && python3 -c "
from src.content_bank_service.qti_parser import QTIImporter, QTIExporter
# Test basic structure exists
assert QTIImporter is not None
assert QTIExporter is not None
importer = QTIImporter()
exporter = QTIExporter()
print('QTI parser module loads correctly')
"
  </verify>
  <done>
    QTIImporter can parse QTI 1.2 XML items; QTIExporter can generate QTI 1.2 XML; both handle basic item types
  </done>
</task>

<task type="auto">
  <name>Extend ContentBankService with full CRUD and QTI support</name>
  <files>dev_package/src/content_bank_service/content_bank.py</files>
  <action>
    Extend ContentBankService:
    - Add items: Dict[str, AssessmentItem] storage
    - Add create_item(item_id: str, content: dict, metadata: ItemMetadata, created_by: str) -> AssessmentItem
    - Add get_item(item_id: str) -> AssessmentItem
    - Add update_item(item_id: str, content: dict, updated_by: str, changes: str) -> AssessmentItem
    - Add delete_item(item_id: str) -> None (soft delete)
    - Add list_items(metadata_filter: Optional[ItemMetadata] = None) -> List[AssessmentItem]
    - Add import_from_qti(qti_path: str) -> List[AssessmentItem] - uses QTIImporter
    - Add export_to_qti(item_ids: List[str], output_path: str) - uses QTIExporter
    Keep existing methods for backward compatibility with demo.
  </action>
  <verify>
    Run: cd dev_package && python3 -c "
from src.content_bank_service.content_bank import ContentBankService
from src.content_bank_service.models import ItemMetadata, AssessmentItem
svc = ContentBankService('data/challenge_bank.json', 'data/failure_injections.json', seed=42)
# Check service has new methods
assert hasattr(svc, 'items')
assert hasattr(svc, 'create_item')
assert hasattr(svc, 'import_from_qti')
assert hasattr(svc, 'export_to_qti')
print('ContentBankService extended correctly')
"
  </verify>
  <done>
    ContentBankService supports full item lifecycle: create with metadata, get, update with version, delete (soft), list with filters, QTI import/export
  </done>
</task>

</tasks>

<verification>
- Item models support metadata and versioning
- QTI parser handles basic QTI 1.2 format
- ContentBankService integrates QTI import/export and CRUD operations
- Existing demo script continues to work
</verification>

<success_criteria>
1. Items can be imported from QTI packages
2. Items can be exported to QTI format
3. Items store metadata (tags, difficulty, time limits)
4. Item versions are tracked with change history
</success_criteria>

<output>
After completion, create `.planning/phases/01-content-bank-identity/01-content-bank-SUMMARY.md`
</output>
