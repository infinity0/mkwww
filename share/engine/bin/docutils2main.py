#!/usr/bin/python3
"""Parse a rST/markdown fragment into a main-like HTML fragment.

Usage: $0 <context-filepath> <input-filepath> [<id-prefix>] < <input-filehandle>

context-filepath
  JSON context/config dictionary. Keys we use:

  settings_override
    Initial parameter to ``docutils.core.publish_parts()``. We also add our own
    overrides on top of this; RTFS for details.

input-filepath
  Path to the input source file. This is used for metadata purposes ONLY.
  The actual file is not read directly; instead we expect either the whole
  file or a portion of it to be passed via stdin. This allows us to support
  (e.g.) *.j2 templates that call us selectively for portions of itself.

id_prefix
  Passed directly to docutils.
"""

from docutils.core import publish_parts
from docutils.io import FileInput
from mkwww.rst import HTMLTranslator, Reader, Writer

import json
import os
import os.path
import subprocess
import sys

bin_base = os.getenv("MKWWW_BIN", ".")

def main(progname, ctxfile, infile, id_prefix="", initial_header_level=1):
  parser_name = os.path.split(progname)[1].removesuffix("2main.py").removesuffix("2main")
  if parser_name == "md":
    parser_name = "myst"
  initial_header_level = int(initial_header_level)
  has_pandoc = 0 == subprocess.call(["which", "pandoc"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

  with open(ctxfile) as fp:
    ctx = json.load(fp)

  parts = publish_parts(
    parser_name=parser_name,
    reader=Reader(),
    writer=Writer(),
    source_class=FileInput,
    source_path=infile,
    source=sys.stdin,
    settings_overrides=ctx.get("settings_override",{}) | {
      "embed_stylesheet": False,
      #"report_level": 1, # e.g. to show "duplicate implicit target name"

      # set idprefix from parameter
      # also makes non-XML section headings like numbers and dates ("2022-02-22")
      # generate a nicer section name
      "id_prefix": id_prefix + "_" if id_prefix else "",
      # mathml works in chrome (in >> 110, behind a flag), firefox, opera
      # this is good enough for us, we can avoid messing with mathjax.
      "math_output": "mathml pandoc" if has_pandoc else "mathml",

      # rst "autodetects" section heading levels, but this runs into issues
      # when e.g. mixing multiple formats using our *2main jinja filters
      # because an rst snippet in the middle of a document doesn't know which
      # level it's at. here we allow the user to supply this info explicitly.
      #
      # we have to do the dance with max(2, initial_header_level) because docutils'
      # HTML5 writer starts counting at 2 for <h2> and uses doctitle_xform to
      # control whether a <h1> title is emitted.
      "initial_header_level": max(2, initial_header_level),
      "doctitle_xform": initial_header_level <= 1,

      # - enable extensions that are included in GFM
      # - enable extensions that add formatting features present in rST
      # - leave MyST features enabled such as roles and directives
      # the user can further override this per-document; for details see
      # https://myst-parser.readthedocs.io/en/latest/configuration.html#local-configuration
      "myst_enable_extensions": [
        "attrs_block",
        "deflist",
        "fieldlist",
        "linkify",
        "strikethrough",
        "tasklist",
      ],
      "suppress_warnings": ["myst.header"],
      # TODO: remove this after https://github.com/executablebooks/MyST-Parser/issues/641
      "myst_all_links_external": True,
    })
  main = parts['html_body'].replace("<main", '<div class="main-docutils"', 1).replace("</main>", "</div>", 1)
  sys.stdout.write(main.rstrip())
  sys.stdout.write("\n")
  sys.stdout.flush()

if __name__ == "__main__":
  sys.exit(main(*sys.argv))
