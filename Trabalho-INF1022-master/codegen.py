RUNTIME = '''_device_states = {}

def inicializar_dispositivos(*namedevices):
    for namedevice in namedevices:
        _device_states.setdefault(namedevice, 0)

def ligar(namedevice):
    _device_states[namedevice] = 1
    print(namedevice + " ligado!")
    return 1

def desligar(namedevice):
    _device_states[namedevice] = 0
    print(namedevice + " desligado!")
    return 0

def verificar(namedevice):
    estado = _device_states.get(namedevice, 0)
    if estado == 1:
        print(namedevice + " esta ligado.")
    else:
        print(namedevice + " esta desligado.")
    return estado

def alerta(namedevice, msg, var=None):
    print(namedevice + " recebeu o alerta:")
    if var is None:
        print(msg)
    else:
        print(msg + " " + str(var))
'''


def py_var(v):
    tag, val = v
    if tag == 'bool':
        return 'True' if val else 'False'
    return str(val)


def py_obs(name, symbols):
    if isinstance(name, tuple) and name[0] == 'actexecute':
        return gen_actexecute_expr(name)
    return symbols.get('py_names', {}).get(name, name)


def gen_actexecute_expr(node):
    _, action, device = node
    return f"{action}({device!r})"


def gen_obs(conds, symbols):
    parts = []
    for _, lhs, op, rhs in conds:
        parts.append(f"{py_obs(lhs, symbols)} {op} {py_var(rhs)}")
    return ' and '.join(parts)


def gen_actexecute_stmt(node, indent, symbols):
    pad = '    ' * indent
    _, action, device = node
    return f"{pad}{action}({device!r})\n"


def gen_alert(node, indent, symbols):
    pad = '    ' * indent
    _, msg, var, devices = node
    out = ''
    for d in devices:
        if var is None:
            out += f"{pad}alerta({d!r}, {msg!r})\n"
        else:
            py_v = py_obs(var, symbols)
            out += f"{pad}alerta({d!r}, {msg!r}, {py_v})\n"
    return out


def gen_cmd(cmd, indent, symbols):
    pad = '    ' * indent
    tag = cmd[0]

    if tag == 'attrib':
        _, obs_name, value = cmd
        py_name = symbols.get('py_names', {}).get(obs_name, obs_name)
        if isinstance(value, tuple) and value[0] == 'actexecute':
            rhs = gen_actexecute_expr(value)
        else:
            rhs = py_var(value)
        return f"{pad}{py_name} = {rhs}\n"

    if tag == 'attrib_device':
        _, _dev, obs_name, value = cmd
        py_name = symbols.get('py_names', {}).get(obs_name, obs_name)
        return f"{pad}{py_name} = {py_var(value)}\n"

    if tag == 'if':
        _, conds, then_cmds, else_cmds = cmd
        out = f"{pad}if {gen_obs(conds, symbols)}:\n"
        for c in then_cmds:
            out += gen_cmd(c, indent + 1, symbols)
        if else_cmds is not None:
            out += f"{pad}else:\n"
            for c in else_cmds:
                out += gen_cmd(c, indent + 1, symbols)
        return out

    if tag == 'actexecute':
        return gen_actexecute_stmt(cmd, indent, symbols)

    if tag == 'alert':
        return gen_alert(cmd, indent, symbols)

    return ''


def generate(ast, symbols=None):
    _, devices, cmds = ast
    if symbols is None:
        observations = []
        for _, _name, obs in devices:
            if obs and obs not in observations:
                observations.append(obs)
        symbols = {
            'observations': observations,
            'py_names': {obs: obs for obs in observations},
        }

    out = RUNTIME + '\ndef main():\n'

    body = ''
    device_names = []
    for _, name, _obs in devices:
        if name not in device_names:
            device_names.append(name)
    if device_names:
        args = ', '.join(repr(name) for name in device_names)
        body += f"    inicializar_dispositivos({args})\n"

    for obs in symbols.get('observations', []):
        py_name = symbols['py_names'].get(obs, obs)
        body += f"    {py_name} = 0\n"

    for c in cmds:
        body += gen_cmd(c, 1, symbols)

    out += body if body else '    pass\n'
    out += '\nif __name__ == "__main__":\n    main()\n'
    return out
