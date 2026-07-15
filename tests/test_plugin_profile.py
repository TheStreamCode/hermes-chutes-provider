"""Offline contract tests for the Chutes Hermes provider."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import types
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_PATH = REPOSITORY_ROOT / "__init__.py"
README_PATH = REPOSITORY_ROOT / "README.md"
CI_WORKFLOW_PATH = REPOSITORY_ROOT / ".github" / "workflows" / "ci.yml"
PACKAGE_PATH = REPOSITORY_ROOT / "hermes_chutes_provider" / "__init__.py"
PYPROJECT_PATH = REPOSITORY_ROOT / "pyproject.toml"
MANIFEST_PATH = REPOSITORY_ROOT / "plugin.yaml"
CHANGELOG_PATH = REPOSITORY_ROOT / "CHANGELOG.md"
RELEASE_VERSION = "0.1.3"


class ProviderProfile:
    """Minimal stand-in for Hermes' ProviderProfile at the import boundary."""

    fallback_models = ()
    default_aux_model = ""
    models_url = ""
    default_headers: dict[str, str] = {}

    def __init__(self, **attributes: object) -> None:
        self.__dict__.update(attributes)


def load_directory_plugin() -> ProviderProfile:
    """Import the provider from its Hermes user-plugin directory layout."""

    if not PLUGIN_PATH.is_file():
        raise AssertionError(f"missing directory plugin entry point: {PLUGIN_PATH}")

    registered: list[ProviderProfile] = []
    providers_module = types.ModuleType("providers")
    providers_module.register_provider = registered.append
    base_module = types.ModuleType("providers.base")
    base_module.ProviderProfile = ProviderProfile

    module_name = "chutes_directory_plugin_under_test"
    module_names = ("providers", "providers.base", module_name)
    previous_modules = {name: sys.modules.get(name) for name in module_names}
    try:
        sys.modules["providers"] = providers_module
        sys.modules["providers.base"] = base_module
        spec = importlib.util.spec_from_file_location(
            module_name,
            PLUGIN_PATH,
            submodule_search_locations=[str(REPOSITORY_ROOT)],
        )
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
    finally:
        for name, previous_module in previous_modules.items():
            if previous_module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = previous_module
        for name in tuple(sys.modules):
            if name.startswith(f"{module_name}."):
                sys.modules.pop(name, None)

    if len(registered) != 1:
        raise AssertionError(f"expected one registered profile, got {len(registered)}")
    return registered[0]


class ChutesDirectoryPluginTests(unittest.TestCase):
    def test_release_version_is_consistent(self) -> None:
        self.assertIn(
            f'__version__ = "{RELEASE_VERSION}"',
            PACKAGE_PATH.read_text(encoding="utf-8"),
        )
        self.assertIn(
            f'version = "{RELEASE_VERSION}"',
            PYPROJECT_PATH.read_text(encoding="utf-8"),
        )
        self.assertIn(
            f"version: {RELEASE_VERSION}",
            MANIFEST_PATH.read_text(encoding="utf-8"),
        )
        self.assertIn(
            f"## [{RELEASE_VERSION}]",
            CHANGELOG_PATH.read_text(encoding="utf-8"),
        )

    def test_registers_the_chutes_profile(self) -> None:
        profile = load_directory_plugin()

        self.assertEqual(profile.name, "chutes")
        self.assertEqual(profile.aliases, ("chutes-ai", "chutesai"))
        self.assertEqual(profile.api_mode, "chat_completions")
        self.assertEqual(profile.auth_type, "api_key")
        self.assertEqual(profile.base_url, "https://llm.chutes.ai/v1")
        self.assertEqual(
            profile.fallback_models,
            ("default:latency", "default:throughput"),
        )
        self.assertEqual(profile.default_aux_model, "")
        self.assertIs(profile.use_live_model_metadata, True)
        self.assertIs(profile.__dict__.get("use_live_model_metadata"), True)
        self.assertEqual(
            profile.env_vars, ("CHUTES_API_KEY", "CHUTES_BASE_URL")
        )

    def test_catalog_setup_failure_returns_none(self) -> None:
        profile = load_directory_plugin()

        self.assertIsNone(profile.fetch_models(base_url="://invalid"))

    def test_live_catalog_only_returns_tool_capable_models(self) -> None:
        profile = load_directory_plugin()
        payload = b'''{
            "data": [
                {"id": "tool-model", "supported_features": ["tools", "reasoning"]},
                {"id": "chat-only-model", "supported_features": ["reasoning"]},
                {"id": "unknown-model"},
                {"id": "null-features", "supported_features": null},
                {"id": 123, "supported_features": ["tools"]},
                {"supported_features": ["tools"]}
            ]
        }'''
        requests = []

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return None

            def read(self) -> bytes:
                return payload

        def open_credentialed_url(request, timeout):
            requests.append((request, timeout))
            return Response()

        hermes_cli_module = types.ModuleType("hermes_cli")
        hermes_cli_module.__path__ = []
        security_module = types.ModuleType("hermes_cli.urllib_security")
        security_module.open_credentialed_url = open_credentialed_url
        module_names = ("hermes_cli", "hermes_cli.urllib_security")
        previous_modules = {name: sys.modules.get(name) for name in module_names}
        try:
            sys.modules["hermes_cli"] = hermes_cli_module
            sys.modules["hermes_cli.urllib_security"] = security_module
            metadata = profile.fetch_model_metadata(
                api_key="cpk_test-key",
                base_url="https://chutes.test/v1",
            )
            models = profile.fetch_models(
                api_key="cpk_test-key",
                base_url="https://chutes.test/v1",
            )
        finally:
            for name, previous_module in previous_modules.items():
                if previous_module is None:
                    sys.modules.pop(name, None)
                else:
                    sys.modules[name] = previous_module

        self.assertEqual(
            metadata,
            [
                {
                    "id": "tool-model",
                    "supported_features": ["tools", "reasoning"],
                }
            ],
        )
        self.assertEqual(models, ["tool-model"])
        self.assertEqual(len(requests), 2)
        request, timeout = requests[0]
        self.assertEqual(request.full_url, "https://chutes.test/v1/models")
        self.assertEqual(request.get_header("Authorization"), "Bearer cpk_test-key")
        self.assertEqual(timeout, 8.0)

    def test_readme_documents_current_and_future_install_paths(self) -> None:
        if not README_PATH.is_file():
            self.fail(f"missing README: {README_PATH}")

        readme = README_PATH.read_text(encoding="utf-8")
        self.assertIn("plugins/model-providers/chutes", readme)
        self.assertIn("NousResearch/hermes-agent#64277", readme)
        self.assertIn("hermes plugins install", readme)
        self.assertIn("hermes_agent.model_providers", readme)
        self.assertIn("default:latency", readme)
        self.assertIn("https://llm.chutes.ai/v1/models", readme)
        self.assertNotIn("deepseek-ai/DeepSeek-V3.2-TEE", readme)
        self.assertNotIn("??", readme)
        self.assertIn("Use the canonical `chutes` name", readme)
        self.assertIn("tool calling", readme)
        self.assertIn("model.context_length", readme)
        self.assertIn("https://github.com/Veightor/chutes-agent-toolkit", readme)
        self.assertNotIn("https://github.com/chutesai/chutes-agent-toolkit", readme)

    def test_ci_runs_the_offline_contract_suite(self) -> None:
        if not CI_WORKFLOW_PATH.is_file():
            self.fail(f"missing CI workflow: {CI_WORKFLOW_PATH}")

        workflow = CI_WORKFLOW_PATH.read_text(encoding="utf-8")
        self.assertIn("python -m unittest discover -s tests -v", workflow)
        self.assertIn("NousResearch/hermes-agent", workflow)
        self.assertIn("46e87b14fd6c943ef0d6671fb0d74c5dde5d4c6b", workflow)
        self.assertIn("HERMES_SOURCE", workflow)
        self.assertIn("python -m pip wheel . --no-deps", workflow)
        self.assertNotIn("CHUTES_API_KEY", workflow)


if __name__ == "__main__":
    unittest.main()
