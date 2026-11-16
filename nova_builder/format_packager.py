from __future__ import annotations

import base64
import json
import os
import re
import shutil
import stat
import subprocess
import tarfile
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import List

from .build_system import BuildSystem
from .manifest import validate_manifest
from .package_format import NovaPackageBuilder
from .platform_compatibility import PlatformCompatibilityChecker
from .phase_two_runtime import NovaProjectPackager


@dataclass(frozen=True)
class FormatOption:
    key: str
    label: str
    extension: str
    available: bool
    reason: str


FORMATS = (
    ("nova", "NOVA application", ".nova"),
    ("deb", "Debian package", ".deb"),
    ("exe", "Windows executable", ".exe"),
    ("pkg", "Apple installer", ".pkg"),
    ("flatpak", "Flatpak bundle", ".flatpak"),
    ("jar", "Java archive", ".jar"),
    ("run", "Linux self-extracting package", ".run"),
    ("appimage", "AppImage", ".AppImage"),
    ("app", "Apple application bundle", ".app"),
)


class ProjectFormatPackager:
    """Availability and packaging for the formats implemented by the prototype."""

    def __init__(self, project_root: str | Path):
        self.project_root = Path(project_root).resolve()

    def available_formats(self) -> List[FormatOption]:
        manifest, manifest_error = self._read_manifest()
        checker = PlatformCompatibilityChecker()
        try:
            current = checker.detect_current_system()
            host_error = ""
        except (RuntimeError, ValueError) as error:
            current = {}
            host_error = str(error)
        project_target = manifest.get("build", {}).get("target", "") if manifest else ""

        options: List[FormatOption] = []
        for key, label, extension in FORMATS:
            available = False
            reason = ""
            if key == "nova":
                available = manifest is not None
                reason = "" if available else manifest_error
            elif key == "deb":
                available = bool(
                    manifest
                    and current.get("target") == "linux-debian-x86_64"
                    and project_target == "linux-debian-x86_64"
                    and shutil.which("dpkg-deb")
                )
                if not available:
                    reason = manifest_error or host_error or "Requires a Debian x86_64 host, Debian target in nova.json, and dpkg-deb"
            elif key == "run":
                available = bool(manifest and current.get("platform") == "linux" and project_target == current.get("target"))
                if not available:
                    reason = manifest_error or host_error or "Requires a Linux project target matching the current host"
            elif key == "exe":
                available = bool(
                    manifest
                    and current.get("platform") == "windows"
                    and manifest["app"]["language"] == "c"
                    and project_target == "windows-x86_64"
                )
                if not available:
                    reason = manifest_error or host_error or "Requires a native Windows x86_64 host, Windows target, C project, and compiler"
            elif key == "jar":
                available = bool(manifest and manifest["app"]["language"] == "java" and shutil.which("jar"))
                if not available:
                    reason = "Java build adapter is not included in this prototype"
            elif key == "flatpak":
                reason = "Flatpak manifest/build integration is not implemented"
            elif key == "appimage":
                reason = "AppImage packaging integration is not implemented"
            elif key in {"pkg", "app"}:
                reason = "Apple platforms are explicitly outside NOVA's supported targets"
            options.append(FormatOption(key, label, extension, available, reason))
        return options

    def package(self, format_key: str, output_path: str | Path) -> Path:
        options = {option.key: option for option in self.available_formats()}
        if format_key not in options:
            raise ValueError(f"Unknown package format: {format_key}")
        option = options[format_key]
        if not option.available:
            raise RuntimeError(option.reason)

        output = Path(output_path).resolve()
        if output.suffix.lower() != option.extension.lower():
            raise ValueError(f"Output file must use {option.extension}")
        if format_key == "nova":
            return Path(NovaProjectPackager(self.project_root).package_project(output).package_path)
        if format_key == "deb":
            return self._package_deb(output)
        if format_key == "run":
            return self._package_run(output)
        if format_key == "exe":
            return self._package_windows_exe(output)
        raise RuntimeError(option.reason)

    def _read_manifest(self):
        manifest_path = self.project_root / "nova.json"
        if not manifest_path.is_file():
            return None, "Open a NOVA project containing nova.json"
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            return None, f"Cannot read nova.json: {error}"
        errors = validate_manifest(manifest)
        if errors:
            return None, "Invalid nova.json: " + "; ".join(errors)
        return manifest, ""

    def _build_payload(self, stage: Path, manifest: dict) -> Path:
        target = manifest["build"]["target"]
        result = BuildSystem.with_default_adapters().build(self.project_root, target)
        if not result.success:
            raise RuntimeError("Build failed: " + "; ".join(result.errors))

        payload = stage / "opt" / self._package_name(manifest) / "project"
        payload.mkdir(parents=True, exist_ok=True)
        skipped = {
            ".git",
            ".venv",
            "venv",
            "__pycache__",
            "build",
            "dist",
            "output",
            ".github",
            "docs",
            "examples",
            "tests",
            "nova_builder.egg-info",
        }
        for source in sorted(self.project_root.rglob("*")):
            if not source.is_file() or source.is_symlink():
                continue
            relative = source.relative_to(self.project_root)
            if any(part in skipped or part.endswith(".egg-info") for part in relative.parts):
                continue
            destination = payload / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)

        if manifest["app"]["language"] == "c":
            binary = Path(result.output_path)
            launcher = payload / manifest["package"]["launcher"]
            launcher.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(binary, launcher)
            if os.name != "nt":
                launcher.chmod(launcher.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        return payload

    def _package_deb(self, output: Path) -> Path:
        manifest, error = self._read_manifest()
        if manifest is None:
            raise ValueError(error)
        package_name = self._package_name(manifest)
        output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="nova-deb-") as temp_dir:
            root = Path(temp_dir) / "root"
            (root / "DEBIAN").mkdir(parents=True)
            payload = self._build_payload(root, manifest)
            control = [
                f"Package: {package_name}",
                f"Version: {manifest['app']['version']}",
                "Section: utils",
                "Priority: optional",
                "Architecture: amd64",
                f"Maintainer: {manifest['app'].get('developer') or 'NOVA package maintainer'}",
                f"Description: {manifest['app'].get('description') or manifest['app']['name']}",
            ]
            if manifest["app"]["language"] == "python":
                dependencies = ["python3"]
            else:
                dependencies = []
            dependencies.extend(manifest["dependencies"]["system"])
            dependencies = list(dict.fromkeys(dependencies))
            if dependencies:
                if any(not re.fullmatch(r"[a-z0-9][a-z0-9+.-]*", dependency) for dependency in dependencies):
                    raise ValueError("Debian dependency names may contain only lowercase package-name characters")
                control.append("Depends: " + ", ".join(dependencies))
            (root / "DEBIAN" / "control").write_text("\n".join(control) + "\n", encoding="utf-8")

            launcher = root / "usr" / "bin" / package_name
            launcher.parent.mkdir(parents=True, exist_ok=True)
            relative_launcher = Path("/opt") / package_name / "project" / Path(manifest["package"]["launcher"])
            if manifest["app"]["language"] == "python":
                command = f'exec python3 "{relative_launcher}" "$@"'
            else:
                command = f'exec "{relative_launcher}" "$@"'
            launcher.write_text(f"#!/bin/sh\nset -eu\n{command}\n", encoding="utf-8")
            launcher.chmod(0o755)

            if manifest["app"]["type"] == "desktop":
                self._install_debian_desktop_files(root, payload, package_name, manifest)

            completed = subprocess.run(
                [shutil.which("dpkg-deb"), "--root-owner-group", "--build", str(root), str(output)],
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
            if completed.returncode:
                raise RuntimeError(completed.stderr.strip() or "dpkg-deb failed")
        return output

    @staticmethod
    def _install_debian_desktop_files(root: Path, payload: Path, package_name: str, manifest: dict) -> None:
        icon_name = package_name
        icon_reference = manifest["package"].get("icon", "")
        if icon_reference:
            icon_relative = Path(icon_reference)
            icon_source = (payload / icon_relative).resolve()
            if icon_relative.is_absolute() or not icon_source.is_relative_to(payload.resolve()):
                raise ValueError("Desktop icon must be a package-relative path")
            if not icon_source.is_file():
                raise FileNotFoundError(f"Desktop icon not found: {icon_reference}")
            if icon_source.suffix.lower() not in {".svg", ".png"}:
                raise ValueError("Debian desktop icons must be SVG or PNG")
            size_directory = "scalable" if icon_source.suffix.lower() == ".svg" else "256x256"
            icon_destination = root / "usr" / "share" / "icons" / "hicolor" / size_directory / "apps" / f"{icon_name}{icon_source.suffix.lower()}"
            icon_destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(icon_source, icon_destination)

        def desktop_escape(value: str) -> str:
            return value.replace("\\", "\\\\").replace("\r", " ").replace("\n", " ")

        desktop_file = root / "usr" / "share" / "applications" / f"{package_name}.desktop"
        desktop_file.parent.mkdir(parents=True, exist_ok=True)
        fields = [
            "[Desktop Entry]",
            "Version=1.0",
            "Type=Application",
            f"Name={desktop_escape(manifest['app']['name'])}",
            f"Comment={desktop_escape(manifest['app'].get('description', ''))}",
            f"Exec=/usr/bin/{package_name}",
            f"TryExec=/usr/bin/{package_name}",
            f"Icon={icon_name}",
            "Terminal=false",
            "StartupNotify=true",
            "Categories=Development;IDE;",
        ]
        desktop_file.write_text("\n".join(fields) + "\n", encoding="utf-8")

    def _package_run(self, output: Path) -> Path:
        manifest, error = self._read_manifest()
        if manifest is None:
            raise ValueError(error)
        package_name = self._package_name(manifest)
        output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="nova-run-") as temp_dir:
            stage = Path(temp_dir) / "payload"
            stage.mkdir()
            self._build_payload(stage, manifest)
            archive_path = Path(temp_dir) / "payload.tar.gz"
            with tarfile.open(archive_path, "w:gz") as archive:
                for path in sorted(stage.rglob("*")):
                    archive.add(path, arcname=path.relative_to(stage).as_posix(), recursive=False)

            with output.open("wb") as destination:
                header = (
                    "#!/bin/sh\n"
                    "set -eu\n"
                    f'install_root="${{1:-$HOME/.local/opt/{package_name}}}"\n'
                    "mkdir -p \"$install_root\"\n"
                    "sed '1,/^__NOVA_PAYLOAD_BELOW__$/d' \"$0\" | base64 -d | tar -xz -C \"$install_root\"\n"
                    f'printf "Installed {package_name} payload in %s\\n" "$install_root"\n'
                    "exit 0\n"
                    "__NOVA_PAYLOAD_BELOW__\n"
                ).encode("utf-8")
                destination.write(header)
                with archive_path.open("rb") as source:
                    carry = b""
                    while chunk := source.read(57):
                        block = carry + chunk
                        usable = len(block) - (len(block) % 57)
                        if usable:
                            destination.write(base64.b64encode(block[:usable]) + b"\n")
                        carry = block[usable:]
                    if carry:
                        destination.write(base64.b64encode(carry) + b"\n")
        output.chmod(0o755)
        return output

    def _package_windows_exe(self, output: Path) -> Path:
        manifest, error = self._read_manifest()
        if manifest is None:
            raise ValueError(error)
        if manifest["app"]["language"] != "c":
            raise RuntimeError("Windows executable packaging currently supports native C projects only")
        result = BuildSystem.with_default_adapters().build(self.project_root, "windows-x86_64")
        if not result.success:
            raise RuntimeError("Build failed: " + "; ".join(result.errors))
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(result.output_path, output)
        return output

    @staticmethod
    def _package_name(manifest: dict) -> str:
        candidate = manifest["app"]["id"].split(".")[-1].lower()
        normalized = re.sub(r"[^a-z0-9+.-]+", "-", candidate).strip(".-")
        if not normalized or not normalized[0].isalnum():
            raise ValueError("app.id cannot be converted to a valid Debian package name")
        return normalized
