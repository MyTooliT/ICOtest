# Initial Programming and Testing Guide

This guide is intended for operators and technicians to perform initial programming and testing on brand new ICOtronic sensor node devices.

## 1. Prerequisites

Before starting, ensure you have:
- A host computer with the **ICOtest** tool installed.
- An **STU** (Smart Tool Unit) connected to the host computer.
- The new sensor node PCB powered and within range.
- A pen or label printer to mark the device name on the PCB.

## 2. Step 1: Initial Programming and Identification

When a new device is first flashed, it will be assigned a default name (e.g., `Minion04`). This name is used to identify it during its first connection to the test system.

### Command
Run the following command to flash the firmware and set the unique Base64-encoded MAC name:

```bash
icotest run -n Minion04 --test-group initial
```

### Expected Output
The tool will flash the firmware, then read the unique MAC address of the device and rename it. You should see a large, high-visibility warning box at the end of the run:

```text
************************************************************
DEVICE RENAMED SUCCESSFULLY
NEW NAME (BASE64 MAC): BYUgAHwA
PLEASE WRITE THIS NAME ON THE PCB LABEL!
************************************************************
```

**IMPORTANT:** The name (e.g., `BYUgAHwA`) is now the permanent identity of this device. Write this name on the designated field on the PCB label immediately.

---

## 2.a Recovery: Rename-only test group

If you reflash a board that already completed initial setup, it will still boot with whatever name is written in EEPROM (for example `Minion03`).
The CLI only knows the device by its current advertised name, so the recovery path is to run the new rename-only test group. The command uses the
old name with `-n`, runs **only** `test_set_base64name`, and rewrites the identity to the Base64-encoded MAC.

```bash
uv run icotest --log info run --test-group rename -n Minion03
```

The rename step logs the same high-visibility warning box as the standard initial setup and produces a JSON report, so you retain an audit trail for the recovery.
After it succeeds, use the newly assigned Base64 name (e.g., `BYUgAHwA`) in the production test group:

```bash
uv run icotest --log info run --test-group production -n BYUgAHwA
```

Use this flow whenever you need to recover a reflashed board whose EEPROM still contains its old name.

---

## 3. Step 2: Hardware Verification (Production Test)

After the initial setup is complete, you must verify the physical quality of the device.

### Command
Rerun the test using the **new name** you just wrote on the PCB:

```bash
icotest run -n BYUgAHwA --test-group production
```

### Expected Output
This command will perform several hardware checks, including:
- **Supply Voltage**: Checks if the battery/supply is within range.
- **Power Usage**: Verifies power consumption is within limits (connected, disconnected, and streaming).
- **Sensor Quality**: Performs a high-resolution noise test on the acceleration sensor.

If the tests pass, you will see a success message:

```text
====================== 8 passed in 45.12s ======================
```

---

## 4. Troubleshooting

### Device Not Found
If you get a `TimeoutError` like this:
```text
E  TimeoutError: Unable to find sensor node with name “Minion04” in 20 seconds
E  Found the following sensor nodes:
E  🤖 Name: Pelzm_04, Number: 0, MAC Address: 14-2D-41-AE-CA-A1, RSSI: -58
```
It means the device is currently named `Pelzm_04` instead of `Minion04`. Rerun the command with the correct name:
```bash
icotest run -n Pelzm_04 --test-group initial
```

### Power Usage Failure
If the power usage test fails:
```text
E  AssertionError: Power usage of 65.0 mW greater than expected maximum of 60.0 mW
```
Check for common assembly issues:
- Short circuits on the PCB.
- Faulty components (e.g., LDO).
- Poor soldering quality.

---

## 5. Traceability and Audit Trail

Every run automatically generates audit files in the `reports/` folder:
- **JSON Report**: `reports/ICOtronic_BYUgAHwA_[TIMESTAMP].json` (Full measurement data and raw waveforms).
- **Log File**: `reports/icotest_[TIMESTAMP]_pytest.log` (Full technical audit trail of the session).

These files should be kept as part of the production record for the device.
