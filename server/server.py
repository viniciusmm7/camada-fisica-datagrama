#####################################################
# Camada Física da Computação
#Carareto
#11/08/2022
#Aplicação
####################################################


#esta é a camada superior, de aplicação do seu software de comunicação serial UART.
#para acompanhar a execução e identificar erros, construa prints ao longo do código! 


from enlace import *
import time, platform, serial.tools.list_ports
import numpy as np

# voce deverá descomentar e configurar a porta com através da qual ira fazer comunicaçao
# para saber a sua porta, execute no terminal :
# python -m serial.tools.list_ports
# para autorizar:
# sudo chmod a+rw /dev/ttyACM0
# serialName = "/dev/ttyACM0"           # Ubuntu (variacao de)

class Server:
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

    def _findArduino(self) -> list:
        result = []
        ports = list(serial.tools.list_ports.comports())
        c = 0
        for p in ports:
            result.append(f'/dev/ttyACM{c}')
            c += 1
        return result[0]

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

            rxLen = self.waitBufferLen()
            self.send_handshake()
            rxBuffer, nRx = self.com1.getData(rxLen)
            rxBuffer = bytearray(rxBuffer)

            while not rxBuffer.endswith(b'\\x01'):
                rxLen = self.waitBufferLen()

                rxBuffer = rxBuffer.decode()
                a = self.com1.getData(rxLen)[0].decode()
                rxBuffer += a
                rxBuffer = rxBuffer.encode()

            time.sleep(0.05)
            array_list = np.asarray(rxBuffer.decode().split('/'))
            sup = ''
            qtd = 0

            for item in array_list:
                sup += item + '/'

            for command in sup.split('/'):
                if command == '\\x01':
                    print('Acabou, recebi o eof')
                    break
                else:
                    qtd += 1

                print(f'\033[92m{qtd}ª comando: {command}\033[0m')
            print(f'\n\033[93mQuantidade de comandos {qtd}\033[0m\n')

            print("recebeu {} bytes" .format(nRx))

            self.com1.sendData(np.asarray(bytes(qtd))) #Array de bytes
            time.sleep(0.05)

            # A camada enlace possui uma camada inferior, TX possui um método para conhecermos o status da transmissão
            # O método não deve estar funcionando quando usado como abaixo. deve estar retornando zero. Tente entender como esse método funciona e faça-o funcionar.
            txSize = self.waitStatus()

            print('enviou = {}'.format(txSize))
        
            # Encerra comunicação
            print("-------------------------")
            print("Comunicação encerrada")
            print("-------------------------")
            self.com1.disable()

        except Exception as erro:
            print("ops! :-\\")
            print(erro)
            self.com1.disable()


# def main():
#     try:
#         print("Iniciou o main")
#         #declaramos um objeto do tipo enlace com o nome "com". Essa é a camada inferior à aplicação. Observe que um parametro
#         #para declarar esse objeto é o nome da porta.
#         com1 = enlace(serialName)
    
#         # Ativa comunicacao. Inicia os threads e a comunicação seiral 
#         com1.enable()
#         #Se chegamos até aqui, a comunicação foi aberta com sucesso. Faça um print para informar.
#         print("Abriu a comunicação")
        
#         #Agora vamos iniciar a recepção dos dados. Se algo chegou ao RX, deve estar automaticamente guardado
#         #Observe o que faz a rotina dentro do thread RX
#         #print um aviso de que a recepção vai começar.
        
#         #Será que todos os bytes enviados estão realmente guardadas? Será que conseguimos verificar?
#         #Veja o que faz a funcao do enlaceRX  getBufferLen
      
#         #acesso aos bytes recebidos
#         rxLen = com1.rx.getBufferLen()
#         while rxLen == 0:
#             rxLen = com1.rx.getBufferLen()
        
#         rxBuffer, nRx = com1.getData(rxLen)
#         rxBuffer = bytearray(rxBuffer)

#         while not rxBuffer.endswith(b'\\x01'):
#             rxLen = com1.rx.getBufferLen()
#             while rxLen == 0:
#                 rxLen = com1.rx.getBufferLen()

#             rxBuffer = rxBuffer.decode()
#             a = com1.getData(rxLen)[0].decode()
#             print(f'{a}')
#             rxBuffer += a
#             rxBuffer = rxBuffer.encode()

#         time.sleep(0.05)
#         array_list = np.asarray(rxBuffer.decode().split('/'))
#         sup = ''
#         qtd = 0

#         for item in array_list:
#             sup += item + '/'
        
#         for command in sup.split('/'):
#             if command == '\\x01':
#                 print('ACABOU, RECEBI O END BYTE')
#                 break
#             else:
#                 qtd += 1

#             print(f'\033[92m{qtd}ª comando: {command}\033[0m')

#         print(f'\n\033[93mQuantidade de comandos {qtd}\033[0m\n')

#         # ===== ERRO HARD CODED =====
#         # rxBuffer = bytes(str(rxBuffer.decode() + '/\x66').encode())

#         print("recebeu {} bytes" .format(nRx))

#         com1.sendData(np.asarray(bytes(qtd))) #Array de bytes
#         time.sleep(0.05)

#         # A camada enlace possui uma camada inferior, TX possui um método para conhecermos o status da transmissão
#         # O método não deve estar funcionando quando usado como abaixo. deve estar retornando zero. Tente entender como esse método funciona e faça-o funcionar.
#         txSize = com1.tx.getStatus()
#         while txSize == 0:
#             txSize = com1.tx.getStatus()

#         print('enviou = {}'.format(txSize))
    
#         # Encerra comunicação
#         print("-------------------------")
#         print("Comunicação encerrada")
#         print("-------------------------")
#         com1.disable()
        
#     except Exception as erro:
#         print("ops! :-\\")
#         print(erro)
#         com1.disable()
        

    #so roda o main quando for executado do terminal ... se for chamado dentro de outro modulo nao roda
if __name__ == "__main__":
    server = Server()
    print('Criou o objeto Server')
    server.main()