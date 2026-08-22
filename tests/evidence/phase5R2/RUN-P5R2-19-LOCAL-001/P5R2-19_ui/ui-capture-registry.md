# P5R2-19 UI capture registry

The dedicated Playwright journey captured each screen after DOM, boundary, and accessibility assertions. The JSON registry written by the test is the machine-readable source for each viewport:

- [Desktop registry](../ui/chromium-desktop/p5r2-ui-capture.json)
- [Mobile registry](../ui/chromium-mobile/p5r2-ui-capture.json)

Screens captured for both viewports:

- SCREEN-08 condition and Data Catalog
- SCREEN-09 execution list / progress
- SCREEN-10 result summary and DELETE-G1 disabled state

The PNG files beside each registry are evidence captures. They are not fixed-dummy acceptance evidence: the journey starts the local Application API and verifies the rendered P5R2 API boundary.
