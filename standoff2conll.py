#!/usr/bin/env python

from __future__ import print_function

import sys
import os
import codecs

from logging import error

from document import Document
from common import pairwise
from asciify import document_to_ascii
from unicode2ascii import log_missing_ascii_mappings
from tagsequence import TAGSETS, IO_TAGSET, IOBES_TAGSET, DEFAULT_TAGSET
from tagsequence import BIO_to_IO, BIO_to_IOBES

def argparser():
    import argparse
    ap = argparse.ArgumentParser(description='Convert standoff to CoNLL format',
                                 usage='%(prog)s [OPTIONS] DIRECTORY')
    ap.add_argument('directory')
    ap.add_argument('-1', '--singletype', default=None, metavar='TYPE',
                    help='replace all annotation types with TYPE')
    ap.add_argument('-a', '--asciify', default=None, action='store_true',
                    help='map input to ASCII')
    ap.add_argument('-s', '--tagset', choices=TAGSETS, default=None,
                    help='tagset (default %s)' % DEFAULT_TAGSET)
    return ap

def is_standoff_file(fn):
    return os.path.splitext(fn)[1] == '.ann'

def txt_for_ann(filename):
    return os.path.splitext(filename)[0]+'.txt'

def read_ann(filename, encoding='utf-8'):
    txtfilename = txt_for_ann(filename)
    with codecs.open(txtfilename, 'rU', encoding=encoding) as t_in:
        with codecs.open(filename, 'rU', encoding=encoding) as a_in:
            return Document.from_standoff(t_in.read(), a_in.read())

def replace_types_with(document, type_):
    from tagsequence import OUT_TAG, parse_tag, make_tag
    for sentence in document.sentences:
        for token in sentence.tokens:
            if token.tag != OUT_TAG:
                token.tag = make_tag(parse_tag(token.tag)[0], type_)

def retag_document(document, tagset):
    if tagset == IO_TAGSET:
        mapper = BIO_to_IO
    elif tagset == IOBES_TAGSET:
        mapper = BIO_to_IOBES
    else:
        raise ValueError('tagset {}'.format(tagset))
    for sentence in document.sentences:
        for t, next_t in pairwise(sentence.tokens, include_last=True):
            next_tag = next_t.tag if next_t is not None else None
            t.tag = mapper(t.tag, next_tag)

def convert_directory(directory, options):
    files = [n for n in os.listdir(directory) if is_standoff_file(n)]
    files = [os.path.join(directory, fn) for fn in files]

    if not files:
        error('No standoff files in {}'.format(directory))
        return

    for fn in sorted(files):
        document = read_ann(fn)
        if options.singletype:
            replace_types_with(document, options.singletype)
        if options.tagset:
            retag_document(document, options.tagset)
        if options.asciify:
            document_to_ascii(document)
        conll_data = document.to_conll()
        sys.stdout.write(conll_data.encode('utf-8'))

def main(argv):
    args = argparser().parse_args(argv[1:])
    if not os.path.isdir(args.directory):
        error('Not a directory: {}'.format(args.directory))
        return 1
    convert_directory(args.directory, args)
    if args.asciify:
        log_missing_ascii_mappings()
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))
