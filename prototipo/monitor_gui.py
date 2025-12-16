"""Monitor GUI - Cliente Modbus com LEDs em tempo real"""
import tkinter as tk
from tkinter import ttk
from pymodbus.client.sync import ModbusSerialClient
from threading import Thread
import time

class MonitorGUI:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("🔍 Monitor BMS - Cliente Modbus")
        self.window.geometry("600x550")
        
        self.client = None
        self.running = False
        
        self.create_widgets()
        
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
        
        # Frame Coil
        coil_frame = ttk.LabelFrame(self.window, text="Coil 0 - Comando Medir Resistência", padding=10)
        coil_frame.pack(fill="x", padx=10, pady=5)
        
        self.coil_canvas = tk.Canvas(coil_frame, width=30, height=30, bg="white")
        self.coil_canvas.pack(side="left", padx=5)
        self.coil_led = self.coil_canvas.create_oval(5, 5, 25, 25, fill="gray", outline="black")
        
        self.coil_label = ttk.Label(coil_frame, text="Status: OFF")
        self.coil_label.pack(side="left", padx=10)
        
        btn_coil_frame = ttk.Frame(coil_frame)
        btn_coil_frame.pack(side="right", padx=10)
        
        self.btn_cmd_on = ttk.Button(btn_coil_frame, text="Ativar", command=self.write_cmd_on, state="disabled")
        self.btn_cmd_on.pack(side="left", padx=2)
        
        self.btn_cmd_off = ttk.Button(btn_coil_frame, text="Desativar", command=self.write_cmd_off, state="disabled")
        self.btn_cmd_off.pack(side="left", padx=2)
        
        # Frame Alarmes
        alarm_frame = ttk.LabelFrame(self.window, text="Discrete Inputs 0-15 (Alarmes)", padding=10)
        alarm_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Canvas com scrollbar
        canvas = tk.Canvas(alarm_frame, height=300)
        scrollbar = ttk.Scrollbar(alarm_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Criar LEDs para alarmes
        self.alarm_leds = []
        self.alarm_labels = []
        
        alarmes = [
            (0, "geral"), (1, "Sens_F"), (2, "reservado"), (3, "reservado"),
            (4, "bateria"), (5, "elemento"), (6, "analog"), (7, "Din"),
            (8, "Vcc"), (9, "Ibat"), (10, "Bat_low"), (11, "Bat_life"),
            (12, "Temp_amb"), (13, "Umid"), (14, "H2"), (15, "reservado")
        ]
        
        for addr, nome in alarmes:
            frame = ttk.Frame(scrollable_frame)
            frame.pack(fill="x", pady=2)
            
            led_canvas = tk.Canvas(frame, width=20, height=20, bg="white")
            led_canvas.pack(side="left", padx=5)
            led = led_canvas.create_oval(3, 3, 17, 17, fill="gray", outline="black")
            self.alarm_leds.append((led_canvas, led))
            
            label = ttk.Label(frame, text=f"{addr:2d} (10{addr+1:03d}) - {nome}: OFF")
            label.pack(side="left", padx=5)
            self.alarm_labels.append(label)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Frame de estatísticas
        stats_frame = ttk.LabelFrame(self.window, text="Estatísticas", padding=10)
        stats_frame.pack(fill="x", padx=10, pady=5)
        
        self.stats_label = ttk.Label(stats_frame, text="Leituras: 0 | Erros: 0 | Taxa: 0.0 Hz")
        self.stats_label.pack()
    
    def connect(self):
        self.client = ModbusSerialClient(
            method='rtu',
            port='COM13',
            baudrate=19200,
            bytesize=8,
            parity='N',
            stopbits=1,
            timeout=3
        )
        
        if self.client.connect():
            self.status_label.config(text="🟢 Conectado", foreground="green")
            self.btn_connect.config(state="disabled")
            self.btn_disconnect.config(state="normal")
            self.btn_cmd_on.config(state="normal")
            self.btn_cmd_off.config(state="normal")
            self.running = True
            Thread(target=self.poll_loop, daemon=True).start()
        else:
            self.status_label.config(text="🔴 Erro ao conectar", foreground="red")
    
    def disconnect(self):
        self.running = False
        if self.client:
            self.client.close()
        self.status_label.config(text="⚪ Desconectado", foreground="gray")
        self.btn_connect.config(state="normal")
        self.btn_disconnect.config(state="disabled")
        self.btn_cmd_on.config(state="disabled")
        self.btn_cmd_off.config(state="disabled")
    
    def poll_loop(self):
        leituras = 0
        erros = 0
        start_time = time.time()
        
        while self.running:
            try:
                # Ler coil 0
                result = self.client.read_coils(0, 1, unit=1)
                if not result.isError():
                    self.update_coil(result.bits[0])
                else:
                    erros += 1
                    print(f"Erro lendo coil: {result}")
                
                time.sleep(0.1)  # Delay entre leituras
                
                # Ler discrete inputs 0-15
                result = self.client.read_discrete_inputs(0, 16, unit=1)
                if not result.isError():
                    self.update_alarms(result.bits[:16])
                    leituras += 1
                else:
                    erros += 1
                    print(f"Erro lendo discrete inputs: {result}")
                
                # Atualizar estatísticas
                elapsed = time.time() - start_time
                taxa = leituras / elapsed if elapsed > 0 else 0
                self.stats_label.config(text=f"Leituras: {leituras} | Erros: {erros} | Taxa: {taxa:.1f} Hz")
                
                time.sleep(1.0)  # Intervalo entre ciclos
                
            except Exception as e:
                erros += 1
                print(f"Exceção: {e}")
    
    def write_cmd_on(self):
        if self.client:
            result = self.client.write_coil(0, True, unit=1)
            if result.isError():
                print(f"Erro escrevendo coil ON: {result}")
    
    def write_cmd_off(self):
        if self.client:
            result = self.client.write_coil(0, False, unit=1)
            if result.isError():
                print(f"Erro escrevendo coil OFF: {result}")
    
    def update_coil(self, value):
        canvas, led = self.coil_canvas, self.coil_led
        if value:
            canvas.itemconfig(led, fill="lime")
            self.coil_label.config(text="Status: ON")
        else:
            canvas.itemconfig(led, fill="gray")
            self.coil_label.config(text="Status: OFF")
    
    def update_alarms(self, bits):
        for i, bit in enumerate(bits):
            canvas, led = self.alarm_leds[i]
            label = self.alarm_labels[i]
            
            if bit:
                canvas.itemconfig(led, fill="red")
                text = label.cget("text").replace("OFF", "ON")
                label.config(text=text, foreground="red")
            else:
                canvas.itemconfig(led, fill="gray")
                text = label.cget("text").replace("ON", "OFF")
                label.config(text=text, foreground="black")
    
    def run(self):
        self.window.mainloop()

if __name__ == '__main__':
    app = MonitorGUI()
    app.run()
