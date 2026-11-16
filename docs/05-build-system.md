# Build System 1.0 Prototype

`BuildSystem` reads `nova.json`, validates it, selects an adapter from `app.language`, checks target/platform declarations, and writes under `build/outputs/<target>/`.

## Python Adapter

- Uses the active Python interpreter.
- Checks that declared libraries are importable by their module names.
- Copies project files to an isolated build output directory and byte-compiles Python sources.
- Does not create a standalone executable or bundle a Python runtime.
- Does not resolve/install dependencies yet; unresolved imports fail with a build error.

## C Adapter

- Finds `cc`, `gcc`, `clang`, or `cl` on PATH.
- Compiles all `.c` sources under `src/` and verifies the manifest entry file exists.
- Captures stdout/stderr and enforces a 120-second timeout.
- Supports native builds only; cross-compilation is rejected.
- Does not yet process a C dependency lockfile or arbitrary compiler/linker settings.

## Build and Package Flow

`nova build PROJECT [--target TARGET]` runs build validation and the selected adapter. `nova package PROJECT OUTPUT.nova` builds first, stages package files and any native launcher, then creates and validates the package. A failed build cannot produce a package.

## Remaining 1.0 Work

Hermetic/locked dependency installation, build cancellation, compiler diagnostic mapping to editor locations, cross-compilation, resource measurement, and verified target CI are not implemented. See [the release gates](11-v1-release.md).
