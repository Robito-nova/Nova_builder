"""NOVA Builder package with lazy-loaded public APIs."""

from importlib import import_module

_EXPORTS = {
    "NovaManifest": (".manifest", "NovaManifest"),
    "validate_manifest": (".manifest", "validate_manifest"),
    "NovaPackageBuilder": (".package_format", "NovaPackageBuilder"),
    "validate_package_structure": (".package_format", "validate_package_structure"),
    "BuildContext": (".build_system", "BuildContext"),
    "BuildResult": (".build_system", "BuildResult"),
    "BuildSystem": (".build_system", "BuildSystem"),
    "LanguageAdapter": (".build_system", "LanguageAdapter"),
    "CAdapter": (".build_adapters", "CAdapter"),
    "PythonAdapter": (".build_adapters", "PythonAdapter"),
    "ExecutionPlan": (".phase_two_runtime", "ExecutionPlan"),
    "NovaProjectPackager": (".phase_two_runtime", "NovaProjectPackager"),
    "NovaRuntime": (".phase_two_runtime", "NovaRuntime"),
    "PlatformCompatibilityChecker": (".platform_compatibility", "PlatformCompatibilityChecker"),
}

__all__ = list(_EXPORTS)


def __getattr__(name: str):
    try:
        module_name, attribute_name = _EXPORTS[name]
    except KeyError as error:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from error
    module = import_module(module_name, __name__)
    value = getattr(module, attribute_name)
    globals()[name] = value
    return value
