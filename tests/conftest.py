"""Pytest configuration shared by the test suite."""

import os
from uuid import uuid4


def pytest_configure(config):
    """Use a unique workspace-local temp directory for each pytest process."""
    if config.option.basetemp is None:
        temp_root = config.rootpath / "scratch" / "pytest_runs"
        temp_root.mkdir(parents=True, exist_ok=True)
        run_name = f"run_{os.getpid()}_{uuid4().hex}"
        config.option.basetemp = str(temp_root / run_name)
