_device_states = {}

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

def main():
    inicializar_dispositivos('Termometro', 'ventilador')
    temperatura = 0
    potencia = 0
    estado_ventilador = 0
    temperatura = 40
    if temperatura > 30:
        estado_ventilador = verificar('ventilador')
        if estado_ventilador == 0:
            ligar('ventilador')
        potencia = 90

if __name__ == "__main__":
    main()
