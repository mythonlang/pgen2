#! /usr/bin/env python
# ______________________________________________________________________
"""
Implements utility data, functions and/or classes for use in developing
tokenizers for pypgen and pygen-generated parser.
"""
# ______________________________________________________________________

import string
try:
    import StringIO as io
except ImportError:
    import io
import tokenize

# ______________________________________________________________________

def testTokenizer (TokenizerClass):
    """testTokenizer()
    Run some silly little test on the tokenizer class argument.
    """
    import sys
    if len(sys.argv) == 1:
        tokenizer = TokenizerClass().tokenize(sys.stdin)
    else:
        tokenizer = TokenizerClass().tokenizeFile(sys.argv[1])
    tokenData = (tokenize.NEWLINE, None, 0)
    while tokenData[0] not in (tokenize.ENDMARKER, tokenize.ERRORTOKEN):
        tokenData = next(tokenizer)
        print(tokenData)

# ______________________________________________________________________

class Tokenizer (object) :
    """A simple lexical analyser based on Python's tokenize module.

    The differences with tokenize module are:
     - new simple tokens may be added (just strings, no regexps)
     - Python's token may be not included
     - tokens may be automatically skipped (removed from the output)
     - tokenize.OP kind is refined (eg, ':' gets kind tokenize.COLON)
    """
    operatorMap = {
        '(' : tokenize.LPAR,
        ')' : tokenize.RPAR,
        '[' : tokenize.LSQB,
        ']' : tokenize.RSQB,
        ':' : tokenize.COLON,
        ',' : tokenize.COMMA,
        ';' : tokenize.SEMI,
        '+' : tokenize.PLUS,
        '+=' : tokenize.PLUSEQUAL,
        '-' : tokenize.MINUS,
        '-=' : tokenize.MINEQUAL,
        '*' : tokenize.STAR,
        '**' : tokenize.DOUBLESTAR,
        '**=' : tokenize.DOUBLESTAREQUAL,
        '*=' : tokenize.STAREQUAL,
        '/' : tokenize.SLASH,
        '//' : tokenize.DOUBLESLASH,
        '//=' : tokenize.DOUBLESLASHEQUAL,
        '/=' : tokenize.SLASHEQUAL,
        '|' : tokenize.VBAR,
        '|=' : tokenize.VBAREQUAL,
        '&' : tokenize.AMPER,
        '&=' : tokenize.AMPEREQUAL,
        '<' : tokenize.LESS,
        '<=' : tokenize.LESSEQUAL,
        '<<' : tokenize.LEFTSHIFT,
        '<<=' : tokenize.LEFTSHIFTEQUAL,
        '>' : tokenize.GREATER,
        '>=' : tokenize.GREATEREQUAL,
        '>>' : tokenize.RIGHTSHIFT,
        '>>=' : tokenize.RIGHTSHIFTEQUAL,
        '=' : tokenize.EQUAL,
        '==' : tokenize.EQEQUAL,
        '.' : tokenize.DOT,
        '%' : tokenize.PERCENT,
        '%=' : tokenize.PERCENTEQUAL,
        '`' : getattr(tokenize, "BACKQUOTE", tokenize.ERRORTOKEN),
        '{' : tokenize.LBRACE,
        '}' : tokenize.RBRACE,
        '^' : tokenize.CIRCUMFLEX,
        '^=' : tokenize.CIRCUMFLEXEQUAL,
        '~' : tokenize.TILDE,
        '!=' : tokenize.NOTEQUAL,
        '<>' : tokenize.NOTEQUAL,
        '@' : tokenize.AT,
        '@=' : getattr(tokenize, 'ATEQUAL', tokenize.ERRORTOKEN),
        '->' : getattr(tokenize, 'RARROW', tokenize.ERRORTOKEN),
        '...' : getattr(tokenize, 'ELLIPSIS', tokenize.ERRORTOKEN),
        ':=' : getattr(tokenize, 'COLONEQUAL', tokenize.ERRORTOKEN),
        }

    def __init__ (self, python=True, opmap={}, skip=None, **extra) :
        """Initialize a new instance.

        Expected arguments are:
         - python: a bool to indicate whether to include or not
           Python's tokens (default to True)
         - opmap: a dict to map litteral tokens (given as '...' in the
           grammar) to token kinds (default to {}). This parameter is
           useful only to redefine Python's mapping
         - skip: a collection of tokens that the tokenizer will
           automatically skip (default to [COMMENT, NL])
         - additional keywords arguments allow to define new tokens,
           for instance, providing
              DOLLAR='$'
           defines a new token called 'DOLLAR' (its kind will be
           automatically computed)

        An instance of Tokenizer has the following attributes:
         - self.operatorMap: a dict mapping operators token literals to the
           corresponding kind, for instance, ':' is mapped to
           tokenize.COLON (this can be overridden using argument
           opmap)
         - self.tok_name: a replacement of tokenize.tok_name that also
           include the user-defined tokens
         - for each token called FOO (including user-defined ones), an
           attribute self.FOO hols the corresponding kind
        """
        self._python = python
        self.operatorMap = opmap.copy()
        if python:
            self.operatorMap = self.__class__.operatorMap.copy()
            self.operatorMap.update(opmap)
        else :
            self.operatorMap = opmap.copy()
        self.tok_name = {}
        self._extra = {}
        if python:
            for kind, name in tokenize.tok_name.items():
                self.tok_name[kind] = name
                setattr(self, name, kind)
            # Hack since NT_OFFSET doesn't appear in pypy's
            # tokenize.tok_name dictionary.
            nt_off_str = 'NT_OFFSET'
            if not hasattr(self, nt_off_str):
                nt_off_kind = tokenize.NT_OFFSET
                self.tok_name[nt_off_kind] = nt_off_str
                setattr(self, nt_off_str, nt_off_kind)
        last = max(n for n in self.tok_name if n != self.NT_OFFSET)
        for shift, (name, txt) in enumerate(sorted(extra.items())) :
            #WARNING: sorted above is required to guaranty that extra
            # tokens will always get the same number (dict order is
            # not guaranteed)
            kind = last + shift
            if kind >= self.NT_OFFSET :
                raise ValueError("too many new tokens")
            self.tok_name[kind] = name
            setattr(self, name, kind)
            self._extra[txt] = kind
        self.operatorMap.update(self._extra)
        if skip is None :
            skip = [self.COMMENT, self.NL]
        self._skip = set(skip)

    def __repr__ (self) :
        """Encodes an instance as Python source code.

        Non-default arguments provided to the constructor are included
        so that exactly the same Tokenizer instance can be recovered
        from the returned source code.

        >>> print repr(Tokenizer())
        Tokenizer()
        >>> print repr(Tokenizer(DOLLAR='$'))
        Tokenizer(DOLLAR='$')
        >>> print repr(Tokenizer(skip=[], DOLLAR='$'))
        Tokenizer(skip=[], DOLLAR='$')
        """
        args = []
        if not self._python :
            args.append("python=%s" % self._python)
        if hasattr(self, "_opmap"):
            args.append("opmap=%r" % self._opmap)
        if self._skip != set([self.COMMENT, self.NL]) :
            args.append("skip=%r" % list(self._skip))
        args.extend("%s=%r" % (self.tok_name[kind], txt) for txt, kind
                    in self._extra.items())
        return "%s(%s)" % (self.__class__.__name__, ", ".join(args))

    def tokenize (self, stream) :
        """Break an input stream into tokens.

        Expected argument is:
         - stream: a file-like object (with a method readline)

        Return a generator of tokens, SyntaxError is raised whenever an
        erroneous token is encountered.

        This is basically the same as tokenize.generate_tokens but:
         - the appropriate tokens are skipped
         - OP kind is converted according to self.operatorMap
         - user-defined tokens are handled

        During the iteration, two more attributes can be used:
         - self.last: last recognized token (ie, last yielded)
         - self.infile: the input stream passed to method tokenize
        """
        self.infile = stream
        self.last = None
        err = self.ERRORTOKEN
        for token in tokenize.generate_tokens(stream.readline) :
            if token[0] == err :
                try :
                    token = (self._extra[token[1]],) + token[1:]
                except :
                    raise SyntaxError(token)
            elif token[0] in self._skip :
                continue
            elif token[0] == self.OP :
                token = (self.operatorMap[token[1]],) + token[1:]
            self.last = token
            yield (self.last[0],
                   self.last[1] or self.tok_name[self.last[0]],
                   self.last[2][0])
   # ____________________________________________________________
    def getOperatorMap (self):
        """getOperatorMap
        """
        return self.operatorMap
    # ____________________________________________________________
    def tokenizeFile (self, filename):
        """StdTokenizer.tokenizeFile()

        FIXME: This is not 'safe' in that it won't close the file
        object.  Maybe deprecate this method in favor of just using
        tokenize()?
        """
        self.filename = filename
        self.fileObj = open(filename)
        return self.tokenize(self.fileObj)
    # ____________________________________________________________
    def tokenizeString (self, inString):
        """StdTokenizer.tokenizeString()
        """
        self.filename = "<string>"
        self.fileObj = io.StringIO(inString)
        return self.tokenize(self.fileObj)

# ______________________________________________________________________

class TokenizerFactory:
    """
    Deprecated.  Just construct a Tokenizer instance.
    """
    # ____________________________________________________________
    def __init__ (self, tokenizerClass, opMap = None):
        if None == opMap:
            opMap = tokenizerClass.operatorMap
        self.tokenizerClass = tokenizerClass
        self.operatorMap = opMap

    # ____________________________________________________________
    def getTokenizer (self):
        return self.tokenizerClass()

    # ____________________________________________________________
    def getTokenizerClass (self):
        return self.tokenizerClass

    # ____________________________________________________________
    def getOperatorMap (self):
        return self.operatorMap

# ______________________________________________________________________
# End of pypgen.tokenizer.
