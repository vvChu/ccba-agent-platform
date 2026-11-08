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

### 2.4 Three-Layer Concentric Surface Architecture & Layout Geometry (`UX-19`)
Enterprise knowledge portals, skills catalogs, and operations cockpits combine **Operate** and **Read** modes across three concentric layers:
1. **Layer 1 — Task-Routing Homepage / Map View (`Operate` — Quick Orientation):**
   - **Above-the-Fold Budget (`< 650px`):** Keep `.hero` padding and vertical margins compact (`24px 0 18px`) so the first task-routing section header (`#goal-init_navigation h2`) starts above `650px` on `1366x768` and `1440x900` screens without scrolling.
   - **Full-Width Section Alignment (`100%`):** Align hero prose, advisor banners, and jump-card grids to `100%` of `--ccba-content-max` (`1120px`) rather than mixing narrower `760px` blocks above `1120px` grids.
   - **Odd-Card Full-Row Span:** When a 2-column task grid has an odd number of cards (e.g., 5 portals), apply `.jump-card:last-child:nth-child(odd) { grid-column: 1 / -1; }` so the final card spans the full row cleanly without leaving a 50% empty hole.
2. **Layer 2 — Asymmetric Workflow Spine (`Operate` — High-Density Scanning):**
   - Use an asymmetric split `grid-template-columns: minmax(260px, 0.55fr) minmax(0, 1.45fr)` (`~27.5%` sticky goal identity, question, primary `"Do this"` CTA, and collapsible SOP drawer on the left; `~72.5%` ordered workflow spine media cards on the right, collapsing to `1fr` below `960px`).
3. **Layer 3 — 5-Section Detail Modal & Safe Markdown Reader (`Read + Operate` — Deep Inspection):**
   - Constrain deep documentation reading and pipeline inspection to a focused `65-75ch` modal/drawer (`max-width: 780px`, `overscroll-behavior: contain`) that preserves parent scroll and filter state.
- **Contextual Button Wrapping Discipline (`UX-19`):**
  - **Short Inline Proximity Buttons** (`📋 Copy`, `Chi tiết`, filter chips, count pills): Enforce `white-space: nowrap` and `flex-shrink: 0` so compact controls never wrap mid-label.
  - **Long Dynamic Command / Path CTA Buttons** (e.g., `🔗 Mở Toàn Văn SKILL.md Gốc (...)`, `.do-this-card` slash commands): Enforce `white-space: normal; overflow-wrap: anywhere; text-align: left;` and stack sibling action rows vertically on mobile (`flex-direction: column; align-items: stretch`) to guarantee `scrollWidth <= clientWidth` down to `375px`.

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
| Unsafe `href="javascript:..."` or unescaped Markdown `innerHTML` (`SLOP-08`) | Use `<button type="button">` for actions and `resolveAndSanitizeHref(rawUrl, basePath)` + `escapeHtml(rawStr)` |

## 4. Portal Ergonomics, URL State & WCAG 2.2 Compliance

### 4.1 Bidirectional URL State Synchronization
In any portal or dashboard, **the URL is the single source of truth for view state**:
- Synchronize search queries (`?q=`), facet filters (`?discipline=MEP&status=fail`), active tabs (`?tab=clauses`), sort order (`?sort=updated_desc`), pagination (`?page=2`), and open detail drawers (`#skill/<slug>` or `#doc/<path>`) with URL query/hash parameters.
- Users must be able to bookmark, copy-paste, or refresh any filtered portal view without losing context.

### 4.2 Data Table Virtualization & Truncation Guards
- **Virtualization:** Any list or table that can exceed `50` rows MUST use row virtualization or `content-visibility: auto` to prevent main-thread DOM lag (keep **INP** `<= 200ms`).
- **Flex/Grid Truncation Guard:** Always add `min-w-0` on flex/grid children containing dynamic text so `text-overflow: ellipsis` works without blowing out the portal layout.

### 4.3 WCAG 2.2 AA/AAA Portal Checklist
- **Focus Not Obscured (`2.4.11`):** Sticky portal headers and bottom action bars MUST define `scroll-margin-top` / `scroll-padding-top` on scroll containers so keyboard **Tab** focus is never hidden behind sticky chrome.
- **Target Size (`2.5.8`):** All buttons, pagination controls, and tree toggles must provide at least `24x24px` hit area (`44x44px` on touch devices).
- **Accessible Authentication (`3.3.8`):** Never block `onPaste` on password, token, or OTP inputs; always set proper `autocomplete` attributes.
- **Multi-Modal Status Encoding (CVD-Safe):** Never use color alone to convey status. Always pair `[Icon] + [Text Badge] + [Color]` (`[PASS]` `#28A745`, `[WARN]` `#F2C811` with dark text `#1A202C`, `[FAIL]` `#DA251C`).

### 4.4 Three-Tier Progression of Attention & SharePoint HTML Pages ("Tối giản & Hé lộ dần" — `UX-18` & `STK-07`)
- **Noxon & IDOP-Cockpit 3-Tier Attention Architecture (`UX-18`):** Enterprise portals must serve as a **decision aid** (*"Not an index of everything, but a decision aid"*), keeping 80% of the initial viewport calm and revealing complexity progressively on user intent (**"Tối giản & Hé lộ dần"**):
  1. **Tier 1 — "What matters to me" (Above-the-Fold Zero-Noise Action Pills & Role-Adaptive Lenses):** Time-of-day + role-aware greeting (**ROLE_ID**) paired with at most **3 Zero-Noise Action Pills** (e.g., **Submissions** pending signature, **Activities** 7-day L10 To-Do, **WorkPackages**) or the single primary command (`Do this with /...`). When a counter is `0`, collapse into a calm green state; clicking a pill slides open a **Proximity Drawer** (*Proximity creates meaning*) with inline summary and 1-touch action buttons without leaving the page. Support **Role-Adaptive Lenses** on the same `Home.html` across executive (`ROLE_DIRECTOR` 2B/5B/10B contract thresholds), admin/accounting (`ROLE_HEAD_ADMIN`, `ROLE_ACCOUNTANT` Gate 1 & receivables), and PM/BIM engineering (`ROLE_PROJECT_MANAGER`, `ROLE_HEAD_BIM_*`) roles.
  2. **Tier 2 — "What is happening around me" (Contextual Workflow Spine, Bento Pulse & 1-Click Mode Toggle):** Ordered step-by-step workflow spine with **Proximity Actions** (`📋 Copy` / `Chi tiết` directly adjacent to each item) or compact daily Bento cards (**Chart.js** / **Fluent UI**). In operations cockpits, provide a **1-Click Situational Mode Toggle** (e.g., **"Chế độ Ngày thường" vs. "Chế độ Họp Thứ Sáu L10 (90-Minute Mode)"**) that expands a 90-minute countdown timer, 10-metric **ScorecardData** (`2026-W43`) charts, and **ProjectIssues** (IDS) table in-place without jumping across `.aspx` pages.
  3. **Tier 3 — "What can I explore" (Lifecycle Stepper, Lazy-Rendered Mermaid & Progressive Drawers):** Replace 48–59 scattered links with a **5-Step Project Lifecycle Bar** (`[1. Đấu thầu] → [2. Giao việc PGV & WBS] → [3. Hồ sơ BIM CDE & QA/QC 5 cấp] → [4. Tạm ứng & Phân bổ 3 tầng] → [5. Nghiệm thu A-B]`) or native `<details class="goal-guides-drawer">` SOP drawers. Selecting `[3. Hồ sơ BIM CDE]` lazy-renders dynamic **Mermaid.js** 5-level QA/QC flowcharts (highlighting bottlenecks such as `ROLE_LEGAL_QA`), embeds lightweight **Babylon.js** 3D WebGL previews in a slide-over drawer, and links to **5TB Master OneDrive Offloading** folders (`iOPS/`, `iCDE/`) via canonical `driveId` + `itemId` URLs (strictly banning `:f:/g/` sharing links).
- **SharePoint `Site Pages` `.html` Sandboxed iFrame, Dual-Zone Isolation & Native RBAC Security Trimming (`STK-07`):**
  - Upload standalone `.html` files directly into SharePoint Online `Site Pages` alongside `.aspx` (**requiring zero M365 Copilot licenses**), enforcing **Dual-Zone isolation** (Zone 1 Public Intranet `ibstbim.sharepoint.com` vs. Zone 2 Operations Engine `/sites/idop`) and embedding **Space Grotesk** (Headlines) + **Inter** / **Be Vietnam Pro** (Body) typography tokens.
  - **Native RBAC Security Trimming:** Execute all Live Data REST/List queries under the authenticated user's SharePoint session across 59 SharePoint Lists, 15 **ROLE_ID**s, and 16 Entra ID Security Groups (`CCBA_*`); never expose sensitive HR/compensation lists (`04_HR_Assets`, `Allocations`) on shared Tier 2 surfaces, and surface gateway indicators (`Submitted_to_IBST`) by role.
  - **Dual-Mode Data Loader:** Fetch live SharePoint Lists when hosted in `Site Pages` (`data-sp-mode="published"`), and fall back automatically to deterministic Preview/Mock JSON with an `.edit-fallback-banner` when opened via local `file://` or inside `Sandboxed iFrame` Edit mode. Restrict external scripts to Microsoft/Cloudflare/jsDelivr managed CDNs compatible with SharePoint CSP.

### 4.5 Left Sidebar Information Architecture & Context-Aware Routing (`UX-20`)
- **280px Persistent App Shell Sidebar:** Size the desktop navigation rail to `width: 280px` (`position: sticky; top: var(--ccba-nav-height); height: calc(100vh - var(--ccba-nav-height))`) so Vietnamese category labels fit on a single line without premature truncation.
- **Usage-Frequency Group Ordering:** Order sidebar navigation groups strictly by daily operator frequency:
  1. `Explore` — Primary workspace views (`Task-Routing Map`, `All Skills Catalog`, `Deep Seams & Contracts`).
  2. `Topics` — Domain portals/categories with active scroll-spy and filter highlighting.
  3. `What's New` — Spotlighted entry-point skills + `🤖 Machine Endpoints` (`llms.txt`).
  4. `Guides` — Deduplicated SOPs, governance rules, and playbooks.
- **Tabular Count Pills & `>4` Progressive Drawer:** Right-align `.sidebar-count-pill` badges with `font-variant-numeric: tabular-nums`. When any secondary sidebar group (such as `Guides`) exceeds `4` items, render the first `4` items directly and tuck the remainder inside a native `<details class="sidebar-guides-more">` progressive disclosure drawer (`+N Xem thêm tài liệu...`).
- **Context-Aware Topic Routing:** Clicking a Topic in the sidebar must respect the active view mode — smooth-scrolling to `#goal-<id>` when in `Map` view, or applying the category chip filter (`?portal=<id>`) in-place when already inside the `Skills Catalog` view.

## 5. Detail View, Inspector Modal & Safe Markdown Reader Architecture (`UX-21`, `UX-22` & Dual-Channel Agent Endpoints)

### 5.1 Five-Section Detail View Anatomy (`UX-21`)
Every skill, ADR, or entity inspector modal MUST follow a standardized 5-section vertical hierarchy with keyboard focus trapping (`Escape` to close, `Tab` / `Shift+Tab` cycle) and `overscroll-behavior: contain`:
1. **Section 1 — Action Header & 1-Click Agent Brief Copy:** Displays the portal/category eyebrow, invocation badge (`User-invoked` / `Model-invoked`), command title, summary, primary action `📋 Copy /<skill>`, **`📄 Copy Brief cho Agent`** (copies a structured Markdown brief containing command, purpose, constraints, and pipeline trail directly to clipboard), and `🔗 Mở Toàn Văn SKILL.md Gốc (GitHub Blob)`.
2. **Section 2 — Interactive Workflow Spine Stepper (`.spine-stepper`):** Horizontal interactive pipeline stepper showing all spine steps of the parent portal (`01 -> 02 -> ...`). Highlights the active skill with `aria-current="step"`, or renders a `🛰️ Satellite` badge when inspecting a specialist satellite skill outside the main spine, enabling 1-click lateral switching between sibling skills without closing the modal.
3. **Section 3 — Defining Constraints & Triggers:** Two-column responsive card grid pairing `Mục Đích & Rào Chắn Bất Biến (Defining Constraints)` (extracted from top headings) with `Khi Nào Sử Dụng & Kích Hoạt (Triggers)` (`when_to_use` + trigger keyword chips).
4. **Section 4 — Value-Chain Pipeline Trail & Seam Contract:** 3-node horizontal pipeline (`Upstream Input -> Current Role -> Downstream Output`) plus conditional `Seam Capability Contract (ADR-0061)` metadata (`seam_id`, `in -> out`, `hardware`, `forbidden_substitute_imports`) when the item is a registered seam.
5. **Section 5 — Hard Completion Lock (ADR-0058) & Live Source Reader:** Displays the deterministic verification gate command (`python scripts/validate_skills.py --file ... --enforce-gpi`) followed by the asynchronous Live Markdown Reader container.

### 5.2 Safe Zero-Dependency Markdown Reader (`UX-22`)
- **HTML Escaping First:** Every line of raw Markdown MUST pass through `escapeHtml(rawStr)` before inline formatting (`<code>`, `<strong>`, `<em>`, `<a>`) is applied. Never pipe unsanitized Markdown into `innerHTML`.
- **Relative Path Rebasing & Protocol Sanitizer (`resolveAndSanitizeHref(rawHref, basePath)`):** Block `javascript:`, `data:`, `vbscript:`, protocol-relative `//`, leading `/`, and backslash `\` URLs (`SLOP-08`). Resolve relative links (`../rules/foo.md`, `./bar.md`) against the current document's `basePath` directory and reject any `..` traversal that attempts to escape the `docs/` root.
- **GFM Pipe Tables & Multi-Line Blockquote Callouts:** Buffer consecutive `| ... |` lines into `renderMdTable(rows, basePath)` wrapped in `<div class="md-table-wrap"><table class="md-table tabular-nums">`. Buffer consecutive `>` lines into unified `<blockquote>` blocks and transform GitHub callout markers (`[!NOTE]`, `[!TIP]`, `[!IMPORTANT]`, `[!WARNING]`, `[!CAUTION]`) into styled `.md-alert-badge` pills.
- **Deterministic Heading Slugs & Scoped Anchor Scrolling:** Generate deterministic heading IDs via `slugifyMdHeading(rawHeading)` (`id="md-anchor-<slug>"`) preserving Unicode/Vietnamese letters (`\p{L}\p{M}\p{N}`). Intercept in-document `#anchor` clicks via `scrollToMdAnchor(anchorId)` (`scrollIntoView` honoring `prefers-reduced-motion: reduce`) so internal TOC links never overwrite the parent SPA URL hash.

### 5.3 Deep-Link Whitelist Routing & Offline Degradation (`UX-22`)
- **Bidirectional Deep-Link Hash Contract:** Synchronize open detail views with `#skill/<slug>` (validated against `const HASH_SLUG_RE = /^[a-z0-9-]+$/` and active `SKILLS[]` entries) and `#doc/<path>` (validated via `findKnownDocGuide(docPath)` against the known `PORTALS[].guides` + `skills/FAQ.md` + `skills/INDEX.md` whitelist). Split query parameters (`?`) before calling `decodeURIComponent(rawHash)` and restore the previous view hash via `history.replaceState` on modal close.
- **Graceful Offline / `file://` Degradation:** When `fetch(docUrl)` fails (e.g., opening `docs/index.html` directly via `file://` without a local HTTP server), render a structured fallback card with a direct link to the canonical GitHub Blob URL (`https://github.com/.../blob/main/docs/<path>`) while keeping the 5-section metadata summary 100% functional from embedded JSON.

### 5.4 Dual-Channel Agent Endpoints (`llms.txt`, `llms-full.txt`, `INDEX.md`)
Every enterprise documentation and skills portal must serve both **Human Operators** (interactive HTML5 App Shell) and **AI Agents** (deterministic plain-text endpoints):
- `docs/llms.txt` — Concise index of portals, slash commands, and canonical doc paths for fast LLM context bootstrapping.
- `docs/llms-full.txt` — Complete consolidated specification across all active skills, pipeline trails, and completion locks for zero-roundtrip RAG ingestion.
- `docs/skills/INDEX.md` — Categorized Markdown master table with GPI scores, triggers, and relative links.

