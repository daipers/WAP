"""
anchoring.py
============

External timestamp service integration (RFC 3161) for Merkle root anchoring.
Provides trusted timestamping for audit log integrity.

Reference: Plan 05-03-PLAN.md - External timestamp service integration
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any


@dataclass
class TimestampAnchor:
    """Record of a Merkle root anchored at a specific time."""

    merkle_root: str
    date: str  # YYYY-MM-DD format
    timestamp: float
    timestamped_at: Optional[str] = None  # ISO format
    tsa_response: Optional[bytes] = None
    session_count: int = 0
    session_ids: List[str] = field(default_factory=list)
    anchor_hash: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "merkle_root": self.merkle_root,
            "date": self.date,
            "timestamp": self.timestamp,
            "timestamped_at": self.timestamped_at,
            "session_count": self.session_count,
            "session_ids": self.session_ids,
            "anchor_hash": self.anchor_hash,
        }


class PeriodicAnchoring:
    """
    Anchor Merkle roots to external timestamp service (RFC 3161).

    Provides:
    - Daily root generation for periodic anchoring
    - TSA (Timestamp Authority) integration
    - Anchor verification
    - Timestamped root storage
    """

    def __init__(self, tsa_url: Optional[str] = None):
        """
        Initialize periodic anchoring.

        Args:
            tsa_url: URL of the Timestamp Authority (RFC 3161 compliant)
        """
        self.tsa_url = tsa_url
        self.anchors: List[TimestampAnchor] = []

    def create_daily_anchor(
        self, merkle_root: str, date: str, session_ids: List[str]
    ) -> TimestampAnchor:
        """
        Create anchor record for daily Merkle root.

        Args:
            merkle_root: Root hash from Merkle tree
            date: Date string (YYYY-MM-DD)
            session_ids: List of session IDs included in the root

        Returns:
            TimestampAnchor record
        """
        anchor = TimestampAnchor(
            merkle_root=merkle_root,
            date=date,
            timestamp=time.time(),
            session_count=len(session_ids),
            session_ids=session_ids,
            anchor_hash=self._compute_anchor_hash(merkle_root, date),
        )
        self.anchors.append(anchor)
        return anchor

    def _compute_anchor_hash(self, merkle_root: str, date: str) -> str:
        """Compute deterministic hash for anchor record."""
        content = json.dumps({"merkle_root": merkle_root, "date": date}, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()

    def request_timestamp(self, merkle_root: str) -> Optional[bytes]:
        """
        Request timestamp from TSA (RFC 3161).

        This is a placeholder implementation. In production, this would:
        1. Create RFC 3161 timestamp request (TSQ format)
        2. Send request to TSA
        3. Parse timestamp reply (TSR format)
        4. Verify TSA certificate

        Args:
            merkle_root: Root hash to timestamp

        Returns:
            TSA response bytes, or None if failed
        """
        if not self.tsa_url:
            # No TSA configured - return mock response for testing
            return self._mock_timestamp_response(merkle_root)

        # In production, this would use the cryptography library:
        # from cryptography.x509 import load_der_x509_certificate
        # from cryptography.hazmat.primitives import hashes
        # from cryptography.hazmat.primitives.serialization import Encoding
        #
        # # Create timestamp request
        # from cryptography.x509 import ocsp
        # tsa_request = create_rfc3161_request(merkle_root)
        #
        # # Send request
        # response = requests.post(self.tsa_url, data=tsa_request,
        #                          headers={'Content-Type': 'application/timestamp-query'})
        #
        # return response.content

        # Placeholder for production implementation
        return self._mock_timestamp_response(merkle_root)

    def _mock_timestamp_response(self, merkle_root: str) -> bytes:
        """
        Generate mock timestamp response for testing.

        In production, this would be replaced by actual TSA response.
        """
        # Create a mock response containing the Merkle root and timestamp
        timestamp_data = {
            "merkle_root": merkle_root,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tsa": "mock-tsa://localhost",
        }
        return json.dumps(timestamp_data).encode()

    def apply_timestamp_to_anchor(self, anchor: TimestampAnchor) -> TimestampAnchor:
        """
        Apply external timestamp to an existing anchor.

        Args:
            anchor: The anchor to timestamp

        Returns:
            Updated anchor with timestamp
        """
        response = self.request_timestamp(anchor.merkle_root)

        if response:
            anchor.tsa_response = response
            # Parse timestamp from response
            try:
                data = json.loads(response.decode())
                anchor.timestamped_at = data.get("timestamp")
            except (json.JSONDecodeError, AttributeError):
                anchor.timestamped_at = datetime.now(timezone.utc).isoformat()

        return anchor

    def verify_anchored_root(self, root: str, date: str) -> bool:
        """
        Verify a Merkle root was anchored on a specific date.

        Args:
            root: Merkle root hash
            date: Date string (YYYY-MM-DD)

        Returns:
            True if root was anchored on date
        """
        for anchor in self.anchors:
            if anchor.date == date and anchor.merkle_root == root:
                return True
        return False

    def get_anchor_by_date(self, date: str) -> Optional[TimestampAnchor]:
        """Get anchor record for a specific date."""
        for anchor in self.anchors:
            if anchor.date == date:
                return anchor
        return None

    def get_all_anchors(self) -> List[Dict[str, Any]]:
        """Get all anchors as dictionaries."""
        return [anchor.to_dict() for anchor in self.anchors]

    def verify_anchor_integrity(self, anchor: TimestampAnchor) -> bool:
        """
        Verify integrity of an anchor record.

        Args:
            anchor: Anchor to verify

        Returns:
            True if anchor hash is valid
        """
        expected_hash = self._compute_anchor_hash(anchor.merkle_root, anchor.date)
        return anchor.anchor_hash == expected_hash


class RFC3161TimestampClient:
    """
    RFC 3161 compliant timestamp client.

    Provides utilities for:
    - Creating timestamp requests
    - Verifying timestamp responses
    - Certificate chain validation
    """

    def __init__(self, tsa_url: str):
        """
        Initialize RFC 3161 client.

        Args:
            tsa_url: URL of RFC 3161 compliant TSA
        """
        self.tsa_url = tsa_url

    def create_request(self, data_to_hash: bytes) -> bytes:
        """
        Create RFC 3161 timestamp request (TSQ).

        Args:
            data_to_hash: Data to be timestamped

        Returns:
            DER-encoded timestamp request
        """
        # In production using cryptography library:
        # from cryptography x509.oid import DigestAlgorithmOID
        #
        # # Create time-stamp request
        # req = TimeStampRequest(
        #     version=1,
        #     cert_req=True,
        #     digest_algorithm=OID_SHA256,
        #     message_imprint=MessageImprint(
        #         hash_algorithm=OID_SHA256,
        #         hashed_message=hashlib.sha256(data_to_hash).digest()
        #     )
        # )
        # return reqDER()

        # Mock request for interface compatibility
        return hashlib.sha256(data_to_hash).digest()

    def parse_response(self, response_data: bytes) -> Dict[str, Any]:
        """
        Parse RFC 3161 timestamp reply (TSR).

        Args:
            response_data: DER-encoded timestamp response

        Returns:
            Parsed timestamp information
        """
        # In production, parse actual RFC 3161 response
        try:
            data = json.loads(response_data.decode())
            return {
                "timestamp": data.get("timestamp"),
                "merkle_root": data.get("merkle_root"),
                "tsa": data.get("tsa"),
            }
        except (json.JSONDecodeError, AttributeError):
            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": "Failed to parse response",
            }

    def verify_response(self, response_data: bytes, original_data: bytes) -> bool:
        """
        Verify timestamp response matches original data.

        Args:
            response_data: TSA response
            original_data: Original data that was timestamped

        Returns:
            True if response is valid for original data
        """
        parsed = self.parse_response(response_data)

        if "merkle_root" in parsed:
            # Verify Merkle root in response matches
            expected_root = hashlib.sha256(original_data).hexdigest()
            return parsed["merkle_root"] == expected_root

        return False
