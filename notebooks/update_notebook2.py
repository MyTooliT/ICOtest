#!/usr/bin/env python3
"""Update notebook loading section and add device summary"""

import json

# New loading section code
loading_code = """# Initialize data loader and load all reports
loader = TestDataLoader()

num_files = loader.find_reports()
num_reports, num_tests, num_measurements = loader.load_all_reports()

print(f"Found {num_files} report files")
print(f"Loaded {num_reports} reports, {num_tests} tests, {num_measurements} measurements")

# Create short aliases for convenience
reports_df = loader.reports_df
tests_df = loader.tests_df
measurements_df = loader.measurements_df

# Get device summary
device_summary = loader.get_device_summary()
print(f"\\nUnique devices: {len(device_summary) if device_summary is not None else 0}")
if device_summary is not None:
    display(device_summary)"""

# New device summary section
device_summary_code = """# Device Summary - Device-centric view
print("=" * 80)
print("DEVICE SUMMARY")
print("=" * 80)

device_summary = loader.get_device_summary()

if device_summary is not None and len(device_summary) > 0:
    print(f"\\nTotal unique devices: {len(device_summary)}")
    print(f"Total test runs: {device_summary['num_runs'].sum()}")
    print(f"Overall pass rate: {device_summary['pass_rate'].mean():.1f}%")
    print("\\nDevice Details:")
    display(device_summary)
else:
    print("No device data available")

print("\\n" + "=" * 80)
print("REPORTS OVERVIEW")
print("=" * 80)
print(f"\\nTotal reports: {len(reports_df)}")
print(f"Date range: {reports_df['created_dt'].min()} to {reports_df['created_dt'].max()}")
print(f"\\nReports by device:")
display(reports_df.groupby('device_id').agg(
    runs=('report_id', 'count'),
    first_run=('created_dt', 'min'),
    last_run=('created_dt', 'max')
).reset_index())"""

# Load notebook
with open("notebooks/test_analysis.ipynb", "r", encoding="utf-8") as f:
    nb = json.load(f)

# Find and replace the loading cell (cell 5)
for i, cell in enumerate(nb["cells"]):
    if cell["cell_type"] == "code":
        source = "".join(cell.get("source", []))
        if "analyzer = TestReportAnalyzer()" in source:
            nb["cells"][i]["source"] = [loading_code]
            print(f"Replaced cell {i} (loading)")
            break

# Find and replace the data inspection cell (cell 7)
for i, cell in enumerate(nb["cells"]):
    if cell["cell_type"] == "code":
        source = "".join(cell.get("source", []))
        if 'print("=" * 80)' in source and "DATA SUMMARY" in source:
            nb["cells"][i]["source"] = [device_summary_code]
            print(f"Replaced cell {i} (device summary)")
            break

# Save
with open("notebooks/test_analysis.ipynb", "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1)

print("Done!")
