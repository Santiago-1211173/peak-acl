# peak_acl/runtime.py
from __future__ import annotations
import asyncio
from dataclasses import dataclass
from typing import Sequence, Tuple, Optional

import aiohttp.web

from .message.aid import AgentIdentifier
from .transport.http_mtp import HttpMtpServer, start_server
from .transport.http_client import HttpMtpClient
from . import df_manager


@dataclass
class CommEndpoint:
    my_aid: AgentIdentifier
    inbox: asyncio.Queue
    client: HttpMtpClient
    server: HttpMtpServer
    runner: aiohttp.web.AppRunner
    site: aiohttp.web.TCPSite
    df_aid: Optional[AgentIdentifier] = None   # <── novo

    # ------------------------------------------------------------------ #
    async def register_df(self, df_aid, services, *, df_url=None,
                          languages=(), ontologies=(), protocols=(), ownership=()):
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
        """Envia SEARCH ao DF."""
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
        """Envia DEREGISTER ao DF."""
        df_ai = df_aid or self.df_aid
        if df_ai is None:
            raise ValueError("deregister_df() sem df_aid definido.")
        await df_manager.deregister(
            my_aid=self.my_aid,
            df_aid=df_ai,
            http_client=self.client,
            df_url=df_url,
        )

    async def close(self):
        await self.runner.cleanup()
        await self.client.close()


async def start_endpoint(
    *,
    my_aid: AgentIdentifier,
    bind_host: str = "0.0.0.0",
    auto_register: bool = False,
    df_aid: Optional[AgentIdentifier] = None,
    services: Optional[Sequence[Tuple[str,str]]] = None,
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
        df_aid=df_aid,   # <── guarda DF
    )

    if auto_register:
        if df_aid is None:
            raise ValueError("auto_register=True mas df_aid=None")
        await ep.register_df(df_aid, services or [], df_url=df_aid.addresses[0])

    return ep
