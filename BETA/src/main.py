"""EmuladorMODBUSRTU - Interface PyQt6 Moderna para Servidor Modbus RTU Serial"""
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                              QLabel, QPushButton, QComboBox, QLineEdit, QTabWidget, 
                              QScrollArea, QCheckBox, QGroupBox, QFileDialog, QMessageBox, QGridLayout)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont
from pymodbus.server import StartAsyncSerialServer
from pymodbus.datastore import ModbusServerContext, ModbusSlaveContext, ModbusSequentialDataBlock
from pymodbus.transaction import ModbusRtuFramer
import asyncio
from csv_parser import MemoryMapParser
from config import Config
import serial.tools.list_ports
import time
import os
import sys
import threading
import traceback

class EventDrivenDataBlock(ModbusSequentialDataBlock):
    """DataBlock com callbacks para notificação imediata de mudanças"""
    def __init__(self, address, values, callback=None):
        super().__init__(address, values)
        self.callback = callback
        self.base_address = address
    
    def setValues(self, address, values):
        super().setValues(address, values)
        if self.callback:
            # Notificar mudança imediatamente
            # address já é o endereço Modbus correto
            for i, value in enumerate(values):
                try:
                    self.callback(address + i, value)
                except Exception as e:
                    print(f"⚠️ Erro no callback addr={address+i}: {e}")

class MonitorThread(QThread):
    update_coil = pyqtSignal(int, bool)
    update_di = pyqtSignal(int, bool)
    update_ir = pyqtSignal(int, int)
    update_hr = pyqtSignal(int, int)
    
    def __init__(self, emulator):
        super().__init__()
        self.emulator = emulator
        self.running = True
    
    def run(self):
        # Thread apenas para manter compatibilidade, eventos são tratados via callback
        while self.running:
            time.sleep(1)  # Apenas mantém thread viva

    def stop(self):
        self.running = False

class ModbusEmulator(QMainWindow):
    server_error = pyqtSignal(str)  # Signal para erros da thread do servidor

    def __init__(self):
        super().__init__()
        self.setWindowTitle("📡 EmuladorMODBUSRTU v1.0.0")

        self.config = Config()
        self.csv_path = self.config.get('last_csv_path', '')
        self.coils_map = {}
        self.di_map = {}
        self.ir_map = {}
        self.hr_map = {}
        self.store = None
        self.context = None
        self.server = None
        self.server_running = False
        
        self.coil_controls = {}
        self.di_controls = {}
        self.ir_controls = {}
        self.hr_controls = {}
        
        self.server_thread = None
        self.serial_port = None  # Guardar referência da porta serial
        self.parity_map = {"None": "N", "Even": "E", "Odd": "O", "Mark": "M", "Space": "S"}
        
        # Conectar signal de erro
        self.server_error.connect(self.on_server_error)

        self.setup_ui()
        self.apply_styles()
    
    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Mapa de Memória Selection
        csv_group = QGroupBox("📄 Mapa de Memória")
        csv_layout = QHBoxLayout()
        self.csv_label = QLineEdit(self.csv_path)
        self.csv_label.setReadOnly(True)
        csv_btn = QPushButton("Selecionar...")
        csv_btn.clicked.connect(self.select_csv)
        csv_edit_btn = QPushButton("✏️ Editar Mapa")
        csv_edit_btn.clicked.connect(self.open_csv_editor)
        csv_layout.addWidget(self.csv_label)
        csv_layout.addWidget(csv_btn)
        csv_layout.addWidget(csv_edit_btn)
        csv_group.setLayout(csv_layout)
        layout.addWidget(csv_group)
        
        # Configuration
        config_group = QGroupBox("⚙️ Configuração Serial")
        config_layout = QHBoxLayout()
        
        config_layout.addWidget(QLabel("Porta:"))
        self.port_combo = QComboBox()
        self.port_combo.addItems(self.get_available_ports())
        self.port_combo.setCurrentText(self.config.get('serial_port', 'COM16'))
        config_layout.addWidget(self.port_combo)
        
        config_layout.addWidget(QLabel("Baudrate:"))
        self.baudrate_combo = QComboBox()
        self.baudrate_combo.addItems(["1200", "2400", "4800", "9600", "19200", "38400", "57600", "115200"])
        self.baudrate_combo.setCurrentText(str(self.config.get('baudrate', 19200)))
        config_layout.addWidget(self.baudrate_combo)
        
        config_layout.addWidget(QLabel("Data Bits:"))
        self.bytesize_combo = QComboBox()
        self.bytesize_combo.addItems(["5", "6", "7", "8"])
        self.bytesize_combo.setCurrentText(str(self.config.get('bytesize', 8)))
        config_layout.addWidget(self.bytesize_combo)
        
        config_layout.addWidget(QLabel("Paridade:"))
        self.parity_combo = QComboBox()
        self.parity_combo.addItems(["None", "Even", "Odd", "Mark", "Space"])
        self.parity_combo.setCurrentText(self.config.get('parity', 'None'))
        config_layout.addWidget(self.parity_combo)
        
        config_layout.addWidget(QLabel("Stop Bits:"))
        self.stopbits_combo = QComboBox()
        self.stopbits_combo.addItems(["1", "2"])
        self.stopbits_combo.setCurrentText(str(self.config.get('stopbits', 1)))
        config_layout.addWidget(self.stopbits_combo)
        
        config_layout.addWidget(QLabel("Slave ID:"))
        self.slave_id_entry = QLineEdit(str(self.config.get('slave_id', 1)))
        self.slave_id_entry.setMaximumWidth(50)
        config_layout.addWidget(self.slave_id_entry)
        
        self.btn_toggle = QPushButton("Iniciar Servidor")
        self.btn_toggle.setFixedWidth(130)
        self.btn_toggle.clicked.connect(self.toggle_server)
        config_layout.addWidget(self.btn_toggle)
        
        self.status_label = QLabel("⚪ Parado")
        self.status_label.setStyleSheet("color: gray; font-weight: bold;")
        config_layout.addWidget(self.status_label)
        
        config_layout.addStretch()
        
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        # Tabs
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        self.create_tabs()
    
    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #ffffff;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #3498db;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
            QTabWidget::pane {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
            }
            QTabBar::tab {
                background-color: #ecf0f1;
                padding: 8px 15px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #3498db;
                color: white;
            }
            QComboBox {
                background-color: white;
                border: 2px solid #bdc3c7;
                border-radius: 4px;
                padding: 5px 10px;
                padding-right: 30px;
                min-width: 80px;
            }
            QComboBox:hover {
                border: 2px solid #3498db;
            }
            QComboBox:focus {
                border: 2px solid #3498db;
            }
            QComboBox::drop-down {
                background-color: #3498db;
                border: none;
                border-top-right-radius: 4px;
                border-bottom-right-radius: 4px;
                width: 25px;
            }
            QComboBox::drop-down:hover {
                background-color: #2980b9;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid white;
                width: 0;
                height: 0;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                border: 2px solid #3498db;
                selection-background-color: #3498db;
                selection-color: white;
                outline: none;
            }
            QComboBox QAbstractItemView::item {
                padding: 5px;
                min-height: 25px;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #bdc3c7;
            }
            QLineEdit {
                padding: 5px;
                border: 1px solid #bdc3c7;
                border-radius: 3px;
            }
        """)
    
    def get_available_ports(self):
        ports = [port.device for port in serial.tools.list_ports.comports()]
        return ports if ports else ["COM16"]
    

    
    def select_csv(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Selecionar Mapa de Memória", "", "CSV files (*.csv);;All files (*.*)")
        if filename:
            self.csv_path = filename
            self.csv_label.setText(filename)
            self.config.set('last_csv_path', filename)
            self.load_csv()
    
    def open_csv_editor(self):
        from csv_editor import CSVEditor
        self.editor = CSVEditor()
        if self.csv_path and os.path.exists(self.csv_path):
            self.editor.load_csv(self.csv_path)
        # Conectar signal para recarregar CSV automaticamente quando editor fecha
        self.editor.csv_saved.connect(self.reload_csv_from_editor)
        self.editor.showMaximized()
    
    def reload_csv_from_editor(self, csv_path):
        """Recarregar CSV após edição no editor"""
        if csv_path and os.path.exists(csv_path):
            print(f"🔄 Recarregando mapa de memória: {csv_path}")
            self.load_csv()

    def load_csv(self):
        try:
            parser = MemoryMapParser(self.csv_path)
            self.coils_map, self.di_map, self.ir_map, self.hr_map = parser.parse()
            
            max_coil = max(self.coils_map.keys()) if self.coils_map else 0
            max_di = max(self.di_map.keys()) if self.di_map else 0
            max_ir = max(self.ir_map.keys()) if self.ir_map else 0
            max_hr = max(self.hr_map.keys()) if self.hr_map else 0
            
            # Criar arrays com tamanho suficiente
            coils_block = [0] * max(max_coil + 100, 1000)
            di_block = [0] * max(max_di + 100, 10000)
            ir_block = [0] * max(max_ir + 100, 10000)
            hr_block = [0] * max(max_hr + 100, 10000)
            
            # Preencher valores diretamente no índice correspondente
            for addr, reg in self.coils_map.items():
                coils_block[addr] = reg['valor_inicial']
            for addr, reg in self.di_map.items():
                di_block[addr] = reg['valor_inicial']
            for addr, reg in self.ir_map.items():
                ir_block[addr] = reg['valor_inicial']
            for addr, reg in self.hr_map.items():
                hr_block[addr] = reg['valor_inicial']
            
            # Criar DataBlocks com callbacks para event-driven updates
            self.store = ModbusSlaveContext(
                co=EventDrivenDataBlock(0, coils_block, lambda addr, val: self.on_coil_changed_callback(addr, val)),
                di=EventDrivenDataBlock(0, di_block, lambda addr, val: self.on_di_changed_callback(addr, val)),
                ir=EventDrivenDataBlock(0, ir_block, lambda addr, val: self.on_ir_changed_callback(addr, val)),
                hr=EventDrivenDataBlock(0, hr_block, lambda addr, val: self.on_hr_changed_callback(addr, val))
            )
            
            # DEBUG: Verificar valores no store após criação
            print("\n🔍 DEBUG: Verificando Store vs Array vs CSV")
            print("="*60)
            for addr in sorted(self.coils_map.keys()):
                array_val = coils_block[addr]
                csv_val = self.coils_map[addr]['valor_inicial']
                store_val = self.store.getValues(1, addr, 1)[0]
                match = "✅" if (array_val == csv_val == store_val) else "❌"
                print(f"{match} Coil {addr}: CSV={csv_val} | Array[{addr}]={array_val} | Store={store_val}")
            print("="*60 + "\n")
            
            # Contexto será recriado no start_server com Slave ID correto
            self.context = None
            self.print_memory_map()
            
            self.create_tabs()
            
            if not hasattr(self, 'monitor_thread') or not self.monitor_thread.isRunning():
                self.monitor_thread = MonitorThread(self)
                self.monitor_thread.update_coil.connect(self.on_coil_changed)
                self.monitor_thread.update_di.connect(self.on_di_changed)
                self.monitor_thread.update_ir.connect(self.on_ir_changed)
                self.monitor_thread.update_hr.connect(self.on_hr_changed)
                self.monitor_thread.start()
            
            QMessageBox.information(self, "Sucesso", f"Mapa de Memória carregado!\n\nTotal: {len(self.coils_map) + len(self.di_map) + len(self.ir_map) + len(self.hr_map)} registradores")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao carregar Mapa de Memória:\n{str(e)}")
    
    def print_memory_map(self):
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
        print(f"TOTAL: {len(self.coils_map) + len(self.di_map) + len(self.ir_map) + len(self.hr_map)}")
        print("="*80 + "\n")
    
    def create_tabs(self):
        self.tabs.clear()
        self.coil_controls.clear()
        self.di_controls.clear()
        self.ir_controls.clear()
        self.hr_controls.clear()
        
        self.create_coils_tab()
        self.create_di_tab()
        self.create_ir_tab()
        self.create_hr_tab()
    
    def create_coils_tab(self):
        scroll = QScrollArea()
        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        columns_layout = QHBoxLayout()
        columns_layout.setSpacing(20)
        sorted_addrs = sorted(self.coils_map.keys())
        items_per_col = (len(sorted_addrs) + 3) // 4
        
        for col in range(4):
            grid = QGridLayout()
            grid.setVerticalSpacing(5)
            
            start_idx = col * items_per_col
            end_idx = min(start_idx + items_per_col, len(sorted_addrs))
            
            if start_idx < len(sorted_addrs):
                lbl0 = QLabel("<b>Base0</b>")
                lbl0.setFixedWidth(60)
                grid.addWidget(lbl0, 0, 0)
                
                lbl1 = QLabel("<b>Base1</b>")
                lbl1.setFixedWidth(60)
                grid.addWidget(lbl1, 0, 1)
                
                grid.addWidget(QLabel("<b>Nome</b>"), 0, 2)
                
                lbl_val = QLabel("<b>Valor</b>")
                lbl_val.setFixedWidth(50)
                grid.addWidget(lbl_val, 0, 3)
            
            row = 1
            for addr in sorted_addrs[start_idx:end_idx]:
                reg = self.coils_map[addr]
                
                l0 = QLabel(str(addr))
                l0.setFixedWidth(60)
                grid.addWidget(l0, row, 0)
                
                l1 = QLabel(str(reg['base1']))
                l1.setFixedWidth(60)
                grid.addWidget(l1, row, 1)
                
                grid.addWidget(QLabel(reg['nome']), row, 2)
                
                # Definir estado inicial baseado no CSV
                initial_value = bool(reg['valor_inicial'])
                btn = QPushButton("ON" if initial_value else "OFF")
                btn.setCheckable(True)
                btn.setChecked(initial_value)
                btn.setMinimumHeight(24)
                btn.setFixedWidth(50)
                if initial_value:
                    btn.setStyleSheet("background-color: #27ae60; color: white;")
                else:
                    btn.setStyleSheet("background-color: #95a5a6; color: white;")
                btn.clicked.connect(lambda checked, a=addr, b=btn: self.toggle_coil(a, b, checked))
                grid.addWidget(btn, row, 3, Qt.AlignmentFlag.AlignLeft)
                self.coil_controls[addr] = btn
                row += 1
            
            col_widget = QWidget()
            col_widget.setLayout(grid)
            if col % 2 == 1:
                col_widget.setStyleSheet("background-color: #cfcfcf;")
            columns_layout.addWidget(col_widget, 1)
        
        main_layout.addLayout(columns_layout)
        scroll.setWidget(container)
        self.tabs.addTab(scroll, f"Coils (01/05) - {len(self.coils_map)}")
    
    def create_di_tab(self):
        scroll = QScrollArea()
        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        columns_layout = QHBoxLayout()
        columns_layout.setSpacing(20)
        sorted_addrs = sorted(self.di_map.keys())
        items_per_col = (len(sorted_addrs) + 3) // 4
        
        for col in range(4):
            grid = QGridLayout()
            grid.setVerticalSpacing(5)
            
            start_idx = col * items_per_col
            end_idx = min(start_idx + items_per_col, len(sorted_addrs))
            
            if start_idx < len(sorted_addrs):
                lbl0 = QLabel("<b>Base0</b>")
                lbl0.setFixedWidth(60)
                grid.addWidget(lbl0, 0, 0)
                
                lbl1 = QLabel("<b>Base1</b>")
                lbl1.setFixedWidth(60)
                grid.addWidget(lbl1, 0, 1)
                
                grid.addWidget(QLabel("<b>Nome</b>"), 0, 2)
                
                lbl_val = QLabel("<b>Valor</b>")
                lbl_val.setFixedWidth(50)
                grid.addWidget(lbl_val, 0, 3)
            
            row = 1
            for addr in sorted_addrs[start_idx:end_idx]:
                reg = self.di_map[addr]
                
                l0 = QLabel(str(addr))
                l0.setFixedWidth(60)
                grid.addWidget(l0, row, 0)
                
                l1 = QLabel(str(reg['base1']))
                l1.setFixedWidth(60)
                grid.addWidget(l1, row, 1)
                
                grid.addWidget(QLabel(reg['nome']), row, 2)
                
                btn = QPushButton("OFF")
                btn.setCheckable(True)
                btn.setMinimumHeight(24)
                btn.setFixedWidth(50)
                # Definir estado inicial baseado no CSV
                initial_value = bool(reg['valor_inicial'])
                btn.setChecked(initial_value)
                if initial_value:
                    btn.setText("ON")
                    btn.setStyleSheet("background-color: #27ae60; color: white;")
                else:
                    btn.setText("OFF")
                    btn.setStyleSheet("background-color: #95a5a6; color: white;")
                btn.clicked.connect(lambda checked, a=addr, b=btn: self.toggle_di(a, b, checked))
                grid.addWidget(btn, row, 3, Qt.AlignmentFlag.AlignLeft)
                self.di_controls[addr] = btn
                row += 1
            
            col_widget = QWidget()
            col_widget.setLayout(grid)
            if col % 2 == 1:
                col_widget.setStyleSheet("background-color: #cfcfcf;")
            columns_layout.addWidget(col_widget, 1)
        
        main_layout.addLayout(columns_layout)
        scroll.setWidget(container)
        self.tabs.addTab(scroll, f"Discrete Inputs (02) - {len(self.di_map)}")
    
    def create_ir_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        columns_layout = QHBoxLayout()
        columns_layout.setSpacing(5)
        sorted_addrs = sorted(self.ir_map.keys())
        items_per_col = (len(sorted_addrs) + 2) // 3
        
        for col in range(3):
            grid = QGridLayout()
            grid.setVerticalSpacing(3)
            grid.setColumnStretch(2, 1)
            
            start_idx = col * items_per_col
            end_idx = min(start_idx + items_per_col, len(sorted_addrs))
            
            if start_idx < len(sorted_addrs):
                lbl0 = QLabel("<b>Base0</b>")
                lbl0.setFixedWidth(60)
                grid.addWidget(lbl0, 0, 0)
                
                lbl1 = QLabel("<b>Base1</b>")
                lbl1.setFixedWidth(60)
                grid.addWidget(lbl1, 0, 1)
                
                grid.addWidget(QLabel("<b>Nome</b>"), 0, 2)
                
                lbl_val = QLabel("<b>Valor</b>")
                lbl_val.setFixedWidth(60)
                grid.addWidget(lbl_val, 0, 3)
                
                lbl_unit = QLabel("<b>Unidade</b>")
                lbl_unit.setFixedWidth(70)
                grid.addWidget(lbl_unit, 0, 4)
            
            row = 1
            for addr in sorted_addrs[start_idx:end_idx]:
                reg = self.ir_map[addr]
                
                l0 = QLabel(str(addr))
                l0.setFixedWidth(60)
                grid.addWidget(l0, row, 0)
                
                l1 = QLabel(str(reg['base1']))
                l1.setFixedWidth(60)
                grid.addWidget(l1, row, 1)
                
                grid.addWidget(QLabel(reg['nome']), row, 2)
                
                entry = QLineEdit(str(reg['valor_inicial']))
                entry.setMinimumHeight(24)
                entry.setFixedWidth(60)
                entry.setStyleSheet("background-color: white;")
                entry.editingFinished.connect(lambda a=addr, e=entry: self.update_ir(a, e.text()))
                grid.addWidget(entry, row, 3)
                
                l_unit = QLabel(reg['unidade'])
                l_unit.setFixedWidth(70)
                grid.addWidget(l_unit, row, 4)
                self.ir_controls[addr] = entry
                row += 1
            
            col_widget = QWidget()
            col_widget.setLayout(grid)
            if col % 2 == 1:
                col_widget.setStyleSheet("background-color: #cfcfcf;")
            columns_layout.addWidget(col_widget, 1)
        
        main_layout.addLayout(columns_layout)
        scroll.setWidget(container)
        self.tabs.addTab(scroll, f"Input Registers (04) - {len(self.ir_map)}")
    
    def create_hr_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        columns_layout = QHBoxLayout()
        columns_layout.setSpacing(5)
        sorted_addrs = sorted(self.hr_map.keys())
        items_per_col = (len(sorted_addrs) + 2) // 3
        
        for col in range(3):
            grid = QGridLayout()
            grid.setVerticalSpacing(3)
            grid.setColumnStretch(2, 1)
            
            start_idx = col * items_per_col
            end_idx = min(start_idx + items_per_col, len(sorted_addrs))
            
            if start_idx < len(sorted_addrs):
                lbl0 = QLabel("<b>Base0</b>")
                lbl0.setFixedWidth(60)
                grid.addWidget(lbl0, 0, 0)
                
                lbl1 = QLabel("<b>Base1</b>")
                lbl1.setFixedWidth(60)
                grid.addWidget(lbl1, 0, 1)
                
                grid.addWidget(QLabel("<b>Nome</b>"), 0, 2)
                
                lbl_val = QLabel("<b>Valor</b>")
                lbl_val.setFixedWidth(60)
                grid.addWidget(lbl_val, 0, 3)
                
                lbl_unit = QLabel("<b>Unidade</b>")
                lbl_unit.setFixedWidth(70)
                grid.addWidget(lbl_unit, 0, 4)
            
            row = 1
            for addr in sorted_addrs[start_idx:end_idx]:
                reg = self.hr_map[addr]
                
                l0 = QLabel(str(addr))
                l0.setFixedWidth(60)
                grid.addWidget(l0, row, 0)
                
                l1 = QLabel(str(reg['base1']))
                l1.setFixedWidth(60)
                grid.addWidget(l1, row, 1)
                
                grid.addWidget(QLabel(reg['nome']), row, 2)
                
                entry = QLineEdit(str(reg['valor_inicial']))
                entry.setMinimumHeight(24)
                entry.setFixedWidth(60)
                entry.setStyleSheet("background-color: white;")
                entry.editingFinished.connect(lambda a=addr, e=entry: self.update_hr(a, e.text()))
                grid.addWidget(entry, row, 3)
                
                l_unit = QLabel(reg['unidade'])
                l_unit.setFixedWidth(70)
                grid.addWidget(l_unit, row, 4)
                self.hr_controls[addr] = entry
                row += 1
            
            col_widget = QWidget()
            col_widget.setLayout(grid)
            if col % 2 == 1:
                col_widget.setStyleSheet("QWidget { background-color: #cfcfcf; } QLineEdit { background-color: white; }")
            columns_layout.addWidget(col_widget, 1)
        
        main_layout.addLayout(columns_layout)
        scroll.setWidget(container)
        self.tabs.addTab(scroll, f"Holding Registers (03/06/16) - {len(self.hr_map)}")
    
    def toggle_coil(self, addr, btn, checked):
        if checked:
            btn.setText("ON")
            btn.setStyleSheet("background-color: #27ae60; color: white;")
        else:
            btn.setText("OFF")
            btn.setStyleSheet("background-color: #95a5a6; color: white;")
        if self.store:
            self.store.setValues(1, addr, [1 if checked else 0])
    
    def toggle_di(self, addr, btn, checked):
        if checked:
            btn.setText("ON")
            btn.setStyleSheet("background-color: #27ae60; color: white;")
        else:
            btn.setText("OFF")
            btn.setStyleSheet("background-color: #95a5a6; color: white;")
        if self.store:
            self.store.setValues(2, addr, [1 if checked else 0])
    
    def update_ir(self, addr, value):
        try:
            if self.store:
                self.store.setValues(4, addr, [int(value)])
        except:
            pass
    
    def update_hr(self, addr, value):
        try:
            if self.store:
                self.store.setValues(3, addr, [int(value)])
        except:
            pass
    
    def on_coil_changed_callback(self, addr, value):
        """Callback chamado imediatamente quando coil muda (event-driven)"""
        # ModbusSequentialDataBlock adiciona +1 internamente, compensar
        real_addr = addr - 1
        if hasattr(self, 'monitor_thread'):
            self.monitor_thread.update_coil.emit(real_addr, bool(value))
    
    def on_di_changed_callback(self, addr, value):
        """Callback chamado imediatamente quando discrete input muda"""
        real_addr = addr - 1
        if hasattr(self, 'monitor_thread'):
            self.monitor_thread.update_di.emit(real_addr, bool(value))
    
    def on_ir_changed_callback(self, addr, value):
        """Callback chamado imediatamente quando input register muda"""
        real_addr = addr - 1
        if hasattr(self, 'monitor_thread'):
            self.monitor_thread.update_ir.emit(real_addr, int(value))
    
    def on_hr_changed_callback(self, addr, value):
        """Callback chamado imediatamente quando holding register muda"""
        real_addr = addr - 1
        if hasattr(self, 'monitor_thread'):
            self.monitor_thread.update_hr.emit(real_addr, int(value))
    
    def on_coil_changed(self, addr, value):
        if addr in self.coil_controls:
            btn = self.coil_controls[addr]
            btn.blockSignals(True)
            btn.setChecked(value)
            if value:
                btn.setText("ON")
                btn.setStyleSheet("background-color: #27ae60; color: white;")
            else:
                btn.setText("OFF")
                btn.setStyleSheet("background-color: #95a5a6; color: white;")
            btn.blockSignals(False)
    
    def on_di_changed(self, addr, value):
        if addr in self.di_controls:
            btn = self.di_controls[addr]
            btn.blockSignals(True)
            btn.setChecked(value)
            if value:
                btn.setText("ON")
                btn.setStyleSheet("background-color: #27ae60; color: white;")
            else:
                btn.setText("OFF")
                btn.setStyleSheet("background-color: #95a5a6; color: white;")
            btn.blockSignals(False)
    
    def on_ir_changed(self, addr, value):
        if addr in self.ir_controls:
            entry = self.ir_controls[addr]
            if not entry.hasFocus():
                entry.blockSignals(True)
                entry.setText(str(value))
                entry.blockSignals(False)
    
    def on_hr_changed(self, addr, value):
        if addr in self.hr_controls:
            entry = self.hr_controls[addr]
            if not entry.hasFocus():
                entry.blockSignals(True)
                entry.setText(str(value))
                entry.blockSignals(False)
    
    def toggle_server(self):
        if self.server_running:
            self.stop_server()
        else:
            self.start_server()
    
    def start_server(self):
        if self.server_running:
            return
        
        if not self.store:
            QMessageBox.warning(self, "Aviso", "Carregue um Mapa de Memória antes de iniciar o servidor")
            return
        
        port = self.port_combo.currentText()
        baudrate = int(self.baudrate_combo.currentText())
        bytesize = int(self.bytesize_combo.currentText())
        parity = self.parity_map[self.parity_combo.currentText()]
        stopbits = int(self.stopbits_combo.currentText())
        
        try:
            slave_id = int(self.slave_id_entry.text())
            if slave_id < 1 or slave_id > 247:
                QMessageBox.warning(self, "Aviso", "Slave ID deve estar entre 1 e 247")
                return
        except ValueError:
            QMessageBox.warning(self, "Aviso", "Slave ID inválido")
            return
        
        available_ports = self.get_available_ports()
        if port not in available_ports:
            QMessageBox.critical(self, "Erro", f"Porta {port} não disponível!\n\nPortas: {', '.join(available_ports)}")
            return
        
        # Testar abertura da porta ANTES de qualquer coisa
        import serial
        try:
            print(f"🔍 Testando porta {port}...")
            
            # Tentar abrir/fechar 3 vezes com intervalo (força liberação)
            for attempt in range(3):
                try:
                    test_serial = serial.Serial(
                        port=port,
                        baudrate=baudrate,
                        bytesize=bytesize,
                        parity=parity,
                        stopbits=stopbits,
                        timeout=1
                    )
                    test_serial.close()
                    time.sleep(0.5)
                    print(f"✅ Porta {port} disponível (tentativa {attempt+1})")
                    break
                except serial.SerialException as e:
                    if attempt < 2:
                        print(f"⚠️ Tentativa {attempt+1} falhou, aguardando...")
                        time.sleep(2)
                    else:
                        raise
        except serial.SerialException as se:
            error_msg = f"Porta {port} ainda está em uso após 3 tentativas.\n\nAguarde mais alguns segundos e tente novamente.\n\nDetalhes: {str(se)}"
            QMessageBox.critical(self, "Porta Serial em Uso", error_msg)
            print(f"❌ {error_msg}")
            return
        except Exception as pe:
            error_msg = f"Erro ao acessar porta {port}: {str(pe)}"
            QMessageBox.critical(self, "Erro de Porta Serial", error_msg)
            print(f"❌ {error_msg}")
            return
        
        try:
            # Criar contexto com Slave ID específico e suporte a broadcast
            self.context = ModbusServerContext(slaves={
                slave_id: self.store,  # Slave específico
                0: self.store          # Broadcast (ID 0)
            }, single=False)
            
            # Criar e iniciar servidor async
            self.server_ready = threading.Event()
            
            async def create_and_run_server():
                self.server = await StartAsyncSerialServer(
                    context=self.context,
                    framer=ModbusRtuFramer,
                    port=port,
                    baudrate=baudrate,
                    bytesize=bytesize,
                    parity=parity,
                    stopbits=stopbits,
                    timeout=1
                )
                # Guardar referência da porta serial para fechar depois
                try:
                    if hasattr(self.server, 'protocol') and hasattr(self.server.protocol, 'transport'):
                        if hasattr(self.server.protocol.transport, '_serial'):
                            self.serial_port = self.server.protocol.transport._serial
                            print(f"🔗 Referência da porta serial capturada")
                except Exception as e:
                    print(f"⚠️ Não foi possível capturar porta: {e}")
                
                self.server_ready.set()
                # Manter servidor rodando
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
            
            self.server_thread = threading.Thread(
                target=run_async_server,
                daemon=True
            )
            self.server_thread.start()
            
            # Aguardar servidor iniciar (não bloqueia se demorar)
            self.server_ready.wait(timeout=1)
            
            self.server_running = True
            self.port_combo.setEnabled(False)
            self.baudrate_combo.setEnabled(False)
            self.bytesize_combo.setEnabled(False)
            self.parity_combo.setEnabled(False)
            self.stopbits_combo.setEnabled(False)
            self.slave_id_entry.setEnabled(False)
            self.status_label.setText(f"🟢 Rodando (ID {slave_id})")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
            self.btn_toggle.setText("Parar Servidor")
            print(f"🚀 Servidor iniciado em {port} @ {baudrate} bps | Slave ID: {slave_id} (Broadcast: ON)")
            
            # Salvar configurações
            self.config.update(
                serial_port=port,
                baudrate=baudrate,
                bytesize=bytesize,
                parity=self.parity_combo.currentText(),
                stopbits=stopbits,
                slave_id=slave_id
            )
        except Exception as e:
            error_msg = str(e)
            QMessageBox.critical(self, "Erro ao iniciar servidor", f"Falha ao iniciar:\n\n{error_msg}")
            print(f"❌ Erro ao iniciar servidor: {error_msg}")
            # Reverter estado
            self.server_running = False
            self.port_combo.setEnabled(True)
            self.baudrate_combo.setEnabled(True)
            self.bytesize_combo.setEnabled(True)
            self.parity_combo.setEnabled(True)
            self.stopbits_combo.setEnabled(True)
            self.slave_id_entry.setEnabled(True)
            # Limpar recursos
            if hasattr(self, 'server') and self.server:
                try:
                    self.server.server_close()
                except:
                    pass
            self.server = None
            self.server_thread = None
            self.server_loop = None

    def on_server_error_callback(self, error_msg):
        """Callback chamado quando há erro na thread do servidor"""
        self.server_error.emit(error_msg)

    def on_server_error(self, error_msg):
        """Slot conectado ao signal de erro - executa na thread principal"""
        self.stop_server()
        QMessageBox.critical(self, "Erro do Servidor Modbus", f"O servidor foi interrompido:\n\n{error_msg}")

    def stop_server(self):
        if not self.server_running:
            return
        
        print("🛑 Parando servidor...")
        
        try:
            # 1. FECHAR PORTA SERIAL DIRETAMENTE (força bruta!)
            if hasattr(self, 'serial_port') and self.serial_port:
                try:
                    if hasattr(self.serial_port, 'is_open') and self.serial_port.is_open:
                        self.serial_port.close()
                        print("🔨 Porta serial fechada na força!")
                except Exception as e:
                    print(f"⚠️ Erro ao fechar porta: {e}")
            
            # 2. Parar loop asyncio
            if hasattr(self, 'server_loop') and self.server_loop:
                try:
                    if self.server_loop.is_running():
                        self.server_loop.call_soon_threadsafe(self.server_loop.stop)
                        print("⏸️ Loop asyncio parado")
                except Exception as e:
                    print(f"⚠️ Erro ao parar loop: {e}")
            
            # 3. Aguardar thread encerrar (aumentado timeout)
            if self.server_thread and self.server_thread.is_alive():
                self.server_thread.join(timeout=3)
                if self.server_thread.is_alive():
                    print("⚠️ Thread ainda viva após 3s!")
                else:
                    print("🧵 Thread encerrada")
            
            # 4. Fechar servidor Modbus
            if hasattr(self, 'server') and self.server:
                try:
                    self.server.server_close()
                    print("📡 Servidor Modbus fechado")
                except Exception as e:
                    print(f"⚠️ Erro ao fechar servidor: {e}")
            
            # 5. Limpar referências
            self.server = None
            self.server_thread = None
            self.server_loop = None
            self.serial_port = None
            
        except Exception as e:
            print(f"⚠️ Erro ao parar servidor: {e}")

        self.server_running = False
        self.port_combo.setEnabled(True)
        self.baudrate_combo.setEnabled(True)
        self.bytesize_combo.setEnabled(True)
        self.parity_combo.setEnabled(True)
        self.stopbits_combo.setEnabled(True)
        self.slave_id_entry.setEnabled(True)
        self.status_label.setText("⚪ Parado")
        self.status_label.setStyleSheet("color: gray; font-weight: bold;")
        self.btn_toggle.setText("Iniciar Servidor")
        
        # DESABILITAR BOTÃO POR 8 SEGUNDOS (Windows + pymodbus precisam liberar)
        self.btn_toggle.setEnabled(False)
        self.status_label.setText("⏳ Aguardando liberar porta...")
        self.status_label.setStyleSheet("color: orange; font-weight: bold;")
        print("⏳ Aguardando 8s para Windows liberar porta...")
        
        # Reabilitar botão após 8 segundos
        QTimer.singleShot(8000, self.enable_start_button)
    
    def enable_start_button(self):
        """Reabilita botão após Windows liberar porta"""
        # Forçar garbage collection para liberar recursos
        import gc
        gc.collect()
        
        self.btn_toggle.setEnabled(True)
        self.status_label.setText("⚪ Parado")
        self.status_label.setStyleSheet("color: gray; font-weight: bold;")
        print("✅ Porta liberada - pode iniciar novamente")
        print("⏹ Servidor parado")
    
    def closeEvent(self, event):
        try:
            # Parar servidor primeiro
            if self.server_running:
                self.stop_server()

            # Parar monitor thread
            if hasattr(self, 'monitor_thread') and self.monitor_thread:
                self.monitor_thread.stop()
                self.monitor_thread.wait(2000)  # Aguardar até 2 segundos
        except Exception as e:
            print(f"⚠️ Erro ao fechar aplicação: {e}")
        finally:
            event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ModbusEmulator()
    window.showMaximized()
    
    if window.csv_path and os.path.exists(window.csv_path):
        window.load_csv()
    else:
        QMessageBox.information(window, "Bem-vindo", "Selecione um Mapa de Memória para começar")
    
    sys.exit(app.exec())
