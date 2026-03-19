from src.radio_receiver import RadioReceiver
from src.data_logger import DataLogger
import time

# Configuração
PORTA_SERIAL = 'COM3' # Altera para a tua porta
radio = RadioReceiver(PORTA_SERIAL)
logger = DataLogger()

print(f"Gravação iniciada em: {logger.filename}")
print("A ler telemetria... Prime CTRL+C para parar.")

try:
    while True:
        pacote = radio.receber_pacote()
        if pacote:
            # 1. Grava no ficheiro
            logger.log(pacote)
            
            # 2. Mostra no ecrã para debug
            print(f"Sucesso: Tempo {pacote['tempo']}ms | Alt: {pacote['alt_baro']}m")
        
        # Pequeno alívio para o processador
        time.sleep(0.01)

except KeyboardInterrupt:
    print("\nParando gravação e fechando rádio...")
    radio.fechar()