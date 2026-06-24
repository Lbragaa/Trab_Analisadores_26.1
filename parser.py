"""Gramatica sintatica, construcao da AST e parser LALR(1) do ObsAct."""

from __future__ import annotations

from typing import Any, List, Optional, Tuple

try:
    from lark import Lark, Token, Transformer
except ImportError as exc:
    raise SystemExit(
        "Dependencia ausente: use `python -m pip install -r requirements.txt`."
    ) from exc

from lexer import LEXER_GRAMMAR, preprocess


PARSER_GRAMMAR = r'''
    start: program
    program: device+ statement*

    device: "dispositivo"i ":"? "{" NAME ("," NAME)? "}"
    statement: cmd "."?
    ?cmd: attrib
        | obsact
        | act

    attrib: "set"i target "=" value
    target: NAME                         -> target_name
          | "{" NAME "," NAME "}"       -> target_device_obs

    ?value: NUMBER                       -> number
          | BOOL                         -> bool_value
          | execute
          | NAME                         -> var_ref

    obsact: "se"i obs "entao"i block ("senao"i block)?
    block: BEGIN_BLOCK cmd_stmt+ END_BLOCK -> multi_block
         | cmd                           -> single_block
    cmd_stmt: cmd "."?

    obs: condition (AND condition)*
    condition: expr OPLOGIC expr
    ?expr: NUMBER                        -> number
         | BOOL                          -> bool_value
         | execute
         | NAME                          -> var_ref

    ?act: execute
        | alert
        | broadcast

    execute: ACTION call_device
    call_device: NAME
               | "(" NAME ")"

    alert: "enviar"i "alerta"i alert_payload NAME
    broadcast: "enviar"i "alerta"i alert_payload "para"i "todos"i ":" name_list
    alert_payload: STRING                    -> payload_msg
                 | "(" STRING ")"           -> payload_msg_paren
                 | "(" STRING "," NAME ")"  -> payload_msg_obs
    name_list: NAME ("," NAME)*
'''

GRAMMAR = PARSER_GRAMMAR + "\n" + LEXER_GRAMMAR
ProgramAst = Tuple[str, List[Any], List[Any]]
_PARSER = Lark(GRAMMAR, parser="lalr", start="start", maybe_placeholders=False)


class ASTBuilder(Transformer):
    """Converte a arvore concreta do Lark em tuplas simples de AST."""

    def start(self, items: List[Any]) -> Any:
        return items[0]

    def NAME(self, token: Token) -> str:
        return str(token)

    def NUMBER(self, token: Token) -> int:
        return int(token)

    def STRING(self, token: Token) -> str:
        return str(token)

    def BOOL(self, token: Token) -> bool:
        return str(token).lower() == "true"

    def OPLOGIC(self, token: Token) -> str:
        return str(token)

    def ACTION(self, token: Token) -> str:
        return str(token).lower()

    def device(self, items: List[Any]) -> Tuple[str, str, Optional[str]]:
        if len(items) == 1:
            return ("device", items[0], None)
        return ("device", items[0], items[1])

    def program(self, items: List[Any]) -> ProgramAst:
        devices, statements = [], []
        for item in items:
            if isinstance(item, tuple) and item[0] == "device":
                devices.append(item)
            elif item is not None:
                statements.append(item)
        return ("program", devices, statements)

    def statement(self, items: List[Any]) -> Any:
        return items[0]

    def target_name(self, items: List[Any]) -> Tuple[str, str]:
        return ("target", items[0])

    def target_device_obs(self, items: List[Any]) -> Tuple[str, str, str]:
        return ("target_device_obs", items[0], items[1])

    def number(self, items: List[Any]) -> Tuple[str, int]:
        return ("number", items[0])

    def bool_value(self, items: List[Any]) -> Tuple[str, bool]:
        return ("bool", items[0])

    def var_ref(self, items: List[Any]) -> Tuple[str, str]:
        return ("var", items[0])

    def attrib(self, items: List[Any]) -> Tuple[str, Any, Any]:
        return ("set", items[0], items[1])

    def call_device(self, items: List[Any]) -> str:
        return items[0]

    def execute(self, items: List[Any]) -> Tuple[str, str, str]:
        return ("execute", str(items[0]).lower(), items[1])

    def payload_msg(self, items: List[Any]) -> Tuple[str, str, Optional[str]]:
        return ("payload", items[0], None)

    def payload_msg_paren(self, items: List[Any]) -> Tuple[str, str, Optional[str]]:
        return ("payload", items[0], None)

    def payload_msg_obs(self, items: List[Any]) -> Tuple[str, str, str]:
        return ("payload", items[0], items[1])

    def alert_payload(self, items: List[Any]) -> Any:
        return items[0]

    def alert(self, items: List[Any]) -> Tuple[str, Any, str]:
        return ("alert", items[0], items[1])

    def name_list(self, items: List[Any]) -> List[str]:
        return list(items)

    def broadcast(self, items: List[Any]) -> Tuple[str, Any, List[str]]:
        return ("broadcast", items[0], items[1])

    def condition(self, items: List[Any]) -> Tuple[str, Any, str, Any]:
        return ("condition", items[0], items[1], items[2])

    def obs(self, items: List[Any]) -> Tuple[str, List[Any]]:
        conditions = [item for item in items if not isinstance(item, Token)]
        return ("and", conditions)

    def single_block(self, items: List[Any]) -> List[Any]:
        return [items[0]]

    def cmd_stmt(self, items: List[Any]) -> Any:
        return items[0]

    def multi_block(self, items: List[Any]) -> List[Any]:
        return [
            item
            for item in items
            if not (
                isinstance(item, Token)
                and item.type in {"BEGIN_BLOCK", "END_BLOCK"}
            )
        ]

    def obsact(
        self, items: List[Any]
    ) -> Tuple[str, Any, List[Any], Optional[List[Any]]]:
        observation = items[0]
        then_block = items[1]
        else_block = items[2] if len(items) > 2 else None
        return ("if", observation, then_block, else_block)


def parse_source(source: str) -> ProgramAst:
    """Analisa o texto ObsAct e retorna sua AST."""
    tree = _PARSER.parse(preprocess(source))
    return ASTBuilder().transform(tree)
