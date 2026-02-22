"""
models.py
=========

Data models for the Content Bank Service.
Provides item metadata, versioning, and assessment item representations.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import time


@dataclass
class ItemMetadata:
    """Metadata associated with an assessment item."""

    tags: List[str] = field(default_factory=list)
    difficulty: int = 1  # 1-5 scale
    time_limit_minutes: int = 0
    domain: str = ""
    skill_tags: List[str] = field(default_factory=list)


@dataclass
class ItemVersion:
    """Represents a single version of an assessment item."""

    version: str
    created_at: float
    created_by: str
    changes: str
    content: dict


@dataclass
class AssessmentItem:
    """
    Represents an assessment item with metadata and version history.
    """

    item_id: str
    current_version: str
    metadata: ItemMetadata
    versions: List[ItemVersion] = field(default_factory=list)
    is_active: bool = True

    def add_version(self, content: dict, created_by: str, changes: str) -> ItemVersion:
        """
        Add a new version of the item.

        Args:
            content: The item content (prompt, questions, etc.)
            created_by: User who created this version
            changes: Description of changes from previous version

        Returns:
            The newly created ItemVersion
        """
        # Determine version number based on current_version and existing versions
        if self.versions:
            # Increment from the last version
            try:
                major, minor = self.current_version.split(".")
                new_minor = int(minor) + 1
                new_version = f"{major}.{new_minor}"
            except (ValueError, AttributeError):
                # Fallback: use timestamp-based version
                new_version = str(int(time.time()))
        else:
            # First version
            new_version = "1.0"

        version = ItemVersion(
            version=new_version,
            created_at=time.time(),
            created_by=created_by,
            changes=changes,
            content=content,
        )

        self.versions.append(version)
        self.current_version = new_version
        return version

    def get_version(self, version: str) -> Optional[ItemVersion]:
        """
        Retrieve a specific version of the item.

        Args:
            version: The version string to retrieve

        Returns:
            The ItemVersion if found, None otherwise
        """
        for v in self.versions:
            if v.version == version:
                return v
        return None

    def get_latest_content(self) -> dict:
        """Get the content of the current version."""
        latest = self.get_version(self.current_version)
        if latest:
            return latest.content
        return {}
