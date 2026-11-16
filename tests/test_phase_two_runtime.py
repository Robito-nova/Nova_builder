import tempfile
import unittest
import json
import importlib.util
import os
import stat
import shutil
import zipfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from nova_builder.phase_two_runtime import NovaProjectPackager, NovaRuntime
from nova_builder.package_format import NovaPackageBuilder, validate_package_structure
from nova_builder.manifest import load_manifest, validate_manifest
from nova_builder.platform_compatibility import PlatformCompatibilityChecker
from nova_builder.build_system import BuildSystem
from nova_builder.project_manager import create_project


class NovaPhaseTwoRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parents[1]
        self.sample_dir = self.root / 'examples' / 'sample_app'

    def test_packager_generates_execution_plan(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'sample.nova'
            packager = NovaProjectPackager(root=self.sample_dir)
            plan = packager.package_project(output_path)

            self.assertEqual(plan.package_format, 'nova')
            self.assertEqual(plan.app_name, 'NovaSampleApp')
            self.assertTrue(plan.executable_like)
            self.assertEqual(plan.launcher, 'src/main.py')
            self.assertTrue(Path(plan.launch_command[0]).is_file())

    def test_runtime_inspects_existing_package(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            package_path = Path(tmpdir) / 'sample.nova'
            NovaPackageBuilder(self.sample_dir).build(package_path)

            runtime = NovaRuntime()
            plan = runtime.inspect_package(package_path)

            self.assertEqual(plan.app_name, 'NovaSampleApp')
            self.assertEqual(plan.package_format, 'nova')
            self.assertEqual(plan.install_mode, 'portable')
            self.assertEqual(plan.launcher, 'src/main.py')

    def test_manifest_rejects_unsupported_platforms(self):
        invalid = {
            "manifestVersion": "1.0",
            "schemaVersion": "1.0",
            "app": {
                "name": "BadApp",
                "id": "com.example.badapp",
                "version": "1.0.0",
                "entryPoint": "src/main.py",
                "language": "python",
                "arch": ["x86_64"],
                "platforms": ["darwin"],
            },
            "build": {
                "toolchain": "python",
                "target": "darwin-arm64",
                "output": "dist/BadApp",
            },
            "package": {
                "kind": "application",
                "format": "nova",
                "launcher": "src/main.py",
                "installMode": "portable",
                "executableLike": True,
                "icon": "assets/icons/app.png",
            },
        }

        self.assertIn("darwin", "; ".join(validate_manifest(invalid)))

    def test_platform_checker_accepts_linux_windows_targets(self):
        checker = PlatformCompatibilityChecker()

        self.assertTrue(checker.is_target_supported("linux-arch-x86_64"))
        self.assertTrue(checker.is_target_supported("linux-debian-x86_64"))
        self.assertTrue(checker.is_target_supported("windows-x86_64"))
        self.assertTrue(checker.is_compatible("linux", "x86_64", "arch"))
        self.assertTrue(checker.is_compatible("linux", "x86_64", "debian"))
        self.assertTrue(checker.is_compatible("windows", "x86_64", "windows"))
        self.assertEqual(checker.resolve_target("windows", "amd64", "windows")["target"], "windows-x86_64")

    def test_platform_checker_rejects_unsupported_cases(self):
        checker = PlatformCompatibilityChecker()

        self.assertFalse(checker.is_target_supported("darwin-arm64"))
        self.assertFalse(checker.is_compatible("linux", "arm64", "ubuntu"))
        self.assertFalse(checker.is_compatible("darwin", "arm64", "macos"))
        self.assertEqual(checker.resolve_target("linux", "x86_64", "arch")["target"], "linux-arch-x86_64")

    def test_platform_detection_reads_host(self):
        checker = PlatformCompatibilityChecker()
        detected = checker.detect_current_system()

        self.assertIn(detected["platform"], {"linux", "windows"})
        self.assertTrue(detected["target"])

    def test_windows_host_detection_classifies_10_and_11(self):
        checker = PlatformCompatibilityChecker()
        cases = (
            (19045, 1, "windows-10"),
            (26100, 1, "windows-11"),
            (20348, 3, "windows-server-2022"),
            (26100, 3, "windows-server-2025"),
        )
        for build, product_type, expected_variant in cases:
            with patch("nova_builder.platform_compatibility.host_platform.system", return_value="Windows"), \
                    patch("nova_builder.platform_compatibility.host_platform.machine", return_value="AMD64"), \
                    patch("nova_builder.platform_compatibility.sys.platform", "win32"), \
                    patch("nova_builder.platform_compatibility.sys.getwindowsversion", return_value=SimpleNamespace(build=build, product_type=product_type), create=True):
                detected = checker.detect_current_system()
                self.assertEqual(detected["target"], "windows-x86_64")
                self.assertEqual(detected["variant"], expected_variant)

    @unittest.skipUnless(importlib.util.find_spec("tkinter"), "Tkinter unavailable")
    def test_desktop_ui_module_imports(self):
        from nova_builder.ui import NovaBuilderApp

        self.assertTrue(NovaBuilderApp)

    def test_project_creation_writes_valid_manifest_and_python_source(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project = create_project(Path(tmpdir) / "HelloNova", "HelloNova")
            manifest = load_manifest(project / "nova.json")
            self.assertEqual(manifest.app_name, "HelloNova")
            self.assertTrue((project / "src" / "main.py").is_file())
            result = BuildSystem.with_default_adapters().build(project)
            self.assertTrue(result.success, result.errors)

    def test_manifest_schema_rejects_wrong_types_and_mismatched_target(self):
        raw = json.loads((self.sample_dir / "nova.json").read_text(encoding="utf-8"))
        raw["app"]["platforms"] = ["windows"]
        raw["build"]["target"] = "linux-debian-x86_64"

        errors = validate_manifest(raw)
        self.assertTrue(any("target" in error.lower() for error in errors))

        raw["app"]["version"] = 1
        self.assertTrue(validate_manifest(raw))

    def test_python_build_compiles_project_and_reports_syntax_errors(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir) / "valid"
            (project / "src").mkdir(parents=True)
            (project / "src" / "main.py").write_text("print('ok')\n", encoding="utf-8")
            shutil.copy(self.sample_dir / "nova.json", project / "nova.json")
            raw = json.loads((project / "nova.json").read_text(encoding="utf-8"))
            raw["app"]["name"] = "BuildTest"
            raw["app"]["id"] = "com.example.buildtest"
            (project / "nova.json").write_text(json.dumps(raw), encoding="utf-8")

            result = BuildSystem.with_default_adapters().build(project, "linux-debian-x86_64")
            self.assertTrue(result.success, result.errors)
            self.assertTrue(Path(result.output_path).exists())

            (project / "src" / "main.py").write_text("def broken(:\n", encoding="utf-8")
            result = BuildSystem.with_default_adapters().build(project, "linux-debian-x86_64")
            self.assertFalse(result.success)
            self.assertTrue(result.errors)

    @unittest.skipUnless(any(shutil.which(name) for name in ("cc", "gcc", "clang", "cl")), "C compiler unavailable")
    def test_c_adapter_builds_executable(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir)
            (project / "src").mkdir()
            (project / "src" / "main.c").write_text("int main(void) { return 0; }\n", encoding="utf-8")
            (project / "src" / "extra.c").write_text("int helper(void) { return 1; }\n", encoding="utf-8")
            raw = json.loads((self.sample_dir / "nova.json").read_text(encoding="utf-8"))
            raw["app"].update({"name": "CTest", "id": "com.example.ctest", "language": "c", "entryPoint": "src/main.c"})
            current = PlatformCompatibilityChecker().detect_current_system()
            raw["app"]["platforms"] = [current["platform"]]
            raw["build"].update({"toolchain": "c", "target": current["target"]})
            raw["package"].update({"launcher": "bin/CTest"})
            (project / "nova.json").write_text(json.dumps(raw), encoding="utf-8")

            result = BuildSystem.with_default_adapters().build(project, current["target"])
            self.assertTrue(result.success, result.errors)
            self.assertTrue(Path(result.output_path).is_file())

    @unittest.skipUnless(any(shutil.which(name) for name in ("cc", "gcc", "clang", "cl")), "C compiler unavailable")
    def test_c_project_packages_and_runs_compiled_artifact(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir) / "c-project"
            (project / "src").mkdir(parents=True)
            (project / "src" / "main.c").write_text("int main(void) { return 0; }\n", encoding="utf-8")
            raw = json.loads((self.sample_dir / "nova.json").read_text(encoding="utf-8"))
            raw["app"].update({"name": "CPackage", "id": "com.example.cpackage", "language": "c", "entryPoint": "src/main.c"})
            current = PlatformCompatibilityChecker().detect_current_system()
            raw["app"]["platforms"] = [current["platform"]]
            raw["build"].update({"toolchain": "c", "target": current["target"]})
            raw["package"].update({"launcher": "bin/CPackage"})
            (project / "nova.json").write_text(json.dumps(raw), encoding="utf-8")

            package_path = Path(tmpdir) / "CPackage.nova"
            plan = NovaProjectPackager(project).package_project(package_path)
            self.assertEqual(plan.launcher, "bin/CPackage")
            result = NovaRuntime().launch(package_path, dry_run=False, trusted=True)
            self.assertEqual(result.returncode, 0)

    def test_package_excludes_output_and_detects_tampering(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir) / "project"
            shutil.copytree(self.sample_dir, project, ignore=shutil.ignore_patterns("output", "__pycache__"))
            output = project / "dist" / "sample.nova"
            NovaPackageBuilder(project).build(output)
            self.assertEqual(validate_package_structure(output), [])
            if os.name == "posix":
                self.assertEqual(stat.S_IMODE(output.stat().st_mode), 0o644)
            tampered = Path(tmpdir) / "tampered.nova"
            with zipfile.ZipFile(output, "r") as source, zipfile.ZipFile(tampered, "w") as destination:
                for info in source.infolist():
                    contents = source.read(info.filename)
                    if info.filename == "src/main.py":
                        contents = b"tampered\n"
                    destination.writestr(info, contents)
            self.assertTrue(any("SHA-256 mismatch" in error for error in validate_package_structure(tampered)))

    def test_package_rejects_traversal_paths(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            package = Path(tmpdir) / "unsafe.nova"
            with zipfile.ZipFile(package, "w") as archive:
                archive.writestr("../outside.txt", "unsafe")
            self.assertTrue(any("Unsafe package path" in error for error in validate_package_structure(package)))

    def test_package_rejects_symlink_entries(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            package = Path(tmpdir) / "symlink.nova"
            info = zipfile.ZipInfo("linked-file")
            info.create_system = 3
            info.external_attr = (stat.S_IFLNK | 0o777) << 16
            with zipfile.ZipFile(package, "w") as archive:
                archive.writestr(info, "target")
            self.assertTrue(any("Symbolic links" in error for error in validate_package_structure(package)))

    def test_package_rejects_oversized_entries(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            package = Path(tmpdir) / "large.nova"
            with zipfile.ZipFile(package, "w") as archive:
                archive.writestr("large.bin", b"1234")
            with patch("nova_builder.package_format.MAX_ENTRY_BYTES", 3):
                self.assertTrue(any("512 MiB limit" in error for error in validate_package_structure(package)))

    def test_package_rejects_suspicious_compression_ratio(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            package = Path(tmpdir) / "compressed.nova"
            with zipfile.ZipFile(package, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
                archive.writestr("repeated.txt", b"0" * 1024 * 1024)
            self.assertTrue(any("Compression ratio limit" in error for error in validate_package_structure(package)))

    def test_package_requires_nova_extension(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            artifact = Path(tmpdir) / "builder.whl"
            artifact.write_bytes(b"not a nova package")
            self.assertEqual(validate_package_structure(artifact), ["NOVA package file must use the .nova extension"])

    def test_runtime_launches_only_after_explicit_trust(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir) / "project"
            shutil.copytree(self.sample_dir, project, ignore=shutil.ignore_patterns("output", "__pycache__"))
            current = PlatformCompatibilityChecker().detect_current_system()
            raw = json.loads((project / "nova.json").read_text(encoding="utf-8"))
            raw["app"]["platforms"] = [current["platform"]]
            raw["build"]["target"] = current["target"]
            (project / "nova.json").write_text(json.dumps(raw), encoding="utf-8")
            package = Path(tmpdir) / "sample.nova"
            NovaPackageBuilder(project).build(package)
            runtime = NovaRuntime()

            with self.assertRaises(PermissionError):
                runtime.launch(package, dry_run=False)

            result = runtime.launch(package, dry_run=False, trusted=True)
            self.assertEqual(result.returncode, 0)

    def test_runtime_rejects_unsatisfied_python_version(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir) / "project"
            shutil.copytree(self.sample_dir, project, ignore=shutil.ignore_patterns("output", "__pycache__"))
            current = PlatformCompatibilityChecker().detect_current_system()
            raw = json.loads((project / "nova.json").read_text(encoding="utf-8"))
            raw["app"]["platforms"] = [current["platform"]]
            raw["build"]["target"] = current["target"]
            raw["runtime"]["required"] = ["python>=99.0"]
            (project / "nova.json").write_text(json.dumps(raw), encoding="utf-8")
            package = Path(tmpdir) / "new-python-required.nova"
            NovaPackageBuilder(project).build(package)

            with self.assertRaisesRegex(RuntimeError, "requires Python"):
                NovaRuntime().launch(package, dry_run=False, trusted=True)


if __name__ == '__main__':
    unittest.main()
