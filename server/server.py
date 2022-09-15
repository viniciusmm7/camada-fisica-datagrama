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
        
        self.packetId = '\\x00'
        # self.lastpacketId = 0

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
    def make_head(self, type='\\x00', h1='\\x00', h2='\\x00', len_packets='\\x00', packet_id='\\x00', h5='\\x00', h6='\\x00', last_packet='\\x00', h8='\\x00', h9='\\x00'):
        return (type + h1 + h2 + len_packets + packet_id + h5 + h6 + last_packet + h8 + h9).encode()

    # ----- Lê o payload (só para reduzir a complexidade do entendimento do main)
    def read_payload(self, n): # n = head[5]
        rxBuffer, nRx = self.com1.getData(n)
        return rxBuffer, nRx

    # ----- Cria o pacote de fato
    def make_packet(self, type='\\x03', payload:bytes=b'', len_packets='\\x00', h5='\\x00') -> bytes:
        head = self.make_head(type=type, len_packets=len_packets, packet_id=self.packetId, h5=h5)
        return (head.decode() + payload.decode() + self.EOF).encode()

    # ----- Envia o handshake (só para reduzir a complexidade do entendimento do main)
    def send_handshake(self):
        self.com1.sendData(np.asarray(self.make_packet(type=self.HANDSHAKE)))

    # ----- Envia o acknowledge (reduzir a complexidade do main)
    def send_ack(self):
        self.com1.sendData(np.asarray(self.make_packet(type=self.ACK)))

    # ====================================================

    def main(self):
        try:
            print('Iniciou o main')
            
            print('Abriu a comunicação')

            rxLen = self.waitBufferLen()
            self.send_handshake()
            print('Enviou o handshake')
            rxBuffer, nRx = self.com1.getData(rxLen)
            rxBuffer = bytearray(rxBuffer)

            while not rxBuffer.endswith(b'\\x01'):
                rxLen = self.waitBufferLen()

                rxBuffer = rxBuffer.decode()
                a = self.com1.getData(rxLen)[0].decode()
                rxBuffer += a
                rxBuffer = rxBuffer.encode()

            time.sleep(0.05)

            print("recebeu {} bytes" .format(nRx))

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

        except Exception as erro:
            print("ops! :-\\")
            print(erro)

        finally:
            self.com1.disable()

if __name__ == "__main__":
    server = Server()
    server.main()