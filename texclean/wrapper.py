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


def clean_trackchanges(input_file, output_file, callback=None):
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

    cmd = [
        get_python_cmd(),
        str(ACCEPTCHANGES_SCRIPT),
        "-c", "-n",
        "--infile", str(input_file),
        "--outfile", str(output_file)
    ]

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


def clean_changes(input_file, output_file, callback=None):
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

    cmd = [
        get_python_cmd(),
        str(PYMERGECHANGES_SCRIPT),
        "-a",
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


def clean_arxiv(folder_path, im_size=500, callback=None):
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

    cmd = [
        arxiv_cleaner_cmd,
        str(folder_path),
        "--im_size", str(im_size)
    ]

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
            arxiv_output = Path(folder_path).with_name(f"{Path(folder_path).name}_arXiv")
            cleaned_output = Path(folder_path).with_name(f"{Path(folder_path).name}-cleaned")

            if arxiv_output.exists():
                shutil.move(str(arxiv_output), str(cleaned_output))
                return True, f"Successfully cleaned folder: {cleaned_output}"
            else:
                return True, f"Successfully cleaned folder: {folder_path}"

        else:
            return False, f"Process failed with return code: {result.returncode}"

    except Exception as e:
        return False, f"Error running arXiv cleaner: {str(e)}"


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