from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from typing import Dict, Iterable, List

from .manifest import validate_manifest

CHECKSUM_PATH = "metadata/checksums.json"
MAX_PACKAGE_BYTES = 2 * 1024 * 1024 * 1024
MAX_ENTRY_BYTES = 512 * 1024 * 1024
MAX_COMPRESSION_RATIO = 250
SKIP_PARTS = {".git", ".venv", "venv", "__pycache__", "build", "dist", "output"}


class NovaPackageBuilder:
    """Create a deterministic ZIP-based `.nova` application package."""

    def __init__(self, root: str | Path):
        self.root = Path(root).resolve()

    def build(self, output_path: str | Path, manifest_path: str | Path = "nova.json") -> str:
        output_file = Path(output_path).resolve()
        if output_file.suffix.lower() != ".nova":
            raise ValueError("NOVA package output must use the .nova extension")
        manifest_file = self.root / manifest_path
        if not manifest_file.is_file():
            raise FileNotFoundError(f"Manifest not found: {manifest_file}")

        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
        errors = validate_manifest(manifest)
        if errors:
            raise ValueError("Invalid NOVA manifest: " + "; ".join(errors))
        launcher = manifest["package"]["launcher"]
        if not (self.root / PurePosixPath(launcher)).is_file():
            raise FileNotFoundError(f"Package launcher not found: {launcher}")

        output_file.parent.mkdir(parents=True, exist_ok=True)
        temp_name = None
        try:
            with tempfile.NamedTemporaryFile(prefix=".nova-", suffix=".tmp", dir=output_file.parent, delete=False) as temp:
                temp_name = temp.name
            digests: Dict[str, str] = {}
            with zipfile.ZipFile(temp_name, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9, strict_timestamps=True) as archive:
                for file_path in self._iter_files(output_file):
                    archive_name = file_path.relative_to(self.root).as_posix()
                    info = zipfile.ZipInfo(archive_name, date_time=(1980, 1, 1, 0, 0, 0))
                    info.compress_type = zipfile.ZIP_DEFLATED
                    info.external_attr = (stat.S_IFREG | 0o644) << 16
                    digest = hashlib.sha256()
                    with file_path.open("rb") as source, archive.open(info, "w", force_zip64=True) as destination:
                        while chunk := source.read(1024 * 1024):
                            digest.update(chunk)
                            destination.write(chunk)
                    digests[archive_name] = digest.hexdigest()

                checksum_bytes = (json.dumps({"algorithm": "sha256", "files": digests}, sort_keys=True, indent=2) + "\n").encode("utf-8")
                info = zipfile.ZipInfo(CHECKSUM_PATH, date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = (stat.S_IFREG | 0o644) << 16
                archive.writestr(info, checksum_bytes)

            os.replace(temp_name, output_file)
            temp_name = None
            output_file.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
        finally:
            if temp_name is not None:
                Path(temp_name).unlink(missing_ok=True)

        validation_errors = validate_package_structure(output_file)
        if validation_errors:
            output_file.unlink(missing_ok=True)
            raise ValueError("Generated invalid NOVA package: " + "; ".join(validation_errors))
        return str(output_file)

    def _iter_files(self, output_file: Path) -> Iterable[Path]:
        for path in sorted(self.root.rglob("*")):
            if not path.is_file() or path.is_symlink():
                continue
            relative = path.relative_to(self.root)
            if any(part in SKIP_PARTS for part in relative.parts):
                continue
            if relative.as_posix() == CHECKSUM_PATH:
                continue
            if path.resolve() == output_file:
                continue
            yield path


def _safe_archive_name(name: str) -> bool:
    if not name or "\\" in name or name.startswith("/"):
        return False
    if len(name) >= 2 and name[1] == ":":
        return False
    path = PurePosixPath(name)
    return not path.is_absolute() and all(part not in {"", ".", ".."} for part in path.parts)


def _sha256_member(archive: zipfile.ZipFile, name: str) -> str:
    digest = hashlib.sha256()
    with archive.open(name, "r") as member:
        while chunk := member.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def validate_package_structure(package_path: str | Path) -> List[str]:
    """Validate archive safety, the manifest, entry point, CRCs, and SHA-256 digests."""
    errors: List[str] = []
    archive_path = Path(package_path)
    if not archive_path.is_file():
        return [f"Package file does not exist: {archive_path}"]
    if archive_path.suffix.lower() != ".nova":
        return ["NOVA package file must use the .nova extension"]
    if archive_path.stat().st_size > MAX_PACKAGE_BYTES:
        return ["Package exceeds the 2 GiB size limit"]

    try:
        with zipfile.ZipFile(archive_path, "r") as archive:
            infos = archive.infolist()
            names = [info.filename for info in infos]
            if len(names) != len(set(names)):
                errors.append("Package contains duplicate paths")
            for info in infos:
                if not _safe_archive_name(info.filename):
                    errors.append(f"Unsafe package path: {info.filename}")
                mode = info.external_attr >> 16
                if stat.S_ISLNK(mode):
                    errors.append(f"Symbolic links are not allowed in packages: {info.filename}")
                if info.file_size > MAX_ENTRY_BYTES:
                    errors.append(f"Package entry exceeds the 512 MiB limit: {info.filename}")
                if info.file_size and info.compress_size == 0:
                    errors.append(f"Invalid compressed size for: {info.filename}")
                elif info.compress_size and info.file_size / info.compress_size > MAX_COMPRESSION_RATIO:
                    errors.append(f"Compression ratio limit exceeded: {info.filename}")
            if sum(info.file_size for info in infos) > MAX_PACKAGE_BYTES:
                errors.append("Uncompressed package exceeds the 2 GiB size limit")
            if errors:
                return errors

            bad_file = archive.testzip()
            if bad_file:
                return [f"CRC check failed for package entry: {bad_file}"]
            name_set = set(names)
            if "nova.json" not in name_set:
                return ["nova.json is missing from package root"]
            if CHECKSUM_PATH not in name_set:
                return [f"{CHECKSUM_PATH} is missing"]

            try:
                manifest = json.loads(archive.read("nova.json"))
            except (json.JSONDecodeError, UnicodeDecodeError) as error:
                return [f"Invalid nova.json: {error}"]
            manifest_errors = validate_manifest(manifest)
            if manifest_errors:
                return ["Invalid nova.json: " + "; ".join(manifest_errors)]
            launcher = manifest["package"]["launcher"]
            if launcher not in name_set:
                errors.append(f"Package launcher is missing: {launcher}")

            try:
                checksum_data = json.loads(archive.read(CHECKSUM_PATH))
                if checksum_data.get("algorithm") != "sha256" or not isinstance(checksum_data.get("files"), dict):
                    raise ValueError("unsupported checksum document")
            except (json.JSONDecodeError, UnicodeDecodeError, ValueError, AttributeError) as error:
                return errors + [f"Invalid checksum metadata: {error}"]

            expected_files = name_set - {CHECKSUM_PATH}
            if set(checksum_data["files"]) != expected_files:
                errors.append("Checksum file list does not match package contents")
            for name, expected_digest in checksum_data["files"].items():
                if name in name_set:
                    actual_digest = _sha256_member(archive, name)
                    if actual_digest != expected_digest:
                        errors.append(f"SHA-256 mismatch: {name}")
    except (zipfile.BadZipFile, OSError) as error:
        errors.append(f"Invalid package archive: {error}")
    return errors
