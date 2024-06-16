# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
import inspect
import os
import sys

sys.path.insert(0, os.path.abspath("_ext"))
sys.path.insert(0, os.path.abspath("../homeassistant"))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Home Assistant'
copyright = '2024, cyr-ius'
author = 'cyr-ius'
release = '0.1'


# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [ 
    'sphinx.ext.duration',
    'sphinx.ext.doctest',
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.githubpages',
    'sphinx.ext.viewcode',
]

templates_path = ['_templates']
exclude_patterns = []

# The master toctree document.
master_doc = "index"

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output
html_use_smartypants = True
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

texinfo_documents = [
    (
        master_doc,
        "Home-Assistant",
        "Home Assistant Documentation",
        author,
        "Home Assistant",
        "Open-source home automation platform.",
        "Miscellaneous",
    )
]

suppress_warnings = [
    "epub.duplicated_toc_entry",
]

python_display_short_literal_types = True
python_use_unqualified_type_names = True
