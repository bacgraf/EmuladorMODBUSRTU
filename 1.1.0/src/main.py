"""EmuladorMODBUSRTU - Interface PyQt6 Moderna para Servidor Modbus RTU Serial"""
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                              QLabel, QPushButton, QComboBox, QLineEdit, QTabWidget, 
                              QScrollArea, QCheckBox, QGroupBox, QFileDialog, QMessageBox, QGridLayout)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QIcon
from csv_parser import MemoryMapParser
from config import Config
from splash import SplashScreen
from modbus_server_multiprocess import ModbusServerMultiprocess as ModbusServer
import serial.tools.list_ports
import multiprocessing as mp
import time
import os
import sys

class ModbusEmulator(QMainWindow):
    server_error = pyqtSignal(str)  # Signal para erros da thread do servidor

    def __init__(self):
        super().__init__()
        self.setWindowTitle("📡 EmuladorMODBUSRTU v1.0.0")
        
        # Definir ícone da janela
        if getattr(sys, 'frozen', False):
            icon_path = os.path.join(sys._MEIPASS, 'icon.png')
        else:
            icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'icon.png')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.config = Config()
        self.csv_path = self.config.get('last_csv_path', '')
        self.coils_map = {}
        self.di_map = {}
        self.ir_map = {}
        self.hr_map = {}
        self.modbus = ModbusServer()
        self.server_running = False
        
        self.coil_controls = {}
        self.di_controls = {}
        self.ir_controls = {}
        self.hr_controls = {}
        
        self.parity_map = {"None": "N", "Even": "E", "Odd": "O", "Mark": "M", "Space": "S"}
        
        
        # Conectar signal de erro
        self.server_error.connect(self.on_server_error)
        
        # Monitoramento de porta
        self.port_check_timer = None
        self.port_check_count = 0
        self.port_check_start = None
        self.port_check_port = None
        self.port_check_baudrate = None
        
        # Polling timer para atualizar UI via shared memory
        self.polling_timer = QTimer()
        self.polling_timer.timeout.connect(self.poll_shared_memory)
        self.last_values = {'coils': {}, 'di': {}, 'ir': {}, 'hr': {}}

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
        
        # ComboBox customizado que atualiza ao abrir
        class RefreshComboBox(QComboBox):
            def showPopup(self):
                parent = self.parent()
                while parent and not hasattr(parent, 'refresh_ports'):
                    parent = parent.parent()
                if parent:
                    parent.refresh_ports()
                super().showPopup()
        
        self.port_combo = RefreshComboBox()
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
        
        # Legenda de permissões
        legend_layout = QHBoxLayout()
        legend_layout.addStretch()
        legend_r = QLabel("🔵 R (Somente Leitura)")
        legend_r.setStyleSheet("color: #2196F3; font-weight: bold;")
        legend_layout.addWidget(legend_r)
        legend_layout.addWidget(QLabel(" | "))
        legend_rw = QLabel("🟢 R/W (Leitura/Escrita)")
        legend_rw.setStyleSheet("color: #4CAF50; font-weight: bold;")
        legend_layout.addWidget(legend_rw)
        legend_layout.addWidget(QLabel(" | "))
        legend_rwb = QLabel("🟡 R/W/B (Leitura/Escrita/Broadcast)")
        legend_rwb.setStyleSheet("color: #FBC02D; font-weight: bold;")
        legend_layout.addWidget(legend_rwb)
        legend_layout.addStretch()
        layout.addLayout(legend_layout)
        
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
    
    def refresh_ports(self):
        """Atualiza lista de portas COM ao abrir dropdown"""
        current = self.port_combo.currentText()
        self.port_combo.blockSignals(True)
        self.port_combo.clear()
        self.port_combo.addItems(self.get_available_ports())
        
        # Restaurar seleção anterior se ainda existir
        idx = self.port_combo.findText(current)
        if idx >= 0:
            self.port_combo.setCurrentIndex(idx)
        
        self.port_combo.blockSignals(False)
    

    
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
            
            # Extrair permissões dos mapas com offset +1
            coils_perm = {addr + 1: reg.get('permissao', 'R/W') for addr, reg in self.coils_map.items()}
            di_perm = {addr + 1: reg.get('permissao', 'R') for addr, reg in self.di_map.items()}
            ir_perm = {addr + 1: reg.get('permissao', 'R') for addr, reg in self.ir_map.items()}
            hr_perm = {addr + 1: reg.get('permissao', 'R/W') for addr, reg in self.hr_map.items()}
            
            # Criar datastore com permissões
            self.modbus.create_datastore(
                coils_block, di_block, ir_block, hr_block,
                None, None, None, None,
                coils_perm, di_perm, ir_perm, hr_perm
            )
            
            self.print_memory_map()
            
            self.create_tabs()
            
            QMessageBox.information(self, "Sucesso", f"Mapa de Memória carregado!\n\nTotal: {len(self.coils_map) + len(self.di_map) + len(self.ir_map) + len(self.hr_map)} registradores")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao carregar Mapa de Memória:\n{str(e)}")
    
    def print_memory_map(self):
        # LOG DETALHADO - Descomente para debug
        pass
        # print("\n" + "="*80)
        # print("MAPA DE MEMÓRIA COMPLETO")
        # print("="*80)
        # 
        # print(f"\n[COILS - Função 01/05] Total: {len(self.coils_map)}")
        # print("-" * 80)
        # for addr in sorted(self.coils_map.keys()):
        #     reg = self.coils_map[addr]
        #     print(f"  Base0: {addr:5d} | Base1: {reg['base1']:5d} | Hex: 0x{addr:04X} | {reg['nome'][:45]:45s} | Val: {reg['valor_inicial']}")
        # 
        # print(f"\n[DISCRETE INPUTS - Função 02] Total: {len(self.di_map)}")
        # print("-" * 80)
        # for addr in sorted(self.di_map.keys()):
        #     reg = self.di_map[addr]
        #     print(f"  Base0: {addr:5d} | Base1: {reg['base1']:5d} | Hex: 0x{addr:04X} | {reg['nome'][:45]:45s} | Val: {reg['valor_inicial']}")
        # 
        # print(f"\n[INPUT REGISTERS - Função 04] Total: {len(self.ir_map)}")
        # print("-" * 80)
        # for addr in sorted(self.ir_map.keys()):
        #     reg = self.ir_map[addr]
        #     print(f"  Base0: {addr:5d} | Base1: {reg['base1']:5d} | Hex: 0x{addr:04X} | {reg['nome'][:35]:35s} | {reg['unidade']:8s} | Val: {reg['valor_inicial']}")
        # 
        # print(f"\n[HOLDING REGISTERS - Função 03/06/16] Total: {len(self.hr_map)}")
        # print("-" * 80)
        # for addr in sorted(self.hr_map.keys()):
        #     reg = self.hr_map[addr]
        #     print(f"  Base0: {addr:5d} | Base1: {reg['base1']:5d} | Hex: 0x{addr:04X} | {reg['nome'][:35]:35s} | {reg['unidade']:8s} | Val: {reg['valor_inicial']}")
        # 
        # print("\n" + "="*80)
        # print(f"TOTAL: {len(self.coils_map) + len(self.di_map) + len(self.ir_map) + len(self.hr_map)}")
        # print("="*80 + "\n")
    
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
                
                nome_label = QLabel(reg['nome'])
                permissao = reg.get('permissao', 'R').upper()
                if 'B' in permissao:
                    nome_label.setStyleSheet("background-color: #FFF9C4; padding: 2px;")
                elif 'W' in permissao:
                    nome_label.setStyleSheet("background-color: #C8E6C9; padding: 2px;")
                else:
                    nome_label.setStyleSheet("background-color: #BBDEFB; padding: 2px;")
                grid.addWidget(nome_label, row, 2)
                
                entry = QLineEdit(str(reg['valor_inicial']))
                entry.setMinimumHeight(24)
                entry.setFixedWidth(60)
                entry.setStyleSheet("background-color: white;")
                entry.textChanged.connect(lambda text, e=entry: e.setText(text.replace(',', '.')) if ',' in text else None)
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
                
                nome_label = QLabel(reg['nome'])
                permissao = reg.get('permissao', 'R').upper()
                if 'B' in permissao:
                    nome_label.setStyleSheet("background-color: #FFF9C4; padding: 2px;")
                elif 'W' in permissao:
                    nome_label.setStyleSheet("background-color: #C8E6C9; padding: 2px;")
                else:
                    nome_label.setStyleSheet("background-color: #BBDEFB; padding: 2px;")
                grid.addWidget(nome_label, row, 2)
                
                entry = QLineEdit(str(reg['valor_inicial']))
                entry.setMinimumHeight(24)
                entry.setFixedWidth(60)
                entry.setStyleSheet("background-color: white;")
                entry.textChanged.connect(lambda text, e=entry: e.setText(text.replace(',', '.')) if ',' in text else None)
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
        
        reg_name = self.coils_map[addr]['nome']
        # print(f"\n👉 [UI CLICK] Clicou em COIL Base0={addr} ({reg_name}) → Enviando valor {1 if checked else 0} para endereço {addr}")
        
        self.modbus.set_value(1, addr + 1, 1 if checked else 0)
    
    def toggle_di(self, addr, btn, checked):
        if checked:
            btn.setText("ON")
            btn.setStyleSheet("background-color: #27ae60; color: white;")
        else:
            btn.setText("OFF")
            btn.setStyleSheet("background-color: #95a5a6; color: white;")
        
        reg_name = self.di_map[addr]['nome']
        # print(f"\n👉 [UI CLICK] Clicou em DI Base0={addr} ({reg_name}) → Enviando valor {1 if checked else 0} para endereço {addr}")
        
        self.modbus.set_value(2, addr + 1, 1 if checked else 0)
    
    def update_ir(self, addr, value):
        try:
            reg_name = self.ir_map[addr]['nome']
            resolucao = float(self.ir_map[addr].get('resolucao', 1))
            value = value.replace(',', '.')
            valor_modbus = int(float(value) / resolucao)
            # print(f"\n👉 [UI CLICK] Editou IR Base0={addr} ({reg_name}) → Valor real: {value}, Modbus: {valor_modbus} (res={resolucao})")
            self.modbus.set_value(4, addr + 1, valor_modbus)
        except:
            pass
    
    def update_hr(self, addr, value):
        try:
            reg_name = self.hr_map[addr]['nome']
            resolucao = float(self.hr_map[addr].get('resolucao', 1))
            value = value.replace(',', '.')
            valor_modbus = int(float(value) / resolucao)
            # print(f"\n👉 [UI CLICK] Editou HR Base0={addr} ({reg_name}) → Valor real: {value}, Modbus: {valor_modbus} (res={resolucao})")
            self.modbus.set_value(3, addr + 1, valor_modbus)
        except:
            pass
    
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
                resolucao = float(self.ir_map[addr].get('resolucao', 1))
                valor_real = value * resolucao
                entry.blockSignals(True)
                entry.setText(str(valor_real))
                entry.blockSignals(False)
    
    def on_hr_changed(self, addr, value):
        if addr in self.hr_controls:
            entry = self.hr_controls[addr]
            if not entry.hasFocus():
                resolucao = float(self.hr_map[addr].get('resolucao', 1))
                valor_real = value * resolucao
                entry.blockSignals(True)
                entry.setText(str(valor_real))
                entry.blockSignals(False)
    
    def toggle_server(self):
        if self.server_running:
            self.stop_server()
        else:
            self.start_server()
    
    def start_server(self):
        if self.server_running:
            return
        
        if not self.modbus.store:
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
        
        # Iniciar servidor usando módulo
        success, message = self.modbus.start(port, baudrate, bytesize, parity, stopbits, slave_id)
        
        if success:
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
            print(message)
            
            # Salvar configurações
            self.config.update(
                serial_port=port,
                baudrate=baudrate,
                bytesize=bytesize,
                parity=self.parity_combo.currentText(),
                stopbits=stopbits,
                slave_id=slave_id
            )
            
            # Iniciar polling para atualizar UI (multiprocessing não tem callbacks)
            # print("🔄 Iniciando polling de shared memory (100ms)...")
            self.polling_timer.start(100)  # A cada 100ms
        else:
            QMessageBox.critical(self, "Erro", f"Falha ao iniciar servidor:\n\n{message}")
            print(f"❌ {message}")

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
        
        from datetime import datetime
        import serial
        
        print("\n" + "="*80)
        print(f"🛑 PARANDO SERVIDOR - {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
        print("="*80)
        
        try:
            print("🛑 Chamando modbus.stop()...")
            self.modbus.stop()
            print("✅ modbus.stop() concluído")
            
            # Parar polling
            if self.polling_timer.isActive():
                self.polling_timer.stop()
                print("⏸️ Polling parado")
            
            self.server_running = False
            self.port_combo.setEnabled(True)
            self.baudrate_combo.setEnabled(True)
            self.bytesize_combo.setEnabled(True)
            self.parity_combo.setEnabled(True)
            self.stopbits_combo.setEnabled(True)
            self.slave_id_entry.setEnabled(True)
            self.btn_toggle.setText("Iniciar Servidor")
            self.btn_toggle.setEnabled(False)  # Desabilitar até porta liberar
            
            # Iniciar monitoramento de porta
            port = self.port_combo.currentText()
            baudrate = int(self.baudrate_combo.currentText())
            
            self.port_check_count = 0
            self.port_check_start = datetime.now()
            self.port_check_port = port
            self.port_check_baudrate = baudrate
            
            self.status_label.setText("⏳ Aguardando porta liberar...")
            self.status_label.setStyleSheet("color: orange; font-weight: bold;")
            
            print("\n🔍 Iniciando monitoramento de porta (timeout: 2min)...")
            print(f"🔍 Testando {port} a cada 1 segundo\n")
            
            # Timer para verificar porta a cada 1 segundo
            self.port_check_timer = QTimer()
            self.port_check_timer.timeout.connect(self.check_port_released)
            self.port_check_timer.start(1000)  # 1 segundo
            
        except Exception as e:
            print(f"❌ Erro ao parar servidor: {e}")
            self.server_running = False
            self.btn_toggle.setEnabled(True)
    
    def check_port_released(self):
        """Verifica se porta foi liberada"""
        from datetime import datetime
        import serial
        
        self.port_check_count += 1
        elapsed = (datetime.now() - self.port_check_start).total_seconds()
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        
        # Timeout de 2 minutos (120 segundos)
        if elapsed > 120:
            self.port_check_timer.stop()
            print(f"\n[{timestamp}] +{elapsed:6.2f}s | ⏱️ TIMEOUT (2 minutos)")
            print("\n" + "="*80)
            print("❌ PORTA NÃO LIBEROU EM 2 MINUTOS - Forçando habilitação do botão")
            print("="*80 + "\n")
            
            self.btn_toggle.setEnabled(True)
            self.status_label.setText("❌ Porta travada - Tente novamente")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            return
        
        # Tentar abrir porta
        try:
            test_serial = serial.Serial(
                port=self.port_check_port,
                baudrate=self.port_check_baudrate,
                timeout=0.1
            )
            test_serial.close()
            
            # SUCESSO! Porta está livre
            self.port_check_timer.stop()
            print(f"[{timestamp}] +{elapsed:6.2f}s | ✅ PORTA LIVRE!")
            print("\n" + "="*80)
            print(f"✅ PORTA LIBERADA EM {elapsed:.2f}s - Botão habilitado")
            print("="*80 + "\n")
            
            self.btn_toggle.setEnabled(True)
            self.status_label.setText("⚪ Parado")
            self.status_label.setStyleSheet("color: gray; font-weight: bold;")
            
        except (OSError, serial.SerialException) as e:
            # Porta ainda em uso
            print(f"[{timestamp}] +{elapsed:6.2f}s | ❌ EM USO (tentativa {self.port_check_count})")
    
    def poll_shared_memory(self):
        """Faz polling de shared memory para atualizar UI (multiprocessing)"""
        if not self.server_running or not self.modbus:
            return
        
        try:
            # Verificar coils - ler do endereço offset+1
            for addr in self.coils_map.keys():
                val = self.modbus.get_value(1, addr + 1)
                if val is not None and val != self.last_values['coils'].get(addr):
                    old_val = self.last_values['coils'].get(addr, 'N/A')
                    self.last_values['coils'][addr] = val
                    
                    # Debug: mostrar mudança
                    reg_name = self.coils_map[addr]['nome']
                    pass # print(f"🔄 [COIL] Base0={addr} | {reg_name[:30]:30s} | Tela: {old_val} → Modbus: {val}")
                    
                    self.on_coil_changed(addr, bool(val))
            
            # Verificar discrete inputs - ler do endereço offset+1
            for addr in self.di_map.keys():
                val = self.modbus.get_value(2, addr + 1)
                if val is not None and val != self.last_values['di'].get(addr):
                    old_val = self.last_values['di'].get(addr, 'N/A')
                    self.last_values['di'][addr] = val
                    
                    # Debug: mostrar mudança
                    reg_name = self.di_map[addr]['nome']
                    pass # print(f"🔄 [DI]   Base0={addr} | {reg_name[:30]:30s} | Tela: {old_val} → Modbus: {val}")
                    
                    self.on_di_changed(addr, bool(val))
            
            # Verificar input registers - ler do endereço offset+1
            for addr in self.ir_map.keys():
                val = self.modbus.get_value(4, addr + 1)
                if val is not None and val != self.last_values['ir'].get(addr):
                    old_val = self.last_values['ir'].get(addr, 'N/A')
                    self.last_values['ir'][addr] = val
                    
                    # Debug: mostrar mudança
                    reg_name = self.ir_map[addr]['nome']
                    unidade = self.ir_map[addr]['unidade']
                    pass # print(f"🔄 [IR]   Base0={addr} | {reg_name[:30]:30s} | Tela: {old_val} → Modbus: {val} {unidade}")
                    
                    self.on_ir_changed(addr, int(val))
            
            # Verificar holding registers - ler do endereço offset+1
            for addr in self.hr_map.keys():
                val = self.modbus.get_value(3, addr + 1)
                if val is not None and val != self.last_values['hr'].get(addr):
                    old_val = self.last_values['hr'].get(addr, 'N/A')
                    self.last_values['hr'][addr] = val
                    
                    # Debug: mostrar mudança
                    reg_name = self.hr_map[addr]['nome']
                    unidade = self.hr_map[addr]['unidade']
                    pass # print(f"🔄 [HR]   Base0={addr} | {reg_name[:30]:30s} | Tela: {old_val} → Modbus: {val} {unidade}")
                    
                    self.on_hr_changed(addr, int(val))
        except Exception as e:
            pass  # Ignorar erros de polling
    
    def closeEvent(self, event):
        try:
            if self.server_running:
                self.stop_server()
        except Exception as e:
            print(f"⚠️ Erro ao fechar aplicação: {e}")
        finally:
            event.accept()

if __name__ == '__main__':
    # CRITICAL: Prevenir spawn de novos processos no Windows
    mp.freeze_support()
    
    # Fechar splash nativo do PyInstaller se existir
    try:
        import pyi_splash
        pyi_splash.close()
    except:
        pass
    
    app = QApplication(sys.argv)
    
    # Definir ícone do aplicativo
    if getattr(sys, 'frozen', False):
        icon_path = os.path.join(sys._MEIPASS, 'icon.png')
    else:
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'icon.png')
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # Mostrar splash screen customizado
    splash = SplashScreen()
    splash.show()
    app.processEvents()
    
    # Aguardar 2 segundos
    QTimer.singleShot(2000, lambda: None)
    time.sleep(2)
    
    # Criar janela principal
    window = ModbusEmulator()
    window.showMaximized()
    
    # Fechar splash
    splash.close()
    
    if window.csv_path and os.path.exists(window.csv_path):
        window.load_csv()
    else:
        QMessageBox.information(window, "Bem-vindo", "Selecione um Mapa de Memória para começar")
    
    sys.exit(app.exec())
