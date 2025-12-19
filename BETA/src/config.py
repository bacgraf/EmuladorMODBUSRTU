"""Gerenciamento de configurações do EmuladorMODBUSRTU"""
import json
import os


class Config:
    """Gerencia persistência de configurações"""
    
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.defaults = {
            "last_csv_path": "",
            "serial_port": "COM16",
            "baudrate": 19200,
            "bytesize": 8,
            "parity": "None",
            "stopbits": 1,
            "slave_id": 1
        }
        self.settings = self.load()
    
    def load(self):
        """Carrega configurações do arquivo"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return {**self.defaults, **json.load(f)}
            except:
                pass
        return self.defaults.copy()
    
    def save(self):
        """Salva configurações no arquivo"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except:
            pass
    
    def get(self, key, default=None):
        """Obtém valor de configuração"""
        return self.settings.get(key, default)
    
    def set(self, key, value):
        """Define valor de configuração"""
        self.settings[key] = value
        self.save()
    
    def update(self, **kwargs):
        """Atualiza múltiplas configurações"""
        self.settings.update(kwargs)
        self.save()
