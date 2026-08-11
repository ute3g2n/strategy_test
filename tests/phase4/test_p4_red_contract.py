"""P4-04D RED sentinel.

このファイルはProduct/Applicationの実装ではない。P4-H1前に、実装・依存・Runを
開始していないことを確認する最小のRED入口であり、P4-H1後に実装契約テストへ
置き換える。外部I/O、DB、Core、UI、fixture変更を行わない。
"""

from importlib import import_module

import pytest


@pytest.mark.parametrize(
    ("contract_id", "future_module"),
    (
        ("TEST-P4-RED-API", "autotrade.product_application.api"),
        ("TEST-P4-RED-DB", "autotrade.product_application.persistence"),
        ("TEST-P4-RED-WORKER", "autotrade.product_application.worker"),
        ("TEST-P4-RED-UI", "autotrade.product_application.ui_contract"),
        ("TEST-P4-RED-MANIFEST", "autotrade.product_application.run_manifest"),
        ("TEST-P4-RED-QUALITY", "autotrade.product_application.quality_contract"),
    ),
    ids=lambda value: value,
)
def test_p4_h1_implementation_contract_is_red(contract_id: str, future_module: str) -> None:
    """P4-H1後に必要な各境界moduleがまだ存在しないことをREDで検出する。"""

    module = import_module(future_module)
    pytest.fail(
        f"{contract_id} unexpectedly resolved {module!r}; replace this sentinel with the approved implementation contract test."
    )
