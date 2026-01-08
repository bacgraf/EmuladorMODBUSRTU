"""Editor CSV para Mapa de Memória EmuladorMODBUSRTU - PyQt6"""
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                              QLabel, QPushButton, QTableWidget, QTableWidgetItem, QComboBox,
                              QLineEdit, QFileDialog, QMessageBox, QHeaderView, QGroupBox, QProgressBar, QMenu, QWidgetAction)
from PyQt6.QtCore import Qt, QPoint, pyqtSignal
from PyQt6.QtGui import QColor, QIntValidator, QDoubleValidator, QIcon, QAction, QShortcut, QKeySequence
import csv
import sys
import os


class NoWheelComboBox(QComboBox):
    """QComboBox que ignora eventos da roda do mouse"""
    def wheelEvent(self, event):
        event.ignore()


class CSVEditor(QMainWindow):
    # Signal para notificar quando CSV foi salvo
    csv_saved = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("📝 Editor CSV - Mapa de Memória EmuladorMODBUSRTU")
        self.csv_path = ""
        self.modified = False
        self.dynamic_mode = True  # True = modo dinâmico, False = modo planilha
        self.use_minmax_format = False  # True = Minimo/Maximo, False = Intervalo
        
        self.setup_ui()
        self.apply_styles()
        self.setup_shortcuts()
    
    def get_fcs(self, tipo, permissao):
        """Retorna os FCs baseado no tipo e permissão"""
        fc_map = {
            'COIL': {'R': '1', 'W': '5', 'R/W': '1/5', 'R/W/B': '1/5', 'R/W/B(0)': '1/5'},
            'DISC': {'R': '2', 'W': '2', 'R/W': '2'},
            'IREG': {'R': '4', 'W': '4', 'R/W': '4'},
            'HREG': {'R': '3', 'W': '6/16', 'R/W': '3/6/16'}
        }
        return fc_map.get(tipo, {}).get(permissao, '')
    
    def update_table_columns(self):
        """Atualiza colunas da tabela baseado no formato"""
        if self.use_minmax_format:
            self.table.setColumnCount(12)
            self.table.setHorizontalHeaderLabels(["Tipo", "RegBase0", "RegBase1", "Objeto", "Unidade", "Resolucao", "Permissao", "FCs", "Minimo", "Maximo", "ValorInicial", "Descricao"])
        else:
            self.table.setColumnCount(11)
            self.table.setHorizontalHeaderLabels(["Tipo", "RegBase0", "RegBase1", "Objeto", "Unidade", "Resolucao", "Permissao", "FCs", "Intervalo", "ValorInicial", "Descricao"])
        
        self.table.setColumnWidth(0, 100)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(self.table.columnCount()-1, QHeaderView.ResizeMode.Stretch)
    
    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Toolbar
        toolbar_group = QGroupBox("📄 Arquivo")
        toolbar_layout = QHBoxLayout()
        
        btn_new = QPushButton("Novo")
        btn_new.setFixedWidth(100)
        btn_new.clicked.connect(self.new_file)
        toolbar_layout.addWidget(btn_new)
        
        btn_open = QPushButton("Abrir...")
        btn_open.setFixedWidth(100)
        btn_open.clicked.connect(self.open_file)
        toolbar_layout.addWidget(btn_open)
        
        btn_save = QPushButton("Salvar")
        btn_save.setFixedWidth(100)
        btn_save.clicked.connect(self.save_file)
        toolbar_layout.addWidget(btn_save)
        
        btn_save_as = QPushButton("Salvar Como...")
        btn_save_as.setFixedWidth(120)
        btn_save_as.clicked.connect(self.save_file_as)
        toolbar_layout.addWidget(btn_save_as)
        
        toolbar_layout.addStretch()
        
        self.file_label = QLabel("Nenhum arquivo carregado")
        self.file_label.setStyleSheet("color: #7f8c8d; font-style: italic;")
        toolbar_layout.addWidget(self.file_label)
        
        toolbar_group.setLayout(toolbar_layout)
        layout.addWidget(toolbar_group)
        
        # Edit toolbar
        edit_group = QGroupBox("✏️ Edição")
        edit_layout = QHBoxLayout()
        
        btn_add_above = QPushButton("⬆️ Adicionar Acima")
        btn_add_above.setFixedWidth(150)
        btn_add_above.clicked.connect(self.add_row_above)
        edit_layout.addWidget(btn_add_above)
        
        btn_add_below = QPushButton("⬇️ Adicionar Abaixo")
        btn_add_below.setFixedWidth(150)
        btn_add_below.clicked.connect(self.add_row_below)
        edit_layout.addWidget(btn_add_below)
        
        btn_remove = QPushButton("➖ Remover Linha")
        btn_remove.setFixedWidth(150)
        btn_remove.clicked.connect(self.remove_row)
        edit_layout.addWidget(btn_remove)
        
        btn_duplicate = QPushButton("📋 Duplicar Linha")
        btn_duplicate.setFixedWidth(150)
        btn_duplicate.clicked.connect(self.duplicate_row)
        edit_layout.addWidget(btn_duplicate)
        
        edit_layout.addStretch()
        
        self.btn_toggle_mode = QPushButton("🔄 Modo Planilha")
        self.btn_toggle_mode.setFixedWidth(150)
        self.btn_toggle_mode.clicked.connect(self.toggle_mode)
        edit_layout.addWidget(self.btn_toggle_mode)
        
        edit_layout.addWidget(QLabel("Filtrar por tipo:"))
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["Todos", "COIL", "DISC", "IREG", "HREG"])
        self.filter_combo.currentTextChanged.connect(self.apply_filters)
        edit_layout.addWidget(self.filter_combo)
        
        edit_group.setLayout(edit_layout)
        layout.addWidget(edit_group)
        
        # Table
        self.table = QTableWidget()
        self.update_table_columns()  # Configura colunas baseado no formato
        self.table.setAlternatingRowColors(True)
        self.table.itemChanged.connect(self.on_item_changed)
        layout.addWidget(self.table)
        
        # Status bar
        status_layout = QHBoxLayout()
        self.status_label = QLabel("Pronto")
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(200)
        self.progress_bar.setVisible(False)
        self.row_count_label = QLabel("0 linhas")
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.progress_bar)
        status_layout.addStretch()
        status_layout.addWidget(self.row_count_label)
        layout.addLayout(status_layout)
    
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
            QTableWidget {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                gridline-color: #ecf0f1;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            QHeaderView::section {
                background-color: #ecf0f1;
                padding: 8px;
                border: none;
                border-right: 1px solid #bdc3c7;
                border-bottom: 2px solid #3498db;
                font-weight: bold;
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
            QTableWidget QComboBox {
                border: 1px solid #bdc3c7;
                padding: 3px 5px;
            }
            QTableWidget QComboBox::drop-down {
                width: 20px;
            }
        """)
    
    def new_file(self):
        if self.modified:
            reply = QMessageBox.question(self, "Salvar alterações?", 
                                        "Deseja salvar as alterações antes de criar um novo arquivo?",
                                        QMessageBox.StandardButton.Yes | 
                                        QMessageBox.StandardButton.No | 
                                        QMessageBox.StandardButton.Cancel)
            if reply == QMessageBox.StandardButton.Yes:
                self.save_file()
            elif reply == QMessageBox.StandardButton.Cancel:
                return
        
        self.table.setRowCount(0)
        self.csv_path = ""
        self.modified = False
        self.file_label.setText("Novo arquivo (não salvo)")
        self.update_row_count()
        self.status_label.setText("Novo arquivo criado")
    
    def open_file(self):
        if self.modified:
            reply = QMessageBox.question(self, "Salvar alterações?", 
                                        "Deseja salvar as alterações antes de abrir outro arquivo?",
                                        QMessageBox.StandardButton.Yes | 
                                        QMessageBox.StandardButton.No | 
                                        QMessageBox.StandardButton.Cancel)
            if reply == QMessageBox.StandardButton.Yes:
                self.save_file()
            elif reply == QMessageBox.StandardButton.Cancel:
                return
        
        filename, _ = QFileDialog.getOpenFileName(self, "Abrir Arquivo", "", "CSV files (*.csv);;All files (*.*)")
        if filename:
            self.load_csv(filename)
            self.status_label.setText(f"Arquivo aberto: {filename}")
    
    def load_csv(self, filename):
        try:
            self.table.blockSignals(True)
            self.table.setRowCount(0)
            
            # Detectar formato do CSV (Intervalo vs Minimo/Maximo)
            with open(filename, 'r', encoding='utf-8-sig') as f:
                sample = f.read(1024)
                f.seek(0)
                sniffer = csv.Sniffer()
                delimiter = sniffer.sniff(sample).delimiter
                
                reader = csv.DictReader(f, delimiter=delimiter)
                first_row = next(reader, None)
                f.seek(0)
                reader = csv.DictReader(f, delimiter=delimiter)
                
                # Detectar formato baseado nas colunas
                if first_row and 'Minimo' in first_row and 'Maximo' in first_row:
                    self.use_minmax_format = True
                else:
                    self.use_minmax_format = False
            
            # Atualizar colunas da tabela
            self.update_table_columns()
            
            # Ler arquivo em memória com progresso
            import os
            file_size = os.path.getsize(filename)
            self.progress_bar.setVisible(True)
            self.progress_bar.setMaximum(100)
            self.status_label.setText("Carregando arquivo...")
            QApplication.processEvents()
            
            data_rows = []
            bytes_read = 0
            with open(filename, 'rb') as f:
                content = f.read()
                bytes_read = len(content)
            
            self.progress_bar.setValue(50)
            
            with open(filename, 'r', encoding='utf-8-sig') as f:
                sample = f.read(1024)
                f.seek(0)
                sniffer = csv.Sniffer()
                delimiter = sniffer.sniff(sample).delimiter
                reader = csv.DictReader(f, delimiter=delimiter)
                data_rows = list(reader)
            
            self.progress_bar.setValue(100)
            self.progress_bar.setVisible(False)
            self.status_label.setText("Criando tabela...")
            QApplication.processEvents()
            
            for idx, row_data in enumerate(data_rows):
                row = self.table.rowCount()
                self.table.insertRow(row)
                
                # Ler colunas baseado no formato
                if self.use_minmax_format:
                    cols_data = [
                        row_data.get('Tipo', ''),
                        row_data.get('RegBase0', ''),
                        row_data.get('RegBase1', ''),
                        row_data.get('Objeto', ''),
                        row_data.get('Unidade', ''),
                        row_data.get('Resolucao', ''),
                        row_data.get('Permissao', ''),
                        row_data.get('FCs', ''),
                        row_data.get('Minimo', ''),
                        row_data.get('Maximo', ''),
                        row_data.get('ValorInicial', ''),
                        row_data.get('Descricao', '')
                    ]
                else:
                    cols_data = [
                        row_data.get('Tipo', ''),
                        row_data.get('RegBase0', ''),
                        row_data.get('RegBase1', ''),
                        row_data.get('Objeto', ''),
                        row_data.get('Unidade', ''),
                        row_data.get('Resolucao', ''),
                        row_data.get('Permissao', ''),
                        row_data.get('FCs', ''),
                        row_data.get('Intervalo', ''),
                        row_data.get('ValorInicial', ''),
                        row_data.get('Descricao', '')
                    ]
                
                # Tipo (ComboBox)
                combo = NoWheelComboBox()
                combo.addItems(["COIL", "DISC", "IREG", "HREG"])
                combo.setCurrentText(cols_data[0])
                combo.currentTextChanged.connect(lambda t, r=row: self.on_tipo_changed(r, t))
                self.table.setCellWidget(row, 0, combo)
                
                # Colunas 1-5 (RegBase0 até Resolucao)
                for col in range(1, 6):
                    self.table.setItem(row, col, QTableWidgetItem(cols_data[col]))
                
                # Permissao (ComboBox)
                perm_combo = NoWheelComboBox()
                if cols_data[0] in ["DISC", "IREG"]:
                    perm_combo.addItems(["R"])
                    perm_combo.setCurrentText("R")
                else:
                    perm_combo.addItems(["R", "W", "R/W", "R/W/B", "R/W/B(0)"])
                    perm_combo.setCurrentText(cols_data[6] if cols_data[6] in ["R", "W", "R/W", "R/W/B", "R/W/B(0)"] else "R")
                perm_combo.currentTextChanged.connect(lambda p, r=row: self.on_permissao_changed(r, p))
                self.table.setCellWidget(row, 6, perm_combo)
                
                # Colunas 7-8 (FCs e Intervalo/Minimo)
                for col in range(7, 9):
                    self.table.setItem(row, col, QTableWidgetItem(cols_data[col]))
                
                # Coluna 9 (Maximo se formato MinMax, senão ValorInicial)
                if self.use_minmax_format:
                    self.table.setItem(row, 9, QTableWidgetItem(cols_data[9]))  # Maximo
                    valor_col = 10
                else:
                    valor_col = 9
                
                # ValorInicial - ComboBox para COIL/DISC
                if cols_data[0] in ["COIL", "DISC"]:
                    valor_combo = NoWheelComboBox()
                    valor_combo.addItems(["OFF", "ON", ""])
                    valor_combo.setCurrentText(cols_data[valor_col] if cols_data[valor_col] in ["ON", "OFF", ""] else "OFF")
                    valor_combo.currentTextChanged.connect(lambda: self.mark_modified())
                    self.table.setCellWidget(row, valor_col, valor_combo)
                else:
                    self.table.setItem(row, valor_col, QTableWidgetItem(cols_data[valor_col]))
                
                # Descricao (última coluna)
                desc_col = 11 if self.use_minmax_format else 10
                self.table.setItem(row, desc_col, QTableWidgetItem(cols_data[desc_col]))
            
            self.csv_path = filename
            self.modified = False
            self.file_label.setText(filename)
            self.update_row_count()
            self.status_label.setText(f"Arquivo carregado: {filename}")
            self.table.blockSignals(False)
            
        except Exception as e:
            self.progress_bar.setVisible(False)
            self.status_label.setText("Erro ao carregar")
            QMessageBox.critical(self, "Erro", f"Falha ao carregar arquivo:\n{str(e)}")
            self.table.blockSignals(False)
    
    def save_file(self):
        if not self.csv_path:
            self.save_file_as()
        else:
            self.write_csv(self.csv_path)
    
    def save_file_as(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Salvar Como", "", "CSV files (*.csv);;All files (*.*)")
        if filename:
            self.write_csv(filename)
    
    def write_csv(self, filename):
        try:
            with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                sample = open(filename.replace('.csv', '_temp.csv'), 'w') if os.path.exists(filename) else None
                
                writer = csv.writer(f, delimiter=',')
                
                # Cabeçalho baseado no formato
                if self.use_minmax_format:
                    writer.writerow(['Tipo', 'RegBase0', 'RegBase1', 'Objeto', 'Unidade', 'Resolucao', 'Permissao', 'FCs', 'Minimo', 'Maximo', 'ValorInicial', 'Descricao'])
                else:
                    writer.writerow(['Tipo', 'RegBase0', 'RegBase1', 'Objeto', 'Unidade', 'Resolucao', 'Permissao', 'FCs', 'Intervalo', 'ValorInicial', 'Descricao'])
                
                for row in range(self.table.rowCount()):
                    # Tipo
                    combo = self.table.cellWidget(row, 0)
                    tipo = combo.currentText() if combo else ""
                    
                    # Colunas 1-5
                    cols = [tipo]
                    for col in range(1, 6):
                        item = self.table.item(row, col)
                        cols.append(item.text() if item else "")
                    
                    # Permissao (col 6)
                    perm_widget = self.table.cellWidget(row, 6)
                    if isinstance(perm_widget, NoWheelComboBox):
                        cols.append(perm_widget.currentText())
                    else:
                        item = self.table.item(row, 6)
                        cols.append(item.text() if item else "")
                    
                    # Colunas 7-8 (FCs e Intervalo/Minimo)
                    for col in range(7, 9):
                        item = self.table.item(row, col)
                        cols.append(item.text() if item else "")
                    
                    # Formato MinMax: adicionar coluna Maximo
                    if self.use_minmax_format:
                        item = self.table.item(row, 9)
                        cols.append(item.text() if item else "")
                        valor_col = 10
                        desc_col = 11
                    else:
                        valor_col = 9
                        desc_col = 10
                    
                    # ValorInicial
                    valor_widget = self.table.cellWidget(row, valor_col)
                    if isinstance(valor_widget, NoWheelComboBox):
                        cols.append(valor_widget.currentText())
                    else:
                        item = self.table.item(row, valor_col)
                        cols.append(item.text() if item else "")
                    
                    # Descricao
                    item = self.table.item(row, desc_col)
                    cols.append(item.text() if item else "")
                    
                    writer.writerow(cols)
            
            self.csv_path = filename
            self.modified = False
            self.file_label.setText(filename)
            self.status_label.setText(f"Arquivo salvo: {filename}")
            QMessageBox.information(self, "Sucesso", "Arquivo salvo com sucesso!")
            
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao salvar arquivo:\n{str(e)}")
    
    def add_row_above(self):
        current_row = self.table.currentRow()
        if current_row < 0:
            row = 0
        else:
            row = current_row
        self._insert_empty_row(row)
        self.status_label.setText("Linha adicionada acima")
    
    def add_row_below(self):
        current_row = self.table.currentRow()
        if current_row < 0:
            row = self.table.rowCount()
        else:
            row = current_row + 1
        self._insert_empty_row(row)
        self.status_label.setText("Linha adicionada abaixo")
    
    def _insert_empty_row(self, row):
        self.table.insertRow(row)
        
        if self.dynamic_mode:
            combo = NoWheelComboBox()
            combo.addItems(["COIL", "DISC", "IREG", "HREG"])
            combo.currentTextChanged.connect(lambda t, r=row: self.on_tipo_changed(r, t))
            self.table.setCellWidget(row, 0, combo)
            
            for col in range(1, 6):
                self.table.setItem(row, col, QTableWidgetItem(""))
            
            # Permissao (ComboBox)
            perm_combo = NoWheelComboBox()
            tipo_combo = self.table.cellWidget(row, 0)
            tipo = tipo_combo.currentText() if tipo_combo else "COIL"
            if tipo in ["DISC", "IREG"]:
                perm_combo.addItems(["R"])
            else:
                perm_combo.addItems(["R", "W", "R/W", "R/W/B", "R/W/B(0)"])
            perm_combo.setCurrentText("R")
            perm_combo.currentTextChanged.connect(lambda p, r=row: self.on_permissao_changed(r, p))
            self.table.setCellWidget(row, 6, perm_combo)
            
            for col in range(7, 9):
                self.table.setItem(row, col, QTableWidgetItem(""))
            
            # ValorInicial - ComboBox com OFF como padrão apenas para COIL (tipo padrão)
            valor_combo = NoWheelComboBox()
            valor_combo.addItems(["OFF", "ON", ""])
            valor_combo.setCurrentText("OFF")
            valor_combo.currentTextChanged.connect(lambda: self.mark_modified())
            self.table.setCellWidget(row, 9, valor_combo)
            
            # Descricao
            self.table.setItem(row, 10, QTableWidgetItem(""))
            
            # Atualizar FCs para o tipo padrão (COIL)
            self.update_fcs(row)
        else:
            # Modo planilha - tudo como texto
            for col in range(11):
                self.table.setItem(row, col, QTableWidgetItem(""))
        
        self.mark_modified()
        self.update_row_count()
    
    def remove_row(self):
        current_row = self.table.currentRow()
        if current_row >= 0:
            reply = QMessageBox.question(self, "Confirmar", 
                                        "Deseja realmente remover esta linha?",
                                        QMessageBox.StandardButton.Yes | 
                                        QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.table.removeRow(current_row)
                self.mark_modified()
                self.update_row_count()
                self.status_label.setText("Linha removida")
        else:
            QMessageBox.warning(self, "Aviso", "Selecione uma linha para remover")
    
    def duplicate_row(self):
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Aviso", "Selecione uma linha para duplicar")
            return
        
        new_row = self.table.rowCount()
        self.table.insertRow(new_row)
        
        # Copiar ComboBox Tipo
        old_combo = self.table.cellWidget(current_row, 0)
        if old_combo:
            tipo = old_combo.currentText()
        else:
            tipo = "COIL"
        
        new_combo = NoWheelComboBox()
        new_combo.addItems(["COIL", "DISC", "IREG", "HREG"])
        new_combo.setCurrentText(tipo)
        new_combo.currentTextChanged.connect(lambda t, r=new_row: self.on_tipo_changed(r, t))
        self.table.setCellWidget(new_row, 0, new_combo)
        
        # Copiar campos 1-5
        for col in range(1, 6):
            item = self.table.item(current_row, col)
            self.table.setItem(new_row, col, QTableWidgetItem(item.text() if item else ""))
        
        # Copiar Permissao (col 6)
        old_perm_combo = self.table.cellWidget(current_row, 6)
        new_perm_combo = NoWheelComboBox()
        if tipo in ["DISC", "IREG"]:
            new_perm_combo.addItems(["R"])
            new_perm_combo.setCurrentText("R")
        else:
            new_perm_combo.addItems(["R", "W", "R/W", "R/W/B", "R/W/B(0)"])
            new_perm_combo.setCurrentText(old_perm_combo.currentText() if old_perm_combo else "R")
        new_perm_combo.currentTextChanged.connect(lambda p, r=new_row: self.on_permissao_changed(r, p))
        self.table.setCellWidget(new_row, 6, new_perm_combo)
        
        # Copiar campos 7-8
        for col in range(7, 9):
            item = self.table.item(current_row, col)
            self.table.setItem(new_row, col, QTableWidgetItem(item.text() if item else ""))
        
        # Copiar ValorInicial (col 9)
        if tipo in ["COIL", "DISC"]:
            old_valor_combo = self.table.cellWidget(current_row, 9)
            new_valor_combo = NoWheelComboBox()
            new_valor_combo.addItems(["OFF", "ON", ""])
            new_valor_combo.setCurrentText(old_valor_combo.currentText() if old_valor_combo else "OFF")
            new_valor_combo.currentTextChanged.connect(lambda: self.mark_modified())
            self.table.setCellWidget(new_row, 9, new_valor_combo)
        else:
            item = self.table.item(current_row, 9)
            self.table.setItem(new_row, 9, QTableWidgetItem(item.text() if item else ""))
        
        # Copiar Descricao (col 10)
        item = self.table.item(current_row, 10)
        self.table.setItem(new_row, 10, QTableWidgetItem(item.text() if item else ""))
        
        self.mark_modified()
        self.update_row_count()
        self.status_label.setText("Linha duplicada")
    
    def toggle_mode(self):
        self.dynamic_mode = not self.dynamic_mode
        
        if self.dynamic_mode:
            self.btn_toggle_mode.setText("🔄 Modo Planilha")
        else:
            self.btn_toggle_mode.setText("🔄 Modo Dinâmico")
        
        # Recarregar tabela no novo modo
        self.reload_table()
    
    def reload_table(self):
        # Salvar dados atuais
        data = []
        for row in range(self.table.rowCount()):
            row_data = {}
            
            # Tipo
            tipo_widget = self.table.cellWidget(row, 0)
            if isinstance(tipo_widget, NoWheelComboBox):
                row_data['tipo'] = tipo_widget.currentText()
            else:
                item = self.table.item(row, 0)
                row_data['tipo'] = item.text() if item else ""
            
            # Colunas 1-5
            for col in range(1, 6):
                item = self.table.item(row, col)
                row_data[f'col{col}'] = item.text() if item else ""
            
            # Permissao (col 6)
            perm_widget = self.table.cellWidget(row, 6)
            if isinstance(perm_widget, NoWheelComboBox):
                row_data['col6'] = perm_widget.currentText()
            else:
                item = self.table.item(row, 6)
                row_data['col6'] = item.text() if item else ""
            
            # Colunas 7-8
            for col in range(7, 9):
                item = self.table.item(row, col)
                row_data[f'col{col}'] = item.text() if item else ""
            
            # ValorInicial (col 9)
            valor_widget = self.table.cellWidget(row, 9)
            if isinstance(valor_widget, NoWheelComboBox):
                row_data['valor'] = valor_widget.currentText()
            else:
                item = self.table.item(row, 9)
                row_data['valor'] = item.text() if item else ""
            
            # Descricao (col 10)
            item = self.table.item(row, 10)
            row_data['descricao'] = item.text() if item else ""
            
            data.append(row_data)
        
        # Recriar tabela
        self.table.blockSignals(True)
        self.table.setRowCount(0)
        
        for row_data in data:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            if self.dynamic_mode:
                # Modo Dinâmico - com dropdowns
                tipo_combo = NoWheelComboBox()
                tipo_combo.addItems(["COIL", "DISC", "IREG", "HREG"])
                tipo_combo.setCurrentText(row_data['tipo'])
                tipo_combo.currentTextChanged.connect(lambda t, r=row: self.on_tipo_changed(r, t))
                self.table.setCellWidget(row, 0, tipo_combo)
                
                # Colunas 1-5
                for col in range(1, 6):
                    self.table.setItem(row, col, QTableWidgetItem(row_data[f'col{col}']))
                
                # Permissao (col 6)
                perm_combo = NoWheelComboBox()
                if row_data['tipo'] in ["DISC", "IREG"]:
                    perm_combo.addItems(["R"])
                    perm_combo.setCurrentText("R")
                else:
                    perm_combo.addItems(["R", "W", "R/W", "R/W/B", "R/W/B(0)"])
                    perm_combo.setCurrentText(row_data['col6'] if row_data['col6'] in ["R", "W", "R/W", "R/W/B", "R/W/B(0)"] else "R")
                perm_combo.currentTextChanged.connect(lambda p, r=row: self.on_permissao_changed(r, p))
                self.table.setCellWidget(row, 6, perm_combo)
                
                # Colunas 7-8
                for col in range(7, 9):
                    self.table.setItem(row, col, QTableWidgetItem(row_data[f'col{col}']))
                
                # ValorInicial (col 9)
                if row_data['tipo'] in ["COIL", "DISC"]:
                    valor_combo = NoWheelComboBox()
                    valor_combo.addItems(["OFF", "ON", ""])
                    valor_combo.setCurrentText(row_data['valor'] if row_data['valor'] in ["ON", "OFF", ""] else "OFF")
                    valor_combo.currentTextChanged.connect(lambda: self.mark_modified())
                    self.table.setCellWidget(row, 9, valor_combo)
                else:
                    self.table.setItem(row, 9, QTableWidgetItem(row_data['valor']))
                
                # Descricao (col 10)
                self.table.setItem(row, 10, QTableWidgetItem(row_data['descricao']))
            else:
                # Modo Planilha - tudo como texto
                self.table.setItem(row, 0, QTableWidgetItem(row_data['tipo']))
                for col in range(1, 6):
                    self.table.setItem(row, col, QTableWidgetItem(row_data[f'col{col}']))
                self.table.setItem(row, 6, QTableWidgetItem(row_data['col6']))
                for col in range(7, 9):
                    self.table.setItem(row, col, QTableWidgetItem(row_data[f'col{col}']))
                self.table.setItem(row, 9, QTableWidgetItem(row_data['valor']))
                self.table.setItem(row, 10, QTableWidgetItem(row_data['descricao']))
        
        self.table.blockSignals(False)
    
    def apply_filters(self):
        filter_tipo = self.filter_combo.currentText()
        
        for row in range(self.table.rowCount()):
            # Obter valores da linha
            if self.dynamic_mode:
                combo = self.table.cellWidget(row, 0)
                tipo = combo.currentText() if combo else ""
            else:
                item = self.table.item(row, 0)
                tipo = item.text() if item else ""
            
            # Aplicar filtro por tipo
            if filter_tipo == "Todos":
                self.table.setRowHidden(row, False)
            else:
                self.table.setRowHidden(row, tipo != filter_tipo)
        
        self.update_row_count()
    
    def on_tipo_changed(self, row, tipo):
        # Atualizar Permissao baseado no tipo
        perm_widget = self.table.cellWidget(row, 6)
        if isinstance(perm_widget, NoWheelComboBox):
            current_perm = perm_widget.currentText()
            perm_widget.clear()
            if tipo in ["DISC", "IREG"]:
                perm_widget.addItems(["R"])
                perm_widget.setCurrentText("R")
            else:
                perm_widget.addItems(["R", "W", "R/W", "R/W/B", "R/W/B(0)"])
                if current_perm in ["R", "W", "R/W", "R/W/B", "R/W/B(0)"]:
                    perm_widget.setCurrentText(current_perm)
                else:
                    perm_widget.setCurrentText("R")
        
        # Trocar entre ComboBox e QTableWidgetItem na coluna ValorInicial (col 9)
        if tipo in ["COIL", "DISC"]:
            # Verificar se já é ComboBox
            current_widget = self.table.cellWidget(row, 9)
            if not isinstance(current_widget, NoWheelComboBox):
                # Criar ComboBox com OFF como padrão para COIL/DISC
                valor_combo = NoWheelComboBox()
                valor_combo.addItems(["OFF", "ON", ""])
                valor_combo.setCurrentText("OFF")
                valor_combo.currentTextChanged.connect(lambda: self.mark_modified())
                self.table.setCellWidget(row, 9, valor_combo)
        else:
            # Verificar se é ComboBox
            current_widget = self.table.cellWidget(row, 9)
            if isinstance(current_widget, NoWheelComboBox):
                # Remover ComboBox e criar QTableWidgetItem vazio para IREG/HREG
                self.table.removeCellWidget(row, 9)
                self.table.setItem(row, 9, QTableWidgetItem(""))
            elif not self.table.item(row, 9):
                # Se não existe item, criar vazio
                self.table.setItem(row, 9, QTableWidgetItem(""))
        
        # Atualizar FCs
        self.update_fcs(row)
        self.mark_modified()
    
    def on_permissao_changed(self, row, permissao):
        # Atualizar FCs
        self.update_fcs(row)
        self.mark_modified()
    
    def update_fcs(self, row):
        # Obter Tipo e Permissão
        tipo_widget = self.table.cellWidget(row, 0)
        perm_widget = self.table.cellWidget(row, 6)
        
        if isinstance(tipo_widget, NoWheelComboBox) and isinstance(perm_widget, NoWheelComboBox):
            tipo = tipo_widget.currentText()
            permissao = perm_widget.currentText()
            fcs = self.get_fcs(tipo, permissao)
            
            # Atualizar campo FCs (col 7)
            item = self.table.item(row, 7)
            if item:
                item.setText(fcs)
            else:
                self.table.setItem(row, 7, QTableWidgetItem(fcs))
    
    def on_item_changed(self, item):
        # Validar campos numéricos
        col = item.column()
        text = item.text()
        
        # RegBase0 e RegBase1 (cols 1 e 2) - apenas inteiros
        if col in [1, 2]:
            if text and not text.isdigit():
                item.setText('')
                QMessageBox.warning(self, "Valor inválido", f"O campo {self.table.horizontalHeaderItem(col).text()} aceita apenas números inteiros.")
                return
        
        # Resolucao (col 5) - decimal ou inteiro
        elif col == 5:
            if text:
                try:
                    float(text)
                except ValueError:
                    item.setText('')
                    QMessageBox.warning(self, "Valor inválido", "O campo Resolucao aceita apenas números (inteiros ou decimais).")
                    return
        
        self.mark_modified()
    
    def mark_modified(self):
        if not self.modified:
            self.modified = True
            if self.csv_path:
                self.file_label.setText(f"{self.csv_path} *")
            else:
                self.file_label.setText("Novo arquivo (não salvo) *")
    
    def setup_shortcuts(self):
        """Configurar atalhos de teclado"""
        # Arquivo
        QShortcut(QKeySequence("Ctrl+S"), self).activated.connect(self.save_file)
        QShortcut(QKeySequence("Ctrl+Shift+S"), self).activated.connect(self.save_file_as)
        QShortcut(QKeySequence("Ctrl+O"), self).activated.connect(self.open_file)
        QShortcut(QKeySequence("Ctrl+N"), self).activated.connect(self.new_file)
        QShortcut(QKeySequence("Ctrl+W"), self).activated.connect(self.close)
        QShortcut(QKeySequence("Ctrl+Q"), self).activated.connect(self.close)
        
        # Edição
        QShortcut(QKeySequence("Ctrl+D"), self).activated.connect(self.duplicate_row)
        QShortcut(QKeySequence("Ctrl+I"), self).activated.connect(self.add_row_below)
        QShortcut(QKeySequence("Ctrl+Insert"), self).activated.connect(self.add_row_below)
        QShortcut(QKeySequence("Ctrl+Shift+Insert"), self).activated.connect(self.add_row_above)
        QShortcut(QKeySequence("Delete"), self).activated.connect(self.remove_row)
        QShortcut(QKeySequence("Ctrl+Delete"), self).activated.connect(self.remove_row)
        
        # Filtros Rápidos
        QShortcut(QKeySequence("Ctrl+1"), self).activated.connect(lambda: self.filter_combo.setCurrentText("COIL"))
        QShortcut(QKeySequence("Ctrl+2"), self).activated.connect(lambda: self.filter_combo.setCurrentText("DISC"))
        QShortcut(QKeySequence("Ctrl+3"), self).activated.connect(lambda: self.filter_combo.setCurrentText("IREG"))
        QShortcut(QKeySequence("Ctrl+4"), self).activated.connect(lambda: self.filter_combo.setCurrentText("HREG"))
        QShortcut(QKeySequence("Ctrl+0"), self).activated.connect(lambda: self.filter_combo.setCurrentText("Todos"))
        QShortcut(QKeySequence("Escape"), self).activated.connect(lambda: self.filter_combo.setCurrentText("Todos"))
        
        # Visualização
        QShortcut(QKeySequence("Ctrl+M"), self).activated.connect(self.toggle_mode)
        QShortcut(QKeySequence("F5"), self).activated.connect(self.reload_file)
        QShortcut(QKeySequence("Ctrl++"), self).activated.connect(self.zoom_in)
        QShortcut(QKeySequence("Ctrl+-"), self).activated.connect(self.zoom_out)
        
        # Navegação
        QShortcut(QKeySequence("Ctrl+Home"), self).activated.connect(lambda: self.table.selectRow(0))
        QShortcut(QKeySequence("Ctrl+End"), self).activated.connect(lambda: self.table.selectRow(self.table.rowCount()-1))
    
    def reload_file(self):
        """Recarregar arquivo atual"""
        if self.csv_path and os.path.exists(self.csv_path):
            if self.modified:
                reply = QMessageBox.question(self, "Recarregar?", 
                                            "Existem alterações não salvas. Deseja recarregar mesmo assim?",
                                            QMessageBox.StandardButton.Yes | 
                                            QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.No:
                    return
            self.load_csv(self.csv_path)
            self.status_label.setText("Arquivo recarregado")
    
    def zoom_in(self):
        """Aumentar zoom da tabela"""
        font = self.table.font()
        font.setPointSize(font.pointSize() + 1)
        self.table.setFont(font)
    
    def zoom_out(self):
        """Diminuir zoom da tabela"""
        font = self.table.font()
        if font.pointSize() > 6:
            font.setPointSize(font.pointSize() - 1)
            self.table.setFont(font)
    
    def update_row_count(self):
        visible_rows = sum(1 for row in range(self.table.rowCount()) if not self.table.isRowHidden(row))
        total_rows = self.table.rowCount()
        if visible_rows == total_rows:
            self.row_count_label.setText(f"{total_rows} linhas")
        else:
            self.row_count_label.setText(f"{visible_rows} de {total_rows} linhas")
    
    def closeEvent(self, event):
        if self.modified:
            reply = QMessageBox.question(self, "Salvar alterações?", 
                                        "Existem alterações não salvas. Deseja salvar antes de sair?",
                                        QMessageBox.StandardButton.Yes | 
                                        QMessageBox.StandardButton.No | 
                                        QMessageBox.StandardButton.Cancel)
            if reply == QMessageBox.StandardButton.Yes:
                self.save_file()
                # Emitir signal após salvar
                if self.csv_path:
                    self.csv_saved.emit(self.csv_path)
                event.accept()
            elif reply == QMessageBox.StandardButton.No:
                event.accept()
            else:
                event.ignore()
        else:
            # Mesmo sem modificações, emitir signal se houver arquivo carregado
            if self.csv_path:
                self.csv_saved.emit(self.csv_path)
            event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = CSVEditor()
    window.showMaximized()
    sys.exit(app.exec())
