# src/peak_acl/df_manager.py
from __future__ import annotations

from typing import Iterable, Optional, Sequence, Tuple, Union, List

from .message.aid import AgentIdentifier
from .message.acl import AclMessage
from .transport.http_client import HttpMtpClient
from .content import decode_content
from . import sl0, fipa_am

__all__ = [
    "register", "deregister", "search_services",
    "decode_df_reply", "is_df_done_msg", "is_df_failure_msg",
    "extract_search_results",
]


# ------------------------------------------------------------------ #
# util
# ------------------------------------------------------------------ #
def _first_url(ai: AgentIdentifier) -> str:
    if not ai.addresses:
        raise ValueError(f"AID sem endereço HTTP: {ai}")
    return ai.addresses[0]


def _coerce_services(
    raw: Iterable[Union[Tuple[str, str], fipa_am.ServiceDescription]],
) -> list[fipa_am.ServiceDescription]:
    out: list[fipa_am.ServiceDescription] = []
    for item in raw:
        if isinstance(item, fipa_am.ServiceDescription):
            out.append(item)
        else:
            n, t = item
            out.append(fipa_am.ServiceDescription(name=n, type=t))
    return out


# ------------------------------------------------------------------ #
# builders + envio
# ------------------------------------------------------------------ #
async def register(
    *,
    my_aid: AgentIdentifier,
    df_aid: AgentIdentifier,
    services: Iterable[Union[Tuple[str, str], fipa_am.ServiceDescription]] = (),
    languages: Sequence[str] = (),
    ontologies: Sequence[str] = (),
    protocols: Sequence[str] = (),
    ownership: Sequence[str] = (),
    http_client: HttpMtpClient,
    df_url: Optional[str] = None,   # <<< retro-compatível; ignorado se None
) -> AclMessage:
    svc_objs = _coerce_services(services)
    ad = fipa_am.build_agent_description(
        aid=my_aid,
        services=svc_objs,
        languages=languages,
        ontologies=ontologies,
        protocols=protocols,
        ownership=ownership,
    )
    content = fipa_am.render_register_content(df_aid, ad)
    msg = AclMessage(
        performative="request",
        sender=my_aid,
        receivers=[df_aid],
        content=content,
        language="fipa-sl0",
        ontology="FIPA-Agent-Management",
        protocol="fipa-request",
    )
    await http_client.send(df_aid, my_aid, msg, df_url or _first_url(df_aid))
    return msg


async def deregister(
    *,
    my_aid: AgentIdentifier,
    df_aid: AgentIdentifier,
    http_client: HttpMtpClient,
    df_url: Optional[str] = None,
) -> AclMessage:
    inner = sl0.Action(
        actor=df_aid,
        act=sl0.Deregister(sl0.DfAgentDescription(name=my_aid)),
    )
    msg = AclMessage(
        performative="request",
        sender=my_aid,
        receivers=[df_aid],
        content=sl0.dumps(inner),
        language="fipa-sl0",
        ontology="FIPA-Agent-Management",
        protocol="fipa-request",
    )
    await http_client.send(df_aid, my_aid, msg, df_url or _first_url(df_aid))
    return msg


async def search_services(
    *,
    my_aid: AgentIdentifier,
    df_aid: AgentIdentifier,
    service_name: Optional[str] = None,
    service_type: Optional[str] = None,
    max_results: Optional[int] = None,
    http_client: HttpMtpClient,
    df_url: Optional[str] = None,
) -> AclMessage:
    """
    Envia REQUEST search ao DF.

    JADE exige sempre o slot :constraints, por isso incluímos
    (search-constraints :max-results X) — se max_results for None,
    usamos -1 (ilimitado).
    """
    # constrói parte services (template)
    svc_bits = []
    if service_name is not None:
        svc_bits.append(f":name {service_name}")
    if service_type is not None:
        svc_bits.append(f":type {service_type}")
    svc_part = ""
    if svc_bits:
        svc_part = f":services (set (service-description {' '.join(svc_bits)}))"

    # constraints
    mr = -1 if max_results is None else max_results
    constraints_part = f"(search-constraints :max-results {mr})"

    content = (
        f"((action (agent-identifier :name {df_aid.name} "
        f":addresses (sequence {_first_url(df_aid)})) "
        f"(search (df-agent-description {svc_part}) {constraints_part})))"
    )

    msg = AclMessage(
        performative="request",
        sender=my_aid,
        receivers=[df_aid],
        content=content,
        language="fipa-sl0",
        ontology="FIPA-Agent-Management",
        protocol="fipa-request",
    )
    await http_client.send(df_aid, my_aid, msg, df_url or _first_url(df_aid))
    return msg


# ------------------------------------------------------------------ #
# Decodificar replies DF
# ------------------------------------------------------------------ #
def decode_df_reply(msg: AclMessage):
    """
    Converte msg.content -> AST SL0; lida com ContentElementList.
    Retorna:
        sl0.Done | sl0.Failure | list[AgentDescription] | payload bruto
    """
    payload = decode_content(msg)

    # Desembrulha ContentElementList [(...)] → (...)
    while isinstance(payload, list) and len(payload) == 1:
        payload = payload[0]

    if isinstance(payload, str):
        return payload

    if isinstance(payload, sl0.Done):
        return payload

    if isinstance(payload, sl0.Failure):
        return payload

    if isinstance(payload, sl0.Result):
        return extract_search_results_from_value(payload.value) or payload

    # Alguns DFs podem devolver diretamente lista de df-agent-description
    if isinstance(payload, list):
        # tenta mapear tudo para AgentDescription
        ads = []
        for it in payload:
            if isinstance(it, sl0.DfAgentDescription):
                from . import fipa_am
                ads.append(fipa_am.from_sl0(it))  # type: ignore[arg-type]
        if ads:
            return ads

    return payload



def is_df_done_msg(msg: AclMessage) -> bool:
    from . import sl0 as _sl0
    return isinstance(decode_df_reply(msg), _sl0.Done)


def is_df_failure_msg(msg: AclMessage) -> bool:
    from . import sl0 as _sl0
    return isinstance(decode_df_reply(msg), _sl0.Failure)


def extract_search_results(msg: AclMessage) -> List[fipa_am.AgentDescription]:
    """
    Se a mensagem for resultado de search, devolve lista de AgentDescription.
    """
    payload = decode_content(msg)
    if isinstance(payload, sl0.Result):
        ads = extract_search_results_from_value(payload.value)
        return ads or []
    return []


def extract_search_results_from_value(val) -> Optional[List[fipa_am.AgentDescription]]:
    """
    Recebe payload.value dum Result SL0; tenta extrair lista de ADs.
    """
    from . import sl0 as _sl0

    ads: List[fipa_am.AgentDescription] = []

    if isinstance(val, _sl0.DfAgentDescription):
        ads.append(fipa_am.from_sl0(val))  # type: ignore[arg-type]
        return ads

    # val pode ser ['set', dfad,...] ou lista pura; ou AST parseado (lista python)
    if isinstance(val, list):
        items = val[1:] if val and isinstance(val[0], str) and val[0].lower() == "set" else val
        for it in items:
            # se já é DfAgentDescription
            if isinstance(it, _sl0.DfAgentDescription):
                ads.append(fipa_am.from_sl0(it))  # type: ignore[arg-type]
            else:
                # tenta reconstruir AST e converter
                try:
                    obj = _sl0._build_ast(it)  # pyright: ignore [reportPrivateUsage]
                    if isinstance(obj, _sl0.DfAgentDescription):
                        ads.append(fipa_am.from_sl0(obj))  # type: ignore[arg-type]
                except Exception:
                    pass
        return ads if ads else None

    return None
