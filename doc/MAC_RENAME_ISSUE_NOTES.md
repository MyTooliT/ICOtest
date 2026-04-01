# MAC Rename Issue Notes

## Problem

The rename-only test group used `sensor_node.get_mac_address()` to derive the new
Base64 device name. On some boards this returned a different MAC than the one
advertised during Bluetooth scanning.

## Observation

For `Minion03` we saw:

- scan result: `14-2D-41-D7-77-6F`
- `get_mac_address()`: `05:85:20:00:7c:00`

Because the rename step Base64-encodes the value returned by the MAC lookup,
the board was renamed to the wrong value.

## Conclusion

The Bluetooth scan result is the reliable source for the device MAC in the
rename flow. The direct `get_mac_address()` call is not trustworthy for this
board path.

## Fix Plan

- Use `collect_sensor_nodes()` in `icotest/test/conftest.py`.
- Match the scanned node by the current Bluetooth name passed with `-n`.
- Use the scanned `mac_address` for rename metadata and report naming.

## Related Filename Issue

Some Base64 MAC values include `/`, which is not safe in report filenames.
The report renaming logic now sanitizes both the device name and the Base64 MAC
before moving the JSON report into `reports/`.

## Operator Impact

Recovery rename flow:

```bash
uv run icotest --log info run --test-group rename -n Minion03
```

After the rename succeeds, the device should be used under the new Base64 name
derived from the scan result.
