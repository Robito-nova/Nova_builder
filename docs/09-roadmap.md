# NOVA Builder Roadmap

## Implemented Prototype

- Architecture, manifest/package drafts, and versioned JSON Schema.
- Arch/Debian/Windows target detection and validation for x86_64, with Windows version kept separate from package target.
- Python and C native-host adapters.
- SHA-256 checked `.nova` packaging and explicit-trust Runtime launch path.
- Basic Python/Tk desktop shell and command-line project/build/package commands.

## Remaining Before 1.0

- OS-level sandboxing and enforced permissions.
- Publisher signatures and key management.
- Isolated dependency resolver and lock format.
- Complete Windows 10/11 and Arch/Debian CI evidence.
- Installer, updater, cancellation, diagnostics/editor integration, and accessibility review.
- Low-resource performance measurements on the reference laptop.
- Security review, dependency license inventory, and user documentation.

The authoritative acceptance list is [docs/11-v1-release.md](11-v1-release.md). Do not advertise a feature as supported until its release gate has been executed on the relevant targets.
