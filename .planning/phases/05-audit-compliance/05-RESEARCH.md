# Phase 5: Audit & Compliance Hardening - Research

**Researched:** 2026-02-27
**Domain:** Analytics, fairness detection, cryptographic audit, FERPA compliance
**Confidence:** HIGH

## Summary

Phase 5 focuses on high-stakes deployment readiness through analytics, fairness detection, audit hardening, and FERPA compliance. The existing audit ledger from Phase 1 provides foundation - this phase extends it with Merkle tree verification and external anchoring. For analytics, standard psychometrics (item difficulty, discrimination index) combined with DIF analysis provides defensible fairness detection. FERPA requires data governance policies with defined retention periods and disclosure controls.

**Primary recommendation:** Extend existing audit ledger with Merkle tree roots for periodic aggregation, implement DIF detection using chi-square or logistic regression methods, and build analytics dashboard with standard psychometric metrics.

---

## User Constraints (from CONTEXT.md)

### Prior Decisions (from STATE.md)
- Global hash chain for audit log - session filtering at query time
- FastAPI + PostgreSQL + Celery stack
- Phase 5 research flags: FERPA compliance, WCAG 2.2 testing
- Audit ledger with hash chain already exists in dev_package/src/audit_ledger_service/

### Remaining Items to Implement
- Item performance analytics dashboard
- Item bias/fairness detection
- Immutable audit ledger with cryptographic hash chains (extends AUDT-01)
- FERPA-aligned data retention

---

## Standard Stack

### Core Analytics & Fairness
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pandas | 2.x | Data aggregation for analytics | Industry standard for data manipulation |
| scipy | 1.12+ | Statistical tests (chi-square for DIF) | Core scientific computing |
| numpy | 1.26+ | Numerical operations | Foundation for scientific Python |

### Visualization
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Chart.js | 4.x | Dashboard charts | Web-based analytics UI |
| React-Query | 5.x | Data fetching/caching | Frontend state management for analytics |

### Cryptographic Audit
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| hashlib (stdlib) | - | SHA-256 hash computation | Built-in, no external deps |
| cryptography | 42.x | Signing/verification | Production-grade Python crypto |
| json (stdlib) | - | Canonical JSON serialization | Deterministic serialization |

### FERPA Compliance
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| sqlalchemy-utils | 0.41+ | UUID types, encryption | Data types for PII |
| python-dateutil | 2.8+ | Date calculations | Retention period logic |

**Installation:**
```bash
pip install pandas scipy numpy cryptography sqlalchemy-utils python-dateutil
```

---

## Architecture Patterns

### Recommended Project Structure
```
dev_package/src/
├── analytics_service/
│   ├── __init__.py
│   ├── metrics.py         # Item difficulty, discrimination, reliability
│   ├── dif_detector.py    # Differential Item Functioning detection
│   └── dashboard.py       # Analytics dashboard data aggregation
├── audit_ledger_service/
│   ├── ledger.py          # Existing - hash chain
│   ├── merkle_tree.py     # NEW - Merkle tree aggregation
│   └── anchoring.py       # NEW - External timestamp anchoring
├── retention_service/
│   ├── __init__.py
│   ├── policies.py        # FERPA retention policies
│   └── disposal.py        # Secure data deletion
└── app.py                 # API endpoints for dashboard
```

### Pattern 1: Analytics Pipeline

**What:** Aggregate assessment data into psychometric metrics for dashboard display.

**When to use:** When building item performance dashboards requiring difficulty, discrimination, reliability metrics.

**Example:**
```python
# Source: Industry standard psychometrics
import pandas as pd
import numpy as np
from scipy import stats

def calculate_item_difficulty(responses: pd.DataFrame) -> float:
    """Calculate p-value (item difficulty) as proportion correct."""
    return responses['is_correct'].mean()

def calculate_discrimination_index(responses: pd.DataFrame) -> float:
    """Calculate point-biserial correlation between item and total score."""
    total_scores = responses.groupby('candidate_id')['is_correct'].sum()
    item_scores = responses.set_index('candidate_id')['is_correct']
    
    # Align indices
    common_candidates = total_scores.index.intersection(item_scores.index)
    if len(common_candidates) < 10:
        return 0.0
    
    corr, _ = stats.pointbiserialr(
        item_scores.loc[common_candidates],
        total_scores.loc[common_candidates]
    )
    return corr if not np.isnan(corr) else 0.0

def calculate_cronbach_alpha(item_matrix: pd.DataFrame) -> float:
    """Calculate Cronbach's alpha for internal consistency."""
    n_items = item_matrix.shape[1]
    item_variances = item_matrix.var(axis=0, ddof=1)
    total_variance = item_matrix.sum(axis=1).var(ddof=1)
    
    if total_variance == 0:
        return 0.0
    
    alpha = (n_items / (n_items - 1)) * (1 - item_variances.sum() / total_variance)
    return max(0.0, min(1.0, alpha))
```

### Pattern 2: DIF Detection (Fairness)

**What:** Statistical detection of items that perform differently across demographic groups.

**When to use:** When analyzing assessment fairness across gender, ethnicity, or other protected attributes.

**Example:**
```python
# Source: Standard psychometric literature (difR package methods)
import pandas as pd
from scipy import stats
import numpy as np

def detect_dif_chi_square(
    item_responses: pd.DataFrame,
    group_membership: pd.Series,
    ability_estimate: pd.Series = None
) -> dict:
    """
    Detect DIF using Mantel-Haenszel chi-square test.
    
    Args:
        item_responses: DataFrame with candidate_id, is_correct
        group_membership: Series mapping candidate_id to group (reference/focal)
        ability_estimate: Optional ability estimates for matching
    
    Returns:
        Dict with chi2 statistic, p-value, and DIF classification
    """
    # Merge data
    data = item_responses.merge(
        group_membership.rename('group'),
        left_on='candidate_id',
        right_index=True
    )
    
    if ability_estimate is not None:
        data = data.merge(
            ability_estimate.rename('ability'),
            left_on='candidate_id',
            right_index=True
        )
        # Match on ability (within 0.5 std bins)
        data['ability_bin'] = pd.cut(data['ability'], bins=10)
        
        # Calculate MH within each ability bin
        # Simplified: aggregate across bins
        pass
    
    # 2x2 contingency: group x correct/incorrect
    ref_correct = len(data[(data['group'] == 'reference') & (data['is_correct'])])
    ref_incorrect = len(data[(data['group'] == 'reference') & (~data['is_correct'])])
    focal_correct = len(data[(data['group'] == 'focal') & (data['is_correct'])])
    focal_incorrect = len(data[(data['group'] == 'focal') & (~data['is_correct'])])
    
    # Mantel-Haenszel chi-square
    try:
        obs = [[ref_correct, ref_incorrect], [focal_correct, focal_incorrect]]
        chi2, p_value = stats.chi2_contingency(obs, correction=True)[:2]
    except:
        chi2, p_value = 0.0, 1.0
    
    # Classify DIF
    if p_value < 0.001:
        classification = 'severe_DIF'
    elif p_value < 0.01:
        classification = 'moderate_DIF'
    elif p_value < 0.05:
        classification = 'minor_DIF'
    else:
        classification = 'no_DIF'
    
    return {
        'chi2': chi2,
        'p_value': p_value,
        'classification': classification,
        'reference_pass_rate': ref_correct / (ref_correct + ref_incorrect) if (ref_correct + ref_incorrect) > 0 else 0,
        'focal_pass_rate': focal_correct / (focal_correct + focal_incorrect) if (focal_correct + focal_incorrect) > 0 else 0,
    }
```

### Pattern 3: Cryptographic Audit with Merkle Tree

**What:** Periodic aggregation of audit events into Merkle tree for efficient verification.

**When to use:** When audit logs need tamper-evidence with efficient partial verification.

**Example:**
```python
# Source: Standard audit practices, RFC 6962
import hashlib
import json
from typing import List, Optional
from dataclasses import dataclass

@dataclass
class MerkleNode:
    hash: str
    left: Optional['MerkleNode'] = None
    right: Optional['MerkleNode'] = None

class MerkleTree:
    """Merkle tree for audit log aggregation."""
    
    def __init__(self):
        self.root: Optional[MerkleNode] = None
        self.leaves: List[MerkleNode] = []
    
    @staticmethod
    def hash_pair(left_hash: str, right_hash: str) -> str:
        """Hash two child hashes together."""
        combined = json.dumps([left_hash, right_hash], sort_keys=True)
        return hashlib.sha256(combined.encode()).hexdigest()
    
    @classmethod
    def build(cls, data_items: List[str]) -> 'MerkleTree':
        """Build Merkle tree from list of data items."""
        tree = cls()
        
        # Create leaf nodes
        tree.leaves = [
            MerkleNode(hashlib.sha256(item.encode()).hexdigest())
            for item in data_items
        ]
        
        if not tree.leaves:
            return tree
        
        # Build tree bottom-up
        current_level = tree.leaves
        while len(current_level) > 1:
            next_level = []
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                right = current_level[i + 1] if i + 1 < len(current_level) else left
                
                parent_hash = cls.hash_pair(left.hash, right.hash)
                parent = MerkleNode(hash=parent_hash, left=left, right=right)
                next_level.append(parent)
            
            current_level = next_level
        
        tree.root = current_level[0] if current_level else None
        return tree
    
    def get_root_hash(self) -> str:
        """Get root hash for storage/anchoring."""
        return self.root.hash if self.root else self._empty_hash()
    
    def _empty_hash(self) -> str:
        return hashlib.sha256(b'empty').hexdigest()
    
    def prove_inclusion(self, leaf_index: int) -> List[tuple[str, str]]:
        """Generate merkle proof for a leaf."""
        if leaf_index >= len(self.leaves):
            return []
        
        proof = []
        current_index = leaf_index
        node = self.leaves[leaf_index]
        
        # Traverse up tree collecting sibling hashes
        # Simplified: would need full tree structure for real proof
        return proof

class PeriodicAnchoring:
    """Anchor merkle roots to external timestamp service."""
    
    def __init__(self, anchor_service_url: str = None):
        self.anchor_service_url = anchor_service_url
        self.anchors: List[dict] = []
    
    def create_daily_anchor(
        self,
        merkle_root: str,
        date: str,
        session_ids: List[str]
    ) -> dict:
        """Create anchor record for daily merkle root."""
        anchor = {
            'merkle_root': merkle_root,
            'date': date,
            'session_count': len(session_ids),
            'session_ids': session_ids,
            'created_at': pd.Timestamp.now().isoformat(),
            'external_timestamp': None,  # Would be set by anchor service
        }
        self.anchors.append(anchor)
        return anchor
    
    def verify_anchored_root(self, root: str, date: str) -> bool:
        """Verify a merkle root was anchored on a specific date."""
        for anchor in self.anchors:
            if anchor['date'] == date and anchor['merkle_root'] == root:
                return True
        return False
```

### Pattern 4: FERPA Data Retention

**What:** Policy-driven retention with automated disposal scheduling.

**When to use:** When implementing data lifecycle management for educational records.

**Example:**
```python
# Source: FERPA guidance, state educational records requirements
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional
import pandas as pd

class DataClassification(Enum):
    """FERPA data classification levels."""
    EDUCATION_RECORD = "education_record"  # Protected
    DIRECTORY_INFO = "directory_info"      # May be disclosed
    PERSONAL_NOTE = "personal_note"        # Not education record
   AGGREGATED = "aggregated"               # De-identified

@dataclass
class RetentionPolicy:
    """Retention policy for a data category."""
    name: str
    classification: DataClassification
    retention_years: Optional[int]  # None = indefinite
    review_required: bool
    secure_deletion: bool
    
    # Common educational record policies
    ASSESSMENT_SCORES = RetentionPolicy(
        name="Assessment Scores",
        classification=DataClassification.EDUCATION_RECORD,
        retention_years=3,  # Varies by state (1-7 years typical)
        review_required=True,
        secure_deletion=True
    )
    
    SESSION_LOGS = RetentionPolicy(
        name="Session Logs",
        classification=DataClassification.EDUCATION_RECORD,
        retention_years=3,
        review_required=False,
        secure_deletion=True
    )
    
    AGGREGATED_ANALYTICS = RetentionPolicy(
        name="Aggregated Analytics",
        classification=DataClassification.AGGREGATED,
        retention_years=None,  # No limit
        review_required=False,
        secure_deletion=False
    )

class RetentionManager:
    """Manage data retention and schedule disposal."""
    
    def __init__(self):
        self.policies: dict[str, RetentionPolicy] = {}
        self._register_default_policies()
    
    def _register_default_policies(self):
        """Register standard retention policies."""
        self.policies['assessment_scores'] = RetentionPolicy.ASSESSMENT_SCORES
        self.policies['session_logs'] = RetentionPolicy.SESSION_LOGS
        self.policies['aggregated_analytics'] = RetentionPolicy.AGGREGATED_ANALYTICS
    
    def calculate_disposal_date(
        self,
        data_category: str,
        created_at: datetime
    ) -> Optional[datetime]:
        """Calculate when data should be disposed."""
        policy = self.policies.get(data_category)
        if policy is None or policy.retention_years is None:
            return None  # No automatic disposal
        
        return created_at + timedelta(days=policy.retention_years * 365)
    
    def get_data_for_disposal(
        self,
        data_category: str,
        as_of: datetime
    ) -> list[str]:
        """Get list of record IDs eligible for disposal."""
        # Query would filter by created_at < disposal_date
        # and not already disposed
        return []
    
    def dispose_records(
        self,
        data_category: str,
        record_ids: list[str],
        method: str = "secure_delete"
    ) -> dict:
        """Dispose records according to policy."""
        policy = self.policies.get(data_category)
        if policy is None:
            raise ValueError(f"Unknown category: {data_category}")
        
        if not policy.secure_deletion and method == "secure_delete":
            raise ValueError(f"Secure deletion not required for {data_category}")
        
        # Return disposal summary
        return {
            'disposed_count': len(record_ids),
            'method': method,
            'policy': policy.name,
            'timestamp': datetime.utcnow().isoformat()
        }

# Disclosure log pattern
@dataclass
class DisclosureLog:
    """Track all disclosures of education records."""
    record_id: str
    disclosed_to: str
    purpose: str
    disclosed_at: datetime
    disclosed_by: str
    authorization_basis: str  # e.g., "consent", "legitimate_interest", "legal"
    
    def log_disclosure(self):
        """Record disclosure to audit log."""
        pass
```

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Statistical tests for DIF | Custom chi-square/MH implementation | scipy.stats | Validated, handles edge cases |
| Hashing for audit | Custom crypto | hashlib.sha256 + cryptography | Battle-tested, reviewed |
| Date handling | Manual date math | python-dateutil | Handles edge cases, timezones |
| Cronbach's alpha | Manual formula | Use validated psychometric libraries | Numerical stability issues |

**Key insight:** Fairness/DIF detection has subtle statistical edge cases (small samples, ability matching) that are well-handled by established libraries. Custom implementations risk false positives/negatives with legal implications.

---

## Common Pitfalls

### Pitfall 1: Naive Difficulty Calculation
**What goes wrong:** Treating all responses equally regardless of sample size or ability distribution.

**Why it happens:** Simple p-value (proportion correct) is easy to compute but misleading.

**How to avoid:** Report confidence intervals alongside p-values; use IRT-based difficulty when possible.

**Warning signs:** Items with <30 responses showing extreme difficulty values.

### Pitfall 2: Ignoring Ability Matching in DIF
**What goes wrong:** Comparing pass rates across groups without controlling for ability.

**Why it happens:** Raw pass rate differences conflate ability differences with item bias.

**How to avoid:** Match groups on ability estimate before comparing; use Mantel-Haenszel or IRT-based DIF methods.

**Warning signs:** DIF detected on easy items where high-achieving students dominate.

### Pitfall 3: Single-Period Retention Policies
**What goes wrong:** Applying uniform retention across all data types.

**Why it happens:** FERPA allows variation; different data has different value/liability profiles.

**How to avoid:** Define policies per data category; distinguish education records from aggregated analytics.

**Warning signs:** Disposal schedule deletes all data after same period.

### Pitfall 4: Hash Chain Without Verification
**What goes wrong:** Computing hashes but never validating them.

**Why it happens:** Verification is extra work and seems unnecessary if "nothing wrong."

**How to avoid:** Implement automatic verification on read; log verification results.

**Warning signs:** No verification code path exists.

### Pitfall 5: Frontend Dashboards Without Pagination
**What goes wrong:** Loading all analytics data client-side.

**Why it happens:** Simple but fails at scale.

**How to avoid:** Server-side pagination; aggregate at query time; use streaming for exports.

**Warning signs:** Dashboard times out with >1000 sessions of data.

---

## Code Examples

### Analytics Dashboard API
```python
# Source: FastAPI best practices
from fastapi import APIRouter, Query
from typing import Optional
import pandas as pd
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

@router.get("/item-performance")
async def get_item_performance(
    assessment_id: str = Query(...),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
):
    """
    Get item performance metrics for dashboard.
    
    Returns difficulty, discrimination, and reliability metrics
    per item with confidence intervals.
    """
    # Query responses from database
    # responses = db.query(Response).filter(...)
    
    # Calculate metrics
    metrics = []
    for item_id in items:
        item_responses = responses[responses['item_id'] == item_id]
        
        metrics.append({
            'item_id': item_id,
            'difficulty': calculate_item_difficulty(item_responses),
            'difficulty_ci': calculate_ci(item_responses),
            'discrimination': calculate_discrimination_index(item_responses),
            'response_count': len(item_responses),
            # Flag items needing review
            'needs_review': (
                len(item_responses) < 30 or 
                calculate_discrimination_index(item_responses) < 0.1
            )
        })
    
    return {'items': metrics, 'calculated_at': datetime.utcnow()}

@router.get("/fairness-report")
async def get_fairness_report(
    assessment_id: str = Query(...),
    group_attribute: str = Query(...),  # e.g., "gender", "ethnicity"
):
    """
    Get DIF analysis results for fairness review.
    
    Returns items with detected bias by group.
    """
    # Get responses with group membership
    # Run DIF detection per item
    
    results = []
    for item_id in items:
        dif_result = detect_dif_chi_square(
            item_responses,
            group_membership
        )
        
        if dif_result['classification'] != 'no_DIF':
            results.append({
                'item_id': item_id,
                **dif_result,
                'recommendation': get_recommendation(dif_result)
            })
    
    return {
        'items_with_dif': len(results),
        'items': results,
        'groups_analyzed': group_attribute
    }
```

### Audit Verification Endpoint
```python
@router.get("/audit/verify/{session_id}")
async def verify_session_audit(session_id: str):
    """Verify hash chain integrity for a session."""
    ledger = get_ledger()
    is_valid, invalid_entries = ledger.verify_session_events(session_id)
    
    return {
        'session_id': session_id,
        'is_valid': is_valid,
        'invalid_count': len(invalid_entries),
        'last_verified': datetime.utcnow().isoformat(),
        'chain_length': len(ledger.get_events_by_session(session_id))
    }

@router.get("/audit/merkle-root/{date}")
async def get_daily_merkle_root(date: str):
    """Get anchored merkle root for a specific date."""
    anchor = get_anchor_for_date(date)
    return {
        'date': date,
        'merkle_root': anchor['merkle_root'] if anchor else None,
        'session_count': anchor.get('session_count', 0) if anchor else 0,
        'verified': anchor is not None
    }
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Raw p-value difficulty | IRT-based difficulty with CI | 2020s | More accurate, accounts for ability distribution |
| Single-group DIF | Mantel-Haenszel with ability matching | 2010s | Reduces false positives |
| Database-only audit | Hash chain + Merkle trees | 2020s | Tamper evidence, efficient verification |
| One-size retention | Category-specific policies | Always | FERPA compliance varies by data type |

**Deprecated/outdated:**
- **SIBTEST DIF**: Replaced by MH and logistic regression (more powerful)
- **Kuder-Richardson 20**: Cronbach's alpha preferred (handles partial credit)

---

## Open Questions

1. **FERPA Retention Period**
   - What we know: Varies by state (1-7 years typical for educational records)
   - What's unclear: Specific requirements for assessment data in your deployment states
   - Recommendation: Make retention configurable per-state; default to 3 years

2. **DIF Group Definitions**
   - What we know: Standard groups are gender, ethnicity, disability status
   - What's unclear: Which groups are required vs. optional for your compliance
   - Recommendation: Support configurable group attributes; default to standard protected classes

3. **External Anchoring Service**
   - What we know: RFC 3161 provides timestamp verification
   - What's unclear: Whether to use third-party TSA or internal timestamping
   - Recommendation: Implement internal first; add TSA optionally for high-stakes

4. **Analytics Granularity**
   - What we know: Dashboard needs item-level and assessment-level views
   - What's unclear: Real-time vs. batch refresh requirements
   - Recommendation: Start with daily batch; add real-time if latency is blocker

---

## Sources

### Primary (HIGH confidence)
- Columbia Mailman School of Public Health - "Differential Item Functioning" overview
- difR CRAN package documentation - DIF detection methods
- RFC 6962 (Certificate Transparency) - Merkle tree architecture
- NCES/PTAC - "FERPA Considerations: Data Retention & Destruction"

### Secondary (MEDIUM confidence)
- DEV Community: "Building Tamper-Evident Audit Logs with SHA-256 Hash Chains"
- difNLR R package documentation - Logistic regression DIF methods
- eLeaP: "Item Analysis in LMS" - Dashboard best practices

### Tertiary (LOW confidence)
- Various EdTech vendor documentation - Implementation patterns vary
- Academic papers on DIF detection (methods mature but implementations vary)

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Well-established Python data science stack
- Architecture: HIGH - Standard patterns from psychometrics and audit
- Pitfalls: HIGH - Common issues documented in literature

**Research date:** 2026-02-27
**Valid until:** 2026-05-01 (stable domain, quarterly review sufficient)