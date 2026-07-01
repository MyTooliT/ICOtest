"""Combined result dialog for Flash + Test workflow"""

import sys
import os
import subprocess

# pylint: disable=no-name-in-module

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QCheckBox,
    QScrollArea,
    QWidget,
    QApplication,
    QFrame,
)

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

# pylint: enable=no-name-in-module


class CombinedResultDialog(QDialog):
    """Shows new Base64 MAC and test results in one view"""

    def __init__(self, device_name, is_new_device, test_results, parent=None):
        super().__init__(parent)
        self.device_name = device_name
        self.is_new_device = is_new_device
        self.test_results = test_results

        self.setWindowTitle("ICOtest Results")
        self.resize(600, 700)
        self.setModal(True)

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # 1. MAC Display Section (Only for new devices)
        if self.is_new_device:
            self._setup_mac_section(layout)

            # Separator
            sep = QFrame()
            sep.setFrameShape(QFrame.Shape.HLine)
            sep.setFrameShadow(QFrame.Shadow.Sunken)
            layout.addWidget(sep)
            layout.addSpacing(10)

        # 2. Test Results Section
        self._setup_results_section(layout)

        # 3. Action Buttons
        self._setup_action_buttons(layout)

    def _setup_mac_section(self, layout):
        """Build the red MAC display box"""
        title = QLabel("DEVICE PROGRAMMED SUCCESSFULLY")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(title)

        subtitle = QLabel("NEW DEVICE NAME:")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        # Huge MAC label
        self.mac_label = QLabel(self.device_name)
        self.mac_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mac_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.mac_label.setStyleSheet("""
            QLabel {
                font-family: Consolas, monospace;
                font-size: 60pt;
                font-weight: bold;
                color: #d32f2f;
                background-color: #ffebee;
                border: 4px solid #d32f2f;
                padding: 20px;
                border-radius: 10px;
            }
        """)
        layout.addWidget(self.mac_label)

        instruction = QLabel("WRITE THIS ON THE PCB LABEL NOW!")
        instruction.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instruction.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        instruction.setStyleSheet("color: #d32f2f;")
        layout.addWidget(instruction)

        # Copy and Checkbox
        controls_layout = QHBoxLayout()

        copy_btn = QPushButton("Copy to Clipboard")
        copy_btn.clicked.connect(self._copy_to_clipboard)
        copy_btn.setMinimumHeight(40)
        controls_layout.addWidget(copy_btn)

        self.confirm_checkbox = QCheckBox(
            f"I have written {self.device_name} on the PCB"
        )
        self.confirm_checkbox.setStyleSheet(
            "font-size: 14pt; font-weight: bold;"
        )
        self.confirm_checkbox.toggled.connect(self._update_button_state)
        controls_layout.addWidget(self.confirm_checkbox)

        layout.addLayout(controls_layout)

    def _setup_results_section(self, layout):
        """Build the test results breakdown"""

        results = self.test_results.get("results", {})
        total = results.get("total", 0)
        passed = results.get("passed", 0)
        failed = results.get("failed", 0)

        # Overall badge
        badge = QLabel()
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if failed > 0:
            badge.setText(f"✗ TESTS FAILED ({passed}/{total} passed)")
            badge.setStyleSheet("""
                QLabel {
                    font-size: 16pt; font-weight: bold;
                    color: white; background-color: #f44336;
                    padding: 10px; border-radius: 5px;
                }
            """)
        else:
            badge.setText(f"✓ ALL TESTS PASSED ({passed}/{total})")
            badge.setStyleSheet("""
                QLabel {
                    font-size: 16pt; font-weight: bold;
                    color: white; background-color: #4caf50;
                    padding: 10px; border-radius: 5px;
                }
            """)
        layout.addWidget(badge)

        layout.addSpacing(10)
        layout.addWidget(QLabel("Test Details:"))

        # Scrollable list of tests
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        for test in results.get("tests", []):
            test_layout = QVBoxLayout()

            # Outcome icon
            icon = "✓" if test["outcome"] == "passed" else "✗"
            color = "green" if test["outcome"] == "passed" else "red"

            name_label = QLabel(
                f"<span style='color: {color}; font-weight:"
                f" bold;'>{icon}</span> {test['name']}"
            )
            name_label.setWordWrap(True)
            test_layout.addWidget(name_label)

            if test.get("error"):
                error_label = QLabel(
                    f"   <span style='color: #666;'>{test['error']}</span>"
                )
                error_label.setWordWrap(True)
                test_layout.addWidget(error_label)

            content_layout.addLayout(test_layout)

        scroll.setWidget(content)
        layout.addWidget(scroll)

    def _setup_action_buttons(self, layout):
        """Build bottom action buttons"""
        layout.addSpacing(10)

        # Report link
        report_path = self.test_results.get("report_path", "")
        report_layout = QHBoxLayout()
        report_layout.addWidget(
            QLabel(f"Report: {os.path.basename(report_path)}")
        )

        open_report_btn = QPushButton("Open Report")
        open_report_btn.clicked.connect(lambda: self._open_file(report_path))
        report_layout.addWidget(open_report_btn)
        layout.addLayout(report_layout)

        layout.addSpacing(10)

        # Main actions
        btn_layout = QHBoxLayout()

        self.test_another_btn = QPushButton("Test Another Device")
        self.test_another_btn.setMinimumHeight(50)
        self.test_another_btn.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.test_another_btn.clicked.connect(self.accept)

        # Disable if new device and hasn't checked box
        if self.is_new_device:
            self.test_another_btn.setEnabled(False)

        btn_layout.addWidget(self.test_another_btn)

        exit_btn = QPushButton("Exit Application")
        exit_btn.setMinimumHeight(50)
        exit_btn.clicked.connect(self.reject)
        btn_layout.addWidget(exit_btn)

        layout.addLayout(btn_layout)

    def _copy_to_clipboard(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.device_name)

    def _update_button_state(self):
        self.test_another_btn.setEnabled(self.confirm_checkbox.isChecked())

    def _open_file(self, path):
        if not path or not os.path.exists(path):
            return

        if sys.platform == "win32":
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.call(["open", path])
        else:
            subprocess.call(["xdg-open", path])
