import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from texcleaner.app import validate_folder_path, validate_tex_path
from texcleaner.wrapper import (
    clean_arxiv,
    clean_changes,
    clean_trackchanges,
    detect_cleaning_module,
    generate_output_filename,
    get_arxiv_cleaner_cmd,
    is_valid_output_suffix,
)


class TrackChangesOptionsTests(unittest.TestCase):
    source = (
        r"Start \add{added} \remove{removed} "
        r"\change{original}{replacement} \annote{kept}{annotation} \note{note} End"
    )

    def run_cleaner(self, *, accept_changes):
        with tempfile.TemporaryDirectory() as temporary_directory:
            input_path = Path(temporary_directory) / "input.tex"
            output_path = Path(temporary_directory) / "output.tex"
            input_path.write_text(self.source, encoding="utf-8")
            success, _ = clean_trackchanges(
                input_path,
                output_path,
                accept_changes=accept_changes,
                remove_annotations=True,
            )
            self.assertTrue(success)
            return output_path.read_text(encoding="utf-8")

    def test_accept_keeps_new_text(self):
        result = self.run_cleaner(accept_changes=True)
        self.assertIn("added", result)
        self.assertIn("replacement", result)
        self.assertNotIn("removed", result)
        self.assertNotIn("original", result)
        self.assertNotIn("annotation", result)

    def test_reject_keeps_old_text(self):
        result = self.run_cleaner(accept_changes=False)
        self.assertIn("removed", result)
        self.assertIn("original", result)
        self.assertNotIn("added", result)
        self.assertNotIn("replacement", result)
        self.assertNotIn("annotation", result)


class ChangesOptionsTests(unittest.TestCase):
    source = (
        r"Start \added{added} \deleted{removed} "
        r"\replaced{replacement}{original} \highlight{plain} \comment{note} End"
    )

    def run_cleaner(self, *, accept_changes):
        with tempfile.TemporaryDirectory() as temporary_directory:
            input_path = Path(temporary_directory) / "input.tex"
            output_path = Path(temporary_directory) / "output.tex"
            input_path.write_text(self.source, encoding="utf-8")
            success, _ = clean_changes(
                input_path,
                output_path,
                accept_changes=accept_changes,
                remove_annotations=True,
            )
            self.assertTrue(success)
            return output_path.read_text(encoding="utf-8")

    def test_accept_keeps_new_text(self):
        result = self.run_cleaner(accept_changes=True)
        self.assertIn("added", result)
        self.assertIn("replacement", result)
        self.assertIn("plain", result)
        self.assertNotIn("removed", result)
        self.assertNotIn("original", result)
        self.assertNotIn("note", result)

    def test_reject_keeps_old_text(self):
        result = self.run_cleaner(accept_changes=False)
        self.assertIn("removed", result)
        self.assertIn("original", result)
        self.assertIn("plain", result)
        self.assertNotIn("added", result)
        self.assertNotIn("replacement", result)
        self.assertNotIn("note", result)


class ArxivOptionsTests(unittest.TestCase):
    @patch("texcleaner.wrapper.subprocess.run")
    @patch("texcleaner.wrapper.shutil.which", return_value="/usr/local/bin/arxiv_latex_cleaner")
    def test_graphics_and_bibliography_options_reach_cli(self, _, run):
        def create_cleaner_output(command, **_):
            input_path = next(
                Path(argument)
                for argument in command
                if Path(argument).resolve(strict=False) == Path(temporary_directory).resolve(strict=False)
            )
            input_path.with_name(f"{input_path.name}_arXiv").mkdir()
            return subprocess.CompletedProcess(command, 0, "", "")

        run.side_effect = create_cleaner_output
        with tempfile.TemporaryDirectory() as temporary_directory:
            success, _ = clean_arxiv(
                temporary_directory,
                resize_images=True,
                im_size=1200,
                compress_pdf=True,
                pdf_resolution=300,
                keep_bib=True,
                verbose=True,
                output_suffix="-submission",
            )

        self.assertTrue(success)
        command = run.call_args.args[0]
        self.assertIn("--resize_images", command)
        self.assertEqual(command[command.index("--im_size") + 1], "1200")
        self.assertIn("--compress_pdf", command)
        self.assertEqual(command[command.index("--pdf_im_resolution") + 1], "300")
        self.assertIn("--keep_bib", command)
        self.assertIn("--verbose", command)

    @patch("texcleaner.wrapper.sys.executable", "TeXCleaner.exe")
    @patch("texcleaner.wrapper.sys.frozen", True, create=True)
    def test_frozen_arxiv_command_uses_bundled_executable(self):
        self.assertEqual(get_arxiv_cleaner_cmd(), ["TeXCleaner.exe", "--run-arxiv-cleaner"])


class SafetyAndParserRegressionTests(unittest.TestCase):
    def test_trackchanges_rejects_same_canonical_path_without_deleting_source(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            input_path = Path(temporary_directory) / "input.tex"
            input_path.write_text(r"A \add{new}.", encoding="utf-8")
            success, message = clean_trackchanges(input_path, input_path, overwrite=True)
            self.assertFalse(success)
            self.assertIn("different", message)
            self.assertTrue(input_path.exists())

    def test_changes_handles_nested_commands_and_escaped_braces(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            input_path = Path(temporary_directory) / "input.tex"
            output_path = Path(temporary_directory) / "output.tex"
            input_path.write_text(r"A \added{outer \added{inner}} and \added{literal \} brace}.", encoding="utf-8")
            success, _ = clean_changes(input_path, output_path)
            self.assertTrue(success)
            self.assertEqual(output_path.read_text(encoding="utf-8"), r"A outer inner and literal \} brace.")

    def test_trackchanges_handles_nested_commands_and_escaped_braces(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            input_path = Path(temporary_directory) / "input.tex"
            output_path = Path(temporary_directory) / "output.tex"
            input_path.write_text(r"A \add{outer \add{inner}} and \add{literal \} brace}.", encoding="utf-8")
            success, _ = clean_trackchanges(input_path, output_path)
            self.assertTrue(success)
            self.assertEqual(output_path.read_text(encoding="utf-8"), r"A outer inner and literal \} brace.")

    def test_failed_overwrite_preserves_existing_file(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            input_path = Path(temporary_directory) / "input.tex"
            output_path = Path(temporary_directory) / "output.tex"
            input_path.write_text("not valid utf-8: \udcff", encoding="utf-8", errors="surrogatepass")
            output_path.write_text("previous result", encoding="utf-8")
            success, _ = clean_changes(input_path, output_path, overwrite=True)
            self.assertFalse(success)
            self.assertEqual(output_path.read_text(encoding="utf-8"), "previous result")

    @patch("texcleaner.wrapper.subprocess.run")
    @patch("texcleaner.wrapper.shutil.which", return_value="/usr/local/bin/arxiv_latex_cleaner")
    def test_failed_arxiv_overwrite_preserves_existing_folder(self, _, run):
        run.return_value = subprocess.CompletedProcess([], 1, "", "cleaner failed")
        with tempfile.TemporaryDirectory() as temporary_directory:
            input_path = Path(temporary_directory) / "project"
            input_path.mkdir()
            output_path = input_path.with_name("project-cleaned")
            output_path.mkdir()
            marker = output_path / "marker.txt"
            marker.write_text("previous result", encoding="utf-8")
            success, _ = clean_arxiv(str(input_path), overwrite=True)
            self.assertFalse(success)
            self.assertEqual(marker.read_text(encoding="utf-8"), "previous result")


class DetectionAndGuiValidationTests(unittest.TestCase):
    def test_detection_scans_complete_file_and_ignores_comments(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            input_path = Path(temporary_directory) / "late.tex"
            input_path.write_text("% \\added{comment}\n" + ("x" * 21000) + r"\added{real}", encoding="utf-8")
            self.assertEqual(detect_cleaning_module(input_path), "changes")

    def test_output_helpers(self):
        self.assertEqual(generate_output_filename("paper.tex", "-final"), "paper-final.tex")
        self.assertTrue(is_valid_output_suffix("-final"))
        self.assertFalse(is_valid_output_suffix("../final"))

    def test_gui_path_validation(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            folder = Path(temporary_directory)
            tex_file = folder / "paper.tex"
            tex_file.write_text("text", encoding="utf-8")
            self.assertEqual(validate_tex_path(str(tex_file)), (True, ""))
            self.assertEqual(validate_folder_path(str(folder)), (True, ""))
            self.assertFalse(validate_tex_path(str(folder))[0])
            self.assertFalse(validate_folder_path(str(tex_file))[0])


if __name__ == "__main__":
    unittest.main()
