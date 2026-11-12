# M365 3-Tier Native Architecture: SharePoint List Formatting & Adaptive Cards

Comprehensive implementation guide for applying the **3-Tier Progression of Attention ("Tối giản & Hé lộ dần")** natively inside **SharePoint Online Lists/Views/Forms (`pnp/List-Formatting`)** and **Microsoft Teams / Power Automate Adaptive Cards (`microsoft/AdaptiveCards`)** without requiring custom SPFx builds or paid M365 Copilot licenses.

---

## 1. Three-Tier Mapping Across Microsoft 365 Native Surfaces

| Attention Tier | Cognitive Question | SharePoint Lists & Views (`pnp/List-Formatting`) | Teams & Outlook Approvals (`microsoft/AdaptiveCards`) | SharePoint Site Pages (`STK-07` & `pnp-modern-search`) |
| :--- | :--- | :--- | :--- | :--- |
| **Tier 1 — Macro / Ambient** | *"What matters to me right now?"* | **`commandBarProps`** (hide noisy default buttons) + **CVD-Safe Status Pills** (`choice-format.json`, `status-format.json`) with `tabular-nums` counters. | **Compact Summary Card** ($\le 5$ key facts: Document/Contract ID, Owner, Gateway Flag `RequiresIBSTSign`, Primary Approve/Reject buttons). | **Zero-Noise Action Pills** ($\le 3$ counters) + **Role-Adaptive Lens** (`ROLE_ID` / Entra ID Group) above `< 650px` fold. |
| **Tier 2 — Meso / Contextual** | *"What is happening around me?"* | **`customCardProps`** (`openOnEvent: "click"` or `"hover"`) rendering an in-place **Proximity Callout Drawer** over the active row without leaving the list view. | **`Action.ToggleVisibility`** / **`Action.ShowCard`** expanding inline allocation breakdown, SLA timer, or clause diff inside the same Teams message. | **Asymmetric Workflow Spine** (`0.55fr : 1.45fr`) + **1-Click Situational Mode Toggle** (Daily Mode vs. L10 Cockpit Mode). |
| **Tier 3 — Micro / Deep-Dive** | *"What can I explore or trigger?"* | **`customRowAction`** (`action: "executeFlow"` or `"defaultClick"`) + **Form JSON Formatting** (`headerJSON`, collapsible `bodyJSON` sections, `footerJSON`) + canonical OneDrive `driveId/itemId` links. | **Deep-Link Handshake** to canonical SharePoint item / OneDrive folder (`Documents/iOPS/` or `Documents/iCDE/`) + full audit trail in `ApprovalNodes`. | **Lifecycle Stepper**, lazy-rendered **Mermaid.js / Babylon.js** drawers, and PnP Modern Search refiner verticals. |

---

## 2. SharePoint List, View & Form JSON Formatting (`pnp/List-Formatting`)

### 2.1. Tier 1 — Zero-Noise Command Bar (`commandBarProps`) & CVD-Safe Column Pills
Enterprise SharePoint Lists suffer from toolbar clutter (`Automate`, `Integrate`, `Power Apps`, `Export to CSV`, `Alert me`) that confuses operators and exposes accidental mutation paths. Strip the toolbar down to essential actions using `commandBarProps` in View JSON (`list-formatting/views/*.json`):

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/sp/v2/row-formatting.schema.json",
  "commandBarProps": {
    "commands": [
      {
        "key": "new",
        "text": "Tạo hồ sơ mới",
        "iconName": "Add",
        "primary": true
      },
      {
        "key": "editInGridView",
        "hide": true
      },
      {
        "key": "export",
        "position": 2,
        "sectionType": "Overflow"
      },
      {
        "key": "automate",
        "hide": true
      },
      {
        "key": "integrate",
        "hide": true
      },
      {
        "key": "alertMe",
        "hide": true
      }
    ]
  }
}
```

- **Multi-Modal Status Pills (`UX-03`):** Always pair `iconName` + text label + semantic Fluent UI theme classes (`sp-field-severity--good`, `sp-field-severity--warning`, `sp-field-severity--blocked`) in `status-format.json` so color-blind operators never rely on hue alone.

### 2.2. Tier 2 — Native Proximity Drawer via `customCardProps`
Instead of forcing users to open the full SharePoint side form (`dispform.aspx`) or navigate away to inspect metadata, attach `customCardProps` to the primary identifier or status column:

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/sp/v2/column-formatting.schema.json",
  "elmType": "div",
  "style": {
    "display": "flex",
    "alignItems": "center",
    "gap": "8px",
    "cursor": "pointer"
  },
  "customCardProps": {
    "openOnEvent": "click",
    "directionalHint": "rightCenter",
    "isBeakVisible": true,
    "formatter": {
      "elmType": "div",
      "style": {
        "padding": "16px",
        "minWidth": "320px",
        "maxWidth": "420px"
      },
      "children": [
        {
          "elmType": "div",
          "style": {
            "fontWeight": "600",
            "fontSize": "14px",
            "marginBottom": "8px"
          },
          "txtContent": "[$Title]"
        },
        {
          "elmType": "div",
          "style": {
            "fontSize": "12px",
            "marginBottom": "12px"
          },
          "txtContent": "= 'Trạng thái trình Viện: ' + [$IBSTSubmissionStatus]"
        },
        {
          "elmType": "button",
          "txtContent": "Kích hoạt luồng trình duyệt",
          "customRowAction": {
            "action": "executeFlow",
            "actionParams": "{\"id\": \"00000000-0000-0000-0000-000000000000\"}"
          }
        }
      ]
    }
  },
  "children": [
    {
      "elmType": "span",
      "txtContent": "@currentField"
    }
  ]
}
```

### 2.3. Tier 3 — Form Layout Sections (`headerJSON`, `bodyJSON`, `footerJSON`)
When an operator opens an item for editing, group fields into progressive logical sections (`Thông tin Định danh`, `Phân bổ & Hạn mức`, `Cổng Phê duyệt Phòng Tổng hợp`) using SharePoint Form JSON configuration rather than exposing a flat 30-field vertical list.

---

## 3. Adaptive Cards 3-Tier Progressive Disclosure (`microsoft/AdaptiveCards`)

When Power Automate posts approval or alert cards into Microsoft Teams (`Team IDOP`) or Outlook Actionable Messages:
1. **Tier 1 (Always Visible):** Title, natural key (`ContractCode` / `SubmissionCode`), requester, gateway indicator (`RequiresIBSTSign`), and primary `Action.Submit` / `Action.Execute` buttons.
2. **Tier 2 (On-Demand Toggle):** Wrap secondary metadata tables (`FactSet` of WBS scopes, target cost allocations, or prior `ApprovalNodes` comments) inside a `Container` with `"id": "detailsContainer", "isVisible": false`, controlled by an `Action.ToggleVisibility` button (`"Xem chi tiết tờ trình & lịch sử duyệt"`).
3. **Tier 3 (Canonical Deep-Link):** Use `Action.OpenUrl` pointing strictly to the canonical SharePoint item URL or Master OneDrive Storage (`driveId` + `itemId`), **never** temporary `:f:/g/` redeem links (`SLOP-09`).

---

## 4. Security & Performance Guardrails on SharePoint Lists

1. **5,000-Item List View Threshold Protection:**
   - Every View JSON (`views/*.json`) filtered or sorted by CAML/OData MUST reference columns with `"Indexed": true` (capped at `MAX_INDEXED_COLUMNS_PER_LIST = 20`).
   - Never apply View Formatting filters on unindexed `MultiChoice`, `Note`, or multi-value `Lookup` columns.
2. **Safe URL Protocol & Canonical Storage Links (`SLOP-08` & `SLOP-09`):**
   - SharePoint List Formatting automatically blocks `javascript:` URLs, and templates or canvases generated by scripts must also ban all `10` sharing markers in `tools.auth.site_preflight.FORBIDDEN_SHARING_MARKERS` (`:f:/g/`, `:b:/g/`, `:u:/g/`, `:x:/g/`, `:w:/g/`, `:v:/g/`, `:p:/g/`, `:o:/g/`, `guestaccess.aspx`, `share=`). Always bind file links to canonical `driveId` + `itemId` or site-relative paths under `Documents/iOPS/` and `Documents/iCDE/`.
3. **Deployment & Verification via CLI (`idop.ps1` & `pnp/cli-microsoft365`):**
   - Validate all JSON formatting files against official schema definitions (`column-formatting.schema.json`, `view-formatting.schema.json`) before deploying through `sp_view_formatter_deployer.py` or `idop.ps1`.

---

## 5. Viva Connections ACEs, SPFx Application Customizers, Purview & PnP Modern Search

### 5.1. Microsoft Viva Connections & Adaptive Card Extensions (`pnp/sp-dev-fx-aces`)
For mobile-first executive and project-manager workflows inside Microsoft Teams (Desktop & Mobile) with `$0` additional licensing cost:
1. **Card View (Tier 1 — "First 5 Seconds" / To Know):**
   - Use `BasicCardView` or `PrimaryTextCardView` to surface at most 1–2 role-scoped metrics (e.g., `IdopWeeklyPulseAce` showing unsubmitted Friday 16:00 ICT `ScorecardData.Value` count or pending `ROLE_HEAD_ADMIN` gateway submissions).
   - Provide an explicit **Zero-Backlog Empty State** (`"All Scorecard metrics & approvals are up to date"`) when `pending_count == 0`.
2. **Quick View (Tier 2/3 — Proximity Slide-Over Modal / To Do):**
   - Clicking the Card View action opens an **Adaptive Card v1.4 JSON Quick View** directly inside Teams/SharePoint without navigating away to a full list page.
   - Include `Input.Number` / `Input.Text` for inline KPI closeout, `Action.ToggleVisibility` for secondary context (`Trend13W`, `FiveWhys`), and `Action.Submit` bound to `AadHttpClient` (Delegated User OBO token — never App-Only certificate on client requests).
3. **Zero-Node Packaging Posture in `IDOP-CCBA-WAY`:**
   - In `tools/deployment/sp_spfx_cockpit_deployer.py` (`build_ace_manifest`), `IdopWeeklyPulseAce` is packaged without a Node SPFx build toolchain as a `WebPart`-shaped component (`componentType: "WebPart"`, `properties.spfxRole = "AdaptiveCardExtension"`, `supportedHosts = ["SharePointWebPart", "TeamsPersonalApp", "TeamsTab"]`). Use native SPFx ACE (`componentType: "AdaptiveCardExtension"`) only when compiling via full SPFx Node toolchain for Viva Connections Dashboard tiles.

### 5.2. SPFx Application Customizers (`pnp/sp-dev-fx-extensions`)
When cross-page navigation or contextual AI assistance is needed across SharePoint Lists and Site Pages:
1. **Top Placeholder (Global Dual-Zone Wayfinding Bar — Target Extension Host):** Render a compact status strip linking Zone 1 (Public Intranet) and Zone 2 (`/sites/idop` Operations Zone) alongside the current L10 weekly cutoff countdown when deployed as a native SPFx Extension.
2. **Right Slide-Over Drawer (`CcbaMindApplicationCustomizer`):** Render **Interactive Decision Cards** (*"Your agent proposes $\to$ You decide"*) over the pre-computed Friday 17:00 ICT derived snapshot. Every proposed mutation (`PROPOSE_IDS_TOP_RANK`, `PROPOSE_SUBMISSION_GATEWAY_CHECK`) MUST carry `requires_human_confirmation: true` and execute under the signed-in user's delegated permissions.
3. **Zero-Node Packaging Posture in `IDOP-CCBA-WAY`:** In `sp_spfx_cockpit_deployer.py` (`build_app_customizer_manifest`), `CcbaMindApplicationCustomizer` is currently packaged as `componentType: "WebPart"` (`properties.spfxRole = "ApplicationCustomizer"`) for unified zero-Node `.sppkg` bundling alongside `IdopL10CockpitWebPart` and `IdopRoleLensWebPart`.

### 5.3. Microsoft Purview Information Protection, PnP Modern Search v4 & Document Sets
1. **Microsoft Purview Retention & Sensitivity Labels:**
   - When a CDE engineering deliverable transitions to `A1 - Published`, apply a Purview Retention Label (`Record` immutability until `RetentionUntil`) to satisfy statutory construction archiving requirements.
   - *Reference Extension Pattern:* When E3/E5 Information Protection licensing is enabled, apply Purview Sensitivity Labels encrypted to Entra ID Security Groups (`CCBA_*`) on confidential Master Storage partitions (`04_HR_Assets`, `02_Contracts`) so downloaded files remain protected off-tenant.
2. **PnP Modern Search v4 (`microsoft-search/pnp-modern-search`) & Search Bookmarks/Acronyms:**
   - Use Microsoft Graph Search Index verticals and taxonomy refiners (`TermSet` facets) for cross-site document discovery without hitting the 5,000-item SharePoint list view threshold.
   - Seed canonical organizational acronyms (`PGV`, `HSHT`, `CDE`, `QCTK`, `QCCTNB`, `L10`, `IDS`) into Microsoft Search Bookmarks & Acronyms for instant Tier 1 resolution in the M365 search bar.
3. **SharePoint Document Sets & Microsoft Forms:**
   - Use **Microsoft Forms** as a zero-noise external intake surface (routing responses into SharePoint via `OpenApiConnectionWebhook`), and **SharePoint Document Sets** to bundle multi-file bidding or completion packages with shared parent metadata (`ProjectCode`, `ContractCode`, `CdeState`).

