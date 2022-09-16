#####################################################
# Camada Física da Computação
#Carareto
#11/08/2022
#Aplicação
####################################################


#esta é a camada superior, de aplicação do seu software de comunicação serial UART.
#para acompanhar a execução e identificar erros, construa prints ao longo do código! 


from html.entities import html5
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
        self.HANDSHAKE = b'\x01'
        self.ACK = b'\x02'
        self.ERROR = b'\x03'
        self.EOF = b'\xAA\xBB\xCC\xDD'

        self.os = platform.system().lower()
        self.serialName = self._findArduino()
        self.com1 = enlace(self.serialName)
        self.com1.enable()
        
        self.packetId = 0
        self.lastpacketId = 0
        # self.lenLastPacket = 0


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
        return rxLen

    def waitStatus(self):
        txSize = self.com1.tx.getStatus()
        while txSize == 0:
            txSize = self.com1.tx.getStatus()
        return txSize
    # ====================================================

    # ========= MÉTODOS PARA ADMINISTRAR PACOTES =========

    # ----- Quebrar os dados em payloads de até 114 bytes
    def make_payload_list(self, data) -> list:
        limit = 114
        payload_list = []

        if limit > len(data):
            limit = len(data)
        payload_list.append(data[:limit])
        data = data[limit:]

        return payload_list, len(payload_list)

    # ----- Cria o head do pacote
    def make_head(self, type=b'\x00', h1=b'\x00', h2=b'\x00', len_packets=b'\x00', packet_id=b'\x00', h5=b'\x00', h6=b'\x00', last_packet=b'\x00', h8=b'\x00', h9=b'\x00'):
        return type + h1 + h2 + len_packets + packet_id + h5 + h6 + last_packet + h8 + h9

    # ----- Lê o payload (só para reduzir a complexidade do entendimento do main)
    def read_payload(self, rxBuffer): # n = head[5]
        h5 = rxBuffer[5]+10
        print('H5 DO READPAYLOAD',h5-10)
        print(rxBuffer[10:h5])
        return rxBuffer[10:h5]

    def get_head_info(self, rxBuffer:bytes):
        head = rxBuffer[:10] # 10 primeiros itens são o head

        len_packets = head[3] # quantidade de pacotes (int)
        packet_id   = head[4] # id do pactote (int)
        h5          = head[5] # se o tipo for handshake, id do arquivo, senão, tamanho do payload (int)
        h6          = head[6] # pacote para recomeçar quando há erro (int)
        last_packet = head[7] # id do último pacote recebido com sucesso (int)

        return len_packets, packet_id, h5, h6, last_packet

    # ----- Cria o pacote de fato
    def make_packet(self, type=b'\x00', payload:bytes=b'', len_packets=b'\x00', h5=b'\x00', h6=b'\x00') -> bytes:
        head = self.make_head(type=type, len_packets=len_packets, packet_id=self.packetId.to_bytes(1, 'big'), h5=h5, last_packet=self.lastpacketId.to_bytes(1, 'big'))
        return head + payload + self.EOF

    # ----- Envia o handshake (só para reduzir a complexidade do entendimento do main)
    def send_handshake(self):
        self.com1.sendData(np.asarray(self.make_packet(type=self.HANDSHAKE)))

    # ----- Verifica se o pacote recebido é um handshake
    # verify_handshake = lambda self, rxBuffer: True if rxBuffer[0] == self.HANDSHAKE else False
    def verify_handshake(self, rxBuffer:bytes) -> bool:
        if rxBuffer[0].to_bytes(1, 'big') == self.HANDSHAKE:
            return True
        return False

    # ----- Envia o acknowledge (reduzir a complexidade do main)
    def send_ack(self, len_packets:int, h5:int):
        self.com1.sendData(np.asarray(self.make_packet(type=self.ACK, len_packets=len_packets.to_bytes(1, 'big'), h5=h5.to_bytes(1, 'big'))))

    # ----- Verifica se o pacote recebido é um acknowledge
    # verify_ack = lambda self, rxBuffer: True if rxBuffer[0] == self.ACK else False
    def verify_ack(self, rxBuffer:bytes) -> bool:
        if rxBuffer[0].to_bytes(1, 'big') == self.ACK:
            return True
        return False

    # ----- Envia o erro
    def send_error(self):
        self.com1.sendData(np.asarray(self.make_packet(type=self.ERROR)))

    # ====================================================

    def main(self):
        try:
            print('Iniciou o main')
            
            print('Abriu a comunicação')

            # ===== HANDSHAKE
            rxLen = self.waitBufferLen()
            
            rxBuffer, nRx = self.com1.getData(rxLen)
            while not rxBuffer.endswith(self.EOF):
                rxLen = self.waitBufferLen()
                a = self.com1.getData(rxLen)[0]
                rxBuffer += a
                time.sleep(0.05)
            
            if not self.verify_handshake(rxBuffer):
                raise Exception('O Handshake não é um Handshake')
            print('Handshake recebido')

            # Quantidade de pacotes de payload
            len_packets = self.get_head_info(rxBuffer)[0]

            self.send_handshake()
            print('Enviou o handshake')
            # ===== END HANDSHAKE

            # ===== DADOS
            while self.packetId < len_packets:
                rxLen = self.waitBufferLen()
                rxBuffer, nRx = self.com1.getData(rxLen)
                # Enquanto o pacote não estiver completo, concatena
                while not rxBuffer.endswith(self.EOF):
                    rxLen = self.waitBufferLen()
                    a = self.com1.getData(rxLen)[0]
                    rxBuffer += a
                    time.sleep(0.05)

                _, packet_id, h5, h6, last_packet = self.get_head_info(rxBuffer)
                
                # DESCOMENTAR A LINHA ABAIXO PARA FORÇAR O ERRO DE ID DE PACOTE
                # packet_id = -1
                if packet_id != self.packetId:
                    # ENVIAR ERRO
                    print('ERRO')
                    self.send_error()

                else:
                    self.send_ack(len_packets=len_packets, h5=h5)
                    print(self.read_payload(rxBuffer))
                    self.packetId += 1
            
            self.com1.sendData(np.asarray(self.make_packet())) #Array de bytes
            time.sleep(0.05)

            # A camada enlace possui uma camada inferior, TX possui um método para conhecermos o status da transmissão
            # O método não deve estar funcionando quando usado como abaixo. deve estar retornando zero. Tente entender como esse método funciona e faça-o funcionar.
            txSize = self.waitStatus()

            print('enviou = {}'.format(txSize))
        
            # Encerra comunicação
            print("-------------------------")
            print("Comunicação encerrada")
            print("-------------------------")

        # except Exception as erro:
        #     print("ops! :-\\")
        #     print(erro)

        finally:
            self.com1.disable()

if __name__ == "__main__":
    server = Server()
    server.main()