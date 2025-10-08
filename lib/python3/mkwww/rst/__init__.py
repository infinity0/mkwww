from mkwww.rst.extensions import AutoContentsTransform, PropagateTargetsListFix, PropagateClassesListFix, AbbrHTML, PermalinkSectionHTML, ExtlinkHTML
from mkwww.rst.tables import MoreColsRowsPostTransform, TableGroupsHTML
from mkwww.rst.dtlist import DetailsListIdsTransform, DetailsListHTML

from docutils.readers.standalone import Reader as _Reader
from docutils.writers.html5_polyglot import Writer as _Writer, HTMLTranslator as _HTMLTranslator


class HTMLTranslator(AbbrHTML, PermalinkSectionHTML, ExtlinkHTML, DetailsListHTML, TableGroupsHTML, _HTMLTranslator):
  pass

class Reader(_Reader):
  def get_transforms(self):
    return super().get_transforms() + [
      AutoContentsTransform,
      PropagateClassesListFix,
      PropagateTargetsListFix,
      MoreColsRowsPostTransform,
      DetailsListIdsTransform,
    ]

class Writer(_Writer):
  def __init__(self):
    super().__init__()
    self.translator_class = HTMLTranslator
