# Language Adapters

NOVA 1.0 selects a language from the manifest and dispatches to a registered `LanguageAdapter`. The current release scope contains Python and C adapters only. C++ is not claimed as supported; it requires its own tested adapter and manifest/toolchain contract.

## Implemented Contract

Adapters implement `detect(project_root)`, `resolve_toolchain(context)`, and `build(context)`. `BuildSystem.with_default_adapters()` registers `PythonAdapter` and `CAdapter`.

## PythonAdapter

Uses the running Python interpreter, validates importable dependencies, stages the project, and byte-compiles `.py` files. Runtime version constraints use forms such as `python>=3.12` or `python==3.12.2`.

## CAdapter

Finds a supported compiler, compiles all `.c` files under `src/`, reports compiler output, and creates a native launcher. Cross-compilation is not configured.

## Extension Policy

A new adapter must define its manifest values, toolchain discovery, dependency behavior, build result, package launcher format, and runtime invocation. It must include tests on every target claimed for support. Adding adapter names without those tests does not constitute language support.
