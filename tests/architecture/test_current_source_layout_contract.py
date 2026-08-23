"""Current product source layout and neutral naming contracts."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
UI_ROOT = ROOT / "ui" / "app"
SERVER_ROOT = ROOT / "scripts" / "application_server"
FORBIDDEN = re.compile(r"p5r2|p5r|phase5r|ui[\\/]mock", re.IGNORECASE)
FIXED_COMPATIBILITY_TOKENS = ("P5R-LEGACY-MIGRATION-V1",)
ACTIVE_FILE_SUFFIXES = {".py", ".ps1", ".js", ".ts", ".tsx", ".css", ".html", ".json"}


def _active_source_files() -> list[Path]:
    roots = [ROOT / "src" / "autotrade" / "application", UI_ROOT / "src", SERVER_ROOT]
    files = [path for root in roots if root.is_dir() for path in root.rglob("*") if path.is_file()]
    files.extend(ROOT / name for name in ("scripts/start_autotrade.ps1", "scripts/stop_autotrade.ps1"))
    return [path for path in files if path.suffix.lower() in ACTIVE_FILE_SUFFIXES]


def test_current_ui_and_server_roots_are_feature_named() -> None:
    assert UI_ROOT.is_dir(), "現行UIはui/appに配置する"
    assert not (ROOT / "ui" / "mock").exists(), "ui/mockを現行UIの配置として残さない"
    assert SERVER_ROOT.is_dir(), "現行API起動ソースはscripts/application_serverに配置する"
    assert not (ROOT / "scripts" / "phase5r").exists(), "scripts/phase5rを現行起動ソースとして残さない"


def test_active_source_does_not_contain_phase_names_or_old_ui_path() -> None:
    violations: list[str] = []
    for path in _active_source_files():
        relative = path.relative_to(ROOT).as_posix()
        if FORBIDDEN.search(relative):
            violations.append(f"path: {relative}")
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for token in FIXED_COMPATIBILITY_TOKENS:
            content = content.replace(token, "")
        if FORBIDDEN.search(content):
            violations.append(f"content: {relative}")
    assert not violations, "現行実行ソースに旧配置またはフェーズ名が残っています: " + ", ".join(violations)


def test_ui_package_and_api_use_feature_names() -> None:
    package = json.loads((UI_ROOT / "package.json").read_text(encoding="utf-8"))
    assert package["name"] == "autotrade-ui"

    source = "\n".join(path.read_text(encoding="utf-8") for path in _active_source_files())
    assert "/api/backtest-product" in source
    assert "/api/p5r2" not in source
