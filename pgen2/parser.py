#! /usr/bin/env python
# ______________________________________________________________________
"""Module pypgen.parser

Implements a recursive descent parser for the Python pgen parser generator
input language.
"""
# ______________________________________________________________________

from __future__ import absolute_import

import token
from . import tokenizer
import pprint

# ______________________________________________________________________
# XXX I am unsure I want these here.  Conversely, pgen really doesn't change
# at all, so what is the harm in duplicating these?

MSTART = 256
RULE = 257
RHS = 258
ALT = 259
ITEM = 260
ATOM = 261

# ______________________________________________________________________

__DEBUG__ = False

# ______________________________________________________________________

def expect (val, tok):
    type, name, lineno = tok
    if val != type:
        if name == None:
            gotStr = token.tok_name[type]
        else:
            gotStr = repr(name)
        errStr = ("Line %d, expecting %s, got %s." %
                  (lineno, token.tok_name[val], gotStr))
        raise SyntaxError(errStr)

# ______________________________________________________________________

def handleStart (tokenizer_obj):
    """handleStart()
    MSTART := ( RULE | NEWLINE )* ENDMARKER
    """
    children = []
    crntToken = next(tokenizer_obj)
    while token.ENDMARKER != crntToken[0]:
        if token.NEWLINE == crntToken[0]:
            children.append((crntToken, []))
            crntToken = None
        else:
            ruleResult, crntToken = handleRule(tokenizer_obj, crntToken)
            children.append(ruleResult)
        if None == crntToken:
            crntToken = next(tokenizer_obj)
    children.append((crntToken, []))
    return (MSTART, children)

# ______________________________________________________________________

def handleRule (tokenizer_obj, crntToken = None):
    """handleRule()
    RULE := NAME COLON RHS NEWLINE
    """
    children = []
    if None == crntToken:
        crntToken = tokenzier()
    expect(token.NAME, crntToken)
    children.append((crntToken, []))
    crntToken = next(tokenizer_obj)
    expect(token.COLON, crntToken)
    children.append((crntToken, []))
    rhsResult, crntToken = handleRhs(tokenizer_obj)
    children.append(rhsResult)
    if None == crntToken:
        crntToken = next(tokenizer_obj)
    expect(token.NEWLINE, crntToken)
    children.append((crntToken, []))
    result = (RULE, children)
    if __DEBUG__:
        pprint.pprint(result)
    return result, None

# ______________________________________________________________________

def handleRhs (tokenizer_obj, crntToken = None):
    """handleRhs()
    RHS := ALT ( VBAR ALT )*
    """
    children = []
    altResult, crntToken = handleAlt(tokenizer_obj, crntToken)
    children.append(altResult)
    if None == crntToken:
        crntToken = next(tokenizer_obj)
    while crntToken[0] == token.VBAR:
        children.append((crntToken, []))
        altResult, crntToken = handleAlt(tokenizer_obj)
        children.append(altResult)
        if None == crntToken:
            crntToken = next(tokenizer_obj)
    result = (RHS, children)
    if __DEBUG__:
        pprint.pprint(result)
    return result, crntToken

# ______________________________________________________________________

def handleAlt (tokenizer_obj, crntToken = None):
    """handleAlt()
    ALT := ITEM+
    """
    children = []
    itemResult, crntToken = handleItem(tokenizer_obj, crntToken)
    children.append(itemResult)
    if None == crntToken:
        crntToken = next(tokenizer_obj)
    while crntToken[0] in (token.LSQB, token.LPAR, token.NAME, token.STRING):
        itemResult, crntToken = handleItem(tokenizer_obj, crntToken)
        children.append(itemResult)
        if None == crntToken:
            crntToken = next(tokenizer_obj)
    return (ALT, children), crntToken

# ______________________________________________________________________

def handleItem (tokenizer_obj, crntToken = None):
    """handleItem()
    ITEM := LSQB RHS RSQB
         | ATOM ( STAR | PLUS )?
    """
    children = []
    if None == crntToken:
        crntToken = next(tokenizer_obj)
    if crntToken[0] == token.LSQB:
        children.append((crntToken, []))
        rhsResult, crntToken = handleRhs(tokenizer_obj)
        children.append(rhsResult)
        if None == crntToken:
            crntToken = next(tokenizer_obj)
        expect(token.RSQB, crntToken)
        children.append((crntToken, []))
        crntToken = None
    else:
        atomResult, crntToken = handleAtom(tokenizer_obj,crntToken)
        children.append(atomResult)
        if None == crntToken:
            crntToken = next(tokenizer_obj)
        if crntToken[0] in (token.STAR, token.PLUS):
            children.append((crntToken, []))
            crntToken = None
    return (ITEM, children), crntToken

# ______________________________________________________________________

def handleAtom (tokenizer_obj, crntToken = None):
    """handleAtom()
    ATOM := LPAR RHS RPAR
          | NAME
          | STRING
    """
    children = []
    if None == crntToken:
        crntToken = next(tokenizer_obj)
    tokType = crntToken[0]
    if tokType == token.LPAR:
        children.append((crntToken, []))
        rhsResult, crntToken = handleRhs(tokenizer_obj)
        children.append(rhsResult)
        if None == crntToken:
            crntToken = next(tokenizer_obj)
        expect(token.RPAR, crntToken)
        children.append((crntToken, []))
        #crntToken = None
    elif tokType == token.STRING:
        children.append((crntToken, []))
        #crntToken = None
    else:
        expect(token.NAME, crntToken)
        children.append((crntToken, []))
        # crntToken = None
    return (ATOM, children), None

# ______________________________________________________________________

def parse_string(in_string, tokenizer_obj=None):
    if tokenizer_obj == None:
        tokenizer_obj = tokenizer.Tokenizer()
    return handleStart(tokenizer_obj.tokenizeString(in_string))

# ______________________________________________________________________

def parse_file(filename, tokenizer_obj=None):
    with open(filename) as fileobj:
        if tokenizer_obj == None:
            tokenizer_obj = tokenizer.Tokenizer()
        ret_val = handleStart(tokenizer_obj.tokenize(fileobj))
    return ret_val

# ______________________________________________________________________

def main ():
    import sys
    if len(sys.argv) > 1:
        parse_tree = parse_file(sys.argv[1])
    else:
        parse_tree = parse_string(sys.stdin.read())
    pprint.pprint(parse_tree)

# ______________________________________________________________________

if __name__ == "__main__":
    main()

# ______________________________________________________________________
# End of pypgen.parser.
