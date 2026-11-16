# GUI Package Format Matrix

The desktop package dialog exposes the requested formats and reports availability for the current host and project. A visible format does not imply a working backend; unavailable choices stay disabled and explain why.

| Format | Prototype status | Requirements / notes |
| --- | --- | --- |
| `.nova` | Available | Uses NOVA build, manifest, checksum, and package validation. Runs with the separate NOVA Runtime. |
| `.deb` | Available on Debian x86_64 when `dpkg-deb` is installed and the manifest target is Debian | Produces an amd64 Debian package with a launcher and project payload. |
| `.run` | Available when the project target matches the current native Linux host | Self-extracting shell installer for the project payload; it is not an OS sandbox or a native executable. |
| `.exe` | Conditional | Windows host only, native C project only, and compiler/toolchain must be installed. No cross-compilation. |
| `.pkg` | Disabled | Apple platforms are outside the supported platform policy. |
| `.app` | Disabled | Apple application bundles are outside the supported platform policy. |
| `.flatpak` | Disabled | Flatpak manifest and bundle backend are not implemented. |
| `.jar` | Disabled | Java build adapter is not implemented. |
| `.AppImage` | Disabled | AppImage backend and runtime integration are not implemented. |

## Importing Project Files

Use **Import Files** in the Builder toolbar to select files. They are copied into `assets/imported/` in the open project and become package inputs. The project still needs a valid `nova.json` and a supported launcher/build configuration.

## Runtime and Safety

- `.deb` and `.run` package formats do not imply sandboxing. Installed code runs with the invoking user's permissions.
- `.run` extracts the payload to the selected destination (default: `~/.local/opt/<package-name>`).
- `.nova` execution remains a separate NOVA Runtime operation and requires explicit trust.
- Apple outputs remain unavailable even if a macOS packaging tool is installed.
