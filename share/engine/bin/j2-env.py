#!/usr/bin/python3
# Convenience wrapper around j2.

import mkwww.j2
import mkwww.j2.filters

import njinja
import json
import sys

def main(*args):
  (context, args) = mkwww.j2.read_context(list(args))
  infile = args.pop(0)
  ctxfile = args.pop(0)
  outfile = args.pop(0)
  depfile = args.pop(0)
  with open(ctxfile) as fp:
    ctx = json.load(fp)
  for k, v in context.items():
    ctx[k] = v
  if "navPath" in ctx and "sitenav" in ctx:
    ctx["nav"] = lambda *args: mkwww.j2.nav(ctx["sitenav"], ctx["navPath"], *args)

  j2env = mkwww.j2.default_env(fmt2main_args=[ctxfile, infile])
  njinja.run_j2(infile, ctx, outfile, depfile=depfile, j2env=j2env)

if __name__ == "__main__":
  sys.exit(main(*sys.argv[1:]))
