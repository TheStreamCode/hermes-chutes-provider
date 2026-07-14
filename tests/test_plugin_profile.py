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


class ProviderProfile:
    """Minimal stand-in for Hermes' ProviderProfile at the import boundary."""

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
    def test_registers_the_chutes_profile(self) -> None:
        profile = load_directory_plugin()

        self.assertEqual(profile.name, "chutes")
        self.assertEqual(profile.aliases, ("chutes-ai", "chutesai"))
        self.assertEqual(profile.api_mode, "chat_completions")
        self.assertEqual(profile.auth_type, "api_key")
        self.assertEqual(profile.base_url, "https://llm.chutes.ai/v1")
        self.assertEqual(
            profile.env_vars, ("CHUTES_API_KEY", "CHUTES_BASE_URL")
        )

    def test_readme_documents_current_and_future_install_paths(self) -> None:
        if not README_PATH.is_file():
            self.fail(f"missing README: {README_PATH}")

        readme = README_PATH.read_text(encoding="utf-8")
        self.assertIn("plugins/model-providers/chutes", readme)
        self.assertIn("NousResearch/hermes-agent#64277", readme)
        self.assertIn("hermes plugins install", readme)
        self.assertIn("hermes_agent.model_providers", readme)

    def test_ci_runs_the_offline_contract_suite(self) -> None:
        if not CI_WORKFLOW_PATH.is_file():
            self.fail(f"missing CI workflow: {CI_WORKFLOW_PATH}")

        workflow = CI_WORKFLOW_PATH.read_text(encoding="utf-8")
        self.assertIn("python -m unittest discover -s tests -v", workflow)
        self.assertNotIn("CHUTES_API_KEY", workflow)


if __name__ == "__main__":
    unittest.main()
