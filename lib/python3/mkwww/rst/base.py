from docutils.parsers.rst import directives, Directive
from docutils.transforms import Transform
from docutils import nodes

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
