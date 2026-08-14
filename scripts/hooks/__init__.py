"""CCBA Platform Lifecycle Hooks Sub-Package.

Provides unified typed contracts, coordinator, and modular hook implementations
for security, diff complexity, file naming, brand compliance, and test speed guardrails.

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

from .base import BaseHook, HookContext, HookEvent, HookResult
from .brand import BrandHook
from .coordinator import HookCoordinator, get_default_coordinator
from .naming import NamingHook
from .privacy import PrivacyHook
from .scout import ScoutBlockHook
from .session import SessionInitHook
from .simplify import SimplifyGateHook
from .speed import TestSpeedHook

__all__ = [
    "BaseHook",
    "HookContext",
    "HookResult",
    "HookEvent",
    "HookCoordinator",
    "get_default_coordinator",
    "PrivacyHook",
    "SimplifyGateHook",
    "ScoutBlockHook",
    "BrandHook",
    "NamingHook",
    "SessionInitHook",
    "TestSpeedHook",
]
