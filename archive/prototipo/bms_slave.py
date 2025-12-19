"""Servidor Modbus RTU EmuladorMODBUSRTU - 19200 8N1 ID1"""
import logging
from pymodbus.server.sync import StartSerialServer
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext, ModbusSequentialDataBlock
from pymodbus.transaction import ModbusRtuFramer

logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)

PORT = 'COM16'
BAUDRATE = 19200

print("=" * 60)
print("📡 EMULADOR MODBUS RTU - EmuladorMODBUSRTU")
print("=" * 60)
print(f"Porta Servidor: {PORT}")
print(f"Porta Cliente: COM13")
print(f"Baudrate: {BAUDRATE} bps")
print(f"Configuração: 8N1")
print(f"Slave ID: 1")
print("=" * 60)
print("Coil (base 0):")
print("  0 - Comando Medir Resistência (R/W - Função 01/05)")
print("Discrete Inputs (base 0):")
print("  0-15 - Alarmes Resumo (10001-10016)")
print("    0: geral, 1: Sens_F, 4: bateria, 5: elemento")
print("    6: analog, 7: Din, 8: Vcc, 9: Ibat")
print("    10: Bat_low, 11: Bat_life, 12: Temp_amb")
print("    13: Umid, 14: H2")
print("=" * 60)

# Inicializar discrete inputs com valores padrão
discrete_values = [0] * 10000
# Pode setar alguns alarmes como exemplo:
# discrete_values[0] = 1  # Alarme geral ativo

store = ModbusSlaveContext(
    di=ModbusSequentialDataBlock(0, discrete_values),
    co=ModbusSequentialDataBlock(0, [0]*100),
    hr=ModbusSequentialDataBlock(0, [0]*100),
    ir=ModbusSequentialDataBlock(0, [0]*100)
)

context = ModbusServerContext(slaves=store, single=True)

print("✅ Servidor iniciado")
print("=" * 60)

StartSerialServer(
    context,
    framer=ModbusRtuFramer,
    port=PORT,
    baudrate=BAUDRATE,
    bytesize=8,
    parity='N',
    stopbits=1,
    timeout=1
)
