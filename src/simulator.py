import random
import math

class FlightSimulator:
    def __init__(self):
        self._sim_profile = self._create_sim_profile()
        self.reset()

    def reset(self):
        """Reinicia a simulação para o momento pré-lançamento."""
        self._sim_profile_index = 0
        if self._sim_profile:
            self._sim_tempo = self._sim_profile[0]["tempo"]
            self._sim_alt = self._sim_profile[0]["alt_baro"]
        else:
            self._sim_tempo = 0
            self._sim_alt = 100

    def _create_sim_profile(self):
        """Gera um voo físico de CanSat dinâmico a 5Hz."""
        profile = []
        dt = 0.2  # Delta de tempo = 0.2s (5Hz)
        tempo = 0.0
        alt = 0.0
        vel = 0.0
        lat, lon = 39.2008, -8.1371
        
        base_alt = 120.0  # Elevação base realista para Ponte de Sor
        
        for i in range(1000): # Simular até 200 segundos
            accel_z = 9.81
            if i < 10: # 2 segundos pré-voo
                alt = 0
                vel = 0
            elif i == 10: # Kick de Lançamento
                vel = 100.0 # Começa a 100m/s
                accel_z = 50.0 # Pico para acionar deteção
            elif vel > 0: # Fase de Subida
                vel -= 10.0 * dt
                accel_z = 0.0 # Queda livre inercial
            else: # Fase de Descida
                if vel > -10.0:
                    vel -= 9.8 * dt # Acelera para baixo
                else:
                    vel = -10.0 # Paraquedas estabiliza
                accel_z = 9.81
                
            alt += vel * dt
            if alt < 0 and i > 20: # Aterragem
                alt = 0
                vel = 0
                accel_z = 9.81
                
            alt_abs = base_alt + alt
            lat += 0.000002
            press = 1013.25 - (alt_abs / 8.0)
            
            # --- Cálculo Físico/Realístico de Distâncias (Haversine/Esférico) ---
            # Garante que as distâncias geradas batem certo ao milímetro com a projeção WGS84 do Mapa Leaflet
            def haversine_dist(lat1, lon1, lat2, lon2):
                R = 6371000.0 # Raio da Terra em metros
                phi1, phi2 = math.radians(lat1), math.radians(lat2)
                dphi = math.radians(lat2 - lat1)
                dlambda = math.radians(lon2 - lon1)
                a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
                return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            
            # Alturas relativas: simulando terreno irregular face ao ponto de lançamento
            dz_a = alt - 8.0    # Baliza A está 8m mais alta que a base
            dz_b = alt + 16.0   # Baliza B está 16m mais baixa que a base
            dz_c = alt - 16.0   # Baliza C está 16m mais alta que a base
            
            dist_a = math.sqrt(haversine_dist(lat, lon, 39.2008, -8.1350)**2 + dz_a**2)
            dist_b = math.sqrt(haversine_dist(lat, lon, 39.2025, -8.1371)**2 + dz_b**2)
            dist_c = math.sqrt(haversine_dist(lat, lon, 39.1990, -8.1390)**2 + dz_c**2)

            profile.append({
                "tempo": int(tempo * 1000), "pressao": press, "temp": 25.0 - (alt_abs / 100.0),
                "alt_baro": alt, "gps": (lat, lon, alt_abs),
                "accel": (random.uniform(-0.5, 0.5), random.uniform(-0.5, 0.5), accel_z + random.uniform(-0.5, 0.5)),
                # Usar int(round) previne que a dist_3d enviada encolha as áreas trigonométricas do Dashboard
                "dist": (int(round(dist_a)), int(round(dist_b)), int(round(dist_c))),
                "pos_xyz": (0, 0, int(alt)), "pressao2": press + random.uniform(-0.5, 0.5),
                "temp2": 25.0 - (alt_abs / 100.0) + random.uniform(-0.2, 0.2),
                "alt_baro2": alt + random.uniform(-0.5, 0.5), "bateria_pct": max(0.0, 100.0 - (tempo / 15.0))
            })
            
            tempo += dt
            if alt == 0 and i > 60:
                # Fica estático no chão uns instantes antes do loop voltar a recomeçar
                for _ in range(10):
                    profile.append(profile[-1].copy())
                break
                
        return profile

    def get_next_packet(self, erro_sim):
        """Recupera o próximo pacote da simulação, aplicando injeção de erros se necessário."""
        sample = self._sim_profile[self._sim_profile_index]
        self._sim_profile_index = (self._sim_profile_index + 1) % len(self._sim_profile)
        pacote = sample.copy()

        # Se o usuário habilitou simulação de erros individuais no Menu, força valores fora de faixa
        if erro_sim['bno']: pacote["accel"] = (60.0, 60.0, 60.0)
        if erro_sim['bmp']:
            pacote["temp"], pacote["pressao"], pacote["alt_baro"] = 200.0, 1500.0, -500.0
        if erro_sim['bmp2']:
            pacote["temp2"], pacote["pressao2"], pacote["alt_baro2"] = 200.0, 1500.0, -500.0
        if erro_sim['bateria']: pacote["bateria_pct"] = -10.0
        if erro_sim['gps']: pacote["gps"] = (50.0, 0.0, pacote["gps"][2])
        
        dist_list = list(pacote["dist"])
        if erro_sim['dist_a']: dist_list[0] = 0
        if erro_sim['dist_b']: dist_list[1] = 0
        if erro_sim['dist_c']: dist_list[2] = 0
        pacote["dist"] = tuple(dist_list)

        raw = f"TS,{pacote['tempo']},{pacote['pressao']:.2f},{pacote['temp']:.2f},{pacote['alt_baro']:.2f}," \
              f"{pacote['gps'][0]:.6f},{pacote['gps'][1]:.6f},{pacote['gps'][2]:.2f}," \
              f"{pacote['accel'][0]:.3f},{pacote['accel'][1]:.3f},{pacote['accel'][2]:.3f}," \
              f"{pacote['dist'][0]},{pacote['dist'][1]},{pacote['dist'][2]}," \
              f"{pacote['pos_xyz'][0]},{pacote['pos_xyz'][1]},{pacote['pos_xyz'][2]}," \
              f"{pacote['pressao2']:.2f},{pacote['temp2']:.2f},{pacote['alt_baro2']:.2f},{pacote['bateria_pct']:.1f}"
        return pacote, raw