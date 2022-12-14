"""
Filters for our j2 templates.
"""

from datetime import datetime
import os
import subprocess

bin_base = os.getenv("MKWWW_BIN", ".")

def fmt2main(fmt, x, *args):
  prog = os.path.join(bin_base, "%s2main" % fmt)
  output = subprocess.check_output([prog] + [str(a) for a in args], input=x.encode("utf-8"))
  return output.decode("utf-8")

def md2main(x, id_prefix=""):
  # TODO: affected by https://github.com/executablebooks/MyST-Parser/issues/644
  # user has to avoid it for now, we don't have a workaround
  return fmt2main("md", x, id_prefix)

def rst2main(x, id_prefix="", initial_header_level=1):
  return fmt2main("rst", x, id_prefix, initial_header_level)

def adoc2main(x, id_prefix=""):
  return fmt2main("adoc", x, id_prefix)

def ts_date(ts):
  return datetime.utcfromtimestamp(int(ts)).strftime('%Y-%m-%d')

def ts_time(ts):
  return datetime.utcfromtimestamp(int(ts)).strftime('%H:%M:%S')
