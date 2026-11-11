# Design Routing Guide

When to use each design sub-skill.

## Skill Overview

| Skill | Purpose | Key Files |
|-------|---------|-----------|
| brand | Brand identity, voice, assets | `design-system-tokens.md` + `logo-color-psychology.md` |
| design-system | 3-layer token architecture, Design Dials, WCAG matrix | `design-system-tokens.md` + `../scripts/ui/search.py` |
| ui-styling | Component composition, `shadcn/ui`, Tailwind, portals | `ui-styling-shadcn.md` + `portal-operate-and-antislop.md` |
| portal-operate | Web portal Operate + Read mode, Homepage/Spine/Detail View, SharePoint HTML Cockpit, Anti-Slop, URL state, WCAG 2.2 | `portal-operate-and-antislop.md` + `../scripts/ui/search.py` |
| logo-design | AI logo generation (55 styles, 30 palettes) | SKILL.md + 4 references + 2 scripts |
| cip-design | Corporate Identity Program (50 deliverables) | SKILL.md + 3 references + 3 scripts |
| slides | HTML presentations with Chart.js | SKILL.md + 4 references |
| banner-design | Banners for social, ads, web, print (22 styles) | SKILL.md + 1 reference |
| social-photos | Multi-platform social media photo layouts & headless export | `social-photos-design.md` |
| icon-design | SVG icon generation (15 styles, reasoning archetype) | SKILL.md + 1 reference + 1 script |
| critique-refine | Two-track UX critique (Nielsen 10 Heuristics) & 6 iterative passes (`polish`, `typeset`, `harden`) | `impeccable-critique-and-refinement.md` |
| seo-discoverability | Evidence-led technical SEO, JSON-LD, XML sitemap, AI crawler matrix & `/llms.txt` | `seo-and-agentic-discoverability.md` |
| visual-prompting | Pre-generation brief gate & 3 AI visual prompting modes (Archetype, Remix, Technical Style) | `ai-visual-prompting-modes.md` |

## Routing by Task Type

### Brand Identity Tasks
**→ brand**

- Define brand colors and typography
- Create logo usage guidelines
- Establish brand voice and tone
- Organize and validate assets
- Create messaging frameworks
- Audit brand consistency

### Token System Tasks
**→ design-system**

- Create design tokens JSON
- Generate CSS variables
- Define component specifications
- Map tokens to Tailwind config
- Validate token usage in code
- Document state and variants

### Implementation Tasks
**→ ui-styling**

- Add shadcn/ui components
- Style with Tailwind classes
- Implement dark mode
- Create responsive layouts
- Build accessible components

### Portal, Homepage & Detail View Tasks (→ portal-operate)
**→ portal-operate**

- Design enterprise information portals, skills catalogs, and SharePoint HTML cockpits (`Operate + Read`)
- Structure 3-Tier Progression of Attention ("Tối giản & Hé lộ dần": Zero-Noise Action Pills + Proximity Drawer → Bento Pulse & 1-Click L10 Mode Toggle → Lifecycle Stepper & Lazy Mermaid/3D CDE Drawer)
- Build 280px App Shell sidebars (`Explore → Topics → What's New → Guides`), `< 650px` task-routing homepages, and `0.55fr:1.45fr` asymmetric workflow spines
- Implement 5-Section Detail Modals (`.spine-stepper`, 1-click `Copy Brief cho Agent`) and Safe Markdown Readers (`escapeHtml(rawStr)`, `resolveAndSanitizeHref(rawUrl, basePath)`, `#skill/` & `#doc/` deep-links)
- Audit UI code for AI slop and XSS link anti-patterns (`SLOP-01` through `SLOP-08`)

### Logo Design Tasks
**→ logo-design**

- Create logos with AI image generation
- Search logo styles, color palettes, industry guidelines
- Generate design briefs
- Explore 55+ styles (minimalist, vintage, luxury, geometric, etc.)

### Corporate Identity Program Tasks
**→ cip-design**

- Generate CIP deliverables (business cards, letterheads, signage, vehicles, apparel)
- Create CIP briefs with industry/style analysis
- Generate mockups with/without logo (Fast/Pro image generation)
- Render HTML presentations from CIP mockups

### Presentation Tasks
**→ slides**

- Create strategic HTML presentations
- Data visualization with Chart.js
- Apply copywriting formulas to slide content
- Use layout patterns and design tokens

### Banner Design Tasks
**→ banner-design**

- Design banners for social media (Facebook, Twitter, LinkedIn, YouTube, Instagram)
- Create ad banners (Google Ads, Meta Ads)
- Website hero banners and headers
- Print banners and covers
- 22 art direction styles (minimalist, bold typography, gradient, glassmorphism, etc.)

### Icon Design Tasks
**→ icon-design**

- Generate SVG icons with AI (Reasoning Model Archetype)
- Batch icon variations in multiple styles
- Multi-size export (16px, 24px, 32px, 48px)
- 15 styles: outlined, filled, duotone, rounded, sharp, gradient, etc.
- 12 categories: navigation, action, communication, media, commerce, data

## Routing by Question Type

| Question | Skill |
|----------|-------|
| "What color should this be?" | brand |
| "How do I create a token for X?" | design-system |
| "How do I build a button component?" | ui-styling |
| "How do I design a portal homepage, sidebar, or workflow spine?" | portal-operate |
| "How should a skill/ADR detail modal or Safe Markdown reader be structured?" | portal-operate |
| "How do I build a SharePoint HTML Page cockpit with progressive disclosure?" | portal-operate |
| "How do I audit my HTML/JSX portal for AI slop and WCAG 2.2 compliance?" | portal-operate |
| "Is this on-brand?" | brand |
| "Should I use a CSS variable here?" | design-system |
| "How do I add dark mode?" | ui-styling |
| "Create a logo for my brand" | logo-design |
| "Generate business card mockups" | cip-design |
| "Create a pitch deck" | slides |
| "Design brand identity package" | cip-design |
| "What logo style fits my industry?" | logo-design |
| "Design a Facebook cover" | banner-design |
| "Create ad banners for Google" | banner-design |
| "Make a website hero banner" | banner-design |
| "Generate a settings icon" | icon-design |
| "Create SVG icons for my app" | icon-design |
| "Design an icon set" | icon-design |
| "Critique, polish, typeset, or harden my UI component/page" | critique-refine |
| "Improve technical SEO, JSON-LD, or AI crawler / llms.txt setup" | seo-discoverability |
| "Structure an AI visual prompt or remix multiple visual references" | visual-prompting |

## Multi-Skill Workflows

### New Project Setup

```
1. brand → Define identity
   - Colors, typography, voice

2. design-system → Create tokens
   - Primitive, semantic, component

3. ui-styling → Implement
   - Configure Tailwind, add components
```

### Design System Migration

```
1. brand → Audit existing
   - Extract brand colors, fonts

2. design-system → Formalize tokens
   - Create three-layer architecture

3. ui-styling → Update code
   - Replace hardcoded values
```

### Component Creation

```
1. design-system → Reference specs
   - Button states, sizes, variants

2. ui-styling → Implement
   - Build with shadcn/ui + Tailwind
```

## Skill Dependencies

```
brand
    ↓ (colors, typography)
design-system
    ↓ (tokens, specs)
ui-styling
    ↓ (components)
Application Code
```

## Quick Commands

**Brand:**
Tra cứu đặc tả thương hiệu và kiểm tra asset theo `design-system-tokens.md`.

**Tokens:**
Sinh và kiểm tra design tokens theo tài liệu `design-system-tokens.md`.

**Components:**
```bash
npx shadcn@latest add button card input
```

## When to Use Multiple Skills

Use **all eight** when:
- Complete brand package from scratch (logo → CIP → presentation)

Use **brand + design-system + ui-styling** when:
- Design system setup and implementation

Use **logo-design + cip-design** when:
- Complete brand identity package with deliverable mockups

Use **logo-design + cip-design + slides** when:
- Brand pitch: generate logo, create CIP mockups, build pitch deck

Use **banner-design + brand** when:
- Social media presence: branded banners across all platforms

Use **icon-design + design-system** when:
- Custom icon set matching design tokens and component specs

Use **brand + design-system** when:
- Defining design language without implementation

Use **design-system + ui-styling** when:
- Implementing existing brand in code
- Building component library
