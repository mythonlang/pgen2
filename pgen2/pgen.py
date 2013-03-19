#! /usr/bin/env python
# ______________________________________________________________________
"""
Python implementation of the CPython distribution parser generator, pgen.
"""
# ______________________________________________________________________
# Module imports

from __future__ import absolute_import

from . import tokenizer, parser, dfa
import sys, token, string, pprint

# ______________________________________________________________________
# Module data

EMPTY = token.ENDMARKER

__DEBUG__ = False

try:
    long(0)
    ascii_letters = string.letters
except:
    # Python 3
    long = int
    ascii_letters = string.ascii_letters

# ______________________________________________________________________

class PyPgen (object):
    """Class PyPgen
    """
    # ____________________________________________________________
    def __init__ (self, opMap = None, **kws):
        """PyPgen.__init__
        """
        self.nfaGrammar = self.dfaGrammar = None
        self.nfa = None
        self.crntType = token.NT_OFFSET
        if None == opMap:
            self.operatorMap = tokenizer.Tokenizer.operatorMap
        else:
            self.operatorMap = opMap
        self.kws = kws

    # ____________________________________________________________
    def addLabel (self, labelList, tokType, tokName):
        """PyPgen.addLabel
        """
        # XXX
        #labelIndex = 0
        #for labelType, labelName in labelList:
        #    if (labelType == tokType) and (labelName == tokName):
        #        return labelIndex
        #    labelIndex += 1
        labelTup = (tokType, tokName)
        if labelTup in labelList:
            return labelList.index(labelTup)
        labelIndex = len(labelList)
        labelList.append(labelTup)
        return labelIndex

    # ____________________________________________________________
    def handleStart (self, ast):
        """PyPgen.handleStart()
        """
        self.nfaGrammar = [[],[(token.ENDMARKER, "EMPTY")]]
        self.crntType = token.NT_OFFSET
        type, children = ast
        assert type == parser.MSTART
        for child in children:
            if child[0] == parser.RULE:
                self.handleRule(child)
        return self.nfaGrammar

    # ____________________________________________________________
    def handleRule (self, ast):
        """PyPgen.handleRule()

        NFA := [ type : Int, name : String, [ STATE ], start : Int,
                 finish : Int ]
        STATE := [ ARC ]
        ARC := ( labelIndex : Int, stateIndex : Int )
        """
        # Build the NFA shell.
        self.nfa = [self.crntType, None, [], -1, -1]
        self.crntType += 1
        # Work on the AST node
        type, children = ast
        assert type == parser.RULE
        name, colon, rhs, newline = children
        assert name[0][0] == token.NAME, "Malformed pgen parse tree"
        self.nfa[1] = name[0][1]
        if (token.NAME, name[0][1]) not in self.nfaGrammar[1]:
            self.nfaGrammar[1].append((token.NAME, name[0][1]))
        assert colon[0][0] == token.COLON, "Malformed pgen parse tree"
        start, finish = self.handleRhs(rhs)
        self.nfa[3] = start
        self.nfa[4] = finish
        assert newline[0][0] == token.NEWLINE, "Malformed pgen parse tree"
        # Append the NFA to the grammar.
        self.nfaGrammar[0].append(self.nfa)

    # ____________________________________________________________
    def handleRhs (self, ast):
        """PyPgen.handleRhs()
        """
        type, children = ast
        assert type == parser.RHS
        start, finish = self.handleAlt(children[0])
        if len(children) > 1:
            cStart = start
            cFinish = finish
            start = len(self.nfa[2])
            self.nfa[2].append([(EMPTY, cStart)])
            finish = len(self.nfa[2])
            self.nfa[2].append([])
            self.nfa[2][cFinish].append((EMPTY, finish))
            for child in children[2:]:
                if child[0] == parser.ALT:
                    cStart, cFinish = self.handleAlt(child)
                    self.nfa[2][start].append((EMPTY, cStart))
                    self.nfa[2][cFinish].append((EMPTY, finish))
        return start, finish

    # ____________________________________________________________
    def handleAlt (self, ast):
        """PyPgen.handleAlt()
        """
        type, children = ast
        assert type == parser.ALT
        start, finish = self.handleItem(children[0])
        if len(children) > 1:
            for child in children[1:]:
                cStart, cFinish = self.handleItem(child)
                self.nfa[2][finish].append((EMPTY, cStart))
                finish = cFinish
        return start, finish

    # ____________________________________________________________
    def handleItem (self, ast):
        """PyPgen.handleItem()
        """
        nodeType, children = ast
        assert nodeType == parser.ITEM
        if children[0][0] == parser.ATOM:
            start, finish = self.handleAtom(children[0])
            if len(children) > 1:
                # Short out the child NFA
                self.nfa[2][finish].append((EMPTY, start))
                if children[1][0][0] == token.STAR:
                    finish = start
                else:
                    assert children[1][0][0] == token.PLUS
        else:
            assert children[0][0][0] == token.LSQB
            start = len(self.nfa[2])
            finish = start + 1
            self.nfa[2].append([(EMPTY, finish)])
            self.nfa[2].append([])
            cStart, cFinish = self.handleRhs(children[1])
            self.nfa[2][start].append((EMPTY, cStart))
            self.nfa[2][cFinish].append((EMPTY, finish))
            assert (len(children) == 3) and (children[2][0][0] == token.RSQB)
        return start, finish

    # ____________________________________________________________
    def handleAtom (self, ast):
        """PyPgen.handleAtom()
        """
        nodeType, children = ast
        assert nodeType == parser.ATOM
        assert type(children[0][0]) == type(())
        tokType, tokName, lineno = children[0][0]
        if tokType == token.LPAR:
            start, finish = self.handleRhs(children[1])
            assert (len(children) == 3) and (children[2][0][0] == token.RPAR)
        elif tokType in (token.STRING, token.NAME):
            start = len(self.nfa[2])
            finish = start + 1
            labelIndex = self.addLabel(self.nfaGrammar[1], tokType, tokName)
            self.nfa[2].append([(labelIndex, finish)])
            self.nfa[2].append([])
        else:
            assert 1 == 0, "Malformed pgen parse tree."
        return start, finish

    # ____________________________________________________________
    def generateDfaGrammar (self, nfaGrammar, start_symbol = None):
        """PyPgen.makeDfaGrammar()
        See notes in pypgen.dfa for output schema.
        """
        dfas = []
        for nfa in nfaGrammar[0]:
            dfas.append(self.nfaToDfa(nfa))
        start_symbol_type = dfas[0][0]
        if start_symbol is not None:
            found = False
            for dfa in dfas:
                if dfa[1] == start_symbol:
                    start_symbol_type = dfa[0]
                    found = True
                    break
            if not found:
                print("PyPgen: Warning, couldn't find nonterminal '%s', "
                      "using '%s' instead." % (start_symbol, dfas[0][1]))
        return [dfas, nfaGrammar[1][:], start_symbol_type, 0]

    # ____________________________________________________________
    def addClosure (self, stateList, nfa, istate):
        stateList[istate] = True
        arcs = nfa[2][istate]
        for label, arrow in arcs:
            if label == EMPTY:
                self.addClosure(stateList, nfa, arrow)

    # ____________________________________________________________
    def nfaToDfa (self, nfa):
        """PyPgen.nfaToDfa()
        """
        tempStates = []
        # tempState := [ stateList : List of Boolean,
        #                arcList : List of tempArc ]
        crntTempState = [[False] * len(nfa[2]), [], False]
        self.addClosure(crntTempState[0], nfa, nfa[3])
        crntTempState[2] = crntTempState[0][nfa[4]]
        if crntTempState[2]:
            print("PyPgen: Warning, nonterminal '%s' may produce empty." %
                  (nfa[1]))
        tempStates.append(crntTempState)
        index = 0
        while index < len(tempStates):
            crntTempState = tempStates[index]
            for componentState in range(0, len(nfa[2])):
                if not crntTempState[0][componentState]:
                    continue
                nfaArcs = nfa[2][componentState]
                for label, nfaArrow in nfaArcs:
                    if label == EMPTY:
                        continue
                    foundTempArc = False
                    for tempArc in crntTempState[1]:
                        if tempArc[0] == label:
                            foundTempArc = True
                            break
                    if not foundTempArc:
                        tempArc = [label, -1, [False] * len(nfa[2])]
                        crntTempState[1].append(tempArc)
                    self.addClosure(tempArc[2], nfa, nfaArrow)
            for arcIndex in range(0, len(crntTempState[1])):
                label, arrow, targetStateList = crntTempState[1][arcIndex]
                targetFound = False
                arrow = 0
                for destTempState in tempStates:
                    if targetStateList == destTempState[0]:
                        targetFound = True
                        break
                    arrow += 1
                if not targetFound:
                    assert arrow == len(tempStates)
                    tempState = [targetStateList[:], [],
                                 targetStateList[nfa[4]]]
                    tempStates.append(tempState)
                # Write arrow value back to the arc
                crntTempState[1][arcIndex][1] = arrow
            index += 1
        tempStates = self.simplifyTempDfa(nfa, tempStates)
        return self.tempDfaToDfa(nfa, tempStates)

    # ____________________________________________________________
    def sameState (self, s1, s2):
        """PyPgen.sameState()
        """
        if (len(s1[1]) != len(s2[1])) or (s1[2] != s2[2]):
            return False
        for arcIndex in range(0, len(s1[1])):
            arc1 = s1[1][arcIndex]
            arc2 = s2[1][arcIndex]
            if arc1[:-1] != arc2[:-1]:
                return False
        return True

    # ____________________________________________________________
    def simplifyTempDfa (self, nfa, tempStates):
        """PyPgen.simplifyDfa()
        """
        if __DEBUG__:
            print("_" * 70)
            pprint.pprint(nfa)
            pprint.pprint(tempStates)
        changes = True
        deletedStates = []
        while changes:
            changes = False
            for i in range(1, len(tempStates)):
                if i in deletedStates:
                    continue
                for j in range(0, i):
                    if j in deletedStates:
                        continue
                    if self.sameState(tempStates[i], tempStates[j]):
                        deletedStates.append(i)
                        for k in range(0, len(tempStates)):
                            if k in deletedStates:
                                continue
                            for arc in tempStates[k][1]:
                                if arc[1] == i:
                                    arc[1] = j
                        changes = True
                        break
        for stateIndex in deletedStates:
            tempStates[stateIndex] = None
        if __DEBUG__:
            pprint.pprint(tempStates)
        return tempStates

    # ____________________________________________________________
    def tempDfaToDfa (self, nfa, tempStates):
        """PyPgen.tempDfaToDfa()
        """
        dfaStates = []
        dfa = [nfa[0], nfa[1], 0, dfaStates, None]
        stateMap = {}
        tempIndex = 0
        for tempState in tempStates:
            if None != tempState:
                stateMap[tempIndex] = len(dfaStates)
                dfaStates.append(([], (0,0,()), 0))
            tempIndex += 1
        for tempIndex in stateMap.keys():
            stateList, tempArcs, accepting = tempStates[tempIndex]
            dfaStateIndex = stateMap[tempIndex]
            dfaState = dfaStates[dfaStateIndex]
            for tempArc in tempArcs:
                dfaState[0].append((tempArc[0], stateMap[tempArc[1]]))
            if accepting:
                dfaState[0].append((EMPTY, dfaStateIndex))
        return dfa

    # ____________________________________________________________
    def translateLabels (self, grammar, additional_tokens = None):
        """PyPgen.translateLabels()
        """
        tokenNames = list(token.tok_name.values())
        # Recipe 252143 (remixed for laziness)
        tokenValues = dict(([v, k] for k, v in token.tok_name.items()))
        if additional_tokens:
            tokenNames.extend(additional_tokens.keys())
            tokenValues.update(additional_tokens)
        labelList = grammar[1]
        for labelIndex in range(0, len(labelList)):
            type, name = labelList[labelIndex]
            if type == token.NAME:
                isNonTerminal = False
                for dfa in grammar[0]:
                    if dfa[1] == name:
                        labelList[labelIndex] = (dfa[0], None)
                        isNonTerminal = True
                        break
                if not isNonTerminal:
                    if __DEBUG__:
                        print(tokenNames)
                    if name in tokenNames:
                        labelList[labelIndex] = (tokenValues[name], None)
                    else:
                        print("Can't translate NAME label '%s'" % name)
            elif type == token.STRING:
                assert name[0] == name[-1]
                sname = name[1:-1]
                if (sname[0] in ascii_letters) or (sname[0] == "_"):
                    labelList[labelIndex] = (token.NAME, sname)
                elif sname in self.operatorMap:
                    labelList[labelIndex] = (self.operatorMap[sname],
                                             None)
                else:
                    print("Can't translate STRING label %s" % name)
        return grammar

    # ____________________________________________________________
    def calcFirstSet (self, grammar, dfa):
        """PyPgen.calcFirstSet()
        """
        if dfa[4] == long(-1):
            print("Left-recursion for '%s'" % dfa[1])
            return
        if dfa[4] != None:
            print("Re-calculating FIRST set for '%s' ???" % dfa[1])
        dfa[4] = long(-1)
        symbols = []
        result = long(0)
        state = dfa[3][dfa[2]]
        for arc in state[0]:
            sym = arc[0]
            if sym not in symbols:
                symbols.append(sym)
                type = grammar[1][sym][0]
                if (type >= token.NT_OFFSET):
                    # Nonterminal
                    ddfa = grammar[0][type - token.NT_OFFSET]
                    if ddfa[4] == long(-1):
                        print("Left recursion below '%s'" % dfa[1])
                    else:
                        if ddfa[4] == None:
                            self.calcFirstSet(grammar, ddfa)
                        result |= ddfa[4]
                else:
                    result |= (long(1) << sym)
        dfa[4] = result

    # ____________________________________________________________
    def generateFirstSets (self, grammar):
        """PyPgen.generateFirstSets()
        """
        dfas = grammar[0]
        index = 0
        while index < len(dfas):
            dfa = dfas[index]
            if None == dfa[4]:
                self.calcFirstSet(grammar, dfa)
            index += 1
        for dfa in dfas:
            set = dfa[4]
            resultStr = ''
            while set > long(0):
                crntBits = set & 0xff
                resultStr += chr(crntBits)
                set >>= 8
            properSize = ((len(grammar[1]) // 8) + 1)
            if len(resultStr) < properSize:
                resultStr += ('\x00' * (properSize - len(resultStr)))
            dfa[4] = resultStr
        return grammar

    # ____________________________________________________________
    def __call__ (self, ast):
        """PyPgen.__call__()
        """
        nfaGrammar = self.handleStart(ast)
        grammar = self.generateDfaGrammar(nfaGrammar)
        self.translateLabels(grammar)
        self.generateFirstSets(grammar)
        grammar[0] = [tuple(elem) for elem in grammar[0]]
        #grammar[0] = map(tuple, grammar[0])
        return tuple(grammar)

# ______________________________________________________________________

class PyPgenParser (object):
    """Class PyPgenParser

    Wrapper class for parsers generated by PyPgen.  Mirrors the pgenParser
    type of the pgen extension module.
    """
    # ____________________________________________________________
    def __init__ (self, grammarObj, tokenizer_cls=None):
        """PyPgenParser.__init__
        Constructor; accepts a DFA tuple (currently documented in
        pypgen.dfa.__doc__).
        """
        self.grammarObj = grammarObj
        self.start = grammarObj[2]
        self.stringMap = None
        self.symbolMap = None
        if None == tokenizer_cls:
            tokenizer_cls = tokenizer.Tokenizer
        self.tokenizer_cls = tokenizer_cls

    # ____________________________________________________________
    def getStart (self):
        """PyPgenParser.getStart
        Return the current start symbol.
        """
        return self.start

    # ____________________________________________________________
    def setStart (self, start):
        """PyPgenParser.setStart
        """
        self.start = start

    # ____________________________________________________________
    def parseTokens (self, tokenizer):
        """PyPgenParser.parseTokens
        Method that takes a tokenizer and the current DFA and returns a parse
        tree.
        """
        return dfa.parsetok(tokenizer, self.grammarObj, self.start)

    # ____________________________________________________________
    def parseFile (self, filename):
        """PyPgenParser.parseFile
        Accepts filename, returns parse tree.
        """
        with open(filename) as fileobj:
            tokenizer = self.tokenizer_cls().tokenize(fileobj)
            ret_val = self.parseTokens(tokenizer)
        return ret_val

    # ____________________________________________________________
    def parseString (self, in_string):
        """PyPgenParser.parseString
        Accepts input string, return parse tree.
        """
        tokenizer = self.tokenizer_cls().tokenizeString(in_string)
        return self.parseTokens(tokenizer)

    # ____________________________________________________________
    def stringToSymbolMap (self):
        """PyPgenParser.stringToSymbolMap
        """
        if None == self.stringMap:
            self.stringMap = {}
            for dfa in self.grammarObj[0]:
                dfaType, dfaName = dfa[:2]
                self.stringMap[dfaName] = dfaType
        return self.stringMap

    # ____________________________________________________________
    def symbolToStringMap (self):
        """PyPgenParser.symbolToStringMap
        """
        if None == self.symbolMap:
            self.symbolMap = {}
            for dfa in self.grammarObj[0]:
                dfaType, dfaName = dfa[:2]
                self.symbolMap[dfaType] = dfaName
        return self.symbolMap

    # ____________________________________________________________
    def toTuple (self):
        """PyPgenParser.toTuple
        """
        return self.grammarObj

# ______________________________________________________________________

def buildParser (grammarST, tokenizer_cls=None, **kws):
    """buildParser
    """
    global __DEBUG__
    if "DEBUG" in kws:
        __DEBUG__ = True
    if None == tokenizer_cls:
        tokenizer_cls = tokenizer.Tokenizer
    pgenObj = PyPgen(tokenizer_cls.operatorMap, **kws)
    return PyPgenParser(pgenObj(grammarST), tokenizer_cls)

# ______________________________________________________________________

def parserMain (gObj):
    """parserMain()
    Main routine for the default CLI for PyPgen generated parsers.
    """
    import getopt
    inputFile = None
    outputFile = None
    graphicalOutput = False
    # ____________________________________________________________
    opts, args = getopt.getopt(sys.argv[1:], "gi:o:")
    for (opt_flag, opt_arg) in opts:
        if opt_flag == "-i":
            inputFile = opt_arg
        elif opt_flag == "-o":
            outputFile = opt_arg
    # ____________________________________________________________
    parser = PyPgenParser(gObj)
    if inputFile != None:
        st = parser.parse_file(inputFile)
    else:
        st = parser.parse_string(sys.stdin.read())
    if outputFile == None:
        outputFileObj = sys.stdout
    else:
        outputFileObj = open(outputFile, "w")
    pprint.pprint(st, outputFileObj)

# ______________________________________________________________________

def main(*args):
    # ____________________________________________________________
    # Generate a test parser
    assert len(args) > 0
    grammarFile = args[0]
    grammarST = parser.parse_file(grammarFile)
    generated_parser = buildParser(grammarST)
    pprint.pprint(generated_parser.toTuple())
    # ____________________________________________________________
    # Parse some input
    if len(args) > 1:
        inputFile = args[1]
        fileObj = open(inputFile)
    else:
        inputFile = "<stdin>"
        fileObj = sys.stdin
    tokenizer_obj = tokenizer.Tokenizer().tokenize(fileObj)
    generated_parser.setStart(257)
    parseTree = generated_parser.parseTokens(tokenizer_obj)
    fileObj.close()
    # ____________________________________________________________
    # Show the result
    pprint.pprint(parseTree)

# ______________________________________________________________________

if __name__ == "__main__":
    main(*(sys.argv[1:]))

# ______________________________________________________________________
# End of pypgen.pgen
