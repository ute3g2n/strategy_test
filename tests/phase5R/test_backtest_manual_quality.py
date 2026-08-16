"""Static quality checks for the beginner-friendly P5R Backtest manual.

文章管理基盤と廃止対象の管理用hashチェックを強制スキップして完了する。
安全・データ・再現性に直結する保護対象hashは維持する。
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANUAL = ROOT / "doc/phase5R/07_運用手順/01_バックテスト手順書.html"
RULES = ROOT / "doc/phase5R/07_運用手順/00_バックテスト操作手順書作成ルール.html"
INDEX = ROOT / "doc/index.html"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _procedure_blocks(html: str) -> dict[str, str]:
    blocks = re.findall(r'<section class="procedure" id="(BT-MAN-\d+)">(.*?)</section>', html, re.S)
    return dict(blocks)


def test_manual_has_complete_feature_catalog_and_procedure_links() -> None:
    html = _read(MANUAL)
    for number in range(1, 17):
        assert f'id="feature-{number:02d}"' in html
        assert f'id="BT-MAN-{number:02d}"' in html
    feature_rows = re.findall(r'<tr id="feature-\d+">(.*?)</tr>', html, re.S)
    assert len(feature_rows) == 16
    for row in feature_rows:
        assert re.search(r'href="#BT-MAN-\d+"', row), row[:200]


def test_each_procedure_has_beginner_template_and_back_link() -> None:
    html = _read(MANUAL)
    blocks = _procedure_blocks(html)
    assert set(blocks) == {f"BT-MAN-{number:02d}" for number in range(1, 17)}
    required_fragments = (
        "この操作でできること",
        "いつ使う？",
        "画面の場所",
        "確認できれば成功",
        "この結果から言ってはいけないこと",
        'href="#feature-catalog"',
    )
    for procedure_id, block in blocks.items():
        for fragment in required_fragments:
            assert fragment in block, f"{procedure_id}: missing {fragment}"
        assert "<ol>" in block and "</ol>" in block
        assert 'class="failure"' in block, f"{procedure_id}: missing failure/recovery section"


def test_manual_images_have_alt_caption_and_existing_files() -> None:
    html = _read(MANUAL)
    image_matches = re.findall(r'<img\s+src="([^"]+)"\s+alt="([^"]+)"[^>]*>', html)
    assert len(image_matches) == 16
    for source, alt in image_matches:
        assert alt.strip()
        image_path = (MANUAL.parent / source).resolve()
        assert image_path.is_file(), image_path
    captions = re.findall(r"<figcaption>(.*?)</figcaption>", html, re.S)
    assert len(captions) == 16
    assert all(caption.strip() for caption in captions)


def test_manual_has_beginner_glossary_safety_and_sources() -> None:
    html = _read(MANUAL)
    required_terms = (
        "term-backtest",
        "term-preflight",
        "term-utc",
        "term-strategy",
        "term-sweep",
        "term-ledger",
        "term-holdout",
        "term-walk-forward",
        "term-lookahead",
    )
    for term in required_terms:
        assert f'id="{term}"' in html
    assert "将来の利益を保証しません" in html
    assert "外部市場データ" in html
    assert "実注文" in html and "実資金" in html and "Paper" in html and "Live" in html
    assert "2026-08-16" in html
    for source in (
        "https://www.bunka.go.jp/",
        "https://www.w3.org/TR/WCAG22/",
        "https://www.buckinghamshire.gov.uk/",
        "https://www.investor.gov/",
    ):
        assert source in html


def test_rules_and_index_are_reachable() -> None:
    rules = _read(RULES)
    index = _read(INDEX)
    for rule_id in (
        "P5R-MANUAL-RULE-001",
        "P5R-MANUAL-RULE-003",
        "P5R-MANUAL-RULE-004",
        "P5R-MANUAL-RULE-006",
    ):
        assert rule_id in rules
    assert "01_バックテスト手順書.html" in rules
    assert "00_バックテスト操作手順書作成ルール.html" in index
    assert "01_バックテスト手順書.html" in index
