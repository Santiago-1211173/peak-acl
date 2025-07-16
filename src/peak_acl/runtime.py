# peak_acl/runtime.py
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Sequence, Tuple, Optional, Iterable, Union

import aiohttp.web

from .message.aid import AgentIdentifier
from .message.acl import AclMessage
from .transport.http_mtp import HttpMtpServer, start_server
from .transport.http_client import HttpMtpClient
from . import df_manager, sl0


# ------------------------------------------------------------------ #
# util
# ------------------------------------------------------------------ #
def _first_url(ai: AgentIdentifier) -> str:
    if not ai.addresses:
        raise ValueError(f"AID sem endereço HTTP: {ai}")
    return ai.addresses[0]


# ------------------------------------------------------------------ #
# Endpoint de comunicação (server inbound + client outbound)
# ------------------------------------------------------------------ #
@dataclass
class CommEndpoint:
    my_aid: AgentIdentifier
    inbox: asyncio.Queue                 # fila inbound (Envelope, AclMessage)
    client: HttpMtpClient                # outbound
    server: HttpMtpServer                # inbound
    runner: aiohttp.web.AppRunner
    site: aiohttp.web.TCPSite
    df_aid: Optional[AgentIdentifier] = field(default=None)

    # ------------------- DF helpers ---------------------------------- #
    async def register_df(self, df_aid, services, *,
                          df_url=None, languages=(), ontologies=(),
                          protocols=(), ownership=()):
        """Envia REQUEST register ao DF."""
        await df_manager.register(
            my_aid=self.my_aid,
            df_aid=df_aid,
            services=services,
            languages=languages,
            ontologies=ontologies,
            protocols=protocols,
            ownership=ownership,
            http_client=self.client,
            df_url=df_url,
        )

    async def search_df(self, *, service_name=None, service_type=None,
                        max_results=None, df_aid=None, df_url=None):
        """Envia REQUEST search ao DF."""
        df_ai = df_aid or self.df_aid
        if df_ai is None:
            raise ValueError("search_df() sem df_aid definido.")
        await df_manager.search_services(
            my_aid=self.my_aid,
            df_aid=df_ai,
            service_name=service_name,
            service_type=service_type,
            max_results=max_results,
            http_client=self.client,
            df_url=df_url,
        )

    async def deregister_df(self, df_aid=None, *, df_url=None):
        """Envia REQUEST deregister ao DF."""
        df_ai = df_aid or self.df_aid
        if df_ai is None:
            raise ValueError("deregister_df() sem df_aid definido.")
        await df_manager.deregister(
            my_aid=self.my_aid,
            df_aid=df_ai,
            http_client=self.client,
            df_url=df_url,
        )

    # ------------------- ACL genérico -------------------------------- #
    async def send_acl(
        self,
        *,
        to: Union[AgentIdentifier, Iterable[AgentIdentifier]],
        performative: str,
        content=None,
        language: Optional[str] = None,
        ontology: Optional[str] = None,
        protocol: Optional[str] = None,
        conversation_id: Optional[str] = None,
        reply_with: Optional[str] = None,
        in_reply_to: Optional[str] = None,
        reply_by: Optional[str] = None,
    ) -> AclMessage:
        """
        Envia uma mensagem ACL genérica (inform, request, etc.).

        `content` pode ser:
            • str  -> usado tal e qual
            • objeto SL0 -> serializado com sl0.dumps()
            • None -> sem campo :content
        """
        # Normaliza recetores
        if isinstance(to, AgentIdentifier):
            receivers = [to]
        else:
            receivers = list(to)
            if not receivers:
                raise ValueError("send_acl() sem receivers.")

        # Serializa conteúdo
        if content is None:
            content_str = None
        elif isinstance(content, str):
            content_str = content
        else:
            # tenta serializar como SL0
            content_str = sl0.dumps(content)

        # Constrói AclMessage "lógico" (inclui todos os receivers)
        msg = AclMessage(
            performative=performative,
            sender=self.my_aid,
            receivers=receivers,
            content=content_str,
            language=language,
            ontology=ontology,
            protocol=protocol,
            conversation_id=conversation_id,
            reply_with=reply_with,
            in_reply_to=in_reply_to,
            reply_by=reply_by,
        )

        # Envia 1 POST por recetor (envelope ponto-a-ponto)
        for r in receivers:
            await self.client.send(r, self.my_aid, msg, _first_url(r))

        return msg

    # ------------------------------------------------------------------ #
    async def close(self):
        await self.runner.cleanup()
        await self.client.close()


# ------------------------------------------------------------------ #
# Arrancar endpoint
# ------------------------------------------------------------------ #
async def start_endpoint(
    *,
    my_aid: AgentIdentifier,
    bind_host: str = "0.0.0.0",
    auto_register: bool = False,
    df_aid: Optional[AgentIdentifier] = None,
    services: Optional[Sequence[Tuple[str, str]]] = None,
    http_client: Optional[HttpMtpClient] = None,
    loop=None,
) -> CommEndpoint:
    """
    Cria server inbound + cliente outbound + inbox,
    opcionalmente regista no DF.
    """
    from urllib.parse import urlparse
    u = urlparse(my_aid.addresses[0])
    port = u.port or 80

    client = http_client or HttpMtpClient()
    server, runner, site = await start_server(
        on_message=None, bind_host=bind_host, port=port, loop=loop
    )

    ep = CommEndpoint(
        my_aid=my_aid,
        inbox=server.inbox,
        client=client,
        server=server,
        runner=runner,
        site=site,
        df_aid=df_aid,
    )

    if auto_register:
        if df_aid is None:
            raise ValueError("auto_register=True mas df_aid=None")
        await ep.register_df(
            df_aid,
            services or [],
            df_url=df_aid.addresses[0],
        )

    return ep
