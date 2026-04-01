"""Workers for background test execution"""

import json
import os
import subprocess
import sys
from pathlib import Path

# pylint: disable=no-name-in-module

from PySide6.QtCore import QThread, Signal

# pylint: enable=no-name-in-module

# pylint: disable=too-few-public-methods


class TestRunner(QThread):
    """Executes icotest CLI as a subprocess and parses results"""

    status_updated = Signal(str)
    output_line = Signal(str)
    test_completed = Signal(dict)
    error_occurred = Signal(str)

    # pylint: disable=too-many-arguments, too-many-positional-arguments

    def __init__(
        self,
        device_name,
        test_group,
        log_level,
        backpack_model="None",
        parent=None,
    ):
        super().__init__(parent)
        self.device_name = device_name
        self.test_group = test_group
        self.log_level = log_level
        self.backpack_model = backpack_model

    # pylint: enable=too-many-arguments, too-many-positional-arguments

    def run(self):
        """Run the test subprocess"""
        try:
            cmd = self._build_command()

            # pylint: disable=consider-using-with
            # Start process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,  # Line buffered
                encoding="utf-8",
                errors="replace",
                env=self._build_environment(),
            )
            # pylint: enable=consider-using-with

            # Read output in real-time
            if process.stdout:
                for line in process.stdout:
                    self.output_line.emit(line)
                    self._parse_status_from_line(line)

            process.wait()

            if process.returncode == 0:
                self._handle_success()
            elif process.returncode == 1:
                self._handle_test_failure()
            else:
                self.error_occurred.emit(
                    f"Tests failed with exit code {process.returncode}"
                )

        except Exception as e:  # pylint: disable=broad-exception-caught
            self.error_occurred.emit(f"Test execution error: {str(e)}")

    def _build_command(self):
        """Construct the CLI command list"""
        cmd = [
            sys.executable,
            "-X",
            "utf8",
            "-m",
            "icotest.cli.tool",
            "--log",
            self.log_level.lower(),
            "run",
            "-n",
            self.device_name,
            "--test-group",
            self.test_group,
        ]

        if self.backpack_model == "None":
            cmd.append("--skip-backpack")

        return cmd

    def _build_environment(self):
        """Force UTF-8 behavior for the child process."""

        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        return env

    def _parse_status_from_line(self, line):
        """Extract status updates from log lines"""
        # Very basic heuristic, can be improved
        if "Uploading firmware" in line or "commander flash" in line:
            self.status_updated.emit("Flashing firmware...")
        elif "Starting " in line and "test" in line.lower():
            self.status_updated.emit("Running tests...")

    def _handle_success(self):
        """Parse JSON report and emit results"""
        try:
            report_data = self._parse_latest_report()
            self.test_completed.emit({
                "returncode": 0,
                "device_name": report_data.get(
                    "device_name", self.device_name
                ),
                "report_path": report_data.get("report_path"),
                "results": report_data.get("results", {}),
            })
        except Exception as e:  # pylint: disable=broad-exception-caught
            self.error_occurred.emit(f"Failed to parse test report: {str(e)}")

    def _handle_test_failure(self):
        """Parse JSON report and emit failure results"""
        try:
            report_data = self._parse_latest_report()
            self.test_completed.emit(
                {
                    "returncode": 1,
                    "device_name": report_data.get("device_name", self.device_name),
                    "report_path": report_data.get("report_path"),
                    "results": report_data.get("results", {}),
                }
            )
        except Exception as e:
            self.error_occurred.emit(f"Failed to parse test report: {str(e)}")

    # pylint: disable=too-many-locals

    def _parse_latest_report(self):
        """Find and parse the most recent JSON report in reports/"""
        reports_dir = Path("reports")
        if not reports_dir.exists():
            return {}

        # Get all json files sorted by modification time
        json_files = sorted(
            reports_dir.glob("*.json"), key=os.path.getmtime, reverse=True
        )

        if not json_files:
            return {}

        latest_report = json_files[0]

        with open(latest_report, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Prefer the device name stored in test metadata.
        device_name = self._extract_device_name_from_report(data) or self.device_name

        # Parse test results
        summary = data.get("summary", {})
        results = {
            "total": summary.get("total", 0),
            "passed": summary.get("passed", 0),
            "failed": summary.get("failed", 0),
            "tests": [],
        }

        for test in data.get("tests", []):
            test_name = test["nodeid"].split("::")[-1]
            outcome = test["outcome"]
            error = None

            if outcome == "failed":
                longrepr = test.get("call", {}).get("longrepr", "")
                if longrepr:
                    error_lines = []
                    for line in str(longrepr).split("\n"):
                        if line.startswith("E "):
                            content = line[2:].strip()
                            # Skip the raw variable evaluation line created by Pytest
                            if not content.startswith("assert "):
                                error_lines.append(content)

                    if error_lines:
                        error = "\n".join(error_lines)
                    else:
                        # Fallback if no specific 'E' lines were found
                        lines = str(longrepr).split("\n")
                        error = "\n".join(lines[:3])

            results["tests"].append(
                {"name": test_name, "outcome": outcome, "error": error}
            )

        return {
            "device_name": device_name,
            "report_path": str(latest_report),
            "results": results,
        }

    # pylint: enable=too-many-locals


# pylint: enable=too-few-public-methods

    @staticmethod
    def _extract_device_name_from_report(data):
        """Read the real device name from report test metadata when present."""

        for test in data.get("tests", []):
            metadata = test.get("metadata")
            if not isinstance(metadata, dict):
                continue

            for key in ("Sensor Node Name", "device_name", "sensor_mac_base64"):
                value = metadata.get(key)
                if value:
                    return value

        return None
