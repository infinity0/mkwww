from . import filters
from jinja2 import ext, nodes, loaders, Markup, Environment

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

# TODO: drop after https://github.com/pallets/jinja/pull/1776
class DependencyRecordedEnvironment(Environment):
  def __init__(self, *args, remember_parsed_names=False, **kwargs):
    super().__init__(*args, **kwargs)
    self._parsed_names = [] if remember_parsed_names else None

  def _parse(self, source, name, filename):
    if name is not None and self._parsed_names is not None:
        self._parsed_names.append(name)
    return super()._parse(source, name, filename)

  def extract_parsed_names(self):
    if self._parsed_names is None:
        return None
    names = self._parsed_names[:]
    self._parsed_names.clear()
    return names

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

def readfile(n):
  with open(n) as fp:
    return fp.read()

def path_exists(f):
  return os.path.exists(f)

def path_join(base, *path):
  return os.path.join(base, *path)

def default_env():
  j2env = DependencyRecordedEnvironment(
    loader = loaders.FunctionLoader(readfile),
    remember_parsed_names = True,
    keep_trailing_newline = True,
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
  j2env.globals |= {
    "path_exists": path_exists,
    "path_join": path_join,
  }
  return j2env
