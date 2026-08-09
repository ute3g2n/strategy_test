"""P3-07 EngineAdapter boundary contracts without an engine SDK."""

from __future__ import annotations

import ast
import importlib
import inspect
from typing import Any

import pytest


def _operation(name: str):
    try:
        module = importlib.import_module("autotrade.backtest.engine_adapter")
    except ModuleNotFoundError as error:
        pytest.fail(f"P3-07 must provide autotrade.backtest.engine_adapter: {error}")
    operation = getattr(module, name, None)
    assert callable(operation), f"autotrade.backtest.engine_adapter.{name} is required"
    return operation


@pytest.mark.parametrize(
    ("operation_name", "input_value", "expected"),
    [
        (
            "reject_offline_violation",
            {"outbound_attempt": True},
            {"status": "STOPPED", "reason": "OFFLINE_POLICY_VIOLATION"},
        ),
        (
            "reject_unpinned_engine",
            {"oci_tag_only": True},
            {"status": "STOPPED", "reason": "ENGINE_IDENTITY_UNPINNED"},
        ),
        (
            "validate_engine_identity",
            {"engine": "ENGINE_NOT_USED"},
            {"status": "STOPPED", "reason": "ENGINE_IDENTITY_UNPINNED"},
        ),
        (
            "reject_engine_sdk_leak",
            {"sdk_type_in_public_dto": True},
            {"status": "STOPPED"},
        ),
        (
            "run_fake_engine_adapter",
            {"sdk_imports": 0},
            {"status": "STOPPED", "reason": "ENGINE_IDENTITY_UNPINNED"},
        ),
    ],
)
def test_engine_adapter_operations_remain_common_dto_only(
    operation_name: str, input_value: dict[str, Any], expected: dict[str, Any]
) -> None:
    result = _operation(operation_name)(input_value)
    assert result == expected


def test_engine_adapter_has_no_vendor_sdk_import_surface() -> None:
    module = importlib.import_module("autotrade.backtest.engine_adapter")
    tree = ast.parse(inspect.getsource(module))
    forbidden_roots = {"nautilus", "quantconnect", "lean", "databento", "broker"}
    imports = [
        node.module.split(".", 1)[0].lower()
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    ]
    imports.extend(
        alias.name.split(".", 1)[0].lower()
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    )
    assert not (set(imports) & forbidden_roots)
