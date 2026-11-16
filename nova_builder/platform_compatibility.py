from __future__ import annotations

import platform as host_platform
import sys
from pathlib import Path
from typing import Dict, Optional


class PlatformCompatibilityChecker:
    """Supported NOVA 1.0 host and package targets."""

    TARGETS = {
        "linux-arch-x86_64": ("linux", "x86_64", "arch"),
        "linux-debian-x86_64": ("linux", "x86_64", "debian"),
        "windows-x86_64": ("windows", "x86_64", "windows"),
    }

    def normalize_arch(self, value: Optional[str]) -> str:
        if value is None:
            return ""
        normalized = str(value).strip().lower()
        if normalized in {"x86_64", "amd64", "x64"}:
            return "x86_64"
        return normalized

    def normalize_distro(self, value: Optional[str]) -> str:
        if value is None:
            return ""
        normalized = str(value).strip().lower()
        aliases = {
            "arch": "arch",
            "archlinux": "arch",
            "debian": "debian",
            "windows": "windows",
        }
        return aliases.get(normalized, normalized)

    def normalize_platform(self, value: Optional[str]) -> str:
        if value is None:
            return ""
        normalized = str(value).strip().lower()
        if normalized in {"darwin", "macos", "macosx", "apple", "ios"}:
            return "unsupported"
        if normalized in {"win32", "win64", "windows"}:
            return "windows"
        if normalized.startswith("linux"):
            return "linux"
        return normalized

    def is_target_supported(self, target: Optional[str]) -> bool:
        return isinstance(target, str) and target.strip().lower() in self.TARGETS

    def is_compatible(self, platform: Optional[str], arch: Optional[str], distro: Optional[str] = None) -> bool:
        normalized_platform = self.normalize_platform(platform)
        normalized_arch = self.normalize_arch(arch)
        normalized_distro = self.normalize_distro(distro)
        if normalized_arch != "x86_64":
            return False
        if normalized_platform == "linux":
            return normalized_distro in {"arch", "debian"}
        if normalized_platform == "windows":
            return normalized_distro in {
                "",
                "windows",
                "windows-10",
                "windows-11",
                "windows-server-2022",
                "windows-server-2025",
            }
        return False

    def resolve_target(self, platform: Optional[str], arch: Optional[str], distro: Optional[str] = None) -> Dict[str, str]:
        normalized_platform = self.normalize_platform(platform)
        normalized_arch = self.normalize_arch(arch)
        normalized_distro = self.normalize_distro(distro)
        if not self.is_compatible(normalized_platform, normalized_arch, normalized_distro):
            raise ValueError(
                f"Unsupported target combination: platform={platform}, arch={arch}, distro={distro}. "
                "NOVA 1.0 supports Arch Linux, Debian Linux, Windows 10 and Windows 11 on x86_64 only."
            )

        if normalized_platform == "linux":
            target = f"linux-{normalized_distro}-x86_64"
        else:
            target = "windows-x86_64"
        return {
            "platform": normalized_platform,
            "arch": normalized_arch,
            "distro": normalized_distro,
            "target": target,
        }

    def detect_current_system(self) -> Dict[str, str]:
        system = host_platform.system().lower()
        machine = self.normalize_arch(host_platform.machine())
        if system == "linux":
            distro = self._linux_distribution_id()
            platform_name = "linux"
        elif system == "windows":
            platform_name = "windows"
            distro = self._windows_version()
        else:
            raise RuntimeError(f"Unsupported host operating system: {host_platform.system()}")

        result = self.resolve_target(platform_name, machine, distro)
        result["variant"] = distro
        result["release"] = host_platform.release()
        result["version"] = host_platform.version()
        return result

    @staticmethod
    def _linux_distribution_id() -> str:
        os_release = Path("/etc/os-release")
        if not os_release.is_file():
            return ""
        values: Dict[str, str] = {}
        for line in os_release.read_text(encoding="utf-8").splitlines():
            if "=" not in line or line.startswith("#"):
                continue
            key, value = line.split("=", 1)
            values[key] = value.strip().strip('"').lower()
        distro_id = values.get("ID", "")
        if distro_id in {"arch", "archlinux"}:
            return "arch"
        if distro_id == "debian":
            return "debian"
        return distro_id

    @staticmethod
    def _windows_version() -> str:
        if sys.platform != "win32":
            return ""
        windows_version = sys.getwindowsversion()
        build = windows_version.build
        if windows_version.product_type != 1:
            if build >= 26100:
                return "windows-server-2025"
            if build >= 20348:
                return "windows-server-2022"
            raise RuntimeError(f"Unsupported Windows Server build: {build}")
        if build >= 22000:
            return "windows-11"
        if build >= 10240:
            return "windows-10"
        raise RuntimeError(f"Unsupported Windows workstation build: {build}")
