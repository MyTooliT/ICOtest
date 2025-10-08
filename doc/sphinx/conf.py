"""Sphinx configuration"""

# pylint: disable=invalid-name

# -- Imports ------------------------------------------------------------------

from pathlib import Path
from datetime import datetime

from sphinx_pyproject import SphinxConfig

# -- Project information ------------------------------------------------------

config = SphinxConfig(
    Path(__file__).parent.parent.parent / "pyproject.toml", globalns=globals()
)
# pylint: disable=redefined-builtin, undefined-variable
copyright = (
    f"{datetime.now().year}, {author}"  # noqa: F821
)  # type: ignore[name-defined]
# pylint: enable=redefined-builtin
project = name  # noqa: F821 # type: ignore[name-defined]
# pylint: enable=undefined-variable

# -- General configuration ----------------------------------------------------

# Run doctest from doctest directive, but not nested tests from autodoc code
doctest_test_doctest_blocks = ""

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- HTML Theme ---------------------------------------------------------------

html_theme = "sphinx_rtd_theme"

# pylint: enable=invalid-name
