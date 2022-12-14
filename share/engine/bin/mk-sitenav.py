#!/usr/bin/python3
# Generate navtree metadata from the metadata of all pages.

import json
import os.path
import sys

def sortnav(node):
  children = list(node["children"].items())
  children.sort(key=lambda elem: elem[1]["navSortKey"] or elem[0],
                reverse=node["navSortChildrenRev"])
  # python 3.6 onwards maintains dictionary insert order
  node["children"] = dict(children)
  for child in node["children"].values():
    sortnav(child)

def main(prefix, overrides, *args):
  suffix = ".json"
  treedata = []
  for arg in args:
    (info, dst) = arg.split("=", 1)
    if not info.endswith(suffix):
      print("cannot add to navtree: %s" % info, file=sys.stderr)
      return 1
    with open(os.path.join(prefix, info)) as fp:
      meta = json.load(fp)
    treedata.append((meta, dst))

  tree = { "children": {} }
  for (meta, dst) in treedata:
    cur = tree
    path = meta["navPath"][:]
    while path:
      ch = path.pop(0)
      if ch not in cur["children"]:
        cur["children"][ch] = { "children": {} }
      cur = cur["children"][ch]
    if "navPath" in cur:
      print("duplicate item", file=sys.stderr)
      return 1
    cur["href"] = dst
    cur |= meta

  sortnav(tree)
  json.dump(tree, sys.stdout)
  print()

if __name__ == "__main__":
  sys.exit(main(*sys.argv[1:]))
