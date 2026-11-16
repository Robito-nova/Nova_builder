import shutil
import subprocess
import tempfile
import unittest
import json
from pathlib import Path
import zipfile

from nova_builder.format_packager import ProjectFormatPackager
from nova_builder.project_manager import create_project


class ProjectFormatPackagerTests(unittest.TestCase):
    def setUp(self):
        self.project = Path(__file__).resolve().parents[1] / "examples" / "sample_app"
        self.packager = ProjectFormatPackager(self.project)

    def test_format_catalog_explains_supported_and_unsupported_formats(self):
        options = {option.key: option for option in self.packager.available_formats()}

        self.assertTrue(options["nova"].available)
        self.assertTrue(options["run"].available)
        self.assertFalse(options["pkg"].available)
        self.assertIn("Apple", options["pkg"].reason)
        self.assertFalse(options["app"].available)
        self.assertFalse(options["flatpak"].available)
        self.assertFalse(options["jar"].available)
        self.assertFalse(options["appimage"].available)

    def test_run_package_extracts_payload(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            package = self.packager.package("run", root / "sample.run")
            target = root / "installed"
            completed = subprocess.run(
                [str(package), str(target)],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertTrue((target / "opt" / "novasampleapp" / "project" / "nova.json").is_file())

    @unittest.skipUnless(shutil.which("dpkg-deb"), "dpkg-deb unavailable")
    def test_deb_package_is_readable_by_dpkg(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            package = self.packager.package("deb", Path(temp_dir) / "sample.deb")
            completed = subprocess.run(
                ["dpkg-deb", "--field", str(package), "Package"],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(completed.stdout.strip(), "novasampleapp")

    def test_unavailable_format_cannot_be_packaged(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaisesRegex(RuntimeError, "Apple platforms"):
                self.packager.package("pkg", Path(temp_dir) / "sample.pkg")

    def test_linux_installer_formats_require_matching_linux_target(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir) / "project"
            shutil.copytree(self.project, project, ignore=shutil.ignore_patterns("output", "__pycache__"))
            manifest_path = project / "nova.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["build"]["target"] = "windows-x86_64"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            options = {option.key: option for option in ProjectFormatPackager(project).available_formats()}
            self.assertFalse(options["deb"].available)
            self.assertFalse(options["run"].available)

    @unittest.skipUnless(shutil.which("dpkg-deb"), "dpkg-deb unavailable")
    def test_gui_deb_installs_desktop_entry_icon_and_dependencies(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project = create_project(Path(temp_dir) / "NOVA Builder", "NOVA Builder")
            manifest_path = project / "nova.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["app"].update({"id": "org.nova.nova-builder", "type": "desktop", "developer": "Robin Güneş"})
            manifest["dependencies"]["system"] = ["python3-jsonschema", "python3-tk"]
            manifest["package"]["icon"] = "assets/icons/nova-builder.svg"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            icon_path = project / "assets" / "icons" / "nova-builder.svg"
            icon_path.parent.mkdir(parents=True, exist_ok=True)
            icon_path.write_text("<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 16 16\"><rect width=\"16\" height=\"16\"/></svg>\n", encoding="utf-8")

            package = ProjectFormatPackager(project).package("deb", Path(temp_dir) / "nova-builder.deb")
            with tempfile.TemporaryDirectory() as extract_dir:
                subprocess.run(["dpkg-deb", "-x", str(package), extract_dir], check=True)
                subprocess.run(["dpkg-deb", "-e", str(package), str(Path(extract_dir) / "control")], check=True)
                desktop_file = Path(extract_dir) / "usr" / "share" / "applications" / "nova-builder.desktop"
                self.assertIn("Exec=/usr/bin/nova-builder", desktop_file.read_text(encoding="utf-8"))
                self.assertIn("Icon=nova-builder", desktop_file.read_text(encoding="utf-8"))
                self.assertTrue((Path(extract_dir) / "usr" / "share" / "icons" / "hicolor" / "scalable" / "apps" / "nova-builder.svg").is_file())
                control = (Path(extract_dir) / "control" / "control").read_text(encoding="utf-8")
                self.assertIn("Depends: python3, python3-jsonschema, python3-tk", control)
                package_contents = subprocess.run(["dpkg-deb", "--contents", str(package)], capture_output=True, text=True, check=True).stdout
                self.assertNotIn("/project/tests/", package_contents)


if __name__ == "__main__":
    unittest.main()
