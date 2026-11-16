from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk

class NovaBuilderApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("NOVA Builder")
        self.root.geometry("1180x720")
        self.root.minsize(900, 560)
        self.project_root: Path | None = None
        self.current_file: Path | None = None
        self.tree_paths: dict[str, Path] = {}
        self.loaded_tree_nodes: set[str] = set()
        self._build_layout()
        self.root.bind("<Control-s>", lambda _event: self.save_file())

    def _build_layout(self) -> None:
        toolbar = ttk.Frame(self.root, padding=(8, 6))
        toolbar.pack(fill="x")
        ttk.Button(toolbar, text="New Project", command=self.new_project).pack(side="left", padx=(0, 6))
        ttk.Button(toolbar, text="Open Project", command=self.open_project).pack(side="left", padx=(0, 6))
        ttk.Button(toolbar, text="Save", command=self.save_file).pack(side="left", padx=6)
        ttk.Button(toolbar, text="Build", command=self.build_project).pack(side="left", padx=6)
        ttk.Button(toolbar, text="Import Files", command=self.import_files).pack(side="left", padx=6)
        ttk.Button(toolbar, text="Package…", command=self.open_package_dialog).pack(side="left", padx=6)
        self.status = ttk.Label(toolbar, text="No project open")
        self.status.pack(side="right")

        main = ttk.Panedwindow(self.root, orient="horizontal")
        main.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        explorer = ttk.Frame(main, width=230)
        editor_area = ttk.Frame(main)
        main.add(explorer, weight=1)
        main.add(editor_area, weight=5)

        ttk.Label(explorer, text="Project Explorer").pack(anchor="w", pady=(0, 4))
        self.project_tree = ttk.Treeview(explorer, show="tree")
        self.project_tree.pack(fill="both", expand=True)
        self.project_tree.bind("<Double-1>", self._open_selected_file)
        self.project_tree.bind("<<TreeviewOpen>>", self._expand_tree_node)

        vertical = ttk.Panedwindow(editor_area, orient="vertical")
        vertical.pack(fill="both", expand=True)
        self.editor = tk.Text(vertical, wrap="none", undo=True, font=("TkFixedFont", 10))
        vertical.add(self.editor, weight=4)
        self.output_tabs = ttk.Notebook(vertical)
        vertical.add(self.output_tabs, weight=1)

        self.build_output = self._make_output_tab("Build Output")
        self.problems_output = self._make_output_tab("Problems")
        terminal_tab = ttk.Frame(self.output_tabs)
        self.terminal_output = tk.Text(terminal_tab, height=7, wrap="word", state="disabled")
        self.terminal_output.pack(fill="both", expand=True)
        command_row = ttk.Frame(terminal_tab, padding=4)
        command_row.pack(fill="x")
        self.terminal_command = ttk.Entry(command_row)
        self.terminal_command.pack(side="left", fill="x", expand=True)
        self.terminal_command.bind("<Return>", self._run_terminal_command)
        ttk.Button(command_row, text="Run", command=self._run_terminal_command).pack(side="left", padx=(6, 0))
        self.output_tabs.add(terminal_tab, text="Terminal")

    def _make_output_tab(self, title: str) -> tk.Text:
        frame = ttk.Frame(self.output_tabs)
        output = tk.Text(frame, height=7, wrap="word", state="disabled")
        output.pack(fill="both", expand=True)
        self.output_tabs.add(frame, text=title)
        return output

    def open_project(self) -> None:
        selected = filedialog.askdirectory(title="Open NOVA project")
        if not selected:
            return
        path = Path(selected).resolve()
        if not (path / "nova.json").is_file():
            messagebox.showerror("Invalid project", "Selected folder does not contain nova.json")
            return
        self.project_root = path
        self.status.configure(text=str(path))
        self._populate_tree()

    def new_project(self) -> None:
        parent = filedialog.askdirectory(title="Choose project location")
        if not parent:
            return
        name = simpledialog.askstring("New NOVA project", "Project name:", parent=self.root)
        if not name:
            return
        language = simpledialog.askstring("Project language", "Choose python or c:", initialvalue="python", parent=self.root)
        if not language:
            return
        try:
            from .project_manager import create_project

            project = create_project(Path(parent) / name, name, language.strip().lower())
        except (OSError, ValueError) as error:
            messagebox.showerror("Project creation failed", str(error))
            return
        self.project_root = project
        self.status.configure(text=str(project))
        self._populate_tree()

    def _populate_tree(self) -> None:
        self.project_tree.delete(*self.project_tree.get_children())
        self.tree_paths.clear()
        self.loaded_tree_nodes.clear()
        if self.project_root is None:
            return
        root_id = self.project_tree.insert("", "end", text=self.project_root.name, open=True)
        self.tree_paths[root_id] = self.project_root
        self._load_tree_children(root_id)

    def _expand_tree_node(self, _event=None) -> None:
        item_id = self.project_tree.focus()
        if item_id:
            self._load_tree_children(item_id)

    def _load_tree_children(self, parent_id: str) -> None:
        if parent_id in self.loaded_tree_nodes:
            return
        folder = self.tree_paths.get(parent_id)
        if folder is None or not folder.is_dir():
            return
        self.loaded_tree_nodes.add(parent_id)

        try:
            children = sorted(folder.iterdir(), key=lambda item: (item.is_file(), item.name.lower()))
        except OSError:
            return
        for child in children:
            if child.name in {".git", ".venv", "venv", "__pycache__", "build", "dist"} or child.is_symlink():
                continue
            item_id = self.project_tree.insert(parent_id, "end", text=child.name, open=False)
            self.tree_paths[item_id] = child
            if child.is_dir():
                self.project_tree.insert(item_id, "end", text="")

    def _open_selected_file(self, _event=None) -> None:
        selection = self.project_tree.selection()
        if not selection:
            return
        path = self.tree_paths.get(selection[0])
        if path is None or not path.is_file():
            return
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as error:
            messagebox.showerror("Cannot open file", str(error))
            return
        self.current_file = path
        self.editor.delete("1.0", "end")
        self.editor.insert("1.0", content)
        self.status.configure(text=str(path))

    def save_file(self) -> None:
        if self.current_file is None:
            return
        self.current_file.write_text(self.editor.get("1.0", "end-1c"), encoding="utf-8")
        self.status.configure(text=f"Saved {self.current_file}")

    def build_project(self) -> None:
        if self.project_root is None:
            messagebox.showinfo("NOVA Builder", "Open a project first")
            return
        from .build_system import BuildSystem

        self._start_job("Build", lambda: BuildSystem.with_default_adapters().build(self.project_root))

    def package_project(self) -> None:
        self.open_package_dialog()

    def import_files(self) -> None:
        if self.project_root is None:
            messagebox.showinfo("NOVA Builder", "Open a project first")
            return
        paths = filedialog.askopenfilenames(title="Add project files")
        if not paths:
            return
        imported_dir = self.project_root / "assets" / "imported"
        imported_dir.mkdir(parents=True, exist_ok=True)
        copied = []
        try:
            for value in paths:
                source = Path(value)
                if not source.is_file() or source.is_symlink():
                    continue
                destination = self._unique_destination(imported_dir / source.name)
                shutil.copy2(source, destination)
                copied.append(destination.name)
        except OSError as error:
            messagebox.showerror("Import failed", str(error))
            return
        self._populate_tree()
        self.status.configure(text=f"Imported {len(copied)} file(s)")
        self._set_text(self.build_output, "Imported files:\n" + "\n".join(copied))

    @staticmethod
    def _unique_destination(destination: Path) -> Path:
        if not destination.exists():
            return destination
        index = 2
        while True:
            candidate = destination.with_name(f"{destination.stem}-{index}{destination.suffix}")
            if not candidate.exists():
                return candidate
            index += 1

    def open_package_dialog(self) -> None:
        if self.project_root is None:
            messagebox.showinfo("NOVA Builder", "Open a project first")
            return
        PackageDialog(self)

    def _start_job(self, label: str, job) -> None:
        self.status.configure(text=f"{label} running...")
        self._set_text(self.build_output, f"{label} started\n")

        def run_job() -> None:
            try:
                result = job()
                self.root.after(0, self._job_finished, label, result, None)
            except Exception as error:
                self.root.after(0, self._job_finished, label, None, error)

        threading.Thread(target=run_job, daemon=True).start()

    def _job_finished(self, label: str, result, error: Exception | None) -> None:
        if error is not None:
            self.status.configure(text=f"{label} failed")
            self._set_text(self.problems_output, str(error))
            return
        if hasattr(result, "errors") and not result.success:
            self.status.configure(text=f"{label} failed")
            self._set_text(self.problems_output, "\n".join(result.errors))
            self._set_text(self.build_output, "\n".join(result.logs + result.errors))
            return
        self.status.configure(text=f"{label} complete")
        if hasattr(result, "logs"):
            self._set_text(self.build_output, "\n".join(result.logs))
            self._set_text(self.problems_output, "\n".join(result.warnings))
        else:
            self._set_text(self.build_output, f"Created {result.package_path} for {result.target}")
            self._set_text(self.problems_output, "")

    @staticmethod
    def _set_text(widget: tk.Text, value: str) -> None:
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", value)
        widget.configure(state="disabled")

    def _run_terminal_command(self, _event=None) -> None:
        command_text = self.terminal_command.get().strip()
        self.terminal_command.delete(0, "end")
        if not command_text:
            return
        if self.project_root is None:
            self._append_terminal("Open a project before running commands.\n")
            return

        project_root = self.project_root
        self._append_terminal(f"$ {command_text}\n")

        def execute() -> None:
            try:
                completed = subprocess.run(
                    shlex.split(command_text),
                    cwd=project_root,
                    capture_output=True,
                    text=True,
                    timeout=60,
                    check=False,
                    shell=False,
                )
                output = f"{completed.stdout}{completed.stderr}\n[exit {completed.returncode}]\n"
            except (OSError, subprocess.TimeoutExpired, ValueError) as error:
                output = f"{error}\n"
            self.root.after(0, self._append_terminal, output)

        threading.Thread(target=execute, daemon=True).start()

    def _append_terminal(self, value: str) -> None:
        self.terminal_output.configure(state="normal")
        self.terminal_output.insert("end", value)
        self.terminal_output.see("end")
        self.terminal_output.configure(state="disabled")


class PackageDialog:
    def __init__(self, app: NovaBuilderApp):
        from .format_packager import ProjectFormatPackager

        self.app = app
        self.root = app.root
        self.project_root = app.project_root
        self.packager = ProjectFormatPackager(self.project_root)
        self.options = {option.key: option for option in self.packager.available_formats()}

        self.window = tk.Toplevel(self.root)
        self.window.title("Package Project")
        self.window.geometry("700x510")
        self.window.minsize(620, 440)
        self.window.transient(self.root)

        self._build_layout()
        self._populate_formats()

    def _build_layout(self) -> None:
        content = ttk.Frame(self.window, padding=16)
        content.pack(fill="both", expand=True)

        ttk.Label(content, text="Package project", font=("TkDefaultFont", 16, "bold")).pack(anchor="w")
        ttk.Label(
            content,
            text=f"{self.project_root}  ·  Select an output format and destination.",
            wraplength=650,
        ).pack(anchor="w", pady=(4, 14))

        formats = ttk.LabelFrame(content, text="Output format", padding=(10, 8))
        formats.pack(fill="both", expand=True)
        self.format_tree = ttk.Treeview(
            formats,
            columns=("extension", "availability"),
            show="tree headings",
            height=9,
            selectmode="browse",
        )
        self.format_tree.heading("#0", text="Package")
        self.format_tree.heading("extension", text="Extension")
        self.format_tree.heading("availability", text="Status")
        self.format_tree.column("#0", width=260, stretch=True)
        self.format_tree.column("extension", width=120, anchor="center", stretch=False)
        self.format_tree.column("availability", width=110, anchor="center", stretch=False)
        self.format_tree.tag_configure("ready", foreground="#16724a")
        self.format_tree.tag_configure("unavailable", foreground="#777777")
        self.format_tree.pack(fill="both", expand=True)
        self.format_tree.bind("<<TreeviewSelect>>", self._format_selected)

        self.reason = ttk.Label(content, text="Choose a format to see its requirements.", wraplength=650, justify="left")
        self.reason.pack(fill="x", pady=(10, 6))
        self.progress = ttk.Progressbar(content, mode="indeterminate")
        self.progress.pack(fill="x", pady=(4, 8))

        actions = ttk.Frame(content)
        actions.pack(fill="x")
        ttk.Button(actions, text="Close", command=self.window.destroy).pack(side="right")
        self.package_button = ttk.Button(actions, text="Choose destination…", command=self._start_packaging)
        self.package_button.pack(side="right", padx=(0, 8))
        self.package_button.state(["disabled"])

    def _populate_formats(self) -> None:
        first_available = None
        for key, option in self.options.items():
            available = "Ready" if option.available else "Unavailable"
            tag = "ready" if option.available else "unavailable"
            row = self.format_tree.insert("", "end", iid=key, text=option.label, values=(option.extension, available), tags=(tag,))
            if option.available and first_available is None:
                first_available = row
        if first_available:
            self.format_tree.selection_set(first_available)
            self._show_option(self.options[first_available])

    def _format_selected(self, _event=None) -> None:
        selection = self.format_tree.selection()
        if not selection:
            return
        self._show_option(self.options[selection[0]])

    def _show_option(self, option) -> None:
        if option.available:
            self.reason.configure(text=f"Available on this system. Output: {option.extension}")
            self.package_button.state(["!disabled"])
        else:
            self.reason.configure(text=f"Unavailable: {option.reason}")
            self.package_button.state(["disabled"])

    def _start_packaging(self) -> None:
        from .format_packager import ProjectFormatPackager

        selection = self.format_tree.selection()
        if not selection:
            return
        option = self.options[selection[0]]
        if not option.available:
            return
        default_name = f"{self.project_root.name}{option.extension}"
        output = filedialog.asksaveasfilename(
            parent=self.window,
            title=f"Save {option.label}",
            initialfile=default_name,
            defaultextension=option.extension,
            filetypes=[(option.label, f"*{option.extension}")],
        )
        if not output:
            return
        output_path = Path(output)
        if output_path.suffix.lower() != option.extension.lower():
            output_path = output_path.with_suffix(option.extension)

        self.package_button.state(["disabled"])
        self.progress.start(12)
        self.reason.configure(text=f"Building and creating {output_path.name}…")
        project_root = self.project_root

        def run_job() -> None:
            try:
                result = ProjectFormatPackager(project_root).package(option.key, output_path)
                self.root.after(0, self._finished, result, None)
            except Exception as error:
                self.root.after(0, self._finished, None, error)

        threading.Thread(target=run_job, daemon=True).start()

    def _finished(self, output: Path | None, error: Exception | None) -> None:
        self.progress.stop()
        self.package_button.state(["!disabled"])
        if error is not None:
            self.reason.configure(text=f"Packaging failed: {error}")
            self.app.status.configure(text="Packaging failed")
            self.app._set_text(self.app.problems_output, str(error))
            return
        self.reason.configure(text=f"Package created: {output}")
        self.app.status.configure(text=f"Packaged {output.name}")
        self.app._set_text(self.app.build_output, f"Created package:\n{output}")


def run_ui() -> None:
    root = tk.Tk()
    app = NovaBuilderApp(root)
    root.mainloop()
