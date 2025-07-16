# src/peak_acl/serialize.py
"""
Serialização de objetos peak_acl → string FIPA ACL.

- Gera sintaxe que o JADE aceita.
- Todos os campos FIPA suportados (ver message.acl.AclMessage).
- :content é SEMPRE colocado entre aspas, como praticado pelo DF/JADE,
  porque o DF espera a expressão SL0 citada. (Se precisares de conteúdo
  não-quoted noutros cenários, abre uma flag no futuro.)

Notas:
• Para SL0 (Action, Register, etc.) usamos peak_acl.sl0.dumps().
• Para AclMessage aninhada chamamos recursivamente dumps().
"""

from __future__ import annotations

from typing import Any, Iterable

from .message.acl import AclMessage
from .message.aid import AgentIdentifier

from . import sl0


# --------------------------------------------------------------------------- #
#  Helpers
# --------------------------------------------------------------------------- #
def _aid_to_fipa(aid: AgentIdentifier) -> str:
    addrs = " ".join(aid.addresses) if aid.addresses else ""
    seq = f"(sequence {addrs})" if addrs else "(sequence)"
    return f"(agent-identifier :name {aid.name} :addresses {seq})"


def _content_to_str(c: Any) -> str:
    """
    Converte o campo content num *texto* que será colocado entre aspas
    pelo serializer principal.
    """
    # Conteúdo SL0 (Action, Register, etc.)
    if isinstance(
        c,
        (
            sl0.Action, sl0.Register, sl0.Deregister, sl0.Modify,
            sl0.Search, sl0.Done, sl0.Failure,
            sl0.DfAgentDescription, sl0.ServiceDescription,
        ),
    ):
        return sl0.dumps(c)

    # Mensagem ACL aninhada (raro, mas suportado)
    if isinstance(c, AclMessage):
        return dumps(c)

    # Já é string -> devolve tal qual (tirando aspas exteriores se houver)
    if isinstance(c, str):
        # remover aspas exteriores caso user tenha passado '"...'"
        if len(c) >= 2 and c[0] == '"' and c[-1] == '"':
            return c[1:-1]
        return c

    # Fallback genérico
    return str(c)


# --------------------------------------------------------------------------- #
#  ACL serializer principal
# --------------------------------------------------------------------------- #
def dumps(msg: AclMessage) -> str:
    p = msg.performative_upper
    parts = [f"({p}"]

    if msg.sender:
        parts.append(f" :sender {_aid_to_fipa(msg.sender)}")

    if msg.receivers:
        recs = " ".join(_aid_to_fipa(a) for a in msg.receivers)
        parts.append(f" :receiver (set {recs})")

    if msg.reply_to:
        rts = " ".join(_aid_to_fipa(a) for a in msg.reply_to)
        parts.append(f" :reply-to (set {rts})")

    if msg.content is not None:
        c = _content_to_str(msg.content)
        # Escape aspas duplas internas
        c = c.replace('"', '\\"')
        parts.append(f' :content "{c}"')

    if msg.language:
        parts.append(f" :language {msg.language}")
    if msg.encoding:
        parts.append(f" :encoding {msg.encoding}")
    if msg.ontology:
        parts.append(f" :ontology {msg.ontology}")
    if msg.protocol:
        parts.append(f" :protocol {msg.protocol}")
    if msg.conversation_id:
        parts.append(f" :conversation-id {msg.conversation_id}")
    if msg.reply_with:
        parts.append(f" :reply-with {msg.reply_with}")
    if msg.in_reply_to:
        parts.append(f" :in-reply-to {msg.in_reply_to}")
    if msg.reply_by:
        parts.append(f" :reply-by {msg.reply_by.strftime('%Y%m%dT%H%M%S')}")

    # extensões
    for k, v in msg.user_params.items():
        parts.append(f" :{k} {v}")

    parts.append(")")
    return "".join(parts)
