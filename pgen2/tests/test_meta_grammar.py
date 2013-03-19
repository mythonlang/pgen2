#! /usr/bin/env python
# ______________________________________________________________________
# Module imports

import unittest
import os

import pgen2.parser
import pgen2.pgen

# ______________________________________________________________________
# Module data

META_GRAMMAR_PATH = os.path.join(os.path.split(pgen2.parser.__file__)[0], 
                                 'tests',
                                 'meta.pgen')

with open(META_GRAMMAR_PATH) as metafile:
    META_GRAMMAR = metafile.read()

# ______________________________________________________________________
# Function definitions

def clean_nonterminals(tree):
    data, children = tree
    try:
        symbol, _, _ = data
        if symbol < pgen2.parser.MSTART:
            symbol = data
    except TypeError:
        symbol = data
    return symbol, [clean_nonterminals(child) for child in children]

# ______________________________________________________________________
# Class definitions

class TestMetaGrammar(unittest.TestCase):
    def test_parse_file(self):
        grammar_st0 = pgen2.parser.parse_file(META_GRAMMAR_PATH)
        grammar_parser = pgen2.pgen.buildParser(grammar_st0)
        grammar_st1 = grammar_parser.parseFile(META_GRAMMAR_PATH)
        self.assertEqual(grammar_st0, clean_nonterminals(grammar_st1))

    def test_parse_string(self):
        grammar_st0 = pgen2.parser.parse_string(META_GRAMMAR)
        grammar_parser = pgen2.pgen.buildParser(grammar_st0)
        grammar_st1 = grammar_parser.parseString(META_GRAMMAR)
        self.assertEqual(grammar_st0, clean_nonterminals(grammar_st1))

# ______________________________________________________________________
# Main (test) routine

if __name__ == "__main__":
    unittest.main()

# ______________________________________________________________________
# End of pgen2.tests.test_meta_grammar
