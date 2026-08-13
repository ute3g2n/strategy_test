# P5-08 Secret verification policy change

- The requirement to submit an API-key portal screenshot is removed for P5-08.
- The existing `DATABENTO_API_KEY` environment variable is used; no new key is required.
- Verification is limited to environment-variable presence.
- The secret value remains prohibited from reading into evidence, logging, JSON, HTML, CLI arguments, or chat.
- Key rotation, deletion, and portal metadata changes are not required by this step.
- A provider authentication failure during the explicit run remains fail-closed.
