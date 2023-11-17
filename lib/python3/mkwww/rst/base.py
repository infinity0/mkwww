from docutils.parsers.rst import directives, Directive, roles
from docutils.transforms import Transform
from docutils import nodes


def find_ancestor_element(node, pred):
  parent = node.parent
  child = node
  while parent:
    if pred(parent):
      return parent
    child = parent
    parent = parent.parent
  return None

def is_invisible(node, reporter):
  return isinstance(node, nodes.Invisible) or isinstance(node, nodes.system_message) and node['level'] < reporter.report_level

# copied mostly from docutils.transforms.ClassAttribute
# TODO: upstream to docutils
class NextElementTransform(Transform):
    def transform_function(self, node, params):
      raise NotImplementedError()

    def apply(self):
        pending = self.startnode
        parent = pending.parent
        child = pending
        while parent:
            # Check for appropriate following siblings:
            for index in range(parent.index(child) + 1, len(parent)):
                element = parent[index]
                if (isinstance(element, nodes.Invisible)
                    or isinstance(element, nodes.system_message)):
                    continue
                self.transform_function(element, pending.details);
                pending.parent.remove(pending)
                return
            else:
                # At end of section or container; apply to sibling
                child = parent
                parent = parent.parent
        error = self.document.reporter.error(
            'No suitable element following "%s" directive'
            % pending.details['directive'],
            nodes.literal_block(pending.rawsource, pending.rawsource),
            line=pending.line)
        pending.replace_self(error)

# copied mostly from docutils.parsers.rst.directives.Class
# TODO: upstream to docutils
class NextElementDirective(Directive):
    pending_class = None

    def get_params(self):
      raise NotImplementedError()

    def run(self):
        params = self.get_params()
        node_list = []
        pending = nodes.pending(
            self.pending_class,
            {'directive': self.name, **params},
            self.block_text)
        # do all processing via pending transforms, so that transforms that might
        # need to recurse into their children are run top-down in a consistent order
        self.state_machine.document.note_pending(pending)
        node_list.append(pending)
        if self.content:
            container = nodes.Element()
            self.state.nested_parse(self.content, self.content_offset,
                                    container)
            node_list.extend(container.children)
        return node_list

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
