# src/peak_acl/df_manager.py
"""
Operações de alto nível sobre o Directory Facilitator (DF) FIPA,
interoperáveis com JADE.

Fornece construtores de mensagens ACL (register/deregister/search) e
wrappers assíncronos que as enviam via HttpMtpClient.

Depende de:
    • peak_acl.message.acl.AclMessage
    • peak_acl.message.aid.AgentIdentifier
    • peak_acl.transport.http_client.HttpMtpClient
    • peak_acl.sl0  (mini-implementação FIPA-SL0)
    • peak_acl.content.decode_content  (para interpretar replies)

Uso típico num agente:

    from peak_acl.df_manager import register
    await register(my_aid, df_aid, [("echo","generic")], http_client=client)

Depois, no dispatcher inbound, podes usar `decode_df_reply()` ou
`is_df_done_msg()` para saber se o DF confirmou.
"""

from __future__ import annotations

import uuid
from typing import Iterable, Optional, Sequence, Tuple

from .message.aid import AgentIdentifier
from .message.acl import AclMessage
from .transport.http_client import HttpMtpClient
from .content import decode_content
from . import sl0

__all__ = [
    "build_register_msg",
    "build_deregister_msg",
    "build_search_msg",
    "register",
    "deregister",
    "search_services",
    "decode_df_reply",
    "is_df_done_msg",
    "is_df_failure_msg",
]


# --------------------------------------------------------------------------- #
# util
# --------------------------------------------------------------------------- #
def _first_url(ai: AgentIdentifier) -> str:
    try:
        return ai.addresses[0]
    except IndexError as exc:
        raise ValueError(f"AID sem endereço HTTP: {ai}") from exc


def _new_tag(prefix: str = "") -> str:
    return prefix + uuid.uuid4().hex


def _mk_request_msg(
    *,
    sender: AgentIdentifier,
    receivers: Sequence[AgentIdentifier],
    content_ast,
    language: str = "fipa-sl0",
    ontology: str = "FIPA-Agent-Management",
    protocol: str = "fipa-request",
    tag: Optional[str] = None,
) -> AclMessage:
    tag = tag or _new_tag(sender.name)
    return AclMessage(
        performative="request",
        sender=sender,
        receivers=list(receivers),
        content=content_ast,
        language=language,
        ontology=ontology,
        protocol=protocol,
        conversation_id=tag,
        reply_with=tag,
    )


# --------------------------------------------------------------------------- #
# construtores (retornam AclMessage; *não* enviam)
# --------------------------------------------------------------------------- #
def build_register_msg(
    my_aid: AgentIdentifier,
    df_aid: AgentIdentifier,
    services: Sequence[Tuple[str, str]] = (),
    *,
    tag: Optional[str] = None,
) -> AclMessage:
    content_ast = sl0.Action(
        actor=df_aid,
        act=sl0.Register(
            sl0.DfAgentDescription(
                name=my_aid,
                services=[sl0.ServiceDescription(name=n, type=t) for n, t in services],
            )
        ),
    )
    return _mk_request_msg(
        sender=my_aid,
        receivers=[df_aid],
        content_ast=content_ast,
        tag=tag,
    )


def build_deregister_msg(
    my_aid: AgentIdentifier,
    df_aid: AgentIdentifier,
    *,
    tag: Optional[str] = None,
) -> AclMessage:
    content_ast = sl0.Action(
        actor=df_aid,
        act=sl0.Deregister(
            sl0.DfAgentDescription(name=my_aid, services=[]),
        ),
    )
    return _mk_request_msg(
        sender=my_aid,
        receivers=[df_aid],
        content_ast=content_ast,
        tag=tag,
    )


def build_search_msg(
    my_aid: AgentIdentifier,
    df_aid: AgentIdentifier,
    *,
    service_name: Optional[str] = None,
    service_type: Optional[str] = None,
    max_results: Optional[int] = None,
    tag: Optional[str] = None,
) -> AclMessage:
    # Template: apenas critérios fornecidos; name omitido (match wildcard no DF)
    svcs = []
    if service_name is not None or service_type is not None:
        svcs.append(sl0.ServiceDescription(name=service_name, type=service_type))
    # DfAgentDescription com nome None = wildcard (ver sl0.DfAgentDescription)
    tmpl = sl0.DfAgentDescription(name=None, services=svcs)
    content_ast = sl0.Action(
        actor=df_aid,
        act=sl0.Search(template=tmpl, max_results=max_results),
    )
    return _mk_request_msg(
        sender=my_aid,
        receivers=[df_aid],
        content_ast=content_ast,
        tag=tag,
    )


# --------------------------------------------------------------------------- #
# wrappers que enviam
# --------------------------------------------------------------------------- #
async def register(
    my_aid: AgentIdentifier,
    df_aid: AgentIdentifier,
    services: Optional[Sequence[Tuple[str, str]]] = None,
    *,
    http_client: HttpMtpClient,
    df_url: Optional[str] = None,
    tag: Optional[str] = None,
) -> AclMessage:
    msg = build_register_msg(my_aid, df_aid, services or (), tag=tag)
    await http_client.send(df_aid, my_aid, msg, df_url or _first_url(df_aid))
    return msg


async def deregister(
    my_aid: AgentIdentifier,
    df_aid: AgentIdentifier,
    *,
    http_client: HttpMtpClient,
    df_url: Optional[str] = None,
    tag: Optional[str] = None,
) -> AclMessage:
    msg = build_deregister_msg(my_aid, df_aid, tag=tag)
    await http_client.send(df_aid, my_aid, msg, df_url or _first_url(df_aid))
    return msg


async def search_services(
    my_aid: AgentIdentifier,
    df_aid: AgentIdentifier,
    *,
    service_name: Optional[str] = None,
    service_type: Optional[str] = None,
    max_results: Optional[int] = None,
    http_client: HttpMtpClient,
    df_url: Optional[str] = None,
    tag: Optional[str] = None,
) -> AclMessage:
    msg = build_search_msg(
        my_aid,
        df_aid,
        service_name=service_name,
        service_type=service_type,
        max_results=max_results,
        tag=tag,
    )
    await http_client.send(df_aid, my_aid, msg, df_url or _first_url(df_aid))
    return msg


# --------------------------------------------------------------------------- #
# helpers para replies do DF
# --------------------------------------------------------------------------- #
def decode_df_reply(msg: AclMessage):
    """
    Decodifica msg.content se language for SL (fipa-sl0,...).
    Devolve AST SL0 (Done/Failure/Action/Result/...) ou string original.
    """
    return decode_content(msg)


def is_df_done_msg(msg: AclMessage) -> bool:
    from . import sl0  # local import
    payload = decode_df_reply(msg)
    return isinstance(payload, sl0.Done)


def is_df_failure_msg(msg: AclMessage) -> bool:
    from . import sl0
    payload = decode_df_reply(msg)
    return isinstance(payload, sl0.Failure)
