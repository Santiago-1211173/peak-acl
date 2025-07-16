# src/peak_acl/visitor.py
"""Visitor ANTLR → AclMessage (modelo completo FIPA)."""

from __future__ import annotations

from typing import Any, Dict, Tuple

from .generated.ACLVisitor import ACLVisitor
from .generated.ACLParser import ACLParser

from .message.acl import AclMessage
from .types import QuotedStr  # mantém compat
from .parse_helpers import to_aid, to_aid_list, to_datetime


# Slots permitidos ao nível raiz (case-insensitive)
ALLOWED_ROOT = {
    "sender", "receiver", "reply-to",
    "content", "language", "encoding", "ontology",
    "protocol", "conversation-id", "reply-with",
    "in-reply-to", "reply-by",
}

# Campos obrigatórios por performativa (mínimo)
MANDATORY_ROOT = {
    "inform": {"content"},
    "request": {"content"},
}


class MessageBuilder(ACLVisitor):
    """
    Percorre a ParseTree produzida por ACLParser e constrói um AclMessage completo.
    Usa _depth para distinguir a mensagem raiz de mensagens aninhadas (AIDs, ações...).
    """

    def __init__(self, raw_text: str) -> None:
        super().__init__()
        self._depth = 0
        self._raw_text = raw_text

    # --------------------------- mensagem ---------------------------------- #
    def visitACLmessage(self, ctx: ACLParser.ACLmessageContext) -> AclMessage:
        self._depth += 1
        try:
            perf = ctx.performative().SYMBOL().getText()
            perf_l = perf.lower()

            # Recolhe params
            params: Dict[str, Any] = {}
            for p_ctx in ctx.param():
                k, v = self.visit(p_ctx)
                params[k] = v

            # Raiz → construir AclMessage estruturado
            if self._depth == 1:
                msg = AclMessage(performative=perf_l, raw_text=self._raw_text)

                missing = MANDATORY_ROOT.get(perf_l, set()) - params.keys()
                if missing:
                    raise ValueError(f"{perf_l} precisa de: {', '.join(missing)}")

                for name, val in params.items():
                    lname = name.lower()
                    if lname == "sender":
                        msg.sender = to_aid(val)
                    elif lname == "receiver":
                        msg.receivers.extend(to_aid_list(val))
                    elif lname == "reply-to":
                        msg.reply_to.extend(to_aid_list(val))
                    elif lname == "content":
                        msg.content = _coerce_content(val)
                    elif lname == "language":
                        msg.language = str(val)
                    elif lname == "encoding":
                        msg.encoding = str(val)
                    elif lname == "ontology":
                        msg.ontology = str(val)
                    elif lname == "protocol":
                        msg.protocol = str(val)
                    elif lname == "conversation-id":
                        msg.conversation_id = str(val)
                    elif lname == "reply-with":
                        msg.reply_with = str(val)
                    elif lname == "in-reply-to":
                        msg.in_reply_to = str(val)
                    elif lname == "reply-by":
                        msg.reply_by = to_datetime(val)
                    else:
                        # extensões
                        msg.user_params[lname] = val
                return msg

            # Mensagem aninhada → devolve AclMessage “genérico” (p/ AID etc.)
            return AclMessage(performative=perf_l, user_params=params)

        finally:
            self._depth -= 1

    # ----------------------- :name value ----------------------------------- #
    def visitACLparam(self, ctx: ACLParser.ACLparamContext) -> Tuple[str, Any]:
        name = ctx.SYMBOL().getText()
        if self._depth == 1:
            lname = name.lower()
            if lname not in ALLOWED_ROOT and not lname.startswith("x-"):
                # aceitaremos silenciosamente para robustez?
                # raise ValueError(...)  # se quiseres estrito
                pass
        value = self.visit(ctx.value())
        return name, value

    # ----------------------- valores --------------------------------------- #
    def visitAtom(self, ctx: ACLParser.AtomContext):
        return ctx.SYMBOL().getText()

    def visitString(self, ctx: ACLParser.StringContext):
        raw = ctx.STRING().getText()  # inclui aspas
        return QuotedStr(bytes(raw[1:-1], "utf-8").decode("unicode_escape"))

    def visitNestedMessage(self, ctx: ACLParser.NestedMessageContext):
        return self.visit(ctx.message())

    def visitListValue(self, ctx: ACLParser.ListValueContext):
        return [self.visit(v) for v in ctx.value()]


# --------------------------------------------------------------------------- #
#  Helpers locais
# --------------------------------------------------------------------------- #
def _coerce_content(val: Any):
    """
    Converte o valor do slot :content num formato amigável:
    - QuotedStr -> str
    - AclMessage -> manter objeto (util para AIDs/ações)
    - lista -> string join
    - atom -> string
    """
    if isinstance(val, QuotedStr):
        return str(val)
    return val
