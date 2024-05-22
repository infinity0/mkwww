#!/usr/bin/python3
# Generate navtree metadata from the metadata of all pages.

import json
import os.path
import sys

def sortnav(srcdir, node):
  subpages = list(node["subpages"].items())
  for elem in subpages:
    if "title" not in elem[1]:
      path = "/".join([srcdir] + node["navPath"] + [elem[0]])
      print("ERROR: please create an empty page for path '%s' in either %s.$fmt or %s/index.$fmt" % (elem[0], path, path), file=sys.stderr)
      raise ValueError("see error message above")
  subpages.sort(key=lambda elem: elem[1]["navSortKey"] or elem[0],
                reverse=node["navSortChildrenRev"])
  # python 3.6 onwards maintains dictionary insert order
  node["subpages"] = dict(subpages)
  for child in node["subpages"].values():
    sortnav(srcdir, child)

def main(*args):
  srcdir = os.getenv("SRC")
  prefix = os.getenv("GEN")
  target = os.getenv("DST")
  suffix = ".json"
  treedata = []
  for arg in args:
    (info, dst) = arg.split("=", 1)
    info = os.path.relpath(info, prefix)
    dst = os.path.relpath(dst, target)
    if not info.endswith(suffix):
      print("ERROR: cannot add to navtree: %s" % info, file=sys.stderr)
      return 1
    with open(os.path.join(prefix, info)) as fp:
      meta = json.load(fp)
    treedata.append((meta, dst))

  tree = { "subpages": {} }
  for (meta, dst) in treedata:
    cur = tree
    path = meta["navPath"][:]
    while path:
      ch = path.pop(0)
      if ch not in cur["subpages"]:
        cur["subpages"][ch] = { "subpages": {} }
      cur = cur["subpages"][ch]
    if "navPath" in cur:
      print("ERROR: duplicate item", file=sys.stderr)
      return 1
    cur["href"] = dst
    cur |= meta

  sortnav(srcdir, tree)
  json.dump(tree, sys.stdout)
  print()

if __name__ == "__main__":
  sys.exit(main(*sys.argv[1:]))
