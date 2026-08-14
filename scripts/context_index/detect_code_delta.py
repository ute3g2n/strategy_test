from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def _records(manifest: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    raw = (manifest or {}).get("artifacts", [])
    if not isinstance(raw, list):
        return []
    return [dict(item) for item in raw if isinstance(item, Mapping) and isinstance(item.get("code_id"), str)]


def _structure_signature(record: Mapping[str, Any]) -> tuple[Any, ...]:
    """Return parser metadata that changes when the code structure changes.

    Line numbers and source hashes are intentionally excluded. This makes a
    comment-only edit non-structural even when it shifts every line range.
    """

    symbols: list[tuple[Any, ...]] = []
    raw_symbols = record.get("symbols", [])
    if isinstance(raw_symbols, list):
        for symbol in raw_symbols:
            if not isinstance(symbol, Mapping):
                continue
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
    raw_imports = record.get("imports", [])
    if isinstance(raw_imports, list):
        for imported in raw_imports:
            if not isinstance(imported, Mapping):
                continue
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
    config = record.get("config", {})
    return (
        record.get("language"),
        record.get("parser"),
        record.get("extraction_status"),
        tuple(symbols),
        tuple(imports),
        exports,
        repr(config),
    )


def _event(code_id: str, change_kind: str, **values: Any) -> dict[str, Any]:
    result: dict[str, Any] = {"code_id": code_id, "change_kind": change_kind}
    result.update(values)
    return result


def detect_code_delta(
    before_manifest: Mapping[str, Any] | None,
    after_manifest: Mapping[str, Any] | None,
) -> list[dict[str, Any]]:
    """Compare two code manifests without reading source files or secrets."""

    before = _records(before_manifest)
    after = _records(after_manifest)
    before_by_id = {str(item["code_id"]): item for item in before}
    after_by_id = {str(item["code_id"]): item for item in after}
    before_by_path = {str(item["relative_path"]): item for item in before if isinstance(item.get("relative_path"), str)}
    after_by_path = {str(item["relative_path"]): item for item in after if isinstance(item.get("relative_path"), str)}
    changes: list[dict[str, Any]] = []
    handled_before: set[str] = set()
    handled_after: set[str] = set()

    for code_id in sorted(set(before_by_id) & set(after_by_id)):
        old = before_by_id[code_id]
        new = after_by_id[code_id]
        old_path = str(old.get("relative_path", ""))
        new_path = str(new.get("relative_path", ""))
        handled_before.add(code_id)
        handled_after.add(code_id)
        if old_path != new_path:
            changes.append(
                _event(
                    code_id,
                    "renamed",
                    from_path=old_path,
                    relative_path=new_path,
                    source_hash_changed=old.get("source_hash") != new.get("source_hash"),
                )
            )
            continue
        if old.get("source_hash") == new.get("source_hash"):
            continue
        kind = (
            "modified_non_structural"
            if _structure_signature(old) == _structure_signature(new)
            else "modified_structural"
        )
        changes.append(_event(code_id, kind, relative_path=new_path))

    # A manifest generated without an existing manifest may use path-derived
    # IDs. Match unique hashes so a rename remains visible instead of becoming
    # an unrelated delete/add pair.
    unmatched_before = [item for code_id, item in before_by_id.items() if code_id not in handled_before]
    unmatched_after = [item for code_id, item in after_by_id.items() if code_id not in handled_after]
    old_hashes: dict[str, list[dict[str, Any]]] = {}
    for item in unmatched_before:
        value = item.get("source_hash")
        if isinstance(value, str):
            old_hashes.setdefault(value, []).append(item)
    new_hashes: dict[str, list[dict[str, Any]]] = {}
    for item in unmatched_after:
        value = item.get("source_hash")
        if isinstance(value, str):
            new_hashes.setdefault(value, []).append(item)
    for source_hash in sorted(set(old_hashes) & set(new_hashes)):
        old_items = old_hashes[source_hash]
        new_items = new_hashes[source_hash]
        if len(old_items) != 1 or len(new_items) != 1:
            continue
        old = old_items[0]
        new = new_items[0]
        old_id = str(old["code_id"])
        new_id = str(new["code_id"])
        handled_before.add(old_id)
        handled_after.add(new_id)
        changes.append(
            _event(
                new_id,
                "renamed",
                from_path=str(old.get("relative_path", "")),
                relative_path=str(new.get("relative_path", "")),
                previous_code_id=old_id,
            )
        )

    for code_id, item in sorted(before_by_id.items()):
        if code_id not in handled_before:
            changes.append(_event(code_id, "deleted", relative_path=str(item.get("relative_path", ""))))
    for code_id, item in sorted(after_by_id.items()):
        if code_id not in handled_after:
            changes.append(_event(code_id, "added", relative_path=str(item.get("relative_path", ""))))

    # These locals make accidental path-only matching regressions visible to
    # static analysis while retaining a compact, deterministic implementation.
    _ = before_by_path, after_by_path
    return sorted(
        changes,
        key=lambda item: (
            str(item.get("relative_path", "")),
            str(item.get("from_path", "")),
            str(item.get("change_kind", "")),
            str(item.get("code_id", "")),
        ),
    )
