# NOVA Builder

NOVA Builder is a lightweight, modular application development and packaging platform. This repository is an alpha prototype moving toward 1.0; it is not yet a production-ready 1.0 release.

## License

Copyright (C) 2026 Robin Güneş

NOVA Builder is licensed by Robin Güneş under the GNU General Public License version 3 only (`GPL-3.0-only`). See [LICENSE](LICENSE) for the complete license text.

## 1.0 Scope

- Implemented language adapters: Python and C.
- Supported targets: Arch Linux x86_64, Debian Linux x86_64, and Windows 10+ x86_64 (`windows-x86_64`). Host Windows version is reported separately from the package target.
- Apple platforms are explicitly unsupported.
- `.nova` is a validated ZIP-based application package for NOVA Runtime. It is not itself a native `.exe` or ELF executable.

## Implemented Prototype Features

- Versioned JSON Schema 2020-12 validation for `nova.json`.
- Host platform and distribution detection.
- Python byte-compilation and native C compiler invocation.
- `.nova` creation with SHA-256 metadata, CRC verification, safe path checks, and archive size limits.
- GUI package selector with file import and native `.nova`, Linux `.deb`, and Linux `.run` outputs; Windows native C `.exe` is host-dependent.
- Debian desktop package with a launcher in the application menu and a custom NOVA Builder icon.
- Runtime package extraction and process launch after explicit trust approval.
- Basic Python/Tk desktop interface and command-line interface.

## Not Yet 1.0-Ready

Operating-system sandboxing, signed publisher identities, isolated dependency resolution, full Windows/Arch CI results, installer/update behavior, and measured low-resource performance remain release gates. See [docs/11-v1-release.md](docs/11-v1-release.md). The GUI lists requested formats but disables formats that cannot be produced on the current system; see [the format matrix](docs/12-format-matrix.md).

Current preview changes are recorded in [CHANGELOG.md](CHANGELOG.md).

## Setup

Requires Python 3.12 or newer. A C compiler is required for C projects. The desktop interface also requires Tk support.

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest discover -s tests -p 'test_*.py' -v
```

On Windows PowerShell, activate with `.venv\\Scripts\\Activate.ps1`.

## Commands

```bash
python -m nova_builder validate examples/sample_app/nova.json
python -m nova_builder build examples/sample_app
python -m nova_builder package examples/sample_app dist/NovaSampleApp.nova
python -m nova_builder verify dist/NovaSampleApp.nova
python -m nova_builder run dist/NovaSampleApp.nova
python -m nova_builder ui
```

`run` inspects by default. To execute a package after reviewing its publisher and permissions, pass `--trust` explicitly.

## Debian Desktop Package

The current Debian x86_64 preview installer is [Nova-Builder_0.1.0_amd64.deb](releases/Nova-Builder_0.1.0_amd64.deb); verify it with [SHA256SUMS](releases/SHA256SUMS). Install the downloaded package with:

```bash
sudo apt install ./Nova-Builder_0.1.0_amd64.deb
```

NOVA Builder then appears in the desktop application menu as **NOVA Builder**. It can also be started from a terminal with `nova-builder`.
