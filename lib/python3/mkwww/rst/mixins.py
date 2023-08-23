from mkwww.rst.base import *
from docutils.nodes import SparseNodeVisitor

import re
from urllib.parse import urlparse


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
class PermalinkSectionHTML(object):
  def add_permalink_ref(self, node, title, toc_backref) -> None:
    if node['ids']:
      format = '<a class="anchor" href="#%s" title="%s"></a>'
      link = format % (node['ids'][0], title)
      if toc_backref:
        self.body[-1] = self.body[-1].replace("><a ", ">%s<a " % link)
      else:
        self.body[-1] += link

  def visit_title(self, node) -> None:
    super().visit_title(node)
    close_tag = self.context[-1]
    if (node.parent.hasattr('ids') and node.parent['ids']):
      # add permalink anchor
      if close_tag.startswith('</a></h'): # toc-backref
        self.add_permalink_ref(node.parent, 'Permalink to this section', True)
      elif close_tag.startswith('</h'):
        self.add_permalink_ref(node.parent, 'Permalink to this section', False)


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
NO_DETAILS_LIST = "no-dtlist"

def is_details_list(node):
  return node and DETAILS_LIST in node['classes']

class DetailsListVisitor(SparseNodeVisitor):
  def __init__(self, document, add):
    super().__init__(document)
    self.add = add

  def visit_bullet_list(self, node) -> None:
    if self.add:
      if DETAILS_LIST not in node['classes']:
        node['classes'].append(DETAILS_LIST)
      if NO_DETAILS_LIST in node['classes']:
        node['classes'].remove(NO_DETAILS_LIST)
    else:
      if DETAILS_LIST in node['classes']:
        node['classes'].remove(DETAILS_LIST)
      if NO_DETAILS_LIST not in node['classes']:
        node['classes'].append(NO_DETAILS_LIST)

class DetailsListTransform(NextElementTransform):
    default_priority = 210
    def transform_function(self, node, params):
      rec = params["rec"]
      if rec is None:
        DetailsListVisitor(self.document, True).visit_bullet_list(node)
      elif rec == "rec":
        node.walkabout(DetailsListVisitor(self.document, True))
      elif rec == "rec-no":
        node.walkabout(DetailsListVisitor(self.document, False))

class DetailsList(NextElementDirective):
    optional_arguments = 1
    has_content = True
    pending_class = DetailsListTransform
    def get_params(self):
      return {
        "rec": directives.choice(self.arguments[0], ("rec", "rec-no")) if len(self.arguments) else None
      }
directives.register_directive("dtlist", DetailsList)


class DetailsListHTML(ReplaceLastTagMixin):

  def visit_bullet_list(self, node) -> None:
    super().visit_bullet_list(node)
    if is_details_list(node):
      self._replace_last_tag("<ul", "<div")

  def depart_bullet_list(self, node):
    super().depart_bullet_list(node)
    if is_details_list(node):
      self._replace_last_tag("</ul", "</div")

  def visit_list_item(self, node):
    super().visit_list_item(node)
    if is_details_list(node.parent):
      self._replace_last_tag("<li", "<details")

  def depart_list_item(self, node):
    super().depart_list_item(node)
    if is_details_list(node.parent):
      self._replace_last_tag("</li", "</details")

  def visit_paragraph(self, node):
    super().visit_paragraph(node)
    if node.parent and is_details_list(node.parent.parent) and node.parent.index(node) == 0:
      self._replace_last_tag("<p", "<summary")

  def depart_paragraph(self, node):
    super().depart_paragraph(node)
    if node.parent and is_details_list(node.parent.parent) and node.parent.index(node) == 0:
      self._replace_last_tag("</p", "<span class=\"dtlist-tooltip\"></span></summary")
