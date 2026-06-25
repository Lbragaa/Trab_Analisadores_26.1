# Trabalho Final INF1022 2026.1 — Analisador Sintático ObsAct

**Disciplina:** INF1022 — Compiladores  
**Professores:** Vitor Pinheiro e Edward Hermann  
**Turma:** 3WB

| Aluno | Matrícula |
|---|---|
| Gabriel de Barros Arruda | 2311723 |
| Arthur Rodrigues Alves Barbosa | 2310394 |

---

## O que foi implementado

Analisador léxico e sintático para a linguagem **ObsAct**, que compila programas `.obsact` para **Python**. Usa **PLY** (Python Lex-Yacc), gerador LALR(1) — análogo ao Bison/Flex, escrito em Python.

Funcionalidades implementadas:

- Declaração de dispositivos: `dispositivo: {namedevice}` e `dispositivo: {namedevice, observation}`
- Atribuição via `set observation = VAR` (inteiros e booleanos `True`/`False`/`true`/`false`/`TRUE`/`FALSE`)
- Atribuição via `set observation = ACTEXECUTE` — captura retorno de `verificar`, `ligar` ou `desligar`
- Atribuição em bloco: `set {namedevice, observation} = VAR`
- Ação `verificar(namedevice)` — retorna 1 (ligado) ou 0 (desligado) de acordo com o estado registrado do dispositivo
- Ações `ligar` (retorna 1) e `desligar` (retorna 0)
- Condicional `se OBS entao CMDS` com corpo **multi-comando** e **ifs aninhados**
- Condicional `se OBS entao CMDS senao CMDS`
- Condição com `verificar(dev)`: `se verificar(umidificador) == 0 entao ...`
- Condições compostas com `&&`
- Operadores lógicos: `>`, `<`, `>=`, `<=`, `==`, `!=`
- Envio de alerta: `enviar alerta ("msg") namedevice` e `enviar alerta ("msg", observation) namedevice`
- Alerta sem parênteses: `enviar alerta "msg" namedevice`
- **Broadcast**: `enviar alerta ("msg") para todos: dev1, dev2, ...`
- Geração das 5 funções de runtime no Python gerado: `ligar`, `desligar`, `verificar`, `alerta` (com e sem variável)
- Inicialização automática de toda `observation` para zero (conforme Suposições do enunciado)
- Validação semântica separada em `semantic.py`: dispositivos e observações declarados, nomes válidos, duplicatas, limite de 100 caracteres para `namedevice`/`msg` e associação em `set {namedevice, observation}`

---

## O que funciona

Todos os 5 testes compilam e executam corretamente:

| Exemplo | Cobertura | Saída |
|---|---|---|
| `exemplo1` | `set`, `se/entao/ligar` simples | `ventilador ligado!` |
| `exemplo2` | `verificar()` em `set`, if multi-cmd com if aninhado | `verificar ventilador` + `ventilador ligado!` |
| `exemplo3` | `se/entao/senao`, alerta sem parênteses | alerta + `lampada desligado!` |
| `exemplo4` | `set {dev,obs}`, if aninhado, `verificar()` em cond, broadcast | alerta + ligar umidificador + desligar lampada |
| `exemplo5` | broadcast com variável para múltiplos dispositivos | (temperatura = 0, condição falsa) |

A função `alerta` concatena `msg + " " + str(observation)` conforme especificado.

---

## O que não funciona / limitações

Não há limitações conhecidas dentro do escopo do enunciado. `set x = verificar(dev)` é aceito para cobrir os exemplos do enunciado: a variável `x` é registrada como variável local e pode ser usada em condições posteriores.

---

## Quais os testes utilizados

5 arquivos em `testes/`, baseados nos exemplos do enunciado (seção 1.2):

| Arquivo | Descrição |
|---|---|
| `exemplo1.obsact` | Termômetro + ventilador; `set`; condicional simples |
| `exemplo2.obsact` | `set x = verificar(dev)`; if com multi-cmd e if aninhado |
| `exemplo3.obsact` | Múltiplos sensores; `se/entao/senao`; alerta sem parênteses |
| `exemplo4.obsact` | `set {dev,obs}`; if aninhado; `verificar()` em condição; broadcast |
| `exemplo5.obsact` | Broadcast com variável para múltiplos dispositivos |

Saídas `.py` geradas estão em `testes/`.

---

## Como executar

**Pré-requisito:**
```bash
pip install ply
```

**Compilar:**
```bash
python obsact.py <entrada.obsact> <saida.py>
```

**Executar o código gerado:**
```bash
python <saida.py>
```

**Exemplo completo:**
```bash
python obsact.py testes/exemplo1.obsact testes/exemplo1.py
python testes/exemplo1.py
# saída: ventilador ligado!
```

---

## Gramática final utilizada

```
programa     ->  devices cmds

devices      ->  device devices | device

device       ->  dispositivo device_open IDENT }
              |  dispositivo device_open IDENT , IDENT }

device_open  ->  : {  |  {

cmds         ->  full_cmd cmds | full_cmd

full_cmd     ->  obsact .
              |  obsact
              |  simple_cmd .

simple_cmd   ->  attrib | act

attrib       ->  set IDENT = var
              |  set IDENT = actexecute
              |  set { IDENT , IDENT } = var

var          ->  NUMBER | TRUE | FALSE

obsact       ->  se obs entao if_cmds
              |  se obs entao if_cmds senao if_cmds

if_cmds      ->  simple_cmd . if_cmds
              |  simple_cmd .
              |  simple_cmd
              |  obsact . if_cmds
              |  obsact .
              |  obsact . if_cmds
              |  obsact

obs          ->  IDENT oplogic var
              |  IDENT oplogic var && obs
              |  verificar ( IDENT ) oplogic var
              |  verificar ( IDENT ) oplogic var && obs

oplogic      ->  >  |  <  |  >=  |  <=  |  ==  |  !=

act          ->  actexecute
              |  enviar alerta alert_args IDENT
              |  enviar alerta alert_args para todos : namelist

actexecute   ->  ligar IDENT
              |  desligar IDENT
              |  verificar ( IDENT )

alert_args   ->  ( STRING )
              |  ( STRING , IDENT )
              |  STRING
              |  STRING , IDENT

namelist     ->  IDENT | IDENT , namelist
```

### Alterações em relação à gramática do enunciado (2026.1)

| Ponto | Alteração |
|---|---|
| `ACTION -> verificar` | `verificar` usa sintaxe de chamada `verificar(dev)`, não `verificar dev`, pois todos os exemplos do enunciado usam parênteses |
| `OBSACT -> se OBS entao CMDS` | Corpo do if é `if_cmds` (não-terminal separado), para evitar conflito LALR(1) com o ponto terminador: permite múltiplos cmds com ou sem ponto no último antes do terminador externo |
| `ATTRIB -> set obs = ACTEXECUTE` | Permite capturar retorno de `ligar`/`desligar`/`verificar` em variável local (ex: `set estado = verificar(vent)`) sem exigir que essa variável seja uma observation declarada |
| `ATTRIB -> set {dev, obs} = VAR` | Nova forma para atribuição com contexto de dispositivo explícito, cobrindo os exemplos da seção 1.2 |
| `DEVICES -> DEVICE DEVICES \| DEVICE` | Recursão à direita (necessário para LALR(1) — enunciado especifica recursão à esquerda) |
| `alert_args` | Aceita mensagem com ou sem parênteses: exemplos alternam entre `("msg")` e `"msg"` |
| `device_open` | Aceita `dispositivo: { }` e `dispositivo { }` |
| Identifiers com `_` | Lexer e validação semântica aceitam `_` em observation names para cobrir variáveis como `estado_ventilador` dos exemplos |
| Validação semântica | Em `semantic.py`: verifica declarações, duplicatas, formatos de nomes |
| 5 funções de runtime | `ligar` retorna 1 e marca o dispositivo como ligado; `desligar` retorna 0 e marca como desligado; `verificar` consulta esse estado |

---

## Estrutura dos arquivos

```
Trabalho 2026.1/
├── obsact.py      # driver principal
├── lexer.py       # analisador léxico (PLY lex)
├── parser.py      # gramática LALR(1) + AST (PLY yacc)
├── semantic.py    # validação semântica e tabela de símbolos
├── codegen.py     # gerador de código Python
├── README.md      # este relatório
└── testes/
    ├── exemplo1.obsact  ...  exemplo5.obsact
    └── exemplo1.py      ...  exemplo5.py
```
