"""Atomic, immutable normalized snapshots for fixture-only replay."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from .manifest import ManifestBuilder, normalized_content_sha256
from .quality import QualityChecker
from .store_contracts import (
    DataVersionManifest,
    NormalizedBar,
    QualityReport,
    ReplaySnapshot,
)


class LocalNormalizedStore:
    """Store one immutable JSON snapshot per deterministic data version."""

    def __init__(self, root: Path) -> None:
        self._root = root

    def write_if_absent(
        self,
        bars: tuple[NormalizedBar, ...],
        manifest: DataVersionManifest,
        report: QualityReport,
    ) -> str:
        if not report.publishable or not report.signal_generation_allowed:
            raise ValueError("QUALITY_REJECTED")
        if manifest.quality_report_sha256 != report.quality_report_sha256:
            raise ValueError("MANIFEST_INTEGRITY")
        if manifest.normalized_content_sha256 != normalized_content_sha256(bars):
            raise ValueError("MANIFEST_INTEGRITY")
        recomputed_report = QualityChecker.check(bars)
        if _report_material(recomputed_report) != _report_material(report):
            raise ValueError("MANIFEST_INTEGRITY")
        path = self._path(manifest.data_version)
        payload = self._serialize(bars, manifest, report)
        if path.exists():
            if path.read_text(encoding="utf-8") != payload:
                raise ValueError("DATA_VERSION_CONFLICT")
            return manifest.data_version
        path.parent.mkdir(parents=True, exist_ok=True)
        created = False
        try:
            with path.open("x", encoding="utf-8", newline="") as handle:
                created = True
                handle.write(payload)
        except FileExistsError:
            if path.read_text(encoding="utf-8") != payload:
                raise ValueError("DATA_VERSION_CONFLICT") from None
        except OSError:
            if created:
                path.unlink(missing_ok=True)
            raise
        return manifest.data_version

    def read_replay_snapshot(self, data_version: str) -> ReplaySnapshot:
        path = self._path(data_version)
        if not path.is_file():
            raise ValueError("MANIFEST_NOT_FOUND")
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            manifest = _manifest_from_json(payload["manifest"])
            report = _report_from_json(payload["quality_report"])
            bars = tuple(_bar_from_json(row) for row in payload["bars"])
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise ValueError("MANIFEST_INTEGRITY") from exc
        if manifest.data_version != data_version:
            raise ValueError("MANIFEST_INTEGRITY")
        if manifest.quality_report_sha256 != report.quality_report_sha256:
            raise ValueError("MANIFEST_INTEGRITY")
        if manifest.normalized_content_sha256 != normalized_content_sha256(bars):
            raise ValueError("MANIFEST_INTEGRITY")
        recomputed_report = QualityChecker.check(bars)
        if _report_material(recomputed_report) != _report_material(report):
            raise ValueError("MANIFEST_INTEGRITY")
        if (
            QualityChecker.report_hash(
                report.flags,
                report.deduplicated_count,
                report.publishable,
                report.excluded_ranges,
            )
            != report.quality_report_sha256
        ):
            raise ValueError("MANIFEST_INTEGRITY")
        rebuilt_manifest = ManifestBuilder.build(
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
        if rebuilt_manifest.data_version != manifest.data_version:
            raise ValueError("MANIFEST_INTEGRITY")
        if not report.publishable or not report.signal_generation_allowed:
            raise ValueError("QUALITY_REJECTED")
        return ReplaySnapshot(bars=bars, manifest=manifest)

    def _path(self, data_version: str) -> Path:
        if not data_version or "/" in data_version or "\\" in data_version:
            raise ValueError("DATA_VERSION_INVALID")
        return self._root / "normalized" / f"{data_version}.json"

    @staticmethod
    def _serialize(bars: tuple[NormalizedBar, ...], manifest: DataVersionManifest, report: QualityReport) -> str:
        payload = {
            "bars": [asdict(bar) for bar in bars],
            "manifest": asdict(manifest),
            "quality_report": asdict(report),
        }
        return json.dumps(payload, default=_json_default, sort_keys=True, separators=(",", ":"))


def _json_default(value: object) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    raise TypeError(f"unsupported JSON value: {type(value).__name__}")


def _manifest_from_json(value: object) -> DataVersionManifest:
    if not isinstance(value, dict):
        raise ValueError("MANIFEST_INTEGRITY")
    raw_sha256s = value.get("raw_sha256s")
    if not isinstance(raw_sha256s, list):
        raise ValueError("MANIFEST_INTEGRITY")
    return DataVersionManifest(
        data_version=_string(value, "data_version"),
        raw_sha256s=tuple(str(item) for item in raw_sha256s),
        normalization_rule_version=_string(value, "normalization_rule_version"),
        catalog_version=_string(value, "catalog_version"),
        catalog_sha256=_string(value, "catalog_sha256"),
        quality_report_sha256=_string(value, "quality_report_sha256"),
        normalized_content_sha256=_string(value, "normalized_content_sha256"),
        fixture_sha256=value.get("fixture_sha256"),
        code_revision=value.get("code_revision"),
        source_mode=_string(value, "source_mode"),
    )


def _report_from_json(value: object) -> QualityReport:
    if not isinstance(value, dict):
        raise ValueError("MANIFEST_INTEGRITY")
    flags = value.get("flags")
    if not isinstance(flags, list):
        raise ValueError("MANIFEST_INTEGRITY")
    publishable = value.get("publishable")
    signal_generation_allowed = value.get("signal_generation_allowed")
    if not isinstance(publishable, bool) or not isinstance(signal_generation_allowed, bool):
        raise ValueError("MANIFEST_INTEGRITY")
    return QualityReport(
        flags=tuple(str(flag) for flag in flags),
        publishable=publishable,
        signal_generation_allowed=signal_generation_allowed,
        quality_report_sha256=_string(value, "quality_report_sha256"),
        deduplicated_count=int(value.get("deduplicated_count", 0)),
        excluded_ranges=tuple(str(item) for item in value.get("excluded_ranges", [])),
    )


def _report_material(report: QualityReport) -> tuple[object, ...]:
    return (
        report.flags,
        report.publishable,
        report.signal_generation_allowed,
        report.quality_report_sha256,
        report.deduplicated_count,
        report.excluded_ranges,
    )


def _bar_from_json(value: object) -> NormalizedBar:
    if not isinstance(value, dict):
        raise ValueError("MANIFEST_INTEGRITY")
    flags = value.get("quality_flags")
    if not isinstance(flags, list):
        raise ValueError("MANIFEST_INTEGRITY")
    return NormalizedBar(
        instrument_id=_string(value, "instrument_id"),
        event_time_utc=datetime.fromisoformat(_string(value, "event_time_utc")),
        open=_string(value, "open"),
        high=_string(value, "high"),
        low=_string(value, "low"),
        close=_string(value, "close"),
        volume=int(value["volume"]),
        raw_object_id=_string(value, "raw_object_id"),
        quality_flags=tuple(str(flag) for flag in flags),
    )


def _string(value: dict[str, object], key: str) -> str:
    result = value.get(key)
    if not isinstance(result, str) or not result:
        raise ValueError("MANIFEST_INTEGRITY")
    return result
