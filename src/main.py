import sys
import os
import time
import random
import csv

# Ocultar avisos de aceleração de hardware do Chromium (WebEngine) no terminal
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--log-level=3 --disable-logging"

from PyQt6.QtWidgets import QApplication, QFileDialog
from PyQt6.QtCore import QTimer
import qdarktheme
from src.radio_receiver import RadioReceiver
from src.data_logger import DataLogger
from src.dashboard import GroundStationUI
from src.simulator import FlightSimulator

class TugaSpaceController:
    def __init__(self):
        self.app = QApplication(sys.argv)
        # Aplica um tema moderno (dark ou light)
        try:
            qdarktheme.setup_theme("dark")
        except AttributeError:
            # Fallback para versões mais antigas do pyqtdarktheme (v1.x)
            self.app.setStyleSheet(qdarktheme.load_stylesheet("dark"))
        except Exception as e:
            print(f"Aviso: Não foi possível carregar o tema escuro. Erro: {e}")
        self.ui = GroundStationUI()
        self.radio = None
        self.logger = None
        self.simulando = False
        
        self.replaying = False
        self.replay_playing = False
        self.replay_packets = []
        self.replay_index = 0
        
        # Liga o botão de conexão
        self.ui.btn_conectar.clicked.connect(self.toggle_conexao)
        
        # Liga os eventos do Player de Replay
        self.ui.btn_load_log.clicked.connect(self.load_log)
        self.ui.btn_prev.clicked.connect(self.prev_frame)
        self.ui.btn_next.clicked.connect(self.next_frame)
        self.ui.btn_play_pause.clicked.connect(self.toggle_play_pause)
        self.ui.slider_replay.sliderMoved.connect(self.slider_moved)
        
        # Liga os atalhos de teclado (setas) ao Replay
        self.ui.on_key_right = lambda: self.next_frame() if self.replaying else None
        self.ui.on_key_left = lambda: self.prev_frame() if self.replaying else None
        
        # Timer de leitura (50Hz)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_loop)

        # Inicializa o simulador
        self.simulator = FlightSimulator()

    def toggle_conexao(self):
        # Se já estiver conectado ou simulando, desconecta
        if self.radio or self.simulando:
            self.desconectar()
            return

        porta = self.ui.combo_portas.currentText()
        
        if porta == "TESTE SIMULADO":
            self.iniciar_simulacao()
        else:
            self.iniciar_radio(porta)

    def iniciar_radio(self, porta):
        try:
            baud = int(self.ui.combo_baud.currentText())
            self.radio = RadioReceiver(porta, baud)
            self.logger = DataLogger() # Novo log
            
            self.ui.set_status_conexao(True, porta)
            self.simulando = False
            self.timer.start(200) # 5 Hz (200ms de intervalo)
            print(f"Rádio conectado em {porta}")
        except Exception as e:
            self.ui.lbl_status.setText(f"Erro Serial: {str(e)[:25]}")
            self.radio = None

    def iniciar_simulacao(self):
        print("A iniciar simulação...")
        self.simulando = True
        self.radio = None
        try:
            self.logger = DataLogger(folder="data_simulada")
        except:
            print("Aviso: Não foi possível criar pasta de log, mas a simulação vai continuar.")
        
        self.ui.set_status_conexao(True, "SIMULAÇÃO")
        self.simulator.reset()
        self.timer.start(200)  # 5 Hz (200ms) simulação igual à realidade
        print("DEBUG: Timer de simulação iniciado!")
        
    def load_log(self):
        fname, _ = QFileDialog.getOpenFileName(self.ui, "Abrir Log de Telemetria", "data", "CSV Files (*.csv)")
        if fname:
            self.desconectar()
            self.replay_packets = []
            try:
                with open(fname, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        try:
                            pacote = {
                                "tempo": int(row["tempo_ms"]), "pressao": float(row["pressao"]),
                                "temp": float(row["temp"]), "alt_baro": float(row["alt_baro"]),
                                "gps": (float(row["lat"]), float(row["lon"]), float(row["gps_alt"])),
                                "accel": (float(row["accX"]), float(row["accY"]), float(row["accZ"])),
                                "dist": (int(row["distA"]), int(row["distB"]), int(row["distC"])),
                                "pos_xyz": (int(row["posX"]), int(row["posY"]), int(row["posZ"])),
                                "pressao2": float(row["pressao2"]), "temp2": float(row["temp2"]),
                                "alt_baro2": float(row["alt_baro2"]), "bateria_pct": float(row["bateria_pct"])
                            }
                            self.replay_packets.append(pacote)
                        except ValueError:
                            continue # Ignora linhas incompletas
                
                if self.replay_packets:
                    self.replaying = True
                    self.replay_index = 0
                    self.replay_playing = False
                    
                    self.ui.btn_prev.setEnabled(True)
                    self.ui.btn_play_pause.setEnabled(True)
                    self.ui.btn_next.setEnabled(True)
                    self.ui.slider_replay.setEnabled(True)
                    self.ui.slider_replay.setMinimum(0)
                    self.ui.slider_replay.setMaximum(len(self.replay_packets) - 1)
                    self.ui.slider_replay.setValue(0)
                    
                    self.ui.set_status_conexao(True, f"REPLAY: {os.path.basename(fname)}")
                    self.update_replay_ui()
                else:
                    self.ui.lbl_replay_info.setText("Erro: Nenhum pacote válido no CSV.")
            except Exception as e:
                self.ui.lbl_replay_info.setText(f"Erro ao ler CSV: {e}")

    def toggle_play_pause(self):
        self.replay_playing = not self.replay_playing
        if self.replay_playing:
            self.timer.start(200) # Reproduz fielmente a 5Hz
            self.ui.btn_play_pause.setText("⏸ Pause")
        else:
            self.timer.stop()
            self.ui.btn_play_pause.setText("▶️ Play")
            
    def prev_frame(self):
        if self.replay_index > 0: self.replay_index -= 1; self.update_replay_ui()
            
    def next_frame(self):
        if self.replay_index < len(self.replay_packets) - 1: self.replay_index += 1; self.update_replay_ui()
            
    def slider_moved(self, val):
        self.replay_index = val; self.update_replay_ui()
        
    def update_replay_ui(self):
        pacote = self.replay_packets[self.replay_index]
        self.ui.slider_replay.blockSignals(True)
        self.ui.slider_replay.setValue(self.replay_index)
        self.ui.slider_replay.blockSignals(False)
        self.ui.lbl_replay_info.setText(f"Frame: {self.replay_index}/{len(self.replay_packets)-1} | Tempo: {pacote['tempo']}ms")
        self.ui.atualizar_ui(pacote, linha=self.replay_index + 1)
        self.ui.atualizar_footer_raw(f"REPLAY: A carregar dados da memória (Log Frame {self.replay_index})")

    def desconectar(self):
        self.timer.stop()
        if self.radio:
            self.radio.fechar()
            self.radio = None
        if self.logger:
            self.logger.fechar()
            self.logger = None
        
        self.simulando = False
        self.replaying = False
        self.replay_playing = False
        
        self.ui.btn_play_pause.setText("▶️ Play")
        self.ui.btn_prev.setEnabled(False)
        self.ui.btn_play_pause.setEnabled(False)
        self.ui.btn_next.setEnabled(False)
        self.ui.slider_replay.setEnabled(False)
        self.ui.lbl_replay_info.setText("Replay: Inativo")
        
        self.ui.set_status_conexao(False)
        self.ui.atualizar_footer_raw("aguardando pacote...")
        print("Desconectado.")

    def update_loop(self):
        try:
            if self.replaying and self.replay_playing:
                self.next_frame()
                if self.replay_index >= len(self.replay_packets) - 1:
                    self.toggle_play_pause() # Auto-pause quando chega ao fim do voo
                return

            pacote = None
            raw_str = ""

            if self.simulando:
                pacote, raw_str = self.simulator.get_next_packet(self.ui.erro_sim)
            elif self.radio:
                pacote = self.radio.receber_pacote()
                if pacote:
                    raw_str = f"TS,{pacote['tempo']},{pacote['pressao']:.2f},{pacote['temp']:.2f},{pacote['alt_baro']:.2f}," \
                              f"{pacote['gps'][0]:.6f},{pacote['gps'][1]:.6f},{pacote['gps'][2]:.2f}," \
                              f"{pacote['accel'][0]:.3f},{pacote['accel'][1]:.3f},{pacote['accel'][2]:.3f}," \
                              f"{pacote['dist'][0]},{pacote['dist'][1]},{pacote['dist'][2]}," \
                              f"{pacote['pos_xyz'][0]},{pacote['pos_xyz'][1]},{pacote['pos_xyz'][2]}," \
                              f"{pacote['pressao2']:.2f},{pacote['temp2']:.2f},{pacote['alt_baro2']:.2f},{pacote['bateria_pct']:.1f}"

            if pacote:
                if self.logger:
                    self.logger.log(pacote)
                self.ui.atualizar_ui(pacote)
                self.ui.atualizar_footer_raw(raw_str)
        except Exception as e:
            print(f"ERRO CRÍTICO no Loop: {e}")

    def run(self):
        self.ui.show()
        ret = self.app.exec()
        self.desconectar() # Garante que fecha o rádio ao sair
        sys.exit(ret)

if __name__ == "__main__":
    controller = TugaSpaceController()
    controller.run()