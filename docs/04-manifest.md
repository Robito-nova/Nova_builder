# NOVA Manifest Standard 1.0

The authoritative machine-readable schema is [`nova-1.0.schema.json`](../nova_builder/schemas/nova-1.0.schema.json). It uses JSON Schema Draft 2020-12. Runtime validation is implemented by `nova_builder.manifest.validate_manifest()` and adds cross-field checks beyond JSON Schema.

## Compatibility

- `manifestVersion` and `schemaVersion` must both be `1.0`.
- Supported targets are `linux-arch-x86_64`, `linux-debian-x86_64`, and `windows-x86_64` (Windows 10 and newer x86_64 hosts).
- Apple platforms and all other distributions, Windows versions, architectures, and cross-compilation targets are rejected in 1.0.
- `app.platforms` and `app.arch` must include the platform and architecture selected by `build.target`.
- `app.language` must match `build.toolchain`.
- Paths in `app.entryPoint` and `package.launcher` must be relative POSIX paths and cannot traverse outside the package.
- Unknown fields are rejected. A future incompatible manifest revision requires a new schema version.

## Example

```json
{
  "manifestVersion": "1.0",
  "schemaVersion": "1.0",
  "app": {
    "name": "HelloNova",
    "id": "org.example.hellonova",
    "version": "1.0.0",
    "description": "Sample NOVA application",
    "developer": "NOVA Example",
    "type": "cli",
    "entryPoint": "src/main.py",
    "language": "python",
    "arch": ["x86_64"],
    "platforms": ["linux", "windows"]
  },
  "runtime": {"required": ["python>=3.12"], "fallback": []},
  "dependencies": {"system": [], "libraries": [], "modules": []},
  "permissions": {"network": false, "filesystem": [], "hardware": []},
  "resources": {"icons": [], "locales": [], "assets": []},
  "build": {
    "toolchain": "python",
    "target": "linux-debian-x86_64",
    "output": "build/outputs/linux-debian-x86_64"
  },
  "package": {
    "kind": "application",
    "format": "nova",
    "launcher": "src/main.py",
    "installMode": "portable",
    "executableLike": true,
    "icon": ""
  }
}
```

## Required and Optional Fields

The JSON Schema is authoritative. `manifestVersion`, `schemaVersion`, all top-level sections, and each section's `required` members are mandatory in 1.0. Descriptive fields such as `app.description`, `app.developer`, and individual resource lists may be empty. Additional unrecognized fields are not accepted in this schema version.

## Evolution Policy

- Patch releases may clarify documentation and fix validators without changing accepted manifests.
- A backward-compatible optional field may be added only through a documented schema revision policy.
- Removing fields, changing types, or changing target semantics requires a new `schemaVersion`.
- A Builder/Runtime must reject unsupported major schema versions clearly; it must not silently reinterpret them.
