# P5-08 execution stop-rule waiver

## User directive

On 2026-08-13, the user directed that the two execution stop rules causing the
P5-08 precondition block be abolished and instructed the run to proceed:

- `BUDGET_CONTROL_CONFIRMATION_REQUIRED`
- `HOST_ISOLATION_VERIFICATION_REQUIRED`

## Scope of this waiver

- The two items are removed as pre-execution hard blockers for this explicit
  P5-08 run only.
- They are recorded as `WAIVED_BY_USER`; neither `UNKNOWN` state is relabeled
  as `VERIFIED`.
- The Databento account monthly limit of 50 USD remains configured according to
  the user's portal action.
- The existing process-level `ProcessEgressGuard` remains active and allows
  only `hist.databento.com:443`.
- The post-run usage audit and the runner's post-run 25 USD check remain active.
- This waiver does not authorize Live, Broker, Paper, Core, Cloud, or any other
  external destination.

## Residual risks

- The monthly account limit is not a proof of a per-run 25 USD maximum.
- Formal OS-level host isolation remains `UNKNOWN`.
- Any provider authentication, network, cost, or data-quality failure remains
  fail-closed and is recorded in the run manifest.
