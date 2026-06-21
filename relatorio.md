# Relatório — Trabalho Final INF1022 2026.1

**Aluno 1:** Diogo Lins Benchimol

**Matrícula:** 2312917  
**Linguagem de saída escolhida:** Python  
**Gerador de analisador sintático:** Lark, usando o modo `parser="lalr"`.

## 1. Objetivo

O objetivo do trabalho foi implementar um analisador sintático para a linguagem **ObsAct**, capaz de receber um programa escrito em ObsAct e gerar como saída um programa equivalente em outra linguagem. Neste trabalho, a linguagem de saída escolhida foi **Python**.

O arquivo principal é `obsact.py`, que realiza quatro etapas:

1. pré-processamento de blocos;
2. análise léxica e sintática com Lark/LALR(1);
3. validações semânticas simples;
4. geração de código Python.

## 2. Como executar

Primeiro, instale a dependência:

```bash
pip install -r requirements.txt
```

Depois, execute o transpilador:

```bash
python obsact.py tests/teste1.obs -o saida.py
python saida.py
```

Também é possível imprimir o Python gerado diretamente no terminal:

```bash
python obsact.py tests/teste1.obs --print
```

## 3. O que foi implementado

Foram implementadas as principais funcionalidades exigidas pelo enunciado:

- declaração de dispositivos com ou sem observação/sensor;
- atribuição de valores inteiros não negativos;
- atribuição de valores booleanos (`True`, `False`, `TRUE`, `FALSE`);
- atribuição com resultado de ação, como `set estado = verificar(ventilador)`;
- comandos `ligar`, `desligar` e `verificar`;
- estruturas condicionais com `se`, `entao` e `senao`;
- condições com operadores `>`, `<`, `>=`, `<=`, `==` e `!=`;
- operador lógico `&&` entre condições;
- envio de alerta para um dispositivo;
- envio de alerta concatenando mensagem e observação;
- envio de alerta em broadcast para vários dispositivos com `para todos:`;
- inicialização automática com zero para observações não definidas pelo programador.

## 4. Alterações e complementos na gramática

A gramática do enunciado foi preservada em espírito, mas algumas regras foram complementadas para aceitar os próprios exemplos do documento e tornar os blocos mais claros na implementação.

As principais alterações foram:

1. O caractere `:` depois de `dispositivo` foi tratado como opcional, pois alguns exemplos usam `dispositivo { Monitor }`.
2. Foi aceito `verificar(dispositivo)` além de `verificar dispositivo`, pois os exemplos usam a versão com parênteses.
3. Foi aceita atribuição no formato `set { dispositivo, observation } = valor`, presente nos exemplos.
4. Foi aceito envio de alerta com e sem parênteses:
   - `enviar alerta "msg" Monitor`
   - `enviar alerta ("msg") Monitor`
   - `enviar alerta ("msg", sensor) Monitor`
5. Foi adicionada a regra de broadcast:
   - `enviar alerta ("msg") para todos: monitor, celular`
   - `enviar alerta ("msg", sensor) para todos: monitor, celular`
6. Uma linha contendo apenas `.` é interpretada como fechamento de bloco com múltiplos comandos. Isso foi feito para remover ambiguidades em comandos `se ... entao` com mais de uma instrução interna.

## 5. Gramática final utilizada

Abaixo está a gramática final em formato simplificado, equivalente à gramática usada no arquivo `obsact.py`.

```text
PROGRAM     -> DEVICE+ STATEMENT*

DEVICE      -> dispositivo :? { NAME }
DEVICE      -> dispositivo :? { NAME , NAME }

STATEMENT   -> CMD .?
CMD         -> ATTRIB | OBSACT | ACT

ATTRIB      -> set TARGET = VALUE
TARGET      -> NAME
TARGET      -> { NAME , NAME }

VALUE       -> NUMBER | BOOL | EXECUTE | NAME

OBSACT      -> se OBS entao BLOCK
OBSACT      -> se OBS entao BLOCK senao BLOCK

BLOCK       -> CMD
BLOCK       -> BEGIN_BLOCK CMD_STMT+ END_BLOCK
CMD_STMT    -> CMD .?

OBS         -> CONDITION
OBS         -> CONDITION && CONDITION && ...
CONDITION   -> EXPR OPLOGIC EXPR
EXPR        -> NUMBER | BOOL | EXECUTE | NAME

ACT         -> EXECUTE | ALERT | BROADCAST
EXECUTE     -> ACTION CALL_DEVICE
ACTION      -> ligar | desligar | verificar
CALL_DEVICE -> NAME
CALL_DEVICE -> ( NAME )

ALERT       -> enviar alerta ALERT_PAYLOAD NAME
BROADCAST   -> enviar alerta ALERT_PAYLOAD para todos : NAME_LIST

ALERT_PAYLOAD -> STRING
ALERT_PAYLOAD -> ( STRING )
ALERT_PAYLOAD -> ( STRING , NAME )

NAME_LIST   -> NAME
NAME_LIST   -> NAME , NAME_LIST

OPLOGIC     -> > | < | >= | <= | == | !=
BOOL        -> TRUE | FALSE | True | False
NUMBER      -> dígito+
NAME        -> letra ou underline seguido de letras, números ou underline
STRING      -> texto entre aspas duplas
```

Na implementação, `BEGIN_BLOCK` e `END_BLOCK` são marcadores internos inseridos pelo pré-processador. O programador escreve apenas uma linha contendo `.` para fechar um bloco com múltiplos comandos.

## 6. Validações semânticas

O transpilador implementa algumas validações além da análise sintática:

- não permite usar dispositivo não declarado;
- não permite declarar o mesmo dispositivo duas vezes;
- verifica se mensagens de alerta têm no máximo 100 caracteres;
- verifica se nomes de dispositivos têm no máximo 100 caracteres;
- emite aviso caso um nome de dispositivo contenha caracteres fora de `[A-Za-z]`, pois a gramática original restringe `namedevice` a letras.

Variáveis/observações usadas no programa são inicializadas com zero no Python gerado, respeitando a suposição do enunciado de que valores não definidos devem começar em zero.

## 7. Geração de código Python

O código Python gerado contém as funções auxiliares pedidas pelo enunciado:

```python
def ligar(namedevice): ...
def desligar(namedevice): ...
def verificar(namedevice): ...
def alerta(namedevice, msg, var=None): ...
```

A função `alerta` usa o terceiro parâmetro opcional `var` para representar tanto a versão com apenas mensagem quanto a versão com mensagem + observação.

Exemplo de tradução:

```text
ligar lampada
```

vira:

```python
ligar('lampada')
```

E:

```text
enviar alerta ("Temperatura em", temperatura) para todos: monitor, celular
```

vira:

```python
alerta('monitor', "Temperatura em", temperatura)
alerta('celular', "Temperatura em", temperatura)
```

## 8. Testes utilizados

Foram incluídos cinco testes na pasta `tests/`:

1. `teste1.obs`: declaração de dispositivos, atribuições simples e comando `se` com `ligar`.
2. `teste2.obs`: bloco com múltiplos comandos, `verificar` e atribuição com retorno de ação.
3. `teste3_broadcast.obs`: envio de alerta para múltiplos dispositivos com `para todos:`.
4. `teste4_senao.obs`: uso de `senao`, alertas e booleanos.
5. `teste5_extra.obs`: combinação de atribuição no formato `{device, observation}`, bloco múltiplo, `verificar`, alerta e `senao`.

Os arquivos Python gerados a partir desses testes estão na pasta `expected/`.

## 9. O que não foi implementado

Não foi implementado um ambiente real de automação de dispositivos. As funções `ligar`, `desligar`, `verificar` e `alerta` apenas simulam o comportamento pedido pelo enunciado usando `print` e um dicionário interno de estados.

Também não foi implementado sistema de tipos avançado: as observações são convertidas diretamente para variáveis Python, e o programador deve evitar nomes que sejam palavras reservadas de Python.

## 10. Conclusão

O trabalho implementa um transpilador funcional de ObsAct para Python, usando um gerador de analisador sintático LALR(1). A implementação cobre a gramática-base, os exemplos do enunciado e a funcionalidade obrigatória de broadcast, além de acrescentar pequenas adaptações documentadas para tornar a linguagem mais prática e menos ambígua.
