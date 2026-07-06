#!/usr/bin/env python
"""
app.py - GUI front-end for cleaning LaTeX track changes

A simple Tkinter application to clean LaTeX documents of track changes markup
from TrackChanges, Changes, or arXiv submission packages.
"""

import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

from .wrapper import (
    clean_trackchanges,
    clean_changes,
    clean_arxiv,
    generate_output_filename
)
from .version import __version__


FILE_OPTIONS = ["trackchanges", "changes"]
FOLDER_OPTIONS = ["arxiv"]


class TeXCleanApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"TeXClean v{__version__} - LaTeX Track Changes Cleaner")
        self.root.geometry("700x600")
        self.root.resizable(True, True)

        self.input_path = tk.StringVar()
        self.cleaning_option = tk.StringVar(value="trackchanges")
        self._last_input_type = "file"

        self.create_widgets()

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)

        title_label = ttk.Label(
            main_frame,
            text="TeXClean - LaTeX Track Changes Cleaner",
            font=("TkDefaultFont", 14, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))

        input_frame = ttk.LabelFrame(main_frame, text="Input", padding="5")
        input_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        input_frame.columnconfigure(0, weight=1)

        self.input_entry = ttk.Entry(input_frame, textvariable=self.input_path)
        self.input_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))

        browse_btn = ttk.Button(input_frame, text="Browse...", command=self.browse_input)
        browse_btn.grid(row=0, column=1)

        self.helper_label = ttk.Label(
            input_frame,
            text="Select a .tex file",
            font=("TkDefaultFont", 9, "italic"),
            foreground="gray"
        )
        self.helper_label.grid(row=1, column=0, columnspan=2, sticky=tk.W, padx=2, pady=(2, 0))

        options_frame = ttk.LabelFrame(main_frame, text="Cleaning Option", padding="5")
        options_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)

        trackchanges_rb = ttk.Radiobutton(
            options_frame,
            text="Remove TrackChanges (trackchanges.sty)",
            variable=self.cleaning_option,
            value="trackchanges",
            command=self._on_option_change
        )
        trackchanges_rb.grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)

        changes_rb = ttk.Radiobutton(
            options_frame,
            text="Remove Track Changes (changes.sty)",
            variable=self.cleaning_option,
            value="changes",
            command=self._on_option_change
        )
        changes_rb.grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)

        arxiv_rb = ttk.Radiobutton(
            options_frame,
            text="Clean for arXiv Submission",
            variable=self.cleaning_option,
            value="arxiv",
            command=self._on_option_change
        )
        arxiv_rb.grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)

        self.clean_btn = ttk.Button(main_frame, text="Clean", command=self.start_cleaning)
        self.clean_btn.grid(row=4, column=0, columnspan=3, pady=10)

        log_label = ttk.Label(main_frame, text="Log Output:", font=("TkDefaultFont", 10, "bold"))
        log_label.grid(row=5, column=0, sticky=tk.W, pady=(10, 5))

        self.log_text = scrolledtext.ScrolledText(
            main_frame,
            height=15,
            width=80,
            state=tk.DISABLED,
            wrap=tk.WORD
        )
        self.log_text.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)

        self.progress = ttk.Progressbar(main_frame, mode="indeterminate")
        self.progress.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)

    def _on_option_change(self):
        option = self.cleaning_option.get()
        current_input_type = "file" if option in FILE_OPTIONS else "folder"

        if self._last_input_type != current_input_type:
            self.input_path.set("")
            self._last_input_type = current_input_type

        if option in FILE_OPTIONS:
            self.helper_label.config(text="Select a .tex file")
        else:
            self.helper_label.config(text="Select a project folder")

    def browse_input(self):
        option = self.cleaning_option.get()

        if option in FILE_OPTIONS:
            file_path = filedialog.askopenfilename(
                title="Select LaTeX File",
                filetypes=[("LaTeX files", "*.tex"), ("All files", "*.*")]
            )
            if file_path:
                self.input_path.set(file_path)
        else:
            folder = filedialog.askdirectory(title="Select LaTeX Project Folder")
            if folder:
                self.input_path.set(folder)

    def _validate_input(self, input_path, option):
        if not input_path:
            return False, "Please select an input file or folder."

        if not os.path.exists(input_path):
            return False, f"Path not found: {input_path}"

        if option in FILE_OPTIONS:
            if not os.path.isfile(input_path):
                return False, "Error: This operation requires a .tex file, not a folder or other file type."
            if not input_path.lower().endswith(".tex"):
                return False, "Error: The selected file must have a .tex extension."
        elif option == "arxiv":
            if not os.path.isdir(input_path):
                return False, "Error: arXiv cleaning requires a project folder, not a file."

        return True, ""

    def log(self, message):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def start_cleaning(self):
        input_path = self.input_path.get().strip()
        option = self.cleaning_option.get()

        valid, error_msg = self._validate_input(input_path, option)
        if not valid:
            messagebox.showerror("Input Error", error_msg)
            return

        self.clean_btn.config(state=tk.DISABLED)
        self.progress.start(10)
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)

        thread = threading.Thread(target=self.run_cleaning, args=(input_path, option))
        thread.daemon = True
        thread.start()

    def run_cleaning(self, input_path, option):
        def callback(message):
            self.root.after(0, self.log, message)

        try:
            if option == "trackchanges":
                output_path = generate_output_filename(input_path, "-cleaned")
                success, message = clean_trackchanges(input_path, output_path, callback)

            elif option == "changes":
                output_path = generate_output_filename(input_path, "-cleaned")
                success, message = clean_changes(input_path, output_path, callback)

            elif option == "arxiv":
                success, message = clean_arxiv(input_path, callback=callback)

            else:
                success = False
                message = f"Unknown option: {option}"

            callback("\n" + message + "\n")

            if success:
                self.root.after(0, lambda: messagebox.showinfo("Success", message))
            else:
                self.root.after(0, lambda: messagebox.showerror("Error", message))

        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            self.root.after(0, self.log, error_msg)
            self.root.after(0, lambda: messagebox.showerror("Error", error_msg))

        finally:
            self.root.after(0, self.progress.stop)
            self.root.after(0, lambda: self.clean_btn.config(state=tk.NORMAL))


def main():
    root = tk.Tk()
    app = TeXCleanApp(root)
    root.mainloop()