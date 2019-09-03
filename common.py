import re

from collections import OrderedDict
from itertools import chain, tee
from functools import reduce

class FormatError(Exception):
    pass


# TODO: Unicode support
TOKENIZATION_REGEXS = OrderedDict([
    # NERsuite-like tokenization: alnum sequences preserved as single
    # tokens, rest are single-character tokens.
    ('default', re.compile(r'([^\W_]+|.)')),
    # Finer-grained tokenization: also split alphabetical from numeric.
    ('fine', re.compile(r'([0-9]+|[^\W0-9_]+|.)')),
    # Whitespace tokenization
    ('space', re.compile(r'(\S+)')),
])

# adapted from http://docs.python.org/library/itertools.html#recipes
def pairwise(iterable, include_last=False):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    next(b, None)
    if not include_last:
        return list(zip(a, b))
    else:
        return list(zip(a, chain(b, (None, ))))

# from http://programmaticallyspeaking.com/split-on-separator-but-keep-the-separator-in-python.html
def split_keep_separator(s, sep='\n'):
    return reduce(lambda acc, elem: acc[:-1] + [acc[-1] + elem] if elem == sep 
                  else acc + [elem], re.split("(%s)" % re.escape(sep), s), [])

def sentence_to_tokens(text, tokenization_re=None):
    """Return list of tokens in given sentence using NERsuite tokenization."""

    if tokenization_re is None:
        tokenization_re = TOKENIZATION_REGEXS.get('default')
    tok = [t for t in tokenization_re.split(text) if t]
    assert ''.join(tok) == text
    return tok
