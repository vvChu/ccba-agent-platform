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

def main() -> None:
    parser = argparse.ArgumentParser(
        description="SharePoint IDOP Deployment Support Toolkit - Scaffolder CLI"
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
        "-o",
        "--output-dir",
        default="./CDE",
        help="Target output directory path (defaults to './CDE').",
    )

    args = parser.parse_args()

    if not (args.cde or args.lists or args.workflows or args.all):
        parser.print_help()
        sys.exit(0)

    output_dir = os.path.abspath(args.output_dir)

    if args.all or args.cde:
        scaffold_cde(output_dir)

    if args.all or args.lists:
        scaffold_lists(output_dir)

    if args.all or args.workflows:
        scaffold_workflows(output_dir)

    print("\nScaffolding process completed successfully.")

if __name__ == "__main__":
    main()
