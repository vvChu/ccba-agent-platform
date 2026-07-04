#!/usr/bin/env python3
"""
Verification script for SharePoint IDOP toolkit setup.
Validates CDE folders, list schemas, PnP scripts, and Power Automate workflows.
"""

import json
import os
import shutil
import subprocess
import sys


def clean_slate(cde_path: str) -> None:
    """Deletes the CDE directory if it exists to ensure a clean slate.

    Args:
        cde_path: The relative or absolute path to the CDE directory.
    """
    if os.path.exists(cde_path):
        print(f"Cleaning slate: Removing existing directory '{cde_path}'...")
        shutil.rmtree(cde_path)
    else:
        print(f"No existing '{cde_path}' directory found. Starting clean.")


def run_scaffolder(cde_path: str) -> None:
    """Runs the idop_scaffolder.py script with all scaffolding options.

    Args:
        cde_path: The target output directory path.

    Raises:
        subprocess.CalledProcessError: If the execution of the scaffolder fails.
    """
    cmd: list[str] = [sys.executable, "scripts/idop_scaffolder.py", "--all", "-o", cde_path]
    print(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    print("Scaffolder Output:")
    print(result.stdout)
    if result.stderr:
        print("Scaffolder Errors/Warnings:", file=sys.stderr)
        print(result.stderr, file=sys.stderr)


def validate_cde_structure(cde_path: str) -> None:
    """Validates that the CDE directory contains exactly the 5 standard CDE folders.

    Args:
        cde_path: The target CDE directory path.

    Raises:
        AssertionError: If validation checks fail.
    """
    print("Validating CDE structure...")
    if not os.path.isdir(cde_path):
        raise AssertionError(f"CDE path '{cde_path}' does not exist or is not a directory.")

    expected_cde_folders: set[str] = {
        "01_WIP",
        "02_Shared",
        "03_Published",
        "04_Archive",
        "05_Contract Reference",
    }

    actual_items: list[str] = os.listdir(cde_path)
    actual_dirs: set[str] = {
        item for item in actual_items if os.path.isdir(os.path.join(cde_path, item))
    }

    # Filter out generated directories (lists, workflows, IDOP_Solution, etc.) by keeping only standard CDE folder prefixes
    cde_folders: set[str] = {d for d in actual_dirs if d.startswith(("01", "02", "03", "04", "05"))}

    assert cde_folders == expected_cde_folders, (
        f"CDE folder mismatch. Expected: {expected_cde_folders}. Got: {cde_folders}"
    )
    print("CDE structure validation passed successfully.")


def validate_lists(cde_path: str) -> None:
    """Validates that lists/ contains 7 valid JSON schemas and 7 PnP PowerShell scripts.

    Args:
        cde_path: The target CDE directory path.

    Raises:
        AssertionError: If validation checks fail.
        json.JSONDecodeError: If any schema file contains invalid JSON.
    """
    print("Validating Lists schemas and PowerShell scripts...")
    lists_path: str = os.path.join(cde_path, "lists")
    if not os.path.isdir(lists_path):
        raise AssertionError(f"Lists path '{lists_path}' does not exist or is not a directory.")

    list_names: list[str] = [
        "CRM",
        "Contracts",
        "Finance",
        "Approvals",
        "HRAdmin",
        "LegalQA",
        "RDProjects",
    ]

    for name in list_names:
        schema_file: str = os.path.join(lists_path, f"{name}_schema.json")
        ps_file: str = os.path.join(lists_path, f"{name}_provision.ps1")

        # 1. Validate Schema File
        if not os.path.isfile(schema_file):
            raise AssertionError(f"Schema file '{schema_file}' is missing.")
        with open(schema_file, encoding="utf-8") as f:
            schema_data = json.load(f)
        if not isinstance(schema_data, dict):
            raise AssertionError(f"Schema file '{schema_file}' is not a valid JSON object.")
        if schema_data.get("listName") != name:
            raise AssertionError(
                f"ListName mismatch in '{schema_file}'. Expected '{name}', got '{schema_data.get('listName')}'."
            )

        # 2. Validate PowerShell Script File
        if not os.path.isfile(ps_file):
            raise AssertionError(f"PnP PowerShell script '{ps_file}' is missing.")

    # Validate that lists folder has exactly 14 files (7 schemas + 7 scripts)
    all_files: list[str] = os.listdir(lists_path)
    if len(all_files) != 14:
        raise AssertionError(
            f"Expected exactly 14 files in '{lists_path}', found {len(all_files)}: {all_files}"
        )

    print("Lists schemas and PowerShell scripts validation passed successfully.")


def validate_workflows(cde_path: str) -> None:
    """Validates workflows/ contains PowerAutomate_spec.md and PowerAutomate_flow_definition.json.

    Args:
        cde_path: The target CDE directory path.

    Raises:
        AssertionError: If validation checks fail.
        json.JSONDecodeError: If flow definition file contains invalid JSON.
    """
    print("Validating Workflows specification and flow definition...")
    workflows_path: str = os.path.join(cde_path, "workflows")
    if not os.path.isdir(workflows_path):
        raise AssertionError(
            f"Workflows path '{workflows_path}' does not exist or is not a directory."
        )

    spec_file: str = os.path.join(workflows_path, "PowerAutomate_spec.md")
    def_file: str = os.path.join(workflows_path, "PowerAutomate_flow_definition.json")

    # 1. Validate PowerAutomate_spec.md
    if not os.path.isfile(spec_file):
        raise AssertionError(f"Specification file '{spec_file}' is missing.")
    with open(spec_file, encoding="utf-8") as f:
        spec_content = f.read()

    # Check for mermaid block
    if "```mermaid" not in spec_content:
        raise AssertionError(
            f"Specification file '{spec_file}' does not contain a '```mermaid' block."
        )

    # Check for all 11 workflow steps
    for i in range(1, 12):
        expected_step: str = f"Step {i}:"
        # Check both "Step i:" and "Step i" to be safe and flexible
        if (
            (expected_step not in spec_content)
            and (f"Step {i}" not in spec_content)
            and (f"Step{i}" not in spec_content)
        ):
            raise AssertionError(f"Specification file '{spec_file}' lacks details for 'Step {i}'.")

    # 2. Validate PowerAutomate_flow_definition.json
    if not os.path.isfile(def_file):
        raise AssertionError(f"Flow definition file '{def_file}' is missing.")
    with open(def_file, encoding="utf-8") as f:
        def_data = json.load(f)
    if not isinstance(def_data, dict):
        raise AssertionError(f"Flow definition file '{def_file}' is not a valid JSON object.")

    # Validate that workflows folder has exactly 2 files
    all_files: list[str] = os.listdir(workflows_path)
    if len(all_files) != 2:
        raise AssertionError(
            f"Expected exactly 2 files in '{workflows_path}', found {len(all_files)}: {all_files}"
        )

    print("Workflows validation passed successfully.")


def run_app_scaffolder(app_path: str) -> None:
    """Runs the app scaffolding command using positional CLI parameter."""
    cmd: list[str] = [sys.executable, "scripts/idop_scaffolder.py", "app", "--app-dir", app_path]
    print(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    print("App Scaffolder Output:")
    print(result.stdout)
    if result.stderr:
        print("App Scaffolder Errors/Warnings:", file=sys.stderr)
        print(result.stderr, file=sys.stderr)


def validate_app_structure(app_path: str) -> None:
    """Validates that the app directory contains exactly the 8 standard files, and that package.json and App.tsx are valid."""
    print("Validating App structure...")
    if not os.path.isdir(app_path):
        raise AssertionError(f"App path '{app_path}' does not exist or is not a directory.")

    expected_files = [
        "package.json",
        "tsconfig.json",
        "vite.config.ts",
        "index.html",
        "src/main.tsx",
        "src/index.css",
        "src/App.css",
        "src/App.tsx",
    ]

    for f in expected_files:
        path = os.path.join(app_path, f)
        if not os.path.isfile(path):
            raise AssertionError(f"Expected skeleton file '{path}' is missing.")

    # Parse package.json inside the generated app to assert dependencies include react, react-dom and devDependencies include vite, typescript
    pkg_path = os.path.join(app_path, "package.json")
    with open(pkg_path, encoding="utf-8") as f:
        pkg = json.load(f)

    deps = pkg.get("dependencies", {})
    dev_deps = pkg.get("devDependencies", {})

    assert "react" in deps, "package.json dependencies missing 'react'"
    assert "react-dom" in deps, "package.json dependencies missing 'react-dom'"
    assert "vite" in dev_deps, "package.json devDependencies missing 'vite'"
    assert "typescript" in dev_deps, "package.json devDependencies missing 'typescript'"

    # Read App.tsx to assert that it contains the CCBA dashboard premium mock elements
    app_tsx_path = os.path.join(app_path, "src", "App.tsx")
    with open(app_tsx_path, encoding="utf-8") as f:
        app_tsx_content = f.read()

    assert (
        "CCBA IDOP Platform" in app_tsx_content
        or "CCBA IDOP Deployment Dashboard" in app_tsx_content
    ), "App.tsx does not contain the CCBA dashboard premium mock elements."

    print("App validation passed successfully.")


def validate_solution_packing(cde_path: str) -> None:
    """Validates that running scaffolder with --pack creates a valid Solution zip file."""
    print("Validating Solution packing...")
    solution_name = "Test_Solution"
    cmd: list[str] = [
        sys.executable,
        "scripts/idop_scaffolder.py",
        "--pack",
        "--solution-name",
        solution_name,
        "-o",
        cde_path,
    ]
    print(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    print("Packer Output:")
    print(result.stdout)

    zip_file = os.path.join(cde_path, f"{solution_name}.zip")
    if not os.path.isfile(zip_file):
        raise AssertionError(f"Expected solution zip file '{zip_file}' was not created.")

    import zipfile

    with zipfile.ZipFile(zip_file, "r") as z:
        namelist = z.namelist()
        assert "Other/Solution.xml" in namelist, "Solution zip missing 'Other/Solution.xml'"

    print("Solution packing validation passed successfully.")


def main() -> None:
    """Main execution orchestrating CDE cleanup, execution, and validation."""
    cde_path: str = "./CDE"
    app_path: str = "./src/test-idop-app"
    try:
        # 1. Clean slate
        clean_slate(cde_path)
        clean_slate(app_path)

        # 2. Run CDE Scaffolder & Validate
        run_scaffolder(cde_path)
        validate_cde_structure(cde_path)
        validate_lists(cde_path)
        validate_workflows(cde_path)

        # 2.5 Run Solution packing & Validate
        validate_solution_packing(cde_path)

        # 3. Run App Scaffolder & Validate
        run_app_scaffolder(app_path)
        validate_app_structure(app_path)

        # 4. Clean up on success
        clean_slate(cde_path)
        clean_slate(app_path)

        print("\nAll verification checks passed successfully!")
        sys.exit(0)
    except Exception as err:
        print(f"\nVerification FAILED: {err}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
