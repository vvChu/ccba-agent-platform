"""test_idop_schema_compatibility.py - ADR 0043 CI Schema & Statechart Contract Gate.

Validates that evolving schemas and approval state machines in IDOP-CCBA-WAY preserve:
1. Core contract integration fields and CdeDocumentSyncService type/choice contracts (Tier-1 Snapshot & Tier-2 Live).
2. SharePoint semantic constraints (20-index ceiling, non-indexable types, Lookup/TermSet integrity).
3. Cycle-safe BFS liveness and IBST Gateway safety invariants on Polymorphic Approval Rollup.
"""

from __future__ import annotations

import copy
import json
import os
import re
from collections import deque
from pathlib import Path
from typing import Any

import pytest
from tests.governance.test_skills_docs_integrity import verify_statechart_anti_lie

MAX_INDEXED_COLUMNS_PER_LIST = 20
NON_INDEXABLE_COLUMN_TYPES: frozenset[str] = frozenset(
    {"ManagedMetadata", "Taxonomy", "Note", "MultiChoice", "URL", "Hyperlink"}
)
TERMINAL_APPROVAL_STATES: frozenset[str] = frozenset({"Approved_Published", "Rejected_Closed"})
REQUIRED_CDE_APPROVAL_CHOICES: frozenset[str] = frozenset({"S0", "S1", "S2", "S3", "A1"})

CDE_SYNC_FIELD_CONTRACT: dict[str, set[str]] = {
    "Title": {"Text"},
    "ProjectCode": {"Text"},
    "Originator": {"Text"},
    "ZoneVolume": {"Text"},
    "LevelLocation": {"Text"},
    "DocumentCode": {"Text"},
    "IsoDocumentName": {"Text"},
    "ApprovalStatus": {"Choice"},
    "Version": {"Text"},
    "FileUrl": {"Hyperlink", "URL"},
}

CORE_REQUIRED_FIELDS: dict[str, dict[str, Any]] = {
    "projects": {
        "ListName": "Projects",
        "RequiredColumns": [
            "ProjectCode",
            "ProjectName",
            "ContractId",
            "Status",
            "CdeFolderPath",
            "RecordsFolderPath",
        ],
    },
    "job_assignments": {
        "ListName": "JobAssignments",
        "RequiredColumns": [
            "ProjectId",
            "PgvCode",
            "ContractId",
            "Status",
            "LegalQAChecker",
        ],
    },
    "cde_documents": {
        "ListName": "CDEDocuments",
        "RequiredColumns": list(CDE_SYNC_FIELD_CONTRACT.keys()),
    },
    "contracts": {
        "ListName": "Contracts",
        "RequiredColumns": [
            "ContractCode",
            "ContractName",
            "RequiresIBSTSign",
            "IBSTSubmissionStatus",
            "ContractFolderUrl",
        ],
    },
    "submissions": {
        "ListName": "Submissions",
        "RequiredColumns": [
            "SubmissionTitle",
            "RelatedEntity",
            "RelatedId",
            "SubmissionStatus",
            "CurrentStep",
            "TargetFolderUrl",
        ],
    },
    "approval_nodes": {
        "ListName": "ApprovalNodes",
        "RequiredColumns": [
            "SubmissionLookup",
            "StepOrder",
            "ApproverRole",
            "Outcome",
        ],
    },
}


def load_golden_snapshot() -> dict[str, Any]:
    """Loads the local Tier-1 Golden Contract Snapshot fixture at Hub.

    Returns:
        Parsed JSON dictionary of the Golden Contract Snapshot.
    """
    repo_root = Path(__file__).resolve().parent.parent.parent
    snap_path = repo_root / "tests" / "fixtures" / "idop_contract" / "core_lists_snapshot.json"
    return dict(json.loads(snap_path.read_text(encoding="utf-8")))


def validate_column_semantics(
    list_name: str, col: dict[str, Any], known_lists: set[str], known_tax: set[str]
) -> list[str]:
    """Validates SharePoint semantic constraints for a single column definition."""
    errors: list[str] = []
    col_name = str(col.get("Name", "<unnamed>"))
    col_type = str(col.get("Type", ""))
    is_multi = col.get("AllowMultiple") is True or col_type in ("LookupMulti", "UserMulti")

    if col.get("Indexed") is True:
        if col_type in NON_INDEXABLE_COLUMN_TYPES:
            errors.append(f"{list_name}.{col_name}: Non-indexable type '{col_type}'")
        elif col_type in ("Lookup", "User", "LookupMulti", "UserMulti") and is_multi:
            errors.append(f"{list_name}.{col_name}: Multi-value {col_type} cannot be indexed")

    if col_type == "Lookup":
        target_list = col.get("Lookup", {}).get("List")
        if not target_list or str(target_list) not in known_lists:
            errors.append(f"{list_name}.{col_name}: Invalid Lookup target '{target_list}'")
    elif col_type in ("ManagedMetadata", "Taxonomy"):
        target_term = col.get("TermSet", {}).get("Name")
        if not target_term or str(target_term) not in known_tax:
            errors.append(f"{list_name}.{col_name}: Invalid TermSet '{target_term}'")
    elif col_type in ("Choice", "MultiChoice"):
        if not isinstance(col.get("Choices"), list) or not col.get("Choices"):
            errors.append(f"{list_name}.{col_name}: {col_type} missing Choices")
    return errors


def validate_idop_list_schema_semantics(
    list_data: dict[str, Any],
    known_lists: set[str],
    known_tax: set[str],
) -> list[str]:
    """Validates list-level 20-index ceiling and column-level semantic rules.

    Args:
        list_data: Parsed JSON list definition dict.
        known_lists: Valid target list identifiers for Lookup fields.
        known_tax: Valid Taxonomy TermSet names.

    Returns:
        List of semantic validation error strings.
    """
    list_name = str(list_data.get("ListName") or "<missing_ListName>")
    columns = list_data.get("Columns")
    if not isinstance(columns, list) or len(columns) == 0:
        return [f"[{list_name}] Missing or empty Columns array"]

    errors: list[str] = []
    indexed_cols = [str(c.get("Name", "")) for c in columns if c.get("Indexed") is True]
    if len(indexed_cols) > MAX_INDEXED_COLUMNS_PER_LIST:
        errors.append(
            f"[{list_name}] Indexed column count ({len(indexed_cols)}) exceeds limit {MAX_INDEXED_COLUMNS_PER_LIST}"
        )

    for col in columns:
        errors.extend(validate_column_semantics(list_name, col, known_lists, known_tax))
    return errors


def validate_core_contract_fields(stem: str, list_data: dict[str, Any]) -> list[str]:
    """Validates that a core IDOP list preserves required fields, types, and CDE choices.

    Args:
        stem: File stem key in CORE_REQUIRED_FIELDS.
        list_data: Parsed JSON list definition dict.

    Returns:
        List of contract drift error strings.
    """
    spec = CORE_REQUIRED_FIELDS[stem]
    errors: list[str] = []
    actual_name = list_data.get("ListName")
    if actual_name != spec["ListName"]:
        errors.append(f"[{stem}] Expected ListName '{spec['ListName']}', got '{actual_name}'")

    col_map: dict[str, dict[str, Any]] = {
        str(c["Name"]): c
        for c in list_data.get("Columns", [])
        if isinstance(c, dict) and "Name" in c
    }
    for req_col in spec["RequiredColumns"]:
        if req_col not in col_map:
            errors.append(f"[{stem}] Missing required core contract column '{req_col}'")

    if stem == "cde_documents":
        for field_name, allowed_types in CDE_SYNC_FIELD_CONTRACT.items():
            if field_name in col_map:
                actual_type = str(col_map[field_name].get("Type", ""))
                if actual_type not in allowed_types:
                    errors.append(
                        f"[cde_documents.{field_name}] Type '{actual_type}' not in {sorted(allowed_types)}"
                    )
        if "ApprovalStatus" in col_map:
            choices = set(col_map["ApprovalStatus"].get("Choices") or [])
            missing_choices = REQUIRED_CDE_APPROVAL_CHOICES - choices
            if missing_choices:
                errors.append(
                    f"[cde_documents.ApprovalStatus] Missing choices: {sorted(missing_choices)}"
                )
    return errors


def build_approval_graph(requires_ibst: bool) -> dict[str, list[str]]:
    """Builds the directed state transition graph for IDOP Polymorphic Approval Rollup.

    Args:
        requires_ibst: Whether RequiresIBSTSign is enabled on the submission/contract.

    Returns:
        Adjacency list mapping state name to list of outgoing target states.
    """
    step2_targets = (
        ["IBST_Gateway_Review", "Returned_Revision", "Rejected_Closed"]
        if requires_ibst
        else ["Approved_Published", "Returned_Revision", "Rejected_Closed"]
    )
    graph: dict[str, list[str]] = {
        "Pending_Step1": ["Pending_Step2", "Returned_Revision", "Rejected_Closed"],
        "Pending_Step2": step2_targets,
        "Returned_Revision": ["Pending_Step1", "Rejected_Closed"],
        "Approved_Published": [],
        "Rejected_Closed": [],
    }
    if requires_ibst:
        graph["IBST_Gateway_Review"] = [
            "Approved_Published",
            "Returned_Revision",
            "Rejected_Closed",
        ]
    return graph


def verify_liveness_and_reachability(
    graph: dict[str, list[str]],
    start_node: str = "Pending_Step1",
) -> list[str]:
    """Verifies via cycle-safe BFS that all states are reachable and free of non-terminal deadlocks.

    Args:
        graph: Directed state transition adjacency mapping.
        start_node: Initial state node.

    Returns:
        List of reachability or deadlock/livelock error strings.
    """
    errors: list[str] = []
    reachable: set[str] = {start_node}
    queue: deque[str] = deque([start_node])
    while queue:
        curr = queue.popleft()
        for nxt in graph.get(curr, []):
            if nxt not in reachable:
                reachable.add(nxt)
                queue.append(nxt)

    unreachable = set(graph.keys()) - reachable
    if unreachable:
        errors.append(f"Unreachable states from '{start_node}': {sorted(unreachable)}")

    for state in sorted(reachable):
        if state in TERMINAL_APPROVAL_STATES:
            continue
        visited: set[str] = {state}
        bfs: deque[str] = deque([state])
        can_terminate = False
        while bfs:
            node = bfs.popleft()
            if node in TERMINAL_APPROVAL_STATES:
                can_terminate = True
                break
            for nxt in graph.get(node, []):
                if nxt not in visited:
                    visited.add(nxt)
                    bfs.append(nxt)
        if not can_terminate:
            errors.append(
                f"State '{state}' is trapped in a deadlock/livelock with no path to terminal state"
            )
    return errors


def verify_ibst_gateway_invariant(
    graph: dict[str, list[str]],
    start_node: str = "Pending_Step1",
) -> list[str]:
    """Verifies via simple-path BFS that every path to Approved_Published traverses IBST_Gateway_Review.

    Args:
        graph: Directed state transition adjacency mapping.
        start_node: Initial state node.

    Returns:
        List of safety invariant violation error strings.
    """
    errors: list[str] = []
    paths_to_approved: list[list[str]] = []
    queue: deque[list[str]] = deque([[start_node]])

    while queue:
        path = queue.popleft()
        curr = path[-1]
        if curr == "Approved_Published":
            paths_to_approved.append(path)
            continue
        for nxt in graph.get(curr, []):
            if nxt not in path:
                queue.append([*path, nxt])

    if not paths_to_approved:
        return ["No valid simple path exists from start_node to 'Approved_Published'"]

    for path in paths_to_approved:
        if "IBST_Gateway_Review" not in path:
            errors.append(f"IBST Gateway bypass detected on path: {' -> '.join(path)}")
    return errors


def test_tier1_golden_snapshot_core_contracts_and_semantics() -> None:
    """Tier-1 CI Gate: Validates the 6 core IDOP lists against Golden Snapshot contracts and semantics."""
    snapshot = load_golden_snapshot()
    known_lists = set(snapshot["known_lists"])
    known_tax = set(snapshot["known_taxonomy"])
    core_lists = snapshot["core_lists"]

    assert set(core_lists.keys()) == set(CORE_REQUIRED_FIELDS.keys())
    for stem, list_data in core_lists.items():
        contract_errors = validate_core_contract_fields(stem, list_data)
        assert not contract_errors, f"Contract drift in {stem}: {contract_errors}"
        semantic_errors = validate_idop_list_schema_semantics(list_data, known_lists, known_tax)
        assert not semantic_errors, f"Semantic violation in {stem}: {semantic_errors}"


def test_core_contract_fields_validation_logic() -> None:
    """Validates that Schema Drift Gate permits open extensions while enforcing field types."""
    snapshot = load_golden_snapshot()
    projects_schema = copy.deepcopy(snapshot["core_lists"]["projects"])
    projects_schema["Columns"].append(
        {"Name": "NewCustomField2026", "Type": "Text", "DisplayName": "Trường mở rộng"}
    )
    assert validate_core_contract_fields("projects", projects_schema) == []


def test_core_contract_fields_drift_detected() -> None:
    """Validates that Schema Drift Gate catches renamed columns, wrong types, and missing CDE choices."""
    snapshot = load_golden_snapshot()
    broken_projects = copy.deepcopy(snapshot["core_lists"]["projects"])
    for col in broken_projects["Columns"]:
        if col["Name"] == "ProjectCode":
            col["Name"] = "MaDuAnRenamed"
    proj_errs = validate_core_contract_fields("projects", broken_projects)
    assert any("ProjectCode" in e for e in proj_errs)

    broken_cde = copy.deepcopy(snapshot["core_lists"]["cde_documents"])
    for col in broken_cde["Columns"]:
        if col["Name"] == "ApprovalStatus":
            col["Choices"] = ["S0", "S1"]
        elif col["Name"] == "FileUrl":
            col["Type"] = "Number"
    cde_errs = validate_core_contract_fields("cde_documents", broken_cde)
    assert any("ApprovalStatus" in e and "Missing choices" in e for e in cde_errs)
    assert any("FileUrl" in e and "Number" in e for e in cde_errs)


def test_semantic_validator_catches_index_and_lookup_violations() -> None:
    """Validates that semantic validator catches >20 indexes, non-indexable types, and broken refs."""
    known_lists = {"Projects", "Customers"}
    known_tax = {"CCBA_TrangThaiChung"}
    bad_schema: dict[str, Any] = {
        "ListName": "BrokenList",
        "Columns": [{"Name": f"IdxCol{i}", "Type": "Text", "Indexed": True} for i in range(21)]
        + [
            {"Name": "BadNoteIdx", "Type": "Note", "Indexed": True},
            {
                "Name": "BadMultiLookupIdx",
                "Type": "Lookup",
                "Indexed": True,
                "AllowMultiple": True,
                "Lookup": {"List": "Projects"},
            },
            {"Name": "GhostLookup", "Type": "Lookup", "Lookup": {"List": "NonExistentList"}},
            {"Name": "GhostTerm", "Type": "ManagedMetadata", "TermSet": {"Name": "CCBA_GhostTerm"}},
        ],
    }
    errs = validate_idop_list_schema_semantics(bad_schema, known_lists, known_tax)
    assert any("exceeds limit 20" in e for e in errs)
    assert any("BadNoteIdx" in e for e in errs)
    assert any("BadMultiLookupIdx" in e for e in errs)
    assert any("NonExistentList" in e for e in errs)
    assert any("CCBA_GhostTerm" in e for e in errs)


def test_approval_statechart_liveness_and_ibst_gateway_litmus() -> None:
    """Verifies cycle-safe BFS liveness and Two-Edit Litmus test on IBST Gateway bypass."""
    ibst_graph = build_approval_graph(requires_ibst=True)
    assert verify_liveness_and_reachability(ibst_graph) == []
    assert verify_ibst_gateway_invariant(ibst_graph) == []

    internal_graph = build_approval_graph(requires_ibst=False)
    assert verify_liveness_and_reachability(internal_graph) == []
    assert any("bypass detected" in e for e in verify_ibst_gateway_invariant(internal_graph))

    # Litmus 1: Inject direct shortcut Pending_Step2 -> Approved_Published when RequiresIBSTSign=True
    bypassed_graph = copy.deepcopy(ibst_graph)
    bypassed_graph["Pending_Step2"].append("Approved_Published")
    litmus_bypass_errs = verify_ibst_gateway_invariant(bypassed_graph)
    assert any(
        "Pending_Step1 -> Pending_Step2 -> Approved_Published" in e for e in litmus_bypass_errs
    )

    # Litmus 2: Inject non-terminal livelock cycle reachable from Pending_Step1
    trapped_graph = copy.deepcopy(ibst_graph)
    trapped_graph["Pending_Step1"].append("Stuck_Review")
    trapped_graph["Stuck_Review"] = ["Stuck_Review"]
    litmus_trap_errs = verify_liveness_and_reachability(trapped_graph)
    assert any("Stuck_Review" in e and "deadlock/livelock" in e for e in litmus_trap_errs)


def test_sharepoint_iac_skill_statechart_and_bug_path_contract() -> None:
    """Verifies that ccba-sharepoint-iac SKILL.md v1.1.0 includes a valid stateDiagram-v2 and bug_path."""
    repo_root = Path(__file__).resolve().parent.parent.parent
    skill_md = (repo_root / ".agents" / "skills" / "ccba-sharepoint-iac" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    mermaid_blocks = re.findall(r"```mermaid\s*\n(.*?)```", skill_md, flags=re.DOTALL)
    assert len(mermaid_blocks) >= 1, (
        "Expected at least one mermaid statechart in ccba-sharepoint-iac"
    )
    assert verify_statechart_anti_lie(mermaid_blocks[0]) == []
    assert "bug_path:" in skill_md and "IBST_Gateway_Review" in skill_md


def _resolve_live_idop_sharepoint_dir() -> Path | None:
    """Resolves the live IDOP-CCBA-WAY datamodel/sharepoint directory if present."""
    env_override = os.environ.get("CCBA_IDOP_PATH")
    if env_override:
        candidate = Path(env_override).resolve() / "datamodel" / "sharepoint"
        return candidate if candidate.is_dir() else None
    repo_root = Path(__file__).resolve().parent.parent.parent
    default_dir = repo_root.parent / "IDOP-CCBA-WAY" / "datamodel" / "sharepoint"
    return default_dir if default_dir.is_dir() else None


def test_tier2_live_idop_schema_and_snapshot_parity_if_present() -> None:
    """Tier-2 Live Gate: Scans all live IDOP-CCBA-WAY lists/taxonomies and checks Golden Snapshot parity."""
    sp_dir = _resolve_live_idop_sharepoint_dir()
    if sp_dir is None:
        pytest.skip(
            "IDOP-CCBA-WAY local directory not found; Tier-1 Golden Snapshot already verified."
        )

    lists_dir = sp_dir / "lists"
    tax_dir = sp_dir / "taxonomy"
    list_files = sorted(lists_dir.rglob("*.json"), key=lambda p: (p.stem, p.as_posix()))
    tax_files = sorted(tax_dir.glob("*.json"), key=lambda p: (p.stem, p.as_posix()))
    assert len(list_files) >= 59, f"Expected >=59 SharePoint lists, found {len(list_files)}"
    assert len(tax_files) >= 21, f"Expected >=21 Taxonomy files, found {len(tax_files)}"

    known_lists: set[str] = set()
    live_lists_by_stem: dict[str, dict[str, Any]] = {}
    for fp in list_files:
        data = json.loads(fp.read_text(encoding="utf-8"))
        if data.get("ListName"):
            known_lists.add(str(data["ListName"]))
        known_lists.add(fp.stem)
        live_lists_by_stem[fp.stem] = data

    known_tax: set[str] = set()
    for fp in tax_files:
        tdata = json.loads(fp.read_text(encoding="utf-8"))
        tname = tdata.get("TermSetInfo", {}).get("Name")
        if tname:
            known_tax.add(str(tname))
        known_tax.add(fp.stem)

    for stem, data in live_lists_by_stem.items():
        sem_errs = validate_idop_list_schema_semantics(data, known_lists, known_tax)
        assert not sem_errs, f"Live semantic error in {stem}: {sem_errs}"

    snapshot = load_golden_snapshot()
    for core_stem in CORE_REQUIRED_FIELDS:
        assert core_stem in live_lists_by_stem, f"Missing live core list: {core_stem}"
        live_core = live_lists_by_stem[core_stem]
        assert validate_core_contract_fields(core_stem, live_core) == []
        assert live_core.get("Columns") == snapshot["core_lists"][core_stem]["Columns"], (
            f"Golden Snapshot drift detected against live IDOP list '{core_stem}'"
        )
