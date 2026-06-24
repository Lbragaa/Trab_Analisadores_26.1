# Transpilador ObsAct para Python

Este projeto le um programa escrito em ObsAct e gera um programa Python
equivalente. O parser usa Lark no modo LALR(1).

## O que o projeto faz

O fluxo completo e:

```text
arquivo .obsact
    -> lexer e pre-processamento
    -> parser e AST
    -> validacao semantica
    -> geracao de Python
    -> arquivo .py
```

O programa Python gerado simula os dispositivos com mensagens no terminal e
um dicionario de estados. Nenhum dispositivo real e controlado.

## Estrutura

- `lexer.py`: terminais do Lark, comentarios e normalizacao dos blocos.
- `parser.py`: regras sintaticas LALR(1), parser e construcao da AST.
- `semantic.py`: dispositivos, observacoes, erros e nomes seguros para Python.
- `codegen.py`: conversao da AST validada para codigo Python.
- `compiler.py`: coordena parser, semantica e geracao.
- `obsact.py`: interface de linha de comando.
- `tests/exemplo*.obsact`: programas ObsAct usados como entrada.
- `tests/test_obsact.py`: testes automatizados.
- `expected/exemplo*.py`: saidas Python de referencia.
- `testes_obsact.zip`: pacote dos casos de teste para entrega.
- `relatorio.md`: relatorio completo do trabalho.

## Requisitos

- Python 3.9 ou superior
- Lark

Instale a dependencia uma vez:

```bash
python -m pip install -r requirements.txt
```

## Como compilar um programa ObsAct

```bash
python obsact.py tests/exemplo1.obsact -o saida.py
```

Esse comando ainda nao executa o comportamento do programa. Ele faz o
transpilador ler `exemplo1.obsact`, verificar o programa e criar `saida.py`.

## Como executar o Python gerado

```bash
python saida.py
```

Agora o Python gerado e executado. As mensagens como `ventilador ligado!`
representam a simulacao das acoes ObsAct.

Para somente mostrar o Python gerado no terminal:

```bash
python obsact.py tests/exemplo1.obsact --print
```

## Como executar os testes

```bash
python -m unittest discover -s tests -v
```

Esse comando nao testa dispositivos reais. Ele verifica automaticamente se:

- os exemplos ObsAct sao reconhecidos;
- o Python gerado possui sintaxe valida e pode ser executado;
- as mensagens e estados esperados aparecem;
- programas incorretos sao rejeitados;
- lexer, parser, semantica e geracao funcionam juntos;
- broadcast, blocos, `senao`, `&&` e limites funcionam.

A suite atual possui 15 grupos de testes. Ao final, `OK` significa que todos
eles passaram.

## Convencao de blocos

Blocos com varios comandos podem ser encerrados por uma linha contendo apenas
`.`. O transpilador tambem reconhece recuo e fim de arquivo para aceitar os
formatos encontrados no enunciado.
