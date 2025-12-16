"""Master Modbus RTU para monitorar o BMS Slave"""
import tkinter as tk
from tkinter import ttk
from pymodbus.client.sync import ModbusSerialClient
from csv_parser import MemoryMapParser
from threading import Thread
import time

class BMSMaster:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("🔍 Monitor BMS - Master Modbus")
        self.window.geometry("900x700")
        
        # Parser CSV
        csv_path = "Documentação/Mapa_de_memoria_BMS.csv"
        parser = MemoryMapParser(csv_path)
        self.coils_map, self.di_map, self.ir_map, self.hr_map = parser.parse()
        
        # Identificar blocos contíguos
        self.coil_blocks = self.find_contiguous_blocks(self.coils_map)
        self.di_blocks = self.find_contiguous_blocks(self.di_map)
        self.ir_blocks = self.find_contiguous_blocks(self.ir_map)
        self.hr_blocks = self.find_contiguous_blocks(self.hr_map)
        
        print(f"Blocos Coils: {self.coil_blocks}")
        print(f"Blocos DI: {self.di_blocks}")
        print(f"Blocos IR: {self.ir_blocks}")
        print(f"Blocos HR: {self.hr_blocks}")
        
        self.client = None
        self.running = False
        
        self.create_widgets()
    
    def find_contiguous_blocks(self, reg_map):
        """Identifica blocos contíguos de endereços"""
        if not reg_map:
            return []
        
        addrs = sorted(reg_map.keys())
        blocks = []
        start = addrs[0]
        count = 1
        
        for i in range(1, len(addrs)):
            if addrs[i] == addrs[i-1] + 1:
                count += 1
            else:
                blocks.append((start, count))
                start = addrs[i]
                count = 1
        blocks.append((start, count))
        return blocks
        
    def create_widgets(self):
        # Frame de conexão
        conn_frame = ttk.LabelFrame(self.window, text="Conexão", padding=10)
        conn_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(conn_frame, text="Porta: COM13 | Baudrate: 19200 | Slave ID: 1").pack()
        
        self.status_label = ttk.Label(conn_frame, text="⚪ Desconectado", foreground="gray")
        self.status_label.pack()
        
        btn_frame = ttk.Frame(conn_frame)
        btn_frame.pack(pady=5)
        
        self.btn_connect = ttk.Button(btn_frame, text="Conectar", command=self.connect)
        self.btn_connect.pack(side="left", padx=5)
        
        self.btn_disconnect = ttk.Button(btn_frame, text="Desconectar", command=self.disconnect, state="disabled")
        self.btn_disconnect.pack(side="left", padx=5)
        
        # Notebook
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.create_coils_tab()
        self.create_discrete_inputs_tab()
        self.create_input_registers_tab()
        self.create_holding_registers_tab()
        
        # Estatísticas
        stats_frame = ttk.LabelFrame(self.window, text="Estatísticas", padding=10)
        stats_frame.pack(fill="x", padx=10, pady=5)
        
        self.stats_label = ttk.Label(stats_frame, text="Leituras: 0 | Erros: 0")
        self.stats_label.pack()
        
        # Log
        log_frame = ttk.LabelFrame(self.window, text="Log", padding=10)
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        log_scroll = ttk.Scrollbar(log_frame)
        log_scroll.pack(side="right", fill="y")
        
        self.log_text = tk.Text(log_frame, height=8, yscrollcommand=log_scroll.set)
        self.log_text.pack(fill="both", expand=True)
        log_scroll.config(command=self.log_text.yview)
        
        # Configurar tags de cor
        self.log_text.tag_config("error", foreground="red")
        self.log_text.tag_config("success", foreground="green")
    
    def log(self, message):
        if "ERRO" in message or "Exceção" in message:
            self.log_text.insert(tk.END, f"{message}\n", "error")
        elif "OK" in message or "sucesso" in message:
            self.log_text.insert(tk.END, f"{message}\n", "success")
        else:
            self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
    
    def bind_mousewheel(self, canvas):
        """Habilita roda do mouse para rolar canvas"""
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", on_mousewheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))
    
    def create_coils_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text=f"Coils (01/05) - {len(self.coils_map)}")
        
        canvas = tk.Canvas(frame)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable = ttk.Frame(canvas)
        
        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        self.coil_leds = {}
        self.coil_labels = {}
        self.coil_buttons = {}
        
        for addr in sorted(self.coils_map.keys()):
            reg = self.coils_map[addr]
            row = ttk.Frame(scrollable)
            row.pack(fill="x", pady=2, padx=5)
            
            # LED
            led_canvas = tk.Canvas(row, width=20, height=20, bg="white")
            led_canvas.pack(side="left", padx=5)
            led = led_canvas.create_oval(3, 3, 17, 17, fill="gray", outline="black")
            self.coil_leds[addr] = (led_canvas, led)
            
            # Endereços
            ttk.Label(row, text=f"{addr}", width=6).pack(side="left", padx=2)
            ttk.Label(row, text=f"{reg['base1']}", width=6).pack(side="left", padx=2)
            
            # Label
            label = ttk.Label(row, text=f"{reg['nome'][:45]}: OFF", width=50)
            label.pack(side="left", padx=5)
            self.coil_labels[addr] = label
            
            # Botões
            btn_on = ttk.Button(row, text="ON", width=5, command=lambda a=addr: self.write_coil(a, True), state="disabled")
            btn_on.pack(side="left", padx=2)
            btn_off = ttk.Button(row, text="OFF", width=5, command=lambda a=addr: self.write_coil(a, False), state="disabled")
            btn_off.pack(side="left", padx=2)
            self.coil_buttons[addr] = (btn_on, btn_off)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.bind_mousewheel(canvas)
    
    def create_discrete_inputs_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text=f"Discrete Inputs (02) - {len(self.di_map)}")
        
        canvas = tk.Canvas(frame)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable = ttk.Frame(canvas)
        
        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        self.di_leds = {}
        self.di_labels = {}
        
        for addr in sorted(self.di_map.keys()):
            reg = self.di_map[addr]
            row = ttk.Frame(scrollable)
            row.pack(fill="x", pady=2, padx=5)
            
            # LED
            led_canvas = tk.Canvas(row, width=20, height=20, bg="white")
            led_canvas.pack(side="left", padx=5)
            led = led_canvas.create_oval(3, 3, 17, 17, fill="gray", outline="black")
            self.di_leds[addr] = (led_canvas, led)
            
            # Endereços
            ttk.Label(row, text=f"{addr}", width=6).pack(side="left", padx=2)
            ttk.Label(row, text=f"{reg['base1']}", width=6).pack(side="left", padx=2)
            
            # Label
            label = ttk.Label(row, text=f"{reg['nome'][:50]}: OFF", width=55)
            label.pack(side="left", padx=5)
            self.di_labels[addr] = label
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.bind_mousewheel(canvas)
    
    def create_input_registers_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text=f"Input Registers (04) - {len(self.ir_map)}")
        
        canvas = tk.Canvas(frame)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable = ttk.Frame(canvas)
        
        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        self.ir_labels = {}
        
        row_num = 0
        for addr in sorted(self.ir_map.keys())[:100]:
            reg = self.ir_map[addr]
            
            ttk.Label(scrollable, text=f"{addr}", width=6).grid(row=row_num, column=0, sticky="w", padx=5, pady=1)
            ttk.Label(scrollable, text=f"{reg['base1']}", width=6).grid(row=row_num, column=1, sticky="w", padx=5, pady=1)
            ttk.Label(scrollable, text=reg['nome'][:30], width=30).grid(row=row_num, column=2, sticky="w", padx=5, pady=1)
            ttk.Label(scrollable, text=reg['unidade'], width=8).grid(row=row_num, column=3, sticky="w", padx=5, pady=1)
            
            label = ttk.Label(scrollable, text="0", width=10)
            label.grid(row=row_num, column=4, sticky="w", padx=5, pady=1)
            self.ir_labels[addr] = label
            row_num += 1
        
        ttk.Label(scrollable, text=f"... mostrando 100 de {len(self.ir_map)} registradores", 
                 foreground="gray").grid(row=row_num, column=0, columnspan=5, pady=10)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.bind_mousewheel(canvas)
    
    def create_holding_registers_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text=f"Holding Registers (03/06/16) - {len(self.hr_map)}")
        
        canvas = tk.Canvas(frame)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable = ttk.Frame(canvas)
        
        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        self.hr_labels = {}
        self.hr_entries = {}
        self.hr_buttons = {}
        
        row_num = 0
        for addr in sorted(self.hr_map.keys())[:100]:
            reg = self.hr_map[addr]
            
            ttk.Label(scrollable, text=f"{addr}", width=6).grid(row=row_num, column=0, sticky="w", padx=5, pady=1)
            ttk.Label(scrollable, text=f"{reg['base1']}", width=6).grid(row=row_num, column=1, sticky="w", padx=5, pady=1)
            ttk.Label(scrollable, text=reg['nome'][:30], width=30).grid(row=row_num, column=2, sticky="w", padx=5, pady=1)
            ttk.Label(scrollable, text=reg['unidade'], width=8).grid(row=row_num, column=3, sticky="w", padx=5, pady=1)
            
            label = ttk.Label(scrollable, text="0", width=10)
            label.grid(row=row_num, column=4, sticky="w", padx=5, pady=1)
            self.hr_labels[addr] = label
            
            entry = ttk.Entry(scrollable, width=10)
            entry.grid(row=row_num, column=5, sticky="w", padx=5, pady=1)
            self.hr_entries[addr] = entry
            
            btn = ttk.Button(scrollable, text="Enviar", width=8, command=lambda a=addr: self.write_hr(a), state="disabled")
            btn.grid(row=row_num, column=6, sticky="w", padx=5, pady=1)
            self.hr_buttons[addr] = btn
            row_num += 1
        
        ttk.Label(scrollable, text=f"... mostrando 100 de {len(self.hr_map)} registradores", 
                 foreground="gray").grid(row=row_num, column=0, columnspan=7, pady=10)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.bind_mousewheel(canvas)
    
    def connect(self):
        self.client = ModbusSerialClient(
            method='rtu',
            port='COM13',
            baudrate=19200,
            bytesize=8,
            parity='N',
            stopbits=1,
            timeout=1
        )
        
        if self.client.connect():
            self.status_label.config(text="🟢 Conectado", foreground="green")
            self.btn_connect.config(state="disabled")
            self.btn_disconnect.config(state="normal")
            self.log("Conectado com sucesso")
            
            # Habilitar botões
            for btn_on, btn_off in self.coil_buttons.values():
                btn_on.config(state="normal")
                btn_off.config(state="normal")
            for btn in self.hr_buttons.values():
                btn.config(state="normal")
            
            self.running = True
            Thread(target=self.poll_loop, daemon=True).start()
        else:
            self.status_label.config(text="🔴 Erro ao conectar", foreground="red")
            self.log("ERRO: Falha ao conectar")
    
    def disconnect(self):
        self.running = False
        if self.client:
            try:
                self.client.close()
            except:
                pass
        self.status_label.config(text="⚪ Desconectado", foreground="gray")
        self.btn_connect.config(state="normal")
        self.btn_disconnect.config(state="disabled")
        self.log("Desconectado")
        
        # Desabilitar botões
        for btn_on, btn_off in self.coil_buttons.values():
            btn_on.config(state="disabled")
            btn_off.config(state="disabled")
        for btn in self.hr_buttons.values():
            btn.config(state="disabled")
    
    def poll_loop(self):
        leituras = 0
        erros = 0
        erros_consecutivos = 0
        
        while self.running:
            try:
                cycle_start = time.time()
                active_tab = self.notebook.index(self.notebook.select())
                sucesso = False
                
                if active_tab == 0 and self.coil_blocks:
                    for start_addr, count in self.coil_blocks:
                        tentativas = 0
                        while tentativas < 5 and self.running:
                            self.log(f"REQ: read_coils(addr={start_addr}, count={count})")
                            result = self.client.read_coils(start_addr, count, unit=1)
                            if not result.isError():
                                self.log(f"RESP: OK - {count} bits lidos")
                                for i in range(count):
                                    addr = start_addr + i
                                    if addr in self.coils_map:
                                        self.update_coil(addr, result.bits[i])
                                sucesso = True
                                break
                            tentativas += 1
                        if tentativas >= 5:
                            self.log(f"ERRO: Falha após 5 tentativas em read_coils(addr={start_addr}, count={count})")
                
                elif active_tab == 1 and self.di_blocks:
                    for start_addr, count in self.di_blocks:
                        tentativas = 0
                        while tentativas < 5 and self.running:
                            self.log(f"REQ: read_discrete_inputs(addr={start_addr}, count={count})")
                            result = self.client.read_discrete_inputs(start_addr, count, unit=1)
                            if not result.isError():
                                self.log(f"RESP: OK - {count} bits lidos")
                                for i in range(count):
                                    addr = start_addr + i
                                    if addr in self.di_map:
                                        self.update_di(addr, result.bits[i])
                                sucesso = True
                                break
                            tentativas += 1
                        if tentativas >= 5:
                            self.log(f"ERRO: Falha após 5 tentativas em read_discrete_inputs(addr={start_addr}, count={count})")
                
                elif active_tab == 2 and self.ir_blocks:
                    addrs_to_read = set(sorted(self.ir_map.keys())[:100])
                    for start_addr, count in self.ir_blocks:
                        if start_addr in addrs_to_read:
                            tentativas = 0
                            while tentativas < 5 and self.running:
                                self.log(f"REQ: read_input_registers(addr={start_addr}, count={count})")
                                result = self.client.read_input_registers(start_addr, count, unit=1)
                                if not result.isError():
                                    self.log(f"RESP: OK - {count} regs lidos")
                                    for i in range(count):
                                        addr = start_addr + i
                                        if addr in self.ir_labels:
                                            self.ir_labels[addr].config(text=str(result.registers[i]))
                                    sucesso = True
                                    break
                                tentativas += 1
                            if tentativas >= 5:
                                self.log(f"ERRO: Falha após 5 tentativas em read_input_registers(addr={start_addr}, count={count})")
                
                elif active_tab == 3 and self.hr_blocks:
                    addrs_to_read = set(sorted(self.hr_map.keys())[:100])
                    for start_addr, count in self.hr_blocks:
                        if start_addr in addrs_to_read:
                            tentativas = 0
                            while tentativas < 5 and self.running:
                                self.log(f"REQ: read_holding_registers(addr={start_addr}, count={count})")
                                result = self.client.read_holding_registers(start_addr, count, unit=1)
                                if not result.isError():
                                    self.log(f"RESP: OK - {count} regs lidos")
                                    for i in range(count):
                                        addr = start_addr + i
                                        if addr in self.hr_labels:
                                            self.hr_labels[addr].config(text=str(result.registers[i]))
                                    sucesso = True
                                    break
                                tentativas += 1
                            if tentativas >= 5:
                                self.log(f"ERRO: Falha após 5 tentativas em read_holding_registers(addr={start_addr}, count={count})")
                
                if sucesso:
                    erros_consecutivos = 0
                    leituras += 1
                else:
                    erros_consecutivos += 1
                    erros += 1
                
                cycle_time = (time.time() - cycle_start) * 1000
                self.stats_label.config(text=f"Leituras: {leituras} | Erros: {erros} | Tempo: {cycle_time:.0f}ms")
                
                time.sleep(1.0)
                
            except Exception as e:
                erros += 1
                erros_consecutivos += 1
                self.log(f"Exceção: {e}")
    
    def update_coil(self, addr, value):
        canvas, led = self.coil_leds[addr]
        label = self.coil_labels[addr]
        reg = self.coils_map[addr]
        
        if value:
            canvas.itemconfig(led, fill="lime")
            label.config(text=f"{reg['nome'][:45]}: ON")
        else:
            canvas.itemconfig(led, fill="gray")
            label.config(text=f"{reg['nome'][:45]}: OFF")
    
    def update_di(self, addr, value):
        canvas, led = self.di_leds[addr]
        label = self.di_labels[addr]
        reg = self.di_map[addr]
        
        if value:
            canvas.itemconfig(led, fill="red")
            label.config(text=f"{reg['nome'][:50]}: ON", foreground="red")
        else:
            canvas.itemconfig(led, fill="gray")
            label.config(text=f"{reg['nome'][:50]}: OFF", foreground="black")
    
    def update_ir(self, addr, value):
        label = self.ir_labels[addr]
        reg = self.ir_map[addr]
        label.config(text=f"{reg['base1']:5d} - {reg['nome'][:45]} [{reg['unidade']}]: {value}")
    
    def write_coil(self, addr, value):
        if self.client:
            self.log(f"REQ: write_coil(addr={addr}, value={value})")
            result = self.client.write_coil(addr, value, unit=1)
            if result.isError():
                self.log(f"RESP: ERRO - {result}")
            else:
                self.log(f"RESP: OK")
    
    def write_hr(self, addr):
        if self.client:
            try:
                value = int(self.hr_entries[addr].get())
                self.log(f"REQ: write_register(addr={addr}, value={value})")
                result = self.client.write_register(addr, value, unit=1)
                if result.isError():
                    self.log(f"RESP: ERRO - {result}")
                else:
                    self.log(f"RESP: OK")
            except Exception as e:
                self.log(f"ERRO: {e}")
    

    
    def run(self):
        self.window.mainloop()

if __name__ == '__main__':
    app = BMSMaster()
    app.run()
