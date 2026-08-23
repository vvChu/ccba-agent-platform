"""Tests for Project Delivery Spoke Setup SOP and Templates (WF-03)."""

from pathlib import Path

import yaml
from scripts.spoke.spoke_adopter import SpokeAdopter
from scripts.spoke.spoke_synchronizer import SpokeRegistrar


def test_delivery_template_yaml_validity():
    """Ensure templates/workspace_context.delivery.yaml is valid YAML and matches schema."""
    template_path = (
        Path(__file__).resolve().parent.parent / "templates" / "workspace_context.delivery.yaml"
    )
    assert template_path.exists(), "Template file must exist"

    data = yaml.safe_load(template_path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)

    # Validate Project block
    assert "project" in data
    proj = data["project"]
    assert proj["archetype"] == "project_delivery"
    assert proj["mode"] == "consulting"
    assert "project_code" in proj
    assert "national_project_id" in proj
    assert "contract_id" in proj

    # Validate Organizational Identity block
    assert "organizational_identity" in data
    org = data["organizational_identity"]
    assert "owner_name" in org
    assert "owner_email" in org
    assert "department" in org
    assert "seat_role" in org

    # Validate QC Governance block
    assert "qc_governance" in data
    qc = data["qc_governance"]
    assert "authorized_qc_level" in qc
    assert qc.get("enable_quad_view_vision") is True

    # Validate Standards Applied block
    assert "standards_applied" in data
    assert isinstance(data["standards_applied"], list)
    assert len(data["standards_applied"]) >= 3

    # Validate CDE Structure block
    assert "cde_structure" in data
    assert len(data["cde_structure"]["folders"]) >= 4


def test_mock_delivery_spoke_adoption_and_sync(tmp_path: Path):
    """Verify that a mock Project Delivery spoke can be adopted and synchronized cleanly."""
    hub_dir = Path(__file__).resolve().parent.parent
    spoke_dir = tmp_path / "2026-04-dh-viet-nhat"
    spoke_dir.mkdir()
    (spoke_dir / ".md").mkdir()

    # Seed workspace_context.yaml from template
    template_path = hub_dir / "templates" / "workspace_context.delivery.yaml"
    (spoke_dir / ".md" / "workspace_context.yaml").write_text(
        template_path.read_text(encoding="utf-8"), encoding="utf-8"
    )

    # 1. Adopt Spoke
    adopter = SpokeAdopter(spoke_root=spoke_dir, hub_root=hub_dir)
    report = adopter.discover()
    assert report.suggested_archetype == "project_delivery"
    assert report.suggested_mode == "consulting" or report.suggested_mode == "hybrid"

    status = adopter.adopt(
        archetype="project_delivery",
        project_type="Thẩm tra thiết kế",
        mode="consulting",
    )
    assert status == 0

    # Verify workflows were copied
    spoke_workflows = spoke_dir / ".agents" / "workflows"
    assert spoke_workflows.exists()
    assert (spoke_workflows / "workflow_pccc_cdt_tuthamdinh.md").exists()

    # Verify Spoke Registrar identifies this as a non-sandbox project delivery spoke
    spoke_info = SpokeRegistrar().build_spoke_info(
        spoke_root=spoke_dir,
        hub_root=hub_dir,
        project_name="2026-04-dh-viet-nhat",
        project_type="Thẩm tra thiết kế",
    )
    assert spoke_info["is_sandbox"] is False
    assert spoke_info["project_type"] == "Thẩm tra thiết kế"
    assert spoke_info["owner_email"] == "chuvu@ibst-bim.vn"
