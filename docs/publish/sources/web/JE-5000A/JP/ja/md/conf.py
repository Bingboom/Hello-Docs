# Minimal Sphinx conf for a pdf-web-sideload staging bundle.
# Content here is not executed by the real pipeline (readthedocs_source.py
# excludes conf.py when copying and writes its own at assembly time); this
# file only needs to exist so discover_manual_sources() recognizes this
# directory as a staged md/ bundle, and to make a standalone verification
# build possible while drafting.
extensions = ["myst_parser"]
source_suffix = {".md": "markdown"}
root_doc = "index"
master_doc = "index"
