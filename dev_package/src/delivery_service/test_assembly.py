"""
test_assembly.py
================

Test assembly service for constructing assessments from the item bank.
Handles item selection, ordering, and validation.
"""

import random
from typing import List, Dict, Any, Optional

from .models import (
    AssessmentDefinition,
    SectionConfig,
    SelectionMode,
    OrderMode,
    NavigationMode,
)
from content_bank_service.content_bank import ContentBankService
from content_bank_service.models import AssessmentItem


class TestAssemblyError(Exception):
    """Exception raised during test assembly."""

    pass


class ValidationError(Exception):
    """Exception raised during validation."""

    pass


class TestAssemblyService:
    """
    Service for assembling tests from the content bank.

    Handles item selection based on section configuration,
    ordering, and validation of assessment definitions.
    """

    def __init__(self, content_bank: ContentBankService, seed: Optional[int] = None):
        """
        Initialize the test assembly service.

        Args:
            content_bank: Reference to ContentBankService for item retrieval
            seed: Optional random seed for reproducible test assembly
        """
        self.content_bank = content_bank
        self._rng = random.Random(seed)

    def select_items(
        self, config: SectionConfig, available_items: List[AssessmentItem]
    ) -> List[AssessmentItem]:
        """
        Select items from the available pool based on selection mode.

        Args:
            config: Section configuration with selection rules
            available_items: List of items to select from

        Returns:
            List of selected items
        """
        if not available_items:
            return []

        selection_mode = config.selection_mode
        items_to_select = config.items_to_select

        # If items_to_select is 0 or greater than available, select all
        if items_to_select <= 0 or items_to_select > len(available_items):
            items_to_select = len(available_items)

        if selection_mode == SelectionMode.RANDOM:
            return self._select_random(available_items, items_to_select)
        elif selection_mode == SelectionMode.FIXED:
            return self._select_fixed(available_items, items_to_select)
        elif selection_mode == SelectionMode.ADAPTIVE:
            return self._select_adaptive(available_items, items_to_select, config)
        else:
            raise TestAssemblyError(f"Unknown selection mode: {selection_mode}")

    def _select_random(
        self, items: List[AssessmentItem], count: int
    ) -> List[AssessmentItem]:
        """Select items randomly from the pool."""
        selected = self._rng.sample(items, min(count, len(items)))
        return selected

    def _select_fixed(
        self, items: List[AssessmentItem], count: int
    ) -> List[AssessmentItem]:
        """Select items in fixed order (first N items)."""
        return items[:count]

    def _select_adaptive(
        self, items: List[AssessmentItem], count: int, config: SectionConfig
    ) -> List[AssessmentItem]:
        """
        Select items adaptively based on parameters.

        Currently implements difficulty-based selection:
        - parameters.get('target_difficulty'): difficulty level (1-5)
        - parameters.get('difficulty_range'): acceptable range around target
        """
        params = config.parameters
        target_difficulty = params.get("target_difficulty", 3)
        difficulty_range = params.get("difficulty_range", 1)

        # Filter by difficulty
        filtered = [
            item
            for item in items
            if abs(item.metadata.difficulty - target_difficulty) <= difficulty_range
        ]

        # If not enough items match, fall back to random
        if len(filtered) >= count:
            return self._rng.sample(filtered, count)
        else:
            # Mix of filtered and other items
            remaining_needed = count - len(filtered)
            other_items = [item for item in items if item not in filtered]
            additional = self._rng.sample(
                other_items, min(remaining_needed, len(other_items))
            )
            return filtered + additional

    def order_items(
        self, items: List[AssessmentItem], mode: OrderMode
    ) -> List[AssessmentItem]:
        """
        Order items based on the specified mode.

        Args:
            items: List of items to order
            mode: Order mode (SEQUENTIAL, RANDOM, SHUFFLE_SECTIONS)

        Returns:
            Ordered list of items
        """
        if not items:
            return []

        if mode == OrderMode.SEQUENTIAL:
            return items  # Keep original order
        elif mode == OrderMode.RANDOM:
            return self._rng.sample(items, len(items))
        elif mode == OrderMode.SHUFFLE_SECTIONS:
            # This is typically applied at section level, but can also
            # mean random within the item list
            return self._rng.sample(items, len(items))
        else:
            raise TestAssemblyError(f"Unknown order mode: {mode}")

    def build_test(self, definition: AssessmentDefinition) -> Dict[str, Any]:
        """
        Assemble a complete test from an assessment definition.

        Args:
            definition: Assessment definition with sections and rules

        Returns:
            Dictionary containing:
            - assessment_id: The assessment ID
            - title: Assessment title
            - sections: List of assembled sections with items
            - navigation_mode: Navigation mode
            - time_limit_seconds: Overall time limit
            - attempt_limit: Maximum attempts
        """
        assembled_sections = []

        for section_config in definition.sections:
            # Get available items from content bank
            available_items = []
            for item_id in section_config.item_pool_ids:
                try:
                    item = self.content_bank.get_item(item_id)
                    if item.is_active:
                        available_items.append(item)
                except KeyError:
                    # Skip items that don't exist in content bank
                    continue

            # Select items based on selection mode
            selected_items = self.select_items(section_config, available_items)

            # Order items based on order mode
            ordered_items = self.order_items(selected_items, section_config.order_mode)

            assembled_sections.append(
                {
                    "section_id": section_config.section_id,
                    "name": section_config.name,
                    "items": ordered_items,
                    "item_count": len(ordered_items),
                    "time_limit_seconds": section_config.time_limit_seconds,
                }
            )

        return {
            "assessment_id": definition.assessment_id,
            "title": definition.title,
            "sections": assembled_sections,
            "total_items": sum(s["item_count"] for s in assembled_sections),
            "navigation_mode": definition.navigation_mode.value,
            "time_limit_seconds": definition.time_limit_seconds,
            "attempt_limit": definition.attempt_limit,
        }

    def validate_assessment(self, definition: AssessmentDefinition) -> Dict[str, Any]:
        """
        Validate an assessment definition.

        Checks:
        - All referenced items exist in content bank
        - All referenced sections exist
        - Configuration values are valid

        Args:
            definition: Assessment definition to validate

        Returns:
            Validation result with status and any errors
        """
        errors = []
        warnings = []

        # Check assessment has sections
        if not definition.sections:
            errors.append("Assessment must have at least one section")

        # Track all item IDs referenced
        all_item_ids = set()

        for section in definition.sections:
            # Check section has items
            if not section.item_pool_ids:
                warnings.append(f"Section '{section.section_id}' has no items in pool")

            # Check each item exists in content bank
            for item_id in section.item_pool_ids:
                all_item_ids.add(item_id)
                try:
                    item = self.content_bank.get_item(item_id)
                    if not item.is_active:
                        warnings.append(
                            f"Item '{item_id}' in section '{section.section_id}' "
                            "is marked as inactive"
                        )
                except KeyError:
                    errors.append(
                        f"Item '{item_id}' referenced in section '{section.section_id}' "
                        "does not exist in content bank"
                    )

            # Validate items_to_select
            if section.items_to_select < 0:
                errors.append(
                    f"Section '{section.section_id}': items_to_select cannot be negative"
                )

            if section.items_to_select > len(section.item_pool_ids):
                warnings.append(
                    f"Section '{section.section_id}': items_to_select ({section.items_to_select}) "
                    f"exceeds available items ({len(section.item_pool_ids)})"
                )

        # Check for duplicate item IDs across sections (warning only)
        seen_ids = set()
        for item_id in all_item_ids:
            if item_id in seen_ids:
                warnings.append(f"Item '{item_id}' is referenced in multiple sections")
            seen_ids.add(item_id)

        is_valid = len(errors) == 0

        return {
            "is_valid": is_valid,
            "errors": errors,
            "warnings": warnings,
            "assessment_id": definition.assessment_id,
        }
