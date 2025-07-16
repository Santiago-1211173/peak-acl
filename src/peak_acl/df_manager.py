from __future__ import annotations
from typing import Sequence, Tuple, List, Optional

import asyncio
from datetime import datetime, timezone

from .message.aid import AgentIdentifier
from .message.acl import AclMessage
from .transport.http_client import HttpMtpClient
from .transport.multipart import build_multipart
from .serialize import dumps
from .parse import parse


# ────────────────────────────────────────────────────────────────────
# 1) Helpers de construção de S‑expressions em SL‑0
# --------------------------------------------------------------------
def _aid_sexp(ai: AgentIdentifier) -> str:
    return f'(agent-identifier :name {ai.name} :addresses (sequence {ai.addresses[0]}))'


def _service_sexp(name: str, s_type: str) -> str:
    return f'(service-description :name {name} :type {s_type})'


def _register_content(
    my_ai: AgentIdentifier,
    df_ai: AgentIdentifier,
    services: Sequence[Tuple[str, str]],
) -> str:
    """
    Devolve a string SL0 que fica dentro de ":content" num pedido register.
    """
    services_set = " ".join(_service_sexp(n, t) for n, t in services)
    return (
        f'((action {_aid_sexp(df_ai)} '
        f'(register (df-agent-description '
        f':name {_aid_sexp(my_ai)} '
        f':services (set {services_set})))) )'
    )


# ────────────────────────────────────────────────────────────────────
# 2) Função pública: auto‑register
# --------------------------------------------------------------------
async def register(
    my_aid: AgentIdentifier,
    df_aid: AgentIdentifier,
    services: Sequence[Tuple[str, str]],
    *,
    http_client: Optional[HttpMtpClient] = None,
    df_url: Optional[str] = None,
) -> None:
    """
    Regista *my_aid* no Directory Facilitator *df_aid* anunciando *services*.
    Se *http_client* for omitido, cria e fecha um internamente.
    """
    if not services:
        raise ValueError("É necessário anunciar pelo menos um serviço")

    content_literal = _register_content(my_aid, df_aid, services)

    acl_str = rf"""(request
      :sender   {_aid_sexp(my_aid)}
      :receiver (set {_aid_sexp(df_aid)})
      :content  "{content_literal}"
      :language fipa-sl0
      :ontology FIPA-Agent-Management
      :protocol fipa-request)"""

    # validação local – falha já aqui se a sintaxe não for aceitável
    acl_msg: AclMessage = parse(acl_str)

    # calcula URL do ACC se não vier de fora
    df_url = df_url or df_aid.addresses[0]

    client_created = False
    if http_client is None:
        http_client = HttpMtpClient()
        client_created = True

    try:
        await http_client.send(df_aid, my_aid, acl_msg, df_url)
    finally:
        if client_created:
            await http_client.close()