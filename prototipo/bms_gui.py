"""Interface Gráfica para controlar o BMS Slave"""
import tkinter as tk
from tkinter import ttk
from pymodbus.server.sync import StartSerialServer
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext, ModbusSequentialDataBlock
from pymodbus.transaction import ModbusRtuFramer
from threading import Thread

class BMSGui:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("🔋 Emulador BMS - Controle de Registradores")
        self.window.geometry("600x700")
        
        # Datastore compartilhado
        self.discrete_values = [0] * 10000
        self.coil_values = [0] * 100
        
        self.store = ModbusSlaveContext(
            di=ModbusSequentialDataBlock(0, self.discrete_values),
            co=ModbusSequentialDataBlock(0, self.coil_values),
            hr=ModbusSequentialDataBlock(0, [0]*100),
            ir=ModbusSequentialDataBlock(0, [0]*100)
        )
        
        self.context = ModbusServerContext(slaves=self.store, single=True)
        
        # Criar interface
        self.create_widgets()
        
        # Iniciar servidor em thread
        Thread(target=self.start_server, daemon=True).start()
    
    def create_widgets(self):
        # Frame de status
        status_frame = ttk.LabelFrame(self.window, text="Status do Servidor", padding=10)
        status_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(status_frame, text="Porta: COM16 | Baudrate: 19200 | Slave ID: 1").pack()
        ttk.Label(status_frame, text="✅ Servidor Rodando", foreground="green").pack()
        
        # Frame Coil
        coil_frame = ttk.LabelFrame(self.window, text="Coil 0 - Comando Medir Resistência", padding=10)
        coil_frame.pack(fill="x", padx=10, pady=5)
        
        coil_left = ttk.Frame(coil_frame)
        coil_left.pack(side="left", fill="x", expand=True)
        
        self.coil0_var = tk.BooleanVar()
        ttk.Checkbutton(coil_left, text="Ativar Comando", variable=self.coil0_var,
                       command=self.update_coil0).pack(side="left")
        
        # LED indicador
        self.coil_led_canvas = tk.Canvas(coil_left, width=30, height=30, bg="white")
        self.coil_led_canvas.pack(side="left", padx=10)
        self.coil_led = self.coil_led_canvas.create_oval(5, 5, 25, 25, fill="gray", outline="black")
        
        self.coil_status_label = ttk.Label(coil_left, text="Status: OFF")
        self.coil_status_label.pack(side="left", padx=5)
        
        # Iniciar monitoramento
        Thread(target=self.monitor_coil, daemon=True).start()
        
        # Frame Alarmes
        alarm_frame = ttk.LabelFrame(self.window, text="Discrete Inputs 0-15 (Alarmes 10001-10016)", padding=10)
        alarm_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Canvas com scrollbar
        canvas = tk.Canvas(alarm_frame, height=250)
        scrollbar = ttk.Scrollbar(alarm_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Criar checkboxes para alarmes
        self.alarm_vars = []
        alarmes = [
            (0, "geral"), (1, "Sens_F"), (2, "reservado"), (3, "reservado"),
            (4, "bateria"), (5, "elemento"), (6, "analog"), (7, "Din"),
            (8, "Vcc"), (9, "Ibat"), (10, "Bat_low"), (11, "Bat_life"),
            (12, "Temp_amb"), (13, "Umid"), (14, "H2"), (15, "reservado")
        ]
        
        for addr, nome in alarmes:
            var = tk.BooleanVar()
            self.alarm_vars.append(var)
            cb = ttk.Checkbutton(
                scrollable_frame,
                text=f"{addr:2d} (10{addr+1:03d}) - {nome}",
                variable=var,
                command=lambda a=addr: self.update_alarm(a)
            )
            cb.pack(anchor="w", pady=2)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Botões
        btn_frame = ttk.Frame(self.window)
        btn_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Button(btn_frame, text="Limpar Todos", command=self.clear_all).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Ativar Todos", command=self.set_all).pack(side="left", padx=5)
    
    def monitor_coil(self):
        """Monitora mudanças no coil 0"""
        import time
        last_value = 0
        while True:
            try:
                values = self.store.getValues(1, 0, 1)  # fc=1, addr=0, count=1
                current_value = values[0]
                
                if current_value != last_value:
                    # Atualizar interface
                    self.coil0_var.set(bool(current_value))
                    if current_value:
                        self.coil_led_canvas.itemconfig(self.coil_led, fill="lime")
                        self.coil_status_label.config(text="Status: ON", foreground="green")
                        print(f"⚡ Coil 0 alterado para ON (por cliente externo)")
                    else:
                        self.coil_led_canvas.itemconfig(self.coil_led, fill="gray")
                        self.coil_status_label.config(text="Status: OFF", foreground="black")
                        print(f"⚡ Coil 0 alterado para OFF (por cliente externo)")
                    last_value = current_value
                
                time.sleep(0.2)
            except:
                time.sleep(0.5)
    
    def update_coil0(self):
        value = 1 if self.coil0_var.get() else 0
        self.store.setValues(1, 0, [value])  # fc=1 (coils), address=0
        if value:
            self.coil_led_canvas.itemconfig(self.coil_led, fill="lime")
            self.coil_status_label.config(text="Status: ON", foreground="green")
        else:
            self.coil_led_canvas.itemconfig(self.coil_led, fill="gray")
            self.coil_status_label.config(text="Status: OFF", foreground="black")
        print(f"Coil 0 = {value}")
    
    def update_alarm(self, addr):
        value = 1 if self.alarm_vars[addr].get() else 0
        self.store.setValues(2, addr, [value])  # fc=2 (discrete inputs)
        print(f"Alarme {addr} (10{addr+1:03d}) = {value}")
    
    def clear_all(self):
        for i, var in enumerate(self.alarm_vars):
            var.set(False)
            self.store.setValues(2, i, [0])
        print("Todos os alarmes limpos")
    
    def set_all(self):
        for i, var in enumerate(self.alarm_vars):
            var.set(True)
            self.store.setValues(2, i, [1])
        print("Todos os alarmes ativados")
    
    def start_server(self):
        print("Servidor Modbus iniciado em COM16")
        StartSerialServer(
            self.context,
            framer=ModbusRtuFramer,
            port='COM16',
            baudrate=19200,
            bytesize=8,
            parity='N',
            stopbits=1,
            timeout=1
        )
    
    def run(self):
        self.window.mainloop()

if __name__ == '__main__':
    app = BMSGui()
    app.run()
