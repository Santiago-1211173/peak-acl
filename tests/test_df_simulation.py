"""
manual_df_loopback.py
─────────────────────
Sobe um servidor HttpMtpServer local (simulando o DF JADE) e envia-lhe um
REQUEST (register …).  Imprime no ecrã o Envelope XML e a ACL recebidos para
verificação visual.
"""

import asyncio
import logging
import aiohttp
import aiohttp.web                      
from datetime import datetime

from peak_acl.message.aid import AgentIdentifier
from peak_acl.message.acl import AclMessage
from peak_acl.transport.http_mtp import HttpMtpServer
from peak_acl.transport.multipart import build_multipart
from peak_acl.serialize import dumps

# ─────────────── CONFIG LOGGING ─────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:%(name)s:%(message)s",
    force=True,
)

# ─────────────── AGENT-IDENTIFIERS (DF e PEAK) ──────────────────────
DF_AID = AgentIdentifier(
    "df@jade-host:1099/JADE",
    ["http://localhost:7777/acc"],
)
PEAK_AID = AgentIdentifier(
    "remote@jade-host:1200/JADE",
    ["http://localhost:56946/acc"],
)


# ─────────────── CONSTRUTOR DA MENSAGEM REQUEST/REGISTER ────────────
def make_register_msg() -> AclMessage:
    content = (
        f'((action {DF_AID.name} '
        f'(register (df-agent-description '
        f':name {PEAK_AID.name} '
        f':services (set (service-description :name echo :type generic))))))'
    )

    return AclMessage(
        performative="request",
        params={
            "sender":   f"(agent-identifier :name {PEAK_AID.name})",
            "receiver": f"(set (agent-identifier :name {DF_AID.name}))",
            "content":  f'"{content}"',
            "language": "fipa-sl0",
            "ontology": "FIPA-Agent-Management",
            "protocol": "fipa-request",
        },
    )


# ─────────────── CALLBACK QUE IMPRIME ENVELOPE + ACL ────────────────
async def on_msg(env, acl):
    print("\n-- CHEGOU AO «DF» -------------------------")
    print("Envelope XML:\n", env.to_xml())
    print("\nACL completa:\n", dumps(acl))
    print("-------------------------------------------\n")


# ─────────────── PROGRAMA PRINCIPAL (ASYNC) ─────────────────────────
async def main():
    # 1) Instancia e arranca servidor
    server = HttpMtpServer(on_msg)
    runner = aiohttp.web.AppRunner(server.app)      # ← .app, não mais server
    await runner.setup()
    await aiohttp.web.TCPSite(runner, "localhost", 7777).start()
    logging.info("Servidor HttpMtpServer (DF simulado) a escutar em :7777/acc")

    # 2) Constrói multipart (envelope+ACL)
    acl_msg = make_register_msg()
    writer, _ = build_multipart(DF_AID, PEAK_AID, acl_msg)

    # 3) Envia-o ao próprio servidor
    async with aiohttp.ClientSession() as sess:
        resp = await sess.post("http://localhost:7777/acc", data=writer)
        logging.info("POST devolveu %s %s", resp.status, await resp.text())

    # 4) Dá tempo para o callback imprimir, depois pára o servidor
    await asyncio.sleep(0.2)
    await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
