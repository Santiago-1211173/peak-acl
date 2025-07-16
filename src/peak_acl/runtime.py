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

    async def register_df(self, df_aid, services, *, df_url=None):
        await df_manager.register(
            my_aid=self.my_aid,
            df_aid=df_aid,
            services=services,
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
    # Deduz porta do 1º endereço HTTP no my_aid
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
    )

    if auto_register:
        if df_aid is None:
            raise ValueError("auto_register=True mas df_aid=None")
        await ep.register_df(df_aid, services or [])

    return ep
