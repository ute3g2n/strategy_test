"""Deterministic data-version manifest construction."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from hashlib import sha256

from .store_contracts import DataVersionManifest, NormalizedBar


class ManifestBuilder:
    """Build an immutable manifest from content-addressed inputs only."""

    @staticmethod
    def build(
        *,
        raw_sha256s: tuple[str, ...],
        normalization_rule_version: str,
        catalog_version: str,
        catalog_sha256: str,
        quality_report_sha256: str,
        normalized_content_sha256: str,
        fixture_sha256: str | None = None,
        code_revision: str | None = None,
        source_mode: str = "fixture_only",
    ) -> DataVersionManifest:
        if not raw_sha256s or any(not value for value in raw_sha256s):
            raise ValueError("MANIFEST_INPUT_MISSING")
        if not all(
            (
                normalization_rule_version,
                catalog_version,
                catalog_sha256,
                quality_report_sha256,
                normalized_content_sha256,
                fixture_sha256,
                code_revision,
                source_mode,
            )
        ):
            raise ValueError("MANIFEST_INPUT_MISSING")
        normalized_raw = tuple(sorted(raw_sha256s))
        material = "|".join(
            (
                *normalized_raw,
                normalization_rule_version,
                catalog_version,
                catalog_sha256,
                quality_report_sha256,
                normalized_content_sha256,
                fixture_sha256 or "<fixture-not-specified>",
                code_revision or "<code-revision-not-specified>",
                source_mode,
                "normalized-v1",
            )
        )
        data_version = "dv_" + sha256(material.encode("utf-8")).hexdigest()[:20]
        return DataVersionManifest(
            data_version=data_version,
            raw_sha256s=normalized_raw,
            normalization_rule_version=normalization_rule_version,
            catalog_version=catalog_version,
            catalog_sha256=catalog_sha256,
            quality_report_sha256=quality_report_sha256,
            normalized_content_sha256=normalized_content_sha256,
            fixture_sha256=fixture_sha256,
            code_revision=code_revision,
            source_mode=source_mode,
        )


def normalized_content_sha256(bars: tuple[NormalizedBar, ...]) -> str:
    """Return the canonical digest for the ordered normalized-bar series."""
    material = json.dumps(
        [asdict(bar) for bar in bars],
        default=_json_default,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + sha256(material).hexdigest()


def _json_default(value: object) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    raise TypeError(f"unsupported JSON value: {type(value).__name__}")
