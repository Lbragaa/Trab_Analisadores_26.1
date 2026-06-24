"""Regras lexicas e pre-processamento da linguagem ObsAct.

O Lark executa o lexer internamente. Este modulo concentra os terminais da
gramatica e a normalizacao dos blocos antes da analise sintatica.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List


LEXER_GRAMMAR = r'''
    ACTION.2: /(?:ligar|desligar|verificar)\b/i
    BEGIN_BLOCK: "__INICIO_BLOCO__"
    END_BLOCK: "__FIM_BLOCO__"
    BOOL.2: /(?:TRUE|FALSE|True|False)\b/
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


def _without_comment(line: str) -> str:
    """Retorna a parte de codigo da linha, ignorando comentario fora de string."""
    in_string = False
    escaped = False
    index = 0

    while index < len(line):
        char = line[index]
        if escaped:
            escaped = False
        elif in_string and char == "\\":
            escaped = True
        elif char == '"':
            in_string = not in_string
        elif not in_string and char == "#":
            return line[:index]
        elif not in_string and line.startswith("//", index):
            return line[:index]
        index += 1

    return line


def preprocess(source: str) -> str:
    """Insere marcadores internos para tornar blocos explicitos ao parser."""
    lines: List[str] = []
    blocks: List[Dict[str, Any]] = []

    for line in source.splitlines():
        code = _without_comment(line)
        stripped = code.strip()
        if not stripped:
            lines.append(line)
            continue

        indent = len(line) - len(line.lstrip(" \t"))

        if stripped == ".":
            closed = False
            while blocks and blocks[-1]["header_indent"] >= indent:
                lines.append("__FIM_BLOCO__")
                blocks.pop()
                closed = True
            if not closed:
                if blocks:
                    # Ponto redundante depois de um if de uma linha.
                    continue
                lines.append(code)
            continue

        is_else = re.match(r"senao\b", stripped, flags=re.IGNORECASE) is not None
        while blocks:
            block = blocks[-1]
            dedented = block["body_indent"] is not None and indent < block["body_indent"]
            matching_else = is_else and indent == block["header_indent"]
            if not (dedented or matching_else):
                break
            lines.append("__FIM_BLOCO__")
            blocks.pop()

        if blocks and blocks[-1]["body_indent"] is None:
            blocks[-1]["body_indent"] = indent

        header = re.search(r"\b(entao|senao)\s*(\.)?\s*$", stripped, flags=re.IGNORECASE)
        if header:
            has_inline_dot = header.group(2) is not None
            normalized = re.sub(r"\.\s*$", "", code) if has_inline_dot else code
            lines.append(normalized.rstrip() + " __INICIO_BLOCO__")
            blocks.append(
                {
                    "header_indent": indent,
                    "body_indent": None,
                    "close_after_one": has_inline_dot,
                }
            )
            continue

        lines.append(line)
        if (
            blocks
            and blocks[-1]["close_after_one"]
            and re.search(r"\.\s*$", code)
        ):
            lines.append("__FIM_BLOCO__")
            blocks.pop()

    while blocks:
        lines.append("__FIM_BLOCO__")
        blocks.pop()

    return "\n".join(lines)
