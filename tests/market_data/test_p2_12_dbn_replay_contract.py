"""P2-12-01 RED contracts for real DBN decoding and replay.

Only the immutable P2-08 payload checksum is checked at this stage.  The
decoder, normalizer, and event factory imports are intentionally RED until
P2-12-02 implements the approved P2-D16 contract.
"""

from __future__ import annotations

import dataclasses
import importlib
from datetime import UTC, datetime
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


def test_p2_12_records_the_approved_real_input_identity_without_opening_it() -> None:
    """P2-12-01 must not open the Git-ignored DBN before H2-5."""

    assert RAW_DBN_SHA256 == "8fd0286a477e073c83e8306c4e1a8ebec3af693141010563edd7e0ec1990b65e"


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

    with pytest.raises(contracts.DbnDecodeError, match=expected_code):
        decoder.DatabentoDbnDecoder().decode(payload, _replay_input(contracts))


def test_normalizer_contract_rejects_missing_raw_received_at() -> None:
    contracts = _contracts()
    normalizer = _normalizer()
    record = contracts.DecodedOhlcvRecord(
        source_symbol="FIX.TEST",
        vendor_instrument_id=1,
        publisher_id=1,
        event_time_utc=datetime(2026, 1, 1, tzinfo=UTC),
        open="1.000000000",
        high="1.000000000",
        low="1.000000000",
        close="1.000000000",
        volume=1,
        record_ordinal=0,
    )

    with pytest.raises(contracts.DbnNormalizationError, match="RAW_RECEIVED_AT_MISSING"):
        normalizer.DbnNormalizer(_catalog_binding(contracts)).normalize((record,), source=None)


@pytest.mark.parametrize("catalog_status", ["not_found", "ambiguous", "pending", "unknown"])
def test_normalizer_contract_rejects_unresolved_catalog_without_guessing(catalog_status: str) -> None:
    contracts = _contracts()
    normalizer = _normalizer()
    record = contracts.DecodedOhlcvRecord(
        source_symbol="FIX.TEST",
        vendor_instrument_id=1,
        publisher_id=1,
        event_time_utc=datetime(2026, 1, 1, tzinfo=UTC),
        open="1.000000000",
        high="1.000000000",
        low="1.000000000",
        close="1.000000000",
        volume=1,
        record_ordinal=0,
    )

    with pytest.raises(contracts.DbnNormalizationError, match="CATALOG_MAPPING_UNRESOLVED"):
        normalizer.DbnNormalizer(_catalog_binding(contracts, catalog_status)).normalize(
            (record,), source=_replay_input(contracts)
        )


def test_normalizer_contract_rejects_invalid_time_price_volume_and_order() -> None:
    contracts = _contracts()
    normalizer = _normalizer()
    invalid_record = contracts.DecodedOhlcvRecord(
        source_symbol="FIX.TEST",
        vendor_instrument_id=1,
        publisher_id=1,
        event_time_utc=datetime(2026, 1, 1),
        open="NaN",
        high="0.000000000",
        low="1.000000000",
        close="1.000000000",
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
    record = contracts.DecodedOhlcvRecord(
        source_symbol="FIX.TEST",
        vendor_instrument_id=1,
        publisher_id=1,
        event_time_utc=datetime(2026, 1, 1, tzinfo=UTC),
        open="1.000000000",
        high="1.000000000",
        low="1.000000000",
        close="1.000000000",
        volume=1,
        record_ordinal=0,
    )

    with pytest.raises(contracts.DbnNormalizationError, match="CATALOG_MAPPING_UNRESOLVED"):
        normalizer.DbnNormalizer(_catalog_binding(contracts, result_version="catalog-other")).normalize(
            (record,), source=_replay_input(contracts)
        )


def test_event_factory_contract_requires_publishable_quality_and_deterministic_id() -> None:
    contracts = _contracts()
    factory = _event_factory()

    with pytest.raises(contracts.DbnEventBuildError, match="QUALITY_REJECTED"):
        factory.MarketEventFactory().build(
            bars=(),
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

    for required_text in (
        "RUN-P2-DBN-001",
        "networkingMode=none",
        "test -L",
        "/mnt",
        "sha256sum",
        "--require-hashes",
        "git diff --cached",
    ):
        assert required_text in entrypoint + isolated_runner


def test_core_contracts_do_not_expose_vendor_sdk_or_secret_fields() -> None:
    contracts = _contracts()
    fields = set(contracts.DbnReplayInput.__dataclass_fields__)

    assert {"api_key", "authorization", "account", "databento_record", "sdk_exception"}.isdisjoint(fields)
