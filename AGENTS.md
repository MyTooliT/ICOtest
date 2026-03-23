# ICOtest Project Guidelines

This document contains project-specific instructions for working with the ICOtest hardware testing framework.

## Project Overview

ICOtest is a Python-based framework for testing hardware devices (sensor nodes). It includes:
- A pytest-based test framework for hardware validation
- A PySide6 GUI for production testing workflows
- SQLite database for tracking device test history
- JSON report generation for test results
- Automatic error recovery with STU reset on connection and streaming failures

## Operational Guidelines

### 1. Ask for Clarification
If you encounter any ambiguity regarding:
- Project-specific logic or architecture
- Naming conventions (e.g., node names like "Pelzm_04" vs. "Minion04")
- Hardware identifiers or configurations
- Architectural decisions

Stop and ask the user for clarification using the `question` tool or direct inquiry.

### 2. Confirm Before Significant Action
Provide a concise plan for complex tasks and wait for user approval before implementing changes.

### 3. Use the Survey Tool for Complex Decisions (Default Behavior)
When facing decisions with multiple options, configurations, or design choices, use the `question` tool instead of asking in text. This applies to:
- Multiple implementation choices or design decisions
- Configuration or naming convention options
- Scope decisions (e.g., "should this apply to X, Y, or Z?")
- Any decision affecting code changes

This ensures clarity, captures decisions clearly, and provides a better user experience.

### 4. Adhere to Project Conventions
Rigorously follow the existing style and structural patterns found in the codebase:
- Follow the naming conventions already established
- Match the code style and formatting
- Use the same patterns for similar features

### 5. Data Integrity and Reporting
Prioritize capturing and logging measurement data in the production reporting system. JSON reports must be generated automatically for all test runs and should include:
- Device identification (Bluetooth name and MAC address)
- Test results (passed/failed counts)
- Detailed error messages for failed tests
- Timestamps for all test runs

Report filenames follow the pattern: `{SensorNodeName}_{CleanedMAC}_{Timestamp}.json`

### 6. No Assumptions About Hardware
Do not assume the presence of hardware identifiers or configurations. Always:
- Verify configurations before proceeding
- Ask the user if hardware settings differ from defaults
- Handle missing or misconfigured hardware gracefully

### 7. Request User Confirmation for Commits
Do not commit changes without asking the user first. Process:
1. Analyze staged changes
2. Provide a commit message suggestion
3. Ask the user for approval or refinements
4. Only commit after user confirmation

### 8. Pragmatic Implementation
Not every suggestion needs to be fully implemented. When the user makes suggestions:
- Challenge aspects that may overcomplicate implementation
- Identify which parts are suitable for immediate implementation
- Propose deferring valuable but unformed ideas to TODOs or documentation
- Communicate trade-offs clearly

## Testing Framework

### Key Components

**Fixtures** (`icotest/test/conftest.py`):
- `stu` - STU connection management
- `sensor_node` - Sensor node connection with automatic reset on timeout
- `sth` - STH-specific sensor connection with automatic reset
- `json_metadata` - JSON report metadata recording

**Features**:
- Automatic STU reset when connection fails with "Unable to connect to sensor"
- Automatic STU reset when data streaming disable fails with "Unable to disable data streaming"
- Auto-retry after reset (3-second wait)
- Comprehensive error extraction for GUI display
- JSON report generation with device tracking including sensor MAC address

### Test Groups

- `initial` - Firmware upload and device renaming
- `production` - Power consumption and sensor tests
- `full` - All tests except STU-specific

## GUI Application

### Structure
- `icotest/gui/main_window.py` - Main application window
- `icotest/gui/workers/test_runner.py` - Background test execution
- `icotest/gui/database/device_db.py` - Device tracking database
- `icotest/gui/dialogs/` - Result dialogs and terminal output

### Behavior
- Log level is hardcoded to "INFO" for all test runs
- Tests are run via the CLI tool (`icotest.cli.tool`)
- Failed tests are displayed with clean error messages (without Pytest source code)
- Test results are stored in SQLite database (`data/devices.db`)
- JSON reports are automatically generated and stored in `reports/` directory

## Command Line Usage

### Running Tests
```bash
uv run icotest --log info run --test-group production -n DeviceName
```

### Starting the GUI
```bash
uv run python -m icotest.cli.gui_main
```

## Database

**Location**: `data/devices.db` (SQLite)

**Tables**:
- `devices` - Tracks programmed and tested devices
  - `device_name` (PRIMARY KEY)
  - `programmed_at` (ISO timestamp)
  - `backpack_model` (hardware variant)
  - `test_status` (pending/passed/failed)
  - `test_completed_at` (ISO timestamp)
  - `report_path` (path to JSON report)

## Important Files

- `.opencoderules` - Legacy rules file (see `AGENTS.md` for active rules)
- `AGENTS.md` - This file with project guidelines (automatically loaded)
- `icotest/cli/tool.py` - CLI command handler
- `icotest/test/conftest.py` - Pytest configuration and fixtures
- `icotest/gui/workers/test_runner.py` - GUI test runner worker
