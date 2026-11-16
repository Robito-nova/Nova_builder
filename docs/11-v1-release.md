# NOVA Builder 1.0 Release Gates

This document is the acceptance checklist for a real 1.0 release. A checked-in prototype feature is not considered production-ready until its release gate has been verified on the supported systems.

## Fixed 1.0 Scope

- Host/package targets: Arch Linux x86_64, Debian Linux x86_64, and Windows 10+ x86_64 (`windows-x86_64`). Windows Server runner variants are detected for CI but do not change the package target.
- Languages: Python and C.
- Apple platforms: unsupported and rejected by the manifest schema.
- Package: ZIP-based `.nova`, launched by a separate NOVA Runtime. The package is not a native executable.

## Implemented in This Prototype

- [x] Versioned `nova-1.0.schema.json` with JSON Schema Draft 2020-12 validation.
- [x] Target and manifest cross-field checks.
- [x] Host detection for Arch, Debian, and Windows 10/11.
- [x] Python syntax compilation and C compiler subprocess with timeout and captured output.
- [x] `.nova` packaging with SHA-256 checksums, CRC verification, duplicate/path/symlink/size/compression checks.
- [x] Runtime extraction into a temporary directory, no shell execution, and explicit trust opt-in.
- [x] Basic Tk desktop shell and CLI.
- [x] CI workflow definitions for Debian/Ubuntu, Arch container, and Windows.

## Required Before Calling It 1.0

- [ ] Execute CI successfully on all three environments; a workflow file alone is not proof of compatibility.
- [ ] Add OS-level sandboxing. `trusted=True` is an explicit user decision, not a sandbox; untrusted code currently runs with the user's account permissions after consent.
- [ ] Define and implement publisher signatures and key rotation. SHA-256 detects accidental or post-build changes but does not establish publisher identity.
- [ ] Define dependency lock format and reproducible, isolated dependency installation; currently Python dependencies must already be importable in the build interpreter.
- [ ] Verify and package Windows C toolchains, executable metadata, and Windows runtime behavior on real Windows 10 and 11 hosts.
- [ ] Make Python package runtime requirements explicit and test on clean installations.
- [ ] Implement platform-specific installer/uninstaller and upgrade behavior, or explicitly exclude system installation from 1.0.
- [ ] Add malformed-archive, path traversal, symlink, oversized archive, checksum, and runtime permission tests.
- [ ] Measure startup time, idle RAM/CPU, and build resource usage on the reference ASUS X550CA profile.
- [ ] Review accessibility, keyboard navigation, error recovery, and packaging UX in the desktop interface.
- [ ] Publish user, developer, manifest, and package format documentation with a compatibility policy.
- [ ] Audit dependency licenses and provide notices/source obligations for distributed dependencies.
- [ ] Tag a release only after the above gates are closed and source/archive artifacts can be reproduced.

## Current Limitations

- C builds are native-host builds only; cross-compilation is intentionally rejected.
- Python build verifies syntax and stages project sources, but does not bundle the Python interpreter.
- Package trust is not publisher-signature verification.
- Runtime does not enforce declared filesystem, network, or hardware permissions at the OS level.
- UI terminal commands are launched directly without a shell; shell syntax, pipelines, and interactive sessions are not supported.
- Installer/update flows and low-resource performance results are not implemented.

## Release Process

1. Run the full test suite and CI on Arch, Debian, Windows 10, and Windows 11.
2. Build clean Python and C sample packages on each supported target.
3. Verify package checksums and runtime behavior on clean target machines.
4. Review the changelog, manifest compatibility, license notices, and dependency inventory.
5. Create a versioned source release and publish matching `.nova`/builder artifacts and checksums.
