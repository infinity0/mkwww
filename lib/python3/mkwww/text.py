import re


# TODO: make this work for all languages
# https://stackoverflow.com/questions/9506869/are-there-character-collections-for-all-international-full-stop-punctuations
HALF_BREAK = ",;:-"
FULL_BREAK = ".?!"
FULL_BREAK_STD = "."

def ensure_full_stop(text):
  # convert half-stop punctuation into full-stop punctuation
  if any(text.endswith(c) for c in HALF_BREAK):
    text = text[:-1].rstrip()
  if not text.endswith(FULL_BREAK_STD):
    text = text + FULL_BREAK_STD
  return text

UNICODE_RANGES_CHINESE = [
  ("\u4E00", "\u9FFF"),
  ("\u3400", "\u4DBF"),
  ("\u20000", "\u2A6DF"),
  ("\u2A700", "\u2B73F"),
  ("\u2B740", "\u2B81F"),
  ("\u2B820", "\u2CEAF"),
  ("\u2CEB0", "\u2EBEF"),
  ("\u30000", "\u3134F"),
  ("\u31350", "\u323AF"),
  ("\uF900", "\uFAFF"),
  ("\u2F800", "\u2FA1F"),
]

def approx_words(text):
  alnum = re.findall("\w", text)
  chinese = sum(1 for c in alnum if any(a <= c <= b for (a, b) in UNICODE_RANGES_CHINESE))
  english = len(alnum) - chinese
  return round(english / 5.75 + chinese * 0.8)

def rough_approx(n):
  r = None
  for t in (10, 50, 100, 500, 1000, 5000, 10000, 50000, 100000, 500000, 1000000):
    k = t / 10
    if n < t:
      r = round(n / k) * k
      break
  return "bruh" if r is None else "%g" % r if r < 1000 else "%gk" % (r / 1000)
