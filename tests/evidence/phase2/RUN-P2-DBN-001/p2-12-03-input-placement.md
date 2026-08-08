# P2-12-03 入力配置・完全性確認

- Run: `RUN-P2-DBN-001`
- 状態: **配置済み・照合済み**
- ユーザー承認: `windows側のinputデータを使って下さい。許可します。`
- Windows入力: `tests/evidence/phase2/RUN-P2-DP-002/raw/mcl-fut-20260615T1200Z-1201Z.dbn`
- WSL保護場所: `/var/lib/autotrade/replay/RUN-P2-DBN-001/input.dbn`
- ファイルサイズ: `22760` bytes
- SHA-256（Windows / WSL / 期待値）: すべて `8fd0286a477e073c83e8306c4e1a8ebec3af693141010563edd7e0ec1990b65e`
- WSL所有者・権限: `root` / `0400`

やさしい説明: Windowsにある決めた一箱を、WSLの鍵付き棚へ置きました。箱の中身を表す長い番号も、Windows・WSL・事前に決めた番号で全部同じです。次の検証では、この箱以外を使いません。
