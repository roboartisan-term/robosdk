# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.

import os
import subprocess
import sys

from recommonmark.parser import CommonMarkParser

try:
    import autoapi
except ModuleNotFoundError:
    subprocess.check_call([sys.executable, "-m", "pip",
                           "install", "sphinx-autoapi"])


_base_path = os.path.abspath("../..")

sys.path.insert(0, _base_path)


os.environ["APIDOC_GEN"] = os.environ.get("APIDOC_GEN", "True")
# -- Project information -----------------------------------------------------

project = "robosdk"
copyright = '2021, Kubeedge'
author = 'Kubeedge'

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named "sphinx.ext.*") or your custom
# ones.

extensions = [
    "recommonmark",
    "sphinx.ext.autodoc",
    "sphinx.ext.coverage",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx_markdown_tables",
    "sphinx_copybutton",
    "sphinx.ext.autosectionlabel",
]

napoleon_google_docstring = True
napoleon_use_param = False
napoleon_use_ivar = True

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
if os.environ["APIDOC_GEN"] == "True":
    exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
else:
    exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "apidoc"]

autoapi_type = "python"
autoapi_dirs = [f"{_base_path}/robosdk", f"{_base_path}/examples"]
autoapi_options = [
    'members', 'undoc-members', 'show-inheritance',
    'show-module-summary', 'special-members', 'imported-members'
]

subprocess.check_call([
    "sphinx-apidoc", "-o", "apidoc", os.path.join(_base_path, "robosdk")
])
autodoc_inherit_docstrings = False
autodoc_member_order = "bysource"
# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = True

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'


# -- Options for HTML output -------------------------------------------------
# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
# html_theme = "alabaster"
html_theme = "sphinx_book_theme"

html_theme_options = {
    "repository_url": "https://github.com/kubeedge/robosdk",
    "use_repository_button": True,
    "use_issues_button": True,
    "use_edit_page_button": True,
    "path_to_docs": "doc/source",
    "home_page_in_toc": True,
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
# html_static_path = ["_static"]
html_title = "latest"
html_logo = "_static/logo.png"
htmlhelp_basename = "RoboSDKDoc"

source_parsers = {
    ".md": CommonMarkParser,
}

source_suffix = [".md", ".rst"]
