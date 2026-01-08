"""Servidor Modbus em processo separado - pode ser morto sem problemas"""
import asyncio
import sys
from pymodbus.server.async_io import StartSerialServer
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext, ModbusSequentialDataBlock
from pymodbus.transaction import ModbusRtuFramer
import pickle

async def run_server(port, baudrate, bytesize, parity, stopbits, slave_id, datastore_file):
    """Executa servidor Modbus em processo separado"""
    
    # Carregar datastore do arquivo
    with open(datastore_file, 'rb') as f:
        data = pickle.load(f)
    
    # Criar datastore
    store = ModbusSlaveContext(
        co=ModbusSequentialDataBlock(0, data['coils']),
        di=ModbusSequentialDataBlock(0, data['di']),
        ir=ModbusSequentialDataBlock(0, data['ir']),
        hr=ModbusSequentialDataBlock(0, data['hr'])
    )
    
    context = ModbusServerContext(slaves={slave_id: store, 0: store}, single=False)
    
    print(f"[PROCESSO] Iniciando servidor em {port} @ {baudrate} bps | Slave ID: {slave_id}")
    
    # Iniciar servidor
    server = await StartSerialServer(
        context=context,
        framer=ModbusRtuFramer,
        port=port,
        baudrate=baudrate,
        bytesize=bytesize,
        parity=parity,
        stopbits=stopbits,
        timeout=1
    )
    
    print(f"[PROCESSO] Servidor rodando (PID: {sys.argv[0]})")
    
    # Rodar para sempre
    await asyncio.Event().wait()

if __name__ == "__main__":
    # Argumentos: port baudrate bytesize parity stopbits slave_id datastore_file
    port = sys.argv[1]
    baudrate = int(sys.argv[2])
    bytesize = int(sys.argv[3])
    parity = sys.argv[4]
    stopbits = int(sys.argv[5])
    slave_id = int(sys.argv[6])
    datastore_file = sys.argv[7]
    
    asyncio.run(run_server(port, baudrate, bytesize, parity, stopbits, slave_id, datastore_file))
