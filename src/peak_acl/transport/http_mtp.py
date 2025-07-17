"""
peak_acl.transport.http_mtp
===========================

Servidor HTTP-MTP *inbound* compatível com JADE.

O JADE envia `multipart/mixed` minimalista, sem Content-Disposition:

    --BOUNDARY
    Content-Type: application/xml

    <envelope>...</envelope>
    --BOUNDARY
    Content-Type: text/plain

    (ACL ...)
    --BOUNDARY--

Alguns agentes podem trocar a ordem ou inserir CR/LF extra. A versão
anterior dependia do parser multipart do aiohttp e de `part.name`,
falhando com tráfego JADE e levando os Deliverer threads do JADE a
bloquearem (avisos “Deliverer stuck”).

Esta implementação:
  • Lê o corpo bruto (`await request.read()`).
  • Extrai boundary via regex.
  • Faz parsing manual tolerante a variações.
  • Identifica envelope/ACL por Content-Type + heurísticas.
  • Responde **imediatamente** 200 ao JADE; parsing em background.
  • Em erro, loga excerto e descarta (sem bloquear JADE).
  • Entrega (Envelope, AclMessage) a callback `on_message`, ou a `inbox`.

Disponibiliza helper `start_server()` usado pelo runtime.

"""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Awaitable, Callable, Optional, Tuple, TYPE_CHECKING

from aiohttp import web

from ..message.envelope import Envelope
from ..parse import parse as parse_acl

if TYPE_CHECKING:  # mypy / pylance only
    from ..message.acl import AclMessage

__all__ = ["HttpMtpServer", "start_server"]

_LOG = logging.getLogger("peak_acl.http_mtp")

# --------------------------------------------------------------------------- #
# Config
# --------------------------------------------------------------------------- #
MAX_REQUEST_SIZE = 5 * 1024 * 1024  # 5 MiB
ACC_ENDPOINT = "/acc"
_BOUNDARY_RE = re.compile(r'boundary="?([^";]+)"?', re.IGNORECASE)


# --------------------------------------------------------------------------- #
# Multipart helpers
# --------------------------------------------------------------------------- #
def _split_parts(raw: bytes, boundary_bytes: bytes) -> list[Tuple[bytes, bytes]]:
    """
    Divide corpo bruto em lista de partes [(headers, body)].

    Não tenta interpretar Content-Transfer-Encoding. Apenas separa.
    """
    marker = b"--" + boundary_bytes
    end_marker = marker + b"--"

    # Normaliza: retira whitespace lateral (CR/LF extra)
    data = raw.strip()

    # Divide por cada ocorrência do marcador (inclusive final)
    chunks = data.split(marker)

    parts: list[Tuple[bytes, bytes]] = []
    for chunk in chunks:
        c = chunk.strip()
        if not c or c == b"--":
            continue
        if c.startswith(b"--"):  # parte final (--BOUNDARY--)
            c = c[2:].lstrip()

        # separa cabeçalhos / corpo
        # prioridade CRLF; fallback LF
        if b"\r\n\r\n" in c:
            hdr, body = c.split(b"\r\n\r\n", 1)
        elif b"\n\n" in c:
            hdr, body = c.split(b"\n\n", 1)
        else:
            hdr, body = b"", c

        # corta CR/LF finais (antes do próximo boundary)
        body = body.rstrip(b"\r\n")
        parts.append((hdr, body))

    return parts


def _guess_is_envelope(body: bytes) -> bool:
    return body.lstrip().startswith(b"<?xml")


def _guess_is_acl(body: bytes) -> bool:
    # ACL strings JADE começam com '(' (ignorar whitespace)
    return body.lstrip().startswith(b"(")


def _extract_envelope_acl(raw: bytes, boundary_bytes: bytes) -> Tuple[str, str]:
    """
    Extrai (envelope_xml, acl_str). Levanta ValueError se falhar.
    """
    parts = _split_parts(raw, boundary_bytes)
    if len(parts) < 2:
        raise ValueError(f"multipart inesperado (<2 partes); partes={len(parts)}")

    env_bytes: Optional[bytes] = None
    acl_bytes: Optional[bytes] = None

    # 1) Usa Content-Type se presente
    for hdr, body in parts:
        hlow = hdr.lower()
        if (b"application/xml" in hlow) and (env_bytes is None):
            env_bytes = body
            continue
        if (b"text/plain" in hlow) and (acl_bytes is None):
            acl_bytes = body
            continue

    # 2) Heurísticas
    for _, body in parts:
        if env_bytes is None and _guess_is_envelope(body):
            env_bytes = body
            continue
        if acl_bytes is None and _guess_is_acl(body):
            acl_bytes = body
            continue

    # 3) Último recurso: assume 1ª parte envelope, 2ª ACL
    if env_bytes is None:
        env_bytes = parts[0][1]
    if acl_bytes is None:
        # toma a última parte não envelope
        for _, body in reversed(parts):
            if body is not env_bytes:
                acl_bytes = body
                break
        else:
            acl_bytes = parts[-1][1]

    # Decodifica
    env_txt = env_bytes.decode("utf-8", errors="replace").strip()
    acl_txt = acl_bytes.decode("utf-8", errors="replace").strip()

    # Sanidade: se ACL claramente não começa por '(' mas envelope sim, troca
    if not _guess_is_acl(acl_bytes) and _guess_is_envelope(acl_bytes) and _guess_is_acl(env_bytes):
        env_txt, acl_txt = acl_txt, env_txt

    return env_txt, acl_txt


# --------------------------------------------------------------------------- #
# Classe principal
# --------------------------------------------------------------------------- #
class HttpMtpServer:
    """
    Servidor HTTP-MTP (INBOUND).

    on_message:
        Callback opcional (`env`, `acl`) chamado por mensagem válida.
        Se None, mensagens vão para `self.inbox`.
    """

    def __init__(
        self,
        on_message: Optional[Callable[[Envelope, "AclMessage"], Awaitable[None]]] = None,
        *,
        client_max_size: int = MAX_REQUEST_SIZE,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ):
        self._on_message = on_message
        self.inbox: "asyncio.Queue[tuple[Envelope, AclMessage]]" = asyncio.Queue()

        self.app: web.Application = web.Application(
            client_max_size=client_max_size,
            loop=loop,
        )

        # middlewares
        self.app.middlewares.extend(
            [self._logging_middleware, self._error_middleware]
        )

        # rota /acc
        self.app.router.add_post(ACC_ENDPOINT, self._handle_post)

    # ------------------------------------------------------------------ #
    # Middlewares
    # ------------------------------------------------------------------ #
    @web.middleware
    async def _logging_middleware(self, request: web.Request, handler):
        resp = await handler(request)
        _LOG.info(
            "%s %s ← %s → %s",
            request.method,
            request.path_qs,
            request.remote,
            resp.status,
        )
        return resp

    @web.middleware
    async def _error_middleware(self, request: web.Request, handler):
        try:
            return await handler(request)
        except web.HTTPException:
            raise
        except Exception as exc:  # pragma: no cover
            _LOG.exception("Erro não tratado no HTTP-MTP")
            raise web.HTTPBadRequest(text=str(exc)) from exc

    # ------------------------------------------------------------------ #
    # /acc handler
    # ------------------------------------------------------------------ #
    async def _handle_post(self, request: web.Request) -> web.StreamResponse:
        raw = await request.read()

        # resposta imediata (não bloquear JADE)
        resp = web.Response(
            text="ok",
            status=200,
            content_type="text/plain",
            headers={"Cache-Control": "no-cache", "Connection": "close"},
        )

        ctype = request.headers.get("Content-Type", "")
        m = _BOUNDARY_RE.search(ctype)
        if not m:
            _LOG.error("Sem boundary em Content-Type: %s", ctype)
            return resp

        boundary_bytes = m.group(1).encode("utf-8", "ignore")

        # processa em background
        asyncio.create_task(self._process_raw(raw, boundary_bytes))
        return resp

    # ------------------------------------------------------------------ #
    async def _process_raw(self, raw: bytes, boundary_bytes: bytes) -> None:
        """
        Parse raw multipart -> Envelope + AclMessage; entrega.
        Executa em Task separada.
        """
        try:
            env_txt, acl_txt = _extract_envelope_acl(raw, boundary_bytes)

            # debug
            _LOG.debug("MTP RAW (%dB) env=%dB acl=%dB",
                       len(raw), len(env_txt), len(acl_txt))
            _LOG.debug("MTP ENV snippet: %s", env_txt[:80].replace("\n", " "))
            _LOG.debug("MTP ACL snippet: %s", acl_txt[:80].replace("\n", " "))

            env = Envelope.from_xml(env_txt)
            acl = parse_acl(acl_txt)

        except Exception:
            # Mostra excerto do corpo para diagnóstico
            sample = raw[:200].decode("utf-8", errors="replace").replace("\n", "\\n")
            _LOG.exception("Falha a processar HTTP-MTP (descartado). Raw[:200]=%r", sample)
            return

        # entrega
        try:
            if self._on_message is not None:
                await self._on_message(env, acl)
            else:
                await self.inbox.put((env, acl))
            _LOG.debug(
                "MTP IN: %s -> %s (%dB)",
                env.from_.name,
                getattr(acl, "performative_upper", "?"),
                len(raw),
            )
        except Exception:  # pragma: no cover - callback externo
            _LOG.exception("Erro no callback on_message (ignorado).")

    # ------------------------------------------------------------------ #
    async def run(self, host: str = "0.0.0.0", port: int = 7777):
        """
        Arranque *blocking* (debug manual).
        """
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        _LOG.info("HttpMtpServer a escutar em http://%s:%d%s", host, port, ACC_ENDPOINT)
        await site.start()
        await asyncio.Event().wait()  # bloqueia


# --------------------------------------------------------------------------- #
# start_server helper (usado pelo runtime)
# --------------------------------------------------------------------------- #
async def start_server(
    *,
    on_message: Optional[Callable[[Envelope, "AclMessage"], Awaitable[None]]] = None,
    bind_host: str = "0.0.0.0",
    port: int = 7777,
    loop: Optional[asyncio.AbstractEventLoop] = None,
    client_max_size: int = MAX_REQUEST_SIZE,
) -> tuple[HttpMtpServer, web.AppRunner, web.TCPSite]:
    server = HttpMtpServer(
        on_message=on_message,
        client_max_size=client_max_size,
        loop=loop,
    )
    runner = web.AppRunner(server.app)
    await runner.setup()
    site = web.TCPSite(runner, bind_host, port)
    await site.start()
    _LOG.info("HttpMtpServer a escutar em http://%s:%d%s", bind_host, port, ACC_ENDPOINT)
    return server, runner, site


# --------------------------------------------------------------------------- #
# Stand‑alone debug
# --------------------------------------------------------------------------- #
if __name__ == "__main__":  # pragma: no cover
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=7777)
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG)

    async def _print_msg(env: Envelope, acl: "AclMessage"):
        _LOG.info("Mensagem recebida: %s -> %s", env.from_.name, acl.performative_upper)

    async def _main():
        await start_server(on_message=_print_msg, bind_host=args.host, port=args.port)
        await asyncio.Event().wait()

    asyncio.run(_main())
