# src/peak_acl/parse.py
from antlr4 import InputStream, CommonTokenStream
from .generated.ACLLexer import ACLLexer
from .generated.ACLParser import ACLParser
from .visitor import MessageBuilder

def parse(raw: str):
    """Converte uma string ACL → objeto AclMessage."""
    stream  = InputStream(raw)
    lexer   = ACLLexer(stream)
    tokens  = CommonTokenStream(lexer)
    parser  = ACLParser(tokens)

    tree    = parser.message()              # ParseTree
    return MessageBuilder().visit(tree)     # ← devolve AclMessage
