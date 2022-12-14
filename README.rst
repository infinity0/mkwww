=====
mkwww
=====

Minimalist engine for building a minimalist static website. Features:

- autogenerate navigation sidebar, and include it on every page
- autogenerate page metadata from git, e.g. author, modtime
- supports md (myst), rst, adoc -- and others can be added easily later

Sphinx can do most of this, but its code, themes, and configuration are all too
bloated for my simple needs; I just want a minimalist website. Other simpler
tools I looked at were either:

- unable to generate a navigation sidebar
- could in theory do it, but you had to learn 1000 internal details
- didn't support all of {md, rst, adoc}

So, I wrote my own. The target audience is someone who, like myself:

- is a technical person that wants to build a minimalist static website
- understands web technology down to its fundamental layers (HTML, CSS, JS)
- appreciates not repeating oneself for basic website tasks such as navigation
  and metadata management, yet also
- appreciates being able to work in those layers directly when needed, in order
  to support technically creative website features that are too unique to be
  handled by higher layer or more "user-friendly" CMS tools

To that end, this tool is essentially a high-level lightweight structure around
jinja2, that automates away those basic website tasks, yet also provides a
simple way to use fundamental web technologies directly.

Dependencies
============

- GNU make -- tested with v4.3
- Python 3 -- tested with v3.10
- jinja2 -- tested with v3.0.3
- jq -- tested with v1.6
- python-tinycss2 -- tested with v1.2.1
- python-myst, python-linkify-it -- optional for MarkDown support; tested with v0.18.1; requires python-docutils
- python-docutils -- optional for reStructuredText support; tested with v0.19
- asciidoctor -- optional for AsciiDoc support; tested with v2.0.17
- pandoc -- optional for better LaTeX MathML support in MarkDown and reStructuredText; tested with v2.17
- asciidoctor-mathematical `custom fork <https://github.com/infinity0/asciidoctor-mathematical>`_ -- optional for LaTeX MathML support in AsciiDoc; tested with `v0.1003.5 <https://github.com/infinity0/asciidoctor-mathematical/tree/local-testing>`_; requires pandoc
- `checklink <https://github.com/w3c/link-checker>`_ -- optional for testing

Usage
=====

Example::

  $ cd example
  $ ../mkwww -j check
  $ open dist/index.html

FAQ
===

What flavour of MarkDown do you use?
  We use the `MyST <https://myst-parser.readthedocs.io/en/latest/>`_ flavour of
  MarkDown. Some nice things about it:

  - it's based on docutils, so integrates nicely with our other support scripts
    for reStructuredText, and saves us duplicating our tweaks
  - it maintains compatibility with `GFM <https://github.github.com/gfm/>`_
    where their features overlap

  See the example site for a demo.

Why don't we just use ``pandoc(1)`` for everything?
  `Pandoc <https://pandoc.org>`_ is a very nice tool that converts between many
  different document formats. By its nature however, it focuses on features
  that are shared between several formats. This means it has to omit supporting
  the most advanced features of a given format. We instead prefer to use the
  "main" tool for each format, to support the most advanced features.
