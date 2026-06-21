# Transpilador ObsAct -> Python (INF1022 2026.1)

Este projeto implementa um analisador sintático para a linguagem **ObsAct** e transpila programas ObsAct para Python.

O parser foi implementado com **Lark** usando o algoritmo **LALR(1)**.

## Como instalar

```bash
pip install -r requirements.txt
```

## Como executar

```bash
python obsact.py tests/teste1.obs -o saida.py
python saida.py
```

Também é possível imprimir o Python gerado:

```bash
python obsact.py tests/teste1.obs --print
```

## Estrutura

- `obsact.py`: analisador léxico, analisador sintático, validações semânticas simples e geração de Python.
- `tests/`: programas ObsAct usados como testes.
- `expected/`: arquivos Python gerados a partir dos testes.
- `relatorio.md`: relatório do trabalho.

## Observação sobre blocos

A linguagem original tem exemplos com um ponto isolado (`.`) para encerrar blocos com múltiplos comandos após `entao`. Para tornar isso determinístico, este trabalho interpreta uma linha contendo apenas `.` como fim de bloco.
