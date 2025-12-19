# 🎉 Release Notes - v0.9.1-beta

**Data:** 2025-01-16  
**Versão:** 0.9.1-beta  
**Status:** Beta - Melhorias Críticas Implementadas

---

## 🆕 Novidades

### 1. Persistência de Configurações ✅
- **Novo módulo:** `src/config.py`
- Configurações agora são salvas automaticamente em `config.json`
- Ao reiniciar o emulador, as últimas configurações são restauradas:
  - Porta serial (COM)
  - Baudrate
  - Data bits
  - Paridade
  - Stop bits
  - Slave ID
  - Último CSV carregado

**Antes:**
```python
# Configurações perdidas ao fechar
```

**Agora:**
```python
from config import Config
config = Config()
config.set('serial_port', 'COM3')
# Salvo automaticamente!
```

---

### 2. Testes Automatizados ✅
- **Novos arquivos:**
  - `tests/test_csv_parser.py` - 6 testes completos
  - `tests/test_config.py` - 4 testes completos

**Executar testes:**
```bash
cd BETA
pip install -r requirements-dev.txt
pytest tests/ -v
```

**Cobertura:**
- ✅ Parsing de COIL, DISC, IREG, HREG
- ✅ Valores iniciais (ON/OFF)
- ✅ CSV vazio
- ✅ Persistência de configurações
- ✅ Update múltiplo

---

### 3. Estrutura Profissional ✅
- Projeto reorganizado em `BETA/`
- Versionamento semântico
- CHANGELOG.md atualizado
- Documentação completa

---

## 🔧 Melhorias Técnicas

### Módulo Config
```python
class Config:
    def __init__(self, config_file="config.json")
    def load()  # Carrega do arquivo
    def save()  # Salva no arquivo
    def get(key, default=None)
    def set(key, value)
    def update(**kwargs)  # Atualiza múltiplos
```

### Integração no main.py
```python
# Inicialização
self.config = Config()
self.csv_path = self.config.get('last_csv_path', '')

# Carregar configurações
self.port_combo.setCurrentText(self.config.get('serial_port', 'COM16'))
self.baudrate_combo.setCurrentText(str(self.config.get('baudrate', 19200)))

# Salvar ao iniciar servidor
self.config.update(
    serial_port=port,
    baudrate=baudrate,
    slave_id=slave_id
)
```

---

## 📊 Estatísticas

### Arquivos Modificados
- `src/main.py` - Integração com Config
- `src/config.py` - Novo módulo
- `tests/test_csv_parser.py` - 6 testes
- `tests/test_config.py` - 4 testes
- `CHANGELOG.md` - Atualizado
- `VERSION` - 0.9.0-beta → 0.9.1-beta
- `src/__init__.py` - __version__ atualizado

### Linhas de Código
- **Adicionadas:** ~250 linhas
- **Testes:** 10 testes automatizados
- **Cobertura:** csv_parser + config

---

## 🚀 Como Atualizar

### Se já tem v0.9.0-beta:
```bash
cd BETA
git pull  # ou copiar arquivos novos
pip install -r requirements-dev.txt
pytest tests/  # Verificar testes
python src/main.py
```

### Primeira instalação:
```bash
cd BETA
run.bat  # Instala tudo automaticamente
```

---

## 🎯 Próximos Passos (v0.9.2 ou v1.0.0)

### Alta Prioridade
- [ ] Log de requisições Modbus em tempo real
- [ ] Validação de endereços duplicados no CSV
- [ ] Adicionar mais testes (csv_editor, main)

### Média Prioridade
- [ ] Simplificar sistema de threading
- [ ] Modo de simulação (valores variando)
- [ ] Exportar estado atual para CSV

### Baixa Prioridade
- [ ] Tema escuro
- [ ] Gráficos em tempo real
- [ ] Modbus TCP

---

## 🐛 Bugs Corrigidos

Nenhum bug conhecido nesta versão.

---

## ⚠️ Breaking Changes

Nenhuma mudança incompatível. Totalmente compatível com v0.9.0-beta.

---

## 📝 Notas de Migração

### De v0.9.0-beta para v0.9.1-beta:

1. **Arquivo de configuração mudou:**
   - Antes: `emulator_modbus_config.txt` (apenas CSV)
   - Agora: `config.json` (todas as configurações)
   
2. **Compatibilidade:**
   - Se existir `emulator_modbus_config.txt`, será ignorado
   - Configurações serão resetadas para padrão na primeira execução
   - Após primeira execução, tudo será salvo em `config.json`

3. **Nenhuma ação necessária:**
   - Apenas execute normalmente
   - Configurações serão salvas automaticamente

---

## 🙏 Agradecimentos

Obrigado por testar a versão beta!

---

## 📧 Suporte

- Issues: GitHub Issues
- Documentação: `BETA/README.md`
- Guia Rápido: `BETA/QUICKSTART.md`

---

**Versão:** 0.9.1-beta  
**Próxima Release:** v1.0.0 (estável)  
**ETA:** A definir
