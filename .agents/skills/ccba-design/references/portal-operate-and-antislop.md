# Web Portal Operate Mode & Anti-Slop Discipline

Comprehensive engineering and visual discipline for enterprise web portals, operator dashboards, statutory knowledge hubs, and BIM/QC consoles. Distilled from `pbakaus/impeccable` (**Operate** mode & **Craft Floor**), `anthropics/skills` (**frontend-design**), `vercel-labs/agent-skills` (**web-design-guidelines**), and `addyosmani/web-quality-skills` (**WCAG 2.2** & **Core Web Vitals**).

## 1. Four Surface Modes Taxonomy

Before writing any HTML/CSS or component code, classify the target screen into one of four **Surface Modes**:

| Surface Mode | Primary Goal | Typical Screens | Default Density Dial | Typography Scale | Motion Budget |
|--------------|--------------|-----------------|----------------------|------------------|---------------|
| **Operate** | Task execution, high-frequency scanning, zero visual fatigue | QC/PCCC dashboards, HSHT checklists, BIM/CDE consoles, admin portals | `8-10` (Dense `8px-24px`) | Single sans-serif, fixed `rem` (`1.125-1.2` ratio) + `tabular-nums` | `150ms-200ms` state-only; zero page-load choreography |
| **Read** | Deep comprehension, verbatim citation accuracy, long-form scanning | Statutory libraries (VBPL/OKF), ADR hubs, technical specifications | `5-6` (Balanced `16px-48px`) | Sans UI + optional serif citations, strict `65-75ch` prose width | Zero decorative motion; instant anchor jumps |
| **Persuade** | Brand storytelling, conversion, capability showcase | Service landing pages, seminar portals, executive pitch overviews | `2-4` (Spacious `24px-96px`) | Expressive display heading + clean body (`<80ch`) | 1 core hero effect + 1 supporting transition |
| **Experience** | Spatial exploration, 3D/CAD model inspection, interactive canvas | 3D BIM viewers, Excalidraw/diagram canvases, molecular/CAD sidecars | `8-9` (Compact floating HUD) | Compact HUD labels (`12px-14px`) + monospace coordinates | 60fps canvas interaction; zero main-thread blocking |

## 2. Portal & Dashboard Rules (Operate Mode)

The primary failure mode of enterprise portals is applying marketing-page patterns (fluid `clamp(2rem, 5vw, 4rem)` headings, huge padding, centered cards, entrance animations) to workspaces where engineers spend 6+ hours daily.

### 2.1 Typography & Numeric Alignment
- **Single Sans-Serif Workhorse:** Use **Inter** (or **Segoe UI** on native Windows office surfaces) with a fixed `rem` scale (`12px` caption, `13px-14px` table/control body, `16px` section title, `20px-24px` page header). Never use fluid `clamp(min, val, max)` inside operator workspaces.
- **Mandatory Tabular Numerals:** Apply `font-variant-numeric: tabular-nums` to all table columns, KPI counters, dates, clause numbers, timestamps, and currency cells so digits align vertically across rows.
- **Line Width Discipline:** Constrain prose/descriptions to `65-75ch`, while allowing data tables and matrix views to expand to `120ch+` or full container width.

### 2.2 Two-Layer Neutral Surface Architecture
- **Restrained Elevation:** Separate navigation rails, sidebars, and toolbars from the primary work canvas using a **2-layer neutral tint** (e.g., `#F8FAFC` app shell vs. `#FFFFFF` primary table surface in light mode; `#0B1B3D` shell vs. `#0F172A` surface in dark mode) paired with `1px solid` hairline borders (`--border`).
- **No Shadow Soup:** Avoid heavy drop shadows (`box-shadow`) inside dense workspaces; reserve elevation strictly for floating overlays (`<dialog>`, `<div popover>`, command palettes, and dropdown menus).

### 2.3 Seven Mandatory Interactive Control States
Every interactive element (buttons, inputs, table rows, filter chips, tree nodes) MUST explicitly support all 7 states:
1. `default` — Restrained border/surface contrast.
2. `hover` — Subtle surface tint shift (`150ms`).
3. `focus-visible` — High-contrast `2px` keyboard focus ring (`outline-offset: 2px`) that is never clipped.
4. `active` — Immediate pressed feedback.
5. `disabled` — Reduced contrast with `cursor: not-allowed` and `disabled` attribute (never rely on opacity alone if text becomes unreadable).
6. `loading` — Layout-preserving **skeleton placeholders** or inline button spinner that preserves button width (never replace an entire workspace table with a centered spinner).
7. `error` — Semantic error border (`#DA251C`), `aria-invalid="true"`, and actionable inline recovery text.

## 3. Anti-Slop Craft Floor (Hard Bans)

To eliminate generic LLM-generated visual tells ("AI slop"), enforce these negative constraints across all web and portal outputs:

| Banned Pattern (AI Slop Tell) | Mandatory Replacement |
|-------------------------------|-----------------------|
| Tracked-out uppercase eyebrow/kicker labels above every heading | Let headings stand on typographic hierarchy and spacing alone |
| Decorative `01 / 02 / 03` numbering on non-sequential feature cards | Use numbering strictly for ordered multi-step procedures |
| Appending `->` or `→` to every button and link | Reserve directional arrows for pagination or external handoffs |
| Nested cards (`card` inside `card` inside `card`) | Use whitespace, `1px` hairline dividers, or structured table rows |
| Thick colored left borders (`border-left: 4px solid`) on cards/callouts | Use `1px` full semantic borders + subtle tinted background + icon badge |
| Raw gray text (`#6B7280`) placed on colored backgrounds | Tint neutral text slightly toward the background hue and verify WCAG contrast |
| Emoji characters (`🚀`, `✨`, `🔥`) used as UI icons | Use consistent SVG stroke icons (`16px` / `20px` viewBox, uniform `1.5px-2px` stroke) |
| Generic purple/indigo/neon gradients on enterprise portals | Use official brand tokens (`#363883`, `#005A9C`, `#0093DD`, `#DA251C`) |

## 4. Portal Ergonomics, URL State & WCAG 2.2 Compliance

### 4.1 Bidirectional URL State Synchronization
In any portal or dashboard, **the URL is the single source of truth for view state**:
- Synchronize search queries (`?q=`), facet filters (`?discipline=MEP&status=fail`), active tabs (`?tab=clauses`), sort order (`?sort=updated_desc`), pagination (`?page=2`), and open detail drawers (`?inspect=item-42`) with URL query parameters.
- Users must be able to bookmark, copy-paste, or refresh any filtered portal view without losing context.

### 4.2 Data Table Virtualization & Truncation Guards
- **Virtualization:** Any list or table that can exceed `50` rows MUST use row virtualization or `content-visibility: auto` to prevent main-thread DOM lag (keep **INP** `<= 200ms`).
- **Flex/Grid Truncation Guard:** Always add `min-w-0` on flex/grid children containing dynamic text so `text-overflow: ellipsis` works without blowing out the portal layout.

### 4.3 WCAG 2.2 AA/AAA Portal Checklist
- **Focus Not Obscured (`2.4.11`):** Sticky portal headers and bottom action bars MUST define `scroll-margin-top` / `scroll-padding-top` on scroll containers so keyboard **Tab** focus is never hidden behind sticky chrome.
- **Target Size (`2.5.8`):** All buttons, pagination controls, and tree toggles must provide at least `24x24px` hit area (`44x44px` on touch devices).
- **Accessible Authentication (`3.3.8`):** Never block `onPaste` on password, token, or OTP inputs; always set proper `autocomplete` attributes.
- **Multi-Modal Status Encoding (CVD-Safe):** Never use color alone to convey status. Always pair `[Icon] + [Text Badge] + [Color]` (`[PASS]` `#28A745`, `[WARN]` `#F2C811` with dark text `#1A202C`, `[FAIL]` `#DA251C`).
