#!/usr/bin/env python3
"""Interface de linha de comando do transpilador ObsAct para Python."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from compiler import transpile_text
from semantic import SemanticError

__all__ = ["SemanticError", "main", "transpile_text"]


def main(argv: Optional[List[str]] = None) -> int:
    cli = argparse.ArgumentParser(description="Transpilador ObsAct -> Python")
    cli.add_argument("entrada", help="arquivo .obsact de entrada")
    cli.add_argument("-o", "--output", help="arquivo .py de saida")
    cli.add_argument(
        "--print",
        action="store_true",
        help="imprime o Python gerado na saida padrao",
    )
    args = cli.parse_args(argv)

    input_path = Path(args.entrada)
    try:
        source = input_path.read_text(encoding="utf-8-sig")
        code, warnings = transpile_text(source)
        if args.output:
            Path(args.output).write_text(code, encoding="utf-8")
    except Exception as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1

    for warning in warnings:
        print(warning, file=sys.stderr)

    if args.print or not args.output:
        print(code)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
