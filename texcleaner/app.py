"""Cross-platform CustomTkinter interface for TeXCleaner."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import filedialog

import customtkinter as ctk

from .version import __version__
from .wrapper import (
    clean_arxiv,
    clean_changes,
    clean_trackchanges,
    detect_cleaning_module,
    generate_output_filename,
    is_valid_output_suffix,
)


def asset_path(name: str) -> Path:
    """Resolve a packaged asset in both source and PyInstaller layouts."""
    source_path = Path(__file__).resolve().parent / "assets" / name
    if source_path.is_file():
        return source_path
    frozen_root = getattr(sys, "_MEIPASS", None)
    if frozen_root:
        return Path(frozen_root) / "texcleaner" / "assets" / name
    return source_path


def validate_tex_path(value: str) -> tuple[bool, str]:
    if not value.strip():
        return False, "Select an input file."
    path = Path(value).expanduser()
    if not path.exists():
        return False, f"Path not found: {path}"
    if not path.is_file():
        return False, "The selected path is not a file."
    if path.suffix.lower() != ".tex":
        return False, "The input file must have a .tex extension."
    return True, ""


def validate_folder_path(value: str) -> tuple[bool, str]:
    if not value.strip():
        return False, "Select a project folder."
    path = Path(value).expanduser()
    if not path.exists():
        return False, f"Folder not found: {path}"
    if not path.is_dir():
        return False, "The selected path is not a folder."
    return True, ""


def open_in_file_manager(path: str) -> None:
    """Reveal an output using the native file manager."""
    output = Path(path).resolve()
    if sys.platform == "win32":
        os.startfile(output if output.is_dir() else output.parent)  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        command = ["open", str(output)] if output.is_dir() else ["open", "-R", str(output)]
        subprocess.Popen(command)
    else:
        subprocess.Popen(["xdg-open", str(output if output.is_dir() else output.parent)])


class LabeledEntry(ctk.CTkFrame):
    def __init__(self, master, label: str, variable, *, width: int = 150, suffix: str = ""):
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self, text=label, anchor="w").grid(row=0, column=0, sticky="w")
        self.entry = ctk.CTkEntry(self, textvariable=variable, width=width)
        self.entry.grid(row=0, column=1, padx=(12, 0), sticky="e")
        if suffix:
            ctk.CTkLabel(self, text=suffix, text_color=("gray45", "gray65")).grid(
                row=0, column=2, padx=(6, 0)
            )


class CleanerTab(ctk.CTkFrame):
    """Shared layout and thread-safe UI helpers for cleaner tabs."""

    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(5, weight=1)

    @staticmethod
    def panel(parent, title: str) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(parent, corner_radius=12)
        frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(frame, text=title, font=ctk.CTkFont(size=15, weight="bold"), anchor="w").grid(
            row=0, column=0, padx=16, pady=(12, 8), sticky="ew"
        )
        return frame

    @staticmethod
    def set_log(textbox: ctk.CTkTextbox, text: str, *, append: bool = False) -> None:
        textbox.configure(state="normal")
        if not append:
            textbox.delete("1.0", "end")
        textbox.insert("end", text)
        textbox.see("end")
        textbox.configure(state="disabled")

    def add_log_area(self) -> None:
        self.status = ctk.CTkLabel(self, text="Ready", anchor="w", text_color=("gray35", "gray70"))
        self.status.grid(row=4, column=0, padx=18, pady=(0, 8), sticky="ew")
        self.log = ctk.CTkTextbox(self, wrap="word", font=ctk.CTkFont(family="Courier", size=12))
        self.log.grid(row=5, column=0, padx=18, pady=(0, 16), sticky="nsew")
        self.log.configure(state="disabled")

    def begin(self, initial_log: str) -> None:
        self.set_log(self.log, initial_log)
        self.clean_button.configure(state="disabled")
        self.progress.pack(side="left", padx=14)
        self.progress.start()
        self.status.configure(text="Working…", text_color=("gray35", "gray70"))

    def finish(self, success: bool, message: str, output_path: str) -> None:
        self.progress.stop()
        self.progress.pack_forget()
        self.clean_button.configure(state="normal")
        self.append_log(f"\n{message}\n")
        if success:
            self.status.configure(
                text=f"Completed: {output_path}",
                text_color=("#267326", "#67c267"),
            )
        else:
            self.show_error(message, append_log=False)

    def append_log(self, message: str) -> None:
        self.set_log(self.log, message, append=True)

    def show_error(self, message: str, *, append_log: bool = True) -> None:
        self.status.configure(text=message, text_color="#d9534f")
        if append_log:
            self.append_log(f"ERROR: {message}\n")

    def copy_output_path(self, path: str) -> None:
        self.clipboard_clear()
        self.clipboard_append(path)
        self.status.configure(text="Output path copied", text_color=("gray35", "gray70"))

    def add_output_actions(self, parent, path_getter) -> None:
        ctk.CTkButton(
            parent,
            text="Open Output",
            width=115,
            command=lambda: self._open_output(path_getter()),
        ).pack(side="right", padx=(6, 0))
        ctk.CTkButton(
            parent,
            text="Copy Path",
            width=100,
            command=lambda: self.copy_output_path(path_getter()),
        ).pack(side="right", padx=(6, 0))

    def _open_output(self, path: str) -> None:
        if not path:
            self.show_error("No output path is available yet.")
            return
        try:
            open_in_file_manager(path)
        except OSError as error:
            self.show_error(f"Could not open the output location: {error}")


class TrackChangesTab(CleanerTab):
    def __init__(self, master):
        super().__init__(master)
        self.input_path = ctk.StringVar()
        self.cleaner_choice = ctk.StringVar(value="Auto detect")
        self.revision_choice = ctk.StringVar(value="Keep new text")
        self.remove_annotations = ctk.BooleanVar(value=True)
        self.output_suffix = ctk.StringVar(value="-cleaned")
        self.overwrite = ctk.BooleanVar(value=False)
        self.completed_output = ""

        ctk.CTkLabel(
            self,
            text="Clean LaTeX Track Changes",
            font=ctk.CTkFont(size=24, weight="bold"),
            anchor="w",
        ).grid(row=0, column=0, padx=18, pady=(16, 12), sticky="ew")

        path_frame = self.panel(self, "Input file")
        path_frame.grid(row=1, column=0, padx=18, pady=(0, 12), sticky="ew")
        path_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkEntry(path_frame, textvariable=self.input_path, placeholder_text="Select a .tex file").grid(
            row=1, column=0, padx=(16, 8), pady=(0, 14), sticky="ew"
        )
        ctk.CTkButton(path_frame, text="Browse…", width=100, command=self.browse).grid(
            row=1, column=1, padx=(0, 16), pady=(0, 14)
        )

        options = ctk.CTkFrame(self, fg_color="transparent")
        options.grid(row=2, column=0, padx=18, pady=(0, 12), sticky="ew")
        options.grid_columnconfigure((0, 1), weight=1, uniform="track-options")

        cleaning = self.panel(options, "Cleaning options")
        cleaning.grid(row=0, column=0, padx=(0, 6), sticky="nsew")
        ctk.CTkLabel(cleaning, text="Cleaner", anchor="w").grid(row=1, column=0, padx=16, sticky="ew")
        ctk.CTkOptionMenu(
            cleaning,
            values=["Auto detect", "TrackChanges", "Changes"],
            variable=self.cleaner_choice,
        ).grid(row=2, column=0, padx=16, pady=(4, 10), sticky="ew")
        ctk.CTkSegmentedButton(
            cleaning,
            values=["Keep new text", "Keep old text"],
            variable=self.revision_choice,
        ).grid(row=3, column=0, padx=16, pady=(2, 10), sticky="ew")
        ctk.CTkSwitch(
            cleaning,
            text="Remove annotations and comments",
            variable=self.remove_annotations,
        ).grid(row=4, column=0, padx=16, pady=(0, 14), sticky="w")

        output = self.panel(options, "Output")
        output.grid(row=0, column=1, padx=(6, 0), sticky="nsew")
        LabeledEntry(output, "Filename suffix", self.output_suffix, width=145).grid(
            row=1, column=0, padx=16, pady=(0, 10), sticky="ew"
        )
        ctk.CTkSwitch(output, text="Replace existing output", variable=self.overwrite).grid(
            row=2, column=0, padx=16, pady=(0, 8), sticky="w"
        )
        self.output_preview = ctk.CTkLabel(output, text="", anchor="w", text_color=("gray35", "gray70"))
        self.output_preview.grid(row=3, column=0, padx=16, pady=(0, 14), sticky="ew")
        self.input_path.trace_add("write", self.update_preview)
        self.output_suffix.trace_add("write", self.update_preview)

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.grid(row=3, column=0, padx=18, pady=(0, 10), sticky="ew")
        self.clean_button = ctk.CTkButton(
            actions,
            text="Detect & Clean",
            width=170,
            height=36,
            font=ctk.CTkFont(weight="bold"),
            command=self.start_cleaning,
        )
        self.clean_button.pack(side="left")
        self.progress = ctk.CTkProgressBar(actions, mode="indeterminate", width=180)
        self.progress.set(0)
        self.add_output_actions(actions, lambda: self.completed_output)
        self.add_log_area()

    def browse(self) -> None:
        selected = filedialog.askopenfilename(
            title="Select LaTeX file",
            filetypes=[("LaTeX files", "*.tex"), ("All files", "*.*")],
        )
        if selected:
            self.input_path.set(selected)

    def update_preview(self, *_args) -> None:
        path = self.input_path.get().strip()
        suffix = self.output_suffix.get()
        if path and is_valid_output_suffix(suffix):
            text = f"Output: {Path(generate_output_filename(path, suffix)).name}"
            self.output_preview.configure(text=text, text_color=("gray35", "gray70"))
        elif suffix and not is_valid_output_suffix(suffix):
            self.output_preview.configure(text="Suffix cannot contain path separators.", text_color="#d9534f")
        else:
            self.output_preview.configure(text="", text_color=("gray35", "gray70"))

    def start_cleaning(self) -> None:
        input_path = self.input_path.get().strip()
        valid, message = validate_tex_path(input_path)
        if not valid:
            self.show_error(message)
            return
        suffix = self.output_suffix.get()
        if not is_valid_output_suffix(suffix):
            self.show_error("Enter a non-empty suffix without path separators or control characters.")
            return

        selected = self.cleaner_choice.get()
        cleaner = detect_cleaning_module(input_path) if selected == "Auto detect" else selected.lower()
        if cleaner is None:
            self.show_error("No supported markup was detected. Select a cleaner explicitly to continue.")
            return

        output_path = generate_output_filename(input_path, suffix)
        settings = {
            "accept_changes": self.revision_choice.get() == "Keep new text",
            "remove_annotations": self.remove_annotations.get(),
            "overwrite": self.overwrite.get(),
        }
        self.completed_output = ""
        self.begin(f"Cleaner: {cleaner}\nStarting cleaning…\n")
        threading.Thread(
            target=self.run_cleaning,
            args=(input_path, output_path, cleaner, settings),
            daemon=True,
        ).start()

    def run_cleaning(self, input_path: str, output_path: str, cleaner: str, settings: dict) -> None:
        callback = lambda message: self.after(0, self.append_log, message)
        try:
            function = clean_trackchanges if cleaner == "trackchanges" else clean_changes
            success, message = function(input_path, output_path, callback=callback, **settings)
        except Exception as error:
            success, message = False, f"Unexpected error: {error}"
        if success:
            self.completed_output = output_path
        self.after(0, self.finish, success, message, output_path if success else "")


class ArxivTab(CleanerTab):
    def __init__(self, master):
        super().__init__(master)
        self.folder_path = ctk.StringVar()
        self.resize_images = ctk.BooleanVar(value=True)
        self.image_size = ctk.StringVar(value="500")
        self.compress_pdf = ctk.BooleanVar(value=False)
        self.pdf_resolution = ctk.StringVar(value="500")
        self.keep_bib = ctk.BooleanVar(value=False)
        self.verbose = ctk.BooleanVar(value=False)
        self.output_suffix = ctk.StringVar(value="-cleaned")
        self.overwrite = ctk.BooleanVar(value=False)
        self.completed_output = ""

        ctk.CTkLabel(
            self,
            text="Prepare an arXiv Submission",
            font=ctk.CTkFont(size=24, weight="bold"),
            anchor="w",
        ).grid(row=0, column=0, padx=18, pady=(16, 12), sticky="ew")

        path_frame = self.panel(self, "Project folder")
        path_frame.grid(row=1, column=0, padx=18, pady=(0, 12), sticky="ew")
        path_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkEntry(
            path_frame,
            textvariable=self.folder_path,
            placeholder_text="Select a LaTeX project folder",
        ).grid(row=1, column=0, padx=(16, 8), pady=(0, 14), sticky="ew")
        ctk.CTkButton(path_frame, text="Browse…", width=100, command=self.browse).grid(
            row=1, column=1, padx=(0, 16), pady=(0, 14)
        )

        options = ctk.CTkFrame(self, fg_color="transparent")
        options.grid(row=2, column=0, padx=18, pady=(0, 12), sticky="ew")
        options.grid_columnconfigure((0, 1), weight=1, uniform="arxiv-options")

        graphics = self.panel(options, "Graphics")
        graphics.grid(row=0, column=0, padx=(0, 6), sticky="nsew")
        ctk.CTkSwitch(
            graphics,
            text="Resize raster images",
            variable=self.resize_images,
            command=self.update_option_states,
        ).grid(row=1, column=0, padx=16, pady=(0, 8), sticky="w")
        self.image_size_row = LabeledEntry(graphics, "Maximum dimension", self.image_size, width=85, suffix="px")
        self.image_size_row.grid(row=2, column=0, padx=16, pady=(0, 12), sticky="ew")
        ctk.CTkSwitch(
            graphics,
            text="Compress PDF graphics",
            variable=self.compress_pdf,
            command=self.update_option_states,
        ).grid(row=3, column=0, padx=16, pady=(0, 8), sticky="w")
        self.pdf_resolution_row = LabeledEntry(
            graphics, "PDF image resolution", self.pdf_resolution, width=85, suffix="dpi"
        )
        self.pdf_resolution_row.grid(row=4, column=0, padx=16, pady=(0, 14), sticky="ew")

        output = self.panel(options, "Cleaning and output")
        output.grid(row=0, column=1, padx=(6, 0), sticky="nsew")
        ctk.CTkSwitch(output, text="Keep BibTeX (.bib) files", variable=self.keep_bib).grid(
            row=1, column=0, padx=16, pady=(0, 8), sticky="w"
        )
        ctk.CTkSwitch(output, text="Show detailed cleaner output", variable=self.verbose).grid(
            row=2, column=0, padx=16, pady=(0, 10), sticky="w"
        )
        LabeledEntry(output, "Folder suffix", self.output_suffix, width=145).grid(
            row=3, column=0, padx=16, pady=(0, 10), sticky="ew"
        )
        ctk.CTkSwitch(output, text="Replace existing output", variable=self.overwrite).grid(
            row=4, column=0, padx=16, pady=(0, 8), sticky="w"
        )
        self.output_preview = ctk.CTkLabel(output, text="", anchor="w", text_color=("gray35", "gray70"))
        self.output_preview.grid(row=5, column=0, padx=16, pady=(0, 14), sticky="ew")
        self.folder_path.trace_add("write", self.update_preview)
        self.output_suffix.trace_add("write", self.update_preview)

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.grid(row=3, column=0, padx=18, pady=(0, 10), sticky="ew")
        self.clean_button = ctk.CTkButton(
            actions,
            text="Clean for arXiv",
            width=170,
            height=36,
            font=ctk.CTkFont(weight="bold"),
            command=self.start_cleaning,
        )
        self.clean_button.pack(side="left")
        self.progress = ctk.CTkProgressBar(actions, mode="indeterminate", width=180)
        self.progress.set(0)
        self.add_output_actions(actions, lambda: self.completed_output)
        self.add_log_area()
        self.update_option_states()

    def browse(self) -> None:
        selected = filedialog.askdirectory(title="Select LaTeX project folder")
        if selected:
            self.folder_path.set(selected)

    def update_option_states(self) -> None:
        self.image_size_row.entry.configure(state="normal" if self.resize_images.get() else "disabled")
        self.pdf_resolution_row.entry.configure(state="normal" if self.compress_pdf.get() else "disabled")

    def update_preview(self, *_args) -> None:
        folder = self.folder_path.get().strip()
        suffix = self.output_suffix.get()
        if folder and is_valid_output_suffix(suffix):
            self.output_preview.configure(
                text=f"Output: {Path(folder).name}{suffix}",
                text_color=("gray35", "gray70"),
            )
        elif suffix and not is_valid_output_suffix(suffix):
            self.output_preview.configure(text="Suffix cannot contain path separators.", text_color="#d9534f")
        else:
            self.output_preview.configure(text="", text_color=("gray35", "gray70"))

    @staticmethod
    def integer(value: str, label: str, minimum: int, maximum: int) -> int:
        try:
            parsed = int(value)
        except ValueError as error:
            raise ValueError(f"{label} must be an integer.") from error
        if not minimum <= parsed <= maximum:
            raise ValueError(f"{label} must be between {minimum:,} and {maximum:,}.")
        return parsed

    def start_cleaning(self) -> None:
        folder = self.folder_path.get().strip()
        valid, message = validate_folder_path(folder)
        if not valid:
            self.show_error(message)
            return
        suffix = self.output_suffix.get()
        if not is_valid_output_suffix(suffix):
            self.show_error("Enter a non-empty suffix without path separators or control characters.")
            return
        try:
            image_size = self.integer(self.image_size.get(), "Image size", 1, 10000)
            pdf_resolution = self.integer(self.pdf_resolution.get(), "PDF resolution", 1, 2400)
        except ValueError as error:
            self.show_error(str(error))
            return

        settings = {
            "im_size": image_size,
            "resize_images": self.resize_images.get(),
            "compress_pdf": self.compress_pdf.get(),
            "pdf_resolution": pdf_resolution,
            "keep_bib": self.keep_bib.get(),
            "verbose": self.verbose.get(),
            "output_suffix": suffix,
            "overwrite": self.overwrite.get(),
        }
        output_path = str(Path(folder).resolve().with_name(Path(folder).name + suffix))
        self.completed_output = ""
        self.begin("Starting arXiv cleaner…\n")
        threading.Thread(
            target=self.run_cleaning,
            args=(folder, output_path, settings),
            daemon=True,
        ).start()

    def run_cleaning(self, folder: str, output_path: str, settings: dict) -> None:
        callback = lambda message: self.after(0, self.append_log, message)
        try:
            success, message = clean_arxiv(folder, callback=callback, **settings)
        except Exception as error:
            success, message = False, f"Unexpected error: {error}"
        if success:
            self.completed_output = output_path
        self.after(0, self.finish, success, message, output_path if success else "")


class TeXCleanerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"TeXCleaner {__version__}")
        self._set_application_icon()
        self.geometry("980x760")
        self.minsize(780, 650)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        tabs = ctk.CTkTabview(self, anchor="nw")
        tabs.grid(row=0, column=0, padx=12, pady=12, sticky="nsew")
        track_tab = tabs.add("Track Changes")
        arxiv_tab = tabs.add("arXiv")
        for tab in (track_tab, arxiv_tab):
            tab.grid_columnconfigure(0, weight=1)
            tab.grid_rowconfigure(0, weight=1)
        TrackChangesTab(track_tab).grid(row=0, column=0, sticky="nsew")
        ArxivTab(arxiv_tab).grid(row=0, column=0, sticky="nsew")

    def _set_application_icon(self) -> None:
        png_path = asset_path("icons/texcleaner-256.png")
        ico_path = asset_path("icons/texcleaner.ico")
        try:
            if sys.platform == "win32" and ico_path.is_file():
                self.iconbitmap(str(ico_path))
            elif png_path.is_file():
                self._icon_photo = tk.PhotoImage(file=str(png_path))
                self.iconphoto(True, self._icon_photo)
        except tk.TclError:
            # A missing/unsupported window icon must not prevent the GUI from running.
            pass


def main(*, appearance: str = "Dark") -> None:
    ctk.set_appearance_mode(appearance)
    ctk.set_default_color_theme("blue")
    TeXCleanerApp().mainloop()


if __name__ == "__main__":
    main()
