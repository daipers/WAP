"""
periodic_aggregation.py
=======================

Periodic Merkle root anchoring (daily/weekly/monthly).
Coordinates aggregation, anchoring, and timestamp requests.

Reference: Plan 05-03-PLAN.md - Periodic root anchoring
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, date, timezone, timedelta
from typing import Dict, Any, List, Optional, Callable
from enum import Enum

from audit_ledger_service.merkle_tree import MerkleTree
from audit_ledger_service.anchoring import PeriodicAnchoring, TimestampAnchor
from audit_ledger_service.ledger import AuditLedger, LedgerEntry


class AggregationPeriod(Enum):
    """Supported aggregation periods."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


@dataclass
class AggregationResult:
    """Result of periodic aggregation."""

    period: str
    start_date: str
    end_date: str
    event_count: int
    session_count: int
    merkle_root: str
    anchor: Optional[TimestampAnchor] = None
    anchored: bool = False
    timestamped: bool = False
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "period": self.period,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "event_count": self.event_count,
            "session_count": self.session_count,
            "merkle_root": self.merkle_root,
            "anchor": self.anchor.to_dict() if self.anchor else None,
            "anchored": self.anchored,
            "timestamped": self.timestamped,
            "created_at": self.created_at,
        }


class PeriodicAggregation:
    """
    Periodic Merkle root anchoring for audit logs.

    Provides:
    - Daily/weekly/monthly aggregation
    - Automatic anchoring scheduling
    - Timestamp coordination
    - Historical anchor storage
    """

    def __init__(
        self, ledger: Optional[AuditLedger] = None, tsa_url: Optional[str] = None
    ):
        """
        Initialize periodic aggregation.

        Args:
            ledger: AuditLedger to aggregate from
            tsa_url: URL for RFC 3161 timestamp service
        """
        self.ledger = ledger
        self.anchoring = PeriodicAnchoring(tsa_url=tsa_url)
        self.aggregation_history: List[AggregationResult] = []
        self._last_aggregation: Dict[str, Optional[str]] = {
            "daily": None,
            "weekly": None,
            "monthly": None,
        }

    def set_ledger(self, ledger: AuditLedger):
        """Set the ledger to aggregate from."""
        self.ledger = ledger

    def aggregate_daily(self, target_date: Optional[date] = None) -> AggregationResult:
        """
        Aggregate audit events for a specific day.

        Args:
            target_date: Date to aggregate (defaults to yesterday)

        Returns:
            AggregationResult with Merkle root
        """
        if target_date is None:
            target_date = date.today() - timedelta(days=1)

        target_str = target_date.isoformat()

        # Get events for the day
        events = self._get_events_for_date(target_date)

        return self._create_aggregation(
            period=AggregationPeriod.DAILY,
            start_date=target_str,
            end_date=target_str,
            events=events,
        )

    def aggregate_weekly(self, target_week: Optional[int] = None) -> AggregationResult:
        """
        Aggregate audit events for a specific week.

        Args:
            target_week: ISO week number (defaults to last week)

        Returns:
            AggregationResult with Merkle root
        """
        today = date.today()

        if target_week is None:
            # Last week
            target_date = today - timedelta(weeks=1)
            year, week, _ = target_date.isocalendar()
        else:
            year = today.year
            week = target_week

        # Calculate week boundaries (Monday to Sunday)
        jan_1 = date(year, 1, 1)
        week_start = jan_1 + timedelta(weeks=week - 1)
        week_start = week_start - timedelta(days=week_start.weekday())
        week_end = week_start + timedelta(days=6)

        events = self._get_events_in_range(week_start, week_end)

        return self._create_aggregation(
            period=AggregationPeriod.WEEKLY,
            start_date=week_start.isoformat(),
            end_date=week_end.isoformat(),
            events=events,
        )

    def aggregate_monthly(
        self, target_month: Optional[int] = None
    ) -> AggregationResult:
        """
        Aggregate audit events for a specific month.

        Args:
            target_month: Month number (defaults to last month)

        Returns:
            AggregationResult with Merkle root
        """
        today = date.today()

        if target_month is None:
            year = today.year
            month = today.month - 1
            if month == 0:
                month = 12
                year -= 1
        else:
            year = today.year
            month = target_month

        # Calculate month boundaries
        if month == 12:
            next_month_year = year + 1
            next_month = 1
        else:
            next_month_year = year
            next_month = month + 1

        month_start = date(year, month, 1)
        month_end = date(next_month_year, next_month, 1) - timedelta(days=1)

        events = self._get_events_in_range(month_start, month_end)

        return self._create_aggregation(
            period=AggregationPeriod.MONTHLY,
            start_date=month_start.isoformat(),
            end_date=month_end.isoformat(),
            events=events,
        )

    def _get_events_for_date(self, target_date: date) -> List[LedgerEntry]:
        """Get all events for a specific date."""
        if not self.ledger:
            return []

        start_ts = datetime.combine(target_date, datetime.min.time()).timestamp()
        end_ts = datetime.combine(target_date, datetime.max.time()).timestamp()

        return [
            entry
            for entry in self.ledger.entries
            if start_ts <= entry.timestamp <= end_ts
        ]

    def _get_events_in_range(
        self, start_date: date, end_date: date
    ) -> List[LedgerEntry]:
        """Get all events in a date range."""
        if not self.ledger:
            return []

        start_ts = datetime.combine(start_date, datetime.min.time()).timestamp()
        end_ts = datetime.combine(end_date, datetime.max.time()).timestamp()

        return [
            entry
            for entry in self.ledger.entries
            if start_ts <= entry.timestamp <= end_ts
        ]

    def _create_aggregation(
        self,
        period: AggregationPeriod,
        start_date: str,
        end_date: str,
        events: List[LedgerEntry],
    ) -> AggregationResult:
        """Create aggregation result from events."""
        # Extract unique sessions
        session_ids = list(set(e.session_id for e in events))

        # Build Merkle tree from events
        event_dicts = [
            json.loads(json.dumps(e.to_dict(), sort_keys=True)) for e in events
        ]
        tree = MerkleTree.build_from_entries(event_dicts)

        result = AggregationResult(
            period=period.value,
            start_date=start_date,
            end_date=end_date,
            event_count=len(events),
            session_count=len(session_ids),
            merkle_root=tree.get_root_hash(),
        )

        # Create anchor
        anchor = self.anchoring.create_daily_anchor(
            merkle_root=result.merkle_root,
            date=start_date,  # Use start date for daily anchoring
            session_ids=session_ids,
        )
        result.anchor = anchor
        result.anchored = True

        # Apply timestamp
        self.anchoring.apply_timestamp_to_anchor(anchor)
        result.timestamped = anchor.timestamped_at is not None

        # Store result
        self.aggregation_history.append(result)
        self._last_aggregation[period.value] = result.merkle_root

        return result

    def get_anchor_for_date(self, target_date: str) -> Optional[TimestampAnchor]:
        """
        Get anchor record for a specific date.

        Args:
            target_date: Date string (YYYY-MM-DD)

        Returns:
            TimestampAnchor if found
        """
        return self.anchoring.get_anchor_by_date(target_date)

    def verify_anchor(self, target_date: str) -> Dict[str, Any]:
        """
        Verify anchor for a specific date.

        Args:
            target_date: Date to verify

        Returns:
            Verification result dictionary
        """
        anchor = self.anchoring.get_anchor_by_date(target_date)

        if not anchor:
            return {
                "verified": False,
                "date": target_date,
                "error": "No anchor found for date",
            }

        # Verify anchor integrity
        integrity_ok = self.anchoring.verify_anchor_integrity(anchor)

        return {
            "verified": integrity_ok,
            "date": target_date,
            "merkle_root": anchor.merkle_root,
            "session_count": anchor.session_count,
            "timestamped": anchor.timestamped_at is not None,
            "timestamp": anchor.timestamped_at,
        }

    def get_aggregation_history(
        self, period: Optional[AggregationPeriod] = None
    ) -> List[Dict[str, Any]]:
        """
        Get aggregation history.

        Args:
            period: Filter by period type

        Returns:
            List of aggregation results
        """
        results = self.aggregation_history

        if period:
            results = [r for r in results if r.period == period.value]

        return [r.to_dict() for r in results]

    def get_last_merkle_root(self, period: str = "daily") -> Optional[str]:
        """
        Get last Merkle root for a period.

        Args:
            period: Period type (daily/weekly/monthly)

        Returns:
            Last Merkle root or None
        """
        return self._last_aggregation.get(period)


class AggregationScheduler:
    """
    Scheduler for periodic aggregation tasks.

    Provides:
    - Cron-like scheduling (simplified)
    - Callback execution
    - Status tracking
    """

    def __init__(self):
        self.tasks: Dict[str, Callable] = {}
        self.last_run: Dict[str, Optional[str]] = {}

    def schedule(self, period: str, callback: Callable):
        """Schedule a task for a period."""
        self.tasks[period] = callback

    def run_daily(self) -> Any:
        """Run daily task."""
        if "daily" in self.tasks:
            result = self.tasks["daily"]()
            self.last_run["daily"] = datetime.now(timezone.utc).isoformat()
            return result

    def run_weekly(self) -> Any:
        """Run weekly task."""
        if "weekly" in self.tasks:
            result = self.tasks["weekly"]()
            self.last_run["weekly"] = datetime.now(timezone.utc).isoformat()
            return result

    def run_monthly(self) -> Any:
        """Run monthly task."""
        if "monthly" in self.tasks:
            result = self.tasks["monthly"]()
            self.last_run["monthly"] = datetime.now(timezone.utc).isoformat()
            return result

    def get_status(self) -> Dict[str, Any]:
        """Get scheduler status."""
        return {"scheduled_tasks": list(self.tasks.keys()), "last_run": self.last_run}
