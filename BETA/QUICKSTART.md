# 🚀 Guia Rápido - EmuladorMODBUSRTU BETA

## Instalação em 3 Passos

### 1️⃣ Executar Script Automático (Recomendado)
```bash
run.bat
```
Este script:
- Cria ambiente virtual automaticamente
- Instala todas as dependências
- Inicia o emulador

### 2️⃣ Instalação Manual
```bash
# Criar ambiente virtual
python -m venv .venv
.venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt

# Executar
python src/main.py
```

### 3️⃣ Usar Executável (após compilar)
```bash
cd build
build.bat
# Executável estará em: dist/EmuladorMODBUSRTU/EmuladorMODBUSRTU.exe
```

## 📖 Uso Básico

1. **Carregar Mapa de Memória**
   - Clique em "Selecionar..."
   - Escolha `examples/exemplo_mapa.csv`

2. **Configurar Porta Serial**
   - Porta: COM16 (ou sua porta)
   - Baudrate: 19200
   - Slave ID: 1

3. **Iniciar Servidor**
   - Clique em "Iniciar Servidor"
   - Status: 🟢 Rodando

4. **Interagir**
   - Coils/DI: Clique ON/OFF
   - IR/HR: Digite valores

## 🛠️ Desenvolvimento

### Estrutura de Arquivos
```
BETA/
├── src/           # Código fonte (editar aqui)
├── tests/         # Testes (adicionar aqui)
├── docs/          # Documentação
├── examples/      # Exemplos de CSV
└── build/         # Scripts de compilação
```

### Adicionar Nova Funcionalidade
```bash
# 1. Editar código em src/
# 2. Adicionar teste em tests/
# 3. Atualizar CHANGELOG.md
# 4. Commit
git commit -m "feat: nova funcionalidade"
```

### Executar Testes
```bash
pip install -r requirements-dev.txt
pytest tests/
```

### Criar Nova Versão
```bash
# 1. Atualizar VERSION
echo "1.0.0" > VERSION

# 2. Atualizar CHANGELOG.md
# 3. Atualizar src/__init__.py
# 4. Commit e tag
git commit -m "chore: bump version to 1.0.0"
git tag -a v1.0.0 -m "Release v1.0.0"
```

## 📚 Documentação Completa

- [README.md](README.md) - Documentação principal
- [CHANGELOG.md](CHANGELOG.md) - Histórico de mudanças
- [VERSIONING.md](VERSIONING.md) - Guia de versionamento
- [TODO.md](TODO.md) - Funcionalidades planejadas

## ❓ Problemas Comuns

**Porta COM em uso**
- Aguarde 8 segundos após parar servidor
- Feche outros programas usando a porta

**Erro ao carregar CSV**
- Verifique formato do CSV
- Use `examples/exemplo_mapa.csv` como referência

**PyQt6 não encontrado**
- Execute: `pip install -r requirements.txt`

## 📧 Suporte

Abra uma issue no GitHub ou consulte a documentação completa.
