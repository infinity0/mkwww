import bs4

def el_lstrip(el):
  if isinstance(el, str):
    el.replace_with(el.lstrip())

def extract_raw(main, selector, postproc=lambda x: x):
  soup = bs4.BeautifulSoup(main, 'html.parser', preserve_whitespace_tags={'html', 'body', 'main', 'div'})

  elements = soup.select(selector)
  extracted = []
  for element in elements:
    el_lstrip(element.next_sibling)
    element.extract()
    element = postproc(element)
    if element.contents:
      el_lstrip(element.contents[0])
    extracted.extend(element.contents)

  return soup, extracted

def extract(main, selector, postproc=lambda x: x):
  soup, extracted = extract_raw(main, selector, postproc=postproc)
  return str(soup), "".join(str(x) for x in extracted)
