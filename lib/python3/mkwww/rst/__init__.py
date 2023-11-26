from mkwww.rst.extensions import PropagateTargetsListFix, PropagateClassesListFix, AbbrHTML, PermalinkSectionHTML, ExtlinkHTML
from mkwww.rst.dtlist import DetailsListIdsTransform, DetailsListHTML

from docutils.readers.standalone import Reader as _Reader
from docutils.writers.html5_polyglot import Writer as _Writer, HTMLTranslator as _HTMLTranslator


class HTMLTranslator(AbbrHTML, PermalinkSectionHTML, ExtlinkHTML, DetailsListHTML, _HTMLTranslator):
  pass

class Reader(_Reader):
  def get_transforms(self):
    return super().get_transforms() + [
      PropagateClassesListFix,
      PropagateTargetsListFix,
      DetailsListIdsTransform,
    ]

class Writer(_Writer):
  def __init__(self):
    super().__init__()
    self.translator_class = HTMLTranslator
