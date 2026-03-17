"""Terminal Output Window for ICOtest GUI"""

import os
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QPushButton,
    QCheckBox,
    QFileDialog,
)
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QFont


class TerminalWindow(QDialog):
    """Window that tails a log file in real-time"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Terminal Output")
        self.resize(800, 600)
        self.setModal(False)

        self.log_file = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._check_new_lines)

        self._setup_ui()

    def _setup_ui(self):
        """Create UI components"""
        layout = QVBoxLayout(self)

        # Text display area
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        # Use monospace font
        font = QFont("Consolas")
        font.setStyleHint(QFont.StyleHint.TypeWriter)
        self.text_edit.setFont(font)

        layout.addWidget(self.text_edit)

        # Controls area
        controls_layout = QHBoxLayout()

        self.auto_scroll_check = QCheckBox("Auto-scroll")
        self.auto_scroll_check.setChecked(True)
        controls_layout.addWidget(self.auto_scroll_check)

        controls_layout.addStretch(1)

        clear_btn = QPushButton("Clear Display")
        clear_btn.clicked.connect(self.text_edit.clear)
        controls_layout.addWidget(clear_btn)

        save_btn = QPushButton("Save to File...")
        save_btn.clicked.connect(self._save_to_file)
        controls_layout.addWidget(save_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.hide)
        controls_layout.addWidget(close_btn)

        layout.addLayout(controls_layout)

    def attach_log_file(self, file_path):
        """Start tailing a new log file"""

        if self.log_file:
            self.log_file.close()
            self.timer.stop()

        if not os.path.exists(file_path):
            self.text_edit.append(f"Waiting for log file: {file_path}")
            return

        try:
            self.log_file = open(file_path, "r", encoding="utf-8")
            # Seek to end so we only get new lines
            self.log_file.seek(0, 2)
            self.timer.start(500)  # Polling interval: 500ms
        except Exception as e:
            self.text_edit.append(f"Error opening log file: {e}")

    def _check_new_lines(self):
        """Poll the file for new lines"""
        if not self.log_file:
            return

        lines = self.log_file.readlines()
        if lines:
            for line in lines:
                # Remove trailing newline to prevent double spacing
                self.text_edit.append(line.rstrip("\r\n"))

            if self.auto_scroll_check.isChecked():
                scrollbar = self.text_edit.verticalScrollBar()
                scrollbar.setValue(scrollbar.maximum())

    def _save_to_file(self):
        """Save terminal content to a user-chosen file"""
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Log Output", "", "Text Files (*.txt);;Log Files (*.log)"
        )
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.text_edit.toPlainText())

    def append_text(self, text):
        """Append text directly from subprocess pipe instead of file tailing"""
        self.text_edit.append(text.rstrip("\r\n"))
        if self.auto_scroll_check.isChecked():
            scrollbar = self.text_edit.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

    def closeEvent(self, event):
        """Handle window close"""
        # We just hide it instead of closing so it can be re-opened
        self.hide()
        event.ignore()
