====================================================================
  UI/UX & PORTAL DESIGN SYSTEM: CCBA-SKILLS-PORTAL
====================================================================
  Query: static-html-portal enterprise catalog search vietnamese khong dau
  Surface Mode: Operate
  Density Dial: 8/10 -> Dense Portal / Cockpit (--space: 4px/8px/12px/16px/24px, control: 28px-32px, tabular-nums)
  Variance Dial: 4/10 -> Balanced Modular Split / Docked Inspector Panels (radius: 6px-8px)
  Motion Dial: 3/10 -> Restrained State-Only Micro-Transitions (150ms-200ms ease-out, zero page-load choreography)
====================================================================

## 1. PRODUCT & PORTAL ARCHETYPE
- **Product Type:** Enterprise Intranet & Executive KPI Cockpit
- **Surface Mode:** Operate
- **Recommended Style:** Fluent 2 Enterprise + Nova Hairline Workspace
- **Recommended Density:** 7 (Balanced Workspace)
- **Primary Tokens:** Primary #363883 | UI Blue #005A9C | Accent #DA251C | Neutral #F8FAFC
- **Core Layout Pattern:** Left Compact Navigation Rail + Top Command Bar (Cmd+K) + 12-Column Responsive KPI & Action Grid
- **Recommended Charts:** KPI Bullet & Sparkline Row | Milestone Gantt & Critical Path | Sankey Workflow Funnel
- **Anti-Patterns:** Nested cards inside cards | inconsistent chart axis scales | missing actionable empty and error states

- **Product Type:** Legal Intelligence & Statutory Portal
- **Surface Mode:** Operate + Read
- **Recommended Style:** Swiss Minimalist Grid + Mira Dense Portal
- **Recommended Density:** 7 (Compact Index + 70ch Reader)
- **Primary Tokens:** Bg #F8FAFC | Primary #363883 | UI Blue #005A9C | Text #2C3E50
- **Core Layout Pattern:** 3-pane split: Collapsible TOC Tree + 70ch Verbatim Statutory Reader + Provenance/AST Diff Inspector
- **Recommended Charts:** Statutory Dependency Graph | Stacked Compliance Bar
- **Anti-Patterns:** Fluid clamp() body text | unverified summaries without verbatim clause citations | hiding filter state from URL

## 2. RECOMMENDED UI STYLE & GEOMETRY
- **Style Name:** Fluent 2 Enterprise
- **Category:** Enterprise System
- **Surface Mode:** Operate
- **Control Height:** 32px-36px
- **Radius:** 4px-6px
- **Spacing Scale:** 12px-32px (--density 7)
- **Primary Palette:** Primary UI Blue #005A9C + Subtle Neutral Layer
- **Typography:** Segoe UI / Inter Regular-SemiBold
- **RTL Support:** full
- **Best For:** Corporate intranets SharePoint M365 hubs administrative approval workflows
- **Avoid For:** High-variance artistic portfolios

- **Style Name:** Polaris Operations
- **Category:** Enterprise System
- **Surface Mode:** Operate
- **Control Height:** 32px-36px
- **Radius:** 8px
- **Spacing Scale:** 12px-32px (--density 7)
- **Primary Palette:** Slate #2C3E50 + CVD-Safe Status Badges (#28A745 #F2C811 #DA251C)
- **Typography:** Inter + Monospace IDs + tabular-nums
- **RTL Support:** full
- **Best For:** Completion checklists (HSHT) procurement dossiers audit & inspection portals
- **Avoid For:** Immersive 3D showcase experiences

## 3. CRITICAL UX & WCAG 2.2 GUARDRAILS
- **Rule ID:** UX-17
- **Priority:** 3-HIGH
- **Category:** Navigation & URL State
- **Rule Name:** Vietnamese Diacritic-Insensitive Search (Khong Dau)
- **Do:** Normalize both search queries and corpus text via NFD diacritic stripping plus d/D mapping so engineers can filter Vietnamese portals with or without accents
- **Dont:** Use raw lowercase substring matching only which fails when users type unaccented Vietnamese keywords like tham tra pccc or phap ly in Cmd+K

- **Rule ID:** UX-08
- **Priority:** 3-HIGH
- **Category:** Navigation & URL State
- **Rule Name:** Bidirectional URL State Synchronization
- **Do:** Synchronize active filters search queries sort order active tabs pagination and open detail drawers with URL query parameters
- **Dont:** Store portal filters table sort state or active tabs only in ephemeral local component memory

## 5. VIETNAMESE-SAFE TYPOGRAPHY & PAIRING
- **Pairing ID:** TYP-01
- **Pairing Name:** CCBA Enterprise & Legal Standard
- **Heading Font:** Be Vietnam Pro
- **Body Font:** Be Vietnam Pro
- **Monospace Font:** JetBrains Mono
- **Vietnamese Support:** 100% Native Vietnamese Diacritics
- **Tabular Nums:** Yes (tnum OpenType)
- **Best For:** Legal portals (VBPL) engineering dashboards corporate portals HSHT checklists
- **CSS Import / Font Stack:** font-sans: 'Be Vietnam Pro', system-ui, sans-serif; font-mono: 'JetBrains Mono', monospace
- **Typography Rules & Guardrails:** Use 600 SemiBold for headings with tracking -0.015em; 400/500 for dense body text; enforce tabular-nums on all clause numbers and metrics

## 6. STACK IMPLEMENTATION GUARDRAILS
- **Stack ID:** STK-05
- **Stack Name:** static-html-portal
- **Target Environment:** Zero-Build Standalone HTML5 Report & Portal
- **Core Libraries:** HTML5 CSS Custom Properties Tailwind Play CDN (or compiled CSS) Chart.js
- **State & Routing Rules:** Use URL hash (#section-id) and lightweight URLSearchParams JS helper for tab and filter persistence without a backend
- **Styling & Token Rules:** Embed self-contained :root and [data-theme='dark'] CSS variables; configure Chart.js with CVD-safe palette and tabular-nums tooltips
- **Anti-Patterns to Ban:** Ban external unpinned JS CDNs that break offline archive viewing; ban multi-axis cluttered charts without direct data labels

## 7. PHASE 4B SURGICAL REFACTOR TOKEN CONTRACT (IMPLEMENTED)
- **Typography Scale (9 tokens, 0.75rem Vietnamese diacritic floor):** `--ccba-text-2xs: 0.75rem`, `--ccba-text-xs: 0.8125rem`, `--ccba-text-sm: 0.875rem`, `--ccba-text-base: 1rem`, `--ccba-text-md: 1.05rem`, `--ccba-text-lg: 1.2rem`, `--ccba-text-xl: 1.35rem`, `--ccba-text-2xl: 1.55rem`, `--ccba-text-3xl: 2.15rem`.
- **Border Radius Scale (4 tokens):** `--ccba-radius-sm: 4px`, `--ccba-radius-md: 6px`, `--ccba-radius-lg: 8px`, `--ccba-radius-pill: 9999px`.
- **Inline Style Prohibition:** `0` `style="` attributes in `scripts/governance/templates/skills_portal.html` and `docs/index.html` (enforced by `test_phase4_operate_mode_and_ccba_design_compliance`).
- **Scoped Hero Fold Budget:** `#viewMap .hero` compacted so `#goal-init_navigation h2` starts at ~603px (above the fold on 1366x768 and 1440x900 viewports).

## 8. PHASE 4C, PR #677 -> #683 & CCBA-DESIGN V2.4.0 ARCHITECTURAL CONTRACT (IMPLEMENTED)
- **3-Layer Concentric Surface & Progressive Disclosure (`UX-18`, `UX-19`, `STK-07`):** Combines "Tối giản & Hé lộ dần" (Tier 1 Zero-Noise Action Pills / Role-Adaptive Lenses + Slide-over Proximity Drawer -> Tier 2 Asymmetric `minmax(260px, 0.55fr) minmax(0, 1.45fr)` Workflow Spine & 1-Click Situational Mode Toggle -> Tier 3 Lifecycle Stepper, lazy-rendered Mermaid/Babylon.js & `<details>` SOP drawers), `100%` section alignment (`1120px`), odd-card full-row span (`.jump-card:last-child:nth-child(odd) { grid-column: 1 / -1; }`), and contextual button wrapping (`nowrap` on short inline proximity buttons vs. `overflow-wrap: anywhere` on long command/path CTAs).
- **280px App Shell Sidebar & Context-Aware Routing (`UX-20`):** Left sidebar sized to `280px`, ordered by usage frequency (`Explore -> Topics -> What's New -> Guides`), `.sidebar-count-pill` with `tabular-nums`, `>4` `<details class="sidebar-guides-more">` progressive drawer, and context-aware Topic routing (`syncSidebarTopicsActive()`).
- **5-Section Detail View, Safe Markdown Reader & Dual-Channel Endpoints (`UX-21`, `UX-22`, `SLOP-08`):** 5-section modal anatomy with `📄 Copy Brief cho Agent`, interactive `.spine-stepper` (`aria-current="step"` and `🛰️ Satellite` badge), XSS-safe Markdown reader (`escapeHtml`, `resolveAndSanitizeHref`, `renderMdTable`, multi-line blockquotes/alerts, `slugifyMdHeading` + `scrollToMdAnchor`), whitelisted `#skill/<slug>` & `#doc/<path>` deep-linking (`findKnownDocGuide`), SharePoint Native RBAC Security Trimming + Offline/Edit fallback, and `llms.txt` / `llms-full.txt` / `INDEX.md` parity.

====================================================================
