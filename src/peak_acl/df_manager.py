# peak_acl/df_manager.py
from __future__ import annotations
from typing import Sequence, Tuple, Optional

from .message.aid import AgentIdentifier
from .message.acl import AclMessage
from .transport.http_client import HttpMtpClient
from .parse import parse

__all__ = ["register", "deregister", "search_services"]

def _aid(ai: AgentIdentifier) -> str:
    return f"(agent-identifier :name {ai.name} :addresses (sequence {ai.addresses[0]}))"

def _services_set(services: Optional[Sequence[Tuple[str,str]]]) -> str:
    if not services:
        return ""  # omite slot
    inner = " ".join(
        f"(service-description :name {n} :type {t})"
        for n,t in services
    )
    return f":services (set {inner})"

# ------------------------------------------------------------------ #
async def register(
    my_aid: AgentIdentifier,
    df_aid: AgentIdentifier,
    services: Optional[Sequence[Tuple[str,str]]] = None,
    *,
    http_client: HttpMtpClient,
    df_url: Optional[str] = None,
) -> None:
    set_services = _services_set(services)
    content_literal = (
        f"((action {_aid(df_aid)} "
        f"(register (df-agent-description :name {_aid(my_aid)} {set_services}))))"
    )
    acl_str = (
        f"(request "
        f":sender {_aid(my_aid)} "
        f":receiver (set {_aid(df_aid)}) "
        f':content "{content_literal}" '
        f":language fipa-sl0 :ontology FIPA-Agent-Management :protocol fipa-request)"
    )
    acl: AclMessage = parse(acl_str)
    await http_client.send(df_aid, my_aid, acl, df_url or df_aid.addresses[0])

# ------------------------------------------------------------------ #
async def deregister(
    my_aid: AgentIdentifier,
    df_aid: AgentIdentifier,
    *,
    http_client: HttpMtpClient,
    df_url: Optional[str] = None,
) -> None:
    content_literal = (
        f"((action {_aid(df_aid)} "
        f"(deregister (df-agent-description :name {_aid(my_aid)}))))"
    )
    acl_str = (
        f"(request "
        f":sender {_aid(my_aid)} "
        f":receiver (set {_aid(df_aid)}) "
        f':content "{content_literal}" '
        f":language fipa-sl0 :ontology FIPA-Agent-Management :protocol fipa-request)"
    )
    acl: AclMessage = parse(acl_str)
    await http_client.send(df_aid, my_aid, acl, df_url or df_aid.addresses[0])

# ------------------------------------------------------------------ #
async def search_services(
    my_aid: AgentIdentifier,
    df_aid: AgentIdentifier,
    *,
    service_type: Optional[str] = None,
    service_name: Optional[str] = None,
    http_client: HttpMtpClient,
    df_url: Optional[str] = None,
) -> None:
    # monta um filtro minimal; DF devolve resposta via INFORM
    filters = []
    if service_name:
        filters.append(f"(service-description :name {service_name})")
    if service_type:
        filters.append(f"(service-description :type {service_type})")
    if filters:
        sv_expr = f":services (set {' '.join(filters)})"
    else:
        sv_expr = ""
    content_literal = (
        f"((action {_aid(df_aid)} "
        f"(search (df-agent-description {sv_expr}))))"
    )
    acl_str = (
        f"(request "
        f":sender {_aid(my_aid)} "
        f":receiver (set {_aid(df_aid)}) "
        f':content "{content_literal}" '
        f":language fipa-sl0 :ontology FIPA-Agent-Management :protocol fipa-request)"
    )
    acl: AclMessage = parse(acl_str)
    await http_client.send(df_aid, my_aid, acl, df_url or df_aid.addresses[0])
