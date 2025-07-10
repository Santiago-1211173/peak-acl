# src/peak_acl/visitor.py
"""Visitor que transforma a ParseTree ANTLR → AclMessage com validação leve."""

from __future__ import annotations

from .generated.ACLVisitor import ACLVisitor         
from .generated.ACLParser import ACLParser
from .message.acl import AclMessage
from .types import QuotedStr

# ─────────────────── PARÂMETROS DE PRIMEIRO NÍVEL ──────────────────────────
ALLOWED_ROOT = {
    # ‘Interface’ FIPA ACL
    "sender", "receiver", "reply-to",
    "content", "language", "encoding", "ontology",
    "protocol", "conversation-id", "reply-with",
    "in-reply-to", "reply-by",
}

MANDATORY_ROOT = {
    "inform":  {"content"},
    "request": {"content"},
}

class MessageBuilder(ACLVisitor):
    """
    Percorre a árvore ANTLR (ACLmessage  → param → value) e devolve um
    AclMessage; valida apenas a *camada de cabeçalho* da mensagem.
    """
    # usamos _depth para distinguir raiz (depth==1) de mensagens aninhadas
    def __init__(self) -> None:
        super().__init__()
        self._depth = 0              

    # ─────────────────────────── mensagem ────────────────────────────────
    def visitACLmessage(self, ctx: ACLParser.ACLmessageContext) -> AclMessage:
        self._depth += 1               # entra numa nova mensagem
        try:
            perf = ctx.performative().SYMBOL().getText().lower()

            params: dict[str, object] = {}
            for p_ctx in ctx.param():
                key, val = self.visit(p_ctx)          
                params[key] = val

            # valida obrigatórios apenas na raiz
            if self._depth == 1:
                missing = MANDATORY_ROOT.get(perf, set()) - params.keys()
                if missing:
                    raise ValueError(f"{perf} precisa de: {', '.join(missing)}")

            return AclMessage(performative=perf, params=params)
        finally:
            self._depth -= 1             # sai da mensagem, restaura profundidade

    # ─────────────────────────── :name value ─────────────────────────────
    def visitACLparam(self, ctx: ACLParser.ACLparamContext):
        name = ctx.SYMBOL().getText()
        # só valida nome se estamos na mensagem de topo
        if self._depth == 1 and name not in ALLOWED_ROOT and not name.startswith("X-"):
            raise ValueError(f"Parâmetro não permitido: {name}")

        value = self.visit(ctx.value())
        return name, value

    # ─────────────────────────── valores ─────────────────────────────────
    def visitAtom(self, ctx: ACLParser.AtomContext):
        return ctx.SYMBOL().getText()

    def visitString(self, ctx: ACLParser.StringContext):
        raw = ctx.STRING().getText()               # "\"hi\""
        return QuotedStr(bytes(raw[1:-1], "utf-8").decode("unicode_escape"))

    def visitNestedMessage(self, ctx: ACLParser.NestedMessageContext):
        return self.visit(ctx.message())

    def visitListValue(self, ctx: ACLParser.ListValueContext):
        return [self.visit(v) for v in ctx.value()]
