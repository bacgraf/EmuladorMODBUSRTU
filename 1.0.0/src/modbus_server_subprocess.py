"""Gerenciador de servidor Modbus usando subprocess - SOLUÇÃO DEFINITIVA"""
import subprocess
import pickle
import tempfile
import os
import sys
from pymodbus.datastore import ModbusSlaveContext, ModbusSequentialDataBlock

class ModbusServerSubprocess:
    """Servidor Modbus que roda em processo separado - pode ser morto instantaneamente"""
    
    def __init__(self):
        self.process = None
        self.running = False
        self.store = None
        self.datastore_file = None
    
    def create_datastore(self, coils_data, di_data, ir_data, hr_data, 
                        coil_callback=None, di_callback=None, 
                        ir_callback=None, hr_callback=None):
        """Cria datastore (callbacks não suportados em subprocess)"""
        self.store = {
            'coils': coils_data,
            'di': di_data,
            'ir': ir_data,
            'hr': hr_data
        }
        return self.store
    
    def start(self, port, baudrate, bytesize, parity, stopbits, slave_id):
        """Inicia servidor em processo separado"""
        if self.running:
            return False, "Servidor já está rodando"
        
        if not self.store:
            return False, "Datastore não criado"
        
        try:
            # Salvar datastore em arquivo temporário
            self.datastore_file = tempfile.mktemp(suffix='.pkl')
            with open(self.datastore_file, 'wb') as f:
                pickle.dump(self.store, f)
            
            # Caminho do script do servidor
            server_script = os.path.join(os.path.dirname(__file__), 'modbus_server_process.py')
            
            # Iniciar processo separado
            self.process = subprocess.Popen([
                sys.executable,
                server_script,
                port,
                str(baudrate),
                str(bytesize),
                parity,
                str(stopbits),
                str(slave_id),
                self.datastore_file
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            self.running = True
            print(f"✅ Servidor iniciado em processo separado (PID: {self.process.pid})")
            return True, f"Servidor iniciado em {port} @ {baudrate} bps | Slave ID: {slave_id} | PID: {self.process.pid}"
            
        except Exception as e:
            self.cleanup()
            return False, str(e)
    
    def stop(self):
        """Para servidor MATANDO o processo - INSTANTÂNEO!"""
        if not self.running:
            return
        
        self.running = False
        print("🛑 Matando processo do servidor...")
        
        if self.process:
            try:
                # MATAR O PROCESSO - Windows libera TUDO automaticamente!
                self.process.kill()
                self.process.wait(timeout=2)
                print(f"💀 Processo {self.process.pid} morto - Porta liberada!")
            except Exception as e:
                print(f"⚠️ Erro ao matar processo: {e}")
        
        self.cleanup()
        print("✅ Servidor parado")
    
    def cleanup(self):
        """Limpa recursos"""
        self.process = None
        if self.datastore_file and os.path.exists(self.datastore_file):
            try:
                os.remove(self.datastore_file)
            except:
                pass
        self.datastore_file = None
    
    def set_value(self, function_code, address, value):
        """Define valor - NÃO SUPORTADO em subprocess (sem comunicação bidirecional)"""
        pass
    
    def get_value(self, function_code, address):
        """Obtém valor - NÃO SUPORTADO em subprocess"""
        return None
