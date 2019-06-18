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
from standoff import DISCONT_RULES, OVERLAP_RULES
from common import TOKENIZATION_REGEXS


def argparser():
    import argparse
    ap = argparse.ArgumentParser(description='Convert standoff to CoNLL format',
                                 usage='%(prog)s [OPTIONS] DIRS/FILES')
    ap.add_argument('-1', '--singletype', default=None, metavar='TYPE',
                    help='replace all annotation types with TYPE')
    ap.add_argument('-a', '--asciify', default=None, action='store_true',
                    help='map input to ASCII')
    ap.add_argument('-c', '--char-offsets', default=False, action='store_true',
                    help='include character offsets')
    ap.add_argument('-n', '--no-sentence-split', default=False,
                    action='store_true',
                    help='do not perform sentence splitting')
    ap.add_argument('-d', '--discont-rule', choices=DISCONT_RULES,
                    default=DISCONT_RULES[0],
                    help='rule to apply to resolve discontinuous annotations')
    ap.add_argument('-i', '--include-docid', default=False, action='store_true',
                    help='include document IDs')
    ap.add_argument('-k', '--tokenization', choices=TOKENIZATION_REGEXS.keys(),
                    default=TOKENIZATION_REGEXS.keys()[0], help='tokenization')
    ap.add_argument('-o', '--overlap-rule', choices=OVERLAP_RULES,
                    default=OVERLAP_RULES[0],
                    help='rule to apply to resolve overlapping annotations')
    ap.add_argument('-s', '--tagset', choices=TAGSETS, default=None,
                    help='tagset (default %s)' % DEFAULT_TAGSET)
    ap.add_argument('-t', '--types', metavar='TYPE', nargs='*',
                    help='filter annotations to given types')
    ap.add_argument('-x', '--exclude', metavar='TYPE', nargs='*',
                    help='exclude annotations of given types')
    ap.add_argument('data', metavar='DIRS/FILES', nargs='+')
    return ap

def is_standoff_file(fn):
    return os.path.splitext(fn)[1] in ('.ann', '.a1')

def txt_for_ann(filename):
    return os.path.splitext(filename)[0]+'.txt'

def document_id(filename):
    return os.path.splitext(os.path.basename(filename))[0]

def read_ann(filename, options, encoding='utf-8'):
    txtfilename = txt_for_ann(filename)
    with codecs.open(txtfilename, 'rU', encoding=encoding) as t_in:
        with codecs.open(filename, 'rU', encoding=encoding) as a_in:
            return Document.from_standoff(
                t_in.read(), a_in.read(),
                sentence_split = not options.no_sentence_split,
                discont_rule = options.discont_rule,
                overlap_rule = options.overlap_rule,
                filter_types = options.types,
                exclude_types = options.exclude,
                tokenization_re = TOKENIZATION_REGEXS.get(options.tokenization),
                document_id = document_id(filename)
            )

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

    convert_files(files, options)

def convert_files(files, options):
    for fn in sorted(files):
        document = read_ann(fn, options)
        if options.singletype:
            replace_types_with(document, options.singletype)
        if options.tagset:
            retag_document(document, options.tagset)
        if options.asciify:
            document_to_ascii(document)
        conll_data = document.to_conll(
            include_offsets=options.char_offsets,
            include_docid=options.include_docid
        )
        sys.stdout.write(conll_data.encode('utf-8'))

def main(argv):
    args = argparser().parse_args(argv[1:])
    files = []
    for path in args.data:
        if os.path.isdir(path):
            convert_directory(path, args)
        else:
            files.append(path)
    if files:
        convert_files(files, args)
    if args.asciify:
        log_missing_ascii_mappings()
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))
