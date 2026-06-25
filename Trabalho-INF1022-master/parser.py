import ply.yacc as yacc
from lexer import tokens

# AST nodes: tuples (tag, ...fields)
# ('program', devices, cmds)
# ('device', namedevice, observation|None)
# ('attrib', obs_name, value)         -- value: ('num',n)|('bool',b)|('actexecute',act,dev)
# ('attrib_device', dev, obs, value)  -- set {dev, obs} = val
# ('if', cond_list, then_cmds, else_cmds|None)
# ('actexecute', 'ligar'|'desligar'|'verificar', device)
# ('alert', msg, obs|None, devices_list)
# cond item: ('cond', lhs, op, rhs)
#   lhs: obs_name str OR ('actexecute',act,dev)

def p_programa(p):
    'programa : devices cmds'
    p[0] = ('program', p[1], p[2])

# ── devices ──────────────────────────────────────────────────────────────────

def p_devices_list(p):
    'devices : device devices'
    p[0] = [p[1]] + p[2]

def p_devices_one(p):
    'devices : device'
    p[0] = [p[1]]

def p_device_simple(p):
    'device : DISPOSITIVO device_open IDENT RBRACE'
    p[0] = ('device', p[3], None)

def p_device_obs(p):
    'device : DISPOSITIVO device_open IDENT COMMA IDENT RBRACE'
    p[0] = ('device', p[3], p[5])

def p_device_open(p):
    '''device_open : COLON LBRACE
                   | LBRACE'''
    p[0] = None

# ── top-level cmds ───────────────────────────────────────────────────────────

def p_cmds_more(p):
    'cmds : full_cmd cmds'
    p[0] = [p[1]] + p[2]

def p_cmds_one(p):
    'cmds : full_cmd'
    p[0] = [p[1]]

def p_full_cmd_obsact_dot(p):
    'full_cmd : obsact DOT'
    p[0] = p[1]

def p_full_cmd_obsact(p):
    'full_cmd : obsact'
    p[0] = p[1]

def p_full_cmd_simple(p):
    'full_cmd : simple_cmd DOT'
    p[0] = p[1]

def p_full_cmd_simple_without_dot(p):
    'full_cmd : simple_cmd'
    p[0] = p[1]

def p_simple_cmd(p):
    '''simple_cmd : attrib
                  | act'''
    p[0] = p[1]

# ── attrib ────────────────────────────────────────────────────────────────────

def p_attrib_var(p):
    'attrib : SET IDENT ASSIGN var'
    p[0] = ('attrib', p[2], p[4])

def p_attrib_actexecute(p):
    'attrib : SET IDENT ASSIGN actexecute'
    p[0] = ('attrib', p[2], p[4])

def p_attrib_device_var(p):
    'attrib : SET LBRACE IDENT COMMA IDENT RBRACE ASSIGN var'
    p[0] = ('attrib_device', p[3], p[5], p[8])

def p_var_num(p):
    'var : NUMBER'
    p[0] = ('num', p[1])

def p_var_true(p):
    'var : TRUE'
    p[0] = ('bool', True)

def p_var_false(p):
    'var : FALSE'
    p[0] = ('bool', False)

# ── obsact (if / if-else) ─────────────────────────────────────────────────────
# Single-act if: "se obs entao act." — the DOT is consumed inside if_cmds.
#   obsact reduces without consuming extra DOT; full_cmd uses 'obsact' (no dot).
# Multi-cmd if:  "se obs entao cmd. cmd. ." — body cmds consume their dots,
#   inner obsacts consume their own dots (via if_cmds: obsact DOT).
#   The lone "." is the obsact block terminator consumed by "obsact DOT" rules.
# Note: a single-act inner if (no lone dot) followed by more outer cmds MUST
#   have an explicit lone "." after it so the parser knows the inner if ended.
#   Example: "se c entao se c2 entao ligar v. . set x=1. ."

def p_obsact_if(p):
    'obsact : SE obs ENTAO if_cmds'
    p[0] = ('if', p[2], p[4], None)

def p_obsact_ifelse(p):
    'obsact : SE obs ENTAO if_cmds SENAO if_cmds'
    p[0] = ('if', p[2], p[4], p[6])

# if_cmds: one or more cmds inside an if body.
# Each simple_cmd may or may not have a trailing dot (to handle both single-line
# and multi-line bodies). PLY resolves shift/reduce by preferring shift (greedy).

def p_if_cmds_simple_dot_more(p):
    'if_cmds : simple_cmd DOT if_cmds'
    p[0] = [p[1]] + p[3]

def p_if_cmds_simple_dot(p):
    'if_cmds : simple_cmd DOT'
    p[0] = [p[1]]

def p_if_cmds_simple(p):
    'if_cmds : simple_cmd'
    p[0] = [p[1]]

def p_if_cmds_obsact_dot_more(p):
    'if_cmds : obsact DOT if_cmds'
    p[0] = [p[1]] + p[3]

def p_if_cmds_obsact_dot(p):
    'if_cmds : obsact DOT'
    p[0] = [p[1]]

def p_if_cmds_obsact_more(p):
    'if_cmds : obsact if_cmds'
    p[0] = [p[1]] + p[2]

def p_if_cmds_obsact(p):
    'if_cmds : obsact'
    p[0] = [p[1]]

# ── obs (conditions) ──────────────────────────────────────────────────────────

def p_obs_ident(p):
    'obs : IDENT OPLOGIC var'
    p[0] = [('cond', p[1], p[2], p[3])]

def p_obs_ident_and(p):
    'obs : IDENT OPLOGIC var AND obs'
    p[0] = [('cond', p[1], p[2], p[3])] + p[5]

def p_obs_verificar(p):
    'obs : VERIFICAR LPAREN IDENT RPAREN OPLOGIC var'
    p[0] = [('cond', ('actexecute', 'verificar', p[3]), p[5], p[6])]

def p_obs_verificar_and(p):
    'obs : VERIFICAR LPAREN IDENT RPAREN OPLOGIC var AND obs'
    p[0] = [('cond', ('actexecute', 'verificar', p[3]), p[5], p[6])] + p[8]

def p_obs_verificar_nospace(p):
    'obs : VERIFICAR IDENT OPLOGIC var'
    p[0] = [('cond', ('actexecute', 'verificar', p[2]), p[3], p[4])]

def p_obs_verificar_nospace_and(p):
    'obs : VERIFICAR IDENT OPLOGIC var AND obs'
    p[0] = [('cond', ('actexecute', 'verificar', p[2]), p[3], p[4])] + p[6]

# ── act ───────────────────────────────────────────────────────────────────────

def p_act_execute(p):
    'act : actexecute'
    p[0] = p[1]

def p_act_alert_direct(p):
    'act : ENVIAR ALERTA alert_args IDENT'
    msg, var = p[3]
    p[0] = ('alert', msg, var, [p[4]])

def p_act_alert_broadcast(p):
    'act : ENVIAR ALERTA alert_args PARA TODOS COLON namelist'
    msg, var = p[3]
    p[0] = ('alert', msg, var, p[7])

def p_actexecute_ligar(p):
    'actexecute : LIGAR IDENT'
    p[0] = ('actexecute', 'ligar', p[2])

def p_actexecute_desligar(p):
    'actexecute : DESLIGAR IDENT'
    p[0] = ('actexecute', 'desligar', p[2])

def p_actexecute_verificar_parens(p):
    'actexecute : VERIFICAR LPAREN IDENT RPAREN'
    p[0] = ('actexecute', 'verificar', p[3])

def p_actexecute_verificar_nospace(p):
    'actexecute : VERIFICAR IDENT'
    p[0] = ('actexecute', 'verificar', p[2])

def p_alert_args_msg(p):
    '''alert_args : LPAREN STRING RPAREN
                  | STRING'''
    p[0] = (p[2], None) if len(p) == 4 else (p[1], None)

def p_alert_args_var(p):
    '''alert_args : LPAREN STRING COMMA IDENT RPAREN
                  | STRING COMMA IDENT'''
    p[0] = (p[2], p[4]) if len(p) == 6 else (p[1], p[3])

def p_namelist_one(p):
    'namelist : IDENT'
    p[0] = [p[1]]

def p_namelist_more(p):
    'namelist : IDENT COMMA namelist'
    p[0] = [p[1]] + p[3]

def p_error(p):
    if p:
        print(f"ERRO SINTATICO: token {p.type}({p.value!r}) linha {p.lineno}")
    else:
        print("ERRO SINTATICO: fim de arquivo inesperado")

parser = yacc.yacc(debug=False, write_tables=False)
