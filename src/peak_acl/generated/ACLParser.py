# Generated from grammar/ACL.g4 by ANTLR 4.13.2
# encoding: utf-8
from antlr4 import *
from io import StringIO
import sys
if sys.version_info[1] > 5:
	from typing import TextIO
else:
	from typing.io import TextIO

def serializedATN():
    return [
        4,1,6,38,2,0,7,0,2,1,7,1,2,2,7,2,2,3,7,3,1,0,1,0,1,0,5,0,12,8,0,
        10,0,12,0,15,9,0,1,0,1,0,1,1,1,1,1,2,1,2,1,2,1,2,1,3,1,3,1,3,1,3,
        1,3,4,3,30,8,3,11,3,12,3,31,1,3,1,3,3,3,36,8,3,1,3,0,0,4,0,2,4,6,
        0,0,38,0,8,1,0,0,0,2,18,1,0,0,0,4,20,1,0,0,0,6,35,1,0,0,0,8,9,5,
        1,0,0,9,13,3,2,1,0,10,12,3,4,2,0,11,10,1,0,0,0,12,15,1,0,0,0,13,
        11,1,0,0,0,13,14,1,0,0,0,14,16,1,0,0,0,15,13,1,0,0,0,16,17,5,2,0,
        0,17,1,1,0,0,0,18,19,5,5,0,0,19,3,1,0,0,0,20,21,5,3,0,0,21,22,5,
        5,0,0,22,23,3,6,3,0,23,5,1,0,0,0,24,36,5,5,0,0,25,36,5,4,0,0,26,
        36,3,0,0,0,27,29,5,1,0,0,28,30,3,6,3,0,29,28,1,0,0,0,30,31,1,0,0,
        0,31,29,1,0,0,0,31,32,1,0,0,0,32,33,1,0,0,0,33,34,5,2,0,0,34,36,
        1,0,0,0,35,24,1,0,0,0,35,25,1,0,0,0,35,26,1,0,0,0,35,27,1,0,0,0,
        36,7,1,0,0,0,3,13,31,35
    ]

class ACLParser ( Parser ):

    grammarFileName = "ACL.g4"

    atn = ATNDeserializer().deserialize(serializedATN())

    decisionsToDFA = [ DFA(ds, i) for i, ds in enumerate(atn.decisionToState) ]

    sharedContextCache = PredictionContextCache()

    literalNames = [ "<INVALID>", "'('", "')'", "':'" ]

    symbolicNames = [ "<INVALID>", "LPAREN", "RPAREN", "COLON", "STRING", 
                      "SYMBOL", "WS" ]

    RULE_message = 0
    RULE_performative = 1
    RULE_param = 2
    RULE_value = 3

    ruleNames =  [ "message", "performative", "param", "value" ]

    EOF = Token.EOF
    LPAREN=1
    RPAREN=2
    COLON=3
    STRING=4
    SYMBOL=5
    WS=6

    def __init__(self, input:TokenStream, output:TextIO = sys.stdout):
        super().__init__(input, output)
        self.checkVersion("4.13.2")
        self._interp = ParserATNSimulator(self, self.atn, self.decisionsToDFA, self.sharedContextCache)
        self._predicates = None




    class MessageContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser


        def getRuleIndex(self):
            return ACLParser.RULE_message

     
        def copyFrom(self, ctx:ParserRuleContext):
            super().copyFrom(ctx)



    class ACLmessageContext(MessageContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a ACLParser.MessageContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def LPAREN(self):
            return self.getToken(ACLParser.LPAREN, 0)
        def performative(self):
            return self.getTypedRuleContext(ACLParser.PerformativeContext,0)

        def RPAREN(self):
            return self.getToken(ACLParser.RPAREN, 0)
        def param(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(ACLParser.ParamContext)
            else:
                return self.getTypedRuleContext(ACLParser.ParamContext,i)


        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterACLmessage" ):
                listener.enterACLmessage(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitACLmessage" ):
                listener.exitACLmessage(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitACLmessage" ):
                return visitor.visitACLmessage(self)
            else:
                return visitor.visitChildren(self)



    def message(self):

        localctx = ACLParser.MessageContext(self, self._ctx, self.state)
        self.enterRule(localctx, 0, self.RULE_message)
        self._la = 0 # Token type
        try:
            localctx = ACLParser.ACLmessageContext(self, localctx)
            self.enterOuterAlt(localctx, 1)
            self.state = 8
            self.match(ACLParser.LPAREN)
            self.state = 9
            self.performative()
            self.state = 13
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==3:
                self.state = 10
                self.param()
                self.state = 15
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 16
            self.match(ACLParser.RPAREN)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class PerformativeContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser


        def getRuleIndex(self):
            return ACLParser.RULE_performative

     
        def copyFrom(self, ctx:ParserRuleContext):
            super().copyFrom(ctx)



    class ACLperformativeContext(PerformativeContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a ACLParser.PerformativeContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def SYMBOL(self):
            return self.getToken(ACLParser.SYMBOL, 0)

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterACLperformative" ):
                listener.enterACLperformative(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitACLperformative" ):
                listener.exitACLperformative(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitACLperformative" ):
                return visitor.visitACLperformative(self)
            else:
                return visitor.visitChildren(self)



    def performative(self):

        localctx = ACLParser.PerformativeContext(self, self._ctx, self.state)
        self.enterRule(localctx, 2, self.RULE_performative)
        try:
            localctx = ACLParser.ACLperformativeContext(self, localctx)
            self.enterOuterAlt(localctx, 1)
            self.state = 18
            self.match(ACLParser.SYMBOL)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ParamContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser


        def getRuleIndex(self):
            return ACLParser.RULE_param

     
        def copyFrom(self, ctx:ParserRuleContext):
            super().copyFrom(ctx)



    class ACLparamContext(ParamContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a ACLParser.ParamContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def COLON(self):
            return self.getToken(ACLParser.COLON, 0)
        def SYMBOL(self):
            return self.getToken(ACLParser.SYMBOL, 0)
        def value(self):
            return self.getTypedRuleContext(ACLParser.ValueContext,0)


        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterACLparam" ):
                listener.enterACLparam(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitACLparam" ):
                listener.exitACLparam(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitACLparam" ):
                return visitor.visitACLparam(self)
            else:
                return visitor.visitChildren(self)



    def param(self):

        localctx = ACLParser.ParamContext(self, self._ctx, self.state)
        self.enterRule(localctx, 4, self.RULE_param)
        try:
            localctx = ACLParser.ACLparamContext(self, localctx)
            self.enterOuterAlt(localctx, 1)
            self.state = 20
            self.match(ACLParser.COLON)
            self.state = 21
            self.match(ACLParser.SYMBOL)
            self.state = 22
            self.value()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ValueContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser


        def getRuleIndex(self):
            return ACLParser.RULE_value

     
        def copyFrom(self, ctx:ParserRuleContext):
            super().copyFrom(ctx)



    class ListValueContext(ValueContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a ACLParser.ValueContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def LPAREN(self):
            return self.getToken(ACLParser.LPAREN, 0)
        def RPAREN(self):
            return self.getToken(ACLParser.RPAREN, 0)
        def value(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(ACLParser.ValueContext)
            else:
                return self.getTypedRuleContext(ACLParser.ValueContext,i)


        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterListValue" ):
                listener.enterListValue(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitListValue" ):
                listener.exitListValue(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitListValue" ):
                return visitor.visitListValue(self)
            else:
                return visitor.visitChildren(self)


    class StringContext(ValueContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a ACLParser.ValueContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def STRING(self):
            return self.getToken(ACLParser.STRING, 0)

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterString" ):
                listener.enterString(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitString" ):
                listener.exitString(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitString" ):
                return visitor.visitString(self)
            else:
                return visitor.visitChildren(self)


    class AtomContext(ValueContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a ACLParser.ValueContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def SYMBOL(self):
            return self.getToken(ACLParser.SYMBOL, 0)

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterAtom" ):
                listener.enterAtom(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitAtom" ):
                listener.exitAtom(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitAtom" ):
                return visitor.visitAtom(self)
            else:
                return visitor.visitChildren(self)


    class NestedMessageContext(ValueContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a ACLParser.ValueContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def message(self):
            return self.getTypedRuleContext(ACLParser.MessageContext,0)


        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterNestedMessage" ):
                listener.enterNestedMessage(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitNestedMessage" ):
                listener.exitNestedMessage(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitNestedMessage" ):
                return visitor.visitNestedMessage(self)
            else:
                return visitor.visitChildren(self)



    def value(self):

        localctx = ACLParser.ValueContext(self, self._ctx, self.state)
        self.enterRule(localctx, 6, self.RULE_value)
        self._la = 0 # Token type
        try:
            self.state = 35
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,2,self._ctx)
            if la_ == 1:
                localctx = ACLParser.AtomContext(self, localctx)
                self.enterOuterAlt(localctx, 1)
                self.state = 24
                self.match(ACLParser.SYMBOL)
                pass

            elif la_ == 2:
                localctx = ACLParser.StringContext(self, localctx)
                self.enterOuterAlt(localctx, 2)
                self.state = 25
                self.match(ACLParser.STRING)
                pass

            elif la_ == 3:
                localctx = ACLParser.NestedMessageContext(self, localctx)
                self.enterOuterAlt(localctx, 3)
                self.state = 26
                self.message()
                pass

            elif la_ == 4:
                localctx = ACLParser.ListValueContext(self, localctx)
                self.enterOuterAlt(localctx, 4)
                self.state = 27
                self.match(ACLParser.LPAREN)
                self.state = 29 
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                while True:
                    self.state = 28
                    self.value()
                    self.state = 31 
                    self._errHandler.sync(self)
                    _la = self._input.LA(1)
                    if not ((((_la) & ~0x3f) == 0 and ((1 << _la) & 50) != 0)):
                        break

                self.state = 33
                self.match(ACLParser.RPAREN)
                pass


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx





