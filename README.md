# GroundStation TugaSpace

Esta é uma aplicação Python para estação terrestre (ground station) destinada a receber e processar telemetria de sistemas embarcados, como foguetes ou satélites do projeto TugaSpace.

## Funcionalidades

- Interface gráfica com PyQt6 para monitoramento em tempo real
- Comunicação serial com rádio APC220
- Logging de dados em CSV
- Modo de simulação para testes sem hardware
- Gráficos de altitude e aceleração
- Validação de checksum e descriptografia de pacotes

## Instalação

1. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```

2. Execute a aplicação:
   ```
   python -m src.main
   ```

## Uso

- Selecione a porta serial ou "TESTE SIMULADO" no menu.
- Clique em "CONECTAR" para iniciar.
- Monitore os dados em tempo real na interface.
- Dados são salvos automaticamente em `data/` ou `data_simulada/`.

## Estrutura do Projeto

- `src/`: Código fonte
  - `main.py`: Controlador principal
  - `dashboard.py`: Interface gráfica
  - `radio_receiver.py`: Comunicação serial
  - `data_logger.py`: Logging de dados
- `data/`: Dados reais logados
- `data_simulada/`: Dados simulados

## Desenvolvimento

Para testes, use `python -m src.main_test` ou `python -m src.test_radio`.