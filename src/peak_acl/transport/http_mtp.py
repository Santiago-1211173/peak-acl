"""
http_mtp.py
───────────
Servidor **INBOUND** FIPA HTTP‑MTP baseado em *aiohttp*.

JADE envia mensagens multipart/mixed **sem** cabeçalhos Content‑Disposition
e sem nomes de parte; o parser multipart do aiohttp não consegue mapear
automaticamente "envelope" / "acl-message". Este módulo faz portanto um
**parsing manual tolerante** do corpo raw:

    --BOUNDARY
    Content-Type: application/xml

    <envelope>...</envelope>
    --BOUNDARY
    Content-Type: text/plain

    (ACL ...)
    --BOUNDARY--

Depois de extrair as duas partes, converte para `Envelope` e `AclMessage`.
Cada mensagem válida é *sempre* colocada em `self.inbox` (asyncio.Queue).
Opcionalmente, também chama um callback `on_message(env, acl)` se fornecido.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Awaitable, Callable, Optional, Tuple

from aiohttp import web
import asyncio, re

from ..message.envelope import Envelope
from ..message.acl import AclMessage
from ..parse import parse

__all__ = ["HttpMtpServer"]

_LOG = logging.getLogger("peak_acl.http_mtp")

# ─── Parâmetros de configuração ───────────────────────────────────────────
MAX_REQUEST_SIZE = 5 * 1024 * 1024  # 5 MiB
ACC_ENDPOINT = "/acc"               # caminho padrão do JADE/DF

_BOUNDARY_RE = re.compile(r'boundary="?([^";]+)"?', re.IGNORECASE)


def _split_jade_multipart(raw: bytes, boundary: bytes) -> Tuple[str, str]:
    """
    Extrai (env_xml_str, acl_str) de um corpo multipart estilo JADE.
    Lança ValueError se algo não bater certo.
    """
    marker = b"--" + boundary
    segments = raw.split(marker)
    parts = []
    for seg in segments[1:]:
        seg = seg.lstrip(b"\r\n")
        if seg.startswith(b"--"):  # terminador
            break
        if not seg:
            continue
        parts.append(seg)
    if len(parts) < 2:
        raise ValueError(f"Esperava >=2 partes, obtive {len(parts)}")

    def _payload(block: bytes) -> bytes:
        if b"\r\n\r\n" not in block:
            raise ValueError("Parte sem cabeçalho CRLF CRLF")
        _hdr, payload = block.split(b"\r\n\r\n", 1)
        return payload.rstrip(b"\r\n")

    env_payload = _payload(parts[0])
    acl_payload = _payload(parts[1])

    env_xml = env_payload.decode("utf-8", errors="replace").strip()
    acl_str = acl_payload.decode("utf-8", errors="replace").strip()
    return env_xml, acl_str


class HttpMtpServer:
    """
    Servidor HTTP-MTP (apenas INBOUND).

    Parameters
    ----------
    on_message
        *Opcional.* Callback assíncrono chamado para cada mensagem válida.
        Se omitido, apenas a fila interna `self.inbox` é usada.
    client_max_size
        Tamanho máximo do corpo (bytes).  Padrão = 5 MiB.
    """

    # ---------------------------------------------------------------------
    def __init__(
        self,
        on_message: Optional[Callable[[Envelope, AclMessage], Awaitable[None]]] = None,
        *,
        client_max_size: int = MAX_REQUEST_SIZE,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ):
        self._on_message = on_message
        self.inbox: asyncio.Queue[Tuple[Envelope, AclMessage]] = asyncio.Queue()

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
        # Ler corpo bruto
        raw = await request.read()

        # Extrair boundary
        ctype = request.headers.get("Content-Type", "")
        if not ctype.lower().startswith("multipart/mixed"):
            raise web.HTTPUnsupportedMediaType(text="Esperava multipart/mixed")
        m = _BOUNDARY_RE.search(ctype)
        if not m:
            raise web.HTTPBadRequest(text="Falta boundary no Content-Type")
        boundary = m.group(1).encode("utf-8")

        try:
            env_xml, acl_str = _split_jade_multipart(raw, boundary)
            env = Envelope.from_xml(env_xml)
            acl = parse(acl_str)
        except Exception as exc:
            _LOG.exception("Falha a processar HTTP-MTP inbound")
            raise web.HTTPBadRequest(text=str(exc)) from exc

        # Coloca sempre na inbox interna
        await self.inbox.put((env, acl))

        # Opcionalmente chama callback
        if self._on_message is not None:
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
