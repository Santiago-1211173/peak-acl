# Generated from grammar/ACL.g4 by ANTLR 4.13.2
from antlr4 import *
from io import StringIO
import sys
if sys.version_info[1] > 5:
    from typing import TextIO
else:
    from typing.io import TextIO


def serializedATN():
    return [
        4,0,6,44,6,-1,2,0,7,0,2,1,7,1,2,2,7,2,2,3,7,3,2,4,7,4,2,5,7,5,1,
        0,1,0,1,1,1,1,1,2,1,2,1,3,1,3,1,3,1,3,5,3,24,8,3,10,3,12,3,27,9,
        3,1,3,1,3,1,4,1,4,5,4,33,8,4,10,4,12,4,36,9,4,1,5,4,5,39,8,5,11,
        5,12,5,40,1,5,1,5,0,0,6,1,1,3,2,5,3,7,4,9,5,11,6,1,0,3,2,0,34,34,
        92,92,6,0,43,43,45,58,64,90,92,92,95,95,97,122,3,0,9,10,13,13,32,
        32,47,0,1,1,0,0,0,0,3,1,0,0,0,0,5,1,0,0,0,0,7,1,0,0,0,0,9,1,0,0,
        0,0,11,1,0,0,0,1,13,1,0,0,0,3,15,1,0,0,0,5,17,1,0,0,0,7,19,1,0,0,
        0,9,30,1,0,0,0,11,38,1,0,0,0,13,14,5,40,0,0,14,2,1,0,0,0,15,16,5,
        41,0,0,16,4,1,0,0,0,17,18,5,58,0,0,18,6,1,0,0,0,19,25,5,34,0,0,20,
        24,8,0,0,0,21,22,5,92,0,0,22,24,9,0,0,0,23,20,1,0,0,0,23,21,1,0,
        0,0,24,27,1,0,0,0,25,23,1,0,0,0,25,26,1,0,0,0,26,28,1,0,0,0,27,25,
        1,0,0,0,28,29,5,34,0,0,29,8,1,0,0,0,30,34,7,1,0,0,31,33,7,1,0,0,
        32,31,1,0,0,0,33,36,1,0,0,0,34,32,1,0,0,0,34,35,1,0,0,0,35,10,1,
        0,0,0,36,34,1,0,0,0,37,39,7,2,0,0,38,37,1,0,0,0,39,40,1,0,0,0,40,
        38,1,0,0,0,40,41,1,0,0,0,41,42,1,0,0,0,42,43,6,5,0,0,43,12,1,0,0,
        0,5,0,23,25,34,40,1,6,0,0
    ]

class ACLLexer(Lexer):

    atn = ATNDeserializer().deserialize(serializedATN())

    decisionsToDFA = [ DFA(ds, i) for i, ds in enumerate(atn.decisionToState) ]

    LPAREN = 1
    RPAREN = 2
    COLON = 3
    STRING = 4
    SYMBOL = 5
    WS = 6

    channelNames = [ u"DEFAULT_TOKEN_CHANNEL", u"HIDDEN" ]

    modeNames = [ "DEFAULT_MODE" ]

    literalNames = [ "<INVALID>",
            "'('", "')'", "':'" ]

    symbolicNames = [ "<INVALID>",
            "LPAREN", "RPAREN", "COLON", "STRING", "SYMBOL", "WS" ]

    ruleNames = [ "LPAREN", "RPAREN", "COLON", "STRING", "SYMBOL", "WS" ]

    grammarFileName = "ACL.g4"

    def __init__(self, input=None, output:TextIO = sys.stdout):
        super().__init__(input, output)
        self.checkVersion("4.13.2")
        self._interp = LexerATNSimulator(self, self.atn, self.decisionsToDFA, PredictionContextCache())
        self._actions = None
        self._predicates = None


