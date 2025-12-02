# -- Settings ------------------------------------------------------------------

# Use latest version of PowerShell on Windows
set windows-shell := ["pwsh.exe", "-NoLogo", "-Command"]

# -- Variables -----------------------------------------------------------------

package := "icotest"

sphinx_directory := "sphinx"
sphinx_input_directory := "doc/sphinx"

# -- Recipes -------------------------------------------------------------------

# Setup Python environment
[group('setup')]
setup:
	uv venv --allow-existing
	uv sync --all-extras

# Check code
[group('lint')]
check: setup
	uv run flake8
	uv run mypy {{package}}
	uv run pylint .

# Test code
[group('test')]
[default]
test: check
	uv run pytest -k 'not firmware_upload' --reruns 5 --reruns-delay 1

# Build documentation
[group('documentation')]
documentation:
	uv run sphinx-build -M html {{sphinx_input_directory}} {{sphinx_directory}}
