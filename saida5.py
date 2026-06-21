# Código gerado automaticamente pelo transpilador ObsAct -> Python.
# Não edite manualmente se pretender regerar este arquivo.

def ligar(namedevice):
    print(str(namedevice) + ' ligado!')
    estados[str(namedevice)] = 1
    return 1

def desligar(namedevice):
    print(str(namedevice) + ' desligado!')
    estados[str(namedevice)] = 0
    return 0

def verificar(namedevice):
    estado = estados.get(str(namedevice), 0)
    if estado:
        print(str(namedevice) + ' está ligado.')
    else:
        print(str(namedevice) + ' está desligado.')
    return estado

def alerta(namedevice, msg, var=None):
    print(str(namedevice) + ' recebeu o alerta:')
    if var is None:
        print(str(msg))
    else:
        print(str(msg) + ' ' + str(var))

# Dispositivos declarados no programa ObsAct
dispositivos = ['celular', 'higrometro', 'lampada', 'umidificador', 'Monitor']
estados = {nome: 0 for nome in dispositivos}

# Observações/sensores. Valores não definidos começam em zero.
movimento = 0
potenciaLampada = 0
potenciaUmidificador = 0
umidade = 0

def main():
    global potenciaLampada
    potenciaLampada = 100
    global umidade
    umidade = 35
    if (umidade < 40):
        alerta('Monitor', "Ar seco detectado")
        if (verificar('umidificador') == 0):
            ligar('umidificador')
        global potenciaUmidificador
        potenciaUmidificador = 100
    if (movimento == True):
        ligar('lampada')
    else:
        desligar('lampada')

if __name__ == '__main__':
    main()
