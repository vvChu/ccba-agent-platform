"""Test configuration and hermetic fixtures for ccba-ai package."""

from __future__ import annotations

import os
from collections.abc import Generator

import pytest


@pytest.fixture(autouse=True)
def isolate_ccba_ai_env() -> Generator[None, None, None]:
    """Ensure ccba-ai tests run with CCBA_AI_MOCK unset so client delegate mocks work properly.

    Restores original environment after each test.
    """
    orig_mock = os.environ.get("CCBA_AI_MOCK")
    if "CCBA_AI_MOCK" in os.environ:
        del os.environ["CCBA_AI_MOCK"]

    yield

    if orig_mock is not None:
        os.environ["CCBA_AI_MOCK"] = orig_mock
    elif "CCBA_AI_MOCK" in os.environ:
        del os.environ["CCBA_AI_MOCK"]
