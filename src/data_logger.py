import csv
import os
from datetime import datetime

class DataLogger:
    def __init__(self, folder="data"):
        if not os.path.exists(folder): os.makedirs(folder)
        ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.filename = os.path.join(folder, f"tugaspace_{ts}.csv")
        self.headers = [
            "timestamp_pc", "tempo_ms", "pressao", "temp", "alt_baro",
            "lat", "lon", "gps_alt", "accX", "accY", "accZ",
            "distA", "distB", "distC", "posX", "posY", "posZ",
            "pressao2", "temp2", "alt_baro2", "bateria_pct"
        ]
        # Mantém o ficheiro aberto na memória
        self.file = open(self.filename, 'w', newline='')
        self.writer = csv.writer(self.file)
        self.writer.writerow(self.headers)
        self.file.flush()

    def log(self, d):
        row = [
            datetime.now().strftime("%H:%M:%S.%f")[:-3], d["tempo"],
            d["pressao"], d["temp"], d["alt_baro"],
            d["gps"][0], d["gps"][1], d["gps"][2],
            d["accel"][0], d["accel"][1], d["accel"][2],
            d["dist"][0], d["dist"][1], d["dist"][2],
            d["pos_xyz"][0], d["pos_xyz"][1], d["pos_xyz"][2],
            d["pressao2"], d["temp2"], d["alt_baro2"], d["bateria_pct"]
        ]
        self.writer.writerow(row)
        self.file.flush() # Garante que os dados são escritos fisicamente no disco na hora

    def fechar(self):
        if self.file and not self.file.closed:
            self.file.close()