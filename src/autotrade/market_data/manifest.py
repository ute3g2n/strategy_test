"""Deterministic data-version manifest construction."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from hashlib import sha256
from typing import TYPE_CHECKING

from .store_contracts import DataVersionManifest, NormalizedBar

if TYPE_CHECKING:
    from .dbn_contracts import DbnCatalogBinding


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
        request_context_sha256: str | None = None,
        decoder_version: str | None = None,
        decoder_artifact_sha256: str | None = None,
    ) -> DataVersionManifest:
        if source_mode == "dbn_replay" or any((request_context_sha256, decoder_version, decoder_artifact_sha256)):
            raise ValueError("MANIFEST_INPUT_MISSING")
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
        return ManifestBuilder._create(
            raw_sha256s=normalized_raw,
            normalization_rule_version=normalization_rule_version,
            catalog_version=catalog_version,
            catalog_sha256=catalog_sha256,
            quality_report_sha256=quality_report_sha256,
            normalized_content_sha256=normalized_content_sha256,
            fixture_sha256=fixture_sha256,
            code_revision=code_revision,
            source_mode=source_mode,
            request_context_sha256=None,
            decoder_version=None,
            decoder_artifact_sha256=None,
        )

    @staticmethod
    def build_dbn(
        *,
        raw_sha256s: tuple[str, ...],
        normalization_rule_version: str,
        catalog: DbnCatalogBinding,
        quality_report_sha256: str,
        normalized_content_sha256: str,
        fixture_sha256: str | None,
        code_revision: str | None,
        source_mode: str,
        request_context_sha256: str | None,
        decoder_version: str | None,
        decoder_artifact_sha256: str | None,
    ) -> DataVersionManifest:
        if (
            not raw_sha256s
            or any(not value for value in raw_sha256s)
            or not all(
                (
                    normalization_rule_version,
                    catalog.catalog_version,
                    catalog.catalog_sha256,
                    quality_report_sha256,
                    normalized_content_sha256,
                    code_revision,
                    request_context_sha256,
                    decoder_version,
                    decoder_artifact_sha256,
                )
            )
            or fixture_sha256 is not None
            or source_mode != "dbn_replay"
        ):
            raise ValueError("MANIFEST_INPUT_MISSING")
        return ManifestBuilder._create(
            raw_sha256s=tuple(sorted(raw_sha256s)),
            normalization_rule_version=normalization_rule_version,
            catalog_version=catalog.catalog_version,
            catalog_sha256=catalog.catalog_sha256,
            quality_report_sha256=quality_report_sha256,
            normalized_content_sha256=normalized_content_sha256,
            fixture_sha256=None,
            code_revision=code_revision,
            source_mode=source_mode,
            request_context_sha256=request_context_sha256,
            decoder_version=decoder_version,
            decoder_artifact_sha256=decoder_artifact_sha256,
        )

    @staticmethod
    def rebuild(manifest: DataVersionManifest) -> DataVersionManifest:
        """Recompute an already parsed manifest without resolving a Catalog again."""
        if manifest.source_mode == "fixture_only":
            return ManifestBuilder.build(
                raw_sha256s=manifest.raw_sha256s,
                normalization_rule_version=manifest.normalization_rule_version,
                catalog_version=manifest.catalog_version,
                catalog_sha256=manifest.catalog_sha256,
                quality_report_sha256=manifest.quality_report_sha256,
                normalized_content_sha256=manifest.normalized_content_sha256,
                fixture_sha256=manifest.fixture_sha256,
                code_revision=manifest.code_revision,
                source_mode=manifest.source_mode,
            )
        if (
            manifest.source_mode != "dbn_replay"
            or manifest.fixture_sha256 is not None
            or not manifest.raw_sha256s
            or any(not value for value in manifest.raw_sha256s)
            or not all(
                (
                    manifest.normalization_rule_version,
                    manifest.catalog_version,
                    manifest.catalog_sha256,
                    manifest.quality_report_sha256,
                    manifest.normalized_content_sha256,
                    manifest.code_revision,
                    manifest.request_context_sha256,
                    manifest.decoder_version,
                    manifest.decoder_artifact_sha256,
                )
            )
        ):
            raise ValueError("MANIFEST_INPUT_MISSING")
        return ManifestBuilder._create(
            raw_sha256s=manifest.raw_sha256s,
            normalization_rule_version=manifest.normalization_rule_version,
            catalog_version=manifest.catalog_version,
            catalog_sha256=manifest.catalog_sha256,
            quality_report_sha256=manifest.quality_report_sha256,
            normalized_content_sha256=manifest.normalized_content_sha256,
            fixture_sha256=None,
            code_revision=manifest.code_revision,
            source_mode=manifest.source_mode,
            request_context_sha256=manifest.request_context_sha256,
            decoder_version=manifest.decoder_version,
            decoder_artifact_sha256=manifest.decoder_artifact_sha256,
        )

    @staticmethod
    def _create(
        *,
        raw_sha256s: tuple[str, ...],
        normalization_rule_version: str,
        catalog_version: str,
        catalog_sha256: str,
        quality_report_sha256: str,
        normalized_content_sha256: str,
        fixture_sha256: str | None,
        code_revision: str | None,
        source_mode: str,
        request_context_sha256: str | None,
        decoder_version: str | None,
        decoder_artifact_sha256: str | None,
    ) -> DataVersionManifest:
        material_parts = [
            *raw_sha256s,
            normalization_rule_version,
            catalog_version,
            catalog_sha256,
            quality_report_sha256,
            normalized_content_sha256,
            fixture_sha256 or "<fixture-not-specified>",
            code_revision or "<code-revision-not-specified>",
            source_mode,
        ]
        if source_mode == "dbn_replay":
            material_parts.extend(
                (
                    request_context_sha256 or "<request-context-not-applicable>",
                    decoder_version or "<decoder-not-applicable>",
                    decoder_artifact_sha256 or "<decoder-artifact-not-applicable>",
                    "normalized-dbn-v1",
                )
            )
        else:
            material_parts.append("normalized-v1")
        material = "|".join(material_parts)
        data_version = "dv_" + sha256(material.encode("utf-8")).hexdigest()[:20]
        return DataVersionManifest(
            data_version=data_version,
            raw_sha256s=raw_sha256s,
            normalization_rule_version=normalization_rule_version,
            catalog_version=catalog_version,
            catalog_sha256=catalog_sha256,
            quality_report_sha256=quality_report_sha256,
            normalized_content_sha256=normalized_content_sha256,
            fixture_sha256=fixture_sha256,
            code_revision=code_revision,
            source_mode=source_mode,
            request_context_sha256=request_context_sha256,
            decoder_version=decoder_version,
            decoder_artifact_sha256=decoder_artifact_sha256,
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
