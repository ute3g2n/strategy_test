# AI Component Rules

## Purpose

This project uses explicit naming, HTML-first specifications, and strict trigger control for AI components.

## Naming

- Generic orchestrator: `AutoTradeProject_*`
- Generic agents: `AutoTrade_Axx_*`
- Generic skills: `autotrade_skill_*`
- Phase-specific orchestrator: `AutoTradePhaseX_*`
- Phase-specific agents: `AutoTradePhaseX_Axx_*`
- Phase-specific skills: `autotrade_phaseX_skill_*`

## Creation Rules

- Prefer generic skills, generic agents, and the generic orchestrator first.
- Create a phase-specific component only when a generic component is insufficient.
- A phase-specific component requires a reason, an expiry or freeze condition, and an HTML specification.
- Never overwrite an existing component when names conflict. Report the conflict and stop.
- Keep Phase 1 components as frozen legacy evidence. Do not delete, move, rename, or overwrite them.

## Trigger Rules

- Prompts must explicitly name the orchestrator, agents, and skills that may be used.
- Do not guess or auto-select existing components for AI component tasks.
- If a named component does not exist and the current step is not a creation step, stop and report the missing names.
- Do not change `default_orchestrator` without explicit approval.

## Output Rules

- Formal specifications must be HTML and saved under `doc/`.
- Planning documents, prompts, logs, and ledgers belong under `plan/`.
- Every HTML artifact under `doc/` must be reachable from `doc/index.html`.
- Phase-specific HTML should be saved under `doc/phaseX/`.
- AI foundation HTML should be saved under `doc/ai_foundation/`.

## Safety Rules

- Do not produce investment advice, trade recommendations, or product recommendations.
- Unknown must not pass. Record unknowns with IDs and target decision timing.
- Do not emit secrets, API keys, or credentials.
- Do not weaken fail-closed, audit trail, or manual intervention controls during revision work.
- Prefer official primary sources when external specifications are needed, and record the URL and check date.
