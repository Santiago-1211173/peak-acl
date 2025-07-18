"""
peak_acl.router
===============

Função utilitária que recebe (env, acl) e devolve (kind, payload)
segundo a semântica definida em events.Kind.

Mantém TODA a lógica de:
  • distinguir DF/externo
  • SL0 decode
  • df_manager.decode_df_reply()
"""

from __future__ import annotations
from typing import Tuple, Any

from .events import Kind
from .message.envelope import Envelope
from .message.acl import AclMessage
from .message.aid import AgentIdentifier
from . import df_manager, content as content_utils, sl0


def classify_message(
    env: Envelope,
    acl: AclMessage,
    df_aid: AgentIdentifier | None,
) -> Tuple[Kind, Any]:
    """Devolve (kind, payload) conforme tabela Kind."""
    sender_is_df = df_aid is not None and env.from_.name == df_aid.name

    # ------------------------------------------------------------------ #
    # Mensagens vindas do DF
    # ------------------------------------------------------------------ #
    if sender_is_df:
        perf = acl.performative_upper

        if perf == "NOT-UNDERSTOOD":
            return "df-not-understood", acl.get("content", "<sem content>")

        payload = df_manager.decode_df_reply(acl)

        if isinstance(payload, sl0.Done):
            return "df-done", payload

        if isinstance(payload, sl0.Failure):
            return "df-failure", payload

        if isinstance(payload, list):        # lista de AgentDescription
            return "df-result", payload

        # fallback genérico
        return "df", payload

    # ------------------------------------------------------------------ #
    # Mensagens de outros agentes
    # ------------------------------------------------------------------ #
    lang = acl.get("language", "").lower() if "language" in acl else ""

    if lang == "fipa-sl0":
        try:
            payload = content_utils.decode_content(acl)
            return "ext-sl0", payload
        except Exception as exc:             # payload inválido
            return "ext-raw", f"(SL0 inválido) {exc}: {acl.get('content','')}"
    else:
        return "ext-raw", acl.get("content", "<sem content>")
