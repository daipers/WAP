"""
content_bank.py
==============

Provides an interface to the content bank and failure injection definitions.
In a real deployment, these objects would be stored in a database with
version control and sampling constraints.  Here we load them from local
JSON files.

Extended with full CRUD operations, versioning, and QTI import/export.
"""

import json
import random
from typing import Dict, Any, List, Optional
import os

from .models import AssessmentItem, ItemMetadata
from .qti_parser import QTIImporter, QTIExporter


class ContentBankService:
    def __init__(
        self, bank_path: str, injections_path: str, seed: Optional[int] = None
    ):
        self.bank_path = bank_path
        self.injections_path = injections_path
        self._challenges: List[Dict[str, Any]] = []
        self._injections: Dict[str, Dict[str, Any]] = {}
        self._rng = random.Random(seed)

        # New: Assessment item storage
        self.items: Dict[str, AssessmentItem] = {}

        # Legacy support: load existing JSON bank
        self._load_bank()
        self._load_injections()

    def _load_bank(self) -> None:
        with open(self.bank_path, "r", encoding="utf-8") as f:
            self._challenges = json.load(f)

    def _load_injections(self) -> None:
        with open(self.injections_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self._injections = {inj["id"]: inj for inj in data}

    def list_challenges(self) -> List[Dict[str, Any]]:
        return self._challenges

    def get_challenge(self, challenge_id: str) -> Dict[str, Any]:
        for ch in self._challenges:
            if ch["id"] == challenge_id:
                return ch
        raise KeyError(f"Challenge {challenge_id} not found")

    def get_injection(self, injection_id: str) -> Dict[str, Any]:
        if injection_id in self._injections:
            return self._injections[injection_id]
        raise KeyError(f"Injection {injection_id} not found")

    def select_random_challenge(
        self, difficulty: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Select a random challenge optionally filtered by difficulty.
        Uses the service's random generator seeded for reproducibility.
        """
        pool = [
            ch
            for ch in self._challenges
            if difficulty is None or ch["difficulty"] == difficulty
        ]
        if not pool:
            raise ValueError(f"No challenges found for difficulty {difficulty}")
        return self._rng.choice(pool)

    # ========== New CRUD Operations for Assessment Items ==========

    def create_item(
        self, item_id: str, content: dict, metadata: ItemMetadata, created_by: str
    ) -> AssessmentItem:
        """
        Create a new assessment item with initial version.

        Args:
            item_id: Unique identifier for the item
            content: Initial content (prompt, questions, etc.)
            metadata: Item metadata
            created_by: User creating the item

        Returns:
            The created AssessmentItem
        """
        if item_id in self.items:
            raise ValueError(f"Item {item_id} already exists")

        item = AssessmentItem(
            item_id=item_id,
            current_version="1.0",
            metadata=metadata,
            versions=[],
            is_active=True,
        )

        item.add_version(content, created_by, "Initial version")
        self.items[item_id] = item
        return item

    def get_item(self, item_id: str) -> AssessmentItem:
        """
        Get an assessment item by ID.

        Args:
            item_id: The item identifier

        Returns:
            The AssessmentItem

        Raises:
            KeyError: If item not found
        """
        if item_id not in self.items:
            raise KeyError(f"Item {item_id} not found")
        return self.items[item_id]

    def update_item(
        self, item_id: str, content: dict, updated_by: str, changes: str
    ) -> AssessmentItem:
        """
        Update an existing item, creating a new version.

        Args:
            item_id: The item identifier
            content: New content for the item
            updated_by: User making the update
            changes: Description of changes from previous version

        Returns:
            The updated AssessmentItem

        Raises:
            KeyError: If item not found
        """
        if item_id not in self.items:
            raise KeyError(f"Item {item_id} not found")

        item = self.items[item_id]
        item.add_version(content, updated_by, changes)
        return item

    def delete_item(self, item_id: str) -> None:
        """
        Soft-delete an assessment item.

        Args:
            item_id: The item identifier

        Raises:
            KeyError: If item not found
        """
        if item_id not in self.items:
            raise KeyError(f"Item {item_id} not found")

        self.items[item_id].is_active = False

    def list_items(
        self, metadata_filter: Optional[ItemMetadata] = None
    ) -> List[AssessmentItem]:
        """
        List all assessment items, optionally filtered by metadata.

        Args:
            metadata_filter: Optional metadata to filter by

        Returns:
            List of matching AssessmentItem objects
        """
        items = [item for item in self.items.values() if item.is_active]

        if metadata_filter:
            filtered = []
            for item in items:
                # Check each metadata field if specified
                if metadata_filter.tags and not any(
                    t in item.metadata.tags for t in metadata_filter.tags
                ):
                    continue
                if (
                    metadata_filter.difficulty
                    and item.metadata.difficulty != metadata_filter.difficulty
                ):
                    continue
                if (
                    metadata_filter.time_limit_minutes
                    and item.metadata.time_limit_minutes
                    != metadata_filter.time_limit_minutes
                ):
                    continue
                if (
                    metadata_filter.domain
                    and item.metadata.domain != metadata_filter.domain
                ):
                    continue
                if metadata_filter.skill_tags and not any(
                    s in item.metadata.skill_tags for s in metadata_filter.skill_tags
                ):
                    continue
                filtered.append(item)
            return filtered

        return items

    def import_from_qti(self, qti_path: str) -> List[AssessmentItem]:
        """
        Import items from a QTI package.

        Args:
            qti_path: Path to QTI file (QTI 1.2 XML or QTI 3.0 JSON)

        Returns:
            List of imported AssessmentItem objects
        """
        importer = QTIImporter()
        items = importer.import_from_file(qti_path)

        # Add imported items to storage
        for item in items:
            self.items[item.item_id] = item

        return items

    def export_to_qti(self, item_ids: List[str], output_path: str) -> None:
        """
        Export items to QTI 1.2 XML format.

        Args:
            item_ids: List of item IDs to export
            output_path: Path to output file

        Raises:
            KeyError: If any item not found
        """
        items = []
        for item_id in item_ids:
            if item_id not in self.items:
                raise KeyError(f"Item {item_id} not found")
            items.append(self.items[item_id])

        exporter = QTIExporter()
        exporter.export_items(items, output_path)
