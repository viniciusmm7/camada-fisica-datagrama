#####################################################
# Camada Física da Computação
#Carareto
#11/08/2022
#Aplicação
####################################################
from enlace import *
import time, platform, serial.tools.list_ports
import numpy as np
from comandos import *
import random

class Client:
    def __init__(self):
        self.HANDSHAKE = '\\x01'
        self.ACK = '\\x02'
        self.EOF = '\\xAA\\xBB\\xCC\\xDD'

        self.os = platform.system().lower()
        self.serialName = self._findArduino()
        self.com1 = enlace(self.serialName)
        self.com1.enable()

        self.packageId = 0
        # self.lastPackageId = 0

    def _findArduino(self):
        result = []
        ports = list(serial.tools.list_ports.comports())
        c = 0
        for p in ports:
            result.append(f'/dev/ttyACM{c}')
            c += 1
        return result[1]

    def waitBufferLen(self):
        rxLen = self.com1.rx.getBufferLen()
        while rxLen == 0:
            rxLen = self.com1.rx.getBufferLen()
        return rxLen

    def waitStatus(self):
        txSize = self.com1.tx.getStatus()
        while txSize == 0:
            txSize = self.com1.tx.getStatus()

    def make_payload_list(self, data) -> list:
        limit = 114
        payload_list = []

        if data.isinstance(str):
            data = data.encode()

        if data.isinstance(bytes):
            if limit > len(data):
                limit = len(data)
            payload_list.append(data[:limit])
            data = data[limit:]

        return payload_list, len(payload_list)

    def make_head(self, type='\\x00', h1='\\x00', h2='\\x00', len_packages='\\x00', package_id='\\x00', h5='\\x00', h6='\\x00', last_package='\\x00', h8='\\x00', h9='\\x00'):
        return (type + h1 + h2 + len_packages + package_id + h5 + h6 + last_package + h8 + h9).encode()

    def read_payload(self, n): # n = head[5]
        rxBuffer, nRx = self.com1.getData(n)
        return rxBuffer, nRx

    def make_package(self, type='\\x00', payload:bytes=b'', len_packages='\\x00', h5='\\x00'):
        
        head = self.make_head(type=type, len_packages=len_packages, package_id=self.packageId, h5=h5)

        return (head.decode() + payload.decode() + self.EOF).encode()


    def send_handshake(self):
        self.com1.sendData(np.asarray(self.make_package(type=self.HANDSHAKE)))

    def send_ack(self):
        self.com1.sendData(np.asarray(self.make_package(type=self.ACK)))
    
    def main(self):
        try:
            print('Iniciou o main')

            print('Abriu a comunicação')

            t0 = calcula_tempo(time.ctime())

            # n = quantidade()
            print('-'*94)
            # print(f'\033[93mQuantidade de comandos {n}\033[0m\n')

            # command = comando(n, lista)

            print('Carregando a mensagem para transmissão: ')
            print('-'*94)
            txBuffer = command

            self.com1.sendData(np.asarray(self.make_package()))

        except:
            pass

    

serialName = "/dev/ttyACM1"  # Ubuntu (variacao de) Porta para utilização do arduino

def main():
    global lista
    try:
        print("Iniciou o main")

        #camada inferior à aplicação
        com1 = enlace(serialName) # Objeto que recebe o nome da porta serial
    

        com1.enable() # Inicia a conexão

        #informa que a comunicação iniciou
        print("Abriu a comunicação")
        inicial = calcula_tempo(time.ctime())

        # Gera uma somatória de comandos para serem transmitidos
        n = quantidade()
        print("-"*94)
        print(f'\033[93mQuantidade de comandos {n}\033[0m\n')
        
        comand = comando(n,lista)
       


        # time.sleep(.2)
        # com1.sendData(b'00')
        # time.sleep(1)


        print("Carregando mensagem para transmissão: ")
        print("-"*94)
        txBuffer = comand  #comando a ser transmitido

        #Verifica o tamanho do comando a ser transmitido



        #metodo da camada enlace, ele iniciará a transmissão 
        com1.sendData(np.asarray(txBuffer)) #Array de bytes

        


        #TESTE UM
        # time.sleep(.2)
        # com1.sendData(b'00')
        # time.sleep(1)



        #Detecta o tamanho da mensagem a ser transmitida em bytes
        txSize = com1.tx.getStatus()
        while txSize == 0:
            txSize = com1.tx.getStatus()


        print('Enviou = {}\033[0m' .format(txSize))
        print("Esperando resposta...")
        print("-"*94)

        #acesso aos bytes recebidos
        txLen = com1.rx.getBufferLen()
        while txLen ==0:
            txLen = com1.rx.getBufferLen()
            final = calcula_tempo(time.ctime())
            delta_t = variacao_tempo(inicial,final)
            if delta_t >= 5:
                print("Time out\n")

                break

        time.sleep(0.05)
        
        rxBuffer, nRx = com1.getData(txLen)

        time.sleep(0.05)
                
        #print(rxBuffer)
        if nRx != 0:
            resposta =  f"\n\033[92mRecebeu {nRx}\033[0m\n"
        if nRx != txSize and delta_t <5:
            resposta = f'\033[91mErro na transição:\033[0m\n  \n\033[92menviado: {n}\n\033[91mrecebido: {nRx}\033[0m'
        if delta_t >= 5:
            resposta = f'\033[93mFalha na comunicação\033[0m'
        
        print(resposta)


        #Encerra comunicação
        print("-"*(94))
        print("\033[95mComunicação encerrada\033[0m")
        print("-"*94)
        com1.disable()

    except Exception as erro:
        print("ops! :-\\")
        print(erro)
        com1.disable()
        

    #so roda o main quando for executado do terminal ... se for chamado dentro de outro modulo nao roda
if __name__ == "__main__":
    main()
