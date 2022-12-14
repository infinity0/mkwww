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

GIT_LOG_NONMINOR = ["git", "log", "--invert-grep", "--grep=^\[minor\]"]

FORMAT_GROUPS = {
  "j2": "mkwww-j2",
  "md": "docutils",
  "rst": "docutils",
  "adoc": "asciidoctor",
}

ENGINE_STYLES = {
  "*0": [],
  "mkwww-j2": ["mkwww-j2-" + f for f in ["extend"]],
  "docutils": ["docutils-" + f for f in ["minimal", "math", "extend"]],
  "asciidoctor": ["asciidoctor-" + f for f in ["default", "reset"]],
  "*1": [],
}

ENGINE_SCRIPTS = {
  "*0": [],
  "mkwww-j2": [],
  "docutils": [],
  "asciidoctor": [],
  "*1": [],
}

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

def main(eng_def, thm_def, subject, rel_subject):
  # git-shortlog for some reason doesn't work when run in parallel
  authors = runlines(GIT_LOG_NONMINOR + ["--format=%an <%ae>", subject])
  authors = [a[0] for a in collections.Counter(authors).most_common()]

  dates = runlines(GIT_LOG_NONMINOR + ["--format=%at", subject])
  if not authors or not dates:
    print("no git info for %s; continuing but there may be errors in output" % subject, file=sys.stderr)

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
  if subject.endswith(".j2"):
    title, formats = j2_meta(subject)
  elif subject.endswith(".md"):
    title = runlines(["sed", "-rne", r"s/^# (.*)/\1/gp;T;q", subject])[0]
    formats = ["md"]
  elif subject.endswith(".rst"):
    title = runlines(["sed", "-rne", r'/^=+$/,/^=+$/p', subject])[1]
    formats = ["rst"]
  elif subject.endswith(".adoc"):
    title = runlines(["sed", "-rne", r"s/^= (.*)/\1/gp;T;q", subject])[0]
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
