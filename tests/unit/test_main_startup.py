"""Unit tests for src.main startup behavior."""

import runpy
import sys
import types

import pytest

from src.main import health_check


@pytest.mark.asyncio
async def test_health_check_returns_expected_payload():
    """Covers the health endpoint function body directly."""
    result = await health_check()
    assert result == {"status": "ok", "message": "Quality Metrics Platform is healthy"}


def test_main_module_invokes_uvicorn_run_in_main_mode():
    """Covers the __main__ startup branch without starting a real server."""
    captured = {}

    def fake_run(app_path, host, port, reload):
        captured["app_path"] = app_path
        captured["host"] = host
        captured["port"] = port
        captured["reload"] = reload

    # Inject a lightweight fake uvicorn module before executing src.main as __main__
    original_uvicorn = sys.modules.get("uvicorn")
    sys.modules["uvicorn"] = types.SimpleNamespace(run=fake_run)

    try:
        runpy.run_module("src.main", run_name="__main__")
    finally:
        if original_uvicorn is not None:
            sys.modules["uvicorn"] = original_uvicorn
        else:
            del sys.modules["uvicorn"]

    assert captured == {
        "app_path": "src.main:app",
        "host": "0.0.0.0",
        "port": 8000,
        "reload": True,
    }
