# P5-06 Evidence index

- Run ID: `RUN-P5-06-LOCAL-001`
- Formal result: `PASS`. The approved host harness produced execution-ID-matched isolation Evidence and the registered four fixed Gates all passed.
- Host isolation: `CONFIRMED`; `networking_mode=none`; loopback only; no default route; wrapper execution ID `f4e85f745e6f4a79909361a360c0e4ae`.
- External communication: `0` attempted by this P5-06 execution.
- P5-DATA-G1: `NOT_APPROVED`; no provider, endpoint, Secret, cost, external Data, Broker, Paper, or Live activity occurred.

| Evidence | Result |
|---|---|
| `dispatch-receipts.md` | Root receipt is actual (`019ff5c0-5620-7881-b7b3-5b6473319164`); all six children use runtime fallback, `independent=false`. |
| `run-manifest.json` | Registered Run, fixed Linux WSL commands, target-only scope, fixture binding, empty Unknowns, and target-only change hash. |
| `red-command.md` | RED: `5 passed, 2 failed`; missing Calendar/as-of contract. |
| `direct-local-checks.md` | Historical direct checks: formatter, lint, type, and `102 passed`. |
| `verification.json` | Formal result PASS; formatter, lint, type, and test all PASS; fixture pre/post hashes match. |
| `host-isolation.json` | Host wrapper Evidence: `CONFIRMED`, `networking_mode=none`, execution ID matched. |
| `automation/run-test-summary.json` | Native Windows wrapper completed with `state=PASS`, exit code `0`. |
| `reviews/python-code-review.md` | Self-review fallback; Critical=0, High=0; no independent-review claim. |
| `reviews/trading-security-review.md` | Self-review fallback; Critical=0, High=0; host isolation resolved by final Run Evidence. |

Fixture SHA-256: `sha256:c19d1c165f0214c2f64218208684e01c1f6b08b838d2821a2b6f172750637a99`.
Target-only change hash: `sha256:92d6223459056eeff446bfe3dbc6dfc4023596e07c1fe8a42a744f0d0f1287fb`.
