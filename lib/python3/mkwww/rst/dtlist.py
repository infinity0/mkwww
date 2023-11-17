from mkwww.text import *
from mkwww.rst.base import *
from docutils.nodes import SparseNodeVisitor, fully_normalize_name as normalize_name
from docutils.transforms.references import DanglingReferences

import re


DETAILS_LIST = "dtlist"

def is_dtlist(node):
  return node and isinstance(node, nodes.bullet_list) and DETAILS_LIST in node['classes']
  # TODO: this is disabled for now until we figure out how to do the UI correctly
  # need to display the toggle switch but also the number bullet point
  #return node and isinstance(node, (nodes.bullet_list, nodes.enumerated_list)) and DETAILS_LIST in node['classes']

def is_dtlist_item(node):
  return node and isinstance(node, nodes.list_item) and is_dtlist(node.parent)

def is_dtlist_summary(node):
  return node and is_dtlist_item(node.parent) and node.parent.index(node) == 0

def dtlist_extract_name(node):
  """Generate a short title from the summary text.

  Split the text on a double-space. Use the first part if there's only 2 parts,
  otherwise use the second part if there's more than 2.
  """
  if is_dtlist_summary(node):
    name = []
    for text in node.findall(nodes.Text, False, True):
      (text2, n) = re.subn(r"(?<![\w\\])=(.+?)(?<!\\)=(?!\w)", lambda x: (name.append(x.group(1)), name[0])[1], text)
      if n:
        text.parent.replace(text, nodes.Text(text2))
        break
    name = name[0] if len(name) else node.astext()
    return name.rstrip(HALF_BREAK + FULL_BREAK)
  return None

DTLIST_FLAGHOW = {
  "self": None,
  "sub": False,
  "rec": True,
}
DTLIST_FLAGWHAT = {
  "yes": True,
  "no": False,
  "inherit": None,
}
DTLIST_FLAGALL = \
  list(DTLIST_FLAGHOW.keys()) + \
  list(DTLIST_FLAGWHAT.keys()) + \
  ["%s-%s" % (x, y) for x in DTLIST_FLAGHOW.keys() for y in DTLIST_FLAGWHAT.keys()]

class DetailsListVisitor(SparseNodeVisitor):
  def __init__(self, document, params):
    super().__init__(document)
    self.params = params

  def apply_class(self, node, val, cls) -> None:
    if val is None:
      pass
    elif val is True and cls not in node['classes']:
      node['classes'].append(cls)
    elif val is False and cls in node['classes']:
      node['classes'].remove(cls)

  def apply_open(self, node, val) -> None:
    if val is None:
      pass
    elif val is True and "open" not in node:
      node['open'] = "open"
    elif val is False and "open" in node:
      del node['open']

  def visit_bullet_list(self, node) -> None:
    if "add" in self.params:
      self.apply_class(node, DTLIST_FLAGWHAT[self.params["add"]], DETAILS_LIST)
    if "simple" in self.params:
      self.apply_class(node, DTLIST_FLAGWHAT[self.params["simple"]], "simple")

  def visit_enumerated_list(self, node) -> None:
    if "add" in self.params:
      self.apply_class(node, DTLIST_FLAGWHAT[self.params["add"]], DETAILS_LIST)
    if "simple" in self.params:
      self.apply_class(node, DTLIST_FLAGWHAT[self.params["simple"]], "simple")

  def visit_list_item(self, node) -> None:
    if is_dtlist_item(node):
      if "open" in self.params:
        self.apply_open(node, DTLIST_FLAGWHAT[self.params["open"]])
      # fix up empty list items so they don't cause errors and look awful
      if len(node.children) == 0:
        node.append(nodes.paragraph())

def dtlist_flag(arg):
  if not arg:
    return ("self", "yes")
  a = arg.split("-", 1)
  if len(a) < 2:
    if a[0] in DTLIST_FLAGHOW:
      return (a[0], "yes")
    if a[0] in DTLIST_FLAGWHAT:
      return ("self", a[0])
  else:
    (x, y) = a
    if x in DTLIST_FLAGHOW and y in DTLIST_FLAGWHAT:
      return (x, y)
  raise ValueError("unknown flag value: %s" % arg)

class DetailsListTransform(NextElementTransform):
  default_priority = 210

  def transform_function(self, node, params):
    for p in ["add", "simple", "open"]:
      if p not in params:
        continue
      (how, what) = dtlist_flag(params[p])
      visitor = DetailsListVisitor(self.document, {p: what})
      if how == "self":
        visitor.visit_bullet_list(node)
        for c in node.children:
          visitor.visit_list_item(c)
      elif how == "sub":
        for c in node.children:
          c.walkabout(visitor)
      else:
        assert how == "rec"
        node.walkabout(visitor)

class DtList(NextElementDirective):
  """Main ..dtlist directive.

  Automatically registered as a directive, you don't need to do anything beyond
  importing this module to enable it.
  """
  optional_arguments = 1
  has_content = True
  pending_class = DetailsListTransform
  option_spec = {
    "simple": lambda x: directives.choice(x, DTLIST_FLAGALL) if x else x,
    "open": lambda x: directives.choice(x, DTLIST_FLAGALL) if x else x,
  }

  def get_params(self):
    return {
      "add": directives.choice(self.arguments[0], DTLIST_FLAGALL) if len(self.arguments) else None,
    } | self.options
directives.register_directive("dtlist", DtList)


_old_dtlist_item_astext = nodes.list_item.astext
def dtlist_item_astext(self):
  if is_dtlist_item(self) and "open" not in self:
    return self.children[0].astext() if len(self.children) else ""
  else:
    return _old_dtlist_item_astext(self)

class DetailsListIdsVisitor(SparseNodeVisitor):
  def visit_paragraph(self, node):
    if is_dtlist_summary(node):
      details_node = node.parent

      # generate id. this must be done first.
      if details_node['ids']:
        # item was already given a manual id
        pass
      else:
        name = normalize_name(dtlist_extract_name(node))
        if name: # skip empty items
          details_node['names'].append(name)
          self.document.note_implicit_target(details_node, details_node)

      # generate child control button and tooltip
      other_children = [n for n in details_node.children[1:] if not is_invisible(n, self.document.reporter)]
      # word count excluding hidden sub-children; we monkey-patch astext() to make this work
      nodes.list_item.astext = dtlist_item_astext
      wc1 = sum(approx_words(n.astext()) for n in other_children)
      nodes.list_item.astext = _old_dtlist_item_astext
      # word count including hidden sub-children
      wc2 = sum(approx_words(n.astext()) for n in other_children)
      if wc1 > 0 or wc2 > 0:
        node.append(nodes.Text(" "))
        if wc1 == wc2:
          text = rough_approx(wc1)
        else:
          text = "%s|%s" % (rough_approx(wc1), rough_approx(wc2))
        node.append(nodes.inline("", text, classes=["dtlist-ctl"]))

class DetailsListIdsTransform(Transform):
  """Automatically generate names and IDs for details-list items.

  Top-level transform not associated with any element.

  You need to pass this to the Reader, e.g. by subclassing
  docutils.readers.standalone.Reader and passing it to publish_parts.
  """
  default_priority = DanglingReferences.default_priority - 1

  def apply(self):
    self.document.walkabout(DetailsListIdsVisitor(self.document))

class DetailsListOpenTransform(Transform):
  default_priority = DetailsListTransform.default_priority + 10

  def apply(self):
    pending = self.startnode
    if is_dtlist_summary(pending.parent):
      pending.parent.parent["open"] = "open"
      pending.parent.remove(pending)
      return
    error = self.document.reporter.error(
        'No suitable element for :dtopen: role',
        nodes.literal_block(pending.rawsource, pending.rawsource),
        line=pending.line)
    pending.replace_self(error)

def dtopen(name, rawtext, text, lineno, inliner, options=None, content=None):
  """:dtopen: role function.

  Set a details list item as open by default.

  Automatically registered as a local rule.
  """
  pending = nodes.pending(
      DetailsListOpenTransform,
      {"refname": text},
      rawtext)
  inliner.document.note_pending(pending)
  return [pending], []
roles.register_local_role("dtopen", dtopen)


class DetailsListHTML(ReplaceLastTagMixin, PermalinkSectionMixin):

  def visit_bullet_list(self, node) -> None:
    super().visit_bullet_list(node)
    if is_dtlist(node):
      self._replace_last_tag("<ul", "<div")

  def depart_bullet_list(self, node):
    super().depart_bullet_list(node)
    if is_dtlist(node):
      self._replace_last_tag("</ul", "</div")

  def visit_enumerated_list(self, node) -> None:
    super().visit_enumerated_list(node)
    if is_dtlist(node):
      self._replace_last_tag("<ol", "<div")

  def depart_enumerated_list(self, node):
    super().depart_enumerated_list(node)
    if is_dtlist(node):
      self._replace_last_tag("</ol", "</div")

  def visit_list_item(self, node):
    super().visit_list_item(node)
    if is_dtlist_item(node):
      if "open" in node:
        self._replace_last_tag("<li", "<details open")
      else:
        self._replace_last_tag("<li", "<details")

  def depart_list_item(self, node):
    super().depart_list_item(node)
    if is_dtlist_item(node):
      self._replace_last_tag("</li", "</details")

  def visit_paragraph(self, node):
    super().visit_paragraph(node)
    if is_dtlist_summary(node):
      self.add_permalink_ref(node.parent, 'Link to this item')
      self._replace_last_tag("<p", "<summary role=\"heading\"")

  def depart_paragraph(self, node):
    super().depart_paragraph(node)
    if is_dtlist_summary(node):
      self._replace_last_tag("</p", "</summary")
