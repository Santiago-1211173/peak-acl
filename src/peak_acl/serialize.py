# src/peak_acl/serialize.py
from __future__ import annotations

from .message.acl import AclMessage
from .message.aid import AgentIdentifier

def _aid_to_fipa(aid: AgentIdentifier) -> str:
    addrs = " ".join(aid.addresses) if aid.addresses else ""
    seq = f"(sequence {addrs})" if addrs else "(sequence)"
    return f"(agent-identifier :name {aid.name} :addresses {seq})"

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
        # formato simples YYYYMMDDTHHMMSS (ajusta conforme necessário)
        parts.append(f" :reply-by {msg.reply_by.strftime('%Y%m%dT%H%M%S')}")

    # extensões
    for k, v in msg.user_params.items():
        parts.append(f" :{k} {v}")

    parts.append(")")
    return "".join(parts)

def _content_to_str(c) -> str:
    if isinstance(c, AclMessage):
        from .serialize import dumps as _d  # evitar import circular se chamado acima
        return _d(c)
    return str(c).replace('"', '\\"')
