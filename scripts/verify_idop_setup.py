#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verification script for SharePoint IDOP toolkit setup.
Validates CDE folders, list schemas, PnP scripts, and Power Automate workflows.
"""

import os
import sys
import json
import shutil
import subprocess
from typing import List, Set

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
    cmd: List[str] = [sys.executable, "scripts/idop_scaffolder.py", "--all", "-o", cde_path]
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

    expected_cde_folders: Set[str] = {
        "01_WIP",
        "02_Shared",
        "03_Published",
        "04_Archive",
        "05_Contract Reference"
    }

    actual_items: List[str] = os.listdir(cde_path)
    actual_dirs: Set[str] = {
        item for item in actual_items if os.path.isdir(os.path.join(cde_path, item))
    }

    # Filter out lists and workflows directory which are generated during --all run
    cde_folders: Set[str] = actual_dirs - {"lists", "workflows"}

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

    list_names: List[str] = [
        "CRM", "Contracts", "Finance", "Approvals", "HRAdmin", "LegalQA", "RDProjects"
    ]

    for name in list_names:
        schema_file: str = os.path.join(lists_path, f"{name}_schema.json")
        ps_file: str = os.path.join(lists_path, f"{name}_provision.ps1")

        # 1. Validate Schema File
        if not os.path.isfile(schema_file):
            raise AssertionError(f"Schema file '{schema_file}' is missing.")
        with open(schema_file, "r", encoding="utf-8") as f:
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
    all_files: List[str] = os.listdir(lists_path)
    if len(all_files) != 14:
        raise AssertionError(f"Expected exactly 14 files in '{lists_path}', found {len(all_files)}: {all_files}")

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
        raise AssertionError(f"Workflows path '{workflows_path}' does not exist or is not a directory.")

    spec_file: str = os.path.join(workflows_path, "PowerAutomate_spec.md")
    def_file: str = os.path.join(workflows_path, "PowerAutomate_flow_definition.json")

    # 1. Validate PowerAutomate_spec.md
    if not os.path.isfile(spec_file):
        raise AssertionError(f"Specification file '{spec_file}' is missing.")
    with open(spec_file, "r", encoding="utf-8") as f:
        spec_content = f.read()

    # Check for mermaid block
    if "```mermaid" not in spec_content:
        raise AssertionError(f"Specification file '{spec_file}' does not contain a '```mermaid' block.")

    # Check for all 11 workflow steps
    for i in range(1, 12):
        expected_step: str = f"Step {i}:"
        # Check both "Step i:" and "Step i" to be safe and flexible
        if (expected_step not in spec_content) and (f"Step {i}" not in spec_content) and (f"Step{i}" not in spec_content):
            raise AssertionError(f"Specification file '{spec_file}' lacks details for 'Step {i}'.")

    # 2. Validate PowerAutomate_flow_definition.json
    if not os.path.isfile(def_file):
        raise AssertionError(f"Flow definition file '{def_file}' is missing.")
    with open(def_file, "r", encoding="utf-8") as f:
        def_data = json.load(f)
    if not isinstance(def_data, dict):
        raise AssertionError(f"Flow definition file '{def_file}' is not a valid JSON object.")

    # Validate that workflows folder has exactly 2 files
    all_files: List[str] = os.listdir(workflows_path)
    if len(all_files) != 2:
        raise AssertionError(f"Expected exactly 2 files in '{workflows_path}', found {len(all_files)}: {all_files}")

    print("Workflows validation passed successfully.")

def main() -> None:
    """Main execution orchestrating CDE cleanup, execution, and validation."""
    cde_path: str = "./CDE"
    try:
        clean_slate(cde_path)
        run_scaffolder(cde_path)
        validate_cde_structure(cde_path)
        validate_lists(cde_path)
        validate_workflows(cde_path)
        print("\nAll verification checks passed successfully!")
        sys.exit(0)
    except Exception as err:
        print(f"\nVerification FAILED: {err}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
