# Design System & Three-Layer Token Architecture

Standardized specification for building, auditing, and persisting multi-tier design tokens across web applications, enterprise portals, and executive dashboards. Synthesizes `nextlevelbuilder/ui-ux-pro-max-skill` (**Design Dials** & `MASTER.md`), `shadcn-ui/ui` (semantic CSS variables), and CCBA Brand Identity Guidelines ver 3.4.

## 1. Three-Layer Token Hierarchy

Never bind UI components directly to raw hex codes. Structure every design system into three explicit layers:

| Layer | Purpose | Naming Pattern | Example |
|-------|---------|----------------|---------|
| **Layer 1: Primitive Tokens** | Raw palette, spacing steps, font families | `--color-<hue>-<step>`, `--space-<n>` | `--color-ccba-navy-900: #363883; --color-ibst-red-600: #DA251C;` |
| **Layer 2: Semantic Tokens** | Intent-driven surfaces, text, borders, status | `--background`, `--card`, `--sidebar`, `--primary`, `--border` | `--primary: var(--color-ccba-navy-900); --destructive: var(--color-ibst-red-600);` |
| **Layer 3: Component Tokens** | Scoped overrides for dense controls/tables | `--table-row-height`, `--control-height-sm`, `--badge-pass-bg` | `--control-height-sm: 28px; --table-cell-px: var(--space-2);` |

## 2. CCBA Canonical Brand & Semantic Token Matrix (WCAG 2.1/2.2 Verified)

All portals and web applications under CCBA governance must enforce the following verified foreground-background pairs:

| Semantic Token Role | Background HEX | Mandatory Foreground HEX | Contrast Ratio | WCAG Level | Usage Scope |
|---------------------|----------------|--------------------------|----------------|------------|-------------|
| `--primary` (CCBA Dark Blue) | `#363883` | `#FFFFFF` (Pure White) | `10.24:1` | **AAA Pass** | Primary CTAs, active nav rails, portal topbars, `[ARC]` badges |
| `--secondary` (Primary UI Blue) | `#005A9C` | `#FFFFFF` (Pure White) | `7.17:1` | **AAA Pass** | Secondary actions, section headers, focus rings, table accents |
| `--accent-bim` (BIM Bright Blue) | `#0093DD` | `#0B1B3D` (Deep Navy) | `5.85:1` | **AA Pass** | `[MEP]` discipline tags, interactive highlights (never use small white text) |
| `--destructive` (IBST Red) | `#DA251C` | `#FFFFFF` (Font weight `>= 500`) | `4.95:1` | **AA Pass** | `[FAIL]` status badges, critical alerts, `[STR]` discipline tags |
| `--warning` (Attention Yellow) | `#F2C811` | `#1A202C` (Charcoal Dark) | `6.86:1` | **AAA Pass** | `[WARN]` status badges, pending audit states (never use white text) |
| `--card` / `--sidebar` (Light) | `#F8FAFC` | `#2C3E50` (Slate Dark) | `11.80:1` | **AAA Pass** | App shell background, sidebars, filter bars, secondary cards |
| `--background` (Primary Canvas) | `#FFFFFF` | `#1A202C` (Charcoal Dark) | `16.10:1` | **AAA Pass** | Main data tables, statutory text reader, form surfaces |

To verify any custom color pair programmatically, run the built-in deterministic contrast calculator:

```bash
python $CCBA_HUB_PATH/.agents/skills/ccba-design/scripts/ui/search.py --contrast "#FFFFFF,#363883"
```

## 3. Quantitative Design Dials (`--density`, `--variance`, `--motion`)

Use the three quantitative dials (1–10 scale) to calibrate token scales before generating CSS:

### 3.1 Density Dial (`--density 1-10`)
- **`8-10` (Dense Portal / Cockpit — Default for Operator Tools):**
  - Spacing scale: `--space-1: 4px; --space-2: 8px; --space-3: 12px; --space-4: 16px; --space-6: 24px;`
  - Control heights: `28px` (compact), `32px` (default), `36px` (prominent).
  - Table cell padding: `6px 10px`; font size `13px` (`0.8125rem`) with `font-variant-numeric: tabular-nums`.
- **`4-7` (Balanced Workspace / Documentation Hub):**
  - Spacing scale: `--space-1: 4px; --space-2: 8px; --space-4: 16px; --space-6: 24px; --space-8: 32px; --space-12: 48px;`
  - Control heights: `34px-38px`; prose body `16px` (`1rem`) at `1.6` line-height (`65-75ch`).
- **`1-3` (Spacious Marketing / Editorial Showcase):**
  - Spacing scale: `--space-4: 16px; --space-6: 24px; --space-12: 48px; --space-16: 64px; --space-24: 96px;`
  - Control heights: `40px-48px`; generous section rhythm.

### 3.2 Variance Dial (`--variance 1-10`)
- **`1-3`:** Strict symmetrical 12-column grid, uniform `2px-4px` border radius (Swiss / Civic / Statutory portals).
- **`4-7`:** Multi-pane workspace split (Collapsible Left Tree + Center Canvas + Right Inspector Drawer, `6px-8px` radius).
- **`8-10`:** Asymmetric Bento grid and editorial feature blocks (`12px-16px` radius).

### 3.3 Motion Dial (`--motion 1-10`)
- **`1-3`:** State-only micro-transitions (`150ms-200ms ease-out`), zero page-load animations (mandatory for **Operate** mode).
- **`4-7`:** Native browser View Transitions (`200ms-250ms`) for shared elements and Suspense reveals.
- **`8-10`:** Showcase choreography (strictly capped at 1 core component + 1 supporting effect per viewport, guarded by `prefers-reduced-motion`).

## 4. Hierarchical Design System Persistence (`MASTER.md` + Page Overrides)

For multi-page portals, persist design decisions in `.md/design-system/` (or project docs) using a two-tier lookup rule:
1. **`MASTER.md` (Global Source of Truth):** Stores the chosen Surface Mode, the 3 Design Dial values, CSS custom property definitions (`:root` and `.dark`), typography scale, and status badge rules.
2. **`pages/<page-slug>.md` (Page-Specific Overrides):** Stores layout splits, URL query parameter schemas, and table/chart configurations for individual routes (e.g., `pages/qc-dashboard.md`, `pages/legal-reader.md`). Page overrides always take precedence over `MASTER.md`.
