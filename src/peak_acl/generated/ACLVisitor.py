# Generated from grammar/ACL.g4 by ANTLR 4.13.2
from antlr4 import *
if "." in __name__:
    from .ACLParser import ACLParser
else:
    from ACLParser import ACLParser

# This class defines a complete generic visitor for a parse tree produced by ACLParser.

class ACLVisitor(ParseTreeVisitor):

    # Visit a parse tree produced by ACLParser#ACLmessage.
    def visitACLmessage(self, ctx:ACLParser.ACLmessageContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ACLParser#ACLperformative.
    def visitACLperformative(self, ctx:ACLParser.ACLperformativeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ACLParser#ACLparam.
    def visitACLparam(self, ctx:ACLParser.ACLparamContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ACLParser#Atom.
    def visitAtom(self, ctx:ACLParser.AtomContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ACLParser#String.
    def visitString(self, ctx:ACLParser.StringContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ACLParser#NestedMessage.
    def visitNestedMessage(self, ctx:ACLParser.NestedMessageContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ACLParser#ListValue.
    def visitListValue(self, ctx:ACLParser.ListValueContext):
        return self.visitChildren(ctx)



del ACLParser