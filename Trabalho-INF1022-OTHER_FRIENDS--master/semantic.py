import keyword
import re

DEVICE_RE = re.compile(r'^[A-Za-z]+$')
OBSERVATION_RE = re.compile(r'^[A-Za-z][A-Za-z0-9_]*$')
MAX_DEVICE_NAME_LEN = 100
MAX_MSG_LEN = 100
RUNTIME_NAMES = {'ligar', 'desligar', 'verificar', 'alerta', 'main'}


class SemanticError(Exception):
    def __init__(self, errors):
        self.errors = errors
        super().__init__('\n'.join(errors))

    def __str__(self):
        return '\n'.join(f'ERRO SEMANTICO: {e}' for e in self.errors)


def validate(ast):
    _, devices, cmds = ast
    errors = []
    device_names = {}
    observations = {}

    for _, name, observation in devices:
        device_errors = _device_name_errors(name, 'declaracao')
        if device_errors:
            errors.extend(device_errors)
        elif name in device_names:
            errors.append(f"dispositivo '{name}' declarado mais de uma vez")
        else:
            device_names[name] = observation

        if observation is not None:
            if not _valid_observation_name(observation):
                errors.append(
                    f"observation '{observation}' invalida; use letras e numeros, comecando por letra"
                )
            else:
                observations.setdefault(observation, []).append(name)

    for cmd in cmds:
        _validate_cmd(cmd, device_names, observations, errors)

    if errors:
        raise SemanticError(errors)

    obs_list = list(observations)
    return {
        'devices': set(device_names),
        'observations': obs_list,
        'observation_devices': observations,
        'py_names': _make_python_names(obs_list),
    }


def _validate_cmd(cmd, devices, observations, errors):
    tag = cmd[0]

    if tag == 'attrib':
        _, obs_name, value = cmd
        if isinstance(value, tuple) and value[0] == 'actexecute':
            # Results from actions may introduce local observation-like variables.
            if not _valid_observation_name(obs_name):
                errors.append(
                    f"observation '{obs_name}' invalida em atribuicao; use letras e numeros, comecando por letra"
                )
            _validate_actexecute(value, devices, 'atribuicao', errors)
            if _valid_observation_name(obs_name):
                observations.setdefault(obs_name, [])
        else:
            _require_observation(obs_name, observations, 'atribuicao', errors)
        return

    if tag == 'attrib_device':
        _, dev_name, obs_name, _value = cmd
        _require_device(dev_name, devices, 'atribuicao', errors)
        _require_observation(obs_name, observations, 'atribuicao', errors)
        if dev_name in devices and obs_name in observations and devices[dev_name] != obs_name:
            errors.append(
                f"observation '{obs_name}' nao pertence ao dispositivo '{dev_name}'"
            )
        return

    if tag == 'if':
        _, conds, then_cmds, else_cmds = cmd
        for cond in conds:
            _validate_cond(cond, devices, observations, errors)
        for c in then_cmds:
            _validate_cmd(c, devices, observations, errors)
        if else_cmds is not None:
            for c in else_cmds:
                _validate_cmd(c, devices, observations, errors)
        return

    if tag == 'actexecute':
        _validate_actexecute(cmd, devices, 'acao', errors)
        return

    if tag == 'alert':
        _, msg, obs_var, target_devices = cmd
        if len(msg) > MAX_MSG_LEN:
            errors.append(f"msg excede {MAX_MSG_LEN} caracteres: {msg[:30]!r}...")
        if obs_var is not None:
            _require_observation(obs_var, observations, 'alerta', errors)
        for d in target_devices:
            _require_device(d, devices, 'alerta', errors)
        return


def _validate_cond(cond, devices, observations, errors):
    _, lhs, _op, _rhs = cond
    if isinstance(lhs, tuple) and lhs[0] == 'actexecute':
        _validate_actexecute(lhs, devices, 'condicao', errors)
    else:
        _require_observation(lhs, observations, 'condicao', errors)


def _validate_actexecute(node, devices, context, errors):
    _, _action, device = node
    _require_device(device, devices, context, errors)


def _require_device(name, devices, context, errors):
    device_errors = _device_name_errors(name, context)
    if device_errors:
        errors.extend(device_errors)
        return
    if name not in devices:
        errors.append(f"dispositivo '{name}' usado em {context} nao foi declarado")


def _require_observation(name, observations, context, errors):
    if not _valid_observation_name(name):
        errors.append(
            f"observation '{name}' invalida em {context}; use letras e numeros, comecando por letra"
        )
        return
    if name not in observations:
        errors.append(
            f"observation '{name}' usada em {context} nao foi declarada em nenhum dispositivo"
        )


def _valid_device_name(name):
    return DEVICE_RE.fullmatch(name) is not None


def _device_name_errors(name, context):
    errors = []
    if len(name) > MAX_DEVICE_NAME_LEN:
        errors.append(
            f"namedevice '{name[:30]}...' excede {MAX_DEVICE_NAME_LEN} caracteres em {context}"
        )
    if not _valid_device_name(name):
        errors.append(f"namedevice '{name}' invalido em {context}; use somente letras")
    return errors


def _valid_observation_name(name):
    return OBSERVATION_RE.fullmatch(name) is not None


def _make_python_names(observations):
    names = {}
    used = set(RUNTIME_NAMES)
    for obs in observations:
        candidate = obs
        if not candidate.isidentifier() or keyword.iskeyword(candidate) or candidate in used:
            candidate = f'obs_{obs}'
        base, suffix = candidate, 2
        while candidate in used:
            candidate = f'{base}_{suffix}'
            suffix += 1
        used.add(candidate)
        names[obs] = candidate
    return names
