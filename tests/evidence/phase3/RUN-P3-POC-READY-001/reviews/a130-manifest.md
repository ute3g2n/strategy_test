# P3-08R-03 A130 Manifest / Verification Review

## 判定

- Review target: `RUN-P3-POC-READY-001`
- Step: `P3-08R-03`
- Findings first: Critical 0 / High 0 / Medium 0 / Unknown 0
- Result: PASS for the R-03 preparation boundary

## 確認内容

1. `run-manifest.json`はP3-09本Run ID、Phase、step、準備Run IDを束縛している。
2. P3-08R-01のinput-contract hash、承認済みparent/child fixture hash、P3-08Aのimage digest・tar hash・LICENSE hashをManifestへ再構成なしで束縛している。
3. R-01時点の`source_contract_head`と、Core reference生成に使用した`code_revision`を分離して記録している。両方ともfull lowercase commitである。
4. Core reference、LEAN output schema、parity mapのファイルhashはManifestと実ファイルで一致している。
5. `manifest_sha256`は自身を除くcanonical payloadから再計算できる。expected値はCore referenceのみを出所とし、LEAN実測値を含まない。
6. P3-AC-01〜08はparity mapへ1件ずつ割り当てられ、未割当数は0である。

## 境界

このレビューはManifestとexpected artifactの固定性を対象とする。LEAN実engineの起動、P3-09本Runの判定、性能実測、WSL隔離GateのPASSは主張しない。
