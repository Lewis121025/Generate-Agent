"""Cost tracking utilities."""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock
from typing import Dict

from .config import settings
from .instrumentation import TelemetryEvent, emit_event


@dataclass(slots=True)
class CostEnvelope:
    limit_usd: float
    spent_usd: float = 0.0

    @property
    def remaining(self) -> float:
        return max(self.limit_usd - self.spent_usd, 0.0)

    def add_cost(self, amount: float) -> None:
        self.spent_usd += amount


class CostTracker:
    """Thread-safe tracker for per-entity cost envelopes."""

    def __init__(self) -> None:
        self._envelopes: Dict[str, CostEnvelope] = {}
        self._lock = Lock()

    def ensure_envelope(
        self,
        entity_id: str,
        limit_usd: float | None = None,
    ) -> CostEnvelope:
        with self._lock:
            if entity_id not in self._envelopes:
                self._envelopes[entity_id] = CostEnvelope(
                    limit_usd=limit_usd or settings.budget.default_project_limit_usd
                )
            return self._envelopes[entity_id]

    def record(self, entity_id: str, amount: float) -> CostEnvelope:
        envelope = self.ensure_envelope(entity_id)
        envelope.add_cost(amount)

        pct = (envelope.spent_usd / envelope.limit_usd) * 100 if envelope.limit_usd else 0
        for threshold in settings.budget.cost_alert_percentages:
            if pct >= threshold:
                emit_event(
                    TelemetryEvent(
                        name="cost_threshold",
                        attributes={"entity_id": entity_id, "threshold": threshold, "spent": envelope.spent_usd},
                    )
                )
                break
        return envelope


cost_tracker = CostTracker()

