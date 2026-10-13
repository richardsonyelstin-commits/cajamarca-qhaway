# Andean Civic Observatory: Design System Specification

## Brand & Style

This design system elevates regional public oversight into an authoritative, investigative journalism standard. Rooted in institutional clarity and civic rigor, it balances high-density open contracting metrics with the refined visual dignity of an independent watchdog publication. 

The aesthetic is **Modern Institutional Journalism**: deliberate, structured, and sober. It avoids sterile government bureaucracy and flashy tech startup tropes, adopting instead the understated gravitas of investigative data desks like ProPublica or ICIJ. Visual elements communicate trust, algorithmic neutrality, and unyielding accuracy through precise borders, meticulous metric callouts, and clean micro-interactions.

## Colors

The palette is anchored by deep Andean slates and structured civic emeralds, establishing a hierarchy based on verifiable facts and analytical restraint.

- **Primary (`#0f172a` / `#000000`)**: Deep Andean Slate anchors headlines, critical data labels, and formal borders, conveying institutional weight and uncompromising focus.
- **Secondary (`#006a63` / `#0f766e`)**: Civic Teal signals verification, official database synchronicity, and active audit points.
- **Named Accents**:
  - `civic-emerald` (`#047857`): Denotes clean procurement pipelines, compliant budgets, and healthy transparency indices.
  - `alert-amber` (`#b45309`) and `alert-rose` (`#e11d48`): Highlight statistical outliers, single-bidder procurement warnings, and discrepancy alerts without resorting to sensationalist alarms.
  - `slate-surface` (`#f8fafc`) and `slate-border` (`#e2e8f0`): Create high-contrast editorial surfaces that separate metric modules cleanly on varied display densities.

## Typography

The typography system pairs the intellectual editorial authority of **Newsreader** with the high-legibility, precision engineering of **Hanken Grotesk**.

- **Editorial Headlines (Newsreader)**: Used for investigation titles, observatory statements, section headers, and qualitative summaries. Its transitional serifs bring gravitas, reinforcing the investigative mission of civic monitoring.
- **Data & Administrative Engine (Hanken Grotesk)**: Powers tables, OCDS metrics, navigation, filters, status pills, and body analysis. Its clean apertures guarantee immediate legibility across dense financial disclosures and low-bandwidth rural mobile interfaces.
- **Data Tables & Codes (JetBrains Mono / Tabular Numerals)**: Strict vertical alignment for figures in Soles (PEN), RUC numbers, and OCDS OCID identifiers.

## Layout & Spacing

A structured 12-column grid system governs desktop interfaces, collapsing to 8 columns on tablet and 4 columns on mobile. 

The layout follows an analytical cadence: ample outer margins frame high-density internal data blocks. Whitespace is deliberate, never ornamental. Sectional content breaks using subtle horizontal grid rules instead of dramatic vertical gaps, preserving page rhythm while retaining an orderly, newspaper-like density of information.

## Elevation & Depth

Visual hierarchy is maintained primarily through structured 1px hairline borders (`#e2e8f0`) and subtle tonal shifts rather than heavy drop shadows. 

- **Surface Elevation**: Ground-level views rest on pure white (`#ffffff`) or subdued civic slate (`#f8fafc`). Elevated cards and inspector sidebars rely on micro-borders paired with a whisper-light ambient blur (`0 1px 3px rgba(15, 23, 42, 0.04)`), preventing visual noise during prolonged audit tasks.
- **Overlay & Modals**: Critical alerts or modal dialogs use an institutional backdrop scrim (`rgba(15, 23, 42, 0.4)`) with an anchor elevation of `0 12px 24px -4px rgba(15, 23, 42, 0.08)`, prioritizing crisp contrast over heavy layering.

## Shapes

The design system employs a soft, geometric radius of `0.25rem` (`rounded` / `rounded-lg`). 

Cards, badges, tables, and form inputs utilize disciplined, near-sharp corners that evoke index cards, legal briefs, and structured public ledgers. Buttons and metric pills adopt this subtle radius to feel modern and touchable while resisting the overly playful, consumer-app appearance of larger pill shapes.
