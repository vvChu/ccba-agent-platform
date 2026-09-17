import os
from collections.abc import Generator

import pytest


@pytest.fixture(scope="session", autouse=True)
def clean_env() -> Generator[None, None, None]:
    # Pop variables that trigger False Positives in HarnessGuard during subprocess env checks
    vars_to_pop = ["MDCONVERT_MAX_OUTPUT_TOKENS", "VSCODE_GIT_ASKPASS_EXTRA_ARGS"]
    popped = {}
    for var in vars_to_pop:
        val = os.environ.pop(var, None)
        if val is not None:
            popped[var] = val

    orig_mock = os.environ.get("CCBA_AI_MOCK")
    os.environ["CCBA_AI_MOCK"] = "1"

    yield

    if orig_mock is not None:
        os.environ["CCBA_AI_MOCK"] = orig_mock
    else:
        os.environ.pop("CCBA_AI_MOCK", None)

    for var, val in popped.items():
        os.environ[var] = val


@pytest.fixture(autouse=True)
def cleanup_lock_files() -> Generator[None, None, None]:
    """Ensure lock files are cleaned up before and after each test execution."""

    def remove_locks():
        for filename in os.listdir("."):
            if filename.endswith(".lock"):
                try:
                    os.remove(filename)
                except OSError:
                    pass

    remove_locks()
    yield
    remove_locks()
