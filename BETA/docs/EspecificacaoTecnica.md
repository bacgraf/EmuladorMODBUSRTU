# 📋 ESPECIFICAÇÃO TÉCNICA PARA DESENVOLVIMENTO DE EMULADOR MODBUS SLAVE

Olá [Nome do Programador],

Precisamos desenvolver um emulador Modbus Slave que implemente o mapa de memória completo de um sistema de gerenciamento de baterias (BMS). Este documento fornece todas as especificações necessárias.

## 🎯 OBJETIVO

Criar um dispositivo virtual Modbus RTU/TCP que responda como um slave, permitindo:

- Leitura de todos os registradores conforme mapa
- Escrita nos registradores R/W
- Simulação realista de valores de bateria
- Controle manual dos valores via interface ou API

## 📊 ESPECIFICAÇÕES TÉCNICAS

### 1. Protocolo Modbus

**Endereçamento:** Modbus 1-based (padrão)

**Funções suportadas:**
- 01 Read Coils (0xxxx)
- 02 Read Discrete Inputs (1xxxx)
- 03 Read Holding Registers (4xxxx)
- 04 Read Input Registers (3xxxx)
- 05 Write Single Coil
- 06 Write Single Register
- 16 Write Multiple Registers

### 2. Áreas de Memória a Implementar

```python
# Estrutura sugerida para implementação
MEMORY_MAP = {
    # Coils (0xxxx) - 1-based
    "coils": {
        1: "Comando - Medir Resistência do Banco",
        2: "Relé 1 - Acionamento",
        3: "Relé 2 - Acionamento",
        4: "Relé 3 - Acionamento",
        5: "Relé 4 - Acionamento",
        # ... até onde necessário
    },

    # Discrete Inputs (1xxxx) - 1-based
    "discrete_inputs": {
        10001: "Alarme geral",
        10002: "Alarme Sens_F",
        # ... todos os alarmes bit a bit
    },

    # Input Registers (3xxxx) - 1-based
    "input_registers": {
        30001: ("Tensão CC no Banco", "V", 0.1, -32768, 32767),
        30002: ("Corrente CC no Banco", "A", 0.1, -32768, 32767),
        # ... todas as medições
    },

    # Holding Registers (4xxxx) - 1-based
    "holding_registers": {
        40001: ("Número do Dispositivo a Monitorar", "", 1, 0, 247),
        40002: ("Comando - Medir Resistência", "", 1, 0, 240),
        # ... todos os registros R/W
    }
}
```

### 3. Valores de Simulação

Os valores devem seguir padrões realistas:

```python
# Exemplos de valores típicos para simulação
DEFAULT_SIMULATION_VALUES = {
    # Medições principais
    30001: 4800,  # 480.0V (48V * 10 células)
    30002: 100,   # 10.0A
    30003: 4800,  # 4.8kW
    30007: 120,   # 120 minutos de autonomia
    30009: 800,   # 80.0% SOC
    30010: 950,   # 95.0% SOH

    # Valores por elemento (exemplo para 240 elementos)
    "element_voltages": [3200] * 240,  # 3.2V por célula
    "element_temperatures": [250] * 240,  # 25.0°C
    "element_resistances": [150] * 240,  # 1.50 mΩ
}
```

## 🚀 ETAPAS DE DESENVOLVIMENTO

### ETAPA 1: Estrutura Base (1-2 dias)
- Configurar servidor Modbus (pymodbus, modbus-tk, ou similar)
- Implementar handler básico com 4 áreas de memória
- Criar mapeamento básico dos endereços

### ETAPA 2: Implementação Completa do Mapa (3-5 dias)
- Implementar TODOS os registradores da tabela
- Configurar permissões (R, R/W, R/W(F), R/W(U))
- Implementar lógica para registradores de 32 bits (MSB/LSB)

### ETAPA 3: Sistema de Simulação (2-3 dias)

Criar engine de simulação realista:
- Variação temporal de valores
- Correlação entre parâmetros
- Alarmes baseados em thresholds

Implementar comportamentos específicos:
- Comando de medição de resistência (registrador 1)
- Balanceador acionado (11002)
- Status de comunicação (30102)

### ETAPA 4: Interface de Controle (2-3 dias)
- API REST/WebSocket para controle manual
- Interface web básica ou CLI
- Import/Export de configurações

### ETAPA 5: Testes e Validação (2 dias)
- Teste com clientes Modbus padrão
- Validação de todos os registradores
- Teste de stress/concorrência

## 💻 SUGESTÃO DE TECNOLOGIAS

### Opção 1: Python (Recomendado para protótipo rápido)

```python
# Bibliotecas sugeridas
requirements.txt:
pymodbus==3.5.4
flask==3.0.0  # Para API de controle
numpy==1.24.0  # Para cálculos de simulação
```

### Opção 2: Node.js (Para integração web)

```javascript
// Bibliotecas sugeridas
{
  "dependencies": {
    "modbus-serial": "^8.0.6",
    "express": "^4.18.2",
    "socket.io": "^4.7.2"
  }
}
```

### Opção 3: C++ (Para performance)

```cpp
// Bibliotecas sugeridas
- libmodbus (http://libmodbus.org/)
- Crow (para API REST) ou simples HTTP server
```

## 🎮 INTERFACE DE CONTROLE SUGERIDA

Precisamos de uma forma de controlar os valores manualmente. Sugiro:

### API REST Endpoints:

```
GET  /api/registers              # Listar todos os registradores
GET  /api/registers/:address     # Ler valor específico
POST /api/registers/:address     # Escrever valor
POST /api/simulation/start       # Iniciar simulação automática
POST /api/simulation/stop        # Parar simulação
POST /api/scenarios/:name        # Carregar cenário pré-definido
```

### Cenários pré-definidos:
- **Normal:** Valores dentro da faixa normal
- **Alarme Tensão Alta:** Vbat_H ativado
- **Falha Elemento:** Um elemento com falha
- **Bateria Fraca:** SOC_L ativado
- **Comunicação Falha:** Erros de comunicação com SN

## 🔧 DETALHES DE IMPLEMENTAÇÃO CRÍTICOS

### 1. Registradores de 32 bits

```python
# Exemplo: Potência no Banco (30031-30032)
def get_power_value():
    msb = registers[30031]  # 0-65535
    lsb = registers[30032]  # 0-65535
    return (msb << 16) | lsb  # Valor de 32 bits
```

### 2. Alarmes Bit a Bit

```python
# Os alarmes estão em words de 16 bits onde cada bit é um alarme
# Exemplo: Registrador 30021 (Resumo de Alarmes)
def decode_alarm_word(value):
    alarms = {
        0: "geral",      # Bit 0
        1: "Sens_F",     # Bit 1
        4: "bateria",    # Bit 4
        # ... etc
    }

    active_alarms = []
    for bit, name in alarms.items():
        if (value >> bit) & 1:
            active_alarms.append(name)

    return active_alarms
```

### 3. Simulação de Elementos (1-240)

Implementar classe BatteryElement:

```python
class BatteryElement:
    def __init__(self, id):
        self.id = id
        self.voltage = 3.2 + random.uniform(-0.1, 0.1)
        self.temperature = 25.0 + random.uniform(-2, 2)
        self.resistance = 1.5 + random.uniform(-0.2, 0.2)
        self.soc = 80.0 + random.uniform(-5, 5)
        self.soh = 95.0 + random.uniform(-3, 3)
        self.alarms = 0
```

## 📁 ESTRUTURA DE PROJETO SUGERIDA

```
modbus_bms_emulator/
├── src/
│   ├── modbus_server.py          # Servidor Modbus principal
│   ├── memory_map.py            # Definição completa do mapa
│   ├── simulation_engine.py     # Motor de simulação
│   ├── api_controller.py        # API REST para controle
│   └── scenarios/               # Cenários pré-definidos
├── config/
│   ├── default_values.yaml      # Valores padrão
│   └── permissions.yaml         # Permissões por registrador
├── tests/
│   ├── test_modbus_responses.py
│   └── test_simulation.py
├── docs/
│   └── register_map_complete.md # Documentação completa
└── requirements.txt
```

## 🧪 TESTES A REALIZAR

- **Teste de Conectividade:** Conexão Modbus básica
- **Teste de Leitura:** Ler todos os blocos de registradores
- **Teste de Escrita:** Escrever em registradores R/W
- **Teste de Alarmes:** Ativar/desativar alarmes via API
- **Teste de Performance:** Múltiplos clientes simultâneos
- **Teste de Cenários:** Transição entre cenários pré-definidos

## 📝 ENTREGÁVEIS

- Código fonte completo e documentado
- Dockerfile para containerização (opcional mas recomendado)
- docker-compose.yml para fácil execução
- Documentação de API e exemplos de uso
- Scripts de teste com exemplos Modbus

## 🕒 PRAZO ESTIMADO

- **Versão básica funcional:** 5-7 dias
- **Versão completa com simulação:** 10-14 dias
- **Versão com interface web:** 15-20 dias
