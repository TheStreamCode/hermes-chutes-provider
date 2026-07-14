# Changelog

All notable changes to this project are documented in this file.

## [0.1.2] - 2026-07-14

### Changed

- Filter the live Chutes catalog to models that advertise tool calling.
- Keep Chutes' `default:latency` and `default:throughput` routing aliases in the
  Hermes model picker without pinning concrete model IDs.
- Opt in to authoritative live context metadata on compatible Hermes builds.
- Test against a pinned Hermes checkout and build the package in CI.
- Correct provider-alias guidance and support Windows PowerShell 5.1 installs.

## [0.1.1] - 2026-07-14

### Changed

- Point Chutes tooling documentation to the maintained Veightor toolkit.

## [0.1.0] - 2026-07-14

### Added

- Standalone Hermes model-provider profile for Chutes.
- User-directory plugin entry point for `chutes`, `chutes-ai`, and `chutesai`.
- Live Chutes model catalog and routing aliases, without static model defaults.
- Offline profile-contract and opt-in Hermes integration tests.
- Manual-install documentation while native standalone distribution support is pending Hermes #64277.
