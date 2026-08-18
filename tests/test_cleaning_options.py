import subprocess
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from texcleaner.server import app
from texcleaner.wrapper import clean_arxiv, clean_changes, clean_trackchanges


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
            input_path = Path(command[1])
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


class OutputPathAPITests(unittest.TestCase):
    def test_completed_job_reports_exact_output_path(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            input_path = Path(temporary_directory) / "manuscript.tex"
            input_path.write_text(r"A \added{new} result.", encoding="utf-8")
            expected_output = input_path.with_name("manuscript-reviewed.tex")

            client = TestClient(app)
            response = client.post(
                "/clean/changes",
                json={
                    "input_path": str(input_path),
                    "keep_version": "new",
                    "remove_annotations": True,
                    "output_suffix": "-reviewed",
                    "overwrite": False,
                },
            )
            job_id = response.json()["job_id"]

            for _ in range(100):
                detail = client.get(f"/jobs/{job_id}").json()
                if detail["status"] in {"success", "error"}:
                    break
                time.sleep(0.01)

            self.assertEqual(detail["status"], "success")
            self.assertEqual(detail["output_path"], str(expected_output))
            self.assertTrue(expected_output.exists())


if __name__ == "__main__":
    unittest.main()
