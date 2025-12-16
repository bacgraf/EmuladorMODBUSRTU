# 🔋 Emulador Modbus RTU Slave BMS

## 🚀 Instalação

```bash
pip install -r requirements.txt
```

## ⚙️ Configuração Fixa

- **Porta:** COM3
- **Baudrate:** 19200 bps
- **Configuração:** 8N1 (8 bits, sem paridade, 1 stop bit)
- **Slave ID:** 1

Para alterar, edite as constantes no início do arquivo `bms_slave.py`.

## ▶️ Execução

```bash
python bms_slave.py
```

## 📊 Mapa de Memória

### Coils (Função 01/05)

| Base 1 | Base 0 | Descrição | Permissão |
|--------|--------|-----------|-----------|
| 1 | 0 | Comando - Medir Resistência do Banco | R/W |
| 2 | 1 | Relé 1 - Acionamento | R |
| 3 | 2 | Relé 2 - Acionamento | R |
| 4 | 3 | Relé 3 - Acionamento | R |
| 5 | 4 | Relé 4 - Acionamento | R |

## 🧪 Teste

Use software cliente Modbus RTU:
- **QModMaster**
- **Modbus Poll**
- **ModScan**

### Exemplo de leitura:
- Função: 01 (Read Coils)
- Endereço: 0 (base 0) ou 1 (base 1)
- Quantidade: 5

### Exemplo de escrita:
- Função: 05 (Write Single Coil)
- Endereço: 0 (base 0) ou 1 (base 1)
- Valor: 0 (OFF) ou 1 (ON)
