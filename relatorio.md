# Relatorio - Trabalho Final INF1022 2026.1

## Identificacao

- **Aluno 1:** Diogo Lins Benchimol
- **Matricula 1:** 2312917
- **Aluno 2:** Luan Carlos Almada Braga
- **Matricula 2:** 2411776
- **Linguagem de entrada:** ObsAct
- **Linguagem de saida:** Python
- **Gerador de analisador:** Lark com o modo LALR(1)

## 1. Objetivo

O trabalho implementa um transpilador capaz de receber um programa escrito em
ObsAct, analisar sua estrutura e gerar um programa Python equivalente.

O programa gerado simula dispositivos e sensores. Ele nao controla equipamentos
reais. As operacoes `ligar`, `desligar`, `verificar` e `alerta` usam mensagens no
terminal e um dicionario interno de estados.

## 2. Arquitetura da implementacao

A implementacao foi dividida em modulos com responsabilidades separadas. O
fluxo possui as seguintes etapas:

1. leitura do arquivo ObsAct em UTF-8;
2. pre-processamento dos blocos de comandos;
3. analise lexica e sintatica com Lark/LALR(1);
4. construcao de uma arvore sintatica abstrata;
5. validacao semantica de dispositivos, observacoes e alertas;
6. conversao segura dos identificadores ObsAct para identificadores Python;
7. geracao do programa Python.

Os modulos sao:

- `lexer.py`: define os terminais usados pelo lexer interno do Lark e realiza
  o pre-processamento dos blocos;
- `parser.py`: define as regras sintaticas, cria o parser LALR(1) e constroi a
  AST;
- `semantic.py`: valida dispositivos, observacoes, mensagens e nomes;
- `codegen.py`: gera o programa Python a partir da AST validada;
- `compiler.py`: coordena parser, analise semantica e geracao;
- `obsact.py`: le argumentos e arquivos pela linha de comando.

O Lark integra lexer e parser. Portanto, `lexer.py` nao implementa um lexer
manual: ele concentra os terminais e regras lexicas que o Lark utiliza.

## 3. Instalacao e execucao

Instale a dependencia:

```bash
python -m pip install -r requirements.txt
```

Para traduzir um arquivo ObsAct:

```bash
python obsact.py tests/exemplo1.obsact -o saida.py
```

Para executar o programa Python gerado:

```bash
python saida.py
```

Para mostrar o codigo gerado sem criar um arquivo:

```bash
python obsact.py tests/exemplo1.obsact --print
```

Para executar os testes automatizados:

```bash
python -m unittest discover -s tests -v
```

## 4. Funcionalidades implementadas

Foram implementadas as seguintes funcionalidades:

- declaracao de dispositivos com ou sem observacao;
- valores inteiros nao negativos;
- valores booleanos `TRUE`, `FALSE`, `True` e `False`;
- atribuicao de valores a observacoes;
- atribuicao do retorno de `ligar`, `desligar` ou `verificar`;
- atribuicao no formato `set {dispositivo, observacao} = valor`;
- acoes `ligar`, `desligar` e `verificar`;
- condicionais com `se`, `entao` e `senao`;
- blocos com varios comandos;
- condicionais aninhadas;
- operadores `>`, `<`, `>=`, `<=`, `==` e `!=`;
- condicoes compostas com `&&`;
- alerta simples;
- alerta com concatenacao entre mensagem e observacao;
- broadcast de alerta para uma lista de dispositivos;
- inicializacao automatica de observacoes com zero;
- controle simulado do estado ligado ou desligado de cada dispositivo;
- protecao contra palavras reservadas e nomes internos do Python.

## 5. Gramatica final

A gramatica abaixo representa a gramatica final de forma simplificada. Os
simbolos `BEGIN_BLOCK` e `END_BLOCK` sao internos e sao inseridos pelo
pre-processador.

```text
PROGRAM       -> DEVICE+ STATEMENT*

DEVICE        -> dispositivo COLON_OPT { NAME }
DEVICE        -> dispositivo COLON_OPT { NAME , NAME }
COLON_OPT     -> : | vazio

STATEMENT     -> CMD DOT_OPT
DOT_OPT       -> . | vazio

CMD           -> ATTRIB
CMD           -> OBSACT
CMD           -> ACT

ATTRIB        -> set TARGET = VALUE
TARGET        -> NAME
TARGET        -> { NAME , NAME }

VALUE         -> NUMBER
VALUE         -> BOOL
VALUE         -> EXECUTE
VALUE         -> NAME

OBSACT        -> se OBS entao BLOCK
OBSACT        -> se OBS entao BLOCK senao BLOCK

BLOCK         -> CMD
BLOCK         -> BEGIN_BLOCK CMD_STMT+ END_BLOCK
CMD_STMT      -> CMD DOT_OPT

OBS           -> CONDITION
OBS           -> CONDITION && OBS

CONDITION     -> EXPR OPLOGIC EXPR

EXPR          -> NUMBER
EXPR          -> BOOL
EXPR          -> EXECUTE
EXPR          -> NAME

ACT           -> EXECUTE
ACT           -> ALERT
ACT           -> BROADCAST

EXECUTE       -> ACTION NAME
EXECUTE       -> ACTION ( NAME )

ACTION        -> ligar
ACTION        -> desligar
ACTION        -> verificar

ALERT         -> enviar alerta ALERT_PAYLOAD NAME

BROADCAST     -> enviar alerta ALERT_PAYLOAD para todos : NAME_LIST

ALERT_PAYLOAD -> STRING
ALERT_PAYLOAD -> ( STRING )
ALERT_PAYLOAD -> ( STRING , NAME )

NAME_LIST     -> NAME
NAME_LIST     -> NAME , NAME_LIST

OPLOGIC       -> > | < | >= | <= | == | !=
BOOL          -> TRUE | FALSE | True | False
NUMBER        -> digito+
NAME          -> letra ou sublinhado seguido de letras, digitos ou sublinhados
STRING        -> texto nao vazio entre aspas duplas
```

Restricoes semanticas complementam a gramatica:

- `namedevice` contem somente letras e possui no maximo 100 caracteres;
- nomes de observacao comecam por letra e podem usar letras, numeros e `_`;
- `msg` nao pode ser vazia e possui no maximo 100 caracteres;
- numeros sao inteiros nao negativos.

## 6. Alteracoes em relacao a gramatica inicial

A gramatica do enunciado possui inconsistencias entre as regras e os exemplos.
As seguintes alteracoes foram realizadas e estao explicitas neste relatorio:

1. O caractere `:` depois de `dispositivo` e opcional porque existem exemplos
   com `dispositivo {Monitor}`.
2. O ponto final e opcional em comandos simples porque alguns exemplos do
   enunciado nao possuem ponto.
3. `verificar` aceita `verificar dispositivo` e `verificar(dispositivo)`.
4. Foi adicionada a atribuicao `set {dispositivo, observacao} = valor`, usada
   nos exemplos.
5. Alertas aceitam mensagem com ou sem parenteses.
6. Foi adicionada a lista de dispositivos necessaria para o broadcast.
7. Expressoes podem usar observacoes e resultados de acoes.
8. Nomes de observacao podem conter numeros e sublinhados depois da primeira
   letra, permitindo nomes como `estado_ventilador`.
9. Blocos com varios comandos usam marcadores internos. Eles podem ser
   encerrados por uma linha contendo apenas `.`, por recuo ou pelo fim do
   arquivo.
10. A forma `entao .`, presente em um exemplo, e tratada como o inicio de um
    bloco de um comando.
11. Para compatibilidade com o exemplo `dispositivo: {umidade}`, um dispositivo
    simples tambem pode ser usado como observacao. Nesse caso, seu valor inicial
    e zero.
12. Comentarios iniciados por `#` ou `//` sao ignorados.

## 7. Validacoes semanticas

O transpilador rejeita:

- dispositivo usado sem declaracao;
- dispositivo declarado mais de uma vez;
- nome de dispositivo com caracteres diferentes de letras;
- nome de dispositivo com mais de 100 caracteres;
- observacao usada sem declaracao;
- nome de observacao invalido;
- associacao incorreta em `set {dispositivo, observacao}`;
- mensagem de alerta vazia;
- mensagem de alerta com mais de 100 caracteres.

Resultados de acoes podem criar variaveis auxiliares. Por exemplo:

```text
set estado_ventilador = verificar(ventilador).
```

Essas variaveis tambem comecam em zero antes da execucao dos comandos.

## 8. Geracao do codigo Python

Todo programa gerado contem as funcoes:

```python
def ligar(namedevice): ...
def desligar(namedevice): ...
def verificar(namedevice): ...
def alerta(namedevice, msg, var=None): ...
```

O Python nao possui sobrecarga tradicional de funcoes. Por isso, as duas
versoes de `alerta` descritas no enunciado foram representadas por uma unica
funcao com o parametro opcional `var`.

O estado dos dispositivos e mantido no dicionario `estados`. `ligar` grava o
valor 1, `desligar` grava 0 e `verificar` consulta o valor atual.

Observacoes sao variaveis locais de `main` e comecam em zero. O gerador troca
nomes que poderiam quebrar o Python. Por exemplo, uma observacao chamada
`class` recebe um nome interno seguro como `obs_class`.

O broadcast gera uma chamada de `alerta` para cada dispositivo informado.

## 9. Testes utilizados

Os cinco arquivos principais em `tests/` foram baseados nos exemplos do
enunciado:

1. `exemplo1.obsact`: declaracoes, atribuicoes e condicional simples;
2. `exemplo2.obsact`: bloco multiplo, `verificar` e condicional aninhada;
3. `exemplo3.obsact`: broadcast e a forma `entao .`;
4. `exemplo4.obsact`: alertas, booleanos e `senao`;
5. `exemplo5.obsact`: atribuicao com dispositivo, bloco aninhado e estado.

O arquivo `tests/test_obsact.py` possui 15 grupos de testes automatizados para:

- execucao direta das etapas modulares;
- compilacao e execucao dos cinco exemplos;
- atribuicoes repetidas;
- leitura de observacao antes de uma atribuicao explicita;
- nomes reservados do Python;
- identificadores que comecam com texto de palavras reservadas;
- resultado de uma acao em uma atribuicao;
- bloco `senao` em varias linhas;
- condicao com `&&`;
- broadcast em uma e em varias linhas;
- comentario depois de `entao`;
- dispositivo simples usado como observacao;
- erros lexicos e semanticos;
- limites de tamanho;
- mensagem vazia;
- geracao pela linha de comando.

As saidas de referencia estao em `expected/`. O arquivo
`testes_obsact.zip` contem os casos utilizados e esta pronto para a entrega.

## 10. O que funciona e limitacoes

Todas as funcionalidades solicitadas pelo enunciado foram implementadas no
ambiente simulado. O transpilador nao se comunica com dispositivos reais.

A linguagem nao possui operacoes aritmeticas, lacos, funcoes definidas pelo
programador ou um sistema avancado de tipos, pois esses recursos nao fazem
parte do escopo solicitado.

Para blocos com varios comandos no mesmo nivel de recuo, recomenda-se usar uma
linha contendo apenas `.` para indicar claramente o fim do bloco.

Mensagens de erro sintatico sao produzidas pelo Lark e podem apresentar nomes
internos dos tokens. Erros semanticos possuem mensagens especificas.

## 11. Arquivos para entrega

- `lexer.py`: terminais e pre-processamento;
- `parser.py`: parser LALR(1) e AST;
- `semantic.py`: validacao e tabela de simbolos;
- `codegen.py`: gerador de Python;
- `compiler.py`: coordenacao do transpilador;
- `obsact.py`: interface de linha de comando;
- `requirements.txt`: dependencia do projeto;
- `tests/`: entradas e testes automatizados;
- `expected/`: programas Python de referencia;
- `testes_obsact.zip`: casos de teste compactados;
- `relatorio.md`: este relatorio;
- `README.md`: instrucoes resumidas.

## 12. Conclusao

O projeto implementa um transpilador ObsAct para Python usando um parser
LALR(1). A implementacao cobre a gramatica base, corrige inconsistencias dos
exemplos, implementa o broadcast obrigatorio, valida os principais erros
semanticos e gera programas Python executaveis.
