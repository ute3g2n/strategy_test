# CTX-07 RED evidence

- Step: CTX-07 — commit前ゲート・監視経路・運用安全化
- 実行日: 2026-08-14
- 方式: TDD。Gateの実装前に、変更経路、H1拒否、Git index保護、A07未起動を固定するテストを追加した。

## 実行結果

```text
Command: .venv/Scripts/python.exe -m pytest tests/context_index/test_context_gate.py -q
Result: collection error
Error: ModuleNotFoundError: No module named 'scripts.context_index.context_watch'
```

これは、CTX-07で追加するGate／watcher実体が未作成であることを確認するREDであり、失敗を成功扱いしていない。

## 固定した失敗条件

- 新規・大幅変更文書はA07のstrict receiptがなければpending／BLOCKEDになる。
- Gate失敗時はmanifestだけでなくGit indexも変更しない。
- Secret、rename、delete、validator不合格、対象外pathはcommit経路を閉じる。
- 既存の未追跡ファイルをauto-commitが暗黙にstageしない。
- H1承認receiptなしのwatch-start／watch-commitは拒否する。

## Runtime境界

CTX-07の固定A07モデル `gpt-5.1` は `Unknown model` で起動できなかった。代替モデルをA07として扱わず、`agent_id=N/A`、`independent=false`、`review_mode=SELF_REVIEW_FALLBACK`相当の制限を受入証跡へ残す。
