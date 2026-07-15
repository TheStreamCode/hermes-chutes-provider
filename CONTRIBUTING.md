# Contributing

Contributions should keep this repository focused on the standalone Chutes model
provider for Hermes Agent.

## Guidelines

- Keep Chutes-specific code outside the Hermes core tree.
- Preserve the generic OpenAI-compatible transport and provider contracts.
- Do not commit API keys, credentials, catalog snapshots, or generated secrets.
- Verify provider and model claims against current authoritative Chutes sources.
- Add or update focused regression tests for behavior changes.

## Validation

Run the offline test suite before opening a pull request:

```bash
python -m unittest discover -s tests -v
```

Changes to packaging should also build a wheel successfully:

```bash
python -m pip wheel . --no-deps
```

## Pull Requests

Explain the behavior changed, the files affected, how the change was validated,
and whether it changes compatibility with Hermes Agent or Chutes.
