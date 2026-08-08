"""P2-12-01 RED contracts for real DBN decoding and replay.

Only the immutable P2-08 payload checksum is checked at this stage.  The
decoder, normalizer, and event factory imports are intentionally RED until
P2-12-02 implements the approved P2-D16 contract.
"""

from __future__ import annotations

import dataclasses
import importlib
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace

import pytest

RAW_DBN_SHA256 = "8fd0286a477e073c83e8306c4e1a8ebec3af693141010563edd7e0ec1990b65e"
SYNTHETIC_RECEIVED_AT = datetime(2026, 1, 1, tzinfo=UTC)


def _contracts() -> object:
    return importlib.import_module("autotrade.market_data.dbn_contracts")


def _decoder() -> object:
    return importlib.import_module("autotrade.market_data.databento_dbn_decoder")


def _normalizer() -> object:
    return importlib.import_module("autotrade.market_data.dbn_normalizer")


def _event_factory() -> object:
    return importlib.import_module("autotrade.market_data.market_event_factory")


def _replay_input(contracts: object) -> object:
    return contracts.DbnReplayInput(
        payload_sha256="sha256:" + RAW_DBN_SHA256,
        raw_object_id="raw-design-fixture",
        raw_received_at_utc=SYNTHETIC_RECEIVED_AT,
        source_vendor="fixture_vendor",
        dataset_ref="FIXTURE.DATASET",
        schema_ref="ohlcv-1m",
        stype="raw_symbol",
        source_symbol="FIX.TEST",
        request_start_utc=datetime(2026, 1, 1, tzinfo=UTC),
        request_end_utc=datetime(2026, 1, 1, 0, 1, tzinfo=UTC),
        request_context_sha256="sha256:" + "1" * 64,
        decoder_version="pinned-decoder-v1",
        decoder_artifact_sha256="sha256:" + "2" * 64,
        normalization_rule_version="dbn-ohlcv-1m-v1",
    )


def _catalog_binding(contracts: object, status: str = "resolved", result_version: str = "catalog-v1") -> object:
    catalog_module = importlib.import_module("autotrade.market_data.catalog_resolver")

    class SyntheticResolver:
        def resolve(self, request: object) -> object:
            del request
            if status == "resolved":
                return catalog_module.ResolveInstrumentResult(
                    "resolved", "inst-fixture", "map-fixture", result_version, None
                )
            return catalog_module.ResolveInstrumentResult(status, None, None, result_version, status)

    return contracts.DbnCatalogBinding(
        catalog_version="catalog-v1",
        catalog_sha256="sha256:" + "c" * 64,
        resolver=SyntheticResolver(),
    )


def _record(contracts: object, **changes: object) -> object:
    values = {
        "source_symbol": "FIX.TEST",
        "vendor_instrument_id": 1,
        "publisher_id": 1,
        "event_time_utc": datetime(2026, 1, 1, tzinfo=UTC),
        "open": "1.000000000",
        "high": "2.000000000",
        "low": "1.000000000",
        "close": "1.500000000",
        "volume": 1,
        "record_ordinal": 0,
    }
    values.update(changes)
    return contracts.DecodedOhlcvRecord(**values)


def test_p2_12_records_the_approved_real_input_identity_without_opening_it() -> None:
    """P2-12-01 must not open the Git-ignored DBN before H2-5."""

    assert RAW_DBN_SHA256 == "8fd0286a477e073c83e8306c4e1a8ebec3af693141010563edd7e0ec1990b65e"


def test_decoder_uses_dbn_metadata_to_resolve_external_instrument_id() -> None:
    decoder = _decoder()
    metadata = SimpleNamespace(mappings={"MCLQ6": [{"symbol": "42026511"}]})

    assert decoder._source_symbol(metadata, 42026511, "MCL.FUT") == "MCLQ6"
    assert decoder._source_symbol(metadata, 99999999, "MCL.FUT") == "MCL.FUT"


def test_decoder_contract_rejects_checksum_mismatch_before_decoding() -> None:
    contracts = _contracts()
    decoder = _decoder()
    provenance = _replay_input(contracts)
    provenance = dataclasses.replace(provenance, payload_sha256="sha256:" + "0" * 64)

    with pytest.raises(contracts.DbnDecodeError, match="RAW_CHECKSUM_MISMATCH"):
        decoder.DatabentoDbnDecoder().decode(b"DBN\x03", provenance)


@pytest.mark.parametrize(
    "payload, expected_code",
    [
        (b"not-dbn", "DECODE_OR_SCHEMA_ERROR"),
        (b"DBN", "DECODE_OR_SCHEMA_ERROR"),
        (b"DBN\x03\x00", "DECODE_RECORD_INVALID"),
    ],
)
def test_decoder_contract_rejects_malformed_or_unsupported_records(payload: bytes, expected_code: str) -> None:
    contracts = _contracts()
    decoder = _decoder()

    source = dataclasses.replace(_replay_input(contracts), payload_sha256="sha256:" + sha256(payload).hexdigest())
    with pytest.raises(contracts.DbnDecodeError, match=expected_code):
        decoder.DatabentoDbnDecoder().decode(payload, source)


def test_normalizer_contract_rejects_missing_raw_received_at() -> None:
    contracts = _contracts()
    normalizer = _normalizer()
    record = _record(contracts)

    with pytest.raises(contracts.DbnNormalizationError, match="RAW_RECEIVED_AT_MISSING"):
        normalizer.DbnNormalizer(_catalog_binding(contracts)).normalize((record,), source=None)


@pytest.mark.parametrize("catalog_status", ["not_found", "ambiguous", "pending", "unknown"])
def test_normalizer_contract_rejects_unresolved_catalog_without_guessing(catalog_status: str) -> None:
    contracts = _contracts()
    normalizer = _normalizer()
    record = _record(contracts)

    with pytest.raises(contracts.DbnNormalizationError, match="CATALOG_MAPPING_UNRESOLVED"):
        normalizer.DbnNormalizer(_catalog_binding(contracts, catalog_status)).normalize(
            (record,), source=_replay_input(contracts)
        )


def test_normalizer_contract_rejects_invalid_time_price_volume_and_order() -> None:
    contracts = _contracts()
    normalizer = _normalizer()
    invalid_record = _record(
        contracts,
        event_time_utc=datetime(2026, 1, 1),
        open="NaN",
        high="0.000000000",
        volume=-1,
        record_ordinal=1,
    )

    with pytest.raises(contracts.DbnNormalizationError, match="QUALITY_REJECTED"):
        normalizer.DbnNormalizer(_catalog_binding(contracts)).normalize(
            (invalid_record,), source=_replay_input(contracts)
        )


def test_normalizer_contract_rejects_catalog_binding_version_mismatch() -> None:
    contracts = _contracts()
    normalizer = _normalizer()
    record = _record(contracts)

    with pytest.raises(contracts.DbnNormalizationError, match="CATALOG_MAPPING_UNRESOLVED"):
        normalizer.DbnNormalizer(_catalog_binding(contracts, result_version="catalog-other")).normalize(
            (record,), source=_replay_input(contracts)
        )


def test_normalizer_excludes_pending_spread_from_main_future_series() -> None:
    contracts = _contracts()
    catalog_module = importlib.import_module("autotrade.market_data.catalog_resolver")

    class MixedResolver:
        def resolve(self, request: object) -> object:
            if request.symbol == "MCLN6-MCLQ6":
                return catalog_module.ResolveInstrumentResult(
                    "unknown",
                    None,
                    "map-spread",
                    "catalog-v1",
                    "REQUIRED_ATTRIBUTE_UNKNOWN",
                    "spread",
                    "pending",
                )
            return catalog_module.ResolveInstrumentResult(
                "resolved", "inst-fixture", "map-future", "catalog-v1", None, "future", "active"
            )

    binding = contracts.DbnCatalogBinding("catalog-v1", "sha256:" + "c" * 64, MixedResolver())
    normalizer = _normalizer().DbnNormalizer(binding)
    records = (
        _record(contracts, source_symbol="MCLN6", record_ordinal=0),
        _record(contracts, source_symbol="MCLN6-MCLQ6", vendor_instrument_id=42460441, record_ordinal=1),
    )

    normalized = normalizer.normalize(records, _replay_input(contracts))

    assert len(normalized) == 1
    assert normalized[0].record_ordinal == 0
    assert normalizer.excluded_ranges == (
        "record_ordinal=1|vendor_instrument_id=42460441|source_symbol=MCLN6-MCLQ6|reason=SPREAD_OUT_OF_MAIN_SERIES",
    )


def test_quality_report_binds_excluded_spread_ranges() -> None:
    quality_module = importlib.import_module("autotrade.market_data.quality")
    bar = (
        _normalizer()
        .DbnNormalizer(_catalog_binding(_contracts()))
        .normalize((_record(_contracts()),), _replay_input(_contracts()))[0]
        .bar
    )

    report = quality_module.QualityChecker.check(
        (bar,), excluded_ranges=("record_ordinal=1|reason=SPREAD_OUT_OF_MAIN_SERIES",)
    )

    assert report.excluded_ranges == ("record_ordinal=1|reason=SPREAD_OUT_OF_MAIN_SERIES",)
    assert report.quality_report_sha256 == quality_module.QualityChecker.report_hash(
        report.flags, report.deduplicated_count, report.publishable, report.excluded_ranges
    )


def test_normalizer_uses_exact_fixed_catalog_request() -> None:
    contracts = _contracts()
    catalog_module = importlib.import_module("autotrade.market_data.catalog_resolver")
    captured: list[object] = []

    class CapturingResolver:
        def resolve(self, request: object) -> object:
            captured.append(request)
            return catalog_module.ResolveInstrumentResult("resolved", "inst-fixture", "map-fixture", "catalog-v1", None)

    binding = contracts.DbnCatalogBinding("catalog-v1", "sha256:" + "c" * 64, CapturingResolver())
    source = _replay_input(contracts)
    _normalizer().DbnNormalizer(binding).normalize((_record(contracts),), source)

    assert len(captured) == 1
    request = captured[0]
    assert (request.vendor, request.dataset_id, request.stype, request.symbol, request.observed_at) == (
        source.source_vendor,
        source.dataset_ref,
        source.stype,
        source.source_symbol,
        datetime(2026, 1, 1, tzinfo=UTC),
    )


def test_event_factory_contract_requires_publishable_quality_and_deterministic_id() -> None:
    contracts = _contracts()
    factory = _event_factory()

    with pytest.raises(contracts.DbnEventBuildError, match="QUALITY_REJECTED"):
        factory.MarketEventFactory().build(
            records=(),
            quality_report=object(),
            manifest=object(),
            run_id="RUN-P2-DBN-001",
            raw_received_at_utc=SYNTHETIC_RECEIVED_AT,
        )


def test_contract_requires_all_replay_provenance_fields() -> None:
    contracts = _contracts()
    fields = set(contracts.DbnReplayInput.__dataclass_fields__)
    catalog_fields = set(contracts.DbnCatalogBinding.__dataclass_fields__)

    assert {
        "payload_sha256",
        "raw_object_id",
        "raw_received_at_utc",
        "stype",
        "request_context_sha256",
        "decoder_version",
        "decoder_artifact_sha256",
        "normalization_rule_version",
    } <= fields
    assert {"catalog_version", "catalog_sha256", "resolver"} <= catalog_fields


def test_dbn_manifest_contract_changes_version_when_decoder_provenance_changes() -> None:
    contracts = _contracts()
    manifest_module = importlib.import_module("autotrade.market_data.manifest")
    common = {
        "raw_sha256s": ("sha256:" + "a" * 64,),
        "normalization_rule_version": "dbn-ohlcv-1m-v1",
        "catalog": _catalog_binding(contracts),
        "quality_report_sha256": "sha256:" + "c" * 64,
        "normalized_content_sha256": "sha256:" + "d" * 64,
        "fixture_sha256": None,
        "code_revision": "revision-v1",
        "source_mode": "dbn_replay",
        "request_context_sha256": "sha256:" + "f" * 64,
        "decoder_version": "decoder-v1",
        "decoder_artifact_sha256": "sha256:" + "1" * 64,
    }
    first = manifest_module.ManifestBuilder.build_dbn(**common)
    changed = manifest_module.ManifestBuilder.build_dbn(**{**common, "decoder_artifact_sha256": "sha256:" + "2" * 64})

    assert first.data_version != changed.data_version

    for key, value in (
        ("request_context_sha256", "sha256:" + "3" * 64),
        ("normalization_rule_version", "dbn-ohlcv-1m-v2"),
        ("code_revision", "revision-v2"),
    ):
        assert first.data_version != manifest_module.ManifestBuilder.build_dbn(**{**common, key: value}).data_version


@pytest.mark.parametrize(
    "bad_field, bad_value",
    [
        ("fixture_sha256", "sha256:" + "f" * 64),
        ("request_context_sha256", None),
        ("decoder_version", None),
        ("decoder_artifact_sha256", None),
    ],
)
def test_dbn_manifest_contract_rejects_wrong_source_mode_or_missing_provenance(
    bad_field: str, bad_value: str | None
) -> None:
    contracts = _contracts()
    manifest_module = importlib.import_module("autotrade.market_data.manifest")
    common = {
        "raw_sha256s": ("sha256:" + "a" * 64,),
        "normalization_rule_version": "dbn-ohlcv-1m-v1",
        "catalog": _catalog_binding(contracts),
        "quality_report_sha256": "sha256:" + "c" * 64,
        "normalized_content_sha256": "sha256:" + "d" * 64,
        "fixture_sha256": None,
        "code_revision": "revision-v1",
        "source_mode": "dbn_replay",
        "request_context_sha256": "sha256:" + "1" * 64,
        "decoder_version": "decoder-v1",
        "decoder_artifact_sha256": "sha256:" + "2" * 64,
    }

    with pytest.raises(ValueError, match="MANIFEST_INPUT_MISSING"):
        manifest_module.ManifestBuilder.build_dbn(**{**common, bad_field: bad_value})


def test_fixture_manifest_contract_rejects_dbn_provenance() -> None:
    _contracts()
    manifest_module = importlib.import_module("autotrade.market_data.manifest")

    with pytest.raises(ValueError, match="MANIFEST_INPUT_MISSING"):
        manifest_module.ManifestBuilder.build(
            raw_sha256s=("sha256:" + "a" * 64,),
            normalization_rule_version="fixture-v1",
            catalog_version="catalog-v1",
            catalog_sha256="sha256:" + "b" * 64,
            quality_report_sha256="sha256:" + "c" * 64,
            normalized_content_sha256="sha256:" + "d" * 64,
            fixture_sha256="sha256:" + "e" * 64,
            code_revision="revision-v1",
            source_mode="fixture_only",
            request_context_sha256="sha256:" + "1" * 64,
        )


def test_event_id_is_reproducible_for_identical_replay_inputs() -> None:
    _contracts()
    factory = _event_factory().MarketEventFactory()
    manifest = SimpleNamespace(data_version="dv-fixed")
    arguments = (manifest, "inst-fixture", datetime(2026, 1, 1, tzinfo=UTC), 0)

    assert factory.event_id(*arguments) == factory.event_id(*arguments)


def test_normal_full_chain_preserves_record_ordinal_and_replay_snapshot(tmp_path: Path) -> None:
    """Two equal-time bars keep a stable order through store and event creation."""
    contracts = _contracts()
    normalizer = _normalizer().DbnNormalizer(_catalog_binding(contracts))
    source = _replay_input(contracts)
    records = (
        _record(contracts, record_ordinal=2),
        _record(contracts, record_ordinal=3),
    )
    normalized = normalizer.normalize(records, source)
    quality_module = importlib.import_module("autotrade.market_data.quality")
    manifest_module = importlib.import_module("autotrade.market_data.manifest")
    store_module = importlib.import_module("autotrade.market_data.normalized_store")
    report = quality_module.QualityChecker.check(tuple(item.bar for item in normalized))
    manifest = manifest_module.ManifestBuilder.build_dbn(
        raw_sha256s=(source.payload_sha256,),
        normalization_rule_version=source.normalization_rule_version,
        catalog=_catalog_binding(contracts),
        quality_report_sha256=report.quality_report_sha256,
        normalized_content_sha256=manifest_module.normalized_content_sha256(tuple(item.bar for item in normalized)),
        fixture_sha256=None,
        code_revision="revision-v1",
        source_mode="dbn_replay",
        request_context_sha256=source.request_context_sha256,
        decoder_version=source.decoder_version,
        decoder_artifact_sha256=source.decoder_artifact_sha256,
    )
    store = store_module.LocalNormalizedStore(tmp_path)
    store.write_if_absent(tuple(item.bar for item in normalized), manifest, report)
    replay = store.read_replay_snapshot(manifest.data_version)
    events = (
        _event_factory()
        .MarketEventFactory()
        .build(normalized, report, replay.manifest, "RUN-P2-DBN-001", source.raw_received_at_utc)
    )

    assert [event.event_id for event in events] == [
        _event_factory().MarketEventFactory().event_id(manifest, "inst-fixture", records[0].event_time_utc, 2),
        _event_factory().MarketEventFactory().event_id(manifest, "inst-fixture", records[1].event_time_utc, 3),
    ]
    assert all(event.received_at_utc == SYNTHETIC_RECEIVED_AT for event in events)
    assert all(event.bar_close_time == event.event_time_utc + timedelta(minutes=1) for event in events)
    assert all(event.data_version == manifest.data_version for event in events)


def test_dbn_snapshot_rejects_tampered_decoder_provenance(tmp_path: Path) -> None:
    contracts = _contracts()
    normalizer = _normalizer().DbnNormalizer(_catalog_binding(contracts))
    source = _replay_input(contracts)
    normalized = normalizer.normalize((_record(contracts),), source)
    quality_module = importlib.import_module("autotrade.market_data.quality")
    manifest_module = importlib.import_module("autotrade.market_data.manifest")
    store_module = importlib.import_module("autotrade.market_data.normalized_store")
    report = quality_module.QualityChecker.check(tuple(item.bar for item in normalized))
    manifest = manifest_module.ManifestBuilder.build_dbn(
        raw_sha256s=(source.payload_sha256,),
        normalization_rule_version=source.normalization_rule_version,
        catalog=_catalog_binding(contracts),
        quality_report_sha256=report.quality_report_sha256,
        normalized_content_sha256=manifest_module.normalized_content_sha256(tuple(item.bar for item in normalized)),
        fixture_sha256=None,
        code_revision="revision-v1",
        source_mode="dbn_replay",
        request_context_sha256=source.request_context_sha256,
        decoder_version=source.decoder_version,
        decoder_artifact_sha256=source.decoder_artifact_sha256,
    )
    store = store_module.LocalNormalizedStore(tmp_path)
    store.write_if_absent(tuple(item.bar for item in normalized), manifest, report)
    snapshot_path = tmp_path / "normalized" / f"{manifest.data_version}.json"
    snapshot_path.write_text(
        snapshot_path.read_text(encoding="utf-8").replace("decoder-v1", "decoder-v2"), encoding="utf-8"
    )
    with pytest.raises(ValueError, match="MANIFEST_INTEGRITY"):
        store.read_replay_snapshot(manifest.data_version)


def test_event_factory_rejects_manifest_or_report_for_different_records() -> None:
    contracts = _contracts()
    source = _replay_input(contracts)
    normalized = _normalizer().DbnNormalizer(_catalog_binding(contracts)).normalize((_record(contracts),), source)
    quality_module = importlib.import_module("autotrade.market_data.quality")
    manifest_module = importlib.import_module("autotrade.market_data.manifest")
    report = quality_module.QualityChecker.check(tuple(item.bar for item in normalized))
    manifest = manifest_module.ManifestBuilder.build_dbn(
        raw_sha256s=(source.payload_sha256,),
        normalization_rule_version=source.normalization_rule_version,
        catalog=_catalog_binding(contracts),
        quality_report_sha256=report.quality_report_sha256,
        normalized_content_sha256=manifest_module.normalized_content_sha256(tuple(item.bar for item in normalized)),
        fixture_sha256=None,
        code_revision="revision-v1",
        source_mode="dbn_replay",
        request_context_sha256=source.request_context_sha256,
        decoder_version=source.decoder_version,
        decoder_artifact_sha256=source.decoder_artifact_sha256,
    )
    replacement = (
        _normalizer()
        .DbnNormalizer(_catalog_binding(contracts))
        .normalize((_record(contracts, close="1.750000000"),), source)
    )

    with pytest.raises(contracts.DbnEventBuildError, match="MANIFEST_INTEGRITY"):
        _event_factory().MarketEventFactory().build(
            replacement, report, manifest, "RUN-P2-DBN-001", source.raw_received_at_utc
        )


def test_dbn_snapshot_rejects_missing_required_code_revision(tmp_path: Path) -> None:
    contracts = _contracts()
    normalizer = _normalizer().DbnNormalizer(_catalog_binding(contracts))
    source = _replay_input(contracts)
    normalized = normalizer.normalize((_record(contracts),), source)
    quality_module = importlib.import_module("autotrade.market_data.quality")
    manifest_module = importlib.import_module("autotrade.market_data.manifest")
    store_module = importlib.import_module("autotrade.market_data.normalized_store")
    report = quality_module.QualityChecker.check(tuple(item.bar for item in normalized))
    manifest = manifest_module.ManifestBuilder.build_dbn(
        raw_sha256s=(source.payload_sha256,),
        normalization_rule_version=source.normalization_rule_version,
        catalog=_catalog_binding(contracts),
        quality_report_sha256=report.quality_report_sha256,
        normalized_content_sha256=manifest_module.normalized_content_sha256(tuple(item.bar for item in normalized)),
        fixture_sha256=None,
        code_revision="revision-v1",
        source_mode="dbn_replay",
        request_context_sha256=source.request_context_sha256,
        decoder_version=source.decoder_version,
        decoder_artifact_sha256=source.decoder_artifact_sha256,
    )
    store = store_module.LocalNormalizedStore(tmp_path)
    store.write_if_absent(tuple(item.bar for item in normalized), manifest, report)
    snapshot_path = tmp_path / "normalized" / f"{manifest.data_version}.json"
    snapshot_path.write_text(
        snapshot_path.read_text(encoding="utf-8").replace('"code_revision":"revision-v1"', '"code_revision":null'),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="MANIFEST_INTEGRITY"):
        store.read_replay_snapshot(manifest.data_version)


def test_future_adapter_boundary_forbids_vendor_and_network_imports_in_core() -> None:
    root = Path(__file__).parents[2] / "src" / "autotrade" / "market_data"
    core_modules = ("dbn_contracts.py", "dbn_normalizer.py", "market_event_factory.py")
    forbidden = ("databento", "http", "socket", "os")

    for module_name in core_modules:
        source = (root / module_name).read_text(encoding="utf-8")
        assert not any(f"import {name}" in source for name in forbidden)

    decoder_source = (root / "databento_dbn_decoder.py").read_text(encoding="utf-8")
    assert "import databento" in decoder_source


def test_future_wsl_dbn_preflight_requires_protected_input_and_wheel_allowlist() -> None:
    root = Path(__file__).parents[2] / "scripts" / "wsl_quality_gate"
    entrypoint = (root / "run_test.ps1").read_text(encoding="utf-8")
    isolated_runner = (root / "run_isolated_p2.ps1").read_text(encoding="utf-8")
    linux_runner = (root / "run_isolated_p2.sh").read_text(encoding="utf-8")
    offline_installer = (root / "prepare_offline_wsl_env.sh").read_text(encoding="utf-8")
    registry = (Path(__file__).parents[2] / "scripts" / "quality_gate" / "trusted_scopes.json").read_text(
        encoding="utf-8"
    )

    for required_text in (
        "RUN-P2-DBN-001",
        "networkingMode=none",
        "test -L",
        "/mnt",
        "sha256sum",
        "--require-hashes",
        'git -c safe.directory="$repository_path" -C "$repository_path" diff --cached',
        'git -c safe.directory="$repository_path" -C "$repository_path" ls-files',
        "post_input_hash",
        "offline-preparation.json",
        "dbn_requirements_sha256",
    ):
        assert required_text in entrypoint + isolated_runner + linux_runner + offline_installer + registry


def test_core_contracts_do_not_expose_vendor_sdk_or_secret_fields() -> None:
    contracts = _contracts()
    fields = set(contracts.DbnReplayInput.__dataclass_fields__)

    assert {"api_key", "authorization", "account", "databento_record", "sdk_exception"}.isdisjoint(fields)
