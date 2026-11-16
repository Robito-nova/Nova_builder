from __future__ import annotations

import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import zipfile
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any, Dict, List

from .manifest import validate_manifest
from .package_format import validate_package_structure
from .platform_compatibility import PlatformCompatibilityChecker


@dataclass
class ExecutionPlan:
    package_path: str
    app_name: str
    app_type: str
    package_format: str
    launcher: str
    install_mode: str
    executable_like: bool
    target: str
    language: str
    permissions: Dict[str, Any] = field(default_factory=dict)
    runtime_requirements: List[str] = field(default_factory=list)
    launch_command: List[str] = field(default_factory=list)


class NovaRuntime:
    """Run validated NOVA packages after the caller explicitly trusts the app."""

    def inspect_package(self, package_path: str | Path) -> ExecutionPlan:
        package_file = Path(package_path).resolve()
        errors = validate_package_structure(package_file)
        if errors:
            raise ValueError("Invalid NOVA package: " + "; ".join(errors))

        with zipfile.ZipFile(package_file, "r") as archive:
            manifest = json.loads(archive.read("nova.json"))

        app = manifest["app"]
        package = manifest["package"]
        target = manifest["build"]["target"]
        launcher = package["launcher"]
        if app["language"] == "python":
            launch_command = [sys.executable, launcher]
        else:
            launch_command = [launcher]

        return ExecutionPlan(
            package_path=str(package_file),
            app_name=app["name"],
            app_type=app["type"],
            package_format=package["format"],
            launcher=launcher,
            install_mode=package["installMode"],
            executable_like=package["executableLike"],
            target=target,
            language=app["language"],
            permissions=dict(manifest["permissions"]),
            runtime_requirements=list(manifest["runtime"]["required"]),
            launch_command=launch_command,
        )

    def launch(
        self,
        package_path: str | Path,
        dry_run: bool = True,
        trusted: bool = False,
        timeout: int = 60,
    ) -> ExecutionPlan | subprocess.CompletedProcess[str]:
        plan = self.inspect_package(package_path)
        if dry_run:
            return plan
        if not trusted:
            raise PermissionError("NOVA apps are untrusted by default; pass trusted=True only after reviewing the publisher and permissions")
        if timeout <= 0:
            raise ValueError("timeout must be positive")

        checker = PlatformCompatibilityChecker()
        try:
            current = checker.detect_current_system()
        except (RuntimeError, ValueError) as error:
            raise RuntimeError(f"NOVA Runtime cannot execute packages on this host: {error}") from error
        if current["target"] != plan.target:
            raise RuntimeError(f"Package target {plan.target} does not match host target {current['target']}")
        self._check_runtime_requirements(plan)

        with tempfile.TemporaryDirectory(prefix="nova-runtime-") as temp_dir:
            extraction_root = Path(temp_dir).resolve()
            with zipfile.ZipFile(plan.package_path, "r") as archive:
                for info in archive.infolist():
                    if info.is_dir():
                        continue
                    relative = PurePosixPath(info.filename)
                    destination = (extraction_root / Path(*relative.parts)).resolve()
                    if not destination.is_relative_to(extraction_root):
                        raise ValueError(f"Unsafe package path: {info.filename}")
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    with archive.open(info, "r") as source, destination.open("xb") as output:
                        shutil.copyfileobj(source, output)

            launcher_path = (extraction_root / Path(*PurePosixPath(plan.launcher).parts)).resolve()
            if not launcher_path.is_relative_to(extraction_root) or not launcher_path.is_file():
                raise ValueError(f"Package launcher is invalid: {plan.launcher}")
            if plan.language == "python":
                command = [sys.executable, str(launcher_path)]
            else:
                if os.name != "nt":
                    launcher_path.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
                command = [str(launcher_path)]
            return subprocess.run(
                command,
                cwd=extraction_root,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
                shell=False,
            )

    @staticmethod
    def _check_runtime_requirements(plan: ExecutionPlan) -> None:
        if plan.language != "python":
            return
        for requirement in plan.runtime_requirements:
            match = re.fullmatch(r"python\s*(>=|==)\s*(\d+)\.(\d+)(?:\.(\d+))?", requirement.lower())
            if not match:
                raise RuntimeError(f"Unsupported Python runtime requirement: {requirement}")
            operator, major, minor, patch = match.groups()
            required = (int(major), int(minor), int(patch or 0))
            current = tuple(sys.version_info[:3])
            compatible = current >= required if operator == ">=" else current == required
            if not compatible:
                raise RuntimeError(f"Package requires Python {operator}{'.'.join(map(str, required))}; current runtime is {sys.version.split()[0]}")


class NovaProjectPackager:
    """Package a project and return its validated execution plan."""

    def __init__(self, root: str | Path):
        self.root = Path(root).resolve()

    def package_project(self, output_path: str | Path) -> ExecutionPlan:
        from .build_system import BuildSystem
        from .package_format import NovaPackageBuilder

        final_package = Path(output_path).resolve()
        final_package.parent.mkdir(parents=True, exist_ok=True)
        build_result = BuildSystem.with_default_adapters().build(self.root)
        if not build_result.success:
            raise RuntimeError("Project build failed: " + "; ".join(build_result.errors))

        manifest_path = self.root / "nova.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        language = manifest["app"]["language"]
        with tempfile.TemporaryDirectory(prefix="nova-package-stage-") as stage_name:
            stage = Path(stage_name)
            self._copy_project_files(stage)
            if language == "c":
                launcher = PurePosixPath(manifest["package"]["launcher"])
                staged_launcher = stage.joinpath(*launcher.parts)
                staged_launcher.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(build_result.output_path, staged_launcher)
                if os.name != "nt":
                    staged_launcher.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
            archive_path = NovaPackageBuilder(stage).build(final_package)
        return NovaRuntime().inspect_package(archive_path)

    def _copy_project_files(self, stage: Path) -> None:
        skipped = {".git", ".venv", "venv", "__pycache__", "build", "dist", "output"}
        for source in sorted(self.root.rglob("*")):
            if not source.is_file() or source.is_symlink():
                continue
            relative = source.relative_to(self.root)
            if any(part in skipped for part in relative.parts):
                continue
            destination = stage / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
