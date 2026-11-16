# Test File

Small C application that prints a Turkish greeting. The source filename contains a space intentionally.

From the NOVA Builder repository root, build and package it with:

```bash
python -m nova_builder validate "test file/nova.json"
python -m nova_builder build "test file"
```

The Debian package is created at `dist/testfile_1.0.0_amd64.deb` when packaging from the graphical package selector or the Python package API.
