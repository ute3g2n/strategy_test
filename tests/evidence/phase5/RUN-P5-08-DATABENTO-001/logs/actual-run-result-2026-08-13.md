# P5-08 actual Databento run result

- Run ID: `RUN-P5-08-DATABENTO-001`
- Start: `2026-08-13T14:30:17Z`
- Finish: `2026-08-13T14:30:19Z`
- External I/O: `true`, limited by the process guard to `hist.databento.com:443`
- Provider response: `HTTP 402 / PROVIDER_STOP_HTTP_402`
- Records acquired: `0`
- Raw files: `0`
- Normalized files: `0`
- API-key value recorded: `false`
- Precondition waivers: Budget execution gate and formal host-isolation execution gate, explicitly directed by the user.
- Final run status: `BLOCKED`

Databento documents HTTP 402 as an issue with account payment information. The
runner stopped on that response and did not retry or continue to the next data
request.
