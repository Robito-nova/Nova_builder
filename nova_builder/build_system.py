from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .manifest import validate_manifest
from .platform_compatibility import PlatformCompatibilityChecker


@dataclass
class BuildContext:
    project_root: Path
    target: str = "linux-x86_64"
    output_dir: Path | None = None
    manifest: Dict[str, Any] | None = None
    env: Dict[str, str] = field(default_factory=dict)


@dataclass
class BuildResult:
    success: bool
    output_path: str | None = None
    logs: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class LanguageAdapter:
    """Base class for all language-specific build adapters."""

    name: str = "base"

    def detect(self, project_root: Path) -> bool:
        raise NotImplementedError

    def resolve_toolchain(self, context: BuildContext) -> Dict[str, Any]:
        raise NotImplementedError

    def build(self, context: BuildContext) -> BuildResult:
        raise NotImplementedError

    def package(self, build_result: BuildResult, context: BuildContext) -> BuildResult:
        raise NotImplementedError


class BuildSystem:
    """Manifest-driven build orchestration for the supported NOVA 1.0 adapters."""

    def __init__(self):
        self.adapters: Dict[str, LanguageAdapter] = {}

    def register_adapter(self, adapter: LanguageAdapter) -> None:
        self.adapters[adapter.name] = adapter

    @classmethod
    def with_default_adapters(cls) -> "BuildSystem":
        from .build_adapters import CAdapter, PythonAdapter

        system = cls()
        system.register_adapter(PythonAdapter())
        system.register_adapter(CAdapter())
        return system

    def detect_language(self, project_root: Path) -> Optional[str]:
        for name, adapter in self.adapters.items():
            if adapter.detect(project_root):
                return name
        return None

    def build(self, project_root: str | Path, target: str | None = None) -> BuildResult:
        from .manifest import load_manifest

        project_path = Path(project_root).resolve()
        manifest_path = project_path / "nova.json"
        if not manifest_path.is_file():
            return BuildResult(False, errors=[f"Project manifest not found: {manifest_path}"])
        try:
            raw_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            errors = validate_manifest(raw_manifest)
            if errors:
                return BuildResult(False, errors=errors)
            manifest = load_manifest(manifest_path).to_dict()
        except (OSError, json.JSONDecodeError, ValueError) as error:
            return BuildResult(False, errors=[f"Could not load project manifest: {error}"])

        selected_target = target or manifest["build"]["target"]
        checker = PlatformCompatibilityChecker()
        if not checker.is_target_supported(selected_target):
            return BuildResult(False, errors=[f"Unsupported build target: {selected_target}"])
        target_platform = "windows" if selected_target.startswith("windows-") else "linux"
        if target_platform not in manifest["app"]["platforms"]:
            return BuildResult(False, errors=[f"Target {selected_target} is not declared in app.platforms"])

        language = manifest["app"]["language"]
        if language not in self.adapters:
            return BuildResult(False, errors=[f"No build adapter registered for language: {language}"])

        output_dir = project_path / "build" / "outputs" / selected_target
        context = BuildContext(
            project_root=project_path,
            target=selected_target,
            output_dir=output_dir,
            manifest=manifest,
        )
        return self.adapters[language].build(context)
