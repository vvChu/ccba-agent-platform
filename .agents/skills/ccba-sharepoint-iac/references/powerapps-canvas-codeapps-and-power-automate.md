# Power Apps (Canvas `.pa.yaml` & Code Apps) and Power Automate Architecture for M365 / IDOP

Distilled from `microsoft/power-platform-skills` (`canvas-apps`, `code-apps`, `power-automate`, `pcf`), `microsoft/powerplatform-build-tools`, and CCBA WAY operational invariants. This reference governs how AI Agents design, author, validate, and package **Power Apps** and **Power Automate** solutions atop SharePoint Online and Microsoft 365.

---

## 1. Licensing-Aware Architecture & Workload Routing (Cost & Quota Optimization)

In the CCBA WAY / IDOP operational model, Microsoft 365 licensing is strictly partitioned to maximize reliability without incurring unnecessary per-seat Premium costs:

| Workload Tier | Target Technology | Connector & License Posture | Primary Use Cases in IDOP |
| :--- | :--- | :--- | :--- |
| **Broad Workforce UI (Zero Extra License)** | **SharePoint List/View JSON Formatting** + **SPFx** + **Site Pages Cockpit (`.html`)** + **Standard Canvas Apps** | `O365_BUSINESS_ESSENTIALS` / Standard M365 Licenses (`shared_sharepointonline`, `shared_office365users`, `shared_office365`, `shared_onedriveforbusiness`, `shared_teams`). | Daily project execution, WBS tracking, PGV forms, CDE document metadata, L10 meeting cockpit. |
| **Targeted Executive / Gateway Apps** | **Power Apps Canvas Apps (`.pa.yaml`)** or **Power Apps Code Apps (`@microsoft/power-apps`)** | Scoped to designated seats or standard connectors where applicable. | 4-Tier PGV allocation matrix (`ContractRoles`, `ContractUnitAllocations`, `ContractTargetCosts`), DynamicForms validation before invoking `Power Automate Main`. |
| **Event-Driven Real-Time Workflows** | **Power Automate Cloud Flows (`PA-01..PA-05`)** | Executed under the dedicated **Managed Workflow Service Account** (`POWERAPPS_PER_USER` quota: `40,000` Power Platform Requests / 24h). | Polymorphic multi-stage approvals (`Submissions`, `ApprovalNodes`), `IBST_Gateway_Review` routing, Teams Adaptive Card notifications, AI Gateway webhook bridges. |
| **Heavy Scheduled / Batch ETL & RBAC Sync** | **Python App-Only Certificate Daemons (`msgraph-sdk-python` / SharePoint REST)** | Entra ID App-Only Certificate (`Zero` consumption of the workflow service account's `40,000 PPR/24h` quota). | Nightly EOS scorecard aggregation, Friday L10 closeout, Entra ID RBAC group provisioning, subledger cutover, and historical reconciliation. |

> [!IMPORTANT]
> **Quota Guardrail:** Never route bulk batch loops (e.g., iterating over thousands of SharePoint rows daily) through Power Automate flows owned by the `POWERAPPS_PER_USER` service account. Offload batch scans to Python App-Only Certificate scripts and reserve Power Automate strictly for event-driven triggers.

---

## 2. Power Apps Canvas Apps (`.pa.yaml`) & 3-Tier Progressive Disclosure

When building or editing a Power Apps Canvas App (via `pac canvas unpack/pack`, `.pa.yaml` source files, or `Canvas Authoring MCP` tools `sync_canvas` / `compile_canvas`):

### 2.1. Workspace & `.pa.yaml` Source Hygiene (`microsoft/power-platform-skills/canvas-apps`)
- Keep `.pa.yaml` source files in a dedicated kebab-case directory containing `App.pa.yaml` and screen `.pa.yaml` files; never mix markdown planning notes or build debris inside the unpacked `.pa.yaml` folder.
- Always run `pac canvas pack` or `compile_canvas` to verify zero Power Fx formula compilation errors before committing.

### 2.2. Three-Tier UI Layout in Canvas Apps
1. **Tier 1 — Compact App Header & Declarative Action Bar (`Height <= 64px`):**
   - Display app title, current user role badge (`User().Email` matched against `Employees.SystemRoles`), and at most **3 primary status filters**.
   - **Declarative Validation Over Blocking Loops:** Never create circular error-popup loops on text inputs. Set the submit button's `DisplayMode` declaratively:
     ```powerfx
     If(
         IsBlank(txtContractCode.Text) || IsBlank(cmbCustomer.Selected) || locIsSubmitting,
         DisplayMode.Disabled,
         DisplayMode.Edit
     )
     ```
2. **Tier 2 — Responsive Auto-Layout Containers & Delegation-Safe Galleries:**
   - Use responsive Horizontal and Vertical **Auto-Layout Containers** (`LayoutDirection`, `LayoutAlignItems`, `LayoutJustifyContent`, `FillPortions`) instead of hardcoded absolute `X/Y` coordinates.
   - Split master list (`0.55fr` / `WidthPortion: 6`) and contextual summary (`1.45fr` / `WidthPortion: 14`) on desktop screens (`Parent.Width >= 960`).
3. **Tier 3 — Slide-Over Context Drawer & Flow Invocation:**
   - Implement a slide-over detail/approval drawer using a right-docked overlay container (`Visible: locShowDetailDrawer`) with keyboard/backdrop close (`UpdateContext({locShowDetailDrawer: false})`).
   - Trigger backend workflows cleanly via `PowerAutomateFlowName.Run(...)` wrapped in `UpdateContext({locIsSubmitting: true})` and `Notify(...)` error handling (`IfError(...)`).

### 2.3. Mandatory Power Fx SharePoint Delegation Guardrails
SharePoint Online connectors (`shared_sharepointonline`) enforce strict **Delegation Rules**. Non-delegable formulas silently truncate queries to the first `500` (or `2,000`) rows, corrupting enterprise financial and contract views:

| Power Fx Operation | Delegable on SharePoint? | Mandatory Pattern on Provisioned SharePoint Lists |
| :--- | :---: | :--- |
| `Filter(List, Column = Value)` | ✅ **Yes** (if indexed) | Ensure `Column` has `"Indexed": true` in `datamodel/sharepoint/lists/*.json` ($\le 20$ indexed columns per list). |
| `StartsWith(Column, Text)` | ✅ **Yes** | Use `StartsWith(ContractCode, txtSearch.Text)` for prefix search on indexed Text columns. |
| `Sort(List, Column, SortOrder)` | ✅ **Yes** | Only sort on single-value indexed columns (`Text`, `Number`, `DateTime`). |
| `Search(List, Text, "Column")` | ❌ **NO** | **BANNED** on lists that can exceed 500 rows. Use `StartsWith` or pre-filtered `Filter()` + client-side search on the small resulting subset. |
| `Lower()` / `Upper()` inside `Filter()` | ❌ **NO** | **BANNED** inside `Filter()`. SharePoint `=` and `StartsWith` are already case-insensitive by default. |
| `CountRows(Filter(...))` | ⚠️ **Limited** | Cache summary counts in a dedicated scorecard/summary list or use indexed status columns rather than calling `CountRows` repeatedly across large lists on `App.OnStart`. |

---

## 3. Power Apps Code Apps (`@microsoft/power-apps` — React + TypeScript + Fluent UI v9, Reference Pattern)

> **Scope Posture:** In `IDOP-CCBA-WAY`, active frontline apps and Standard flows ship via Canvas `.pa.yaml` (`powerapps/src/IdopFieldApprovalApp.pa.yaml`) and `PA-01..PA-05` (`tools/deployment/pa_solution_packager.py`). Use **Code Apps** as a reference expansion pattern when a bespoke React/TypeScript SPA hosted inside Power Apps is explicitly required.

When building a custom Code App (distilled from `microsoft/power-platform-skills/plugins/code-apps`):
1. **Scaffold & Tooling:** Initialize with `pac code init` (Vite + React + TypeScript + `@fluentui/react-components`), mapping Fluent v9 tokens (`colorBrandBackground`, `colorNeutralStroke1`) to CCBA brand colors (`#363883`, `#005A9C`, `#DA251C`).
2. **Standard M365 Data Sources:** Register connectors declaratively via `add-sharepoint`, `add-office365`, `add-onedrive`, and `add-teams`, ensuring all queries respect SharePoint Native RBAC Security Trimming.
3. **3-Tier Operate Mode Compliance:** Enforce all `/ccba-design` Operate Mode rules (`tabular-nums`, `< 650px` fold budget, bidirectional URL hash/query state, and zero `SLOP-01..09` findings).

---

## 4. Power Automate Cloud Flows (`OpenApiConnection` & Solution Packaging)

Distilled from `microsoft/power-platform-skills/plugins/power-automate` (`build-flow`, `diagnose-flow`, `route-environments`) and `pa_solution_packager.py`:

1. **Mandatory `OpenApiConnection` Binding (`SLOP-09`):**
   - Every connector action in a Power Automate flow definition (`workflow.json`) MUST use `"type": "OpenApiConnection"` paired with `"connectionName"` referencing a Solution **Connection Reference** (`connectionreferences`).
   - **Strictly Ban:** Legacy `"type": "ApiConnection"`, hardcoded `"Invoker"` bindings, or embedding raw credentials/tokens inside connector action parameters.
2. **Environment Variables for Site & List Binding:**
   - Never hardcode SharePoint Site URLs or List GUIDs directly inside flow actions when packaging for multi-environment deployment. Bind `"dataset"` and `"table"` to Power Platform **Environment Variables** (`environmentvariabledefinitions`).
3. **Infinite Trigger Loop Prevention:**
   - When a flow triggers on `When_an_item_is_created_or_modified` (`Submissions` or `Contracts`) and updates the same item's status (`IBSTSubmissionStatus`), ALWAYS configure a **Trigger Condition** (`@not(equals(triggerOutputs()?['body/Editor/Email'], 'ibstpm@ibst-bim.vn'))` or status-transition guard) to prevent infinite self-triggering loops that exhaust the `40,000 PPR/24h` quota in minutes.
4. **Solution Packaging & Static Verification (`pa_solution_packager.py` & `pac solution`):**
   - Package flows, connection references, environment variables, and Canvas Apps into a structured Solution archive (`Solution.xml`, `customizations.xml`, `Workflows/*.json`) and validate via `pa_solution_packager.py` / `pac solution check` before importing into target environments.
