"""Deterministic data-version manifest construction."""

from __future__ import annotations

from hashlib import sha256

from .store_contracts import DataVersionManifest


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
        fixture_sha256: str | None = None,
        code_revision: str | None = None,
        source_mode: str = "fixture_only",
    ) -> DataVersionManifest:
        if not raw_sha256s or any(not value for value in raw_sha256s):
            raise ValueError("MANIFEST_INPUT_MISSING")
        if not all((normalization_rule_version, catalog_version, catalog_sha256, quality_report_sha256)):
            raise ValueError("MANIFEST_INPUT_MISSING")
        normalized_raw = tuple(sorted(raw_sha256s))
        material = "|".join(
            (
                *normalized_raw,
                normalization_rule_version,
                catalog_version,
                catalog_sha256,
                quality_report_sha256,
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
            fixture_sha256=fixture_sha256,
            code_revision=code_revision,
            source_mode=source_mode,
        )
