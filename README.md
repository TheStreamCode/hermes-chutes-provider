# Hermes Chutes Provider

Standalone Chutes model provider plugin for Hermes Agent

[![CI](https://github.com/TheStreamCode/hermes-chutes-provider/actions/workflows/ci.yml/badge.svg)](https://github.com/TheStreamCode/hermes-chutes-provider/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Release](https://img.shields.io/github/v/release/TheStreamCode/hermes-chutes-provider)](https://github.com/TheStreamCode/hermes-chutes-provider/releases/latest)

Chutes exposes an OpenAI-compatible API at `https://llm.chutes.ai/v1`. This plugin declares a
Chutes provider profile for [Hermes Agent](https://github.com/NousResearch/hermes-agent) through
the existing user model-provider discovery path, so Chutes-specific maintenance stays outside the
Hermes core tree. It is an independent, unofficial integration, not affiliated with, endorsed by,
sponsored by, or approved by Chutes Global Corp or Nous Research.

## Project status

| Area | Current status |
| --- | --- |
| Stable release | [`v0.1.5`](https://github.com/TheStreamCode/hermes-chutes-provider/releases/tag/v0.1.5) |
| Supported installation | Manual directory install from the released tag |
| Native Hermes install | Pending upstream standalone-plugin support in [Hermes PR #64277](https://github.com/NousResearch/hermes-agent/pull/64277) |
| Python | 3.11 or newer |
| Distribution | GitHub Releases only; not published to PyPI |

## Install

### Manual directory install

Clone the latest released snapshot into the active Hermes profile:

```bash
export HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
mkdir -p "$HERMES_HOME/plugins/model-providers"
git clone --branch v0.1.5 --depth 1 \
  https://github.com/TheStreamCode/hermes-chutes-provider.git \
  "$HERMES_HOME/plugins/model-providers/chutes"
```

On PowerShell:

```powershell
$hermesHome = if ($env:HERMES_HOME) { $env:HERMES_HOME } else { Join-Path $HOME ".hermes" }
$target = Join-Path $hermesHome "plugins\model-providers\chutes"
New-Item -ItemType Directory -Force (Split-Path -Parent $target)
git clone --branch v0.1.5 --depth 1 https://github.com/TheStreamCode/hermes-chutes-provider.git $target
```

#### Development checkout

To test unreleased changes, clone `main` instead by omitting `--branch` and `--depth`. Treat that
checkout as development code rather than a published release.

### Native Git and pip installs

The eventual native command will be:

```bash
hermes plugins install TheStreamCode/hermes-chutes-provider
```

The package also declares the `hermes_agent.model_providers` entry point for pip installation.
These routes depend on standalone distribution support from
[NousResearch/hermes-agent#64277](https://github.com/NousResearch/hermes-agent/pull/64277). Until
that change is merged and included in a Hermes release verified by this repository, use the manual
directory install above.

## Quick start

1. Add the key to `$HERMES_HOME/.env`:

   ```dotenv
   CHUTES_API_KEY=cpk_...
   # Optional endpoint override:
   # CHUTES_BASE_URL=https://llm.chutes.ai/v1
   ```

2. Select the provider in `$HERMES_HOME/config.yaml`:

   ```yaml
   model:
     provider: chutes
     default: default:latency
   ```

3. Start a new Hermes process and run `hermes doctor`. The Provider Connectivity section should
   list Chutes. The provider registry resolves `chutes-ai` and `chutesai` as aliases for
   authentication and runtime configuration. Use the canonical `chutes` name in `provider:model`
   picker input and in new configuration.

## Features

- Declares a declarative Chutes provider profile; Hermes' existing Generic OpenAI-compatible transport performs the requests, so the plugin adds no custom transport.
- Discovers current tool-capable models from the live Chutes catalog and falls back to Chutes'
  routing aliases when that catalog cannot be reached.
- Supplies no static concrete model or auxiliary model, so Hermes never silently routes requests
  to retired model IDs.
- Keeps the stable `chutes` provider identity with the `chutes-ai` and `chutesai` aliases.
- Installs as a user-directory plugin without patching Hermes Agent.
- Declares no runtime dependencies; Python 3.11 or newer.

## Models

`default:latency` is Chutes' routing alias for interactive use. Use `default:throughput` for
long-running or background work, or select a concrete model returned by the live
[`https://llm.chutes.ai/v1/models`](https://llm.chutes.ai/v1/models) catalog.

The live catalog is the source of truth for availability, capabilities, and pricing. The picker
keeps the two routing aliases and includes only live models that advertise tool calling. If the
catalog is unavailable, the routing aliases remain selectable; restore network access before
choosing a concrete model instead of relying on a stale local list.

Hermes builds without provider live-metadata support discover model IDs but may not import their
context limits. When selecting a concrete model, copy its live `context_length` value to
`model.context_length` in the Hermes configuration. Routing aliases do not have one fixed context
window because their target can change between requests.

## Requirements

- A Hermes Agent installation with model-provider plugin discovery.
- A Chutes API key from [chutes.ai/app/api](https://chutes.ai/app/api).
- Python 3.11 or newer; CI covers 3.11, 3.12, 3.13, and 3.14.
- Network access to `https://llm.chutes.ai/v1` for inference and catalog discovery.

## Configuration

| Variable | Required | Default | Purpose |
| --- | --- | --- | --- |
| `CHUTES_API_KEY` | yes | none | Bearer credential for inference and catalog requests |
| `CHUTES_BASE_URL` | no | `https://llm.chutes.ai/v1` | Overrides the OpenAI-compatible endpoint |
| `model.provider` | yes | none | Set to `chutes` in the Hermes configuration |

The key belongs in the Hermes profile's ignored environment file. This repository never reads it
from its own tree and never writes it anywhere.

## Privacy and security

The provider holds no credentials of its own: it reads `CHUTES_API_KEY` from the Hermes profile
and passes it to the transport, and no test may call paid inference or use a real key. Outbound
requests go through Hermes' `open_credentialed_url`, which applies the host's URL safety checks.
Do not paste API keys, prompts, or account data into issues. See [SECURITY.md](SECURITY.md) for
private reporting.

## Troubleshooting

### Model picker shows only routing aliases

The live catalog at `https://llm.chutes.ai/v1/models` could not be reached, so only the
`default:latency` routing aliases are offered. Check network access to `llm.chutes.ai`, verify
`CHUTES_BASE_URL` if overridden, then reload the picker. Concrete model IDs return once the
catalog loads.

### 401 Unauthorized on inference or catalog requests

The `CHUTES_API_KEY` is missing, expired, or revoked. Generate a new key, update the active Hermes
profile's environment configuration, and retry. The provider never logs or persists the key, so
there is nothing to scrub from local state; replace it.

### Gateway keeps serving the old provider profile

After upgrading or rotating credentials, restart the Hermes gateway so it re-discovers the
installed provider profile instead of serving the cached one. Then re-run the picker to confirm the
new version and models appear.

## Development

Run the offline contract tests without a Hermes installation or API key:

```bash
python -m unittest discover -s tests -v
```

The integration test is skipped unless `HERMES_SOURCE` points at a Hermes Agent checkout with its
dependencies installed:

```bash
HERMES_SOURCE=/path/to/hermes-agent python -m unittest discover -s tests -v
```

Build the wheel the same way CI does:

```bash
python -m pip wheel . --no-deps
```

No test may call paid inference or use a real API key. CI pins the Hermes revision it tests
against, so a Hermes-side change never silently turns the integration contract red. Version bumps
must keep `pyproject.toml`, `plugin.yaml`, `CITATION.cff`, `CHANGELOG.md`, and the install tag
above in sync; `test_release_metadata_is_consistent` enforces it.

## Support

See [SUPPORT.md](SUPPORT.md), [Issues](https://github.com/TheStreamCode/hermes-chutes-provider/issues),
and GitHub Discussions. For Chutes skills, setup recipes, model guidance, and platform
documentation, see [Veightor/chutes-agent-toolkit](https://github.com/Veightor/chutes-agent-toolkit).
Support for Hermes Agent itself belongs to the Hermes project, not to this plugin.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for the change and validation workflow,
[SECURITY.md](SECURITY.md) for private vulnerability reporting, and
[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for participation expectations. Pull requests must pass
the required CI checks.

## License

Project-owned code and documentation are licensed under the [MIT License](LICENSE). Third-party
names, services, and trademarks remain the property of their respective owners; see
[NOTICE](NOTICE).

---

Maintained by [Michael Gasperini (Mikesoft)](https://mikesoft.it).
If this project is useful to you, consider
[sponsoring its maintenance](https://github.com/sponsors/TheStreamCode).
