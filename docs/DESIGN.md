# Design direction

Use Notion as inspiration for calm navigation, readable workspaces and progressive
disclosure; Spotify for surface hierarchy, accessible controls and simple primary
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

The overview presents four source collections and the saved library. A dark sidebar
anchors navigation around Overview, Data explorer and Saved forecasts. The data
workspace uses provider tabs, catalog search and a large series panel; focus mode
hides the catalog for more chart space. Ctrl/Cmd+K reveals and focuses search.
Data, Statistics and Forecast tabs
share the series context. Advanced parameters and provenance use disclosures.

Saved-series shortcuts persist in browser storage, with a selector available when
the sidebar collapses. CSV import previews mapped columns. Tables offer sorting,
missing-only filtering, page size and optional full precision. Headline metrics
use readable precision; exports preserve values. Forecast charts distinguish
observations from dashed predictions and shaded intervals; holdout charts overlay
actuals and predictions. Saved runs reopen without refitting.

The layout stacks below 740px. Tables scroll inside their panels. Metadata uses
compact labels with strengthened contrast. Model controls retain settings across
tab/date changes, and old results are labeled when their configuration is stale.

Metadata suggestions are navigation shortcuts, not synthetic time series. Green
identifies the active series and does not judge an economic outcome. Chart gaps
remain gaps; keyboard users can inspect every original value in the table. Loading,
provider errors, empty searches and empty date ranges have explicit states.
The source guide uses a native modal dialog with focus containment and Escape.

Forecast setup provides calendar/sample readiness and an explicit action to apply
a complete history segment. Result comparisons show ranks from validation only,
even when the holdout view is open. Data headlines collapse in the Forecast tab
to prioritize model controls and results. Shared controls remain in `styles.css`;
`workbench.css` defines the navigation, discovery and refined workspace surfaces.

Scenario editing remains future work. No formal accessibility certification is
claimed; continue testing keyboard and assistive technology behavior as the workspace grows.
