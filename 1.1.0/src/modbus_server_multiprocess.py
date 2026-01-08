"""Servidor Modbus com multiprocessing - comunicação bidirecional + kill instantâneo"""
import multiprocessing as mp
import asyncio
import time
import sys
from pymodbus.server.async_io import ModbusSerialServer
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext, ModbusSequentialDataBlock
from pymodbus.transaction import ModbusRtuFramer
from pymodbus.pdu import ExceptionResponse



class SharedDataBlock(ModbusSequentialDataBlock):
    """DataBlock que sincroniza com shared array"""
    def __init__(self, address, values, shared_array):
        super().__init__(address, values)
        self.shared_array = shared_array
        for i, val in enumerate(values):
            if i < len(shared_array):
                shared_array[i] = val
    
    def setValues(self, address, values):
        super().setValues(address, values)
        for i, val in enumerate(values):
            idx = address + i
            if idx < len(self.shared_array):
                self.shared_array[idx] = val
    
    def getValues(self, address, count=1):
        for i in range(count):
            idx = address + i
            if idx < len(self.shared_array):
                self.values[idx] = self.shared_array[idx]
        return super().getValues(address, count)

class CustomModbusServerContext(ModbusServerContext):
    """Context customizado que valida permissões"""
    def __init__(self, slaves, single, permissions, allowed_fcs):
        super().__init__(slaves=slaves, single=single)
        self.permissions = permissions
        self.allowed_fcs = allowed_fcs
    
    def setValues(self, unit, fx, address, values):
        """Intercepta escritas e valida permissões"""
        # LOG DETALHADO - Descomente para debug
        # print(f"\n📨 WRITE: Unit={unit}, FC={fx}, Addr={address}, Values={values}")
        
        fc_to_type = {1: 'coils', 5: 'coils', 15: 'coils', 6: 'hr', 16: 'hr'}
        reg_type = fc_to_type.get(fx)
        
        if reg_type:
            perms = self.permissions.get(reg_type, {})
            
            for i in range(len(values)):
                addr = address + i
                perm = perms.get(addr, 'R/W').upper()
                # print(f"  → Addr {addr}: Permissão={perm}")
                
                if 'W' not in perm:
                    print(f"❌ BLOQUEADO: Escrita em endereço {addr} somente leitura (Permissão: {perm})")
                    return None
            
            # print(f"  ✅ PERMITIDO\n")
        
        return super().setValues(unit, fx, address, values)

def run_modbus_server(port, baudrate, bytesize, parity, stopbits, slave_id, 
                      coils_array, di_array, ir_array, hr_array,
                      coils_perm, di_perm, ir_perm, hr_perm,
                      coils_fcs, di_fcs, ir_fcs, hr_fcs):
    """Função executada no processo separado"""
    
    async def start_server():
        # Criar datablocks compartilhados
        store = ModbusSlaveContext(
            co=SharedDataBlock(0, list(coils_array), coils_array),
            di=SharedDataBlock(0, list(di_array), di_array),
            ir=SharedDataBlock(0, list(ir_array), ir_array),
            hr=SharedDataBlock(0, list(hr_array), hr_array)
        )
        
        # Context customizado com permissões e FCs
        permissions = {
            'coils': coils_perm,
            'di': di_perm,
            'ir': ir_perm,
            'hr': hr_perm
        }
        allowed_fcs = {
            'coils': coils_fcs,
            'di': di_fcs,
            'ir': ir_fcs,
            'hr': hr_fcs
        }
        context = CustomModbusServerContext(slaves={slave_id: store, 0: store}, single=False, permissions=permissions, allowed_fcs=allowed_fcs)
        
        print(f"[PROCESSO] Servidor Modbus iniciado em {port} @ {baudrate} bps | Slave ID: {slave_id}")
        
        # Criar servidor dentro de função async
        server = ModbusSerialServer(
            context=context,
            framer=ModbusRtuFramer,
            port=port,
            baudrate=baudrate,
            bytesize=bytesize,
            parity=parity,
            stopbits=stopbits,
            timeout=1
        )
        
        await server.serve_forever()
    
    # Criar novo event loop para o processo filho
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(start_server())
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()

class ModbusServerMultiprocess:
    """Servidor Modbus com multiprocessing - melhor dos dois mundos"""
    
    def __init__(self):
        self.process = None
        self.running = False
        self.store = None
        self.coils_array = None
        self.di_array = None
        self.ir_array = None
        self.hr_array = None
    
    def create_datastore(self, coils_data, di_data, ir_data, hr_data, 
                        coil_callback=None, di_callback=None, 
                        ir_callback=None, hr_callback=None,
                        coils_perm=None, di_perm=None, ir_perm=None, hr_perm=None,
                        coils_fcs=None, di_fcs=None, ir_fcs=None, hr_fcs=None):
        """Cria datastore compartilhado com permissões e FCs"""
        self.store = {
            'coils': list(coils_data),
            'di': list(di_data),
            'ir': list(ir_data),
            'hr': list(hr_data)
        }
        self.permissions = {
            'coils': coils_perm or {},
            'di': di_perm or {},
            'ir': ir_perm or {},
            'hr': hr_perm or {}
        }
        self.allowed_fcs = {
            'coils': coils_fcs or {},
            'di': di_fcs or {},
            'ir': ir_fcs or {},
            'hr': hr_fcs or {}
        }
        return self.store
    
    def start(self, port, baudrate, bytesize, parity, stopbits, slave_id):
        """Inicia servidor em processo separado com shared arrays"""
        if self.running:
            return False, "Servidor já está rodando"
        
        if not self.store:
            return False, "Datastore não criado"
        
        try:
            # Criar arrays compartilhados (ctypes)
            self.coils_array = mp.Array('i', self.store['coils'])
            self.di_array = mp.Array('i', self.store['di'])
            self.ir_array = mp.Array('i', self.store['ir'])
            self.hr_array = mp.Array('i', self.store['hr'])
            
            # Iniciar processo com permissões e FCs
            self.process = mp.Process(
                target=run_modbus_server,
                args=(port, baudrate, bytesize, parity, stopbits, slave_id,
                      self.coils_array, self.di_array, self.ir_array, self.hr_array,
                      self.permissions['coils'], self.permissions['di'], 
                      self.permissions['ir'], self.permissions['hr'],
                      self.allowed_fcs['coils'], self.allowed_fcs['di'],
                      self.allowed_fcs['ir'], self.allowed_fcs['hr'])
            )
            self.process.start()
            
            # Aguardar inicialização
            time.sleep(0.5)
            
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
        
        if self.process and self.process.is_alive():
            print(f"💀 Matando processo {self.process.pid}...")
            self.process.kill()
            self.process.join(timeout=2)
            print(f"💀 Processo morto - Porta liberada!")
        
        self.cleanup()
    
    def cleanup(self):
        """Limpa recursos"""
        self.coils_array = None
        self.di_array = None
        self.ir_array = None
        self.hr_array = None
        self.process = None
    
    def set_value(self, function_code, address, value):
        """Define valor via shared array"""
        if not self.running:
            return
        
        try:
            array_map = {1: self.coils_array, 2: self.di_array, 3: self.hr_array, 4: self.ir_array}
            array = array_map.get(function_code)
            if array and address < len(array):
                array[address] = value
        except Exception as e:
            print(f"⚠️ Erro ao definir valor: {e}")
    
    def get_value(self, function_code, address):
        """Obtém valor via shared array"""
        if not self.running:
            return None
        
        try:
            array_map = {1: self.coils_array, 2: self.di_array, 3: self.hr_array, 4: self.ir_array}
            array = array_map.get(function_code)
            if array and address < len(array):
                return array[address]
        except Exception as e:
            print(f"⚠️ Erro ao obter valor: {e}")
        
        return None
