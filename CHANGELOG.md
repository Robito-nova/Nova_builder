# Changelog

## 0.1.0a1 - 2026-11-11

Initial alpha prototype. This is not a NOVA Builder 1.0 release.

- Added Python and native C build adapters for x86_64 host builds.
- Added Arch Linux, Debian Linux, Windows 10, and Windows 11 target identification.
- Added manifest 1.0 JSON Schema validation.
- Added `.nova` packaging with SHA-256 integrity metadata and archive safety checks.
- Added GUI file import and a package-format selector for available `.nova`, Linux `.deb`, and Linux `.run` outputs; unavailable formats explain their requirements.
- Added native Debian package and Linux self-extracting `.run` backends. Windows `.exe` is limited to native C builds on Windows; Apple outputs remain disabled.
- Added explicit-trust Runtime launch flow, CLI, project templates, and basic Tk desktop UI.
- Added local integration tests and cross-platform CI workflow definitions.

Known release blockers are listed in [docs/11-v1-release.md](docs/11-v1-release.md).
