#####################################################
# Camada Física da Computação
#Carareto
#11/08/2022
#Aplicação
####################################################
from faulthandler import cancel_dump_traceback_later
from http import client
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

        self.status = 0
        
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
            if self.status==1:
                break
            rxLen = self.com1.rx.getBufferLen()
            self.t1 = calcula_tempo(time.ctime())
            if variacao_tempo(self.t0, self.t1) > 5 and self.status == 0:
                res = input("Tentar reconexção?(s/n) ")

                if res.lower() == "s":
                    self.t0 = calcula_tempo(time.ctime())
                    self.send_handshake()
                else:
                    raise Exception('Time out. Servidor não respondeu.')


            if rxLen != 0:
                break
                

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
        cont = 0 


        if limit > len(data):
            limit = len(data)
        payload_list.append(data[:limit])
        data = data[limit:]
        print(len(payload_list))
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
            head = self.make_head(type=type, len_packets=len_packets, packet_id='\\x0'+hex(self.packetId)[2:], h5=h5, last_packet='\\x0'+hex(self.lastpacketId)[2:])
        elif self.packetId < 16:
            head = self.make_head(type=type, len_packets=len_packets, packet_id='\\x0'+hex(self.packetId)[2:], h5=h5, last_packet='\\x'+hex(self.lastpacketId)[2:])
        elif self.lastpacketId < 16:
            head = self.make_head(type=type, len_packets=len_packets, packet_id='\\x'+hex(self.packetId )[2:], h5=h5, last_packet='\\x0'+hex(self.lastpacketId)[2:])
        else:
            head = self.make_head(type=type, len_packets=len_packets, packet_id='\\x'+hex(self.packetId)[2:], h5=h5, last_packet='\\x'+hex(self.lastpacketId)[2:])

        return (head.decode() + payload.decode() + self.EOF).encode()

    # ----- Envia o handshake (só para reduzir a complexidade do entendimento do main)
    def send_handshake(self):
        
        self.com1.sendData(np.asarray(self.make_packet(type=self.HANDSHAKE)))
        
    
    # ----- Verifica se o pacote recebido é um handshake
    # verify_handshake = lambda self, rxBuffer: True if rxBuffer[0] == self.HANDSHAKE else False
    def verify_handshake(self, rxBuffer:bytes) -> bool:
        self.status = 1
        if  '\\' + rxBuffer.decode().split('\\')[1] == self.HANDSHAKE:

            return True

        return False

    # ----- Envia o acknowledge (reduzir a complexidade do main)
    def send_ack(self):
        self.com1.sendData(np.asarray(self.make_packet(type=self.ACK)))

    # ----- Verifica se o pacote recebido é um acknowledge
    # verify_ack = lambda self, rxBuffer: True if rxBuffer[0] == self.ACK else False
    def verify_ack(self, rxBuffer:bytes,len_packets) -> bool:
        ver = rxBuffer.decode().split('\\') 
        ver.pop(0)
        if ver[0] == self.ACK and ver[3]==len_packets:
            return True
        
        return False

    # ====================================================
    
    def main(self):
        try:
            print('Iniciou o main')
          
            data = (123665476457676357632412314212413231416).to_bytes(16,'big')
            print(len(data))
            print('Abriu a comunicação')

            self.t0 = calcula_tempo(time.ctime())

            print('Enviando Handshake:')
            
            self.send_handshake()
            rxLen = self.waitBufferLen()
            rxBuffer, nRx = self.com1.getData(rxLen)

            
            if not self.verify_handshake(rxBuffer):
                raise Exception('O Handshake não é um Handshake.')
            else:
                print('*'*98)
                print('Handshake recebido')

            payloads, len_packets = self.make_payload_list(data)
       

            while self.packetId < len_packets:
                self.com1.sendData(np.asarray(self.make_packet(payload=payloads[self.packetId], len_packets=hex(len_packets))))
    
                txSize = self.waitStatus()
                self.packetId += 1
         
                # Acknowledge/Not Acknowledge
                rxLen = self.waitBufferLen()
                rxBuffer, nRx = self.com1.getData(rxLen)
                print('crasg')
                if not self.verify_ack(rxBuffer,len_packets):
                    print('to aqui')
                    self.packetId -= 1
                    break
                else:
                    print('acabou')
                    print(f'Enviado {nRx}')
                    break
            #self.com1.sendData(np.asarray(self.make_packet()))


        except Exception as erro:
            print("ops! :-\\")
            print(erro)
   
       
        finally:
            self.com1.disable()
        
    #so roda o main quando for executado do terminal ... se for chamado dentro de outro modulo nao roda
if __name__ == "__main__":
    client = Client()
    client.main()
