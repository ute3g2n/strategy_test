#!/usr/bin/env python3
"""Run the deterministic, non-hash protected-hash policy scan.

This helper is deliberately a lexical policy check. It never calculates,
reads, stores, compares, or prints a hash value, and it never writes a
manifest or retries after a hash-related finding.

Authority: 文章管理基盤と廃止対象の管理用hashチェックを強制スキップして完了する。
安全・データ・再現性に直結する保護対象hashは維持する。
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Final

REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[2]

MANAGEMENT_PATTERNS: Final[tuple[tuple[str, str], ...]] = (
    (r"\bsource_hash\b", "source_hash is a management identity field"),
    (r"\bartifact_hash\b", "artifact_hash is a management identity field"),
    (r"\bchange_hash\b", "change_hash is a management diff field"),
    (r"\bmanifest_sha256\b", "manifest_sha256 is a management manifest field"),
    (r"\bevidence_sha256\b", "evidence_sha256 is a management evidence field"),
    (r"\bresult_sha256\b", "result_sha256 is a management result field"),
    (r"\breceipt_hash\b", "receipt_hash is a management receipt field"),
    (r"\bfile_identity_hash\b", "file_identity_hash is a management identity field"),
    (r"\bstale(?:_hash|\s+hash)?\b", "stale hash checking is a management flow"),
    (r"hash\s*(?:mismatch|不一致)\s*(?:retry|再試行)", "hash mismatch retry is prohibited"),
)

PROTECTED_PATTERNS: Final[tuple[tuple[str, str], ...]] = (
    (r"(?:raw|payload|fixture|dbn|normalized|catalog)[^\n]{0,80}(?:sha256|hash)", "direct data identity"),
    (
        r"(?:replay|engine|dependency|checkpoint|snapshot|state)[^\n]{0,80}(?:sha256|hash)",
        "direct reproducibility or recovery identity",
    ),
)

PURPOSE_WORDS: Final[tuple[str, ...]] = (
    "safety",
    "data",
    "reproducibility",
    "再現性",
    "安全",
    "データ",
    "fail-closed",
    "停止",
)

PROHIBITION_MARKERS: Final[tuple[str, ...]] = (
    "do not",
    "must not",
    "never",
    "禁止",
    "廃止",
    "しない",
    "しません",
    "含めない",
    "作らない",
    "計算しない",
    "保存しない",
    "要求しない",
)


def _safe_target(raw_path: str) -> Path:
    """Resolve one repository-relative target without following an escape."""

    target = (REPO_ROOT / raw_path).resolve()
    try:
        target.relative_to(REPO_ROOT)
    except ValueError as error:
        raise ValueError("TARGET_OUTSIDE_REPOSITORY") from error
    if not target.is_file():
        raise ValueError("TARGET_NOT_A_FILE")
    return target


def _candidate(path: str, category: str, reason: str, suggestion: str) -> dict[str, str]:
    return {
        "path": path,
        "location": "static lexical candidate scan",
        "category": category,
        "reason": reason,
        "suggestion": suggestion,
    }


def _is_prohibition_line(line: str) -> bool:
    lowered = line.lower()
    return any(marker in lowered for marker in PROHIBITION_MARKERS)


def _has_active_management_match(pattern: str, text: str) -> bool:
    """Ignore policy prose that explicitly prohibits the matched field."""

    return any(
        re.search(pattern, line, flags=re.IGNORECASE) and not _is_prohibition_line(line)
        for line in text.splitlines()
    )


def scan_text(path: str, text: str) -> dict[str, object]:
    """Classify policy candidates without deriving any digest or identity."""

    candidates: list[dict[str, str]] = []
    lowered = text.lower()
    for pattern, reason in MANAGEMENT_PATTERNS:
        if _has_active_management_match(pattern, text):
            candidates.append(
                _candidate(
                    path,
                    "MANAGEMENT",
                    reason,
                    "remove the management-hash flow; use path, schema, state, links, or semantic identifiers",
                )
            )
    protected_found = False
    for pattern, reason in PROTECTED_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            protected_found = True
            candidates.append(
                _candidate(
                    path,
                    "PROTECTED",
                    reason,
                    "keep only with explicit purpose, direct cause, and fail-closed stop scope",
                )
            )
    generic_hash = "hash" in lowered or "sha256" in lowered or "checksum" in lowered
    purpose_found = any(word.lower() in lowered for word in PURPOSE_WORDS)
    policy_only = any(_is_prohibition_line(line) for line in text.splitlines())
    if generic_hash and not protected_found and not candidates and not (purpose_found and policy_only):
        candidates.append(
            _candidate(
                path,
                "UNKNOWN",
                "hash-like wording has no explicit protected safety, data, or reproducibility purpose",
                "send to Human Gate; do not add, remove, compare, or retry by assumption",
            )
        )

    if any(item["category"] == "MANAGEMENT" for item in candidates):
        decision = "BLOCKED"
        action = "remove or rewrite the management-hash flow, then use non-hash structural checks"
    elif any(item["category"] == "UNKNOWN" for item in candidates):
        decision = "NEEDS_HUMAN_GATE"
        action = "obtain a human decision about the hash purpose before changing the artifact"
    elif protected_found and purpose_found:
        decision = "ALLOW"
        action = "retain the protected boundary and document its fail-closed stop scope"
    elif protected_found:
        decision = "NEEDS_HUMAN_GATE"
        action = "document direct purpose and fail-closed stop scope before allowing the protected hash"
    else:
        decision = "ALLOW"
        action = "continue with non-hash structural, path, state, and link checks"
    return {
        "decision": decision,
        "targets": [path],
        "candidates": candidates,
        "required_action": action,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Static non-hash protected policy guard")
    parser.add_argument("paths", nargs="+", help="repository-relative files to inspect")
    args = parser.parse_args()
    reports: list[dict[str, object]] = []
    for raw_path in args.paths:
        target = _safe_target(raw_path)
        reports.append(scan_text(raw_path, target.read_text(encoding="utf-8")))
    if len(reports) == 1:
        print(json.dumps(reports[0], ensure_ascii=False, indent=2))
        return 0 if reports[0]["decision"] == "ALLOW" else 2
    print(json.dumps({"reports": reports}, ensure_ascii=False, indent=2))
    return 0 if all(report["decision"] == "ALLOW" for report in reports) else 2


if __name__ == "__main__":
    raise SystemExit(main())
