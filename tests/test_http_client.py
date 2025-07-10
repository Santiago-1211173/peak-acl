"""
manual_client_loopback.py
Envia uma ACL (inform) com HttpMtpClient para um HttpMtpServer local
e imprime o Envelope XML + ACL ao chegar.
"""

import asyncio
import logging
import aiohttp.web
from datetime import datetime

from peak_acl.message.aid import AgentIdentifier
from peak_acl.parse import parse
from peak_acl.serialize import dumps
from peak_acl.transport.http_mtp import HttpMtpServer
from peak_acl.transport.http_client import HttpMtpClient

# ───────────── logging visível ───────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:%(name)s:%(message)s",
    force=True,
)

# ───────────── AID & ACL --------------------------------------------
TO_AID   = AgentIdentifier("receiver@host:7777/JADE",
                           ["http://localhost:7777/acc"])
FROM_AID = AgentIdentifier("sender@host:56946/JADE",
                           ["http://localhost:56946/acc"])

ACL_MSG = parse('(inform :sender sender :receiver receiver :content "hello")')


# ───────────── callback que imprime envelope + acl ───────────────────
async def on_msg(env, acl):
    print("\n=== ENVELOPE XML ===\n", env.to_xml())
    print("\n=== ACL STRING ===\n", dumps(acl), "\n")


# ───────────── programa principal ────────────────────────────────────
async def main():
    # 1) subir servidor local
    server = HttpMtpServer(on_msg)
    runner = aiohttp.web.AppRunner(server.app)       # composição
    await runner.setup()
    await aiohttp.web.TCPSite(runner, "localhost", 7777).start()
    logging.info("HttpMtpServer a escutar em http://localhost:7777/acc")

    # 2) enviar mensagem com HttpMtpClient
    async with HttpMtpClient(retries=1) as client:
        await client.send(TO_AID, FROM_AID, ACL_MSG, "http://localhost:7777/acc")

    # 3) dar tempo ao callback e encerrar
    await asyncio.sleep(0.2)
    await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
