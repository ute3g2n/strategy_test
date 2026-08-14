from __future__ import annotations

# Step 02 user authority: code-management hashes, content fingerprints, stale
# checks, and hash retries are force-skipped. Code deltas use IDs, paths, and
# extracted structural metadata only.
from collections.abc import Mapping
from typing import Any


def _records(manifest: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    raw = (manifest or {}).get("artifacts", [])
    if not isinstance(raw, list):
        return []
    return [dict(item) for item in raw if isinstance(item, Mapping) and isinstance(item.get("code_id"), str)]


def _structure_signature(record: Mapping[str, Any]) -> tuple[Any, ...]:
    symbols: list[tuple[Any, ...]] = []
    for symbol in record.get("symbols", []) if isinstance(record.get("symbols"), list) else []:
        if isinstance(symbol, Mapping):
            symbols.append(
                (
                    symbol.get("name"),
                    symbol.get("qualified_name"),
                    symbol.get("kind"),
                    symbol.get("parent"),
                    tuple(symbol.get("decorators", [])) if isinstance(symbol.get("decorators", []), list) else (),
                    bool(symbol.get("public")),
                )
            )
    symbols.sort(key=repr)
    imports: list[tuple[Any, ...]] = []
    for imported in record.get("imports", []) if isinstance(record.get("imports"), list) else []:
        if isinstance(imported, Mapping):
            imports.append(
                (
                    imported.get("kind"),
                    imported.get("module"),
                    imported.get("name"),
                    imported.get("alias"),
                    imported.get("level"),
                )
            )
    imports.sort(key=repr)
    exports = tuple(sorted(str(item) for item in record.get("exports", []) if isinstance(item, str)))
    return (
        record.get("language"),
        record.get("parser"),
        record.get("extraction_status"),
        tuple(symbols),
        tuple(imports),
        exports,
        repr(record.get("config", {})),
    )


def _event(code_id: str, change_kind: str, **values: Any) -> dict[str, Any]:
    result: dict[str, Any] = {"code_id": code_id, "change_kind": change_kind}
    result.update(values)
    return result


def detect_code_delta(
    before_manifest: Mapping[str, Any] | None,
    after_manifest: Mapping[str, Any] | None,
) -> list[dict[str, Any]]:
    """Compare two code manifests without reading source files or hash fields."""

    before = _records(before_manifest)
    after = _records(after_manifest)
    before_by_id = {str(item["code_id"]): item for item in before}
    after_by_id = {str(item["code_id"]): item for item in after}
    changes: list[dict[str, Any]] = []
    for code_id in sorted(set(before_by_id) & set(after_by_id)):
        old = before_by_id[code_id]
        new = after_by_id[code_id]
        old_path = str(old.get("relative_path", ""))
        new_path = str(new.get("relative_path", ""))
        if old_path != new_path:
            changes.append(_event(code_id, "renamed", from_path=old_path, relative_path=new_path))
        elif _structure_signature(old) != _structure_signature(new) or old.get("byte_size") != new.get("byte_size"):
            kind = (
                "modified_structural"
                if _structure_signature(old) != _structure_signature(new)
                else "modified_non_structural"
            )
            changes.append(_event(code_id, kind, relative_path=new_path))
    for code_id, item in sorted(before_by_id.items()):
        if code_id not in after_by_id:
            changes.append(_event(code_id, "deleted", relative_path=str(item.get("relative_path", ""))))
    for code_id, item in sorted(after_by_id.items()):
        if code_id not in before_by_id:
            changes.append(_event(code_id, "added", relative_path=str(item.get("relative_path", ""))))
    return sorted(
        changes,
        key=lambda item: (
            str(item.get("relative_path", "")),
            str(item.get("from_path", "")),
            str(item.get("change_kind", "")),
            str(item.get("code_id", "")),
        ),
    )
