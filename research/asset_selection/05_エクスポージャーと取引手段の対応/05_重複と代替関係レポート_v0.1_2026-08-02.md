# P05 Duplicate and Proxy Report v0.1

- Step ID: P05
- Role: Exposure-Vehicle Mapper
- Status: completed
- Created at: 2026-08-02T15:14:39.3532820+09:00

## Summary

- Exposure-vehicle map rows: 154
- Unique canonical exposures: 129
- Exposures with multiple vehicles: 23
- ID migrations requiring rename: 0

## Hard gate status carried from P04

- pending_evidence: 149
- research_only: 5

## Direct / Proxy classes

- direct_listed_derivative: 149
- proxy_research_only: 5

## Proxy group counts

- PG-FX-CURRENCY-FUTURES: 25
- PG-RATES-US: 20
- PG-METALS-FUTURES: 15
- PG-ENERGY-FUTURES: 14
- PG-EQ-JAPAN: 12
- PG-GRAINS-OILSEEDS: 12
- PG-EQ-US: 11
- PG-ENVIRONMENTAL-POWER: 9
- PG-CRYPTO-FUTURES: 6
- PG-EQ-GLOBAL-REGIONAL: 5
- PG-SOFTS: 5
- PG-RESEARCH-DATA-ONLY: 5
- PG-EQ-EUROPE: 4
- PG-VOLATILITY: 4
- PG-LIVESTOCK: 3
- PG-EQ-CHINA: 3
- PG-REAL-ESTATE: 1

## Main duplicate vehicle groups

The following exposures have multiple vehicle variants. Primary/Fallback is not decided in P05.

- EXP-METAL-JP-GOLD: 3 vehicles (OSE:GOLDSTD/future_standard, OSE:GOLDMINI/future_mini, OSE:POCKETGOLD100/future_micro)
- EXP-EQ-JP-NIKKEI225: 3 vehicles (OSE:NK225L/future_standard, OSE:NK225M/future_mini, OSE:NK225MC/future_micro)
- EXP-AGRI-US-SOYBEANS: 2 vehicles (CBOT:ZS/future_standard, CBOT:XK/future_micro)
- EXP-CRYPTO-GLOBAL-BTC: 2 vehicles (CME:BTC/crypto_future, CME:MBT/crypto_future)
- EXP-AGRI-US-CORN: 2 vehicles (CBOT:ZC/future_standard, CBOT:XC/future_micro)
- EXP-AGRI-US-WHEAT: 2 vehicles (CBOT:ZW/future_standard, CBOT:XW/future_micro)
- EXP-CRYPTO-GLOBAL-ETH: 2 vehicles (CME:ETH/crypto_future, CME:MET/crypto_future)
- EXP-RATES-JP-JGB10Y: 2 vehicles (OSE:JGB10Y/future_standard, OSE:MINIJGB10Y/future_mini)
- EXP-METAL-JP-PLATINUM: 2 vehicles (OSE:PLATSTD/future_standard, OSE:PLATMINI/future_mini)
- EXP-EQ-DE-DAX: 2 vehicles (EUREX:FDAX/future_standard, EUREX:FDXM/future_mini)
- EXP-EQ-JP-TOPIX: 2 vehicles (OSE:TOPIX/future_standard, OSE:MTOPIX/future_mini)
- EXP-METAL-GLOBAL-COPPER: 2 vehicles (COMEX:HG/future_standard, COMEX:MHG/future_micro)
- EXP-EQ-US-DOW: 2 vehicles (CME:YM/future_standard, CME:MYM/future_micro)
- EXP-FX-G10-EURUSD: 2 vehicles (CME:6E/future_standard, CME:M6E/future_micro)
- EXP-EQ-US-RUSSELL2000: 2 vehicles (CME:RTY/future_standard, CME:M2K/future_micro)
- EXP-EQ-US-SP500: 2 vehicles (CME:ES/future_standard, CME:MES/future_micro)
- EXP-EQ-US-NASDAQ100: 2 vehicles (CME:NQ/future_standard, CME:MNQ/future_micro)
- EXP-FX-G10-USDJPY: 2 vehicles (CME:6J/future_standard, CME:MJY/future_micro)
- EXP-METAL-GLOBAL-GOLD: 2 vehicles (COMEX:GC/future_standard, COMEX:MGC/future_micro)
- EXP-METAL-GLOBAL-SILVER: 2 vehicles (COMEX:SI/future_standard, COMEX:SIL/future_micro)
- EXP-ENERGY-US-WTI: 2 vehicles (NYMEX:CL/future_standard, NYMEX:MCL/future_micro)
- EXP-FX-G10-GBPUSD: 2 vehicles (CME:6B/future_standard, CME:M6B/future_micro)
- EXP-FX-G10-AUDUSD: 2 vehicles (CME:6A/future_standard, CME:M6A/future_micro)

## P06 implications

- P06 should evaluate each candidate_id, not only each exposure, because standard/mini/micro variants can have materially different capital fit.
- Same exposure variants should be compared on multiplier, tick value, margin, liquidity, spread, data availability, and contract lifecycle.
- Proxy groups should be used for concentration checks. They are not automatic substitutes for each other.
- Research-only rows remain traceable but should not pass Hard Gate without executable broker/venue evidence.

## ID policy

- No exposure_id was renamed in P05.
- `candidate_id` remains the immutable execution key from P04.
- `exposure_cluster_id` is added for grouping and does not replace canonical IDs.

