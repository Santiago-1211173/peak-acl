"""
peak_acl.events
===============

Estruturas de alto‑nível para o *routing* de mensagens recebidas
via HTTP‑MTP.  O utilizador final (agente) só lida com MsgEvent.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Literal, Any

from .message.aid import AgentIdentifier
from .message.envelope import Envelope
from .message.acl import AclMessage

# --------------------------------------------------------------------------- #
Kind = Literal[
    "df", "df-done", "df-failure", "df-result", "df-not-understood",
    "ext-sl0", "ext-raw"
]


@dataclass(slots=True)
class MsgEvent:
    """Mensagem já classificada pelo runtime."""
    env:      Envelope
    acl:      AclMessage
    sender:   AgentIdentifier            # = env.from_
    kind:     Kind
    payload:  Any                        # Done / Failure / list[AD] / str / etc.

    # Qualquer helper que queiras adicionar no futuro (ex.: reply()).
