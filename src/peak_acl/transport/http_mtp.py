"""
peak_acl.transport.http_mtp
===========================

Servidor HTTP-MTP *inbound* compatível com JADE.

O JADE envia `multipart/mixed` minimalista:
    --BOUNDARY
    Content-Type: application/xml

    <envelope>...</envelope>
    --BOUNDARY
    Content-Type: text/plain

    (ACL ...)
    --BOUNDARY--

Esta versão:

• Lê o corpo bruto (`await request.read()`).
• Extrai `boundary` do cabeçalho Content-Type via regex.
• Faz parsing case-insensitivo das partes (application/xml vs text/plain).
• Aceita ordem arbitrária; fallback por heurística (body que começa com
  '<?xml' é envelope; o outro é ACL).
• Responde *imediatamente* 200 ao JADE e processa em *background* para
  não bloquear o thread de entrega do JADE.
• Em caso de erro de parsing, loga e descarta (não falha HTTP).
• Entrega (Envelope, AclMessage) a:
    - callback `on_message` se fornecido; **ou**
    - fila interna `inbox` (asyncio.Queue[(Envelope, AclMessage)]).

Fornece também helper `start_server()` que cria `AppRunner` + `TCPSite`
e devolve `(server, runner, site)` — usado pelo runtime.

"""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Awaitable, Callable, Optional, Tuple, TYPE_CHECKING

from aiohttp import web

from ..message.envelope import Envelope
from ..parse import parse as parse_acl

if TYPE_CHECKING:  # apenas para type checkers
    from ..message.acl import AclMessage

__all__ = ["HttpMtpServer", "start_server"]

_LOG = logging.getLogger("peak_acl.http_mtp")

# --------------------------------------------------------------------------- #
# Configurações
# --------------------------------------------------------------------------- #
MAX_REQUEST_SIZE = 5 * 1024 * 1024  # 5 MiB
ACC_ENDPOINT = "/acc"
_BOUNDARY_RE = re.compile(r'boundary="?([^";]+)"?', re.IGNORECASE)


# --------------------------------------------------------------------------- #
# Helpers de parsing multipart JADE
# --------------------------------------------------------------------------- #
def _split_parts(raw: bytes, boundary_bytes: bytes) -> list[Tuple[bytes, bytes]]:
    """
    Divide o corpo bruto em partes [(headers, body), ...].

    Retorna lista vazia se parsing falhar.
    """
    marker = b"--" + boundary_bytes
    end_marker = marker + b"--"

    # Garante fim uniforme
    data = raw
    # Alguns servidores acrescentam CRLF antes/after; limpa
    data = data.strip()

    # Divide pelo marcador (não remove preâmbulo porque JADE não envia)
    chunks = data.split(marker)
    parts: list[Tuple[bytes, bytes]] = []

    for chunk in chunks:
        # descarta vazio / preâmbulo
        c = chunk.strip()
        if not c or c == b"--":
            continue
        if c.startswith(b"--"):  # final
            c = c[2:].lstrip()

        # separa headers/body
        # prioridade CRLF; fallback LF
        sep = b"\r\n\r\n"
        if sep in c:
            hdr, body = c.split(sep, 1)
        else:
            sep2 = b"\n\n"
            if sep2 in c:
                hdr, body = c.split(sep2, 1)
            else:
                # sem header separator? assume tudo body
                hdr, body = b"", c

        # retira trailing CRLF que antecede boundary seguinte
        body = body.rstrip(b"\r\n")

        parts.append((hdr, body))

    return parts


def _extract_envelope_acl(raw: bytes, boundary_bytes: bytes) -> Tuple[str, str]:
    """
    Extrai (envelope_xml, acl_str) do corpo multipart.
    Levanta ValueError se falhar.
    """
    parts = _split_parts(raw, boundary_bytes)
    if len(parts) < 2:
        raise ValueError(f"multipart inesperado (<2 partes); partes={len(parts)}")

    env_bytes: Optional[bytes] = None
    acl_bytes: Optional[bytes] = None

    # 1ª passagem por Content-Type
    for hdr, body in parts:
        hlow = hdr.lower()
        if b"application/xml" in hlow and env_bytes is None:
            env_bytes = body
        elif b"text/plain" in hlow and acl_bytes is None:
            acl_bytes = body

    # 2ª passagem por heurística
    if env_bytes is None or acl_bytes is None:
        for _, body in parts:
            if env_bytes is None and body.lstrip().startswith(b"<?xml"):
                env_bytes = body
            elif acl_bytes is None:
                acl_bytes = body

    if env_bytes is None or acl_bytes is None:
        raise ValueError("não consegui identificar envelope/ACL nas partes")

    try:
        env_txt = env_bytes.decode("utf-8", errors="replace").strip()
    except Exception as exc:  # pragma: no cover - extremely rare
        raise ValueError(f"falha a decodificar envelope: {exc}") from exc

    try:
        acl_txt = acl_bytes.decode("utf-8", errors="replace").strip()
    except Exception as exc:  # pragma: no cover
        raise ValueError(f"falha a decodificar ACL: {exc}") from exc

    return env_txt, acl_txt


# --------------------------------------------------------------------------- #
# Classe principal
# --------------------------------------------------------------------------- #
class HttpMtpServer:
    """
    Servidor HTTP-MTP (apenas INBOUND).

    Parameters
    ----------
    on_message:
        Callback opcional chamado para cada mensagem válida:
            async def on_message(env: Envelope, acl: AclMessage) -> None
        Se `None`, as mensagens são colocadas em `self.inbox`.

    client_max_size:
        Tamanho máximo do corpo (bytes).  Padrão 5 MiB.

    loop:
        Event loop opcional (para compatibilidade antiga; raro de usar).
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
            [
                self._logging_middleware,
                self._error_middleware,
            ]
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
            raise  # já mapeado
        except Exception as exc:  # qualquer outro → 400
            _LOG.exception("Erro não tratado no HTTP-MTP")
            raise web.HTTPBadRequest(text=str(exc)) from exc

    # ------------------------------------------------------------------ #
    # Handler principal (/acc)
    # ------------------------------------------------------------------ #
    async def _handle_post(self, request: web.Request) -> web.StreamResponse:
        # lê corpo bruto
        raw = await request.read()

        # prepara resposta imediata
        resp = web.Response(
            text="ok",
            status=200,
            content_type="text/plain",
            headers={"Cache-Control": "no-cache", "Connection": "close"},
        )

        # extrai boundary
        ctype = request.headers.get("Content-Type", "")
        m = _BOUNDARY_RE.search(ctype)
        if not m:
            _LOG.error("Sem boundary em Content-Type: %s", ctype)
            return resp  # responde 200 mesmo assim

        boundary_bytes = m.group(1).encode("utf-8", "ignore")

        # processa em background (não bloquear JADE Deliverer)
        asyncio.create_task(self._process_raw(raw, boundary_bytes))
        return resp

    # ------------------------------------------------------------------ #
    async def _process_raw(self, raw: bytes, boundary_bytes: bytes) -> None:
        """
        Parse raw multipart -> Envelope + AclMessage; entrega.
        Executa em task separada.
        """
        try:
            env_txt, acl_txt = _extract_envelope_acl(raw, boundary_bytes)
            env = Envelope.from_xml(env_txt)
            acl = parse_acl(acl_txt)
        except Exception:
            _LOG.exception("Falha a processar HTTP-MTP (descartado).")
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
    # Helper de arranque bloqueante (útil em scripts de teste)
    # ------------------------------------------------------------------ #
    async def run(self, host: str = "0.0.0.0", port: int = 7777):
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, host=host, port=port)
        _LOG.info("HttpMtpServer a escutar em http://%s:%d%s", host, port, ACC_ENDPOINT)
        await site.start()
        await asyncio.Event().wait()  # bloqueia para sempre


# --------------------------------------------------------------------------- #
# Função helper para o runtime (cria runner + site e devolve objetos)
# --------------------------------------------------------------------------- #
async def start_server(
    *,
    on_message: Optional[Callable[[Envelope, "AclMessage"], Awaitable[None]]] = None,
    bind_host: str = "0.0.0.0",
    port: int = 7777,
    loop: Optional[asyncio.AbstractEventLoop] = None,
    client_max_size: int = MAX_REQUEST_SIZE,
) -> tuple[HttpMtpServer, web.AppRunner, web.TCPSite]:
    """
    Cria e inicia um HttpMtpServer escutando em (bind_host, port).

    Retorna: (server, runner, site)
    """
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
# Standalone (debug manual)
# --------------------------------------------------------------------------- #
if __name__ == "__main__":  # pragma: no cover - modo manual
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=7777)
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG)

    async def _print_msg(env: Envelope, acl: "AclMessage"):
        _LOG.info("Mensagem recebida: %s -> %s", env.from_.name, acl.performative_upper)

    async def _main():
        server, runner, site = await start_server(
            on_message=_print_msg, bind_host=args.host, port=args.port
        )
        await asyncio.Event().wait()

    asyncio.run(_main())
