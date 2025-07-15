"""
http_client.py
──────────────
Cliente assíncrono FIPA HTTP-MTP.

• Empacota Envelope + ACL em multipart/mixed
• POST ao ACC remoto com retries e back-off exponencial
• Gere e reutiliza um aiohttp.ClientSession (boa prática)
"""

from __future__ import annotations

import asyncio
import logging
import random
from typing import Optional

import aiohttp
from aiohttp import ClientTimeout

from ..message.aid import AgentIdentifier
from ..message.acl import AclMessage
from .multipart import build_multipart

__all__ = ["HttpMtpClient", "HttpMtpError"]

_LOG = logging.getLogger("peak_acl.http_mtp_client")


class HttpMtpError(RuntimeError):
    """Falha definitiva ao enviar a mensagem para o ACC."""


class HttpMtpClient:
    def __init__(
        self,
        *,
        retries: int = 3,
        backoff_base: float = 0.8,
        backoff_cap: float = 4.0,
        timeout: float = 10.0,
        session: Optional[aiohttp.ClientSession] = None,
    ):
        """
        Parameters
        ----------
        retries          número de tentativas antes de falhar
        backoff_base     segundos iniciais para back-off exponencial
        backoff_cap      valor máximo de back-off (segundos)
        timeout          timeout de cada pedido (segundos)
        session          opcional: fornece uma ClientSession externa
        """
        self.retries = retries
        self.backoff_base = backoff_base
        self.backoff_cap = backoff_cap
        self._owns_session = session is None
        self.session = session or aiohttp.ClientSession(
            timeout=ClientTimeout(total=timeout)
        )

    async def send(
        self,
        to_ai: AgentIdentifier,
        from_ai: AgentIdentifier,
        acl_msg: AclMessage,
        acc_url: str,
    ) -> None:

        body, ctype = build_multipart(to_ai, from_ai, acl_msg)
        headers = {
            "Content-Type": ctype,
            "Cache-Control": "no-cache",
            "Mime-Version": "1.0",
        }

        attempt = 0
        delay = self.backoff_base
        while True:
            try:
                print("──── Cabeçalhos HTTP enviados ────")
                for k, v in headers.items():
                    print(f"{k}: {v}")
                print("──── Início do corpo (primeiros 400 bytes) ────")
                print(body[:400].decode("utf-8", errors="replace"))
                print("──── Fim debug ────")

                async with self.session.post(acc_url, data=body, headers=headers) as resp:
                    if resp.status == 200:
                        _LOG.info("Enviado para %s (status 200)", acc_url)
                        return
                    raise HttpMtpError(f"ACC devolveu {resp.status}")
            except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
                attempt += 1
                if attempt > self.retries:
                    raise HttpMtpError(
                        f"Falhou após {self.retries} tentativas: {exc}"
                    ) from exc

                jitter = random.uniform(0, 0.3 * delay)
                _LOG.warning("Tentativa %d falhou (%s); retry em %.1fs",
                             attempt, exc, delay + jitter)
                await asyncio.sleep(delay + jitter)
                delay = min(delay * 2, self.backoff_cap)

    # ------------------------------------------------------------------
    async def close(self):
        """Fecha a ClientSession se foi criada internamente."""
        if self._owns_session and not self.session.closed:
            await self.session.close()

    # Context-manager assíncrono
    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        await self.close()
