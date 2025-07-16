# src/peak_acl/message/acl.py
"""
Modelo completo de mensagem FIPA-ACL para o peak_acl.

Compatível com JADE:
- Todos os slots FIPA (performative, sender, receiver, reply-to, ...)
- Campos opcionais = None quando ausentes
- receivers / reply_to = listas de AgentIdentifier
- Acesso estilo msg["content"] suportado para retro-compatibilidade
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from .aid import AgentIdentifier


# --------------------------------------------------------------------------- #
#  Util performativa -> formato padrão FIPA (UPPERCASE, hífens)
# --------------------------------------------------------------------------- #
def _norm_performative(p: str) -> str:
    return p.strip().upper().replace("_", "-")


@dataclass
class AclMessage:
    performative: str

    # Agentes
    sender: Optional[AgentIdentifier] = None
    receivers: List[AgentIdentifier] = field(default_factory=list)
    reply_to: List[AgentIdentifier] = field(default_factory=list)

    # Conteúdo e meta
    content: Optional[Any] = None          # str | bytes | objeto | AclMessage
    language: Optional[str] = None
    encoding: Optional[str] = None
    ontology: Optional[str] = None
    protocol: Optional[str] = None

    # Correlação / diálogo
    conversation_id: Optional[str] = None
    reply_with: Optional[str] = None
    in_reply_to: Optional[str] = None
    reply_by: Optional[datetime] = None

    # Parâmetros definidos pelo utilizador / extensões X-
    user_params: Dict[str, Any] = field(default_factory=dict)

    # Texto original (debug opcional)
    raw_text: Optional[str] = None

    # ------------------------------------------------------------------ #
    def add_receiver(self, aid: AgentIdentifier) -> None:
        self.receivers.append(aid)

    def add_reply_to(self, aid: AgentIdentifier) -> None:
        self.reply_to.append(aid)

    @property
    def performative_upper(self) -> str:
        return _norm_performative(self.performative)

    # --- Acesso tipo dicionário (retro-compat.) ----------------------- #
    def __getitem__(self, key: str):
        k = key.lower()
        if k == "content":
            return self.content
        if k == "language":
            return self.language
        if k == "encoding":
            return self.encoding
        if k == "ontology":
            return self.ontology
        if k == "protocol":
            return self.protocol
        if k in ("conversation-id", "conversationid"):
            return self.conversation_id
        if k in ("reply-with", "replywith"):
            return self.reply_with
        if k in ("in-reply-to", "inreplyto"):
            return self.in_reply_to
        if k in ("reply-by", "replyby"):
            return self.reply_by
        return self.user_params[k]

    def __setitem__(self, key: str, value: Any):
        k = key.lower()
        if k == "content":
            self.content = value
        elif k == "language":
            self.language = value
        elif k == "encoding":
            self.encoding = value
        elif k == "ontology":
            self.ontology = value
        elif k == "protocol":
            self.protocol = value
        elif k in ("conversation-id", "conversationid"):
            self.conversation_id = value
        elif k in ("reply-with", "replywith"):
            self.reply_with = value
        elif k in ("in-reply-to", "inreplyto"):
            self.in_reply_to = value
        elif k in ("reply-by", "replyby"):
            self.reply_by = value
        else:
            self.user_params[k] = value
