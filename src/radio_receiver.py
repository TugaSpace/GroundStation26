import serial
import struct

class RadioReceiver:
    def __init__(self, port, baudrate=9600, chave_xor=0xAC):
        # Timeout curto para não travar a interface
        self.ser = serial.Serial(port, baudrate, timeout=0.05)
        self.chave_xor = chave_xor
        # Formato ATUALIZADO: 3s(ID), L(Tempo), 13f(Dados + novos), 6H(Dist/Pos), B(Checksum)
        # Novos campos: pressao2, temp2, altBaro2, bateria_pct (4 floats)
        self.formato = "<3sL13f6HB"
        self.tamanho_pacote = struct.calcsize(self.formato)

    def descriptografar(self, dados):
        lista_bytes = bytearray(dados)
        # Pula os 3 bytes do cabeçalho "TS\0"
        for i in range(3, len(lista_bytes)):
            lista_bytes[i] ^= self.chave_xor
        return bytes(lista_bytes)

    def validar_checksum(self, dados_limpos):
        cs_recebido = dados_limpos[-1]
        cs_calculado = 0
        for i in range(len(dados_limpos) - 1):
            cs_calculado ^= dados_limpos[i]
        return cs_recebido == cs_calculado

    def receber_pacote(self):
        # Varre ativamente o buffer para limpar lixo até achar o início do pacote
        while self.ser.in_waiting >= self.tamanho_pacote:
            if self.ser.read(1) == b'T':
                if self.ser.read(1) == b'S':
                    resto = self.ser.read(self.tamanho_pacote - 2)
                    if len(resto) == self.tamanho_pacote - 2:
                        pacote_bruto = b'TS' + resto
                        limpo = self.descriptografar(pacote_bruto)
                        
                        if self.validar_checksum(limpo):
                            res = struct.unpack(self.formato, limpo)
                            return {
                                "tempo": res[1], "pressao": res[2], "temp": res[3],
                                "alt_baro": res[4], "gps": (res[5], res[6], res[7]),
                                "accel": (res[8], res[9], res[10]),
                                "dist": (res[11], res[12], res[13]),
                                "pos_xyz": (res[14], res[15], res[16]),
                                # Novos campos BMP2 e bateria
                                "pressao2": res[17], "temp2": res[18], "alt_baro2": res[19],
                                "bateria_pct": res[20]
                            }
        return None

    def fechar(self):
        if self.ser.is_open:
            self.ser.close()