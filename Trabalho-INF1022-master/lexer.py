import ast

import ply.lex as lex

reserved = {
    'dispositivo': 'DISPOSITIVO',
    'set': 'SET',
    'se': 'SE',
    'entao': 'ENTAO',
    'senao': 'SENAO',
    'enviar': 'ENVIAR',
    'alerta': 'ALERTA',
    'para': 'PARA',
    'todos': 'TODOS',
    'ligar': 'LIGAR',
    'desligar': 'DESLIGAR',
    'verificar': 'VERIFICAR',
    'True': 'TRUE',
    'False': 'FALSE',
    'TRUE': 'TRUE',
    'FALSE': 'FALSE',
    'true': 'TRUE',
    'false': 'FALSE',
}

tokens = [
    'IDENT', 'NUMBER', 'STRING',
    'COLON', 'COMMA', 'DOT', 'ASSIGN',
    'LBRACE', 'RBRACE', 'LPAREN', 'RPAREN',
    'AND', 'OPLOGIC',
] + sorted(set(reserved.values()))

t_COLON   = r':'
t_COMMA   = r','
t_DOT     = r'\.'
t_ASSIGN  = r'='
t_LBRACE  = r'\{'
t_RBRACE  = r'\}'
t_LPAREN  = r'\('
t_RPAREN  = r'\)'
t_AND     = r'&&'

def t_OPLOGIC(t):
    r'>=|<=|==|!=|>|<'
    return t

def t_NUMBER(t):
    r'\d+'
    t.value = int(t.value)
    return t

def t_STRING(t):
    r'"([^"\\]|\\.)*"'
    t.value = ast.literal_eval(t.value)
    return t

def t_IDENT(t):
    r'[A-Za-z][A-Za-z0-9_]*'
    t.type = reserved.get(t.value, 'IDENT')
    return t

t_ignore = ' \t\r\ufeff'

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

def t_error(t):
    message = f"ERRO LEXICO: caractere inesperado {t.value[0]!r} linha {t.lineno}"
    print(message)
    if not hasattr(t.lexer, 'errors'):
        t.lexer.errors = []
    t.lexer.errors.append(message)
    t.lexer.skip(1)

lexer = lex.lex()
lexer.errors = []
