# P5-08 Databento portal entitlement evidence

This evidence records the Databento portal screens supplied by the user. No
API key value, account identifier, payment detail, or credential is stored.

## Confirmed facts

- Dataset: `GLBX.MDP3` / CME Globex MDP 3.0.
- Product evidence: `MCL` / Micro WTI Crude Oil Futures.
- Publisher and venues: CME; CME, CBOT, NYMEX, COMEX.
- Historical data license: the portal states that a license is not required.
- Required schemas: `TBBO`, `OHLCV-1m`, `Definition`, `Statistics`.
- Schema availability details show all four required schemas available from
  `2010-06-06 UTC`.
- P5-08 target period `2025-02-24T00:00:00Z` through
  `2026-08-01T00:00:00Z` is within the confirmed availability start.
- This confirmation is limited to catalog availability and Historical license
  applicability. It does not prove API-key authentication, budget control, or
  host isolation.

## Stored portal screenshots

| Evidence | SHA-256 |
|---|---|
| `portal/catalog-mcl-product.png` | `BDFFF8D029B8C784E76B48C8242918C72185CA925D17D1CDA59F5306F18D3064` |
| `portal/dataset-specifications.png` | `8DFDA291C85FCB2D674C1066469F1A92247EE9FA38E70DE8F7C7489216147FCF` |
| `portal/dataset-license.png` | `51B1B570040AD983F368E3620A3A990D4ABA9A26D09FA1CF2953344359562B94` |
| `portal/dataset-availability-summary.png` | `19458F36391AC6515CC0A9A1605B9FB63C1D2E4F971EC95148183C1CFFFA3DD7` |
| `portal/dataset-schemas.png` | `658A4185CCB0AB2B1623D3EEB9F91919CE9EEFFC5C85FD6BA289693C73ED958A` |
| `portal/schema-availability-details.png` | `DE3CD25A8AAEE40770E36124F08987A4B96CEC6E75CBF232CAD8414F609EB989` |
