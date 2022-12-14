from mkwww.rst.base import *


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

