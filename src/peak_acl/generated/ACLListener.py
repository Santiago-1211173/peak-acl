# Generated from grammar/ACL.g4 by ANTLR 4.13.2
from antlr4 import *
if "." in __name__:
    from .ACLParser import ACLParser
else:
    from ACLParser import ACLParser

# This class defines a complete listener for a parse tree produced by ACLParser.
class ACLListener(ParseTreeListener):

    # Enter a parse tree produced by ACLParser#ACLmessage.
    def enterACLmessage(self, ctx:ACLParser.ACLmessageContext):
        pass

    # Exit a parse tree produced by ACLParser#ACLmessage.
    def exitACLmessage(self, ctx:ACLParser.ACLmessageContext):
        pass


    # Enter a parse tree produced by ACLParser#ACLperformative.
    def enterACLperformative(self, ctx:ACLParser.ACLperformativeContext):
        pass

    # Exit a parse tree produced by ACLParser#ACLperformative.
    def exitACLperformative(self, ctx:ACLParser.ACLperformativeContext):
        pass


    # Enter a parse tree produced by ACLParser#ACLparam.
    def enterACLparam(self, ctx:ACLParser.ACLparamContext):
        pass

    # Exit a parse tree produced by ACLParser#ACLparam.
    def exitACLparam(self, ctx:ACLParser.ACLparamContext):
        pass


    # Enter a parse tree produced by ACLParser#Atom.
    def enterAtom(self, ctx:ACLParser.AtomContext):
        pass

    # Exit a parse tree produced by ACLParser#Atom.
    def exitAtom(self, ctx:ACLParser.AtomContext):
        pass


    # Enter a parse tree produced by ACLParser#String.
    def enterString(self, ctx:ACLParser.StringContext):
        pass

    # Exit a parse tree produced by ACLParser#String.
    def exitString(self, ctx:ACLParser.StringContext):
        pass


    # Enter a parse tree produced by ACLParser#NestedMessage.
    def enterNestedMessage(self, ctx:ACLParser.NestedMessageContext):
        pass

    # Exit a parse tree produced by ACLParser#NestedMessage.
    def exitNestedMessage(self, ctx:ACLParser.NestedMessageContext):
        pass


    # Enter a parse tree produced by ACLParser#ListValue.
    def enterListValue(self, ctx:ACLParser.ListValueContext):
        pass

    # Exit a parse tree produced by ACLParser#ListValue.
    def exitListValue(self, ctx:ACLParser.ListValueContext):
        pass



del ACLParser