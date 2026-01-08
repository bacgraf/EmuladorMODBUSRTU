"""Parser do CSV para construir mapa de memória"""
import csv

class MemoryMapParser:
    def __init__(self, csv_path):
        self.csv_path = csv_path
        self.coils = {}
        self.discrete_inputs = {}
        self.input_registers = {}
        self.holding_registers = {}
        
    def parse(self):
        """Lê o CSV e organiza por função Modbus"""
        with open(self.csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                try:
                    tipo = row.get('Tipo', '').strip()
                    base0 = row.get('RegBase0', '').strip()
                    base1 = row.get('RegBase1', '').strip()
                    objeto = row.get('Objeto', '').strip()
                    unidade = row.get('Unidade', '').strip()
                    resolucao = row.get('Resolucao', '').strip()
                    permissao = row.get('Permissao', '').strip()
                    fcs = row.get('FCs', '').strip()
                    intervalo = row.get('Intervalo', '').strip()
                    valor_inicial = row.get('ValorInicial', '').strip()
                    descricao = row.get('Descricao', '').strip()
                    
                    # Ignorar linhas vazias
                    if not tipo or not base0 or not base1 or not objeto:
                        continue
                    
                    # Converter endereços
                    addr_base0 = int(base0)
                    addr_base1 = int(base1)
                    
                    # Valor inicial
                    if valor_inicial.upper() == 'ON':
                        val_inicial = 1
                        pass # print(f"DEBUG PARSER: {tipo} {addr_base0} = ON → 1")
                    elif valor_inicial.upper() == 'OFF':
                        val_inicial = 0
                        pass # print(f"DEBUG PARSER: {tipo} {addr_base0} = OFF → 0")
                    elif valor_inicial:
                        val_inicial = int(valor_inicial)
                        pass # print(f"DEBUG PARSER: {tipo} {addr_base0} = {valor_inicial} → {val_inicial}")
                    else:
                        val_inicial = 0
                        pass # print(f"DEBUG PARSER: {tipo} {addr_base0} = (vazio) → 0")
                    
                    # Criar registro
                    reg = {
                        'base0': addr_base0,
                        'base1': addr_base1,
                        'tipo': tipo,
                        'nome': objeto,
                        'unidade': unidade,
                        'resolucao': resolucao,
                        'permissao': permissao,
                        'fcs': fcs,
                        'intervalo': intervalo,
                        'valor_inicial': val_inicial,
                        'descricao': descricao
                    }
                    
                    # Classificar por tipo
                    if tipo == 'COIL':
                        self.coils[addr_base0] = reg
                    elif tipo == 'DISC':
                        self.discrete_inputs[addr_base0] = reg
                    elif tipo == 'IREG':
                        self.input_registers[addr_base0] = reg
                    elif tipo == 'HREG':
                        self.holding_registers[addr_base0] = reg
                
                except Exception as e:
                    continue
        
        print(f"✅ CSV parseado:")
        print(f"   Coils: {len(self.coils)}")
        print(f"   Discrete Inputs: {len(self.discrete_inputs)}")
        print(f"   Input Registers: {len(self.input_registers)}")
        print(f"   Holding Registers: {len(self.holding_registers)}")
        
        return self.coils, self.discrete_inputs, self.input_registers, self.holding_registers
