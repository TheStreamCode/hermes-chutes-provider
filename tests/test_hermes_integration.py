"""Integration contract against a local Hermes Agent checkout."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
HERMES_SOURCE = os.environ.get("HERMES_SOURCE", "")
HERMES_PYTHON = os.environ.get("HERMES_PYTHON", sys.executable)


@unittest.skipUnless(HERMES_SOURCE, "set HERMES_SOURCE to run Hermes integration tests")
class HermesIntegrationTests(unittest.TestCase):
    def test_user_directory_plugin_registers_profile_and_aliases(self) -> None:
        hermes_source = Path(HERMES_SOURCE).resolve()
        self.assertTrue((hermes_source / "providers" / "__init__.py").is_file())

        with tempfile.TemporaryDirectory() as temporary_directory:
            hermes_home = Path(temporary_directory) / "hermes-home"
            target = hermes_home / "plugins" / "model-providers" / "chutes"
            target.parent.mkdir(parents=True)
            shutil.copytree(
                REPOSITORY_ROOT,
                target,
                ignore=shutil.ignore_patterns(".git", "__pycache__", ".venv"),
            )

            environment = os.environ.copy()
            environment["HERMES_HOME"] = str(hermes_home)
            environment["PYTHONPATH"] = str(hermes_source)
            environment["CHUTES_API_KEY"] = "cpk_test-key"
            environment["CHUTES_BASE_URL"] = "https://chutes.test/v1"

            program = """
from providers import get_provider_profile

profile = get_provider_profile("chutes")
assert profile is not None
assert profile.name == "chutes"
assert get_provider_profile("chutes-ai") is profile
assert get_provider_profile("chutesai") is profile
assert profile.base_url == "https://llm.chutes.ai/v1"
assert profile.env_vars == ("CHUTES_API_KEY", "CHUTES_BASE_URL")

from hermes_cli.auth import PROVIDER_REGISTRY, resolve_provider
assert "chutes" in PROVIDER_REGISTRY
assert resolve_provider("chutes-ai") == "chutes"
assert resolve_provider("chutesai") == "chutes"

from hermes_cli.models import CANONICAL_PROVIDERS
assert any(entry.slug == "chutes" for entry in CANONICAL_PROVIDERS)

from hermes_cli.runtime_provider import resolve_runtime_provider
runtime = resolve_runtime_provider(requested="chutes")
assert runtime["provider"] == "chutes"
assert runtime["api_key"] == "cpk_test-key"
assert runtime["base_url"] == "https://chutes.test/v1"

from hermes_cli.doctor import _build_apikey_providers_list
rows = [row for row in _build_apikey_providers_list() if row[0] == "Chutes"]
assert len(rows) == 1
assert rows[0][1] == ("CHUTES_API_KEY",)
assert rows[0][2] == "https://llm.chutes.ai/v1/models"
assert rows[0][3] == "CHUTES_BASE_URL"
"""
            result = subprocess.run(
                [HERMES_PYTHON, "-c", program],
                cwd=hermes_source,
                env=environment,
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
