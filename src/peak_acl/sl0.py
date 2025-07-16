# src/peak_acl/sl0.py
"""
Mini-implementação FIPA-SL0 suficiente para interagir com DF/AMS via JADE.

Suporta:
- (action <AID> (register|deregister|modify <df-agent-description>))
- (action <AID> (search <df-agent-description> [<max-results>]))
- (done <exp>)  ; usado em INFORM de confirmação
- (failure <reason>) ; mapeio simples
- Estruturas agent-identifier, df-agent-description, service-description.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Iterator, List, Optional, Sequence, Tuple, Union

from .message.aid import AgentIdentifier


# ------------------------------------------------------------------ #
# AST dataclasses
# ------------------------------------------------------------------ #
@dataclass
class ServiceDescription:
    name: Optional[str] = None
    type: Optional[str] = None
    # TODO: add props, languages, ontologies, protocols quando precisares


@dataclass
class DfAgentDescription:
    name: AgentIdentifier
    services: List[ServiceDescription] = field(default_factory=list)


@dataclass
class Register:
    dfad: DfAgentDescription


@dataclass
class Deregister:
    dfad: DfAgentDescription


@dataclass
class Modify:
    dfad: DfAgentDescription


@dataclass
class Search:
    template: DfAgentDescription
    max_results: Optional[int] = None


@dataclass
class Action:
    actor: AgentIdentifier            # agente alvo da acção (normalmente DF/AMS)
    act: Union[Register, Deregister, Modify, Search]


@dataclass
class Done:
    what: Any                         # normalmente Action


@dataclass
class Failure:
    reason: Any                       # livre


# ------------------------------------------------------------------ #
# Public API (alto nível)
# ------------------------------------------------------------------ #
def build_register_content(my: AgentIdentifier,
                           services: Sequence[Tuple[str, str]],
                           *,
                           df: AgentIdentifier) -> str:
    """Conveniente: gera string SL0 ((action (agent-identifier...) (register ...)))."""
    sd = [ServiceDescription(name=n, type=t) for n, t in services]
    expr = Action(actor=df, act=Register(DfAgentDescription(name=my, services=sd)))
    return dumps(expr)


def is_done(expr: Any) -> bool:
    """True se parse SL0 devolveu Done()."""
    return isinstance(expr, Done)


# ------------------------------------------------------------------ #
# Serializer
# ------------------------------------------------------------------ #
def dumps(obj: Any) -> str:
    """Serializa AST SL0 → string (SEM aspas exteriores)."""
    return _render(obj)


def _render(obj: Any) -> str:
    if isinstance(obj, Action):
        return f"(action {_render_aid(obj.actor)} {_render(obj.act)})"
    if isinstance(obj, Register):
        return f"(register {_render_dfad(obj.dfad)})"
    if isinstance(obj, Deregister):
        return f"(deregister {_render_dfad(obj.dfad)})"
    if isinstance(obj, Modify):
        return f"(modify {_render_dfad(obj.dfad)})"
    if isinstance(obj, Search):
        tail = f" {_render_dfad(obj.template)}"
        if obj.max_results is not None:
            tail += f" {obj.max_results}"
        return f"(search{tail})"
    if isinstance(obj, Done):
        return f"(done {_render(obj.what)})"
    if isinstance(obj, Failure):
        return f"(failure {_render(obj.reason)})"
    if isinstance(obj, DfAgentDescription):
        return _render_dfad(obj)
    if isinstance(obj, ServiceDescription):
        return _render_sd(obj)
    if isinstance(obj, AgentIdentifier):
        return _render_aid(obj)
    # atoms / strings
    return str(obj)


def _render_aid(aid: AgentIdentifier) -> str:
    if aid.addresses:
        seq = " ".join(aid.addresses)
        return f"(agent-identifier :name {aid.name} :addresses (sequence {seq}))"
    return f"(agent-identifier :name {aid.name} :addresses (sequence))"


def _render_sd(sd: ServiceDescription) -> str:
    parts = ["(service-description"]
    if sd.name is not None:
        parts.append(f" :name {sd.name}")
    if sd.type is not None:
        parts.append(f" :type {sd.type}")
    parts.append(")")
    return "".join(parts)


def _render_dfad(dfad: DfAgentDescription) -> str:
    parts = ["(df-agent-description :name ", _render_aid(dfad.name)]
    if dfad.services:
        parts.append(" :services (set")
        for sd in dfad.services:
            parts.append(f" {_render_sd(sd)}")
        parts.append(")")
    parts.append(")")
    return "".join(parts)


# ------------------------------------------------------------------ #
# Parser (tokenize → lista → AST)
# Robusto a whitespace / quebras de linha / escapes básicos.
# ------------------------------------------------------------------ #
def loads(src: str) -> Any:
    """
    Parse string SL0 → AST Python.
    Levanta ValueError em erro.
    """
    tokens = list(_tokenize(src))
    expr, pos = _parse_expr(tokens, 0)
    if pos != len(tokens):
        raise ValueError("Tokens sobrando no fim do SL0.")
    return _build_ast(expr)


# ---------- tokenizer ------------------------------------------------------- #
def _tokenize(s: str) -> Iterator[str]:
    i, n = 0, len(s)
    while i < n:
        c = s[i]
        if c.isspace():
            i += 1
            continue
        if c in "()":
            yield c
            i += 1
            continue
        if c == '"':
            # string
            i += 1
            buf = []
            while i < n:
                c = s[i]
                if c == '\\':
                    if i + 1 < n:
                        buf.append(s[i + 1])
                        i += 2
                        continue
                if c == '"':
                    i += 1
                    break
                buf.append(c)
                i += 1
            yield '"' + "".join(buf) + '"'
            continue
        # atom
        j = i
        while j < n and not s[j].isspace() and s[j] not in "()":
            j += 1
        yield s[i:j]
        i = j


# ---------- recursive list parser ------------------------------------------ #
def _parse_expr(toks: List[str], pos: int):
    if pos >= len(toks):
        raise ValueError("Fim inesperado.")
    t = toks[pos]
    if t == "(":
        lst: List[Any] = []
        pos += 1
        while pos < len(toks) and toks[pos] != ")":
            sub, pos = _parse_expr(toks, pos)
            lst.append(sub)
        if pos >= len(toks):
            raise ValueError("Parêntese não fechado.")
        pos += 1  # consume ')'
        return lst, pos
    elif t == ")":
        raise ValueError("')' inesperado.")
    else:
        # atom or string -> strip quotes
        if t.startswith('"') and t.endswith('"') and len(t) >= 2:
            return t[1:-1], pos + 1
        return t, pos + 1


# ---------- AST builder ---------------------------------------------------- #
def _build_ast(e: Any) -> Any:
    """
    Converte lista genérica ['action', <aid>, <body>] → instâncias dataclasses.
    Usa matching leniente (case-insensitive).
    """
    if not isinstance(e, list) or not e:
        return e

    head = str(e[0]).lower()

    if head == "action" and len(e) >= 3:
        actor = _build_aid(e[1])
        act = _build_ast(e[2])
        return Action(actor=actor, act=act)

    if head == "register" and len(e) >= 2:
        return Register(_build_dfad(e[1]))

    if head == "deregister" and len(e) >= 2:
        return Deregister(_build_dfad(e[1]))

    if head == "modify" and len(e) >= 2:
        return Modify(_build_dfad(e[1]))

    if head == "search" and len(e) >= 2:
        templ = _build_dfad(e[1])
        maxres = None
        if len(e) >= 3:
            try:
                maxres = int(e[2])
            except Exception:
                pass
        return Search(template=templ, max_results=maxres)

    if head == "done" and len(e) >= 2:
        return Done(_build_ast(e[1]))

    if head == "failure" and len(e) >= 2:
        return Failure(_build_ast(e[1]))

    if head == "df-agent-description":
        return _build_dfad(e)

    if head == "service-description":
        return _build_sd(e)

    if head == "agent-identifier":
        return _build_aid(e)

    # generic fallback: lista de sub‑expr
    return [ _build_ast(x) for x in e ]


def _build_aid(e: Any) -> AgentIdentifier:
    if not isinstance(e, list):
        # simples atom?
        return AgentIdentifier(str(e), [])
    # formato (:name foo :addresses (sequence url...))
    name = None
    addrs: List[str] = []
    i = 1  # skip 'agent-identifier'
    while i < len(e):
        if isinstance(e[i], str) and e[i].lower() == ":name" and i + 1 < len(e):
            name = str(e[i + 1])
            i += 2
        elif isinstance(e[i], str) and e[i].lower() == ":addresses" and i + 1 < len(e):
            addrs = _extract_sequence(e[i + 1])
            i += 2
        else:
            i += 1
    if name is None:
        raise ValueError("agent-identifier sem :name")
    return AgentIdentifier(name, addrs)


def _build_sd(e: Any) -> ServiceDescription:
    sd = ServiceDescription()
    i = 1
    while i < len(e):
        tag = e[i]
        if isinstance(tag, str):
            lt = tag.lower()
            if lt == ":name" and i + 1 < len(e):
                sd.name = str(e[i + 1])
                i += 2
                continue
            if lt == ":type" and i + 1 < len(e):
                sd.type = str(e[i + 1])
                i += 2
                continue
        i += 1
    return sd


def _build_dfad(e: Any) -> DfAgentDescription:
    # e começa por 'df-agent-description' ou já foi passado slot value
    if not isinstance(e, list):
        raise ValueError("df-agent-description malformado")
    # se a chamada veio de 'register', o 1º elem e[0] == 'df-agent-description'
    # mas se vier de slot value, e é sublista; tratamos ambos
    if isinstance(e[0], str) and e[0].lower() != "df-agent-description":
        # sublista: e = [':name', AID, ':services', (set ...)]
        items = ["df-agent-description"] + e
        e = items
    name: Optional[AgentIdentifier] = None
    svcs: List[ServiceDescription] = []
    i = 1
    while i < len(e):
        tag = e[i]
        if isinstance(tag, str):
            lt = tag.lower()
            if lt == ":name" and i + 1 < len(e):
                name = _build_aid(e[i + 1])
                i += 2
                continue
            if lt == ":services" and i + 1 < len(e):
                svcs = _extract_services(e[i + 1])
                i += 2
                continue
        i += 1
    if name is None:
        raise ValueError("df-agent-description sem :name")
    return DfAgentDescription(name=name, services=svcs)


def _extract_sequence(e: Any) -> List[str]:
    # e pode ser ['sequence', url1, url2] ou lista directa
    if isinstance(e, list) and e and isinstance(e[0], str) and e[0].lower() == "sequence":
        return [str(x) for x in e[1:]]
    if isinstance(e, list):
        return [str(x) for x in e]
    return [str(e)]


def _extract_services(e: Any) -> List[ServiceDescription]:
    # e pode ser ['set', <sd>, <sd>...] ou lista directa
    items = e
    if isinstance(e, list) and e and isinstance(e[0], str) and e[0].lower() == "set":
        items = e[1:]
    if not isinstance(items, list):
        items = [items]
    return [_build_sd(x) for x in items]
