# Relatório - Trabalho Final INF1022 2026.1

## Identificação

- **Aluno 1:** Diogo Lins Benchimol
- **Matrícula 1:** 2312917
- **Aluno 2:** Luan Carlos Almada Braga
- **Matrícula 2:** 2411776
- **Linguagem de entrada:** ObsAct
- **Linguagem de saída:** Python
- **Gerador de analisador:** Lark com o modo LALR(1)

## 1. Objetivo

O trabalho implementa um transpilador capaz de receber um programa escrito em
ObsAct, analisar sua estrutura e gerar um programa Python equivalente.

O programa gerado simula dispositivos e sensores. Ele não controla equipamentos
reais. As operações `ligar`, `desligar`, `verificar` e `alerta` usam mensagens no
terminal e um dicionário interno de estados.

## 2. Arquitetura da implementação

A implementação foi dividida em módulos com responsabilidades separadas. O
fluxo possui as seguintes etapas:

1. leitura do arquivo ObsAct em UTF-8;
2. pré-processamento dos blocos de comandos;
3. análise léxica e sintática com Lark/LALR(1);
4. construção de uma árvore sintática abstrata;
5. validação semântica de dispositivos, observações e alertas;
6. conversão segura dos identificadores ObsAct para identificadores Python;
7. geração do programa Python.

Os módulos são:

- `lexer.py`: define os terminais usados pelo lexer interno do Lark e realiza
  o pré-processamento dos blocos;
- `parser.py`: define as regras sintáticas, cria o parser LALR(1) e constrói a
  AST;
- `semantic.py`: valida dispositivos, observações, mensagens e nomes;
- `codegen.py`: gera o programa Python a partir da AST validada;
- `compiler.py`: coordena parser, análise semântica e geração;
- `obsact.py`: lê argumentos e arquivos pela linha de comando.

O Lark integra lexer e parser. Portanto, `lexer.py` não implementa um lexer
manual: ele concentra os terminais e regras léxicas que o Lark utiliza.

## 3. Instalação e execução

Instale a dependência:

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

Para mostrar o código gerado sem criar um arquivo:

```bash
python obsact.py tests/exemplo1.obsact --print
```

Para executar os testes automatizados:

```bash
python -m unittest discover -s tests -v
```

## 4. Funcionalidades implementadas

Foram implementadas as seguintes funcionalidades:

- declaração de dispositivos com ou sem observação;
- valores inteiros não negativos;
- valores booleanos `TRUE`, `FALSE`, `True` e `False`;
- atribuição de valores a observações;
- atribuição do retorno de `ligar`, `desligar` ou `verificar`;
- atribuição no formato `set {dispositivo, observacao} = valor`;
- ações `ligar`, `desligar` e `verificar`;
- condicionais com `se`, `entao` e `senao`;
- blocos com vários comandos;
- condicionais aninhadas;
- operadores `>`, `<`, `>=`, `<=`, `==` e `!=`;
- condições compostas com `&&`;
- alerta simples;
- alerta com concatenação entre mensagem e observação;
- broadcast de alerta para uma lista de dispositivos;
- inicialização automática de observações com zero;
- controle simulado do estado ligado ou desligado de cada dispositivo;
- proteção contra palavras reservadas e nomes internos do Python.

## 5. Gramática final

A gramática abaixo representa a gramática final de forma simplificada. Os
símbolos `BEGIN_BLOCK` e `END_BLOCK` são internos e são inseridos pelo
pré-processador.

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

Restrições semânticas complementam a gramática:

- `namedevice` contém somente letras e possui no máximo 100 caracteres;
- nomes de observação começam por letra e podem usar letras, números e `_`;
- `msg` não pode ser vazia e possui no máximo 100 caracteres;
- números são inteiros não negativos.

## 6. Alterações em relação à gramática inicial

A gramática do enunciado possui inconsistências entre as regras e os exemplos.
As seguintes alterações foram realizadas e estão explícitas neste relatório:

1. O caractere `:` depois de `dispositivo` é opcional porque existem exemplos
   com `dispositivo {Monitor}`.
2. O ponto final é opcional em comandos simples porque alguns exemplos do
   enunciado não possuem ponto.
3. `verificar` aceita `verificar dispositivo` e `verificar(dispositivo)`.
4. Foi adicionada a atribuição `set {dispositivo, observacao} = valor`, usada
   nos exemplos.
5. Alertas aceitam mensagem com ou sem parênteses.
6. Foi adicionada a lista de dispositivos necessária para o broadcast.
7. Expressões podem usar observações e resultados de ações.
8. Nomes de observação podem conter números e sublinhados depois da primeira
   letra, permitindo nomes como `estado_ventilador`.
9. Blocos com vários comandos usam marcadores internos. Eles podem ser
   encerrados por uma linha contendo apenas `.`, por recuo ou pelo fim do
   arquivo.
10. A forma `entao .`, presente em um exemplo, é tratada como o início de um
    bloco de um comando.
11. Para compatibilidade com o exemplo `dispositivo: {umidade}`, um dispositivo
    simples também pode ser usado como observação. Nesse caso, seu valor inicial
    é zero.
12. Comentários iniciados por `#` ou `//` são ignorados.

## 7. Validações semânticas

O transpilador rejeita:

- dispositivo usado sem declaração;
- dispositivo declarado mais de uma vez;
- nome de dispositivo com caracteres diferentes de letras;
- nome de dispositivo com mais de 100 caracteres;
- observação usada sem declaração;
- nome de observação inválido;
- associação incorreta em `set {dispositivo, observacao}`;
- mensagem de alerta vazia;
- mensagem de alerta com mais de 100 caracteres.

Resultados de ações podem criar variáveis auxiliares. Por exemplo:

```text
set estado_ventilador = verificar(ventilador).
```

Essas variáveis também começam em zero antes da execução dos comandos.

## 8. Geração do código Python

Todo programa gerado contém as funções:

```python
def ligar(namedevice): ...
def desligar(namedevice): ...
def verificar(namedevice): ...
def alerta(namedevice, msg, var=None): ...
```

O Python não possui sobrecarga tradicional de funções. Por isso, as duas
versões de `alerta` descritas no enunciado foram representadas por uma única
função com o parâmetro opcional `var`.

O estado dos dispositivos é mantido no dicionário `estados`. `ligar` grava o
valor 1, `desligar` grava 0 e `verificar` consulta o valor atual.

Observações são variáveis locais de `main` e começam em zero. O gerador troca
nomes que poderiam quebrar o Python. Por exemplo, uma observação chamada
`class` recebe um nome interno seguro como `obs_class`.

O broadcast gera uma chamada de `alerta` para cada dispositivo informado.

## 9. Testes utilizados

Os cinco arquivos principais em `tests/` foram baseados nos exemplos do
enunciado:

1. `exemplo1.obsact`: declarações, atribuições e condicional simples;
2. `exemplo2.obsact`: bloco múltiplo, `verificar` e condicional aninhada;
3. `exemplo3.obsact`: broadcast e a forma `entao .`;
4. `exemplo4.obsact`: alertas, booleanos e `senao`;
5. `exemplo5.obsact`: atribuição com dispositivo, bloco aninhado e estado.

O arquivo `tests/test_obsact.py` possui 15 grupos de testes automatizados para:

- execução direta das etapas modulares;
- compilação e execução dos cinco exemplos;
- atribuições repetidas;
- leitura de observação antes de uma atribuição explícita;
- nomes reservados do Python;
- identificadores que começam com texto de palavras reservadas;
- resultado de uma ação em uma atribuição;
- bloco `senao` em várias linhas;
- condição com `&&`;
- broadcast em uma e em várias linhas;
- comentário depois de `entao`;
- dispositivo simples usado como observação;
- erros léxicos e semânticos;
- limites de tamanho;
- mensagem vazia;
- geração pela linha de comando.

As saídas de referência estão em `expected/`. O arquivo
`testes_obsact.zip` contém os casos utilizados e está pronto para a entrega.

## 10. O que funciona e limitações

Todas as funcionalidades solicitadas pelo enunciado foram implementadas no
ambiente simulado. O transpilador não se comunica com dispositivos reais.

A linguagem não possui operações aritméticas, laços, funções definidas pelo
programador ou um sistema avançado de tipos, pois esses recursos não fazem
parte do escopo solicitado.

Para blocos com vários comandos no mesmo nível de recuo, recomenda-se usar uma
linha contendo apenas `.` para indicar claramente o fim do bloco.

Mensagens de erro sintático são produzidas pelo Lark e podem apresentar nomes
internos dos tokens. Erros semânticos possuem mensagens específicas.

## 11. Arquivos para entrega

- `lexer.py`: terminais e pré-processamento;
- `parser.py`: parser LALR(1) e AST;
- `semantic.py`: validação e tabela de símbolos;
- `codegen.py`: gerador de Python;
- `compiler.py`: coordenação do transpilador;
- `obsact.py`: interface de linha de comando;
- `requirements.txt`: dependência do projeto;
- `tests/`: entradas e testes automatizados;
- `expected/`: programas Python de referência;
- `testes_obsact.zip`: casos de teste compactados;
- `relatorio.md`: este relatório;
- `README.md`: instruções resumidas.

## 12. Conclusão

O projeto implementa um transpilador ObsAct para Python usando um parser
LALR(1). A implementação cobre a gramática base, corrige inconsistências dos
exemplos, implementa o broadcast obrigatório, valida os principais erros
semânticos e gera programas Python executáveis.
