# Hermes Chutes Provider

Standalone [Hermes Agent](https://github.com/NousResearch/hermes-agent)
model-provider plugin for [Chutes](https://chutes.ai). Chutes exposes an
OpenAI-compatible API at `https://llm.chutes.ai/v1`.

This repository intentionally stays outside the Hermes core tree. It uses
Hermes' user model-provider discovery path, so Chutes-specific maintenance does
not need an upstream Hermes source change.

This is an independent, unofficial integration. It is not affiliated with,
endorsed by, sponsored by, or approved by Chutes Global Corp or Nous Research.

## Requirements

- A Hermes Agent installation with model-provider plugin discovery.
- A Chutes API key from [chutes.ai/app/api](https://chutes.ai/app/api).

## Install

### Manual directory install

Clone this repository into the active Hermes profile:

```bash
export HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
mkdir -p "$HERMES_HOME/plugins/model-providers"
git clone https://github.com/TheStreamCode/hermes-chutes-provider.git \
  "$HERMES_HOME/plugins/model-providers/chutes"
```

On PowerShell:

```powershell
$hermesHome = if ($env:HERMES_HOME) { $env:HERMES_HOME } else { Join-Path $HOME ".hermes" }
$target = Join-Path $hermesHome "plugins\model-providers\chutes"
New-Item -ItemType Directory -Force (Split-Path -Parent $target)
git clone https://github.com/TheStreamCode/hermes-chutes-provider.git $target
```

Add the key to `$HERMES_HOME/.env`:

```dotenv
CHUTES_API_KEY=cpk_...
# Optional endpoint override:
# CHUTES_BASE_URL=https://llm.chutes.ai/v1
```

Then select the provider in `$HERMES_HOME/config.yaml`:

```yaml
model:
  provider: chutes
  default: default:latency
```

Start a new Hermes process and run:

```bash
hermes doctor
```

The Provider Connectivity section should list Chutes. The provider registry
resolves `chutes-ai` and `chutesai` as aliases for authentication and runtime
configuration. Use the canonical `chutes` name in `provider:model` picker input
and new configuration.

### Native Git and pip installs

The eventual native command will be:

```bash
hermes plugins install TheStreamCode/hermes-chutes-provider
```

The package also declares the `hermes_agent.model_providers` entry point for
pip installation. These routes depend on standalone distribution support from
[NousResearch/hermes-agent#64277](https://github.com/NousResearch/hermes-agent/pull/64277).
Until that change is merged and included in a Hermes release verified by this
repository, use the manual directory install above.

## Models

`default:latency` is Chutes' routing alias for interactive use. Use
`default:throughput` for long-running or background work, or select a concrete
model returned by the live
[`https://llm.chutes.ai/v1/models`](https://llm.chutes.ai/v1/models) catalog.

The live catalog is the source of truth for availability, capabilities, and
pricing. The picker keeps the two routing aliases above and includes only live
models that advertise tool calling. This provider intentionally supplies no
static concrete model or auxiliary model, so Hermes does not silently route
requests to retired model IDs. If the catalog is unavailable, the routing
aliases remain selectable; restore network access before choosing a concrete
model instead of relying on a stale local list.

Hermes builds without provider live-metadata support discover model IDs but may
not import their context limits. When selecting a concrete model, copy its live
`context_length` value to `model.context_length` in the Hermes configuration.
Routing aliases do not have one fixed context window because their target can
change between requests.

## Scope

This plugin declares metadata for Hermes' existing generic OpenAI-compatible
transport and provider-discovery systems. It does not modify Hermes Agent, add
a custom transport, or include Chutes API keys.

For Chutes skills, setup recipes, model guidance, and platform documentation,
see [Veightor/chutes-agent-toolkit](https://github.com/Veightor/chutes-agent-toolkit).

## Development

Run the offline contract tests without a Hermes installation or API key:

```bash
python -m unittest discover -s tests -v
```

## License

Project-owned code and documentation are licensed under the [MIT License](LICENSE).
Third-party names, services, and trademarks remain the property of their respective
owners; see [NOTICE](NOTICE).
