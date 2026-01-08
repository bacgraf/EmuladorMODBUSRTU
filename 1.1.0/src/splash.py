"""Splash Screen para EmuladorMODBUSRTU"""
from PyQt6.QtWidgets import QSplashScreen
from PyQt6.QtCore import Qt, QTimer, QRect
from PyQt6.QtGui import QPixmap, QFont, QColor, QPainter
import os
import sys

class SplashScreen(QSplashScreen):
    def __init__(self, max_width=500, max_height=375, logo_width=200, logo_height=100, version="v1.0.0"):
        # Buscar imagem Splash.png
        if getattr(sys, 'frozen', False):
            # Executável PyInstaller
            base_path = sys._MEIPASS
        else:
            # Desenvolvimento
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        splash_path = os.path.join(base_path, 'Splash.png')
        
        pixmap = QPixmap(splash_path)
        
        # Redimensionar se necessário mantendo proporção
        if pixmap.width() > max_width or pixmap.height() > max_height:
            pixmap = pixmap.scaled(max_width, max_height, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        
        super().__init__(pixmap, Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
        
        # Carregar logo teksea.png
        logo_path = os.path.join(base_path, 'teksea.png')
        self.logo = QPixmap(logo_path)
        if not self.logo.isNull():
            self.logo = self.logo.scaled(logo_width, logo_height, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.logo_width = logo_width
        self.logo_height = logo_height
        self.version = version
    
    def drawContents(self, painter):
        """Desenha texto customizado no splash"""
        # Desenhar logo no canto superior esquerdo
        if hasattr(self, 'logo') and not self.logo.isNull():
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            painter.drawPixmap(10, 10, self.logo)
        
        # Linha 1: "Emulador" (fonte maior)
        font1 = QFont("Arial", 36, QFont.Weight.Bold)
        painter.setFont(font1)
        rect1 = QRect(0, self.height() // 2 - 40, self.width(), 50)
        # Contorno preto
        painter.setPen(QColor("black"))
        for dx in [-2, 0, 2]:
            for dy in [-2, 0, 2]:
                if dx != 0 or dy != 0:
                    painter.drawText(rect1.adjusted(dx, dy, dx, dy), Qt.AlignmentFlag.AlignCenter, "Emulador")
        # Texto branco
        painter.setPen(QColor("white"))
        painter.drawText(rect1, Qt.AlignmentFlag.AlignCenter, "Emulador")
        
        # Linha 2: "MODBUS RTU" (fonte menor)
        font2 = QFont("Arial", 24, QFont.Weight.Bold)
        painter.setFont(font2)
        rect2 = QRect(0, self.height() // 2 + 10, self.width(), 40)
        # Contorno preto
        painter.setPen(QColor("black"))
        for dx in [-2, 0, 2]:
            for dy in [-2, 0, 2]:
                if dx != 0 or dy != 0:
                    painter.drawText(rect2.adjusted(dx, dy, dx, dy), Qt.AlignmentFlag.AlignCenter, "MODBUS RTU")
        # Texto branco
        painter.setPen(QColor("white"))
        painter.drawText(rect2, Qt.AlignmentFlag.AlignCenter, "MODBUS RTU")
        
        # Versão no canto inferior direito
        font_version = QFont("Arial", 10)
        painter.setFont(font_version)
        rect_version = QRect(0, self.height() - 30, self.width() - 10, 20)
        painter.drawText(rect_version, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom, self.version)
    
    def show_for_duration(self, duration_ms=2000):
        """Mostra splash por duração específica"""
        self.show()
        QTimer.singleShot(duration_ms, self.close)
