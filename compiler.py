"""Coordenacao das etapas do transpilador ObsAct para Python."""

from __future__ import annotations

from typing import List, Tuple

from codegen import generate_python
from parser import parse_source
from semantic import analyze


def transpile_text(source: str) -> Tuple[str, List[str]]:
    """Executa parser, semantica e geracao sobre um texto ObsAct."""
    program = parse_source(source)
    symbols = analyze(program)
    code = generate_python(program, symbols)
    return code, symbols.warnings
