# P04 Pending Conflicts v0.1

- Step ID: P04
- Status: completed_pending_next_steps
- Created at: 2026-08-02T13:53:07.1831656+09:00

## Summary

- Verified universe rows: 154
- pending_evidence rows: 149
- research_only rows: 5

## Key unresolved items

- IBSJ product pages and API docs verify the broker/API framework, but they do not prove every symbol in the longlist is tradable by a Japan-resident account today.
- IBSJ product-search pages explicitly warn that displayed products may include items not tradable in an IBSJ account. Therefore symbol-level tradability remains pending where only generic venue evidence exists.
- Web API access for individuals requires a fully open and funded live account, and the live account must be IBKR Pro. Paper-account API usage inherits that prerequisite.
- Most API market data requires a live Level 1 subscription. This blocks any assumption that realtime or historical data is available at zero cost.
- OSE/TOCOM evidence is stronger than overseas venues because IBSJ publishes domestic trading rules and OSE fee schedules directly.
- NASDAQ rows are kept as research-only because executable venue mapping was not verified in P04.

## Venue row counts

- CBOT: 15
- CFE: 2
- CME: 36
- COMEX: 6
- EUREX: 14
- ICEEU: 4
- ICEUS: 10
- NASDAQ: 5
- NYMEX: 9
- OSE: 31
- SGX: 13
- TOCOM: 9

## P05 handoff

- P05 should consolidate duplicate vehicles and normalize exposures using this verified universe.
- P06 must not pass any candidate whose margin, multiplier, minimum quantity, or Japan-resident eligibility remains unknown.
- If earlier hard-gate pressure is needed, prioritize OSE/TOCOM, then CME/CBOT/NYMEX/COMEX/SGX, then ICE/EUREX/CFE.

