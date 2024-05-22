#!/usr/bin/python3
# Generate metadata about a page.

from jinja2 import nodes
import mkwww.j2

import collections
import json
import os
import os.path
import subprocess
import sys

bin_base = os.getenv("MKWWW_BIN", ".")

def runlines(*args, **kwargs):
  output = subprocess.check_output(*args, **kwargs)
  return list(output.decode("utf-8").splitlines())

def runfirstline(*args, **kwargs):
  p = subprocess.Popen(*args, stdout=subprocess.PIPE, **kwargs)
  for i in p.stdout.readlines():
    if i.rstrip(b"\n"):
      p.terminate()
      return i.decode("utf-8").rstrip("\n")

GIT_LOG_NONMINOR = ["git", "log", "--invert-grep", "--grep=^\[minor\]"]

FORMAT_GROUPS = {
  "j2": "mkwww-j2",
  "md": "docutils",
  "rst": "docutils",
  "adoc": "asciidoctor",
}

ENGINE_STYLES = {
  "*0": ["reset-colors"],
  "mkwww-j2": ["mkwww-j2-" + f for f in ["extend"]],
  "docutils": ["docutils-" + f for f in ["minimal", "math", "extend", "dtlist"]],
  "asciidoctor": ["asciidoctor-" + f for f in ["default", "reset"]],
  "*1": [],
}

ENGINE_SCRIPTS = {
  "*0": ["prep"],
  "mkwww-j2": [],
  "docutils": ["docutils-" + f for f in ["dtlist"]],
  "asciidoctor": [],
  "*1": [],
}

def guess_main_format(subject):
  (main, ext) = os.path.splitext(subject)
  fmts = [f for f in FORMAT_GROUPS.keys() if f != "j2"]
  if not ext:
    return None
  ext = ext[1:]
  if ext == "j2":
    (main, ext2) = os.path.splitext(main)
    if ext2 and ext2[1:] in fmts:
      return ext2[1:]
    else:
      return ext
  elif ext in fmts:
    return ext
  return None

def j2_meta(subject):
  # we must extract the metadata before rendering the template (for final
  # distribution), because we need the title for sitenav.json, which is in turn
  # needed for rendering the template (for final distribution).
  j2env = mkwww.j2.default_env()
  with open(subject) as fp:
    template = j2env.parse(fp.read())
  title = None
  for n in template.find_all(nodes.Assign):
    if isinstance(n.target, nodes.Name) and n.target.name == "title":
      title = n.node.as_const()
      break
  formats = [n.name.removesuffix("2main")
    for n in template.find_all(nodes.Filter)
    if n.node is None and n.name.endswith("2main")]
  return title, ["j2"] + sorted(set(formats))

def main(eng_def, thm_def, subject, *args):
  # git-shortlog for some reason doesn't work when run in parallel
  authors = list(runlines(GIT_LOG_NONMINOR + ["--format=%an <%ae>", subject]))
  authors = [a[0] for a in collections.Counter(authors).most_common()]

  dates = list(runlines(GIT_LOG_NONMINOR + ["--format=%at", subject]))
  if not authors or not dates:
    print("mkwww: mk-pageinf: no git info for %s; continuing but there may be errors or missing data in output" % subject, file=sys.stderr)

  rel_subject = os.path.relpath(subject, os.getenv("SRC"))
  rel_subject = os.path.normpath(rel_subject)
  nav_path = os.path.splitext(os.path.splitext(rel_subject)[0])[0]
  nav_path = nav_path.split(os.sep)
  if nav_path[0] == "":
    nav_path = nav_path[1:]
  if nav_path[-1] == "index":
    nav_path = nav_path[:-1]

  # TODO(--): maybe extract titles "properly" via their respective tools
  title = None
  formats = None
  UT = "<%s>" % os.path.basename(os.path.splitext(rel_subject)[0].removesuffix("/index"))
  fmt = guess_main_format(subject)
  if fmt == "j2":
    title, formats = j2_meta(subject)
  elif fmt == "md":
    title = runfirstline(["sed", "-rne", r"s/^# ?(.*)/\1/gp;T;q", subject]) or UT
    formats = ["md"]
  elif fmt == "rst":
    title = runfirstline(["sed", "-rne", r's/^(=+)$/&/;t y;h;b;:y x;p', subject]) or UT
    formats = ["rst"]
  elif fmt == "adoc":
    title = runfirstline(["sed", "-rne", r"s/^= ?(.*)/\1/gp;T;q", subject]) or UT
    formats = ["adoc"]
  else:
    print("don't know how to extract metadata from:", subject, file=sys.stderr)
    return 1
  engineGroups = ["*0"] + sorted(set(FORMAT_GROUPS[f] for f in formats)) + ["*1"]

  out = {}

  with open(eng_def) as fp:
    out |= json.load(fp)

  with open(thm_def) as fp:
    out |= json.load(fp)

  out |= {
    "authors": authors,
    "createdTs": dates[-1] if dates else 0,
    "modifiedTs": dates[0] if dates else 0,
    "baseRel": os.path.relpath(".", os.path.dirname(rel_subject)),
    "navPath": nav_path,
    "title": title,
    "engine_styles": [s for g in engineGroups for s in ENGINE_STYLES[g]],
    "engine_scripts": [s for g in engineGroups for s in ENGINE_SCRIPTS[g]],
  }

  # load override if it exists
  override = "%s.json" % subject
  if os.path.exists(override):
    with open(override) as fp:
      out |= json.load(fp)

  out.pop("_comment", None)
  out.pop("_", None)

  json.dump(out, sys.stdout, indent=2, ensure_ascii=False)
  print("")

if __name__ == "__main__":
  sys.exit(main(*sys.argv[1:]))
