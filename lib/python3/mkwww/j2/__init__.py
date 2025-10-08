from . import filters
from jinja2 import ext, nodes, loaders, Environment
try:
  from jinja2.utils.markupsafe import Markup
except ImportError:
  from markupsafe import Markup

import inspect
import json
import re
import os

envvar = re.compile(r"^(\w+)=(.*)")
def read_context(args):
  context = {}
  while True:
    m = envvar.match(args[0])
    if m:
      if m.group(2).startswith("json:"):
        with open(m.group(2)[5:]) as fp:
          val = json.load(fp)
      else:
        val = m.group(2)
      context[m.group(1)] = val
      args.pop(0)
    else:
      break
  return (context, args)

# https://stackoverflow.com/a/64392515
class IncludeRawExtension(ext.Extension):
  tags = {"include_raw"}

  def parse(self, parser):
    lineno = parser.stream.expect("name:include_raw").lineno
    template = parser.parse_expression()
    result = self.call_method("_render", [template], lineno=lineno)
    return nodes.Output([result], lineno=lineno)

  def _render(self, filename):
    # TODO: tweak after https://github.com/pallets/jinja/pull/1776
    self.environment._parsed_names.append(filename)
    return Markup(self.environment.loader.get_source(self.environment, filename)[0])

def _startPath(cwd, path="", rel=True):
  sep = os.path.sep
  if type(path) == str:
    if path.startswith(sep):
      startPath = path
    else:
      startPath = sep + sep.join(cwd + [path]) if rel else path
  elif type(path) == list:
    if path and path[0] == sep:
      startPath = sep.join(path)
    else:
      startPath = sep + sep.join(cwd + path if rel else path)
  startPath = os.path.normpath(startPath).split(sep)[1:]
  return [] if startPath == [""] else startPath

def nav(sitenav, cwd, path="", rel=True):
  pagenav = sitenav
  navPath = _startPath(cwd, path, rel)
  while navPath:
    head = navPath.pop(0)
    pagenav = pagenav["subpages"][head]
  return pagenav

def default_env(fmt2main_args=[]):
  j2env = Environment(
    extensions = [
      'jinja2.ext.i18n',
      'jinja2.ext.do',
      'jinja2.ext.loopcontrols',
      IncludeRawExtension,
    ],
  )
  j2env.filters |= {
    name: func
    for name, func in inspect.getmembers(filters)
    if inspect.isfunction(func)
  }
  j2env.filters |= {
    name: func
    for name, func in inspect.getmembers(filters.DynamicFilters(fmt2main_args))
    if not name.startswith("_") and inspect.ismethod(func)
  }
  return j2env

def main():
  import itertools
  results = {
    (('a', 'b'), '', True): ['a', 'b'],
    (('a', 'b'), '.', True): ['a', 'b'],
    (('a', 'b'), '..', True): ['a'],
    (('a', 'b'), (), True): ['a', 'b'],
    (('a', 'b'), ('.',), True): ['a', 'b'],
    (('a', 'b'), ('..',), True): ['a'],
  }
  errors = False
  for s, p, r in itertools.product(
      ([], ["a", "b"]),
      ("", "/", ".", "..", [], ["/"], ["."], [".."]),
      (False, True)
    ):
    res = _startPath(s, p, r)
    k = tuple([tuple(s), (tuple(p) if type(p) == list else p), r])
    if res != results.get(k, []):
      print(k, res)
      errors = True
  return 1 if errors else 0

if __name__ == "__main__":
  sys.exit(main())