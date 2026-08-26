import subprocess
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from texcleaner.server import app, configure_auth_token
from texcleaner.wrapper import clean_arxiv, clean_changes, clean_trackchanges


configure_auth_token("test-token")
AUTH_HEADERS = {"Authorization": "Bearer test-token"}


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
            result = output_path.read_text(encoding="utf-8")
            self.assertEqual(result, r"A outer inner and literal \} brace.")

    def test_trackchanges_handles_nested_commands_and_escaped_braces(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            input_path = Path(temporary_directory) / "input.tex"
            output_path = Path(temporary_directory) / "output.tex"
            input_path.write_text(r"A \add{outer \add{inner}} and \add{literal \} brace}.", encoding="utf-8")
            success, _ = clean_trackchanges(input_path, output_path)
            self.assertTrue(success)
            result = output_path.read_text(encoding="utf-8")
            self.assertEqual(result, r"A outer inner and literal \} brace.")

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


class OutputPathAPITests(unittest.TestCase):
    def test_completed_job_reports_exact_output_path(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            input_path = Path(temporary_directory) / "manuscript.tex"
            input_path.write_text(r"A \added{new} result.", encoding="utf-8")
            expected_output = input_path.with_name("manuscript-reviewed.tex").resolve()

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
                headers=AUTH_HEADERS,
            )
            job_id = response.json()["job_id"]

            for _ in range(100):
                detail = client.get(f"/jobs/{job_id}", headers=AUTH_HEADERS).json()
                if detail["status"] in {"success", "error"}:
                    break
                time.sleep(0.01)

            self.assertEqual(detail["status"], "success")
            self.assertEqual(detail["output_path"], str(expected_output))
            self.assertTrue(expected_output.exists())


class APISecurityAndDetectionTests(unittest.TestCase):
    def test_api_requires_bearer_token(self):
        response = TestClient(app).get("/")
        self.assertEqual(response.status_code, 401)

    def test_detection_scans_complete_file_and_ignores_comments(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            input_path = Path(temporary_directory) / "late.tex"
            input_path.write_text("% \\added{comment}\n" + ("x" * 21000) + r"\added{real}", encoding="utf-8")
            client = TestClient(app)
            response = client.get(
                "/detect",
                params={"input_path": str(input_path)},
                headers=AUTH_HEADERS,
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["detected"], "changes")

    def test_websocket_streams_logs_and_finishes(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            input_path = Path(temporary_directory) / "stream.tex"
            input_path.write_text(r"A \added{new}.", encoding="utf-8")
            client = TestClient(app)
            response = client.post(
                "/clean/changes",
                json={"input_path": str(input_path)},
                headers=AUTH_HEADERS,
            )
            self.assertEqual(response.status_code, 200)
            job_id = response.json()["job_id"]
            with client.websocket_connect(f"/ws/logs/{job_id}", headers=AUTH_HEADERS) as websocket:
                messages = [websocket.receive_json()]
                for _ in range(20):
                    if messages[-1].get("status") in {"success", "error"}:
                        break
                    messages.append(websocket.receive_json())
            self.assertTrue(any(message.get("logs") for message in messages))
            self.assertEqual(messages[-1].get("status"), "success")


if __name__ == "__main__":
    unittest.main()
