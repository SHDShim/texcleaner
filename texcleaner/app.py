#!/usr/bin/env python
"""
app.py - GUI front-end for cleaning LaTeX track changes

A simple Tkinter application to clean LaTeX documents of track changes markup
from TrackChanges, Changes, or arXiv submission packages.
"""

import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

from .wrapper import (
    clean_trackchanges,
    clean_changes,
    clean_arxiv,
    generate_output_filename,
    detect_cleaning_module
)
from version import __version__


class TeXCleanerApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"TeXCleaner v{__version__} - LaTeX Track Changes Cleaner")
        self.root.geometry("700x500")
        self.root.resizable(True, True)

        self.input_path = tk.StringVar()

        self.create_widgets()

    def create_widgets(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.trackchanges_tab = ttk.Frame(self.notebook)
        self.arxiv_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.trackchanges_tab, text="Track Changes Cleaner")
        self.notebook.add(self.arxiv_tab, text="arXiv Cleaner")

        self._create_trackchanges_tab()
        self._create_arxiv_tab()

    def _create_trackchanges_tab(self):
        main_frame = ttk.Frame(self.trackchanges_tab, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        title_label = ttk.Label(
            main_frame,
            text="Clean LaTeX Track Changes",
            font=("TkDefaultFont", 14, "bold")
        )
        title_label.pack(pady=(0, 20))

        input_frame = ttk.LabelFrame(main_frame, text="Input File", padding="5")
        input_frame.pack(fill=tk.X, pady=5)
        input_frame.columnconfigure(0, weight=1)

        self.trackchanges_entry = ttk.Entry(input_frame, textvariable=self.input_path)
        self.trackchanges_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        browse_btn = ttk.Button(input_frame, text="Browse...", command=self._browse_trackchanges_input)
        browse_btn.pack(side=tk.RIGHT)

        helper_label = ttk.Label(
            input_frame,
            text="Select a .tex file",
            font=("TkDefaultFont", 9, "italic"),
            foreground="gray"
        )
        helper_label.pack(anchor=tk.W, pady=(2, 0))

        self.trackchanges_clean_btn = ttk.Button(
            main_frame,
            text="Detect & Clean",
            command=self._start_trackchanges_cleaning
        )
        self.trackchanges_clean_btn.pack(pady=20)

        log_label = ttk.Label(main_frame, text="Log Output:", font=("TkDefaultFont", 10, "bold"))
        log_label.pack(anchor=tk.W, pady=(10, 5))

        self.trackchanges_log = scrolledtext.ScrolledText(
            main_frame,
            height=12,
            width=80,
            state=tk.DISABLED,
            wrap=tk.WORD
        )
        self.trackchanges_log.pack(fill=tk.BOTH, expand=True, pady=5)

        self.trackchanges_progress = ttk.Progressbar(main_frame, mode="indeterminate")
        self.trackchanges_progress.pack(fill=tk.X, pady=5)

    def _create_arxiv_tab(self):
        main_frame = ttk.Frame(self.arxiv_tab, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        title_label = ttk.Label(
            main_frame,
            text="Clean for arXiv Submission",
            font=("TkDefaultFont", 14, "bold")
        )
        title_label.pack(pady=(0, 20))

        input_frame = ttk.LabelFrame(main_frame, text="Project Folder", padding="5")
        input_frame.pack(fill=tk.X, pady=5)
        input_frame.columnconfigure(0, weight=1)

        self.arxiv_entry = ttk.Entry(input_frame)
        self.arxiv_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        browse_btn = ttk.Button(input_frame, text="Browse...", command=self._browse_arxiv_input)
        browse_btn.pack(side=tk.RIGHT)

        helper_label = ttk.Label(
            input_frame,
            text="Select a project folder",
            font=("TkDefaultFont", 9, "italic"),
            foreground="gray"
        )
        helper_label.pack(anchor=tk.W, pady=(2, 0))

        self.arxiv_clean_btn = ttk.Button(
            main_frame,
            text="Clean for arXiv",
            command=self._start_arxiv_cleaning
        )
        self.arxiv_clean_btn.pack(pady=20)

        log_label = ttk.Label(main_frame, text="Log Output:", font=("TkDefaultFont", 10, "bold"))
        log_label.pack(anchor=tk.W, pady=(10, 5))

        self.arxiv_log = scrolledtext.ScrolledText(
            main_frame,
            height=12,
            width=80,
            state=tk.DISABLED,
            wrap=tk.WORD
        )
        self.arxiv_log.pack(fill=tk.BOTH, expand=True, pady=5)

        self.arxiv_progress = ttk.Progressbar(main_frame, mode="indeterminate")
        self.arxiv_progress.pack(fill=tk.X, pady=5)

    def _browse_trackchanges_input(self):
        file_path = filedialog.askopenfilename(
            title="Select LaTeX File",
            filetypes=[("LaTeX files", "*.tex"), ("All files", "*.*")]
        )
        if file_path:
            self.input_path.set(file_path)

    def _browse_arxiv_input(self):
        folder = filedialog.askdirectory(title="Select LaTeX Project Folder")
        if folder:
            self.arxiv_entry.delete(0, tk.END)
            self.arxiv_entry.insert(0, folder)

    def _log(self, message, log_widget):
        log_widget.config(state=tk.NORMAL)
        log_widget.insert(tk.END, message)
        log_widget.see(tk.END)
        log_widget.config(state=tk.DISABLED)

    def _clear_log(self, log_widget):
        log_widget.config(state=tk.NORMAL)
        log_widget.delete(1.0, tk.END)
        log_widget.config(state=tk.DISABLED)

    def _validate_tex_input(self, input_path):
        if not input_path:
            return False, "Please select an input file."
        if not os.path.exists(input_path):
            return False, f"Path not found: {input_path}"
        if not os.path.isfile(input_path):
            return False, "Error: This operation requires a .tex file."
        if not input_path.lower().endswith(".tex"):
            return False, "Error: The selected file must have a .tex extension."
        return True, ""

    def _validate_folder_input(self, folder_path):
        if not folder_path:
            return False, "Please select a project folder."
        if not os.path.exists(folder_path):
            return False, f"Folder not found: {folder_path}"
        if not os.path.isdir(folder_path):
            return False, "Error: This operation requires a folder."
        return True, ""

    def _start_trackchanges_cleaning(self):
        input_path = self.input_path.get().strip()

        valid, error_msg = self._validate_tex_input(input_path)
        if not valid:
            messagebox.showerror("Input Error", error_msg)
            return

        detected = detect_cleaning_module(input_path)

        if detected is None:
            result = messagebox.askyesno(
                "No Track Changes Detected",
                "No track changes markup (trackchanges or changes package) was detected in the file.\n\n"
                "Would you like to try cleaning anyway?"
            )
            if not result:
                return
            detected = "trackchanges"
        else:
            module_name = "TrackChanges (trackchanges.sty)" if detected == "trackchanges" else "Changes (changes.sty)"
            result = messagebox.askyesno(
                "Confirm Detected Module",
                f"Detected '{module_name}' signatures in the file.\n\n"
                f"Is this correct and would you like to proceed with cleaning?"
            )
            if not result:
                return

        self._clear_log(self.trackchanges_log)
        self.trackchanges_clean_btn.config(state=tk.DISABLED)
        self.trackchanges_progress.start(10)
        self._log(f"Detected module: {detected}\n", self.trackchanges_log)
        self._log("Starting cleaning...\n", self.trackchanges_log)

        thread = threading.Thread(
            target=self._run_trackchanges_cleaning,
            args=(input_path, detected)
        )
        thread.daemon = True
        thread.start()

    def _run_trackchanges_cleaning(self, input_path, detected_module):
        def callback(message):
            self.root.after(0, self._log, message, self.trackchanges_log)

        try:
            output_path = generate_output_filename(input_path, "-cleaned")

            if detected_module == "trackchanges":
                success, message = clean_trackchanges(input_path, output_path, callback)
            else:
                success, message = clean_changes(input_path, output_path, callback)

            callback("\n" + message + "\n")

            if success:
                self.root.after(0, lambda: messagebox.showinfo("Success", message))
            else:
                self.root.after(0, lambda: messagebox.showerror("Error", message))

        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            self.root.after(0, self._log, error_msg, self.trackchanges_log)
            self.root.after(0, lambda: messagebox.showerror("Error", error_msg))

        finally:
            self.root.after(0, self.trackchanges_progress.stop)
            self.root.after(0, lambda: self.trackchanges_clean_btn.config(state=tk.NORMAL))

    def _start_arxiv_cleaning(self):
        folder_path = self.arxiv_entry.get().strip()

        valid, error_msg = self._validate_folder_input(folder_path)
        if not valid:
            messagebox.showerror("Input Error", error_msg)
            return

        self._clear_log(self.arxiv_log)
        self.arxiv_clean_btn.config(state=tk.DISABLED)
        self.arxiv_progress.start(10)

        thread = threading.Thread(target=self._run_arxiv_cleaning, args=(folder_path,))
        thread.daemon = True
        thread.start()

    def _run_arxiv_cleaning(self, folder_path):
        def callback(message):
            self.root.after(0, self._log, message, self.arxiv_log)

        try:
            success, message = clean_arxiv(folder_path, callback=callback)

            callback("\n" + message + "\n")

            if success:
                self.root.after(0, lambda: messagebox.showinfo("Success", message))
            else:
                self.root.after(0, lambda: messagebox.showerror("Error", message))

        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            self.root.after(0, self._log, error_msg, self.arxiv_log)
            self.root.after(0, lambda: messagebox.showerror("Error", error_msg))

        finally:
            self.root.after(0, self.arxiv_progress.stop)
            self.root.after(0, lambda: self.arxiv_clean_btn.config(state=tk.NORMAL))


def main():
    root = tk.Tk()
    app = TeXCleanerApp(root)
    root.mainloop()