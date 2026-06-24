# ICOtest Production GUI - Technical Design Specification

**Version:** 1.0  
**Date:** 2026-03-17  
**Status:** Approved for Implementation

---

## 1. Executive Summary

This document specifies the design and implementation of a graphical user interface (GUI) for the ICOtest hardware testing framework. The GUI is designed for production line technicians to program and test ICOtronic sensor nodes with minimal training required.

### Key Design Principles
- **Simplicity First**: Remove complexity wherever possible
- **Clear Workflow**: Guide operators through a linear process
- **Immediate Feedback**: Show test progress and results in real-time
- **Traceability**: Track all programmed devices in local database
- **Maintainability**: Easy to extend and modify later

### Target Users
- Production line technicians with basic computer skills
- Engineering staff performing ad-hoc testing and diagnostics

---

## 2. Architecture Overview

### Technology Stack
- **GUI Framework**: PySide6 (Qt for Python, LGPL license)
- **Test Execution**: Subprocess invocation of existing `icotest` CLI tool
- **Database**: SQLite for local device tracking
- **Configuration**: Reuses existing dynaconf-based config system

### Project Structure
```
icotest/
├── cli/
│   ├── tool.py           # Existing CLI (unchanged)
│   └── gui_main.py       # NEW: GUI entry point
├── gui/                  # NEW: GUI module
│   ├── __init__.py
│   ├── main_window.py    # Main application window
│   ├── dialogs.py        # Combined result dialog
│   ├── terminal.py       # Terminal output window
│   ├── workers.py        # Background test execution
│   └── database.py       # SQLite operations
```

**Estimated Total Lines of Code**: ~700-900 lines

### Integration Approach
- **Non-invasive**: Does not modify existing CLI tool or test framework
- **Subprocess-based**: Runs `icotest` CLI as separate process
- **Report-based**: Parses JSON reports for results (no internal API coupling)

---

## 3. Design Decisions & Rationale

### 3.1 Hardware Configuration Simplification

**Decision**: Remove sensor selection from GUI entirely.

**Rationale**:
- In practice, almost all devices have ADXL356 + ADXL1001 present
- Sensor configuration adds complexity without practical value
- `config.yaml` already has correct defaults
- Reduces GUI from 3 checkboxes + validation logic to zero

**Impact**:
- Removes ~100 lines of code
- Eliminates need for dynaconf environment variable manipulation
- Simpler UI with less cognitive load

### 3.2 Combined Result Dialog (Option A)

**Decision**: Show device name and test results in a single dialog instead of two separate dialogs.

**Rationale**:
- **Time Savings**: 4-8 hours development time saved (32% less code)
- **Better UX**: Operator sees everything in one glance, fewer clicks
- **Simpler State Machine**: 3 states instead of 5, easier to maintain
- **Lower Bug Risk**: Fewer dialog transitions = fewer edge cases

**Tradeoff**: Less isolated "write on PCB" prompt, mitigated by:
- Large, prominent MAC display (60pt font)
- Required checkbox: "☐ I have written [NAME] on the PCB label"
- Red border around MAC section for visibility

**Alternative Considered**: Two separate dialogs (Flash Complete → Test Summary)
- Rejected due to higher complexity and marginal UX benefit

### 3.3 BackPack Configuration

**Decision**: Keep simple dropdown with toggle logic for `--skip-backpack` flag.

**Implementation**:
```python
if backpack_model == "None":
    cmd.append("--skip-backpack")
# Otherwise, run all tests (including BackPack tests)
```

**Rationale**:
- Gives operators immediate control over test execution
- Simple boolean logic (no complex filtering)
- Easy to extend with new BackPack models later

**Options**: "None" (default), "BaP-DBS-1.3.0"

### 3.4 Test Execution Strategy

**Decision**: Run all tests using existing `--test-group` CLI arguments, no environment variable manipulation.

**Commands**:
```bash
# Flash New Device:
icotest run -n Minion04 --test-group initial --log-cli-level [LEVEL]
# Then automatically:
icotest run -n [BASE64MAC] --test-group production --log-cli-level [LEVEL] [--skip-backpack]

# Retest Existing:
icotest run -n [DEVICE_NAME] --test-group production --log-cli-level [LEVEL] [--skip-backpack]
```

**Rationale**:
- Reuses battle-tested CLI tool without modification
- No risk of GUI-specific bugs affecting test execution
- Easy to debug (can reproduce issues via CLI)
- Future test group refinements are simple CLI arg changes

### 3.5 Terminal Output Window

**Decision**: Separate, optional window for detailed log viewing.

**Rationale**:
- **User Control**: Operators who don't need logs keep it closed
- **Flexibility**: Can be resized, moved to second monitor
- **Clean Main UI**: Keeps primary interface uncluttered
- **Debugging**: Essential for troubleshooting issues

**Implementation**: Non-modal QDialog with real-time log file tailing (QTimer polling every 500ms)

### 3.6 Status Indicator Minimalism

**Decision**: Simple status text with 4 states only.

**States**:
1. "Ready" - Awaiting user action
2. "Flashing firmware..." - During initial setup
3. "Running tests..." - During production tests
4. "Complete" - Tests finished (auto-clears when showing result dialog)

**Rationale**:
- Avoids complexity of granular progress tracking ("test 3/8...")
- pytest output is unpredictable, hard to parse reliably
- Detailed progress visible in terminal window if needed
- Simpler to implement and maintain

**Alternative Considered**: Granular progress bar with per-test status
- Rejected due to parsing complexity and marginal user value

### 3.7 No Standalone Packaging (Phase 1)

**Decision**: Ship as Python application requiring local Python environment.

**Rationale**:
- **Validate Workflow First**: Ensure GUI actually improves productivity before investing in packaging
- **Easier Iteration**: Faster development cycle without packaging overhead
- **Future-Proof**: Can add PyInstaller/.exe packaging later if validated

**Deployment**: Users run `python -m icotest.cli.gui_main` or via entry point `icotest-gui`

### 3.8 Database Schema Simplification

**Decision**: Track only essential device information, defer advanced features.

**Schema**:
```sql
CREATE TABLE devices (
    device_name TEXT PRIMARY KEY,       -- Base64 MAC address
    programmed_at TEXT NOT NULL,        -- ISO timestamp
    backpack_model TEXT,                -- "None" or "BaP-DBS-1.3.0"
    test_status TEXT,                   -- 'pending', 'passed', 'failed'
    test_completed_at TEXT,             -- ISO timestamp
    report_path TEXT                    -- Path to JSON report
);
```

**Rationale**:
- Removed `sensor` field (always ADXL356 + ADXL1001)
- Removed `notes` field (defer to future if needed)
- Removed `firmware_version` (can parse from report if needed)
- Simple schema = easier queries and maintenance

**Storage Location**: `data/devices.db` (created automatically on first run)

---

## 4. User Interface Specification

### 4.1 Main Window

```
┌────────────────────────────────────────────────────────────────┐
│  ICOtest Production Assistant           Logger: [WARNING ▼]   │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ Hardware Configuration                                    │ │
│  │                                                           │ │
│  │ BackPack Hardware:                                        │ │
│  │ [None                    ▼]                               │ │
│  │                                                           │ │
│  │ Device Name (for retest only):                           │ │
│  │ [____________]                                            │ │
│  │ (Leave blank for new device)                             │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌─────────────────────────┐  ┌─────────────────────────┐     │
│  │ Flash + Rename + Test   │  │      Rename Only        │     │
│  │   (Initialize board)    │  │ (Recovery rename only)  │     │
│  └─────────────────────────┘  └─────────────────────────┘     │
│  ┌─────────────────────────┐  ┌─────────────────────────┐     │
│  │     Flash Only          │  │  Retest Existing Device │     │
│  │  (Firmware only)        │  │  (Run production tests) │     │
│  └─────────────────────────┘  └─────────────────────────┘     │
│                                                                 │
│  Status: Ready                                                 │
│                                                                 │
│  [Show Terminal Output]                                        │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

**Window Properties**:
- Fixed size: 700x520 pixels
- Centered on screen at startup
- Title: "ICOtest Production Assistant"
- Not resizable (keeps layout consistent)

**Widget Specifications**:

| Widget | Type | Properties |
|--------|------|------------|
| Logger Dropdown | QComboBox | Options: DEBUG, INFO, WARNING, ERROR. Default: WARNING. Persisted to local config. |
| BackPack Dropdown | QComboBox | Options: "None", "BaP-DBS-1.3.0". Default: "None". |
| Device Name Input | QLineEdit | Max 8 chars. Alphanumeric only. Placeholder: "Leave blank for new device". |
| Flash + Rename + Test Button | QPushButton | Enabled only when device name is empty. |
| Rename Only Button | QPushButton | Enabled when device name is valid. |
| Flash Only Button | QPushButton | Always enabled. |
| Retest Button | QPushButton | Enabled only when device name is valid. |
| Status Label | QLabel | Gray text, left-aligned. Updates during execution. |
| Terminal Button | QPushButton | Opens terminal window. Always enabled. |

**Validation Rules**:
```python
def validate_ui_state(self):
    device_name = self.device_name_input.text().strip()
    
    # Flash + Rename + Test button: requires empty device name
    self.flash_test_button.setEnabled(len(device_name) == 0)
    
    # Rename and Retest buttons: require non-empty, valid device name
    is_valid_name = (
        len(device_name) > 0 and 
        len(device_name) <= 8 and 
        device_name.isalnum()
    )
    self.rename_button.setEnabled(is_valid_name)
    self.retest_button.setEnabled(is_valid_name)
    self.flash_only_button.setEnabled(True)
```

### 4.2 Combined Result Dialog

```
┌───────────────────────────────────────────────────────┐
│  Device Programmed & Tested               [X] Close   │
├───────────────────────────────────────────────────────┤
│                                                        │
│  ┌──────────────────────────────────────────────────┐ │
│  │ ************************************************ │ │
│  │                                                  │ │
│  │         NEW DEVICE NAME: BYUgAHwA               │ │
│  │                                                  │ │
│  │         WRITE THIS ON THE PCB LABEL NOW!        │ │
│  │                                                  │ │
│  │ ************************************************ │ │
│  │                                                  │ │
│  │ [Copy to Clipboard]                             │ │
│  │                                                  │ │
│  │ ☐ I have written BYUgAHwA on the PCB label      │ │
│  └──────────────────────────────────────────────────┘ │
│                                                        │
│  ─────────────────────────────────────────────────    │
│                                                        │
│  ┌──────────────────────────────────────────────────┐ │
│  │          ✓ ALL TESTS PASSED                      │ │
│  │            8 / 8 tests                           │ │
│  └──────────────────────────────────────────────────┘ │
│                                                        │
│  Test Details:                                        │
│  ✓ test_power_usage_disconnected                     │
│  ✓ test_power_usage_connected                        │
│  ✓ test_power_usage_streaming                        │
│  ✓ test_acceleration_sensor_self_test                │
│  ✓ test_acceleration_single_value                    │
│  ✓ test_acceleration_noise                           │
│  ✓ test_acceleration_3a_alt                          │
│  ✓ test_acceleration_3a_optimized                    │
│                                                        │
│  Report: reports/ICOtronic_BYUgAHwA_2026-03-17_...   │
│  [Open Report]                                        │
│                                                        │
│  [Test Another Device]  [Exit Application]           │
└───────────────────────────────────────────────────────┘
```

**Dialog Properties**:
- Modal (blocks main window)
- Size: 600x700 pixels
- Centered on main window

**MAC Name Section Styling**:
```python
mac_label.setStyleSheet("""
    QLabel {
        font-size: 60pt;
        font-weight: bold;
        color: #d32f2f;  /* Red */
        background-color: #ffebee;
        border: 3px solid #d32f2f;
        padding: 20px;
        border-radius: 10px;
    }
""")
```

**Checkbox Behavior**:
- "Test Another Device" button disabled until checkbox is checked
- Forces operator acknowledgment of PCB labeling

**Test Results Section**:
- If PASSED: Green checkmark (✓), green badge
- If FAILED: Red X (✗), red badge, show error messages
- Test list scrollable if more than 10 tests

### 4.3 Terminal Output Window

```
┌──────────────────────────────────────────────────────┐
│  Test Output                              [X] Close  │
├──────────────────────────────────────────────────────┤
│  INFO   Using sensor node name: BYUgAHwA            │
│  INFO   Running production tests (power + sensors)   │
│  INFO   Power usage (disconnected): 1.05 mW         │
│  INFO   Power usage (connected): 21.3 mW            │
│  INFO   Power usage (streaming): 43.2 mW            │
│  ...                                                 │
│                                                      │
│  [✓] Auto-scroll  [Clear]  [Save to File...]        │
└──────────────────────────────────────────────────────┘
```

**Window Properties**:
- Non-modal (can stay open while using main window)
- Size: 800x600 pixels (resizable)
- Position: Right side of screen by default

**Implementation Details**:
```python
class TerminalWindow(QDialog):
    def __init__(self, log_file_path):
        super().__init__()
        self.log_file = open(log_file_path, 'r')
        self.log_file.seek(0, 2)  # Seek to end
        
        # Tail log file every 500ms
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_new_lines)
        self.timer.start(500)
    
    def check_new_lines(self):
        line = self.log_file.readline()
        if line:
            self.text_edit.append(line.rstrip())
            if self.auto_scroll_checkbox.isChecked():
                self.text_edit.moveCursor(QTextCursor.End)
```

**Features**:
- Auto-scroll (default: enabled)
- Clear button (clears display, doesn't delete log file)
- Save button (exports current content to user-chosen file)
- Monospace font for readability

---

## 5. Workflow Specifications

### 5.1 Flash + Rename + Test Workflow

**Preconditions**:
- Device is powered and within range of STU
- Device name input is empty

**Steps**:
1. User selects BackPack configuration
2. User selects logger level (if not using default)
3. User clicks "Flash + Rename + Test" button
4. GUI validates: device name is empty ✓
5. GUI disables buttons, updates status: "Flashing firmware..."
6. GUI spawns background thread to run:
   ```bash
   icotest run -n Minion04 --test-group initial --log-cli-level [LEVEL]
   ```
7. Terminal window streams output in real-time (if open)
8. Thread monitors subprocess completion
9. On completion, GUI parses latest JSON report to extract Base64 MAC
10. GUI updates status: "Running tests..."
11. GUI spawns new thread to run:
    ```bash
    icotest run -n [BASE64MAC] --test-group production --log-cli-level [LEVEL] [--skip-backpack if None]
    ```
12. Thread monitors subprocess completion
13. On completion, GUI parses JSON report for test results
14. GUI saves device to database:
    ```python
    db.insert_device(
        device_name=base64_mac,
        programmed_at=datetime.now().isoformat(),
        backpack_model=backpack_selection,
        test_status="pending"
    )
    ```
15. GUI shows Combined Result Dialog with MAC + test results
16. User checks "I have written [NAME] on the PCB label" checkbox
17. GUI updates database:
    ```python
    db.update_test_status(
        device_name=base64_mac,
        status="passed" or "failed",
        completed_at=datetime.now().isoformat(),
        report_path=report_path
    )
    ```
18. User clicks "Test Another Device" or "Exit"
19. If "Test Another Device": GUI resets to Ready state
20. If "Exit": Application closes

**Error Handling**:
- Subprocess timeout (10 minutes): Show error dialog, return to Ready
- Subprocess non-zero exit: Show error with stderr, return to Ready
- JSON parsing failure: Show error, return to Ready
- Database write failure: Log warning, continue (non-critical)

### 5.2 Flash Only Workflow

**Preconditions**:
- Device is powered and within range of STU

**Steps**:
1. User enters the current device name or leaves the default name in place
2. User selects BackPack configuration
3. User clicks "Flash Only" button
4. GUI validates: button is always available
5. GUI disables inputs and starts the firmware upload test group
6. GUI runs:
   ```bash
   icotest run -n [DEVICE_NAME] --test-group flash-only --log-cli-level [LEVEL]
   ```
7. GUI shows a simple success dialog after flashing completes

### 5.3 Rename Only Workflow

**Preconditions**:
- Device already has a valid current name in the input field

**Steps**:
1. User enters the existing device name
2. User clicks "Rename Only" button
3. GUI validates the device name
4. GUI runs:
   ```bash
   icotest run -n [DEVICE_NAME] --test-group rename --log-cli-level [LEVEL]
   ```
5. GUI updates the device name field with the new Base64 name

### 5.4 Retest Existing Device Workflow

**Preconditions**:
- Device name input is NOT empty (8 chars max, alphanumeric)

**Steps**:
1. User enters device name (e.g., "BYUgAHwA")
2. User selects BackPack configuration
3. User selects logger level (if not using default)
4. User clicks "Retest Existing Device" button
5. GUI validates: device name is valid ✓
6. GUI disables buttons, updates status: "Running tests..."
7. GUI spawns background thread to run:
   ```bash
   icotest run -n [DEVICE_NAME] --test-group production --log-cli-level [LEVEL] [--skip-backpack if None]
   ```
8. Terminal window streams output in real-time (if open)
9. Thread monitors subprocess completion
10. On completion, GUI parses JSON report for test results
11. GUI checks if device exists in database:
    - If exists: Update test status
    - If not exists: Insert new record (retest of device not in our DB)
12. GUI shows Combined Result Dialog (without MAC section, just test results)
13. User clicks "Test Another Device" or "Exit"

**Note**: For retest workflow, Combined Result Dialog does NOT show MAC section or checkbox, only test results.

---

## 6. Technical Implementation Details

### 6.1 Background Test Execution

**Class**: `TestRunner(QThread)`

**Responsibilities**:
- Build pytest command with correct arguments
- Run subprocess and capture output
- Parse JSON reports
- Emit signals for UI updates

**Signals**:
```python
class TestRunner(QThread):
    status_updated = Signal(str)        # "Flashing firmware..."
    output_line = Signal(str)           # Raw stdout line
    test_completed = Signal(dict)       # {"returncode": 0, "device_name": "...", "results": {...}}
    error_occurred = Signal(str)        # Error message
```

**Implementation**:
```python
def run(self):
    try:
        # Build command
        cmd = [
            sys.executable, "-m", "icotest.cli.tool",
            "run", "-n", self.device_name,
            "--test-group", self.test_group,
            "--log-cli-level", self.log_level
        ]
        
        # Add --skip-backpack if needed
        if self.backpack_model == "None":
            cmd.append("--skip-backpack")
        
        # Run subprocess
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        # Stream output
        for line in process.stdout:
            self.output_line.emit(line)
        
        process.wait()
        
        # Parse results
        if process.returncode == 0:
            report_data = self._parse_latest_report()
            self.test_completed.emit({
                "returncode": 0,
                "device_name": report_data["device_name"],
                "results": report_data["results"]
            })
        else:
            self.error_occurred.emit(f"Tests failed with code {process.returncode}")
    
    except Exception as e:
        self.error_occurred.emit(str(e))
```

### 6.2 JSON Report Parsing

**Function**: `parse_json_report(report_path: str) -> dict`

**Returns**:
```python
{
    "device_name": "BYUgAHwA",  # Extracted from metadata or filename
    "results": {
        "total": 8,
        "passed": 8,
        "failed": 0,
        "tests": [
            {
                "name": "test_power_usage_disconnected",
                "outcome": "passed",
                "error": None
            },
            # ...
        ]
    }
}
```

**Implementation**:
```python
def parse_json_report(report_path):
    with open(report_path) as f:
        data = json.load(f)
    
    # Extract device name from filename or metadata
    device_name = None
    filename = Path(report_path).stem  # e.g., "ICOtronic_BYUgAHwA_2026-03-17_14-30"
    match = re.search(r'_([A-Za-z0-9]{8})_', filename)
    if match:
        device_name = match.group(1)
    
    # Parse test results
    results = {
        "total": data["summary"]["total"],
        "passed": data["summary"].get("passed", 0),
        "failed": data["summary"].get("failed", 0),
        "tests": []
    }
    
    for test in data.get("tests", []):
        test_name = test["nodeid"].split("::")[-1]
        outcome = test["outcome"]
        error = None
        
        if outcome == "failed":
            # Extract first line of error message
            longrepr = test.get("call", {}).get("longrepr", "")
            if longrepr:
                error = longrepr.split("\n")[0][:200]  # First 200 chars
        
        results["tests"].append({
            "name": test_name,
            "outcome": outcome,
            "error": error
        })
    
    return {
        "device_name": device_name,
        "results": results
    }
```

### 6.3 Database Operations

**Class**: `DeviceDatabase`

**Schema**:
```sql
CREATE TABLE IF NOT EXISTS devices (
    device_name TEXT PRIMARY KEY,
    programmed_at TEXT NOT NULL,
    backpack_model TEXT,
    test_status TEXT,
    test_completed_at TEXT,
    report_path TEXT
);

CREATE INDEX IF NOT EXISTS idx_programmed_at ON devices(programmed_at DESC);
```

**Methods**:
```python
class DeviceDatabase:
    def __init__(self, db_path="data/devices.db"):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self._create_tables()
    
    def insert_device(self, device_name, programmed_at, backpack_model):
        """Insert new device after programming"""
        self.conn.execute(
            """
            INSERT INTO devices (device_name, programmed_at, backpack_model, test_status)
            VALUES (?, ?, ?, 'pending')
            """,
            (device_name, programmed_at, backpack_model)
        )
        self.conn.commit()
    
    def update_test_status(self, device_name, status, completed_at, report_path):
        """Update after production tests complete"""
        self.conn.execute(
            """
            UPDATE devices
            SET test_status = ?, test_completed_at = ?, report_path = ?
            WHERE device_name = ?
            """,
            (status, completed_at, report_path, device_name)
        )
        self.conn.commit()
    
    def device_exists(self, device_name):
        """Check if device is already in database"""
        cursor = self.conn.execute(
            "SELECT 1 FROM devices WHERE device_name = ?",
            (device_name,)
        )
        return cursor.fetchone() is not None
```

### 6.4 Configuration Persistence

**Logger Level Setting**:
```python
# Save to local config file
config_file = Path.home() / ".icotest_gui.json"

def save_logger_level(level: str):
    config = {}
    if config_file.exists():
        with open(config_file) as f:
            config = json.load(f)
    config["logger_level"] = level
    with open(config_file, 'w') as f:
        json.dump(config, f)

def load_logger_level() -> str:
    if config_file.exists():
        with open(config_file) as f:
            config = json.load(f)
            return config.get("logger_level", "WARNING")
    return "WARNING"
```

---

## 7. Implementation Phases

### Phase 1: Core UI (1-2 days)
**Files**: `gui_main.py`, `main_window.py`

**Deliverables**:
- Main window layout with all widgets
- BackPack dropdown
- Device name input with validation
- Action buttons with enable/disable logic
- Logger level dropdown with persistence
- Status indicator

**Testing**:
- Buttons enable/disable correctly based on device name
- Logger level persists between app restarts
- Window layout renders correctly

### Phase 2: Test Execution (2 days)
**Files**: `workers.py`, `terminal.py`

**Deliverables**:
- `TestRunner` QThread for subprocess execution
- Command building with correct arguments
- Real-time output capture
- Terminal window with log tailing
- Status indicator updates

**Testing**:
- Can run `--test-group initial` successfully
- Can run `--test-group production` successfully
- Terminal receives output in real-time
- Status updates correctly

### Phase 3: Dialogs & Results (1 day)
**Files**: `dialogs.py`

**Deliverables**:
- Combined Result Dialog
- MAC name display with copy button
- Checkbox for PCB labeling confirmation
- Test results list with pass/fail status
- JSON report parsing

**Testing**:
- Dialog correctly shows MAC name
- Copy to clipboard works
- Checkbox prevents proceeding until checked
- Test results display correctly for pass/fail scenarios

### Phase 4: Database (1 day)
**Files**: `database.py`

**Deliverables**:
- SQLite schema creation
- Insert device after flash
- Update test status after tests
- Device existence checking

**Testing**:
- Devices correctly saved to database
- Test status updates work
- Database persists between runs

### Phase 5: Polish & Testing (1 day)
**Files**: All files

**Deliverables**:
- Error handling for all failure scenarios
- Basic Qt stylesheet for professional appearance
- User testing with real hardware
- Bug fixes

**Testing**:
- Error scenarios handled gracefully
- No crashes during normal operation
- UI looks professional

---

## 8. Future Enhancements (Deferred)

### 8.1 Device History Browser
**Description**: Screen to view all programmed devices with search/filter.

**Estimated Effort**: 1-2 days

### 8.2 Advanced BackPack Models
**Description**: Support for multiple BackPack versions with version-specific tests.

**Estimated Effort**: 0.5 days (just add to dropdown)

### 8.3 Standalone Executable Packaging
**Description**: PyInstaller-based `.exe` for Windows deployment.

**Estimated Effort**: 1 day

### 8.4 Label Printer Integration
**Description**: Direct printing of Base64 MAC names to label printer.

**Estimated Effort**: 2-3 days (hardware-dependent)

### 8.5 Multi-Device Batch Mode
**Description**: Queue multiple devices for sequential programming/testing.

**Estimated Effort**: 2-3 days

### 8.6 Cloud Database Integration
**Description**: Sync device records to central server/database.

**Estimated Effort**: 3-5 days

---

## 9. Risk Analysis & Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Subprocess hangs indefinitely | Medium | High | Implement 10-minute timeout with "Abort" button |
| JSON report format changes | Low | Medium | Version checking and fallback parsing |
| Database corruption | Very Low | Medium | SQLite is robust; regular backups recommended |
| Qt threading issues | Low | High | Use signals/slots exclusively for thread communication |
| Hardware connection issues | High | Low | Show clear error messages, provide troubleshooting guide link |

---

## 10. Success Metrics

### Phase 1 Success Criteria
- GUI launches without errors
- All widgets render correctly
- Button validation works as specified

### Phase 2 Success Criteria
- Can successfully run initial setup for a real device
- Terminal output displays in real-time
- Status indicator updates correctly

### Phase 3 Success Criteria
- Combined Result Dialog shows correct device name
- Test results parse correctly from JSON reports
- Checkbox confirmation works

### Phase 4 Success Criteria
- Devices are saved to database
- Database can be queried with SQLite browser
- Test status updates correctly

### Phase 5 Success Criteria
- Operator can program 10 devices in a row without issues
- No crashes or hangs observed
- Positive feedback from production technicians

---

## 11. Glossary

| Term | Definition |
|------|------------|
| **Base64 MAC** | 8-character Base64-encoded representation of the device's MAC address (e.g., "BYUgAHwA") |
| **BackPack** | Additional hardware module that can be attached to sensor nodes (e.g., "BaP-DBS-1.3.0") |
| **STH** | Smart Tool Holder - a type of ICOtronic sensor node |
| **STU** | Smart Tool Unit - the base station that communicates with sensor nodes |
| **Test Group** | Predefined set of pytest markers (`initial`, `production`, `full`) |
| **dynaconf** | Configuration management library used by icotest |

---

## 12. Approval & Sign-off

**Document Author**: OpenCode AI Assistant  
**Date**: 2026-03-17  
**Status**: Ready for Implementation

**Approved By**: [User]  
**Date**: [Pending]

---

## Appendix A: File Structure Reference

```
icotest/
├── gui/
│   ├── __init__.py          # Package initialization
│   ├── main_window.py       # MainWindow class (~250 lines)
│   ├── dialogs.py           # CombinedResultDialog class (~200 lines)
│   ├── terminal.py          # TerminalWindow class (~150 lines)
│   ├── workers.py           # TestRunner QThread (~150 lines)
│   └── database.py          # DeviceDatabase class (~100 lines)
├── cli/
│   └── gui_main.py          # Entry point (~30 lines)
└── doc/
    ├── INITIAL_SETUP_GUIDE.md          # Operator manual
    ├── PRODUCTION_DATA_COLLECTION.md   # Technical documentation
    └── GUI_DESIGN_SPECIFICATION.md     # This document
```

---

## Appendix B: Example Command Line Invocations

**Run GUI:**
```bash
# Via entry point (after installation):
icotest-gui

# Or directly:
python -m icotest.cli.gui_main
```

**Equivalent CLI commands that GUI executes:**
```bash
# Flash new device:
icotest run -n Minion04 --test-group initial --log-cli-level WARNING

# Then automatically:
icotest run -n BYUgAHwA --test-group production --log-cli-level WARNING --skip-backpack

# Retest existing (with BackPack):
icotest run -n BYUgAHwA --test-group production --log-cli-level INFO
```

---

**End of Design Specification**
