#!/usr/bin/env python3
"""Update notebook with device-centric data loader"""

import json

# New data loader code
data_loader_code = '''# Define data loading classes for device-centric analysis

class TestDataLoader:
    """Load and normalize test reports into device-centric tables"""
    
    def __init__(self, reports_dir='../reports'):
        self.reports_dir = Path(reports_dir)
        self.reports_df = None
        self.tests_df = None
        self.measurements_df = None
        self.series_store = {}
        self.report_files = []
    
    def find_reports(self):
        """Find all JSON report files"""
        hardware_test_files = glob.glob(str(self.reports_dir / 'hardware_test_*.json'))
        icotronic_files = glob.glob(str(self.reports_dir / 'ICOtronic_*.json'))
        renamed_files = glob.glob(str(self.reports_dir / '*_*_*_*.json'))
        
        all_files = sorted(set(hardware_test_files + icotronic_files + renamed_files))
        self.report_files = [f for f in all_files if not f.endswith('.log')]
        return len(self.report_files)
    
    def load_all_reports(self):
        """Load all reports and create normalized tables"""
        reports = []
        tests = []
        measurements = []
        
        for report_file in self.report_files:
            try:
                with open(report_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                filename = Path(report_file).stem
                report_info = self._parse_report(filename, data)
                reports.append(report_info)
                
                for test in data.get('tests', []):
                    test_info, test_measurements, series_data = self._parse_test(
                        test, report_info['report_id'], report_info['device_id'], 
                        report_info['created_dt']
                    )
                    tests.append(test_info)
                    measurements.extend(test_measurements)
                    
                    if series_data:
                        key = (report_info['device_id'], report_info['report_id'], test_info['test_name'])
                        self.series_store[key] = series_data
                        
            except Exception as e:
                print(f"Error loading {filename}: {e}")
        
        self.reports_df = pd.DataFrame(reports)
        self.tests_df = pd.DataFrame(tests)
        self.measurements_df = pd.DataFrame(measurements) if measurements else pd.DataFrame()
        
        return len(reports), len(tests), len(measurements)
    
    def _parse_report(self, filename, data):
        """Extract report-level information"""
        timestamp = data.get('created')
        timestamp_dt = datetime.fromtimestamp(timestamp) if timestamp else None
        
        run_id = filename
        device_id = self._extract_device_id(filename, data)
        
        return {
            'report_id': run_id,
            'device_id': device_id,
            'created': timestamp,
            'created_dt': timestamp_dt,
            'duration': data.get('duration'),
            'exitcode': data.get('exitcode'),
            'total_tests': data.get('summary', {}).get('total', 0),
            'passed_tests': data.get('summary', {}).get('passed', 0),
            'failed_tests': data.get('summary', {}).get('failed', 0),
            'is_legacy': device_id is None or device_id == filename
        }
    
    def _extract_device_id(self, filename, data):
        """Extract device_id from filename or test metadata"""
        parts = filename.split('_')
        
        if len(parts) >= 2:
            prefix = parts[0]
            if prefix in ['hardware', 'ICOtronic']:
                return None
            return prefix
        
        for test in data.get('tests', []):
            meta = test.get('metadata', {})
            if 'sensor_mac_base64' in meta:
                return meta['sensor_mac_base64']
        
        return None
    
    def _parse_test(self, test, report_id, device_id, created_dt):
        """Parse individual test and its measurements"""
        nodeid = test.get('nodeid', '')
        test_name = nodeid.split('::')[-1] if '::' in nodeid else nodeid
        
        duration = None
        if test.get('call') and isinstance(test['call'], dict):
            duration = test['call'].get('duration')
        
        test_info = {
            'report_id': report_id,
            'device_id': device_id,
            'test_name': test_name,
            'nodeid': nodeid,
            'outcome': test.get('outcome', 'unknown'),
            'duration_s': duration,
            'created_dt': created_dt
        }
        
        test_measurements = []
        series_data = {}
        
        metadata = test.get('metadata', {})
        if metadata:
            for key, value in metadata.items():
                if key == 'sensor_mac_base64':
                    test_info['device_id'] = value
                    continue
                
                if isinstance(value, list) and len(value) > 10:
                    series_data[key] = np.array(value)
                    continue
                
                if isinstance(value, dict) and 'value' in value:
                    measurement = {
                        'report_id': report_id,
                        'device_id': device_id,
                        'test_name': test_name,
                        'metric': key,
                        'value': value.get('value'),
                        'unit': value.get('unit', ''),
                        'lower_limit': value.get('lower_limit'),
                        'upper_limit': value.get('upper_limit'),
                        'description': value.get('description', '')
                    }
                    test_measurements.append(measurement)
                
                elif isinstance(value, str):
                    test_info[f'{key}_text'] = value
        
        return test_info, test_measurements, series_data
    
    def get_device_summary(self):
        """Get device-level summary statistics"""
        if self.reports_df is None:
            return None
        
        summary = self.reports_df.groupby('device_id').agg(
            num_runs=('report_id', 'count'),
            total_tests=('total_tests', 'sum'),
            total_passed=('passed_tests', 'sum'),
            total_failed=('failed_tests', 'sum'),
            date_range=('created_dt', lambda x: f"{x.min().date()} to {x.max().date()}")
        ).reset_index()
        
        summary['pass_rate'] = (summary['total_passed'] / summary['total_tests'] * 100).round(1)
        
        return summary
    
    def get_test_history(self, device_id):
        """Get all tests for a specific device"""
        return self.tests_df[self.tests_df['device_id'] == device_id].sort_values('created_dt')
    
    def get_measurements(self, device_id=None, test_name=None):
        """Get measurements with optional filtering"""
        df = self.measurements_df
        
        if device_id:
            df = df[df['device_id'] == device_id]
        if test_name:
            df = df[df['test_name'] == test_name]
        
        return df
    
    def get_series(self, device_id, report_id, test_name):
        """Get time series data for a specific test"""
        key = (device_id, report_id, test_name)
        return self.series_store.get(key, {})

print("TestDataLoader class defined")'''

# Load notebook
with open("notebooks/test_analysis.ipynb", "r", encoding="utf-8") as f:
    nb = json.load(f)

# Find and replace the TestReportAnalyzer cell
for i, cell in enumerate(nb["cells"]):
    if cell["cell_type"] == "code":
        source = "".join(cell.get("source", []))
        if "class TestReportAnalyzer" in source:
            nb["cells"][i]["source"] = [data_loader_code]
            print(f"Replaced cell {i}")
            break

# Save
with open("notebooks/test_analysis.ipynb", "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1)

print("Done!")
