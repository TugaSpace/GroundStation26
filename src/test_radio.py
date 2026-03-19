# Ajuste a porta COM de acordo com o seu computador
# radio = RadioReceiver(port='COM3') 

# print("Aguardando telemetria TugaSpace...")
# try:
#     while True:
#         dados = radio.receber_pacote()
#         if dados:
#             print(f"[{dados['tempo']}ms] Alt: {dados['alt_baro']:.2f}m | GPS: {dados['gps']}")
#             print(f"  BMP2: Alt2={dados['alt_baro2']:.2f}m Temp2={dados['temp2']:.1f}°C | Bateria: {dados['bateria_pct']:.1f}%")
# except KeyboardInterrupt:
#     radio.fechar()
#     print("\nConexão encerrada.")

print("Teste de importação bem-sucedido. Para testar rádio real, descomente o código acima.")