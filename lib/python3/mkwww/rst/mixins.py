from mkwww.rst.base import *
from docutils.nodes import SparseNodeVisitor, fully_normalize_name as normalize_name
from docutils.transforms.references import PropagateTargets, DanglingReferences

import re
from urllib.parse import urlparse


# :abbr: implementation copied from sphinx
abbr_re = re.compile(r'\((.*)\)$', re.S)
def abbr(name, rawtext, text, lineno, inliner, options=None, content=None):
  options = options or {}
  matched = abbr_re.search(text)
  if matched:
    text = text[:matched.start()].strip()
    options['title'] = matched.group(1)
  else:
    text = self.text

  return [nodes.abbreviation(rawtext, text, **options)], []
roles.register_local_role("abbr", abbr)

class AbbrHTML(object):
  def visit_abbreviation(self, node):
    attrs = {}
    if node.hasattr('title'):
      attrs['title'] = node['title']
    self.body.append(self.starttag(node, 'abbr', '', **attrs))


class ReplaceLastTagMixin(object):
  def _replace_last_tag(self, fr, to):
    for i in (1,2,3):
      if len(self.body) >= i and self.body[-i].strip():
        self.body[-i] = self.body[-i].replace(fr, to)
        return


# code for section heading anchors ("permalinks")
# lifted and adapted slightly from sphinx.writers.html5.HTML5Translator
# main differences are to match asciidoc:
# - anchor is generated before the heading, instead of after
# - anchor class name is "anchor", instead of "headerlink"
class PermalinkSectionMixin(object):
  def add_permalink_ref(self, node, title, toc_backref=False) -> None:
    if node['ids']:
      cancel = '<a class="anchor-cancel" href="#" title="Cancel anchor target"></a>'
      link = '%s<a class="anchor" href="#%s" title="%s"></a>' % (cancel, node['ids'][0], self.attval(title))
      if toc_backref:
        self.body[-1] = self.body[-1].replace("><a ", ">%s<a " % link)
      else:
        self.body[-1] += link

class PermalinkSectionHTML(PermalinkSectionMixin):
  def visit_title(self, node) -> None:
    super().visit_title(node)
    close_tag = self.context[-1]
    if (node.parent.hasattr('ids') and node.parent['ids']):
      # add permalink anchor
      if close_tag.startswith('</a></h'): # toc-backref
        self.add_permalink_ref(node.parent, 'Link to this section', True)
      elif close_tag.startswith('</h'):
        self.add_permalink_ref(node.parent, 'Link to this section', False)


class PropagateTargetsListFixer(SparseNodeVisitor):
  """
  rST can't give manual names to the first list item::

      .. _name-1:

    - item 1

      .. _name-2:

    - item 2

  results in _name-1 being given to the overall list, not item 1, even though
  _name-2 is correctly given to item 2.

  We work around this here, at the cost of being no longer able to give manual
  names to the overall list. (No it doesn't work even if you unindent _name-1.)

  See https://stackoverflow.com/questions/50138672/how-to-add-anchor-in-list-element for details
  """
  # code copied from PropagateTargets.apply
  def transplant_id(self, target, next_node):
    next_node['ids'].extend(target['ids'])
    next_node['names'].extend(target['names'])
    # Set defaults for next_node.expect_referenced_by_name/id.
    if not hasattr(next_node, 'expect_referenced_by_name'):
        next_node.expect_referenced_by_name = {}
    if not hasattr(next_node, 'expect_referenced_by_id'):
        next_node.expect_referenced_by_id = {}
    for id in target['ids']:
        # Update IDs to node mapping.
        self.document.ids[id] = next_node
        # If next_node is referenced by id ``id``, this
        # target shall be marked as referenced.
        next_node.expect_referenced_by_id[id] = target
    for name in target['names']:
        next_node.expect_referenced_by_name[name] = target
    # If there are any expect_referenced_by_... attributes
    # in target set, copy them to next_node.
    next_node.expect_referenced_by_name.update(
        getattr(target, 'expect_referenced_by_name', {}))
    next_node.expect_referenced_by_id.update(
        getattr(target, 'expect_referenced_by_id', {}))
    # Set refid to point to the first former ID of target
    # which is now an ID of next_node.
    target['refid'] = target['ids'][0]
    # Clear ids and names; they have been moved to
    # next_node.
    target['ids'] = []
    target['names'] = []
    self.document.note_refid(target)

  def visit_list_item(self, node):
    if node.parent.index(node) == 0 and not node['ids'] and node.parent['ids']:
      self.transplant_id(node.parent, node)

class PropagateTargetsListFix(Transform):
  default_priority = PropagateTargets.default_priority + 1

  def apply(self):
    self.document.walkabout(PropagateTargetsListFixer(self.document))


# code copied from sphinx.utils.docutils.ReferenceRole to avoid dependency
explicit_title_re = re.compile(r'^(.+?)\s*(?<!\x00)<(.*?)>$', re.DOTALL)
def parse_linktext(text):
  matched = explicit_title_re.match(text)
  if matched:
    has_explicit_title = True
    title = nodes.unescape(matched.group(1))
    target = nodes.unescape(matched.group(2))
  else:
    has_explicit_title = False
    title = nodes.unescape(text)
    target = nodes.unescape(text)

  return has_explicit_title, title, target

class ExtlinkHTML(ReplaceLastTagMixin):
  def visit_reference(self, node):
    super().visit_reference(node)
    if "target" in node:
      self._replace_last_tag("<a", "<a target=\"%s\"" % self.attval(node["target"]))

def ext(name, rawtext, text, lineno, inliner, options=None, content=None):
  """:ext: role function.

  Indicate an external link. Can nest markup inside the text, unlike the
  default set of rST roles.

  Automatically registered as a local rule.
  """
  (h, text, target) = parse_linktext(text)
  if h and text == "_":
    text = urlparse(target).netloc.removeprefix("www.")

  # https://stackoverflow.com/questions/44829580/composing-roles-in-restructuredtext/68865718#68865718
  label = nodes.reference(rawtext, refuri=target, classes=["extlink-label"], target="_blank")
  out, messages = inliner.parse(text, lineno, inliner, label)
  label += out
  # icon text is empty in the html; the actual icon is added in CSS
  # non-empty icon text can screw with auto-id-name logic
  icon = nodes.reference('', '', refuri=target, classes=["extlink-icon"], target="_blank")
  # two <a> so it's easier to style them separately
  return [label, icon], messages
roles.register_local_role("ext", ext)


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

# TODO: make this work for all languages
# https://stackoverflow.com/questions/9506869/are-there-character-collections-for-all-international-full-stop-punctuations
HALF_BREAK = ",;:-"
FULL_BREAK = ".?!"
FULL_BREAK_STD = "."

def ensure_full_stop(text):
  # convert half-stop punctuation into full-stop punctuation
  if any(text.endswith(c) for c in HALF_BREAK):
    text = text[:-1].rstrip()
  if not text.endswith(FULL_BREAK_STD):
    text = text + FULL_BREAK_STD
  return text

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


class DetailsListIdsVisitor(SparseNodeVisitor):
  def visit_paragraph(self, node):
    if is_dtlist_summary(node):
      details_node = node.parent
      if details_node['ids']:
        # item was already given a manual id
        return
      name = normalize_name(dtlist_extract_name(node))
      if name: # skip empty items
        details_node['names'].append(name)
        self.document.note_implicit_target(details_node, details_node)

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
      self._replace_last_tag("</p", "<span class=\"dtlist-tooltip\"></span></summary")
