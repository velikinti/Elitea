import os
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from endpoints.automation import routes as automation_routes
from endpoints.automation.utility import integrate_script_to_framework
from settings import settings


def _make_app() -> FastAPI:
    app = FastAPI()
    app.include_router(automation_routes.router)
    return app


@pytest.fixture(autouse=True)
def _set_non_prod_env(monkeypatch: pytest.MonkeyPatch):
    # Default to non-prod so missing QA_API_KEY does not 503.
    monkeypatch.setattr(settings, "environment", "dev", raising=False)


def test_generate_tests_without_api_key_returns_401(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "api_key", "valid-key", raising=False)

    client = TestClient(_make_app())
    payload = {
        "api_spec": {
            "method": "GET",
            "url": "https://example.com/health",
            "headers": {},
            "body": None,
            "query_params": {},
        },
        "generator_type": "llm",
    }

    r = client.post("/generate-tests", json=payload)
    assert r.status_code == 401
    assert "Missing or invalid" in r.text


def test_generate_tests_with_invalid_api_key_returns_401(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "api_key", "valid-key", raising=False)

    client = TestClient(_make_app())
    payload = {
        "api_spec": {
            "method": "GET",
            "url": "https://example.com/health",
            "headers": {},
            "body": None,
            "query_params": {},
        },
        "generator_type": "llm",
    }

    r = client.post("/generate-tests", json=payload, headers={"X-API-Key": "wrong-key"})
    assert r.status_code == 401


def test_docs_accessible_in_dev(monkeypatch: pytest.MonkeyPatch):
    # This verifies the docs policy set in main_app() (docs enabled when not prod)
    from main import main_app

    monkeypatch.setattr(settings, "environment", "dev", raising=False)
    app = main_app()
    client = TestClient(app)

    r = client.get("/docs")
    assert r.status_code == 200


def test_integrate_script_rejects_target_dir_outside_allowed_root(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    # Arrange framework root and generated script
    framework_root = tmp_path / "framework"
    framework_root.mkdir(parents=True)
    monkeypatch.setattr(settings, "test_framework_path", str(framework_root), raising=False)

    generated_dir = Path.cwd() / settings.base_output_folder / "testscript"
    generated_dir.mkdir(parents=True, exist_ok=True)
    test_file = generated_dir / "test_sample.py"
    test_file.write_text("def test_ok():\n    assert True\n", encoding="utf-8")

    # Act/Assert: absolute dir outside framework root should be rejected
    outside_dir = tmp_path / "outside"
    outside_dir.mkdir()

    with pytest.raises(ValueError) as e:
        integrate_script_to_framework(str(test_file), str(outside_dir))

    assert "framework_test_dir" in str(e.value)
    assert "must be within allowed root" in str(e.value)


def test_integrate_script_allows_target_dir_within_allowed_root(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    framework_root = tmp_path / "framework"
    (framework_root / "api" / "tests").mkdir(parents=True)
    monkeypatch.setattr(settings, "test_framework_path", str(framework_root), raising=False)

    generated_dir = Path.cwd() / settings.base_output_folder / "testscript"
    generated_dir.mkdir(parents=True, exist_ok=True)
    test_file = generated_dir / "test_sample2.py"
    test_file.write_text("def test_ok2():\n    assert True\n", encoding="utf-8")

    # NOTE: We don't want to actually run pytest of an external framework here.
    # The function will attempt to run pytest; to keep this test light, provide an empty directory
    # and assert that integration itself succeeds and returns a dict.
    # Use a relative dir under framework_root.
    result = integrate_script_to_framework(str(test_file), "api/tests")
    assert result["success"] is True
    assert str(framework_root) in result["destination_file"]


def test_review_update_rejects_file_path_outside_generated_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    from endpoints.automation.utility import generate_test_scripts

    # Setup dummy framework markdown file
    md = tmp_path / "framework.md"
    md.write_text("# framework analysis\n" + ("x" * 200), encoding="utf-8")

    # Ensure generated dir exists
    generated_dir = Path.cwd() / settings.base_output_folder / "testscript"
    generated_dir.mkdir(parents=True, exist_ok=True)

    # Use a file outside generated dir
    outside = tmp_path / "outside.py"
    outside.write_text("def test_TC001():\n    assert True\n", encoding="utf-8")

    # minimal test case object structure expected by agent; we won't hit agent if we monkeypatch it
    class DummyAgent:
        def __init__(self, *args, **kwargs):
            pass

        def generate_scripts(self, test_cases, review=None, file_path=None):
            # returns a review update targeting provided file_path
            return [{"test_case_code": "TC001", "script": "def test_TC001():\n    assert True\n", "file_path": file_path, "has_review": True}]

    monkeypatch.setattr("endpoints.automation.utility.TestScriptAgent", DummyAgent)

    with pytest.raises(ValueError) as e:
        generate_test_scripts(
            test_cases=[
                {
                    "name": "t",
                    "code": "TC001",
                    "description": "d",
                    "request": {"url": "https://example.com"},
                    "expected_status": 200,
                    "steps": [],
                }
            ],
            framework_markdown_path=str(md),
            review="please update",
            file_path=str(outside),
            api_key="dummy",
        )

    assert "not permitted" in str(e.value)
