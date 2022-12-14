#!/usr/bin/python3

import itertools
import os.path
import re
import sys
from tinycss2 import ast
import tinycss2

# match a comma but only if it's not in parentheses
# https://stackoverflow.com/a/9030062
selsplit = re.compile(r"(,\s*)(?![^(]*\))")

# drop non-minimal asciidoctor styling rules
# see https://github.com/asciidoctor/asciidoctor/issues/4376
# TODO: this is a massive hack, we should stop doing it once they fix that issue
asciidoctor_disable = re.compile("|".join([
  r"#content\b",
  r"#toc\b",
  r"#header\b",
  r"#footer\b",
  r"\.sect1\b",
  r"(^|\s*)h[1-6]\b",
  r"(^|\s*)a\b",
  r"^p$",
  r"^p strong$",
  r"\.quoteblock p\b$",
  r"\.paragraph\.lead>p\b$",
  r"^table tr td$",
  r"\.videoblock\b$",
]))

def transform_rules(rules, prune_asciidoctor, prefix):
  for rule in rules:
    if rule.type == 'qualified-rule':
      # transform selectors
      prelude = tinycss2.serialize(rule.prelude)
      parts = selsplit.split(prelude)
      if prune_asciidoctor and any((asciidoctor_disable.match(p) for p in parts)):
        # drop certain selectors
        parts = ["#disabled-rule-asciidoctor"]
      else:
        selectors, commas = parts[0::2], parts[1::2]
        parts[0::2] = [prefix + " " + s for s in selectors]
      rule.prelude = tinycss2.parse_component_value_list("".join(parts))

      # transform content
      if prune_asciidoctor:
        # drop font-family rules
        new_content = []
        keep = True
        for r in rule.content:
          if r.type == 'ident' and r.value == 'font-family':
            keep = False
          if keep:
            new_content.append(r)
          if r.type == 'literal' and r.value == ';':
            keep = True
        rule.content = new_content

    elif rule.type == 'at-rule':
      if not rule.content:
        continue
      content_rules = tinycss2.parse_rule_list(tinycss2.serialize(rule.content))
      if any((r.type == 'error' for r in content_rules)):
        continue
      transform_rules(content_rules, prune_asciidoctor, prefix)
      rule.content = tinycss2.parse_component_value_list(tinycss2.serialize(content_rules))

def scan_comments(rules):
  return "".join(r.value.lower() if r.type == 'comment' else '' for r in rules[:8])

def main(fn, *args):
  with open(fn) as fp:
    rules = tinycss2.parse_stylesheet(fp.read())

  comments = scan_comments(rules)
  fn = os.path.basename(fn)
  if fn.startswith('mkwww-j2-'):
    transform_rules(rules, False, "main .main-mkwww-j2")
  if fn.startswith('docutils-'):
    transform_rules(rules, False, "main .main-docutils")
  if fn.startswith('asciidoctor-'):
    transform_rules(rules, fn.endswith('-default.css'), "main .main-asciidoc")

  sys.stdout.write(tinycss2.serialize(rules))
  sys.stdout.flush()

if __name__ == "__main__":
  sys.exit(main(*sys.argv[1:]))
