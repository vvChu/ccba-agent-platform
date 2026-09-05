"""registry.py - Encrypted Registration Engine for registering Spokes to Hub.

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

import base64
import hashlib
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from .base import HAS_CRYPTOGRAPHY
from .catalog import CatalogMerger

if HAS_CRYPTOGRAPHY:
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey


class SpokeRegistrar:
    """Encrypted Registration Engine for registering Spokes to Hub."""

    def build_spoke_info(
        self,
        spoke_root: Path,
        hub_root: Path,
        project_name: str,
        project_type: str,
    ) -> dict[str, Any]:
        """Build standardized spoke metadata dict for registration."""
        context_file = spoke_root / ".md" / "workspace_context.yaml"
        if not context_file.exists():
            context_file = spoke_root / ".agents" / "workspace_context.yaml"

        is_sandbox = False
        owner_email = ""

        if context_file.exists():
            try:
                with open(context_file, encoding="utf-8") as f:
                    ctx = yaml.safe_load(f) or {}
                    proj = ctx.get("project", {})
                    sub_type = proj.get("sub_type", "")
                    guardrails = ctx.get("guardrails", {})
                    if sub_type == "personal_sandbox" or guardrails.get("sandbox_mode") is True:
                        is_sandbox = True
                    identity = ctx.get("organizational_identity", {})
                    owner_email = identity.get("owner_email", "")
            except Exception:
                pass

        info: dict[str, Any] = {
            "name": project_name,
            "path": str(spoke_root.resolve()),
            "project_type": project_type,
            "last_sync": datetime.now().isoformat(),
            "is_sandbox": is_sandbox,
        }
        if owner_email:
            info["owner_email"] = owner_email
        return info

    def register(
        self,
        spoke_root: Path,
        hub_root: Path,
        project_name: str,
        project_type: str,
        dry_run: bool = False,
    ) -> None:
        """Register Spoke to Hub encrypted spoke_registry.yaml."""
        if not HAS_CRYPTOGRAPHY:
            print(
                "[Registry] Warning: cryptography package not installed. Skipping Spoke registration.",
                file=sys.stderr,
            )
            return

        public_key_path = hub_root / ".agents" / "resources" / "registry_public_key.pem"
        if not public_key_path.exists():
            legacy_path = (
                hub_root / ".agents" / "workflows" / "resources" / "registry_public_key.pem"
            )
            if legacy_path.exists():
                public_key_path = legacy_path
            else:
                return

        if dry_run:
            print(
                f"[Registry] [DRY-RUN] Would register Spoke '{project_name}' to Hub Spoke Registry (Encrypted)."
            )
            return

        try:
            with open(public_key_path, "rb") as f:
                public_key = serialization.load_pem_public_key(f.read())

            if not isinstance(public_key, RSAPublicKey):
                print("[Registry] Warning: Public key is not RSA key.", file=sys.stderr)
                return

            spoke_info = self.build_spoke_info(spoke_root, hub_root, project_name, project_type)
            spoke_yaml = yaml.dump(spoke_info, allow_unicode=True)

            encrypted_bytes = public_key.encrypt(
                spoke_yaml.encode("utf-8"),
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None,
                ),
            )
            encrypted_b64 = base64.b64encode(encrypted_bytes).decode("utf-8")

            registry_file = hub_root / ".md" / "data" / "spoke_registry.yaml"
            registry_file.parent.mkdir(parents=True, exist_ok=True)

            registry_data: dict[str, Any] = {"spokes": []}
            if registry_file.exists():
                try:
                    with open(registry_file, encoding="utf-8") as f:
                        registry_data = yaml.safe_load(f) or {"spokes": []}
                except Exception:
                    pass

            spoke_id = hashlib.sha256(str(spoke_root.resolve()).encode("utf-8")).hexdigest()

            spokes = registry_data.get("spokes", [])
            updated = False
            for s in spokes:
                if s.get("spoke_id") == spoke_id:
                    s["encrypted_data"] = encrypted_b64
                    updated = True
                    break
            if not updated:
                spokes.append({"spoke_id": spoke_id, "encrypted_data": encrypted_b64})
            registry_data["spokes"] = spokes

            CatalogMerger(registry_file).atomic_write(registry_data)
            print(
                f"[Registry] Successfully registered Spoke '{project_name}' to Hub Spoke Registry (Encrypted)."
            )
        except Exception as e:
            print(f"[Registry] Warning: Failed to register Spoke to Hub: {e}", file=sys.stderr)
