from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def read_text(relative_path: str) -> str:
    return (PROJECT_ROOT / relative_path).read_text(encoding="utf-8-sig")


def test_windows_entrypoints_delegate_from_any_working_directory() -> None:
    start_bat = read_text("start_autotrade.bat")
    stop_bat = read_text("stop_autotrade.bat")

    assert "%~dp0" in start_bat
    assert "scripts\\start_autotrade.ps1" in start_bat
    assert "-ExecutionPolicy Bypass" in start_bat
    assert "%*" in start_bat
    assert "%~dp0" in stop_bat
    assert "scripts\\stop_autotrade.ps1" in stop_bat


def test_start_script_has_loopback_build_health_and_failure_boundaries() -> None:
    script = read_text("scripts/start_autotrade.ps1")

    required_fragments = (
        "127.0.0.1:8765",
        "127.0.0.1:4173",
        "application_api_server.py",
        "npm ci",
        "'run', 'build'",
        "'run', 'preview'",
        "health",
        "NoBrowser",
        "Get-NetTCPConnection",
        "RedirectStandardOutput",
        "RedirectStandardError",
        "Start-Process",
        "二重起動しません",
        "ポートは既に使われています",
    )
    for fragment in required_fragments:
        assert fragment in script, fragment

    assert r"E:\strategy_test_data\autotrade" in script
    assert "Join-Path $storageRoot 'logs'" in script
    assert "runtime\\autotrade_app" not in script
    assert "autotrade-phase5r" not in script
    assert "0.0.0.0" not in script
    assert "Broker" not in script
    assert "Secret" not in script


def test_stop_script_only_targets_local_autotrade_start_commands() -> None:
    script = read_text("scripts/stop_autotrade.ps1")

    assert "backtest_api_server" in script
    assert "ui\\app" in script
    assert "npm.*preview|vite.*preview" in script
    assert "--port\\s+8765" in script
    assert "--port\\s+4173" in script
    assert "Stop-Process" in script
    assert r"E:\strategy_test_data\autotrade" in script
    assert "Join-Path $storageRoot 'logs'" in script
    assert "runtime\\autotrade_app" not in script


def test_manual_explains_one_step_start_stop_and_recovery() -> None:
    manual = read_text("doc/phase5R/07_運用手順/01_バックテスト手順書.html")

    required_fragments = (
        "start_autotrade.bat",
        "stop_autotrade.bat",
        r"E:\strategy_test_data\autotrade\logs",
        "127.0.0.1:8765",
        "127.0.0.1:4173",
        "npm ci",
        "ポートが使われている",
        "health check",
    )
    for fragment in required_fragments:
        assert fragment in manual, fragment
