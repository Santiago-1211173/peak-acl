"""
http_mtp.py
───────────
Servidor HTTP-MTP compatível com JADE.

Aceita mensagens multipart/mixed no formato:
    --BOUNDARY
    Content-Type: application/xml

    <envelope>...</envelope>
    --BOUNDARY
    Content-Type: text/plain

    (ACL ...)
    --BOUNDARY--
Sem `Content-Disposition` nem `name=` (formato JADE).

Também aceita formato "nomeado" (part.name == "envelope"/"acl-message") caso
futuras implementações o adicionem.

Em caso de erro de parsing:
    • Regista _LOG.error()
    • Responde 200 (JADE considera entrega OK; evita MTS-error tempestade)
      *a não ser* que o cabeçalho Content-Type não seja multipart → 415.
"""

from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime, timezone
from typing import Awaitable, Callable, Optional, Tuple

from aiohttp import web

from ..message.envelope import Envelope
from ..parse import parse as parse_acl

__all__ = ["HttpMtpServer", "start_server"]

_LOG = logging.getLogger("peak_acl.http_mtp")

MAX_REQUEST_SIZE = 5 * 1024 * 1024
ACC_ENDPOINT = "/acc"


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _split_multipart_raw(raw: bytes, ctype_header: str) -> Tuple[str, str]:
    """
    Fallback parser minimalista (compat JADE).
    Retorna (envelope_xml, acl_str) ou levanta ValueError.
    """
    m = re.search(r'boundary="?([^";]+)"?', ctype_header, re.IGNORECASE)
    if not m:
        raise ValueError("sem boundary no Content-Type")

    boundary = m.group(1).encode("utf-8")
    marker = b"--" + boundary
    parts = raw.split(marker)
    if len(parts) < 3:
        raise ValueError(f"multipart inesperado (<3 partes); len={len(parts)}")

    # partes[1] envelope, partes[2] ACL (JADE)
    def _extract_payload(part_bytes: bytes) -> bytes:
        # remove prefix CRLF
        part_bytes = part_bytes.lstrip(b"\r\n")
        # corta cabecalhos até CRLF CRLF
        try:
            _, body = part_bytes.split(b"\r\n\r\n", 1)
        except ValueError:
            raise ValueError("sem duplo CRLF em parte multipart")
        # remove sufixo CRLF--? e whitespace
        body = body.rstrip(b"\r\n")
        return body

    env_b = _extract_payload(parts[1])
    acl_b = _extract_payload(parts[2])

    return (
        env_b.decode("utf-8", errors="replace"),
        acl_b.decode("utf-8", errors="replace"),
    )


# --------------------------------------------------------------------------- #
# Servidor
# --------------------------------------------------------------------------- #
class HttpMtpServer:
    """
    Servidor HTTP-MTP (INBOUND).

    on_message(env, acl) será chamado para cada mensagem válida.
    Se `on_message` for None, coloca (env, acl) numa `inbox` interna (.inbox).
    """

    def __init__(
        self,
        on_message: Optional[Callable[[Envelope, "AclMessage"], Awaitable[None]]] = None,
        *,
        client_max_size: int = MAX_REQUEST_SIZE,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ):
        from ..message.acl import AclMessage  # lazy import to avoid circular

        self._on_message_cb = on_message
        self.inbox: asyncio.Queue = asyncio.Queue()  # sempre existe

        self.app: web.Application = web.Application(
            client_max_size=client_max_size, loop=loop
        )

        self.app.middlewares.extend(
            [self._logging_middleware, self._error_middleware]
        )
        self.app.router.add_post(ACC_ENDPOINT, self._handle_mtp)

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
            raise
        except Exception as exc:
            _LOG.exception("Erro não tratado")
            raise web.HTTPBadRequest(text=str(exc)) from exc

    # ------------------------------------------------------------------ #
    async def _handle_mtp(self, request: web.Request) -> web.StreamResponse:
        ctype = request.headers.get("Content-Type", "")
        if not ctype.lower().startswith("multipart/mixed"):
            raise web.HTTPUnsupportedMediaType(text="Esperava multipart/mixed")

        envelope_txt: Optional[str] = None
        acl_txt: Optional[str] = None

        # 1ª tentativa – parser aiohttp
        try:
            reader = await request.multipart()
            idx = 0
            async for part in reader:
                pt_ct = part.headers.get("Content-Type", "").lower()
                txt = await part.text()
                if part.name in {"envelope", "acl-message"}:
                    if part.name == "envelope":
                        envelope_txt = txt
                    else:
                        acl_txt = txt
                else:
                    # fallback por ordem/tipo
                    if idx == 0 or pt_ct.startswith("application/xml"):
                        envelope_txt = txt
                    else:
                        acl_txt = txt
                idx += 1
        except Exception as exc:
            _LOG.warning("aiohttp.multipart falhou (%s); usar fallback bruto", exc)

        # 2ª tentativa – fallback manual se faltou algo
        if envelope_txt is None or acl_txt is None:
            raw = await request.read()
            try:
                envelope_txt, acl_txt = _split_multipart_raw(raw, ctype)
            except Exception as exc:  # parsing falhou
                _LOG.error("Falha a extrair envelope/ACL (%s); ignorar msg", exc)
                # responde 200 para não disparar MTS-error; JADE já loga.
                return web.Response(text="ignored", status=200)

        # 3) Parse envelope + ACL
        try:
            env = Envelope.from_xml(envelope_txt)
        except Exception as exc:
            _LOG.error("Envelope inválido: %s\n%s", exc, envelope_txt)
            return web.Response(text="bad-envelope", status=200)

        try:
            acl = parse_acl(acl_txt)
        except Exception as exc:
            _LOG.error("ACL inválido: %s\n%s", exc, acl_txt)
            return web.Response(text="bad-acl", status=200)

        # 4) Entregar
        if self._on_message_cb is not None:
            await self._on_message_cb(env, acl)
        else:
            await self.inbox.put((env, acl))

        return web.Response(text="ok", status=200)

    # ------------------------------------------------------------------ #
    async def run(self, host: str = "0.0.0.0", port: int = 7777):
        """Arranca standalone (bloqueante)."""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        _LOG.info("HttpMtpServer a escutar em %s:%d%s", host, port, ACC_ENDPOINT)
        await site.start()
        try:
            await web._run_app(self.app)  # type: ignore[attr-defined]
        finally:
            await runner.cleanup()


# --------------------------------------------------------------------------- #
# helper para arrancar server e devolver (server, runner, site)
# --------------------------------------------------------------------------- #
async def start_server(
    *,
    on_message=None,
    bind_host="0.0.0.0",
    port=7777,
    loop=None,
) -> tuple[HttpMtpServer, web.AppRunner, web.TCPSite]:
    srv = HttpMtpServer(on_message, client_max_size=MAX_REQUEST_SIZE, loop=loop)
    runner = web.AppRunner(srv.app)
    await runner.setup()
    site = web.TCPSite(runner, bind_host, port)
    await site.start()
    _LOG.info("HttpMtpServer a escutar em http://%s:%d%s", bind_host, port, ACC_ENDPOINT)
    return srv, runner, site
