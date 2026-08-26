#!/usr/bin/env python3
"""Integration layer for the bundled LaTeX and arXiv cleaners."""

from contextlib import contextmanager
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import unicodedata


PACKAGE_DIR = Path(__file__).parent.resolve()
SCRIPTS_DIR = PACKAGE_DIR / "scripts"
TRACKCHANGES_DIR = SCRIPTS_DIR / "trackchanges-py3"
CHANGES_DIR = SCRIPTS_DIR / "changes"
ACCEPTCHANGES_SCRIPT = TRACKCHANGES_DIR / "acceptchanges3.py"
PYMERGECHANGES_SCRIPT = CHANGES_DIR / "pyMergeChanges.py"
PROCESS_TIMEOUT_SECONDS = 15 * 60

_lock_guard = threading.Lock()
_output_locks: dict[str, threading.Lock] = {}


def get_python_cmd():
    return sys.executable


def _canonical(path):
    return Path(path).expanduser().resolve(strict=False)


def _same_path(first, second):
    first_path = _canonical(first)
    second_path = _canonical(second)
    if first_path == second_path:
        return True
    try:
        return os.path.exists(first_path) and os.path.exists(second_path) and os.path.samefile(first_path, second_path)
    except OSError:
        return False


def _validate_output(input_path, output_path, overwrite):
    if _same_path(input_path, output_path):
        return False, "Input and output files must be different"
    output_path = _canonical(output_path)
    if not output_path.parent.is_dir():
        return False, f"Output directory not found: {output_path.parent}"
    if output_path.exists():
        if not overwrite:
            return False, f"Output already exists: {output_path}"
        if output_path.is_dir():
            return False, f"Output path is a directory: {output_path}"
    return True, output_path


def _temporary_output(output_path):
    descriptor, name = tempfile.mkstemp(prefix=f".{output_path.name}.", suffix=".tmp", dir=output_path.parent)
    os.close(descriptor)
    os.unlink(name)
    return Path(name)


@contextmanager
def _output_lock(path):
    key = str(_canonical(path))
    with _lock_guard:
        lock = _output_locks.setdefault(key, threading.Lock())
    with lock:
        yield


def _run_cleaner(command, cwd, callback):
    if callback:
        callback(f"Command: {' '.join(command)}\n")
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            cwd=str(cwd),
            timeout=PROCESS_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return None, f"Cleaner timed out after {PROCESS_TIMEOUT_SECONDS} seconds"
    except OSError as error:
        return None, f"Error starting cleaner: {error}"

    if callback and result.stdout:
        callback(result.stdout)
    if callback and result.stderr:
        callback(result.stderr)
    return result, None


def clean_trackchanges(
    input_file,
    output_file,
    callback=None,
    accept_changes=True,
    remove_annotations=True,
    overwrite=False,
):
    """Clean a file using trackchanges.sty without risking the source/output."""
    input_path = _canonical(input_file)
    if input_path.is_dir():
        return False, "Error: This operation requires a .tex file, not a directory."
    if not input_path.is_file():
        return False, f"Input file not found: {input_file}"
    if not ACCEPTCHANGES_SCRIPT.is_file():
        return False, f"Script not found: {ACCEPTCHANGES_SCRIPT}"

    valid, output_or_message = _validate_output(input_path, output_file, overwrite)
    if not valid:
        return False, output_or_message
    output_path = output_or_message

    command = [get_python_cmd(), str(ACCEPTCHANGES_SCRIPT), "-c", "--infile", str(input_path)]
    if not accept_changes:
        command.append("--reject")
    if remove_annotations:
        command.append("--notes")

    with _output_lock(output_path):
        temporary_path = _temporary_output(output_path)
        command.extend(["--outfile", str(temporary_path)])
        try:
            result, error = _run_cleaner(command, TRACKCHANGES_DIR, callback)
            if error:
                return False, error
            if result.returncode != 0:
                return False, f"Process failed with return code: {result.returncode}"
            if not temporary_path.is_file():
                return False, "Cleaner finished but did not create an output file."
            os.replace(temporary_path, output_path)
            return True, f"Successfully cleaned: {output_path}"
        finally:
            temporary_path.unlink(missing_ok=True)


def clean_changes(
    input_file,
    output_file,
    callback=None,
    accept_changes=True,
    remove_annotations=True,
    overwrite=False,
):
    """Clean a file using changes.sty without risking the source/output."""
    input_path = _canonical(input_file)
    if input_path.is_dir():
        return False, "Error: This operation requires a .tex file, not a directory."
    if not input_path.is_file():
        return False, f"Input file not found: {input_file}"
    if not PYMERGECHANGES_SCRIPT.is_file():
        return False, f"Script not found: {PYMERGECHANGES_SCRIPT}"

    valid, output_or_message = _validate_output(input_path, output_file, overwrite)
    if not valid:
        return False, output_or_message
    output_path = output_or_message

    action_flags = "a" if accept_changes else "r"
    if remove_annotations:
        action_flags += "h"

    with _output_lock(output_path):
        temporary_path = _temporary_output(output_path)
        command = [get_python_cmd(), str(PYMERGECHANGES_SCRIPT), f"-{action_flags}", str(input_path), str(temporary_path)]
        try:
            result, error = _run_cleaner(command, CHANGES_DIR, callback)
            if error:
                return False, error
            if result.returncode != 0:
                return False, f"Process failed with return code: {result.returncode}"
            if not temporary_path.is_file():
                return False, "Cleaner finished but did not create an output file."
            os.replace(temporary_path, output_path)
            return True, f"Successfully cleaned: {output_path}"
        finally:
            temporary_path.unlink(missing_ok=True)


def _replace_path(source, destination):
    """Replace a file/directory while retaining a recoverable backup until success."""
    destination = Path(destination)
    backup_root = None
    backup = None
    if os.path.lexists(destination):
        backup_root = Path(tempfile.mkdtemp(prefix=".texcleaner-backup-", dir=destination.parent))
        backup = backup_root / destination.name
        shutil.move(str(destination), str(backup))
    try:
        shutil.move(str(source), str(destination))
    except Exception:
        if backup is not None and not os.path.lexists(destination):
            shutil.move(str(backup), str(destination))
        raise
    finally:
        if backup_root is not None:
            shutil.rmtree(backup_root, ignore_errors=True)


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
    """Clean and organize a LaTeX project for arXiv submission."""
    input_path = _canonical(folder_path)
    if input_path.is_file():
        return False, "Error: arXiv cleaning requires a folder, not a file."
    if not input_path.is_dir():
        return False, f"Folder not found: {folder_path}"
    if not isinstance(im_size, int) or not 1 <= im_size <= 10000:
        return False, "Image size must be between 1 and 10000."
    if not isinstance(pdf_resolution, int) or not 1 <= pdf_resolution <= 2400:
        return False, "PDF resolution must be between 1 and 2400."
    if not is_valid_output_suffix(output_suffix):
        return False, "Output suffix must be non-empty and cannot contain path separators."

    arxiv_cleaner_cmd = shutil.which("arxiv_latex_cleaner")
    if not arxiv_cleaner_cmd:
        return False, "arxiv_latex_cleaner not found. Please install it in the docflow environment."

    default_output = input_path.with_name(f"{input_path.name}_arXiv")
    cleaned_output = input_path.with_name(f"{input_path.name}{output_suffix}")
    existing_outputs = {default_output, cleaned_output}
    if not overwrite:
        for existing_output in existing_outputs:
            if os.path.lexists(existing_output):
                return False, f"Output already exists: {existing_output}"

    with _output_lock(cleaned_output):
        staging_root = None
        try:
            # Existing output paths are handled in a staging directory. This keeps
            # overwrite failures from deleting a previously valid submission.
            if overwrite:
                staging_root = Path(tempfile.mkdtemp(prefix=f".{input_path.name}-", dir=input_path.parent))
                staged_input = staging_root / input_path.name
                shutil.copytree(input_path, staged_input)
                run_input = staged_input
                run_default = staged_input.with_name(f"{staged_input.name}_arXiv")
            else:
                run_input = input_path
                run_default = default_output

            command = [arxiv_cleaner_cmd, str(run_input)]
            if resize_images:
                command.extend(["--resize_images", "--im_size", str(im_size)])
            if compress_pdf:
                command.extend(["--compress_pdf", "--pdf_im_resolution", str(pdf_resolution)])
            if keep_bib:
                command.append("--keep_bib")
            if verbose:
                command.append("--verbose")

            if callback:
                callback("Running arXiv cleaner...\n")
            result, error = _run_cleaner(command, run_input.parent, callback)
            if error:
                return False, error
            if result.returncode != 0:
                return False, f"Process failed with return code: {result.returncode}"
            if not run_default.is_dir():
                return False, "Cleaner finished but the expected output folder was not created."

            if overwrite:
                _replace_path(run_default, cleaned_output)
            elif run_default != cleaned_output:
                shutil.move(str(run_default), str(cleaned_output))
            return True, f"Successfully cleaned folder: {cleaned_output}"
        except (OSError, shutil.Error) as error:
            return False, f"Error finalizing arXiv output: {error}"
        finally:
            if staging_root is not None:
                shutil.rmtree(staging_root, ignore_errors=True)


TRACKCHANGES_PATTERNS = [
    re.compile(r"\\(?:annote|note|add|remove|change)(?![A-Za-z@])\s*(?:\[[^\]]*\])?\s*[{[]"),
    re.compile(r"\\usepackage(?:\[[^\]]*\])?\{trackchanges\}"),
]
CHANGES_PATTERNS = [
    re.compile(r"\\(?:added|deleted|replaced|highlight|comment)(?![A-Za-z@])\s*(?:\[[^\]]*\])?\s*[{[]"),
    re.compile(r"\\usepackage(?:\[[^\]]*\])?\{changes\}"),
]


def _remove_tex_comments(content):
    lines = []
    for line in content.splitlines(keepends=True):
        for position, char in enumerate(line):
            if char == "%" and not _is_escaped_percent(line, position):
                line = line[:position] + ("\n" if line.endswith("\n") else "")
                break
        lines.append(line)
    return "".join(lines)


def _is_escaped_percent(line, position):
    slashes = 0
    position -= 1
    while position >= 0 and line[position] == "\\":
        slashes += 1
        position -= 1
    return slashes % 2 == 1


def detect_cleaning_module(input_file):
    path = _canonical(input_file)
    if not path.is_file():
        return None
    try:
        content = _remove_tex_comments(path.read_text(encoding="utf-8", errors="ignore"))
    except OSError:
        return None

    trackchanges_score = sum(pattern.search(content) is not None for pattern in TRACKCHANGES_PATTERNS)
    changes_score = sum(pattern.search(content) is not None for pattern in CHANGES_PATTERNS)
    if changes_score > trackchanges_score:
        return "changes"
    if trackchanges_score > changes_score:
        return "trackchanges"
    return None


def generate_output_filename(input_path, suffix="-cleaned"):
    path = Path(input_path)
    return str(path.parent / f"{path.stem}{suffix}{path.suffix}")


def is_valid_output_suffix(suffix):
    return (
        isinstance(suffix, str)
        and bool(suffix)
        and "/" not in suffix
        and "\\" not in suffix
        and all(unicodedata.category(character) != "Cc" for character in suffix)
    )
