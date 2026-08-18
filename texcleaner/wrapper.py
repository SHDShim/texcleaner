#!/usr/bin/env python
"""
wrapper.py - Integration layer for LaTeX track changes cleaning scripts

This module provides a unified interface for cleaning LaTeX documents of track changes
markup from three different packages:
1. TrackChanges (trackchanges.sty)
2. Changes (changes.sty)
3. arXiv submission cleaner
"""

import os
import subprocess
import sys
import shutil
from pathlib import Path


PACKAGE_DIR = Path(__file__).parent.resolve()
SCRIPTS_DIR = PACKAGE_DIR / "scripts"
TRACKCHANGES_DIR = SCRIPTS_DIR / "trackchanges-py3"
CHANGES_DIR = SCRIPTS_DIR / "changes"
ACCEPTCHANGES_SCRIPT = TRACKCHANGES_DIR / "acceptchanges3.py"
PYMERGECHANGES_SCRIPT = CHANGES_DIR / "pyMergeChanges.py"


def get_python_cmd():
    """Return the path to the Python interpreter."""
    return sys.executable


def clean_trackchanges(
    input_file,
    output_file,
    callback=None,
    accept_changes=True,
    remove_annotations=True,
    overwrite=False,
):
    """
    Clean LaTeX document using trackchanges.sty.

    Uses acceptchanges3.py with -c -n flags to accept all changes and remove annotations.

    Args:
        input_file: Path to input .tex file
        output_file: Path to output .tex file
        callback: Optional function to receive progress updates

    Returns:
        tuple: (success: bool, message: str)
    """
    if os.path.isdir(input_file):
        return False, "Error: This operation requires a .tex file, not a directory."

    if not os.path.exists(input_file):
        return False, f"Input file not found: {input_file}"

    if not os.path.exists(ACCEPTCHANGES_SCRIPT):
        return False, f"Script not found: {ACCEPTCHANGES_SCRIPT}"

    output_path = Path(output_file)
    if output_path.exists():
        if not overwrite:
            return False, f"Output already exists: {output_file}"
        if output_path.is_dir():
            return False, f"Output path is a directory: {output_file}"
        output_path.unlink()

    cmd = [
        get_python_cmd(),
        str(ACCEPTCHANGES_SCRIPT),
        "-c",
        "--infile", str(input_file),
        "--outfile", str(output_file)
    ]
    if not accept_changes:
        cmd.append("--reject")
    if remove_annotations:
        cmd.append("--notes")

    if callback:
        callback(f"Running TrackChanges cleaner...\nCommand: {' '.join(cmd)}\n")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(TRACKCHANGES_DIR)
        )

        if result.stdout:
            if callback:
                callback(result.stdout)
        if result.stderr:
            if callback:
                callback(result.stderr)

        if result.returncode == 0:
            return True, f"Successfully cleaned: {output_file}"
        else:
            return False, f"Process failed with return code: {result.returncode}"

    except Exception as e:
        return False, f"Error running TrackChanges cleaner: {str(e)}"


def clean_changes(
    input_file,
    output_file,
    callback=None,
    accept_changes=True,
    remove_annotations=True,
    overwrite=False,
):
    """
    Clean LaTeX document using changes.sty.

    Uses pyMergeChanges.py with -a flag to accept all changes.

    Args:
        input_file: Path to input .tex file
        output_file: Path to output .tex file
        callback: Optional function to receive progress updates

    Returns:
        tuple: (success: bool, message: str)
    """
    if os.path.isdir(input_file):
        return False, "Error: This operation requires a .tex file, not a directory."

    if not os.path.exists(input_file):
        return False, f"Input file not found: {input_file}"

    if not os.path.exists(PYMERGECHANGES_SCRIPT):
        return False, f"Script not found: {PYMERGECHANGES_SCRIPT}"

    if input_file == output_file:
        return False, "Input and output files must be different"

    output_path = Path(output_file)
    if output_path.exists():
        if not overwrite:
            return False, f"Output already exists: {output_file}"
        if output_path.is_dir():
            return False, f"Output path is a directory: {output_file}"
        output_path.unlink()

    action_flags = "a" if accept_changes else "r"
    if remove_annotations:
        action_flags += "h"

    cmd = [
        get_python_cmd(),
        str(PYMERGECHANGES_SCRIPT),
        f"-{action_flags}",
        str(input_file),
        str(output_file)
    ]

    if callback:
        callback(f"Running Changes cleaner...\nCommand: {' '.join(cmd)}\n")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(CHANGES_DIR)
        )

        if result.stdout:
            if callback:
                callback(result.stdout)
        if result.stderr:
            if callback:
                callback(result.stderr)

        if result.returncode == 0:
            return True, f"Successfully cleaned: {output_file}"
        else:
            return False, f"Process failed with return code: {result.returncode}"

    except Exception as e:
        return False, f"Error running Changes cleaner: {str(e)}"


def clean_arxiv(
    folder_path,
    im_size=500,
    callback=None,
    resize_images=True,
    compress_pdf=False,
    pdf_resolution=500,
    keep_bib=False,
    verbose=False,
    output_suffix="-cleaned",
    overwrite=False,
):
    """
    Clean and organize LaTeX files for arXiv submission.

    Uses arxiv_latex_cleaner to remove comments, resize images, and organize files.

    Args:
        folder_path: Path to the LaTeX project folder
        im_size: Maximum image dimension (default: 500)
        callback: Optional function to receive progress updates

    Returns:
        tuple: (success: bool, message: str)
    """
    if os.path.isfile(folder_path):
        return False, "Error: arXiv cleaning requires a folder, not a file."

    if not os.path.exists(folder_path):
        return False, f"Folder not found: {folder_path}"

    arxiv_cleaner_cmd = shutil.which("arxiv_latex_cleaner")
    if not arxiv_cleaner_cmd:
        return False, "arxiv_latex_cleaner not found. Please install it in the docflow environment."

    if not is_valid_output_suffix(output_suffix):
        return False, "Output suffix must be non-empty and cannot contain path separators."

    input_path = Path(folder_path)
    default_output = input_path.with_name(f"{input_path.name}_arXiv")
    cleaned_output = input_path.with_name(f"{input_path.name}{output_suffix}")

    for existing_output in {default_output, cleaned_output}:
        if existing_output.exists():
            if not overwrite:
                return False, f"Output already exists: {existing_output}"
            if existing_output.is_dir():
                shutil.rmtree(existing_output)
            else:
                existing_output.unlink()

    cmd = [arxiv_cleaner_cmd, str(folder_path)]
    if resize_images:
        cmd.extend(["--resize_images", "--im_size", str(im_size)])
    if compress_pdf:
        cmd.extend(["--compress_pdf", "--pdf_im_resolution", str(pdf_resolution)])
    if keep_bib:
        cmd.append("--keep_bib")
    if verbose:
        cmd.append("--verbose")

    if callback:
        callback(f"Running arXiv cleaner...\nCommand: {' '.join(cmd)}\n")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )

        if result.stdout:
            if callback:
                callback(result.stdout)
        if result.stderr:
            if callback:
                callback(result.stderr)

        if result.returncode == 0:
            if default_output.exists() and default_output != cleaned_output:
                shutil.move(str(default_output), str(cleaned_output))
                return True, f"Successfully cleaned folder: {cleaned_output}"
            elif cleaned_output.exists():
                return True, f"Successfully cleaned folder: {cleaned_output}"
            else:
                return False, "Cleaner finished but the expected output folder was not created."

        else:
            return False, f"Process failed with return code: {result.returncode}"

    except Exception as e:
        return False, f"Error running arXiv cleaner: {str(e)}"


import re


TRACKCHANGES_PATTERNS = [
    re.compile(r'\\annote\s*[{[]'),
    re.compile(r'\\note\s*[{[]'),
    re.compile(r'\\add\s*[{[]'),
    re.compile(r'\\remove\s*[{[]'),
    re.compile(r'\\change\s*[{[]'),
]

CHANGES_PATTERNS = [
    re.compile(r'\\added\s*[{[]'),
    re.compile(r'\\deleted\s*[{[]'),
    re.compile(r'\\replaced\s*[{[]'),
    re.compile(r'\\highlight\s*[{[]'),
    re.compile(r'\\comment\s*[{[]'),
]


def detect_cleaning_module(input_file):
    if os.path.isdir(input_file):
        return None

    if not os.path.exists(input_file):
        return None

    try:
        with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read(20000)
    except Exception:
        return None

    trackchanges_score = 0
    for pattern in TRACKCHANGES_PATTERNS:
        if pattern.search(content):
            trackchanges_score += 1

    changes_score = 0
    for pattern in CHANGES_PATTERNS:
        if pattern.search(content):
            changes_score += 1

    if changes_score > 0 and trackchanges_score == 0:
        return "changes"
    elif trackchanges_score > 0 and changes_score == 0:
        return "trackchanges"
    elif changes_score > trackchanges_score:
        return "changes"
    elif trackchanges_score > changes_score:
        return "trackchanges"
    else:
        return None


def generate_output_filename(input_path, suffix="-cleaned"):
    """
    Generate output filename by adding a suffix before the extension.

    Args:
        input_path: Path to input file
        suffix: Suffix to add before file extension (default: "-cleaned")

    Returns:
        str: Generated output filename
    """
    path = Path(input_path)
    return str(path.parent / f"{path.stem}{suffix}{path.suffix}")


def is_valid_output_suffix(suffix):
    """Return whether a user-provided suffix stays within the input directory."""
    return bool(suffix) and "/" not in suffix and "\\" not in suffix and "\0" not in suffix
