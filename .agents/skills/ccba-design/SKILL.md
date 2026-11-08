---
name: ccba-design
description: Design brand identity, web portals, UI/UX systems, logos, banners, and
  CIP assets. Use for design tokens, portal Operate mode, shadcn/Tailwind, and brand
  deliverables.
user-invocable: true
command: /ccba-design
when_to_use: Invoke for brand systems, web portal UI/UX, design tokens, and visual identity.
category: frontend
gpi:
  s: 4.0
  k: 3.0
  a: 1.0
  p: 1.0
keywords:
- brand
- logo
- CIP
- banners
- identity
- portal
- ui-ux
argument-hint: '[design-type] [context]'
license: MIT
metadata:
  author: CCBA
  version: 2.4.0
bundle: _consulting
tier: kernel
layer: _consulting
disable-model-invocation: true
triggers:
- brand
- logo
- CIP
- banners
- identity
- ccba-design
- logo design
- slide design
- banner design
- cip mockup
- mockup
- design-system
- ui-styling
- portal design
- ui-ux
---

# Design

Unified design skill: brand, tokens, UI, logo, CIP, slides, banners, social photos, icons.

---

## 🏛️ Platform-Aware Architecture Posture (ADR-0061)

Skill này thuộc thế năng **`compose-existing`**, hợp thành từ các Seam AI của nền tảng:
* **Định Tuyến & Sinh Nội Dung:** Mọi tương tác văn bản và sáng tạo thiết kế bắt buộc định tuyến qua Seam `model_routing.v1` (`from ccba_ai import choose_model`) và `ai_chat.v1` (`from ccba_ai import ai`). Tuyệt đối không hardcode API key, không nhúng model slug trực tiếp.
* **Hạ Tầng AI Gateway:** Sử dụng gateway tập trung trên máy chủ Spark (:8090) qua package `ccba-ai`. Khi gateway gặp sự cố, hệ thống dừng lại báo lỗi (Fail-Fast), không tự ý fallback vào các CLI cá nhân không kiểm soát.

---

## When to Use

- Brand identity, voice, assets
- Design system tokens and specs
- UI styling with shadcn/ui + Tailwind
- Web portals, task-routing homepages, SharePoint HTML cockpits ("Tối giản & Hé lộ dần"), and 5-section detail views (`Operate + Read`)
- Logo design and AI generation
- Corporate identity program (CIP) deliverables
- Presentations and pitch decks
- Banner design for social media, ads, web, print
- Social photos for Instagram, Facebook, LinkedIn, Twitter, Pinterest, TikTok

## Sub-skill Routing

| Task | Sub-skill | Details |
|------|-----------|---------|
| Brand identity, voice, assets | Brand & Tokens (built-in) | `references/design-system-tokens.md` |
| Tokens, specs, CSS vars, dials | Design System (built-in) | `references/design-system-tokens.md` |
| shadcn/ui, Tailwind, composition | UI Styling (built-in) | `references/ui-styling-shadcn.md` |
| Web portals, Operate + Read mode, Homepage/Spine/Detail View, Anti-Slop | Portal UX (built-in) | `references/portal-operate-and-antislop.md` |
| Logo creation, AI generation | Logo (built-in) | `references/logo-design.md` |
| CIP mockups, deliverables | CIP (built-in) | `references/cip-design.md` |
| Presentations, pitch decks | Slides (built-in) | `references/slides.md` |
| Banners, covers, headers | Banner (built-in) | `references/banner-sizes-and-styles.md` |
| Social media images/photos | Social Photos (built-in) | `references/social-photos-design.md` |
| SVG icons, icon sets | Icon (built-in) | `references/icon-design.md` |

## UI/UX & Web Portal Design (Built-in)

Deterministic BM25 search over 6 UI/UX datasets (`styles.csv`, `ux-guidelines.csv`, `charts.csv`, `products.csv`, `typography.csv`, `stacks.csv`), quantitative Design Dials (`--density`, `--variance`, `--motion`), WCAG 2.1/2.2 contrast verification, and static UI slop code auditing (`SLOP-01` through `SLOP-08`).

### Portal App Shell, Spine & Detail View Architecture

- **3-Tier Progression of Attention ("Tối giản & Hé lộ dần" — `UX-18` & `STK-07`):** Keep 80% of the initial viewport calm (*"Not an index of everything, but a decision aid"*): Tier 1 Above-the-Fold Zero-Noise Action Pills, Role-Adaptive Lenses & Slide-over Proximity Drawer → Tier 2 Asymmetric Workflow Spine (`minmax(260px, 0.55fr) minmax(0, 1.45fr)`), Bento Pulse & 1-Click Situational Mode Toggle (e.g., Daily vs. Friday L10 90-Minute Mode) → Tier 3 Project Lifecycle Stepper Bar, lazy-rendered Mermaid QA/QC flows, Babylon.js 3D preview & native `<details>` SOP drawers (`UX-19`).
- **280px App Shell Sidebar & Context-Aware Routing (`UX-20`):** Order sidebar groups by operator frequency (`Explore → Topics → What's New → Guides`), align `.sidebar-count-pill` with `tabular-nums`, tuck `>4` secondary guides into `<details class="sidebar-guides-more">`, and route Topic clicks context-awarely (scroll on Map view vs. filter chip in Catalog view).
- **5-Section Detail Modal, Safe Markdown Reader & Dual-Channel Endpoints (`UX-21` & `UX-22`):** Combine 1-click `📄 Copy Brief cho Agent`, interactive `.spine-stepper` (`aria-current="step"` / `🛰️ Satellite`), XSS-safe Markdown rendering (`escapeHtml(rawStr)` + `resolveAndSanitizeHref(rawHref, basePath)` + `slugifyMdHeading(rawHeading)` + `scrollToMdAnchor(anchorId)`), whitelisted `#skill/<slug>` & `#doc/<path>` deep-links, SharePoint `SitePages` Native RBAC Security Trimming + Dual-Mode Offline Fallback, and machine endpoints (`llms.txt`, `llms-full.txt`, `INDEX.md`).

### UI/UX: Generate & Persist Portal Design System (`MASTER.md` + Page Overrides)

```bash
python $CCBA_HUB_PATH/.agents/skills/ccba-design/scripts/ui/search.py "legal portal statutory" --design-system -p "CCBA-Portal" --stack nextjs-shadcn --density 8 --variance 4 --motion 3 --persist .md/design-system
python $CCBA_HUB_PATH/.agents/skills/ccba-design/scripts/ui/search.py "qc audit heatmap" --design-system -p "CCBA-Portal" --page qc-dashboard --density 9 --persist .md/design-system
```

### UI/UX: Search Domains (`product`, `style`, `ux`, `chart`, `typography`, `stack`), Verify Contrast & Audit UI Code

```bash
python $CCBA_HUB_PATH/.agents/skills/ccba-design/scripts/ui/search.py "qc dashboard pccc" --domain product
python $CCBA_HUB_PATH/.agents/skills/ccba-design/scripts/ui/search.py "mira dense hairline" --domain style
python $CCBA_HUB_PATH/.agents/skills/ccba-design/scripts/ui/search.py "wcag focus sticky url" --domain ux
python $CCBA_HUB_PATH/.agents/skills/ccba-design/scripts/ui/search.py "heatmap clash compliance" --domain chart
python $CCBA_HUB_PATH/.agents/skills/ccba-design/scripts/ui/search.py "vietnamese be vietnam pro tabular" --domain typography
python $CCBA_HUB_PATH/.agents/skills/ccba-design/scripts/ui/search.py --stack sharepoint-spfx
python $CCBA_HUB_PATH/.agents/skills/ccba-design/scripts/ui/search.py --stack sharepoint-html-page
python $CCBA_HUB_PATH/.agents/skills/ccba-design/scripts/ui/search.py --contrast "#FFFFFF,#363883"
python $CCBA_HUB_PATH/.agents/skills/ccba-design/scripts/ui/search.py --audit-file path/to/Component.tsx
```

## Logo Design (Built-in)

55+ styles, 30 color palettes, 25 industry guides.

### Logo: Generate Design Brief

```bash
python $CCBA_HUB_PATH/.agents/skills/ccba-design/scripts/logo/search.py "tech startup modern" --design-brief -p "BrandName"
```

### Logo: Search Styles/Colors/Industries

```bash
python $CCBA_HUB_PATH/.agents/skills/ccba-design/scripts/logo/search.py "minimalist clean" --domain style
python $CCBA_HUB_PATH/.agents/skills/ccba-design/scripts/logo/search.py "tech professional" --domain color
python $CCBA_HUB_PATH/.agents/skills/ccba-design/scripts/logo/search.py "healthcare medical" --domain industry
```

### Logo: Generate with AI

*(Lưu ý: Lối sinh tệp PNG hiện dừng Fail-Fast tại adapter để chờ chuẩn hóa Seam Card sinh ảnh trong Đợt 4B. Tiêu chí hoàn thành hiện tại tập trung vào design brief, SVG icons và design tokens; tiêu chí sinh tệp ảnh PNG tự động sẽ kích hoạt khi Seam ảnh Đợt 4B có mặt).*

```bash
python $CCBA_HUB_PATH/.agents/skills/ccba-design/scripts/logo/generate.py --brand "TechFlow" --style minimalist --industry tech
python $CCBA_HUB_PATH/.agents/skills/ccba-design/scripts/logo/generate.py --prompt "coffee shop vintage badge" --style vintage
```

After generation, ask user about HTML preview via `ask_question`. If yes, generate an interactive HTML preview gallery.

## CIP Design (Built-in)

50+ deliverables, 20 styles, 20 industries. Fast and pro generation modes.

### CIP: Generate Brief

```bash
python $CCBA_HUB_PATH/.agents/skills/ccba-design/scripts/cip/search.py "tech startup" --cip-brief -b "BrandName"
```

### CIP: Search Domains

```bash
python $CCBA_HUB_PATH/.agents/skills/ccba-design/scripts/cip/search.py "business card letterhead" --domain deliverable
python $CCBA_HUB_PATH/.agents/skills/ccba-design/scripts/cip/search.py "luxury premium elegant" --domain style
python $CCBA_HUB_PATH/.agents/skills/ccba-design/scripts/cip/search.py "hospitality hotel" --domain industry
python $CCBA_HUB_PATH/.agents/skills/ccba-design/scripts/cip/search.py "office reception" --domain mockup
```

### CIP: Generate Mockups

```bash
# With logo (RECOMMENDED)
python $CCBA_HUB_PATH/.agents/skills/ccba-design/scripts/cip/generate.py --brand "TopGroup" --logo /path/to/logo.png --deliverable "business card" --industry "consulting"

# Full CIP set
python $CCBA_HUB_PATH/.agents/skills/ccba-design/scripts/cip/generate.py --brand "TopGroup" --logo /path/to/logo.png --industry "consulting" --set

# Pro model (4K text)
python $CCBA_HUB_PATH/.agents/skills/ccba-design/scripts/cip/generate.py --brand "TopGroup" --logo logo.png --deliverable "business card" --model pro

# Without logo
python $CCBA_HUB_PATH/.agents/skills/ccba-design/scripts/cip/generate.py --brand "TechFlow" --deliverable "business card" --no-logo-prompt
```

Models: `flash` (default, fast generation), `pro` (high-quality generation)

### CIP: Render HTML Presentation

```bash
python $CCBA_HUB_PATH/.agents/skills/ccba-design/scripts/cip/render-html.py --brand "TopGroup" --industry "consulting" --images /path/to/cip-output
```

**Tip:** If no logo exists, use Logo Design section above first.

## Slides (Built-in)

Strategic HTML presentations with Chart.js, design tokens, copywriting formulas.

Load `references/slides-create.md` for the creation workflow.

### Slides: Knowledge Base

| Topic | File |
|-------|------|
| Creation Guide | `references/slides-create.md` |
| Layout Patterns | `references/slides-layout-patterns.md` |
| HTML Template | `references/slides-html-template.md` |
| Copywriting | `references/slides-copywriting-formulas.md` |
| Strategies | `references/slides-strategies.md` |

## Banner Design (Built-in)

22 art direction styles across social, ads, web, print. Uses `frontend-design`, `ai-artist`, `ai-multimodal`, and browser capture tools.

Load `references/banner-sizes-and-styles.md` for complete sizes and styles reference.

### Banner: Workflow

1. **Gather requirements** via `ask_question` — purpose, platform, content, brand, style, quantity
   **Completion Criterion:** Requirements document populated with specific width, height, style preferences, and copy.
2. **Research** — Browse reference styles, layouts, and visual patterns
   **Completion Criterion:** At least 3 reference styles or design inspirations documented.
3. **Design** — Create HTML/CSS banner layout and generate visual assets
   **Completion Criterion:** Valid HTML/CSS files representing the banner layout generated.
4. **Export** — Screenshot to PNG at exact dimensions via Chrome headless or Playwright
   **Completion Criterion:** High-resolution PNG banner files exported at targeted dimensions with correct naming.
5. **Present** — Show all options side-by-side, iterate on feedback
   **Completion Criterion:** Presentation output containing links to generated banners displayed to the user.

### Banner: Quick Size Reference

| Platform | Type | Size (px) |
|----------|------|-----------|
| Facebook | Cover | 820 x 312 |
| Twitter/X | Header | 1500 x 500 |
| LinkedIn | Personal | 1584 x 396 |
| YouTube | Channel art | 2560 x 1440 |
| Instagram | Story | 1080 x 1920 |
| Instagram | Post | 1080 x 1080 |
| Google Ads | Med Rectangle | 300 x 250 |
| Website | Hero | 1920 x 600-1080 |

### Banner: Top Art Styles

| Style | Best For |
|-------|----------|
| Minimalist | SaaS, tech |
| Bold Typography | Announcements |
| Gradient | Modern brands |
| Photo-Based | Lifestyle, e-com |
| Geometric | Tech, fintech |
| Glassmorphism | SaaS, apps |
| Neon/Cyberpunk | Gaming, events |

### Banner: Design Rules

- Safe zones: critical content in central 70-80%
- One CTA per banner, bottom-right, min 44px height
- Max 2 fonts, min 16px body, ≥32px headline
- Text under 20% for ads (Meta penalizes)
- Print: 300 DPI, CMYK, 3-5mm bleed

## Icon Design (Built-in)

15 styles, 12 categories. SVG text output generation via reasoning model routing.

### Icon: Generate Single Icon

```bash
python $CCBA_HUB_PATH/.agents/skills/ccba-design/scripts/icon/generate.py --prompt "settings gear" --style outlined
python $CCBA_HUB_PATH/.agents/skills/ccba-design/scripts/icon/generate.py --prompt "shopping cart" --style filled --color "#6366F1"
python $CCBA_HUB_PATH/.agents/skills/ccba-design/scripts/icon/generate.py --name "dashboard" --category navigation --style duotone
```

### Icon: Generate Batch Variations

```bash
python $CCBA_HUB_PATH/.agents/skills/ccba-design/scripts/icon/generate.py --prompt "cloud upload" --batch 4 --output-dir ./icons
```

### Icon: Multi-size Export

```bash
python $CCBA_HUB_PATH/.agents/skills/ccba-design/scripts/icon/generate.py --prompt "user profile" --sizes "16,24,32,48" --output-dir ./icons
```

### Icon: Top Styles

| Style | Best For |
|-------|----------|
| outlined | UI interfaces, web apps |
| filled | Mobile apps, nav bars |
| duotone | Marketing, landing pages |
| rounded | Friendly apps, health |
| sharp | Tech, fintech, enterprise |
| flat | Material design, Google-style |
| gradient | Modern brands, SaaS |

**Model:** Định tuyến qua `model_routing.v1` (`ModelArchetype.REASONING`) — text-only output (SVG is XML text). No image generation API needed.

## Social Photos (Built-in)

Multi-platform social image design: HTML/CSS → screenshot export. Uses structured design tokens, clean typography, and headless browser capture tools.

Load `references/social-photos-design.md` for sizes, templates, best practices.

### Social Photos: Workflow

1. **Orchestrate** — Define task checklist and organize design workflow
   **Completion Criterion:** Task checklist initialized with output targets.
2. **Analyze** — Parse prompt: subject, platforms, style, brand context, content elements
   **Completion Criterion:** Clear analysis of output sizes and key visual requirements documented.
3. **Ideate** — 3-5 concepts, present via `ask_question`
   **Completion Criterion:** Concepts presented to user and a final design direction approved.
4. **Design** — Extract brand colors/tokens, structure HTML/CSS layouts per idea × size
   **Completion Criterion:** Design HTML files generated utilizing proper CSS/JS and matching approved concept.
5. **Export** — Chrome headless or Playwright screenshot at exact px (2x deviceScaleFactor)
   **Completion Criterion:** Image files (PNG/JPG) exported at designated device scale factor.
6. **Verify** — Visually inspect exported designs via Chrome DevTools or Playwright; fix layout/styling issues and re-export
   **Completion Criterion:** Browser screenshot validation logs confirm no visual overflow or text layout issues.
7. **Report** — Summary with design decisions and asset paths
   **Completion Criterion:** Report file created summarizing style decisions.
8. **Organize** — Structure output files and reports in dedicated subdirectories
   **Completion Criterion:** Output assets structured neatly in dedicated subdirectories.

### Social Photos: Key Sizes

| Platform | Size (px) | Platform | Size (px) |
|----------|-----------|----------|-----------|
| IG Post | 1080×1080 | FB Post | 1200×630 |
| IG Story | 1080×1920 | X Post | 1200×675 |
| IG Carousel | 1080×1350 | LinkedIn | 1200×627 |
| YT Thumb | 1280×720 | Pinterest | 1000×1500 |

## Workflows

### Complete Brand Package

1. **Logo** → `scripts/logo/generate.py` → Generate logo brief / concept
   - **Completion Criterion:** Đã xác lập design brief và concept định hướng; tiêu chí sinh file PNG tự động sẽ kích hoạt khi Seam ảnh Đợt 4B có mặt (hiện tại dừng Fail-Fast tại adapter).
2. **CIP** → `scripts/cip/generate.py` → Create deliverable specifications
   - **Completion Criterion:** Đã lập danh mục đặc tả CIP deliverables; tiêu chí sinh ảnh mockup PNG sẽ kích hoạt khi Seam ảnh Đợt 4B có mặt (hiện tại dừng Fail-Fast tại adapter).
3. **Presentation** → Load `references/slides-create.md` → Build pitch deck
   - **Completion Criterion:** Presentation pitch deck created adhering to the brand guidelines.

### New Design System

1. **Brand & Brief** (`scripts/ui/search.py --design-system --persist`) → Define product archetype, dials, and persist `MASTER.md`
   - **Completion Criterion:** Core brand foundations and `MASTER.md` brief persisted under `.md/design-system/<project-slug>/`.
2. **Tokens & Contrast** (`references/design-system-tokens.md`, `--contrast`) → Create 3-layer semantic tokens and verify WCAG 2.2 ratios
   - **Completion Criterion:** Semantic design tokens and Vietnamese-safe font pairings configured with verified WCAG AA/AAA contrast ratios.
3. **Implement** (`references/ui-styling-shadcn.md`, `--stack`) → Configure Tailwind, `shadcn/ui` geometry preset, or SharePoint SPFx tokens
   - **Completion Criterion:** Component styling rules and URL-synchronized state implemented in the target stack.
4. **Audit** (`scripts/ui/search.py --audit-file`) → Run static UI Slop and Operate-mode compliance scanner
   - **Completion Criterion:** Zero `SLOP-01` through `SLOP-08` findings reported on generated UI components.

### Information Portal, Homepage & Detail View Design

1. **Archetype & Surface Dials** (`scripts/ui/search.py "<query>" --design-system --persist .md/design-system`) → Classify surface mode (`Operate + Read`), set Dials (`--density 8 --variance 4 --motion 3`), and persist `MASTER.md` + `pages/<page>.md`
   - **Completion Criterion:** Hierarchical design brief persisted under `.md/design-system/<project>/` with verified WCAG 2.2 AA/AAA token pairs (`>= 4.5:1`) and Vietnamese-safe typography (`Be Vietnam Pro` + `JetBrains Mono`).
2. **App Shell & Left Sidebar IA** (`references/portal-operate-and-antislop.md`, `UX-20`) → Implement sticky header (`62px`, `flex-wrap: nowrap`), `280px` left sidebar ordered by operator frequency (`Explore → Topics → What's New → Guides`), `.sidebar-count-pill` (`tabular-nums`), `>4` `<details class="sidebar-guides-more">` drawer, and context-aware Topic routing
   - **Completion Criterion:** App shell sidebar renders without horizontal overflow or premature Vietnamese label truncation and synchronizes active states across views.
3. **Task-Routing Homepage & Progressive Disclosure** (`UX-18`, `UX-19`, `STK-07`) → Build `< 650px` above-the-fold hero (`100%` width alignment), odd-card full-row grid span (`.jump-card:last-child:nth-child(odd) { grid-column: 1 / -1; }`), 3-Tier "Tối giản & Hé lộ dần" layout (Zero-Noise Action Pills + Proximity Drawer → Asymmetric `0.55fr:1.45fr` Workflow Spine / 1-Click L10 Mode Toggle → Lifecycle Stepper / `<details>` SOP drawers), and contextual button wrapping (`nowrap` on short inline buttons vs. `overflow-wrap: anywhere` on long command CTAs)
   - **Completion Criterion:** First task section header starts `< 650px` on desktop and `scrollWidth <= clientWidth` holds at `1440px`, `1024px`, `768px`, and `375px`.
4. **5-Section Detail Modal & Interactive Spine Stepper** (`UX-21`) → Implement 5-section inspector modal (Action Header + `📄 Copy Brief cho Agent`, interactive `.spine-stepper` with `aria-current="step"` and `🛰️ Satellite` badge, Defining Constraints & Triggers, Pipeline Trail & Seam Contract, Hard Completion Lock) with keyboard focus trap and `overscroll-behavior: contain`
   - **Completion Criterion:** Detail modal supports 1-click Agent Brief copy, lateral spine stepper navigation, `Escape` close, and `Tab` focus trapping.
5. **Safe Markdown Reader, Deep-Links & Dual-Channel Endpoints** (`UX-22`) → Implement `escapeHtml(rawStr)`, `resolveAndSanitizeHref(rawHref, basePath)`, `renderMdTable(rows, basePath)`, blockquote callout badges, `slugifyMdHeading(rawHeading)` + `scrollToMdAnchor(anchorId)`, whitelisted `#skill/<slug>` & `#doc/<path>` hash routing, offline/SharePoint RBAC fallback, and `llms.txt` / `llms-full.txt` / `INDEX.md` parity
   - **Completion Criterion:** Zero XSS protocol/path traversal vectors, deterministic heading anchor scrolling, and 100% parity across human HTML and machine endpoints.
6. **Deterministic Slop Audit & Verification Gate** (`scripts/ui/search.py --audit-file`) → Run static UI Slop scanner (`SLOP-01`..`SLOP-08`) and governance integrity tests
   - **Completion Criterion:** Zero `SLOP-01` through `SLOP-08` findings and all verification gates (`validate_skills.py --enforce-gpi`, `verify-patch`) exit with code `0`.

## References

| Topic | File |
|-------|------|
| Design Routing | `references/design-routing.md` |
| Logo Design Guide | `references/logo-design.md` |
| Logo Styles | `references/logo-style-guide.md` |
| Logo Colors | `references/logo-color-psychology.md` |
| Logo Prompts | `references/logo-prompt-engineering.md` |
| CIP Design Guide | `references/cip-design.md` |
| CIP Deliverables | `references/cip-deliverable-guide.md` |
| CIP Styles | `references/cip-style-guide.md` |
| CIP Prompts | `references/cip-prompt-engineering.md` |
| Slides Create | `references/slides-create.md` |
| Slides Layouts | `references/slides-layout-patterns.md` |
| Slides Template | `references/slides-html-template.md` |
| Slides Copy | `references/slides-copywriting-formulas.md` |
| Slides Strategy | `references/slides-strategies.md` |
| Banner Sizes & Styles | `references/banner-sizes-and-styles.md` |
| Social Photos Guide | `references/social-photos-design.md` |
| Icon Design Guide | `references/icon-design.md` |
| Portal Operate & Anti-Slop | `references/portal-operate-and-antislop.md` |
| Design System & Tokens | `references/design-system-tokens.md` |
| UI Styling & shadcn | `references/ui-styling-shadcn.md` |

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/bm25_engine.py` | Shared deterministic BM25 search engine across UI/UX, Logo, and CIP domains |
| `scripts/ui/search.py` | Search UI/UX styles, guidelines, charts, products, typography, stacks, dials, and WCAG contrast |
| `scripts/ui/core.py` | UI/UX domain search, Design Dials, WCAG 2.2 contrast calculator, and UI slop auditor |
| `scripts/logo/search.py` | Search logo styles, colors, industries |
| `scripts/logo/generate.py` | Generate logos with AI |
| `scripts/logo/core.py` | BM25 search engine for logo data |
| `scripts/cip/search.py` | Search CIP deliverables, styles, industries |
| `scripts/cip/generate.py` | Generate CIP mockups with AI |
| `scripts/cip/render-html.py` | Render HTML presentation from CIP mockups |
| `scripts/cip/core.py` | BM25 search engine for CIP data |
| `scripts/icon/generate.py` | Generate SVG icons with AI |

## Setup

Tất cả các script trong skill sử dụng trực tiếp SDK nền tảng CCBA:
```bash
pip install -e packages/ccba-ai
```
Định tuyến mô hình bắt buộc thông qua Seam `ccba_ai.routing.choose_model()`.

## Tích hợp hệ thống & Vị trí trong Luồng công việc (Workflow Position)

- **Thường chạy sau:** `/ccba-domain-modeling`, `/ccba-to-spec`, hoặc `/ccba-grilling` (**Nhánh C: Visual Prototype Grilling** — khi đã hội tụ phương án giao diện qua 3–5 prototype HTML có floating picker).
- **Thường chạy trước:** `/ccba-implement`, `/ccba-sharepoint-iac` (nếu triển khai cổng thông tin trên SharePoint Online / IDOP), `/ccba-seminar-builder`, và `/ccba-web-testing` (hậu kiểm Playwright E2E, Visual Regression, `axe-core` A11y và Lighthouse Core Web Vitals).

## Progressive Disclosure & Reference Index (Level 3)

Khi thực thi các tác vụ thiết kế chuyên sâu, Agent sử dụng công cụ `view_file` để nạp hướng dẫn chi tiết theo nhu cầu:

| Tệp Tham Chiếu | Ngữ Cảnh Triệu Hồi & Mục Đích Sử Dụng |
| :--- | :--- |
| `references/portal-operate-and-antislop.md` | Kỷ luật thiết kế Cổng thông tin (Operate Mode), chống AI-Slop, đồng bộ URL state và WCAG 2.2 |
| `references/design-system-tokens.md` | Kiến trúc Design Tokens 3 tầng, 3 núm vặn Design Dials và ma trận tương phản màu CCBA |
| `references/ui-styling-shadcn.md` | Quy chuẩn `shadcn/ui` Geometry Presets (`mira`, `nova`), Tailwind semantic tokens và Compound Components |
| `references/logo-design.md` | Quy trình tạo logo, brief nhận diện và bộ biến thể thương hiệu |
| `references/logo-style-guide.md` | Cẩm nang phong cách thiết kế logo theo từng nhóm ngành nghề |
| `references/logo-color-psychology.md` | Tâm lý học màu sắc và bảng phối màu tương thích theo cảm xúc |
| `references/logo-prompt-engineering.md` | Kỹ thuật prompt AI sinh hình ảnh logo vector và biểu trưng |
| `references/cip-design.md` | Thiết kế bộ nhận diện thương hiệu doanh nghiệp (CIP) toàn diện |
| `references/cip-deliverable-guide.md` | Danh mục 50+ ấn phẩm bàn giao CIP (namecard, phong bì, đồng phục) |
| `references/cip-style-guide.md` | Tiêu chuẩn thẩm mỹ, typography và khoảng cách an toàn cho CIP |
| `references/cip-prompt-engineering.md` | Kỹ thuật prompt sinh phối cảnh mockups thực tế cho ấn phẩm CIP |
| `references/banner-sizes-and-styles.md` | Thông số kích thước chuẩn và 22 phong cách thiết kế banner |
| `references/social-photos-design.md` | Thiết kế hình ảnh mạng xã hội (Facebook, Instagram, LinkedIn, X) |
| `references/icon-design.md` | Thiết kế icon SVG, biểu tượng giao diện và bộ icons đồng nhất |
| `references/slides.md` | Tổng quan quy trình thiết kế slide thuyết trình chuyên nghiệp |
| `references/slides-create.md` | Khởi tạo cấu trúc slide bài trình bày theo mục tiêu truyền thông |
| `references/slides-strategies.md` | Chiến lược cấu trúc câu chuyện và tâm lý khán giả khi trình bày |
| `references/slides-layout-patterns.md` | Bố cục layout slide (so sánh, timeline, card, số liệu nổi bật) |
| `references/slides-copywriting-formulas.md` | Công thức viết lời tựa, tiêu đề và tóm lược thông điệp cốt lõi |
| `references/slides-html-template.md` | Mẫu khung mã nguồn HTML/CSS/JS slide trình diễn tương tác |
| `references/design-routing.md` | Ma trận định tuyến nghiệp vụ thiết kế đa bộ môn và phân loại tài sản |

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

## Chuẩn Mực Vận Hành & Khảo Sát Kiểm Chứng
* **Ranh giới trách nhiệm rõ ràng:** Phân tách rành mạch dữ liệu đầu vào và kết quả đầu ra.
* **Kiểm chứng độc lập:** Đối soát kết quả với các tiêu chuẩn tham chiếu trước khi nghiệm thu.
