from mkwww.rst.base import *
from docutils.nodes import SparseNodeVisitor


class MoreColsRowsTransform(Transform):
  # https://docutils.sourceforge.io/docs/ref/transforms.html
  default_priority = 700

  def apply(self):
    pending = self.startnode
    if pending.parent and isinstance(pending.parent.parent, nodes.entry):
      cell = pending.parent.parent
      morecols = pending.details.get("morecols", 0)
      morerows = pending.details.get("morerows", 0)
      if morecols:
        cell["morecols"] = morecols
      if morerows:
        cell["morerows"] = morerows
      row = cell.parent
      coln = cell.parent.index(cell)
      rown = row.parent.index(row)
      # NOTE: cannot merge across thead/tbody boundary
      for r in row.parent.children[rown:rown+morerows+1]:
        for c in r.children[coln:coln+morecols+1]:
          if c is not cell:
            c["removeme"] = True
      pending.parent.remove(pending)
      return
    error = self.document.reporter.error(
        'No suitable element for :morecols: role',
        nodes.literal_block(pending.rawsource, pending.rawsource),
        line=pending.line)
    pending.replace_self(error)

class MoreColsRowsPostVisitor(SparseNodeVisitor):
  def visit_entry(self, node):
    if node.get("removeme", False):
      node.parent.remove(node)

class MoreColsRowsPostTransform(Transform):
  default_priority = MoreColsRowsTransform.default_priority + 1

  def apply(self):
    self.document.walkabout(MoreColsRowsPostVisitor(self.document))

def mergecell(name, rawtext, cols, rows, lineno, inliner, options=None, content=None):
  pending = nodes.pending(
      MoreColsRowsTransform,
      {"morecols": int(cols) if cols.strip() else 0, "morerows": int(rows) if rows.strip() else 0},
      rawtext)
  inliner.document.note_pending(pending)
  return [pending], []

def morecols(name, rawtext, text, lineno, inliner, options=None, content=None):
  """:morecols: role function.

  Syntax: :morecols:`cols` or :morecols:`cols,rows`.

  Merge a table cell into the next column(s) and/or row(s). Note: you cannot
  merge across a thead/tbody boundary, this doesn't work in HTML either.

  Automatically registered as a local rule.
  """
  if "," in text:
    cols, rows = text.split(",")
  else:
    cols, rows = text, "0"
  return mergecell(name, rawtext, cols, rows, lineno, inliner, options, content)

def morerows(name, rawtext, text, lineno, inliner, options=None, content=None):
  """:morerows: role function.

  Syntax: :morerows:`rows` or :morerows:`rows,cols`.

  Merge a table cell into the next row(s) and/or column(s). Note: you cannot
  merge across a thead/tbody boundary, this doesn't work in HTML either.

  Automatically registered as a local rule.
  """
  if "," in text:
    rows, cols = text.split(",")
  else:
    rows, cols = text, "0"
  return mergecell(name, rawtext, cols, rows, lineno, inliner, options, content)

roles.register_local_role("morecols", morecols)
roles.register_local_role("morerows", morerows)

def parse_tgroups(specstr):
  specs = []
  for rowspec in specstr.split(","):
    parts = rowspec.strip().split(".")
    (num, flags) = (parts[0]+":").split(":")[:2]
    (hnum, bnum) = ("0+"+num).rsplit("+")[-2:]
    hnum = -1 if hnum == "*" else int(hnum)
    bnum = -1 if bnum == "*" else int(bnum)
    classes = parts[1:]
    specs.append((hnum, bnum, flags, classes))
  return specs

class TableGroupsTransform(NextElementTransform):
  default_priority = 260

  def transform_function(self, node, params):
    if not isinstance(node, nodes.table):
      raise ValueError("table-groups: not a table: %s", node.shortrepr())

    tgroup = node.next_node(lambda x: isinstance(x, nodes.tgroup))
    colspec = []
    if "cols" in params:
      tgroup["colgroups"] = colspec = parse_tgroups(params["cols"])

    if "rows" in params:
      groups = []

      thead = tgroup.next_node(lambda x: isinstance(x, nodes.thead))
      if thead:
        tgroup.remove(thead)
        groups.append(thead)
      tbody = tgroup.next_node(lambda x: isinstance(x, nodes.tbody))
      tgroup.remove(tbody)

      for (hnum, bnum, flags, classes) in parse_tgroups(params["rows"]):
        hnum = len(tbody.children) if hnum < 0 else hnum
        bnum = len(tbody.children) - hnum if bnum < 0 else bnum
        if "H" in flags:
          if len(groups) > 0:
            raise ValueError("thead (H) must be first group")
          group = nodes.thead()
        elif "F" in flags:
          group = nodes.tbody()
          group["tagname"] = "tfoot"
          if bnum + hnum != len(tbody.children):
            raise ValueError("tfoot (F) must be last group")
        else:
          group = nodes.tbody()
        groups.append(group)

        group["classes"] = classes
        for i in range(hnum + bnum):
          row = tbody.pop(0)
          group.append(row)
          if i < hnum:
            for e in row:
              e["tagname"] = "th"
          i = 0
          for (chnum, cbnum, _, _) in colspec:
            for e in row.children[i:i+chnum]:
              e["tagname"] = "th"
            i += chnum + cbnum

      for g in groups:
        tgroup.append(g)

class TableGroups(NextElementDirective):
  """Main ..table-groups directive.

  Automatically registered as a directive, you don't need to do anything beyond
  importing this module to enable it.
  """
  optional_arguments = 0
  has_content = True
  pending_class = TableGroupsTransform
  option_spec = {
    "rows": directives.unchanged,
    "cols": directives.unchanged,
  }

  def get_params(self):
    return self.options
directives.register_directive("table-groups", TableGroups)

"""Unconditionally generate <colgroup> elements for user styling purposes.

TODO: this will be obsolete once browsers support CSS4 :nth-col().
"""
class TableGroupsHTML(object):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.colgroups = []

  def visit_tgroup(self, node):
    super().visit_tgroup(node)
    self.colgroups = node.get("colgroups", [])

  def depart_colspec(self, node):
    super().depart_colspec(node)
    # only activate on the last colspec node, as per logic in super()
    if isinstance(node.next_node(descend=False, siblings=True),
                  nodes.colspec):
      return
    # write colgroup if not already written
    if all("colgroup" not in self.body[-i] for i in (1,2,3)):
      c = 0
      for (hnum, bnum, _, classes) in self.colgroups:
        self.body.append(self.starttag(node, 'colgroup', classes=classes))
        for node in self.colspecs[c:c+hnum+bnum]:
            self.body.append(self.emptytag(node, 'col'))
        self.body.append('</colgroup>\n')
        c += hnum + bnum

  def visit_tbody(self, node):
    super().visit_tbody(node)
    if "tagname" in node:
      self._replace_last_tag("<tbody", "<%s" % node["tagname"])

  def depart_tbody(self, node):
    super().depart_tbody(node)
    if "tagname" in node:
      self._replace_last_tag("</tbody", "</%s" % node["tagname"])

  def visit_entry(self, node):
    super().visit_entry(node)
    if "tagname" in node:
      tgroup = node.parent.parent
      atts = ''
      if isinstance(tgroup, nodes.tbody) and "tagname" not in tgroup:
        atts = ' scope="row"'
      self._replace_last_tag("<td", "<%s%s" % (node["tagname"], atts))

  def depart_entry(self, node):
    super().depart_entry(node)
    if "tagname" in node:
      self._replace_last_tag("</td", "</%s" % node["tagname"])
