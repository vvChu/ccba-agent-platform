#!/usr/bin/env python3
"""
SharePoint IDOP Deployment Support Toolkit
Provides automated scaffolding for CDE layout, lists configuration, and Power Automate specs.
"""

import argparse
import json
import os
import re
import subprocess
import sys

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
    template_path = os.path.join(os.path.dirname(__file__), "templates", "idop", "PowerAutomate_spec.md")
    with open(template_path, encoding="utf-8") as f:
        return f.read()

def generate_flow_definition() -> dict:
    template_path = os.path.join(os.path.dirname(__file__), "templates", "idop", "PowerAutomate_flow_definition.json")
    with open(template_path, encoding="utf-8") as f:
        return json.load(f)

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
    import shutil
    templates_app_dir = os.path.join(os.path.dirname(__file__), "templates", "idop", "app")
    shutil.copytree(templates_app_dir, app_dir, dirs_exist_ok=True)
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

def pack_solution(output_dir: str, solution_name: str, publisher_name: str, publisher_prefix: str) -> None:
    print(f"\nPacking solution: {solution_name}...")
    import shutil
    import zipfile

    # 1. Check if pac CLI is available
    pac_available = False
    try:
        cmd = ["pac", "--version"]
        if os.name == "nt":
            subprocess.run(cmd, shell=True, check=True, capture_output=True)
        else:
            subprocess.run(cmd, check=True, capture_output=True)
        pac_available = True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Warning: Power Platform CLI (pac) is not installed or not in PATH.")
        print("Falling back to programmatically packaging files into a standard ZIP archive...")

    solution_dir = os.path.join(output_dir, solution_name)
    os.makedirs(solution_dir, exist_ok=True)

    if pac_available:
        try:
            # 2. Run 'pac solution init'
            print("Initializing solution project using 'pac solution init'...")
            cmd_init = [
                "pac", "solution", "init",
                "--publisher-name", publisher_name,
                "--publisher-prefix", publisher_prefix,
                "--outputDirectory", solution_dir
            ]
            if os.name == "nt":
                subprocess.run(cmd_init, shell=True, check=True)
            else:
                subprocess.run(cmd_init, check=True)

            # Copy generated workflows and lists schemas into solution
            workflows_src = os.path.join(output_dir, "workflows")
            if os.path.exists(workflows_src):
                shutil.copytree(workflows_src, os.path.join(solution_dir, "workflows"), dirs_exist_ok=True)

            lists_src = os.path.join(output_dir, "lists")
            if os.path.exists(lists_src):
                shutil.copytree(lists_src, os.path.join(solution_dir, "lists"), dirs_exist_ok=True)

            # 3. Run 'pac solution pack'
            zip_file_path = os.path.join(output_dir, f"{solution_name}.zip")
            print(f"Packing solution using 'pac solution pack' to {zip_file_path}...")
            cmd_pack = [
                "pac", "solution", "pack",
                "--folder", solution_dir,
                "--zipfile", zip_file_path
            ]
            if os.name == "nt":
                subprocess.run(cmd_pack, shell=True, check=True)
            else:
                subprocess.run(cmd_pack, check=True)
            print(f"Solution packed successfully via pac CLI: {zip_file_path}")
            return
        except Exception as e:
            print(f"pac solution commands failed: {e}")
            print("Falling back to Python zipfile packaging...")

    # Fallback/Offline programmatic packaging
    zip_file_path = os.path.join(output_dir, f"{solution_name}.zip")
    print(f"Generating solution ZIP archive programmatically at: {zip_file_path}")

    # Write a simple customizations.xml and solution.xml to mock the Solution structure
    os.makedirs(os.path.join(solution_dir, "Other"), exist_ok=True)

    solution_xml = f"""<?xml version="1.0" encoding="utf-8"?>
<ImportExportXml version="9.2.0.0" SchemaVersion="1.0" Description="" OrganizationVersion="" OrganizationUniqueName="">
  <SolutionManifest>
    <UniqueName>{solution_name}</UniqueName>
    <LocalizedNames>
      <LocalizedName description="{solution_name}" languagecode="1033" />
    </LocalizedNames>
    <Descriptions />
    <Version>1.0.0.0</Version>
    <Managed>0</Managed>
    <Publisher>
      <UniqueName>{publisher_name}</UniqueName>
      <LocalizedNames>
        <LocalizedName description="{publisher_name}" languagecode="1033" />
      </LocalizedNames>
      <Descriptions />
      <EMailAddress />
      <SupportingWebsiteUrl />
      <CustomizationPrefix>{publisher_prefix}</CustomizationPrefix>
      <CustomizationOptionValuePrefix>10000</CustomizationOptionValuePrefix>
    </Publisher>
  </SolutionManifest>
</ImportExportXml>"""

    with open(os.path.join(solution_dir, "Other", "Solution.xml"), "w", encoding="utf-8") as f:
        f.write(solution_xml)

    # Copy generated workflows and lists schemas into solution
    workflows_src = os.path.join(output_dir, "workflows")
    if os.path.exists(workflows_src):
        shutil.copytree(workflows_src, os.path.join(solution_dir, "workflows"), dirs_exist_ok=True)

    lists_src = os.path.join(output_dir, "lists")
    if os.path.exists(lists_src):
        shutil.copytree(lists_src, os.path.join(solution_dir, "lists"), dirs_exist_ok=True)

    # Zip the solution folder
    with zipfile.ZipFile(zip_file_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(solution_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, solution_dir)
                zipf.write(file_path, arcname)

    print(f"Fallback solution zip file created successfully: {zip_file_path}")

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
        "--pack", action="store_true", help="Pack the solution using Microsoft Power Platform CLI."
    )
    parser.add_argument(
        "--solution-name", default="IDOP_Solution", help="Name of the solution (defaults to 'IDOP_Solution')."
    )
    parser.add_argument(
        "--publisher-name", default="CCBA", help="Publisher name for the solution (defaults to 'CCBA')."
    )
    parser.add_argument(
        "--publisher-prefix", default="ccba", help="Publisher prefix for the solution (defaults to 'ccba')."
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        default="./CDE",
        help="Target output directory path (defaults to './CDE').",
    )

    args = parser.parse_args()

    if not (args.cde or args.lists or args.workflows or args.all or args.action == "app" or args.app or args.pack):
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

    if args.all or args.pack:
        pack_solution(output_dir, args.solution_name, args.publisher_name, args.publisher_prefix)

    print("\nScaffolding process completed successfully.")

if __name__ == "__main__":
    main()
