from __future__ import annotations

import importlib.util
import py_compile
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict

from .build_system import BuildContext, BuildResult, LanguageAdapter
from .platform_compatibility import PlatformCompatibilityChecker


class PythonAdapter(LanguageAdapter):
    name = "python"

    def detect(self, project_root: Path) -> bool:
        return (project_root / "nova.json").is_file()

    def resolve_toolchain(self, context: BuildContext) -> Dict[str, str]:
        return {"executable": sys.executable, "version": sys.version.split()[0]}

    def build(self, context: BuildContext) -> BuildResult:
        entry = context.project_root / context.manifest["app"]["entryPoint"]
        if not entry.is_file():
            return BuildResult(False, errors=[f"Python entry point not found: {entry}"])

        missing = [
            name for name in context.manifest["dependencies"]["libraries"]
            if importlib.util.find_spec(name.replace("-", "_")) is None
        ]
        if missing:
            return BuildResult(
                False,
                errors=["Unresolved Python dependencies: " + ", ".join(missing)],
                warnings=["Install dependencies in the selected Python environment before building."],
            )

        output_dir = context.output_dir
        payload = output_dir / "payload"
        output_dir.mkdir(parents=True, exist_ok=True)
        if payload.exists():
            shutil.rmtree(payload)

        ignored = shutil.ignore_patterns(
            ".git", ".venv", "venv", "__pycache__", "build", "dist", "output", "*.pyc"
        )
        shutil.copytree(context.project_root, payload, ignore=ignored)
        cache_dir = output_dir / "pycache"
        cache_dir.mkdir(parents=True, exist_ok=True)

        compile_errors = []
        for source in sorted(payload.rglob("*.py")):
            relative = source.relative_to(payload).with_suffix(".pyc")
            compiled = cache_dir / relative
            compiled.parent.mkdir(parents=True, exist_ok=True)
            try:
                py_compile.compile(str(source), cfile=str(compiled), doraise=True)
            except py_compile.PyCompileError as error:
                compile_errors.append(str(error))

        if compile_errors:
            return BuildResult(False, logs=[f"Python: {sys.version.split()[0]}"], errors=compile_errors)
        return BuildResult(
            True,
            output_path=str(payload),
            logs=[f"Python {sys.version.split()[0]}: sources copied and byte-compiled", f"Output: {payload}"],
        )


class CAdapter(LanguageAdapter):
    name = "c"
    TIMEOUT_SECONDS = 120

    def detect(self, project_root: Path) -> bool:
        manifest_path = project_root / "nova.json"
        return manifest_path.is_file()

    def resolve_toolchain(self, context: BuildContext) -> Dict[str, str]:
        compiler = next((shutil.which(name) for name in ("cc", "gcc", "clang", "cl") if shutil.which(name)), None)
        if compiler is None:
            raise FileNotFoundError("No supported C compiler found (tried cc, gcc, clang, cl)")
        return {"executable": compiler, "name": Path(compiler).name}

    def build(self, context: BuildContext) -> BuildResult:
        source = context.project_root / context.manifest["app"]["entryPoint"]
        if not source.is_file():
            return BuildResult(False, errors=[f"C entry point not found: {source}"])
        sources = sorted((context.project_root / "src").rglob("*.c"))
        if source not in sources:
            sources.append(source)

        try:
            current = PlatformCompatibilityChecker().detect_current_system()
        except (RuntimeError, ValueError) as error:
            return BuildResult(False, errors=[str(error)])
        if current["target"] != context.target:
            return BuildResult(
                False,
                errors=[f"C cross-compilation is not configured: host={current['target']}, requested={context.target}"],
            )

        try:
            toolchain = self.resolve_toolchain(context)
        except FileNotFoundError as error:
            return BuildResult(False, errors=[str(error)])

        output_dir = context.output_dir / "bin"
        output_dir.mkdir(parents=True, exist_ok=True)
        executable_name = context.manifest["app"]["name"]
        if current["platform"] == "windows":
            executable_name += ".exe"
        executable = output_dir / executable_name
        compiler_name = toolchain["name"].lower()
        if compiler_name == "cl.exe" or compiler_name == "cl":
            command = [toolchain["executable"], "/nologo", "/O2", *(str(item) for item in sources), f"/Fe:{executable}"]
        else:
            command = [toolchain["executable"], "-O2", "-Wall", "-Wextra", *(str(item) for item in sources), "-o", str(executable)]

        try:
            completed = subprocess.run(
                command,
                cwd=context.project_root,
                capture_output=True,
                text=True,
                timeout=self.TIMEOUT_SECONDS,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return BuildResult(False, logs=["Compiler timed out"], errors=[f"C compilation exceeded {self.TIMEOUT_SECONDS}s"])
        except OSError as error:
            return BuildResult(False, errors=[f"Could not start C compiler: {error}"])

        logs = [line for line in (completed.stdout + "\n" + completed.stderr).splitlines() if line]
        if completed.returncode != 0:
            return BuildResult(False, logs=logs, errors=[f"C compiler exited with status {completed.returncode}"])
        return BuildResult(True, output_path=str(executable), logs=logs + [f"Output: {executable}"])
