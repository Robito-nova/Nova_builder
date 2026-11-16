from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="nova", description="NOVA Builder and Runtime")
    commands = parser.add_subparsers(dest="command")

    validate = commands.add_parser("validate", help="validate a nova.json manifest")
    validate.add_argument("manifest", type=Path)

    create = commands.add_parser("create", help="create a Python or C project")
    create.add_argument("path", type=Path)
    create.add_argument("name")
    create.add_argument("--language", choices=("python", "c"), default="python")
    create.add_argument("--target")

    build = commands.add_parser("build", help="build a project with its declared language adapter")
    build.add_argument("project", type=Path)
    build.add_argument("--target")

    package = commands.add_parser("package", help="build and package a project as .nova")
    package.add_argument("project", type=Path)
    package.add_argument("output", type=Path)

    verify = commands.add_parser("verify", help="verify a .nova package")
    verify.add_argument("package", type=Path)

    run = commands.add_parser("run", help="inspect or run a .nova package")
    run.add_argument("package", type=Path)
    run.add_argument("--trust", action="store_true", help="explicitly trust and execute the package")
    run.add_argument("--timeout", type=int, default=60)

    commands.add_parser("ui", help="start the NOVA desktop interface")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "validate":
        from .manifest import load_manifest

        manifest = load_manifest(args.manifest)
        print(f"Valid NOVA manifest 1.0: {manifest.app_name} {manifest.version}")
        return 0

    if args.command == "create":
        from .project_manager import create_project

        project = create_project(args.path, args.name, args.language, args.target)
        print(f"Created {args.language} project: {project}")
        return 0

    if args.command == "build":
        from .build_system import BuildSystem

        result = BuildSystem.with_default_adapters().build(args.project, args.target)
        for line in result.logs:
            print(line)
        for warning in result.warnings:
            print(f"warning: {warning}")
        for error in result.errors:
            print(f"error: {error}")
        return 0 if result.success else 1

    if args.command == "package":
        from .phase_two_runtime import NovaProjectPackager

        plan = NovaProjectPackager(args.project).package_project(args.output)
        print(f"Created {plan.package_path} for {plan.target}")
        return 0

    if args.command == "verify":
        from .package_format import validate_package_structure
        from .phase_two_runtime import NovaRuntime

        errors = validate_package_structure(args.package)
        if errors:
            for error in errors:
                print(f"error: {error}")
            return 1
        plan = NovaRuntime().inspect_package(args.package)
        print(f"Valid NOVA package: {plan.app_name} ({plan.target})")
        return 0

    if args.command == "run":
        from .phase_two_runtime import NovaRuntime

        runtime = NovaRuntime()
        if not args.trust:
            plan = runtime.inspect_package(args.package)
            print(f"Package: {plan.app_name} ({plan.target})")
            print("Declared permissions:")
            print(json.dumps(plan.permissions, indent=2, sort_keys=True))
            print("Not executed. Review the publisher and permissions, then rerun with --trust.")
            return 0
        result = runtime.launch(args.package, dry_run=False, trusted=True, timeout=args.timeout)
        if result.stdout:
            print(result.stdout, end="")
        if result.stderr:
            print(result.stderr, end="")
        return result.returncode

    if args.command == "ui":
        from .ui import run_ui

        run_ui()
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
