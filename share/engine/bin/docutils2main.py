#!/usr/bin/python3

from docutils.core import publish_parts
from docutils.io import FileInput
from docutils.writers.html5_polyglot import Writer as _Writer, HTMLTranslator as _HTMLTranslator
from mkwww.rst.mixins import PermalinkSectionHTML, DetailsListHTML

import json
import os
import os.path
import subprocess
import sys

bin_base = os.getenv("MKWWW_BIN", ".")

class HTMLTranslator(PermalinkSectionHTML, DetailsListHTML, _HTMLTranslator):
  pass

class Writer(_Writer):
  def __init__(self):
    super().__init__()
    self.translator_class = HTMLTranslator

def main(progname, ctxfile, id_prefix="", initial_header_level=1):
  parser_name = os.path.split(progname)[1].removesuffix("2main.py").removesuffix("2main")
  if parser_name == "md":
    parser_name = "myst"
  initial_header_level = int(initial_header_level)
  has_pandoc = 0 == subprocess.call(["which", "pandoc"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
  # TODO: drop after https://sourceforge.net/p/docutils/patches/197/
  if has_pandoc:
    os.environ["PATH"] = "%s:%s" % (bin_base, os.environ["PATH"])

  with open(ctxfile) as fp:
    ctx = json.load(fp)
  parts = publish_parts(
    parser_name=parser_name,
    writer=Writer(),
    source_class=FileInput,
    source=sys.stdin,
    settings_overrides=ctx.get("settings_override",{}) | {
      "embed_stylesheet": False,

      # set idprefix from parameter
      # by default, make this "_" to be slightly more consistent with asciidoc
      # also makes non-XML section headings like numbers and dates ("2022-02-22")
      # generate a nicer section name
      "id_prefix": id_prefix + "_",
      # mathml works in chrome (in >> 110, behind a flag), firefox, opera
      # this is good enough for us, we can avoid messing with mathjax.
      # TODO: switch latexml to pandoc after https://sourceforge.net/p/docutils/patches/197/
      "math_output": "mathml latexml" if has_pandoc else "mathml",

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

      # automatically enable extensions that are included in GFM, but also
      # leave MyST features enabled such as roles and directives. the user can
      # further override this on a per-document basis, for details see
      # https://myst-parser.readthedocs.io/en/latest/configuration.html#local-configuration
      "myst_enable_extensions": [
        "linkify",
        "strikethrough",
        "tasklist",
      ],
      "suppress_warnings": ["myst.header"],
      # TODO: remove this after https://github.com/executablebooks/MyST-Parser/issues/641
      "myst_all_links_external": True,
    })
  # TODO: bug with docutils; remove after https://sourceforge.net/p/docutils/patches/197/
  if os.path.exists("./latexmlpost.log"):
    os.unlink("./latexmlpost.log")
  main = parts['html_body'].replace("<main", '<div class="main-docutils"', 1).replace("</main>", "</div>", 1)
  sys.stdout.write(main.rstrip())
  sys.stdout.write("\n")
  sys.stdout.flush()

if __name__ == "__main__":
  sys.exit(main(*sys.argv))
