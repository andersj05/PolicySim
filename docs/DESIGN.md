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

## Implemented explorer

The first screen uses a persistent workspace sidebar, two source cards, a search
bar with Ctrl/Cmd+K focus, catalog results and an observation detail panel. Each
series offers a time chart, exact-value table, source notes and a JSON download.
Country/aggregate and date controls expose selection without numerical transforms.
The layout stacks below 740px; provenance stays available on narrow windows.

Metadata suggestions are navigation shortcuts, not synthetic time series. Green
identifies the active series and does not judge an economic outcome. Chart gaps
remain gaps; keyboard users can inspect every original value in the table. Loading,
provider errors, empty searches and empty date ranges have explicit states.
The source guide uses a native modal dialog with focus containment and Escape.

Scenario and comparison screens remain future milestones. No formal accessibility
certification is claimed; continue testing contrast, keyboard and assistive
technology behavior as the workspace grows.
