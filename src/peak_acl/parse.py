# src/peak_acl/parse.py
from __future__ import annotations

from antlr4 import InputStream, CommonTokenStream

from .generated.ACLLexer import ACLLexer
from .generated.ACLParser import ACLParser
from .visitor import MessageBuilder


def parse(raw: str):
    """
    Converte uma string ACL → objeto AclMessage completo.
    Levanta ValueError em caso de erro sintático.
    """
    stream = InputStream(raw)
    lexer = ACLLexer(stream)
    tokens = CommonTokenStream(lexer)
    parser = ACLParser(tokens)

    tree = parser.message()

    # opcional: verificar se houve erros de parser (token recognition errors)
    if parser.getNumberOfSyntaxErrors() > 0:
        raise ValueError(f"Erro(s) de sintaxe ACL: {parser.getNumberOfSyntaxErrors()}")

    return MessageBuilder(raw).visit(tree)
