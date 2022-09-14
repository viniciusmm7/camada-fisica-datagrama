#####################################################
# Camada Física da Computação
#Carareto
#11/08/2022
#Aplicação
####################################################
from faulthandler import cancel_dump_traceback_later
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
        
        self.t0 = 0
        self.t1 = 0
        self.packetId = 0
        self.lastpacketId = 0

    # ----- Método para a primeira porta com arduíno
    #       se tiver mais de uma (sozinho, por exemplo)
    def _findArduino(self) -> list:
        result = []
        ports = list(serial.tools.list_ports.comports())
        c = 0
        for p in ports:
            result.append(f'/dev/ttyACM{c}')
            c += 1
        return result[0]

    # ===== MÉTODOS PARA EVITAR REPETIÇÃO DE CÓDIGO =====
    def waitBufferLen(self):
        rxLen = self.com1.rx.getBufferLen()
        while rxLen == 0:
            rxLen = self.com1.rx.getBufferLen()
            self.t1 = calcula_tempo(time.ctime())
            if calcula_tempo(self.t0, self.t1) > 5:
                raise Exception('Time out. Servidor não respondeu.')
        return rxLen

    def waitStatus(self):
        txSize = self.com1.tx.getStatus()
        while txSize == 0:
            txSize = self.com1.tx.getStatus()
        return txSize
    # ====================================================

    # ========= MÉTODOS PARA ADMINISTRAR PACOTES =========

    # ----- Quebrar os dados em payloads de até 114 bytes
    def make_payload_list(self, data):
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

    # ----- Cria o head do pacote
    def make_head(self, type='\\x00', h1='\\x00', h2='\\x00', len_packets='\\x00', packet_id='\\x00', h5='\\x00', h6='\\x00', last_packet='\\x00', h8='\\x00', h9='\\x00'):
        return (type + h1 + h2 + len_packets + packet_id + h5 + h6 + last_packet + h8 + h9).encode()

    # ----- Lê o payload (só para reduzir a complexidade do entendimento do main)
    def read_payload(self, n): # n = head[5]
        rxBuffer, nRx = self.com1.getData(n)
        return rxBuffer, nRx

    # ----- Cria o pacote de fato
    def make_packet(self, type='\\x00', payload:bytes=b'', len_packets='\\x00', h5='\\x00') -> bytes:
        if self.packetId < 16 and self.lastpacketId < 16:
            head = self.make_head(type=type, len_packets=len_packets, packet_id='\\x0'+format(self.packetId, 'x'), h5=h5, last_packet='\\x0'+format(self.lastpacketId, 'x'))
        elif self.packetId < 16:
            head = self.make_head(type=type, len_packets=len_packets, packet_id='\\x0'+format(self.packetId, 'x'), h5=h5, last_packet='\\x'+format(self.lastpacketId, 'x'))
        elif self.lastpacketId < 16:
            head = self.make_head(type=type, len_packets=len_packets, packet_id='\\x'+format(self.packetId, 'x'), h5=h5, last_packet='\\x0'+format(self.lastpacketId, 'x'))
        else:
            head = self.make_head(type=type, len_packets=len_packets, packet_id='\\x'+format(self.packetId, 'x'), h5=h5, last_packet='\\x'+format(self.lastpacketId, 'x'))

        return (head.decode() + payload.decode() + self.EOF).encode()

    # ----- Envia o handshake (só para reduzir a complexidade do entendimento do main)
    def send_handshake(self):
        self.com1.sendData(np.asarray(self.make_packet(type=self.HANDSHAKE)))
    
    # ----- Verifica se o pacote recebido é um handshake
    # verify_handshake = lambda self, rxBuffer: True if rxBuffer[0] == self.HANDSHAKE else False
    def verify_handshake(self, rxBuffer:bytes) -> bool:
        if rxBuffer[0] == self.HANDSHAKE:
            return True
        return False

    # ----- Envia o acknowledge (reduzir a complexidade do main)
    def send_ack(self):
        self.com1.sendData(np.asarray(self.make_packet(type=self.ACK)))

    # ----- Verifica se o pacote recebido é um acknowledge
    # verify_ack = lambda self, rxBuffer: True if rxBuffer[0] == self.ACK else False
    def verify_ack(self, rxBuffer) -> bool:
        if rxBuffer[0] == self.ACK:
            return True
        return False

    # ====================================================
    
    def main(self):
        try:
            print('Iniciou o main')
            data = '' # Qualquer coisa que deva ser mandado

            print('Abriu a comunicação')

            self.t0 = calcula_tempo(time.ctime())

            print('Enviando Handshake:')
            self.send_handshake()
            rxLen = self.waitBufferLen()
            rxBuffer, nRx = self.com1.getData(rxLen)
            
            if not self.verify_handshake(rxBuffer):
                raise Exception('O Handshake não é um Handshake.')

            payloads, len_packets = self.make_payload_list(data)

            while self.packetId < len_packets:
                self.com1.sendData(np.asarray(self.make_packet(payload=payloads[self.packetId], len_packets=len_packets)))
                txSize = self.waitStatus()
                self.packetId += 1
                
                # Acknowledge/Not Acknowledge
                rxLen = self.waitBufferLen()
                rxBuffer, nRx = self.com1.getData()

                if not self.verify_ack(rxBuffer):
                    self.packetId -= 1
                else:



            self.com1.sendData(np.asarray(self.make_packet()))

        except Exception as erro:
            print('Ops! :-\\')
            print(erro)

        finally:
            self.com1.disable()

    

# serialName = "/dev/ttyACM1"  # Ubuntu (variacao de) Porta para utilização do arduino

# def main():
#     global lista
#     try:
#         print("Iniciou o main")

#         #camada inferior à aplicação
#         com1 = enlace(serialName) # Objeto que recebe o nome da porta serial
    

#         com1.enable() # Inicia a conexão

#         #informa que a comunicação iniciou
#         print("Abriu a comunicação")
#         inicial = calcula_tempo(time.ctime())

#         # Gera uma somatória de comandos para serem transmitidos
#         n = quantidade()
#         print("-"*94)
#         print(f'\033[93mQuantidade de comandos {n}\033[0m\n')
        
#         comand = comando(n,lista)
       


#         # time.sleep(.2)
#         # com1.sendData(b'00')
#         # time.sleep(1)


#         print("Carregando mensagem para transmissão: ")
#         print("-"*94)
#         txBuffer = comand  #comando a ser transmitido

#         #Verifica o tamanho do comando a ser transmitido



#         #metodo da camada enlace, ele iniciará a transmissão 
#         com1.sendData(np.asarray(txBuffer)) #Array de bytes

        


#         #TESTE UM
#         # time.sleep(.2)
#         # com1.sendData(b'00')
#         # time.sleep(1)



#         #Detecta o tamanho da mensagem a ser transmitida em bytes
#         txSize = com1.tx.getStatus()
#         while txSize == 0:
#             txSize = com1.tx.getStatus()


#         print('Enviou = {}\033[0m' .format(txSize))
#         print("Esperando resposta...")
#         print("-"*94)

#         #acesso aos bytes recebidos
#         txLen = com1.rx.getBufferLen()
#         while txLen ==0:
#             txLen = com1.rx.getBufferLen()
#             final = calcula_tempo(time.ctime())
#             delta_t = variacao_tempo(inicial,final)
#             if delta_t >= 5:
#                 print("Time out\n")

#                 break

#         time.sleep(0.05)
        
#         rxBuffer, nRx = com1.getData(txLen)

#         time.sleep(0.05)
                
#         #print(rxBuffer)
#         if nRx != 0:
#             resposta =  f"\n\033[92mRecebeu {nRx}\033[0m\n"
#         if nRx != txSize and delta_t <5:
#             resposta = f'\033[91mErro na transição:\033[0m\n  \n\033[92menviado: {n}\n\033[91mrecebido: {nRx}\033[0m'
#         if delta_t >= 5:
#             resposta = f'\033[93mFalha na comunicação\033[0m'
        
#         print(resposta)


#         #Encerra comunicação
#         print("-"*(94))
#         print("\033[95mComunicação encerrada\033[0m")
#         print("-"*94)
#         com1.disable()

#     except Exception as erro:
#         print("ops! :-\\")
#         print(erro)
#         com1.disable()
        

    #so roda o main quando for executado do terminal ... se for chamado dentro de outro modulo nao roda
if __name__ == "__main__":
    main()
