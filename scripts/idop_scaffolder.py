#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SharePoint IDOP Deployment Support Toolkit
Provides automated scaffolding for CDE layout, lists configuration, and Power Automate specs.
"""

import argparse
import os
import json
import sys
import re
import subprocess
from typing import Dict, List, Any

# Define List Schemas
LIST_SCHEMAS = {
    "CRM": {
        "listName": "CRM",
        "displayName": "CRM Leads",
        "fields": [
            {"internal_name": "ContactPerson", "display_name": "Contact Person", "type": "Text"},
            {"internal_name": "Email", "display_name": "Email", "type": "Text"},
            {"internal_name": "Phone", "display_name": "Phone", "type": "Text"},
            {"internal_name": "Status", "display_name": "Lead Status", "type": "Choice", "choices": ["Lead", "Contacted", "Proposal", "Contracted", "Lost"]},
            {"internal_name": "EstimatedValue", "display_name": "Estimated Value", "type": "Currency"},
            {"internal_name": "AssignedTo", "display_name": "Assigned To", "type": "User"}
        ]
    },
    "Contracts": {
        "listName": "Contracts",
        "displayName": "Contracts",
        "fields": [
            {"internal_name": "CRMReference", "display_name": "CRM Lead", "type": "Lookup", "lookup_list": "CRM", "lookup_field": "Title"},
            {"internal_name": "ContractType", "display_name": "Contract Type", "type": "Choice", "choices": ["NDA", "Service Agreement", "Procurement", "Employment"]},
            {"internal_name": "Value", "display_name": "Contract Value", "type": "Currency"},
            {"internal_name": "StartDate", "display_name": "Start Date", "type": "DateTime"},
            {"internal_name": "EndDate", "display_name": "End Date", "type": "DateTime"},
            {"internal_name": "Signee", "display_name": "Signee", "type": "User"},
            {"internal_name": "Status", "display_name": "Contract Status", "type": "Choice", "choices": ["Draft", "Under Review", "Active", "Expired", "Terminated"]}
        ]
    },
    "Finance": {
        "listName": "Finance",
        "displayName": "Finance & Transactions",
        "fields": [
            {"internal_name": "ContractReference", "display_name": "Related Contract", "type": "Lookup", "lookup_list": "Contracts", "lookup_field": "Title"},
            {"internal_name": "Amount", "display_name": "Amount", "type": "Currency"},
            {"internal_name": "PaymentDate", "display_name": "Payment Date", "type": "DateTime"},
            {"internal_name": "PaymentType", "display_name": "Payment Type", "type": "Choice", "choices": ["Revenue", "Expense"]},
            {"internal_name": "Category", "display_name": "Category", "type": "Choice", "choices": ["Software License", "Consulting Fee", "Payroll", "Office Expense", "Tax"]},
            {"internal_name": "ApprovedBy", "display_name": "Approved By", "type": "User"}
        ]
    },
    "Approvals": {
        "listName": "Approvals",
        "displayName": "Approval Tasks",
        "fields": [
            {"internal_name": "RelatedContract", "display_name": "Related Contract", "type": "Lookup", "lookup_list": "Contracts", "lookup_field": "Title"},
            {"internal_name": "Approver", "display_name": "Approver", "type": "User"},
            {"internal_name": "Status", "display_name": "Approval Status", "type": "Choice", "choices": ["Pending", "Approved", "Rejected"]},
            {"internal_name": "SubmissionDate", "display_name": "Submission Date", "type": "DateTime"},
            {"internal_name": "Comments", "display_name": "Comments", "type": "Note"}
        ]
    },
    "HRAdmin": {
        "listName": "HRAdmin",
        "displayName": "HR Administration",
        "fields": [
            {"internal_name": "EmployeeUser", "display_name": "Employee User", "type": "User"},
            {"internal_name": "Department", "display_name": "Department", "type": "Choice", "choices": ["Engineering", "Sales", "HR", "Finance", "Legal"]},
            {"internal_name": "JobTitle", "display_name": "Job Title", "type": "Text"},
            {"internal_name": "HireDate", "display_name": "Hire Date", "type": "DateTime"},
            {"internal_name": "Skills", "display_name": "Skills", "type": "MultiChoice", "choices": ["Python", "SharePoint", "PowerAutomate", "Legal", "Finance", "React", "AWS"]},
            {"internal_name": "Salary", "display_name": "Salary", "type": "Currency"}
        ]
    },
    "LegalQA": {
        "listName": "LegalQA",
        "displayName": "Legal QA & Audits",
        "fields": [
            {"internal_name": "ContractRef", "display_name": "Contract Reference", "type": "Lookup", "lookup_list": "Contracts", "lookup_field": "Title"},
            {"internal_name": "AssignedLegalExpert", "display_name": "Assigned Legal Expert", "type": "User"},
            {"internal_name": "Severity", "display_name": "Severity", "type": "Choice", "choices": ["Low", "Medium", "High", "Critical"]},
            {"internal_name": "ResolutionDate", "display_name": "Resolution Date", "type": "DateTime"},
            {"internal_name": "AuditStatus", "display_name": "Audit Status", "type": "Choice", "choices": ["Open", "In Progress", "Resolved"]}
        ]
    },
    "RDProjects": {
        "listName": "RDProjects",
        "displayName": "R&D Projects",
        "fields": [
            {"internal_name": "Manager", "display_name": "Project Manager", "type": "User"},
            {"internal_name": "Budget", "display_name": "Budget", "type": "Currency"},
            {"internal_name": "StartDate", "display_name": "Start Date", "type": "DateTime"},
            {"internal_name": "TargetDate", "display_name": "Target Date", "type": "DateTime"},
            {"internal_name": "Status", "display_name": "Project Status", "type": "Choice", "choices": ["Planned", "In Progress", "On Hold", "Completed"]}
        ]
    }
}

def sanitize_powershell_string(val: str) -> str:
    """Sanitizes and escapes strings to be placed inside a double-quoted PowerShell string.
    
    Rejects inputs containing characters outside the safe whitelist to prevent command injection.
    """
    if not isinstance(val, str):
        raise ValueError("Input must be a string")
    
    # Check against a strict whitelist of safe characters
    # Allowing letters, numbers, spaces, underscores, hyphens, ampersands, and parentheses
    if not re.match(r"^[a-zA-Z0-9_ \-\&\(\)]*$", val):
        raise ValueError(f"Dangerous character detected in input: {val!r}")
    
    # Escape PowerShell special characters within double quotes: $, `, "
    return val.replace("`", "``").replace("$", "`$").replace('"', '`"')

def generate_powershell_script(list_name: str, schema: dict) -> str:
    safe_list_name = sanitize_powershell_string(list_name)
    lines = []
    lines.append(f"""# SharePoint PnP PowerShell Provisioning Script for '{safe_list_name}'
# Generated by SharePoint IDOP Deployment Support Toolkit
# Environment: SharePoint Online

param (
    [Parameter(Mandatory = $true)]
    [string]$SiteUrl
)

# --- Helper Functions ---

function Connect-SharePoint {{
    param (
        [string]$Url
    )
    Write-Host "Connecting to SharePoint Online at $Url..."
    try {{
        Connect-PnPOnline -Url $Url -Interactive -ErrorAction Stop
        Write-Host "Successfully connected to $Url" -ForegroundColor Green
    }} catch {{
        Write-Error "Failed to connect: $_"
        exit 1
    }}
}}

function Ensure-SharePointList {{
    param (
        [string]$Title
    )
    Write-Host "Ensuring list '$Title' exists..."
    $list = Get-PnPList -Identity $Title -ErrorAction SilentlyContinue
    if ($null -eq $list) {{
        $list = New-PnPList -Title $Title -Template GenericList
        Write-Host "Created list '$Title'." -ForegroundColor Green
    }} else {{
        Write-Host "List '$Title' already exists." -ForegroundColor Yellow
    }}
    return $list
}}

function Add-SharePointField {{
    param (
        [string]$ListTitle,
        [string]$DisplayName,
        [string]$InternalName,
        [string]$Type,
        [string[]]$Choices = @(),
        [string]$LookupList = $null,
        [string]$LookupField = "Title"
    )
    Write-Host "Adding field '$DisplayName' ($Type) to list '$ListTitle'..."
    
    # Check if field already exists
    $field = Get-PnPField -List $ListTitle -Identity $InternalName -ErrorAction SilentlyContinue
    if ($null -ne $field) {{
        Write-Host "Field '$InternalName' already exists in '$ListTitle'." -ForegroundColor Yellow
        return
    }}

    $Required = "FALSE"
    # Helper to escape XML characters
    function Escape-XmlString {{
        param ([string]$string)
        if ([string]::IsNullOrEmpty($string)) {{ return "" }}
        return $string.Replace("&", "&amp;").Replace("<", "&lt;").Replace(">", "&gt;").Replace('"', "&quot;").Replace("'", "&apos;")
    }}

    $EscapedDisplayName = Escape-XmlString $DisplayName
    $EscapedInternalName = Escape-XmlString $InternalName
    $EscapedLookupField = Escape-XmlString $LookupField

    switch ($Type) {{
        "Text" {{
            Add-PnPField -List $ListTitle -DisplayName $DisplayName -InternalName $InternalName -Type Text -AddToDefaultView
        }}
        "Note" {{
            Add-PnPField -List $ListTitle -DisplayName $DisplayName -InternalName $InternalName -Type Note -AddToDefaultView
        }}
        "Choice" {{
            $choiceXml = "<Field Type='Choice' DisplayName='$EscapedDisplayName' Name='$EscapedInternalName' StaticName='$EscapedInternalName' Required='$Required'><CHOICES>"
            foreach ($choice in $Choices) {{
                $escapedChoice = Escape-XmlString $choice
                $choiceXml += "<CHOICE>$escapedChoice</CHOICE>"
            }}
            $choiceXml += "</CHOICES></Field>"
            Add-PnPFieldFromXml -List $ListTitle -FieldXml $choiceXml -AddToDefaultView
        }}
        "MultiChoice" {{
            $choiceXml = "<Field Type='MultiChoice' DisplayName='$EscapedDisplayName' Name='$EscapedInternalName' StaticName='$EscapedInternalName' Required='$Required'><CHOICES>"
            foreach ($choice in $Choices) {{
                $escapedChoice = Escape-XmlString $choice
                $choiceXml += "<CHOICE>$escapedChoice</CHOICE>"
            }}
            $choiceXml += "</CHOICES></Field>"
            Add-PnPFieldFromXml -List $ListTitle -FieldXml $choiceXml -AddToDefaultView
        }}
        "User" {{
            Add-PnPField -List $ListTitle -DisplayName $DisplayName -InternalName $InternalName -Type User -AddToDefaultView
        }}
        "Currency" {{
            Add-PnPField -List $ListTitle -DisplayName $DisplayName -InternalName $InternalName -Type Currency -AddToDefaultView
        }}
        "DateTime" {{
            Add-PnPField -List $ListTitle -DisplayName $DisplayName -InternalName $InternalName -Type DateTime -AddToDefaultView
        }}
        "Boolean" {{
            Add-PnPField -List $ListTitle -DisplayName $DisplayName -InternalName $InternalName -Type Boolean -AddToDefaultView
        }}
        "Lookup" {{
            if ($null -ne $LookupList -and $LookupList -ne "") {{
                $targetList = Get-PnPList -Identity $LookupList
                $targetListGuid = $targetList.Id
                $xml = "<Field Type='Lookup' DisplayName='$EscapedDisplayName' Name='$EscapedInternalName' StaticName='$EscapedInternalName' List='{{$targetListGuid}}' ShowField='$EscapedLookupField' Required='$Required' />"
                Add-PnPFieldFromXml -List $ListTitle -FieldXml $xml -AddToDefaultView
            }} else {{
                Write-Error "Lookup field '$DisplayName' is missing lookup list reference."
                throw "LookupList missing"
            }}
        }}
        Default {{
            Write-Error "Unsupported field type '$Type' for field '$DisplayName'."
            throw "Unsupported field type '$Type'"
        }}
    }}
    Write-Host "Successfully added field '$DisplayName'." -ForegroundColor Green
}}

# --- Execution ---

# 1. Connect to Site
Connect-SharePoint -Url $SiteUrl

# 2. Ensure list exists
Ensure-SharePointList -Title "{safe_list_name}"
""")

    fields = schema.get("fields", [])
    for field in fields:
        internal_name_raw = field.get("internal_name")
        if not internal_name_raw:
            raise ValueError(f"Field is missing 'internal_name' in list '{list_name}'")
        
        display_name_raw = field.get("display_name", internal_name_raw)
        ftype_raw = field.get("type", "Text")
        
        internal_name = sanitize_powershell_string(internal_name_raw)
        display_name = sanitize_powershell_string(display_name_raw)
        ftype = sanitize_powershell_string(ftype_raw)
        
        if ftype in ("Choice", "MultiChoice"):
            choices = field.get("choices")
            if choices is None:
                choices = []
            choices_clean = [sanitize_powershell_string(str(c)) for c in choices]
            choices_str = ", ".join([f'"{c}"' for c in choices_clean])
            lines.append(f'Add-SharePointField -ListTitle "{safe_list_name}" -DisplayName "{display_name}" -InternalName "{internal_name}" -Type "{ftype}" -Choices @({choices_str})')
        elif ftype == "Lookup":
            lookup_list_raw = field.get("lookup_list", "")
            lookup_field_raw = field.get("lookup_field", "Title")
            lookup_list = sanitize_powershell_string(lookup_list_raw)
            lookup_field = sanitize_powershell_string(lookup_field_raw)
            lines.append(f'Add-SharePointField -ListTitle "{safe_list_name}" -DisplayName "{display_name}" -InternalName "{internal_name}" -Type "{ftype}" -LookupList "{lookup_list}" -LookupField "{lookup_field}"')
        else:
            lines.append(f'Add-SharePointField -ListTitle "{safe_list_name}" -DisplayName "{display_name}" -InternalName "{internal_name}" -Type "{ftype}"')

    lines.append(f"\nWrite-Host \"Provisioning of list '{safe_list_name}' completed successfully!\" -ForegroundColor Green")
    return "\n".join(lines)

def generate_power_automate_spec() -> str:
    return """# Power Automate 11-Step Workflow Specification
## Project: SharePoint IDOP Deployment Support Toolkit

This document specifies the end-to-end Power Automate workflow that automates the project and document lifecycle across CRM, Contracts, Finance, Approvals, HRAdmin, LegalQA, and RDProjects.

---

### Workflow Overview & Flowchart

```mermaid
graph TD
    Step1[1. Lead Intake: Trigger on CRM Lead] --> Step2[2. Quotation Calculation]
    Step2 --> Step3[3. Approvals Submission]
    Step3 -->|Approved| Step4[4. CDE Provisioning]
    Step3 -->|Rejected| EndLoss[Mark CRM as Lost & Terminate]
    Step4 --> Step5[5. Task Assignment in RDProjects]
    Step5 --> Step6[6. Timesheet Log Reference Creation]
    Step6 --> Step7[7. Expense Tracking Initialization]
    Step7 --> Step8[8. Invoice Generation in Finance]
    Step8 --> Step9[9. Cashflow Update]
    Step9 --> Step10[10. KPI Dashboard Calculation]
    Step10 --> Step11[11. Project Closure & Archiving]
    Step11 --> EndSuccess([Process Complete])
```

---

### Step-by-Step Details

#### Step 1: Lead Intake
- **Trigger**: When a new item is created in the **CRM** list.
- **Actions**:
  - Get item details.
  - Set status variable.
- **Variables**: `LeadID` (String), `LeadStatus` (String).

#### Step 2: Quotation
- **Trigger**: Step 1 completion.
- **Actions**:
  - Retrieve pricing matrices.
  - Calculate `EstimatedValue` based on customer requirements.
  - Update **CRM** list status to "Proposal".
- **Variables**: `QuotationAmount` (Float/Currency).

#### Step 3: Approvals
- **Trigger**: Status changed to "Proposal".
- **Actions**:
  - Create approval request (Start and wait for approval).
  - Assign to designated manager from CRM `AssignedTo` or dynamic mapping.
  - Record approval response in **Approvals** list.
  - If approved, transition status to "Contracted". If rejected, set status to "Lost".
- **Variables**: `ApprovalOutcome` (String), `ApproverEmail` (String).

#### Step 4: CDE Provisioning
- **Trigger**: Approval Outcome equals "Approved".
- **Actions**:
  - Create folder structure in CDE Document Library:
    - `/01_WIP/{LeadName}_{LeadID}`
    - `/02_Shared/{LeadName}_{LeadID}`
    - `/03_Published/{LeadName}_{LeadID}`
  - Initialize permissions.
- **Variables**: `CDEFolderPath` (String).

#### Step 5: Task Assignment
- **Trigger**: Folder creation completion.
- **Actions**:
  - Create a new project record in the **RDProjects** list.
  - Add tasks and assign them to the Project Manager from CRM.
- **Variables**: `ProjectID` (String), `TaskManagerEmail` (String).

#### Step 6: Timesheet
- **Trigger**: Project task generation.
- **Actions**:
  - Register initial timesheet tracking reference block in HR system or dynamic SharePoint log.
- **Variables**: `TimesheetStatus` (String).

#### Step 7: Expense
- **Trigger**: Timesheet registration.
- **Actions**:
  - Log initial setup expenses under **Finance** list.
- **Variables**: `SetupExpenseAmount` (Float/Currency).

#### Step 8: Invoice
- **Trigger**: Expense validation.
- **Actions**:
  - Create first milestone invoice entry in the **Finance** list.
  - Link invoice to the **Contracts** using the Lookup field.
- **Variables**: `InvoiceNumber` (String).

#### Step 9: Cashflow
- **Trigger**: Invoice entry.
- **Actions**:
  - Recalculate cashflow indicators.
  - Update Finance statistics.
- **Variables**: `ProjectedCashflow` (Float/Currency).

#### Step 10: KPI
- **Trigger**: Cashflow update.
- **Actions**:
  - Calculate team performance ratios and delivery schedules in **RDProjects**.
- **Variables**: `KPIScore` (Float).

#### Step 11: Project Closure
- **Trigger**: Project deliverables verified.
- **Actions**:
  - Move/archive WIP files to `/04_Archive/`.
  - Mark CRM status to "Completed" and Contracts status to "Active" (or "Expired").
- **Variables**: `ClosureStatus` (String).
"""

def generate_flow_definition() -> dict:
    return {
        "$schema": "https://schema.management.azure.com/providers/Microsoft.PowerApps/apis/shared_logicflows/schemas/2016-06-01/workflowdefinition.json#",
        "contentVersion": "1.0.0.0",
        "parameters": {
            "$connections": {
                "defaultValue": {},
                "type": "Object"
            }
        },
        "triggers": {
            "When_a_new_lead_is_created_in_CRM": {
                "type": "OpenApiConnection",
                "inputs": {
                    "host": {
                        "apiId": "/providers/Microsoft.PowerApps/apis/shared_sharepointonline",
                        "connectionName": "shared_sharepointonline",
                        "operationId": "GetOnNewItems"
                    },
                    "parameters": {
                        "dataset": "https://tenant.sharepoint.com/sites/site",
                        "table": "CRM"
                    }
                }
            }
        },
        "actions": {
            "Initialize_LeadID": {
                "type": "InitializeVariable",
                "inputs": {
                    "variables": [
                        {
                            "name": "LeadID",
                            "type": "string",
                            "value": "@triggerOutputs()?['body/ID']"
                        }
                    ]
                },
                "runAfter": {}
            },
            "Calculate_Quotation": {
                "type": "Compose",
                "inputs": {
                    "EstimatedValue": "@mul(triggerOutputs()?['body/EstimatedValue'], 1.1)"
                },
                "runAfter": {
                    "Initialize_LeadID": ["Succeeded"]
                }
            },
            "Start_and_wait_for_an_approval": {
                "type": "OpenApiConnectionWebhook",
                "inputs": {
                    "host": {
                        "apiId": "/providers/Microsoft.PowerApps/apis/shared_approvals",
                        "connectionName": "shared_approvals",
                        "operationId": "StartAndWaitForAnApproval"
                    },
                    "parameters": {
                        "approvalType": "Basic",
                        "title": "Approval for CRM Lead @{triggerOutputs()?['body/Title']}"
                    }
                },
                "runAfter": {
                    "Calculate_Quotation": ["Succeeded"]
                }
            },
            "Condition_on_Approval": {
                "type": "If",
                "expression": {
                    "equals": [
                        "@outputs('Start_and_wait_for_an_approval')?['body/outcome']",
                        "Approved"
                    ]
                },
                "actions": {
                    "Create_CDE_Folders": {
                        "type": "OpenApiConnection",
                        "inputs": {
                            "host": {
                                "apiId": "/providers/Microsoft.PowerApps/apis/shared_sharepointonline",
                                "connectionName": "shared_sharepointonline",
                                "operationId": "CreateNewFolder"
                            },
                            "parameters": {
                                "dataset": "https://tenant.sharepoint.com/sites/site",
                                "folderPath": "01_WIP/@{triggerOutputs()?['body/Title']}",
                                "listName": "CDE"
                            }
                        }
                    }
                },
                "runAfter": {
                    "Start_and_wait_for_an_approval": ["Succeeded"]
                }
            }
        },
        "outputs": {}
    }

def scaffold_cde(output_dir: str) -> None:
    print(f"Scaffolding CDE directory layout in: {output_dir}")
    cde_folders = [
        "01_WIP",
        "02_Shared",
        "03_Published",
        "04_Archive",
        "05_Contract Reference"
    ]
    for folder in cde_folders:
        path = os.path.join(output_dir, folder)
        try:
            os.makedirs(path, exist_ok=True)
            print(f"  [Created] {path}")
        except (PermissionError, FileNotFoundError, OSError) as e:
            print(f"Error: Failed to create CDE directory '{path}': {e}", file=sys.stderr)
            sys.exit(1)

def scaffold_lists(output_dir: str) -> None:
    lists_dir = os.path.join(output_dir, "lists")
    try:
        os.makedirs(lists_dir, exist_ok=True)
    except (PermissionError, FileNotFoundError, OSError) as e:
        print(f"Error: Failed to create lists directory '{lists_dir}': {e}", file=sys.stderr)
        sys.exit(1)
    print(f"Generating list schemas and PnP PowerShell scripts in: {lists_dir}")

    for list_key, schema in LIST_SCHEMAS.items():
        # 1. Write JSON Schema
        schema_path = os.path.join(lists_dir, f"{list_key}_schema.json")
        try:
            with open(schema_path, "w", encoding="utf-8") as f:
                json.dump(schema, f, indent=2, ensure_ascii=False)
            print(f"  [Created Schema] {schema_path}")
        except (PermissionError, FileNotFoundError, OSError) as e:
            print(f"Error: Failed to write schema file '{schema_path}': {e}", file=sys.stderr)
            sys.exit(1)

        # 2. Write PnP PowerShell Script
        try:
            ps_script = generate_powershell_script(list_key, schema)
            ps_path = os.path.join(lists_dir, f"{list_key}_provision.ps1")
            with open(ps_path, "w", encoding="utf-8") as f:
                f.write(ps_script)
            print(f"  [Created PnP Script] {ps_path}")
        except ValueError as e:
            print(f"Error: Schema validation failed for list '{list_key}': {e}", file=sys.stderr)
            sys.exit(1)
        except (PermissionError, FileNotFoundError, OSError) as e:
            print(f"Error: Failed to write script file '{ps_path}': {e}", file=sys.stderr)
            sys.exit(1)

def scaffold_workflows(output_dir: str) -> None:
    workflows_dir = os.path.join(output_dir, "workflows")
    try:
        os.makedirs(workflows_dir, exist_ok=True)
    except (PermissionError, FileNotFoundError, OSError) as e:
        print(f"Error: Failed to create workflows directory '{workflows_dir}': {e}", file=sys.stderr)
        sys.exit(1)
    print(f"Generating Power Automate workflows in: {workflows_dir}")

    spec_path = os.path.join(workflows_dir, "PowerAutomate_spec.md")
    try:
        spec_content = generate_power_automate_spec()
        with open(spec_path, "w", encoding="utf-8") as f:
            f.write(spec_content)
        print(f"  [Created Spec] {spec_path}")
    except (PermissionError, FileNotFoundError, OSError) as e:
        print(f"Error: Failed to write workflow spec '{spec_path}': {e}", file=sys.stderr)
        sys.exit(1)

    def_path = os.path.join(workflows_dir, "PowerAutomate_flow_definition.json")
    try:
        def_content = generate_flow_definition()
        with open(def_path, "w", encoding="utf-8") as f:
            json.dump(def_content, f, indent=2, ensure_ascii=False)
        print(f"  [Created Flow Definition] {def_path}")
    except (PermissionError, FileNotFoundError, OSError) as e:
        print(f"Error: Failed to write flow definition '{def_path}': {e}", file=sys.stderr)
        sys.exit(1)

def generate_fallback_skeleton(app_dir: str) -> None:
    os.makedirs(os.path.join(app_dir, "src"), exist_ok=True)
    
    package_json = {
      "name": "ccba-idop-app",
      "private": True,
      "version": "0.1.0",
      "type": "module",
      "scripts": {
        "dev": "vite",
        "build": "tsc && vite build",
        "preview": "vite preview"
      },
      "dependencies": {
        "react": "^18.2.0",
        "react-dom": "^18.2.0"
      },
      "devDependencies": {
        "@types/react": "^18.2.15",
        "@types/react-dom": "^18.2.7",
        "@vitejs/plugin-react": "^4.0.3",
        "typescript": "^5.0.2",
        "vite": "^4.4.5"
      }
    }
    
    tsconfig_json = {
      "compilerOptions": {
        "target": "ES2020",
        "useDefineForClassFields": True,
        "lib": ["DOM", "DOM.Iterable", "ES2020"],
        "module": "ESNext",
        "skipLibCheck": True,
        "moduleResolution": "node",
        "allowImportingTsExtensions": True,
        "resolveJsonModule": True,
        "isolatedModules": True,
        "noEmit": True,
        "jsx": "react-jsx",
        "strict": True,
        "noUnusedLocals": True,
        "noUnusedParameters": True,
        "noImplicitReturns": True
      },
      "include": ["src"]
    }
    
    vite_config = """import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
})
"""

    index_html = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>CCBA IDOP Platform</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
"""

    main_tsx = """import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
"""

    index_css = """:root {
  font-family: Inter, system-ui, Avenir, Helvetica, Arial, sans-serif;
  line-height: 1.5;
  font-weight: 400;

  color-scheme: dark;
  color: rgba(255, 255, 255, 0.87);
  background-color: #0f172a;

  font-synthesis: none;
  text-rendering: optimizeLegibility;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

body {
  margin: 0;
  display: flex;
  place-items: center;
  min-width: 320px;
  min-height: 100vh;
}

#root {
  width: 100%;
  margin: 0 auto;
}
"""

    app_css = """.dashboard-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
  background-color: #0f172a;
  color: #f8fafc;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #1e293b;
  padding-bottom: 1rem;
  margin-bottom: 2rem;
}

.header h1 {
  font-size: 1.8rem;
  font-weight: 700;
  color: #38bdf8;
  margin: 0;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2.5rem;
}

.metric-card {
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}

.metric-card h3 {
  font-size: 0.875rem;
  color: #94a3b8;
  margin-top: 0;
  margin-bottom: 0.5rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.metric-value {
  font-size: 1.8rem;
  font-weight: 700;
  color: #f8fafc;
}

.pipeline-tracker {
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 8px;
  padding: 1.5rem;
  margin-bottom: 2.5rem;
}

.pipeline-tracker h2 {
  font-size: 1.25rem;
  color: #38bdf8;
  margin-top: 0;
  margin-bottom: 1.2rem;
}

.steps-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: relative;
  overflow-x: auto;
  padding: 1rem 0;
}

.step-node {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  min-width: 80px;
  z-index: 1;
}

.step-circle {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #475569;
  color: #f8fafc;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
  border: 2px solid #0f172a;
}

.step-node.completed .step-circle {
  background: #10b981;
}

.step-node.active .step-circle {
  background: #38bdf8;
  box-shadow: 0 0 10px #38bdf8;
}

.step-label {
  font-size: 0.7rem;
  color: #94a3b8;
  max-width: 90px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.step-node.active .step-label {
  color: #38bdf8;
  font-weight: 600;
}

.leads-section {
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 8px;
  padding: 1.5rem;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.2rem;
}

.section-header h2 {
  font-size: 1.25rem;
  color: #38bdf8;
  margin: 0;
}

.btn-primary {
  background: #0284c7;
  color: #fff;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  transition: background 0.2s;
}

.btn-primary:hover {
  background: #0369a1;
}

.btn-secondary {
  background: #475569;
  color: #fff;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  transition: background 0.2s;
  margin-right: 0.5rem;
}

.btn-secondary:hover {
  background: #334155;
}

.leads-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
}

.leads-table th {
  border-bottom: 2px solid #334155;
  padding: 0.75rem;
  color: #94a3b8;
  font-size: 0.875rem;
  font-weight: 600;
}

.leads-table td {
  border-bottom: 1px solid #334155;
  padding: 0.75rem;
  font-size: 0.875rem;
  color: #e2e8f0;
}

.status-badge {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: capitalize;
}

.status-badge.lead { background: rgba(56, 189, 248, 0.2); color: #38bdf8; }
.status-badge.contacted { background: rgba(251, 191, 36, 0.2); color: #fbbf24; }
.status-badge.proposal { background: rgba(167, 139, 250, 0.2); color: #a78bfa; }
.status-badge.contracted { background: rgba(16, 185, 129, 0.2); color: #10b981; }
.status-badge.lost { background: rgba(239, 68, 68, 0.2); color: #ef4444; }

.modal-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.modal-content {
  background: #1e293b;
  border: 1px solid #475569;
  border-radius: 8px;
  padding: 2rem;
  width: 100%;
  max-width: 450px;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.3);
}

.modal-content h3 {
  margin-top: 0;
  margin-bottom: 1.5rem;
  color: #38bdf8;
}

.form-group {
  margin-bottom: 1.25rem;
}

.form-group label {
  display: block;
  font-size: 0.875rem;
  color: #94a3b8;
  margin-bottom: 0.5rem;
}

.form-control {
  width: 100%;
  background: #0f172a;
  border: 1px solid #334155;
  border-radius: 6px;
  padding: 0.5rem;
  color: #fff;
  box-sizing: border-box;
}

.form-control:focus {
  border-color: #38bdf8;
  outline: none;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 1.5rem;
}
"""

    app_tsx = """import React, { useState } from 'react';
import './App.css';

interface Lead {
  id: number;
  contactPerson: string;
  email: string;
  phone: string;
  status: 'lead' | 'contacted' | 'proposal' | 'contracted' | 'lost';
  estimatedValue: number;
  assignedTo: string;
}

const INITIAL_LEADS: Lead[] = [
  { id: 1, contactPerson: 'John Doe', email: 'john@example.com', phone: '+123456789', status: 'lead', estimatedValue: 15000, assignedTo: 'Alice Smith' },
  { id: 2, contactPerson: 'Jane Smith', email: 'jane@example.com', phone: '+987654321', status: 'proposal', estimatedValue: 45000, assignedTo: 'Bob Johnson' },
  { id: 3, contactPerson: 'David Miller', email: 'david@example.com', phone: '+112233445', status: 'contracted', estimatedValue: 75000, assignedTo: 'Charlie Brown' }
];

const PIPELINE_STEPS = [
  'Lead Intake',
  'Quotation',
  'Approvals',
  'CDE Provisioning',
  'Task Assignment',
  'Timesheet Log',
  'Expense Track',
  'Invoice Gen',
  'Cashflow Update',
  'KPI Dashboard',
  'Project Closure'
];

export default function App() {
  const [leads, setLeads] = useState<Lead[]>(INITIAL_LEADS);
  const [activeStep, setActiveStep] = useState<number>(3); // Default: CDE Provisioning (index 3)
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Form State
  const [contactPerson, setContactPerson] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [status, setStatus] = useState<Lead['status']>('lead');
  const [estimatedValue, setEstimatedValue] = useState('');
  const [assignedTo, setAssignedTo] = useState('');

  // Derived metrics
  const totalLeads = leads.length;
  const pipelineValue = leads.reduce((sum, l) => sum + l.estimatedValue, 0);
  const activeApprovals = leads.filter(l => l.status === 'proposal').length;
  const integrationStatus = 'Online';

  const handleCreateLead = (e: React.FormEvent) => {
    e.preventDefault();
    if (!contactPerson || !email) return;

    const newLead: Lead = {
      id: Date.now(),
      contactPerson,
      email,
      phone,
      status,
      estimatedValue: Number(estimatedValue) || 0,
      assignedTo: assignedTo || 'Unassigned'
    };

    setLeads([...leads, newLead]);
    setIsModalOpen(false);

    // Reset Form
    setContactPerson('');
    setEmail('');
    setPhone('');
    setStatus('lead');
    setEstimatedValue('');
    setAssignedTo('');
  };

  return (
    <div className="dashboard-container">
      {/* Header */}
      <header className="header">
        <div>
          <h1>CCBA IDOP Deployment Dashboard</h1>
          <p style={{ color: '#64748b', margin: '4px 0 0 0', fontSize: '0.9rem' }}>
            Premium SharePoint Integrated Deployment Operations Platform (IDOP)
          </p>
        </div>
        <div style={{ color: '#10b981', fontWeight: 600, fontSize: '0.9rem' }}>
          ● System Active
        </div>
      </header>

      {/* Metrics Grid */}
      <div className="metrics-grid">
        <div className="metric-card">
          <h3>CRM Leads</h3>
          <div className="metric-value">{totalLeads}</div>
        </div>
        <div className="metric-card">
          <h3>Pipeline Value</h3>
          <div className="metric-value">${pipelineValue.toLocaleString()}</div>
        </div>
        <div className="metric-card">
          <h3>Active Approvals</h3>
          <div className="metric-value">{activeApprovals}</div>
        </div>
        <div className="metric-card">
          <h3>Integration Status</h3>
          <div className="metric-value" style={{ color: '#10b981' }}>{integrationStatus}</div>
        </div>
      </div>

      {/* 11-Step Pipeline Tracker */}
      <div className="pipeline-tracker">
        <h2>11-Step Power Automate Pipeline Tracker</h2>
        <div className="steps-container">
          {PIPELINE_STEPS.map((step, index) => {
            let className = 'step-node';
            if (index < activeStep) className += ' completed';
            else if (index === activeStep) className += ' active';
            return (
              <div 
                key={step} 
                className={className}
                style={{ cursor: 'pointer' }}
                onClick={() => setActiveStep(index)}
                title={`Click to set active step to ${step}`}
              >
                <div className="step-circle">
                  {index < activeStep ? '✓' : index + 1}
                </div>
                <div className="step-label">{step}</div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Leads Table Section */}
      <div className="leads-section">
        <div className="section-header">
          <h2>Active CRM Leads</h2>
          <button className="btn-primary" onClick={() => setIsModalOpen(true)}>
            + Add New Lead
          </button>
        </div>

        <table className="leads-table">
          <thead>
            <tr>
              <th>Contact Person</th>
              <th>Email</th>
              <th>Phone</th>
              <th>Status</th>
              <th>Estimated Value</th>
              <th>Assigned To</th>
            </tr>
          </thead>
          <tbody>
            {leads.map((lead) => (
              <tr key={lead.id}>
                <td>{lead.contactPerson}</td>
                <td>{lead.email}</td>
                <td>{lead.phone || 'N/A'}</td>
                <td>
                  <span className={`status-badge ${lead.status}`}>{lead.status}</span>
                </td>
                <td>${lead.estimatedValue.toLocaleString()}</td>
                <td>{lead.assignedTo}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Interactive Modal */}
      {isModalOpen && (
        <div className="modal-backdrop">
          <div className="modal-content">
            <h3>Add New CRM Lead</h3>
            <form onSubmit={handleCreateLead}>
              <div className="form-group">
                <label>Contact Person *</label>
                <input 
                  type="text" 
                  className="form-control" 
                  value={contactPerson} 
                  onChange={(e) => setContactPerson(e.target.value)} 
                  required 
                />
              </div>
              <div className="form-group">
                <label>Email *</label>
                <input 
                  type="email" 
                  className="form-control" 
                  value={email} 
                  onChange={(e) => setEmail(e.target.value)} 
                  required 
                />
              </div>
              <div className="form-group">
                <label>Phone</label>
                <input 
                  type="text" 
                  className="form-control" 
                  value={phone} 
                  onChange={(e) => setPhone(e.target.value)} 
                />
              </div>
              <div className="form-group">
                <label>Status</label>
                <select 
                  className="form-control" 
                  value={status} 
                  onChange={(e) => setStatus(e.target.value as Lead['status'])}
                >
                  <option value="lead">Lead</option>
                  <option value="contacted">Contacted</option>
                  <option value="proposal">Proposal</option>
                  <option value="contracted">Contracted</option>
                  <option value="lost">Lost</option>
                </select>
              </div>
              <div className="form-group">
                <label>Estimated Value ($)</label>
                <input 
                  type="number" 
                  className="form-control" 
                  value={estimatedValue} 
                  onChange={(e) => setEstimatedValue(e.target.value)} 
                />
              </div>
              <div className="form-group">
                <label>Assigned To</label>
                <input 
                  type="text" 
                  className="form-control" 
                  value={assignedTo} 
                  onChange={(e) => setAssignedTo(e.target.value)} 
                />
              </div>
              <div className="modal-actions">
                <button type="button" className="btn-secondary" onClick={() => setIsModalOpen(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  Create Lead
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
"""

    with open(os.path.join(app_dir, "package.json"), "w", encoding="utf-8") as f:
        json.dump(package_json, f, indent=2)
    with open(os.path.join(app_dir, "tsconfig.json"), "w", encoding="utf-8") as f:
        json.dump(tsconfig_json, f, indent=2)
    with open(os.path.join(app_dir, "vite.config.ts"), "w", encoding="utf-8") as f:
        f.write(vite_config)
    with open(os.path.join(app_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_html)
    with open(os.path.join(app_dir, "src", "main.tsx"), "w", encoding="utf-8") as f:
        f.write(main_tsx)
    with open(os.path.join(app_dir, "src", "index.css"), "w", encoding="utf-8") as f:
        f.write(index_css)
    with open(os.path.join(app_dir, "src", "App.css"), "w", encoding="utf-8") as f:
        f.write(app_css)
    with open(os.path.join(app_dir, "src", "App.tsx"), "w", encoding="utf-8") as f:
        f.write(app_tsx)
    
    print("Programmatic skeleton generation complete.")

def scaffold_app(app_dir: str) -> None:
    print(f"Scaffolding React app in: {app_dir}")
    degit_success = False
    
    try:
        print("Attempting to clone via degit...")
        cmd = ["npx", "--yes", "degit", "microsoft/PowerAppsCodeApps/templates/starter", app_dir, "--force"]
        if os.name == "nt":
            subprocess.run(cmd, shell=True, timeout=15, check=True, capture_output=True, text=True)
        else:
            subprocess.run(cmd, timeout=15, check=True, capture_output=True, text=True)
        degit_success = True
        print("Successfully cloned template via degit.")
    except Exception as e:
        print(f"degit failed or timed out: {e}")
        print("Falling back to local React + TS + Vite skeleton generation...")
        
    # Always generate or overwrite the skeleton files to ensure the premium CCBA mockup dashboard and all 8 files exist
    generate_fallback_skeleton(app_dir)

def main() -> None:
    parser = argparse.ArgumentParser(
        description="SharePoint IDOP Deployment Support Toolkit - Scaffolder CLI"
    )
    parser.add_argument(
        "action",
        nargs="?",
        choices=["app"],
        help="Optional action to perform (e.g. 'app' to scaffold the Code App)."
    )
    parser.add_argument(
        "--cde", action="store_true", help="Scaffold CDE directory layout."
    )
    parser.add_argument(
        "--lists",
        action="store_true",
        help="Generate 7 list JSON schemas and 7 PnP PowerShell provisioning scripts.",
    )
    parser.add_argument(
        "--workflows",
        action="store_true",
        help="Generate Power Automate markdown spec and mock JSON Flow Definition.",
    )
    parser.add_argument(
        "--all", action="store_true", help="Execute all three generation steps."
    )
    parser.add_argument(
        "--app", action="store_true", help="Scaffold React + TS + Vite app."
    )
    parser.add_argument(
        "--app-dir",
        default="./src/idop-app",
        help="Target output directory for the app (defaults to './src/idop-app')."
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        default="./CDE",
        help="Target output directory path (defaults to './CDE').",
    )

    args = parser.parse_args()

    if not (args.cde or args.lists or args.workflows or args.all or args.action == "app" or args.app):
        parser.print_help()
        sys.exit(0)

    output_dir = os.path.abspath(args.output_dir)

    if args.all or args.cde:
        scaffold_cde(output_dir)

    if args.all or args.lists:
        scaffold_lists(output_dir)

    if args.all or args.workflows:
        scaffold_workflows(output_dir)

    if args.action == "app" or args.app:
        app_dir = os.path.abspath(args.app_dir)
        scaffold_app(app_dir)

    print("\nScaffolding process completed successfully.")

if __name__ == "__main__":
    main()
