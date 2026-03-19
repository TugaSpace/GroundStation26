import sys
import os
import math
from PyQt6.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, 
                             QLabel, QPushButton, QComboBox, QCheckBox, QGroupBox, QFormLayout, QFrame, QGridLayout, QLineEdit, QMenu, QProgressBar, QSlider)
from PyQt6.QtGui import QAction

try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    WEB_ENGINE_AVAILABLE = True
except ImportError:
    WEB_ENGINE_AVAILABLE = False
from PyQt6.QtCore import Qt
import pyqtgraph as pg
from serial.tools import list_ports

class GroundStationUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TugaSpace - Ground Station v1.1")
        self.resize(1300, 800)
        self.pacotes_recebidos = 0

        # Estilo para valores
        estilo_val = "font-size: 14px; font-weight: bold; color: #4CAF50;"

        # Dicionário de simulação de erros (por hardware)
        self.erro_sim = {
            'bno': False,
            'bmp': False,
            'bmp2': False,
            'gps': False,
            'bateria': False,
            'dist_a': False,
            'dist_b': False,
            'dist_c': False
        }

        # Criar Menu de Testes
        self._criar_menu_testes()

        # Widget Principal
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.layout_geral = QVBoxLayout(self.main_widget)

        # Layout Central (Config + Dados + Gráficos)
        self.layout_central = QHBoxLayout()
        self.layout_geral.addLayout(self.layout_central)

        # ==========================================
        # 1. PAINEL LATERAL ESQUERDO (Config & Dados)
        # ==========================================
        self.panel_esquerdo = QHBoxLayout()
        self.layout_central.addLayout(self.panel_esquerdo)

        self.col_esquerda = QVBoxLayout()
        self.col_direita = QVBoxLayout()
        
        self.panel_esquerdo.addLayout(self.col_esquerda)
        self.panel_esquerdo.addLayout(self.col_direita)

        # Módulo Missão (Deteção de Eventos)
        self.panel_missao = QGroupBox("Status da Missão")
        self.panel_missao.setFixedWidth(260)
        self.missao_layout = QFormLayout()
        
        self.lbl_linha = QLabel("0")
        self.lbl_linha.setStyleSheet(estilo_val)
        self.missao_layout.addRow("Linha:", self.lbl_linha)

        self.lbl_tempo = QLabel("0 ms")
        self.lbl_tempo.setStyleSheet(estilo_val)
        self.missao_layout.addRow("Tempo:", self.lbl_tempo)

        self.lbl_fase_voo = QLabel("PRÉ-VOO")
        self.lbl_fase_voo.setStyleSheet("font-size: 14px; font-weight: bold; color: #FF9800;")
        self.missao_layout.addRow("Fase:", self.lbl_fase_voo)
        
        self.lbl_vel_vert = QLabel("0.0 m/s")
        self.lbl_vel_vert.setStyleSheet(estilo_val)
        self.missao_layout.addRow("Vel Vert:", self.lbl_vel_vert)
        
        self.lbl_max_alt = QLabel("0.0 m")
        self.lbl_max_alt.setStyleSheet(estilo_val)
        self.missao_layout.addRow("Apogeu:", self.lbl_max_alt)
        
        self.panel_missao.setLayout(self.missao_layout)
        self.col_esquerda.addWidget(self.panel_missao)

        # --- Sub-Painel A: Configuração ---
        self.panel_config = QGroupBox("Conectividade APC220")
        self.panel_config.setFixedWidth(260)
        self.panel_layout = QFormLayout()
        
        self.combo_portas = QComboBox()
        self.btn_refresh = QPushButton("Atualizar Portas")
        self.btn_refresh.clicked.connect(self.listar_portas)
        
        self.combo_baud = QComboBox()
        self.combo_baud.addItems(["2400", "4800", "9600", "19200"])
        self.combo_baud.setCurrentText("9600")
        
        self.btn_conectar = QPushButton("CONECTAR")
        self.btn_conectar.setMinimumHeight(40)
        
        self.panel_layout.addRow(self.btn_refresh)
        self.panel_layout.addRow("Porta:", self.combo_portas)
        self.panel_layout.addRow("Baud:", self.combo_baud)
        self.panel_layout.addRow(self.btn_conectar)

        self.panel_config.setLayout(self.panel_layout)
        self.col_esquerda.addWidget(self.panel_config)

        # Módulo BNO (Aceleração Linear)
        self.panel_bno = QGroupBox("BNO - Aceleração")
        self.panel_bno.setFixedWidth(160)
        self.bno_layout = QFormLayout()
        self.lbl_accel_x = QLabel("0.00")
        self.lbl_accel_x.setStyleSheet(estilo_val)
        self.bno_layout.addRow("Accel X:", self.lbl_accel_x)
        self.lbl_accel_y = QLabel("0.00")
        self.lbl_accel_y.setStyleSheet(estilo_val)
        self.bno_layout.addRow("Accel Y:", self.lbl_accel_y)
        self.lbl_accel_z = QLabel("0.00")
        self.lbl_accel_z.setStyleSheet(estilo_val)
        self.bno_layout.addRow("Accel Z:", self.lbl_accel_z)

        self.panel_bno.setLayout(self.bno_layout)
        self.col_direita.addWidget(self.panel_bno)

        # Módulo BMP (Pressão / Temp / Alt Barométrica)
        self.panel_bmp = QGroupBox("BMP388")
        self.panel_bmp.setFixedWidth(140)
        self.bmp_layout = QFormLayout()
        self.lbl_bmp_temp = QLabel("0.0 °C")
        self.lbl_bmp_temp.setStyleSheet(estilo_val)
        self.bmp_layout.addRow("Temp (BMP):", self.lbl_bmp_temp)
        self.lbl_bmp_press = QLabel("0.0 hPa")
        self.lbl_bmp_press.setStyleSheet(estilo_val)
        self.bmp_layout.addRow("Pressão (BMP):", self.lbl_bmp_press)
        self.lbl_alt_baro = QLabel("0.0 m")
        self.lbl_alt_baro.setStyleSheet(estilo_val)
        self.bmp_layout.addRow("Alt Barométrica:", self.lbl_alt_baro)
        self.panel_bmp.setLayout(self.bmp_layout)
        self.col_direita.addWidget(self.panel_bmp)

        # Módulo BMP2 (Segundo sensor BMP388)
        self.panel_bmp2 = QGroupBox("BMP388 #2")
        self.panel_bmp2.setFixedWidth(140)
        self.bmp2_layout = QFormLayout()
        self.lbl_bmp2_temp = QLabel("0.0 °C")
        self.lbl_bmp2_temp.setStyleSheet(estilo_val)
        self.bmp2_layout.addRow("Temp (BMP2):", self.lbl_bmp2_temp)
        self.lbl_bmp2_press = QLabel("0.0 hPa")
        self.lbl_bmp2_press.setStyleSheet(estilo_val)
        self.bmp2_layout.addRow("Pressão (BMP2):", self.lbl_bmp2_press)
        self.lbl_alt_baro2 = QLabel("0.0 m")
        self.lbl_alt_baro2.setStyleSheet(estilo_val)
        self.bmp2_layout.addRow("Alt Barométrica 2:", self.lbl_alt_baro2)
        self.panel_bmp2.setLayout(self.bmp2_layout)
        self.col_direita.addWidget(self.panel_bmp2)

        # Módulo Bateria (ao lado da Conectividade)
        self.panel_bateria = QGroupBox("Bateria")
        self.panel_bateria.setFixedWidth(140)
        self.bateria_layout = QVBoxLayout()

        # Gauge Horizontal Espesso
        self.bateria_gauge = QProgressBar()
        self.bateria_gauge.setRange(0, 100)
        self.bateria_gauge.setValue(0)
        self.bateria_gauge.setTextVisible(True)
        self.bateria_gauge.setFormat("%p %")
        self.bateria_gauge.setFixedHeight(30) # Torna a barra bem mais grossa
        self.bateria_gauge.setStyleSheet("QProgressBar { border: 1px solid #555; border-radius: 5px; text-align: center; font-weight: bold; }")
        self.bateria_layout.addWidget(self.bateria_gauge)

        self.panel_bateria.setLayout(self.bateria_layout)
        self.col_direita.addWidget(self.panel_bateria)

        # Módulo GPS/Altitude (ao lado da Conectividade)
        self.panel_gps_alt = QGroupBox("GPS")
        self.panel_gps_alt.setFixedWidth(170) # Aumentado um pouco para caber os decimais
        self.gps_alt_layout = QFormLayout()
        self.lbl_gps_lat = QLabel("0.000000")
        self.lbl_gps_lat.setStyleSheet(estilo_val)
        self.gps_alt_layout.addRow("Lat:", self.lbl_gps_lat)
        self.lbl_gps_lon = QLabel("0.000000")
        self.lbl_gps_lon.setStyleSheet(estilo_val)
        self.gps_alt_layout.addRow("Long:", self.lbl_gps_lon)
        self.lbl_gps_alt = QLabel("0.0 m")
        self.lbl_gps_alt.setStyleSheet(estilo_val)
        self.gps_alt_layout.addRow("Alt GF:", self.lbl_gps_alt)
        self.panel_gps_alt.setLayout(self.gps_alt_layout)
        self.col_direita.addWidget(self.panel_gps_alt)
        
        # Módulo Posição XY (Fusion e Calculado)
        self.panel_xy = QGroupBox("Posição Local XY (m)")
        self.panel_xy.setFixedWidth(170)
        self.xy_layout = QFormLayout()
        self.lbl_xy_telem = QLabel("0.0, 0.0")
        self.lbl_xy_telem.setStyleSheet(estilo_val)
        self.xy_layout.addRow("Telemetria:", self.lbl_xy_telem)
        self.lbl_xy_calc = QLabel("0.0, 0.0")
        self.lbl_xy_calc.setStyleSheet(estilo_val)
        self.xy_layout.addRow("Trilateração:", self.lbl_xy_calc)
        self.panel_xy.setLayout(self.xy_layout)
        self.col_direita.addWidget(self.panel_xy)

        self.col_direita.addStretch()
        
        # --- Sub-Painel C: Definições de Balizas ---
        self.panel_balizas = QGroupBox("Definições de Balizas")
        self.panel_balizas.setFixedWidth(260)
        self.balizas_layout = QFormLayout()
        
        # Pressão de Referência (Zero Altitude)
        self.edit_press_base = QLineEdit("998.25")
        self.btn_calibrar_base = QPushButton("Calibrar (0m)")
        self.btn_calibrar_base.setStyleSheet("background-color: #607D8B; color: white; border-radius: 3px; font-weight: bold;")
        self.btn_calibrar_base.clicked.connect(self._calibrar_pressao_base)
        
        box_base = QHBoxLayout()
        box_base.addWidget(self.edit_press_base)
        box_base.addWidget(self.btn_calibrar_base)
        self.balizas_layout.addRow("Pressão Zero (hPa):", box_base)
        
        # Baliza A
        self.edit_baliza_a_lat = QLineEdit("39.2008")
        self.edit_baliza_a_lon = QLineEdit("-8.1350")
        self.edit_baliza_a_press = QLineEdit("997.25")  # hPa (aprox 128m / +8m rel)
        self.lbl_baliza_a_alt = QLabel("0.0 m")
        self.lbl_baliza_a_alt.setStyleSheet("font-size: 12px; color: #AAAAAA;")
        
        self.box_alt_a = QHBoxLayout()
        self.box_alt_a.addWidget(self.lbl_baliza_a_alt)

        self.balizas_layout.addRow("Baliza A Lat:", self.edit_baliza_a_lat)
        self.balizas_layout.addRow("Baliza A Lon:", self.edit_baliza_a_lon)
        self.balizas_layout.addRow("Baliza A Pressão:", self.edit_baliza_a_press)
        self.balizas_layout.addRow("Baliza A Alt:", self.box_alt_a)
        
        # Baliza B
        self.edit_baliza_b_lat = QLineEdit("39.2025")
        self.edit_baliza_b_lon = QLineEdit("-8.1371")
        self.edit_baliza_b_press = QLineEdit("1000.25") # hPa (aprox 104m / -16m rel)
        self.lbl_baliza_b_alt = QLabel("0.0 m")
        self.lbl_baliza_b_alt.setStyleSheet("font-size: 12px; color: #AAAAAA;")
        
        self.box_alt_b = QHBoxLayout()
        self.box_alt_b.addWidget(self.lbl_baliza_b_alt)

        self.balizas_layout.addRow("Baliza B Lat:", self.edit_baliza_b_lat)
        self.balizas_layout.addRow("Baliza B Lon:", self.edit_baliza_b_lon)
        self.balizas_layout.addRow("Baliza B Pressão:", self.edit_baliza_b_press)
        self.balizas_layout.addRow("Baliza B Alt:", self.box_alt_b)
        
        # Baliza C
        self.edit_baliza_c_lat = QLineEdit("39.1990")
        self.edit_baliza_c_lon = QLineEdit("-8.1390")
        self.edit_baliza_c_press = QLineEdit("996.25")  # hPa (aprox 136m / +16m rel)
        self.lbl_baliza_c_alt = QLabel("0.0 m")
        self.lbl_baliza_c_alt.setStyleSheet("font-size: 12px; color: #AAAAAA;")
        
        self.box_alt_c = QHBoxLayout()
        self.box_alt_c.addWidget(self.lbl_baliza_c_alt)

        self.balizas_layout.addRow("Baliza C Lat:", self.edit_baliza_c_lat)
        self.balizas_layout.addRow("Baliza C Lon:", self.edit_baliza_c_lon)
        self.balizas_layout.addRow("Baliza C Pressão:", self.edit_baliza_c_press)
        self.balizas_layout.addRow("Baliza C Alt:", self.box_alt_c)

        # Distâncias para cada baliza (A/B/C)
        self.lbl_dist_a = QLabel("0 m")
        self.lbl_dist_a.setStyleSheet("font-size: 12px; color: #AAAAAA;")
        self.lbl_dist_b = QLabel("0 m")
        self.lbl_dist_b.setStyleSheet("font-size: 12px; color: #AAAAAA;")
        self.lbl_dist_c = QLabel("0 m")
        self.lbl_dist_c.setStyleSheet("font-size: 12px; color: #AAAAAA;")
        self.balizas_layout.addRow("Dist A:", self.lbl_dist_a)
        self.balizas_layout.addRow("Dist B:", self.lbl_dist_b)
        self.balizas_layout.addRow("Dist C:", self.lbl_dist_c)
        
        self.panel_balizas.setLayout(self.balizas_layout)
        
        self.col_esquerda.addWidget(self.panel_balizas)
        
        self.col_esquerda.addStretch() # Empurra tudo para cima

        # Atualizar altitudes calculadas
        self.atualizar_altitudes_balizas()
        
        # Conectar mudanças para atualizar altitudes em tempo real
        self.edit_press_base.textChanged.connect(self.atualizar_altitudes_balizas)
        self.edit_baliza_a_press.textChanged.connect(self.atualizar_altitudes_balizas)
        self.edit_baliza_b_press.textChanged.connect(self.atualizar_altitudes_balizas)
        self.edit_baliza_c_press.textChanged.connect(self.atualizar_altitudes_balizas)

        # ==========================================
        # 2. ÁREA DE GRÁFICOS (Central)
        # ==========================================
        self.layout_graficos_container = QHBoxLayout()
        self.layout_central.addLayout(self.layout_graficos_container)

        # --- Coluna Esquerda: 3 Gráficos Verticais ---
        self.layout_graficos_esquerda = QVBoxLayout()

        # Cores e pens usados para gráficos (para referencia visual de erro)
        self._plot_bg_ok = '#111111'
        self._plot_bg_err = '#330000'
        self._plot_pen_err = pg.mkPen('#f44336', width=2)
        self._plot_pen_err_accel = pg.mkPen('#f44336', width=1.5)

        self._plot_pen_temp = pg.mkPen('c', width=2)
        self._plot_pen_temp2 = pg.mkPen('m', width=2, style=Qt.PenStyle.DashLine)
        self._plot_pen_alt = pg.mkPen('y', width=2)
        self._plot_pen_alt2 = pg.mkPen('w', width=2, style=Qt.PenStyle.DashLine)
        self._plot_pen_accel_x = pg.mkPen('r', width=1.5)
        self._plot_pen_accel_y = pg.mkPen('g', width=1.5)
        self._plot_pen_accel_z = pg.mkPen('b', width=1.5)

        # Plot de Temperatura
        self.plot_temp = pg.PlotWidget(title="Temperatura (°C)")
        self.plot_temp.setBackground(self._plot_bg_ok)
        self.curve_temp = self.plot_temp.plot(pen=self._plot_pen_temp, name="BMP1")
        self.curve_temp2 = self.plot_temp.plot(pen=self._plot_pen_temp2, name="BMP2")
        self.plot_temp.addLegend()
        self.data_temp = []
        self.data_temp2 = []
        self.layout_graficos_esquerda.addWidget(self.plot_temp, 1)

        # Plot de Altitude
        self.plot_alt = pg.PlotWidget(title="Altitude Barométrica (m)")
        self.plot_alt.setBackground(self._plot_bg_ok)
        self.curve_alt = self.plot_alt.plot(pen=self._plot_pen_alt, name="Alt BMP1")
        self.curve_alt2 = self.plot_alt.plot(pen=self._plot_pen_alt2, name="Alt BMP2")
        self.plot_alt.addLegend()
        self.data_alt = []
        self.data_alt2 = []
        self.layout_graficos_esquerda.addWidget(self.plot_alt, 1)

        # Plot de Aceleração (mostra magnitude total)
        self.plot_accel = pg.PlotWidget(title="Aceleração Linear (m/s²)")
        self.plot_accel.setBackground(self._plot_bg_ok)
        # 3 curves para X, Y, Z
        self.curve_accel_x = self.plot_accel.plot(pen=self._plot_pen_accel_x, name="X")
        self.curve_accel_y = self.plot_accel.plot(pen=self._plot_pen_accel_y, name="Y")
        self.curve_accel_z = self.plot_accel.plot(pen=self._plot_pen_accel_z, name="Z")
        self.data_accel_x = []
        self.data_accel_y = []
        self.data_accel_z = []
        self.plot_accel.addLegend()
        self.layout_graficos_esquerda.addWidget(self.plot_accel, 1)

        self.layout_graficos_container.addLayout(self.layout_graficos_esquerda, 1)

        # --- Coluna Direita: Mapa ---
        self.container_plots = QVBoxLayout()
        self.layout_graficos_container.addLayout(self.container_plots, 1)


        # Mapa (metade direita)
        if WEB_ENGINE_AVAILABLE:
            # Barra superior de controlo do mapa
            self.map_top_layout = QHBoxLayout()
            self.chk_seguir_mapa = QCheckBox("Seguir Posição Automaticamente")
            self.chk_seguir_mapa.setChecked(True)
            self.chk_seguir_mapa.setStyleSheet("font-weight: bold; color: #4CAF50;")
            self.map_top_layout.addWidget(self.chk_seguir_mapa)
            self.map_top_layout.addStretch()
            self.container_plots.addLayout(self.map_top_layout)
            
            self.map_view = QWebEngineView()
            
            # Disfarçar o User-Agent como Google Chrome para evitar bloqueio 403 do OpenStreetMap
            profile = self.map_view.page().profile()
            profile.setHttpUserAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 TugaSpace/1.1")
            
            # --- Ativar Cache Persistente (Mapa Offline) ---
            cache_dir = os.path.abspath(os.path.join(os.getcwd(), "map_cache"))
            profile.setCachePath(cache_dir)
            profile.setPersistentStoragePath(cache_dir)

            # Reduzido para garantir que a janela não fica maior que a resolução do monitor
            self.map_view.setMinimumWidth(350)
            self.map_view.setMinimumHeight(300)
            self.map_view.setHtml(self._build_map_html())
            self.container_plots.addWidget(self.map_view, 1)
        else:
            self.map_placeholder = QLabel(
                """Mapa não disponível.
Instalar PyQt6-WebEngine:
  pip install PyQt6-WebEngine"""
            )
            self.map_placeholder.setStyleSheet("font-size: 12px; color: #888888; text-align: center;")
            self.map_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.container_plots.addWidget(self.map_placeholder, 1)

        # ==========================================
        # 2.5 REPLAY CONTROLS (Acima do rodapé)
        # ==========================================
        self.replay_frame = QFrame()
        self.replay_layout = QHBoxLayout(self.replay_frame)
        self.replay_layout.setContentsMargins(10, 5, 10, 5)
        
        self.btn_load_log = QPushButton("📂 Abrir Log CSV")
        self.btn_load_log.setStyleSheet("font-weight: bold; background-color: #607D8B; color: white;")
        self.btn_prev = QPushButton("⏪ -1 Frame")
        self.btn_play_pause = QPushButton("▶️ Play")
        self.btn_next = QPushButton("⏩ +1 Frame")
        self.slider_replay = QSlider(Qt.Orientation.Horizontal)
        self.lbl_replay_info = QLabel("Replay: Inativo")
        self.lbl_replay_info.setStyleSheet("font-weight: bold; color: #AAAAAA;")
        
        for btn in [self.btn_prev, self.btn_play_pause, self.btn_next, self.slider_replay]:
            btn.setEnabled(False)
            self.replay_layout.addWidget(btn)
        
        self.replay_layout.insertWidget(0, self.btn_load_log)
        self.replay_layout.addWidget(self.lbl_replay_info)
        self.layout_geral.addWidget(self.replay_frame)

        # ==========================================
        # 3. LINHA DE TELEMETRIA (Rodapé)
        # ==========================================
        self.footer = QFrame()
        self.footer.setFrameShape(QFrame.Shape.HLine)
        self.footer.setFrameShadow(QFrame.Shadow.Sunken)
        self.layout_geral.addWidget(self.footer)

        self.footer_layout = QHBoxLayout()
        self.lbl_status = QLabel("Sinal: DESCONECTADO")
        self.lbl_status.setStyleSheet("font-weight: bold; color: #f44336;")
        
        self.lbl_raw_telemetry = QLabel("Raw: aguardando pacote...")
        self.lbl_raw_telemetry.setStyleSheet("font-family: Consolas, monospace; color: #FFFFFF; font-size: 14px; font-weight: bold;")
        self.lbl_raw_telemetry.setFixedWidth(1200)
        self.lbl_raw_telemetry.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        self.footer_layout.addWidget(self.lbl_status)
        self.footer_layout.addStretch()
        self.footer_layout.addWidget(self.lbl_raw_telemetry)
        
        self.layout_geral.addLayout(self.footer_layout)
        
        self.listar_portas()
        
        self.on_key_right = None
        self.on_key_left = None

    def add_data_field(self, title, default_val, row, layout, style_lbl, style_val, obj_name):
        lbl = QLabel(title)
        lbl.setStyleSheet(style_lbl)
        val = QLabel(default_val)
        val.setStyleSheet(style_val)
        setattr(self, obj_name, val) # Cria self.lbl_tempo, etc.
        layout.addWidget(lbl, row, 0)
        layout.addWidget(val, row, 1, Qt.AlignmentFlag.AlignRight)

    def _criar_menu_testes(self):
        """Cria o menu de testes de simulação de erros por hardware."""
        menu_bar = self.menuBar()
        menu_testes = menu_bar.addMenu("Testes (Simulação)")

        # BNO
        action_bno = QAction("Simular erro BNO", self, checkable=True)
        action_bno.triggered.connect(lambda checked: self._toggle_erro('bno', checked))
        menu_testes.addAction(action_bno)

        # BMP
        action_bmp = QAction("Simular erro BMP388", self, checkable=True)
        action_bmp.triggered.connect(lambda checked: self._toggle_erro('bmp', checked))
        menu_testes.addAction(action_bmp)

        # BMP2
        action_bmp2 = QAction("Simular erro BMP388 #2", self, checkable=True)
        action_bmp2.triggered.connect(lambda checked: self._toggle_erro('bmp2', checked))
        menu_testes.addAction(action_bmp2)

        # Bateria
        action_bateria = QAction("Simular erro Bateria", self, checkable=True)
        action_bateria.triggered.connect(lambda checked: self._toggle_erro('bateria', checked))
        menu_testes.addAction(action_bateria)

        # GPS
        action_gps = QAction("Simular erro GPS", self, checkable=True)
        action_gps.triggered.connect(lambda checked: self._toggle_erro('gps', checked))
        menu_testes.addAction(action_gps)

        # Separador
        menu_testes.addSeparator()

        # Distâncias individuais (Balizas A, B, C)
        action_dist_a = QAction("Simular erro Distância A", self, checkable=True)
        action_dist_a.triggered.connect(lambda checked: self._toggle_erro('dist_a', checked))
        menu_testes.addAction(action_dist_a)

        action_dist_b = QAction("Simular erro Distância B", self, checkable=True)
        action_dist_b.triggered.connect(lambda checked: self._toggle_erro('dist_b', checked))
        menu_testes.addAction(action_dist_b)

        action_dist_c = QAction("Simular erro Distância C", self, checkable=True)
        action_dist_c.triggered.connect(lambda checked: self._toggle_erro('dist_c', checked))
        menu_testes.addAction(action_dist_c)

    def _toggle_erro(self, sensor, estado):
        """Alterna o estado da simulação de erro para um sensor específico."""
        self.erro_sim[sensor] = estado

    def listar_portas(self):
        self.combo_portas.clear()
        # Adiciona opção de TESTE SIMULADO
        self.combo_portas.addItem("TESTE SIMULADO")
        portas = [p.device for p in list_ports.comports()]
        self.combo_portas.addItems(portas)
        # Seleciona a simulação por padrão para facilitar o teste
        self.combo_portas.setCurrentText("TESTE SIMULADO")

    def _calibrar_pressao_base(self):
        """Define a pressão atual do CanSat como a pressão do nível 0m (chão)."""
        if hasattr(self, '_last_pressao'):
            self.edit_press_base.setText(f"{self._last_pressao:.2f}")

    def atualizar_altitudes_balizas(self):
        # Calcula altitude RELATIVA das balizas a partir da pressão base do CanSat (0m)
        try:
            press_base = float(self.edit_press_base.text())
        except ValueError:
            press_base = 1013.25

        try:
            press_a = float(self.edit_baliza_a_press.text())
            self._alt_baliza_a = (press_base - press_a) * 8.0
            self.lbl_baliza_a_alt.setText(f"{self._alt_baliza_a:.1f} m (Rel)")
        except ValueError:
            self._alt_baliza_a = 0.0
            self.lbl_baliza_a_alt.setText("Erro")
        
        try:
            press_b = float(self.edit_baliza_b_press.text())
            self._alt_baliza_b = (press_base - press_b) * 8.0
            self.lbl_baliza_b_alt.setText(f"{self._alt_baliza_b:.1f} m (Rel)")
        except ValueError:
            self._alt_baliza_b = 0.0
            self.lbl_baliza_b_alt.setText("Erro")
        
        try:
            press_c = float(self.edit_baliza_c_press.text())
            self._alt_baliza_c = (press_base - press_c) * 8.0
            self.lbl_baliza_c_alt.setText(f"{self._alt_baliza_c:.1f} m (Rel)")
        except ValueError:
            self._alt_baliza_c = 0.0
            self.lbl_baliza_c_alt.setText("Erro")
            
    def set_status_conexao(self, conectado, porta=""):
        self._press_calibrada_auto = False  # Prepara para auto-calibrar no 1º pacote da nova ligação
        if conectado:
            self.lbl_status.setText(f"Sinal: CONECTADO ({porta})")
            self.lbl_status.setStyleSheet("font-weight: bold; color: #4CAF50;")
            self.btn_conectar.setText("DESCONECTAR")
            self.btn_conectar.setStyleSheet("background-color: #f44336; color: white;")
        else:
            self.lbl_status.setText("Sinal: DESCONECTADO")
            self.lbl_status.setStyleSheet("font-weight: bold; color: #f44336;")
            self.btn_conectar.setText("CONECTAR")
            self.btn_conectar.setStyleSheet("background-color: #4CAF50; color: white;")

    def atualizar_ui(self, d, linha=None):
        self._last_pressao = d['pressao']
        
        if linha is not None:
            self.pacotes_recebidos = linha
        else:
            self.pacotes_recebidos += 1
        self.lbl_linha.setText(str(self.pacotes_recebidos))

        # Auto-calibração silenciosa logo no primeiro pacote de telemetria recebido
        if not getattr(self, '_press_calibrada_auto', False):
            self._calibrar_pressao_base()
            self._press_calibrada_auto = True
        
        # 1. Atualizar Painel Numérico (Esquerdo)
        self.lbl_tempo.setText(f"{d['tempo']} ms")
        self.lbl_gps_lat.setText(f"{d['gps'][0]:.6f}")
        self.lbl_gps_lon.setText(f"{d['gps'][1]:.6f}")
        self.lbl_gps_alt.setText(f"{d['gps'][2]:.1f} m")
        # Nota: BNO Status precisa ser adicionado à struct do Teensy se quiseres ver
        # self.lbl_bno_status.setText(f"{d['bno_status']}") 

        # 2. Atualizar Gráficos (Central)
        # Temperatura
        self.data_temp.append(d['temp'])
        self.data_temp2.append(d['temp2'])
        self.curve_temp.setData(self.data_temp[-200:])  # Mostra últimos 200 pontos
        self.curve_temp2.setData(self.data_temp2[-200:])

        # Altitude
        self.data_alt.append(d['alt_baro'])
        self.data_alt2.append(d['alt_baro2'])
        self.curve_alt.setData(self.data_alt[-200:])  # Mostra últimos 200 pontos
        self.curve_alt2.setData(self.data_alt2[-200:])  # Mostra últimos 200 pontos

        # Aceleração (X, Y, Z)
        self.data_accel_x.append(d['accel'][0])
        self.data_accel_y.append(d['accel'][1])
        self.data_accel_z.append(d['accel'][2])
        self.curve_accel_x.setData(self.data_accel_x[-200:])
        self.curve_accel_y.setData(self.data_accel_y[-200:])
        self.curve_accel_z.setData(self.data_accel_z[-200:])

        # Atualiza valores em cada módulo
        self.lbl_accel_x.setText(f"{d['accel'][0]:.2f}")
        self.lbl_accel_y.setText(f"{d['accel'][1]:.2f}")
        self.lbl_accel_z.setText(f"{d['accel'][2]:.2f}")

        self.lbl_bmp_temp.setText(f"{d['temp']:.1f} °C")
        self.lbl_bmp_press.setText(f"{d['pressao']:.1f} hPa")
        self.lbl_alt_baro.setText(f"{d['alt_baro']:.1f} m")

        # Novos campos BMP2 e bateria
        self.lbl_bmp2_temp.setText(f"{d['temp2']:.1f} °C")
        self.lbl_bmp2_press.setText(f"{d['pressao2']:.1f} hPa")
        self.lbl_alt_baro2.setText(f"{d['alt_baro2']:.1f} m")

        # Indicador de carga (gauge)
        bateria_val = d.get('bateria_pct', 0)
        bateria_clamped = max(0, min(100, int(bateria_val)))
        self.bateria_gauge.setValue(bateria_clamped)
        
        # Estilo dinâmico mantendo as bordas arredondadas e espessura
        base_style = "QProgressBar { border: 1px solid #555; border-radius: 5px; text-align: center; font-weight: bold; font-size: 13px; "
        if bateria_val < 20:
            self.bateria_gauge.setStyleSheet(base_style + "color: #ffffff; background: #330000; } QProgressBar::chunk { background: #f44336; border-radius: 4px; }")
        elif bateria_val < 50:
            self.bateria_gauge.setStyleSheet(base_style + "color: #ffffff; background: #333300; } QProgressBar::chunk { background: #ff9800; border-radius: 4px; }")
        else:
            self.bateria_gauge.setStyleSheet(base_style + "color: #ffffff; background: #003300; } QProgressBar::chunk { background: #4CAF50; border-radius: 4px; }")

        self.lbl_gps_lat.setText(f"{d['gps'][0]:.6f}")
        self.lbl_gps_lon.setText(f"{d['gps'][1]:.6f}")
        self.lbl_gps_alt.setText(f"{d['gps'][2]:.1f} m")

        # --- Lógica de Tendência de Voo (Subida / Descida) ---
        if not hasattr(self, '_alt_history'):
            self._alt_history = []
            self.fase_voo = "PRÉ-VOO"
            self.max_alt = 0.0
            self.max_accel = 0.0
            self._vel_history = []
            
        self._alt_history.append(d['alt_baro'])
        if len(self._alt_history) > 6:  # A 5Hz, 6 pacotes formam 5 intervalos = Exatamente 1.0 segundo!
            self._alt_history.pop(0)
            
        vel_vertical = 0.0
        alt_atual = d['alt_baro']
        accel_z_abs = abs(d['accel'][2])

        if len(self._alt_history) >= 6:
            vel_vertical = self._alt_history[-1] - self._alt_history[0]  # Direto em m/s porque a janela é de 1 segundo

            self._vel_history.append(vel_vertical)
            if len(self._vel_history) > 6:
                self._vel_history.pop(0)

        # --- Máquina de Estados (Deteção de Eventos) ---
        if alt_atual > self.max_alt:
            self.max_alt = alt_atual
            self.lbl_max_alt.setText(f"{self.max_alt:.1f} m")

        if accel_z_abs > self.max_accel:
            self.max_accel = accel_z_abs

        self.lbl_vel_vert.setText(f"{vel_vertical:.1f} m/s")

        if self.fase_voo == "PRÉ-VOO":
            if accel_z_abs > 25.0 or vel_vertical > 10.0:
                self.fase_voo = "🚀 LANÇAMENTO"
                self.lbl_fase_voo.setStyleSheet("font-size: 14px; font-weight: bold; color: #f44336;")
        
        elif self.fase_voo == "🚀 LANÇAMENTO":
            if vel_vertical > 2.0 and accel_z_abs < 15.0:
                self.fase_voo = "📈 EM SUBIDA"
                self.lbl_fase_voo.setStyleSheet("font-size: 14px; font-weight: bold; color: #4CAF50;")
        
        elif self.fase_voo == "📈 EM SUBIDA":
            if vel_vertical < 0 and alt_atual < (self.max_alt - 2.0):
                self.fase_voo = "✨ APOGEU"
                self.lbl_fase_voo.setStyleSheet("font-size: 14px; font-weight: bold; color: #FFD700;")
        
        elif self.fase_voo == "✨ APOGEU":
            if vel_vertical < -2.0:
                self.fase_voo = "🪂 DESCIDA"
                self.lbl_fase_voo.setStyleSheet("font-size: 14px; font-weight: bold; color: #2196F3;")
        
        elif self.fase_voo == "🪂 DESCIDA":
            if len(self._vel_history) == 6:
                vel_media = sum(self._vel_history) / 6
                variancia = sum((v - vel_media)**2 for v in self._vel_history) / 6
                if -15 < vel_media < -5 and variancia < 2.0: # Adaptado à velocidade terminal (-10 m/s)
                    self.fase_voo = "⚖️ VEL TERMINAL"
                    self.lbl_fase_voo.setStyleSheet("font-size: 13px; font-weight: bold; color: #00BCD4;")
                    
            if abs(vel_vertical) < 0.5 and alt_atual < (self.max_alt - 15.0):
                self.fase_voo = "🏁 ATERROU"
                self.lbl_fase_voo.setStyleSheet("font-size: 14px; font-weight: bold; color: #4CAF50;")
                
        elif self.fase_voo == "⚖️ VEL TERMINAL":
            if abs(vel_vertical) < 0.5 and alt_atual < (self.max_alt - 15.0):
                self.fase_voo = "🏁 ATERROU"
                self.lbl_fase_voo.setStyleSheet("font-size: 14px; font-weight: bold; color: #4CAF50;")

        self.lbl_fase_voo.setText(self.fase_voo)

        # --- Cálculo das Distâncias projetadas no plano XY ---
        # CRÍTICO: Não podemos confiar cegamente no d['alt_baro'] porque o firmware real pode
        # estar a enviar uma cota absoluta (ex: 120m). Para que a diferença de altura (Z) das balizas bata 
        # matematicamente certo, o CanSat tem de ser forçado à mesma base calibrada na UI.
        try:
            press_base = float(self.edit_press_base.text())
        except ValueError:
            press_base = 1013.25
            
        alt_cansat = (press_base - d['pressao']) * 8.0

        alt_a = getattr(self, '_alt_baliza_a', 0.0)
        alt_b = getattr(self, '_alt_baliza_b', 0.0)
        alt_c = getattr(self, '_alt_baliza_c', 0.0)

        def calc_2d(dist_3d, alt_c, alt_b):
            if dist_3d <= 0: return -1.0 # Negativo indica erro ou desconexão (apaga o anel)
            dz = abs(alt_c - alt_b)
            
            # Mitiga o erro de arredondamento de rádio (int). Se a distância foi arredondada para baixo,
            # impede que um cateto se torne (ilogicamente) superior à hipotenusa e colapse o anel 2D a zero.
            if dz > dist_3d:
                dz = dist_3d
                
            val = dist_3d**2 - dz**2
            if val > 0:
                return math.sqrt(val)
            else:
                # Se a altura Z for maior que a distância lida devido a erro do sensor, 
                # o CanSat está virtualmente no mesmo eixo XY da baliza. O raio 2D é 0.
                return 0.0

        dist_a_2d = calc_2d(d['dist'][0], alt_cansat, alt_a)
        dist_b_2d = calc_2d(d['dist'][1], alt_cansat, alt_b)
        dist_c_2d = calc_2d(d['dist'][2], alt_cansat, alt_c)

        self.lbl_dist_a.setText(f"{d['dist'][0]} m  (XY: {dist_a_2d:.1f} m)")
        self.lbl_dist_b.setText(f"{d['dist'][1]} m  (XY: {dist_b_2d:.1f} m)")
        self.lbl_dist_c.setText(f"{d['dist'][2]} m  (XY: {dist_c_2d:.1f} m)")

        # Colorir etiquetas de distância se forem 0 (vermelho) ou ok (cinza)
        for lbl, dist_val in [(self.lbl_dist_a, d['dist'][0]), 
                               (self.lbl_dist_b, d['dist'][1]), 
                               (self.lbl_dist_c, d['dist'][2])]:
            if dist_val == 0:
                lbl.setStyleSheet("font-size: 12px; color: #f44336; font-weight: bold;")
            else:
                lbl.setStyleSheet("font-size: 12px; color: #AAAAAA;")
                
        # XY Telemetria (vindo do BNO/Cansat via Fusion)
        telem_x, telem_y = d.get('pos_xyz', (0, 0, 0))[0:2]
        self.lbl_xy_telem.setText(f"{telem_x:.1f}, {telem_y:.1f}")

        # XY Calculado por Trilateração Linear na UI
        try:
            lat_a = float(self.edit_baliza_a_lat.text())
            lon_a = float(self.edit_baliza_a_lon.text())
            lat_b = float(self.edit_baliza_b_lat.text())
            lon_b = float(self.edit_baliza_b_lon.text())
            lat_c = float(self.edit_baliza_c_lat.text())
            lon_c = float(self.edit_baliza_c_lon.text())
            
            # Conversão para o plano local usando Baliza A como origem (0,0)
            x_b = (lon_b - lon_a) * 86260
            y_b = (lat_b - lat_a) * 111320
            x_c = (lon_c - lon_a) * 86260
            y_c = (lat_c - lat_a) * 111320
            
            if dist_a_2d >= 0 and dist_b_2d >= 0 and dist_c_2d >= 0:
                B1 = (dist_a_2d**2 - dist_b_2d**2 + x_b**2 + y_b**2) / 2.0
                B2 = (dist_a_2d**2 - dist_c_2d**2 + x_c**2 + y_c**2) / 2.0
                det = x_b * y_c - x_c * y_b
                
                if abs(det) > 0.1: # Evita divisão por zero se balizas colineares
                    calc_x = (B1 * y_c - B2 * y_b) / det
                    calc_y = (x_b * B2 - x_c * B1) / det
                    self.lbl_xy_calc.setText(f"{calc_x:.1f}, {calc_y:.1f}")
                    
                    if WEB_ENGINE_AVAILABLE and hasattr(self, 'map_view'):
                        calc_lat = lat_a + (calc_y / 111320.0)
                        calc_lon = lon_a + (calc_x / 86260.0)
                        self.map_view.page().runJavaScript(
                            f"updateMarker('calc_pos', {calc_lat}, {calc_lon}, 'Interseção Trilaterada 🎯', 'calc');"
                        )
                else:
                    self.lbl_xy_calc.setText("Erro (Colinear)")
            else:
                self.lbl_xy_calc.setText("Sem sinal")
        except ValueError:
            self.lbl_xy_calc.setText("Erro Coords")

        # 2b. Checar Hardware por módulo
        status = self._check_hardware(d)
        self._set_panel_status(self.panel_bno, status['bno'])
        self._set_panel_status(self.panel_bmp, status['bmp'])
        self._set_panel_status(self.panel_bmp2, status['bmp2'])
        self._set_panel_status(self.panel_bateria, status['bateria'])
        self._set_panel_status(self.panel_gps_alt, status['gps'])
        self._set_panel_status(self.panel_balizas, status['dist'])

        # --- Referências visuais nos gráficos quando há erro de hardware ---
        bno_error = bool(status['bno'])
        bmp_error = bool(status['bmp'])

        # Aceleração (BNO)
        self.plot_accel.setBackground(self._plot_bg_err if bno_error else self._plot_bg_ok)
        self.curve_accel_x.setPen(self._plot_pen_err_accel if bno_error else self._plot_pen_accel_x)
        self.curve_accel_y.setPen(self._plot_pen_err_accel if bno_error else self._plot_pen_accel_y)
        self.curve_accel_z.setPen(self._plot_pen_err_accel if bno_error else self._plot_pen_accel_z)

        # Temperatura / Altitude (BMP)
        self.plot_temp.setBackground(self._plot_bg_err if bmp_error else self._plot_bg_ok)
        self.curve_temp.setPen(self._plot_pen_err if bmp_error else self._plot_pen_temp)
        self.plot_alt.setBackground(self._plot_bg_err if bmp_error else self._plot_bg_ok)
        self.curve_alt.setPen(self._plot_pen_err if bmp_error else self._plot_pen_alt)

        # 3. Atualizar Mapa
        if WEB_ENGINE_AVAILABLE and hasattr(self, 'map_view'):
            lat, lon, alt_gps = d['gps']
            
            # Atualiza marcador atual e desenha ponto na trajetória
            self.map_view.page().runJavaScript(
                f"updateMarker('current', {lat}, {lon}, '<b>Foguetão</b><br>Lat: {lat:.6f}<br>Lon: {lon:.6f}<br>Alt: {alt_gps:.1f}m', 'rocket');"
                f"addTrajectoryPoint({lat}, {lon});"
            )

            # Faz o mapa centrar automaticamente se a opção estiver ativa
            if hasattr(self, 'chk_seguir_mapa') and self.chk_seguir_mapa.isChecked():
                self.map_view.page().runJavaScript(f"centerMap({lat}, {lon});")

            # Beacons
            try:
                lat_a = float(self.edit_baliza_a_lat.text())
                lon_a = float(self.edit_baliza_a_lon.text())
                self.map_view.page().runJavaScript(
                    f"updateMarker('baliza_a', {lat_a}, {lon_a}, 'Baliza A (📡)', 'beacon');"
                    f"updateCircle('circ_a', {lat_a}, {lon_a}, {dist_a_2d}, '#FF5722');"
                )
            except ValueError:
                pass

            try:
                lat_b = float(self.edit_baliza_b_lat.text())
                lon_b = float(self.edit_baliza_b_lon.text())
                self.map_view.page().runJavaScript(
                    f"updateMarker('baliza_b', {lat_b}, {lon_b}, 'Baliza B (📡)', 'beacon');"
                    f"updateCircle('circ_b', {lat_b}, {lon_b}, {dist_b_2d}, '#4CAF50');"
                )
            except ValueError:
                pass

            try:
                lat_c = float(self.edit_baliza_c_lat.text())
                lon_c = float(self.edit_baliza_c_lon.text())
                self.map_view.page().runJavaScript(
                    f"updateMarker('baliza_c', {lat_c}, {lon_c}, 'Baliza C (📡)', 'beacon');"
                    f"updateCircle('circ_c', {lat_c}, {lon_c}, {dist_c_2d}, '#2196F3');"
                )
            except ValueError:
                pass

    def atualizar_footer_raw(self, raw_string):
        """Atualiza a linha de telemetria bruta no rodapé"""
        # Limita o tamanho para não quebrar o layout
        if len(raw_string) > 120:
            raw_string = raw_string[:117] + "..."
        self.lbl_raw_telemetry.setText(f"Raw: {raw_string}")

    def _set_panel_status(self, panel: QGroupBox, issues: list):
        """Dá destaque (vermelho) ao painel se houver issues."""
        if issues:
            panel.setStyleSheet("QGroupBox { border: 2px solid #f44336; }")
        else:
            panel.setStyleSheet("")

    def _check_hardware(self, d):
        """Retorna dict com listas de issues por módulo."""
        status = {
            "bno": [],
            "bmp": [],
            "bmp2": [],
            "bateria": [],
            "gps": [],
            "dist": []
        }

        # BNO (aceleração)
        for i, ax in enumerate(d.get('accel', (0, 0, 0))):
            if abs(ax) > 30:
                status['bno'].append(f"Aceleração e{i} alta: {ax:.1f} m/s²")

        # BMP (temp, pressão, alt)
        temp = d.get('temp', 0)
        if not (-40 <= temp <= 85):
            status['bmp'].append(f"Temp BMP fora: {temp:.1f} °C")
        press = d.get('pressao', 0)
        if not (300 <= press <= 1200):
            status['bmp'].append(f"Pressão fora: {press:.1f} hPa")
        alt_baro = d.get('alt_baro', 0)
        if not (-200 <= alt_baro <= 20000):
            status['bmp'].append(f"Alt Baro fora: {alt_baro:.1f} m")

        # BMP2 (segundo sensor)
        temp2 = d.get('temp2', 0)
        if not (-40 <= temp2 <= 85):
            status['bmp2'].append(f"Temp BMP2 fora: {temp2:.1f} °C")
        press2 = d.get('pressao2', 0)
        if not (300 <= press2 <= 1200):
            status['bmp2'].append(f"Pressão BMP2 fora: {press2:.1f} hPa")
        alt_baro2 = d.get('alt_baro2', 0)
        if not (-200 <= alt_baro2 <= 20000):
            status['bmp2'].append(f"Alt Baro2 fora: {alt_baro2:.1f} m")

        # Bateria
        bateria_pct = d.get('bateria_pct', 0)
        if not (0 <= bateria_pct <= 100):
            status['bateria'].append(f"Bateria fora: {bateria_pct:.1f} %")

        # GPS (faixa aproximada para Portugal)
        gps = d.get('gps', (None, None, None))
        if gps[0] is not None and gps[1] is not None:
            if not (36 <= gps[0] <= 42 and -10 <= gps[1] <= -6):
                status['gps'].append(f"GPS fora da área: {gps[0]:.6f}, {gps[1]:.6f}")

        # Distâncias devem ser positivas
        for i, dist in enumerate(d.get('dist', (0, 0, 0))):
            if dist <= 0:
                status['dist'].append(f"Distância {chr(65+i)} inválida: {dist}")

        # Tempo crescente
        tempo = d.get('tempo')
        if tempo is not None:
            if hasattr(self, '_last_tempo') and tempo <= self._last_tempo:
                status['bmp'].append(f"Tempo não crescente: {tempo}")
            self._last_tempo = tempo

        return status
        
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Right and self.on_key_right:
            self.on_key_right()
        elif event.key() == Qt.Key.Key_Left and self.on_key_left:
            self.on_key_left()
        else:
            super().keyPressEvent(event)

    def _build_map_html(self):
        """Retorna o HTML utilizado para renderizar o mapa embedded."""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Mapa</title>
            <meta charset="utf-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
            <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
            <style>
                html, body { height: 100%; margin: 0; padding: 0; }
                #map { height: 100%; width: 100%; }
                .emoji-icon { font-size: 26px; line-height: 26px; text-align: center; background: transparent; border: none; }
            </style>
        </head>
        <body>
            <div id="map"></div>
            <script>
                // Centro no Aeródromo de Ponte de Sor (zoom ajustado para 18 para detalhe máximo)
                var map = L.map('map').setView([39.2008, -8.1371], 18);
                
                // Mapa de Satélite (Esri World Imagery)
                L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
                    attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
                }).addTo(map);
                
                // Ícones personalizados com Emojis
                var rocketIcon = L.divIcon({html: '🚀', className: 'emoji-icon', iconSize: [26, 26], iconAnchor: [13, 13]});
                var beaconIcon = L.divIcon({html: '📡', className: 'emoji-icon', iconSize: [26, 26], iconAnchor: [13, 13]});
                var calcIcon = L.divIcon({html: '🎯', className: 'emoji-icon', iconSize: [26, 26], iconAnchor: [13, 13]});

                var markers = {};
                var circles = {};
                var flightPath = L.polyline([], {color: '#f44336', weight: 4}).addTo(map); // Linha vermelha

                function updateMarker(id, lat, lon, label, type) {
                    var icon = (type === 'rocket') ? rocketIcon : ((type === 'calc') ? calcIcon : beaconIcon);
                    if (markers[id]) {
                        // Atualiza a posição de forma fluida (não apaga e desenha de novo)
                        markers[id].setLatLng([lat, lon]);
                        markers[id].setPopupContent(label);
                    } else {
                        markers[id] = L.marker([lat, lon], {icon: icon}).addTo(map).bindPopup(label);
                    }
                }

                function updateCircle(id, lat, lon, radius, color) {
                    if (radius < 0) {
                        if (circles[id]) { map.removeLayer(circles[id]); delete circles[id]; }
                        return;
                    }
                    var r = radius > 0 ? radius : 0.5; // Raio mínimo exigido pelo leaflet para existir
                    if (circles[id]) {
                        circles[id].setLatLng([lat, lon]);
                        circles[id].setRadius(r);
                    } else {
                        circles[id] = L.circle([lat, lon], {
                            color: color, fillColor: color, fillOpacity: 0.15, radius: r, weight: 2
                        }).addTo(map);
                    }
                }

                function addTrajectoryPoint(lat, lon) {
                    flightPath.addLatLng([lat, lon]);
                }

                function centerMap(lat, lon) {
                    map.panTo([lat, lon], {animate: true, duration: 0.25});
                }
            </script>
        </body>
        </html>
        """