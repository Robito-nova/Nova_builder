from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any, Dict, List

from jsonschema import Draft202012Validator

from .platform_compatibility import PlatformCompatibilityChecker

SCHEMA_PATH = Path(__file__).parent / "schemas" / "nova-1.0.schema.json"
PLATFORM_CHECKER = PlatformCompatibilityChecker()


@dataclass
class NovaManifest:
    """Manifest model for the NOVA 1.0 application format."""

    app_name: str
    app_id: str
    version: str
    description: str = ""
    developer: str = ""
    entry_point: str = ""
    app_type: str = "desktop"
    language: str = "python"
    arch: List[str] = field(default_factory=lambda: ["x86_64"])
    platforms: List[str] = field(default_factory=lambda: ["linux"])
    runtime_required: List[str] = field(default_factory=list)
    dependencies: Dict[str, List[str]] = field(default_factory=lambda: {"system": [], "libraries": [], "modules": []})
    permissions: Dict[str, Any] = field(default_factory=lambda: {"network": False, "filesystem": [], "hardware": []})
    resources: Dict[str, List[str]] = field(default_factory=lambda: {"icons": [], "locales": [], "assets": []})
    build: Dict[str, str] = field(default_factory=lambda: {"toolchain": "python", "target": "linux-debian-x86_64", "output": "build/output"})
    package: Dict[str, Any] = field(default_factory=lambda: {
        "kind": "application",
        "format": "nova",
        "launcher": "src/main.py",
        "installMode": "portable",
        "executableLike": True,
        "icon": "assets/icons/app.png",
    })

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "NovaManifest":
        errors = validate_manifest(data)
        if errors:
            raise ValueError("; ".join(errors))

        app = data["app"]
        runtime = data["runtime"]
        return NovaManifest(
            app_name=app["name"],
            app_id=app["id"],
            version=app["version"],
            description=app.get("description", ""),
            developer=app.get("developer", ""),
            entry_point=app["entryPoint"],
            app_type=app["type"],
            language=app["language"],
            arch=list(app["arch"]),
            platforms=list(app["platforms"]),
            runtime_required=list(runtime["required"]),
            dependencies={key: list(value) for key, value in data["dependencies"].items()},
            permissions=dict(data["permissions"]),
            resources={key: list(value) for key, value in data["resources"].items()},
            build=dict(data["build"]),
            package=dict(data["package"]),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "manifestVersion": "1.0",
            "schemaVersion": "1.0",
            "app": {
                "name": self.app_name,
                "id": self.app_id,
                "version": self.version,
                "description": self.description,
                "developer": self.developer,
                "type": self.app_type,
                "entryPoint": self.entry_point,
                "language": self.language,
                "arch": self.arch,
                "platforms": self.platforms,
            },
            "runtime": {"required": self.runtime_required, "fallback": []},
            "dependencies": self.dependencies,
            "permissions": self.permissions,
            "resources": self.resources,
            "build": self.build,
            "package": self.package,
        }


def validate_manifest(data: Dict[str, Any]) -> List[str]:
    """Validate the versioned JSON Schema and NOVA target consistency rules."""
    if not isinstance(data, dict):
        return ["manifest must be a JSON object"]

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    errors = [
        f"{'.'.join(str(part) for part in error.absolute_path) or 'manifest'}: {error.message}"
        for error in validator.iter_errors(data)
    ]
    if errors:
        return sorted(errors)

    app = data["app"]
    target = data["build"]["target"]
    target_platform = "windows" if target.startswith("windows-") else "linux"
    target_arch = PLATFORM_CHECKER.normalize_arch(target.rsplit("-", 1)[-1])
    app_platforms = {PLATFORM_CHECKER.normalize_platform(item) for item in app["platforms"]}
    app_arches = {PLATFORM_CHECKER.normalize_arch(item) for item in app["arch"]}

    if target_platform not in app_platforms:
        errors.append(f"build.target {target!r} is not listed in app.platforms")
    if target_arch not in app_arches:
        errors.append(f"build.target {target!r} architecture is not listed in app.arch")
    if app["language"] != data["build"]["toolchain"]:
        errors.append("app.language must match build.toolchain")

    for label, value in (("app.entryPoint", app["entryPoint"]), ("package.launcher", data["package"]["launcher"])):
        path = PurePosixPath(value)
        if path.is_absolute() or ".." in path.parts or "\\" in value:
            errors.append(f"{label} must be a safe project-relative POSIX path")

    return errors


def load_manifest(path: str | Path) -> NovaManifest:
    with open(path, "r", encoding="utf-8") as handle:
        raw = json.load(handle)
    return NovaManifest.from_dict(raw)


def save_manifest(manifest: NovaManifest, path: str | Path) -> None:
    errors = validate_manifest(manifest.to_dict())
    if errors:
        raise ValueError("; ".join(errors))
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "w", encoding="utf-8") as handle:
        json.dump(manifest.to_dict(), handle, indent=2)
        handle.write("\n")
