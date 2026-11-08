# UI Styling, Component Composition & shadcn/Tailwind Architecture

Production implementation patterns for building accessible, maintainable web interfaces and enterprise portals using Tailwind CSS, `shadcn/ui` (Radix UI / Base UI), and modern React composition. Synthesizes `shadcn-ui/ui` (`skills/shadcn`) and `vercel-labs/agent-skills` (`composition-patterns`, `react-best-practices`, `react-view-transitions`).

## 1. Geometry-First Style Presets (`shadcn/ui` Taxonomy)

Select a geometry preset based on the target screen's **Surface Mode** and **Density Dial** before styling components:

| Preset Name | Control Height | Border Radius | Surface Treatment | Ideal Target |
|-------------|----------------|---------------|-------------------|--------------|
| **`mira`** | `28px-32px` | `4px` (`rounded-sm`) | High-density rows, `1px` crisp borders, compact badges | Dense data portals, QC audit tables, BIM property inspectors (`--density 9-10`) |
| **`nova`** | `32px-36px` | `6px` (`rounded-md`) | 2-layer neutral surfaces, hairline dividers over shadows | Multi-panel SaaS workspaces, HSHT trackers, issue boards (`--density 7-8`) |
| **`lyra`** | `28px-32px` | `0px-2px` (`rounded-none`) | Boxy technical framing, monospace telemetry cells | AI Gateway consoles, CLI/eval harness monitors (`--density 8-9`) |
| **`vega`** | `36px-40px` | `6px-8px` (`rounded-md`) | Balanced enterprise spacing, clear form groups | Corporate intranets, administrative portals, standard CRUD apps (`--density 6-7`) |
| **`maia`** | `40px-48px` | `8px-12px` (`rounded-lg`) | Generous whitespace, editorial typography contrast | Service landing pages, executive summaries, pitch portals (`--density 2-4`) |

## 2. Strict Tailwind CSS & Semantic Token Guardrails

Enforce these styling rules to prevent broken dark mode, layout drift, and inconsistent spacing:

| Category | Prohibited Anti-Pattern | Mandatory Pattern |
|----------|-------------------------|-------------------|
| **Colors & Dark Mode** | Hardcoded palette utilities (`bg-slate-900`, `text-white`, `border-gray-200`) or scattered `dark:` overrides | Semantic token utilities (`bg-background`, `bg-card`, `text-foreground`, `text-muted-foreground`, `border-border`) |
| **Flex/Grid Spacing** | Margin utilities `space-x-*` and `space-y-*` (break on wrapping and RTL layouts) | Explicit `flex gap-*` or `grid gap-*` utilities |
| **Equal Dimensions** | Redundant `w-4 h-4` or `w-8 h-8` pairs | Unified `size-4`, `size-8` utilities |
| **Numeric Columns** | Default proportional font digits in tables, counters, and badges | `tabular-nums` utility class on all numeric, date, and ID elements |
| **Flex Truncation** | `truncate` inside a flex item without width constraint (causes container overflow) | Pair `min-w-0 flex-1` on the flex child with `truncate` |

## 3. Component Composition & Anti-Boolean-Prop Discipline

### 3.1 Eliminate Boolean Prop Proliferation
Never create monolithic components configured by 4+ boolean flags (e.g., `<PortalTable isCompact isEditable showToolbar showPagination isReadOnly />`). Boolean flags multiply state combinations exponentially ($2^n$) and create unmaintainable conditionals.

Instead, use **Compound Components** sharing a decoupled 3-part Context contract `{ state, actions, meta }`:

```tsx
// Recommended Compound Component Pattern for Portals
<DataTable.Root state={tableState} actions={tableActions} meta={tableMeta}>
  <DataTable.Toolbar>
    <DataTable.SearchFilter paramKey="q" />
    <DataTable.FacetFilter paramKey="status" options={statusOptions} />
  </DataTable.Toolbar>
  <DataTable.Viewport virtualized={rowCount > 50}>
    <DataTable.Header sticky />
    <DataTable.Body />
  </DataTable.Viewport>
  <DataTable.Pagination paramKey="page" />
</DataTable.Root>
```

### 3.2 Complete Primitive Anatomy (`shadcn/ui` Rules)
- **Cards:** Always use the full semantic structure (`<Card>`, `<CardHeader>`, `<CardTitle>`, `<CardDescription>`, `<CardContent>`, `<CardFooter>`) rather than raw `div` wrappers with ad-hoc padding.
- **Dialogs, Sheets & Drawers:** Every `<DialogContent>`, `<SheetContent>`, or `<DrawerContent>` MUST include an accessible `<DialogTitle>` / `<SheetTitle>` (use `sr-only` only when a visible title is genuinely redundant) and trap focus cleanly.
- **Forms & Validation:** Group controls using `<FieldGroup>`, `<Field>`, `<FieldLabel>`, `<FieldDescription>`, and `<FieldError>`. Bind `aria-invalid={true}` and `data-invalid` on invalid fields, and move focus to the first invalid control on submit.
- **Empty & Skeleton States:** Use dedicated `<Empty>` and `<Skeleton>` primitives matching the exact geometry of the loaded view so **CLS** stays `<= 0.1`.

## 4. Semantic View Transitions & Motion Hierarchy

When applying native browser View Transitions (`document.startViewTransition` or React `<ViewTransition>`):
1. **Shared Element Morphs:** Use unique `view-transition-name` tokens for expanding a table row into a detail inspector drawer.
2. **Suspense & Data Reveals:** Cross-fade skeleton placeholders into loaded data within `150ms-200ms`.
3. **Peer Tab Navigation:** Never use directional left/right slide animations when switching between peer portal tabs; use instant swap or subtle `150ms` opacity cross-fade.
4. **Reduced Motion Guard:** Always wrap non-essential motion in `@media (prefers-reduced-motion: no-preference)`.
