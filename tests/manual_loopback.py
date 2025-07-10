# tests/manual_loopback.py  (versão actualizada)

import asyncio, logging, aiohttp

from peak_acl.transport.http_mtp import HttpMtpServer
from peak_acl.message.aid import AgentIdentifier
from peak_acl.parse import parse
from peak_acl.serialize import dumps
from peak_acl.transport.multipart import build_multipart

logging.basicConfig(level=logging.INFO)


async def on_msg(env, acl):
    print("\n=== ENVELOPE XML ===\n", env.to_xml())
    print("\n=== ACL STRING ===\n", dumps(acl), "\n")

async def main():
    # ── subir servidor ─────────────────────────────────────────────
    server = HttpMtpServer(on_msg)
    runner = aiohttp.web.AppRunner(server)
    await runner.setup()
    await aiohttp.web.TCPSite(runner, "localhost", 7777).start()

    # ── construir mensagem dinâmica ────────────────────────────────
    to_ai   = AgentIdentifier("receiver@host:7778/JADE",
                              ["http://localhost:7777/acc"])
    from_ai = AgentIdentifier("sender@host:56946/JADE",
                              ["http://localhost:56946/acc"])

    acl_msg = parse('(inform :sender sender :receiver receiver :content "ok")')
    writer, _ = build_multipart(to_ai, from_ai, acl_msg)

    async with aiohttp.ClientSession() as s:
        r = await s.post("http://localhost:7777/acc", data=writer)
        print("POST status →", r.status, await r.text())

    await runner.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
