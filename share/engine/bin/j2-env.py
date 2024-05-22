#!/usr/bin/python3
# Convenience wrapper around j2.

import mkwww.j2
import mkwww.j2.filters

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

  j2env = mkwww.j2.default_env(ctxfile, infile)
  result = j2env.get_template(infile).render(ctx)
  with open(outfile, 'w') as fp:
    fp.write(result)

  deps = j2env.extract_parsed_names()
  assert deps[0] == infile
  with open(depfile, 'w') as fp:
    print("%s: %s" % (outfile, " ".join(deps)), file=fp)

if __name__ == "__main__":
  sys.exit(main(*sys.argv[1:]))
