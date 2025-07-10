"""
http_mtp.py
───────────
Implementa o lado servidor do FIPA HTTP-MTP em cima de *aiohttp*.

• NÃO herda de `web.Application`  ➜ compatível com futuras versões 4.x
• Middleware de logging + captura de erros → HTTP 400
• Valida Content-Type = multipart/mixed; extrai envelope + ACL
• Chama um callback assíncrono `on_message(env, acl)`
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Awaitable, Callable, Optional

from aiohttp import web
import asyncio

from ..message.envelope import Envelope
from ..parse import parse

__all__ = ["HttpMtpServer"]

_LOG = logging.getLogger("peak_acl.http_mtp")

# ─── Parâmetros de configuração ───────────────────────────────────────────
MAX_REQUEST_SIZE = 5 * 1024 * 1024  # 5 MiB
ACC_ENDPOINT = "/acc"               # caminho padrão do JADE/DF


class HttpMtpServer:
    """
    Servidor HTTP-MTP (apenas INBOUND).

    Parameters
    ----------
    on_message
        Callback assíncrono chamado para cada mensagem válida:
        ``async def on_message(env: Envelope, acl: AclMessage) -> None``.
    client_max_size
        Tamanho máximo do corpo (bytes).  Padrão = 5 MiB.
    """

    # ---------------------------------------------------------------------
    def __init__(
        self,
        on_message: Callable[[Envelope, "AclMessage"], Awaitable[None]],
        *,
        client_max_size: int = MAX_REQUEST_SIZE,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ):
        self._on_message = on_message

        self.app: web.Application = web.Application(
            client_max_size=client_max_size, loop=loop
        )

        # middlewares
        self.app.middlewares.extend([
            self._logging_middleware,
            self._error_middleware,
        ])

        # rota /acc
        self.app.router.add_post(ACC_ENDPOINT, self._handle_mtp)

    # ------------------------------------------------------------------ #
    #                        MIDDLEWARES                                  #
    # ------------------------------------------------------------------ #
    @web.middleware
    async def _logging_middleware(self, request: web.Request, handler):
        t0 = datetime.now(timezone.utc)
        resp = await handler(request)
        delta = (datetime.now(timezone.utc) - t0).total_seconds() * 1000
        _LOG.info("%s %s → %s (%.0f ms)",
                  request.method, request.path_qs, request.remote, delta)
        return resp

    @web.middleware
    async def _error_middleware(self, request: web.Request, handler):
        try:
            return await handler(request)
        except web.HTTPException:
            raise                                      # já mapeado
        except Exception as exc:                       # qualquer outro → 400
            _LOG.exception("Erro não tratado")
            raise web.HTTPBadRequest(text=str(exc)) from exc

    # ------------------------------------------------------------------ #
    #                          HANDLER                                    #
    # ------------------------------------------------------------------ #
    async def _handle_mtp(self, request: web.Request) -> web.StreamResponse:
        # 1) Validar Content-Type
        ctype = request.headers.get("Content-Type", "")
        if not ctype.startswith("multipart/mixed"):
            raise web.HTTPUnsupportedMediaType(text="Esperava multipart/mixed")

        # 2) Ler partes
        try:
            reader = await request.multipart()
        except ValueError as e:
            raise web.HTTPBadRequest(text=str(e)) from e

        parts: dict[str, str] = {}
        async for part in reader:
            if part.name in {"envelope", "acl-message"}:
                parts[part.name] = await part.text()

        if "envelope" not in parts or "acl-message" not in parts:
            raise web.HTTPBadRequest(text="Falta envelope ou acl-message")

        # 3) Parse envelope + ACL
        env = Envelope.from_xml(parts["envelope"])
        acl = parse(parts["acl-message"])

        # 4) Entregar ao callback
        await self._on_message(env, acl)
        return web.Response(text="ok", status=200)

    # ------------------------------------------------------------------ #
    #                    MÉTODOS DE AJUDA                                 #
    # ------------------------------------------------------------------ #
    async def run(
        self,
        host: str = "0.0.0.0",
        port: int = 7777,
    ):
        """Arranca o servidor *blocking* – útil em scripts."""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        _LOG.info("HttpMtpServer a escutar em %s:%d%s", host, port, ACC_ENDPOINT)
        await site.start()

        # Espera infinita até KeyboardInterrupt
        try:
            await web._run_app(self.app)  # type: ignore[attr-defined]
        finally:
            await runner.cleanup()
