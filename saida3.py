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
dispositivos = ['monitor', 'celular', 'Termometro']
estados = {nome: 0 for nome in dispositivos}

# Observações/sensores. Valores não definidos começam em zero.
temperatura = 0

def main():
    global temperatura
    temperatura = 37
    if (temperatura > 30):
        alerta('monitor', "Temperatura em", temperatura)
        alerta('celular', "Temperatura em", temperatura)

if __name__ == '__main__':
    main()
