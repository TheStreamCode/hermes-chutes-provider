"""Offline behavior of the provider-owned live context hook."""

import unittest
from unittest.mock import patch

from test_plugin_profile import load_directory_plugin


class LiveContextTests(unittest.TestCase):
    def test_cache_is_scoped_to_endpoint_and_credential_even_with_models_url(self):
        profile = load_directory_plugin()
        profile.models_url = "https://catalog.chutes.test/models"
        rows = (
            ("https://one.test/v1", "fixture-one", 32768),
            ("https://two.test/v1", "fixture-one", 65536),
            ("https://one.test/v1", "fixture-two", 131072),
        )
        for url, key, window in rows:
            with patch.object(profile, "fetch_model_metadata", return_value=[
                {"id": "tool-model", "context_length": window},
            ]) as fetch:
                self.assertEqual(profile.live_context_length(
                    "tool-model", base_url=url, api_key=key,
                ), window)
                fetch.assert_called_once_with(api_key=key, base_url=url)
        with patch.object(profile, "fetch_model_metadata") as fetch:
            self.assertEqual(profile.live_context_length(
                "tool-model", base_url=rows[0][0], api_key=rows[0][1],
            ), rows[0][2])
            fetch.assert_not_called()

    def test_failed_probe_is_cached_and_retried_after_ttl(self):
        profile = load_directory_plugin()
        with patch("time.monotonic", return_value=0), patch.object(
            profile, "fetch_model_metadata", return_value=None,
        ) as fetch:
            self.assertIsNone(profile.live_context_length("tool-model"))
            self.assertIsNone(profile.live_context_length("tool-model"))
            fetch.assert_called_once()
        with patch("time.monotonic", return_value=301), patch.object(
            profile, "fetch_model_metadata", return_value=[
                {"id": "tool-model", "context_length": 32768},
            ],
        ) as fetch:
            self.assertEqual(profile.live_context_length("tool-model"), 32768)
            fetch.assert_called_once()

    def test_outage_keeps_only_the_same_catalogs_last_known_window(self):
        profile = load_directory_plugin()
        with patch("time.monotonic", return_value=0), patch.object(
            profile, "fetch_model_metadata", return_value=[
                {"id": "tool-model", "context_length": 32768},
            ],
        ):
            self.assertEqual(profile.live_context_length("tool-model"), 32768)
        with patch("time.monotonic", return_value=301), patch.object(
            profile, "fetch_model_metadata", return_value=None,
        ):
            self.assertEqual(profile.live_context_length("tool-model"), 32768)
            self.assertIsNone(profile.live_context_length("tool-model", api_key="other-fixture"))

    def test_window_requires_an_exact_id_and_positive_integer(self):
        for window in (None, 0, -1, True, "32768", 32768):
            with self.subTest(window=window):
                profile = load_directory_plugin()
                with patch.object(profile, "fetch_model_metadata", return_value=[
                    {"id": "tool-model", "context_length": window},
                ]):
                    self.assertIsNone(profile.live_context_length("tool-model-large"))
                    self.assertEqual(profile.live_context_length("tool-model"),
                                     32768 if type(window) is int and window > 0 else None)

    def test_successful_empty_catalog_does_not_reuse_removed_models(self):
        profile = load_directory_plugin()
        with patch("time.monotonic", return_value=0), patch.object(
            profile, "fetch_model_metadata", return_value=[
                {"id": "tool-model", "context_length": 32768},
            ],
        ):
            self.assertEqual(profile.live_context_length("tool-model"), 32768)
        with patch("time.monotonic", return_value=301), patch.object(
            profile, "fetch_model_metadata", return_value=[],
        ):
            self.assertIsNone(profile.live_context_length("tool-model"))
