#!/usr/bin/env python3
"""Update filtering and add device drill-down"""

import json

# New filtering code
filtering_code = """# Interactive filtering by device
print("=" * 80)
print("FILTER DATA")
print("=" * 80)

# Get unique values
devices = sorted([d for d in reports_df['device_id'].unique() if d is not None])
tests = sorted(tests_df['test_name'].unique())
outcomes = sorted(tests_df['outcome'].unique())

# Date range
min_date = reports_df['created_dt'].min()
max_date = reports_df['created_dt'].max()

# Create widgets
device_selector = widgets.SelectMultiple(
    options=devices,
    value=(devices[0],) if devices else (),
    description='Devices:',
    rows=min(5, len(devices))
)

test_selector = widgets.SelectMultiple(
    options=tests,
    description='Tests:',
    rows=min(5, len(tests))
)

outcome_selector = widgets.SelectMultiple(
    options=outcomes,
    value=tuple(outcomes),
    description='Outcomes:',
    rows=min(3, len(outcomes))
)

min_date_widget = widgets.Text(
    value=min_date.strftime('%Y-%m-%d %H:%M') if min_date else '',
    description='From:',
    placeholder='YYYY-MM-DD HH:MM'
)

max_date_widget = widgets.Text(
    value=max_date.strftime('%Y-%m-%d %H:%M') if max_date else '',
    description='To:',
    placeholder='YYYY-MM-DD HH:MM'
)

print("\\n1. Select Devices:")
display(device_selector)
print("\\n2. Select Tests (leave empty for all):")
display(test_selector)
print("\\n3. Select Outcomes:")
display(outcome_selector)
print("\\n4. Date Range:")
display(widgets.VBox([min_date_widget, max_date_widget]))"""

# Filtering function
filter_func_code = '''# Apply filters and get filtered data
def get_filtered_data():
    """Apply all filters and return filtered DataFrame"""
    df = tests_df.copy()
    
    # Filter by device
    if device_selector.value:
        df = df[df['device_id'].isin(device_selector.value)]
    
    # Filter by test
    if test_selector.value:
        df = df[df['test_name'].isin(test_selector.value)]
    
    # Filter by outcome
    if outcome_selector.value:
        df = df[df['outcome'].isin(outcome_selector.value)]
    
    # Filter by date range
    try:
        start_date = datetime.strptime(min_date_widget.value, '%Y-%m-%d %H:%M') if min_date_widget.value else reports_df['created_dt'].min()
        end_date = datetime.strptime(max_date_widget.value, '%Y-%m-%d %H:%M') if max_date_widget.value else reports_df['created_dt'].max()
        
        df = df[(df['created_dt'] >= start_date) & (df['created_dt'] <= end_date)]
    except ValueError:
        print("Invalid date format. Using full range.")
    
    return df.sort_values('created_dt')

df_filtered = get_filtered_data()
print(f"\\nFiltered: {len(df_filtered)} test records")
display(df_filtered.head(10))'''

# Device drill-down code
device_drill_code = '''# Device Drill-Down
print("=" * 80)
print("DEVICE DRILL-DOWN")
print("=" * 80)

# Select a device to analyze
device_dropdown = widgets.Dropdown(
    options=devices,
    description='Device:'
)

display(device_dropdown)

def show_device_details(device_id):
    """Show all tests and measurements for a device"""
    device_tests = loader.get_test_history(device_id)
    device_reports = reports_df[reports_df['device_id'] == device_id]
    
    print(f"\\n{'='*60}")
    print(f"Device: {device_id}")
    print(f"{'='*60}")
    
    print(f"\\nReports: {len(device_reports)}")
    print(f"Tests: {len(device_tests)}")
    print(f"Pass rate: {(device_tests['outcome'] == 'passed').sum() / len(device_tests) * 100:.1f}%")
    
    print("\\nTest Results Over Time:")
    display(device_tests[['created_dt', 'test_name', 'outcome', 'duration_s']])
    
    # Show recent measurements if available
    device_measurements = loader.get_measurements(device_id=device_id)
    if len(device_measurements) > 0:
        print("\\nLatest Measurements:")
        latest = device_measurements.dropna(subset=['value']).sort_values('report_id').groupby('metric').last()
        display(latest[['value', 'unit']])

# Create interactive output
out = widgets.interactive_output(show_device_details, {'device_id': device_dropdown})
display(out)'''

# Load notebook
with open("notebooks/test_analysis.ipynb", "r", encoding="utf-8") as f:
    nb = json.load(f)

# Find and replace filtering cell (around cell 10)
replaced_count = 0
for i, cell in enumerate(nb["cells"]):
    if cell["cell_type"] == "code":
        source = "".join(cell.get("source", []))

        # Replace filtering setup
        if "# Create device, test, and outcome selectors" in source:
            nb["cells"][i]["source"] = [filtering_code]
            replaced_count += 1
            print(f"Replaced cell {i} (filtering setup)")

        # Replace filtering function
        elif "# Create filtered dataset based on selections" in source:
            nb["cells"][i]["source"] = [filter_func_code]
            replaced_count += 1
            print(f"Replaced cell {i} (filtering function)")

# Save
with open("notebooks/test_analysis.ipynb", "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1)

print(f"Done! Replaced {replaced_count} cells.")
