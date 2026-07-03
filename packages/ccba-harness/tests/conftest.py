import os

import pytest


@pytest.fixture(scope="session", autouse=True)
def clean_env():
    # Pop variables that trigger False Positives in HarnessGuard during subprocess env checks
    vars_to_pop = ["MDCONVERT_MAX_OUTPUT_TOKENS", "VSCODE_GIT_ASKPASS_EXTRA_ARGS"]
    popped = {}
    for var in vars_to_pop:
        val = os.environ.pop(var, None)
        if val is not None:
            popped[var] = val

    yield

    # Restore them after the session
    for var, val in popped.items():
        os.environ[var] = val
