# NOVA Package Format 1.0

`.nova` is a ZIP-based application package interpreted by the separate NOVA Runtime. It is not a native Windows `.exe` or Linux ELF binary. The Runtime validates and extracts the package, then starts the manifest launcher using the declared language runtime.

## Archive Layout

```text
Example.nova
├── nova.json
├── src/                    # optional application source
├── assets/                 # optional user-facing assets
├── resources/              # optional runtime resources
├── bin/                    # native application launchers, when applicable
└── metadata/
    └── checksums.json      # SHA-256 digest for every other file
```

The manifest must be at the archive root. The path in `package.launcher` must identify a file in the archive. Python apps can point at their source entry point; native apps should include the compiled artifact.

## Integrity and Validation

The package builder writes deterministic ZIP entries and SHA-256 digests. The validator checks ZIP CRCs, duplicate names, path traversal, absolute paths, backslashes, symlinks, per-file and total size limits, compression ratios, manifest schema, launcher presence, and digest equality.

SHA-256 detects file changes relative to the included metadata, but the metadata is not signed. It does not prove who published the package. Publisher signatures and key management remain a 1.0 release blocker.

## Runtime Behavior

Runtime inspection does not execute the package. Execution requires explicit caller consent (`trusted=True` in the API or `--trust` in the CLI), revalidates the package, checks that the package target matches the current supported host, extracts to a temporary directory, and starts the declared launcher without a shell. Temporary extraction is cleanup, not an operating-system sandbox. Once executed, the application has the permissions of the current user; treat untrusted apps as unsafe even when the prompt is present.

## Format Compatibility

- Container format: ZIP.
- Manifest: `nova.json`, manifest/schema version `1.0`.
- Supported build targets: Arch Linux x86_64, Debian Linux x86_64, and Windows 10+ x86_64 (`windows-x86_64`). Windows host variants are detected separately; package identity does not break between Windows releases.
- Apple platforms are unsupported.
- Future incompatible package changes require a new package/manifest compatibility revision.
