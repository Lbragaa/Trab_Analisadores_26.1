# Transpilador ObsAct para Python

Este projeto lê um programa escrito em ObsAct e gera um programa Python
equivalente. O parser usa Lark no modo LALR(1).

## O que o projeto faz

O fluxo completo é:

```text
arquivo .obsact
    -> lexer e pré-processamento
    -> parser e AST
    -> validação semântica
    -> geração de Python
    -> arquivo .py
```

O programa Python gerado simula os dispositivos com mensagens no terminal e
um dicionário de estados. 

## Estrutura

- `lexer.py`: terminais do Lark, comentários e normalização dos blocos.
- `parser.py`: regras sintáticas LALR(1), parser e construção da AST.
- `semantic.py`: dispositivos, observações, erros e nomes seguros para Python.
- `codegen.py`: conversão da AST validada para código Python.
- `compiler.py`: coordena parser, semântica e geração.
- `obsact.py`: interface de linha de comando.
- `tests/exemplo*.obsact`: programas ObsAct usados como entrada.
- `tests/test_obsact.py`: testes automatizados.
- `expected/exemplo*.py`: saídas Python de referência.
- `testes_obsact.zip`: pacote dos casos de teste para entrega.
- `relatorio.md`: relatório completo do trabalho.

## Requisitos

- Python 3.9 ou superior
- Lark

Instale a dependência uma vez:

```bash
python -m pip install -r requirements.txt
```

## Como compilar um programa ObsAct

```bash
python obsact.py tests/exemplo1.obsact -o saida.py
```

Esse comando ainda não executa o comportamento do programa. Ele faz o
transpilador ler `exemplo1.obsact`, verificar o programa e criar `saida.py`.

## Como executar o Python gerado

```bash
python saida.py
```

Agora o Python gerado é executado. As mensagens como `ventilador ligado!`
representam a simulação das ações ObsAct.

Para somente mostrar o Python gerado no terminal:

```bash
python obsact.py tests/exemplo1.obsact --print
```

## Como executar os testes

```bash
python -m unittest discover -s tests -v
```

Verifica automaticamente se:

- os exemplos ObsAct são reconhecidos;
- o Python gerado possui sintaxe válida e pode ser executado;
- as mensagens e estados esperados aparecem;
- programas incorretos são rejeitados;
- lexer, parser, semântica e geração funcionam juntos;
- broadcast, blocos, `senao`, `&&` e limites funcionam.

A suíte atual possui 15 grupos de testes. Ao final, `OK` significa que todos
eles passaram.

## Convenção de blocos

Blocos com vários comandos podem ser encerrados por uma linha contendo apenas
`.`. O transpilador também reconhece recuo e fim de arquivo para aceitar os
formatos encontrados no enunciado.
