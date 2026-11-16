from __future__ import annotations

import json
import re
from pathlib import Path

from .platform_compatibility import PlatformCompatibilityChecker


def create_project(path: str | Path, name: str, language: str = "python", target: str | None = None) -> Path:
    project_path = Path(path).resolve()
    if language not in {"python", "c"}:
        raise ValueError("NOVA 1.0 project templates support only python and c")
    if project_path.exists() and any(project_path.iterdir()):
        raise FileExistsError(f"Project directory is not empty: {project_path}")
    if not name.strip() or Path(name).name != name or any(character in name for character in '<>:"/\\|?*'):
        raise ValueError("Project name must be a non-empty folder name without path or reserved characters")

    checker = PlatformCompatibilityChecker()
    current = checker.detect_current_system()
    selected_target = target or current["target"]
    if not checker.is_target_supported(selected_target):
        raise ValueError(f"Unsupported target: {selected_target}")
    target_platform = "windows" if selected_target.startswith("windows-") else "linux"
    if target_platform != current["platform"]:
        raise ValueError("Project templates currently require a native target on the current host")

    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    if not slug:
        raise ValueError("Project name must contain letters or numbers")
    app_id = f"org.nova.{slug.replace('-', '.')}"
    entry_point = "src/main.py" if language == "python" else "src/main.c"
    launcher = entry_point if language == "python" else f"bin/{name}.exe" if target_platform == "windows" else f"bin/{name}"
    manifest = {
        "manifestVersion": "1.0",
        "schemaVersion": "1.0",
        "app": {
            "name": name,
            "id": app_id,
            "version": "0.1.0",
            "description": "",
            "developer": "",
            "type": "desktop",
            "entryPoint": entry_point,
            "language": language,
            "arch": ["x86_64"],
            "platforms": [target_platform],
        },
        "runtime": {"required": ["python>=3.12"] if language == "python" else [], "fallback": []},
        "dependencies": {"system": [], "libraries": [], "modules": []},
        "permissions": {"network": False, "filesystem": [], "hardware": []},
        "resources": {"icons": [], "locales": [], "assets": []},
        "build": {"toolchain": language, "target": selected_target, "output": f"build/outputs/{selected_target}"},
        "package": {
            "kind": "application",
            "format": "nova",
            "launcher": launcher,
            "installMode": "portable",
            "executableLike": True,
            "icon": "",
        },
    }

    project_path.mkdir(parents=True, exist_ok=True)
    (project_path / "src").mkdir()
    (project_path / "assets").mkdir()
    (project_path / "resources").mkdir()
    (project_path / "metadata").mkdir()
    (project_path / "nova.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    if language == "python":
        source = 'def main() -> None:\n    print("Hello from NOVA")\n\n\nif __name__ == "__main__":\n    main()\n'
    else:
        source = '#include <stdio.h>\n\nint main(void) {\n    puts("Hello from NOVA");\n    return 0;\n}\n'
    (project_path / entry_point).write_text(source, encoding="utf-8")
    return project_path
