"""Validacao semantica e tabela de simbolos do ObsAct."""

from __future__ import annotations

import ast
import keyword
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set

from parser import ProgramAst


class SemanticError(Exception):
    """Erro encontrado depois que a sintaxe ja foi reconhecida."""


@dataclass(frozen=True)
class Device:
    name: str
    observation: Optional[str] = None


@dataclass
class SemanticResult:
    devices: Dict[str, Device]
    variables: Set[str]
    python_names: Dict[str, str]
    warnings: List[str]


class SemanticAnalyzer:
    OBSERVATION_RE = re.compile(r"[A-Za-z][A-Za-z0-9_]*")
    PYTHON_RESERVED = {
        "alerta",
        "desligar",
        "dispositivos",
        "estados",
        "ligar",
        "main",
        "verificar",
    }

    def __init__(self, program: ProgramAst):
        self.program = program
        self.devices: Dict[str, Device] = {}
        self.variables: Set[str] = set()
        self.python_names: Dict[str, str] = {}
        self.warnings: List[str] = []

    def analyze(self) -> SemanticResult:
        """Valida a AST e devolve os simbolos necessarios para a geracao."""
        _, devices, statements = self.program
        for _, name, observation in devices:
            self._declare_device(name, observation)

        for statement in statements:
            self._validate_statement(statement)

        self._build_python_names()
        return SemanticResult(
            devices=self.devices,
            variables=self.variables,
            python_names=self.python_names,
            warnings=self.warnings,
        )

    def _declare_device(self, name: str, observation: Optional[str]) -> None:
        if len(name) > 100:
            raise SemanticError(f"Nome de dispositivo com mais de 100 caracteres: {name}")
        if not re.fullmatch(r"[A-Za-z]+", name):
            raise SemanticError(
                f"Nome de dispositivo invalido; use somente letras: {name}"
            )
        if name in self.devices:
            raise SemanticError(f"Dispositivo declarado mais de uma vez: {name}")
        if observation:
            self._validate_observation_name(observation)

        self.devices[name] = Device(name, observation)
        if observation:
            self.variables.add(observation)

    def _validate_statement(self, statement: Any) -> None:
        kind = statement[0]
        if kind == "set":
            self._validate_assignment(statement)
        elif kind == "execute":
            self._check_device(statement[2])
        elif kind == "alert":
            self._check_payload(statement[1])
            self._check_device(statement[2])
        elif kind == "broadcast":
            self._check_payload(statement[1])
            for device in statement[2]:
                self._check_device(device)
        elif kind == "if":
            self._validate_observation(statement[1])
            for child in statement[2]:
                self._validate_statement(child)
            if statement[3]:
                for child in statement[3]:
                    self._validate_statement(child)

    def _validate_assignment(self, statement: Any) -> None:
        target, expression = statement[1], statement[2]
        if target[0] == "target":
            observation = target[1]
            self._validate_observation_name(observation)
            if expression[0] == "execute":
                self._validate_expression(expression)
                self.variables.add(observation)
                return
            self._require_variable(observation)
        else:
            device, observation = target[1], target[2]
            self._check_device(device)
            self._validate_observation_name(observation)
            self._require_variable(observation)
            if self.devices[device].observation != observation:
                raise SemanticError(
                    f"A observacao '{observation}' nao pertence ao dispositivo '{device}'"
                )
        self._validate_expression(expression)

    def _check_payload(self, payload: Any) -> None:
        message = ast.literal_eval(payload[1])
        if not message:
            raise SemanticError("Mensagem de alerta nao pode ser vazia.")
        if len(message) > 100:
            raise SemanticError("Mensagem de alerta com mais de 100 caracteres.")
        if payload[2]:
            self._require_variable(payload[2])

    def _validate_observation(self, observation: Any) -> None:
        for condition in observation[1]:
            self._validate_expression(condition[1])
            self._validate_expression(condition[3])

    def _validate_expression(self, expression: Any) -> None:
        if expression[0] == "execute":
            self._check_device(expression[2])
        elif expression[0] == "var":
            self._require_variable(expression[1])

    def _check_device(self, name: str) -> None:
        if name not in self.devices:
            raise SemanticError(f"Dispositivo usado sem declaracao: {name}")

    def _validate_observation_name(self, name: str) -> None:
        if self.OBSERVATION_RE.fullmatch(name) is None:
            raise SemanticError(
                f"Nome de observacao invalido; use letras, numeros e sublinhado: {name}"
            )

    def _require_variable(self, name: str) -> None:
        self._validate_observation_name(name)
        if name in self.devices and self.devices[name].observation is None:
            # Compatibilidade com o exemplo ``dispositivo: {umidade}``.
            self.variables.add(name)
            return
        if name not in self.variables:
            raise SemanticError(f"Observacao usada sem declaracao: {name}")

    def _build_python_names(self) -> None:
        used = set(self.PYTHON_RESERVED)
        for name in sorted(self.variables):
            candidate = name
            if keyword.iskeyword(candidate) or candidate in used:
                candidate = f"obs_{candidate}"
            base = candidate
            suffix = 2
            while candidate in used or keyword.iskeyword(candidate):
                candidate = f"{base}_{suffix}"
                suffix += 1
            self.python_names[name] = candidate
            used.add(candidate)


def analyze(program: ProgramAst) -> SemanticResult:
    """Atalho funcional para executar a analise semantica."""
    return SemanticAnalyzer(program).analyze()
