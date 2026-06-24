"""Geracao do programa Python equivalente a partir da AST validada."""

from __future__ import annotations

from typing import Any, List

from parser import ProgramAst
from semantic import SemanticError, SemanticResult


class CodeGenerator:
    def __init__(self, program: ProgramAst, symbols: SemanticResult):
        self.program = program
        self.devices = symbols.devices
        self.variables = symbols.variables
        self.python_names = symbols.python_names

    def generate(self) -> str:
        """Gera o arquivo Python completo como texto."""
        _, _devices, statements = self.program
        lines: List[str] = []
        lines += self._runtime()
        lines.append("")
        lines.append("# Dispositivos declarados no programa ObsAct")
        device_names = list(self.devices.keys())
        lines.append(f"dispositivos = {device_names!r}")
        lines.append("estados = {nome: 0 for nome in dispositivos}")
        lines.append("")
        lines.append("def main():")
        if self.variables:
            lines.append("    # Observacoes nao definidas comecam em zero.")
            for variable in sorted(self.variables):
                lines.append(f"    {self._python_name(variable)} = 0")
        if statements:
            for statement in statements:
                lines += self._statement(statement, 1)
        elif not self.variables:
            lines.append("    pass")
        lines.append("")
        lines.append("if __name__ == '__main__':")
        lines.append("    main()")
        return "\n".join(lines) + "\n"

    @staticmethod
    def _runtime() -> List[str]:
        return [
            "# Codigo gerado automaticamente pelo transpilador ObsAct -> Python.",
            "# Nao edite manualmente se pretender regerar este arquivo.",
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
            "        print(str(namedevice) + ' esta ligado.')",
            "    else:",
            "        print(str(namedevice) + ' esta desligado.')",
            "    return estado",
            "",
            "def alerta(namedevice, msg, var=None):",
            "    print(str(namedevice) + ' recebeu o alerta:')",
            "    if var is None:",
            "        print(str(msg))",
            "    else:",
            "        print(str(msg) + ' ' + str(var))",
        ]

    @staticmethod
    def _indent(level: int) -> str:
        return "    " * level

    def _statement(self, statement: Any, level: int) -> List[str]:
        kind = statement[0]
        indent = self._indent(level)
        if kind == "set":
            target, expression = statement[1], statement[2]
            variable = target[1] if target[0] == "target" else target[2]
            return [
                f"{indent}{self._python_name(variable)} = {self._expression(expression)}"
            ]
        if kind == "execute":
            return [f"{indent}{self._execute(statement)}"]
        if kind == "alert":
            return [f"{indent}{self._alert(statement[1], statement[2])}"]
        if kind == "broadcast":
            return [
                f"{indent}{self._alert(statement[1], device)}"
                for device in statement[2]
            ]
        if kind == "if":
            lines = [f"{indent}if {self._observation(statement[1])}:"]
            for child in statement[2]:
                lines += self._statement(child, level + 1)
            if statement[3] is not None:
                lines.append(f"{indent}else:")
                for child in statement[3]:
                    lines += self._statement(child, level + 1)
            return lines
        raise SemanticError(f"Comando desconhecido: {statement}")

    def _expression(self, expression: Any) -> str:
        kind = expression[0]
        if kind == "number":
            return str(expression[1])
        if kind == "bool":
            return "True" if expression[1] else "False"
        if kind == "var":
            return self._python_name(expression[1])
        if kind == "execute":
            return self._execute(expression)
        raise SemanticError(f"Expressao desconhecida: {expression}")

    @staticmethod
    def _execute(expression: Any) -> str:
        _, action, device = expression
        return f"{action}({device!r})"

    def _observation(self, observation: Any) -> str:
        parts = []
        for condition in observation[1]:
            _, left, operator, right = condition
            parts.append(
                f"({self._expression(left)} {operator} {self._expression(right)})"
            )
        return " and ".join(parts)

    def _alert(self, payload: Any, device: str) -> str:
        _, message, observation = payload
        if observation is None:
            return f"alerta({device!r}, {message})"
        return (
            f"alerta({device!r}, {message}, "
            f"{self._python_name(observation)})"
        )

    def _python_name(self, name: str) -> str:
        return self.python_names[name]


def generate_python(program: ProgramAst, symbols: SemanticResult) -> str:
    """Atalho funcional para gerar Python."""
    return CodeGenerator(program, symbols).generate()
