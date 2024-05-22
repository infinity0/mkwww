from mkwww.rst.base import *
from docutils.nodes import SparseNodeVisitor
from docutils.transforms.references import PropagateTargets
from docutils.transforms.misc import ClassAttribute

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


class PermalinkSectionHTML(PermalinkSectionMixin):
  def visit_title(self, node) -> None:
    super().visit_title(node)
    # work around annoying bug in docutils 0.21
    if isinstance(node.parent, nodes.topic):
      if (self.settings.toc_backlinks
          and 'contents' in node.parent['classes']):
        self._replace_last_tag(' href="#top">', '>')

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

class PropagateClassesListFixer(SparseNodeVisitor):

  def visit_pending(self, node):
    super().visit_pending(node)
    # TODO: the way we exclude simple here is a bit of a hack. What about other stuff?
    if node.transform is ClassAttribute and "simple" not in node.details["class"]:
      target = node.next_node(ascend=True)
      parent = node.parent
      if isinstance(target, (nodes.bullet_list, nodes.enumerated_list)):
        parent.remove(node)
        target.insert(0, node)

class PropagateClassesListFix(Transform):
  default_priority = ClassAttribute.default_priority - 1

  def apply(self):
    self.document.walkabout(PropagateClassesListFixer(self.document))


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
