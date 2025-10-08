"""
Filters for our j2 templates.
"""

from datetime import datetime
import os
import subprocess
import tempfile

bin_base = os.getenv("MKWWW_BIN", ".")

def ts_date(ts):
  return datetime.utcfromtimestamp(int(ts)).strftime('%Y-%m-%d')

def ts_time(ts):
  return datetime.utcfromtimestamp(int(ts)).strftime('%H:%M:%S')

# filters that depend on the environment
class DynamicFilters(object):

  def __init__(self, fmt2main_args=[]):
    # can be empty, then filters will throw an error - which doesn't matter if filters aren't used
    self.fmt2main_args = fmt2main_args
    self.toc_out = []

  def _fmt2main(self, fmt, x, *opts):
    if len(self.fmt2main_args) != 2:
      raise ValueError("fmt2main expects 2 args in fmt2main_args")
    prog = os.path.join(bin_base, "%s2main" % fmt)
    with tempfile.NamedTemporaryFile(mode='w+') as tocfile:
      output = subprocess.check_output(
        [prog] + self.fmt2main_args + [tocfile.name] + [str(o) for o in opts],
        input=x.encode("utf-8"))
      tocfile.seek(0)
      self.toc_out.append(tocfile.read())
    return output.decode("utf-8")

  def md2main(self, x, id_prefix=""):
    # TODO: affected by https://github.com/executablebooks/MyST-Parser/issues/644
    # user has to avoid it for now, we don't have a workaround
    return self._fmt2main("md", x)

  def rst2main(self, x, id_prefix="", initial_header_level=1):
    return self._fmt2main("rst", x, id_prefix, initial_header_level)

  def adoc2main(self, x, id_prefix=""):
    return self._fmt2main("adoc", x, id_prefix)

  def fmt2main_toc(self, _):
    """Extract the tables-of-contents that have been generated so far by fmt2main.

    Must be called *after* all the other fmt2main calls."""
    return "".join(self.toc_out)
