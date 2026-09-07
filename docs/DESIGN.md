# Design direction

Use Notion as inspiration for calm navigation, readable workspaces and progressive
disclosure; Robinhood for numerical hierarchy, focused charts and simple primary
actions. These are directional references, not copied assets or a final design.

Primary loop: find a series → inspect provenance → define assumptions → run
analysis → compare outcomes → save a reproducible research record.

- Neutral surfaces, strong typography, generous spacing and one accent color.
- Persistent workspace navigation; defer a block editor until needed.
- Lead with research question, units, timeframe and the most useful chart.
- Disclose advanced parameters progressively; keep assumptions discoverable.
- Show source, period, retrieval time, vintage, transformations and uncertainty
  beside results. Distinguish observations, fits and forecasts.
- Green is not automatically a good economic outcome.
- Explicit loading, missing, empty, stale and error states.
- Keyboard operation, visible focus, semantic HTML, readable contrast, reduced
  motion and non-color-only chart encodings. Target WCAG 2.2 AA.
- Support narrow windows without hiding provenance.

Before implementation, review sketches for a series browser, scenario editor and
comparison view. The current screen only verifies the frontend toolchain.
