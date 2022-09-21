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
        self.HANDSHAKE = b'\x01'
        self.ACK = b'\x02'
        self.EOF = b'\xAA\xBB\xCC\xDD'
        self.ERROR = b'\x03'
        self.REENVIO = b'\x01' #WTF


        self.os = platform.system().lower()
        self.serialName = self._findArduino()
        self.com1 = enlace(self.serialName)
        self.com1.enable()

        self.status = 0
        
        self.t0 = 0
        self.t1 = 0
        self.packetId = 0
        self.lastpacketId = 0
        self.lenPackets = 0 

        
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
                    self.send_handshake(len_packets=self.lenPackets.to_bytes(1,'big'))
                    rxLen = self.waitBufferLen()
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

        while len(data) > 0:
            if limit > len(data):
                limit = len(data)
            payload_list.append(data[:limit])
            data = data[limit:]
        #print(len(payload_list))
        return payload_list, len(payload_list)

    # ----- Cria o head do pacote
    def make_head(self, type=b'\x00', h1=b'\x00', h2=b'\x00', len_packets=b'\x00', packet_id=b'\x00', h5=b'\x00', h6=b'\x00', last_packet=b'\x00', h8=b'\x00', h9=b'\x00'):
        return (type + h1 + h2 +len_packets + packet_id + h5 + h6 + last_packet + h8 + h9)

    # ----- Lê o payload (só para reduzir a complexidade do entendimento do main)
    def read_payload(self, n): # n = head[5]
        rxBuffer, nRx = self.com1.getData(n)
        return rxBuffer, nRx

    # ----- Cria o pacote de fato
    def make_packet(self, type=b'\x00', payload:bytes=b'', len_packets=b'\x00', h5:bytes=b'\x00') -> bytes:

        head = self.make_head(type=type, len_packets=len_packets, packet_id=self.packetId.to_bytes(1,'big'), h5=h5, last_packet=self.lastpacketId.to_bytes(1,'big'))
        return (head + payload + self.EOF)

    # ----- Envia o handshake (só para reduzir a complexidade do entendimento do main)
    def send_handshake(self,len_packets):     
        self.com1.sendData(np.asarray(self.make_packet(type=self.HANDSHAKE, len_packets=len_packets)))
        
    
    # ----- Verifica se o pacote recebido é um handshake
    # verify_handshake = lambda self, rxBuffer: True if rxBuffer[0] == self.HANDSHAKE else False
    def verify_handshake(self, rxBuffer:bytes) -> bool:
        
        self.status = 1
       
        if  rxBuffer[0].to_bytes(1,'big') == self.HANDSHAKE:
            return True

        return False

    # ----- Envia o acknowledge (reduzir a complexidade do main)
    def send_ack(self):
        self.com1.sendData(np.asarray(self.make_packet(type=self.ACK)))

    # ----- Verifica se o pacote recebido é um acknowledge
    # verify_ack = lambda self, rxBuffer: True if rxBuffer[0] == self.ACK else False
    def verify_ack(self, rxBuffer:bytes) -> bool:
        
        if rxBuffer[0] == self.ACK:
            return True
        
        return False
    # ====================================================

    def get_error_info(self, rxBuffer:bytes):

        head = rxBuffer[:10] # 10 primeiros itens são o head
     
        h0 = head[0].to_bytes(1,'big')
  
        return h0,None,None


    def main(self):
        try:
            print('Iniciou o main')
          

            #print(len(data))
            print('Abriu a comunicação')

            self.t0 = calcula_tempo(time.ctime())
            
            
            print('Enviando Handshake:')
            n = quantidade()
            data = comando(n,lista)
            payloads, self.lenPackets = self.make_payload_list(data)
            self.com1.rx.clearBuffer()
            
            self.send_handshake(self.lenPackets.to_bytes(1,'big'))
   
            rxLen = self.waitBufferLen()
            rxBuffer, nRx = self.com1.getData(rxLen)
            

            if not self.verify_handshake(rxBuffer):

                raise Exception('O Handshake não é um Handshake.')
            else:
                print('*'*98)
                print('\033[92mHandshake recebido\033[0m')

            

            print(f'quantidade de comandos {n}') 
          
            print(f'quantidade de payloads {len(payloads)}')
         
      
            
       
            #self.com1.sendData(np.asarray(self.make_packet(payload=payloads[self.packetId], len_packets=hex(len_packets))))
            while self.packetId < self.lenPackets:
                susi = hex(len(payloads[self.packetId])).encode()[2:]
                #vel = bytearray.fromhex(susi)
        
                print(susi)
                #print(vel)

           
                #envio de pacotes
                self.com1.sendData(np.asarray(self.make_packet(payload=payloads[self.packetId], len_packets=self.lenPackets.to_bytes(1,'big'),h5=vel)))
                time.sleep(0.1)
                #recebe a resposta do servidor
                rxLen = self.waitBufferLen()
                rxBuffer, nRx = self.com1.getData(rxLen)
              

                while not rxBuffer.endswith(self.EOF):
                   # print('infinit')
                    rxLen = self.waitBufferLen()
                    a = self.com1.getData(rxLen)[0]
                    rxBuffer += a
                    time.sleep(0.05)

                

                #verifica rx
                mens,packet_id, last_packet= self.get_error_info(rxBuffer)
                

                if mens == self.ERROR:
                    print('UEPA')
                    self.com1.sendData(np.asarray(self.make_packet(payload=payloads[self.packetId], len_packets=self.lenPackets.to_bytes(1,'big'))))
                    time.sleep(0.1)
                    rxLen = self.waitBufferLen()
                    rxBuffer, nRx = self.com1.getData(rxLen)
                
                elif mens == self.ACK:
         
                    
                    self.packetId += 1

                    #else:
                    txSize = self.waitStatus()
                    
                    self.lastpacketId = self.packetId - 1
                
                    # Acknowledge/Not Acknowledge
                    rxLen = self.waitBufferLen()
                    rxBuffer, nRx = self.com1.getData(rxLen)
            
                    
                    print(f'Enviando pacote {self.packetId}')
                    print(f'Payload tamanho {txSize-14}')
                
                else:
        
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