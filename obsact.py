#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Transpilador ObsAct -> Python.
Implementado com Lark usando parser LALR(1).
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

try:
    from lark import Lark, Transformer, Token, Tree
except ImportError as exc:
    raise SystemExit(
        "Dependência ausente: instale com `pip install -r requirements.txt` "
        "ou `pip install lark`."
    ) from exc

GRAMMAR = r'''
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
    alert_payload: STRING                -> payload_msg
                 | "(" STRING ")"       -> payload_msg_paren
                 | "(" STRING "," NAME ")" -> payload_msg_obs
    name_list: NAME ("," NAME)*

    ACTION.2: /ligar|desligar|verificar/i
    BEGIN_BLOCK: "__INICIO_BLOCO__"
    END_BLOCK: "__FIM_BLOCO__"
    BOOL.2: /TRUE|FALSE|True|False/
    AND: "&&"
    OPLOGIC: ">="|"<="|"=="|"!="|">"|"<"
    NAME: /[A-Za-z_][A-Za-z0-9_]*/
    NUMBER: /[0-9]+/
    STRING: /"([^"\\]|\\.)*"/

    %import common.WS
    %ignore WS
    %ignore /#[^\n]*/
    %ignore /\/\/[^\n]*/
'''


def preprocess(source: str) -> str:
    """
    Normaliza blocos da linguagem ObsAct.

    - Uma linha contendo apenas '.' vira o marcador interno de fim de bloco.
    - Uma linha que termina em 'entao' ou 'senao' recebe o marcador interno
      de início de bloco, permitindo vários comandos até o ponto isolado.
    """
    lines = []
    for line in source.splitlines():
        if re.fullmatch(r"\s*\.\s*", line):
            lines.append("__FIM_BLOCO__")
            continue
        if re.search(r"\b(entao|senao)\s*$", line, flags=re.IGNORECASE):
            lines.append(line + " __INICIO_BLOCO__")
        else:
            lines.append(line)
    return "\n".join(lines)


@dataclass
class Device:
    name: str
    observation: Optional[str] = None


class ASTBuilder(Transformer):

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

    def program(self, items: List[Any]) -> Tuple[str, List[Any], List[Any]]:
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

    def action(self, items: List[Any]) -> str:
        # Lark passa o literal reconhecido como Tree; o texto original aparece em children.
        return str(items[0]).lower() if items else ""

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
            item for item in items
            if not (isinstance(item, Token) and item.type in {"BEGIN_BLOCK", "END_BLOCK"})
        ]

    def obsact(self, items: List[Any]) -> Tuple[str, Any, List[Any], Optional[List[Any]]]:
        obs = items[0]
        then_block = items[1]
        else_block = items[2] if len(items) > 2 else None
        return ("if", obs, then_block, else_block)


class SemanticError(Exception):
    pass


class CodeGenerator:
    def __init__(self, ast: Tuple[str, List[Any], List[Any]]):
        self.ast = ast
        self.devices: Dict[str, Device] = {}
        self.variables: Set[str] = set()
        self.warnings: List[str] = []

    def validate(self) -> None:
        _, devices, statements = self.ast
        for _, name, observation in devices:
            if len(name) > 100:
                raise SemanticError(f"Nome de dispositivo com mais de 100 caracteres: {name}")
            if not re.fullmatch(r"[A-Za-z]+", name):
                self.warnings.append(
                    f"Aviso: o dispositivo '{name}' contém caracteres fora de [A-Za-z]. "
                    "A gramática original limita namedevice a letras."
                )
            if name in self.devices:
                raise SemanticError(f"Dispositivo declarado mais de uma vez: {name}")
            self.devices[name] = Device(name, observation)
            if observation:
                self.variables.add(observation)

        for stmt in statements:
            self._collect_and_validate_stmt(stmt)

    def _collect_and_validate_stmt(self, stmt: Any) -> None:
        kind = stmt[0]
        if kind == "set":
            target = stmt[1]
            if target[0] == "target":
                self.variables.add(target[1])
            else:
                device, obs = target[1], target[2]
                self._check_device(device)
                self.variables.add(obs)
            self._collect_expr(stmt[2])
        elif kind == "execute":
            self._check_device(stmt[2])
        elif kind == "alert":
            self._check_payload(stmt[1])
            self._check_device(stmt[2])
        elif kind == "broadcast":
            self._check_payload(stmt[1])
            for device in stmt[2]:
                self._check_device(device)
        elif kind == "if":
            self._collect_obs(stmt[1])
            for child in stmt[2]:
                self._collect_and_validate_stmt(child)
            if stmt[3]:
                for child in stmt[3]:
                    self._collect_and_validate_stmt(child)

    def _check_payload(self, payload: Any) -> None:
        msg = self._unquote(payload[1])
        if len(msg) > 100:
            raise SemanticError("Mensagem de alerta com mais de 100 caracteres.")
        if payload[2]:
            self.variables.add(payload[2])

    def _collect_obs(self, obs: Any) -> None:
        for cond in obs[1]:
            self._collect_expr(cond[1])
            self._collect_expr(cond[3])

    def _collect_expr(self, expr: Any) -> None:
        if expr[0] == "execute":
            self._check_device(expr[2])
        elif expr[0] == "var":
            self.variables.add(expr[1])

    def _check_device(self, name: str) -> None:
        if name not in self.devices:
            raise SemanticError(f"Dispositivo usado sem declaração: {name}")

    @staticmethod
    def _unquote(s: str) -> str:
        # Interpreta escapes simples no mesmo estilo de strings Python.
        return bytes(s[1:-1], "utf-8").decode("unicode_escape")

    def generate(self) -> str:
        self.validate()
        _, _devices, statements = self.ast
        lines: List[str] = []
        lines += self._runtime()
        lines.append("")
        lines.append("# Dispositivos declarados no programa ObsAct")
        device_names = list(self.devices.keys())
        lines.append(f"dispositivos = {device_names!r}")
        lines.append("estados = {nome: 0 for nome in dispositivos}")
        lines.append("")
        lines.append("# Observações/sensores. Valores não definidos começam em zero.")
        for var in sorted(self.variables):
            lines.append(f"{var} = 0")
        lines.append("")
        lines.append("def main():")
        if statements:
            for stmt in statements:
                lines += self._stmt(stmt, 1)
        else:
            lines.append("    pass")
        lines.append("")
        lines.append("if __name__ == '__main__':")
        lines.append("    main()")
        return "\n".join(lines) + "\n"

    def _runtime(self) -> List[str]:
        return [
            "# Código gerado automaticamente pelo transpilador ObsAct -> Python.",
            "# Não edite manualmente se pretender regerar este arquivo.",
            "",
            "def ligar(namedevice):",
            "    print(str(namedevice) + ' ligado!')",
            "    estados[str(namedevice)] = 1",
            "    return 1",
            "",
            "def desligar(namedevice):",
            "    print(str(namedevice) + ' desligado!')",
            "    estados[str(namedevice)] = 0",
            "    return 0",
            "",
            "def verificar(namedevice):",
            "    estado = estados.get(str(namedevice), 0)",
            "    if estado:",
            "        print(str(namedevice) + ' está ligado.')",
            "    else:",
            "        print(str(namedevice) + ' está desligado.')",
            "    return estado",
            "",
            "def alerta(namedevice, msg, var=None):",
            "    print(str(namedevice) + ' recebeu o alerta:')",
            "    if var is None:",
            "        print(str(msg))",
            "    else:",
            "        print(str(msg) + ' ' + str(var))",
        ]

    def _indent(self, level: int) -> str:
        return "    " * level

    def _stmt(self, stmt: Any, level: int) -> List[str]:
        kind = stmt[0]
        ind = self._indent(level)
        if kind == "set":
            target, expr = stmt[1], stmt[2]
            var_name = target[1] if target[0] == "target" else target[2]
            return [f"{ind}global {var_name}", f"{ind}{var_name} = {self._expr(expr)}"]
        if kind == "execute":
            return [f"{ind}{self._execute(stmt)}"]
        if kind == "alert":
            return [f"{ind}{self._alert(stmt[1], stmt[2])}"]
        if kind == "broadcast":
            lines = []
            for device in stmt[2]:
                lines.append(f"{ind}{self._alert(stmt[1], device)}")
            return lines
        if kind == "if":
            lines = [f"{ind}if {self._obs(stmt[1])}:"]
            if stmt[2]:
                for child in stmt[2]:
                    lines += self._stmt(child, level + 1)
            else:
                lines.append(self._indent(level + 1) + "pass")
            if stmt[3] is not None:
                lines.append(f"{ind}else:")
                if stmt[3]:
                    for child in stmt[3]:
                        lines += self._stmt(child, level + 1)
                else:
                    lines.append(self._indent(level + 1) + "pass")
            return lines
        raise SemanticError(f"Comando desconhecido: {stmt}")

    def _expr(self, expr: Any) -> str:
        kind = expr[0]
        if kind == "number":
            return str(expr[1])
        if kind == "bool":
            return "True" if expr[1] else "False"
        if kind == "var":
            return expr[1]
        if kind == "execute":
            return self._execute(expr)
        raise SemanticError(f"Expressão desconhecida: {expr}")

    def _execute(self, expr: Any) -> str:
        _, action, device = expr
        return f"{action}({device!r})"

    def _obs(self, obs: Any) -> str:
        parts = []
        for cond in obs[1]:
            _, left, op, right = cond
            parts.append(f"({self._expr(left)} {op} {self._expr(right)})")
        return " and ".join(parts)

    def _alert(self, payload: Any, device: str) -> str:
        _, msg, observation = payload
        if observation is None:
            return f"alerta({device!r}, {msg})"
        return f"alerta({device!r}, {msg}, {observation})"


def parse_source(source: str) -> Tuple[str, List[Any], List[Any]]:
    parser = Lark(GRAMMAR, parser="lalr", start="start", maybe_placeholders=False)
    tree = parser.parse(preprocess(source))
    return ASTBuilder().transform(tree)


def transpile_text(source: str) -> Tuple[str, List[str]]:
    ast = parse_source(source)
    generator = CodeGenerator(ast)
    code = generator.generate()
    return code, generator.warnings


def main(argv: Optional[List[str]] = None) -> int:
    cli = argparse.ArgumentParser(description="Transpilador ObsAct -> Python")
    cli.add_argument("entrada", help="arquivo .obs de entrada")
    cli.add_argument("-o", "--output", help="arquivo .py de saída")
    cli.add_argument("--print", action="store_true", help="imprime o Python gerado na saída padrão")
    args = cli.parse_args(argv)

    in_path = Path(args.entrada)
    try:
        source = in_path.read_text(encoding="utf-8")
        code, warnings = transpile_text(source)
    except Exception as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1

    for warning in warnings:
        print(warning, file=sys.stderr)

    if args.output:
        Path(args.output).write_text(code, encoding="utf-8")
    if args.print or not args.output:
        print(code)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
