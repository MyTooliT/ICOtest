"""Main Application Window for ICOtest GUI"""

import sys
import json
from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QLineEdit,
    QPushButton,
    QGroupBox,
    QFormLayout,
    QMessageBox,
    QApplication,
)
from PySide6.QtCore import Qt, QThread, Signal

from icotest.gui.dialogs.combined_result import CombinedResultDialog
from icotest.gui.dialogs.terminal_output import TerminalWindow
from icotest.gui.workers.test_runner import TestRunner
from icotest.gui.database.device_db import DeviceDatabase


class DeviceScanner(QThread):
    """Background worker to scan for Bluetooth sensor nodes"""

    devices_found = Signal(list)
    scan_failed = Signal(str)

    def run(self):
        """Scan for available sensor nodes"""
        from icotronic.can.connection import Connection
        import asyncio

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            async def scan():
                async with Connection() as stu:
                    nodes = await stu.collect_sensor_nodes(timeout=5)
                    return [(node.name, str(node.mac_address)) for node in nodes]

            devices = loop.run_until_complete(scan())
            loop.close()
            self.devices_found.emit(devices)

        except Exception as e:
            self.scan_failed.emit(str(e))


class MainWindow(QMainWindow):
    """Main window for ICOtest Production Assistant"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("ICOtest Production Assistant")
        self.setFixedSize(700, 450)

        self.db = DeviceDatabase()
        self.terminal = TerminalWindow(self)
        self.test_runner = None
        self.production_runner = None

        # Load persisted settings
        self.config_file = Path.home() / ".icotest_gui.json"
        self._load_config()

        self._setup_ui()
        self._validate_ui_state()

    def _setup_ui(self):
        """Create and layout all widgets"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # 1. Header (Title + Logger)
        header_layout = QHBoxLayout()
        title = QLabel("ICOtest Production Assistant")
        title.setStyleSheet("font-size: 16pt; font-weight: bold;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        header_layout.addWidget(QLabel("Logger Level:"))
        self.logger_combo = QComboBox()
        self.logger_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.logger_combo.setCurrentText(self.config.get("logger_level", "WARNING"))
        self.logger_combo.currentTextChanged.connect(self._save_config)
        header_layout.addWidget(self.logger_combo)

        main_layout.addLayout(header_layout)
        main_layout.addSpacing(20)

        # 2. Hardware Configuration
        config_group = QGroupBox("Hardware Configuration")
        config_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        form_layout = QFormLayout(config_group)
        form_layout.setSpacing(15)

        # BackPack Dropdown
        self.backpack_combo = QComboBox()
        self.backpack_combo.addItems(["None", "BaP-DBS-1.3.0"])
        form_layout.addRow("BackPack Hardware:", self.backpack_combo)

        # Device Name (for retest only) - Scan button + dropdown
        device_layout = QHBoxLayout()
        self.device_combo = QComboBox()
        self.device_combo.setEditable(True)
        self.device_combo.setPlaceholderText("Select device or enter name...")
        self.device_combo.setMinimumWidth(200)
        self.device_combo.currentIndexChanged.connect(self._validate_ui_state)
        device_layout.addWidget(self.device_combo)

        self.scan_btn = QPushButton("Scan")
        self.scan_btn.setMaximumWidth(60)
        self.scan_btn.clicked.connect(self._on_scan_clicked)
        device_layout.addWidget(self.scan_btn)

        form_layout.addRow("Device (for retest):", device_layout)

        main_layout.addWidget(config_group)
        main_layout.addSpacing(20)

        # 3. Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(20)

        self.flash_btn = QPushButton("Flash New Device\n(Initialize board)")
        self.flash_btn.setMinimumHeight(60)
        self.flash_btn.setStyleSheet("""
            QPushButton { font-size: 12pt; font-weight: bold; }
            QPushButton:disabled { color: #888; }
        """)
        self.flash_btn.clicked.connect(self._on_flash_clicked)
        btn_layout.addWidget(self.flash_btn)

        self.retest_btn = QPushButton("Retest Existing Device\n(Skip flash)")
        self.retest_btn.setMinimumHeight(60)
        self.retest_btn.setStyleSheet("""
            QPushButton { font-size: 12pt; font-weight: bold; }
            QPushButton:disabled { color: #888; }
        """)
        self.retest_btn.clicked.connect(self._on_retest_clicked)
        btn_layout.addWidget(self.retest_btn)

        main_layout.addLayout(btn_layout)
        main_layout.addSpacing(20)

        # 4. Status and Terminal
        footer_layout = QHBoxLayout()

        self.status_label = QLabel("Status: Ready")
        self.status_label.setStyleSheet("font-size: 11pt; color: #555;")
        footer_layout.addWidget(self.status_label)

        footer_layout.addStretch()

        term_btn = QPushButton("Show Terminal Output")
        term_btn.clicked.connect(self.terminal.show)
        footer_layout.addWidget(term_btn)

        main_layout.addLayout(footer_layout)

    def _validate_ui_state(self):
        """Enable/disable buttons based on input"""
        name = self.device_combo.currentText().strip()

        # Flash: requires empty name
        self.flash_btn.setEnabled(len(name) == 0)

        # Retest: requires valid name
        is_valid_name = len(name) > 0 and name.isalnum()
        self.retest_btn.setEnabled(is_valid_name)

    def _set_ui_running(self, is_running):
        """Disable inputs during execution"""
        self.device_combo.setEnabled(not is_running)
        self.scan_btn.setEnabled(not is_running)
        self.backpack_combo.setEnabled(not is_running)
        self.logger_combo.setEnabled(not is_running)

        if is_running:
            self.flash_btn.setEnabled(False)
            self.retest_btn.setEnabled(False)
        else:
            self._validate_ui_state()

    def _load_config(self):
        self.config = {}
        if self.config_file.exists():
            try:
                with open(self.config_file, "r") as f:
                    self.config = json.load(f)
            except Exception:
                pass

    def _save_config(self):
        self.config["logger_level"] = self.logger_combo.currentText()
        try:
            with open(self.config_file, "w") as f:
                json.dump(self.config, f)
        except Exception:
            pass

    def _on_flash_clicked(self):
        """Start the 'Flash New Device' workflow"""
        self._set_ui_running(True)
        self.status_label.setText("Status: Flashing firmware...")
        self.status_label.setStyleSheet(
            "font-size: 11pt; color: #0066cc; font-weight: bold;"
        )
        self.terminal.text_edit.clear()

        # Assuming Minion04 is the default factory name
        self.test_runner = TestRunner(
            device_name="Minion04",
            test_group="initial",
            log_level=self.logger_combo.currentText(),
            backpack_model=self.backpack_combo.currentText(),
            parent=self,
        )

        self.test_runner.status_updated.connect(
            lambda s: self.status_label.setText(f"Status: {s}")
        )
        self.test_runner.output_line.connect(self.terminal.append_text)
        self.test_runner.error_occurred.connect(self._on_test_error)
        self.test_runner.test_completed.connect(self._on_flash_completed)

        self.test_runner.start()

    def _on_flash_completed(self, result_dict):
        """Initial flash is done, now run production tests automatically"""
        base64_mac = result_dict.get("device_name")
        if not base64_mac or base64_mac == "Minion04":
            self._on_test_error("Failed to extract new Base64 MAC address")
            return

        self.status_label.setText(f"Status: Running tests on {base64_mac}...")

        # Save to DB
        self.db.insert_device(base64_mac, self.backpack_combo.currentText())

        # Run production tests
        self._run_production_tests(base64_mac, is_new_device=True)

    def _on_scan_clicked(self):
        """Scan for available Bluetooth sensor nodes"""
        self.scan_btn.setEnabled(False)
        self.scan_btn.setText("Scanning...")
        self.status_label.setText("Status: Scanning for devices...")
        self.terminal.append_text("Scanning for Bluetooth sensor nodes...\n")

        self.scanner = DeviceScanner(self)
        self.scanner.devices_found.connect(self._on_scan_completed)
        self.scanner.scan_failed.connect(self._on_scan_failed)
        self.scanner.start()

    def _on_scan_completed(self, devices):
        """Handle scan completed - populate dropdown"""
        self.scan_btn.setEnabled(True)
        self.scan_btn.setText("Scan")
        self.status_label.setText("Status: Ready")

        # Clear and populate combo
        self.device_combo.clear()

        if not devices:
            self.terminal.append_text("No sensor nodes found.\n")
            QMessageBox.information(self, "Scan Complete", "No sensor nodes found.")
            return

        # Add devices to combo - show only name, store name as data
        for name, mac in devices:
            self.device_combo.addItem(name, name)  # Display name, store name as data

        self.terminal.append_text(f"Found {len(devices)} device(s):\n")
        for name, mac in devices:
            self.terminal.append_text(f"  - {name} ({mac})\n")

    def _on_scan_failed(self, error_msg):
        """Handle scan failure"""
        self.scan_btn.setEnabled(True)
        self.scan_btn.setText("Scan")
        self.status_label.setText("Status: Scan failed")
        self.terminal.append_text(f"Scan failed: {error_msg}\n")
        QMessageBox.warning(
            self, "Scan Failed", f"Failed to scan for devices:\n{error_msg}"
        )

    def _on_retest_clicked(self):
        """Start the 'Retest Existing' workflow"""
        # Use currentData if available (from scan), otherwise currentText (manual entry)
        device_name = (
            self.device_combo.currentData() or self.device_combo.currentText().strip()
        )
        self._set_ui_running(True)
        self.status_label.setText(f"Status: Running tests on {device_name}...")
        self.status_label.setStyleSheet(
            "font-size: 11pt; color: #0066cc; font-weight: bold;"
        )
        self.terminal.text_edit.clear()

        # If this is a manual retest of a board not in DB, insert it
        if not self.db.device_exists(device_name):
            self.db.insert_device(device_name, self.backpack_combo.currentText())

        self._run_production_tests(device_name, is_new_device=False)

    def _run_production_tests(self, device_name, is_new_device):
        self.production_runner = TestRunner(
            device_name=device_name,
            test_group="production",
            log_level=self.logger_combo.currentText(),
            backpack_model=self.backpack_combo.currentText(),
            parent=self,
        )

        self.production_runner.status_updated.connect(
            lambda s: self.status_label.setText(f"Status: {s}")
        )
        self.production_runner.output_line.connect(self.terminal.append_text)
        self.production_runner.error_occurred.connect(self._on_test_error)

        # Capture the context for the callback
        self.production_runner.test_completed.connect(
            lambda res: self._on_production_completed(res, is_new_device)
        )

        self.production_runner.start()

    def _on_production_completed(self, result_dict, is_new_device):
        """Tests finished, show summary dialog"""
        self.status_label.setText("Status: Complete")
        self.status_label.setStyleSheet(
            "font-size: 11pt; color: #4caf50; font-weight: bold;"
        )
        self._set_ui_running(False)

        device_name = result_dict.get("device_name", "Unknown")
        results = result_dict.get("results", {})
        report_path = result_dict.get("report_path")

        # Update DB
        status = "passed" if results.get("failed", 0) == 0 else "failed"
        self.db.update_test_status(device_name, status, report_path)

        # Show combined dialog
        dialog = CombinedResultDialog(device_name, is_new_device, result_dict, self)

        if dialog.exec():
            # User clicked "Test Another Device"
            self.device_combo.setCurrentIndex(0)
            self.status_label.setText("Status: Ready")
            self.status_label.setStyleSheet("font-size: 11pt; color: #555;")
        else:
            # User clicked "Exit"
            QApplication.quit()

    def _on_test_error(self, error_msg):
        """Handle subprocess or parsing errors"""
        self.status_label.setText("Status: Error")
        self.status_label.setStyleSheet(
            "font-size: 11pt; color: #d32f2f; font-weight: bold;"
        )
        self._set_ui_running(False)

        QMessageBox.critical(
            self,
            "Execution Error",
            f"An error occurred during execution:\n\n{error_msg}\n\nCheck terminal output for details.",
        )
