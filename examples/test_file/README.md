# Test File

Small C CLI example for NOVA packaging.

Build and package from the repository root:

```bash
python -m nova_builder validate examples/test_file/nova.json
python -m nova_builder build examples/test_file
```

The GUI package selector can create a Debian `.deb` from this project on a Debian x86_64 host with `dpkg-deb` installed.
