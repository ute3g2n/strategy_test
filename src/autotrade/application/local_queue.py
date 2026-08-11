"""A process-local queue facade; durable queue state remains in MetadataStore."""

from __future__ import annotations

from .contracts import JobView
from .persistence import MetadataStore


class LocalQueue:
    def __init__(self, store: MetadataStore) -> None:
        self.store = store

    def claim(self, worker_id: str) -> JobView | None:
        return self.store.claim_next_job(worker_id)
