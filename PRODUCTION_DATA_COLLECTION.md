# Production Data Collection & Traceability

This document describes the production data collection system implemented in **ICOtest**. This system is designed to provide full traceability for hardware during the assembly and production phases of the ICOtronic system.

## 1. Overview and Purpose

The primary goal of this data collection framework is to ensure that every device leaving production has a digital "birth certificate." By recording specific physical measurements, power consumption levels, and sensor noise profiles, we can:

1.  **Trace Issues Back**: If a device fails in the field, we can look up its production report to see if there were early indicators of failure (e.g., high power draw or marginal SNR).
2.  **Monitor Quality Trends**: Aggregate data from multiple production runs to identify drifts in component quality or assembly processes.
3.  **Automate Quality Gates**: Ensure that every device strictly adheres to specified hardware limits before being marked as "ready for shipment."

---

## 2. Hardware Traceability

Every production run is uniquely linked to the physical hardware under test.

### Automatic Identification
The framework automatically retrieves the device's **MAC address** and **Node Name** during the test session. These identifiers are:
*   Injected into the global metadata of the report.
*   Used to dynamically name the output file.

### Report Naming Convention
Reports are stored in the `reports/` directory with the following format:
`reports/[DEVICE_TYPE]_[BASE64_MAC]_[TIMESTAMP].json`

**Example**: `reports/STH_CGvXAd6B_2026-03-10_15-30.json`
*(Note: Base64 encoding is used for the MAC address to ensure filenames are URL-friendly and concise.)*

---

## 3. Data Collection Details

Unlike standard test frameworks that only report "Pass/Fail," ICOtest captures the underlying raw data.

### Standardized Measurements
All critical physical values (Voltage, Power, Bias, SNR) are recorded in a structured format:
*   **Value**: The actual measured quantity.
*   **Unit**: The unit of measurement (V, mW, g, dB).
*   **Limits**: The upper and lower bounds used for the pass/fail decision.
*   **Description**: A human-readable label for the measurement.

### Full Time-Series Recordings
For sensor tests (Noise and 3-Axis), the **entire raw data stream** is captured.
*   **Capacity**: Typically 10,000 samples per channel (X, Y, Z).
*   **Utility**: Allows post-production analysis such as FFTs, spectral density checks, or vibration analysis without needing to re-run the physical hardware.

### Diagnostic Failure Analysis
Each test includes a `failure_analysis` field. If a test fails, this field provides production staff with immediate technical context (e.g., "High power draw often indicates a short circuit or faulty LDO").

---

## 4. Usage in Production

### Running the Tests
To run a standard production test suite, use the `--test-group` flag:

```bash
icotest run --test-group production
```

This command automatically:
1.  Filters the test suite to include power and sensor tests.
2.  **Auto-enables** the JSON reporting plugin.
3.  Configures the report to be saved in the `reports/` directory.

### Reviewing the Results
The resulting JSON files can be:
*   **Read manually**: They are structured and human-readable.
*   **Ingested into a database**: The consistent schema allows for easy integration with production monitoring dashboards or ELK stacks.

---

## 5. Developer Guide: Recording New Data

To record a new measurement in a test, use the `json_metadata` fixture and its helper function `record`:

```python
async def test_my_new_hardware_feature(sensor_node, json_metadata):
    value = await sensor_node.get_some_value()
    
    # Capture the measurement with its context
    json_metadata["record"](
        "my_feature_name",
        value,
        unit="units",
        lower=0.5,
        upper=1.5,
        description="Detailed description of what this measures"
    )
    
    # Standard assertion follows
    assert 0.5 <= value <= 1.5
```

For large data sets, you can directly assign to the metadata dictionary:
```python
json_metadata["raw_samples"] = list(my_raw_data_array)
```
