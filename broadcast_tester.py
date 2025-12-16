"""Testador de Broadcast Modbus - PyQt6"""
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                              QLabel, QPushButton, QComboBox, QLineEdit, QTextEdit,
                              QGroupBox, QSpinBox, QRadioButton, QButtonGroup)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont
from pymodbus.client.sync import ModbusSerialClient
import serial.tools.list_ports
import sys
import time

class BroadcastTester(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("📡 Testador de Broadcast Modbus")
        self.setGeometry(100, 100, 900, 700)
        
        self.client = None
        self.parity_map = {"None": "N", "Even": "E", "Odd": "O"}
        
        self.setup_ui()
        self.apply_styles()
    
    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Configuração Serial
        config_group = QGroupBox("⚙️ Configuração Master")
        config_layout = QHBoxLayout()
        
        config_layout.addWidget(QLabel("Porta:"))
        self.port_combo = QComboBox()
        self.port_combo.addItems(self.get_available_ports())
        self.port_combo.setCurrentText("COM13")
        config_layout.addWidget(self.port_combo)
        
        config_layout.addWidget(QLabel("Baudrate:"))
        self.baudrate_combo = QComboBox()
        self.baudrate_combo.addItems(["9600", "19200", "38400", "57600", "115200"])
        self.baudrate_combo.setCurrentText("19200")
        config_layout.addWidget(self.baudrate_combo)
        
        config_layout.addWidget(QLabel("Paridade:"))
        self.parity_combo = QComboBox()
        self.parity_combo.addItems(["None", "Even", "Odd"])
        config_layout.addWidget(self.parity_combo)
        
        self.btn_connect = QPushButton("Conectar")
        self.btn_connect.clicked.connect(self.connect_client)
        config_layout.addWidget(self.btn_connect)
        
        self.btn_disconnect = QPushButton("Desconectar")
        self.btn_disconnect.clicked.connect(self.disconnect_client)
        self.btn_disconnect.setEnabled(False)
        config_layout.addWidget(self.btn_disconnect)
        
        self.status_label = QLabel("⚪ Desconectado")
        self.status_label.setStyleSheet("color: gray; font-weight: bold;")
        config_layout.addWidget(self.status_label)
        
        config_layout.addStretch()
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        # Teste de Broadcast
        test_group = QGroupBox("📡 Teste de Broadcast")
        test_layout = QVBoxLayout()
        
        # Seleção de Slave ID
        id_layout = QHBoxLayout()
        id_layout.addWidget(QLabel("Slave ID:"))
        
        self.id_group = QButtonGroup()
        self.radio_broadcast = QRadioButton("0 (Broadcast)")
        self.radio_broadcast.setChecked(True)
        self.id_group.addButton(self.radio_broadcast)
        id_layout.addWidget(self.radio_broadcast)
        
        self.radio_specific = QRadioButton("Específico:")
        self.id_group.addButton(self.radio_specific)
        id_layout.addWidget(self.radio_specific)
        
        self.slave_id_spin = QSpinBox()
        self.slave_id_spin.setRange(1, 247)
        self.slave_id_spin.setValue(1)
        self.slave_id_spin.setMaximumWidth(60)
        id_layout.addWidget(self.slave_id_spin)
        
        id_layout.addStretch()
        test_layout.addLayout(id_layout)
        
        # Comandos de Teste
        cmd_layout = QHBoxLayout()
        
        # Write Coil
        coil_box = QGroupBox("Write Coil (FC 05)")
        coil_layout = QVBoxLayout()
        
        addr_layout = QHBoxLayout()
        addr_layout.addWidget(QLabel("Endereço:"))
        self.coil_addr = QSpinBox()
        self.coil_addr.setRange(0, 65535)
        self.coil_addr.setValue(0)
        addr_layout.addWidget(self.coil_addr)
        coil_layout.addLayout(addr_layout)
        
        val_layout = QHBoxLayout()
        val_layout.addWidget(QLabel("Valor:"))
        self.coil_value = QComboBox()
        self.coil_value.addItems(["OFF (0)", "ON (1)"])
        val_layout.addWidget(self.coil_value)
        coil_layout.addLayout(val_layout)
        
        self.btn_write_coil = QPushButton("Enviar")
        self.btn_write_coil.clicked.connect(self.write_coil)
        self.btn_write_coil.setEnabled(False)
        coil_layout.addWidget(self.btn_write_coil)
        
        coil_box.setLayout(coil_layout)
        cmd_layout.addWidget(coil_box)
        
        # Write Register
        reg_box = QGroupBox("Write Register (FC 06)")
        reg_layout = QVBoxLayout()
        
        reg_addr_layout = QHBoxLayout()
        reg_addr_layout.addWidget(QLabel("Endereço:"))
        self.reg_addr = QSpinBox()
        self.reg_addr.setRange(0, 65535)
        self.reg_addr.setValue(0)
        reg_addr_layout.addWidget(self.reg_addr)
        reg_layout.addLayout(reg_addr_layout)
        
        reg_val_layout = QHBoxLayout()
        reg_val_layout.addWidget(QLabel("Valor:"))
        self.reg_value = QSpinBox()
        self.reg_value.setRange(0, 65535)
        self.reg_value.setValue(100)
        reg_val_layout.addWidget(self.reg_value)
        reg_layout.addLayout(reg_val_layout)
        
        self.btn_write_reg = QPushButton("Enviar")
        self.btn_write_reg.clicked.connect(self.write_register)
        self.btn_write_reg.setEnabled(False)
        reg_layout.addWidget(self.btn_write_reg)
        
        reg_box.setLayout(reg_layout)
        cmd_layout.addWidget(reg_box)
        
        # Read Test
        read_box = QGroupBox("Read Test (FC 01/03)")
        read_layout = QVBoxLayout()
        
        read_addr_layout = QHBoxLayout()
        read_addr_layout.addWidget(QLabel("Endereço:"))
        self.read_addr = QSpinBox()
        self.read_addr.setRange(0, 65535)
        self.read_addr.setValue(0)
        read_addr_layout.addWidget(self.read_addr)
        read_layout.addLayout(read_addr_layout)
        
        read_type_layout = QHBoxLayout()
        read_type_layout.addWidget(QLabel("Tipo:"))
        self.read_type = QComboBox()
        self.read_type.addItems(["Coil (FC 01)", "Holding Reg (FC 03)"])
        read_type_layout.addWidget(self.read_type)
        read_layout.addLayout(read_type_layout)
        
        self.btn_read = QPushButton("Ler")
        self.btn_read.clicked.connect(self.read_value)
        self.btn_read.setEnabled(False)
        read_layout.addWidget(self.btn_read)
        
        read_box.setLayout(read_layout)
        cmd_layout.addWidget(read_box)
        
        test_layout.addLayout(cmd_layout)
        test_group.setLayout(test_layout)
        layout.addWidget(test_group)
        
        # Teste Automático
        auto_group = QGroupBox("🤖 Teste Automático")
        auto_layout = QHBoxLayout()
        
        auto_layout.addWidget(QLabel("Sequência de teste completa:"))
        self.btn_auto_test = QPushButton("Executar Teste Completo")
        self.btn_auto_test.clicked.connect(self.run_auto_test)
        self.btn_auto_test.setEnabled(False)
        self.btn_auto_test.setFixedWidth(200)
        auto_layout.addWidget(self.btn_auto_test)
        
        auto_layout.addStretch()
        auto_group.setLayout(auto_layout)
        layout.addWidget(auto_group)
        
        # Log
        log_group = QGroupBox("📋 Log de Comunicação")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(250)
        log_layout.addWidget(self.log_text)
        
        btn_clear = QPushButton("Limpar Log")
        btn_clear.clicked.connect(self.log_text.clear)
        btn_clear.setFixedWidth(120)
        log_layout.addWidget(btn_clear)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
    
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
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
            QComboBox, QSpinBox {
                background-color: white;
                border: 2px solid #bdc3c7;
                border-radius: 4px;
                padding: 5px;
            }
        """)
    
    def get_available_ports(self):
        ports = [port.device for port in serial.tools.list_ports.comports()]
        return ports if ports else ["COM13"]
    
    def log(self, message, color="black"):
        colors = {"error": "red", "success": "green", "info": "blue", "warning": "orange"}
        color_code = colors.get(color, color)
        self.log_text.append(f'<span style="color: {color_code};">{message}</span>')
    
    def connect_client(self):
        port = self.port_combo.currentText()
        baudrate = int(self.baudrate_combo.currentText())
        parity = self.parity_map[self.parity_combo.currentText()]
        
        try:
            self.client = ModbusSerialClient(
                method='rtu',
                port=port,
                baudrate=baudrate,
                parity=parity,
                stopbits=1,
                bytesize=8,
                timeout=1
            )
            
            if self.client.connect():
                self.log(f"✅ Conectado em {port} @ {baudrate} bps", "success")
                self.status_label.setText("🟢 Conectado")
                self.status_label.setStyleSheet("color: green; font-weight: bold;")
                self.btn_connect.setEnabled(False)
                self.btn_disconnect.setEnabled(True)
                self.btn_write_coil.setEnabled(True)
                self.btn_write_reg.setEnabled(True)
                self.btn_read.setEnabled(True)
                self.btn_auto_test.setEnabled(True)
            else:
                self.log(f"❌ Falha ao conectar em {port}", "error")
        except Exception as e:
            self.log(f"❌ Erro: {str(e)}", "error")
    
    def disconnect_client(self):
        if self.client:
            self.client.close()
            self.client = None
            self.log("⚪ Desconectado", "info")
            self.status_label.setText("⚪ Desconectado")
            self.status_label.setStyleSheet("color: gray; font-weight: bold;")
            self.btn_connect.setEnabled(True)
            self.btn_disconnect.setEnabled(False)
            self.btn_write_coil.setEnabled(False)
            self.btn_write_reg.setEnabled(False)
            self.btn_read.setEnabled(False)
            self.btn_auto_test.setEnabled(False)
    
    def get_slave_id(self):
        if self.radio_broadcast.isChecked():
            return 0
        return self.slave_id_spin.value()
    
    def write_coil(self):
        if not self.client:
            return
        
        slave_id = self.get_slave_id()
        addr = self.coil_addr.value()
        value = self.coil_value.currentIndex() == 1
        
        try:
            self.log(f"📤 Enviando Write Coil: Slave={slave_id}, Addr={addr}, Value={value}", "info")
            result = self.client.write_coil(addr, value, unit=slave_id)
            
            if slave_id == 0:
                self.log(f"📡 Broadcast enviado (sem resposta esperada)", "warning")
            elif result.isError():
                self.log(f"❌ Erro: {result}", "error")
            else:
                self.log(f"✅ Coil {addr} escrito com sucesso: {value}", "success")
        except Exception as e:
            self.log(f"❌ Exceção: {str(e)}", "error")
    
    def write_register(self):
        if not self.client:
            return
        
        slave_id = self.get_slave_id()
        addr = self.reg_addr.value()
        value = self.reg_value.value()
        
        try:
            self.log(f"📤 Enviando Write Register: Slave={slave_id}, Addr={addr}, Value={value}", "info")
            result = self.client.write_register(addr, value, unit=slave_id)
            
            if slave_id == 0:
                self.log(f"📡 Broadcast enviado (sem resposta esperada)", "warning")
            elif result.isError():
                self.log(f"❌ Erro: {result}", "error")
            else:
                self.log(f"✅ Register {addr} escrito com sucesso: {value}", "success")
        except Exception as e:
            self.log(f"❌ Exceção: {str(e)}", "error")
    
    def read_value(self):
        if not self.client:
            return
        
        slave_id = self.get_slave_id()
        addr = self.read_addr.value()
        
        if slave_id == 0:
            self.log(f"⚠️ Broadcast não suporta leitura (apenas escrita)", "warning")
            return
        
        try:
            if self.read_type.currentIndex() == 0:
                self.log(f"📥 Lendo Coil: Slave={slave_id}, Addr={addr}", "info")
                result = self.client.read_coils(addr, 1, unit=slave_id)
                if not result.isError():
                    self.log(f"✅ Coil {addr} = {result.bits[0]}", "success")
                else:
                    self.log(f"❌ Erro: {result}", "error")
            else:
                self.log(f"📥 Lendo Holding Register: Slave={slave_id}, Addr={addr}", "info")
                result = self.client.read_holding_registers(addr, 1, unit=slave_id)
                if not result.isError():
                    self.log(f"✅ Register {addr} = {result.registers[0]}", "success")
                else:
                    self.log(f"❌ Erro: {result}", "error")
        except Exception as e:
            self.log(f"❌ Exceção: {str(e)}", "error")
    
    def run_auto_test(self):
        if not self.client:
            return
        
        self.log("\n" + "="*60, "info")
        self.log("🤖 INICIANDO TESTE AUTOMÁTICO DE BROADCAST", "info")
        self.log("="*60, "info")
        
        slave_id = self.slave_id_spin.value()
        
        # Teste 1: Escrever via broadcast
        self.log(f"\n📡 TESTE 1: Broadcast Write Coil (addr=0, value=ON)", "info")
        self.client.write_coil(0, True, unit=0)
        self.log("✅ Comando broadcast enviado", "success")
        time.sleep(0.5)
        
        # Teste 2: Ler valor específico
        self.log(f"\n📥 TESTE 2: Ler Coil do Slave {slave_id} (addr=0)", "info")
        result = self.client.read_coils(0, 1, unit=slave_id)
        if not result.isError():
            self.log(f"✅ Slave {slave_id} respondeu: Coil 0 = {result.bits[0]}", "success")
        else:
            self.log(f"❌ Slave {slave_id} não respondeu", "error")
        time.sleep(0.5)
        
        # Teste 3: Escrever via broadcast OFF
        self.log(f"\n📡 TESTE 3: Broadcast Write Coil (addr=0, value=OFF)", "info")
        self.client.write_coil(0, False, unit=0)
        self.log("✅ Comando broadcast enviado", "success")
        time.sleep(0.5)
        
        # Teste 4: Verificar mudança
        self.log(f"\n📥 TESTE 4: Verificar mudança no Slave {slave_id}", "info")
        result = self.client.read_coils(0, 1, unit=slave_id)
        if not result.isError():
            self.log(f"✅ Slave {slave_id} respondeu: Coil 0 = {result.bits[0]}", "success")
        else:
            self.log(f"❌ Slave {slave_id} não respondeu", "error")
        time.sleep(0.5)
        
        # Teste 5: Write Register via broadcast
        self.log(f"\n📡 TESTE 5: Broadcast Write Register (addr=0, value=999)", "info")
        self.client.write_register(0, 999, unit=0)
        self.log("✅ Comando broadcast enviado", "success")
        time.sleep(0.5)
        
        # Teste 6: Ler register
        self.log(f"\n📥 TESTE 6: Ler Register do Slave {slave_id} (addr=0)", "info")
        result = self.client.read_holding_registers(0, 1, unit=slave_id)
        if not result.isError():
            self.log(f"✅ Slave {slave_id} respondeu: Register 0 = {result.registers[0]}", "success")
        else:
            self.log(f"❌ Slave {slave_id} não respondeu", "error")
        
        self.log("\n" + "="*60, "info")
        self.log("✅ TESTE AUTOMÁTICO CONCLUÍDO", "success")
        self.log("="*60 + "\n", "info")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = BroadcastTester()
    window.show()
    sys.exit(app.exec())
