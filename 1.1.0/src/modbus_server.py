"""Módulo Modbus Server - Gerencia servidor Modbus RTU Serial"""
import asyncio
import threading
import time
import warnings

# Suprimir warnings de tasks pendentes do pymodbus
warnings.filterwarnings('ignore', category=RuntimeWarning, message='coroutine.*was never awaited')
warnings.filterwarnings('ignore', message='Task was destroyed but it is pending')
from pymodbus.server.async_io import StartSerialServer
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext, ModbusSequentialDataBlock
from pymodbus.transaction import ModbusRtuFramer


class EventDrivenDataBlock(ModbusSequentialDataBlock):
    """DataBlock com callbacks para notificação imediata de mudanças"""
    def __init__(self, address, values, callback=None):
        super().__init__(address, values)
        self.callback = callback
        self.base_address = address
    
    def setValues(self, address, values):
        super().setValues(address, values)
        if self.callback:
            for i, value in enumerate(values):
                try:
                    self.callback(address + i, value)
                except Exception as e:
                    print(f"⚠️ Erro no callback addr={address+i}: {e}")


class ModbusServer:
    """Servidor Modbus RTU Serial"""
    
    def __init__(self):
        self.server = None
        self.server_thread = None
        self.server_loop = None
        self.server_ready = None
        self.serial_port = None
        self.running = False
        self.context = None
        self.store = None
    
    def create_datastore(self, coils_data, di_data, ir_data, hr_data, 
                        coil_callback=None, di_callback=None, 
                        ir_callback=None, hr_callback=None):
        """Cria datastore com callbacks"""
        self.store = ModbusSlaveContext(
            co=EventDrivenDataBlock(0, coils_data, coil_callback),
            di=EventDrivenDataBlock(0, di_data, di_callback),
            ir=EventDrivenDataBlock(0, ir_data, ir_callback),
            hr=EventDrivenDataBlock(0, hr_data, hr_callback)
        )
        return self.store
    
    def start(self, port, baudrate, bytesize, parity, stopbits, slave_id):
        """Inicia servidor Modbus"""
        if self.running:
            return False, "Servidor já está rodando"
        
        if not self.store:
            return False, "Datastore não criado"
        
        try:
            # Criar contexto com Slave ID específico e broadcast
            self.context = ModbusServerContext(slaves={
                slave_id: self.store,
                0: self.store
            }, single=False)
            
            self.server_ready = threading.Event()
            
            async def create_and_run_server():
                self.server = await StartSerialServer(
                    context=self.context,
                    framer=ModbusRtuFramer,
                    port=port,
                    baudrate=baudrate,
                    bytesize=bytesize,
                    parity=parity,
                    stopbits=stopbits,
                    timeout=1
                )
                
                # Capturar referência da porta serial
                try:
                    if hasattr(self.server, 'protocol') and hasattr(self.server.protocol, 'transport'):
                        if hasattr(self.server.protocol.transport, '_serial'):
                            self.serial_port = self.server.protocol.transport._serial
                except Exception as e:
                    print(f"⚠️ Não foi possível capturar porta: {e}")
                
                self.server_ready.set()
                await asyncio.Event().wait()
            
            def run_async_server():
                self.server_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self.server_loop)
                try:
                    self.server_loop.run_until_complete(create_and_run_server())
                except asyncio.CancelledError:
                    pass
                except Exception as e:
                    print(f"⚠️ Servidor encerrado: {e}")
                finally:
                    self.server_loop.close()
            
            self.server_thread = threading.Thread(target=run_async_server, daemon=True)
            self.server_thread.start()
            self.server_ready.wait(timeout=1)
            
            self.running = True
            return True, f"Servidor iniciado em {port} @ {baudrate} bps | Slave ID: {slave_id}"
            
        except Exception as e:
            self.cleanup()
            return False, str(e)
    
    def stop(self):
        """Para servidor Modbus - NOVA ORDEM: Porta PRIMEIRO"""
        if not self.running:
            return
        
        self.running = False
        print("🛑 Iniciando parada do servidor...")
        
        # 1️⃣ FECHAR PORTA SERIAL PRIMEIRO (antes de qualquer coisa!)
        if self.serial_port:
            try:
                if hasattr(self.serial_port, 'is_open') and self.serial_port.is_open:
                    self.serial_port.close()
                    print("🔌 Porta serial fechada PRIMEIRO")
            except Exception as e:
                print(f"⚠️ Erro ao fechar porta: {e}")
        
        time.sleep(0.5)  # Aguardar porta fechar
        
        # 2️⃣ Fechar servidor Modbus
        if self.server:
            try:
                self.server.server_close()
                print("📡 Servidor Modbus fechado")
            except Exception as e:
                print(f"⚠️ Erro ao fechar servidor: {e}")
        
        # 3️⃣ Cancelar tasks e parar loop
        if self.server_loop and self.server_loop.is_running():
            try:
                def cancel_all_tasks():
                    tasks = asyncio.all_tasks(self.server_loop)
                    print(f"   📋 Cancelando {len(tasks)} tasks pendentes...")
                    for task in tasks:
                        task.cancel()
                    self.server_loop.stop()
                
                self.server_loop.call_soon_threadsafe(cancel_all_tasks)
                print("⏸️ Tasks canceladas e loop parado")
            except Exception as e:
                print(f"⚠️ Erro ao parar loop: {e}")
        
        print("✅ Servidor parado")
        self.cleanup()
    
    def cleanup(self):
        """Limpa recursos"""
        self.server = None
        # NÃO limpar server_thread e server_loop - deixar Python gerenciar
        self.serial_port = None
    
    def set_value(self, function_code, address, value):
        """Define valor em registrador"""
        if self.store:
            self.store.setValues(function_code, address, [value])
    
    def get_value(self, function_code, address):
        """Obtém valor de registrador"""
        if self.store:
            return self.store.getValues(function_code, address, 1)[0]
        return None
