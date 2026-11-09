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
   - SharePoint List Formatting automatically blocks `javascript:` URLs, but templates generated by scripts must also ban raw sharing links (`/:f:/g/`, `/:b:/g/`, `/:w:/g/`, `/:x:/g/`). Always bind file links to canonical `driveId` + `itemId` or site-relative paths under `Documents/iOPS/` and `Documents/iCDE/`.
3. **Deployment & Verification via CLI (`idop.ps1` & `pnp/cli-microsoft365`):**
   - Validate all JSON formatting files against official schema definitions (`column-formatting.schema.json`, `view-formatting.schema.json`) before deploying through `sp_view_formatter_deployer.py` or `idop.ps1`.
