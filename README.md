# Transpilador ObsAct para Python

Este projeto implementa um analisador lexico, sintatico e semantico para a
linguagem ObsAct. O programa usa Lark no modo LALR(1) e gera codigo Python.

## Requisitos

- Python 3.9 ou superior
- Lark

Instalacao:

```bash
python -m pip install -r requirements.txt
```

## Como executar

Para traduzir um arquivo ObsAct:

```bash
python obsact.py tests/exemplo1.obsact -o saida.py
python saida.py
```

Para mostrar o Python gerado no terminal:

```bash
python obsact.py tests/exemplo1.obsact --print
```

## Como executar os testes

```bash
python -m unittest discover -s tests -v
```

Os testes verificam:

- os cinco exemplos principais do enunciado;
- blocos com varios comandos e condicionais aninhadas;
- atribuicoes repetidas e inicializacao com zero;
- nomes que sao reservados em Python;
- dispositivos e observacoes nao declarados;
- associacao entre dispositivo e observacao;
- limites de tamanho de mensagens;
- geracao pela linha de comando.

## Estrutura

- `obsact.py`: parser, validacao semantica e gerador de Python.
- `tests/exemplo*.obsact`: casos de teste ObsAct.
- `tests/test_obsact.py`: testes automatizados.
- `expected/exemplo*.py`: saidas Python geradas para os exemplos.
- `testes_obsact.zip`: pacote com os casos de teste para entrega.
- `relatorio.md`: relatorio do trabalho.

## Convencao de blocos

Blocos com varios comandos podem ser encerrados por uma linha contendo apenas
`.`. O transpilador tambem reconhece o recuo e o fim do arquivo para aceitar os
formatos encontrados nos exemplos do enunciado.
