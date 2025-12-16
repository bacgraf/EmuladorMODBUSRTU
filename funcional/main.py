"""EmuladorMODBUSRTU com interface em abas - Lê CSV automaticamente"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pymodbus.server.sync import ModbusSerialServer
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext, ModbusSequentialDataBlock
from pymodbus.transaction import ModbusRtuFramer
from threading import Thread
from csv_parser import MemoryMapParser
import time
import serial.tools.list_ports
import os

class ModbusEmulator:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("📡 EmuladorMODBUSRTU - Baseado em CSV")
        self.window.geometry("1200x800")
        self.window.resizable(True, True)
        
        # CSV path
        self.config_file = "emulator_modbus_config.txt"
        last_csv = self.load_last_csv_path()
        self.csv_path = tk.StringVar(value=last_csv if last_csv else "")
        self.coils_map = {}
        self.di_map = {}
        self.ir_map = {}
        self.hr_map = {}
        
        self.store = None
        self.context = None
        
        # Controles da interface
        self.coil_controls = {}
        self.di_controls = {}
        self.ir_controls = {}
        self.hr_controls = {}
        
        self.server = None
        self.server_running = False
        self.selected_port = tk.StringVar(value="COM16")
        self.selected_baudrate = tk.IntVar(value=19200)
        self.selected_bytesize = tk.IntVar(value=8)
        self.selected_parity = tk.StringVar(value="None")
        self.selected_stopbits = tk.IntVar(value=1)
        self.slave_id = tk.IntVar(value=1)
        self.parity_map = {"None": "N", "Even": "E", "Odd": "O", "Mark": "M", "Space": "S"}
        
        self.create_widgets()
        
        # Carregar último CSV
        if self.csv_path.get() and os.path.exists(self.csv_path.get()):
            self.load_csv()
        else:
            messagebox.showinfo("Bem-vindo", "Selecione um arquivo CSV para começar")
        
        # ESC para sair do fullscreen
        self.window.bind('<Escape>', lambda e: self.window.quit())
    
    def print_memory_map(self):
        """Imprime mapa completo de memória no terminal"""
        print("\n" + "="*80)
        print("MAPA DE MEMÓRIA COMPLETO")
        print("="*80)
        
        print(f"\n[COILS - Função 01/05] Total: {len(self.coils_map)}")
        print("-" * 80)
        for addr in sorted(self.coils_map.keys()):
            reg = self.coils_map[addr]
            print(f"  Base0: {addr:5d} | Base1: {reg['base1']:5d} | Hex: 0x{addr:04X} | {reg['nome'][:45]:45s} | Val: {reg['valor_inicial']}")
        
        print(f"\n[DISCRETE INPUTS - Função 02] Total: {len(self.di_map)}")
        print("-" * 80)
        for addr in sorted(self.di_map.keys()):
            reg = self.di_map[addr]
            print(f"  Base0: {addr:5d} | Base1: {reg['base1']:5d} | Hex: 0x{addr:04X} | {reg['nome'][:45]:45s} | Val: {reg['valor_inicial']}")
        
        print(f"\n[INPUT REGISTERS - Função 04] Total: {len(self.ir_map)}")
        print("-" * 80)
        for addr in sorted(self.ir_map.keys()):
            reg = self.ir_map[addr]
            print(f"  Base0: {addr:5d} | Base1: {reg['base1']:5d} | Hex: 0x{addr:04X} | {reg['nome'][:35]:35s} | {reg['unidade']:8s} | Val: {reg['valor_inicial']}")
        
        print(f"\n[HOLDING REGISTERS - Função 03/06/16] Total: {len(self.hr_map)}")
        print("-" * 80)
        for addr in sorted(self.hr_map.keys()):
            reg = self.hr_map[addr]
            print(f"  Base0: {addr:5d} | Base1: {reg['base1']:5d} | Hex: 0x{addr:04X} | {reg['nome'][:35]:35s} | {reg['unidade']:8s} | Val: {reg['valor_inicial']}")
        
        print("\n" + "="*80)
        print(f"TOTAL DE REGISTRADORES: {len(self.coils_map) + len(self.di_map) + len(self.ir_map) + len(self.hr_map)}")
        print("="*80 + "\n")
    
    def get_available_ports(self):
        ports = [port.device for port in serial.tools.list_ports.comports()]
        return ports if ports else ["COM16"]
    
    def update_ports(self, event=None):
        ports = self.get_available_ports()
        self.port_combo.config(values=ports)
        if self.selected_port.get() not in ports and ports:
            self.selected_port.set(ports[0])
    
    def load_last_csv_path(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    return f.read().strip()
        except:
            pass
        return None
    
    def save_last_csv_path(self, path):
        try:
            with open(self.config_file, 'w') as f:
                f.write(path)
        except:
            pass
    
    def load_csv(self):
        try:
            csv_file = self.csv_path.get()
            parser = MemoryMapParser(csv_file)
            self.coils_map, self.di_map, self.ir_map, self.hr_map = parser.parse()
            
            # Salvar como último arquivo usado
            self.save_last_csv_path(csv_file)
            
            max_coil = max(self.coils_map.keys()) if self.coils_map else 0
            max_di = max(self.di_map.keys()) if self.di_map else 0
            max_ir = max(self.ir_map.keys()) if self.ir_map else 0
            max_hr = max(self.hr_map.keys()) if self.hr_map else 0
            
            coils_block = [0] * max(max_coil + 100, 1000)
            di_block = [0] * max(max_di + 100, 10000)
            ir_block = [0] * max(max_ir + 100, 10000)
            hr_block = [0] * max(max_hr + 100, 10000)
            
            for addr, reg in self.coils_map.items():
                coils_block[addr] = reg['valor_inicial']
            for addr, reg in self.di_map.items():
                di_block[addr] = reg['valor_inicial']
            for addr, reg in self.ir_map.items():
                ir_block[addr] = reg['valor_inicial']
            for addr, reg in self.hr_map.items():
                hr_block[addr] = reg['valor_inicial']
            
            self.store = ModbusSlaveContext(
                co=ModbusSequentialDataBlock(0, coils_block),
                di=ModbusSequentialDataBlock(0, di_block),
                ir=ModbusSequentialDataBlock(0, ir_block),
                hr=ModbusSequentialDataBlock(0, hr_block)
            )
            
            self.context = ModbusServerContext(slaves=self.store, single=True)
            self.print_memory_map()
            
            # Recriar abas
            for widget in self.notebook.winfo_children():
                widget.destroy()
            self.create_coils_tab()
            self.create_discrete_inputs_tab()
            self.create_input_registers_tab()
            self.create_holding_registers_tab()
            
            # Iniciar monitor se não estiver rodando
            if not hasattr(self, 'monitor_thread') or not self.monitor_thread.is_alive():
                self.monitor_thread = Thread(target=self.monitor_changes, daemon=True)
                self.monitor_thread.start()
            
            messagebox.showinfo("Sucesso", f"CSV carregado com sucesso!\n\nTotal: {len(self.coils_map) + len(self.di_map) + len(self.ir_map) + len(self.hr_map)} registradores")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao carregar CSV:\n{str(e)}")
    
    def select_csv(self):
        filename = filedialog.askopenfilename(
            title="Selecionar arquivo CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialdir=os.path.dirname(self.csv_path.get()) if os.path.exists(self.csv_path.get()) else "."
        )
        if filename:
            self.csv_path.set(filename)
            self.save_last_csv_path(filename)
            self.load_csv()
    
    def create_widgets(self):
        # Frame CSV
        csv_frame = ttk.Frame(self.window)
        csv_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(csv_frame, text="📄 Arquivo CSV:", font=("Arial", 9)).pack(side="left", padx=(0,5))
        ttk.Entry(csv_frame, textvariable=self.csv_path, state="readonly", width=60).pack(side="left", padx=(0,5))
        ttk.Button(csv_frame, text="Selecionar...", command=self.select_csv).pack(side="left")
        
        # Frame superior - Status
        status_frame = ttk.Frame(self.window)
        status_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(status_frame, text="📡 Porta:", font=("Arial", 9)).pack(side="left", padx=(0,2))
        
        self.port_combo = ttk.Combobox(status_frame, textvariable=self.selected_port, 
                                       values=self.get_available_ports(), width=8, state="readonly")
        self.port_combo.bind("<Button-1>", self.update_ports)
        self.port_combo.pack(side="left", padx=(0,8))
        
        ttk.Label(status_frame, text="Baudrate:", font=("Arial", 9)).pack(side="left", padx=(0,2))
        
        self.baudrate_combo = ttk.Combobox(status_frame, textvariable=self.selected_baudrate,
                                           values=[1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200],
                                           width=7, state="readonly")
        self.baudrate_combo.pack(side="left", padx=(0,8))
        
        ttk.Label(status_frame, text="Data Bits:", font=("Arial", 9)).pack(side="left", padx=(0,2))
        
        self.bytesize_combo = ttk.Combobox(status_frame, textvariable=self.selected_bytesize,
                                           values=[5, 6, 7, 8], width=3, state="readonly")
        self.bytesize_combo.pack(side="left", padx=(0,8))
        
        ttk.Label(status_frame, text="Paridade:", font=("Arial", 9)).pack(side="left", padx=(0,2))
        
        self.parity_combo = ttk.Combobox(status_frame, textvariable=self.selected_parity,
                                        values=["None", "Even", "Odd", "Mark", "Space"], width=6, state="readonly")
        self.parity_combo.pack(side="left", padx=(0,8))
        
        ttk.Label(status_frame, text="Stop Bits:", font=("Arial", 9)).pack(side="left", padx=(0,2))
        
        self.stopbits_combo = ttk.Combobox(status_frame, textvariable=self.selected_stopbits,
                                          values=[1, 2], width=3, state="readonly")
        self.stopbits_combo.pack(side="left", padx=(0,8))
        
        ttk.Label(status_frame, text="Slave ID:", font=("Arial", 9)).pack(side="left", padx=(0,2))
        
        self.slave_id_entry = ttk.Entry(status_frame, textvariable=self.slave_id, width=4)
        self.slave_id_entry.pack(side="left")
        
        self.status_label = ttk.Label(status_frame, text="⚪ Parado", foreground="gray", 
                 font=("Arial", 10, "bold"))
        self.status_label.pack(side="right")
        
        self.btn_toggle = ttk.Button(status_frame, text="▶ Iniciar Servidor", command=self.toggle_server)
        self.btn_toggle.pack(side="right", padx=5)
        
        # Notebook (abas)
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Criar abas
        self.create_coils_tab()
        self.create_discrete_inputs_tab()
        self.create_input_registers_tab()
        self.create_holding_registers_tab()
    
    def bind_mousewheel(self, canvas):
        """Habilita roda do mouse para rolar canvas"""
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", on_mousewheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))
    
    def create_coils_tab(self):
        """Aba Coils (Função 01/05)"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text=f"Coils (01/05) - {len(self.coils_map)} regs")
        
        # Canvas com scrollbar
        canvas = tk.Canvas(frame)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable = ttk.Frame(canvas)
        
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Header
        header = ttk.Frame(scrollable)
        header.pack(fill="x", padx=5, pady=5)
        ttk.Label(header, text="Base0", width=6, font=("Arial", 9, "bold")).pack(side="left")
        ttk.Label(header, text="Base1", width=6, font=("Arial", 9, "bold")).pack(side="left")
        ttk.Label(header, text="Nome", width=50, font=("Arial", 9, "bold")).pack(side="left")
        ttk.Label(header, text="Valor", width=10, font=("Arial", 9, "bold")).pack(side="left")
        
        # Registradores
        for addr in sorted(self.coils_map.keys()):
            reg = self.coils_map[addr]
            row = ttk.Frame(scrollable)
            row.pack(fill="x", padx=5, pady=2)
            
            ttk.Label(row, text=f"{addr}", width=6).pack(side="left")
            ttk.Label(row, text=f"{reg['base1']}", width=6).pack(side="left")
            ttk.Label(row, text=reg['nome'][:50], width=50).pack(side="left")
            
            var = tk.BooleanVar(value=bool(reg['valor_inicial']))
            cb = ttk.Checkbutton(row, variable=var, 
                                command=lambda a=addr, v=var: self.update_coil(a, v))
            cb.pack(side="left")
            self.coil_controls[addr] = var
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        scrollable.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))
        self.bind_mousewheel(canvas)
    
    def create_discrete_inputs_tab(self):
        """Aba Discrete Inputs (Função 02)"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text=f"Discrete Inputs (02) - {len(self.di_map)} regs")
        
        canvas = tk.Canvas(frame)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable = ttk.Frame(canvas)
        
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Header
        header = ttk.Frame(scrollable)
        header.pack(fill="x", padx=5, pady=5)
        ttk.Label(header, text="Base0", width=6, font=("Arial", 9, "bold")).pack(side="left")
        ttk.Label(header, text="Base1", width=6, font=("Arial", 9, "bold")).pack(side="left")
        ttk.Label(header, text="Nome", width=50, font=("Arial", 9, "bold")).pack(side="left")
        ttk.Label(header, text="Valor", width=10, font=("Arial", 9, "bold")).pack(side="left")
        
        for addr in sorted(self.di_map.keys()):
            reg = self.di_map[addr]
            row = ttk.Frame(scrollable)
            row.pack(fill="x", padx=5, pady=2)
            
            ttk.Label(row, text=f"{addr}", width=6).pack(side="left")
            ttk.Label(row, text=f"{reg['base1']}", width=6).pack(side="left")
            ttk.Label(row, text=reg['nome'][:50], width=50).pack(side="left")
            
            var = tk.BooleanVar(value=bool(reg['valor_inicial']))
            cb = ttk.Checkbutton(row, variable=var,
                                command=lambda a=addr, v=var: self.update_di(a, v))
            cb.pack(side="left")
            self.di_controls[addr] = var
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        scrollable.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))
        self.bind_mousewheel(canvas)
    
    def create_input_registers_tab(self):
        """Aba Input Registers (Função 04)"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text=f"Input Registers (04) - {len(self.ir_map)} regs")
        
        canvas = tk.Canvas(frame)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable = ttk.Frame(canvas)
        
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Header
        header = ttk.Frame(scrollable)
        header.grid(row=0, column=0, columnspan=5, sticky="ew", padx=5, pady=5)
        ttk.Label(header, text="Base0", width=6, font=("Arial", 9, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(header, text="Base1", width=6, font=("Arial", 9, "bold")).grid(row=0, column=1, sticky="w")
        ttk.Label(header, text="Nome", width=35, font=("Arial", 9, "bold")).grid(row=0, column=2, sticky="w")
        ttk.Label(header, text="Unidade", width=10, font=("Arial", 9, "bold")).grid(row=0, column=3, sticky="w")
        ttk.Label(header, text="Valor", width=15, font=("Arial", 9, "bold")).grid(row=0, column=4, sticky="w")
        
        row_num = 1
        for addr in sorted(self.ir_map.keys())[:100]:
            reg = self.ir_map[addr]
            
            ttk.Label(scrollable, text=f"{addr}", width=6).grid(row=row_num, column=0, sticky="w", padx=5, pady=1)
            ttk.Label(scrollable, text=f"{reg['base1']}", width=6).grid(row=row_num, column=1, sticky="w", padx=5, pady=1)
            ttk.Label(scrollable, text=reg['nome'][:35], width=35).grid(row=row_num, column=2, sticky="w", padx=5, pady=1)
            ttk.Label(scrollable, text=reg['unidade'], width=10).grid(row=row_num, column=3, sticky="w", padx=5, pady=1)
            
            var = tk.StringVar(value=str(reg['valor_inicial']))
            entry = ttk.Entry(scrollable, textvariable=var, width=15)
            entry.grid(row=row_num, column=4, sticky="w", padx=5, pady=1)
            entry.bind("<Return>", lambda e, a=addr, v=var: self.update_ir(a, v))
            entry.bind("<FocusOut>", lambda e, a=addr, v=var: self.update_ir(a, v))
            self.ir_controls[addr] = var
            row_num += 1
        
        ttk.Label(scrollable, text=f"... mostrando 100 de {len(self.ir_map)} registradores",
                 foreground="gray").grid(row=row_num, column=0, columnspan=5, pady=10)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        scrollable.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))
        self.bind_mousewheel(canvas)
    
    def create_holding_registers_tab(self):
        """Aba Holding Registers (Função 03/06/16)"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text=f"Holding Registers (03/06/16) - {len(self.hr_map)} regs")
        
        canvas = tk.Canvas(frame)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable = ttk.Frame(canvas)
        
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Header
        header = ttk.Frame(scrollable)
        header.grid(row=0, column=0, columnspan=5, sticky="ew", padx=5, pady=5)
        ttk.Label(header, text="Base0", width=6, font=("Arial", 9, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(header, text="Base1", width=6, font=("Arial", 9, "bold")).grid(row=0, column=1, sticky="w")
        ttk.Label(header, text="Nome", width=35, font=("Arial", 9, "bold")).grid(row=0, column=2, sticky="w")
        ttk.Label(header, text="Unidade", width=10, font=("Arial", 9, "bold")).grid(row=0, column=3, sticky="w")
        ttk.Label(header, text="Valor", width=15, font=("Arial", 9, "bold")).grid(row=0, column=4, sticky="w")
        
        row_num = 1
        for addr in sorted(self.hr_map.keys())[:100]:
            reg = self.hr_map[addr]
            
            ttk.Label(scrollable, text=f"{addr}", width=6).grid(row=row_num, column=0, sticky="w", padx=5, pady=1)
            ttk.Label(scrollable, text=f"{reg['base1']}", width=6).grid(row=row_num, column=1, sticky="w", padx=5, pady=1)
            ttk.Label(scrollable, text=reg['nome'][:35], width=35).grid(row=row_num, column=2, sticky="w", padx=5, pady=1)
            ttk.Label(scrollable, text=reg['unidade'], width=10).grid(row=row_num, column=3, sticky="w", padx=5, pady=1)
            
            var = tk.StringVar(value=str(reg['valor_inicial']))
            entry = ttk.Entry(scrollable, textvariable=var, width=15)
            entry.grid(row=row_num, column=4, sticky="w", padx=5, pady=1)
            entry.bind("<Return>", lambda e, a=addr, v=var: self.update_hr(a, v))
            entry.bind("<FocusOut>", lambda e, a=addr, v=var: self.update_hr(a, v))
            self.hr_controls[addr] = var
            row_num += 1
        
        ttk.Label(scrollable, text=f"... mostrando 100 de {len(self.hr_map)} registradores",
                 foreground="gray").grid(row=row_num, column=0, columnspan=5, pady=10)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        scrollable.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))
        self.bind_mousewheel(canvas)
    
    def update_coil(self, addr, var):
        value = 1 if var.get() else 0
        self.store.setValues(1, addr, [value])
    
    def update_di(self, addr, var):
        value = 1 if var.get() else 0
        self.store.setValues(2, addr, [value])
    
    def update_ir(self, addr, var):
        try:
            value = int(var.get())
            self.store.setValues(4, addr, [value])
        except:
            pass
    
    def update_hr(self, addr, var):
        try:
            value = int(var.get())
            self.store.setValues(3, addr, [value])
        except:
            pass
    
    def monitor_changes(self):
        """Monitora mudanças externas nos registradores"""
        while True:
            time.sleep(0.2)
            
            # Atualizar Coils (escritas externas via Modbus)
            for addr in self.coil_controls:
                try:
                    value = self.store.getValues(1, addr, 1)[0]
                    current = self.coil_controls[addr].get()
                    if bool(value) != current:
                        self.coil_controls[addr].set(bool(value))
                except:
                    pass
            
            # Atualizar Holding Registers (escritas externas via Modbus)
            for addr in self.hr_controls:
                try:
                    value = self.store.getValues(3, addr, 1)[0]
                    current = self.hr_controls[addr].get()
                    if str(value) != current:
                        self.hr_controls[addr].set(str(value))
                except:
                    pass
    
    def toggle_server(self):
        if self.server_running:
            self.stop_server()
        else:
            self.start_server()
    
    def start_server(self):
        if self.server_running:
            return
        
        port = self.selected_port.get()
        baudrate = self.selected_baudrate.get()
        bytesize = self.selected_bytesize.get()
        parity = self.parity_map[self.selected_parity.get()]
        stopbits = self.selected_stopbits.get()
        available_ports = self.get_available_ports()
        
        if port not in available_ports:
            messagebox.showerror("Erro", f"Porta {port} não está disponível!\n\nPortas disponíveis: {', '.join(available_ports)}")
            return
        
        try:
            self.server = ModbusSerialServer(
                self.context,
                framer=ModbusRtuFramer,
                port=port,
                baudrate=baudrate,
                bytesize=bytesize,
                parity=parity,
                stopbits=stopbits,
                timeout=1
            )
            
            Thread(target=self.server.serve_forever, daemon=True).start()
            self.server_running = True
            self.port_combo.config(state="disabled")
            self.baudrate_combo.config(state="disabled")
            self.bytesize_combo.config(state="disabled")
            self.parity_combo.config(state="disabled")
            self.stopbits_combo.config(state="disabled")
            self.slave_id_entry.config(state="disabled")
            self.status_label.config(text="✅ Rodando", foreground="green")
            self.btn_toggle.config(text="⏸ Parar Servidor")
            print(f"🚀 Servidor Modbus RTU iniciado em {port} @ {baudrate} bps, {bytesize}{parity}{stopbits}, Slave ID: {self.slave_id.get()}")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao iniciar servidor na porta {port}:\n{str(e)}")
            print(f"❌ Erro ao iniciar servidor: {e}")
    
    def stop_server(self):
        if not self.server_running:
            return
        
        if self.server:
            self.server.server_close()
            self.server = None
        
        self.server_running = False
        self.port_combo.config(state="readonly")
        self.baudrate_combo.config(state="readonly")
        self.bytesize_combo.config(state="readonly")
        self.parity_combo.config(state="readonly")
        self.stopbits_combo.config(state="readonly")
        self.slave_id_entry.config(state="normal")
        self.status_label.config(text="⚪ Parado", foreground="gray")
        self.btn_toggle.config(text="▶ Iniciar Servidor")
        print("⏹ Servidor Modbus RTU parado")
    
    def run(self):
        self.window.mainloop()

if __name__ == '__main__':
    app = ModbusEmulator()
    app.run()

